---
created: "2026-11-04T23:17:47Z"
updated: "2026-11-04T23:17:47Z"
---

# Fit, checkpoint placement and evidence grounding

Used for Part 1 (Fit and alternatives) and Part 2 (Checkpoint table).

## Use conditions

Structured reflection is warranted when at least one of these holds:

- The next step is irreversible, externally visible, privileged, costly or difficult to undo.
- A long tool chain has produced new information that changes constraints or invalidates the plan.
- Objective verification signals exist and must be interpreted before repair.
- The task is high-stakes: a missed defect has material safety, legal, financial, cybersecurity or operational cost.
- An intermediate result has low calibrated confidence, conflicting evidence, missing required fields, anomalous tool behaviour or an out-of-distribution signal.
- A plan checkpoint needs an explicit continue, replan or escalate decision.
- A candidate answer must satisfy a detailed rubric, citation requirement or policy before release.
- A failed attempt contains actionable feedback that can guide a bounded revision.
- The organization needs a machine-queryable record of what was checked and why a transition occurred.

Reflection pays off most when the task is both consequential and verifiable.

## When-not conditions

Skip or sample reflection when:

- The task is simple, low-stakes, cheap to undo and already covered by deterministic validation.
- The next action is read-only and a mistake has negligible impact.
- No useful verification signal exists, so reflection would only restate the same uncertain belief.
- The model only transforms format under a strict schema and a deterministic validator fully decides success.
- Latency dominates and paired evaluations show no material quality gain.
- A stronger model, a more fitting tool, better retrieval or a clearer instruction gives more improvement per unit cost.
- The candidate is already objectively correct and revision risk exceeds expected benefit.
- The reflection would require storing sensitive reasoning or data that policy forbids.

A reflection pass is not an explanation to a user, a compliance certification, a security approval, or evidence that hidden reasoning was faithful.

## Who or what assesses

- Deterministic verification first whenever a test, parser, type checker, policy rule, solver, database invariant or exact target can decide. Do not ask an LLM to replace a reliable machine check.
- Typed self-reflection when the same model must summarize defects and next action cheaply; ground it in external observations and calibrate it per task class. It is not the sole judge of the same model's correctness.
- A separate critic when diversity, specialization or producer-critic separation has shown value, when the producer has known self-bias, or when the task lacks a deterministic verifier. Two calls on the same base model, prompt family or context are not independent. Blind the critic to producer identity and prior confidence where possible.
- Multiple candidates or self-consistency when several reasoning paths are plausible and an objective selector exists; this is not defect diagnosis.
- Provider extended or adaptive thinking when it performs better and the application does not need a typed, inspectable checkpoint. A structured reflection tool is for an application that must consume, gate, correlate and evaluate the assessment.

## Alternatives to compare

For each task class, compare: no reflection; deterministic verification only; a stronger producer model; provider reasoning or extended-thinking mode; typed self-reflection; a separate blinded critic; multiple candidates with objective selection; human review at the decision boundary. Choose the cheapest configuration that meets quality and risk targets; the quantity that matters is cost per successful task, not cost per call.

## Placements and trigger types

The `trigger_type` values are: mandatory_policy_gate, verifier_failure, low_confidence, tool_error, anomaly, plan_checkpoint, pre_action, pre_release, sampled_audit, human_request.

- After a material tool result: when new information changes the plan, contains an error, contradicts prior assumptions or completes a critical prerequisite. Not after every trivial read.
- At a plan checkpoint: before committing to a new phase, especially when dependencies or constraints changed.
- Before an irreversible action: current verification, a structured reflection, deterministic policy approval, and human approval where policy demands it. Reflection is advisory within this sequence.
- Before a final answer: when claims, citations, required sections or high-impact advice need release checks.
- After a verifier failure: diagnose the failure and propose one bounded repair, not a full regeneration.
- After repeated tool errors: decide whether to change arguments, switch to a permitted tool, degrade gracefully or escalate.
- On an adaptive trigger: risk score, calibrated uncertainty, anomaly detection, out-of-distribution score, conflicting sources or a sampling policy.

## Modes

- mandatory: the checkpoint precedes an irreversible action or a policy gate requires it.
- adaptive: the checkpoint fires only on its named trigger (verifier failure, tool error, low calibrated confidence, anomaly, source conflict, risk score).
- sampled: a when-not condition holds, and a sample of the skipped cases or of passes is routed to review so that skipping can be monitored.
- disabled: a when-not condition holds and no sampling is set; the skip is logged with its policy reason.

## Evidence bundle by subject

Build the bundle before reflection; the reflector receives observations, not an invitation to introspect.

- Code: test names and outcomes, compiler and type-checker diagnostics, lint findings, coverage deltas, static-analysis alerts, dependency and secret scans, the relevant diff spans.
- Factual answers: decomposed claims, retrieved source spans, publication and freshness metadata, citation-entailment results, contradictions, unresolved claims.
- Tool workflows: normalized tool outputs, error classes, policy decisions, database preconditions and postconditions, authoritative state reads.
- Plans: user constraints, resource limits, capability and permission checks, dependency status, identified irreversible steps.
- Structured outputs: schema-validation errors and business-rule failures.
- Security decisions: deterministic policy-engine results, authorization scopes, data classification, destination, approval state, threat-detection signals.
- Benchmark tasks: target or ground-truth references hidden from the producer when the protocol requires blinding.

Bind every evidence record to the exact candidate digest; never reflect on test results from a different revision. Reuse a verifier result across revisions only when its dependency graph proves the change cannot affect it.

## Evidence levels

- Level 0, introspective assertion: no external observation cited. It may guide exploration but cannot pass a consequential gate.
- Level 1, referenced observation: cites a specific tool result, source span, policy clause, test name or user requirement. The reference must resolve; the interpretation may still be wrong.
- Level 2, independently verified fact: a trusted verifier confirms it (a passing test suite, a valid signature, a policy-engine decision, an exact-state comparison, human approval, a ground-truth match).

A pass for a high-impact action needs Level 2 evidence for every critical invariant. Level 0 confidence never compensates for missing verification.
