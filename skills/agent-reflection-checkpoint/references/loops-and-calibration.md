---
created: "2026-11-04T23:17:47Z"
updated: "2026-11-04T23:17:47Z"
---

# Transitions, bounded loops and calibration

Used for Part 4 (Transition and loop rules) and Part 5 (Calibration plan).

## Transition rule (verdict to workflow state)

The state machine combines the validated reflection with objective verifier states and policy:

- Continue only when the gate is satisfied.
- Revise only when there is an actionable defect and a permitted change.
- Gather evidence only for a named unresolved invariant.
- Replan when the current strategy is invalid, not merely because the prose could be improved.
- Escalate on critical ambiguity, persistent failure, low calibrated confidence or a policy requirement.
- Block on a prohibited action, missing authorization, an unresolved critical defect or exhausted safe options. After a policy block the only valid transitions are a safe alternative, human escalation where policy permits an exception, or terminate; do not retry after a policy block or deterministic invalidity.
- Abstain safely when evidence is insufficient.

## Gate for a high-impact action

The action proceeds only when all required external verifiers pass, evidence is fresh, authorization and approval are valid, the reflection schema is valid, no blocking defect remains, and budget and policy allow it. A model-generated pass alone never satisfies the gate. Immediately before an irreversible action, re-read authoritative state, confirm evidence freshness, validate idempotency and destination, obtain required approval and rerun policy. For the highest-risk actions, the same model instance does not produce, reflect, approve and execute.

For lower-risk tasks a conditional gate is allowed: a calibrated pass above a task-specific threshold may skip a second critic only if deterministic checks pass and monitoring samples the skipped cases.

## Loops, caps and exits

Evidence gathering. Enter when a mandatory check is missing, evidence is stale, two trusted signals conflict, or the verdict is gather_evidence.
1. Name the exact unresolved claim or invariant and its required trust tier.
2. Select the cheapest allowed verifier that can resolve it; prefer deterministic over model judgments and read-only over side-effecting checks.
3. Run it through the normal tool-use controls (arguments, authority, timeout, result schema validated).
4. Store the result as an immutable evidence record with source, digest, time, scope and trust tier.
5. Recompute coverage; the reflector does not mark its own requested evidence as verified.
6. Cap: at most two rounds by default before escalating; a higher cap only where evaluation shows value.
7. Exits: sufficient evidence, a definitive verifier failure, a budget stop, or escalation. Stop at once when the next verifier would repeat an equivalent result, cannot reduce uncertainty, or would need unauthorized action.

Schema repair. If the reflection record fails validation, allow one repair attempt using the validation errors; then abstain and escalate or use the safe fallback. A format repair is not evidence that the verdict is correct.

Reflect, revise, reverify. Enter when the validated verdict is revise and the expected value of repair is positive.
1. Save the pre-revision candidate as the rollback baseline.
2. Select one defect or a small coherent set; do not rewrite unrelated correct content.
3. Record the change hypothesis: targeted defect IDs, intended change, expected verifier movement, protected invariants that must not regress. Block the revision if targeted defect IDs are missing from it.
4. Produce a child revision with new revision and candidate IDs, an exact diff and a parent link.
5. Rerun every verifier the change affects plus regression checks for protected invariants.
6. Adopt the child only if all blocking checks pass and the predefined improvement criterion is met; roll back when the child fails a check the parent passed.
7. Reflect again only if material defects remain and budget remains, not to seek a more enthusiastic pass.
8. Cap: at most two revision cycles by default for ordinary tasks and three for high-value, strongly verifiable tasks; a higher cap needs task-specific evaluation evidence.
9. Exits: verified pass, safe fallback, escalation, budget exhaustion, or no improvement. Return the highest-scoring verified candidate, not the last one.

No-improvement rule: stop when the objective score fails to improve by the minimum meaningful delta in two consecutive revisions, when the same defect signature recurs twice, or when a revision reverts a change made in the previous two iterations without new evidence.

Anti-oscillation rule: compute a canonical defect signature and a revision-diff fingerprint; if states repeat, content reverts A to B to A, or verdicts alternate between the same two states without new evidence, stop and escalate or roll back.

Escalation. Enter when a critical defect persists, evidence conflicts, confidence is below the routing threshold, the repair cap is reached, policy requires review, or the reflector abstains.
1. Preserve the highest-scoring verified candidate and the complete evidence bundle.
2. Escalate first to the least costly independent capability that addresses the failure: a specialized deterministic checker, a different prompt with a blinded critic, a stronger model, or a domain tool.
3. Reverify the proposed correction with the original objective checks.
4. If still unresolved and impact is material, create a human-review item with the candidate, diff, defects, evidence, policy results and recommended options.
5. Cap: at most two automated escalation levels by default.
6. Exits: verified success, explicit human decision, safe fallback, rollback, or terminal block. A stronger model's confidence without better evidence is not a successful escalation.

Budget. Set per-task ceilings for reflection calls, total model turns, input and output tokens, verifier calls, wall time and money. Reserve part of the budget for final verification and escalation. Stop when expected marginal value is non-positive, the no-improvement rule fires, or the remaining budget cannot complete re-verification.

Context. Keep immutable artifacts out of the active prompt; carry only a bounded summary and resolvable references, not the full reflection history.

## Calibration plan

- Event: confidence is the predicted probability that the verdict matches the designated ground-truth outcome for this task class. Do not mix confidence in defect existence, in evidence interpretation and in final task success.
- Profiles: keep separate calibration profiles by model snapshot, prompt version, task class, risk tier, verdict type, evidence tier and, where data permits, language and domain. A threshold is valid only for the profile that produced it.
- Measures: Brier score, the mean of the squared difference between predicted probability and the binary correctness label (lower is better; report sample count and base rate). Expected calibration error, the sum over predefined confidence bins of the bin's share of samples times the absolute gap between mean confidence and accuracy (state bin boundaries, minimum bin size, equal-width or equal-frequency). Reliability by confidence bucket. For multiclass verdicts, a proper multiclass scoring rule or one-versus-rest calibration with confusion matrices; abstain and escalate are scored under the routing policy and cost function, not as errors.
- Thresholds: derived from held-out data and the explicit costs of false pass, false block, escalation, latency and human review, not from intuition.
- Without a compatible or current profile: confidence is advisory only, and routing follows deterministic risk policy. A threshold crossing caused only by repeated self-assessment is disallowed.

Calibration-tuning loop. Enter when a new model or prompt is introduced, monitoring detects drift, a subgroup misses tolerance, or enough new ground truth accumulates.
1. Freeze a temporally held-out calibration set and a separate final test set.
2. Collect raw confidence, verdict, evidence tier, task metadata and outcome without tuning on the test set.
3. Plot reliability by bucket; compute Brier score, expected calibration error, coverage, selective accuracy and subgroup gaps.
4. Fit a simple post-hoc calibrator (temperature, Platt or isotonic scaling) only when sample size and monotonicity assumptions are adequate.
5. Choose routing thresholds from the explicit costs above.
6. Reevaluate on the untouched test set and compare with the prior profile.
7. Promote only if calibration improves without unacceptable accuracy, coverage or subgroup regression.
8. Cap: at most one tuning cycle per frozen split; create a new split for further tuning.
9. Exits: an approved profile, advisory-only confidence, or disabled confidence routing.

Outcome capture: record the final artifact, user or human outcome, grader results, incidents, rollbacks and delayed ground truth, joined to every reflection and revision in the trace; update calibration only after the outcome rule is satisfied.
