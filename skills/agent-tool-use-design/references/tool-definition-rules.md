---
created: "2026-11-04T19:58:31Z"
updated: "2026-11-04T19:58:31Z"
---

# Tool definition rules: need, names, descriptions, schemas, envelopes, versions

Rules for part 1 (Tool inventory) and part 2 (Tool definitions) of the deliverable. A model call is a proposal; application code owns validation, execution and consequences.

## 1. Is a tool warranted?

Use function calling when at least one holds:
- The answer depends on state that changes after training (inventory, balances, system status, current documents).
- The task needs private or tenant-specific data that a policy-controlled lookup can retrieve.
- Correctness depends on deterministic computation, database constraints, a compiler, a verifier or another authoritative service.
- The user asked for an external side effect (create a ticket, send a message, change a record, deploy code, control a device).
- Another software component will consume a typed intermediate value.
- A long-running operation must be started, monitored, cancelled or resumed.
- A bounded specialist agent has a capability the current agent lacks, under a clear delegation contract.

Do not use function calling when:
- The task is self-contained language work (explanation, transformation, brainstorming, summarizing supplied text).
- Every request must execute exactly one known function: route in application code instead of asking the model to choose.
- The model lacks the information to choose safely: ask the user or run a deterministic lookup first.
- The action is prohibited, cannot be authorized, cannot be reversed, or has no acceptable approval path.
- The same result is already in trusted state and fresh enough.
- The tool's reliability, ownership, data handling or side effects are unknown.
- The only capability offered is an open-ended shell, browser, SQL, URL-fetch or admin tool where a narrow operation would do.

If the goal is only to make the model's reply fit a schema, use the provider's structured response mode; do not invent a no-op tool to get JSON.

## 2. Risk classes (inventory column)

Assign each tool one class: read-only public; read-only private; reversible write; externally visible write; financial or security change; destructive; arbitrary execution. Stop and ask when a tool's owner or data handling is unknown.

## 3. Names and boundaries

- Stable, action-oriented, unambiguous names in a domain_object_action shape, for example `ledger_entry_get`, `ledger_entry_reverse`. Namespace by domain when collisions are possible.
- Avoid generic names: `run`, `query`, `manage`, `execute`.
- Never put a secret, tenant ID, hostname or environment in a model-visible name.
- Split tools by authority and consequence, not by the shape of the underlying API: reading and sending mail are two tools because they need different scopes and approvals; prefer a get tool and a mark-paid tool over one admin tool.
- One tool, one coherent effect. Combine deterministic, inseparable substeps behind one narrow operation when they share one authorization decision and one atomic outcome. Split when steps differ in permissions, approval needs, failure recovery or audit requirements.
- Do not expose transport details the model does not need.

## 4. Description elements

Every description states:
1. The exact operation and its authoritative data source.
2. Positive triggers: when to select it.
3. Negative triggers: when it must not be selected.
4. Required preconditions and permissions.
5. Side effects, reversibility, and whether it contacts an external party.
6. Freshness and consistency guarantees.
7. Output shape and meaningful error classes.
8. A safe alternative when selection is inappropriate.

Include two to five input examples when the provider supports them or selection quality is weak. Put confusing near-neighbour examples in the evaluation set rather than in every prompt.

## 5. Input schema rules

- Explicit types, descriptions, formats, enums and units. Prefer canonical identifiers, obtained by a separate resolver step, to free text.
- Never ask the model for server-controlled fields: tenant ID, authenticated user ID, role, final authorization scope, price from the system of record, audit principal. Inject them from trusted session state after validation, and ignore any model attempt to set them.
- State-changing tool: an idempotency key or operation ID controlled by the orchestrator; an expected version or precondition token where optimistic concurrency matters; a dry-run or preview mode when practical.
- Money: currency plus decimal amount under deterministic decimal arithmetic, not a binary float.
- Timestamps: require a time zone or an absolute standard format.
- File paths and URLs: canonicalize and check against allowlists after parsing.

Schema construction:
- Use the smallest schema that expresses the business contract; prefer shallow objects, short enums, explicit units, bounded arrays and provider-supported primitives.
- Reject unknown fields in both provider strict mode and application validation.
- Prefer a discriminated union or separate tools to a polymorphic union.
- Compile schemas at build time; test minimum, maximum, null, Unicode, locale, timestamp, nested-object, empty-array and adversarial-string cases.
- Constrained decoding helps when malformed structure is itself a major failure mode; it is never evidence of truth or authorization. Skip it for free-form prose, for schemas too broad to add safety, when the provider subset cannot express the critical constraints, or when its latency is unacceptable and a tiny deterministic parser is simpler.
- Treat refusal, truncation, safety stop, maximum-token stop and interrupted streaming as separate outcomes, not schema failures. Never execute streamed arguments incrementally: buffer until the call is complete, then parse and validate.

## 6. Output envelope

Return a typed envelope with: outcome category, data, error code, safe error message, retryability, external operation ID, state version, provenance, freshness timestamp, partial-result indicator. Do not make the model infer success from prose; keep raw provider responses out of model context and pass the smallest trusted representation.

Outcome categories:
- `success`: the operation is complete.
- `partial_success`: some declared suboperations completed; list them.
- `invalid_request`: input failed deterministic validation.
- `unauthorized` or `forbidden`: identity or policy denied execution; do not retry without changed authorization.
- `not_found` or `conflict`: business-state failure needing new information or replanning.
- `rate_limited` or `temporarily_unavailable`: retryable under policy.
- `timeout_unknown`: the caller timed out and does not know whether a side effect occurred; reconcile before any retry.
- `permanent_failure`: retrying unchanged input is not useful.

Example envelope for a reversible write (illustrative values):

```json
{"outcome": "timeout_unknown", "data": null, "error_code": "UPSTREAM_TIMEOUT",
 "message": "Shelf move not confirmed", "retryable": false,
 "external_operation_id": null, "state_version": "v41",
 "provenance": "warehouse-system", "fresh_as_of": "2026-03-02T10:15:00Z",
 "partial": false}
```

## 7. Versioning

- Hash the canonical schema and the description separately; use semantic versions for the behavioural contract.
- An additive optional field may be backward compatible internally but not under a provider's strict schema: test it.
- Renaming a field, changing units, changing side effects, broadening authority or changing error semantics needs a new major version and an approval review.
- Keep old and new versions during migration only if both remain policy-safe; remove deprecated tools from model exposure promptly.

## 8. Provider-neutral descriptor

Keep one internal descriptor per tool and compile it into each provider's schema. Fields: globally unique tool ID, display name, provider-safe alias, semantic version, owner, description, negative-use guidance, input schema, output schema, examples, side-effect class, idempotency behaviour, required scopes, data classification, timeout, retry policy, concurrency limit, cost estimate, freshness, approval policy, deprecation state. Reject deployment if a provider compiler silently drops a constraint that application validation does not reproduce. Pin model snapshots, SDK versions, API versions and schema tests; never infer one provider's behaviour from another's.

## 9. Provider notes (stated as of September 2026; confirm against the provider's current documentation before relying on them)

- OpenAI: a function has type, name, description, parameters and strict. Set strict explicitly to true (Responses and Chat Completions differ in defaults). Strict mode requires every object to set additionalProperties to false and every property to appear in required; an optional value is a union with null; only a subset of JSON Schema is accepted, so compile and test. Return each function_call_output under the same call_id. Disable parallel tool calls for ordered dependencies, approval-gated actions, non-idempotent operations, or models with known parallel-call caveats. Programmatic tool calling suits only low-risk, machine-checkable intermediate calls that do not each need approval.
- Anthropic: tools carry name, description and input_schema; names match the pattern of 1 to 64 letters, digits, underscores or hyphens. Descriptions should say what the tool does, when to use and not use it, behaviour, limitations and parameter meaning; optional input examples are supported. Return each tool_result under its tool_use id. disable_parallel_tool_use limits automatic choice to at most one tool. Programmatic calling rejects recursive reference cycles for eligible custom tools.
- Google Gemini: declarations use a subset of OpenAPI schema (type, nullable, required, format, description, properties, items, enum, anyOf, $ref, $defs); do not assume other attributes work. Modes: AUTO, VALIDATED (natural language or a schema-adherent call), ANY (one or more calls required), NONE (no calls); an allowlist narrows eligible functions. Parallel calls are for independent operations, compositional calls for dependent ones.
- Tool choice in general: automatic for ordinary behaviour, forced or allowlisted for deterministic workflow stages, no-tool mode when external access is not allowed.
