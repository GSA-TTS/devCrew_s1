---
created: "2026-11-04T23:24:01Z"
updated: "2026-11-04T23:24:01Z"
---

# Evaluation plan: metrics, dataset, baselines, release

Public suites serve comparison and failure discovery; release decisions rest on a private, policy-accurate labeled dataset.

## Metrics

Compute each over a declared time window, environment, tenant class, task class, language, model-host pair, catalog version, index version, retriever configuration and \(k\). \(R_k(q)\) is the top-\(k\) retrieved set, \(G(q)\) the gold-acceptable tool set.

Retrieval-only:
- Recall@\(k\): \(\sum_q |R_k(q) \cap G(q)| / \sum_q |G(q)|\); also report macro recall (mean per-query recall).
- Precision@\(k\): \(\sum_q |R_k(q) \cap G(q)| / \sum_q |R_k(q)|\).
- Hit rate@\(k\): queries with at least one gold tool in \(R_k(q)\), over tool-required queries.
- Complete-set recall@\(k\): queries with \(G(q) \subseteq R_k(q)\), over tool-required queries; use for multi-tool tasks.
- MRR@\(k\): mean of \(1/r_q\), \(r_q\) the rank of the first gold tool at or before \(k\), zero if none.
- nDCG@\(k\): \(DCG@k / IDCG@k\), with \(DCG@k = \sum_{i=1}^{k}(2^{rel_i}-1)/\log_2(i+1)\) and a declared convention when the ideal gain is zero.

Selection and recovery:
- Retrieval miss rate: tool-required decisions with no acceptable tool exposed, over tool-required decisions.
- Selection accuracy conditional on retrieval: decisions selecting an acceptable tool when one was exposed, over decisions with one exposed.
- Wrong-tool-called rate: executed calls whose tool is not acceptable, over executed calls on labeled tasks; report harmful and harmless separately.
- No-tool false-positive rate: gold no-tool tasks that expose or call a non-core task tool, over gold no-tool tasks; report exposure and call separately.
- Re-retrieval rate and re-retrieval recovery rate; \(k\)-escalation rate with success after escalation and added tokens.

Freshness and safety (release target zero for the last three):
- Index staleness per tool: retrieval time minus the latest approved catalog change not yet in the active index; report maximum, \(p_{95}\) and the fraction beyond the freshness objective.
- Catalog coverage: approved active tool versions fully represented in the active index, over those required.
- Deletion leakage rate: queries returning a revoked or deleted version, over queries issued after its revocation.
- Unauthorized exposure rate: candidate exposures violating current entitlement, over candidate exposures.
- Security escape rate: adversarial cases producing unauthorized exposure, disclosure, selection or action, over adversarial cases run (target zero for critical outcomes).

End-to-end and cost:
- End-to-end task success: admitted tasks with all required postconditions verified, over admitted tasks.
- Retrieval-attributable failure rate: failed tasks that pass with the oracle eligible set but fail with retrieved tools, over evaluated tool-required tasks.
- Tokens saved versus the static catalog, same tokenizer, tool-definition plus retrieval-control tokens; also as a percentage of static tokens.
- Cost per verified successful task.
- Latency \(p_{50}\), \(p_{95}\), \(p_{99}\) per stage (eligibility, rewrite, embedding, lexical, vector, fusion, reranking, hydration, total retrieval, end-to-end); do not average percentiles.

## Private labeled dataset

Fields per case: raw request, bounded conversation state, task class, eligible catalog snapshot, acceptable tool set, required complete set, ordered dependencies where they apply, prohibited tools, no-tool label, ambiguity label, expected clarification, end-state verifier.

Case types: exact names, aliases and parameter names; paraphrases, terse and long turns, corrections, pronouns, misspellings, locales; near-neighbour tools differing by scope, data source, write authority, units, region or output; no-tool, unsupported, ambiguous and unavailable-but-related tasks; single, parallel, dependent and iterative multi-tool tasks; new, deprecated, removed, migrated and renamed tools; empty results, low margins, outages, stale or partial indexes, duplicate IDs, cache failures; unauthorized tools, cross-tenant collisions, revoked permissions, region limits; keyword stuffing, poisoned descriptions, homoglyph names, hidden instructions, cross-server shadowing, malicious synthetic queries, graph amplification.

Keep a hidden holdout, time-split cases for new tools and owner-blind review.

## Baselines and ablations

Full eligible static catalog (when it fits); always-on core only; deterministic rules or namespace routing; lexical only; dense only; hybrid without reranking; hybrid with each candidate reranker; raw versus conversation-aware rewrite versus capability hypothesis; fixed versus adaptive \(k\); description-only versus parameter-, example-, synthetic-query- and documentation-expanded indexes; no graph versus dependency expansion; generic versus tool-trained retriever when available. Hold catalog, model, task set, seed policy and execution fixtures constant, and evaluate both against oracle labels and through end-to-end completion.

## Offline tuning loop

Enter for any change to catalog text, synthetic queries, analyzer, embedding model, index parameters, filters, fusion, reranker, query construction, graph, \(k\), provider tool search, model, policy or labels.

1. Freeze candidate and baseline artifacts, versions, test-set digest, model-host pair and budgets.
2. Declare primary and guardrail metrics by risk and task class before running.
3. Run index integrity, authorization, deletion, tenant-isolation and deterministic unit tests.
4. Run retrieval-only tests, then paired end-to-end tests with the retrieved set, the oracle eligible set and the static full catalog; repeat stochastic runs enough to measure pass rate and all-runs reliability.
5. Run adversarial ranking, poisoning, stale-index, outage and recovery cases; any critical unauthorized exposure or action fails the release.
6. Classify errors from paired traces by catalog, eligibility, query, lexical, dense, fusion, reranking, cutoff, selection, invocation, execution or verifier.
7. Change one major variable and rerun the full suite, previously passing cases included.
8. Exit to shadow traffic only when primary metrics pass and every guardrail is noninferior within the declared bound; stop after five tuning iterations without held-out improvement and revisit tool boundaries, labels or architecture.

## Online release loop

1. Shadow mode without changing exposed tools; compare candidate and production sets on the same requests and inspect high-risk disagreements by hand.
2. Canary on an allowlisted, low-risk cohort, invocation still governed by existing policy; randomize at task or tenant level, not per retrieval round.
3. Measure verified success, retrieval miss, wrong-tool call, no-tool false positives, re-retrieval, tokens, latency tails, cost and support corrections, under a predeclared sample or confidence rule and minimum duration.
4. Promote only if safety is noninferior and the primary outcome improves, or stays within a declared noninferiority margin while cost or latency improves.
5. Roll back on any critical unauthorized exposure, deleted-tool return, cross-tenant leak, harmful wrong-tool action, material success regression or budget breach.
6. Cap sequential comparisons at two before returning to offline analysis.

## Public suites (comparison only)

ToolRet (heterogeneous tool retrieval, recall and completeness), ToolBench and StableToolBench (large API catalogs, end-to-end), Meta-Bench (missing-function detection, irrelevance), API-Bank (separates planning, retrieval and calling), BFCL (downstream selection and calling, not large-catalog retrieval), ToolSandbox and ToolHop (stateful and multi-hop use), MCPTox (adversarial tool descriptions). State their limits: stale catalogs, simulated APIs, labels missing valid alternatives, answer-leaking names, English-only data; do not compare scores across different catalog snapshots, candidate budgets, definition formats or evaluator versions.
