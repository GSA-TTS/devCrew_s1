---
created: "2026-11-04T19:39:57Z"
updated: "2026-11-04T19:39:57Z"
---

# Production readiness checklist and setup order

## Setup order

1. Inventory agents, tools, servers, models, data sources, destinations, identities, secrets, side effects, owners, regions, protocols and recovery mechanisms. Stop if ownership or authoritative state is unknown.
2. Define trust domains and tenant boundaries; classify each capability (public read, private read, reversible write, externally visible write, financial or security change, destructive, privileged administration, arbitrary execution).
3. Choose centralized, regional, federated or hierarchical topology; declare availability, consistency, partition and stale-policy behaviour.
4. Establish user and workload identity, delegated authorization, token exchange, secret storage, rotation, revocation and downstream audiences.
5. Define canonical agent and tool descriptors, schemas, lifecycle states, namespace rules, version policy and provenance requirements.
6. Implement policy input schemas and deny-by-default baseline policies; add RBAC administration, ABAC request context, ReBAC resource relationships and attenuated delegation where needed.
7. Put all execution behind enforcement points and block direct tool egress from model workers.
8. Provision durable task state, workflow history, idempotency records, queueing, quotas, budgets, timeouts, retries, breakers and compensation handlers.
9. Configure signed policy and catalog distribution, cache keys, invalidation, rollback, maximum staleness and regional reconciliation.
10. Instrument traces, decision logs, audit integrity, redaction, retention and access controls before sensitive traffic.
11. Build simulators and shadow evaluation for every consequential tool; never test email, deletion, payments, production permissions or public posting against real destinations.
12. Run policy, identity, cross-tenant, routing, failure, overload, partition, stale-config, injection, poisoning, sandbox and kill-switch tests.
13. Start with read-only canary traffic; add reversible writes with approvals; add irreversible authority only after separate evidence and incident drills.
14. Document rollback, failover, credential revocation, queue draining, unknown-outcome reconciliation and communications ownership.

## Readiness questions

Deployment is ready only when every applicable answer is yes. Any no keeps the affected agent, tool, tenant, region or authority class disabled or read-only until the control exists.

- Are management, decision, enforcement, data and evidence planes explicitly separated?
- Is every execution path completely mediated, including MCP, A2A, sandbox and direct API paths?
- Does every agent and tool have an owner, unique identity, immutable version, provenance, lifecycle state and kill switch?
- Does the registry hold schemas, side effects, data classes, scopes, destinations, retry semantics, cost, health and deprecation?
- Are registration, compatibility and rollout loops bounded and tested?
- Does deterministic filtering precede semantic retrieval, with abstention and no-match behaviour?
- Are user, workload, actor, tenant, purpose, audience and delegation preserved through every hop?
- Are credentials short-lived, narrow, rotated, revocable and absent from model context and ordinary logs?
- Does policy evaluate canonical arguments, resource relationships, destination, data class, state, approval and budget?
- Are RBAC, ABAC, ReBAC and delegation attenuation used where appropriate?
- Are approvals specific, informed, time-bounded, operation-bound and revalidated?
- Are policy tests, mutation tests, differential replay, shadow mode, canary and rollback in place?
- Are desired and actual registry, policy, identity, gateway, quota and disablement states continuously reconciled?
- Are side effects idempotent, reconcilable, compensable where meaningful and durably recorded?
- Are retries, deadlines, circuit breakers, bulkheads, queues, quotas and cost caps bounded at one owning layer?
- Are multi-region consistency, configuration staleness, partition behaviour, disaster recovery and blast radius documented and tested?
- Do caches include tenant, identity, policy, relationship, version, freshness and revocation context?
- Can kill switches stop discovery, dispatch, credential issuance and unsafe in-flight work within the target time?
- Can traces correlate task, agent, delegation, selection, policy, approval, quota, workflow, call, attempt, external operation and verification?
- Are audit events append-only, integrity-checked, access-controlled, restorable and retention-governed?
- Do evaluations cover policy correctness, false allows and denies, cross-tenancy, prompt injection, tool poisoning, delegation drift, failure injection, overload, stale state, audit tampering and kill switches?
- Are consequential tools simulated for evaluation and introduced through read-only, reversible, then higher-authority stages?
- Are operator ownership, on-call, incident response, evidence export, credential revocation, rollback and user communication procedures tested?
