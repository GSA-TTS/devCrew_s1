---
created: "2026-11-04T23:04:58Z"
updated: "2026-11-04T23:04:58Z"
---

# Calibration and evaluation plan

Calibration asks whether predictions assigned confidence p are correct about p of the time, for the defined event and population.

## Dataset and partitions

Freeze a representative dataset with immutable example IDs, time windows, task and risk slices, adversarial cases, out-of-distribution cases and authoritative labels. Split it into fitting, threshold-selection and untouched evaluation partitions, disjoint from each other and from training. Never place labels in model context. Without immutable split identity and complete bundle identity (model, prompt, retrieval, tool, policy, calibrator, threshold), calibration comparisons are not reproducible.

## Calibrators

- Temperature scaling fits one positive temperature to logits; use it when logits retain useful relative structure.
- Platt scaling fits a logistic mapping from a scalar score to probability; use it, or an appropriately regularized monotonic method, for arbitrary scalar scores.
- Never fit and report performance on the same examples.

## Metrics

- Reliability diagram with per-bin counts, always published beside ECE, generated from the same frozen population.
- ECE: group eligible labeled predictions into declared bins, take each bin's absolute gap between mean calibrated probability and empirical success, weight by bin count and sum. Report bin edges, counts, empty-bin handling, weighting, target label, confidence definition, confidence intervals and slice results, in equal-width and equal-mass versions. Fixed-width ECE can hide local errors or change with the bin count; prefer equal-mass bins when samples are sparse.
- Brier score: mean of (p minus y) squared, with y one for success and zero for failure; lower is better, and it reflects both calibration and resolution.
- Log loss: mean negative log of the probability assigned to the observed outcome, after a documented numerical floor rather than the log of zero. Report it with Brier, because a model can improve one while changing discrimination or sharpness.
- AUROC for failure ranking: incorrect is the positive class, uncertainty is the score; report the direction. It measures ranking, not calibration or operational coverage.
- Risk-coverage: sort eligible predictions from highest to lowest release confidence, accept each prefix and compute its loss; coverage is the accepted fraction and risk the loss among accepted examples. Report AURC (lower is better for the same task and loss), risk at required coverage and coverage at the maximum tolerated risk, because the area alone can obscure the production point.
- Abstention precision: incorrect predictions among abstentions divided by all labeled abstentions. Abstention recall: incorrect predictions among abstentions divided by all incorrect predictions that would otherwise have been eligible. Also report unnecessary-abstention rate, coverage and critical-error escape rate.
- Escalation yield: escalations that correct an upstream error or produce a preregistered material improvement, divided by completed escalations; report resolution rate, queue time, incremental cost and residual error separately.
- Also compare latency, cost and slice results.

## Offline loop

1. Enter before launch and after any material model, prompt, retrieval, policy, tool or data change.
2. Run the exact production pipeline; fit calibrators only on the fitting partition, choose thresholds only on the threshold-selection partition, and evaluate once on the untouched partition.
3. Compare uncalibrated, temperature- or Platt-scaled, and combined-signal models on the metrics above. Reject aggregate ECE gains that worsen critical-slice risk or reviewer capacity.
4. Shadow the candidate against production traffic without granting it authority. Require the preregistered acceptance bounds and no material safety regression.
5. Promote the model-calibrator-threshold-policy bundle atomically, record its effective time and keep the rollback bundle.
6. Repeat until acceptance tests pass or the candidate is rejected, with a hard cap of three fit-and-evaluate rounds per release. Do not tune on the untouched partition; create a new versioned split for a later release.
