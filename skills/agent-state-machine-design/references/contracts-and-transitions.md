---
created: "2026-11-04T19:46:11Z"
updated: "2026-11-04T19:53:06Z"
---

# Terms, invariants, contracts and the transition algorithm

## 1. Terms

At any decision boundary the active configuration is one state, a nested state stack, or a set of concurrently active regions; the active state is never inferred from free-form conversation text.

- Guard: a side-effect-free predicate evaluated against an immutable transition snapshot; it answers whether a transition is eligible.
- Transition action: deterministic state mutation. Effect action: interaction with the outside world; needs idempotency and reconciliation.
- Compensation: a new business action that mitigates a prior committed effect; it is not time travel and may itself fail.
- Terminal state: permits no ordinary outgoing transition; administrative repair, archive or migration paths are separately authorized.

## 2. Invariants that apply to every design

1. The control plane, not the LLM, owns the active state and the transition set.
2. All mutation occurs through declared transitions; direct state writes are rejected.
3. Guards are deterministic, side-effect-free, versioned and evaluated immediately before commit.
4. Authorization is both a guard and an execution-time check; a prior model decision never grants permission.
5. One transition attempt reads one state version and commits one successor version atomically.
6. Every event and effect has an idempotency key and an attributable producer.
7. Replay returns recorded non-deterministic results; it does not call a model or external service again.
8. State, context, event history and external reality are distinct; resume reconciles all four.
9. Parallel writes use declared reducers or ownership; last-write-wins is never an accidental default.
10. Every cycle has a progress measure, visit limit, deadline and terminal escape.
11. Every nonterminal state has at least one eventually enabled progress, cancellation, timeout or failure path.
12. Every effectful transition defines success evidence, ambiguity handling, and compensation or manual resolution.
13. Untrusted text cannot introduce a state, event, guard, tool, destination or approval.
14. Machine and state-schema versions are pinned per execution.
15. Every transition is observable without raw sensitive context in telemetry.

## 3. State domains

Define separately: workflow control state, domain (business) state, model-visible working context, immutable event history, external effect state, and derived read views. Assign one authority and one consistency expectation to each. Done when no field has two writable authorities and no critical fact exists only in a prompt transcript. Eventually consistent read views are never presented as the just-committed write state.

## 4. Terminal outcomes

Define the outcomes the workflow can end in: successful, rejected, canceled, expired, failed-recoverable, failed-terminal, compensation-required, compensation-failed and manual-review. A safe terminal path exists for every run (completed, rejected, canceled, expired, failed-terminal or human-review-required). Before enumerating states, list users, tenants, task classes, allowed and prohibited effects, data domains, expected duration, concurrency, human roles, deadlines and recovery obligations; every task class needs an acceptance condition, a forbidden outcome and a maximum authority.

## 5. State contract

Fields of each state: stable state ID, display name, parent region, state kind, entry event, required fields, invariant IDs, allowed event types, permitted outgoing transition IDs, deadline, maximum visits, owner, policy class, context-view selector, and terminal status where applicable. An explicit unknown or repair state is allowed only if it fails closed; it is never a permissive wildcard.

Enumerate states from external obligations and failure modes, not happy-path screens. Remove synonyms and payload-only distinctions. Add explicit waiting, timeout, cancellation, ambiguity, repair and terminal failure states where they change behaviour. Done when every nonterminal state has a progress or safe-stop path.

Complexity control: before adding a state, ask whether it changes legal events, guards, effects, deadlines, ownership or observability; if it changes only payload data, keep it as a typed field. Before adding a boolean flag, ask whether its combinations create illegal or untested configurations; if so, make it an explicit state or orthogonal region. Factor shared behaviour into hierarchical parents, separate independent concerns into bounded orthogonal regions, parameterize repeated states instead of cloning them, use submachines with typed entry and exit contracts, abstract large domains into guard-relevant equivalence classes, keep policy predicates outside the topology when they do not alter the lifecycle, and refuse dynamic topology changes that cannot be versioned and observed.

## 6. Event contract

Fields of each event: event ID, type, schema version, producer, observed time, effective time, correlation and causation IDs, run and state version, payload reference, integrity hash, sensitivity class and deduplication key. For each event type name its producer, schema, ordering key, deduplication rule and freshness policy. Every consumer is idempotent: deduplicate on producer and event ID, keep the highest contiguous sequence per ordering key, and define behaviour for duplicates, gaps, reordering and late events. Use dead-letter handling for poison events only after bounded retries classify the failure as persistent; a dead-letter record carries original event reference, attempts, last error, owner, next review time, replay authorization and retention.

Use event sourcing when exact reconstruction, temporal audit, branching, delayed consumers or correction by superseding events is required; current state is then a projection of accepted events and snapshots are not independent truth. Replay is deterministic with respect to recorded inputs (model responses, tool results, clock reads, random choices, policy decisions, external acknowledgements). Regeneration is a fork with a new lineage, labelled counterfactual or retry, never a replay.

## 7. Transition contract

Fields of each transition: transition ID and version; source configuration; triggering event type and schema; target configuration; priority; guard IDs; action IDs; effect class; idempotency-key derivation; retry and timeout policy; compensation reference; required approval; concurrency rule; precondition and postcondition IDs; emitted events; terminal reason code.

For each source state and event, define target, guards, actions, effects, postconditions, retry class and compensation. Deny and authorization guards are independent of model output. Specify deterministic tie-breaking or reject ambiguous eligible transitions. Unknown events are ignored, quarantined or routed to a named error state according to a stated policy. Done when no event-state pair silently falls through and no critical transition lacks a guard.

## 8. Evaluating one transition

1. Authenticate the event producer; resolve tenant, principal, run and branch.
2. Validate event schema, sequence, freshness, signature where required, and deduplication key.
3. Load the exact machine and policy versions pinned to the execution.
4. Read the current state under a lease or expected-version constraint.
5. Enumerate only transitions declared for that state and event type.
6. Evaluate deny rules and authorization before model-dependent conditions.
7. Evaluate deterministic guards against the same immutable snapshot.
8. If several transitions remain, resolve by declared priority or raise an ambiguity error; never depend on iteration order.
9. Write a transition-intent record before an external effect.
10. Run pure state actions and validate the proposed successor against schema, invariants and postconditions.
11. Run effect actions through the effect ledger and the destination's idempotency protocol.
12. Atomically commit successor state, transition result and emitted events, or record an incomplete effect requiring reconciliation.
13. Emit state-exit, transition, state-entry and policy-decision telemetry.

Entry: one authenticated event and one current state version. Exit: exactly one successor version commits, the event is rejected with a reason, execution waits without mutation, or the run enters a named repair or terminal state. Repeat only when a new event arrives or a retry policy changes the attempt number and backoff time.

## 9. LLM decision points

- Define exactly which states may call a model and what it may propose.
- Require structured route output with reason, evidence references and uncertainty; map only allowlisted labels to internal events.
- After parsing, validate enum, state-specific schema, evidence references, confidence policy and deterministic guards. Structured output is not authorization or semantic correctness, and model confidence never overrides a guard.
- Retry generation only with a changed prompt or clarified evidence and a bounded attempt count; otherwise transition to clarification, fallback or review.
- Test malformed, out-of-enum, low-confidence, adversarial and contradictory outputs.
- Do not ask the same potentially compromised model whether a privileged transition is safe; do not rely on prompt warnings, delimiters or confidence thresholds as authorization; never expose a generic set-state tool, only narrowly scoped events or commands whose effects are checked independently.
