# Entity Resolution and Deduplication for Large-Scale Knowledge Graphs

## Key Takeaways

- **Entity resolution (ER) is more than deduplication**: it identifies and links records that refer to the same real‑world entity or the same underlying *claim*, often across noisy and heterogeneous sources.[1][2]
- In a knowledge graph, ER is both a **data quality problem** (avoiding double-counting) and a **semantic problem** (making sure logically equivalent things share an identity while distinct things remain distinct).[3][4]
- Best practice is a **multi-stage, explanation-friendly pipeline**: preprocessing → blocking → matching → clustering/canonicalization, often enhanced with **graph structure** and **LLM-based semantic similarity**.[5][6][7][8][1]
- For EKIs, uniqueness must be enforced at the **semantic-claim level**, not just string equality, while **preserving full provenance for every merged record**.[4]

The sections below expand each of your bullets into a concrete, implementation-oriented view.

***

## 1. Entity Resolution vs Simple Deduplication

### 1.1 Conceptual Distinction

Classical **deduplication** focuses on removing exact or near‑exact copies (e.g., same ID or almost identical records). **Entity resolution**, by contrast, is defined as “identifying and merging records that represent the same real‑world object” across sources, formats, and time.[2][1]

Characteristics of ER:[1][4][2]

- Records may:
  - Use different identifiers.
  - Differ in spelling, abbreviations, and formatting.
  - Have incomplete or conflicting attributes.
- ER must:
  - Decide which records **co-refer** to the same entity.
  - Cluster them together.
  - Produce a **canonical or “golden” representation** (or at least a link structure) that downstream applications can rely on.

In a knowledge graph context, Linkurious and Senzing emphasize that without ER the “graph” is just **disconnected facts**, with duplicate nodes and missing links that undermine analytics and investigations.[3][4]

For your system:

- **Deduplication** is the trivial case: removing exact duplicate documents or EKI records (e.g., same checksum, same normalized text).
- **Entity resolution** is the non‑trivial case: identifying EKIs that express the *same underlying claim* or DataItems that correspond to the *same research artifact* even when titles, metadata, or text differ.

### 1.2 Entity-Resolved Knowledge Graphs

Senzing calls the combination of ER + KG an **Entity‑Resolved Knowledge Graph (ERKG)**:[4]

- At the **data graph level**, every record (raw data record) is present, with full provenance.
- At the **entity level**, records that refer to the same entity are linked to (or merged into) a resolved node.
- The resolved node maintains **full attribution**, i.e., which source records contributed to it, supporting audits and feedback loops.[4]

This model is highly relevant to your EKI uniqueness requirement:

- Think of **EKI clusters** as the entity‑resolved layer:
  - One canonical EKI node per unique claim.
  - Many raw or intermediate statements that contributed to that canonical claim, each with links and provenance.

***

## 2. Beyond Static Keys: Blocking, Matching, and Clustering

Large-scale ER uses a **pipeline**, both in traditional relational settings and in KG/graph-based approaches.[6][7][5][2]

### 2.1 Pipeline Stages

Typical stages:[7][5][6][2]

- **Preprocessing / normalization**:
  - Clean and standardize fields (e.g., case-folding, removing boilerplate terms, normalizing identifiers).
  - For EKIs, normalize claim text (strip formatting, normalize terminology as far as safe).
- **Blocking**:
  - Reduce the O(\(n^2\)) candidate space by grouping potentially matching records into “blocks” based on shared tokens or keys; only compare records within the same block.[5][6][7][2]
- **Matching**:
  - For candidate pairs within each block, compute one or more **similarity scores** or apply classification models (rule-based, ML-based, or LLM-based).[6][7][1]
- **Clustering / canonicalization**:
  - Turn pairwise matches into **clusters** of co‑referent records and define a canonical entity representation (golden record) or maintain an entity node linked to all constituent records.[7][6][4]

For EKIs, this pipeline operates over **extracted claims** rather than people or organizations, but the logic is identical.

### 2.2 Why Entity Resolution Goes Beyond Dedup

ER must handle:[9][2][4]

- *Partial overlap*: records share some attributes (e.g., same DOI or same claim phrasing) but differ in others.
- *Temporal drift*: older records vs newer corrections; same paper but different versions.
- *Conflicts*: two sources asserting different values for the same attribute.

This is why Senzing warns against “trying to approximate ER later inside graph apps”: custom ad‑hoc de‑dup logic in downstream analytics is expensive, error‑prone, and not fit for purpose.[4]

Best practice for your KG:

- Treat **ER as a dedicated step** in your ingestion / EKI creation workflow, with:
  - Clear configuration.
  - Metrics (precision/recall, false merge/split rates).
  - Auditability of decisions.

***

## 3. Graph-Based Blocking and Structural Similarity

Your prompt mentions **graph-based blocking**—a strategy that leverages graph structure to focus comparisons on promising candidates instead of relying only on shared attribute keys.

### 3.1 Graph-Based Blocking Concepts

TigerGraph describes **graph-based blocking** as using graph structure—shared neighbors, label proximity, and structural patterns—to form candidate sets.[10]

Examples:[10][2][5][6][7]

- Two person nodes might be candidate duplicates if:
  - They share many neighbors (same address node, same employer node, same phone).
- Two EKI nodes might be candidate duplicates if:
  - They connect to the same set of KDIs (e.g., same KSI and same ATLAS technique) and similar DataItems.
- Blocking keys can be **derived from graph structure**:
  - E.g., hash of sorted neighbor identifiers, or composite of neighbor types and roles.

Research on graph-based ER shows two main patterns:[5][6][7]

- **Token-based graph ER**:
  - Build a bipartite graph between records and tokens; cluster record nodes that share token nodes, sometimes via clique detection or community detection.[6]
- **Record–record similarity graphs**:
  - Build a graph where nodes are records and edges are weighted by similarity; then prune and cluster.[2][7][5][6]

Papadakis et al. survey approximate blocking techniques and pruning algorithms (e.g., Cardinality Node Pruning, Weight Node Pruning) for such similarity graphs, significantly reducing comparisons while preserving high recall.[2]

### 3.2 Benefits for Your Use Case

For EKIs:

- Blocking only on text similarity might miss semantically equivalent but lexically different statements.
- **Graph-based blocking** can consider:
  - Shared KDIs (same KSI, same ATLAS technique).
  - Shared DataItems (multiple EKIs derived from the same paper segment).
  - Shared context (same threat model, same architecture component).

Practical approach:

- Define **blocking signatures** that mix content and structure, e.g.:
  - [normalized lemma bag-of-words for claim] + [KDI codes] + [data source class].
- Use these to build:
  - Token-based blocks (for lexical similarity).
  - Structural blocks (shared KDI/neighbor patterns).

This enhances recall without exploding the candidate space.

***

## 4. Deterministic, Probabilistic, and Hybrid Matching

### 4.1 Deterministic Matching

Deterministic (rule-based) matching relies on **exact or near-exact patterns**:[11][12][9][4]

- Same DOI or checksum ⇒ same DataItem.
- Same normalized claim hash and same KDIs ⇒ same EKI.
- Same author list + title normalization ⇒ high-confidence DataItem match.

OpenCorporates’ legal-entity KG, for example, combines **deterministic IDs (registry numbers, LEIs)** with probabilistic signals like shared officers or addresses, and insists on logging why each match was made.[12]

Advantages:

- High precision and explainability.
- Critical for compliance, sanctions, and regulatory evidence.[12][4]

Disadvantages:

- Lower recall when data is messy; cannot handle semantically equivalent but not identical fields.

For your KG, deterministic rules are ideal for:

- **DataItems**: DOIs, arXiv IDs, stable URLs, or cryptographic hashes.
- Some EKIs: when the extracted normalized claim and all KDIs match exactly.

### 4.2 Probabilistic / ML-Based Matching

When deterministic keys are unavailable or incomplete, ER uses **probabilistic methods**:[7][6][2]

- Compute feature vectors (edit distance, token Jaccard, numeric distance) for pairs and train models (logistic regression, XGBoost, deep nets) to classify pairs as matches/non-matches.
- Use **thresholds** and calibration to decide merges, with downstream clustering algorithms to enforce global consistency.[6][7]

Graph-based frameworks like FAMER and ModER use similarity graphs and hierarchical clustering for unsupervised ER.[7][6]

For EKIs:

- Features may include:
  - Text embeddings (cosine similarity).
  - Overlap in KDIs, DataItems, and provenance.
  - Structural similarity (graph neighbor overlap).

Best practice:

- Use **probabilistic scores** as a second layer:
  - Deterministic matches first.
  - Statistical models to expand recall, with human review thresholds where stakes are high.

***

## 5. LLM-Based and Semantic Entity Resolution

### 5.1 LLMs for Entity Matching

Recent work shows that **LLMs can significantly improve entity matching performance**, especially for complex, text-heavy records:[13][14][8][1]

- LLMs can:
  - Interpret unstructured descriptions, synonyms, abbreviations.
  - Reason about semantics across multiple fields at once.

The paper “Match, Compare, or Select?” investigates LLM-based entity matching strategies:[1]

- **Matching**: independently classify each pair as match/non-match.
- **Comparing**: have the LLM compare two candidate records jointly to decide which one matches a reference better.
- **Selecting**: given a reference and multiple candidates, have the LLM select the best match globally.

Findings:[1]

- Incorporating **record interactions** (comparing/selecting) yields better performance than independent pairwise classification.
- Their composite framework (ComEM) that combines strategies and LLMs improves both **effectiveness and efficiency**.

### 5.2 Semantic ER for Knowledge Graphs

Emerging “semantic entity resolution” for KGs focuses on cases where the graph itself is built from unstructured text via LLMs:[8][13]

- Each node or EKI may be the result of a generation step.
- Semantic ER uses **type-aware prompts and context** from the graph to merge records with similar semantics, not just similar strings.[13][8]

Best practices from these efforts:[14][8][13]

- Use LLMs **inside a structured pipeline**:
  - Blocking via cheap lexical/structural methods first.
  - LLMs applied on *shortlisted candidates* only, to stay cost-effective.
- Log **why** LLMs recommended a match (e.g., include a rationale string or structured explanation in the EKI provenance), similar to rule IDs in rule-based systems.[14][12]
- Treat LLM decisions as **proposals**, subject to:
  - Thresholds.
  - Human review in high-impact domains.
  - Graph-level consistency checks (e.g., 1–1 matching constraints, no contradictory merges).[15][1]

For EKIs, LLM-based ER is particularly attractive because:

- EKIs are textual and conceptual.
- LLMs can identify that “FedRAMP KSI-02 requires continuous monitoring of ML assets” and “Continuous AI system monitoring is mandated under FedRAMP KSI‑2” express the *same* claim under similar scope.

### 5.3 Cluster Repair with LLMs

Even with good pipelines, ER clusters can be **over-merged or under-merged**. Recent work combines **graph metrics and LLMs for cluster repair**:[15]

- Use graph metrics (e.g., centrality, cluster density) to detect suspicious clusters.
- Use LLMs to inspect cluster members and propose splits/merges.

This suggests a powerful pattern for your KG:

- Periodically perform **“EKI cluster audits”**:
  - Find anomalous EKI clusters (too heterogeneous, conflicting KDIs or claims).
  - Use LLMs plus provenance signals to suggest corrections.

***

## 6. Uniqueness Policy for EKIs

Your requirement is that **EKIs must be unique—no duplicated or even similar EKIs**. Applying ER best practices, this becomes a **policy and modeling** question, not just a matching algorithm.

### 6.1 What Counts as “Same EKI”?

For EKIs (claims), two candidates might be:

- **Exact duplicates**:
  - Identical normalized claim text and identical KDIs.
- **Strict semantic equivalents**:
  - Different wording but same underlying proposition and scope (e.g., same risk, control, conditions).
- **Similar but distinct**:
  - Same topic but different scope, conditions, or modality (e.g., “reduces risk” vs “eliminates risk”; general vs specific cases).

Best practice:

- Define **EKI equivalence criteria** that include:
  - Normalized text similarity (embedding + lexical).
  - Same KDIs (or compatible subset/superset).
  - Same polarity (support vs challenge).
- Define multiple bands:
  - “Must-merge” (strong equivalent).
  - “Candidate-merge” (review required).
  - “Related-but-distinct” (link via `RELATED_TO` rather than merge).

### 6.2 Canonical EKI vs Cluster of Variants

To preserve provenance and editorial nuance while enforcing uniqueness, consider a two-level model:

- **Canonical EKI node**:
  - Represents the unique, normalized claim.
  - Has properties for canonical phrasing, claim type, domain anchors (KDIs), etc.
- **EKI variant nodes** (optional, depending on scale):
  - Each variant is linked to the canonical EKI via `VARIANT_OF`.
  - Variants carry:
    - Original text.
    - Source (DataItems).
    - Extraction method.
    - Confidence, timestamp.

ER then becomes the process of *assigning EKI variants to canonical EKIs* (or creating new canonical EKIs when no match exists).

This respects both:

- **Uniqueness** at the canonical level.
- **Evidence richness** and textual diversity at the variant level.

You can implement this in a pure single-level graph (just collapsing nodes), but the explicit two-level design tends to be easier to reason about.

***

## 7. Provenance-Aware ER: Never Lose Source Links

Senzing emphasizes that in an entity-resolved KG, each resolved entity must maintain **full attribution**, i.e., a mapping back to each source record and system key it represents.[4]

Best practices:[3][12][4]

- Never drop provenance when merging:
  - The resolved EKI should link to all DataItems and extraction Activities from which any of its prior variants were derived.
- Log **why** each merge occurred:
  - Which rules fired, which ML model scored the match, which LLM verdict was used.[12][14]
- Distinguish:
  - **Merging** (unifying identifiers).
  - **Linking** (e.g., `EQUIVALENT_TO`, `SIMILAR_TO` edges) when full merge is not justified.

For EKIs in a safety-critical cybersecurity context, a conservative approach is warranted:

- Err on the side of **not merging** when semantics or scope are ambiguous.
- Use explicit relationships (`RELATES_TO`, `IS_BROADER_THAN`, `SUPPORTS`) to capture proximity without conflating claims.

***

## 8. Where to Perform ER: Before or Inside the Graph?

Senzing notes that ER can be applied either:[4]

- **Before the graph**:
  - Resolve entities in the data layer, then ingest resolved entities into the KG.
- **Inside the graph**:
  - Ingest raw records into a “data graph” and run ER over the graph structure.

Their guidance:[4]

- Either architecture can work, but approximate ER done ad‑hoc later inside graph applications tends to be costlier and less reliable.
- Best practice is:
  - Treat ER as a **first-class, well-governed component** of your pipeline.
  - Maintain both the **raw data graph** and the **entity-resolved layer** so analysts can trace back to original records.

For your 4-layer design:

- ER for **DataItems**:
  - Likely best done at or just after ingestion (ETL layer), using deterministic + probabilistic rules.[11][4]
- ER for **EKIs**:
  - Needs graph context (KDIs, provenance, previous EKIs), so best performed **within the KG**, but as a dedicated, well-defined step:
    - New EKI candidates → blocking → LLM/ML matching → cluster assignment/canonicalization → updated links/provenance.

***

## 9. Practical Guidelines for Your EKI ER Design

Bringing this into concrete guidance for your system:

- **Define EKI equivalence types**:
  - Exact duplicate.
  - Strong semantic equivalent (same claim, scope).
  - Related but distinct (keep separate; add `RELATED_TO` or `REFINES` edge).
- **Implement a multi-stage ER pipeline**:
  - Preprocess and normalize EKI text.
  - Block using:
    - Lexical signatures (stems/lemmas, key phrases).
    - Graph structure (shared KDIs, shared DataItems).[10][5][2][6][7]
  - Match candidate pairs via:
    - Deterministic rules (e.g., same DOI + same normalized claim).
    - Probabilistic models over features (string similarity, embedding similarity, structural overlap).[2][6][7]
    - LLM-based semantic comparison and selecting for hardest cases.[8][13][14][1]
  - Cluster and canonicalize:
    - Build an “EKI similarity graph” and cluster records into canonical EKIs.
    - Use graph metrics + LLMs periodically to repair clusters.[15][7]
- **Make ER explainable and provenance-friendly**:
  - Log which rules or models led to each merge.[14][12][4]
  - Ensure every canonical EKI retains links to all contributing DataItems and Activities.
- **Establish governance and review**:
  - Thresholds for automatic merges.
  - Queues for human review in ambiguous or high-impact cases (e.g., critical security guidance).

If implemented this way, your EKI layer becomes **semantically clean, provenance-rich, and scalable**, enabling reliable graph algorithms and AI agents without the distortions caused by duplicates or over-merging.

[1](https://arxiv.org/html/2405.16884v2)
[2](http://www.vldb.org/pvldb/vol9/p684-papadakis.pdf)
[3](https://linkurious.com/blog/entity-resolution-knowledge-graph/)
[4](https://senzing.com/entity-resolved-knowledge-graphs/)
[5](https://aclanthology.org/W13-5010.pdf)
[6](https://thesai.org/Downloads/Volume13No9/Paper_1-ModER_Graph_based_Unsupervised_Entity_Resolution.pdf)
[7](https://arxiv.org/pdf/2112.06331.pdf)
[8](https://blog.graphlet.ai/the-rise-of-semantic-entity-resolution-45c48d5eb00a)
[9](https://www.reddit.com/r/dataengineering/comments/1k8dmdp/have_you_ever_used_record_linkage_entity/)
[10](https://www.tigergraph.com/glossary/entity-resolution/)
[11](https://www.falkordb.com/blog/how-to-build-a-knowledge-graph/)
[12](https://blog.opencorporates.com/2025/10/01/legal-entity-knowledge-graphs/)
[13](https://towardsdatascience.com/the-rise-of-semantic-entity-resolution/)
[14](https://tilores.io/content/Can-LLMs-be-used-for-Entity-Resolution)
[15](https://dl.acm.org/doi/10.1145/3735511)
[16](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_3fea1735-a8ad-4396-891a-1a8fed03d040/1592f948-26a4-4e54-ab38-d9248f8ecb8a/prompt_context.txt)
[17](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_3fea1735-a8ad-4396-891a-1a8fed03d040/3a973b45-ab29-4350-bec4-1078d015344b/2008.07863v1_metadata.json)
[18](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_3fea1735-a8ad-4396-891a-1a8fed03d040/212b25f9-e567-4815-b258-a356736d83e0/2504.00441_metadata.txt)
[19](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_3fea1735-a8ad-4396-891a-1a8fed03d040/9c991d75-fa25-4889-8bfa-e7fc9cbbd050/README.md)