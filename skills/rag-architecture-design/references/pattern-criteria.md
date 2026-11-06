---
created: "2026-11-04T23:57:57Z"
updated: "2026-11-05T00:03:54Z"
---

# Pattern criteria for the Pattern verdicts table

One entry per row of the table. Each entry gives the conditions behind the Deciding condition column (the use conditions that support Test against baseline, the conditions that make the pattern Not justified) and the Baseline to beat column.

## 1. Hybrid sparse-dense retrieval

- Adopt when: the corpus mixes natural language with identifiers or specialist terminology (names, quotations, product codes, error messages, legal citations, rare terms); hybrid is then the default.
- Test against baseline when: the corpus is plain natural-language text with no such terms. Lexical search (BM25 or equivalent) remains the required baseline for most text corpora and dense embeddings serve paraphrases; keep the fused hybrid only if the target slice improves and all hard gates hold.
- Baseline to beat: lexical-only and dense-only retrieval run separately, each generating with explicit citations and no agent loop.

## 2. Query transformation

- Test against baseline when at least one holds: the query depends on dialogue history (pronouns, ellipsis, omitted entities); spelling, transliteration, jargon or acronym mismatch blocks lexical recall; query and corpus use systematically different terminology; a broad request has several distinct faithful formulations; the request has several independently answerable parts or a multi-hop dependency; typed filters (time, jurisdiction, tenant, document type) can narrow a large corpus without excluding answers; first retrieval shows low answer-bearing recall, no authoritative hit or uncovered required subquestions.
- Not justified when the query is: short, precise and aligned with the corpus; an exact identifier, error code, SKU, citation, file path, API name or quoted string; a name whose spelling is evidentiary; code, a stack trace, a formula or a log line; a direct structured value from a system of record; or the user requests verbatim search, the rewriter cannot run inside an approved boundary, or the retriever already meets the target slice.
- Baseline to beat: the raw query, kept as a control branch.

## 3. Corrective retrieval (CRAG-style evaluate and correct)

- Test against baseline when all hold: initial retrieval quality varies materially by query; retrieval errors cause a measured downstream failure; at least one correction route can add eligible evidence; a labeled set exists or can be built to calibrate the evaluator and actions; added latency and cost fit; the system can trace evidence, enforce budgets and stop or escalate.
- A simplified corrective loop (an LLM judge returning constrained relevance verdicts) fits when the workload is exploratory or low volume, two correction attempts and one approved alternate source are enough, and human review covers high-risk cases.
- Not justified when: a one-pass retriever already meets target quality; every query must use one designated authoritative source; exact data comes from a database, API or knowledge graph; no alternate evidence source exists; external search is the only correction and egress policy forbids it; the corpus, access lists or index lifecycle are broken (repair those first); the evaluator is less reliable than a simple score or source rule; tight latency makes one evaluator call uneconomic.
- Baseline to beat: the one-pass retriever with reranking.

## 4. Self-reflective retrieval (Self-RAG)

- Trained Self-RAG: test against baseline when all hold: retrieval need varies by query or generation segment; some requests benefit from skipping retrieval while others need several acquisitions; segment-level support and utility decisions improve a named failure slice; training data and model-serving control are available; added branch, token and critic cost fits; a calibrated abstention and external-verification path exists.
- Prompt-based (Self-RAG-inspired) loop: fits when the workload is exploratory or low volume, fine-tuning is unavailable, a general model can return constrained critique labels, and independent evidence checks and strict loop limits compensate. Name it prompt-based, not Self-RAG.
- Use a separate verifier instead of self-critique when claims are high impact, regulated, safety-critical or adversarial, when generator and critic share provider or failure modes, or when a deterministic check (database, rules engine, calculator, entailment check) can verify the output.
- Not justified when: every request must retrieve from an authoritative source (use mandatory retrieval plus verification); one retrieval pass already meets the target; latency forbids one extra call; the corpus or retriever is the main defect; a structured lookup gives exact correctness.
- Baseline to beat: one retrieval pass with claim verification.

## 5. Agentic retrieval

- Test against baseline only when all hold: the task needs an unknown or query-dependent sequence of retrieval or tool actions; one-pass hybrid retrieval and the relevant simpler corrective or reflective pattern fail a named, measured slice; intermediate evidence can change the next action; approved tools produce materially different evidence; the system can enforce budgets, persist state, trace trajectories, verify citations, abstain and escalate; expected gain exceeds added latency, cost and attack surface.
- Not justified when: a direct database, API, graph query or calculator yields the answer; one-pass hybrid retrieval meets the gates; poor evidence quality is the main defect and one bounded corrective action can repair it; segment-level critique without novel planning is the need; valid paths are known and a deterministic workflow covers them; strict latency, determinism or audit requirements forbid dynamic paths; no alternate tool or source exists; the system cannot log actions, cap loops or abstain.
- Baseline to beat: one-pass hybrid retrieval, the corrective pattern and a deterministic workflow.

## 6. GraphRAG and graph-backed retrieval

- Test against baseline when at least one graph operation is essential and measurable: questions need two or more evidence-bearing relations across documents with no single chunk holding the answer; typed path constraints, direction, exclusions or temporal overlap; cross-document entity identity materially affects retrieval; users need explainable evidence paths; questions ask for corpus-wide themes or patterns; a governed ontology enables useful expansion; authoritative structured graph data already exists; query volume amortizes extraction and summary cost.
- Not justified when: answers are exact values from a database or graph query (use direct lookup); most questions are single-passage lookups, quotations, definitions or identifier searches; the corpus fits tested long context or in-memory hybrid retrieval; relations are sparse or cannot be extracted with acceptable precision; there is no identity policy, provenance, deletion path or permission model; the corpus changes faster than the graph and summaries can be refreshed; p95 latency or cost cannot absorb graph expansion; the graph would be chunks joined by embedding similarity; a regulated decision would rest on unreviewed extracted assertions.
- Baseline to beat: hybrid retrieval with bounded reranking on the same frozen corpus, answer model, token ceiling, authorization policy and labeled queries. Route only the winning query classes to the graph.

## 7. Hierarchical index retrieval

- Test against baseline when at least one holds and can be tested: many long documents while most queries concern one or a few documents or sections; users ask at materially different granularities; small units are needed for recall but larger parents for interpretation; the source has meaningful structure (book, chapter, section, filing, exhibit); a governed taxonomy supports broader and narrower navigation; a cheap coarse stage can drop irrelevant candidates while keeping relevant leaves; the corpus is too large for flat exact vector search; query volume amortizes summary and clustering cost.
- Not justified when: the corpus fits tested long context; flat hybrid already reaches the required leaf recall and context precision; most queries are identifiers, quotations or rare terms; the hierarchy is arbitrary or unrelated to how questions refer to the corpus; content changes faster than summaries can refresh; one wrong top-level choice is unacceptable and alternate branches cannot be kept; the corpus is small and query volume low; there is no lineage map, deletion path, authorization model or stage-level evaluation set; the proposed hierarchy is only an HNSW setting.
- Baseline to beat: flat hybrid retrieval, kept as fallback and permanent control.

## 8. Multimodal retrieval

- Test against baseline when at least one material answer depends on what text extraction does not faithfully preserve: chart values, table row-column structure or spanning cells, page layout, handwriting, diagrams, formulas, photographs or interface states as primary evidence, speaker identity or timing in audio, actions or order in video; users query by image, screenshot, audio or video; answers need a visual or temporal citation a reviewer can inspect.
- Not justified when: trustworthy digital text and structure already preserve every answer-bearing span; questions are exact identifiers, quotations or clauses; the answer is a structured value from an API or database; images are decorative; original assets, coordinates, authorization state or lineage cannot be retained; personal, biometric, medical or licensed-media policy forbids the derivatives; added rendering, image tokens, storage or p95 latency exceeds the envelope.
- Baseline to beat: an authorization-equivalent text-only pipeline with a validated parser. Name the actual architecture: text retrieval with visual verification, proxy-text multimodal indexing, visual page retrieval, or fused multimodal retrieval.

## 9. Modular composition

- Test against baseline when at least two hold: distinct query classes need different corpora, retrievers, models or verification policies; components must be upgraded or rolled back independently; several teams own separate stages with their own service objectives; experiments must swap one component while holding the rest; the system needs conditional, parallel, iterative, multimodal, multi-corpus or multi-agent retrieval; compliance requires auditable boundaries and source-specific credentials; traffic or cost requires independent scaling.
- Not justified when: one corpus, retriever, prompt and model meet all requirements; there is no labeled evaluation set or observability; the project is a short-lived prototype; the team cannot operate versioned contracts, traces and failure policies; network boundaries would cost more latency and reliability than the module gives.
- Baseline to beat: an in-process linear pipeline with the same typed contracts. Modularize only the stage whose failure, scaling, security or experimentation need is demonstrated.
