---
created: "2026-11-05T00:00:25Z"
updated: "2026-11-05T00:00:25Z"
---

# Evaluation plan: set, metrics, release gates

Material for the Evaluation plan part. Sections 1 to 5 apply to every retrieval design; section 6 adds the comparison each pattern row marked Test against baseline needs.

## 1. Evaluation set

- Fields per case: case ID, query, conversation context, user, tenant and role, expected sources, answer-bearing spans, acceptable answer, required abstention, risk tier, slice labels.
- Case types: positive, negative, ambiguous, unanswerable, stale, contradictory, adversarial (poisoned, unauthorized), multilingual, multi-hop, exact-match, table and multimodal cases; real examples sampled under privacy policy plus synthetic edge cases; hard negatives from the same entity, period or terminology.
- Keep tuning, development and held-out regression sets separate; freeze the held-out set before tuning.

## 2. Retrieval metrics

Recall@k and Hit@k against answer-bearing chunks; precision@k or context precision; mean reciprocal rank; nDCG@k for graded relevance; coverage of required subquestions; duplicate-context ratio and source diversity; access-violation rate (zero in tested cases); freshness lag and stale-hit rate. Report slice values beside averages: an average can hide total failure on identifiers, languages, tenants or high-risk topics.

## 3. Generation and citation metrics

Answer correctness; faithfulness (claims entailed by retrieved evidence); citation precision (cited evidence supports the claim); citation recall (material claims carry citations); abstention precision and recall on unanswerable questions; contradiction and temporal handling; calibration of confidence against correctness. LLM judges are measurement instruments: calibrate them against blinded human labels, measure disagreement and pin judge versions.

## 4. Performance and cost metrics

p50, p95 and p99 latency per stage (planning, embedding, sparse, dense, graph, fusion, reranking, assembly, generation, verification); input, context, output, embedding and judge tokens; cost per request and per successful answer; index build time, update visibility lag and deletion propagation lag; cache hit and false-hit rates; error, timeout, retry and fallback rates.

## 5. Release loop and hard gates

- Stages: unit, smoke, authorization and deterministic retrieval checks; the full offline suite compared with the baseline by slice; shadow traffic; a canary to a small authorized share with automatic rollback.
- At most five tuning cycles on the development set per proposed change; after five, reformulate the hypothesis.
- Initial hard gates: zero access-control violations; zero known citation-to-wrong-source defects in the critical set; no material groundedness regression; no p95 latency budget breach; no stale result beyond the source's freshness objective. Set numeric quality thresholds from task risk and the current baseline, not from vendor claims.
- Red-team before release: indirect prompt injection, hidden multimodal instructions, poisoning, source spoofing, malicious tool descriptions, cross-tenant queries and cache leakage; zero known authorization violations before release.
- Reject a change that improves the average while breaking a security, freshness, high-risk quality or tail-latency gate.

## 6. Pattern comparisons

- Hybrid: sparse-only, dense-only and overlap cohorts on a held-out set; fusion tuned only on the development set.
- Query transformation: raw-query control on every case; per-transformation ablation; unique relevant-hit contribution, Recall@k delta, coverage delta and precision delta per variant; intent-preservation checks on protected spans.
- Corrective: per threshold pair, evaluator precision, recall, macro-F1, calibration error, correction success, over-correction, latency, cost and policy violations, by query class and risk tier.
- Self-reflective: each uncertainty calibrated separately (expected and maximum calibration error, Brier score, negative log likelihood, reliability curves by slice); risk plotted against coverage, not accuracy on answered cases only.
- Agentic: direct lookup, single-pass hybrid, corrective and a deterministic workflow on identical frozen cases; step and trajectory labels, ablations, judge calibration, fault injection and load tests; one frozen regression case per agency failure mode.
- GraphRAG: same corpus, model, token ceiling and authorization policy for hybrid and graph; single-hop, multi-hop, temporal, entity-ambiguous, path-constrained and corpus-global slices; graph-build, summary and query cost, p95 latency, correctness, citation support and graph-quality errors.
- Hierarchical: lexical-only, dense-only, flat hybrid and each proposed hierarchy; leaf Recall@k, answer support, build time, update lag, storage and cost; routing accuracy, reachability, over-pruning, backtracking and per-stage candidate survival; every level compared against removing it.
- Multimodal: text-sufficient and visual-dependent cases labeled separately; answer accuracy, page or region Recall@k, citation precision, groundedness, parse errors, input tokens, cost, index bytes and deletion time; claim checks by modality (table cells and units, chart axes and legend, image region, timestamped clip).
- Modular: component, routing, ablation, interaction, end-to-end, adversarial and load tests against the frozen linear baseline; per-module lift, latency, cost and error contribution; router regret and calibration.
