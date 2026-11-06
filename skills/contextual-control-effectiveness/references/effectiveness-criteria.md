---
created: "2026-11-04T19:52:15Z"
updated: "2026-11-04T19:52:15Z"
---

# Criteria for control effectiveness by context

## 1. Scope

- Decision question: the choice the analysis informs (which control to deploy for which segment, site or condition).
- Population, systems or domains the findings apply to, with inclusions and exclusions.
- Stakes: low, medium or high, from risk tolerance and consequence severity; higher stakes call for more rigour.
- Assumptions about how each control works and how far findings generalize.

## 2. Control inventory

- For each control: mechanism of action, resource requirements, implementation complexity, known preconditions.
- Type: preventive, detective or corrective; deterministic or probabilistic; static or adaptive.
- Controls must be distinct from each other (not redundant); the set should span the options, established and novel.

## 3. Contextual factors and strata

- Factor categories: environmental (physical conditions, infrastructure, resources), population (demographics, capability, behaviour, baseline risk), temporal (period, season, maturity stage, trend), organizational (governance, culture, policies, decision processes), technical (architecture, data characteristics, computational limits).
- Prioritize factors by plausibility, measurability, variance in the target population and actionability.
- Continuous factor: set meaningful boundaries (quartiles, domain thresholds or cut-points). Categorical factor: categories mutually exclusive and collectively exhaustive.
- Measure factors at baseline, before the control was applied, to avoid post-treatment bias.
- Each observation falls in exactly one stratum; each stratum needs enough cases for a stable estimate.

## 4. Evidence and data

- Per control and stratum, collect: outcome measures, process metrics, resource use, adverse events, implementation fidelity.
- Evidence sources: randomized trials (when ethical and feasible), observational studies with comparison groups, historical records and databases, simulation, and expert assessment (only when empirical data are unavailable).
- Harmonize units and scales across sources; check for systematic measurement error between contexts.
- Missing data: impute, run a sensitivity analysis, or exclude with a stated reason.
- Stop and ask the user when the outcome is missing entirely or takes only one value, or when the data cannot be read or are empty.

## 5. Effect metrics

| Outcome type | Metrics | Estimation |
|---|---|---|
| Binary | risk difference, relative risk, odds ratio, number needed to treat | logistic regression or risk difference |
| Continuous | mean difference, standardized mean difference (Cohen's d, Hedges' g) | linear regression or t-test |
| Time to event | hazard ratio, survival curves, median time difference | Cox proportional hazards or Kaplan-Meier |
| Count | effect from the regression | Poisson or negative binomial regression |
| Composite | multi-criteria score, cost-effectiveness ratio, utility measure | a stated weighting scheme across the outcomes |

- Say whether the scale is absolute (differences) or relative (ratios); an interaction can appear on one scale and not the other (additive versus multiplicative).
- Set a minimum important difference (MID) for the primary outcome; add secondary outcomes (safety, cost, user satisfaction) where they bear on the choice.
- For each control and stratum record: effect estimate, 95% confidence interval, p-value, sample size, and whether the method's assumptions hold.

## 6. Effectiveness rating per control and stratum

- Effective: the effect exceeds the MID and the confidence interval excludes the null.
- Partially effective: the effect exceeds the MID but the interval includes the null, or the effect is below the MID but significant.
- Ineffective: the effect does not exceed the MID, or the interval includes harm.
- Insufficient data: flag the stratum. At least 30 to 50 observations per stratum are recommended; below that, estimates are unstable. Pool adjacent strata only if they are conceptually similar, or accept coarser strata.
- Rank the controls within each stratum (descending for a benefit, ascending for a harm), name the top performer and its margin over the next best.
- Rate the quality of the evidence behind each estimate, and keep statistical significance apart from practical significance: a detectable but small difference may not matter operationally.

## 7. Differences across strata

- For each control, compare its estimates across all strata and test heterogeneity: Q statistic and I squared, chi-squared test, or interaction terms in a regression.
- If effects differ: name the outlying strata, find threshold values of continuous factors where effectiveness shifts, and flag the control for interaction testing.
- Check that the difference is not due only to differences in study quality or measurement error.

## 8. Interactions

Types:
- Quantitative: the size of the effect changes across contexts, the direction does not.
- Qualitative (crossover): the direction reverses, beneficial in some contexts and harmful in others.
- Synergistic: the combined effect exceeds the sum of the individual effects.
- Antagonistic: the combined effect is less than the sum of the individual effects.

Testing and description:
- Model the outcome on control, moderator and control by moderator (plus confounders); test with a Wald or likelihood ratio test.
- Adjust for multiple testing (Bonferroni, false discovery rate or hierarchical shrinkage) when many interactions are examined.
- Measure magnitude with the relative excess risk due to interaction, the synergy index or an interaction contrast.
- Detecting an interaction typically needs about four times the sample size of a main effect; say when the data are underpowered for it.
- For each significant interaction give the effect at each moderator level, the crossover point where the ranking of controls changes, and the pattern (dose-response, threshold, non-linear).
- Rule out artifacts such as ceiling effects or unreliable measurement in small subgroups.
- Examine three-way interactions only when theory justifies them and the sample permits; keep any complex model interpretable.

Credibility:
- Criteria: pre-specified, magnitude above the minimum detectable effect, precise estimate, plausible mechanism, consistent across related outcomes, survives multiple-testing correction, groups balanced within moderator levels, not explained by another factor.
- Score as the share of criteria met (0 to 1): high at 0.8 or more, moderate from 0.5 to 0.79, low below 0.5.
- For a low-credibility interaction give an alternative explanation (chance finding, residual confounding) and give it less weight in the rules.
- Flag for human review any crossover interaction and any qualitative interaction with major policy implications.

## 9. Decision rules

- Keep a contextual factor in the rules only if it changes the ranking of controls across its levels; otherwise omit it.
- Rule form:

```text
IF <context condition>
  RECOMMEND <control>  (rating: <effective | partially effective>)
  ALTERNATIVES <control, control> if the primary is unavailable
  EXPECTED OUTCOME <estimate> [95% CI <low> to <high>]
  EVIDENCE <high | moderate | low>
```

- Weigh effectiveness against cost, feasibility and risk in a decision matrix; a control that is better on every criterion dominates, otherwise list the trade-offs between the Pareto-optimal ones.
- Edge cases: for overlapping strata or continuous factors, draw smooth boundaries; for an ambiguous context, recommend the control with the best worst-case performance across the plausible strata; for a novel context, flag for human review and recommend the control with the broadest effectiveness profile.
- Contradictory rules: refine overlapping context definitions; widen uncertainty margins where measurement error pushes cases across a threshold; where controls are truly equivalent, recommend both as equivalent.
- Effects differ across strata but no interaction is found (possible causes: small strata, a non-linear pattern, an unmeasured moderator): try another stratification, note that the mechanism is unclear, and recommend the control with the best average performance with that caveat.
- A combination that cannot be estimated: mark it missing with the reason and leave it out of the recommendations.
- Coherence: every context combination gets a recommendation; no context gets two contradictory ones; small changes in context do not flip the recommendation; recommended controls are feasible under the stated resource limits. Flag for human review when the rules contradict expert judgement or are unstable in more than 15% of contexts.
- Frequent switching between controls has costs (transition overhead, learning curves, coordination); a stabilization period before switching may be appropriate.

## 10. Limitations and monitoring

- Finer strata give more specific findings but less power within each stratum.
- Many control and context combinations inflate false positives; pre-specified hypotheses partly mitigate this.
- Findings may not transfer to other populations, settings or periods: state the boundary conditions and validate in independent samples before wide deployment.
- Observational data can carry unmeasured confounding: report a sensitivity analysis with the estimates.
- Measurement error in factors or outcomes weakens estimates and can misclassify contexts; misclassifying the current context leads to the wrong control.
- If contexts correlate with protected attributes (race, gender, socioeconomic status), check whether context-based selection produces equitable outcomes across groups; where the best control is costly or scarce, name the allocation question.
- Monitoring triggers: performance degradation, a shift in the distribution of contextual factors, an unexpected performance pattern, and a scheduled re-evaluation as evidence accumulates.

## Example of a rule pair (format only)

Road-safety interventions compared across road type and lighting:

```text
IF road = rural two-lane AND lighting = unlit
  RECOMMEND edge-line rumble strips  (rating: effective)
  ALTERNATIVES retroreflective delineators
  EXPECTED OUTCOME <crash reduction> [95% CI <low> to <high>]
  EVIDENCE moderate (two observational studies with comparison sites)

IF context not seen in the evidence (for example a mountain pass with seasonal closure)
  FLAG for human review
  RECOMMEND the intervention rated effective in the most strata
```
