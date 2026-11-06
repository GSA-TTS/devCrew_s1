---
created: "2026-11-05T00:28:39Z"
updated: "2026-11-05T00:31:39Z"
---

# Reasoning methods: failure map, fit, own gates, caps and pre-release items

Each Own gates line names the gates that get a row of their own; none means only the general gates apply.

## Failure map

Match the observed baseline failure to the smallest intervention.

| Observed failure | Route |
|---|---|
| Missing current, proprietary or citable facts | Retrieval with provenance first; no reasoning method replaces it |
| Arithmetic, date logic, data transformation, symbolic or algorithmic work | Deterministic function, or program-aided reasoning in a sandbox |
| Short sequential derivation | Chain-of-thought (zero-shot or few-shot) |
| Omitted prerequisites, lost intermediate values, failure on longer compositions | Least-to-most |
| Stochastic path errors on answers that can be normalized and compared | Self-consistency |
| Early choices lead to different futures and recovery matters | Tree-of-thought |
| Partial results must merge, feed several consumers or be invalidated | Graph-of-thought |
| The right strategy is missed, several decompositions or search policies are plausible | Forest-of-thought |
| A hidden governing rule, or a retrieval query too specific for the corpus | Step-back |
| Missing strategy, unfamiliar surface form, sparse demonstrations, need for cross-domain insight | Analogical |
| A recurring task family where a validated procedure likely exists | Buffer of thoughts |
| Latency on multi-part answers whose points are independent | Skeleton-of-thought |
| The answer needs search, database access, code execution or other tools | ReAct |
| Defects a rubric can identify | Self-refine |
| Unsupported claims in fact-dense output | Chain-of-verification, preferring retrieval or deterministic tools to self-verification |

## General pre-release items (every method)

- Direct baseline and the proposed configuration evaluated on the same immutable dataset, paired and budget-matched.
- The chosen technique has a documented failure hypothesis.
- Every loop has entry, exit and cap conditions.
- Critical claims have external verification.
- Traces hold versions, seeds, tokens, costs, latencies, retries and candidate links; raw content capture follows privacy policy.
- Tool and code execution are sandboxed; prompt-injection tests pass.
- Robustness is reported across seeds and perturbations.
- Rollback is immediate and tested.

## Chain-of-thought

- Use when: a conventional, non-reasoning model faces a genuine multistep task. Zero-shot: state the objective, constraints and required output and ask the model to reason before answering; prefer an outcome-oriented instruction (work through the dependencies, verify the result, return the output) over demanding a transcript. Few-shot: when the task has a stable reasoning grammar that examples can demonstrate; demonstrations are correct, diverse, close to deployment inputs and stored as versioned data.
- Not when: direct retrieval, fixed-schema extraction, simple classification, stylistic rewriting, or a calculation a deterministic function handles. No few-shot when examples leak labels, teach brittle shortcuts, consume the context needed for evidence, or conflict with the target format. On a reasoning model, explicit chain-of-thought is redundant when the application needs only the answer, and a think-step-by-step cue may hinder it.
- Own gates: none.
- Caps: malformed-output retry count (to set).

## Self-consistency

- Use when: answers can be normalized and compared, candidate errors are partly independent, and higher latency is acceptable. Normalize units and formats and group equivalent answers before aggregating.
- Not when: agreement would be taken as correctness; correlated candidates can agree on the same misconception, so high-stakes outputs need an external verifier.
- Own gates: none.
- Caps: preregister the agreement threshold before sampling; start with three candidates; expand to five or more only if agreement is below the preregistered threshold and the Budget Gate permits. Exit when the leading answer's agreement exceeds the threshold and passes verification; otherwise abstain, retrieve more evidence or escalate.

## Least-to-most

- Use when: the baseline fails because it omits prerequisites, loses track of intermediate values or cannot generalize to a longer composition; the task has two or more answerable subproblems; verified earlier answers materially simplify later ones; and a mostly acyclic dependency order exists.
- Better alternative: plain chain-of-thought for a few tightly coupled steps; self-consistency when complete attempts are cheap and decomposition is unstable; tree-of-thought for branching; graph-of-thought for merges; a fixed workflow graph for predetermined operations; a reasoning model when one response passes verification without explicit state; parallel decomposition and aggregation when nearly all nodes are independent; successive prompting when each answer reveals the next question.
- Own gates: Decomposition-Need Gate (the use-when conditions above).
- Default caps: twelve subproblems, depth four, three decomposition candidates, two validation repairs, two global re-decompositions, one malformed-output retry, two assembly repairs, thirty-two model calls, twenty tool calls, sixty thousand total tokens, 120 seconds, and cost no greater than five times the direct baseline or a lower absolute limit. Tighten by task; raise only through pre-run policy.
- Pre-release items: the task genuinely has useful prerequisites; every externally checkable subproblem names its permitted evidence and a verifier stronger than self-assertion, otherwise it gets human review or is not load-bearing; only hard dependencies are serialized and ready independent nodes execute in parallel; decomposition and solver prompts are separately versioned; every node and edge is typed; dependency execution is acyclic; descendants cannot consume unverified or stale results; cache keys include dependency, evidence, model, prompt, policy and authorization versions.

## Tree-of-thought

- Use when: early choices create materially different futures, errors can be recovered by backtracking, a partial state exposes useful information, more than one route deserves exploration, and a value function, constraint checker, simulator or terminal test can distinguish progress.
- Not when: the task is essentially linear, the first answer already passes an external verifier, intermediate states cannot be scored, or latency must stay near one model call.
- Better alternative: plain chain-of-thought when decomposition is sequential and backtracking rarely changes the result; self-consistency when complete attempts are cheap, final answers can be normalized or verified, and partial-state scoring is unreliable; best-of-N when there are no useful shared prefixes or independent diversity matters more than guided exploration.
- Own gates: Search-Need Gate (the use-when conditions). Evaluation Gate: the evaluator ranks sibling states better than chance, its score correlates with eventual success on held-out tasks, and an external terminal verifier exists; intrinsic self-correction is not sufficient; if no useful evaluator exists, use independent sampling plus human or external verification, or abstain. Privacy Gate: redact sensitive spans and store compact structured summaries. Tool-Safety Gate: any tool action passes typed argument validation, authorization, rate limits and confirmation independently of its node score.
- Caps: fix maximum generated nodes, evaluated nodes, depth, children per expansion, simultaneous calls, model tokens, tool calls, wall time and currency cost before execution (each to set unless the user gives it); refuse a configuration whose worst-case authorized spend exceeds the task contract.
- Pre-release items: beats direct, plain chain-of-thought, reasoning-model, self-consistency and best-of-N alternatives on paired, budget-matched data; the task has a canonical state and legal transitions; evaluator top-k recall and calibration meet thresholds; terminal success is externally verified; concurrency cannot overspend.

## Forest-of-thought

- Use when: failures come from missing the right strategy rather than executing one known strategy poorly, several decompositions or search policies are plausible, final candidates can be normalized and externally checked, and extra calls fit the latency and cost contract.
- Not when: retrieval, extraction, summarization, classification, translation, stylistic rewriting, deterministic calculation, or a direct answer that already passes acceptance.
- Better alternative: plain chain-of-thought when reasoning is sequential and one decomposition is stable; self-consistency when complete samples are cheap, answer equivalence is easy and partial states cannot be scored; tree-of-thought when one tree with shared state, pruning and backtracking captures the search space; graph-of-thought when intermediate products must merge or be revised by several parents; a reasoning model when its single response meets quality under the budget and no branch-level control is needed.
- Own gates: Forest-Need Gate (the use-when conditions, after a direct and, where appropriate, a reasoning-model baseline). Diversity Gate: at least two genuinely different tree policies (decomposition templates, search algorithms, evidence partitions, models or verifier objectives); temperature changes alone do not count; if pilot trees produce the same intermediate states, citations, tool plan and answer, route to one tree plus stronger verification. Selection Gate: a deterministic answer normalizer and at least one outcome verifier, trusted tool, calibrated judge or human review path.
- Caps: fix initial trees, maximum activated trees, nodes and depth per tree, simultaneous calls, correction rounds, evaluator calls, tool calls, input and output tokens, wall time and currency cost (each to set unless the user gives it); reject a configuration whose maximum authorized spend exceeds the task contract even if expected spend is lower. Parallelism reduces wall time but not token cost.
- Pre-release items: beats direct, reasoning-model, chain-of-thought, self-consistency and single-tree alternatives on paired, budget-matched data; every tree has a distinct documented policy; answer normalization and outcome verification are tested; sparse activation improves cost-adjusted results; consensus weights are calibrated and correlation-limited; cancellation works.

## Graph-of-thought

- Use when: an output must combine independently useful parents, a subresult feeds more than one downstream consumer, new evidence may invalidate descendants, or the task's natural structure is a dependency network. Difficulty alone is not a reason.
- Better alternative: plain chain-of-thought when reasoning is mostly sequential and one verified path suffices; self-consistency when complete attempts are cheap and answers normalize cleanly; tree-of-thought when alternatives branch and compete but rarely merge; a plain workflow graph when the operation graph is known in advance (extraction, ETL, fixed review pipelines, build systems); a reasoning model when one response passes the verifier inside the budget and shared state, provenance or resumability is unnecessary.
- Own gates: Graph-Need Gate (the use-when conditions). Merge Gate: at least one merge whose output is better than selecting the best parent; if the only operation is choosing a branch, the design is tree-of-thought or best-of-N; if merging is concatenation, it is parallel prompting plus summarization. If permitted storage and observability cannot support the graph safely, the general Safety Gate fails; route to a stateless or minimally retained method.
- Caps: fix maximum nodes, edges, graph depth, refinement generations, merge fan-in, model calls, tool calls, tokens, cost, wall time, stored bytes and concurrent workers (each to set unless the user gives it).
- Pre-release items: beats the cheaper valid alternative on paired, budget-matched data; at least one aggregation or reuse operation contributes positive verified gain; every atomic claim links to evidence identifiers and every aggregate keeps those links; executable dependencies are acyclic; invalidation tests show no stale ancestor reaches a released output; merges keep provenance and do not double-count evidence.

## Skeleton-of-thought

- Use when: a latency-sensitive, multi-part answer has points with fixed shared context that can be expanded independently, such as factored explanations, independent comparisons, multi-aspect reviews and catalogs of recommendations. A point is independent when reversing order does not change correctness, it needs no sibling's value or decision, it mutates no shared state, and its interpretation needs no earlier point.
- Not when: math, coding, proofs, step-by-step derivations, narrative writing, stateful debugging or any dependent steps; cost matters more than latency; a short answer suffices; the backend is saturated; the provider serializes or heavily rate-limits parallel calls; or repeated sensitive context is unacceptable. An outline without concurrent expansion is not this method.
- Better alternative: sequential generation, least-to-most, chain-of-thought, graph-of-thought, a fixed workflow graph, or abstention, when routing fails.
- Own gates: Routing and suitability: expected points are independently expandable, at least two points contain meaningful work, the predicted latency benefit clears the configured margin, the cost ceiling holds, and capacity admission succeeds. Speed-up is most plausible with decode-bound generation, spare capacity, moderate point count, balanced lengths and permitted concurrency; measure wall time and throughput together.
- Default caps: eight skeleton points, two candidates and two repairs, concurrency four, one transient retry per point, semantic re-expansion of two points, two merge repairs, one fallback, twenty model calls, thirty thousand tokens, 90 seconds, and cost three times the verified sequential baseline. Counters never reset.
- Pre-release items: traffic-calibrated routing; working category and saturation exclusions; tested concurrency, backpressure, quota, retry, timeout, cancellation, straggler and fallback behavior; deterministic assembly; paired speed-up, cost, quality, throughput and tail-latency metrics under representative server load.

## Step-back

- Use when: the baseline failure can plausibly be traced to a hidden governing rule, an overly specific retrieval query, a need to recall a stable schema before applying details, or repeated surface-level reasoning that ignores an invariant; a candidate principle could change the answer and can be independently grounded.
- Not when: exact local evidence is decisive; the task is retrieval, extraction, classification, summarization or transformation with no abstract inference; the user asks for a direct fact already in the corpus; the question states the governing principle; a deterministic formula or database query suffices; the latency budget forbids two model stages; or the principle cannot be sourced and the risk tier forbids model-generated guidance. For legal, medical, financial, safety and compliance decisions, default to authoritative retrieval and human review, with step-back used only to identify candidate governing material.
- Better alternative: least-to-most when prerequisites and intermediate state are the bottleneck; query decomposition when several missing facts must be joined; both methods together only when separate ablations justify the compound cost. On a reasoning model, test one simple direct prompt first; external step-back stays justified for auditable principle retrieval, cache reuse, authorization, provenance and separate evaluation.
- Own gates: Step-Back-Need Gate (the use-when conditions, after a direct baseline and, where appropriate, a reasoning-model or plain chain-of-thought baseline, with a logged failure hypothesis).
- Default caps: two abstraction candidates, two abstraction repairs, three principle-retrieval rounds, eight principle chunks and eight case chunks before reranking, one re-abstraction, two answer attempts, two verification repairs, sixteen model calls, twelve retrieval calls, thirty thousand total tokens, sixty seconds, and cost no greater than three times the cheaper baseline. Tighten by domain; never reset counters after re-abstraction.
- Pre-release items: beats the cheaper valid baseline on paired, difficulty-stratified data; matched-token, matched-cost, matched-call and matched-latency controls; principle correctness, relevance, grounding and exception coverage pass thresholds; direct and chain-of-thought bail-outs work; retrieval queries both the original and the step-back question and keeps the two results separable; case evidence can contradict a principle.

## Analogical

- Use when: the target shares checkable relational structure with experience, cross-domain transfer can suggest a mechanism, or verified examples teach a stable pattern; enter only with a recorded failure hypothesis such as missing strategy, unfamiliar surface form, sparse demonstrations or need for cross-domain insight.
- Not when: the task is direct lookup of an actual precedent, citation, current fact or record (retrieve it); deterministic rules, a calculator, schema validation or executable tests decide the answer. In legal, medical, financial, policy and safety-critical contexts a fabricated precedent is unacceptable: generated examples are labelled hypothetical, authentic authority is retrieved, and if authenticity cannot be established the system abstains.
- Better alternative: plain chain-of-thought for a short sequential derivation without reusable source cases; a reasoning model directly when it meets the verifier and latency target; tree- or graph-of-thought when branching search or merging dominates. On a reasoning model, test a direct baseline before adding a self-generated example preamble; external analogy stays worthwhile for authenticated precedents, reusable case memory, explicit cross-domain mappings, disanalogy controls, inspectable provenance or governed adaptation. Tune one compute axis at a time.
- Own gates: Analogy-Need Gate (the use-when conditions). Release Gate: release the analogy-assisted result only if it passes all critical checks and either improves the outcome or provides required traceable insight without unacceptable cost; if both it and the baseline pass, prefer the cheaper answer.
- Default caps: five exemplars, three mappings, two mapping repairs and two adaptations per source, two re-retrievals, one verifier retry per claim, twenty-four thousand tokens, ninety seconds, and cost no greater than four times the direct baseline or a lower absolute limit. Counters are global and never reset.
- Pre-release items: direct and reasoning-model baselines measured; use cases and prohibited domains documented; case provenance and synthetic labelling enforced; transfer claims have independent verifiers; the held-out suite measures counterfactual robustness, contamination, negative transfer, abstention, cost and latency.

## Buffer of thoughts

- Use when: high-volume, recurring task families with stable procedural structure, independently verifiable outcomes, enough traffic to amortize curation, and measurable value over direct reasoning; enter only with a named recurring-task hypothesis (a validated procedure likely exists, retrieval and instantiation fit the budget, and external procedural memory may improve accuracy, latency, cost, consistency or auditability).
- Not when: novel or creative problems without recurring structure, low-volume or non-repeating distributions, safety-critical one-off decisions, direct factual lookup, or tasks a deterministic tool or reasoning model already solves reliably and economically. A template never substitutes for current evidence.
- Better alternative: few-shot examples for format or boundary cases; tree-of-thought when the correct strategy is genuinely uncertain and exploration is valuable; graph-of-thought when partial results have reusable dependencies and merges; fine-tuning for stable, labelled, latency-sensitive behavior safe to distribute globally. On a reasoning model, test one direct call first; a buffer still pays for organization-specific verified procedures, cross-run learning, provenance, access control, predictable tool use, rapid updates or cheaper small-model performance.
- Own gates: Buffer-Need Gate (the use-when conditions, after a verified cheaper baseline).
- Default caps: two distillation repairs, twenty retrieval candidates, three reranked templates, two selection rounds, two instantiations, two verification repairs, one fallback, one write candidate, twenty model calls, thirty thousand tokens, ninety seconds, and cost no greater than three times the verified direct baseline. Counters never reset.
- Pre-release items: the recurring distribution justifies a buffer; template and episode stores are separate; thresholds and abstention are calibrated; template-free recovery works; writes are quarantined and verified; poisoning, injection, cross-tenant and near-miss tests pass.

## Other routes

- ReAct: each iteration has a bounded intent, one authorized action, a captured observation and an updated decision; observations are untrusted data; stop when the goal test passes, no authorized action can reduce uncertainty, two successive iterations make no material progress, or the action budget is exhausted.
- Program-aided reasoning: the runtime is sandboxed (no network by default, no secrets, capped CPU, memory, output and wall time, discarded after each execution); a successful exit code is not semantic correctness, so add tests and invariants.
- Self-refine: separate critic and reviser prompts; the critic cites a specific defect and acceptance criterion; exit when all criteria pass, improvement stays below a minimum delta for two iterations, or the iteration budget is reached.
- Chain-of-verification: verification questions target independently checkable claims and their answers do not copy the draft.
