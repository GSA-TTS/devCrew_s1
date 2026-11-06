---
created: "2026-11-04T22:58:58Z"
updated: "2026-11-04T22:58:58Z"
---

# Scenario stress-test method: values, tests and question sets

Each section serves one part of the answer. Column names match the tables in the skill's Goal.

## Uncertainty and assumption register

- Drivers to scan: political, economic, social, technological, environmental, legal, operational, safety and adversarial forces that could change the decision.
- Class values: Predetermined (a relatively predetermined trend), Measurable (uncertain but measurable), Deep (deeply uncertain), Controllable (the decision maker controls it), Endogenous (it depends on how actors respond).
- Impact and Uncertainty: rank each row High, Medium or Low on decision impact and on uncertainty. Keep important disagreements as separate rows or as a wide range instead of averaging them away.
- Observability: how and how early the row's state could be seen; it feeds the signposts.
- Load-bearing: answer these questions about the baseline plan and mark yes on each assumption they expose. What must remain true for the plan to work? Which assumptions carry it? What evidence could falsify them? Who benefits from believing them? Which correlated assumptions have been treated as independent?
- Scenario axes are the High impact uncertainties whose different states imply different actions. Predetermined trends belong in every scenario unless evidence supports a break.

## Scenario set

- Generation methods, to be mixed for diversity: crossing two independent critical uncertainties, morphological combinations, actor-by-actor moves, causal maps, historical analogies, shock injection, backcasting from target states. Do not let one convenient two-by-two matrix exclude a different High impact uncertainty.
- Draft candidates independently before settling on the set, then curate them.
- Field contents:
  - Driving uncertainties: the register IDs the scenario turns on and the state each takes.
  - Causal path: the sequence of events from today's starting conditions to the end state.
  - Actor responses: the incentives and moves of regulators, customers, suppliers, competitors, partners or adversaries.
  - Key assumptions: what the scenario takes as given.
  - Ranges: quantitative ranges where defensible; otherwise none defensible.
  - Implications: answers to the implication questions below.
  - Disconfirming evidence: an observation that would show this future is not arriving.
- Role in set values: Favourable, Adverse, Mixed, Structural break, Compound stress, Challenges preferred strategy, Reversed actor response. One scenario may carry several roles. Avoid a token black swan with no causal path or decision relevance.
- Validation criteria for every candidate: plausibility, internal consistency (linked variables move together and the causal path could produce the end state), relevance to the focal decision, distinctness, coverage of major uncertainties, temporal coherence, actor realism, traceability to evidence.
- Curation: reject a scenario that violates known physical, legal, temporal or budget constraints unless that violation is the uncertainty being explored; merge near-duplicates; split a scenario that hides incompatible pathways; annotate low-evidence assumptions. Do not reject an uncomfortable scenario merely because its probability is unknown.
- Tests, reported in the coverage line:
  - Coverage: every High impact uncertainty and every load-bearing assumption is stressed by at least one scenario.
  - Discrimination: if two scenarios lead to the same preferred decision and reveal no different vulnerability, one may be redundant.
  - Surprise: ask which plausible causal mechanism the set leaves out.
- Implication questions, the same for every scenario: what fails first; what becomes easier; what capability remains scarce; what action becomes impossible if delayed; what new information would have the greatest value. Note also new threats, opportunities, bottlenecks, newly binding constraints and second-order effects. Keep consequences of the scenario apart from consequences of the organization's response, and write unknown rather than filling a gap with fluent speculation.

## Strategy portfolio

- Strategies should differ in timing, commitment, architecture and exposure.
- Class values:
  - Core: a no-regret action that produces acceptable value across nearly all relevant scenarios, such as improving observability, fixing a known control weakness or removing a single point of failure.
  - Hedge: reduces the downside if an adverse future occurs, usually at a known carrying cost.
  - Option: preserves the right but not the obligation to act later, such as a pilot, a reserve contract, a modular interface, a trained backup team or a pre-negotiated licence.
  - Big bet: high value in a narrower future with exposure elsewhere; it needs explicit risk acceptance.
  - Contingent: tied to a named trigger, owner, lead time and branch playbook.
  - Exit: an exit or safe-state action that limits loss when no primary strategy remains acceptable.
- Avoid putting every action in Core: some actions only look universally beneficial because their opportunity cost, maintenance cost or downside has not been examined.

## Stress-test matrix

- Common criteria for every cell: goal attainment, hard-constraint satisfaction, safety, cost, time, resource consumption, reversibility, adaptability, stakeholder impact, recovery and residual uncertainty.
- Keep facts from the user or a cited source apart from your own judgement within each cell.
- Challenge the favoured strategy as a red team would: attack its data, trigger logic and recovery claims, ask what hidden event would reverse the ranking, and test correlated failures rather than assuming every uncertainty is independent.

## Robustness comparison

- Views to compare: the number of scenarios meeting the minimum acceptable outcomes; worst-case performance; regret, the gap to the best strategy in a given scenario, at its largest; downside severity; recovery time; switching cost; resource reserve left.
- Report results by criterion and scenario rather than as one score.

## Vulnerabilities and responses

- Failure conditions: the combination of uncertain conditions under which the strategy misses a minimum acceptable outcome or a hard constraint.
- Response values: Modify core (change the core strategy), Hedge (buy a hedge), Option (preserve an option), Accept and govern (accept the residual risk and name who governs it).

## Robust adaptive plan

- Prefer staged commitments when information will arrive over time: commit now to common capabilities; run probes that reduce important uncertainty; reserve resources for contingent moves; delay irreversible bets until their information deadline, not indefinitely.
- Options have carrying costs, expiry dates and prerequisites, and some capabilities need early investment, so do not defer every commitment.
- The result is a conditional policy, not a paragraph expressing confidence.

## Signposts and triggers

- A signpost is an observable indicator tied to an uncertainty or a causal transition. A trigger is a rule that changes action when one or more signposts cross a threshold.
- Column contents: Data source (where and how it is measured); Threshold, direction and persistence (the value, which way it must move, how long it must hold, and the confidence needed); Check frequency; Owner and authority (who watches and who may activate the branch); Lead time (time the branch needs from activation to effect, and the activation window); Branch; Rollback condition; Fallback if data missing.
- Use leading indicators where possible: a trigger that becomes visible only after the response window closes is a postmortem label, not a control.
- Combine indicators when any single one is noisy. Use persistence or hysteresis rules, switching costs, cooldown periods or stronger evidence before a reversal, so the plan does not oscillate around a threshold, while keeping an emergency override.
- When indicators conflict, gather evidence that discriminates between them rather than averaging them into false certainty.

## Branch playbooks

- Contents: prerequisites, tasks, resources, communications, safety checks, handoffs, success condition, abort condition.
- Write the playbook before activation and recommend a rehearsal.

## Review and replanning

- Refresh cadence: strategic scenarios may be reviewed quarterly or semiannually; operational cases may need daily or event-driven updates. The cadence must be shorter than the time needed to observe, decide and act before a commitment becomes irreversible.
- Replanning routes:
  - Reality stays within a modeled scenario but a strategy underperforms: repair the strategy (redo its stress test and vulnerabilities).
  - A new causal mechanism appears, constraints change, or no scenario fits: rebuild the relevant part of the uncertainty register and the scenarios.
  - The objective or the decision authority changes: reframe the decision.
- Version scenarios instead of rewriting them in place, so the user can reconstruct what was known at the time. Retire a scenario only when its causal mechanism is no longer plausible.
