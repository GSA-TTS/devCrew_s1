---
created: "2026-11-05T00:38:23Z"
updated: "2026-11-05T00:38:23Z"
---

# Claims and verification questions

Use this when filling the Claim, Type and Question cells of the ledger.

## What becomes a row

Write a row for every proposition a reasonable reader could treat as true about the world, a supplied document, a computation, a policy or an artifact, whether the draft states it or implies it. Typical kinds: existence or identity of an entity, membership, dates and durations, locations, quantities and units, rankings, quotations, attributions, causal relations, comparisons, technical capabilities, current availability, legal or policy status, and a statement that a cited source supports a proposition.

Content that is not an ordinary factual claim gets a label in the Type cell instead of a factual type:

- opinion: pure opinion, aesthetic preference, or advice whose correctness depends on values rather than evidence;
- prediction: forecasts, possibilities and counterfactuals;
- hypothetical: content clearly labelled as fictional or hypothetical;
- normative: legal, policy or ethical judgements that need accountable interpretation;
- not verifiable: a proposition with no operational truth condition.

## Splitting a sentence into claims

- A claim is atomic when one verdict can apply to the whole of it. Split a conjunction when either side could be true on its own.
- Separate identity from date, action from cause, quantity from comparison, and quotation text from attribution.
- Keep qualifiers such as as of, approximately, in the United States, among public companies, according to the report and caused by: removing them changes the proposition.
- Numbers: keep value, unit, scale, denominator, time window, population, currency, nominal or real basis, and rounding. Percentages: keep the denominator. Ranges: keep both bounds and whether they are inclusive. Dates: keep timezone and calendar when they matter.
- Causal claims: one row for each event occurring and one for the causal link; evidence that two events co-occur is not evidence of cause.
- Implicit claims: ask what a reader must believe for the sentence to make sense. A phrase such as the second-largest provider implies the entity exists, belongs to a comparison set and ranks second under some metric and time; add those rows when they matter to the draft's point.
- Resolve pronouns and local references by adding only the context needed, without changing the proposition under test.

## Question form by claim type

- Existence or identity: which entity has the defining attributes.
- Membership or list inclusion: which entities meet the criteria, not whether the draft's entity counts.
- Date or chronology: when the event occurred and, when needed, which event came first.
- Number or quantity: the value with its unit, denominator, date and source basis.
- Quotation or attribution: who made the statement, where, and whether the wording is exact or paraphrased.
- Capability or availability: whether the feature exists in the named product version, region, plan and date.
- Comparison or ranking: the metric, the comparison set, the period and the order.
- Causal: separately, whether the cause occurred, whether the effect occurred, and what evidence supports a causal link.
- Citation support: whether a named source passage entails the exact claim and whether it contradicts any qualifier.
- Computation: the inputs, then the result worked out step by step.

Ask open questions (when did it happen) rather than yes-or-no questions that carry the draft's value (did it happen in that year): yes-or-no forms invite agreement with the premise.

## Standalone wording

- A question must name the entity, time frame, jurisdiction, document version, comparison class and definitions needed to answer it without the draft.
- Leave out the draft's asserted value and any wording that signals agreement, loaded premises or unsupported assumptions.
- Context added only to identify the subject (a person's title, for example) is not under test unless it has its own row; keep clear which proposition gets the verdict.

## Coverage

- Every claim with a factual type maps to at least one question or to a direct computation.
- One question may cover several rows only when their expected evidence and verdict cannot be separated; every question maps back to at least one row.
- Merge two questions only when they cover the same rows and need the same evidence; keep distinct qualifiers, dates, units, jurisdictions and attributions apart.
- For a Critical row, ask what other reading of the claim or what counterevidence the current wording could miss, and widen the question to cover it.
