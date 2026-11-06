---
created: "2026-11-04T19:44:53Z"
updated: "2026-11-04T19:44:53Z"
---

# Containment, recovery patterns and repair routing

## Stage owners (where a routed repair goes)

Route the actual repair to the stage that owns the failed operation, and describe the change in that stage's terms.

| Stage owner | Owns |
|---|---|
| Processing pipeline | Ingestion, parsing, normalization, retrieval, reranking, assembly, citation binding, per-call delivery |
| Lifecycle | Checkpoints, replay, branching, retention, invalidation, recovery, erasure propagation |
| Hierarchy | Scope, inheritance, authority, precedence, cross-level resolution |
| State machine | Legal transitions, guards, effects, retries, compensation, terminal states |
| Streaming | Framing, ordering, replay, backpressure, cancellation, partial-output safety |
| Durable-memory write | Memory eligibility, provenance, conflict resolution, idempotent writes, projections, write-time poisoning defense |
| Selection | Read-time eligibility, relevance, sufficiency, diversity, trust tiers, tool selection, ordering, token allocation |
| Compression | General compression, protected atoms, faithfulness, rehydration, cumulative degradation |
| Semantic compression | Proposition-level compression, semantic deduplication, clustering, graph representations, semantic verification |
| Sliding window | Resident-set movement, atomic eviction, boundary validity, anchors, overflow |
| Memory blocks | Prompt-resident persistent blocks, controlled edits, capacity, drift, rollback |
| Prompt and KV caches | Provider prompt caches, self-hosted KV caches, prefix identity, eviction, routing, cache isolation |
| Isolation | Tenant, task, agent, trust, capability, cache, execution and failure boundaries, adversarial quarantine |
| Long-context model architecture | Effective-context evaluation, bounded-memory serving |

## Containment

Contain before recovery: stop publication or actions; open the circuit for the implicated source, tool or agent; freeze suspect writes; quarantine records and their descendants; disable serving aliases; preserve evidence; revoke capability if adversarial. State which of these are done, proposed or not needed.

## Recovery patterns (choose the least destructive valid one)

| Pattern | Use when | Do not |
|---|---|---|
| Context reset | Working context is confused, distracted or path-dependent but durable sources are trustworthy. Reassemble from authoritative sources and the current task contract. | Copy the old transcript wholesale; reset while persistent poisoning remains in any reusable derivative (a clean prompt over a poisoned index is not a reset). |
| Selective purge with derivative invalidation | Specific records are false, malicious, unauthorized or illegally retained. Tombstone or quarantine the canonical records, traverse lineage, invalidate indexes, summaries, graph assertions, blocks, checkpoints, caches and serving aliases, then verify negative retrieval. | Hard-delete first and investigate later; preserve the minimum authorized evidence. |
| Rollback to checkpoint | State was known-good at a specific version and later mutations are attributable. Restore, reconcile external side effects, pin compatible code and policy versions. | Assume rollback reverses emails, payments, publications or other external effects; those need reconciliation or compensation. |
| Clean session restart with verified handoff | The trajectory is path-dependent, context is bloated, or provider continuation state cannot be trusted. Build a new handoff from immutable evidence, active objective, completed work, unresolved questions, side effects and explicit exclusions; validate it before the new run. | Summarize the suspect transcript with the same uncontrolled process and call it clean. |
| Quarantine pending review | Truth, authorization or attack status is unresolved. Quarantined content stays visible to authorized reviewers but is ineligible for retrieval, memory rendering, compression input and tool decisions. | Leave quarantine as permanent storage without owners, age alerts, retention and disposition. |
| Safe fallback and abstention | A smaller approved context, read-only mode, deterministic answer, cached authoritative fact or human escalation, only when policy defines which guarantee is relaxed. | Return an older or simpler answer without labelling its freshness and limitation. |

Verify recovery by replaying the triggering case and neighbouring cases, confirming derivative invalidation, and comparing exact context fingerprints. Reopen gradually through a canary or half-open probe, never only because time passed.

## Retry

Retry only when the failure is plausibly transient or the strategy changes: narrow retrieval, switch from semantic to lexical search, retrieve an authoritative source, remove suspect context, rebuild from immutable records, choose an evaluated model, or ask for clarification. Identical retries amplify cost and can strengthen a poisoned trajectory.

## Adversarial response (prompt injection, malicious memory, descriptor tampering, cross-tenant content, capability misuse)

1. Stop affected actions and durable writes.
2. Open the circuit for the implicated source, namespace, tool or agent.
3. Quarantine the source and its descendants, preserving hashes and lineage.
4. Revoke task or derivative credentials when exposure is plausible.
5. Trace every downstream read, write, summary, block, index, cache, agent handoff and external effect.
6. Determine whether confidentiality, integrity or availability was affected.
7. Notify the security owner under the established severity policy.
8. Rebuild from trusted sources rather than editing hostile content in place.
9. Add the attack and nearby variants to adversarial regression tests.
10. Reopen only after isolation controls and stage-local fixes pass negative tests.

Never ask the suspect context how to remediate itself. A natural-language apology from the model is not evidence of containment.

## Actions that need the owner's authorization

An agent may inspect traces, classify incidents, run approved offline evaluations, create local fixtures, propose quarantines and prepare rollback plans. It needs authorization before changing production traffic, deleting or restoring production records, revoking credentials, expanding logging of sensitive content, opening or closing a security incident, weakening a gate, or making an irreversible external change. Present such steps as proposals for the owner.

## Follow-up questions for the write-up

- What was the earliest contract violation, and why did the owning stage create it?
- Why did each downstream breaker fail to contain it, and why was it silent?
- What was the propagation and blast radius?
- Was retry behaviour helpful or amplifying? Did an abstention policy exist and fire?
- Which minimized fixture now prevents recurrence?
