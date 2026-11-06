---
created: "2026-11-04T19:39:57Z"
updated: "2026-11-04T19:39:57Z"
---

# Components, topology, registry, discovery and admission

## Five planes and seven contracts

Planes:
- Management: owners register agents, tools, policies, identities, quotas, regions, approvals, lifecycle states and rollout intent.
- Decision: resolves eligible capabilities, evaluates policy, decides approval and budget requirements, issues a short-lived execution grant.
- Enforcement: gateways, sidecars, sandbox brokers and downstream services validate the grant and block bypass.
- Data: tool workers, APIs, databases, models, browsers and peer agents do the work and return bounded results.
- Evidence: traces, decision logs, audit records, evaluations, attestations and reconciliations prove what happened.

Contracts every invocation crosses:
1. Identity: user, tenant, agent workload, delegator, environment and downstream audience authenticated and bound.
2. Discovery: only eligible, approved, healthy, compatible capabilities disclosed or selected.
3. Input: arguments syntactically valid, canonical, semantically valid, tenant-scoped, free of model-controlled identity fields.
4. Policy: a deterministic decision binds principal, purpose, tool version, arguments, data, destination, state, policy version and required approval.
5. Execution: a named executor gets bounded authority, deadline, idempotency key, resources and egress.
6. Result: output typed, provenance-bearing, size-bounded, classified and safe to expose.
7. Evidence: every proposal, decision, approval, attempt, state transition and verification correlated and replayable without unneeded secrets.

## Required components

- Control-plane API and configuration store: management writes separate from runtime reads; immutable versions, optimistic concurrency, signed manifests, encryption, backups, change history.
- Registry and discovery index: canonical descriptors and agent records; search indexes built only from approved versions.
- Policy decision point: pinned engine with schemas, tests, signed bundles, decision explanations, bounded external data.
- Policy enforcement points: at ingress, tool gateway, sandbox broker, peer-agent gateway and downstream service when possible.
- Identity and token broker: authenticates user and workload, constrained token exchange, short-lived execution grants, revocation.
- Secret manager: credentials resolved inside the executor or gateway, never in model context.
- Gateway or execution broker: canonicalizes requests, validates grants, applies deadlines and limits, injects credentials, dispatches, normalizes outputs, reconciles operations.
- Durable state and workflow engine: task, call, decision, approval, retry, compensation and external-operation state.
- Queue and scheduler: backpressure, priority, fairness, cancellation, delay, dead-letter quarantine.
- Quota and budget service: calls, tokens, bytes, concurrency, side effects and money per user, tenant, agent, tool, destination and global pool.
- Observability and audit services: OpenTelemetry signals, append-only decision events, security logs, audit exports, privacy-controlled evidence.
- Evaluation and replay harness: tests policies, schemas, routing, security, failures, rollback and historical decisions with simulators.
- Administrative console and API: ownership, approvals, staged rollout, disablement, credential revocation, policy simulation, drift review, evidence access, incident operations.
- Sandbox and egress proxy: whenever arbitrary execution or untrusted servers exist.

Conditional: a durable workflow engine and message queue are optional only for a tiny synchronous read-only deployment; they are required for long-running work, approvals, retries that must survive restarts, side effects, sagas, asynchronous tools, high volume, multi-region recovery or backpressure. A sandbox service is mandatory for generated code, shell execution, browser automation over untrusted content, or untrusted local MCP servers.

## Gateway roles

- Tool or AI gateway: calls cross a network boundary and need common authentication, policy enforcement, validation, rate limiting, egress restriction, protocol translation, tracing or revocation.
- LLM proxy: model-provider routing and spend controls.
- MCP gateway: server discovery, authorization, namespacing, definition pinning and tool mediation.
- Sidecar or node-local proxy: local enforcement where latency matters.
- One proxy should not be assumed to perform every role safely.
- Inline enforcement is required for authorization, secrets, quotas, egress and irreversible side effects. Out-of-band analysis suits anomaly detection, quality scoring, trend analysis and retrospective audit; it may alert or trigger a later kill switch but cannot prevent a completed action.
- MCP servers and A2A peer agents go behind the same internal registry, policy, identity, definition-hash, sandbox and tracing controls. A public MCP registry listing is metadata, not a trust or authorization decision; a signed A2A Agent Card proves identity and integrity, not fitness or authorization. Register peer agents as principals and capabilities.
- When comparing products, evaluate exact version, maturity, policy depth, identity semantics, fail behaviour, exportability and bypass resistance; product category labels are not interchangeable, and a cloud offering is a composable part, not proof the full control plane exists.

## Topology

- Centralized: small or medium deployment, one trust domain, low decision latency, simple operations, strong consistency. Risk: correlated outage and large blast radius.
- Regional or federated: data residency, latency, scale or organizational autonomy needs local decisions. Keep a global source of signed desired state with local decision and enforcement points; define conflict precedence, maximum configuration staleness, emergency deny propagation and partition behaviour. A regional cache must not create authority absent from global policy.
- Hierarchical: large organizations. A global baseline sets non-overridable security constraints; domain planes narrow authority and add requirements; tenant planes may narrow further. Child policy must not weaken parent denies; compile the effective policy and keep its lineage.
- In every topology, keep model inference, bulky tool results and long-running execution out of the control-plane process; keep the decision path small, deterministic, horizontally scalable and independently deployable.

## Canonical descriptors

Tool version: globally unique ID, namespace, provider-safe aliases, owner, human sponsor, source repository, provenance attestation, semantic version, immutable schema hash, description hash, input and output schemas, examples, negative-use guidance, protocol and version, endpoint identity, side-effect and reversibility class, required scopes, data classes, destinations, region constraints, timeout, retry semantics, idempotency behaviour, concurrency class, estimated cost, approval class, health, lifecycle state, deprecation deadline.

Agent version: identity blueprint, owner, runtime, model and snapshot, orchestrator version, allowed task classes, tool namespaces, data classes, delegation policy, maximum depth, budget profile, policy attachments, region, evaluation evidence, lifecycle state.

Lifecycle states: draft, validating, approved, canary, active, degraded, quarantined, deprecated, disabled, retired. Only approved, canary or active assets are exposed. A health check does not override lifecycle or policy.

Versioning: semantic versions for behavioural contracts. Additive optional fields can still break strict provider schemas and need compatibility tests. New side effects, broader destinations, changed units, changed identity semantics, renamed required fields or changed error meanings need a major version. Run old and new versions together only during a bounded migration and only if both stay safe. Publish by atomic pointer or signed manifest, never in-place mutation; keep the prior version for rollback; model workers never read unapproved drafts.

Capability classes (for trust domains and approval): public read, private read, reversible write, externally visible write, financial or security change, destructive, privileged administration, arbitrary execution.

## Registration and validation loop

Enter when a tool, agent, schema, endpoint, identity, policy attachment or material descriptor changes.
1. Accept a signed registration from an authenticated owner; allocate a registration ID and an immutable candidate version.
2. Validate descriptor schema, ownership, namespace, uniqueness, endpoint identity, provenance, required metadata and tenant scope.
3. Compile input and output contracts for every supported provider and protocol; reject silently dropped constraints.
4. Run positive, negative, boundary, unknown-field, malformed, compatibility, authorization, timeout, cancellation and output-normalization tests against a simulator or isolated staging endpoint.
5. Verify downstream scopes, egress destinations, secret references, idempotency, health probes, quotas, approval class and rollback action.
6. Evaluate policy in shadow mode over representative recorded requests against the approved baseline.
7. A deterministic defect repairable without changing authority returns named validation errors and allows a new immutable candidate.
8. Exit approved only after ownership, security, compatibility, policy, observability, evaluation and rollback gates pass.
9. Exit to human security or data review for new authority, a new data class, an external destination, arbitrary execution, unsigned provenance or a policy exception.
10. Exit rejected after three automated validation rounds or one repeated candidate hash. Never auto-edit policy or broaden scopes to make registration pass.

## Discovery and routing

- Pass the full catalog to the model only when it is small, stable, distinct and cheap enough not to harm context; otherwise use progressive disclosure.
- Use retrieval when the eligible catalog is large, descriptions are costly or namespaces overlap. Use deterministic routing or explicit workflow state when the application already knows the operation, the catalog is tiny, or a missed capability would be safety-critical.
- Retrieval procedure:
  1. Filter by tenant, principal, agent, purpose, environment, region, protocol, lifecycle, health, data class, side-effect ceiling, scope, budget and policy.
  2. Build the query from the task goal and workflow state, without secrets.
  3. Retrieve a diversified top-k set, normally starting at five to ten candidates.
  4. Rerank by semantic relevance, negative-use rules, compatibility, observed verified success, latency, cost, freshness and health. Policy is a constraint, never a score.
  5. Expose exact immutable versions and enough metadata for safe selection.
  6. Permit abstention and clarification.
  7. Broaden once with alternate wording only if no eligible candidate covers the task.
  8. Exit with a candidate set, a clarification, or capability_unavailable after at most two retrieval rounds.
- Never route on highest similarity alone: require a minimum calibrated score or margin, deterministic capability coverage and policy eligibility. Popularity, prior usage or reinforcement feedback never promote an unsafe or unhealthy tool.

Dynamic exposure: compute the exposed set per request from trusted session state; the model never submits its own role, tenant, clearance or approval status; record the exact ordered exposed set and its hash. Do not remove a tool version from an approved durable workflow in a safe in-flight stage unless the version is compromised: for normal deprecation, pin the workflow and block new starts; for emergency disablement, stop dispatch, revoke credentials, cancel safe work, quarantine results and reconcile unknown outcomes.

## Admission control

- Admit before expensive retrieval or model work when possible, and again before dispatch.
- Check: authentication, tenant status, risk, data class, region, tool and agent lifecycle, budgets, concurrency, queue depth, dependency health, policy availability, approval requirements and emergency controls.
- Shed load before overload creates cascading latency; prefer tenant-fair queues and priority classes; no single agent, tool or tenant may consume all decision capacity.
- Quotas and budgets are hierarchical (global, region, tenant, user, agent, tool, destination, risk class) over rate, concurrency, queue, token, byte, tool-call, side-effect and money. Reserve budget atomically before dispatch and release unused capacity. Separate read, write, approval, evaluation and administrative pools.
- Queues: never queue an expired request, a revoked capability, or an approval whose operation hash changed; re-evaluate policy at dequeue if identity, policy, configuration or resource state may have changed.
