---
created: "2026-11-04T19:30:52Z"
updated: "2026-11-04T19:36:00Z"
---

# Criteria and tables for forecasting control misalignment

One section per stage of the method. Each gives the criteria to apply and the table layout to fill.

## 1. Scope and horizons

- Scope: name each capability and threat under analysis (for example automation capabilities, attack vectors, regulatory requirements) and the operational area it touches.
- Horizons: short term 6 to 12 months, medium term 1 to 3 years, long term 3 to 5 years or more. Tie each horizon to a milestone the user plans around (budget cycle, system refresh, contract renewal, rule effective date) where one is known.
- Experts: for each capability or threat area, name the role that should challenge the forecast (security architect, fraud lead, identity program owner, counsel).

## 2. Scenarios

- Driving forces: list the forces in four groups: economic, technological, regulatory, social.
- Critical uncertainties: keep the forces that are high impact and low predictability; these are the axes the scenarios differ on.
- Build 3 to 5 scenarios, always including a most-likely and a worst-case one; a best-case one is optional. Each scenario is internally consistent (its assumptions do not contradict each other) and the set does not overlap (no two scenarios describe the same future).
- Each scenario gets: a one-line narrative, its horizon, the trigger events that would show it is arriving, and a likelihood rating with its basis.
- Quantitative trend: only when the user supplies a time series for a capability or threat measure (attack volume, tool cost, time to exploit). Fit a simple trend, give the projection with a confidence range, and state the method and its fit error (mean absolute error or similar). With short or noisy series, fall back to a moving average and label the result lower confidence.

Scenario table:

| Scenario | Horizon | Driving forces | Trigger events | Likelihood (basis) |
|---|---|---|---|---|

## 3. Control-context map

Inventory attributes per control: purpose and risk addressed, type (preventive, detective or corrective), frequency, owner, evidence it produces, dependencies.

Context mapping per control: the environmental factors it mitigates (technical, operational, regulatory, market), the design assumption it rests on (what must stay true for it to work), and the measurable context parameter that would show the assumption failing.

Current effectiveness baseline: rate coverage (how much of the risk the control's scope addresses) and impact (how much it reduces the risk) and combine them into one rating. Mark whether the rating rests on a design test (does the control logic address the intended risk, does the owner have the authority and access) or on an operating test (sampled executions over a period, usually 12 months); with neither, mark it not tested.

Control-context table:

| Control | Type | Context addressed | Design assumption | Context parameter | Current rating (basis) |
|---|---|---|---|---|---|

## 4. Misalignment detection

For each control and each scenario, compare the control's current capacity with the demand the scenario places on it, and record the shortfall, its size and when it appears.

Misalignment types (assign exactly one primary type; add a secondary type in the notes if needed):

- Capacity: the control lacks the scale or throughput the future volume needs.
- Coverage: the control's scope does not reach the evolved threat surface.
- Technology: the control relies on a technology the future threat defeats or that becomes obsolete.
- Process: the control's workflow does not fit how operations will run.
- Timing: the control responds more slowly than the threat now moves.

Root cause: ask why the gap exists until the answer is a design assumption or a dependency (the Five Whys technique); for a gap with several contributing factors, group them by cause category (fishbone diagram); for a gap that needs several conditions to fail together, lay out the combination (fault tree). Record the evidence for each root cause.

Stress tests: for each serious gap, state the boundary condition at which the control fails (volume, speed, technique) and how sensitive the finding is to the scenario's assumptions.

## 5. Prioritization

- Likelihood: the chance the scenario materializes and the control then fails.
- Impact: the severity if the control fails, across financial, operational, reputational and compliance consequences.
- Score: likelihood times impact on one stated scale (for example 1 to 5 each, giving scores from 1 to 25). Apply the scale the same way to every misalignment.
- Adjusting factors, recorded beside the score and used to break ties or raise urgency: organizational preparedness, interconnectedness (failure of this control triggers other failures), velocity (how fast the threat evolves), regulatory mandate, and time to misalignment.

Priority table:

| Rank | Control | Scenario | Type | Likelihood | Impact | Score | Velocity | Time to misalignment | Other factors |
|---|---|---|---|---|---|---|---|---|---|

## 6. Adaptation options

Option patterns, of which each critical misalignment gets at least 3:

- Strengthen: raise frequency, widen scope or upgrade the technology of the existing control.
- Replace: a new control mechanism in its place.
- Compensate: a supplementary control that covers the gap.
- Automate: use automation or AI to scale capacity.
- Redesign to prevent: move from a detective control to a preventive one.

Adaptive behaviour (for controls that must keep fitting a changing context): adjust the control's parameters from measured error (direct), estimate how the environment is changing and then update the control (indirect), or combine both (hybrid); or define distinct control states that switch on context signals.

Feasibility, rated per option as High, Medium or Low on four dimensions:

- Technical: maturity and availability of the technology needed.
- Operational: fit with existing processes and systems.
- Resource: budget, staff and time needed.
- Organizational: culture, change readiness and skills.

Dependencies: name what must be in place first, sequence options along those chains, and flag which can run in parallel. A dependency cycle means the sequence is wrong: break it by splitting one option.

## 7. Selection

Structured decision-making:

1. Decision context: which adaptations to adopt for which misalignment, by when.
2. Objectives: risk reduction, cost efficiency, implementation speed, sustainability, each with a measure.
3. Alternatives: the options that passed feasibility.
4. Consequences: estimate each option's result on each objective in a consequence table.
5. Trade-offs: weight the objectives (weights sum to 1.0), compute a weighted score, and note where objectives conflict.
6. Decide: recommend the top option, with the runner-up and the variable that would flip the choice.

Consequence table:

| Option | Risk reduction | Cost | Speed | Sustainability | Weighted score |
|---|---|---|---|---|---|

Plan for each selected adaptation: sequence position, dependency, owner role, success measure, and rollback trigger (the failure criterion that sends it back to the prior control).

## 8. Early warning indicators

For each scenario that drives a top misalignment, define a measurable signal that the scenario is unfolding, its threshold, and the action when it is crossed (bring the adaptation forward, start the pilot, re-run the forecast). Prefer signals that the user already collects. Check each threshold against past data where available, so it neither fires constantly nor never fires.

| Indicator | Scenario | Threshold | Action when crossed |
|---|---|---|---|

## 9. Data quality and errors

- Completeness: note missing controls, missing attributes or gaps in a time series and what they affect.
- Accuracy and consistency: when sources disagree, prefer the more authoritative one (official advisory or standard over vendor marketing, recent over old) and say which was used.
- Timeliness: give the date of each external fact.
- Fallbacks: when a quantitative forecast is not possible, use scenarios with qualitative likelihoods and label them judgement.
