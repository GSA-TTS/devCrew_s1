---
id: FR-SELFCONSISTENCY
purpose: Sample, normalize and aggregate several answers to raise reliability and
  estimate confidence, with a three-sample fallback and a bounded workflow
slug: self-consistency-sampling
created: '2026-11-04T14:38:43Z'
updated: '2026-11-04T18:59:49Z'
---

# Self-consistency sampling

Generate several diverse attempts at the same task, map each final answer into a validated equivalence class, then select a class or abstain under limits fixed in advance. Aggregate evidence about answers, never strings, verbosity or the look of independent thought. Samples from one model are draws from one distribution, not independent experts: their errors are often correlated.

Never keep sampling because a preferred answer has not won, never lower a threshold after seeing results, and never let agreement override deterministic evidence.

## Decide whether to use it

Use it when the answer is constrained or reliably normalizable (short maths, multiple choice, symbolic tasks, factual fields with fixed evidence), several routes can reach it, one attempt shows real path variance, extra samples cost less than a stronger model, and disagreement is useful for abstention.

Do not use it when:

- a tool, lookup, test, solver or exact postcondition decides correctness: generate candidates only for coverage and let the checker decide;
- one direct pass already meets the verified target;
- there is no canonical answer (long-form writing, summaries, brainstorming, translation) or several answers are legitimately valid;
- the question is ambiguous, evidence is missing or untrusted, or the prompt carries a false premise every sample shares;
- the decision is safety-critical or irreversible and needs evidence and an audit trail, not a vote;
- normalization cannot avoid silent class splits or merges.

## Fix the run contract before the first sample

Record: objective, answer schema, equivalence rule, allowed evidence, risk tier, required verifier, quality target, abstention behaviour, aggregation, tie and stopping rules, and ceilings for samples, calls, tokens, cost and time. Missing fields: clarify, or apply a documented conservative default. Counters never reset after a profile change or verifier call.

## Design the sampling

- Start near the model's recommended sampling settings; tune one knob at a time. Pick the lowest-variance setting that still yields distinct valid answers. Repeated greedy calls are not self-consistency.
- Generate each sample independently, without showing peer answers or vote totals.
- Raise diversity in this order, only while duplicates stay high: distinct seeds; temperature or top-p within range; reordered examples; paraphrases checked to keep meaning and output format, with no extra hints; a different decomposition; varied retrieval queries; a different model family.
- Track duplicate rate, distinct answer classes and evidence overlap. Lexical variety without answer or error variety does not justify another sample.
- Record seed, model, settings and prompt version; record seed control as `unsupported` rather than inventing one.

## Normalize into equivalence classes

Naive string voting splits `0.5`, `1/2` and `50%`, and merges distinct answers after aggressive cleanup. Normalize in this order:

1. Parse the response against the expected schema.
2. Isolate the final-answer field; do not rely on reasoning text.
3. Keep the raw answer before transforming it.
4. Apply deterministic, task-specific canonicalization.
5. Validate type, units, domain, cardinality and constraints.
6. Compute the class key and note the rules used and any lossy step.
7. Mark failures; never coerce an unparseable answer into the nearest popular class.

Use the narrowest equivalence the task justifies. If pairwise judgements say A equals B and B equals C but A differs from C, that is a normalization failure.

- Numbers: parse fractions, percentages and notation; convert units and reject incompatible ones; set tolerance from the task, never from the samples; a missing required unit makes the answer invalid; keep currencies apart; resolve locale and timezone before comparing dates.
- Sets: deduplicate and sort. Lists: keep order and multiplicity. Records: compare required fields. Multi-label: decide exact, subset or overlap acceptance before sampling.
- Symbolic: simplify under declared assumptions, check boundary values; numeric spot checks only screen; on parser failure reject, never fall back to string similarity.
- Free text: only when the release criterion is semantic. Extract atomic claims, separate core conclusion from optional detail, shuffle candidate order, have the judge return class membership and conflicts (not a merged answer), keep contradictions and different scopes apart, and treat clustering that changes with order as failure. Semantic agreement can still be wrong.

## Aggregate

- Plurality takes the most votes; majority needs more than half. Say which, and report winning share, runner-up share, margin, number of classes and invalid fraction. A 4-3-3 split is not strong consensus.
- Use unweighted plurality when samples share one policy and normalization is reliable.
- Weight by likelihood or stated confidence only after calibration on held-out data, capped per sample; stated confidence is not a probability, and absent log probabilities, never fabricate weights.
- With a calibrated verifier, sum bounded scores per class or take the best-scored candidate; deterministic checks come first.
- A candidate with a unit mismatch, failed test or unauthorized evidence is ineligible.

Tie rule, in order: prefer the class with a decisive deterministic pass; then higher calibrated verifier support; then one deliberately diverse extra sample if budget and expected value allow; then a blinded adjudicator given the task and evidence, not the tallies; otherwise abstain. Never break ties by first sample, longest rationale, highest self-confidence or lexical order.

## Choose sample count and when to stop

Escalation ladder:

1. Run one direct attempt and any deterministic checks; stop if a decisive check passes.
2. Otherwise run an odd batch of three or five.
3. Stop if agreement and release criteria pass.
4. If disagreement is reducible and budget remains, add two or four samples.
5. If samples are redundant, change one diversity dimension instead of adding clones.
6. If a verifier can resolve candidates, use it before another large batch.
7. If disagreement reflects missing evidence, retrieve it or ask the user.
8. If uncertainty is still material at the ceiling, abstain or escalate.

Stop when the leader cannot be overtaken with the remaining samples, or, after a minimum count, when share and top-two margin exceed preset thresholds. Identical paths cannot meet a threshold through repetition. Stop escalating when the leader flips in two consecutive batches without a growing verified margin. A heuristic threshold is not a correctness probability.

## Confidence and abstention

Vote share is not calibrated confidence; duplicates and correlated errors inflate it. Keep three signals apart: agreement (how concentrated support is), correctness confidence (chance the answer is right), and evidence sufficiency (whether required support exists). High agreement never compensates for missing evidence.

Abstain with a specific reason code: ambiguity, missing evidence, normalization failure, low agreement, correlated consensus, verifier conflict, no valid candidate, budget exhausted, safety policy. Never merge them into "low confidence"; each needs a different remedy. Say what would change the decision; offer a verified partial answer or a clarifying question when that reduces harm.

## Three-sample fallback (no infrastructure)

For one-off, low-risk, supervised tasks:

1. Write the normalization rule before any call.
2. Make three calls with the same task and deliberately varied, validated phrasing; ask for a short final-answer field only.
3. Normalize by the rule; use plurality only when answers are unambiguous.
4. Check the winner against any available tool or supplied evidence.
5. Stop at three; never continue until agreement appears.
6. Abstain if all three differ, normalization fails or a critical claim cannot be verified.
7. Note prompts, model, visible settings, outputs, classes, decision and limitations.

This tier is not reproducible; never use it for high volume, high stakes or unattended actions.

## Bounded workflow and limits

1. Contract: complete the run contract.
2. Triage: check whether a tool, lookup or test answers directly; run the cheapest direct attempt and verify it, and keep it if it passes. Sample only when normalization is feasible, diversity can be created and budget fits. At most three routing checks.
3. Dry run: one easy and one adversarial case; repair the setup if outputs are identical, malformed or shifted in meaning.
4. Sampling: mark invalid samples ineligible rather than silently regenerating them. A batch gains only if it adds a new valid path, class, evidence route or verifier-passing candidate. At most one sampling-profile change.
5. Normalization: at most one parse retry; for free text, two blinded judgements plus one adjudication. Abstain if many candidates cannot be classified or the winner depends on an unresolved merge.
6. Diagnosis (low agreement, tie, verifier conflict): name the cause (ambiguity, format split, equivalence defect, missing or conflicting evidence, prompt defect, correlated error, tool failure, adversarial input) and apply one targeted fix. At most two interventions and one extra evidence round; an undirected sample is not a fix.
7. Verification: deterministic checks, then authoritative retrieval or execution, then a blinded model verifier for what remains. A verified minority may defeat the majority; record the override. Abstain if verifiers conflict or nothing passes.
8. Abstention: map to a reason code; one reconsideration after a material new fact. Humans review consequential cases that lack a decisive verifier.
9. Change control: after any change to model, prompt, settings, normalizer or thresholds, re-test against direct and fixed-N baselines; keep the baseline when results are inconclusive.
