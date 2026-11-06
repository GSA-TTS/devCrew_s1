---
created: "2026-11-04T23:04:58Z"
updated: "2026-11-04T23:04:58Z"
---

# Drift and recalibration plan

## What to monitor

Input mix, language, task family, corpus and index versions, model revision, confidence distributions, agreement, semantic entropy, claim support, abstention, escalation, tool failures, latency, cost and delayed outcomes. Compare rolling windows with the launch reference and a recent stable reference. Dashboards show calibration and selective-risk slices, not average confidence alone.

## Statistics

- Before labels arrive: compare current and reference distributions of task mix and every major signal with Jensen-Shannon divergence for binned distributions, Kolmogorov-Smirnov distance for continuous scores, and changes in mean, quantiles, missingness and out-of-distribution rate. Use population stability index only as a coarse dashboard indicator, paired with those statistics, sample counts and uncertainty intervals. No universal drift threshold is valid for every feature.
- Once labels arrive: changes in accuracy, ECE, Brier score, log loss, AURC, risk at target coverage, abstention precision and recall, conformal coverage and escalation yield, with bootstrap confidence intervals.
- Alert only after minimum sample rules or a critical incident trigger; small-window noise must not cause threshold thrashing.

## Triggers for investigation

- Any unannounced model revision.
- A prompt, policy, index or tool-schema change.
- Confidence or feature drift beyond its validated control limit.
- An ECE, Brier, log loss, AURC, coverage or critical-error breach after enough labels accrue.
- Conformal undercoverage.
- A protected-slice regression.
- A cluster of confidently wrong incidents.

A scheduled quarterly review is a backstop, not a substitute for event-driven recalibration.

## On a trigger

1. Freeze automatic threshold updates and attach the affected bundle version.
2. Choose a safe mode: preserve the old route if compatible, raise abstention, narrow scope, require verification, or send the risk tier to humans.
3. Assemble a recent labeled recalibration window while preserving a future holdout.
4. Repeat the offline calibration loop, then shadow and canary the replacement.
5. Exit when metrics recover and incident owners approve promotion, or keep the system in degraded safe mode.

Cap automatic recalibration attempts at one per trigger; further failure requires human review.

## Decision records

- Threshold decision: decision ID, eligible population, calibrated score, uncertainty rank, candidate actions, accept, escalate and abstain thresholds, cost matrix version, capacity constraint, hard-check results, selected action, decision reason code, policy overrides, override actor, timestamp. Preserve both the threshold and the score; a boolean alone cannot reconstruct a risk-coverage curve.
- Abstention: abstention ID, reason code, triggering signals, failed checks, evidence attempted, recovery cycles, safe partial response status, later correctness of the withheld answer if measurable, whether abstention was appropriate, resolution.
- Escalation: source and destination model or human queue, priority, queue delay, handling time, adjudicated outcome, whether escalation corrected an error or changed the action, incremental latency and cost, reviewer agreement.
- Route critical confident errors, threshold bypasses, prompt-injection successes and unauthorized actions to the incident path immediately; enqueue delayed labeling for each run.
- Monitoring data are sensitive: do not log credentials, authentication tokens, raw private chain-of-thought, unrestricted personal data or unredacted retrieved documents by default; apply field-level redaction, least-privilege access and retention by risk.
