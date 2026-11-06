# Hierarchical Index Retrieval

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Hierarchical index retrieval constitutes the task family of building a multi-level index over a corpus, with summaries or clusters at upper levels and source passages at the leaves, then routing a query down the levels rather than scanning all passages flat. This guide provides AI agents with a structured protocol for selecting a depth, constructing levels under a summary fidelity standard, declaring a routing rule and fan-out at every level, executing a bounded descent, and verifying the result against a flat baseline on the same evaluation set. It treats routing error compounding as the method's defining failure: a branch wrongly discarded at an upper level cannot be recovered at a lower one, because the correct passages are no longer reachable, and flat retrieval has no equivalent failure. It specifies a numeric routing loss measurement separating evidence lost to routing from evidence lost to ranking, a beam and backtracking policy that mitigates premature commitment, an incremental maintenance path that repairs only the ancestry above a changed passage, and a re-index trigger with a stated bound. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that hierarchy is admitted on measured gain and retired when a flat index performs as well.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Hierarchical index**: A multi-level structure over one corpus in which leaf nodes carry source passages and internal nodes carry derived representations of their descendants. The structure exists to make routing cheaper than exhaustive scanning, not to make the corpus better organised.

**Level**: One horizontal stratum of the index, numbered from the leaves upward. Level 0 holds source passages. Every level above 0 holds derived nodes whose content is produced from the level below.

**Depth**: The number of levels between the leaves and the root, excluding vector-engine implementation layers. Depth is a decision justified by corpus size and measured routing accuracy, never a default inherited from a framework.

**Leaf**: A node holding an exact span of authorized source content, with recoverable offsets and a source version. Leaves alone are citable evidence.

**Internal node**: A node whose content is derived from its children, holding a summary, a cluster description, a centroid, a heading path, or an extractive digest. An internal node is a routing artifact and is never cited as evidence for a factual claim.

**Level routing**: The decision, taken at each level, of which child nodes to descend into and which to discard. Level routing is the mechanism that carries the method; every other component exists to make it accurate or to detect when it was not.

**Fan-out**: The declared maximum number of child branches retained at one level for continued descent. Fan-out is fixed before the query runs and is enforced deterministically.

**Beam**: The set of branches active at the current level, whose size never exceeds the declared fan-out. A beam wider than 1 is the primary mitigation against premature commitment to a single branch.

**Routing error compounding**: The property that a branch discarded at level N cannot be recovered at any level below N, because its descendants never enter the candidate set. The error is absorbing rather than correctable, which distinguishes hierarchical retrieval from flat retrieval, where every passage remains reachable until the final cut.

**Unreachable leaf**: An answer-bearing leaf whose every ancestor path was discarded before the leaf level was reached. Unreachable leaves are invisible to a reranker and to a generator, and they are the failure the flat-baseline comparison exists to count.

**Routing loss**: The difference between conditional leaf recall measured with the correct parent supplied and actual end-to-end leaf recall measured with real routing, expressed in percentage points. It isolates evidence lost to routing from evidence lost to ranking within a correctly routed branch.

**Flat baseline**: A single-level retrieval configuration over the same leaves, using lexical, dense, or fused retrieval, evaluated on the same cases under the same reranker, token ceiling, and authorization policy. It is a permanent control, not a one-time comparison discarded after adoption.

**Summary fidelity**: The property that an internal node's derived representation retains the terms required to route a query to the node's own children. A fluent summary that omits the discriminating detail makes its branch unroutable, and fluency is not evidence of fidelity.

**Child-discriminability**: The measured ability of a parent representation to be selected for queries answerable only from that parent's descendants, and not selected for queries answerable only from a sibling's descendants. It is the acceptance test for summary fidelity.

**Ancestry**: The ordered set of internal nodes on the path from one leaf to the root. A change to a leaf invalidates its ancestry and nothing else, which is what makes incremental repair bounded.

**Child content hash**: A digest computed over the ordered child identifiers, their content hashes, their relevant metadata, and the governing policy fingerprint. A mismatch between a node's stored hash and its recomputed hash defines staleness deterministically, without reference to timestamps.

**Re-index trigger**: The declared condition under which incremental ancestry repair is abandoned and the affected levels are rebuilt from scratch, stated as a cumulative-change threshold with a bound on how long repair may be deferred.

**Descent record**: The logged account of one routing decision, carrying the candidates considered, their scores, the branches retained, the branches pruned, and the reason for each prune. Routing loss cannot be diagnosed after the fact without it.

**Build amortisation**: The relationship between the model calls and compute spent constructing internal levels and the query volume over which that cost is recovered. Construction cost scales with corpus size; maintenance cost scales with change.

### 1.2 The Execution Tier Partition

Hierarchical retrieval fails most often at the boundary between what software must decide and what a model may decide. The partition below is binding on every phase of Section II, and every step names the tier that owns it.

**Deterministic tier**: Software, scripts, queries, schema validators, and index APIs own everything requiring exactness, reproducibility, auditability, or scale. This tier holds level construction bookkeeping, including node typing, stable identifier assignment, parent and child edge recording, lineage propagation, and cycle and orphan detection. It executes routing, meaning that it applies authorization and metadata filters before any scoring, computes every score and every threshold comparison, and applies the retention decision. It maintains the beam, enforcing that the number of retained branches never exceeds the declared fan-out. It performs ancestry invalidation by recomputing child content hashes and walking the reverse derivation index. It accounts for every budget dimension, covering depth, branches, candidates, tokens, model calls, latency, and money. It computes the flat-baseline recall comparison and every metric reported in Sections II and III. Results produced by this tier are reproducible from the index manifest and the query.

**Model tier**: LLM calls own work requiring open-vocabulary judgement that no deterministic rule covers. This tier writes the summary or description carried by an internal node, and it supplies the relevance judgement used to prefer one candidate branch over another when lexical and dense signals are insufficient to separate them. It never enforces authorization, never computes a score that a gate depends on, never extends a candidate set it was given, and never declares its own summary faithful.

**Hybrid tier**: Work where the model proposes and software verifies, or software retrieves and the model adjudicates. Summarisation is a model output that a deterministic fidelity gate accepts or rejects on entity, quantity, date, negation, and coverage preservation. Branch selection is a model preference expressed over a deterministically retrieved and authorized candidate set, whose membership the model may not extend and whose cardinality the model may not exceed.

**Authority on disagreement**: The deterministic tier holds authority in every conflict. A model branch preference never exceeds the declared fan-out; where a model nominates more branches than the fan-out permits, the deterministic tier truncates the nomination in rank order and records the truncation. Where a model judges a branch relevant that the authorization filter excluded, the branch stays excluded. Where a model asserts a summary is faithful but the child-discriminability check fails, the summary is rejected regardless of stated confidence.

**Logging obligation**: Every routing decision is logged with the alternatives it rejected and the reason for each rejection. A descent that records only the branch taken makes routing loss undiagnosable after the fact, because the discarded branch that held the answer leaves no trace.

**Tier Ownership by Artifact**:

| Artifact | Owning tier | Rejection rule enforced deterministically |
| :-- | :-- | :-- |
| Node typing, identifiers, and lineage | Deterministic | A node lacking a parent edge, a level, or a source version is quarantined |
| Authorization and metadata filtering | Deterministic | Any candidate lacking a resolved policy decision is dropped before scoring |
| Internal node summary text | Model | Not applicable |
| Summary fidelity verdict | Deterministic | A summary failing child-discriminability is rejected and the node falls back to an extractive representation |
| Candidate scoring and threshold comparison | Deterministic | A score composition without a declared normalisation is rejected |
| Branch preference among candidates | Hybrid | A preference naming a candidate absent from the retrieved set is discarded |
| Beam maintenance and fan-out enforcement | Deterministic | A retained set larger than the declared fan-out is truncated in rank order |
| Backtracking and dead-end detection | Deterministic | A backtrack beyond the declared bound terminates the descent |
| Ancestry invalidation and repair scheduling | Deterministic | A node whose recomputed child content hash differs from its stored hash is marked stale |
| Flat-baseline recall comparison | Deterministic | A comparison run under unequal token or reranker budgets is void |
| Routing loss attribution | Deterministic | An attribution computed without oracle-parent labels is rejected |

### 1.3 Depth Selection and the Condition for a Flat Index

Depth is not a free parameter and hierarchy is not universally superior. Each added level introduces one more opportunity for routing error compounding, one more set of derived artifacts to keep fresh, and one more model call per node at build time. A level is admitted only where it pays for those costs in measured terms.

**The admission rule for one level**: A candidate level is admitted only where all three conditions hold on the frozen evaluation set. Routing accuracy at that level, meaning the proportion of cases in which at least one correct branch is retained, is at least 0.90. The level reduces the candidate population entering the next stage by at least 60 percent. End-to-end leaf recall does not fall by more than 2 percentage points against the configuration without that level. A level failing any condition is removed, and a level that improves no measured quantity is a defect rather than a neutral addition.

**The depth ceiling**: Maximum semantic depth is 5 levels, excluding vector-engine implementation layers. Beyond 5 levels the compounded routing accuracy of a chain of independent decisions falls below usable rates even at high per-level accuracy, since per-level accuracy multiplies along the path.

**Corpus-scale starting points**: The table below states the depth to attempt first, before measurement adjusts it. These are deployment defaults, recorded as such in Section V, and each must be confirmed by the admission rule rather than assumed.

**Depth Selection by Corpus Scale and Structure**:

| Leaf passage count | Source structure available | Starting depth | First structure to try |
| :-- | :-- | :-- | :-- |
| Below 10,000 | Any | 0, meaning a flat index | Flat fused retrieval with a reranker |
| 10,000 to 100,000 | Headings or sections present | 2 | Document or section level over leaves |
| 10,000 to 100,000 | Absent | 2 | Clustered level over leaves |
| 100,000 to 10,000,000 | Headings or sections present | 3 | Document over section over leaves |
| 100,000 to 10,000,000 | Absent | 3 | Two clustered levels over leaves |
| Above 10,000,000 | Any | 4 | Collection over document over section over leaves |

**When a flat index is the correct choice**: Agents must select a flat index, and must reject hierarchy, where any of the following holds. The authorized corpus fits reliably within the tested context occupancy of the generator, so no retrieval narrowing is required. Flat fused retrieval already meets the contract's leaf recall on every slice, leaving no failure for hierarchy to fix. The dominant query class is exact identifiers, rare terms, or quotations, which lexical retrieval resolves without narrowing. The corpus changes faster than internal levels can be repaired within the freshness objective, measured as a change rate exceeding the repair throughput. Query volume is too low for build cost to amortise within the declared amortisation window. No source structure exists and clustering produces membership stability below 0.70 across random seeds, so the routing target itself is unstable. One wrong branch would be unacceptable and the latency budget cannot fund a fan-out above 1. In each case the correct action is to retain the flat index and record the rejection with its measured evidence, not to build a shallow hierarchy as a compromise.

### 1.4 The Routing Failure Taxonomy and Structural Boundaries

Every failed evaluation case is attributed to exactly one class. Attribution is deterministic, computed from the labelled answer-bearing spans, the descent records, the admitted set, and the resolved citations. Classes are ordered so that the first matching condition wins.

**Class R1, routing miss**: The answer-bearing leaf exists in the authorized corpus, and no ancestor of that leaf survived to the leaf level. The evidence was unreachable, and no reranker, no larger candidate pool, and no better generator addresses it. Remedies are wider fan-out, a repaired parent representation, backtracking, or rejection of the hierarchy for that slice.

**Class R2, ranking miss**: A correct branch was retained and the answer-bearing leaf entered the candidate set, but fell below the admitted cut. The defect lies in leaf-level ranking, fusion, or cut depth, and it is the same defect a flat index would exhibit. Widening fan-out does not address it.

**Class R3, fidelity miss**: The correct branch was discarded because its parent representation omitted the term, entity, quantity, date, or negation that the query depended on, while sibling representations carried superficially similar language. R3 is a subclass of routing miss distinguished by its remedy, which is summary repair rather than beam widening, and it is detected by the child-discriminability check rather than by fan-out ablation.

**Class R4, staleness miss**: The correct branch was discarded, or a discarded branch was correct, because the parent representation described a state of its children that no longer holds. Remedies are ancestry repair and the staleness serving rule, never beam widening, which merely spreads the query across equally stale representations.

**Routing Failure Attribution and Remedy Map**:

| Class | Deterministic attribution test | Remedies that apply | Remedies that cannot help |
| :-- | :-- | :-- | :-- |
| R1 routing miss | No ancestor of the labelled leaf survives to leaf level, and the parent representation covers the query terms | Wider fan-out, backtracking, flat fallback, hierarchy rejection | Reranking, deeper leaf cut, better generator |
| R2 ranking miss | The labelled leaf enters the leaf candidate set and misses the admitted cut | Reranking, deeper leaf cut, fusion repair | Wider fan-out, added levels |
| R3 fidelity miss | Branch discarded and the parent representation lacks a query term present in its children | Summary regeneration, extractive fallback, term injection | Wider fan-out alone, deeper leaf cut |
| R4 staleness miss | Branch decision made against a node whose recomputed child content hash differs from its stored hash | Ancestry repair, staleness refusal, prior manifest rollback | Wider fan-out, reranking |

**Boundary against a graph community hierarchy**: A graph community hierarchy is built over an extracted entity and relation graph, where levels are communities produced by graph clustering over that graph's topology, and a community summary describes a set of entities and their relations. A document index hierarchy is built over the corpus itself, where levels are containment or similarity groupings of passages, and an internal node describes a set of passages. The two answer different questions and are governed by different guides. Corpus-wide synthesis over entity relations, multi-hop relational questions, and community-level thematic queries belong to the graph guide named in Section VII. Narrowing a passage corpus so that a query scans a fraction of its passages belongs here. Where both structures exist in one deployment, exactly one of them owns any given derived summary, and the invalidation path for that summary belongs to its owner; duplicating community reports and document summaries over the same content without a single ownership and invalidation path produces two structures that drift apart silently.

**Boundary against approximate nearest-neighbour graph layers**: A vector engine that traverses nested proximity-graph layers, or that probes a subset of inverted-file cells, implements a search acceleration structure whose layers are algorithmic, not semantic. Its upper-layer nodes are not summaries, documents, topics, or broader concepts, and its edges are not content relations. Agents must not present an engine's internal layering as a hierarchical retrieval architecture, must not expose layer numbers as semantic levels, and must not infer a parent-child meaning from a proximity edge. Such structures enter this guide only as declared configuration on the deterministic tier, measured by recall loss against exact search.

**Boundary against parent expansion**: Retrieving a small unit and supplying a larger enclosing unit is a context assembly device, not a routing hierarchy. It changes what is given to the generator after retrieval has already selected the leaf, and it carries no routing error compounding because no branch was discarded. Deployments frequently need it, and Phase 4 specifies it, but a system doing only this has a flat index with expansion, and it must be evaluated and described as such.

**Boundary against query transformation**: Rewriting, decomposing, or expanding a query changes what is asked. Level routing changes where it is asked. The two compose, and a decomposed sub-question may be routed independently, but a routing failure is never repaired by rewriting alone once the branch is gone.

***

## II. Operational Framework: Depth-Bounded Level Routing Verified Against a Flat Baseline

The framework assumes a corpus, an authorization policy, and a declared retrieval contract exist. Phases 1 through 4 run in sequence to produce a serving hierarchy. Phase 5 runs continuously against corpus change. Phase 6 gates every release and may return control to Phase 1 by retiring the hierarchy. No phase may be skipped on the grounds that a framework default supplies its answer.

### Phase 1: Corpus Analysis, Flat Baseline Establishment, and Depth Selection

**Objective**: Determine whether hierarchy is warranted and at what depth, by measuring a flat index first and admitting levels only against its named failures.

#### Step 1.1: Establish the Retrieval Contract and the Stage-Aware Evaluation Set

**Required Actions**:

- State the question classes the system must answer, the evidence standard for a material claim, the citation granularity, and the acceptable abstention, before any index is designed.
- Declare the latency, monetary, token, storage, and freshness budgets, each with a numeric limit and a stated consequence for breach.
- Label at least 200 evaluation cases, each carrying the query, the authorized principal, the answer-bearing leaf identifiers, and the exact spans within them.
- Label for every case the set of acceptable ancestors at every candidate level, so that routing can be scored independently of leaf ranking.
- Assign slice labels covering broad synthesis, exact detail, multi-document, cross-branch, temporal, long-document, stale-content, unauthorized, and unanswerable cases, with at least 20 cases per slice that the deployment will serve.
- Split the set into a tuning portion and a frozen held-out portion, and record the split so that no threshold, depth, summary prompt, or fan-out is ever tuned on the frozen portion.

**Required Outputs**:

- A retrieval contract record naming question classes, evidence standard, and abstention rule.
- A budget ledger with a numeric limit per bounded dimension.
- A versioned evaluation set with per-case leaf labels, per-level ancestor labels, and slice labels.
- A declared tuning and held-out split with its random seed recorded.

**Quality Checkpoints**:

- Every case carries at least one answer-bearing leaf identifier or an explicit unanswerable marker; cases with neither are removed before measurement.
- Every case that will be used to score routing carries acceptable-ancestor labels at every candidate level; cases lacking them can measure end-to-end recall but never routing loss.
- Every slice the deployment serves carries at least 20 cases; a slice below 20 is reported as unmeasured rather than as passing.
- The held-out portion is at least 30 percent of cases and has never been read by a tuning process.

***

#### Step 1.2: Measure the Flat Baseline and Attribute Its Failures

**Required Actions**:

- Build a flat index over the leaves alone, with no internal levels, using lexical retrieval, dense retrieval, and their fusion.
- Run the full evaluation set against the flat configuration under the reranker, token ceiling, and authorization policy the hierarchy will later use, so the comparison is not confounded by unequal budgets.
- Record leaf Recall@k, the admitted-set hit rate, end-to-end answer support, p95 latency, and cost per query for the flat configuration, globally and per slice.
- Attribute every flat failure to a retrieval miss, a ranking miss, or a downstream utilisation failure, and name the dominant class per slice.
- State the specific failure class hierarchy is expected to fix, and the slice on which it must be fixed, before any level is constructed.
- Preserve the flat configuration as a permanent control and as a runtime fallback path, not as a discarded experiment.

**Required Outputs**:

- A flat baseline measurement record with global and per-slice metrics.
- A failure attribution table naming the dominant failure class per slice.
- A hierarchy hypothesis naming the target slice, the target metric, and the minimum gain that would justify construction.
- A retained flat serving path registered as the fallback route.

**Quality Checkpoints**:

- The flat baseline includes a fused lexical and dense configuration; a dense-only baseline understates flat performance and inflates every later hierarchy gain.
- The declared hierarchy hypothesis names one target slice and one target metric; a hypothesis asserting general improvement is rejected as unfalsifiable.
- The minimum justifying gain is at least 5 percentage points on the target slice's primary metric.
- The flat path remains executable at serving time; a baseline that cannot be run again cannot function as a control.

***

#### Step 1.3: Select Depth and Declare the Build Cost Envelope

**Required Actions**:

- Count leaf passages and determine whether reliable source structure exists, then read the starting depth from the table in Section 1.3.
- Prefer source structure over invented groupings at every level where headings, sections, or containment are reliable, and fall back to clustering only where structure is absent or cuts across the questions asked.
- Estimate build cost before construction as one summarisation call per internal node, plus embedding cost per node, plus clustering compute, and state the total in model calls, tokens, and money.
- Compute the amortisation window as build cost divided by projected query volume, and reject the design where cost does not amortise within 90 days at projected volume.
- Declare the maximum depth, the branching factor range per level, and the minimum and maximum node counts per level before any node is built.
- Record the depth decision with the corpus measurement that produced it, so a later corpus change can re-trigger the decision rather than inherit it.

**Required Outputs**:

- A depth declaration naming the number of levels and the grouping basis at each.
- A build cost estimate in model calls, tokens, and money, with the amortisation window in days.
- A per-level structural envelope naming branching factor bounds and node count bounds.
- A recorded corpus measurement supporting the depth decision.

**Quality Checkpoints**:

- Declared depth does not exceed 5 semantic levels; a design requiring more is rejected and re-scoped.
- Build cost amortises within 90 days at projected query volume; a longer window halts construction pending a volume or scope revision.
- Every level's grouping basis is named as structural or clustered; a level whose basis is unstated cannot be maintained or evaluated.
- The depth decision cites a corpus measurement rather than a framework default.

***

### Phase 2: Level Construction and Summary Fidelity Gating

**Objective**: Build every internal level with complete lineage and admit no node representation that cannot route a query to its own children.

#### Step 2.1: Construct Typed Nodes, Edges, and Reverse Lineage

**Required Actions**:

- Assign every node a stable identifier derived from source identity and content, never from array position or insertion order, so that identifiers survive a rebuild.
- Type every node by its role, distinguishing source-bearing leaves from derived internal nodes, and refuse to store structure, derived text, and source content in one untyped field.
- Type every parent-child edge by its semantics, distinguishing containment in the source, summarisation over children, algorithmic clustering, and ordering, so that a later process knows which edges a content change invalidates.
- Record per node the level, parent identifiers, child identifiers, child count, source version, source offsets, content hash, child content hash, and authorization labels.
- Build the reverse derivation index mapping every leaf to its complete ancestry, its cluster memberships, its derived embeddings, and its cache keys, since incremental repair is impossible without it.
- Validate before release that every leaf is reachable from an authorized root, that no forbidden cycle exists, that no internal node has zero children, and that no node is orphaned.

**Required Outputs**:

- A typed node store carrying leaves and internal nodes with complete per-node metadata.
- A typed edge set recording the semantics of every parent-child relation.
- A reverse derivation index from every leaf to every artifact derived from it.
- A structural validation report covering reachability, cycles, orphans, and empty parents.

**Quality Checkpoints**:

- Every leaf is reachable from at least one authorized root; unreachable leaves are quarantined and counted, never dropped silently.
- Zero forbidden cycles and zero empty internal nodes exist at release; either condition halts publication of the build.
- Every internal node records the ordered child set and the child content hash from which its representation was derived.
- Node identifiers are reproducible across a rebuild from the same source snapshot.

***

#### Step 2.2: Construct Level Representations Under the Summary Construction Standard

**Required Actions**:

- Generate every internal node representation as query-independent, so that one representation serves all queries and no representation is tuned to the evaluation set.
- Preserve in the representation the discriminating detail its children carry, meaning named entities, identifiers, dates, quantities, units, negations, exceptions, qualifications, and the range of distinct topics present, since these are the terms a query will route on.
- Enumerate the topical extent of the children explicitly, including topics present in a minority of children, because a representation describing only the dominant topic makes minority children unroutable.
- State the representation's boundary, naming what its subtree does not contain, so that a routing decision can reject the branch as confidently as it can select it.
- Attach to every abstractive representation a deterministically computed term field holding the union of discriminative terms extracted from the children, since the abstractive text is lossy by construction and the term field is not.
- Bound representation length to a declared token ceiling per level, and record the summariser model version, prompt version, token counts, and ordered child hashes with every representation.
- Prefer an extractive or structural representation, built from headings, lead sentences, and metadata, wherever it passes the Step 2.3 gate, because it costs no model call and cannot hallucinate.

**Required Outputs**:

- One representation per internal node carrying abstractive text, the deterministic term field, and a stated boundary.
- A construction manifest recording summariser model, prompt version, token counts, and ordered child hashes per node.
- A per-level token ceiling declaration.
- A record of which nodes use extractive or structural representations rather than generated ones.

**Quality Checkpoints**:

- Every representation is query-independent; a representation generated against evaluation queries is discarded and regenerated.
- Every representation carries a deterministic term field; an abstractive summary standing alone is rejected because its omissions are undetectable at routing time.
- Every representation names what its subtree does not contain.
- Every representation records the ordered child hash from which it was derived, so staleness is computable without re-reading the children.

***

#### Step 2.3: Gate Every Representation on Child-Discriminability

**Required Actions**:

- Synthesise for every internal node a set of probe queries derived from its children's distinctive spans, generating at least 3 probes per child up to a bounded sample of 30 probes per node.
- Score every probe against the node's own representation and against its sibling representations, using the same retrieval configuration serving will use.
- Require self-routing recall of at least 0.95, meaning the node's own representation is retained for at least 95 percent of probes derived from its own children.
- Require sibling separation, meaning the node's representation outranks every sibling for at least 90 percent of probes derived from its own children; a node that cannot be told apart from its siblings supplies no routing signal.
- Measure routing-term coverage as the proportion of discriminative child terms present in the representation or its term field, and require at least 0.90.
- Regenerate a failing representation at most twice, using the specific missing terms as the repair instruction, then fall back to an extractive or structural representation rather than regenerating further.
- Quarantine any node still failing after the extractive fallback, mark its subtree as reachable only through the flat fallback path, and count it against the build's fidelity budget.

**Required Outputs**:

- A per-node fidelity record carrying self-routing recall, sibling separation, and routing-term coverage.
- A repair log naming each regeneration, its missing-term instruction, and its outcome.
- A quarantine list of nodes that failed the gate after fallback.
- A build-level fidelity summary reporting the proportion of nodes passing at first generation.

**Quality Checkpoints**:

- Self-routing recall is at least 0.95 and sibling separation at least 0.90 for every serving node; nodes below either bound are quarantined rather than served.
- Routing-term coverage is at least 0.90 for every serving node.
- No node undergoes more than 2 regenerations; a third attempt is prohibited because repeated generation against the same children produces correlated omissions.
- Quarantined nodes are at most 2 percent of internal nodes; above that the level's grouping basis is rejected and Phase 2 restarts with a different basis.

***

### Phase 3: Routing Policy Declaration and Fan-Out Binding

**Objective**: Fix the rule that selects branches at every level, together with the fan-out that bounds premature commitment, before any query is served.

#### Step 3.1: Declare the Routing Rule and Score Composition at Every Level

**Required Actions**:

- State for each level, as a written rule, what is being selected, which signals contribute, how they are combined, and what makes a branch eligible at all.
- Apply authorization and hard metadata filters before scoring at every level, so that an unauthorized branch never enters the candidate set and never influences a threshold.
- Compose the branch score from named components, covering lexical match against the term field, dense similarity against the representation, structural or metadata match, and an optional model relevance judgement, and declare the normalisation applied before combination.
- Score against both the abstractive representation and the deterministic term field, and record the components separately, because a branch selected only by the term field indicates the abstractive text failed and a branch selected only by dense similarity indicates a possible fidelity gap.
- Calibrate a level-specific retention threshold on the tuning split rather than reusing one global threshold, since score distributions differ by level and a shared threshold over-prunes the level with the tighter distribution.
- Forbid any level from selecting exactly 1 branch by default; a fan-out of 1 is permitted only where measured routing accuracy at that level is at least 0.98 on the tuning split.

**Per-Level Routing Policy Declaration**:

| Declared element | Required form | Deterministic rejection condition |
| :-- | :-- | :-- |
| Selection unit | Named node type retained at this level | A level whose selection unit is unstated is not served |
| Eligibility filter | Authorization and metadata predicates applied before scoring | Any candidate lacking a resolved policy decision |
| Score components | Named signals with declared normalisation | A composition mixing unnormalised score scales |
| Retention threshold | Level-specific numeric value fitted on the tuning split | A threshold fitted on the held-out split |
| Fan-out | Integer maximum branches retained | A retained set exceeding the integer |
| Tie policy | Deterministic ordering rule for equal scores | A nondeterministic tie break, which makes runs irreproducible |
| Model judgement role | Preference only, over the retrieved candidate set | A judgement naming a candidate outside the set |

**Required Outputs**:

- A per-level routing rule statement covering selection unit, eligibility, signals, and combination.
- A calibrated retention threshold per level with the tuning evidence that produced it.
- A score component schema recording each signal separately at query time.
- A declared tie-breaking rule producing reproducible ordering.

**Quality Checkpoints**:

- Authorization filtering precedes scoring at every level; a level scoring before filtering is a blocking defect and halts release.
- Every level carries its own calibrated threshold; a shared global threshold is rejected.
- Score components are recorded separately rather than only as a combined value.
- No level defaults to a fan-out of 1 without measured routing accuracy of at least 0.98.

***

#### Step 3.2: Declare Fan-Out, Pruning Bounds, and the Backtracking Rule

**Required Actions**:

- Declare a numeric fan-out per level, defaulting to 3 branches at every level above the leaves, and justify any narrower value with measured routing accuracy at that level.
- Compute the compounded reachability estimate as the product of per-level routing accuracies across the declared depth, and reject a configuration whose product falls below 0.90 on the tuning split.
- Widen fan-out rather than adding a level whenever compounded reachability is the binding constraint, since an added level multiplies another accuracy term into the product.
- Declare a maximum of 2 backtracks per query, where a backtrack returns to the nearest level holding an untried sibling above threshold and expands exactly one alternative branch.
- Declare the dead-end conditions that trigger a backtrack, covering a branch with no authorized children, no children above threshold, a stale representation, or a repeated frontier state.
- Declare the flat fallback trigger, requiring a single flat retrieval pass over the authorized leaves whenever the descent terminates without covering every required sub-question, and count fallback invocation as a routing failure signal rather than as a success.
- Bound the descent with per-query limits on depth, total branches expanded, candidates scored, model calls, tokens, latency, and money, and require the descent to return supported partial results when a bound is reached rather than truncating silently.

**Required Outputs**:

- A per-level fan-out declaration with its justification.
- A compounded reachability estimate computed across the declared depth.
- A backtracking policy naming the bound, the trigger conditions, and the target selection rule.
- A flat fallback trigger specification with its accounting treatment.
- A per-query budget declaration covering every bounded dimension.

**Quality Checkpoints**:

- Compounded reachability across the declared depth is at least 0.90 on the tuning split; a lower value requires wider fan-out or fewer levels before release.
- Backtracks per query do not exceed 2; an unbounded backtracking policy converts a bounded descent into an exhaustive scan at higher cost than the flat baseline.
- Every dead-end condition is detectable deterministically from the descent state, without a model judgement.
- The flat fallback is reachable from every terminal state of the descent.

***

#### Step 3.3: Bind the Model Branch Preference to the Declared Fan-Out

**Required Actions**:

- Supply the model tier only the authorized candidate set retrieved deterministically at the current level, together with each candidate's representation and term field.
- Require the model to return a ranked preference over that set with a stated reason per candidate, and prohibit it from naming any node absent from the set.
- Truncate any preference longer than the declared fan-out in the model's own rank order, record the truncation, and never widen the beam because the model expressed more preferences.
- Discard any preference naming an unavailable candidate, and fall back to the deterministic score ordering for that level rather than re-prompting more than once.
- Record the model's preference beside the deterministic score ordering, so that disagreement between them becomes a measurable signal rather than an invisible override.
- Reserve at least 1 branch slot for the highest deterministic scorer where the model's ordering differs from it, so that a model misjudgement cannot discard the strongest lexical or dense match on its own.

**Required Outputs**:

- A candidate package supplied to the model tier at each level, recording exactly what was shown.
- A model preference record with a reason per candidate.
- A truncation log naming every preference cut by the fan-out bound.
- A disagreement record comparing model ordering against deterministic ordering per level.

**Quality Checkpoints**:

- No branch is expanded that the deterministic retrieval did not supply; a model-introduced branch is a blocking defect.
- The retained branch count never exceeds the declared fan-out, whatever the model returns.
- The highest deterministic scorer occupies a branch slot whenever model and deterministic orderings disagree.
- Model and deterministic orderings are both recorded; storing only the final selection makes routing loss unattributable between the tiers.

***

### Phase 4: Bounded Retrieval Execution and Flat-Baseline Verification

**Objective**: Execute the descent under the declared policy and establish numerically how much evidence the hierarchy loses relative to a flat index on the same cases.

#### Step 4.1: Execute the Bounded Descent and Record Every Decision With Its Alternatives

**Required Actions**:

- Enter the descent at the authorized root set, applying authorization before the first score is computed and again at every subsequent level.
- Score the eligible children at the current level under the declared rule, retain the branches permitted by the fan-out, and prune the remainder.
- Record for every level a descent record naming the candidates considered, each candidate's component scores and combined score, the branches retained, the branches pruned, and the reason for each prune, expressed as below threshold, outside fan-out, unauthorized, or stale.
- Require a gain condition to continue descending, meaning the level must cover a query constraint not already covered or improve predicted leaf reachability; a higher similarity score carrying no new coverage is not a reason to continue.
- Detect dead ends and repeated frontier states deterministically, and issue a backtrack within the declared bound when one occurs.
- Terminate the descent when the leaf level is reached for every required sub-question, when a budget bound is met, or when the backtrack bound is exhausted, and invoke the flat fallback where required sub-questions remain uncovered.
- Return supported partial results with a statement of what was not covered whenever a bound terminates the descent, rather than presenting a truncated result as complete.

**Required Outputs**:

- A per-level descent record with candidates, component scores, retentions, prunes, and prune reasons.
- A terminal state record naming the termination cause and the covered sub-questions.
- A backtrack log naming each backtrack, its trigger, and its target.
- A fallback invocation record where the flat path was used.

**Quality Checkpoints**:

- Every pruned candidate is recorded with a reason; a descent recording only retained branches cannot support routing loss diagnosis and fails the release gate.
- Authorization is evaluated at every level, and the decision identifier is recorded per level rather than once per request.
- No descent exceeds the declared depth, fan-out, or backtrack bounds.
- Every termination names one declared cause; a descent ending without a recorded cause is treated as a defect rather than as a success.

***

#### Step 4.2: Assemble Evidence From Leaves Under an Expansion Cap

**Required Actions**:

- Rank the retrieved leaves, and where required rank source-bearing parents, but never rank an internal representation into the evidence set as though it were source content.
- Expand a selected leaf to the smallest enclosing unit that resolves a missing referent, definition, qualification, or temporal condition, and stop at the first unit that resolves it.
- Cap expansion at 2 enclosing levels and at 1 adjacent sibling on each side, and enforce the request's evidence token ceiling by truncating at a structural boundary rather than mid-unit.
- Deduplicate overlapping ancestors and descendants so that the same content does not occupy several evidence slots at different levels.
- Preserve the originally matched leaf and its exact span for citation, and never allow an expanded parent to inherit the leaf's relevance score unmodified.
- Refuse to satisfy a missing qualifier from an internal node representation; where the qualifier is absent from every authorized leaf, state the gap or abstain.

**Required Outputs**:

- An admitted evidence set of leaf spans with source identifiers, versions, and offsets.
- An expansion record naming each expansion, its trigger, and the unit added.
- A deduplication record naming suppressed ancestor-descendant overlaps.
- A citation map binding every material claim to a leaf span.

**Quality Checkpoints**:

- No internal node representation appears in the admitted evidence set; a citation resolving to a derived summary marks the claim unsupported.
- Expansion does not exceed 2 enclosing levels or 1 sibling on each side.
- Every admitted span resolves to an authorized leaf at the version recorded in the manifest.
- Duplicate content across levels occupies at most 1 evidence slot.

***

#### Step 4.3: Run the Flat-Baseline Recall Comparison and Compute Routing Loss

**Required Actions**:

- Run the hierarchical configuration and the retained flat configuration over the same evaluation cases, under the same reranker, the same evidence token ceiling, the same authorization policy, and the same generator, so that any difference is attributable to routing.
- Run a third oracle-routing configuration in which the labelled correct ancestor is supplied at every level and only leaf-level retrieval executes, producing conditional leaf recall.
- Compute routing loss as conditional leaf recall minus actual hierarchical leaf recall, in percentage points, globally and per slice.
- Compute the hierarchy margin as actual hierarchical leaf recall minus flat leaf recall, in percentage points, globally and per slice.
- Count unreachable answer-bearing leaves directly, defined as labelled leaves whose every ancestor was pruned before the leaf level, and report the count alongside the rates.
- Apply the decision rules: routing loss at or below 3 percentage points is acceptable; above 3 and at or below 10 requires fan-out widening or representation repair before release; above 10 rejects the hierarchy for the affected slice, which is routed to the flat path permanently.
- Reject the hierarchy entirely where the hierarchy margin is below 5 percentage points on the declared target slice, or where the margin is negative on any slice, or where the margin disappears once token and reranker budgets are equalised.
- Record the comparison as a permanent release artifact and re-run it at every release, since a hierarchy that earned its place against one corpus may not against the next.

**Required Outputs**:

- A three-way comparison record covering flat, hierarchical, and oracle-routing configurations.
- A routing loss figure in percentage points, globally and per slice.
- A hierarchy margin figure in percentage points, globally and per slice.
- An unreachable answer-bearing leaf count with the identifiers of the affected cases.
- A routing decision record naming which slices the hierarchy serves and which the flat path serves.

**Quality Checkpoints**:

- All three configurations ran under identical reranker, token, authorization, and generator settings; an unequal comparison is void and is re-run rather than reported.
- Routing loss is at or below 3 percentage points on every served slice, or the slice is routed to the flat path.
- The hierarchy margin is at least 5 percentage points on the declared target slice; a hierarchy failing this is retired rather than retained.
- Unreachable answer-bearing leaves number 0 in the highest risk tier; any non-zero count in that tier halts release.

***

### Phase 5: Incremental Maintenance and Ancestry Repair

**Objective**: Keep derived levels consistent with a changing corpus by repairing only the ancestry above each change, and rebuild only when a declared trigger fires.

#### Step 5.1: Detect Impact Through the Reverse Derivation Index

**Required Actions**:

- Treat every corpus event as a repair trigger, covering insertion, update, deletion, reordering, reclassification, permission change, and summariser or prompt version change, and assign each event an idempotency key.
- Recompute the child content hash of every node whose children the event touched, and compare it against the stored hash rather than comparing timestamps, since a timestamp records when a job ran and not whether content changed.
- Walk the reverse derivation index from every affected leaf to its complete ancestry, and additionally to any cluster whose membership the event alters, since a clustered level's parents can be invalidated by a change to a node they do not contain.
- Mark every node with a hash mismatch as stale, and mark every derived artifact keyed on that node, covering embeddings, routing caches, descent caches, and evaluation fixtures.
- Compute the blast radius of the event as the count of nodes marked stale, and compare it against the per-event bound before any repair work is scheduled.
- Record the impact set with the event key, so that a repeated delivery of the same event repairs nothing a second time.

**Required Outputs**:

- An impact set naming every stale node and every stale derived artifact.
- A blast radius count per event.
- An invalidated cache key list bound to the event.
- An idempotency record preventing duplicate repair.

**Quality Checkpoints**:

- Staleness is determined by hash comparison; a maintenance path relying on timestamps alone is rejected because it misses content-preserving reorderings and policy changes.
- Every clustered level's membership recomputation is included in the impact walk, not only the containment ancestry.
- Every cache keyed on a stale node is invalidated in the same transaction that marks the node stale.
- The impact set is computable without scanning the corpus; a maintenance design requiring a full scan per event does not meet the incremental requirement.

***

#### Step 5.2: Repair Only the Affected Ancestry Under a Blast-Radius Bound

**Required Actions**:

- Repair from the bottom upward, recomputing the smallest affected parents first, then propagating only where a parent's recomputed representation or ordered child hash actually changed.
- Stop propagation at the first level where both the ordered child hash and the validated representation are unchanged, since an unchanged parent cannot have changed its own ancestors.
- Re-run the Step 2.3 child-discriminability gate on every repaired representation, applying the same thresholds used at build time, and never publish a repaired node that would have failed at build.
- Enforce a per-event blast radius bound of 200 nodes or 2 percent of internal nodes, whichever is smaller, and enforce a per-event token, money, and wall-clock ceiling alongside it.
- Abandon incremental repair where the bound is exceeded, retain the prior manifest as the serving version, mark the affected routes stale, and schedule a shadow rebuild rather than repairing past the bound.
- Propagate deletions and permission revocations through the same path, removing the leaf from every serving index, invalidating every ancestor that depended on it, and proving absence by source identifier, leaf identifier, content hash, and serving query before the new manifest is published.
- Publish repairs as an immutable manifest with a rollback target, never by mutating a serving node in place.

**Required Outputs**:

- A repair transaction record naming every recomputed node and the level at which propagation stopped.
- A fidelity re-verification record for every repaired representation.
- A deletion proof for every removed or revoked leaf.
- A new immutable manifest with its rollback target.

**Quality Checkpoints**:

- Repair touches only nodes in the impact set; a repair recomputing an unaffected subtree indicates a defective derivation index and halts the maintenance path.
- Propagation stops at the first unchanged parent; unconditional propagation to the root converts every edit into a near-full rebuild.
- Every repaired representation passes the same fidelity thresholds as a newly built one.
- No deletion is considered complete without a passing negative retrieval test against the new manifest.

***

#### Step 5.3: Enforce the Re-Index Trigger and the Staleness Serving Rule

**Required Actions**:

- Declare the re-index trigger as a disjunction of measured conditions, firing when cumulative changed leaves reach 15 percent of the corpus since the last full build, when clustered membership stability falls below 0.80 against the prior build, when routing accuracy falls 5 percentage points below its build-time value, or when stale nodes exceed 5 percent of internal nodes.
- Bound the trigger by requiring a full rebuild to complete within 7 days of firing, and treat an unmet bound as a release-blocking condition rather than as a backlog item.
- Apply the staleness serving rule at query time, refusing a stale node as a routing target for freshness-critical and authorization-sensitive queries, and routing those queries to the flat path instead.
- Measure stale exposure as the proportion of served queries whose descent traversed at least 1 stale node, and hold it at or below 1 percent; above 1 percent, route the affected slice to the flat path until repair completes.
- Rebuild into a shadow index, compare it against the serving index on the frozen evaluation set before any traffic moves, and switch the serving alias atomically with the prior manifest retained for rollback.
- Recompute the Phase 1 depth decision at every full rebuild, since corpus growth or contraction may have moved the corpus into a different depth band or below the hierarchy threshold entirely.

**Required Outputs**:

- A declared re-index trigger with its four measured conditions and their current values.
- A stale exposure measurement over served queries.
- A shadow rebuild comparison record against the serving index.
- A recomputed depth decision produced at each full rebuild.

**Quality Checkpoints**:

- Every trigger condition is measured continuously rather than evaluated on request; an unmeasured condition cannot fire.
- Stale exposure is at or below 1 percent of served queries; above that the affected slice serves from the flat path.
- No rebuild replaces a serving index without a shadow comparison on the frozen evaluation set.
- The depth decision is recomputed at every full rebuild rather than inherited from the previous build.

***

### Phase 6: Loss Attribution, Ablation, and Release Gating

**Objective**: Attribute every failure to a named cause, prove that every level earns its cost, and gate release on measured evidence rather than on aggregate improvement.

#### Step 6.1: Attribute Every Miss to Routing, Ranking, Fidelity, or Staleness

**Required Actions**:

- Classify every failed case into exactly one class from Section 1.4, applying the ordered tests to the descent records, the admitted set, and the labelled spans.
- Separate routing loss from ranking loss numerically, using the oracle-routing configuration from Step 4.3, and never report a single end-to-end recall figure as the diagnosis of a hierarchical system.
- Distinguish a fidelity miss from a fan-out miss by re-running the failed case with fan-out widened to include the correct branch; recovery under wider fan-out indicates a fan-out miss, and continued failure indicates the representation itself lacks the discriminating term.
- Distinguish a staleness miss by recomputing the child content hashes of the nodes on the failing decision path at the time of the failure.
- Report per-stage candidate survival, meaning the proportion of labelled relevant leaves whose eligible ancestor remains after each level, so that the level at which evidence disappears is identified rather than inferred.
- Report over-pruning per level, defined as relevant candidates removed at that level divided by relevant candidates entering it, and treat any level above 5 percent as the first repair target.
- Aggregate attribution by slice, since a hierarchy can be healthy in aggregate while losing an entire slice to a single mis-specified level.

**Required Outputs**:

- A per-case attribution record naming exactly one failure class.
- A stage-wise candidate survival curve across levels.
- A per-level over-pruning rate.
- A slice-level attribution summary naming the dominant class per slice.

**Quality Checkpoints**:

- Every failed case carries exactly one class; an unclassified failure indicates missing descent records and blocks the release gate.
- Routing loss and ranking loss are reported separately; a report giving only end-to-end recall is rejected as non-diagnostic.
- Over-pruning is at or below 5 percent at every level; a level above it is repaired or removed before release.
- Attribution is computed per slice as well as in aggregate.

***

#### Step 6.2: Run the Required Ablations Including Level Removal

**Required Actions**:

- Ablate each level individually by collapsing it and routing directly from its parent to its children, and retain the level only where its removal degrades a measured quantity.
- Ablate fan-out by running the declared width, the width below it, and the width above it, and select the smallest width whose routing loss is at or below 3 percentage points.
- Ablate the model branch preference by running deterministic scoring alone, and retain the model tier at routing only where it improves routing accuracy by at least 2 percentage points over deterministic scoring at equal cost.
- Ablate the abstractive representation against the deterministic term field and against an extractive or structural representation, and adopt the cheapest representation that passes the fidelity gate and the routing accuracy target.
- Ablate backtracking and the flat fallback separately, reporting how many cases each recovers, since a fallback recovering many cases indicates the routing policy rather than the fallback needs repair.
- Hold the generator, reranker, evidence token ceiling, and authorization policy fixed across every ablation, and report both aggregate and per-slice results.
- Run every ablation on the tuning split, and confirm the selected configuration once on the frozen split without further adjustment.

**Required Ablation Set and Retention Rule**:

| Ablation | Comparison run | Retention rule for the ablated component |
| :-- | :-- | :-- |
| Level removal | Collapse one level, route parent to grandchildren | Retain only where removal costs at least 2 points of recall or 60 percent of candidate reduction |
| Fan-out width | Declared width against one narrower and one wider | Adopt the narrowest width holding routing loss at or below 3 points |
| Model branch preference | Deterministic scoring alone | Retain only where routing accuracy improves by at least 2 points at equal cost |
| Abstractive representation | Term field alone, and extractive representation | Retain only where it beats the cheapest passing alternative on routing accuracy |
| Backtracking | Descent with backtracking disabled | Retain where it recovers at least 2 percent of cases |
| Flat fallback | Descent with fallback disabled | Always retained; a high recovery rate is a routing defect signal, not a success |
| Whole hierarchy | Flat fused baseline at equal budgets | Retain only where the target-slice margin is at least 5 points |

**Required Outputs**:

- An ablation record per component with aggregate and per-slice deltas.
- A selected configuration naming depth, fan-out, representation type, and model tier role.
- A frozen-split confirmation run of the selected configuration.
- A removal record naming every component ablation retired.

**Quality Checkpoints**:

- Every level in the served configuration has been ablated individually; an unablated level is unjustified complexity.
- Downstream components are held fixed across ablations; a comparison changing two variables is void.
- The frozen split is used exactly once per release, for confirmation only.
- Every retained component satisfies its stated retention rule; components failing it are removed rather than kept as legacy.

***

#### Step 6.3: Operate the Release Gate and the Hierarchy Retirement Rule

**Required Actions**:

- Freeze the candidate manifest with every dependent version, covering parser, node schema, summariser model and prompt, clustering configuration and its random seed, embedding model, index parameters, routing policy, thresholds, and evaluation set version.
- Run the structural suite first, covering schema validation, cycle detection, orphan detection, lineage completeness, hash coverage, authorization tests, and deletion proofs, and treat any failure as blocking.
- Run the quality suite second, covering the three-way flat comparison, routing loss, per-stage survival, over-pruning, fidelity rates, stale exposure, latency percentiles, and cost per correct grounded answer.
- Apply the hard gates, which are zero authorization defects, zero unreachable answer-bearing leaves in the highest risk tier, routing loss at or below 3 percentage points on every served slice, stale exposure at or below 1 percent, and no regression on any per-slice recall figure.
- Reject the release where aggregate quality improves while any hard gate fails, since an aggregate gain that conceals a slice failure is the characteristic failure of hierarchical systems.
- Cap tuning at 5 cycles on the tuning split per release, and reformulate the architecture rather than continuing to tune thresholds, prompts, or fan-out beyond that.
- Apply the retirement rule at every release, retiring the hierarchy or one of its levels wherever the flat path now matches it within 5 percentage points on every slice, since corpus, embedding, or chunking changes can close the gap that justified construction.
- Switch the serving alias atomically, retain the prior manifest, and arm automatic rollback on any authorization defect, unproven deletion, reachability regression above 2 percentage points, stale exposure above the limit, or sustained latency or cost breach.

**Required Outputs**:

- A frozen candidate manifest with every dependent version recorded.
- A structural suite report and a quality suite report with per-slice results.
- A hard gate verdict record naming each gate and its measured value.
- A release decision with an approver, a rollback target, and a retirement assessment.

**Quality Checkpoints**:

- Every hard gate carries a measured value rather than an assertion; an unmeasured gate is treated as failed.
- No release proceeds on aggregate improvement while a per-slice recall figure regresses.
- Tuning cycles per release do not exceed 5; a sixth cycle triggers architecture reformulation.
- The retirement assessment is performed at every release, and a hierarchy no longer beating the flat path by 5 percentage points on any slice is retired.

***

## III. Implementation Guidance for AI Agents

AI agents operating a hierarchical index must follow systematic protocols ensuring that every routing decision is bounded, recorded with its alternatives, and verifiable against a flat control. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Corpus Analyst Agent**: Measures leaf count, structural availability, change rate, and query volume, and owns the depth decision and the flat baseline. It alone may declare that a corpus does not warrant hierarchy, and it re-runs that declaration at every full rebuild.
2. **Construction Agent**: Builds typed nodes, typed edges, lineage, and the reverse derivation index, and emits the immutable build manifest. It may not publish a build failing structural validation.
3. **Summarisation Agent**: Operates on the model tier and writes internal node representations from authorized children only. It never judges its own output, never sees evaluation queries, and never extends its input beyond the children it was given.
4. **Fidelity Gate Agent**: Runs child-discriminability, sibling separation, and routing-term coverage deterministically, and holds authority to reject a representation, order a bounded regeneration, or force the extractive fallback.
5. **Routing Executor**: Applies authorization, scores candidates, maintains the beam, enforces fan-out, detects dead ends, issues backtracks within bound, and writes the descent record. It alone expands a branch, and it never expands one the retrieval did not supply.
6. **Maintenance Agent**: Detects impact through the reverse derivation index, repairs affected ancestry within the blast radius bound, enforces the staleness serving rule, and fires the re-index trigger.
7. **Evaluation Agent**: Runs the flat, hierarchical, and oracle-routing configurations, computes routing loss and the hierarchy margin, attributes every failure, and returns the release verdict with evidence. It may veto a release and may order retirement of a level.

**Separation Requirement**: The agent that writes a representation never judges it, and the agent that executes routing never edits the representations it routes on. Fusing these roles makes a fidelity failure indistinguishable from a routing failure, because the same component would both cause and assess it.

**Workflow Execution Pattern**:

```
STATE: Level_Routing_Decision
INPUTS:
  1. Authorized candidate children at current level
  2. Declared routing rule, threshold, and fan-out for this level
  3. Remaining depth, branch, candidate, token, latency, and cost budgets
  4. Frontier state hash from the previous level
ACTIONS:
  1. Apply authorization and metadata filters before any scoring
  2. Compute component scores and combined score per candidate
  3. Request model branch preference over the filtered candidate set
  4. Truncate preference to declared fan-out in rank order
  5. Reserve one slot for the highest deterministic scorer on disagreement
  6. Retain branches, prune remainder, write descent record with reasons
VALIDATION:
  - retained_branch_count <= declared_fan_out
  - every_retained_branch IN authorized_candidate_set
  - pruned_candidates_recorded_with_reason == TRUE
  - stale_node_selected_for_freshness_critical_query == FALSE
  - frontier_state_hash != previous_frontier_state_hash
  - remaining_budget_all_dimensions > 0
TRANSITIONS:
  IF leaf_level_reached THEN next_state = Evidence_Assembly
  IF dead_end_detected AND backtracks_used < 2 THEN next_state = Backtrack
  IF dead_end_detected AND backtracks_used == 2 THEN next_state = Flat_Fallback
  IF budget_exhausted THEN next_state = Partial_Result_With_Coverage_Statement
  IF validation_failed THEN next_state = Routing_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended retention and prune set with its scores and reasons before committing it; confirm it against the validation block while no descent cost is committed; commit the expansion only after validation passes, writing the descent record in the same operation so that no branch is expanded without a corresponding record.

**Approval Gate**: Human authorisation is required before publishing any manifest whose routing loss exceeds 3 percentage points on a served slice, before serving any slice carrying a non-zero unreachable answer-bearing leaf count in the highest risk tier, before widening fan-out above 5 at any level, before relaxing any fidelity threshold below the Step 2.3 values, and before a full rebuild whose estimated cost exceeds 20 percent of the monthly retrieval budget. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the manifest, routing policy, thresholds, and budget ledger in durable state, since a build or a maintenance run may outlive a single context window.
- Process construction and repair one level at a time, appending results to durable storage rather than holding a whole level in working context.
- Write a handoff record at every context boundary naming the completed levels, the pending levels, the blast radius consumed, and the remaining budget.
- Never load a full descent trace into working context to make a routing decision; the decision depends only on the current level's candidates and the declared policy.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Baseline and Depth Justification (After Phase 1)**

- **Automated Check**: The flat fused baseline ran on the full evaluation set; the hierarchy hypothesis names one slice and one metric with a minimum gain of at least 5 percentage points; declared depth is within 5 levels; build cost amortises within 90 days.
- **Agent Action on Pass**: Proceed to level construction.
- **Agent Action on Failure**: Halt and return the missing measurement; no level is constructed against an unmeasured baseline.
- **Human Review Trigger**: An amortisation window above 90 days, or a corpus below 10,000 leaves proposed for hierarchy.

**Checkpoint 2: Structural Integrity (After Phase 2, Step 2.1)**

- **Automated Check**: Every leaf reachable from an authorized root; zero cycles; zero empty internal nodes; reverse derivation index complete; identifiers reproducible across rebuild.
- **Agent Action on Pass**: Proceed to representation construction.
- **Agent Action on Failure**: Quarantine the affected subtree and halt; structural defects are never carried into a build.
- **Human Review Trigger**: More than 1 percent of leaves unreachable from any authorized root.

**Checkpoint 3: Summary Fidelity (After Phase 2)**

- **Automated Check**: Self-routing recall at least 0.95 and sibling separation at least 0.90 for every serving node; routing-term coverage at least 0.90; quarantined nodes at most 2 percent of internal nodes.
- **Agent Action on Pass**: Proceed to routing policy declaration.
- **Agent Action on Failure**: Regenerate the failing nodes at most twice, then force the extractive fallback; nodes still failing are quarantined and their subtrees served through the flat path.
- **Human Review Trigger**: Quarantined nodes above 2 percent, which rejects the level's grouping basis.

**Checkpoint 4: Routing Policy Validity (After Phase 3)**

- **Automated Check**: Authorization precedes scoring at every level; every level carries a calibrated threshold; compounded reachability at least 0.90; fan-out declared per level; backtrack bound at most 2; flat fallback reachable from every terminal state.
- **Agent Action on Pass**: Proceed to serving and verification.
- **Agent Action on Failure**: Halt; an unbounded or unfiltered routing policy is never served with a warning attached.
- **Human Review Trigger**: A declared fan-out of 1 at any level, or compounded reachability below 0.90 after one widening attempt.

**Checkpoint 5: Flat-Baseline Verification (After Phase 4)**

- **Automated Check**: Three configurations ran under identical reranker, token, authorization, and generator settings; routing loss at or below 3 percentage points per served slice; hierarchy margin at least 5 percentage points on the target slice; unreachable answer-bearing leaves zero in the highest risk tier.
- **Agent Action on Pass**: Register the hierarchy as the serving path for the qualifying slices.
- **Agent Action on Failure**: Route the failing slice to the flat path and return the routing loss figure; the hierarchy is never retained for a slice it loses on.
- **Human Review Trigger**: Routing loss above 10 percentage points on any slice, or a negative hierarchy margin on any slice.

**Checkpoint 6: Maintenance Consistency (Continuous, Phase 5)**

- **Automated Check**: Staleness determined by hash comparison; blast radius within 200 nodes or 2 percent of internal nodes; every repaired representation re-passes the fidelity gate; stale exposure at or below 1 percent of served queries; deletion proofs pass.
- **Agent Action on Pass**: Publish the repaired manifest and switch the alias.
- **Agent Action on Failure**: Retain the prior manifest, mark affected routes stale, and schedule a shadow rebuild.
- **Human Review Trigger**: Any unproven deletion, any permission broadening, or stale exposure above 1 percent for more than 24 hours.

**Checkpoint 7: Release and Retirement (After Phase 6)**

- **Automated Check**: All hard gates carry measured values; no per-slice recall regression; every level individually ablated; tuning cycles at most 5; retirement assessment performed.
- **Agent Action on Pass**: Switch the serving alias atomically and retain the prior manifest.
- **Agent Action on Failure**: Halt release and return the failing gates with measured values.
- **Human Review Trigger**: Aggregate improvement accompanied by any per-slice regression, or a retirement recommendation against a hierarchy in production.

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

**Error Type 1: Routing Error Compounding**

- **Symptoms**: Conditional leaf recall under oracle routing substantially exceeds actual leaf recall; labelled leaves appear in no candidate set; the failure concentrates in one slice; a stronger reranker produces no improvement.
- **Diagnostic Steps**: Compute routing loss per level from the descent records, locate the level at which candidate survival drops, and re-run the failing cases with the correct branch forced to determine whether the leaf retriever succeeds when reached.
- **Resolution Protocol**: Option A, widen fan-out at the identified level and re-measure routing loss. Option B, repair the representations at that level under Step 2.3 where the fan-out ablation shows the branch was scored below its siblings on a term the children carry. Option C, collapse the level entirely where its removal does not degrade candidate reduction beyond the retention rule. Option D, route the affected slice permanently to the flat path.
- **Escalation Trigger**: Routing loss above 10 percentage points on any slice escalates immediately and routes that slice to the flat path; this class is never resolved by adding a level, since another level multiplies a further accuracy term into compounded reachability.

**Error Type 2: Summary Fidelity Failure**

- **Symptoms**: Branches are discarded whose children contain the query's entity, date, or quantity; representations read fluently while omitting minority topics; sibling separation falls near chance; regenerated summaries repeat the same omission.
- **Diagnostic Steps**: Compare the representation's term field against the union of discriminative child terms, and identify whether the missing term is absent from the abstractive text, from the term field, or from both.
- **Resolution Protocol**: Option A, regenerate with the specific missing terms supplied as the repair instruction, at most twice. Option B, fall back to an extractive or structural representation, which cannot omit a term it did not paraphrase. Option C, reduce the node's child count by splitting it, since a representation summarising too many heterogeneous children cannot retain every discriminator within its token ceiling. Option D, quarantine the node and serve its subtree through the flat path.
- **Escalation Trigger**: A third regeneration is prohibited, because repeated generation from the same children and prompt produces correlated omissions; after two failures the extractive fallback is mandatory.

**Error Type 3: Ancestry Staleness and Repair Blowout**

- **Symptoms**: Stale exposure rises above 1 percent of served queries; a single change event marks a large fraction of internal nodes stale; repair jobs exceed their wall-clock ceiling; routing decisions cite children that no longer exist.
- **Diagnostic Steps**: Inspect the impact walk for the offending event and determine whether the blast radius came from containment ancestry, which is bounded by depth, or from clustered membership recomputation, which is not.
- **Resolution Protocol**: Option A, repair within the blast radius bound and publish a new manifest. Option B, abandon incremental repair, retain the prior manifest, mark affected routes stale, and schedule a shadow rebuild. Option C, replace the clustered level with a structural level where membership recomputation is the recurring cause, since containment ancestry bounds the blast radius by construction.
- **Escalation Trigger**: Stale exposure above 1 percent for more than 24 hours escalates and routes the affected slice to the flat path; a repair exceeding the blast radius bound is never continued past the bound.

**Error Type 4: Cluster Drift and Unstable Routing**

- **Symptoms**: Small corpus or random-seed changes relocate many nodes; membership stability against the prior build falls below 0.80; routing decisions for unchanged queries change between builds; summary churn rises without corpus change.
- **Diagnostic Steps**: Recompute membership overlap against the prior build, re-run clustering under at least 2 alternative random seeds, and compare routing decisions on a fixed query sample across those builds.
- **Resolution Protocol**: Option A, pin the random seed and training sample for reproducibility while continuing to test alternates for robustness. Option B, replace the clustered level with the source structure where structure exists, since containment does not drift. Option C, permit bounded soft membership so that boundary nodes reach more than one parent, with a declared duplication cap.
- **Escalation Trigger**: Membership stability below 0.80 fires the re-index trigger; below 0.70 the clustered basis is rejected and the level is rebuilt on a different basis or removed.

**Error Type 5: Descent Cost Explosion**

- **Symptoms**: Broad queries fan out across many branches; per-query model calls exceed the declared bound; p95 latency exceeds the flat path; cost per correct grounded answer rises while recall stays flat.
- **Diagnostic Steps**: Attribute cost per level from the descent records, separating candidate scoring, model branch preference calls, backtracking, and fallback invocations.
- **Resolution Protocol**: Option A, narrow fan-out to the smallest width holding routing loss at or below 3 percentage points. Option B, remove the model branch preference at levels where deterministic scoring matched it within 2 percentage points. Option C, stop before a stage whose measured p95 exceeds the remaining deadline and return supported partial results.
- **Escalation Trigger**: A hierarchical configuration whose cost per correct grounded answer exceeds the flat path escalates for retirement review; the descent is never continued on the expectation that remaining budget alone justifies it.

**Error Type 6: Hierarchy Margin Collapse**

- **Symptoms**: The hierarchy margin falls below 5 percentage points on the target slice; the margin disappears once token and reranker budgets are equalised; the flat fallback recovers a growing share of queries.
- **Diagnostic Steps**: Re-run the three-way comparison at equal budgets, and determine whether the flat path improved through a corpus, chunking, or embedding change, or whether the hierarchy degraded through drift or staleness.
- **Resolution Protocol**: Option A, repair the hierarchy where the cause is drift or staleness and re-measure. Option B, collapse the levels that no longer satisfy the level retention rule. Option C, retire the hierarchy and serve from the flat path, retaining the measurement record that justifies the retirement.
- **Escalation Trigger**: A negative margin on any slice routes that slice to the flat path at once; a margin below 5 percentage points on the target slice at two consecutive releases retires the hierarchy without further tuning.

**Troubleshooting Decision Tree**:

```
EVALUATION DETECTS A RECALL FAILURE
├─ EVIDENCE NEVER REACHED THE LEAF STAGE
│   ├─ Correct branch scored below siblings on a term children carry
│   │   → Repair representation; force extractive fallback after 2 attempts
│   ├─ Correct branch scored above threshold but outside fan-out
│   │   → Widen fan-out at that level; re-measure routing loss
│   ├─ Correct branch pruned as stale
│   │   → Repair ancestry; refuse stale nodes for freshness-critical routes
│   └─ Routing loss above 10 points after repair
│       → ESCALATE; route slice to flat path permanently
├─ EVIDENCE REACHED THE LEAF STAGE AND MISSED THE CUT
│   ├─ Leaf ranking defect → Repair fusion or deepen the leaf cut
│   └─ Wider fan-out attempted → Reject; fan-out cannot fix a ranking miss
├─ STRUCTURE DEFECT
│   ├─ Leaf unreachable from any authorized root → Quarantine and count
│   ├─ Cycle or empty internal node detected → HALT build; do not publish
│   └─ Membership stability below 0.80 → Fire re-index trigger
├─ COST OR LATENCY DEFECT
│   ├─ Model preference calls dominate cost → Ablate; remove below 2-point gain
│   ├─ Backtracking dominates cost → Repair routing policy, not the bound
│   └─ Cost per correct answer above flat path → ESCALATE for retirement review
└─ COMPARISON DEFECT
    ├─ Budgets unequal across configurations → Void the result; re-run
    ├─ Frozen split used for tuning → Void the release; rebuild the split
    └─ Aggregate gain with per-slice regression → HALT release; ESCALATE
```

### D. Performance Metrics and Continuous Learning

**Routing and Reachability Metrics**:

- **Routing accuracy per level**: Cases retaining at least 1 correct branch at that level (target: at least 0.90; a level below 0.90 is repaired or removed).
- **Compounded reachability**: Product of per-level routing accuracies across the served depth (target: at least 0.90).
- **Routing loss**: Conditional leaf recall under oracle routing minus actual leaf recall (target: at most 3 percentage points; above 10 routes the slice to the flat path).
- **Unreachable answer-bearing leaves**: Labelled leaves whose every ancestor was pruned (target: 0 in the highest risk tier).
- **Over-pruning per level**: Relevant candidates removed divided by relevant candidates entering (target: at most 5 percent per level).
- **Backtracking recovery rate**: Cases recovered by a backtrack (target: at least 2 percent, or backtracking is removed as unearned cost).
- **Flat fallback invocation rate**: Queries requiring the flat path (target: at most 10 percent; a higher rate indicates the routing policy, not the fallback, needs repair).

**Fidelity and Freshness Metrics**:

- **Self-routing recall**: Nodes retained for probes derived from their own children (target: at least 0.95 per serving node).
- **Sibling separation**: Nodes outranking every sibling on their own probes (target: at least 0.90 per serving node).
- **Routing-term coverage**: Discriminative child terms present in the representation or term field (target: at least 0.90).
- **First-pass fidelity rate**: Representations passing the gate without regeneration (target: at least 0.85; below it the summary standard or the token ceiling is misspecified).
- **Stale exposure**: Served queries whose descent traversed at least 1 stale node (target: at most 1 percent).
- **Membership stability**: Overlap of clustered membership against the prior build (target: at least 0.80).

**Cost and Comparative Metrics**:

- **Hierarchy margin**: Hierarchical leaf recall minus flat leaf recall at equal budgets (target: at least 5 percentage points on the target slice; negative on any slice routes that slice flat).
- **Candidate reduction per level**: Proportion of candidates eliminated at that level (target: at least 60 percent, or the level fails the retention rule).
- **Build cost amortisation**: Build cost divided by projected query volume (target: recovery within 90 days).
- **Maintenance cost ratio**: Repair cost over the period divided by initial build cost (target: below 0.25 per quarter; above it indicates the corpus changes faster than the hierarchy can be maintained).
- **Cost per correct grounded answer**: Total cost divided by answers supported by resolving citations (target: below the flat path at matched quality).

**Log-Pattern Failure Detection**: A rising flat fallback rate with stable leaf recall indicates a routing policy degrading while the leaf index holds. Descent records showing the correct branch consistently ranked second indicate a fan-out of 1 where 2 is required. Prune reasons concentrated on one level indicate a threshold mis-calibrated for that level's score distribution. Summary churn without corpus change indicates clustering instability rather than content change. Model branch preferences disagreeing with deterministic ordering on cases that later fail indicate the model tier is not earning its place at routing.

**Learning and Adaptation Mechanisms**:

- **Failure-to-case conversion**: Convert every confirmed production routing failure into a labelled evaluation case carrying its correct ancestors, so the next release measures the defect rather than rediscovering it.
- **Threshold recalibration**: Recompute per-level thresholds and fan-out at every full rebuild against observed score distributions; the values stated in this guide are deployment defaults, not constants.
- **Representation policy revision**: Where extractive representations match generated ones on routing accuracy for a level across two releases, adopt the extractive form permanently and retire the model calls for that level.
- **Depth revision**: Re-run the depth decision at every full rebuild, admitting or collapsing levels against the retention rule rather than preserving the depth the first build happened to choose.

**Human-in-the-Loop Boundaries**: Relaxation of a fidelity threshold, publication of a manifest carrying an unproven deletion, service of a slice with unreachable answer-bearing leaves in the highest risk tier, and retirement of a hierarchy in production are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how a corpus is narrowed and how that narrowing is verified, rather than what the corpus contains. Its phases hold wherever a corpus is too large to scan flat, carries a groupable structure, and supports a labelled evaluation set.

### 4.1 Cross-Domain Application Patterns

**Regulatory and legal document archives**: Source structure is authoritative and stable, so levels follow filing, exhibit, section, and clause containment rather than clustering. Representations must be extractive or heavily term-augmented, because a paraphrase that drops a qualifier, a monetary threshold, or a negation makes the governing clause unroutable and the exception invisible. Fan-out stays at 3 or above, since adjacent clauses in sibling sections are frequently the discriminating comparison. The evidence rule binds hardest here: an internal representation never supports a claim, and every citation resolves to a clause span at a stated source version.

**Software engineering corpora**: Repository, package, module, and symbol containment supplies a reliable structural hierarchy at no summarisation cost, and it should be preferred over any clustered alternative. The structural index often substitutes for retrieval rather than supplementing it, because a symbol lookup is exact where similarity search only approximates. Change rate is the binding constraint: commits invalidate ancestry continuously, so the blast radius bound and the incremental repair path matter more than depth, and a corpus whose repair throughput cannot match its commit rate should be served flat.

**Clinical and biomedical literature**: Queries arrive at materially different granularities, from a therapeutic area overview to a single reported dosage, which is the condition hierarchy addresses best. Cluster levels are useful where publication structure cuts across the questions asked, but membership stability must be gated tightly, since drifting topic boundaries relocate evidence between builds. Summary fidelity gates must treat quantities, units, populations, and negated findings as discriminative terms, because these are exactly what a fluent abstract-level summary compresses away.

**Field service and manufacturing documentation**: Manuals carry deep authored structure with cross-references that do not fit one parent path, so cross-links are maintained beside the containment tree rather than forced into it. Latency budgets are typically strict and connectivity intermittent, so depth is kept at 2 and fan-out narrow, with the flat fallback held locally. Version proliferation across equipment revisions makes the staleness serving rule load-bearing, since routing to a superseded revision produces confidently wrong procedures.

**Customer support and operational knowledge bases**: Daily content change and high query volume favour hierarchy on amortisation grounds while penalising it on maintenance grounds. The usual configuration is one shallow structural level over articles with an extractive representation, since generated summaries would be repaired more often than read. A slice changing faster than repair throughput is routed flat permanently rather than served from a stale ancestry.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small corpora and low query volume**: Serve flat. Below 10,000 leaf passages the candidate reduction hierarchy provides is not worth one additional absorbing failure mode, and build cost rarely amortises. Retain the evaluation set and the failure attribution discipline, which are valuable independently of hierarchy.
- **Large static corpora**: Depth 3 to 4 with structural levels where available, generated representations gated at build time, and a low maintenance budget. Build cost dominates and amortises well, so the fidelity gate can afford regeneration and the ablation suite can afford full level removal trials.
- **Large volatile corpora**: Prefer shallow depth, extractive representations, and containment levels, because every added level and every generated summary multiplies repair cost. Where the re-index trigger fires more often than once per quarter, the corpus is changing faster than the hierarchy earns its cost, and flat retrieval with a strong reranker is the better architecture.
- **High-risk and irreversible-decision domains**: Retain every phase, hold unreachable answer-bearing leaves at 0, widen fan-out rather than narrowing it, and require the flat path to run in parallel as a permanent control rather than as a fallback. Abstention is preferred over an answer assembled from a branch the system cannot show was correctly chosen.
- **Strict latency budgets**: Narrow fan-out and reduce depth rather than removing the descent record, since the record is what makes a later routing failure diagnosable and costs little. Where latency forbids more than one level, serve flat with parent expansion and describe the system accurately as flat rather than as hierarchical.
- **Multi-tenant and access-controlled deployments**: Build policy-homogeneous parents wherever the corpus permits, since a representation summarising children under mixed restrictions cannot be safely shown to the union of their principals. Where mixed parents are unavoidable, assign the strictest restriction of any contributing child and hide the node's existence, label, count, score, and rank from principals lacking that access, since branch existence and result counts are themselves disclosures.

***

## V. Limitations and Considerations

**Routing error is absorbing rather than correctable**: A branch discarded at an upper level removes its entire subtree from consideration, and no downstream component can recover it, because the evidence never enters any candidate set a reranker or generator sees. The consequence is a failure mode flat retrieval does not have, invisible to end-to-end accuracy metrics that report only what was answered. The mitigation is the combination specified in Phases 3 and 4: a fan-out above 1 by default, a bounded backtracking rule, a permanent flat fallback, and the routing loss measurement that quantifies the residual loss rather than assuming it away.

**Upper levels are lossy by construction**: Any representation shorter than its children omits something, and the omitted detail is discovered only when a query depends on it. The consequence is that a fluent, well-formed summary can silently make its branch unroutable for exactly the queries that branch should serve. The mitigation is the deterministic term field attached to every representation, which is not subject to paraphrase loss, together with the child-discriminability gate that tests routability against the node's own children before the node is served, and the mandatory extractive fallback after two failed regenerations.

**The numeric thresholds here are deployment defaults**: The fan-out of 3, the depth ceiling of 5, the 0.90 routing accuracy floor, the 3 percentage point routing loss tolerance, the 5 percentage point hierarchy margin, the 0.95 self-routing recall, the 1 percent stale exposure limit, the 15 percent re-index trigger, and the 90 day amortisation window were chosen to be operable on first deployment. They are not derived from a universal property of corpora, and no single published result establishes them. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute them against its own measured score distributions and observed outcomes at every full rebuild.

**Build cost scales with corpus size and maintenance cost with change rate**: Constructing internal levels costs approximately one model call per internal node plus embedding and clustering compute, and every corpus change invalidates the ancestry above the changed passage. The consequence is that a corpus large enough to need hierarchy is expensive to build and a corpus volatile enough to change often is expensive to keep fresh, and these pressures oppose each other. The mitigation is the amortisation window in Step 1.3, the blast radius bound and bottom-up propagation stop rule in Step 5.2, and the re-index trigger in Step 5.3, which together bound both costs and convert an unbounded repair into a scheduled rebuild.

**Routing loss measurement depends on ancestor labels**: Computing routing loss requires knowing which ancestors were correct for each case, and those labels cost human judgement, must be re-derived whenever the hierarchy is restructured, and can themselves be wrong. The consequence is that this guide's central verification is the most expensive artifact it requires, and deployments under schedule pressure tend to skip it and report end-to-end recall alone. The mitigation is to label a bounded subset, at least 20 cases per served slice, and to treat an unlabelled slice as unmeasured rather than as passing.

**Clustered levels drift and structural levels do not**: Where no source structure exists, levels must be induced, and induced groupings move when the corpus or the random seed changes, relocating evidence and invalidating summaries without any content having changed. The consequence is routing instability that presents as intermittent recall failure and is easily misattributed to the leaf retriever. The mitigation is the membership stability gate at 0.80, seed and training-sample pinning for reproducibility with alternate-seed testing for robustness, and a standing preference for source structure wherever it is reliable.

**Parent representations create an authorization leakage path**: A principal unable to read a leaf may still infer its content from a shared parent summary, a cluster label, a child count, a branch score, or the mere existence of a branch. The consequence is a disclosure that leaf-level access control does not prevent and that ordinary retrieval testing does not detect. The mitigation is to build policy-homogeneous parents where possible, to assign a mixed parent the strictest restriction among its children, to evaluate authorization before routing so forbidden branches never enter a candidate set, and to hide node existence, labels, counts, scores, and ranks rather than filtering them after selection.

**Comparative gain is contingent and can evaporate**: A hierarchy that beat a flat baseline at one release may not at the next, because an improved embedding model, a better chunking strategy, or a corpus change can close the gap that justified construction. The consequence is retained complexity that no longer earns its operational cost while continuing to carry its failure modes. The mitigation is the retirement rule in Step 6.3, which re-runs the comparison at every release and retires a hierarchy or a level that no longer clears its margin, treating removal as a normal outcome rather than as a project failure.

**Structural conformance is not retrieval quality**: A hierarchy can satisfy every checkpoint in this guide, pass every fidelity gate, and still be organised along a dimension that has nothing to do with how questions refer to the corpus. The framework detects malformed structure, lost evidence, and stale derivatives; it does not detect a well-built hierarchy over the wrong grouping. No checkpoint here substitutes for reviewing the grouping basis against the questions the system actually receives.

***

## VI. Conclusion and Summary

Hierarchical index retrieval is a narrowing discipline before it is an indexing technique. Its value comes from scanning a fraction of a corpus while still reaching the passages that answer the question, and its entire risk sits in the branches discarded along the way. A wrong turn at an upper level is absorbing: the correct passages become unreachable, no reranker sees them, and end-to-end accuracy reports only the answers that survived. Flat retrieval carries no equivalent failure, which is why a flat index is the control against which hierarchy must continually justify itself rather than the primitive it replaces.

A team introducing hierarchy should build the flat baseline and the labelled evaluation set first, name the single slice and metric hierarchy is meant to improve, and construct the shallowest structure that could improve it. Levels are admitted one at a time against measured candidate reduction and recall, representations are gated on their ability to route to their own children, and routing loss is computed against oracle routing at every release. A hierarchy that cannot show its margin over the flat path is retired, and retirement is an ordinary outcome of the measurement.

**Key Success Factors**:

- **Flat baseline first and permanently**: The flat index is measured before any level is built, retained as a runtime fallback, and re-compared at every release; a hierarchy is never adopted or kept without a margin measured at equal budgets.
- **Fan-out above one by default**: Premature commitment to a single branch is the principal cause of unreachable evidence, and a declared fan-out with bounded backtracking is the mitigation that the deterministic tier enforces regardless of model preference.
- **Fidelity gated at construction**: Every internal representation is tested for its ability to route queries to its own children, carries a deterministic term field that paraphrase cannot erode, and falls back to an extractive form after two failed repairs.
- **Bounded ancestry repair**: A change invalidates the ancestry above it and nothing more, propagation stops at the first unchanged parent, and a repair exceeding its blast radius becomes a scheduled rebuild rather than an unbounded job.
- **Routing loss measured, not assumed**: Conditional recall under oracle routing is computed alongside actual recall, so evidence lost to routing is separated from evidence lost to ranking and each defect reaches the component that can fix it.
- **Every decision logged with its alternatives**: A descent record naming the branches discarded and the reason for each is what makes a routing failure diagnosable after the fact; a record of the path taken alone is not.

By following this guide, AI agents can build multi-level indexes that narrow large corpora at bounded cost, prove numerically how much evidence the narrowing loses, and retire the structure without regret when a flat index serves the corpus as well.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified during this conversion. The two final entries were located during conversion research rather than taken from the prose source, and are recorded with the titles and locations under which they were found.

**Corpus pointers**:

- `Hierarchical Index Retrieval: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the mechanism taxonomy separating semantic from acceleration hierarchies, the architecture catalogue, the build, descent, expansion, and release loops, the staleness and invalidation model, the failure mode inventory, and the stage-level metrics. Its inline citations supply the external references below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification: archetype, step slot template, and conformance envelope.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — parent guide for retrieval architecture selection: the retrieval contract, the evaluation set and slice discipline, and the selection ladder on which hierarchical indexing is one rung.
- `advanced_task_guides/knowledge-retrieval/guide_GraphRAG.md` — owner of entity graph construction and community hierarchies, per the boundary drawn in Section 1.4.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — rewriting and decomposition, where a sub-question is routed independently in Phase 4.
- `advanced_task_guides/knowledge-retrieval/guide_ModularRAG.md` — module contracts and index release orchestration, for the manifest and rollback machinery in Phase 6.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — bounded retrieval control loops, for the budget accounting governing the descent.
- `advanced_task_guides/knowledge-retrieval/guide_CorrectiveRAG.md` — detecting insufficient retrieval before generation, where a descent leaves a sub-question uncovered.
- `advanced_task_guides/knowledge-retrieval/guide_SelfRAG.md` — adjudicated support verification, for the prohibition on citing an internal representation as evidence.
- `advanced_task_guides/knowledge-retrieval/guide_CodebaseStructureRetrieval.md` — structural retrieval over machine-parseable corpora, for the pattern in Section 4.1.
- `advanced_task_guides/knowledge-retrieval/guide_MultimodalRAG.md` — modality-specific controls where leaves carry tables, figures, or page regions.

**External references**:

*Recursive summary trees and interactive long-document navigation*

1. Sarthi and colleagues, *RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval* — https://arxiv.org/abs/2401.18059
2. Chen and colleagues, *Walking Down the Memory Maze: Beyond Context Limit through Interactive Reading* — https://arxiv.org/abs/2310.05029

*Framework implementations of hierarchical and recursive retrieval*

3. LlamaIndex, *Auto Merging Retriever* — https://developers.llamaindex.ai/python/framework/integrations/retrievers/auto_merging_retriever/
4. LlamaIndex, *Structured Hierarchical Retrieval* — https://developers.llamaindex.ai/python/examples/query_engine/multi_doc_auto_retrieval/multi_doc_auto_retrieval/
5. LlamaIndex, document-summary index API reference — https://developers.llamaindex.ai/python/framework-api-reference/indices/document_summary/
6. LlamaIndex, *Metadata Replacement + Node Sentence Window* — https://developers.llamaindex.ai/python/examples/node_postprocessor/metadatareplacementdemo/
7. LlamaIndex, retriever API reference — https://developers.llamaindex.ai/python/framework-api-reference/retrievers/auto_merging/

*Vector search acceleration structures, distinguished from semantic levels*

8. Malkov and Yashunin, *Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs* — https://arxiv.org/abs/1603.09320
9. Facebook Research, *Faiss indexes* — https://github.com/facebookresearch/faiss/wiki/Faiss-indexes

*Knowledge organization hierarchies*

10. W3C, Miles and Bechhofer, editors, *SKOS Simple Knowledge Organization System Reference* — https://www.w3.org/TR/skos-reference/

*Learned routing, structure-aware indexes, and cheaper internal representations*

11. Gupta and colleagues, *Hierarchical Retrieval at Scale: Bridging Transparency and Efficiency*, whose earlier version circulated under the title *ReTreever: Tree-based Coarse-to-Fine Representations for Retrieval* — https://arxiv.org/abs/2502.07971
12. Chen and colleagues, *Hierarchical corpus encoder: Fusing generative retrieval and dense indices* — https://arxiv.org/abs/2502.18877
13. Wang and colleagues, *BookRAG: A Hierarchical Structure-aware Index-based Approach for Retrieval-Augmented Generation on Complex Documents* — https://arxiv.org/abs/2512.03413
14. Zhao and Yang, *Hierarchical Abstract Tree for Cross-Document Retrieval-Augmented Generation* — https://arxiv.org/abs/2605.00529
15. Yeh and colleagues, *KohakuRAG: A simple RAG framework with hierarchical document indexing* — https://arxiv.org/abs/2603.07612
16. Chen and colleagues, *HC-RAG: Evidence-Centric Retrieval-Augmented Generation over Heterogeneous Financial Filings* — https://arxiv.org/abs/2608.12335
17. Sun, *SVD-RAG: Efficient Tree-Organized Retrieval-Augmented Generation via Singular Value Decomposition* — https://arxiv.org/abs/2607.10316

*Security controls for retrieval systems*

18. OWASP, *RAG Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html

*Incremental maintenance of derived hierarchies, located during conversion research*

19. *EraRAG: Efficient and Incremental Retrieval Augmented Generation for Growing Corpora* — https://arxiv.org/pdf/2506.20963
20. *Cost Scales with Change, Not Corpus Size: Incrementally Maintaining an Evolving Semantic Substrate* — https://arxiv.org/abs/2608.16621
