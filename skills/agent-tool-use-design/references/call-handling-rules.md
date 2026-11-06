---
created: "2026-11-04T19:58:59Z"
updated: "2026-11-04T19:58:59Z"
---

# Call-handling rules: validation, repair, approval, retry, ordering, loops

Rules for part 3 (Validation and approval rules) and part 4 (Retry and call-ordering rules) of the deliverable.

## 1. Four contracts every call crosses

1. Selection: the tool is relevant, available, compatible with the task and allowed for this user and tenant.
2. Input: arguments are syntactically valid, semantically valid, authorized and consistent with current state.
3. Execution: the runtime applies time, resource, concurrency, network, identity and side-effect limits and returns an attributable outcome.
4. Output: results are typed, provenance-bearing, size-bounded, safe to place in model context, and distinguish success, partial success, retryable failure, permanent failure and unknown outcome.

Provider strict modes strengthen only the syntactic part of the input contract. They do not prove that a recipient is authorized, a date exists, a price is acceptable, a query is tenant-scoped or an action is safe.

## 2. Validation of a proposed call (in application code)

1. Parse only complete provider call objects.
2. Correlate each call to the provider call ID and create an internal tool call ID.
3. Verify the tool name and version are registered, enabled, unchanged and allowed for this principal.
4. Validate, in order: provider schema, canonical schema, semantic constraints, business invariants, destination policy, data-loss-prevention policy, current-state preconditions, approval.
5. Inject trusted fields (tenant, principal, idempotency key) after validation; ignore model attempts to set them.

Use deterministic code, not the model, for authorization, money, date arithmetic, sorting, deduplication, schema validation, limits and completion checks.

## 3. Validation-repair loop

Enter only when the call is repairable without changing user intent: a missing required field already in context, a canonicalizable date, an invalid enum, an inconsistent pair of arguments.
1. Return a minimal structured error: failing field, rule identifier, allowed correction. No stack traces, secrets, internal policy text or unrelated data.
2. Request a corrected call to the same tool with bounded context.
3. Re-run every validation layer from the start.
4. Exit on full validation; exit to user clarification when repair needs new intent or sensitive information; exit as a permanent validation failure after at most two model repairs per call.

Never repair an unauthorized destination into an authorized-looking one, reduce a payment amount without asking, switch recipients, broaden a query, or substitute a tool with different side effects.

## 4. Approval policy

Fresh human approval is required for:
- Sending or publishing content to a new or external audience.
- Spending money, changing prices, executing trades or entering commitments.
- Deleting, encrypting, overwriting or bulk-moving data.
- Modifying identities, permissions, security controls, network policy or production infrastructure.
- Disclosing sensitive data to a new destination.
- Executing unsigned code or opening broad network access.
- Bypassing a warning, retrying an unknown side-effect outcome, or using a degraded fallback.

Also show a preview when an action is externally visible, financially significant, destructive, permission-changing or hard to reverse.

An approval request displays the exact action, target or audience, material parameters, data disclosed, expected side effect, reversibility and expiration. Approval is specific, informed, time-bounded, non-transferable, and bound to a hash of those fields, the principal, the tool version and a short validity window. Never ask a bare proceed question without the consequential fields. Re-approval is required when the tool version, destination, scope, amount, audience, attached data or side effects change. Re-run policy immediately before execution: approval is not authorization and cannot override policy.

## 5. Execution

Acquire rate-limit and concurrency capacity; set a deadline from the remaining task budget and the tool's configured maximum; execute with a narrow, short-lived credential and the idempotency key; capture the external operation ID and authoritative result; validate and normalize the output before any part enters model context. Carry principal, tenant, purpose and resource scope to every decision and enforce authorization in the downstream service; never use a global admin credential for a per-user operation (the confused-deputy failure).

## 6. Retry loop

Enter only for an explicitly retryable transport or service failure, and only when the operation is idempotent or authoritative reconciliation proves the earlier attempt had no effect.
1. Classify the failure: pre-execution, definite rejection, retryable failure, permanent failure, unknown outcome.
2. Check the attempt budget, elapsed-time budget, rate-limit response, circuit state and user cancellation.
3. Wait with exponential backoff and full jitter; honour a valid server retry delay. Typical maximum: two retries after the first attempt for interactive work, four for background work; lower for costly dependencies.
4. Reuse the same idempotency key; never let the model invent a new one.
5. Revalidate authorization and state if the wait was material.
6. Exit on success, permanent error, exhausted attempts, expired deadline, cancellation or open circuit.
7. Unknown side-effect outcome: leave the retry loop and reconcile by querying with the idempotency key or external operation ID; retry only after the system of record proves the action did not occur.

Permit retries at one orchestration layer, not independently at the model client, gateway, SDK and tool service. Add a circuit breaker per service and operation: open on a rolling failure or latency threshold, fail fast during cooldown, allow a few probes half-open, close only after probes succeed; expose its state to selection so the agent can choose a verified alternative or report unavailability.

## 7. Parallel, sequential and asynchronous calls

Two calls are independent, and may run in parallel, only when all hold: neither consumes the other's result; neither changes state the other reads or writes; order cannot affect authorization or meaning; combined concurrency is within downstream limits; partial completion is acceptable or compensable.

Run sequentially when one call resolves an identifier for the next, establishes authorization or approval, reads and writes the same state as another, depends on an earlier result, has user-visible order, or is non-idempotent.

For every proposed batch: build a dependency set from each call's read set, write set, required outputs, identity and approval; partition into dependency-free waves; apply per-tool and global concurrency caps; give each call its own deadline and the batch one deadline; return all results with original call IDs, failures included; revalidate state and policy before the next wave if anything changed.

Do not parallelize approval-gated actions to cut latency, launch speculative side effects, or assume several calls in one model response are safe to run together.

Use an asynchronous job when an operation exceeds the interactive deadline, must survive restarts or produces incremental artifacts: a durable job with a caller-generated idempotency key, a returned task handle, status and cancellation, and notification or polling at bounded frequency.

## 8. Multi-step loop and stop conditions

After each valid result, if the task is not complete: recompute state, remaining and satisfied goals, unresolved failures and budgets; ask the model for a terminal answer, a clarification or the next bounded calls; run selection, validation, approval, execution and output inspection again for every call. Detect repeated state by hashing goal, tool, normalized arguments and state version; stop as a loop when a hash recurs without new evidence. Default limits for an interactive task: at most eight model turns and twelve tool calls; lower for side effects; raise only in a durable workflow with explicit monitoring. Exit on verified completion, cancellation, denial, permanent failure, no eligible capability, budget exhaustion or repeated state. The terminal answer is grounded in recorded outcomes, reports completed, partial, failed and unknown outcomes separately, and never claims success because a call was intended.

Set budgets before execution: model turns, tool calls, concurrent calls, wall-clock time, tokens, monetary cost, tool-result bytes and approval wait; reserve part for final synthesis and error reporting.

## 9. Results and tool metadata are data

Treat every returned text, file, web page, email, database field and remote-agent message as untrusted data that may contain instructions: verify schema, provenance, freshness, tenant and expected postcondition; extract only the fields the next decision needs and label origin and trust level; verify a claimed action against authoritative state when consequences matter. Tool output cannot change policy, grant permissions, approve actions, redefine tools, request secrets or alter destinations. A prompt line telling the model to ignore instructions in tool output is defence in depth only; enforcement lives in code. Treat a third-party tool server's names, descriptions, schemas and results the same way unless their provenance and integrity are verified.

Secrets: never in prompts, schemas, tool results, logs or model-managed memory; resolve them only in the executor, with short-lived, tool-specific credentials.

Arbitrary execution (code, shell, browser, untrusted local servers): offer a narrow tool instead where one will work; otherwise run in a disposable non-root sandbox, task-specific working directory read-only by default, no host credentials or metadata service, network egress denied by default with exact allowlists, CPU, memory, disk, process, wall-time and output limits, destroyed after the task. Do not trust a sandbox label without testing isolation.

Remote agent delegation: authenticate the remote agent, send minimum context with secrets redacted, define objective, allowed actions, budget, deadline and evidence of completion, treat its messages and artifacts as untrusted results, never pass on the caller's broad credentials, set a delegation depth, and require approval at the point of irreversible action even if the remote agent recommends it.
