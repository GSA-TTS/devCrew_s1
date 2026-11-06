---
id: FR-METAREASONING
purpose: Entry gate and control loop for choosing a solving strategy and effort level,
  and for detecting stuck states and diminishing returns
slug: strategy-effort-control
created: '2026-11-04T14:38:43Z'
updated: '2026-11-04T18:55:41Z'
---

# Strategy and effort control

Use this procedure to decide how to work on a task, how much effort to spend, and when to continue, change course, ask for help or stop. Keep three roles distinct even when one agent plays all of them: one does the task, one monitors progress, evidence, uncertainty and resources, and one decides the next transition.

## Operating principle

Continue a computation only when its expected gain in decision quality, uncertainty reduction, safety or information value exceeds its expected cost in tokens, time, money, tool calls and opportunity. Treat this as an estimate to make at each checkpoint, not a value you can know in advance. Optimise total utility, not accuracy alone: weigh task quality, safety, constraint satisfaction, reversibility, user preference, latency and cost. High-risk or irreversible actions carry a larger penalty for residual uncertainty and a lower threshold for independent verification or human review; low-risk, reversible actions can tolerate cheaper approximations.

## Entry gate

Run a cheap check before opening the loop. Open it when at least one of these is materially present:

- the task is novel, ambiguous, long-horizon, multi-domain or changing;
- several plausible strategies exist, or the right first strategy is uncertain;
- actions are costly or hard to reverse;
- evidence is incomplete or conflicting, or tools behave unreliably;
- the task has safety, legal, financial, scientific or mission-critical consequences;
- adaptive effort is likely to save more than the loop costs.

Skip the full loop for a simple lookup, a deterministic transformation, a well-tested fixed workflow, a low-value one-shot request or a strict low-latency task where one known method is adequate. Skip it also when no real alternative strategy, verification signal or intervention exists: a monitor that cannot change behaviour adds cost without control. A plain plan, a single critique pass or a fixed routing rule is often enough.

## The loop

### 1. Set the decision contract

Before choosing a method, state the objective, acceptance tests, constraints, risk class, authorised actions and evidence standard. Separate hard constraints, which are never traded away, from preferences that may be balanced. Define what counts as success, failure, partial success and "unknown". Record the limits on time, tokens, tool calls, money, iterations and human attention, and a deadline if delay has a cost. Write the contract in a few sentences or as structured state the monitor can check; "think harder" is not a target.

### 2. Characterise the task and build a small portfolio

Identify the task type, sources of uncertainty, dependencies, reversibility, available evidence and likely failure modes. Pick a few genuinely different methods, each with when it applies, its strengths, weaknesses, cost, required tools and stopping rule: for example direct solution, decomposition, retrieval and synthesis, interleaved reasoning and tool use, calculation in code, constraint solving, simulation, tree search, critique and revision, independent cross-checking, human escalation. Keep the portfolio small enough to compare; a hard problem may need a combination rather than one winner.

### 3. Choose the first strategy and a checkpoint horizon

Choose the cheapest strategy likely to satisfy the contract, not the most elaborate one. Estimate confidence separately for factual correctness, plan feasibility, constraint satisfaction and tool reliability; one global number hides failure modes. Set a short horizon (one subgoal, one tool result or one bounded tranche of reasoning) so real evidence arrives before the full budget is committed. Use past performance on similar tasks when you have it. For a novel case, prefer reversible probes that reveal information: a small worked example, a primary source, a unit test, one simulated branch. Keep a fallback plan before any irreversible action.

### 4. Execute one bounded tranche

Run only to the next checkpoint. Produce inspectable outputs: sourced claims, calculations, test results, plan state, tool observations, constraint checks; hidden reasoning traces need not be kept. Validate inputs and outputs at every tool or agent boundary: an output that matches its schema is not thereby correct.

### 5. Monitor

At each checkpoint compare the state with the contract. Measure progress on subgoals, uncertainties resolved and still open, evidence quality, contradictions, constraint violations, action failures, repeated states and remaining budget. Note confidence changes and their causes. Keep "no evidence yet" apart from "evidence of failure". Combine internal signals (confidence, inconsistency, repetition, estimated competence) with external checks (primary sources, tests, simulators, validators, independent models, human feedback). Self-evaluation without a suitable external test can miss correct answers and make harmful edits.

### 6. Evaluate the strategy, not just the latest answer

Ask whether the strategy makes enough progress per unit of cost, whether its assumptions still hold, whether recent evidence is independent, whether errors are local or structural, whether confidence is calibrated for this task class, and whether another method now has higher expected value. Treat self-reported confidence as one feature, never as proof. Calibrated confidence means that claims made at a stated level succeed at about that rate; for long outputs, judge confidence per fact or per criterion rather than one score for the whole.

### 7. Make one explicit control decision

Choose exactly one primary transition, with secondary safeguards if needed.

| Decision | When |
|---|---|
| Continue | Progress is positive, assumptions hold, no hard constraint is violated, and expected gain exceeds marginal cost. |
| Verify | The candidate looks good but a consequential claim, calculation or action is uncertain. Use a check with a different failure mode: run the calculation after reasoning it, consult a primary source after recall. |
| Repair | The defect is local and the strategy is sound. Give specific feedback and revise only the failing part. |
| Switch strategy | Progress stalls, assumptions fail, errors recur, or another method's value is now higher. Carry verified state forward and record why; do not restart from a blank slate. |
| Branch | Alternatives have comparable value and errors are consequential. Limit the branch count, give each a small budget, prune on shared criteria, and merge only evidence-supported claims. Diversity of method beats repeated samples with the same blind spot. |
| Escalate | Authority, competence, evidence, budget or a safe action is missing. Hand over the objective, current state, evidence, open questions, strategies tried, costs and recommended choices, not a raw transcript. |
| Stop: success | Acceptance tests pass, required verification is done, and residual uncertainty is within risk tolerance. |
| Stop: bounded failure or abstention | A hard limit is reached, further computation has no positive expected value, no safe strategy remains, or evidence is insufficient. Report what is known, unknown, attempted and needed next. |

### 8. Update and repeat

After continue, verify, repair, switch or branch, update the working state, strategy history, remaining budget and next checkpoint, then return to step 4. Never go from a control decision straight into an unmonitored long run. The loop ends only through a declared exit: verified success, acceptable partial completion, safe abstention, human takeover, budget exhaustion, deadline, unrecoverable constraint violation or diminishing returns. At exit, check the contract once more and record the outcome, keeping result quality separate from process efficiency.

## Stuck states

Declare the loop stuck when any of these appears:

- the same state, error, unsupported claim or action pattern recurs;
- two consecutive checkpoints show no material drop in uncertainty and no subgoal progress;
- revisions oscillate between alternatives;
- confidence rises without new evidence;
- the remaining budget cannot complete the current strategy.

Tune these thresholds by task class.

On the first stuck signal, diagnose the cause: missing information, an invalid assumption, tool failure, lost context, poor decomposition, a missing capability or an unsatisfiable constraint. On the second, forbid an identical retry and require a changed method, a changed evidence source, a smaller subproblem or escalation. Keep a retry budget per failure signature so a paraphrased retry does not escape the limit. Independent strategies that reach the same supported conclusion show convergence; strategies that repeat the same unsupported premise show correlated failure.

## Diminishing returns

Estimate the quality gained per extra unit of cost. Stop or switch when the recent marginal gain falls below a preset threshold, when confidence stops improving after independent evidence, or when expected gain is below the delay and resource cost. Never continue merely because budget remains. Equally, never stop only because confidence is high while a hard acceptance test or safety check is still unmet.

## Guardrails

- More tokens, agents or reflection are not better reasoning by themselves.
- Do not let one agent's unverified confidence and critique be the sole judge of its own output.
- Do not apply one confidence threshold across domains, risk levels and model versions.
- Do not switch so often that no method reaches an informative checkpoint.
- Keep "unknown" a legitimate outcome: a well-supported abstention beats a confident, unverified completion.
- When adding this control to an existing process, measure a baseline first, then add checkpoint monitoring and one control action (usually escalation or switching) behind explicit thresholds before adding branching.
