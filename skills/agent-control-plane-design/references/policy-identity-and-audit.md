---
created: "2026-11-04T19:39:57Z"
updated: "2026-11-04T19:39:57Z"
---

# Policy, approvals, identity, delegation, failure behaviour and audit

## Authorization model and engine choice

- Compose models by question: coarse RBAC for administrative duties and stable job roles; ABAC for tenant, purpose, data class, time, environment, risk, destination and arguments; ReBAC for resource relationships (owns, manages, is assigned to); capability-style grants to constrain delegated operations.
- Deny when required attributes are missing, types mismatch, policy is stale beyond tolerance, or the decision service cannot prove a safe grant.
- Engines: OPA (Rego over structured input, structured decisions, decision logs with decision ID and bundle context) when policies span heterogeneous infrastructure and complex JSON context; Cedar (principal-action-resource-context, schema-aware validation) when application authorization, explicit entity relationships, analyzability and a compact model are primary; Casbin where established ACL, RBAC, ABAC, ReBAC, tenant-domain and deny-override models fit. Choose by testing expressiveness, validation, distribution, latency, explanation, multi-tenancy and fail behaviour, not syntax preference. No network calls or mutable side effects inside policy evaluation; give it bounded, freshness-labelled data.

## Policy input and decision

Input: authenticated user and agent identities, tenant, delegator chain, purpose, environment, region, tool and version, canonical arguments, resource and relationship attributes, destination, input and output data classes, workflow stage, prior decisions, approval artifact, time, budget state, risk.

Decision: effect (allow, deny, require approval, or allow with constraints), decision ID, policy bundle and rule versions, reason codes, obligations, filtered fields, maximum result class and size, credential scope, deadline, quota allocation, approval class, expiry. The model may see a safe reason code, never the confidential policy body or a hint that helps evade it.

Argument-level rules cover recipients, account IDs, record filters, paths, URLs, SQL resource scopes, amounts, date ranges, batch size, export formats and requested permissions. Canonicalize before evaluation; re-evaluate redirects, resolved destinations and downstream resource IDs where ambiguity remains.

Data and egress: bind every input, intermediate, result, artifact and destination to a data class and handling policy (purpose, residency, retention, audience, transformation, egress). An allowed tool does not make every argument, record or destination allowed. Egress is deny by default with exact destination classes, methods, ports, byte limits and redirect checks; prefer brokered access. The model must not turn a denied upload into an email, URL fetch, log message, DNS query or peer-agent handoff.

## Approval loop

Fresh human approval is required for external communications, spending, destructive actions, production changes, identity or permission changes, sensitive-data release, security-control changes, novel code or packages, and degraded fallbacks.

Enter only after deterministic validation and policy return require approval.
1. Create an approval request ID and an operation hash over user, agent, tenant, tool version, canonical arguments, destination, disclosed data, side effects, reversibility, policy version and expiry.
2. Show the approver the exact action, target or audience, material arguments, data released, expected effect, uncertainty, reversibility and expiry.
3. Wait durably without holding a worker or credential open; cancel on user cancellation, expiry, tool disablement or material state change.
4. On denial, record a reason code and exit denied; a materially different safe plan may be proposed, a rephrasing of the same operation may not.
5. On a requested modification, create a new proposal and operation hash; never mutate an approved artifact.
6. On approval, re-run policy and state checks immediately before dispatch.
7. Succeed only when the approval is valid and every bound field still matches.
8. At most one clarification and one revised request per intent; after a second denial or expiry, stop or escalate to a named owner.

Approval is not authorization: it can satisfy a policy precondition but cannot override a prohibition or grant a missing downstream permission.

## Decision, appeal and escalation loop

1. Canonicalize the request; obtain fresh identity context.
2. Evaluate the pinned effective policy and its data.
3. Allowed: issue a short-lived, single-purpose execution grant.
4. Approval required: enter the approval loop.
5. Denied for missing or malformed attributes: one deterministic enrichment or correction, then re-evaluate.
6. Denied by policy: return a stable reason code and safe remediation; the model does not generate alternative arguments just to obtain allow.
7. One appeal, only for a claimed policy-input error, stale relationship data or a documented exception path, routed to an independent authorized reviewer.
8. A granted exception is explicit, narrow, time-bounded, attributable, and a new policy or signed exception artifact; re-evaluate from the start.
9. Security signals, cross-tenant attempts, policy tampering and repeated evasions skip appeal and go to incident response.

## Policy testing and rollout

- Unit-test every rule with allow, deny, missing-attribute, wrong-type, boundary and conflict cases; property-test tenant isolation, deny precedence, monotone scope attenuation, bounded amounts, destination allowlists and approval binding; mutation-test critical policies.
- Roll out signed immutable bundles through development, offline replay, shadow mode, canary enforcement, phased enforcement and general availability. Shadow decisions never grant authority. Compare old and new decisions on the same canonical requests; every broadened allow needs review and an owner.
- Roll back on any critical unauthorized action, cross-tenant allow, material false-deny spike, decision-latency breach or bundle-distribution inconsistency.
- Cap ordinary automated iteration at five rounds; unresolved conflicts go to the policy owner.

## Identity and credentials

- Every deployed agent gets a unique workload identity bound to its lifecycle, environment, tenant scope, owner and attested runtime; separate identities for development, staging and production and for materially different authority classes; issuance stops when an agent or blueprint is disabled. Workload identity (for example SPIFFE IDs with short-lived identity documents) avoids static workload secrets.
- On-behalf-of work preserves user ID, agent ID, actor ID, tenant, purpose, audience, scopes, delegation chain and original authorization time. Never collapse an agent acting for a user into a generic service account, and never use global admin credentials for per-user work.
- Token exchange (OAuth 2.0 Token Exchange, subject and actor tokens) issues short-lived, audience-restricted tokens no broader than the intersection of user authority, agent authority, task purpose, tool requirements and policy. Never forward a broad user token when a narrower exchanged token can be issued.
- Confused-deputy checks: the requester may invoke the agent, the agent may request the operation, the user may access the resource, the destination expects the agent, the purpose is permitted. Bind grants to tool, version, canonical argument hash, destination, tenant, expiry and optionally a nonce or channel. Downstream services enforce authorization themselves rather than trusting a gateway header from arbitrary networks.
- Secrets resolve only in the execution broker or tool worker; configuration holds references; rotate automatically; record a credential-reference hash; revoke on disablement or compromise. Never put secrets in prompts, schemas, tool descriptions, model-visible errors, logs, workflow history or agent memory.
- Tenant appears in every key and authorization decision; per-tenant keys, namespaces, queues, caches, indexes and evidence access where the threat model needs hard isolation; continuous cross-tenant negative tests.

## Multi-agent delegation

- A delegation record holds source and target agent IDs, originating user and tenant, purpose, task subset, allowed tools, data classes, destination constraints, budget, deadline, maximum further depth, policy version and parent delegation ID.
- Monotone attenuation: a child receives less authority, never more; at branch joins use the intersection of inherited grants unless a fresh authorization says otherwise. Re-anchor critical decisions to the original user request and policy, not a paraphrased handoff. Cap delegation depth.
- All agents share the task ID; delegation ID, parent delegation ID and trace links cross process boundaries.

## Failure behaviour, kill switches and caches

- Fail closed for policy, identity, approval, secret and high-risk enforcement outages. A documented fail-open mode is allowed only for low-risk, read-only, non-sensitive operations with a bounded duration, local allowlist, stale limit, no new credentials, explicit alert and later reconciliation; never for writes, cross-tenant access, sensitive egress or administration.
- Set a maximum staleness per artifact; emergency denies, revocations and kill switches propagate faster than ordinary configuration; an enforcement point that cannot prove fresh policy, catalog or revocation state restricts or denies by risk.
- Kill switches by agent, tool, version, server, tenant, destination, model, region and action class, independent of the model and the ordinary deployment pipeline. Activation prevents new dispatch, stops credential issuance or revokes, removes the asset from discovery, cancels safe in-flight work, quarantines uncertain outputs and starts reconciliation. Prefer reversible disablement over deletion; test every switch quarterly and after topology changes.
- Separate caches for catalog, policy bundle, authorization decisions (stable reads only), read results and identity metadata (no reusable bearer secrets), each keyed with tenant, version and revocation context. Never cache writes or approvals; invalidate on role, relationship, policy, tool, schema, lifecycle, destination, tenant, kill-switch or revocation change. A cache hit never bypasses the inline enforcement point.

## Audit and evidence

- Append-only audit events for registration, policy change, decision, approval, execution grant, attempt, result verification, disablement and administrative access. Chain event hashes or use an immutable ledger where non-repudiation is required; sign exports, synchronize time, separate writer and auditor roles, encrypt records, test restoration. An ordinary mutable application log is not non-repudiable.
- One trace per user task, with spans for admission, identity binding, catalog filtering, retrieval, model selection, canonicalization, policy decision, approval, quota reservation, queueing, token exchange, each execution attempt, reconciliation, output validation, delegation, compensation and final verification.
- Correlation IDs: trace ID joins one interactive path; task ID survives restarts, approvals and failover; request ID deduplicates ingress; tool call ID identifies one logical proposal; each retry has its own attempt ID under one execution ID; policy decision ID, approval request ID, quota reservation, execution grant and external operation ID all reference the tool call ID; workflow ID and durable event number order state; delegation ID and parent delegation keep authority lineage; registration ID and reconciliation ID tie runtime versions to management changes. Never reuse IDs across tenants.
- Record identity references, token issuer, audience, scope-set hash and credential-reference hash, never token or secret values. Keep raw sensitive prompts, arguments, results and tool definitions out of ordinary telemetry; keep high-cardinality IDs in traces and logs, not metric labels.
- Compliance: map controls to obligations but do not claim framework compliance (NIST AI RMF, EU AI Act, SOC 2) from architecture alone; SOC 2 evidence shows operating effectiveness of the actual controls, which a tool purchase does not create.
