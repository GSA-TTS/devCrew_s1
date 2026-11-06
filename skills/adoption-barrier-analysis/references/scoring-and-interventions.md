---
created: "2026-11-04T19:29:55Z"
updated: "2026-11-04T19:35:11Z"
---

# Prioritization scoring and intervention matching

## Multi-criteria scoring

Criteria, each scored 0 to 100, where a higher score always means a stronger case for acting on the barrier first:

| Criterion | Question | 0 | 100 |
| :-- | :-- | :-- | :-- |
| Magnitude | How many people or units does it affect? | very few | the whole target population |
| Severity | How strongly does it impede adoption? | barely | blocks adoption |
| Modifiability | How feasible is it to address? | fixed | easily addressed |
| Cost-effectiveness | Expected return on the effort to address it | poor | high |
| Equity | Does addressing it reduce disparities or help vulnerable groups? | no | strongly |

Steps:
1. Score every barrier on every criterion; no cell left empty. Use the user's figures where given (normalize them to 0 to 100); otherwise give a judgement score and label it estimate.
2. Weights: use the decision-makers' weights (from pairwise comparison or direct rating) when the user gives them. Otherwise use the default set and label it default: magnitude 0.30, severity 0.30, modifiability 0.20, cost-effectiveness 0.15, equity 0.05. Weights must sum to 1.0; if supplied weights do not, divide each by their total.
3. Priority score of a barrier = sum over criteria of weight times score.
4. Rank barriers by priority score, highest first. The top 3 to 5 are the barriers for immediate intervention.
5. Sensitivity: recompute with at least one alternative weight set, such as an optimistic, a pessimistic or a balanced scenario, and state whether the top-ranked barriers change. A ranking that changes under reasonable weights is reported as unstable. Example sets, a convention of this skill rather than of the method: equal weights of 0.20; or modifiability raised to 0.40 with magnitude and severity lowered to 0.20 each.

Compact example (weights default): magnitude 80, severity 70, modifiability 90, cost-effectiveness 60, equity 40 gives 0.30 x 80 + 0.30 x 70 + 0.20 x 90 + 0.15 x 60 + 0.05 x 40 = 24 + 21 + 18 + 9 + 2 = 74.

Alternative formula that weights severity more (Hanlon method, adapted):
priority = (magnitude + 2 x severity) x modifiability x PEARL,
where PEARL is 1 only if acting on the barrier is Proper (appropriate), Economical (resources exist), Acceptable to stakeholders, Resourced (staff and technology reachable) and Legal; any "no" makes PEARL 0 and drops the barrier from the action list. Use it when the user asks for it or when feasibility screening matters more than fine ranking; state which formula was used.

## Overall constraint degree (when blocking, delay or reduction figures exist)

- Adoption ceiling = 100% x product of (1 minus blocking rate) over all blocking barriers. Two barriers blocking 25% and 10% give 100% x 0.75 x 0.90 = 67.5%.
- Delay index = sum of (share affected x delay) over slowing barriers, in days.
- Quality reduction = sum of (share affected x reduction) over reducing barriers.
- Barrier burden = w1 x (1 minus ceiling) + w2 x (delay index / longest acceptable delay) + w3 x quality reduction, on a 0 to 1 scale (0 no constraint, 1 maximum), with w1 to w3 summing to 1.
- A ceiling above 100% or a rate below 0 is a calculation or input error: recheck the inputs before reporting.

## Intervention matching

Match on the barrier's root cause, not its symptom.

| Determinant | Intervention strategies |
| :-- | :-- |
| Knowledge | education, training, job aids, decision support tools |
| Attitudes | testimonials, persuasive messaging, modelling by respected figures |
| Beliefs | correcting myths, sharing evidence, interactive workshops |
| Emotions | anxiety reduction, motivational interviewing, counselling |
| Skills | hands-on training, simulation, supervised practice, coaching |
| Habits | restructuring the environment, cues and reminders, incentives |
| Norms | social marketing, peer networks, local champions |
| Access | providing resources, infrastructure investment, policy change |

For each chosen intervention, give an implementation specification: who delivers it, what is done, when, where, how, and the resources needed.

## Monitoring

- Adoption indicators: rate (share of the target population that has adopted), depth (intensity of use among adopters), quality (fidelity to intended use), outcome (effect of adoption). Give each a measurement method, frequency and target value.
- Process indicators: interventions delivered as planned, target groups reached, resources spent as budgeted.
- Outcome indicators: prevalence of each barrier falling, adoption rate rising, delays shortening.
- Checkpoints after each implementation phase, and a periodic check that removed barriers have not returned. Name the deviation that triggers corrective action.

## Pilot before full rollout

Run the interventions with 10 to 20% of the target population first. Ask: are they acceptable to users, are there unintended consequences, are they feasible with the resources available, which components work best and worst. End the pilot with a go or no-go decision for full rollout.

## Explaining the top recommendation

For each top-priority barrier, state: the reasoning chain from evidence to recommendation; the evidence (user data, cited sources); the alternatives considered and why they ranked lower; the assumptions and limitations; and a confidence score from 0 to 1 based on data adequacy and agreement across methods. A confidence below 0.60 means the conclusion should be checked with stakeholders before resources are committed.
