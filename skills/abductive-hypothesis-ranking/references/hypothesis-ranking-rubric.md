---
created: "2026-11-04T19:29:37Z"
updated: "2026-11-04T19:29:37Z"
---

# Hypothesis ranking rubric

Use these records, scales and templates for every hypothesis set, evidence list, test plan and update.

## 1. Explanandum record

- Observation: what changed or failed, the metric or symptom, its unit.
- Time window and baseline: when it started, compared with what.
- Boundary: which system, product, site, segment or population is in scope.
- Decision: what the answer will be used to decide, and the cost of acting on a wrong cause.
- Allowed evidence: what the user has supplied or can collect.

## 2. Mechanism families (coverage checklist)

Before ranking, check the set against each family and add a candidate where one applies:

- Common cause: the frequent, ordinary explanation for this kind of change.
- Interacting or compound cause: two or more factors together, none sufficient alone.
- Observation or measurement failure: tracking, logging, sensor, definition or data-pipeline change that makes the observation an artifact.
- Benign explanation: the observation is expected or harmless once its context is known.
- Other or unknown: the reserve for causes not yet represented. Always present.

Diversity is by mechanism, not wording: two candidates that differ only in phrasing are one candidate.

## 3. Hypothesis record

For each candidate:

- ID and one-line statement.
- Mechanism: how it would produce the observation.
- Scope: which part of the observation it explains, and what it leaves unexplained.
- Assumptions it needs.
- Predicted present: what should be observed if it is true.
- Predicted absent: what should not be observed if it is true.
- Disconfirmer: the observation that would refute it.
- Relation to others: mutually exclusive, overlapping, or composable (can be true together).

Reject a candidate that misses the core observation, contradicts a supplied fact or the timeline, cannot be refuted by any possible observation, or rests on a fact nobody supplied.

## 4. Evidence labels

Each atomic evidence item gets one label:

- Fact: supplied by the user or by an executed observation.
- Retrieved claim: from a document the user supplied, attributed to it.
- Assumption: taken as true without evidence; say so.
- Inference: derived from other items; name them.
- Absence: something not observed; note whether the observation could have detected it.

## 5. Evidence-by-hypothesis matrix

Rate each evidence item against each hypothesis:

- C: consistent (expected if the hypothesis is true).
- N: neutral or not applicable.
- I: inconsistent.
- X: strong contradiction (meets the hypothesis's disconfirmer).

Rules:

- An item rated the same for every hypothesis is not diagnostic; keep it in the matrix but give it no ranking weight.
- Weigh I and X ratings more than C ratings: rank by how little evidence each hypothesis contradicts, not by how many items fit it.
- Do not add the marks up as if they were independent probabilities. Two items from one source or subsystem count as one confirmation.
- Absence counts against a hypothesis only when the observation had a real chance to detect the expected signal.
- Note which single item, if wrong, would change the order (the pivotal evidence).

## 6. Ranking

Keep four fields apart for each hypothesis: evidence fit (from the matrix), prior (base rate, history or an expert range, with its source), testability, and the action it would imply. Then rank:

- Prior: an ordinal band (high, medium, low) unless a defensible numeric base rate exists; never invent decimals.
- Order: first by evidence fit (fewest inconsistencies), then by prior; a vivid rare cause does not outrank a common one on coherence alone, and several common causes together may beat one exotic cause.
- Numbers: label them relative scores unless the set is declared exhaustive and the numbers come from base rates or data; never normalize an incomplete set to 100 percent, and leave weight on Other or unknown.
- Explanatory virtues (scope, precision, mechanism, simplicity, coherence) are tie-breakers, fixed before looking at which answer they favor; they are not probabilities.

## 7. Status labels

Active, weakened, provisionally supported, refuted, merged, split, unverifiable. Mark refuted only when a declared contradiction rule meets a reliable observation; otherwise mark weakened.

## 8. Discriminating test plan

For each candidate test:

- Test: what to look at, query, compare or try.
- Predicted outcome under each active hypothesis.
- Which hypotheses it separates, or which leader it could rule out.
- Cost, delay, risk, privacy impact, reversibility.

Order the tests by how well they separate the leading hypotheses per unit of cost and delay. A test whose outcome is the same under every leader does not discriminate; drop it. A test that only confirms the current leader again is ranked below one that could refute it. Never propose a destructive or hazardous test only to gain information.

## 9. Update record (when the user reports a test result)

- Result, with its label (fact, or collection failure: a test that failed to run is not a negative result).
- For each hypothesis: rank and status before, the effect of this result, rank and status after.
- Status changes and the reason.
- Priors stay as first stated; if new base-rate evidence arrives, state a revised prior as a new version.

## 10. Re-generation triggers and limits

Re-generate when all named hypotheses are refuted, a new result falls outside every candidate's predictions, or after two tests no hypothesis is clearly ahead of the next (with numeric scores: the leader is less than twice the next-best). First diagnose why the set failed: missing mechanism, wrong boundary, compound cause, faulty observation, outdated model of the system, or wrong granularity. Expand only along that diagnosis.

Limits: 3 to 6 hypotheses in the first round; at most 3 new candidates when a coverage check fails; at most 12 active hypotheses; at most 2 re-generation cycles and 6 new hypotheses across them. When a limit is reached, report the case as unresolved.

## 11. Answer template

```markdown
**Observation.** <what, unit, window, boundary>. **Decision it informs.** <decision, or "assumed: ...">

| Rank | Hypothesis | Mechanism | Predicts present / absent | For | Against | Prior | Status | Would change the ranking |
|---|---|---|---|---|---|---|---|---|
| 1 | ... | ... | ... / ... | ... | ... | medium | active | ... |
| - | Other or unknown | not yet represented | - | - | - | - | reserve | ... |

**Discriminating tests (in order).**
1. <test>: if H1, expect ...; if H2, expect ...; cost and risk ...

**Status.** <Leading hypothesis | Supported diagnosis | Unresolved | Not established>: <one sentence>. **What the evidence does not show.** <assumptions linking evidence to cause; tests not yet run>.
```
