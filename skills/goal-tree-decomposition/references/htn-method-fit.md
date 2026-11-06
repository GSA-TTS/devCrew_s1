---
id: FR-HTN
purpose: When hierarchical task-network decomposition fits versus a plain checklist,
  how it differs from goal decomposition, and its plan-execute workflow and failure
  rules
slug: htn-method-fit
created: '2026-11-04T14:38:43Z'
updated: '2026-11-04T18:56:05Z'
---

# Hierarchical task-network (HTN) method fit

Use this to decide whether work needs a hierarchical task network or something simpler, and, when HTN fits, to run its plan-execute loop and failure rules.

## Terms

- Compound task: work too abstract to execute directly.
- Primitive task: an action the executor can invoke directly (atomic at the chosen interface).
- Method: a conditional recipe refining one compound task: its applicability conditions, the subtasks it introduces and their constraints. Several methods per task are the planner's controlled alternatives.
- Task network: task occurrences plus constraints (ordering, bindings, resources, required facts), totally or partially ordered.
- Operator: a primitive task's preconditions and modeled effects, plus cost, permissions and expected output.
- Decomposition: replacing a compound task with an applicable method's subnetwork until only valid primitives remain or no permitted refinement works.

## How HTN differs from nearby patterns

| Pattern | What it does | Choose it over HTN when |
|---|---|---|
| Plain checklist or flat sequence | Lists steps; cheap, easy to inspect; no alternative methods, recursion or backtracking | The task is short, stable and nearly deterministic |
| Goal-based planning (state goal, search any action sequence) | Searches any actions whose effects reach the goal | The end state is clear and valid procedure should emerge from general search |
| Goal decomposition | Breaks a goal into subgoals without typed tasks, registered methods, applicability conditions or network constraints | A hierarchy is needed but no validated domain model exists yet; it may propose candidate methods, which must be checked before adoption |
| Orchestration and task management | Tracks assignment, dependencies, status and handoffs of work already chosen | The question is scheduling and supervision, not how to refine work (often used together with HTN) |
| Constraint satisfaction | Assigns values or schedules under hard and soft constraints | The core problem is allocation; embed a solver inside an HTN method when a decomposition creates such a subproblem |
| Plan then execute | Builds a plan before tool calls; the plan may be flat | Dependencies are predictable; HTN may produce that upfront plan or interleave planning and acting |
| Reflection, scenario testing, TODO recitation | Critique, stress-test or keep steps salient | Never: they surround HTN as controls and must not silently override its constraints |

HTN completeness is relative to the method library: a valid action sequence is not an HTN solution if no allowed decomposition generates it.

## When HTN fits

Use HTN when most of these hold:

1. The work is complex enough to benefit from several abstraction levels.
2. Experts can describe repeatable ways to do it, or standard operating procedures already exist.
3. The procedure itself matters for safety, compliance, quality or coordination (acceptable procedure is part of the problem definition).
4. Different procedures apply under different conditions.
5. Plans must be understandable to reviewers, or an agent must stay inside an auditable procedural envelope.
6. The same top-level task recurs, so successful decompositions can be reused.
7. In multi-agent work, compound tasks map to roles and the network can express ordering or synchronization.

Use a hybrid when only part of the problem has stable procedural knowledge: HTN for compliance and handoffs, other planners, solvers or reactive controllers below it, with each primitive task's boundary at that subsystem's interface.

## When HTN does not fit

- A short, linear task a validated checklist can represent: HTN adds failure modes without meaningful choice.
- A highly dynamic environment where state changes faster than decomposition and validation can run: let a reactive policy handle urgent response; HTN may set slower strategic intent.
- No one can state reliable methods or applicability conditions. Language-model text can propose decompositions, but treat it as model authoring followed by schema, constraint and execution validation, not as proof a plan is safe or feasible.
- Avoid unrestricted recursion, unbounded task insertion or elaborate partial ordering unless the domain needs them and termination is understood.
- The output merely has headings or phases. A document hierarchy is not evidence that runtime search over alternative methods is needed; with one stable procedure and locally handled failures, generate directly from a checklist.

## Plan-execute workflow

Entry: an accepted task, a validated domain model, a current-enough state snapshot, available executors, and explicit resource and authorization budgets. Normal exit: every required primitive passed its postcondition check, hard constraints hold and the completion condition is true. Other exits: safe rejection, budget exhaustion, cancellation, or escalation with a failure record. The loop serves plan-then-execute and interleaved acting.

1. Create the run context: identifiers, task, parameters, state snapshot with freshness, versions, budgets, approvals, allowed side effects. Reject or pause if data, permission or a safe execution boundary is missing.
2. Create the initial network with its ordering, deadline, resource and policy constraints; validate types and invariants. Stop on a malformed network instead of letting the planner repair its own input silently.
3. Check termination each iteration. Compound tasks remain: decompose. Only primitives remain: confirm at least one executable ordering, then validate the whole plan or (interleaved) execute an enabled primitive. Nothing executable and completion false: the network is blocked; go to failure handling.
4. Select the next task: the earliest unresolved one if totally ordered, otherwise one whose predecessors are satisfied, preferring the most constrained or riskiest. Log the reason.
5. For a compound task, enumerate every method whose head matches, bind parameters, evaluate conditions and mark each applicable, inapplicable, unknown or error. Unknown is never true for a safety-critical condition.
6. Rank applicable methods by the declared policy (success, risk, cost, preferences) and keep the full ordered set for backtracking. A model-proposed method must use a registered identifier and pass symbolic validation.
7. Open a choice point: save network, state, budgets and untried methods. Apply the method, preserve ordering constraints, link parent and child.
8. Propagate constraints at once and reject the branch on the first hard violation.
9. Update projected state only where the planning semantics allow, and keep projected state separate from observed state.
10. Repeat from step 3 until the network is primitive and valid, a branch fails, a budget is reached, cancellation occurs or external state invalidates an assumption.
11. On decomposition failure, backtrack to the latest choice point with an untried method; mark the failed branch and reason, release its reservations, try the next method.
12. If no method applies, classify the cause: incomplete state, missing domain coverage, true impossibility or exhausted resource bound. Then observe (only through an authorized action), use an explicit fallback, relax declared soft preferences only, ask a human, delegate through a modeled primitive, or stop safely. Never invent an unregistered method.
13. Before consequential execution, validate: hard constraints hold, dependencies form a valid schedule, projected preconditions hold in sequence, budgets and approvals suffice.
14. Execute one enabled primitive: recheck preconditions on fresh observed state, use an idempotency key for retriable side effects, enforce timeout and retry limits.
15. Verify effects with the postcondition checker; classify the attempt as succeeded, failed, uncertain or cancelled; update observed state only from evidence.
16. After success, mark the task complete, enable successors and return to step 3.
17. After primitive failure, apply only the bounded retry policy for transient, idempotent failures. Stop advancing the branch if a precondition no longer holds, the effect is uncertain or retries are exhausted.
18. Choose recovery: local repair when a registered alternative or compensation step keeps the method's invariants; backtrack when the decomposition is no longer viable and earlier work is harmless or compensable; replan from observed state when completed actions or external events invalidated assumptions.
19. Protect replanning: count replans, keep completed tasks and irreversible effects, rebuild only the affected remainder. Escalate on maximum replans, repeated states, oscillating method choices, or deadline, cost or risk thresholds.
20. Close the run. Declare success only after every required primitive and the completion condition are verified; report outputs, deviations and lineage. On non-success report the terminal category, uncompensated effects, exhausted alternatives and what information or authority is needed.

## Failure rules

- Keep planning failure (no permitted primitive network under current knowledge, model, constraints and budget) separate from execution failure (a primitive did not produce verified effects); they need different fixes.
- Backtrack before consequential execution or when completed effects are reversible.
- Replan when observed state diverges from projection, a tool becomes unavailable, a resource or deadline changes, or an irreversible action makes the branch obsolete.
- Compensate when an action succeeded but must be semantically undone.
- Escalate when safety or authorization is uncertain, all allowed methods fail, coverage is missing, or replanning oscillates.
- In dynamic domains, plan a little, act, observe and resume rather than building a large open-loop plan.
- Never roll back the event log when backtracking: append a restoration event and keep every rejected branch.
- Never assume a timeout means no side effect; reconcile uncertain effects before retrying or switching to a conflicting branch.
