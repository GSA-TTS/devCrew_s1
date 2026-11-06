---
created: "2026-11-04T23:37:05Z"
updated: "2026-11-04T23:37:05Z"
---

# Goal-tree records and validation tests

The fields, value lists and tests that fill each part of the deliverable.

## Decomposition lenses

Pick one primary lens before proposing children; use the others to test for omissions.

- Outcome: which observable states jointly establish the parent (the preferred backbone).
- Capability: which capabilities must exist.
- Lifecycle: which phase outcomes must be achieved.
- Risk: which safeguards and mitigations must hold.
- Stakeholder: which beneficiary or accountable group needs a distinct result.
- System: which components or interfaces.

Siblings named by different lenses (one for a team, one for a phase) usually overlap; label the lens when mixing.

## Goal-tree row (one per node)

| Column | What it holds |
|---|---|
| ID | Stable node identifier, such as G1.2; the root is G0. |
| Parent | Parent ID; the root reads none. |
| Outcome | The desired state of a named subject, with its scope; never an activity alone. |
| Class | required, conditional, optional or guardrail. |
| Contribution | How satisfying the node advances or safeguards its parent. |
| Outcome criterion | Measure, baseline, target and deadline or checkpoint. A figure the user did not give reads assumption next to a proposed value, or target to be set by the named owner. |
| Guardrail criterion | The trade-off the method must not create, or none for this node. |
| Evidence | The named evidence a neutral reviewer would use to judge pass, fail, blocked or not yet observed. |
| Owner or executor | Accountable owner or capable executor class. |
| Assumptions and constraints | Assumptions feasibility depends on, and hard constraints that must stay true. External outcomes the owner does not control go here as assumptions or dependencies. |
| Low confidence | Which of interpretation, coverage contribution, feasibility, measurability, dependency accuracy or evidence availability is judged weak, and whether the node needs external evidence or human review; none if no dimension is weak. |
| Leaf status | For a non-leaf, parent. For a leaf: ready, refine, exploratory, existing method, solver subproblem, delegated or rejected (definitions below). |

A row, in this format:

| ID | Parent | Outcome | Class | Contribution | Outcome criterion | Guardrail criterion | Evidence | Owner or executor | Assumptions and constraints | Low confidence | Leaf status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G1 | G0 | Median support response time is at most four hours | required | Establishes the speed half of the root | Median response time, baseline eight hours, target four hours for four consecutive weeks, by December 31 | Customer satisfaction does not decline by more than one percentage point | Weekly queue report from the ticket system | Support operations lead | Assumes staffing stays at current level | none | parent |

Leaf status values:

- ready: a planner or executor can identify the next action or a known method; inputs and outputs are clear; completion can be verified; remaining uncertainty is within the receiver's tolerance; another level would not materially reduce risk or ambiguity.
- refine: fails one of the ready conditions and the refinement budget is not spent.
- exploratory: domain knowledge is insufficient; its children are evidence-producing subgoals.
- existing method: a validated template, procedure or task network the user named covers it.
- solver subproblem: feasibility depends on capacity, timing, routing or exclusivity and needs a constraint solver.
- delegated: handed to a downstream planner with an appropriate formalism.
- rejected: removed by a validation test; keep the row with the reason.

## Child tests

Each set of children must pass:

1. Necessary contribution: each child explains how it advances or safeguards the parent; ornamental branches go unless marked optional.
2. Collective coverage: required children cover the parent's success criteria, constraints and major failure modes, relative to the declared scope, assumptions and risk tolerance.
3. Limited overlap: no two children claim the same outcome or evidence without a declared shared interface; model cross-cutting concerns as shared constraints or cross-links.
4. Measurability and falsifiability: a neutral reviewer can decide pass, fail, blocked or not yet observed from named evidence.
5. Feasibility and controllability: the responsible actor has means, authority, inputs, resources and time.
6. Operational readiness: as defined for the ready status.

Adversarial questions for each child; any yes means rewrite or remove it:

- Could it be marked complete without advancing the parent?
- Could the parent fail even if it succeeds?
- Could nobody determine whether it succeeded?
- Could another child own the same result?

## Dependency row

| Column | Values |
|---|---|
| From | Node ID that must supply or finish first. |
| To | Node ID that waits. |
| Type | precedence, data, resource, approval, mutual exclusion or conditional trigger. |
| Join | all predecessors, any one, a threshold, or a named condition. |
| Condition or artifact | The required predecessor state or artifact. |

Repair an accidental cycle by changing scope, separating an outcome from its verification, or defining an intermediate artifact. An intentional loop states its condition, maximum iterations, progress test and stop reason.

## Feasibility verdicts

- feasible within declared assumptions;
- logically contradictory;
- resource-infeasible;
- temporally infeasible;
- unauthorized;
- unverifiable;
- outside known capabilities;
- uncertain because information is missing.

For any verdict other than feasible, give the failing requirement, the evidence for the diagnosis, whether it is certain or uncertain, and the smallest changes that restore feasibility: narrowing scope, extending time, adding resources, obtaining permission, changing a soft threshold, or converting a performance goal into a learning goal.

## Challenge scenarios

One normal scenario, one missing-input scenario, one dependency failure, one deadline or resource stress, one changed assumption and one adversarial interpretation. For each, say whether the hierarchy still preserves the original objective, whether every failure becomes visible, whether guardrails survive, and whether escalation happens before unsafe action.

## Freeze record

Version, date, selected candidate and lens, why each alternative was rejected, the assumption set, evidence references, results of the child tests, coverage, dependency and feasibility checks, and the approver role where approval is needed. A later change creates a new version with its reason and the version it derives from.

## Leaf hand-off contract (one per required leaf)

- Leaf ID and tree version.
- Task objective: the leaf outcome translated into work.
- Serves: the goal criterion the task exists for.
- Acceptance criteria and who or what validates completion.
- Inputs: verified inputs and artifact references needed to start.
- Outputs: required outputs.
- Predecessors: from the dependency rows.
- Constraints and permissions: hard constraints, approvals and authority that travel with the task.
- Deadline or checkpoint.
- Owner and escalation owner.
- Open uncertainty and assumptions.
- Next expected action.

A field the user's material does not settle reads not stated, with what would settle it.

## Exit categories

- approved tree: versioned, acyclic or loop-bounded, required leaves measurable, feasible within declared assumptions, linked to every parent criterion, ready for planning;
- direct execution: decomposition was not justified;
- existing method: a validated template, procedure or task network replaced a new hierarchy;
- infeasible with reasons;
- clarification required;
- safe refusal;
- cancellation;
- budget exhausted with the best validated partial tree.
