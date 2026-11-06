---
created: "2026-11-04T23:58:31Z"
updated: "2026-11-04T23:58:31Z"
---

# Memory shared across agents, and distributed storage

Use this file to fill the Multi-agent and distribution part.

## Sharing pattern across agents

- One agent with a governed tool catalog: the default baseline when one model can plan the task, all tools share one trust boundary and context stays bounded. Split only after evaluation shows that access isolation, parallelism, specialist models or context isolation improve cost or risk per successful task.
- Expertise directory (who knows what): when agents differ materially in validated expertise, tools, data access, language, jurisdiction, cost or authority, tasks recur often enough to learn routing, and no one agent can hold all context. Each entry is a versioned hypothesis about a holder's fitness for a class of work, in three layers: declared (what the holder claims), observed (outcomes under named evaluations), effective (the policy-approved capability routing uses). A declaration alone never grants authorization or a high-impact route. Learn reliability only from adjudicated or mechanically verified outcomes, and discount it when the holder's model, prompt, tools or data change.
- Shared blackboard: when producers iteratively post hypotheses, constraints, evidence and partial solutions to a common workspace that every participant benefits from. Give agents typed views, ownership, versioning, access policy and bounded subscriptions, not the whole board.
- Full context sharing: only for two or three homogeneous agents in a short, low-sensitivity deliberation. Not for long tasks, many agents, mixed tenants, privileged tools or untrusted retrieved content.
- Static routing when task classes are few and ownership is contractual; human assignment for novel high-impact work, contested authority or irreversible actions.
- Shared history keeps participant and tenant boundaries; limit each agent to the memories its current purpose needs. A handoff transfers responsibility: name the outgoing and incoming owner, task state, pending obligations, evidence, approvals and side effects, and have the recipient accept or reject.

## Whether to distribute storage

Distribute only for a measured requirement that vertical scaling and one high-availability primary cannot meet: throughput or corpus growth beyond one node after optimization; data residency or multi-region latency; blast-radius isolation between tenants, workloads or sensitivity classes; heterogeneous memory needing specialized stores with measurable gains; region-loss continuity with stated recovery-point and recovery-time objectives.

Do not distribute because agents are distributed, because a vendor offers a cluster, or for hypothetical scale. A strong default is one region, one canonical transactional database, one object store and optional derived search indexes; add read replicas, shards or a second region only after measuring the pressure that needs them.

## Choices once distributed

- Tenancy: a shared store with mandatory tenant keys and row-level enforcement for many small tenants with uniform schemas; schema per tenant for moderate isolation; database or cluster per tenant for contractual isolation, custom residency, noisy or high-value tenants.
- Consistency by memory type: strong for authorization, ownership, deletion state, checkpoints that gate side effects, uniqueness and claim status changes; session consistency where an agent must read its own writes; bounded or eventual for search, recommendations and rebuildable derivatives, with a stale-result marker and a repair objective.
- Starting staleness targets to adjust from evidence: working state and side-effect checkpoints, zero stale reads; episodes, read-your-writes in session, cross-session retrieval up to 5 seconds and search derivatives up to 30 seconds behind; semantic claims, discovery up to 60 seconds stale but zero for a decision using a high-impact claim; vector indexes up to 60 seconds for ordinary personalization and 5 minutes for background discovery; caches up to 30 seconds for low-risk content and zero for authorization, consent, deletion or ownership.
- Conflict-free replicated types only for state with a valid merge (grow-only sets, counters, collaborative text), never to decide which of two contradictory claims is true, whether consent was revoked or who owns a resource.
- A saga when an operation spans services whose steps commit independently with idempotent compensation; a distributed transaction only when atomic visibility is indispensable.
- Caching only for a measured latency or load problem, with tenant-scoped keys and invalidation; never put authorization, erasure status or just-written critical memory behind an asynchronously invalidated cache, and never let a cache become the system of record.
- Keep canonical records and versions in the transactional store; vectors, lexical documents and summaries are regenerable. Choose one general store when scale is modest, joins and atomicity dominate, or the team cannot staff reconciliation.
