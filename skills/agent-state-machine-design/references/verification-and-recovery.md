---
created: "2026-11-04T19:46:11Z"
updated: "2026-11-04T19:46:11Z"
---

# Properties, verification, failure recovery, tests, telemetry and migration

## 1. Properties

- Safety: something that must never occur (an effect never executes before approval; a canceled run never starts a new effect; no terminal state has an ordinary outgoing transition; no run exceeds its retry, visit, fan-out, token or cost bounds; a secret-bearing state never invokes an unapproved egress tool).
- Liveness: progress that must eventually occur under stated fairness assumptions (every accepted intent eventually reaches a confirmed, compensated, expired or manual-review status; every fan-out branch is joined, canceled or explicitly abandoned before completion).
- Bounded response: progress required before a deadline.

## 2. Verification order

1. Static validation: unique IDs, valid targets, reachable terminal states, no orphan states, no duplicate priorities, complete event schemas, bounded cycles.
2. Reachability and strongly connected component analysis: flag states that cannot reach any terminal state, transitions that can never fire, cycles without a decreasing measure, and approvals bypassed by alternate edges.
3. Explicit-state model checking of a bounded abstraction: replace unbounded text, timestamps and IDs with equivalence classes; cap queue sizes, retries, workers and recursion; then test that implementation events refine the abstraction. TLA+ suits temporal and distributed coordination properties; it does not replace semantic output evaluation. Use workflow-net soundness for concurrent workflows, statechart reachability for hierarchy and orthogonal regions, and product construction with a property automaton for temporal policies.
4. Runtime monitors when properties depend on live events or dynamic agents: they consume the committed transition stream, keep bounded state, emit pass, pending, violation or inconclusive, and trigger a predefined response. Satisfying selected assertions does not prove total correctness.

Never model-check raw natural language or an unbounded production state, and never weaken a property to make verification terminate. Document abstraction assumptions, fairness, bounds, unchecked data predicates and tool semantics. When a counterexample appears, keep its exact event sequence as a regression case, change one design variable and rerun.

## 3. Failure modes and bounded recovery

| Failure | Recovery |
|---|---|
| Undeclared transition | Reject, log producer and payload hash; do not infer a nearby state. |
| Overlapping guards | Stop with ambiguity, keep the candidates, require definition repair; do not choose by iteration order. |
| Invariant failure before commit | Reject the successor and keep the prior state. |
| Invariant failure after an external effect | Enter reconciliation or compensation; do not pretend the transition was atomic. |
| Lost event | Detect the sequence gap, pause dependent transitions, fetch from the authoritative producer, escalate after the deadline. |
| Duplicate or late event | Deduplicate; if it refers to an obsolete state version, record and ignore or reconcile under explicit policy. |
| Stuck state | Verify timer delivery and pending dependency, emit a timeout event once, then retry, cancel, compensate or escalate by policy. |
| Livelock | Stop after the visit or no-progress threshold, checkpoint, enter a diagnostic or manual-review state. |
| Deadlock at join | Identify missing branches and resource waits, cancel safe branches, go to timeout or partial-result handling. |
| Reducer conflict | Reject the join, keep branch outputs, apply owner or human resolution. |
| Ambiguous effect | Query the destination with the idempotency key; never retry until status is authoritative. |
| Compensation failure | Retry within its own policy, then enter compensation_failed with an owner and an unresolved-obligation record. |
| Prompt-injection route hijack | Reject the unauthorized event or route, quarantine the source content, revoke delegated credentials, inspect later transitions. |
| Forged or stale approval | Deny, expire the token, require a new approval bound to current state and arguments. |
| Checkpoint corruption | Verify hashes, restore the last valid checkpoint, replay recorded events, quarantine the corrupt record. |
| Replay nondeterminism | Stop, route to a compatible worker or patch; do not force new code through old history. |
| Definition mismatch | Keep the execution on its pinned version or run an approved migration; never resolve against a moving latest. |
| Telemetry outage | Buffer bounded metadata securely, or stop high-risk effects when auditability is mandatory. |

Every recovery path names the changed input, maximum attempts, deadline, authority, idempotency behaviour, effect risk and terminal outcome. Never repeat an unchanged deterministic failure.

## 4. Test layers

Definition tests (unique IDs, valid targets, known schemas, terminal closure, bounded cycles); guard tests (true, false, boundary, missing, stale, unauthorized, adversarial inputs); reducer tests (identity, associativity, commutativity where required, idempotence, deduplication, conflicts); transition tests (preconditions, successor schema, invariants, postconditions, emitted events, rejected direct writes); path tests (happy paths, each terminal state, each retry class, timeout, cancellation, approval denial, compensation); transition-pair tests for each reachable adjacent pair; property-based stateful tests that generate event sequences and assert global invariants; concurrency tests (completion order, duplicates, dropped, delayed events, cancellation races); fault injection (kill workers, stores, brokers, policy services, tracing at every boundary); replay tests (identical state, completed effects skipped); simulation with virtual time; adversarial tests (injected transition names, forged approvals, stale tokens, malicious tool text, resource-exhaustion loops); migration tests. Edge coverage of every transition is not proof; also cover state pairs, paths, guard clauses, invariants, effects, compensation and concurrency order. Report a coverage figure only with its reachable denominator, path definitions and version cohort.

## 5. Telemetry to emit

Emit state-entry, state-exit, transition-attempt, guard-decision, action, effect, retry, timeout, compensation, approval and terminal events, as metadata only: store prompts, events, tool arguments and state payloads only in a separately authorized store and use hashes or categorical summaries in traces; never log hidden reasoning. The telemetry is sufficient when an operator can answer why a run is waiting, which guard denied it, which effect is ambiguous, which version owns it and how to resume safely without reading raw prompts. Signals worth alerting on: stuck states, loop counts, retry and compensation spikes, queue age, guard denials, transition coverage, terminal distribution, invariant violations and version cohorts.

## 6. Versioning and in-flight migration

Version topology, state schema, event schema, guards, reducers, actions, effects, compensation, policy bindings, prompts, model routes, tool schemas and runtime separately, bound together in an immutable release manifest. Pointing in-flight executions at the latest definition is not a migration plan. Choose one strategy per in-flight cohort:
- Drain: stop new starts on the old version and let runs finish there; when duration is bounded and old workers can stay supported.
- Continue-as-old: route each execution to a compatible worker version; for long-lived histories where replay compatibility is paramount.
- Checkpoint migration: pause at a safe boundary, snapshot and hash state, reconcile effects, transform state deterministically, validate target invariants, write a migration event, keep a rollback reference; only with deterministic, tested transforms.
- Bridge states: temporary compatibility states or event adapters when external producers cannot switch atomically; remove them after the cohort drains.
- Terminate and restart: only when restart is safe, effects are reconciled and users are informed.

Inventory active state counts, pending timers, interrupts, approvals, branches, effects, retries and compensation; prove or test a mapping for every reachable old state; make the transformer idempotent. Never reinterpret an old approval as covering a broader new effect. If the new definition cannot interpret the old state or approval, keep the old worker or terminate safely. Do not combine topology, policy, model and tool changes in one release unless an emergency owner accepts the loss of attribution.

## 7. Readiness for limited production

1. The abstraction is justified against a simpler free-form or transactional baseline.
2. States, events, guards, transitions, actions, effects, compensations, waits and terminal outcomes have versioned typed contracts.
3. Direct state mutation is blocked and every commit uses expected-version concurrency.
4. Authorization and high-risk guards are deterministic and independent of the model.
5. LLM route proposals are schema-constrained, allowlisted, and abstain or escalate safely.
6. Every cycle, retry, wait, fan-out, recursion and queue has enforced bounds and a safe terminal path.
7. Every effect has an intent record, idempotency key, acknowledgement evidence, reconciliation, and compensation or manual-resolution policy.
8. Parallel branches have ownership, reducers, join, cancellation, late-result and conflict semantics.
9. Checkpoints resume in a fresh process without repeating completed effects.
10. Static validation finds no orphan states, invalid targets, ambiguous priorities or unbounded cycles.
11. Critical safety, liveness, bounded-response and proper-completion properties pass model checking or justified equivalent analysis.
12. Unit, path, property-based, concurrency, fault, adversarial, replay and migration tests meet predeclared gates.
13. Transition logs and traces reconstruct active state, guard decisions, effects, waits and terminal reasons without unsafe payload logging.
14. Stuck, loop, retry, timeout, compensation, terminal-error, coverage, fidelity, latency, cost and security metrics have baselines and alerts.
15. Old and new definitions can coexist, drain or migrate with tested compatibility and rollback.
16. Operators have rehearsed cancellation, ambiguous-effect reconciliation, compensation failure, lost events, checkpoint corruption, policy outage and worker rollback.
