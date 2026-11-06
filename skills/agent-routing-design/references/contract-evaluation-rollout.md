---
created: "2026-11-05T00:11:10Z"
updated: "2026-11-05T00:14:08Z"
---

# Route contract, uncertainty, evaluation and rollout

Use this file to fill the Route contract, Uncertainty and fallbacks, Evaluation plan and Rollout plan parts.

## Route catalog columns

Treat the catalog as a versioned interface. One row per target, plus a row for each non-executing route the design keeps (clarify, abstain, deny or quarantine, human review).

| Column | What it holds |
|---|---|
| Route ID | Stable identifier, never reused for a different meaning |
| Owner | Accountable team or role |
| Purpose | What work the route serves |
| Inclusion | Positive criteria and the decisive evidence |
| Exclusions | Explicit exclusions and the confusing neighbour routes |
| Modalities and required context | Accepted modalities and languages; trusted context the route needs |
| Risk class | Consequence class of a wrong route, including side effects (read, write, external, irreversible) |
| Allowed tools and data | Minimum tool and data scope, with read and write separated |
| Output contract | What the handler returns |
| Latency and cost envelope | Latency objective and cost envelope |
| Retry and fallback | Retry policy and the fallback route |

## Router output fields

- Schema version and taxonomy version.
- Decision type: single, multi, clarify, abstain, deny or human_review.
- One primary route identifier, selected only from an enum.
- Zero or more secondary route identifiers, when multi-route execution is allowed.
- A confidence value plus a confidence-method identifier (never a bare number of unknown meaning).
- Top alternatives and their scores, when the method supports them.
- A short reason code from a controlled list, not free-form reasoning.
- Missing-information fields and one bounded clarification question, when clarify is chosen.
- Risk flags and the required approval level.

The dispatcher rejects unknown identifiers, schema mismatches, prohibited combinations, excessive route counts and missing required fields, and never executes a URL, function, model or tool name the router invented. It accepts only registered, currently eligible routes and rechecks authorization, side effects, budgets and state at execution time.

## Decision outcomes

| Outcome | When it applies |
|---|---|
| single | One route meets its acceptance rule and no policy gate blocks it |
| multi | The request holds independent intents that can each be served safely |
| ordered subroutes | One result is a prerequisite for another |
| primary with secondary intents | One specialist should coordinate the others |
| clarify | Required information is absent and one user answer can separate the candidates |
| human_review | Intent is understandable but policy, risk or novelty needs judgement |
| abstain | The request is outside the taxonomy or no route is appropriate (or a bounded general route takes it) |
| deny or quarantine | Policy prohibits processing, or the content cannot be safely inspected |

For multi-intent execution: decompose into bounded subrequests, authorize each independently, keep one shared trace identifier, cap fan-out, parallelize only read-only or independent work, serialize state-changing work, and report partial failure as partial.

After a clarification answer, rebuild the routing input from approved state, recompute eligibility and rerun the thresholds. Stop with abstention or human review when the user declines, the answer does not resolve the ambiguity, or a clarification, time or cost budget is exhausted.

## Uncertainty signals and thresholds

- Signals: top-two score margin, embedding similarity and nearest-neighbour distance, entropy or token log probabilities when available, disagreement across repeated samples or across rule, embedding, classifier and LLM stages, distance from the training distribution, downstream answer verification. Record which signal produced the score.
- Self-reported LLM confidence is a feature, not a probability of correctness; calibrate a usable decision score on held-out data and re-fit thresholds after any change to a model, prompt, taxonomy or traffic mix.
- Set thresholds by expected harm, not only overall accuracy: low-risk reversible routes may accept lower confidence with automatic fallback; sensitive-data access, write tools, financial actions, safety-critical advice and external communication need higher confidence plus deterministic authorization or human approval. Separate thresholds for understanding and for acting where justified.
- No universal threshold exists. Fit thresholds on a validation split, produce risk-coverage and subgroup curves, and define the branch from each score band to accept, clarify, abstain, review, deny or escalate.

## Fallback policy

- Classification fallback: retry once only for transient transport or invalid-schema failures, then a secondary router or safe default.
- Availability fallback: another healthy deployment that meets the same capability, privacy, region and safety requirements.
- Quality fallback: escalate from a cheaper route after verification failure.
- Ambiguity fallback: clarify or abstain.
- Policy fallback: deny or require human approval; never downgrade a policy restriction.
- Overload fallback: shed low-priority traffic, queue bounded work, or return a degraded response.

Every design sets per-stage timeouts, a total deadline, a maximum attempt count and a maximum accumulated cost; uses circuit breakers on unhealthy dependencies; and prevents loops with a visited-route set and a decrementing route-attempt budget.

## Evaluation

- Baselines: the simplest valid rules baseline and a majority or default baseline; add embedding or classifier baselines where appropriate. No learned router is built without a comparator.
- Route-decision quality: overall accuracy; macro and support-weighted precision, recall and F1; per-route precision and recall and the confusion pairs; exact and partial route-set match for multi-intent requests; abstention coverage, accepted-case error and risk-coverage curves; clarification, human-review, default-route and unnecessary-escalation rates; calibration with reliability curves and a proper score where the output is probabilistic.
- Efficiency and reliability: routing and total latency at p50, p95 and p99; queue delay; retries, timeouts, schema failures, fallback depth; router, downstream, fallback and total cost per request, counting every attempted stage.
- End-to-end utility: task success, policy compliance, user correction or rephrase rate, time to resolution, cost per resolved task, quality by route. Record route correctness and downstream success separately, so a weak handler is not misread as a routing error.
- Test set: a representative stratified sample of real traffic; a temporal holdout from a later period; boundary examples for every confusing route pair; ambiguous, incomplete, multi-intent, multilingual, long and attachment-bearing inputs; out-of-scope inputs with no valid route; rare high-impact safety and authorization cases; injection and jailbreak cases; dependency failure, overload, timeout and malformed-output cases; subgroup slices with privacy review.
- Model selection: collect counterfactual outcomes by running the candidate models on the same sampled requests; otherwise correct-model labels only encode annotator opinion.
- Instrument before optimizing: log version and configuration provenance (router, prompt, taxonomy, policy, thresholds, candidate pool, exemplars), the decision data (eligible routes, selected route, scores and score method, threshold, reason code) and outcome labels, keeping raw prompts, secrets and personal data out of general telemetry.
- Gates: predeclare per-route, safety, latency, cost and subgroup gates before the final holdout; reject a candidate that improves average accuracy while violating any of them; assign each failure to its layer (taxonomy, missing context, prompt or rules, model, calibration, drift, downstream handler, policy, label) and fix that layer; iterate offline until the gates pass on the standard and adversarial suites for at least two frozen runs; never tune on the final holdout.

## Rollout

Release routing changes independently from handler changes, in this order:
1. Validate schemas, route allowlists and policy precedence in continuous integration.
2. Freeze the candidate artifact: prompt, model, taxonomy, thresholds, exemplars or rules, candidate pool, price book and code.
3. Run offline and adversarial tests against the gates.
4. Replay historical traffic with side effects disabled or mocked; never replay write operations against live systems.
5. Shadow live traffic while only production executes, and inspect disagreements.
6. Canary a small, reversible, eligible low-risk cohort with a concurrent control.
7. Expand in bounded stages by feature flag, repeating the canary check at each stage, while monitoring route quality, end-to-end success, safety, latency, cost, abstention and subgroup slices.
8. Promote only after the observation window covers the relevant traffic cycles.

Automatic rollback triggers: any safety or authorization incident, an unacceptable rise in wrong-route or final-failure rate, end-to-end regression, latency or cost breach, elevated fallback depth, or loss of telemetry; stop at once on a security boundary breach. Keep a kill switch and a deterministic safe route that do not depend on the router. When models, providers, prices, handlers, prompts, policies or the taxonomy change, return to the earliest affected step and repeat the evaluation-to-canary loop.

Change the taxonomy through versioned proposals (merge, split, add, deprecate, alias), run old and new taxonomies in parallel, and keep the old version for rollback.
