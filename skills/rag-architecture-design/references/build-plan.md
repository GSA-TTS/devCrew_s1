---
created: "2026-11-04T23:58:58Z"
updated: "2026-11-05T00:09:42Z"
---

# Build plan: contract, tier and baseline stages

Material for the Build plan part. Sections 1 to 7 are the baseline stages, written in this order; section 8 covers the paths that need no retrieval index.

## 1. Contract

- User task, answer form, source boundaries, authority hierarchy, freshness objective, privacy classification and access model.
- Maximum p95 latency, cost per answer, context tokens, retrieval rounds and tool calls.
- What counts as a material claim and when the system must abstain.
- Success, security and failure metrics, defined before selecting tools.

## 2. Infrastructure tier

Mark each dependency available, provisionable, requires approval or unavailable, then pick the tier.

- No persistent infrastructure: bounded local files or already-authorized URLs read at request time, lexical or in-memory matching, full corpus in context when it fits, a temporary in-session embedding index. For exploration, one-off research, fewer than roughly hundreds of modest documents, or low query volume. Not when persistence, concurrency, low latency, strict deletion, tenant isolation, high recall or continuous freshness is required.
- Minimal production (the default tier): source connector or ingestion job; parser that keeps headings, page numbers, tables and metadata; chunking with stable IDs; one embedding endpoint pinned by name and version; one index with vector search and metadata filtering; a lexical or full-text index when identifiers, names, codes, quotations or rare terms matter; rank-based fusion (RRF); one reranker when first-stage precision is insufficient; citation-constrained generation; a small version-controlled evaluation set and harness; structured logs and traces; a refresh job with deletion support.
- Full or high-assurance: add a component only when its need exists, for example a graph store when path queries or ontology constraints are first-class, a model gateway with budgets and redaction, an evaluation service with CI gates, change-data-capture ingestion with blue-green reindexing, a policy decision point for document- and chunk-level authorization.

## 3. Corpus and provenance

- Per source: identity, type, owner, authority tier, license; tenant, access principals, classification, personal-data labels, retention; created, updated, ingested and validity times; content hash, source and parser versions, language; parent-child links, page or timestamp bounds, section path, modality.
- Ingestion: approved sources and authenticated connectors only; validate type, size, malware status and hash; parse to a canonical form keeping the original; keep structure, tables, captions and page coordinates; deduplicate exact copies by hash and near-duplicates by a reviewed threshold; extract security labels before chunking; derive stable document and chunk IDs from source identity, version and offsets; quarantine malformed or policy-violating documents; make deletion reach every derivative (indexes, graph, cache, evaluation samples).
- Ingestion validation loop: parse and index a stratified sample and check counts, parse success, access-list coverage, chunk sizes, duplicate rate and provenance; at most two automated repair attempts, then quarantine the source and request human review. Initial hard gates: 100% required access fields, 100% stable source links, zero known cross-tenant collisions, at least 99% parse success for supported formats.

## 4. Chunking

Chunking is an experimental variable.

- Fixed-size: homogeneous documents, weak structure, a baseline; start around 300–800 model tokens with 10–20% overlap and tune. Not as the final strategy when chunks split clauses, tables, code units or headings from bodies.
- Structure-aware: sentence, paragraph, heading, section, slide or table boundaries when structure is reliable; attach the section path and page or line coordinates.
- Parent-child or sentence window: index small units, expand to a bounded parent or neighbouring sentences when facts need nearby definitions or exceptions; cap expansion by tokens and stop at section boundaries.
- Semantic chunking: weak formatting with detectable topic shifts; compare against structure-aware and fixed baselines.
- Contextual or late chunking: contextual descriptions when passages hold pronouns or local terminology (store generated context apart from quoted source text); late chunking when a long-context embedding model can encode the whole document.
- Multi-representation: titles, answerable questions, summaries or entities indexed beside the original when user language differs from source language; generated representations are never cited.
- Acceptance: evaluate at least three candidate configurations on a labeled query set; select the smallest that meets target Recall@k while controlling duplicate context, context tokens, ingestion cost and p95 latency; reject one that improves average recall but harms critical slices (identifiers, multilingual, tables, recent updates, access-controlled documents).

## 5. Retrieval methods

- Lexical (BM25 or equivalent) for names, quotations, codes, error messages, citations and rare terms.
- Dense embeddings for paraphrase and natural-language questions; shortlist models from broad benchmarks, then test on domain data; change the model only with a versioned reindex.
- Hybrid: retrieve sparse and dense independently, keep raw ranks and scores, fuse with reciprocal rank fusion when score scales differ; tune fusion only on the development set.
- Structured filters and routing: typed filters for tenant, time, jurisdiction, language and security labels; exact computations to databases or APIs, relationship questions to a graph, semantic questions to text retrieval. Do not infer a restrictive filter from weak evidence.
- Multi-vector or late interaction only after a confirmed first-stage recall failure.

## 6. Reranking and context assembly

- Reranker: cross-encoder for highest precision on a modest pool (often 20–100 chunks); late-interaction for larger pools; listwise LLM reranking only when domain reasoning is essential and its risks are controlled; deterministic rules for authority, validity and access before model scoring. Do not rerank thousands of candidates.
- Assembly order: remove inaccessible, expired, quarantined and invalid-version chunks; deduplicate; group by source and keep diversity when corroboration matters; expand only the needed parent or window; keep both sides of a material contradiction; allocate tokens by subquestion; order so the strongest evidence is not buried mid-context; attach a citation key to every evidence unit; delimit evidence from instructions and mark it untrusted.
- Authorization is enforced before ranking and again before context assembly, never only after generation.
- Compression only for relevant but verbose evidence; not for legal clauses, safety constraints, numeric tables or code without a verified lossless form.

## 7. Generation, verification and loop limits

- Generation cites original evidence at claim level; generated summaries, rewrites, hypothetical documents and graph inferences are never cited as sources.
- Generation-verification loop: split the draft into atomic claims, map each to citation keys, check entailment, authority and contradiction; retrieve once more for unsupported material claims and regenerate only the affected passage; two verification rounds; then every material claim is supported, qualified or removed, or the system abstains with the evidence bundle for human review.
- Retrieval refinement loop: round 1 faithful standalone query with hybrid retrieval and reranking; round 2 one transformation chosen by diagnosis; round 3 wider authorized sources or approved tools; at most three rounds and two generated variants per round by default; after round 3 answer only the supported parts and state the missing evidence.
- Every loop: charge calls to per-request token, money, time and tool-call budgets; stop on repeated plans or chunk sets, no new authoritative evidence, or falling groundedness; retrieved text never changes limits, tools or destinations.

## 8. Paths without a retrieval index

- Structured lookup: query the system of record and return the record with its provenance; the generator does not rediscover it from prose.
- Long context: the authorized input fits below a tested occupancy threshold, initially 50–70% of the context limit after reserving output and system tokens; the corpus is stable for the request; position-sensitivity tests pass. Compare against retrieval on tokens, time to first token, latency, cost, citation precision and worst-slice reliability.
- Core plus search route: load a small authoritative core in full and search the larger corpus on demand.
- Parametric route: record the target fact, risk tier, allowed routes (parametric, retrieved, parametric plus retrieved, abstain), attempt limits and the evidence-gain definition; route current, private, high-impact, disputed or source-required claims to retrieval or a system of record.
