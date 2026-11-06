---
created: "2026-11-04T19:59:23Z"
updated: "2026-11-04T19:59:23Z"
---

# Tool-call evaluation: case set, metric formulas, iteration loop, readiness

Rules for part 5 (Evaluation plan) of the deliverable.

## 1. Private evaluation set (case categories)

Build it from the real task distribution, with policy-accurate expectations:
- Clear calls, clear no-call cases, and ambiguous cases that require clarification.
- Near-neighbour tools and misleading names.
- Missing, extra, conflicting, null, boundary, Unicode, locale, timestamp and oversized arguments.
- Independent parallel calls, hidden dependencies, races and partial failures.
- Rate limits, timeouts before and after side effects, malformed outputs, stale data, circuit opening and provider interruptions.
- Repeated-state loops, budget exhaustion, cancellation, and resume after restart.
- Direct and indirect prompt injection in every tool-result channel and modality.
- Poisoned tool descriptions, changed definition hashes, duplicate names and cross-server shadowing, when third-party tool servers are used.
- Cross-user and cross-tenant access attempts, destination substitution, privilege escalation, secret exfiltration and confused-deputy scenarios.
- Approval bypass, approval-field mutation and misleading preview text.
- Alternate model snapshots, provider outages, tool versions and catalog orderings.

Side-effecting tools run against simulators and read tools against replay fixtures: evaluation never sends real email, moves money, deletes data or contacts uncontrolled destinations. Never replay a write against production.

Run stochastic cases several times and report both pass rate and all-runs reliability: the rate at which all k trials pass is lower than single-run success and exposes inconsistency.

Public suites give comparability but no single benchmark represents production, and benchmark success does not test production authorization or side effects.

## 2. Metric formulas

Compute over a declared window and cohort. Count a logical call once unless the formula uses attempts.

- Tool-call success rate = logical calls with verified success / logical calls executed. Exclude policy-denied proposals from the denominator and report them separately.
- First-attempt success rate = calls succeeding on attempt 1 / logical calls executed.
- Schema validation failure rate = proposals failing the canonical input schema on first validation / tool-call proposals.
- Semantic validation failure rate = schema-valid proposals failing semantic or business validation / schema-valid proposals.
- Repair success rate = invalid proposals repaired and then validated within the limit / proposals entering repair.
- Retry rate = logical calls with more than one attempt / logical calls executed. Retry amplification = execution attempts / logical calls executed.
- Hallucinated tool rate = proposals naming an unexposed, unknown, disabled or version-mismatched tool / tool-call proposals.
- Hallucinated or invalid parameter rate = proposals with an unknown field, invented required value, invalid reference or semantically impossible value / tool-call proposals; keep the subcategories separate.
- Tool-selection accuracy = tasks selecting a gold-acceptable tool / tasks requiring a tool with an acceptable tool available.
- Unnecessary tool-use rate = tasks invoking any tool when the gold policy says no tool / gold no-tool tasks.
- Missed tool-use rate = tasks making no call when the gold policy requires one / gold tool-required tasks.
- Abstention precision = correct abstentions / all abstentions; abstention recall = correct abstentions / tasks where abstention is required.
- Policy denial rate = proposals denied by policy / proposals evaluated by policy; segment by reason.
- Approval modification rate = approval prompts the user edits before approving / approval prompts approved; high values suggest poor intent capture.
- Unknown side-effect rate = executed write calls ending in unknown outcome / executed write calls.
- Circuit-open rate = calls failed fast due to an open circuit / eligible execution requests.
- Cache hit rate = eligible reads served from cache / cache-eligible reads; stale-response rate = cached responses violating freshness at consumption / cached responses served.
- Latency percentile p_x = the duration below which x percent of the cohort falls; report task end-to-end, model-turn, queue, approval-wait, execution-attempt and successful-call latency separately; never average percentiles.
- Task completion rate = tasks whose verified terminal state satisfies all required goals / admitted tasks. Partial completion rate = tasks with at least one but not all required goals verified / admitted tasks.
- Cost per successful task = model, tool and allocated infrastructure cost for the cohort / verified successful tasks. Wasted cost = cost of failed, denied-after-generation, duplicated or looped work / total cost.
- Calls per successful task = logical tool calls in successful tasks / successful tasks; turns per successful task likewise.
- Security incident escape rate = adversarial cases producing a prohibited disclosure or action / adversarial cases executed; the release target for critical prohibited outcomes is zero.

## 3. What must be recorded for these metrics

Correlation: one trace ID per task; a task ID durable across retries and restarts; one turn ID per model decision; one tool call ID per logical proposal, even across retries; a unique attempt ID per attempt sharing the call's idempotency key; provider call ID and external operation ID; selection, policy decision and approval request IDs referenced from the tool call ID. Never reuse IDs across tenants. Keep high-cardinality IDs in traces and logs, not metric labels.

Per call: tool ID and version, raw and canonical argument hashes, schema and semantic validation results with rule outputs, repair attempt and outcome, policy decision and reason code, approval decision and whether a field changed afterwards, attempt number, outcome class, retryable flag, circuit state, unknown-outcome flag, authoritative verification result, cost. Do not record raw authentication tokens or unredacted sensitive prompts, arguments or results in ordinary telemetry.

## 4. Evaluation iteration loop

Enter for every model, prompt, schema, tool, policy, provider or orchestrator change.
1. Freeze candidate artifact hashes and declare metric thresholds by risk class before viewing results.
2. Run schema compatibility and unit tests, then deterministic simulated-tool tests.
3. Run the full private set across several seeds or repetitions, plus relevant public suites.
4. Compare against the production baseline with paired cases; segment failures into selection, syntax, semantics, authorization, execution, result interpretation, completion, security, latency and cost.
5. Inspect trace evidence for regressions, not just aggregate scores.
6. Change one major variable at a time: description, schema, retrieval, policy, model or loop logic.
7. Repeat until all critical security tests pass, quality thresholds are met, and latency and cost stay within budget.
8. Exit to a read-only canary; promote reversible writes only after canary metrics and manual trace review pass.
9. Roll back automatically on a critical prohibited action, cross-tenant access, secret leak, unknown-outcome spike, or a meaningful completion regression.

Cap ordinary offline optimization at five iterations before revisiting the architecture or the evaluation labels. Keep a hidden holdout and rotate adversarial cases rather than tuning to a fixed benchmark. Do not promote a change because one public leaderboard score improved.

## 5. Readiness questions (all must be yes)

- Is every exposed capability necessary, owned, versioned and revocable?
- Are the selection, input, execution and output contracts explicit?
- Do provider schemas compile and pass compatibility tests?
- Are semantic validation and policy enforcement independent of the model?
- Are per-user and per-tenant credentials least-privileged?
- Are side effects idempotent, reconcilable, approval-bound or compensable?
- Are timeout, retry, circuit-breaker, rate, concurrency and budget policies configured?
- Is arbitrary execution isolated?
- Are sensitive telemetry fields redacted by default?
- Can the stated metrics be calculated exactly from recorded fields?
- Do evaluations include abstention, no-tool cases, fault injection, indirect injection, cross-tenant tests and repeated trials?
- Is there a simulator for every consequential action?

If any answer is no, keep the capability read-only or disabled until the missing control exists.
