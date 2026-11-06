---
created: "2026-11-04T19:46:11Z"
updated: "2026-11-04T19:46:11Z"
---

# Choosing the abstraction, the formal model and the executor

## 1. Is a state machine the right abstraction?

Inventory the known phases, legal ordering, approval gates, side effects, waits and failure obligations.

- Use a state machine if these can be named and validated.
- Use a free-form loop if action choice is genuinely open-ended and low risk, and wrap the loop in a small supervisory machine.
- Reject the state-machine approach when event rates or latency budgets make transition persistence infeasible, when hard-real-time certification requires a different formalism and runtime, or when the machine would merely rename every model thought.
- Always record the model choice and the simpler baseline it was compared with (a free-form loop or a simple transactional executor).

## 2. Formal models

| Model | Use when | Do not use when |
|---|---|---|
| Flat finite-state machine | Control modes are few, mutually exclusive and easy to enumerate; gives simple reachability and transition coverage. | State combinations multiply independently: encoding tool availability, approval status, retry status, subtask phase and cancellation as one combined state name produces state explosion. |
| Hierarchical state machine or statechart | Many substates share entry, exit, timeout or error behaviour (hierarchy); independent concerns truly progress concurrently (orthogonal regions); resuming the prior substate is semantically correct and authorized (history). | Hierarchy would conceal many implicit entry and exit side effects. Never take a shallow- or deep-history transition after policy, identity, credential or external-world assumptions changed; re-enter through a validation state instead. |
| Pushdown model | Nested calls must return to a precise caller with a bounded frame: delegated subtasks, recursive parsing, nested approvals, structured plans. Each frame carries a return state, local variables, caller identity, budget slice and cancellation lineage. | A bounded queue or explicit subgraph suffices. Enforce maximum stack depth, total frames and per-frame tokens, and a rule for propagating failure and cancellation. Arbitrary recursive spawning by an LLM is uncontrolled resource creation, not a pushdown discipline. |
| Petri net or workflow net | Concurrency, synchronization, resource tokens, mutual exclusion or multiple active instances are central; a marking makes simultaneous state explicit. Workflow-net soundness (completion stays reachable, completion is proper, no dead transition) validates fan-out/fan-in. | A small sequential controller is clearer. Inhibitor or reset extensions can make analysis far harder or undecidable; prefer ordinary nets with bounded data abstractions. |
| Probabilistic or nondeterministic transition system | Uncertainty itself affects control and can be calibrated: confidence-based escalation, stochastic environment response, risk-sensitive planning. Keep proposal probability separate from transition legality: an illegal transition never becomes legal because the model is confident. | The LLM would be the unvalidated transition function. Treat the model as a proposer of a structured event or route label from an allowlist; schema conformance does not prove semantic validity, authorization or safety. |
| Free-form loop inside a supervisory machine | The environment is exploratory, the next useful action cannot be enumerated economically, effects are read-only or reversible, and occasional route variation is acceptable. Wrap it in a small machine: planning, acting, verifying, waiting and terminal outcomes, with tool, budget, security and stop guards. | Payments, deployments, access grants, destructive actions, regulated approvals, or any workflow whose legal transitions and obligations are known in advance. |

Begin with the smallest machine that captures the real control and risk boundaries.

## 3. Infrastructure the design must name

Minimum, even for a low-risk single-process prototype: a versioned schema for machine, state, event, guard, transition, action, effect, compensation and terminal outcome; stable IDs (machine definition, run, thread, branch, state instance, transition attempt, event, action, tool call, approval, policy decision); a transition dispatcher outside the model that rejects undeclared transitions; atomic compare-and-swap state changes with one append-only transition journal; deterministic guard functions for authorization, budgets, schema checks and high-risk gates; structured model output followed by allowlist and guard validation; an idempotency-key store for every retryable effect; explicit deadlines, retry classes, backoff, maximum visits, maximum depth and terminal error states; a checkpoint and artifact store for pause and resume; a simulator that injects events, tool results, timeouts, duplicates and failures; metadata-only traces and a queryable transition log; a safe terminal path.

Optional at small scale: a model checker for a small acyclic machine whose state space tests can inspect exhaustively; a broker if all events are synchronous and local; a durable engine if the whole task is short, side-effect-free and cheap to restart. An independent guard or policy engine becomes mandatory as soon as the model can request consequential actions or tenant-sensitive data.

Add when justified:
- A durable workflow engine (or equivalent journaled executor) when work can outlive a process, wait on people or external events, cross deployments, or produce effects that cannot simply be recomputed.
- An event broker when several producers or consumers need asynchronous delivery, buffering or ordered partitions.
- Event sourcing when audit, replay, temporal queries, branching or view reconstruction justify the complexity; CQRS only where separating mutation from read models earns its cost.
- A model checker when errors can cause severe harm or when concurrency and cycles defeat convincing test coverage.

## 4. Executor options

Choose from requirements, not familiarity or feature count. Compare a simple transactional executor, a graph framework and durable engines against duration, waits, concurrency, deployment, audit, language, tenancy and operations. Record which component owns state, history, timers, retries, checkpoints and version routing. Validate the choice with one representative thin slice whose worker is killed at every boundary: it must resume to the correct terminal state without duplicate effects.

- LangGraph: fits when control alternates among model calls, tools, evaluators, workers and human gates and graph-level persistence and inspection are valuable. Parallel nodes run in super-steps with per-key reducers, and an unspecified reducer normally means replacement. Rules: a narrow typed state schema that separates control fields (phase, attempt, approval, pending effects) from message history and evidence; nodes return partial updates; every concurrently written key has an associative, deterministic reducer (commutative if completion order is not guaranteed); conditional edges validate model-produced labels against an allowlist; cycles only for evaluator-refinement, tool-use or clarification loops with progress and visit bounds; dynamic fan-out only after bounding worker count and aggregate tokens; subgraphs with separate schemas for private worker state; a production checkpointer when execution must survive interruption. An interrupted node restarts from its beginning on resume, so keep pre-interrupt work pure or idempotent, never put non-idempotent effects before an interrupt, do not catch the interrupt exception, and keep interrupt ordering deterministic. A checkpointer is not an event-sourced ledger, policy engine or effect coordinator, and a graph picture is not proof of reachability, termination or security.
- Temporal: long-lived code-defined workflows needing durable timers, signals, child workflows, retries and replay across worker failure. Map states to workflow variables or child workflows, events to signals or activity completions, guards to deterministic workflow code and effects to Activities, made idempotent because retries are commonly at least once. Never call an LLM, network, wall clock or random generator directly from replayed orchestration code unless the SDK gives a recorded deterministic primitive. Keep authoritative domain records in their own store, not only in workflow history. Use worker versioning to keep in-flight executions on compatible workers.
- AWS Step Functions: AWS-native integrations, JSON-defined workflows, managed retries, catches, timers, parallel and map states. Retriers and catchers are ordered and error-name-specific, so classify errors instead of one broad policy. A parallel state fails as a unit when an uncaught branch fails. Versions and aliases pin definitions; updating an alias does not change running executions. Review definition, input, permissions, idempotency and effect state before a redrive.
- Restate: durable RPC, per-key virtual objects, journaled handlers, built-in state and concurrency controls.
- Inngest: event-triggered functions, step-level memoization, retries, concurrency limits, throttling, managed pause and resume.
- For any engine, verify cancellation semantics, ordering, history retention, maximum duration, payload limits, replay behaviour, tenancy, encryption, version deployment and portability; do not infer identical guarantees from the shared phrase durable execution. Present product behaviour as to verify against the product's current documentation.

Do not introduce a durable engine for a pure, sub-second, side-effect-free calculation that can restart cheaply, and do not use one as a business database, long-term memory, policy engine or prompt store. If engine history becomes the only place to answer domain questions, audit, serving and orchestration are coupled improperly.
