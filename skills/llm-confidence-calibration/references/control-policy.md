---
created: "2026-11-04T23:04:58Z"
updated: "2026-11-04T23:04:58Z"
---

# Thresholds and control actions

## Setting thresholds

- Define the costs of wrong automation, abstention, model or human escalation, latency and tools.
- Minimize expected cost subject to maximum critical risk, minimum coverage, reviewer capacity and latency.
- Select each operating threshold on the threshold-selection partition, never on the final test set or after an incident.
- Use slice-specific thresholds only with enough calibration data and approval.
- Keep thresholds server-side: attackers can game a visible threshold or manipulate a confidence self-report through prompt injection. Never let retrieved instructions redefine the confidence target.
- An emitted I-don't-know is an abstention action to evaluate, not evidence that the model knew it was wrong.

## Control states

Each state gives the three fields of a row of the thresholds table after its name: Threshold, Action, Reason codes. Compare the calibrated release probability or risk score with the task-specific thresholds; ties choose the safer state.

- Accept. Threshold: accept threshold, with all hard checks passed. Action: pass the release gate below, then authorize only the requested scope. Reason codes: none.
- Recover. Threshold: recover threshold. Action: one corrective action chosen by cause (below), then reassess. Reason codes: the classified cause.
- Escalate. Threshold: escalate threshold, or a cause that needs a stronger model or a person. Action: route to the approved stronger model or enqueue human review. Reason codes: capability mismatch, high consequences, unresolved conflict, policy uncertainty.
- Abstain. Threshold: abstain threshold, or required evidence unavailable with no safe recovery. Action: abstain, name what is missing and how a person can resolve it, and give the next safe step. Reason codes: the classified cause.

Causes to classify, separately from the score: ambiguity, missing evidence, retrieval failure, model uncertainty, verifier conflict, tool failure, policy uncertainty, suspected shift, budget exhaustion.

## Corrective action by cause

- Missing evidence: retrieve with provenance.
- Computable uncertainty: call a deterministic tool in a sandbox.
- Low agreement: generate only the allowed additional candidates.
- Plausible local defect: run an independent verifier or one evidence-conditioned revision.
- Capability mismatch: route to the approved stronger model.
- High consequences, unresolved conflict or policy uncertainty: enqueue human review.

Schedule exactly one action per cycle; do not launch every recovery in parallel by default. Run it with validated arguments, least privilege, a deadline and a cost cap, and treat retrieved text and tool output as untrusted data.

## Verifier order

Deterministic validators first, retrieval-and-entailment checks second, specialized classifiers third, LLM judges last.

## Recovery loop and caps

- After an action, recompute only the signals it affects, keep the previous values, run the independent verifier, and require an evidence-linked reason for every score change.
- Repeat assess, act and reassess until confidence clears the accept threshold and hard checks pass, evidence is exhausted, two consecutive cycles improve calibrated confidence by less than the configured minimum delta, or any cap is reached.
- Default caps: two corrective cycles, one stronger-model escalation, one human escalation, three retrieval queries, one verifier retry, and a task-specific token, cost and wall-time ceiling; change them only through versioned policy.
- Exhaustion exits with abstention or the best verified partial result. Never lower a threshold inside the loop.

## Release gate

Check output schema, claim support, deterministic postconditions, safety policy, calibration validity and privacy. High confidence cannot override a failed hard check. If all pass, authorize only the requested scope. If a safe partial response is possible, remove unsupported claims and clearly limit the answer; otherwise abstain and give the next safe step.
