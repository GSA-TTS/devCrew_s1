---
created: "2026-11-04T23:04:58Z"
updated: "2026-11-04T23:08:05Z"
---

# Confidence signals

Each entry gives the four fields of a row of the Confidence signals table: Access, Target event, Use, Caveat. Fill Target event from the monitored decision when the entry says so.

## Black-box signals (API access only)

### Verbalized confidence
- Access: black-box.
- Target event: the event named in a separate, tightly specified question, for example the probability that this normalized answer passes the stated validator. A bare question about how confident the model is, without a target, gives no target event.
- Use: cheap, easy-to-explain score, used after calibration.
- Caveat: models tend to be overconfident, no tested elicitation method dominates across tasks, and professional-knowledge tasks remain difficult. Parse only a bounded numeric field and keep the raw response for protected debugging if policy permits.

### P(True)
- Access: black-box.
- Target event: the proposed answer is correct.
- Use: accept or reject a candidate.
- Caveat: keep its label separate from P(IK): a model may know the topic yet produce a defective answer.

### P(IK)
- Access: black-box.
- Target event: the model knows the answer (answerability), predicted before it commits to one.
- Use: route the request or allocate effort.
- Caveat: its calibration generalized imperfectly to new tasks; a model may guess correctly without reliable knowledge.

### Critique, judge or consistency judgment
- Access: black-box.
- Target event: the candidate passes a rubric or matches reference answers or evidence.
- Use: independent verifier or a feature of the combined score.
- Caveat: intrinsic self-correction is not a dependable verifier; models can fail to correct reasoning without external feedback and can degrade their first answer, so give the critic independent evidence, deterministic test results, or a rubric with reference answers. Judges show position, verbosity, self-enhancement and limited-reasoning effects, self-preference for their own generations, and sycophancy. Randomize candidate order, normalize length, hide model identity, include counter-sycophancy tests, use reference-based checks, and adjudicate consequential disagreements with independent humans or deterministic evidence. Two correlated judges are not independent confirmation, and a generator-judge pair can collude around the same shortcut. A stated rationale is an inspectable artifact, not the causal reason or evidence that the model is certain.

### Self-consistency agreement
- Access: black-box, several generations.
- Target event: concentration of support for the leading normalized answer (agreement), not correctness.
- Use: agreement signal, from the leading cluster's frequency or entropy.
- Caveat: agreement is not calibrated correctness; correlated samples can repeat one misconception, injected premise or memorized shortcut. Never keep sampling until a desired answer wins.

### Semantic entropy
- Access: black-box, several generations.
- Target event: uncertainty over groups of generations that express the same meaning; it was more predictive of question-answering accuracy than comparable baselines and has detected confabulations across datasets and tasks.
- Use: uncertainty score where surface-form agreement splits equivalent answers.
- Caveat: pin the sampling policy, equivalence model, bidirectional entailment rule, clustering algorithm and sample count; treat clustering errors as estimator errors. It costs several generations and does not fit a strict single-call path.

### Sampling-based contradiction check
- Access: black-box, several generations, no knowledge source.
- Target event: the samples contradict each other on a claim.
- Use: warning signal when no knowledge source is available.
- Caveat: consistency is not truth.

## Evidence signals

### Claim support
- Access: any; needs a knowledge source or retrieval.
- Target event: each atomic claim is supported by a reliable source.
- Use: claim-level accept, remove or veto; long-form factual precision is the proportion of atomic facts supported.
- Caveat: give each claim an ID, a source requirement, cited evidence IDs and a support status. Use deterministic matching for identifiers and quantities, natural-language inference for entailment only after validating it on the domain, and a human adjudicator for material ambiguous claims. A document-level score must not hide one critical unsupported claim. Retrieval grounding is necessary but insufficient: measure passage relevance, answer faithfulness, citation entailment, currency and authority. In closed corpora, deny unsupported external claims.

### Guardrail model
- Access: any.
- Target event: a policy class, an injection attempt or an obvious unsupported claim.
- Use: policy and injection screening.
- Caveat: keep it independent of the generator where feasible and evaluate false negatives by attack family. A guardrail score never overrides a deterministic policy violation.

## White-box signals (log probabilities or model access)

### Token log probability, token entropy, candidate-label probability
- Access: white-box or log-probability-enabled API.
- Target event: the model's local next-token distribution, not factual correctness.
- Use: score fixed-format labels where possible, or use mean log probability per scored token, still stratified by output length.
- Caveat: raw sequence log probability is a sum and generally decreases with length. Do not compare free-form sequence scores across templates without validating the normalization. Structured outputs complicate token- and sequence-level uncertainty.

### Ensemble
- Access: independently trained models or materially different model families.
- Target event: epistemic disagreement among members.
- Use: uncertainty that is often strongly calibrated, including on unfamiliar inputs.
- Caveat: needs parallel compute and genuinely diverse members; several API aliases backed by one model are not an ensemble.

### Monte Carlo dropout
- Access: model access (dropout kept at inference).
- Target event: spread across repeated sampled passes, an approximation of Bayesian inference.
- Use: uncertainty score where the model can be run with dropout.
- Caveat: adds latency and should not be presumed robust under shift.

## Set-valued calibration

### Conformal prediction
- Access: any score that can serve as a nonconformity score, plus a held-out calibration set.
- Target event: the returned prediction set contains an acceptable answer at a target error level.
- Use: prediction set or abstention policy; conformal language modeling calibrates sampling and rejection rules so a small response set contains an acceptable answer with high probability.
- Caveat: guarantees are marginal and rely on exchangeability between calibration and test examples, so drift can break coverage. Log realized set coverage and set size, and never present the nominal level as an unconditional guarantee after a distribution change.

## Uncertainty under shift

Many uncertainty methods and post-hoc calibration degrade under dataset shift; model-marginalizing methods were comparatively strong in large comparisons. Calibration can collapse on out-of-distribution inputs: detect novelty and route those cases separately rather than stretching an in-domain probability.

## Combining signals

Combine signals only through a versioned rule or model fitted on held-out data. Features may include P(True), normalized log probability, semantic entropy, agreement, retrieval coverage, claim support, verifier status, novelty, tool errors and budget state. Avoid correlated double-counting. Require improvement over the best single-signal baseline in selective risk.

## Signal records

Parse every signal into a typed record with its target, direction, range, source, model and prompt version, and validity status. Reject malformed, out-of-range, injected or unavailable signals rather than coercing them. Validate structured signals outside the prompt.
