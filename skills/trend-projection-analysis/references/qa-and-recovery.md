---
created: "2026-11-05T00:02:08Z"
updated: "2026-11-05T00:02:08Z"
---

# Checkpoints per part and recovery by symptom

## Checkpoints

Apply the checkpoint of a part as soon as the part is written.

- Task specification: objectives are specific and do not contradict each other; the horizon and granularity are feasible for the data expected; the topic unit is clearly defined.
- Time axis: intervals cover the whole past horizon with no unintended gaps; no information dated after an interval describes that interval; the granularity is justified by how often the data are reported.
- Landscape: no impossible values (negative counts); coverage matches the time axis; an interval with little data is flagged; topic definitions are the same in every interval; no interval is empty unless there was no activity, which is then said; descriptive figures look plausible (no explosive outlier without a reason); level shifts that coincide with a change in measurement or reporting, and units or definitions that change over time, are flagged rather than read as real change.
- Transitions: many emergences and disappearances at every step point to misaligned or inconsistent topic definitions rather than real change; labels are re-checked under an alternative threshold.
- Patterns: model assumptions are met or noted; a pattern is not an artifact of the start or end of the data; trend models backtest with acceptable error.
- Drivers: each driver precedes or coincides with the change it is said to drive; correlations are not over-read as causes without appropriate methods; results hold under alternative model specifications.
- Forecasts: backtest performance is compared with the naive or simple-trend benchmark; projections respect domain constraints (no negative counts); scenario assumptions are explicit and consistent with each other.
- Uncertainty profile: interval coverage is close to the nominal level on held-out data; high-uncertainty zones are flagged and explained; the narrative agrees with the numeric intervals.
- Synthesis: every major conclusion traces to evidence and to rows of the earlier parts; limitations and uncertainties are kept; no part contradicts another.

## Recovery by symptom

- Large gaps or uneven sampling: mark the gaps; avoid naive interpolation across a structural gap, and instead restrict the modelling to covered periods or use methods robust to irregular spacing (mixed-effects or irregular time-series models); widen the uncertainty for affected periods.
- An abrupt change at the time of a metadata or method change (a new reporting standard): check for the method change, locate the shift by change-point detection, then re-base the series, add an indicator for the break, or analyse the periods before and after separately.
- Topics appear and disappear through instability of the grouping, not real change: use the same grouping in every interval and align groups across intervals, raise the support needed to count a topic, and put low-support items under a noise or other topic.
- A model fits history well but backtests poorly: simplify or regularize it, use fewer predictors, backtest with rolling windows at realistic horizons, and prefer an interpretable model when driver inference matters.
- A strong correlation read as causation: without causal identification, label the driver associated and say why.
- Projections swing with small changes in history or configuration: re-estimate without the most recent periods and compare, use ensembles or robust models, and where appropriate shorten the horizon and flag longer-range projections as highly uncertain.
