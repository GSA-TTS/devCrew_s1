# Task Management and Orchestration

**Status**: Beta testing

**Change logs**:

- [09/06/2026] - Initialization

***

## Executive Summary

Task Management and Orchestration is the control discipline that converts an accepted objective into a governed set of work items and drives those items to a verified terminal outcome. It owns the task lifecycle: creation, validation, assignment, dependency tracking, scheduling, execution, status tracking, handoff, retry, compensation, completion, cancellation, and escalation. This guide provides AI agents with a structured protocol for that discipline: a minimum task and run model, an explicit state machine, a seven-phase control loop running from run admission through liveness assurance and closure, layered failure controls, an append-only logging schema, and metric families carrying numeric targets. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures, so that control decisions rest on observed evidence rather than reported status and recovery is selected from a causal classification rather than a generic failure signal.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Task Management and Orchestration**: The control discipline that decides which task occurrences are presently eligible, which executor receives each one, what context and authority travel with it, how completion is verified, and what happens when execution diverges from the plan. Its artifacts are a task registry, a dependency model, a state machine, one or more ready queues, assignment and lease records, and an append-only execution history.

**Task definition**: A reusable description of a kind of work, stating purpose, typed inputs, required outputs, completion validator, predecessors, resource and capability needs, permissions, priority policy, expected duration and cost, deadline, timeout, retry policy, idempotency behavior, side effects, compensation action, escalation owner, and context-transfer policy.

**Task occurrence**: One invocation of a definition within one run, with bound inputs and its own state. The distinction prevents the status of one invocation from contaminating another. An occurrence is atomic at the orchestration boundary: one input contract, one output contract, one owner at a time, observable completion criteria, and a declared failure policy, whether it internally calls a model, tool, human, solver, or subworkflow.

**Execution attempt**: One bounded execution of an occurrence by one executor under one lease. Retries create new attempts inside the same occurrence and the same idempotency scope.

**Dependency graph**: A directed structure whose nodes are task occurrences and whose edges mean one task depends on an output, condition, or terminal state of another [9]. An acyclic graph makes eligibility and parallelism tractable because it contains no circular waits.

**Task queue**: The decoupling layer between scheduling and execution. Queue delivery is not proof of execution, and an executor's successful return is not proof that the desired postcondition holds [10].

**Lease**: A time-bounded grant of ownership recording assignee, assignment reason, issue time, expiry, capability match, and concurrency slot. A running executor renews it through heartbeats or progress checkpoints [16].

**Plan generation**: A versioned snapshot of the dependency graph and its task states. Replanning creates a new generation and supersedes obsolete tasks rather than erasing them.

**Handoff package**: A controlled transfer of responsibility carrying objective, acceptance criteria, minimum necessary context, verified inputs, artifact references, constraints, permissions, uncertainty, failed attempts, and the next expected action. A handoff is not a transcript dump [17].

**Compensation**: A new task that semantically counteracts a completed action. It is not state restoration, because other processes may already have observed the original effect [21].

**Verified completion**: A success verdict issued by the declared validator against observed artifacts and, for consequential actions, an external receipt or state read. A tool's reported success and the validator's acceptance are separate signals.

A task list records intent; an orchestrator governs eligibility, ownership, authority, verification, and divergence. Orchestration must therefore distinguish four events that naive implementations conflate: assignment, start, attempt completion, and verified task completion.

### 1.2 Orchestration, Choreography, and Neighbouring Coordination Patterns

Orchestration uses a logical coordinator that holds workflow state and directs participants. The coordinator may be replicated for availability, but the decision model is centralized: it resolves dependencies, issues commands, records transitions, and determines what happens next. Choreography distributes that control; participants subscribe to events, perform local work, and emit new events, and no component holds the whole command sequence [11][12].

**Coordination pattern selection**:

| Pattern | Control locus | Select when | Principal cost |
| :-- | :-- | :-- | :-- |
| Orchestration | Coordinator holds workflow state | An accountable end-to-end owner must enforce deadlines, budgets, approvals, security boundaries, exact joins, or compensation order, and operators need one place to intervene | Coordinator complexity, a large shared state surface, throughput bottlenecks, and a failure domain requiring durability |
| Choreography | Distributed across event subscribers | Participants are independently owned, interaction is event-driven, no participant needs global optimization, and adding subscribers must not change a central definition | Event contracts, correlation, duplicate handling, ordering, weaker observability, eventual consistency |
| Hybrid | Central case governance, local event reactions | The case needs governance and audit while domain services stay decoupled | Two coordination models to operate and an explicitly stated boundary |

Choreographed segments require a shared correlation identifier, idempotent consumers, and dead-letter handling, because no coordinator associates related messages.

Orchestration also differs from the adjacent planning patterns set out below, each of which decides something orchestration does not, and AI agents must not substitute one for another:

- **Goal decomposition**: Decides which measurable subgoals exist. It makes vague scope concrete but supplies no durable ownership, retries, or handoffs.
- **Hierarchical task network planning**: Refines a compound task through domain-approved methods into executable primitives. It answers which valid procedure produces the work; orchestration answers what is ready now, who owns it, and what follows an observed result [13].
- **Meta-reasoning**: Selects reasoning strategies. Its output may change a route, but state transitions remain governed by orchestration policy.
- **Constraint-satisfaction planning**: Finds feasible assignments under hard and soft constraints. Embed it in the scheduler when capacity, deadlines, permissions, or resource conflicts make greedy assignment inadequate.
- **Plan and execute decoupling**: Builds a full call sequence before execution. It supplies the initial graph and exposes parallelism, but goes stale when observations violate assumptions; orchestration supplies runtime state, bounded replanning, and recovery.
- **Scenario planning and world-model simulation**: Prepare strategies across plausible futures and predict consequences of candidate actions. Either generates contingencies; neither replaces task ownership or lifecycle control.
- **Plan recitation**: Keeps the plan salient inside an executor's context. It is a working-memory aid, never the authoritative registry, because context is truncated, replayed, and handed off.

### 1.3 The Minimum Task and Run Model

Every run, workflow definition, plan generation, task definition, task occurrence, attempt, executor, artifact, event, and human approval requires a stable identifier independent of any display name. Lineage is preserved from objective to task, task to attempt, and input artifact to output artifact. Control state is held in an explicit state machine, never in free-form status text [14][15], and hard conditions are stored separately from preferences, because a deadline or a permission cannot be traded away when an executor predicts higher answer quality.

**Task occurrence state machine**:

| State | Meaning | Actor permitted to enter it | Permitted next states |
| :-- | :-- | :-- | :-- |
| created | Bound to a definition, guards not yet evaluated | Task creator | blocked, ready, skipped, cancelled |
| blocked | A required predecessor, artifact, approval, or resource is unsatisfied | Dependency resolver | ready, skipped, cancelled, escalated |
| ready | All guards satisfied, eligible for ranking | Dependency resolver | reserved, cancelled, escalated |
| reserved | Slot acquired, lease issued, acknowledgment pending | Scheduler | running, ready, cancelled, timed-out |
| running | Lease acknowledged, one attempt executing | Lease holder | waiting, succeeded, failed, timed-out, uncertain, cancelled |
| waiting | Blocked on a human decision, external event, or rate-limit window | Lease holder | running, ready, timed-out, cancelled, escalated |
| retry-wait | Failure classified retryable, backoff pending | Recovery controller | ready, failed, escalated |
| succeeded | Validator issued a verified success verdict | Completion validator | compensated |
| failed | Attempt and recovery budgets exhausted, or class is terminal | Recovery controller | compensated, escalated |
| cancelled | Terminated by policy after effects were reconciled | Orchestrator | compensated |
| skipped | Branch condition resolved against this occurrence | Dependency resolver | — |
| compensated | A verified compensation counteracted the original effect | Completion validator | escalated |
| escalated | Held by a modeled human decision with owner, deadline, and default | Orchestrator | ready, cancelled, failed |
| timed-out | A layered timeout fired, reconciliation pending | Monitor | running, ready, failed, uncertain, escalated |
| uncertain | Side-effect status unresolved after reconciliation | Monitor | succeeded, failed, escalated |

Each transition declares its legal actor, guard, and side effect, and commits atomically with its event record or through compare-and-set on the task version, so two schedulers cannot both create authoritative assignments. Only the dependency resolver moves a task from blocked to ready; only a scheduler reserves it; only the lease holder starts or reports it; only the validator marks it succeeded.

**Minimum record template**:

```
RUN RECORD
  RUN_ID / CORRELATION_ID:
  OBJECTIVE / TASK_CLASS / RISK_TIER:
  ACCEPTANCE_TESTS:
  HARD_CONSTRAINTS:
  PREFERENCES:
  AUTHORIZATION_SCOPE:
  BUDGETS: TIME / TOKENS / MONEY / TOOL_CALLS / TASKS / FANOUT / REPLANS / ATTEMPTS
  WORKFLOW_VERSION / POLICY_VERSION / MODEL_VERSION / TOOL_VERSIONS:
  REQUIRED_HUMAN_GATES:
  TERMINAL_STATUS / TERMINAL_REASON:

TASK DEFINITION RECORD
  DEFINITION_ID / PURPOSE:
  TYPED_INPUTS / REQUIRED_OUTPUTS:
  COMPLETION_VALIDATOR:
  PREDECESSORS:
  CAPABILITY_NEEDS / PERMISSIONS:
  PRIORITY_POLICY:
  EXPECTED_DURATION / EXPECTED_COST / DEADLINE / TIMEOUT:
  RETRY_POLICY / IDEMPOTENCY_BEHAVIOR / SIDE_EFFECT_CLASS:
  COMPENSATION_ACTION / ESCALATION_OWNER:
  CONTEXT_TRANSFER_POLICY:

TASK OCCURRENCE RECORD
  OCCURRENCE_ID / DEFINITION_ID / RUN_ID / PLAN_GENERATION_ID:
  PARENT_OCCURRENCE_ID:
  BOUND_INPUTS:
  STATE / STATE_VERSION:
  JOIN_POLICY: ALL | ANY | THRESHOLD_K | NAMED_CONDITION
  CANCELLATION_SCOPE:
  LEASE: HOLDER / ISSUED_AT / EXPIRES_AT / CAPABILITY_MATCH / SLOT
  CURRENT_ATTEMPT_ID / IDEMPOTENCY_KEY:
  ARTIFACT_REFERENCES:
  TERMINAL_REASON:
```

Every task output is an immutable artifact or a versioned reference carrying provenance. An assignment is a time-bounded lease rather than permanent ownership, and lease expiry triggers reconciliation of possible side effects before any duplicate dispatch.

### 1.4 Applicability Criteria and Exclusions

Centralized orchestration is warranted when work contains 3 or more interdependent occurrences, or when 2 or more executors, tools, or humans must coordinate; when tasks can run in parallel; when progress must survive process failure or a pause exceeding an executor's context lifetime; when priorities change during execution; when cost and capacity require scheduling; when actions need approval or compensation; or when operators need end-to-end visibility. It is preferred over pure choreography when a case has an accountable end-to-end owner, global deadlines or budgets, complex joins, regulated audit requirements, cross-service compensation, or dynamic assignment. Choreography is preferred when autonomous components react locally to stable event contracts; a hybrid applies when the case needs governance while local domains stay decoupled.

Orchestration must not be added to a single model call, a single atomic tool action, a short deterministic transformation, or a fixed pipeline of fewer than 3 steps that ordinary application control flow can execute and observe. AI agents must select the lowest coordination complexity that reliably works, because every hop adds latency, cost, and failure modes [22][23]. Orchestration is also inappropriate when registry, queue, persistence, and monitoring overhead exceeds 20% of the work's execution cost; when the latency budget cannot absorb at least 2 coordination hops; when no reliable completion signal exists; or when tasks are so tightly coupled that splitting them generates more communication than useful work. In those cases the correct response is to keep the operation atomic, use a local pipeline, or redesign the task boundary.

***

## II. Operational Framework: The Governed Task Lifecycle

The framework decomposes orchestration into seven sequential phases. Phases 3 through 6 form a repeating loop reentered after every success, failure decision, handoff, approval, external event, or plan change, and Phase 7 terminates that loop under a declared exit condition.

**Control loop invariant**:

```
LOOP WHILE UNRESOLVED_REQUIRED_TASKS EXIST AND BUDGETS REMAIN
  RESOLVE   ELIGIBILITY OVER AFFECTED FRONTIER PLUS PERIODIC RECONCILIATION
  RANK      READY SET BY POLICY SCORE, HARD GATES HELD OUTSIDE THE SCORE
  SELECT    EXECUTOR BY CAPABILITY, AUTHORIZATION, CAPACITY, COST
  RESERVE   ATOMICALLY: SLOT + LEASE + ATTEMPT_ID + IDEMPOTENCY_KEY
  DISPATCH  WITH IDEMPOTENCY KEY BOUND TO OCCURRENCE, NOT TO ATTEMPT
  MONITOR   HEARTBEAT / LEASE / TIMEOUT / BUDGET / WAIT CONDITION
  VALIDATE  POSTCONDITION AGAINST OBSERVED EVIDENCE AND EXTERNAL RECEIPTS
  COMMIT    OUTCOME + LINEAGE + LEASE RELEASE + SUCCESSOR TRANSITIONS
  RECOVER   ON FAILURE: CLASSIFY THEN RETRY | REPAIR | REASSIGN | REPLAN
                        | COMPENSATE | ESCALATE | FAIL TERMINALLY
  SWEEP     ON FIXED CADENCE FOR NO-PROGRESS AND ORPHANED CONDITIONS
EXIT WHEN VERIFIED_SUCCESS OR ANOTHER DECLARED TERMINAL CONDITION IS TRUE
```

### Phase 1: Run Admission and Contract Definition

**Objective**: Admit only objectives whose completion can be verified and whose side effects are authorized, and freeze the run contract before any work item exists.

#### Step 1.1: Verify Admission Conditions

**Required Actions**:

- Confirm the objective names an accountable requester, a supported task class, and a risk classification.
- Confirm success criteria are observable and expressible as machine-checkable acceptance tests against artifacts or external state.
- Confirm the authorization boundary covers every implied side effect; reject or escalate otherwise.
- Admit an objective with missing input data only when an authorized task can retrieve or request that data.

**Required Outputs**:

- An admission decision record with requester, task class, and risk tier.
- An acceptance-test specification stated as observable postconditions.

**Quality Checkpoints**:

- Every acceptance criterion is evaluable against an artifact or an external state read, never against a self-reported status string.
- No implied side effect falls outside the recorded authorization scope.
- Inadmissible objectives are rejected or escalated within 1 scheduler tick rather than admitted provisionally.

***

#### Step 1.2: Freeze the Run Contract and Budgets

**Required Actions**:

- Record hard constraints and preferences in separate fields, so no preference overrides a deadline, permission, or approval gate.
- Set numeric ceilings for wall-clock time, tokens, money, tool calls, task count, fan-out, plan generations, and total attempts.
- Record workflow, policy, model, prompt, tool, and environment versions plus required human gates.
- Create a clarification task or stop safely when a contract field required by the task class is absent.

**Required Outputs**:

- A frozen run contract separating hard constraints from preferences.
- A budget ledger with an allocation and a consumption counter per dimension.

**Quality Checkpoints**:

- Every budget dimension carries a numeric ceiling; a run with any unbounded dimension is refused admission.
- Hard constraints sit outside the priority score and cannot be traded for predicted quality gain.
- Missing required fields produce a clarification task or a safe stop, never a default assumption.

***

#### Step 1.3: Establish Identifiers and Lineage

**Required Actions**:

- Mint stable identifiers for run, correlation, workflow, plan generation, definitions, occurrences, attempts, executors, artifacts, events, and approvals.
- Derive no identifier from a display name, title, or other mutable field.
- Record lineage from objective to task, task to attempt, and input artifact to output artifact.

**Required Outputs**:

- An identifier registry covering every entity class the run will produce.
- A lineage skeleton traversable in both ancestor and descendant directions.

**Quality Checkpoints**:

- Zero identifiers derive from a mutable display name.
- Every occurrence resolves to exactly 1 parent run and 1 registered definition.
- Lineage queries return a complete ancestor chain for 100% of artifacts produced.

***

### Phase 2: Task Set Construction and Dependency Modelling

**Objective**: Convert a plan from any source into a validated, acyclic, machine-checkable dependency graph with declared join and cancellation semantics, persisted as a versioned plan generation.

#### Step 2.1: Create and Validate the Initial Task Set

**Required Actions**:

- Obtain candidate tasks from a fixed workflow, goal decomposer, hierarchical planner, agent planner, or human requester.
- Bind each candidate to a registered definition, and reject unregistered tool actions and invented executor roles rather than accepting plausible prose.
- Validate typed inputs, output contracts, dependency references, permissions, retry and timeout policies, and lineage.
- Reject any task lacking a completion validator or an output contract.

**Required Outputs**:

- A validated occurrence set bound to registered definitions.
- A rejection log carrying a normalized reason code per rejected candidate.

**Quality Checkpoints**:

- 100% of scheduled occurrences bind to a registered definition; unbound candidates are never scheduled.
- Every occurrence carries an output contract and a named completion validator.
- Task count and fan-out remain within contract ceilings; a breach halts creation and escalates.

***

#### Step 2.2: Construct the Dependency Graph and Declare Control Semantics

**Required Actions**:

- Add precedence, data, approval, and resource edges, typing each edge explicitly.
- Declare a join policy for every convergence node as all-required, any-one, threshold of k, or a named condition.
- Declare the cancellation scope of every decision branch, naming which descendants stop when it resolves.
- Run cycle detection before the first scheduling tick, and express intentional loops as bounded state-machine transitions or a new occurrence per iteration.

**Required Outputs**:

- A typed dependency graph with per-node join policy and cancellation scope.
- A cycle-detection report naming circular waits and their affected tasks.

**Quality Checkpoints**:

- Every convergence node declares one of the 4 join policies; untyped joins block scheduling.
- Cycle detection returns 0 unintentional cycles, or affected tasks stay blocked pending repair or escalation.
- Intentional loops carry a loop condition plus a decreasing measure or an iteration ceiling within the contract limit.

***

#### Step 2.3: Initialize Task State and Persist the Plan Generation

**Required Actions**:

- Place occurrences with unmet prerequisites in blocked, fully guarded occurrences in ready, and conditional branches in dormant or skipped until their condition resolves.
- Persist the graph and the initial state assignment together as one versioned plan generation.
- Hold no control state whose only copy is an executor's private context.

**Required Outputs**:

- An initial state assignment covering every occurrence in the graph.
- A persisted plan generation record with version identifier and creation source.

**Quality Checkpoints**:

- Graph and state persist in 1 atomic write; partial persistence is rolled back and retried.
- Zero task states exist only inside an executor's context window.
- Conditional branches are dormant or skipped, never ready, until their condition resolves.

***

### Phase 3: Eligibility Resolution and Scheduling

**Objective**: Determine which occurrences are presently eligible, rank them without weakening any hard gate, and select an executor that is both capable and authorized.

#### Step 3.1: Resolve Eligibility Against the Affected Frontier

**Required Actions**:

- Recompute eligibility for the affected frontier at every tick or relevant event, and run a full reconciliation on a cadence no longer than 300 seconds.
- Evaluate eligibility as verified predecessor terminal states, existing artifacts passing schema checks, an open time window, valid approvals and permissions, reservable resources, and absence of cancellation or supersession.
- Emit a dependency-resolution event with its evidence reference for every newly satisfied or violated condition.

**Required Outputs**:

- An eligible set snapshot with a stable snapshot identifier.
- Dependency-resolution event records with evidence references and timestamps.

**Quality Checkpoints**:

- Eligibility derives from persisted state, never from an executor's claim about its own progress.
- A full reconciliation has completed within the last 300 seconds; a longer gap raises a liveness alert.
- Every newly ready occurrence carries an evidence reference per satisfied condition.

***

#### Step 3.2: Prioritize Ready Tasks Without Overriding Hard Gates

**Required Actions**:

- Rank only ready occurrences, excluding blocked, waiting, and reserved occurrences from the ranking input.
- Compute the score from deadline slack, critical-path impact, business value, failure risk, expected information gain, cost, locality, and waiting age.
- Hold hard gates outside the score, so no score value admits an ineligible task.
- Apply aging boosts and reserved capacity per task class to prevent starvation, and record score components with the chosen occurrence.

**Required Outputs**:

- A ranked ready list with a per-component score breakdown.
- A starvation-guard record naming boosted occurrences and reserved capacity.

**Quality Checkpoints**:

- Zero blocked or ineligible occurrences appear in the ranked list.
- Every decision records its score components; a single opaque priority number fails the checkpoint.
- No ready occurrence exceeds its class starvation threshold, set by default at 10 times the class median queue wait, without an aging boost or escalation.

***

#### Step 3.3: Select an Authorized and Capable Executor

**Required Actions**:

- Filter candidates by capability, tool access, security clearance, context capacity, availability, model suitability, cost ceiling, and historical reliability for the task class.
- Select from the filtered set by policy, optimization, or a bidding protocol in which a manager announces a typed task, contractors bid, and the manager awards the work.
- Fall back to direct policy assignment when negotiation cost approaches the value of distributing the task.
- Record the selection reason and every candidate rejection reason.

**Required Outputs**:

- An executor selection record with capability-match evidence.
- A candidate rejection list with normalized reason codes.

**Quality Checkpoints**:

- The selected executor satisfies 100% of required capabilities and permissions.
- Negotiation overhead consumes no more than 10% of expected execution cost; above that the scheduler reverts to policy assignment.
- Selection and rejection reasons are recorded for every candidate considered.

***

### Phase 4: Atomic Dispatch and Bounded Execution

**Objective**: Transfer each task under a time-bounded lease and run exactly one bounded attempt whose consequential side effects cannot be duplicated.

#### Step 4.1: Reserve and Dispatch Atomically

**Required Actions**:

- Acquire the required concurrency and resource slots before any state change.
- Create an attempt identifier and a lease recording assignee, reason, issue time, expiry, capability match, and slot.
- Transition ready to reserved through compare-and-set on the task version, aborting on version conflict.
- Publish the assignment with an idempotency key bound to the occurrence, and reconcile queue against task record before republishing after an ambiguous publication failure.

**Required Outputs**:

- A lease record and a reservation record for the occurrence.
- A dispatch message carrying the idempotency key and task version.

**Quality Checkpoints**:

- State transition and dispatch publication commit together or not at all.
- The idempotency key is bound to the occurrence and never to the attempt.
- No 2 leases are simultaneously valid for one occurrence; the second reservation aborts on version conflict.

***

#### Step 4.2: Accept the Lease and Start Deliberately

**Required Actions**:

- Validate lease, task version, bound inputs, granted permissions, and fresh preconditions before acknowledging.
- Acknowledge and transition reserved to running, or reject with a code drawn from capability mismatch, stale version, missing input, policy denial, or capacity loss.
- Return a rejected occurrence to scheduling without consuming an execution retry unless task work actually began.
- Expire unacknowledged reservations at the acknowledgment deadline, set by default at 30 seconds.

**Required Outputs**:

- An acknowledgment record or a normalized rejection record.
- A running-state transition with actor, guard evaluation, and task version.

**Quality Checkpoints**:

- Rejection reasons come from the closed vocabulary; free-text reasons fail the checkpoint.
- Reservations unacknowledged beyond 30 seconds return to ready and release their slot.
- A rejection issued before work began consumes 0 execution retries.

***

#### Step 4.3: Execute One Bounded Attempt Under Active Monitoring

**Required Actions**:

- Perform only the assigned scope, taking no action outside the permissions transferred with the lease.
- Emit heartbeats or checkpoints at an interval no greater than one third of lease duration, and store intermediate artifacts outside conversational context.
- Apply the occurrence-scoped idempotency key to every consequential side effect, so a repeated attempt cannot repeat the business operation.
- Monitor lease expiry, heartbeat age, execution timeout, deadline slack, spend, repeated tool signatures, and output growth.
- Transition to waiting and release expensive capacity when blocked on a human, external event, or rate-limit window.

**Required Outputs**:

- Attempt telemetry covering heartbeats, checkpoints, and incremental resource consumption.
- Intermediate artifact references stored outside conversational context.

**Quality Checkpoints**:

- Heartbeat interval is at most one third of lease duration; a missed heartbeat triggers investigation, never immediate reassignment.
- 100% of consequential side effects carry the occurrence-scoped idempotency key.
- Waiting occurrences release expensive executor capacity within 1 heartbeat interval.

***

### Phase 5: Completion Validation and Dependent Release

**Objective**: Convert an apparent success into a verified completion supported by evidence, release exactly the successors the workflow declares, and transfer responsibility through a bounded handoff package.

#### Step 5.1: Validate Completion Against Observed Evidence

**Required Actions**:

- Run the postcondition checker against observed artifacts rather than the executor's report.
- Obtain an external receipt or state read for every consequential action before issuing a success verdict.
- Classify the attempt as verified success, failure, or uncertain, keeping the tool result separate from the validator verdict.
- Retain outputs failing validation as evidence, leaving the occurrence unmarked as succeeded.

**Required Outputs**:

- A validation record with per-criterion results and observed evidence references.
- An attempt classification of verified success, failure, or uncertain.

**Quality Checkpoints**:

- Schema conformity alone never yields a verified success verdict.
- A consequential action without external confirmation classifies as uncertain, never as succeeded.
- 100% of failed validations retain their outputs as evidence.

***

#### Step 5.2: Commit the Outcome and Release Dependents

**Required Actions**:

- Record attempt outcome, artifact lineage, resource consumption, lease release, and the transition to succeeded in one atomic operation.
- Reevaluate every immediate successor and move each occurrence whose final unmet condition is satisfied from blocked to ready.
- Hold each join until its declared branch policy is satisfied, and cancel branches the resolved decision made unnecessary.
- Release independent occurrences for parallel execution only where inputs, side effects, resource locks, and join semantics permit.

**Required Outputs**:

- A committed terminal state with lineage and resource accounting.
- Successor transition events and branch cancellation notices.

**Quality Checkpoints**:

- Outcome commit and lease release occur in 1 transaction; a partial commit rolls back.
- No join fires before its declared branch policy is satisfied.
- Parallel release occurs only where the recorded side-effect and resource-lock analysis permits it.

***

#### Step 5.3: Assemble the Handoff Package

**Required Actions**:

- Assemble objective, acceptance criteria, minimum necessary context, verified inputs, artifact references, constraints, permissions, uncertainty, failed attempts, and the next expected action.
- Strip secrets, unrestricted personal data, and transcript material irrelevant to the next contract.
- Version the package, bound its size against the receiving executor's context capacity, and record context omitted by policy.

**Required Outputs**:

- A versioned handoff package with recorded size and permission set.
- An omission record naming withheld context and the policy that withheld it.

**Quality Checkpoints**:

- Zero handoffs transfer a full conversational transcript.
- The package carries every acceptance criterion the receiving executor must satisfy.
- Package size leaves at least 20% context headroom for the receiver; a larger package is reduced before transfer.

***

### Phase 6: Failure Classification and Bounded Recovery

**Objective**: Select recovery from a causal classification rather than a generic failure signal, and bound every recovery path by attempts, time, cost, and plan generations.

#### Step 6.1: Classify the Failure Before Selecting Recovery

**Required Actions**:

- Assign exactly one category from the closed taxonomy of transient infrastructure fault, rate limit, timeout, invalid input, deterministic code or prompt defect, policy denial, missing capability, bad output, upstream defect, stale plan, and uncertain side effect.
- Compute a failure signature from error class, definition, executor class, and input hash, so recurrences are recognizable.
- Determine side-effect certainty by reading external state, treating a timeout as evidence of lost observability rather than proof of inaction.
- Reject a generic executor-failed reason code as a classification.

**Required Outputs**:

- A causal classification with its failure signature.
- A side-effect certainty verdict supported by an external state read.

**Quality Checkpoints**:

- Every failed attempt carries exactly 1 category from the closed taxonomy.
- Side-effect certainty is determined before recovery, never inferred from a missing heartbeat.
- 0 attempts terminate with an unclassified or free-text reason code.

***

#### Step 6.2: Apply Bounded Retry, Repair, or Reassignment

**Required Actions**:

- Retry only when the objective is unchanged and valid, the class is retryable, idempotency is safe, attempt and budget limits remain, and time, executor, or environment has materially changed.
- Apply exponential backoff with jitter for shared transient faults, preserve the occurrence and its idempotency scope, and mint a new attempt identifier.
- Repair the task when its input, prompt, tool binding, or local strategy is defective while the graph remains valid.
- Reassign when another executor holds a better capability match or the lease holder is unavailable.
- Count every retry at the orchestration layer, including retries a tool performs internally.

**Required Outputs**:

- A recovery decision record naming the selected path and its justification.
- A new attempt identifier, repair task, or reassignment record.

**Quality Checkpoints**:

- Retries per occurrence do not exceed the contract ceiling, set by default at 3; the next failure escalates.
- Authorization denials, schema violations, deterministic defects, and exhausted quotas consume 0 retries absent a material change.
- Tool-level retries are counted inside the orchestration budget, so nested retries cannot multiply load invisibly.

***

#### Step 6.3: Replan, Compensate, and Escalate

**Required Actions**:

- Replan when observed state invalidates dependencies, required tasks, or success conditions, creating a new plan generation that preserves completed and irreversible effects.
- Supersede rather than erase obsolete tasks, and revalidate every affected region of the graph.
- Execute compensations as new idempotent tasks in reverse commit order, verifying each outcome rather than assuming it.
- Escalate to a modeled human decision carrying request, owner, deadline, allowed decisions, and a default on timeout whenever an action is irreversible or compensation fails.
- Resume orchestration through a recorded event, never through an unrecorded edit to shared state.

**Required Outputs**:

- A new plan generation with supersession records and preserved work.
- A compensation task set with per-compensation verification results.
- An escalation record with owner, deadline, allowed decisions, and default action.

**Quality Checkpoints**:

- Plan generations per run do not exceed the contract ceiling, set by default at 5; the next replan escalates.
- Every compensation is idempotent and its outcome verified; unverified compensations escalate.
- Every escalation names an owner, a deadline, and a default action on timeout.

***

### Phase 7: Liveness Assurance and Run Closure

**Objective**: Detect occurrences that stopped making progress, distinguish the pathology before applying a control, and close the run in a declared terminal state with a reconciled outcome package.

#### Step 7.1: Run the No-Progress Sweep

**Required Actions**:

- Sweep on a cadence no longer than 60 seconds for ready occurrences never selected, reserved occurrences never acknowledged, running occurrences with expired leases, waiting occurrences whose wake condition passed, blocked occurrences whose predecessors are all terminal, occurrences assigned to decommissioned executors, and runs with no runnable task and unmet completion.
- Reconcile every finding against the append-only log and external side effects before changing state.
- Record each finding with its category, evidence, and applied control.

**Required Outputs**:

- Sweep findings grouped by category with evidence references.
- Reconciliation records showing an external state read before each corrective transition.

**Quality Checkpoints**:

- Sweep cadence never exceeds 60 seconds; a longer gap raises a liveness alert.
- No state change follows a sweep finding before external reconciliation completes.
- Every finding resolves to a reclassification, a recovery action, or an escalation within 2 sweep cycles.

***

#### Step 7.2: Diagnose Liveness Pathologies Separately

**Required Actions**:

- Declare deadlock when unresolved occurrences wait in a cycle of dependencies or exclusive resources with no legal releasing transition, and break it only through a declared victim, a resource-order rule, plan repair, or escalation.
- Declare livelock when state changes repeat without progress, such as alternating assignment and rejection.
- Declare starvation when a ready occurrence is bypassed while later eligible peers repeatedly run.
- Declare orphaning when a nonterminal occurrence has no live parent run, owner, or lease, reconciling external effects before cancelling it.
- Terminate repeated-state loops when the same failure signature, graph hash, and assignment choice recur without new evidence.

**Required Outputs**:

- A pathology diagnosis per finding with supporting evidence.
- An applied control record naming the control matched to the diagnosis.

**Quality Checkpoints**:

- Each pathology receives its matched control; a generic restart is never the first response.
- Loop termination triggers when an identical failure signature, graph hash, and assignment choice recur 3 times without new evidence.
- Orphaned occurrences are reconciled against external effects before cancellation, with 0 unreconciled cancellations.

***

#### Step 7.3: Close and Reconcile the Run

**Required Actions**:

- Reevaluate top-level acceptance tests, required tasks, branch and join semantics, uncompensated effects, approvals, and artifacts before closing.
- Release all leases and reservations and cancel descendants the terminal decision made unnecessary.
- Issue a terminal status from the closed vocabulary of verified success, verified partial completion, safe rejection, cancellation, compensated failure, budget or deadline exhaustion, and human takeover.
- Produce an outcome package containing verified deliverables, remaining uncertainty, terminal reason, human decisions, costs, timing, plan changes, and complete lineage.

**Required Outputs**:

- A terminal status with a reason code from the closed exit vocabulary.
- An outcome package with deliverables, uncertainty, costs, timing, and lineage.

**Quality Checkpoints**:

- The absence of a running task never closes a run on its own; closure requires a satisfied completion or declared terminal condition.
- 0 leases and 0 reservations outlive the run.
- Uncompensated effects are enumerated in the outcome package rather than omitted.

***

## III. Implementation Guidance for AI Agents

AI agents operating an orchestrator must hold control state outside their own context, treat evidence rather than status claims as authoritative, and bound every recovery path numerically. The following guidance translates the lifecycle into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Orchestrator Agent**: Owns the run contract, exit conditions, authorization scope, and budget ledger. The only role permitted to close a run.
2. **Dependency Resolver**: Evaluates eligibility predicates and is the only role permitted to move an occurrence to ready or skipped. Emits resolution events with evidence.
3. **Scheduler**: Ranks the ready set, selects executors, acquires slots, and is the only role permitted to reserve an occurrence.
4. **Executor Agents**: Accept leases, run one bounded attempt each, emit heartbeats, and report results. Never write authoritative task state.
5. **Completion Validator**: Runs postcondition checks against artifacts and receipts, and is the only role permitted to mark an occurrence succeeded or compensated.
6. **Recovery Controller**: Classifies failures, selects the recovery path, and enforces attempt and plan-generation ceilings.
7. **Liveness Monitor**: Runs the sweep, diagnoses deadlock, livelock, starvation, and orphaning, and escalates when a control cannot restore progress.
8. **Audit Ledger**: Appends every event immutably and materializes run, task, attempt, assignment, artifact, and executor views for fast control.

**Workflow Execution Pattern**:

```
STATE: Phase_3_Eligibility_And_Scheduling
ACTIONS:
  1. Recompute affected frontier, emit dependency-resolution events
  2. Rank ready set with recorded score components
  3. Filter executors by capability, authorization, capacity, cost
  4. Emit selection record with rejection reasons
VALIDATION:
  - blocked_tasks_in_ranked_list == 0
  - selected_executor_capability_match == 1.00
  - full_reconciliation_age_seconds <= 300
  - oldest_ready_age <= class_starvation_threshold
TRANSITIONS:
  IF all_validations_pass THEN next_state = Phase_4_Dispatch_And_Execution
  IF starvation_detected THEN next_state = Phase_3_Aging_Boost
  ELSE next_state = Phase_7_Liveness_Assurance
```

**Two-Phase Action Pattern**: AI agents must separate decision from effect on every consequential transition.

1. **Plan**: Compute the eligible set, ranking, executor selection, and reservation intent without publishing a dispatch.
2. **Validate**: Confirm hard gates, permissions, budgets, and version currency while the decision is still reversible.
3. **Execute**: Commit the reservation and publish the dispatch atomically, only after validation passes.

**Approval Gate**: Human authorization is required before any task whose side effect is irreversible, whose risk tier is the highest declared for its class, whose monetary effect exceeds the contract's approval threshold, or whose compensation is undefined. The gate is a waiting occurrence with request, owner, deadline, allowed decisions, and a default on timeout, and orchestration resumes through a recorded approval event.

**Context Management Requirements**:

- Persist all control state in the durable registry; an executor's context window is a cache, never the source of truth.
- Transfer handoff packages rather than transcripts, holding at least 20% context headroom for the receiver.
- Store intermediate artifacts by reference and pass hashes rather than payloads across queue boundaries.
- Reload state from the registry after any executor restart, replay, or truncation, and revalidate the task version before resuming.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Admission Integrity (After Phase 1)**

- **Automated Check**: Acceptance tests are machine-checkable; every budget dimension carries a numeric ceiling; authorization covers all implied side effects.
- **Agent Action on Pass**: Proceed to task set construction.
- **Agent Action on Failure**: Reject the run or create a clarification task; construct no tasks.
- **Human Review Trigger**: Any objective whose completion cannot be verified automatically.

**Checkpoint 2: Graph Validity (After Phase 2)**

- **Automated Check**: 100% of occurrences bound to registered definitions; 0 unintentional cycles; every join typed; counts within ceilings.
- **Agent Action on Pass**: Proceed to eligibility resolution.
- **Agent Action on Failure**: Hold affected tasks blocked and repair the plan.
- **Human Review Trigger**: If 2 successive repair attempts leave a cycle or untyped join in place.

**Checkpoint 3: Scheduling Fairness (Every Scheduler Tick)**

- **Automated Check**: 0 ineligible tasks ranked; score components recorded; oldest ready age within the class threshold.
- **Agent Action on Pass**: Dispatch the selected occurrence.
- **Agent Action on Failure**: Apply aging or reserved capacity and re-rank before dispatching.
- **Human Review Trigger**: Starvation persisting more than 3 consecutive sweep cycles in a protected class.

**Checkpoint 4: Dispatch Atomicity (After Reservation)**

- **Automated Check**: Transition and dispatch committed together; exactly 1 valid lease; idempotency key bound to the occurrence.
- **Agent Action on Pass**: Allow the attempt to start.
- **Agent Action on Failure**: Abort the reservation, release slots, return the occurrence to ready.
- **Human Review Trigger**: Any observation of 2 or more concurrent leases on one occurrence.

**Checkpoint 5: Completion Evidence (After Validation)**

- **Automated Check**: Success verdicts cite observed artifacts; consequential actions cite external receipts; validator verdict recorded separately from the tool result.
- **Agent Action on Pass**: Commit the outcome and release dependents.
- **Agent Action on Failure**: Classify as failed or uncertain and enter recovery.
- **Human Review Trigger**: Uncertain classifications exceeding 5% of attempts in a task class.

**Checkpoint 6: Recovery Boundedness (After Each Recovery Decision)**

- **Automated Check**: Retries within ceiling; category drawn from the closed taxonomy; plan generations within ceiling; compensation outcomes verified.
- **Agent Action on Pass**: Continue the control loop.
- **Agent Action on Failure**: Escalate rather than retry.
- **Human Review Trigger**: Any irreversible action whose compensation failed or is undefined.

**Checkpoint 7: Closure Completeness (After Phase 7)**

- **Automated Check**: Terminal status from the closed vocabulary; 0 outstanding leases; acceptance tests reevaluated; uncompensated effects enumerated.
- **Agent Action on Pass**: Publish the outcome package and archive the run.
- **Agent Action on Failure**: Hold the run open and complete reconciliation.
- **Human Review Trigger**: Any closure carrying uncompensated irreversible effects.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID / CHECKPOINT_NAME:
PHASE_BOUNDARY:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
FAIL_ACTION:
ESCALATION_OWNER:
RESPONSIBLE_ROLE:
```

### C. Error Handling and Troubleshooting

Failure controls are layered rather than singular, and each carries a numeric bound with a stated consequence when breached.

**Failure control matrix**:

| Control | Mechanism | Default bound | Consequence when breached |
| :-- | :-- | :-- | :-- |
| Timeouts | Separate queue-wait, acknowledgment, start-to-finish, heartbeat, per-attempt, and end-to-end layers | Acknowledgment 30 s; heartbeat at most one third of lease duration | The occurrence enters timed-out and reconciliation begins; a timeout never authorizes a duplicate irreversible action |
| Retries | Bounded by attempts, elapsed time, cost, and failure signature, counted at the orchestration layer | 3 attempts per occurrence, exponential backoff with jitter | The next failure escalates; authorization, schema, deterministic, and quota failures consume 0 retries |
| Concurrency | Atomic transitions, leases, version checks, resource reservations, and a guarded scheduling critical section | Exactly 1 valid lease per occurrence; slots capped per class | The second reservation aborts on version conflict; slot exhaustion holds the occurrence in ready with backpressure |
| Cancellation | Stops unscheduled descendants, requests cooperative stop from running tasks, reconciles non-cancellable effects | Cooperative stop window of 1 heartbeat interval | Cancellation is terminal only after leases and effects are accounted for; the task record is never deleted |
| Human intervention | Waiting occurrence with request, owner, deadline, allowed decisions, and default on timeout | Escalation deadline set per risk tier | The declared default executes and is recorded; orchestration never resumes through an unrecorded state edit |
| Budget guards | Ceilings on tokens, money, calls, tasks, fan-out, depth, elapsed time, and plan generations | 5 plan generations per run; task and fan-out ceilings per contract | Creation halts and the run escalates or exits under budget exhaustion |

**Error Type 1: Uncertain Side Effect After Lost Observability**

- **Symptoms**: A lease expired, a heartbeat lapsed, or an acknowledgment was lost while a consequential action may already have committed.
- **Diagnostic Steps**: Read external state or the target receipt for the occurrence-scoped idempotency key; compare the observed effect against the expected postcondition.
- **Resolution Protocol**: Option A, confirm the effect and mark succeeded through the validator. Option B, confirm its absence and return the occurrence to ready. Option C, hold the occurrence uncertain and escalate.
- **Escalation Trigger**: Any consequential action unresolved after 2 reconciliation cycles.

**Error Type 2: Duplicate Authority or Split Ownership**

- **Symptoms**: Two executors report on one occurrence; a stale executor writes a transition after reassignment; redelivery produces a second attempt.
- **Diagnostic Steps**: Compare task versions and lease identifiers on both reports; confirm the dispatch used an occurrence-scoped idempotency key.
- **Resolution Protocol**: Option A, reject the stale-version transition and retain the rejection as race evidence. Option B, deduplicate at the idempotency key and keep only the first authoritative completion. Option C, compensate the duplicate effect where both reports produced one.
- **Escalation Trigger**: Any observed duplicate irreversible effect halts dispatch for the affected task class.

**Error Type 3: Deterministic Defect Presented as a Transient Failure**

- **Symptoms**: An identical failure signature recurs across attempts, executors, and backoff intervals with no change in the observed error.
- **Diagnostic Steps**: Compare signatures across attempts; confirm input hash and prompt version are unchanged; test the same input against a second executor class.
- **Resolution Protocol**: Option A, reclassify as deterministic and stop retrying. Option B, create a repair task for the defective input, prompt, or tool binding. Option C, replan the dependent region of the graph.
- **Escalation Trigger**: 3 identical failure signatures without new evidence terminate retrying and escalate.

**Error Type 4: Stalled Graph With No Runnable Task**

- **Symptoms**: The run holds no ready, reserved, or running occurrence while its completion condition remains unmet.
- **Diagnostic Steps**: Distinguish deadlock, livelock, starvation, and orphaning using Step 7.2; check whether a join awaits a cancelled or skipped branch.
- **Resolution Protocol**: Option A, resolve the cycle through a declared victim or resource-order rule. Option B, repair a join policy waiting on branches the workflow never produces. Option C, replan the region and supersede the stalled occurrences.
- **Escalation Trigger**: Any stall persisting beyond 2 sweep cycles after a control was applied.

**Error Type 5: Plan Oscillation and Unbounded Expansion**

- **Symptoms**: Repeated replans produce alternating graphs; task count, fan-out, or depth grows without a rise in verified completions.
- **Diagnostic Steps**: Compare graph hashes across generations; measure verified completions per generation; check counters against ceilings.
- **Resolution Protocol**: Option A, freeze at the last generation producing verified progress. Option B, restrict the generating agent to registered definitions only. Option C, escalate to human replanning with completed work preserved.
- **Escalation Trigger**: 5 plan generations in one run, or 2 successive generations producing 0 verified completions.

**Troubleshooting Decision Tree**:

```
RUN IS NOT PROGRESSING
├─ TASK HAS AN OWNER
│   ├─ Heartbeat lapsed → Reconcile effect → succeeded | ready | uncertain
│   ├─ Lease expired, effect confirmed → Mark succeeded via validator
│   └─ Lease expired, effect unknown → Hold uncertain → ESCALATE
├─ TASK IS READY BUT NEVER SELECTED
│   ├─ Bypassed by newer peers → Apply aging or reserved capacity
│   └─ No capable executor available → Widen filter or ESCALATE
├─ TASK IS BLOCKED WITH TERMINAL PREDECESSORS
│   ├─ Join awaits a skipped branch → Repair join policy
│   └─ Dependency cycle → Declared victim, resource order, or ESCALATE
├─ ATTEMPT FAILED
│   ├─ Transient class, budget remains → Retry with backoff, new attempt id
│   ├─ Deterministic class → Repair task, no retry
│   ├─ Policy denial or missing capability → Reassign or ESCALATE
│   └─ Stale plan → Replan, supersede, preserve completed work
└─ NO RUNNABLE TASK AND UNMET COMPLETION
    ├─ Uncompensated effect present → Compensate, verify, then close
    └─ Compensation failed or undefined → ESCALATE, do not close
```

### D. Observability, Metrics, and Implementation Selection

**Logging Architecture**: AI agents must write an append-only event stream as the audit record and materialize run, task, attempt, assignment, artifact, and executor views for fast control. Trace and span hierarchies carry parent identifiers, timings, attributes, and status, and span links preserve causal relationships across asynchronous queue boundaries [24].

**Event envelope template**:

```
EVENT ENVELOPE
  SCHEMA_VERSION / EVENT_ID / EVENT_TYPE:
  WALL_CLOCK_TIMESTAMP / MONOTONIC_SEQUENCE:
  RUN_ID / WORKFLOW_VERSION / PLAN_GENERATION_ID:
  OCCURRENCE_ID / ATTEMPT_ID / ACTOR_ID:
  TRACE_ID / SPAN_ID / CORRELATION_ID / CAUSATION_ID:
  PRIOR_TASK_VERSION / NEW_TASK_VERSION:
  SOURCE_SYSTEM:
  OUTCOME: ACCEPTED | REJECTED | DEDUPLICATED
```

**Level-specific fields**:

- **Run**: objective and task class, requester class, risk tier, definition and policy versions, plan source, input and dataset versions, environment, model, prompt and tool versions, sampling settings, authorization scope, deadline, budgets, entry decision, terminal status and reason, acceptance-test results, final artifacts, and uncompensated effects.
- **Task**: definition and occurrence identifiers, parent, plan generation, creation source, normalized objective, schema versions, artifact references and hashes, predecessors and successors, join policy, hard guards, required capabilities and permissions, resource demand, base and effective priority, deadline, timeout, retry and compensation policies, side-effect and idempotency class, current state, and state version.
- **Transition**: prior and next state, reason code, triggering event, actor, guard evaluation, dependency counts before and after, versions, and whether the transition was accepted, rejected, or deduplicated. Rejected transitions are retained because they reveal races and stale executors.
- **Dependency and graph change**: edge identifier and type, predecessor and successor, required state or artifact, resolution timestamp, evidence reference, block and unblock reasons, time blocked, join version, and added, removed, superseded, or rewired elements with the replan trigger.
- **Scheduling**: eligible set snapshot reference, score components, critical-path estimate, queue position estimate, capacity limits, candidates considered, chosen occurrence and executor, rejection reasons, policy version, and decision latency.
- **Assignment and handoff**: assigner, prior and new owner, capability match, assignment method, lease issue and expiry, acknowledgment time, package version and size, permissions transferred, context omitted by policy, and handoff reason.
- **Attempt**: scheduled, dispatched, acknowledged, started, first and last heartbeat, and finished timestamps; queue-wait, dispatch, startup, execution, validation, and total durations; executor, model, tool and environment versions; attempt number; idempotency key reference; input and output hashes; token, call and cost counters; checkpoint references; response code; error taxonomy; and retryability decision.
- **Validation and recovery**: validator and acceptance-test versions, tested postconditions, observed evidence, per-criterion results, independent checker identity, discrepancies, final verdict, failure signature, causal category, side-effect certainty, retry delay, remaining budgets, superseded work, compensation order and result, human request and decision, and recovery duration.
- **Executor and queue**: registration and capability versions, health, concurrency slots, busy and idle intervals, assignments accepted and rejected, lease expirations, queue depth by class and priority, oldest ready age, arrival and service rates, dead-letter count, redeliveries, and backpressure.

Telemetry must exclude secrets, unrestricted personal data, and hidden reasoning traces; concise decisions, reason codes, evidence references, and externally visible actions suffice [25]. Exports require redaction, access control, encryption, retention limits, and secure artifact references. Metric labels use bounded cardinality while high-cardinality identifiers remain in traces and logs.

**Metric families and targets**: Metrics are computed over comparable task classes and workflow versions, and reported as distributions and percentiles rather than one global average.

| Metric family | Definition | Default target | Action when missed |
| :-- | :-- | :-- | :-- |
| Throughput | Verified terminal tasks per unit time, with run and accepted-artifact throughput alongside | Non-decreasing across versions at matched quality | Test for task fragmentation before accepting a gain as real |
| Cycle time | Verified completion minus creation, decomposed into blocked, queue-wait, dispatch, startup, execution, validation, retry, and human-wait | 95th percentile within the class deadline | Attack the largest decomposed segment before adding capacity |
| End-to-end success | Runs passing the top-level acceptance test over admitted runs, with abstention, compensated-failure, and escalation rates separate | 95% or the class contractual rate | Halt promotion of the workflow version and diagnose by phase |
| Failure and retry | Failed over started attempts, terminal failures over resolved occurrences, retries over started occurrences, retry recovery yield, duplicate-side-effect incidents | Duplicate side effects at 0; retry rate below 20% | Any duplicate side effect halts dispatch for the class pending idempotency review |
| Dependency blocking | Blocked time by predecessor, missing artifact, approval, resource, and erroneous dependency, with critical-path share | Critical-path blocking share below 30% of cycle time | Restructure the graph region contributing the largest share |
| Queue health | Depth, arrival and service rates, oldest ready age, queue-wait percentiles, dispatch latency, starvation count | Starvation count at 0 | Apply aging, reserved capacity, or backpressure before adding executors |
| Utilization and parallel efficiency | Busy leased over available eligible time, productive utilization counting only accepted outputs, elapsed execution against the critical-path bound | Productive utilization at least 80% of raw utilization | A large gap indicates rework; diagnose validation failures first |
| Handoff quality | Acceptance and reassignment rates, time to acknowledgment, package size, missing-context failures, first-attempt success after handoff | Missing-context failures below 5% of handoffs | Expand the handoff contract rather than the transcript |
| Detection and recovery | Stuck-task detection latency and precision, recovery rate, deadlock detection rate, false alarms, time to resolution, graph-signature recurrence | Detection within 2 sweep cadences; safe recovery at 100% | Any safety-violating recovery halts automated recovery for the class |
| Plan stability | Replans per run, change size, preserved useful work, replan latency and cost, oscillation count, recovery success | At most 5 replans with 0 oscillations | Freeze at the last generation producing verified progress and escalate |
| Cost adherence | Tokens, calls, infrastructure time, and money per verified task and successful run, with planning, coordination, execution, validation, and rework shares and tail cost | 95% of runs within every budget dimension | Reduce coordination or rework share before raising the budget |
| Fairness and robustness | Deadline-meeting rate by priority, age at start, inversion count, starvation rate, protected-class delay, all-run success across repetitions, variance across seeds and routes | 0 systematic delay in protected classes; bounded degradation under stress | Audit the priority policy; a stressed run violating a hard constraint blocks promotion |

**Robustness and Promotion Discipline**: A stress suite must perturb benign wording, task arrival order, executor availability, model seed, tool latency, rate limits, malformed responses, duplicate delivery, lost acknowledgment, stale artifacts, permission denial, queue backlog, scheduler restart, external cancellation, and compensation failure, comparing each stressed run against a clean paired run under the same workflow and policy version. A robust system preserves hard constraints, either recovers or fails safely, and shows bounded degradation rather than identical internal traces. Reporting success because at least one of several attempts succeeded is prohibited as a reliability claim. Workflow and policy changes replay against a fixed evaluation corpus using simulated or read-only substitutes for consequential side effects, and promote only when safety and acceptance rates hold while the target metric improves without unacceptable regression in tail latency, cost, fairness, intervention rate, or variance.

**Implementation Selection**: AI agents select an execution substrate by required durability, execution semantics, deployment environment, language, operational maturity, and observability, never by demonstration brevity.

- **Durable workflow engines**: Provide persistent execution history, task queues, declarative activity retry policies, timeouts, and heartbeats [20][26]. Select when tasks are long-running, failures must survive process restarts, or side effects need replay-safe coordination.
- **Scheduled dependency graph platforms**: Provide explicit upstream and downstream dependencies, task-instance states, pools, and concurrency limits enforced by locking at the scheduling transition [7][8]. Select for batch pipelines on periodic schedules.
- **Distributed task queues**: Provide worker pools, routing, and acknowledgment modes whose delivery semantics require explicit idempotency design, because a message can be redelivered when a worker disappears [10]. Select when the need is dispatch and capacity rather than lifecycle governance.
- **Agent coordination frameworks**: Provide orchestrator and worker flows [27][28], handoff primitives, group and manager-led collaboration, human approval points [30], state sharing, branching, loops [29], and run-level tracing [31]. They supply coordination primitives, not a complete reliability policy.
- **Recommended composition**: A durable engine holds authority over lifecycle, state, and recovery while framework runs execute as bounded task attempts inside it, placing probabilistic reasoning inside deterministic lifecycle controls.

***

## IV. Domain-Agnostic Application Guidance

The framework generalises because its phases depend on the structure of the coordination problem rather than the subject matter of the work coordinated.

### 4.1 Cross-Domain Adaptation Principles

**Research and analysis programs**: Acceptance tests become coverage, source support, and reproducibility criteria. Handoffs carry claim identifiers and source artifacts rather than transcripts, and optional evidence branches are declared skippable so one unavailable source cannot fail a run.

**Software delivery**: Acceptance tests become build, test, scan, and health-verification postconditions. Deterministic test failures are non-retryable by classification, while infrastructure crashes are reassigned against the same immutable artifact.

**Service operations and case routing**: Acceptance tests become resolution criteria bounded by response deadlines. Specialist transfers are modeled handoffs, and customer-facing actions above a declared threshold require a modeled approval occurrence.

**Incident response**: Acceptance tests become containment, eradication, and recovery postconditions verified by external state reads. Priority weights deadline slack and blast radius, and escalation owners are named per severity tier.

**Compliance workflows**: Acceptance tests become control-evidence postconditions. Append-only lineage, rejected transitions, and approval records become the audit product, and no branch may be erased.

**Model development pipelines**: Acceptance tests become dataset, training, evaluation, and promotion postconditions, with version manifests covering data, model, prompt, and policy, because metrics are not comparable across unrecorded behavioral change.

### 4.2 Worked Application Patterns

**Multi-agent research pipeline**: A request enters with criteria requiring coverage, primary-source support, and reproducible synthesis. Decomposition creates question framing, source discovery, source reading, claim extraction, contradiction analysis, drafting, citation validation, and final review occurrences. Discovery branches by subtopic, reading depends on selected sources, drafting proceeds per section against available evidence, and final review is an all-required join. Retrieval routes to executors with retrieval access, quantitative claims to a computation-capable executor, and evidence review to an independent executor or human. A timed-out fetch retries only the read task; a permanently inaccessible source triggers substitution or an explicitly unsupported claim, never a whole-run failure. Robustness testing removes a key source, delays one executor, and paraphrases the request; success requires supported conclusions or declared uncertainty, not identical wording.

**Build and deployment pipeline**: The graph contains compile, unit test, security test, package, stage, approve, deploy, verify, and rollback occurrences. Compilation fans out to test shards under a concurrency cap protecting shared infrastructure; packaging waits on an all-required join; production deployment waits on an approval occurrence and a validated artifact hash. A deterministic test failure consumes 0 retries and produces a repair task; a crashed runner is reassigned against the same immutable artifact. A deployment whose acknowledgment was lost triggers a target-state read before any second deployment. Failed health validation triggers a compensation workflow that rolls back to the recorded prior version and verifies service health, and the run stays open until deployment or rollback reaches a verified state.

**Case routing and resolution**: Intake creates classification, identity and entitlement checks, evidence collection, specialist resolution, approval, response, and follow-up occurrences. A simple case stays with one executor; a case crossing a policy or monetary threshold hands off to a specialist with the relevant facts, policy version, collected evidence, and actions already taken. The orchestrator enforces response deadlines, suppresses duplicate outbound messages through occurrence-scoped idempotency, waits on a modeled approval above the declared threshold, and reassigns when a specialist lease expires. Choreography may still distribute analytics and notification events while the orchestrator owns the case outcome.

### 4.3 Scale Adaptation

- **Small scope** (3 to 20 occurrences, 1 to 2 executor classes): Retain the state machine, leases, idempotency keys, and validators. Collapse the scheduler into a single-threaded loop and set the sweep cadence at 60 seconds.
- **Medium scope** (20 to 500 occurrences, 3 or more executor classes): Add priority scoring with aging, per-class concurrency caps, reserved capacity, and full reconciliation every 300 seconds.
- **Large scope** (more than 500 occurrences, replicated schedulers): Guard the scheduling critical section with locking or compare-and-set, partition queues by class, add backpressure at declared queue-depth thresholds, and run deadlock detection continuously.
- **Composite programs**: Where a program exceeds one orchestrator's operational envelope, split it into a parent run whose occurrences are child runs, preserving lineage across the boundary rather than flattening the graph.

***

## V. Limitations and Considerations

**Coordination overhead is often unrecovered**: Registry, queue, persistence, and monitoring cost is paid on every task regardless of value delivered, and a small task set can spend more on coordination than on work. The mitigation is the exclusion rule in Section 1.4, which requires demonstrating that orchestration outperforms a simpler baseline at matched quality and risk before deployment.

**The coordinator is a failure domain**: A centralized decision model concentrates availability risk and creates a shared state surface that can bottleneck throughput. The mitigation is a replicated coordinator with durable state, compare-and-set transitions, and a tested restart path, accepting that replication raises operational complexity rather than removing the risk.

**Verification is bounded by the validator**: A validator confirms only the postconditions it was given, and schema conformity is not semantic correctness. The mitigation is risk-proportionate validation, pairing automated checks with external receipts for consequential actions and independent or human review at the highest risk tier.

**Compensation cannot restore state**: A compensating action counteracts an effect semantically, but other processes may already have observed the original, and exact restoration is often impossible. The mitigation is to define compensation during task design, keep it idempotent, verify its outcome, and route irreversible actions through an approval gate.

**Uncertainty is not eliminable**: An executor can complete an operation and fail before reporting it, so some outcomes remain unknown until an external state read resolves them. The mitigation is a first-class uncertain state, occurrence-scoped idempotency keys, and a rule that no timeout authorizes a duplicate irreversible action.

**Metrics can be gamed by fragmentation**: Task throughput rises when tasks are split, and retry rates fall when retries move inside tools. The mitigation is to report run and accepted-artifact throughput alongside task throughput, count nested retries at the orchestration layer, and pair raw with productive utilization.

**Generated plans can expand without bound**: A planning agent with authority to create tasks, retries, and replans can consume budgets without producing verified completions. The mitigation is hard ceilings on task count, fan-out, depth, attempts, cost, elapsed time, and plan generations, enforced by the orchestrator rather than the planner.

**Telemetry carries confidentiality exposure**: Captured inputs, outputs, and handoff packages may contain sensitive data, and correlation identifiers make that data joinable. The mitigation is data minimization, redaction before export, access control, encryption, retention limits, and a prohibition on logging hidden reasoning traces.

***

## VI. Conclusion and Summary

Task Management and Orchestration is a control discipline before it is an architecture. Its value comes from a durable registry that outlives every executor's context, an explicit state machine whose transitions are legal and atomic, an eligibility predicate no priority score can override, and a completion verdict grounded in observed evidence rather than reported status. The seven phases express one repeating loop: resolve what is eligible, schedule and dispatch it under a bounded lease, execute one attempt, validate it against evidence, recover from a classified failure, sweep for lost progress, and close only under a declared terminal condition.

A system is ready for controlled production only when task and run schemas are versioned; dependencies and join semantics are explicit; legal transitions are enforced atomically; assignments use leases; side effects are idempotent or explicitly non-retryable; outputs carry postcondition validators; retries, fan-out, task count, replans, time, and cost are bounded numerically; timeouts and uncertain outcomes trigger reconciliation rather than duplication; compensation and human escalation are modeled as first-class tasks; scheduler and queue recovery are tested; append-only lineage spans the whole run; and success, cost, latency, fairness, recovery, and robustness are measured against a simpler baseline.

**Key Success Factors**:

- **Durable authority**: State, ownership, dependencies, and completion live in the registry, never only inside an executor's context window.
- **Evidence over assertion**: A status string is not a transition, a tool's success is not an acceptance, and a timeout is not proof that nothing happened.
- **Atomic transitions**: Every state change commits with its event record or through compare-and-set on the task version, so duplicate authority is impossible even when duplicate processing occurs.
- **Causal recovery**: Retry, repair, reassignment, replan, compensation, and escalation are selected from a classified failure category, never from a generic failure signal.
- **Bounded everything**: Attempts, fan-out, depth, plan generations, elapsed time, and cost carry numeric ceilings, and every ceiling names the action taken when breached.
- **Fairness and lineage**: Aging, quotas, and reserved capacity prevent starvation, while superseded plans, rejected transitions, and failed branches are preserved for audit, diagnosis, and robustness measurement.

By following this guide, AI agents can plan what work should exist, orchestrate only what is presently eligible, assign it to a capable and authorized executor, trust evidence rather than status claims, and repeat the resolve, schedule, execute, validate, and recover loop until a declared exit condition is true. Orchestration creates value where coordination complexity is real; where the work is simple, the most robust orchestrator is no orchestrator at all.

***

## VII. References and Further Reading

This guide was converted from a single originating prose document. Entries 1 through 6 are corpus pointers naming that source and the sibling guides whose methods compose with it. Entries 7 through 31 are external references transcribed from the originating prose guide as they appeared there; they were not independently re-verified during this conversion, so a reader depending on a specific claim should consult the cited work directly.

**Corpus pointers**

1. `Task Management and Orchestration in AI Agent Systems` — the originating prose guide from which this operational guide was derived. Source of the task and run model, the state machine, the control loop, the failure controls, the logging fields, the metric definitions, the practical scenarios, and the minimal production-readiness standard.
2. `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guide for the event schema, signal selection, and instrumentation practices underlying Section III.D.
3. `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guide for deriving monitoring constraints and detection thresholds of the kind used by the liveness sweep in Phase 7.
4. `advanced_task_guides/policy-risk/guide_SystemSpecificRiskAssessment.md` — companion guide for assigning the risk tiers and approval thresholds recorded in the run contract in Phase 1.
5. `advanced_task_guides/policy-risk/guide_LifecycleComparison_n_RiskAnalysis.md` — companion guide for comparing lifecycle designs when selecting between orchestration, choreography, and hybrid coordination.
6. `advanced_task_guides/authoring/guide_guidewriting.md` — the house-style specification governing the structure, register, and conformance envelope of this document.

**External references: purpose and operating idea**

7. Airflow DAG concepts — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
8. Airflow scheduler — https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/scheduler.html
9. van der Aalst and colleagues, “Workflow Patterns” — https://www.vdaalst.com/publications/p159.pdf
10. Celery task guidance — https://docs.celeryq.dev/en/main/userguide/tasks.html

**External references: orchestration, choreography, and neighboring patterns**

11. AWS coordination guidance — https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/workflow-coordination.html
12. Azure Architecture Center — https://learn.microsoft.com/en-us/azure/architecture/patterns/choreography
13. Georgievski and Aiello’s HTN overview — https://arxiv.org/abs/1403.7426

**External references: the minimum task and run model**

14. Airflow task instances — https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html
15. Prefect states — https://docs.prefect.io/v3/concepts/states
16. Temporal activity definition — https://docs.temporal.io/activity-definition
17. OpenAI Agents SDK handoffs — https://openai.github.io/openai-agents-python/handoffs/

**External references: the control loop**

18. Smith, “The Contract Net Protocol” — https://dl.acm.org/doi/10.1109/TC.1980.1675516
19. Skaltsis, Shin, and Tsourdos — https://pure.kaist.ac.kr/en/publications/a-survey-of-task-allocation-techniques-in-mas/
20. Temporal retry policies — https://docs.temporal.io/encyclopedia/retry-policies
21. Garcia-Molina and Salem, “Sagas” — https://dl.acm.org/doi/pdf/10.1145/38713.38742

**External references: when to use TMO, and when not to use it**

22. Azure AI agent orchestration patterns — https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns
23. AutoGen teams — https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html

**External references: logging metadata and observability**

24. OpenTelemetry trace concepts — https://opentelemetry.io/docs/concepts/signals/traces/
25. OpenAI Agents SDK tracing — https://openai.github.io/openai-agents-python/tracing/

**External references: implementation choices**

26. Temporal documentation — https://docs.temporal.io/
27. LangGraph workflows and agents — https://docs.langchain.com/oss/python/langgraph/workflows-agents
28. LangGraph persistence — https://docs.langchain.com/oss/python/langgraph/durable-execution
29. CrewAI Flows — https://docs.crewai.com/v1.15.17/en/concepts/flows
30. Microsoft Agent Framework — https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/
31. OpenAI Agents SDK — https://openai.github.io/openai-agents-python/

