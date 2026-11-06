# Graph-Based Retrieval-Augmented Generation

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Graph-based retrieval-augmented generation constitutes the task family of answering questions against an explicit graph index rather than against passages alone, using either hierarchical community summaries for corpus-wide questions or bounded entity neighbourhoods for entity-specific questions. This guide provides AI agents with a structured protocol for deciding whether a graph index is justified, constructing the retrieval-side artifacts, routing each query to exactly one mode, traversing under hard budgets, and maintaining the index as source material changes. It treats the underlying knowledge graph as an input produced by a separate construction discipline and verified before retrieval use, so that this guide governs retrieval over a graph rather than the building of one. It specifies an indexing cost estimate that must precede construction, a break-even condition below which a simpler retrieval architecture is the correct choice, a routing rule that classifies each query as global, local, hybrid, or no-graph together with the recovery path for a misclassification in each direction, an execution tier partition assigning graph storage, community detection, traversal, cost accounting, and citation resolution to deterministic software and extraction, summarisation, and synthesis to model calls, and a re-indexing policy bounding the blast radius of a source change.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Graph index**: The complete set of retrieval-side artifacts derived from a knowledge graph: the served node and edge projections, the seed indexes over entity names and descriptions, the community partition, the community summary hierarchy, and the manifests that make all of them reproducible from a stated graph version.

**Knowledge graph**: The store of canonical entities, typed relation assertions, qualifiers, and provenance links from which the graph index is derived. It is an input to this method, governed by the construction guides named in Section 1.2.

**Assertion**: An addressable relation record carrying subject, predicate, object, direction, polarity, confidence, valid-time interval, transaction-time interval, and at least one evidence reference to an immutable source span. Assertions are the only graph artifacts a material claim may cite.

**Community**: A cluster of entities produced by a graph partitioning algorithm run over the served edge projection. A community is an algorithmic artifact, not a real-world grouping and not an ontology class.

**Community summary**: A model-generated report describing one community at one hierarchy level, bound to the exact assertion set that supported it and invalidated when that set changes.

**Community level**: One tier of the summary hierarchy. Lower levels hold more, smaller communities and therefore more reports; higher levels hold fewer, broader reports.

**Global query mode**: The mode that answers a question about themes, distributions, comparisons, or aggregates across the corpus by mapping the question over community summaries at a selected level, rating and filtering partial results, and reducing them into an answer.

**Local query mode**: The mode that answers a question about named or implied entities by resolving seed entities, expanding a bounded neighbourhood, and assembling the connected assertions and their supporting text.

**Hybrid query mode**: The mode that begins from community summaries to establish corpus context and then refines through bounded local expansion, used where a question names entities but requires corpus-level framing.

**Seed entity**: A canonical entity resolved from the query text by identifier match, alias match, lexical match, or embedding match, from which local expansion begins.

**Frontier**: The set of nodes eligible for expansion at the current traversal round, after relation-type, direction, time, confidence, provenance, and authorization filters have been applied.

**Evidence packet**: The token-bounded, deterministically ordered serialisation of selected assertions, paths, community context, and supporting source spans that is handed to the synthesis call.

**Indexing cost**: The total model and compute cost of producing the graph index from a corpus, dominated by extraction calls over chunks and summarisation calls over communities at every retained level.

**Break-even query volume**: The number of queries over one re-index interval at which the amortised indexing cost equals the cumulative per-query saving that the graph index delivers over the incumbent architecture.

**Re-index interval**: The declared period, or the declared quantity of source change, after which the graph index is rebuilt or incrementally repaired.

**Blast radius**: The set of chunks, entities, assertions, embeddings, communities, summaries, caches, and evaluation cases that a single source change invalidates.

**Mode misroute**: A query answered in a mode other than the one its evidence requirement demanded, detected after the fact by mode-specific evidence signatures rather than by the router's own confidence.

**Material claim**: A statement in the answer that a reader would act on, which must resolve to at least one admitted source span. The term is used as defined in the companion retrieval guides.

### 1.2 The Scope Boundary Against Knowledge Graph Construction

This guide governs retrieval over a graph. It does not govern the building of one. The distinction is load-bearing, because the two disciplines have different owners, different quality gates, and different failure modes, and conflating them produces a guide that verifies neither.

**Owned by the construction discipline**: Schema and ontology design, competency-question capture, identity criteria, entity resolution and deduplication, coreference handling, relation normalisation, constraint validation, provenance modelling, identifier policy, storage scalability, and the human review paths that govern all of them. These are specified in `advanced_task_guides/knowledge-graphs/guide_KG_SchemaDesign.md`, `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md`, `advanced_task_guides/knowledge-graphs/guide_KG_QualityControl.md`, `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md`, `advanced_task_guides/knowledge-graphs/guide_KG_identifierFairPrinciples.md`, `advanced_task_guides/knowledge-graphs/guide_KG_ScalabilityArch.md`, and `advanced_task_guides/knowledge-graphs/guide_KG_HumanAIcolab.md`. Agents needing a method for any of them load the relevant guide rather than improvising one here.

**Owned by this guide**: The extraction contract that the constructed graph must satisfy before retrieval consumes it, the verification applied to that contract, the retrieval-side projections and seed indexes, community detection and hierarchical summarisation, query classification and mode routing, bounded traversal and path selection, evidence assembly and citation resolution, the indexing cost gate, and incremental re-indexing driven by retrieval-side invalidation.

**The handoff**: The construction discipline delivers a versioned graph and a quality report. This guide accepts it only where the report satisfies the numeric thresholds in Step 2.2, and returns it otherwise. Extraction quality bounds everything downstream: a false merge creates spurious paths that traversal will find and synthesis will cite, and a dropped qualifier converts a conditional assertion into an unconditional one that no retrieval control can repair. No traversal bound, reranking pass, or synthesis instruction recovers evidence the graph never carried or corrects an entity that the graph merged wrongly.

**The neighbouring retrieval boundary**: Passage-level retrieval, chunking, lexical and dense indexing, fusion, and reranking are specified in `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md`, which places graph-backed retrieval at rung 12 of its selection ladder. Multi-round agent-controlled retrieval with tool selection and evidence-gain budgets is specified in `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md`. This guide assumes both are available and does not restate them.

### 1.3 The Global and Local Query Mode Partition

Two query modes organise the method. They read different artifacts, carry different cost profiles, fail differently, and hold different evidence standards. A system that runs one mode for all traffic is either overspending or under-answering.

**Global mode**: Reads community summaries at a selected level. Cost scales with the number of reports at that level, because each report costs at least one model call in the map stage. Latency is dominated by that fan-out. Its evidence standard is coverage: the answer must draw on a declared minimum number of distinct communities and must state the level it was computed at, because a theme derived from three reports out of four hundred is not a corpus-wide finding. Its characteristic failure is aggregation loss, where a specific fact present in one report is averaged out of the reduced answer.

**Local mode**: Reads entity neighbourhoods. Cost scales with fan-out and hop count, not with corpus size, so it is the cheaper mode by one to two orders of magnitude on a large corpus. Its evidence standard is path validity: every material claim resolves to an assertion whose direction, valid-time interval, and provenance survive inspection. Its characteristic failure is coverage collapse, where the seed entities are resolved correctly but the answer-bearing assertions sit outside the expanded neighbourhood.

**Hybrid mode**: Reads a small set of semantically selected community summaries to establish context, emits follow-up sub-questions, and answers them by local expansion. It costs more than local mode and less than a full global map-reduce. It is admitted only where a measured slice shows it beating both single modes.

**No-graph route**: Passage retrieval without any graph operation. It is the correct route for single-passage lookups, quotations, definitions, and exact identifier searches, and it remains the majority route on most corpora.

**The routing rule**: A query routes to local mode where at least 1 and at most 5 canonical entities resolve from the query text at or above the seeding confidence threshold, and the question's answer is expected within 3 hops of that seed set. It routes to global mode where no bounded entity set exists whose neighbourhood could contain the answer, which is the case for questions about themes, distributions, prevalence, comparisons across the corpus, or the absence of something. It routes to hybrid mode where entities resolve but the question also asks how those entities sit relative to the corpus. It routes to no-graph where the question requires no relation traversal, which the classifier detects as zero required relation hops. Where the classifier's confidence falls below 0.70, the router runs the local probe first, because local is the cheaper mode and its failure is detectable in one round.

**Misclassification in the local-to-global direction**: A global question answered locally produces a confident answer supported by a small neighbourhood that is unrepresentative of the corpus. It is detected deterministically when the assembled evidence spans fewer than 3 distinct communities or fewer than 5 distinct source documents while the question carried a corpus-scope marker. The recovery is a single promotion to global mode at the next higher community level, charged against the query budget, with the local answer discarded rather than merged.

**Misclassification in the global-to-local direction**: A local question answered globally spends the full map-reduce cost and returns a generic summary that omits the specific value. It is detected when the reduced answer contains no claim resolving to an assertion-level citation, or when the question named an identifier or an exact value that the answer does not carry. The recovery is demotion to local mode, but the global cost is already spent and is not recoverable, which is why the router runs the cheap entity-resolution probe before committing to global mode on any query whose classification confidence is below 0.70.

**Mode Selection and Failure Signature Table**:

| Mode | Entry condition | Cost driver | Evidence standard | Detected misroute signature |
| :-- | :-- | :-- | :-- | :-- |
| No-graph | Zero required relation hops | Passage retrieval only | Answer-bearing span cited | Answer needs a relation the passage does not state |
| Local | 1 to 5 seed entities resolve, answer within 3 hops | Fan-out and hop count | Every material claim on a valid assertion path | Fewer than 3 communities or 5 documents covered on a corpus-scope question |
| Hybrid | Seeds resolve and corpus framing required | Selected reports plus local rounds | Both standards, applied per sub-question | Follow-up questions repeat without new coverage |
| Global | No bounded entity set contains the answer | Report count at the selected level | Minimum distinct-community coverage met | Zero assertion-level citations in the reduced answer |

### 1.4 Execution Tier Partition and Authority

The partition below is binding on every phase of Section II. Every step names the tier that owns it, and every step mixing tiers names the handoff.

**Deterministic tier**: Software, graph queries, partitioning libraries, schema validators, budget services, and manifest stores own everything requiring exactness, reproducibility, auditability, or scale. This tier owns graph storage and the served projections; community detection, including the random seed, resolution parameter, and size threshold that make a partition reproducible; every traversal operation, including frontier construction, filter application, fan-out capping, path enumeration, and cycle detection; index maintenance, including blast-radius computation, summary invalidation, and version promotion; cost accounting across extraction tokens, summarisation tokens, query tokens, model calls, graph operations, latency, and money; authorization decisions at seeding, at every traversed node and edge, at summarisation scope, and again at serialisation; and citation resolution, which matches every claim in the answer against an admitted source span. Outputs of this tier are reproducible from the graph version, the index manifest, and the query.

**Model tier**: LLM calls own work requiring open-vocabulary judgement no deterministic rule covers. This tier owns entity and relation extraction from source text, community summarisation, query classification into a mode, the proposal of sub-questions in hybrid mode, relevance rating of community reports in the global map stage, and answer synthesis from the evidence packet. This tier never enforces authorization, never sets or raises a budget, never selects the community partition, and never declares its own output supported.

**Hybrid tier**: Work where the model proposes and software verifies. Extraction is a model proposal that a validator accepts or rejects against the extraction contract. Query classification is a model label that the deterministic router accepts only where the label's precondition holds, so a local label with zero resolved seed entities is rejected and re-routed. Community summarisation is a model output whose supporting assertion set is fixed by software before the call and checked against the summary after it. Answer synthesis is a model output whose citations a deterministic resolver admits or rejects.

**Authority on disagreement**: The deterministic tier holds authority in every conflict, without exception. A model may narrow a traversal, lower a hop bound, abstain early, or decline to answer. A model may never raise a budget ceiling, extend a frontier the filters excluded, add a citation the resolver rejected, promote a query to a more expensive mode after the budget is exhausted, or mark a summary faithful on its own assertion.

**Tier Ownership by Artifact**:

| Artifact | Owning tier | Rejection rule enforced deterministically |
| :-- | :-- | :-- |
| Extracted entities and assertions | Hybrid | An assertion whose evidence span does not contain its subject and object is rejected |
| Graph version and index manifest | Deterministic | An index built from an unpinned graph version is rejected |
| Community partition | Deterministic | A partition without a recorded seed, resolution, and size threshold is rejected |
| Community summary text | Hybrid | A summary citing an assertion outside its fixed input set is rejected |
| Query mode label | Hybrid | A local label with zero resolved seed entities is rejected and re-routed |
| Frontier and traversal path set | Deterministic | A path containing an unauthorized edge or an invalid direction is dropped |
| Evidence packet | Deterministic | Content exceeding the token ceiling is truncated at a path boundary, never at a provenance field |
| Answer text | Model | Not applicable |
| Citation resolution | Deterministic | A citation resolving only to a community summary marks the claim unsupported |
| Cost ledger and gate verdicts | Deterministic | A gate verdict produced from a model estimate rather than a metered figure is rejected |

***

## II. Operational Framework: Cost-Gated Graph Index Construction and Mode-Routed Retrieval

The framework assumes an incumbent passage-retrieval baseline exists and is measured, and that a knowledge graph is either available or buildable under the construction guides named in Section 1.2. Phases 1 through 3 build the graph index and may terminate the adoption at any gate. Phases 4 and 5 run per query. Phase 6 runs on source change and returns control to Phase 1 where the break-even condition lapses.

### Phase 1: Corpus Scoping, Mode Demand Profiling, and Indexing Cost Estimation

**Objective**: Establish what fraction of real query traffic needs a graph operation, estimate the cost of building the index that would serve it, and state the condition under which the adoption is abandoned in favour of a simpler architecture.

#### Step 1.1: Profile Query Demand Across the Four Routes

**Required Actions**:

- Sample at least 300 real queries from production logs, or from a stakeholder-elicited set where no logs exist, stratifying by task rather than by frequency so rare high-value classes survive.
- Label every sampled query with its required route, no-graph, local, hybrid, or global, applying the routing rule in Section 1.3 by hand against the labelled answer.
- Record for each graph-requiring query the minimum number of relation hops its answer needs and the number of distinct source documents its evidence spans.
- Compute the route mix as four proportions summing to 1.00, and compute the share of traffic that no graph operation would serve.
- Reject the adoption at this step where the combined local, hybrid, and global share falls below 15 percent of sampled traffic, recording the measured share as the reason.

**Required Outputs**:

- A route-labelled query sample of at least 300 entries with per-query hop counts and document spans.
- A route mix expressed as four proportions with confidence intervals where the sample supports them.
- A named target slice identifying the query class the graph index exists to serve.

**Quality Checkpoints**:

- The route mix proportions sum to 1.00 and every entry carries exactly one route label.
- The target slice is named as a query class, not as a general expectation of improvement.
- The combined graph-requiring share is at or above 15 percent, or the adoption is recorded as rejected at this step.

***

#### Step 1.2: Estimate Indexing Cost Before Any Construction Runs

**Required Actions**:

- Draw a pilot sample of 1 to 5 percent of corpus chunks, matched to the full corpus on document length, source type, and entity density within 10 percent on each dimension.
- Run extraction over the pilot sample only, metering input tokens, output tokens, model calls, retries, and wall time per chunk.
- Run community detection and summarisation over the pilot graph, metering summarisation tokens and calls per community and recording the community count at every retained level.
- Extrapolate total indexing cost as pilot extraction cost per chunk multiplied by total chunks, plus pilot summarisation cost per community multiplied by the projected community count at every retained level, and state the result as a range whose upper bound is 1.5 times the point estimate.
- Add the recurring cost of the re-index policy proposed in Phase 6, expressed as cost per re-index interval, because a one-time build figure understates total cost on any corpus that changes.
- Halt and escalate where the point estimate exceeds the approved budget, rather than starting construction and discovering the overrun mid-build.

**Required Outputs**:

- A metered pilot cost record covering extraction and summarisation separately.
- A total indexing cost estimate stated as a point value and an upper bound.
- A recurring re-indexing cost figure per interval.

**Quality Checkpoints**:

- Every cost figure derives from a metered pilot run rather than from a model's estimate or a published benchmark.
- The pilot sample matches the corpus on length, source type, and entity density within 10 percent on each dimension.
- The estimate separates extraction cost from summarisation cost, because the two scale with different quantities and only one of them scales with community count.

***

#### Step 1.3: Declare the Break-Even Condition and the Abandonment Rule

**Required Actions**:

- Measure the incumbent baseline's per-query cost and its accuracy on the target slice, holding answer model, context-token ceiling, and authorization policy constant.
- Estimate the graph index's per-query cost by mode from the pilot, weighted by the route mix from Step 1.1.
- Compute the break-even query volume as total indexing cost per interval divided by the per-query saving; where the graph index costs more per query than the baseline, record that no volume produces cost break-even and that the adoption must rest on the accuracy gain instead.
- Declare the accuracy admission threshold: the graph index is admitted only where it improves the primary metric on the target slice by at least 5 percentage points over the incumbent on a frozen evaluation set, with no regression above 2 percentage points on any other slice and no regression on any citation or authorization gate.
- Declare the abandonment rule in advance, naming the measured conditions that retire the graph index and return traffic to the baseline.

**Required Outputs**:

- A break-even query volume figure, or a recorded statement that cost break-even is unreachable.
- A stated accuracy admission threshold with its slice, metric, and measurement conditions.
- A written abandonment rule carrying numeric triggers.

**Quality Checkpoints**:

- The break-even calculation uses the metered indexing cost from Step 1.2 and the projected query volume over one re-index interval, not over an unbounded horizon.
- The admission threshold names a metric, a slice, and a frozen evaluation set rather than an unqualified expectation of better answers.
- The abandonment rule is written before construction begins, so retirement is a measurement rather than a negotiation.

***

### Phase 2: Graph Index Construction for Retrieval

**Objective**: Accept a constructed graph under a verified extraction contract and derive the served projections and seed indexes that retrieval will read, so that no retrieval operation runs against an unverified graph.

#### Step 2.1: Bind the Extraction Contract and Pin the Graph Version

**Required Actions**:

- Obtain the extraction contract from the construction discipline, naming the permitted entity types, relation types, direction, required qualifiers, temporal representation, provenance fields, and confidence semantics.
- Reject any relation type that no query in the Step 1.1 sample requires, because every retained type adds extraction cost, traversal fan-out, and evaluation surface without serving traffic.
- Pin the graph version, the extraction model and prompt versions, the schema or ontology version, and the constraint version into a single immutable manifest that every downstream artifact references.
- Confirm that every assertion carries at least one evidence reference resolving to an immutable source span with document identifier, version, and offsets, and quarantine assertions that do not.
- Record the authorization labels attached to each node, edge, and property, and confirm the policy decision point can evaluate them before any retrieval reads the graph.

**Required Outputs**:

- An extraction contract record listing permitted types with the query class each serves.
- An immutable graph index manifest pinning every version the index depends on.
- A quarantine set of assertions lacking resolvable evidence references.

**Quality Checkpoints**:

- Every retained relation type maps to at least 1 query in the Step 1.1 sample.
- The manifest pins every version, and an index built from an unpinned graph version is rejected before it is served.
- 100 percent of served assertions carry a resolvable evidence reference; quarantined assertions are excluded from every projection.

***

#### Step 2.2: Verify Extraction Quality Before the Graph Is Used for Retrieval

**Required Actions**:

- Draw a stratified verification sample of at least 200 served assertions, covering every relation type, every source class, and every confidence band, with at least 20 assertions per relation type that carries more than 1 percent of edge mass.
- Adjudicate each sampled assertion against its cited source span for subject identity, object identity, predicate meaning, direction, polarity, and qualifier retention, recording a single pass or fail verdict per dimension.
- Compute edge validity as the proportion of sampled assertions passing every dimension, and compute direction accuracy and qualifier retention separately, because a direction error and a dropped qualifier fail in different ways downstream.
- Obtain the entity-resolution false-merge rate and false-split rate from the construction discipline's quality report, and recompute the false-merge rate on the 20 highest-degree entities, since a false merge on a hub creates spurious paths across the whole graph.
- Return the graph to construction where edge validity falls below 0.90, where direction accuracy falls below 0.95, where the overall false-merge rate exceeds 0.02, or where the high-degree false-merge rate exceeds 0.00, and record the failing figure rather than proceeding with a warning.

**Required Outputs**:

- A verification report with edge validity, direction accuracy, qualifier retention, and false-merge and false-split rates, each with its sample size.
- A high-degree entity audit covering the 20 highest-degree served entities.
- An accept or return verdict with the failing figure named where the verdict is return.

**Quality Checkpoints**:

- Edge validity is at or above 0.90, direction accuracy at or above 0.95, and qualifier retention at or above 0.90 on the verification sample.
- The false-merge rate is at or below 0.02 overall and exactly 0.00 on the 20 highest-degree entities.
- No retrieval artifact is built from a graph whose verification verdict is return.

***

#### Step 2.3: Build the Served Projections and Seed Indexes

**Required Actions**:

- Materialise the served edge projection from accepted assertions only, carrying edge identifier, direction, type, confidence, valid-time interval, provenance key, and authorization label on every edge.
- Build the seed index over canonical entity names, aliases, external identifiers, and entity descriptions, supporting exact identifier match, normalised alias match, lexical match, and embedding match in that precedence order.
- Compute and store the degree distribution, and mark every entity above the 99th degree percentile as a hub, so traversal can penalise hubs without recomputing degree per query.
- Materialise the assertion-to-source-span map that citation resolution will read, keyed so that resolution is a lookup rather than a search.
- Verify the projection is reproducible by rebuilding it from the pinned manifest and confirming that node count, edge count, and edge-set hash match the original exactly.

**Required Outputs**:

- A served edge projection with the full per-edge attribute set.
- A seed index with the four match strategies and their precedence order recorded.
- A hub register listing every entity above the 99th degree percentile.
- An assertion-to-source-span map supporting constant-time citation resolution.

**Quality Checkpoints**:

- The rebuilt projection matches the original on node count, edge count, and edge-set hash exactly; any mismatch blocks serving.
- Every served edge carries a non-null direction, valid-time interval, provenance key, and authorization label.
- Seed index precedence is recorded and enforced by software, so an embedding match never outranks an exact identifier match.

***

### Phase 3: Community Detection and Hierarchical Summarisation

**Objective**: Partition the served graph reproducibly and generate the summary hierarchy that global mode reads, under a summarisation budget that bounds the dominant indexing cost.

#### Step 3.1: Run Community Detection Under a Pinned Deterministic Configuration

**Required Actions**:

- Select a hierarchical partitioning algorithm and record its name, version, random seed, resolution parameter, edge-weight policy, and maximum community size threshold in the index manifest, since a partition without these is not reproducible and therefore not auditable.
- Run detection recursively until every community falls at or below the size threshold, recording the resulting level count and the community count at each level.
- Compute partition stability by repeating detection with at least 5 different random seeds and measuring the proportion of entity pairs assigned to the same community across runs.
- Reject the partition and either raise the resolution parameter or reduce hub influence where pairwise stability falls below 0.80, because an unstable partition produces summaries that change between builds for no source reason.
- Record community size distribution, and flag any level whose largest community exceeds 20 percent of served entities, since a single dominant community defeats the purpose of the partition.

**Required Outputs**:

- A community partition with a level identifier, parent identifier, membership set, and membership hash per community.
- A pinned detection configuration recorded in the index manifest.
- A stability report across at least 5 seeds with the pairwise agreement figure.

**Quality Checkpoints**:

- The partition is reproducible from the manifest: a re-run with the recorded seed and parameters yields identical membership hashes.
- Pairwise membership stability across 5 seeds is at or above 0.80.
- No community at any level holds more than 20 percent of served entities.

***

#### Step 3.2: Generate Level-Bounded Community Summaries Under a Budget

**Required Actions**:

- Decide which levels are summarised before any summarisation call runs, and justify each retained level by naming the global query class it serves, because summarisation cost scales with the number of reports and lower levels multiply that count.
- Fix the input assertion set for each community summary deterministically before the model call, so the summary's provenance is a software-owned fact rather than a model claim.
- Restrict each summary's input set to assertions sharing one authorization scope, or generate policy-homogeneous summaries per scope, so that no report mixes evidence a single reader may not see.
- Meter summarisation tokens, calls, and cost per community and per level against the Step 1.2 estimate, halting the build where cumulative cost exceeds 1.5 times the estimate rather than continuing to completion.
- Cache each summary under a key combining the membership hash, the input assertion-set hash, the summarisation prompt version, and the authorization scope, so an unchanged community is never re-summarised.

**Required Outputs**:

- A summary set covering every retained level, each summary bound to its input assertion-set hash and authorization scope.
- A per-level summarisation cost record compared against the Step 1.2 estimate.
- A summary cache keyed on membership, input, prompt version, and scope.

**Quality Checkpoints**:

- Every retained level names the global query class it serves; a level serving no class is dropped before summarisation runs.
- Cumulative summarisation cost stays at or below 1.5 times the Step 1.2 estimate, or the build halts and escalates.
- No summary mixes assertions from more than 1 authorization scope.

***

#### Step 3.3: Certify Summary Faithfulness and Bind Invalidation Dependencies

**Required Actions**:

- Sample at least 30 summaries per retained level, or all of them where a level holds fewer than 30, and adjudicate every claim in each sampled summary against its fixed input assertion set.
- Compute summary faithfulness as the proportion of summary claims traceable to at least 1 input assertion, and unsupported-claim rate as its complement.
- Reject the summary set and regenerate with a tighter prompt where faithfulness falls below 0.95 at any level, because global answers inherit every unsupported claim their source reports carry.
- Record the invalidation dependency for every summary: the assertion identifiers it consumed, the membership hash it was computed from, and the parent summaries that consumed it, so Phase 6 can invalidate precisely rather than rebuilding everything.
- Mark every summary as derived evidence in the serving layer, so that citation resolution can distinguish a summary from an assertion and refuse a material claim supported only by a summary.

**Required Outputs**:

- A faithfulness report per level with sample size, faithfulness figure, and unsupported-claim rate.
- An invalidation dependency record per summary listing consumed assertions and consuming parents.
- A derived-evidence marking applied to 100 percent of summaries in the serving layer.

**Quality Checkpoints**:

- Summary faithfulness is at or above 0.95 at every retained level.
- Every summary carries a complete invalidation dependency record; a summary without one cannot be maintained and is rejected.
- Citation resolution treats every summary as derived, so no material claim resolves to a summary alone.

***

### Phase 4: Query Classification and Mode Routing

**Objective**: Assign each query to exactly one route under a rule software enforces, charge the route against a mode-specific budget, and detect a misroute before its cost compounds.

#### Step 4.1: Classify the Query and Resolve Candidate Seed Entities

**Required Actions**:

- Extract from the query text the named entities, the implied relation constraints, the direction and temporal constraints, the negations, and the expected answer form, emitting a structured intent record rather than a free-text interpretation.
- Resolve candidate seed entities against the seed index in the recorded precedence order, and record the match strategy, the score, and the margin over the runner-up for every candidate.
- Emit a route label with a confidence figure, drawn from the closed vocabulary of no-graph, local, hybrid, and global.
- Compute the corpus-scope marker deterministically from the query text, set where the query asks for themes, prevalence, distribution, comparison across the corpus, or the absence of something, since this marker is the primary evidence for a global route.
- Compute the required hop count as the minimum number of relation traversals the intent record implies, and set it to 0 where the answer is a single stated property.

**Required Outputs**:

- A structured intent record with entities, relation constraints, temporal constraints, negations, and expected answer form.
- A ranked seed candidate set with match strategy, score, and margin per candidate.
- A route label with a confidence figure and a computed corpus-scope marker.

**Quality Checkpoints**:

- The route label is one of exactly 4 values; a label outside the vocabulary is rejected and the query is re-classified once.
- Every seed candidate carries a match strategy and a margin, so precedence violations are detectable.
- The corpus-scope marker and the required hop count are computed by software from the intent record, never asserted by the classifying model.

***

#### Step 4.2: Enforce the Routing Rule and the Mode Budget

**Required Actions**:

- Reject a local label carrying zero resolved seed entities above the seeding confidence threshold, and re-route to global where the corpus-scope marker is set or to no-graph where it is not.
- Reject a global label where 1 to 5 seed entities resolve, the corpus-scope marker is clear, and the required hop count is at or below 3, because that combination defines a local query and global mode would spend the map-reduce cost for nothing.
- Run the local probe first where classification confidence falls below 0.70, since local mode is the cheaper mode and its insufficiency is detectable in 1 round.
- Charge the route against its mode budget before execution: a per-query token ceiling, a model-call ceiling, a graph-operation ceiling, and a wall-clock deadline, each set separately per mode because their cost profiles differ by more than an order of magnitude.
- Refuse execution and abstain where the projected cost of the selected mode exceeds the remaining query budget, rather than starting a map-reduce that the budget cannot finish.

**Required Outputs**:

- A final route decision with the rule clause that produced it and the rejected labels recorded.
- A mode budget allocation covering tokens, model calls, graph operations, and wall clock.
- A pre-execution cost projection compared against the remaining budget.

**Quality Checkpoints**:

- Every route decision names the rule clause that produced it, so routing is auditable rather than opaque.
- No query executes in global mode with 1 to 5 resolved seeds, a clear corpus-scope marker, and a hop requirement at or below 3.
- No mode executes where its projected cost exceeds the remaining budget; the query abstains instead.

***

#### Step 4.3: Detect Misroutes in Both Directions and Execute One Recovery

**Required Actions**:

- Detect the local-to-global misroute after local assembly by testing whether the assembled evidence spans at least 3 distinct communities and at least 5 distinct source documents on any query carrying the corpus-scope marker, and promote to global mode once where it does not.
- Detect the global-to-local misroute after the reduce stage by testing whether the reduced answer carries at least 1 claim resolving to an assertion-level citation, and demote to local mode once where it does not.
- Permit exactly 1 recovery per query, and record the recovery as a routing failure against the classifier rather than as a normal execution path, so that classifier quality is measurable.
- Discard the misrouted answer rather than merging it with the recovered answer, because a merged answer inherits the coverage defect that triggered the recovery.
- Abstain with the supported partial result where the recovery would exceed the remaining budget, stating which mode was attempted and what evidence standard was not met.

**Required Outputs**:

- A misroute verdict per query with the failing signature named.
- At most 1 recorded recovery per query, attributed to the classifier.
- A routing failure ledger supporting per-class classifier accuracy measurement.

**Quality Checkpoints**:

- At most 1 recovery executes per query; a second detected misroute terminates the query in abstention.
- No answer produced under a detected misroute is merged into the recovered answer.
- Every recovery is attributed to the classifier, so recovery rate is measurable per query class rather than absorbed as ordinary cost.

***

### Phase 5: Traversal, Evidence Assembly, and Answer Synthesis

**Objective**: Gather the smallest evidence set that answers the query under hard traversal bounds, serialise it without losing direction, time, or provenance, and admit only claims whose citations resolve.

#### Step 5.1: Execute Bounded Local Traversal

**Required Actions**:

- Construct the frontier from the resolved seed set, applying relation-type, direction, valid-time, confidence, provenance, and authorization filters before expansion rather than after it, since post-retrieval filtering is not access control.
- Expand at most 3 hops and at most 3 traversal rounds by default, and cap per-node fan-out at 25 neighbours, total nodes at 200, and total edges at 500, tightening every bound on graphs whose 99th-percentile degree exceeds 500.
- Penalise hub entities from the Step 2.3 hub register by requiring a hub to satisfy a relation-type constraint from the intent record before it enters the frontier, because an unconstrained hub expansion floods the evidence set with unrelated neighbours.
- Compute evidence gain per round as the count of newly covered intent constraints supported by non-duplicate assertions, and stop expansion where gain falls to 0 for 1 round, where the frontier hash repeats, or where any budget dimension is exhausted.
- Run at most 1 constrained path search or connecting-subgraph search where required terminals remain disconnected after the hop bound, rejecting any path containing an invalid direction, a temporally impossible join, an unauthorized edge, or an inferred edge the intent record disallows.

**Required Outputs**:

- A bounded subgraph carrying the smallest connected assertion set that covers the intent constraints.
- A per-round traversal record with frontier size, nodes and edges touched, filters applied, evidence gain, and stop reason.
- A coverage report naming every intent constraint left unsatisfied.

**Quality Checkpoints**:

- Hop count, round count, fan-out, node count, and edge count all stay at or below their declared bounds; a breach terminates traversal rather than raising the bound.
- No path in the returned subgraph contains an unauthorized edge, an invalid direction, or a temporally impossible join.
- Traversal stops on a declared condition, and the stop reason is recorded for every query.

***

#### Step 5.2: Execute Global Map-Reduce Over a Selected Community Level

**Required Actions**:

- Select the community level before the map stage from the intent record's breadth, defaulting to the highest level whose report count fits the mode budget, and record the selected level with the answer because a theme is only meaningful relative to the granularity it was computed at.
- Restrict the mapped report set to summaries whose authorization scope the requester satisfies, and never widen the set to improve coverage.
- Rate each mapped report for relevance and extract rated partial points, discarding points below the relevance threshold before the reduce stage rather than carrying them into it.
- Enforce the coverage standard: require partial points from at least 3 distinct communities and at least 5 distinct source documents before the reduce stage runs, and abstain with the coverage figure where the standard is not met.
- Trace every reduced claim back to the partial point, the community summary, and the underlying assertions that produced it, so a global answer remains resolvable to primary evidence.

**Required Outputs**:

- A selected community level recorded with the answer.
- A rated partial-point set with per-point community and document attribution.
- A coverage figure stating distinct communities and distinct documents contributing to the answer.

**Quality Checkpoints**:

- The selected level and its report count are recorded, and the report count stays within the global mode budget.
- The coverage standard of at least 3 communities and at least 5 documents is met, or the query abstains with the measured figure.
- Every reduced claim traces to at least 1 underlying assertion, not merely to a summary.

***

#### Step 5.3: Serialise the Evidence Packet and Resolve Every Citation

**Required Actions**:

- Serialise the evidence packet in deterministic order, preserving for every assertion its subject, predicate, object, direction, edge identifier, confidence, valid-time interval, status, and evidence key.
- Separate the packet into declared classes, asserted evidence, entailed evidence, algorithmic scores, and generated summaries, so the synthesis call cannot treat a summary as an assertion.
- Allocate the token ceiling to query-critical paths first, then alternative paths, then community context, truncating descriptions before dropping any provenance field or qualifier, and truncate at a path boundary rather than mid-path.
- Delimit the packet as untrusted evidence and strip or neutralise any instruction-like content in retrieved node labels, descriptions, or summaries, since graph text is as injectable as passage text.
- Resolve every material claim in the synthesised answer against the assertion-to-source-span map, marking as unsupported any claim resolving only to a summary, only to an algorithmic score, or to nothing, and either retrieve again, qualify the claim, or abstain.

**Required Outputs**:

- A token-bounded evidence packet with class separation and full per-assertion attributes.
- A synthesised answer whose material claims each carry at least 1 citation.
- A citation resolution report listing every unsupported claim with its failure reason.

**Quality Checkpoints**:

- Packet size stays at or below the mode token ceiling, and no truncation removed a provenance field, a qualifier, or a direction.
- Every material claim resolves to at least 1 admitted source span; a claim resolving only to a summary is marked unsupported.
- The answer states its mode and, in global mode, its community level, so a reader can judge the evidence standard it was produced under.

***

### Phase 6: Index Maintenance, Incremental Re-Indexing, and Drift

**Objective**: Keep the graph index fresh at bounded cost by invalidating precisely what a source change touched, and re-enter the break-even test when the cost profile or the query mix changes.

#### Step 6.1: Compute the Blast Radius of a Source Change

**Required Actions**:

- Detect source creates, updates, deletes, permission changes, and schema changes through an idempotency key, and map each to the chunks it touches through the immutable source manifest.
- Propagate the impact deterministically through the derivation index: chunks to mentions, mentions to entities, entities to assertions, assertions to embeddings and to the summaries whose input sets contain them, and summaries to their consuming parents at higher levels.
- Compute the changed-entity mass as the proportion of served entities affected, weighted by degree, since a change touching one hub invalidates more of the partition than a change touching a hundred leaves.
- Classify the change as local repair where changed-entity mass falls at or below 5 percent and no community membership changes, as partition repair where membership changes but changed-entity mass stays at or below 10 percent, and as full rebuild above 10 percent or on any schema or partition-configuration change.
- Record the projected re-indexing cost for the classified change before executing it, and escalate where it exceeds 25 percent of the original full-build cost, because a change that expensive is a rebuild wearing a repair's name.

**Required Outputs**:

- A blast-radius record listing every invalidated chunk, mention, entity, assertion, embedding, summary, cache entry, and evaluation case.
- A changed-entity mass figure computed on a degree-weighted basis.
- A change classification of local repair, partition repair, or full rebuild, with its projected cost.

**Quality Checkpoints**:

- Every invalidated artifact traces to the source change through the derivation index; an artifact invalidated without a traced dependency indicates a broken index and halts the update.
- The change classification follows the stated mass thresholds; a classification chosen to avoid a rebuild is a defect.
- Projected re-indexing cost is recorded before execution, and a projection above 25 percent of full-build cost escalates.

***

#### Step 6.2: Execute Bounded Incremental Re-Indexing

**Required Actions**:

- Apply every change in a staging index rather than in the served one, closing transaction intervals or writing tombstones instead of overwriting values in place.
- Re-extract only the affected chunks, re-resolve only the affected entities and their immediate neighbourhoods, and re-summarise only the communities whose membership hash or input assertion-set hash changed, together with their consuming parents.
- Cascade deletion and permission revocation to every artifact in the blast radius, including embeddings, cached summaries, and cached evidence packets, and prove absence with a deletion audit query rather than assuming the cascade completed.
- Run at most 2 automated repair passes over validation failures, stopping earlier where the build hash repeats or where the violation count does not decrease, and escalate rather than attempting a third.
- Promote the staging index to the serving alias only where the frozen evaluation set shows no regression above 2 percentage points on any slice and no regression on any citation or authorization gate, retaining the prior index as an immediate rollback target.

**Required Outputs**:

- A staged index version with its own manifest and a recorded parent version.
- A re-index cost record comparing actual against the Step 6.1 projection.
- A promotion or retention verdict with the evaluation figures that produced it.

**Quality Checkpoints**:

- At most 2 automated repair passes run per update; a third escalates to human review.
- The deletion audit query returns zero residual artifacts for every deleted or de-permissioned source.
- No index is promoted while a regression above 2 percentage points on any slice, or any citation or authorization gate failure, is outstanding.

***

#### Step 6.3: Monitor Drift and Re-Enter the Break-Even Test

**Required Actions**:

- Monitor the retrieval-side drift signals: route mix shift, misroute recovery rate, empty-traversal rate, seed resolution rate, evidence gain per round, community size distribution, partition stability across rebuilds, and summary faithfulness on a rolling sample.
- Monitor the cost signals: indexing cost per re-index interval, per-query cost by mode, and the realised query volume against the break-even volume declared in Step 1.3.
- Re-enter Phase 1 where the graph-requiring share of traffic falls below 15 percent for 2 consecutive measurement periods, where realised query volume falls below the break-even volume for 2 consecutive intervals, or where the target-slice advantage over the baseline falls below 5 percentage points.
- Retire the graph index and return traffic to the baseline where the re-entered break-even test fails, recording the measured figures rather than retaining the index on the argument that it was already built.
- Convert every adjudicated failure, misroute, and unsupported claim into a case in the frozen evaluation set, so the next release measures against the failures the last one produced.

**Required Outputs**:

- A drift dashboard covering route mix, misroute rate, traversal efficiency, partition stability, and summary faithfulness.
- A cost-versus-break-even record per re-index interval.
- A retention or retirement verdict with the measured figures that produced it.

**Quality Checkpoints**:

- Every drift signal has a declared threshold and a named action; a monitored signal without a threshold is a report rather than a control.
- The break-even test is re-entered on the stated triggers rather than on request.
- Retirement is executed on a failed break-even test; sunk indexing cost is never accepted as a reason to retain the index.

***

## III. Implementation Guidance for AI Agents

AI agents operating graph-based retrieval must follow systematic protocols ensuring that indexing cost is estimated before it is incurred, that every query executes in exactly one declared mode under a mode-specific budget, and that every material claim resolves to primary evidence rather than to a generated summary. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Cost Gate Agent**: Owns the pilot metering, the indexing cost estimate, the break-even calculation, and the abandonment rule. It alone may authorise construction, and it may refuse an adoption whose estimate exceeds budget regardless of expected quality gain.
2. **Index Builder Agent**: Owns the extraction contract binding, the served projections, the seed indexes, and the index manifest. It never serves an index whose rebuild hash does not match its original.
3. **Graph Verification Agent**: Owns the verification sample, the edge-validity and direction-accuracy computation, and the high-degree false-merge audit. It may return a graph to the construction discipline and may not be overridden by a schedule.
4. **Community Agent**: Owns the partition configuration, the stability measurement, the summarisation budget, and the invalidation dependency records. It halts summarisation on budget breach rather than completing the level.
5. **Router Agent**: Owns query classification, seed resolution, the routing rule, the mode budget allocation, and the misroute detection tests. It issues exactly 1 route per query and at most 1 recovery.
6. **Traversal Agent**: Owns frontier construction, filter application, bound enforcement, path selection, and the traversal record. It never expands a node the filters excluded and never raises its own bounds.
7. **Assembly Agent**: Owns evidence packet serialisation, class separation, token allocation, citation resolution, and the abstention path. It marks a claim unsupported irrespective of the synthesising model's stated confidence.
8. **Maintenance Agent**: Owns change detection, blast-radius computation, incremental re-indexing, promotion gating, and the drift dashboard. It may retire the index on a failed break-even test.

**Workflow Execution Pattern**:

```
STATE: Query_Route_Selection
INPUTS:
  1. Structured intent record from Step 4.1
  2. Ranked seed candidate set with match strategy and margin
  3. Route label with confidence, corpus-scope marker, required hop count
  4. Remaining query budget across tokens, calls, graph ops, wall clock
ACTIONS:
  1. Validate the route label against its precondition
  2. Reject and re-route a local label with zero resolved seeds
  3. Reject and re-route a global label with 1-5 seeds and hops <= 3
  4. Run the local probe first where classification confidence < 0.70
  5. Allocate the mode budget and project execution cost
VALIDATION:
  - route_label IN {no_graph, local, hybrid, global}
  - route_count == 1
  - projected_mode_cost <= remaining_budget
  - authorization_context_bound == TRUE
  - rule_clause_recorded == TRUE
TRANSITIONS:
  IF route == local THEN next_state = Bounded_Local_Traversal
  IF route == global THEN next_state = Community_Map_Reduce
  IF route == hybrid THEN next_state = Report_Prior_Then_Local
  IF route == no_graph THEN next_state = Passage_Retrieval_Route
  IF projected_mode_cost > remaining_budget THEN next_state = Declared_Abstention
  IF validation_failed THEN next_state = Routing_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended route, its mode budget, and its projected cost without executing it; confirm the projection against the validation block while no model call has been made; execute only after validation passes, recording the routing event in the same operation. This ordering matters most for global mode, whose cost is committed at the first map call and is not recoverable by a later demotion.

**Approval Gate**: Human authorisation is required before any full index build whose estimate exceeds the approved budget, before promoting an index whose verification sample shows edge validity below 0.90, before any re-index classified as a full rebuild, before any change to the authorization scope of a community summary, and before retiring a graph index that a regulated workflow depends on. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the index manifest, the cost ledger, the route mix, and the break-even figures in durable state, since the index outlives any single context window.
- Stream traversal results into the evidence packet under the token ceiling rather than holding a full neighbourhood in working context.
- Summarise superseded traversal rounds into their evidence references once the round's contribution is recorded, retaining the references and discarding the raw frontier.
- Count the router's and the map stage's own token consumption against the query budget rather than treating orchestration as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Adoption Justification (After Phase 1)**

- **Automated Check**: The route-labelled sample holds at least 300 entries; the graph-requiring share is at or above 15 percent; the indexing cost estimate derives from a metered pilot; the break-even volume and the abandonment rule are both recorded.
- **Agent Action on Pass**: Proceed to index construction.
- **Agent Action on Failure**: Halt the adoption and return the failing figure; no extraction runs against an unjustified estimate.
- **Human Review Trigger**: An indexing cost estimate above the approved budget, or a target slice below 15 percent of traffic that a stakeholder nonetheless requires.

**Checkpoint 2: Graph Admissibility (After Phase 2)**

- **Automated Check**: Edge validity at or above 0.90; direction accuracy at or above 0.95; qualifier retention at or above 0.90; overall false-merge rate at or below 0.02; high-degree false-merge rate at 0.00; projection rebuild hash matches.
- **Agent Action on Pass**: Proceed to community detection.
- **Agent Action on Failure**: Return the graph to the construction discipline with the failing metric and the sampled counter-examples.
- **Human Review Trigger**: Any false merge among the 20 highest-degree entities, or edge validity below 0.80.

**Checkpoint 3: Index Integrity (After Phase 3)**

- **Automated Check**: Partition reproducible from the manifest; pairwise stability at or above 0.80 across 5 seeds; no community above 20 percent of entities; summary faithfulness at or above 0.95 per level; summarisation cost at or below 1.5 times estimate; every summary carries an invalidation dependency record.
- **Agent Action on Pass**: Enable global mode for serving.
- **Agent Action on Failure**: Withhold global mode and serve local mode only; a failed summary hierarchy does not block entity-level retrieval.
- **Human Review Trigger**: Summarisation cost above 1.5 times the estimate, or faithfulness below 0.90 at any level.

**Checkpoint 4: Route Validity (After Phase 4)**

- **Automated Check**: Exactly 1 route per query; the rule clause recorded; no local route with zero resolved seeds; no global route with 1 to 5 seeds and a hop requirement at or below 3; projected cost within the remaining budget.
- **Agent Action on Pass**: Execute the selected mode.
- **Agent Action on Failure**: Re-classify once, then abstain; an invalid route is never executed with a warning attached.
- **Human Review Trigger**: Misroute recovery rate above 10 percent of queries in any class over a rolling window of 200 queries.

**Checkpoint 5: Evidence Sufficiency (After Phase 5)**

- **Automated Check**: All traversal bounds respected; no unauthorized edge in any returned path; global coverage at or above 3 communities and 5 documents; every material claim resolved to at least 1 admitted source span; no claim supported by a summary alone.
- **Agent Action on Pass**: Release the answer with its mode, its evidence references, and, in global mode, its community level.
- **Agent Action on Failure**: Qualify the unsupported claims, retrieve once more within budget, or abstain with the supported partial result.
- **Human Review Trigger**: Unsupported-claim rate above 5 percent over a rolling window of 200 answers.

**Checkpoint 6: Maintenance and Freshness (After Phase 6)**

- **Automated Check**: Every invalidated artifact traced through the derivation index; deletion audit returns zero residuals; at most 2 repair passes; no slice regression above 2 percentage points; realised query volume compared against break-even.
- **Agent Action on Pass**: Promote the index version and archive the prior manifest as the rollback target.
- **Agent Action on Failure**: Retain the prior index and mark affected answers stale rather than serving an unvalidated build.
- **Human Review Trigger**: Any residual artifact after a deletion cascade, or a second consecutive interval below break-even volume.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
INDEX_VERSION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Indexing Cost Overrun**

- **Symptoms**: Cumulative extraction or summarisation cost exceeds the Step 1.2 estimate before the build completes; community count at a retained level exceeds the projection; extraction retries rise on a source class absent from the pilot.
- **Diagnostic Steps**: Attribute the overrun to extraction or to summarisation separately, since only summarisation scales with community count; compare the realised community count per level against the projection; check whether the pilot sample missed a document class with higher entity density.
- **Resolution Protocol**: Option A, drop the lowest retained community level and re-estimate, since report count roughly multiplies at each level down. Option B, route extraction for low-density source classes to a cheaper model and reserve the stronger model for classes the verification sample shows it needs. Option C, defer summarisation entirely and serve local mode only until query volume justifies the summary hierarchy. Option D, abandon the adoption under the Step 1.3 rule and return traffic to the baseline.
- **Escalation Trigger**: Cumulative cost above 1.5 times the estimate halts the build and escalates; the build is never continued on the expectation that the remaining chunks are cheaper.

**Error Type 2: Extraction Quality Failure Discovered After Serving**

- **Symptoms**: Unsupported-claim rate rises without a routing change; users report entities conflated in answers; paths appear that contradict the source text; direction errors surface in adjudicated cases.
- **Diagnostic Steps**: Re-run the Step 2.2 verification sample on the served index; segment edge validity by relation type, source class, and extraction model version; recompute the high-degree false-merge audit, since one hub merge produces many wrong paths.
- **Resolution Protocol**: Option A, suppress the affected relation types from traversal while the graph is repaired, which degrades coverage rather than correctness. Option B, return the graph to the construction discipline under the entity-resolution and quality-control guides and roll back to the prior index version. Option C, raise the confidence threshold for the affected relation types and accept the reduced recall until re-extraction completes.
- **Escalation Trigger**: Any false merge among the 20 highest-degree entities halts serving of local mode for the affected neighbourhoods; this class is never resolved by adjusting traversal bounds, because the defect is in the graph rather than in the retrieval.

**Error Type 3: Persistent Mode Misrouting**

- **Symptoms**: Misroute recovery rate above 10 percent in a query class; global answers repeatedly demoted to local; local answers repeatedly promoted to global on corpus-scope questions; per-query cost rising with flat answer quality.
- **Diagnostic Steps**: Segment recovery rate by query class, by corpus-scope marker value, and by seed resolution count; determine whether the classifier is mislabelling or the seed index is failing to resolve entities the query names.
- **Resolution Protocol**: Option A, where seed resolution is the cause, extend the seed index with the missing aliases and identifiers rather than retraining the classifier. Option B, where the corpus-scope marker is the cause, extend its lexical trigger set from the adjudicated cases and re-measure. Option C, lower the local-probe confidence threshold below 0.70 so more queries take the cheap path first. Option D, route the affected class deterministically by template where its intent is stable enough to recognise without a model call.
- **Escalation Trigger**: Recovery rate above 20 percent in any class over 200 queries suspends automatic routing for that class and routes it to the declared default mode until recalibration completes.

**Error Type 4: Traversal Explosion or Coverage Collapse**

- **Symptoms**: Node and edge budgets exhaust before intent constraints are covered; frontier size grows superlinearly per hop; or the opposite, expansion terminates at round 1 with zero evidence gain and unsatisfied constraints.
- **Diagnostic Steps**: Inspect the degree of the entities entering the frontier against the hub register; check whether filters removed the answer-bearing edges by testing a filter-free expansion in a sandbox; confirm the seed set resolved to the entities the query named.
- **Resolution Protocol**: Option A, on explosion, tighten fan-out and require hubs to satisfy a relation-type constraint before entering the frontier. Option B, on collapse, widen the relation-type allowlist by one type at a time and re-measure, never by removing the authorization or valid-time filters. Option C, run one constrained path search between the required terminals rather than one more undirected hop. Option D, fall back to the no-graph route and answer from passages, recording the graph coverage gap as an evaluation case.
- **Escalation Trigger**: Three consecutive rounds with zero evidence gain terminates traversal; a coverage gap recurring in more than 10 percent of a query class escalates to index review rather than to further bound tuning.

**Error Type 5: Stale or Unreproducible Index State**

- **Symptoms**: A rebuild from the manifest produces a different edge-set hash; community membership shifts between builds with no source change; summaries reference assertions no longer served; deletion audit returns residual artifacts.
- **Diagnostic Steps**: Compare the manifest's pinned versions against the versions actually used; verify the partition seed and resolution parameter were recorded and applied; walk the derivation index for the residual artifacts to find the missing dependency edge.
- **Resolution Protocol**: Option A, restore the prior index version from the rollback target and re-run the update with corrected pinning. Option B, where the derivation index is incomplete, rebuild it from the source manifest before any further incremental update, since precise invalidation is impossible without it. Option C, promote a full rebuild where the divergence cannot be attributed, accepting the cost rather than serving an index whose provenance is unknown.
- **Escalation Trigger**: Any residual artifact surviving a deletion cascade halts serving for the affected scope; this class is never resolved by retrying the cascade.

**Error Type 6: Summary-Only Support and Injection Through Graph Text**

- **Symptoms**: Material claims resolve only to community summaries; answers assert corpus-wide findings with no assertion-level citation; retrieved node labels or summary text contains instruction-like content; behaviour changes after a specific document enters the corpus.
- **Diagnostic Steps**: Segment unsupported claims by whether their nearest resolution was a summary, a score, or nothing; scan the evidence packets of affected queries for instruction-like content in labels, descriptions, and summaries; trace the offending text to its source document and version.
- **Resolution Protocol**: Option A, tighten the synthesis constraint so summaries may supply framing but never support a material claim, and re-run the affected queries. Option B, quarantine the source document and invalidate every derived artifact in its blast radius. Option C, neutralise instruction-like content at serialisation and add the pattern to the injection test set. Option D, abstain on the affected query class until the quarantine completes.
- **Escalation Trigger**: Any confirmed instruction-following from retrieved graph text halts serving and escalates to security review; this class is never resolved by a prompt adjustment alone.

**Troubleshooting Decision Tree**:

```
GRAPH RETRIEVAL PRODUCES A DEFECT
├─ COST DEFECT
│   ├─ Build cost above 1.5x estimate → HALT build; drop lowest level or defer summaries
│   ├─ Query volume below break-even for 2 intervals → Re-enter Phase 1; retire on failure
│   └─ Re-index projected above 25% of full build → Reclassify as rebuild; escalate
├─ GRAPH DEFECT
│   ├─ Edge validity below 0.90 → Return graph to construction; roll back index
│   ├─ False merge on a high-degree entity → HALT local mode for that neighbourhood
│   └─ Qualifier dropped in extraction → Suppress relation type; re-extract
├─ ROUTING DEFECT
│   ├─ Local route with zero resolved seeds → Reject label; re-route by scope marker
│   ├─ Global route with 1-5 seeds and hops <= 3 → Reject label; route local
│   └─ Recovery rate above 20% in a class → Suspend auto-routing; use default mode
├─ TRAVERSAL DEFECT
│   ├─ Frontier growth superlinear → Tighten fan-out; constrain hub entry
│   ├─ Zero evidence gain for 3 rounds → Terminate; emit supported partial result
│   └─ Required terminals disconnected → One constrained path search, then abstain
├─ EVIDENCE DEFECT
│   ├─ Claim resolves to summary only → Mark unsupported; qualify or abstain
│   ├─ Global coverage below 3 communities → Abstain with the coverage figure
│   └─ Instruction-like content in graph text → HALT; quarantine source; security review
└─ INDEX DEFECT
    ├─ Rebuild hash mismatch → Block serving; re-pin manifest versions
    ├─ Partition unstable across seeds → Raise resolution; re-detect before summarising
    └─ Residual artifact after deletion → HALT scope; rebuild derivation index
```

### D. Performance Metrics and Continuous Learning

**Index Quality Metrics**:

- **Edge validity**: Served assertions whose cited span supports subject, object, predicate, and direction (target: at least 0.90; below 0.80 blocks serving).
- **Direction accuracy**: Served assertions whose direction matches the source (target: at least 0.95).
- **High-degree false-merge count**: False merges among the 20 highest-degree entities (target: 0; any occurrence halts local mode for the affected neighbourhoods).
- **Partition stability**: Entity pairs co-assigned across 5 detection seeds (target: at least 0.80).
- **Summary faithfulness**: Summary claims traceable to an input assertion (target: at least 0.95 per level).

**Retrieval and Routing Metrics**:

- **Route accuracy**: Queries whose executed mode matches the adjudicated required mode (target: at least 0.85 per class).
- **Misroute recovery rate**: Queries requiring a mode recovery (target: at most 0.10; above 0.20 in a class suspends automatic routing there).
- **Seed resolution rate**: Local-route queries resolving at least 1 seed entity above threshold (target: at least 0.90).
- **Traversal efficiency**: Newly covered intent constraints per 100 edges touched (target: monitored per class, with a declared floor set from the first 200 adjudicated queries).
- **Global coverage**: Distinct communities and documents contributing to a global answer (target: at least 3 and 5 respectively; below either, the query abstains).
- **Citation precision**: Material claims resolving to an admitted source span (target: at least 0.95).
- **Unsupported-claim rate**: Material claims resolving to nothing or to a summary alone (target: at most 0.05).

**Cost and Freshness Metrics**:

- **Indexing cost per interval**: Metered extraction plus summarisation cost per re-index interval (target: at or below 1.5 times the Step 1.2 estimate).
- **Cost per query by mode**: Metered tokens, calls, and money separated by route (target: global mode cost recorded and compared against its measured quality gain each interval).
- **Break-even margin**: Realised query volume over break-even volume (target: above 1.0; below 1.0 for 2 consecutive intervals triggers retirement review).
- **Target-slice advantage**: Primary metric gain over the incumbent baseline on the target slice (target: at least 5 percentage points; below it, the index is retired).
- **Freshness lag**: Time from source change to served index reflecting it (target: within the declared re-index interval).
- **Deletion lag**: Time from deletion request to zero residual artifacts (target: within the declared policy window, with the audit query as evidence).

**Learning and Adaptation Mechanisms**:

- **Adjudicated case capture**: Every misroute, unsupported claim, coverage collapse, and false merge becomes a case in the frozen evaluation set, so the next release measures against the failures the last one produced.
- **Threshold recalibration**: Recompute seeding confidence, classification confidence, fan-out caps, and evidence-gain floors per corpus and per query class; the values in this guide are deployment defaults rather than measured constants.
- **Relation-type pruning**: Retire any relation type that no query in the rolling route sample requires, since every retained type carries extraction, traversal, and evaluation cost.
- **Level pruning**: Retire any community level whose reports serve no answered global query over a full re-index interval, since level count is the dominant summarisation cost multiplier.

**Human-in-the-Loop Boundaries**: Approving an index build above the estimated budget, overriding a graph verification return verdict, widening a community summary's authorization scope, promoting an index with an outstanding regression, and retiring a graph index that a regulated workflow depends on are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the relationship between a query's evidence requirement and the graph structure that can satisfy it, rather than the content of any particular graph. Its phases hold wherever a corpus carries relations that span documents, a query mix contains both entity-specific and corpus-wide questions, and indexing cost is a real constraint.

### 4.1 Cross-Domain Application Patterns

**Regulatory and compliance analysis**: The route mix is dominated by local queries naming a control, a clause, or an obligation, with a minority of global queries asking which themes recur across a corpus of findings. Extraction quality is the binding constraint, because a conflated obligation produces a path that appears to connect a requirement to an unrelated control. The evidence standard tightens: a material claim resolves to the clause text, never to a community summary, and abstention is preferred over a synthesised paraphrase. Global mode is often retired after the first interval, because the corpus-wide question count rarely reaches break-even against summarisation cost.

**Scientific literature synthesis**: Both modes carry real traffic. Local queries ask how two named mechanisms, compounds, or measures relate; global queries ask which approaches dominate a field, which is exactly the query class community summaries serve. Extraction quality suffers on nomenclature variance, so the seed index must carry synonym sets and the false-split rate matters as much as the false-merge rate. Re-indexing runs on a publication cadence rather than continuously, which makes the re-index interval long and the break-even calculation favourable.

**Enterprise incident and operations analysis**: Local queries dominate, asking which services, changes, and owners connect to an incident. Freshness is the binding constraint rather than cost, because an index reflecting yesterday's topology answers today's question wrongly. Blast-radius computation runs continuously, and the change classification thresholds tighten so that partition repair is preferred over batching changes into a rebuild. Global mode is admitted only for retrospective review, where latency is not a constraint.

**Investigative and due-diligence work**: Path validity is the product rather than a control. Users need the connecting path itself, so the constrained path search in Step 5.1 is a primary operation rather than a fallback, and the evidence packet's direction, valid-time, and provenance fields are the answer's substance. False merges are the dominant risk, because a merged entity manufactures a connection that does not exist, and the high-degree audit threshold of zero is a hard requirement rather than a default.

**Product and customer feedback analysis**: Global queries dominate, asking which concerns recur and how they cluster, which is the query class this architecture serves best and the one most vulnerable to over-claiming. The coverage standard binds hardest here: a theme drawn from three reports out of hundreds is not a corpus-wide finding, and the answer must state its community level so a reader can judge the granularity. Extraction is cheap on short documents, so the summarisation cost dominates and level pruning is the main cost control.

### 4.2 Scale, Risk, and Cost Adaptation

- **Small corpora below the tested long-context threshold**: The break-even test almost always fails. Serve the no-graph route with passage retrieval or long-context routing, and record the corpus size that would change the verdict rather than building an index that cannot amortise.
- **Large, slowly changing corpora**: The most favourable case. Long re-index intervals amortise indexing cost across many queries, partition stability is achievable, and community summaries stay valid long enough to earn their generation cost. Retain all phases as specified.
- **Large, rapidly changing corpora**: The least favourable case for global mode. Community summaries invalidate faster than they amortise, because a change to one entity's assertions invalidates every summary above it in the hierarchy. Serve local mode only, defer summarisation until the change rate falls, and record the freshness figure that would permit global mode.
- **High-risk and regulated work**: Tighten every evidence threshold: require assertion-level citation for 100 percent of material claims, forbid summary-supported claims entirely rather than marking them unsupported, bind the approval gate before any index promotion, and treat abstention as the preferred outcome where the evidence standard is not met.
- **Strict latency budgets**: Global mode's map stage is the dominant latency term and does not shorten without reducing report count. Reduce the retained level count rather than truncating the map stage, since a truncated map produces a coverage figure that no longer means what it claims. Where latency forbids any map stage, disable global mode and route corpus-wide questions to a declared fallback.
- **Multi-tenant deployments**: Generate policy-homogeneous community summaries per scope rather than one summary set filtered at read time, since a summary computed across scopes cannot be safely redacted after the fact. Accept the duplicated summarisation cost as the price of the isolation, and count it in the Step 1.2 estimate.

***

## V. Limitations and Considerations

**Indexing cost is real and scales with corpus size**: Extraction runs at least one model call per chunk and summarisation runs at least one per community per retained level, so total indexing cost grows with the corpus in a way passage indexing does not. On a corpus that never receives enough queries, or that changes faster than it amortises, the correct architecture is passage retrieval. The mitigation is the metered pilot in Step 1.2, the break-even condition in Step 1.3, and the re-entry triggers in Step 6.3, which together make retirement a measurement rather than an admission of failure.

**Graph retrieval is not uniformly better than vector retrieval**: Published comparisons and the sibling selection ladder both place graph-backed retrieval as a rung entered against a measured gap, not as an upgrade. On single-passage lookups and exact identifier searches the graph adds cost and latency without adding evidence, and a system routing all traffic through it performs worse than the baseline it replaced. The mitigation is the four-route classification in Phase 4, which keeps the no-graph route as a first-class outcome, and the 15 percent traffic floor in Step 1.1.

**Extraction quality bounds every downstream control**: A false merge, a reversed direction, or a dropped qualifier produces evidence that traversal will find and synthesis will cite, and no traversal bound or reranking pass repairs it. The mitigation is the verification gate in Step 2.2 with its stated thresholds, the zero-tolerance high-degree false-merge audit, and the return path to the construction discipline rather than a workaround in the retrieval layer.

**Community detection is an algorithmic artifact, not a taxonomy**: A community is the output of a partitioning algorithm under a chosen resolution parameter and random seed. It is not an ontology class, not a real-world group, and not stable under configuration change. The mitigation is the pinned configuration and the 0.80 stability floor in Step 3.1, together with the rule that no material claim is supported by community membership alone.

**Global answers inherit their summaries' defects**: A reduced global answer is a summary of summaries, and every unsupported claim in a source report can propagate into it while remaining invisible to answer-level correctness scoring. The mitigation is the 0.95 faithfulness gate in Step 3.3, the coverage standard in Step 5.2, and the citation rule that marks a claim unsupported where it resolves only to a summary.

**Incremental re-indexing is bounded but not cheap**: Because summaries are built hierarchically, a correction to one entity's assertions invalidates every summary above it, so a small source change can require summarisation work far out of proportion to its size. The mitigation is the degree-weighted blast-radius computation in Step 6.1, the change classification thresholds that route large-mass changes to an honest rebuild, and the 25 percent projection trigger that escalates a repair pretending to be cheap.

**Thresholds here are deployment defaults, not measured constants**: The 15 percent traffic floor, the 5 percentage point admission threshold, the 0.90 edge validity gate, the 0.80 stability floor, the 0.95 faithfulness gate, the 0.70 classification confidence threshold, the 3-hop and 25-fan-out traversal bounds, the 3-community and 5-document coverage standard, and the 5 and 10 percent change-mass thresholds were chosen to be operable on first deployment. None derives from a universal property of graphs or corpora. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute them per corpus and per query class against observed outcomes.

**Trained graph retrievers sit outside this method**: Retrieval approaches that train a graph neural network over the served graph can outperform traversal on stable, well-labelled graphs, but they require model training rather than runtime invocation, and they add retraining cost, out-of-distribution exposure, and calibration burden. The mitigation is to treat them as a separate adoption decision with its own break-even test, entered only after bounded traversal has failed a named slice, and to keep the traversal path available as the fallback.

**Graph text is an injection surface**: Node labels, entity descriptions, and generated community summaries all carry text drawn from sources, and a summary can launder injected instructions into an artifact that looks system-generated. The mitigation is the untrusted-evidence delimitation and neutralisation in Step 5.3, the quarantine and blast-radius invalidation path in Error Type 6, and the rule that a confirmed instruction-following event halts serving rather than triggering a prompt adjustment.

**Structural conformance is not evidential soundness**: A query can satisfy every checkpoint here, route correctly, traverse within bounds, and resolve every citation, while answering a question the graph was never built to answer. The framework detects malformed retrieval, not a misconceived information need, and no checkpoint substitutes for reviewing whether the target slice is the right slice.

***

## VI. Conclusion and Summary

Graph-based retrieval is an economic decision before it is a retrieval technique. Its distinguishing property is not that a graph represents relations, but that building the index costs many model calls up front and that this cost scales with the corpus while passage indexing does not. A team that treats the graph as strictly better than vector retrieval will build an index that most of its traffic does not need, pay for a summary hierarchy that its query volume never amortises, and discover the arithmetic only after the budget is spent. A team that estimates the cost from a metered pilot, states a break-even condition, and holds a route that bypasses the graph entirely will spend graph money only where graph structure is what the question requires.

The method's second organising idea is that global and local are genuinely different retrieval systems sharing one index. They read different artifacts, cost different amounts by more than an order of magnitude, meet different evidence standards, and fail in opposite directions. Routing is therefore a control decision that software must own and audit, not a hint a model supplies. A misroute toward local mode is cheap and recoverable; a misroute toward global mode commits its cost at the first map call and cannot be undone, which is why the cheap probe runs first whenever the classification is uncertain.

A team introducing this architecture should establish the passage baseline first, profile the real route mix from real queries, and meter a pilot before extracting anything at scale. It should then serve local mode alone, verify the graph against the Step 2.2 thresholds, and add the summary hierarchy only after global queries appear in enough volume to justify their generation cost. Every threshold in this guide is a starting value to be recalibrated against observed outcomes, and every artifact it produces is disposable if the break-even test later fails.

**Key Success Factors**:

- **Cost estimated before it is incurred**: A metered pilot, an extrapolated total with an upper bound, a recurring re-index figure, and a break-even volume all exist before the first production extraction call runs.
- **Construction quality verified before retrieval consumes it**: Edge validity, direction accuracy, qualifier retention, and the zero-tolerance high-degree false-merge audit gate the graph's entry into the index, because no retrieval control repairs a defective assertion.
- **Exactly one route per query, chosen by rule**: Software enforces the routing rule, records the clause that produced the decision, rejects labels whose preconditions fail, and permits at most one recovery, so routing quality is measurable rather than assumed.
- **Every material claim on primary evidence**: Community summaries supply framing and never support a material claim; citation resolution is a deterministic lookup whose verdict outranks the synthesising model's confidence.
- **Bounded traversal with declared stops**: Hop, round, fan-out, node, edge, token, and latency ceilings are set before expansion, hubs enter the frontier only under a relation constraint, and every traversal terminates on a recorded condition.
- **Retirement as a measurement**: The abandonment rule is written before construction, the break-even test is re-entered on stated triggers, and a built index is retired when it stops earning its cost rather than retained because it exists.

By following this guide, AI agents can determine whether a graph index is warranted at all, build only the retrieval artifacts their query mix uses, route each question to the mode its evidence requirement demands, and answer from assertions a reviewer can trace to source rather than from summaries that no longer resolve.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them; except where an entry is explicitly marked as verified during conversion, they were not independently re-verified, and their titles and locations are reproduced rather than checked. Entries marked verified were retrieved during the research conducted for this conversion.

**Corpus pointers**:

- `GraphRAG: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the adoption criteria and the conditions under which passage retrieval wins, the construction pipeline stages, the extraction, resolution, traversal, query-repair, update, and release loops with their iteration bounds, the global, local, drift, and cost-reduced query mode descriptions, the retrieval strategy inventory, the evidence serialisation rules, the authorization and multi-tenancy controls, the graph-quality, retrieval, answer, robustness, and cost metric families, and the tracing field inventory. It carries inline citations to primary literature and vendor documentation on graph retrieval, community detection, benchmarking, query generation, ontology standards, and graph platforms; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — the parent selection guide. Source of the selection ladder that places graph-backed retrieval at rung 12, the failure taxonomy, the frozen evaluation set discipline, and the material-claim and citation-resolution vocabulary this guide adopts.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — companion guidance on multi-round retrieval control, evidence-gain budgets, repetition prohibition, and the abstention path, applicable to the traversal loop in Step 5.1 and the hybrid mode in Phase 4.
- `advanced_task_guides/knowledge-retrieval/guide_ModularRAG.md` — companion guidance on module contracts and routing architecture, applicable to the four-route router in Phase 4.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — companion guidance on query interpretation and rewriting, applicable to the intent record in Step 4.1.
- `advanced_task_guides/knowledge-retrieval/guide_HierarchicalIndexRetrieval.md` — companion guidance on multi-level index structures and bounded expansion, applicable to the community level hierarchy in Phase 3.
- `advanced_task_guides/knowledge-retrieval/guide_CorrectiveRAG.md` — companion guidance on retrieval verdicts and correction actions, applicable to the misroute recovery in Step 4.3.
- `advanced_task_guides/knowledge-retrieval/guide_SelfRAG.md` — companion guidance on adjudicated support verdicts, applicable to the citation resolution gate in Step 5.3.
- `advanced_task_guides/knowledge-graphs/guide_KG_SchemaDesign.md` — the construction-side authority on schema and ontology design. Referenced from Section 1.2 and Step 2.1; this guide does not restate its method.
- `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md` — the construction-side authority on entity resolution and deduplication. Referenced from Step 2.2, which consumes its false-merge and false-split figures rather than recomputing them from first principles.
- `advanced_task_guides/knowledge-graphs/guide_KG_QualityControl.md` — the construction-side authority on constraint validation and consistency checking, supplying the quality report that Step 2.2 gates against.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — the construction-side authority on fact-level provenance and lineage, supplying the derivation index that Step 6.1 walks.
- `advanced_task_guides/knowledge-graphs/guide_KG_identifierFairPrinciples.md` — the construction-side authority on identifier policy, applicable to the canonical identifiers the seed index resolves against.
- `advanced_task_guides/knowledge-graphs/guide_KG_ScalabilityArch.md` — the construction-side authority on graph storage and scaling, applicable to the served projections in Step 2.3.
- `advanced_task_guides/knowledge-graphs/guide_KG_HumanAIcolab.md` — the construction-side authority on human and agent collaboration over a graph, applicable to the review paths named in the approval gate.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the traversal and query records in Phases 5 and 6.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops and value-of-computation gating, applicable to the mode budget and stopping rules.

**External references**:

*Graph retrieval architecture and query modes*

1. Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Metropolitansky, Ness, and Larson, *From Local to Global: A Graph RAG Approach to Query-Focused Summarization* — https://arxiv.org/abs/2404.16130
2. Microsoft GraphRAG, *Overview* — https://microsoft.github.io/graphrag/index/overview/
3. Microsoft GraphRAG, *Dataflow* — https://microsoft.github.io/graphrag/index/default_dataflow/
4. Microsoft GraphRAG, *Global Search* — https://microsoft.github.io/graphrag/query/global_search/
5. Microsoft GraphRAG, *Local Search* — https://microsoft.github.io/graphrag/query/local_search/
6. Microsoft GraphRAG, *DRIFT Search* — https://microsoft.github.io/graphrag/query/drift_search/
7. Traag, Waltman, and van Eck, *From Louvain to Leiden: guaranteeing well-connected communities* — https://arxiv.org/abs/1810.08473

*Indexing cost and cost-reduced variants*

8. Microsoft Research, *LazyGraphRAG: Setting a new standard for quality and cost* — https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/
9. Microsoft Research, *GraphRAG: Improving global search via dynamic community selection* — https://www.microsoft.com/en-us/research/blog/graphrag-improving-global-search-via-dynamic-community-selection/ (verified during conversion)
10. *Cost-Aware Query Routing in RAG: Empirical Analysis of Retrieval Depth Tradeoffs* — https://arxiv.org/abs/2606.02581 (verified during conversion)

*Retrieval strategies over graphs*

11. Gutiérrez et al., *HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models* — https://arxiv.org/abs/2405.14831
12. Mavromatis and Karypis, *GNN-RAG: Graph Neural Retrieval for Efficient Large Language Model Reasoning on Knowledge Graphs* — https://aclanthology.org/2025.findings-acl.856/
13. Luo et al., *Graph-R1: Towards Agentic GraphRAG Framework via End-to-end Reinforcement Learning* — https://arxiv.org/abs/2507.21892

*Benchmarking and comparison against passage retrieval*

14. Xiao et al., *GraphRAG-Bench: Challenging Domain-Specific Reasoning for Evaluating Graph Retrieval-Augmented Generation* — https://arxiv.org/abs/2506.02404
15. GraphRAG-Bench, *When to use Graphs in RAG: A Comprehensive Analysis for Graph Retrieval-Augmented Generation*, official benchmark repository — https://github.com/GraphRAG-Bench/GraphRAG-Benchmark (verified during conversion)
16. Fan, Xue, Liu, and Tan, *Do We Still Need GraphRAG? Benchmarking RAG and GraphRAG for Agentic Search Systems* — https://arxiv.org/abs/2604.09666
17. *RAG vs. GraphRAG: A Systematic Evaluation and Key Insights* — https://arxiv.org/abs/2502.11371 (verified during conversion)
18. *In-depth Analysis of Graph-based RAG in a Unified Framework* — https://arxiv.org/abs/2503.04338 (verified during conversion)

*Generated graph queries and their failure modes*

19. Feng, Papicchio, and Rahman, *CypherBench: Towards Precise Retrieval over Full-scale Modern Knowledge Graphs in the LLM Era* — https://arxiv.org/abs/2412.18702
20. LlamaIndex, *Property Graph Index* — https://docs.llamaindex.ai/en/stable/module_guides/indexing/lpg_index_guide/

*Graph semantics, provenance, and validation standards*

21. Keet and Khan, *Discerning and Characterising Types of Competency Questions for Ontologies* — https://arxiv.org/abs/2412.13688
22. W3C, *Shapes Constraint Language (SHACL)* — https://www.w3.org/TR/shacl/
23. W3C, *OWL 2 Web Ontology Language Document Overview (Second Edition)* — https://www.w3.org/TR/owl2-overview/
24. W3C, *PROV-O: The PROV Ontology* — https://www.w3.org/TR/prov-o/
25. W3C, *RDF 1.2 Concepts and Abstract Data Model*, Candidate Recommendation — https://www.w3.org/TR/rdf12-concepts/
26. ISO, *ISO/IEC 21838-2:2021 Information technology — Top-level ontologies — Part 2: Basic Formal Ontology* — https://www.iso.org/standard/74572.html
27. BFO 2020 official artifact repository — https://github.com/BFO-ontology/BFO-2020

*Graph platforms, access control, and retrieval security*

28. Neo4j, *neo4j-graphrag-python documentation* — https://neo4j.com/docs/neo4j-graphrag-python/current/
29. Neo4j, *Fine-grained access control* — https://neo4j.com/docs/operations-manual/current/tutorial/access-control/
30. AWS, *Amazon Neptune now supports open-source GraphRAG toolkit* — https://aws.amazon.com/about-aws/whats-new/2025/01/amazon-neptune-open-source-graphrag-toolkit/
31. Kùzu, *Getting Started* — https://kuzudb.com/docusaurus/getting-started/
32. LangChain graph integrations — https://python.langchain.com/docs/integrations/graphs/
33. GraphDB, *SHACL validation — GraphDB 11.0 documentation* — https://graphdb.ontotext.com/documentation/11.0/shacl-validation.html
34. OWASP, *Retrieval-Augmented Generation (RAG) Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
