---
created: "2026-11-04T23:59:27Z"
updated: "2026-11-05T00:03:54Z"
---

# Pattern components for the Build plan

For each pattern marked Adopt or Test against baseline, the build choices to name and the default loop limits stated for that pattern. A default limit is raised only from measured marginal-gain evidence.

## Query transformation

- Query contract before any rewrite: original query, relevant turns, goal and answer form, protected spans (quotes, identifiers, names, numbers, dates, units, code, paths), positive and negative constraints, tenant and authorization scope, jurisdiction, language, freshness, ambiguities, risk tier, maximum variants and calls.
- One primary transformation per diagnosed mismatch:
  - Conversational dependence: standalone rewrite resolving only the needed history; branch or ask when referents are ambiguous.
  - Spelling or encoding: lossless normalization; search original and corrected forms when unsure; never correct identifiers or names.
  - Vocabulary mismatch: controlled-vocabulary or acronym expansion first, then pseudo-relevance feedback (RM3-style), then LLM term expansion as typed facets; document expansion (doc2query) is an ingestion option when offline cost is acceptable.
  - Zero-shot dense mismatch with no labels: HyDE, with the lexical branch kept; reject variants adding unsupported names, numbers or dates.
  - Several faithful formulations: multi-query fan-out of the raw query plus no more than three transformed variants, fused with RRF and route labels, with a per-family contribution cap.
  - Typed constraints: filters for time intervals, numeric ranges, jurisdiction, document type; relative dates resolved against an explicit anchor and timezone; negation kept as an explicit predicate.
  - Multi-hop or compound: decomposition with stable subquestion IDs, dependencies and join rules; dependent subquestions run serially.
  - Missing bridge concept: step-back query retrieved beside the original, never instead of it.
- Defaults: one normalization repair, one routing revision, three transformed variants plus raw, two feedback rounds, eight required subquestions, dependency depth four, one cache revalidation.
- A transformation cache key never uses query text alone; it includes tenant, authorization fingerprint, policy, rewriter and index versions.

## Corrective retrieval

- Keep four judgments separate: passage relevance, evidence sufficiency, source admissibility, action utility.
- Evaluator choice: a fine-tuned discriminative evaluator for high volume or controlled weights; an existing cross-encoder when its scores separate the action classes, with a calibration layer; a calibrated classifier when features beyond text matter (rank gaps, authority, freshness); an LLM judge with a versioned verdict schema for low-volume prototyping; a cascade sending only an uncertainty band to the LLM or a human.
- Thresholds: sweep lower and upper thresholds on the development set and choose the least expensive pair that meets all hard gates. Published paper thresholds are reproduction settings, not production values.
- Actions: Correct (refine passing documents into strips, then a sufficiency check), Incorrect (drop failed passages, diagnose, choose the least risky correction), Ambiguous (refine internal evidence plus at most one alternate route).
- One primary correction per attempt: faithful rewrite, decomposition, one changed retrieval parameter family, an approved secondary index, strip refinement, structured lookup, approved web search after internal routes, or human escalation. Never widen authorization or tenant scope to improve recall.
- Defaults: two correction attempts, two query variants per attempt, one external search route, three total retrieval calls. Stop when the state repeats, two attempts add no authoritative evidence, or any budget is exhausted.

## Self-reflective retrieval

- Roles: generator proposes claims; critic scores retrieval need, relevance, support and utility; verifier checks atomic claims against evidence or deterministic tools; a policy layer enforces authorization, budgets and abstention. Prefer different model families or deterministic tools for generator and verifier when shared failure is costly.
- Force retrieval for current facts, citations, access-controlled facts, user-specific records, high-risk advice or an authoritative source.
- Calibrate retrieval-need, evidence, support and answer uncertainty separately; no single self-reported confidence number.
- Claim labels: supported, partially supported, unsupported, contradicted, not verifiable.
- Defaults: three retrieval rounds, two generated query variants per round, one alternate source route; six segments and beam width two as a conservative reproduction baseline; two repairs per segment.

## Agentic retrieval

- Control architecture: single-agent router (shallow decomposition, finite action set); ReAct-style (next action depends on the latest observation; not for long trajectories); plan-and-execute (separable subquestions, parallel fan-out); deterministic graph or state machine (known states, regulated or high-risk workflows); hybrid bounded-agent graph, where a planner selects approved subgraphs (the default production recommendation); multi-agent only when role separation or parallelism shows incremental value.
- Plan object: subquestions with IDs, required, optional or exploratory status, dependencies, admissible evidence, join rule and unresolved outcome; validate coverage, acyclicity and total budget before execution.
- Tool selection order: authorization and data class; exact system of record before unstructured retrieval; authority, freshness and modality; remaining budgets; expected evidence gain per unit cost.
- Defaults: two plan revisions, eight required subquestions, two retrieval rounds per subquestion, one alternative tool route, two verification rounds, two conflict rounds, one automated escalation attempt; reserve time and tokens for final verification.
- Failure modes to test: goal drift, plan lock-in, premature convergence, over-retrieval, tool thrash, context rot, citation laundering, memory poisoning, budget gaming.

## GraphRAG

- Competency questions first, each with a gold graph pattern and the source span that must support the answer.
- Semantics: schema-free extraction for exploring; ontology-constrained extraction for stable identity and governed relations; a two-layer raw plus canonical model when both matter. RDF/OWL when global identifiers, vocabulary reuse or formal entailment are first-class; a labeled property graph when traversal, Cypher and graph algorithms dominate.
- Every relation assertion keeps source span, source version, confidence, valid time and transaction time; entities are never merged on matching labels alone.
- Retrieval: exact IDs and aliases first, then lexical and embedding seeds; one-hop neighbourhoods for direct relations and two or three hops for tested multi-hop questions, with fan-out and hub controls; local search for entity-centric questions, global search only for corpus-wide sensemaking; hybrid graph and text fusion by default when the graph was extracted from text.
- Answers cite source passages, not community reports or inferred paths.
- Defaults: three traversal rounds and three hops, stricter for dense graphs.

## Hierarchical index retrieval

- Simplest first: source structure before invented clusters; sentence window or parent-child before recursive summary trees; document summaries before multi-level cluster summaries; taxonomy or temporal navigation only for queries that express those semantics; HNSW, IVF and product quantization are serving choices, not a semantic hierarchy.
- Options: document-summary index over chunk indexes (keep several candidate documents when routing confidence is low); parent-child; sentence window; auto-merging; RAPTOR-style trees only when cross-chunk synthesis fails with the simpler options; table-of-contents routing for books; metadata routing across corpora with top-n kept at low confidence; multi-stage cascades with a recall target per stage.
- Summaries, cluster labels and routing descriptions route but are never cited; a summary over mixed-policy children takes the strictest policy of its children.
- Keep the flat hybrid path as fallback.

## Multimodal retrieval

- Classify each asset first: digital text page, scanned page, handwritten page, mixed page, screenshot, table image, audio, video, unsupported.
- Representation by diagnosed failure: parse then embed for digital-native documents; single-vector screenshot embedding (DSE-style) when page-level recall suffices; multi-vector late interaction (ColPali-style) when evidence is local or small; an end-to-end visual path (VisRAG-style) when parsing loses key content; multi-page visual retrieval (M3DocRAG-style) for cross-page evidence; proxy text (OCR, captions, table-to-text, transcripts) when queries are textual. Modality-specific encoders with rank fusion are the default safe choice.
- Tables keep row, column, header and footnote addresses; charts keep axes, legend and caption; audio and video units keep timestamps.
- Citations name the page region, table cells or timestamp interval; generated captions and transcripts are never cited as the original.
- Defaults: three automated parse attempts per page and no more than two engines beyond the default; three routing decisions and four active modality routes per request.

## Modular composition

- Module contract: identity and versions; request context (tenant, authorization scope, deadline); closed input and output schemas with provenance and score semantics; control (timeout, retries, budgets); error classes; security (data class, egress, logging); compatibility.
- A replacement is plug-compatible only after contract, security, golden-case, quality, latency and rollback checks pass.
- Topology: linear, conditional, branching, looping or a bounded hybrid, with joins, fallbacks, loop limits and cycle detection declared in an immutable manifest; a deterministic DAG when valid paths are known; agentic control when step count cannot be known in advance; a hybrid where an agent picks from approved subgraphs.
- Fallback chains defined before release (dense to lexical, reranker to fused rank, remote corpus to a recent authorized snapshot); never fall back from an access-controlled corpus to model memory.
