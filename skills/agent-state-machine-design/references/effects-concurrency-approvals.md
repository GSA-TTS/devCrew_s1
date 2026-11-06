---
created: "2026-11-04T19:46:11Z"
updated: "2026-11-04T19:46:11Z"
---

# Effects, retries, compensation, concurrency, approvals and security controls

## 1. Effects

For every effect define: intent record, destination, idempotency key, acknowledgement evidence, reconciliation query, retry safety, and compensation or manual remediation. Put non-idempotent work after approvals and durable intent records. An exactly-once claim is not enough: the external destination must enforce the same idempotency key or support authoritative reconciliation. Done only when ambiguous outcomes block retry and enter reconciliation, and the system neither loses a confirmed effect nor repeats one under injected lost acknowledgements and duplicate deliveries.

## 2. Failure classes and retry

Classify failures before retry:
- Transient transport, rate-limit or dependency failures: may retry with bounded exponential backoff and jitter.
- Invalid input, failed authorization, invariant violations, unsupported transitions: deterministic; never retry unchanged.
- Ambiguous outcomes: reconcile before any retry.
- Capacity or policy failures: wait for an event or enter a human-review state.
- Cancellation and expiry: move to named terminal or compensating paths.

Every retry policy states: error classes, maximum attempts, maximum elapsed time, backoff, jitter, per-attempt timeout, total deadline, cost cap, idempotency behaviour and terminal transition. Use separate schedule-to-start, start-to-close, heartbeat, idle and overall workflow deadlines when the engine supports them. A timeout is an event, not merely an exception: decide whether it causes retry, fallback, compensation, escalation or expiration.

## 3. Compensation (saga)

Use a saga when one business operation spans independently committed services and atomic rollback is unavailable. Record each completed forward action and its compensation; compensate in reverse dependency order unless the domain says otherwise. Compensating actions are application-specific, may not restore the exact prior state, and need their own recovery handling. Do not call compensation rollback: a sent email cannot be unsent, a disclosed secret cannot be undisclosed, a financial reversal is a new auditable transaction. Mark each action compensable, non-compensable or requiring manual remediation before implementation. Never retry compensation blindly: give it idempotency, deadlines, escalation and a terminal compensation_failed state. Compensation occurs only for a recorded successful forward effect.

## 4. Concurrency and joins

- State whether concurrent regions share no state, append to a collection, reduce values, acquire exclusive resources, or synchronize at a join. Prefer no shared mutable state.
- Each fan-out: branch IDs, maximum parallelism, deadline, cancellation propagation, quorum, and whether partial results are acceptable.
- Each fan-in: expected branches, completion condition, reducer, missing-branch behaviour, duplicate handling and conflict policy.
- Reducers under parallel completion are associative, and commutative unless branch order is deterministic and recorded; deduplication is explicit. Concatenating model messages in arrival order is not a stable reducer when order affects later prompts.
- Multi-agent: single-writer ownership per state field wherever possible; otherwise expected-version writes, leases with fencing tokens, or a conflict-free data type whose semantics match the field. Never last-write-wins for approvals, permissions, money, external effects, user corrections or mutually exclusive decisions. A worker's completion is an event proposed to the parent machine, not authority to mutate parent state.
- Tolerate duplicate, late and out-of-order events: partition ordering by run or aggregate ID, carry causal and correlation IDs, and at joins compare branch inputs against the parent version they forked from; stale results are revalidated, rebased or discarded.
- Done when every parallel branch can finish, fail, time out or cancel without stranding the parent, and every shared field has a conflict policy.
- Test deadlock, livelock, starvation, duplicate completion, one branch never returning, cancellation racing with success, and a late success arriving after compensation.

## 5. Interrupts and approvals

Define the approval payload, approver role, exact proposed effect, expiry, revocation and resume event. Persist before waiting. Bind each approval to machine version, state version, exact action and arguments, amount or scope, approver, expiry and nonce; invalidate it if material arguments, target, policy or state change. On resume, revalidate identity, state version, machine version, policy, deadline, effect arguments and external reality, after every wait. Exit with approved, denied, expired, canceled or superseded. Never treat silence as approval. Separate proposer, approver and executor for high-risk transitions.

## 6. Security controls

Treat every transition as an authorization boundary. Threats: a user or retrieved document naming a privileged state; prompt injection causing a route change; a tool result fabricating approval; a worker impersonating a parent; replay of a stale approval; confused-deputy access through a high-privilege state; event spoofing; schema downgrade; forged completion; denial of service through loops or fan-out. Controls:
- Derive active state from trusted storage, never from model text.
- Allow only event types registered for the current state and an authenticated producer.
- Keep permissions, budgets, target allowlists and approval records outside model-editable context.
- Re-authorize immediately before effect execution with current identity, resource, action, environment and time.
- Use least-privilege, short-lived credentials issued only after guards pass.
- Cap visits, recursion, fan-out, payloads, tool calls and spend before allocation.
- Sign machine releases and reject unknown or downgraded schemas.
- Rate-limit event producers and quarantine malformed or repeatedly denied events.
- Keep a kill switch and cancellation path outside the model.
- Minimize tools and privileges, and require human approval for high-impact actions.
