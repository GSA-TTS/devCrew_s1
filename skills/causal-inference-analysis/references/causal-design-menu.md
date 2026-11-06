---
created: "2026-11-04T22:59:34Z"
updated: "2026-11-04T23:04:56Z"
---

# Causal design menu

Use the section that matches the step: estimands and assumption categories for the causal question and the assumptions table, strategies for identification, audit checks for the data and design audit, estimators for estimation, checks for refutation and sensitivity, and the counterfactual section for questions about one unit or incident.

## Estimands

Define the estimand before choosing an estimator.

- ATE and ATT: name which one the question asks for; one does not answer the other.
- CATE: supports heterogeneous-effect or uplift decisions. A CATE policy needs validation of both the effect heterogeneity and the decision value.
- Local effect: what IV (compliers) and regression discontinuity (units near the cutoff) identify.
- Controlled direct, natural direct and natural indirect effects: pathway questions that encode different interventions. Natural effects can require cross-world counterfactual assumptions that ordinary treatment ignorability does not imply. Define, identify, estimate and sensitivity-test a mediation target; do not read pathways from regression coefficients.

## Assumption categories

Use these names in the Category column: consistency, SUTVA, exchangeability, positivity (overlap, judged in the target population), exclusion, independence, monotonicity, faithfulness, functional form, missingness, transportability and measurement. The three instrument assumptions (exclusion, independence, monotonicity) are usually not testable from the main data.

Propensity scores balance measured covariates only, not unknown confounders.

## Identification strategies

Try them in this order, keeping the ones the question and data allow. Each line gives what it needs and what it identifies.

1. Randomized assignment: the benchmark design. Randomization protects assignment, not every analysis choice.
2. Backdoor adjustment: adjustment for a measured set of pre-treatment common causes; needs exchangeability and positivity given that set.
3. Frontdoor: a measured mediator under stringent conditions, even when treatment and outcome are confounded.
4. Instrumental variable: relevance, exclusion, independence and monotonicity; identifies a local effect for compliers; weak instruments are a concern.
5. Regression discontinuity: assignment by a fixed cutoff, continuity at the cutoff and no precise manipulation; identifies a local effect near the cutoff.
6. Difference-in-differences: a defensible counterfactual trend for the treated group; staggered adoption needs more than a naive two-way fixed-effect regression.
7. Synthetic control: a credible donor pool and good pre-treatment fit for one treated aggregate.
8. Longitudinal g-methods (parametric g-formula, marginal structural models with inverse-probability weights, structural nested models): for time-varying treatment with confounding affected by prior treatment; they need sequential exchangeability, consistency and positivity.
9. Transport assumptions: carrying an effect from the studied population to another.
10. Partial-identification bounds: a range when no point is identified.

## Design-specific audit checks

- Randomized experiment: interference, noncompliance, attrition, peeking, multiplicity, novelty and external validity.
- Regression discontinuity: manipulation around the cutoff.
- Difference-in-differences: pre-treatment trends.
- Synthetic control: donor-pool quality and pre-treatment fit.
- Instrumental variable: instrument strength and plausibility of exclusion.

## Estimators

Candidates: matching, outcome regression, inverse-probability weighting, augmented inverse-probability weighting and targeted maximum-likelihood estimation.

- Inverse-probability weighting: extreme weights warn of weak overlap.
- Augmented inverse-probability weighting: being doubly robust does not protect against unmeasured confounding, positivity failure or the wrong estimand.

Pairs with different nuisance-model dependencies: outcome regression with inverse-probability weighting, matching with augmented weighting, augmented weighting with targeted maximum likelihood.

## Refutation and sensitivity checks

- Placebo treatment and placebo (dummy) outcome.
- Random common cause and simulated confounder.
- Data subset, bootstrap and leave-one-cluster-out.
- Alternative adjustment sets.
- Negative-control exposures or outcomes: causally irrelevant to the target pathway yet sharing its biases; a failed control reveals concern but does not give the size of the bias.
- Design-specific falsifications (the audit checks above, rerun as tests).
- E-value: the minimum risk-ratio association an unmeasured confounder would need with both treatment and outcome to explain away the adjusted association; give it for the estimate and for the confidence limit nearest the null, with any scale conversion, and note that it addresses one sensitivity model.
- Rosenbaum bounds: for matched designs.

Use one sensitivity family per major bias model plus one complement, and keep distinct sensitivity models as separate results rather than one score.

## Counterfactual questions

- Structural counterfactuals run in three moves: abduction (update the background state from what was observed for the unit), action (replace the mechanism of the intervened variable) and prediction (propagate the changed model with that background state).
- A population interventional effect can be identifiable while the individual counterfactual is not; mediation, probability of necessity and joint potential-outcome claims often need cross-world assumptions or structural restrictions.
- For an incident, state the intervention and its time (would the failure have occurred had the change been rolled back at that time), and separate contributing, necessary and sufficient causes, triggers, conditions and remediation levers. A predictive alert may sit downstream of the failure and be useless to manipulate.
- Root-cause claims need discriminating predictions, intervention or replay evidence, negative controls and alternatives, and a stated attribution type: marginal, conditional, mediated, necessary or sufficient.
