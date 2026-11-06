---
created: "2026-11-05T00:02:08Z"
updated: "2026-11-05T00:02:08Z"
---

# Records and label sets for each part of the analysis

One section per output part, in output order. Each gives what the part's fields hold and the labels allowed in them.

## 1. Task specification

- Domain: free text naming the topic family.
- Topic unit: what counts as one topic or state (a threat vector, a product category, an indicator, a policy, a behaviour).
- Stakeholder and decisions: whose perspective, and which decisions the analysis informs (resource allocation, risk mitigation, product roadmap, policy design).
- Past horizon: start and end.
- Future horizon: baseline horizon and extended horizon.
- Granularity: the time resolution (for example quarterly or yearly) and the minimal meaningful change, the smallest change in an attribute that counts as a change.
- Objectives: a ranked list.
- Constraints: limits on data, compute and time.

## 2. Time axis

- Time metric: calendar time, age or tenure, or event time (time since launch, time since an intervention); several may run in parallel.
- Intervals: equal length (years) or irregular but meaningful (policy regimes, market cycles).
- T0: the latest time from which projections start; it can differ from today when the data stop earlier.
- Forecast horizons: near-, medium- and long-term windows, with the step size.
- Mapping rule: how a dated record is placed in an interval (for example, map all timestamps to quarterly bins by end-of-quarter date).
- Look-back and look-ahead: no information dated after an interval is used to describe that interval.

## 3. Landscape per interval

- Topic ID: a stable identifier kept across all intervals; a topic re-defined later keeps its ID only if its meaning is unchanged.
- Attributes: prevalence, intensity, magnitude, severity or importance, as counts or rates per interval, continuous measures (mean, median) or derived indicators (scores, composite indices). Relationships (subtopics, co-occurrence, clusters) go here when they matter to a transition.
- Quality flag: ok, sparse (little data for the interval), gap (no data), or measurement change (a change in reporting standard, unit or definition in this interval).
- When topics are not given by the user, define them by a taxonomy or by grouping the evidence, and keep the same definitions in every interval.

## 4. Transitions

Labels (one per row):

- Emergence: the topic appears with no prior counterpart, or with past presence below the threshold.
- Disappearance: present at the earlier interval, absent or below the residual threshold at the later one.
- Intensification: an increase in prevalence or severity larger than the threshold.
- Mitigation: a decrease in prevalence or severity larger than the threshold.
- Plateau: change within the threshold.
- Shift in focus: the topic's relationships or subcomponents change (an attack moving from one vector to another).
- Split (one topic becomes several), Merge (several become one), Reconfiguration (cluster structure changes).

Matching: link each topic to its counterpart in the next interval by identity, label or overlap of members; allow one-to-one, one-to-many (split), many-to-one (merge) and no match (candidate emergence or disappearance).

Transition summary: a matrix with one row per step (interval pair) and one column per label, holding the count of rows with that label.

## 5. Patterns

- Pattern type: monotonic trend (growth or decline), regime shift or structural break, cycle or seasonality, diffusion (S-curve, adoption wave), or shift in cluster or interaction structure.
- Time scale: short-, medium- or long-term.
- Life-cycle stage: emergent, growth, maturity or decline, with the quantitative threshold used for the stage written in the cell.
- Strength or robustness: significance, effect size or support (how many intervals or sources show it).
- Methods, where figures allow: time-series or longitudinal models for numeric attributes, Markov or hidden Markov models for regime labels, change-point detection for shifts in mean, variance or trend, sequential pattern mining for event sequences.

## 6. Drivers

- Hypotheses: list candidates by political, economic, social, technological, environmental, legal, organizational and behavioral factors, or from a causal diagram, plus interventions, competitor actions and outside events found in the evidence.
- Evidence type: quantitative association (correlation or regression), causal estimate, or expert judgment (structured elicitation such as Delphi or scenario workshops, with assumptions written down).
- Causal identification: a stated causal structure (a directed acyclic graph with its adjustment set), checked temporal precedence, and a method such as difference-in-differences, propensity scores, instrumental variables or synthetic controls.
- Strength and direction: the sign of the influence and an effect size when the evidence gives one.
- Window: the period in which the driver acts.
- Confidence: high, medium or low, with the key assumptions.

## 7. Forecasts

- Model classes: classical time-series (ARIMA or SARIMA, exponential smoothing, TBATS), regression or causal driver-based models, machine-learning or foundation models for time series. The choice must respect the data's non-stationarity, seasonality and missingness.
- Simple baselines for comparison: naive, seasonal naive, linear trend.
- Evaluation: rolling-origin backtesting or time-series cross-validation, not random splits.
- Scenarios: optimistic, base, pessimistic or exploratory narratives, each with its driver trajectories; a subjective probability per scenario is optional.
- Ensembles: stacking, weighted averaging or distributional ensembles, to reduce structural uncertainty.
- Model metadata: model type, training window, performance against the baselines.

## 8. Uncertainty profile

- Statistical: prediction intervals from parametric methods (residual variance, Bayesian posterior predictive) or distribution-free methods (conformal prediction, including time-series extensions), each with its nominal level.
- Calibration: interval coverage on held-out data compared with the nominal level.
- Structural: spread across model classes.
- Scenario: spread across scenarios.
- Data: intervals or topics with poor quality or high missingness, with the likely direction of bias.
- Narrative: the main sources of uncertainty for the quantity and what evidence would reduce them.

Format of one row, with placeholders:

```text
| Q1 <quantity> | <step> | <central> | <low> to <high> (<level> interval) | coverage <x> against <level> on <n> held-out steps | <main sources of uncertainty>; <evidence that would narrow it> |
```
