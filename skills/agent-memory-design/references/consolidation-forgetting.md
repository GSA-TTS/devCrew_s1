---
created: "2026-11-04T23:58:31Z"
updated: "2026-11-04T23:58:31Z"
---

# Consolidation, retention classes and forgetting

Use this file to fill the Retention class column and the Consolidation and Forgetting and deletion parts.

## Is consolidation appropriate

Consolidate when raw experience grows faster than it can be retrieved economically, future tasks repeatedly need stable abstractions, evidence spans sessions, or repeated query-time synthesis costs more than a validated reusable artifact. It pays back only when expected reuse times the avoided retrieval, context and reasoning cost exceeds generation, validation, review, storage, monitoring, correction and retirement cost, allowing for the chance the artifact is wrong.

Do not consolidate merely because storage is large. Keep raw or lightly indexed evidence when exact wording, chronology, audit, dispute resolution, rare incidents or attribution matter. Avoid it when the domain changes faster than the refresh target, reuse is unlikely, evidence cannot be validated, deletion cannot reach derivatives, or the artifact would encode one user's data into a shared model.

## Products and what each must prove

- Summary: for overview or bounded retrieval when the important questions can be declared in advance. Keeps source pointers, time span, uncertainty, contradictions, protected facts (names, identifiers, quantities, deadlines, quotations, negations) and omitted categories. Rolling summaries only while the raw transcript remains; regenerate from sources periodically; never summarize a summary after the sources are gone.
- Episode-to-claim extraction: when a proposition can be stated atomically with an entity, a validity interval and evidence. One event shows the event happened, not a general rule. Consequential claims need an authoritative source or independent corroboration; block promotion on unresolved contradiction.
- Reflection: proposes higher-level relationships or hypotheses for planning. Label it inferred, cite supporting memory IDs per sentence, search for counterexamples, give it an expiry, cap its depth, and do not let it cite itself. Do not use unreviewed reflection for medical, legal, financial, employment or access-control decisions.
- Procedure extraction: when tasks recur, outcomes are observable and successes and failures reveal stable steps. The candidate states preconditions, inputs, ordered actions, tool permissions, validators, failure branches, stop conditions, rollback and source trajectories; it is tested in a sandbox on unseen tasks before shadow and canary, and kept in a versioned registry.
- Profile and preference consolidation: for explicit, durable preferences within consent and purpose; keep direct statements apart from inferred behaviour, scope them, make them inspectable and correctable, and expire them when context changes. Do not infer sensitive attributes from behaviour or merge identities or tenants.
- Deduplication and merging: exact deduplication keeps reference counts; semantic merging only when identity, scope, time, authority and polarity match, with a reversible merge record. Do not merge rare failures into a dominant success pattern.
- Index and embedding rebuild: a derived-view rebuild, not promotion. Build a new generation, compare in shadow, switch an alias atomically, keep the old generation for rollback; never mix embedding model versions in one index.
- Parametric promotion: only for stable, high-reuse behaviour that external memory cannot serve within measured latency, offline or deployment limits. Train an isolated adapter, compare it with retrieval of the same artifact, keep the external artifact and training lineage as canonical.

Never overwrite source episodes with the abstraction.

## Promotion states and gates

Every candidate moves through candidate (machine-proposed, not generally retrievable), provisional (automated gates passed, limited exposure), approved (required authority accepted), published (immutable version active), deprecated, invalidated, deleted; later states never erase history. Set gates per artifact and consequence class. Repetition is not corroboration: ten copies of one generated answer have one independent source. Require human approval for consequential personal profiles, safety procedures, permissions, regulated facts, high-blast-radius skills and any promotion whose validator cannot see real outcomes.

## Triggers

- Event-driven: a closed episode, verified outcome, source correction, deletion, policy change, schema migration or embedding release; published from the canonical transaction and not blocking the user-facing write.
- Periodic: backlogs, contradiction scans, profile refresh; cadence from the maximum tolerable staleness.
- Budget pressure: start above a high watermark and stop below a lower one; pressure never bypasses evidence gates.
- Idle time: when load is low and results can wait; pause on latency or error-budget breach.

## Retention classes (assign one per memory at write time)

1. Protected evidence: legal hold, records a law or regulator requires, deletion attestations, safety incident evidence, financial or access-control audit records, minimal anti-reintroduction tombstones. Never forgotten while its authority is active, but isolated from personalization and action; needs a basis, owner, start, review date, release authority and scope.
2. Mandatory deletion: valid erasure request without exception, expired consent-dependent data, ended purpose, prohibited collection, expired secrets, confirmed malicious memory. Forgotten on an event or schedule within a stated deadline, derivatives and recipients included.
3. Default decay or revalidation: inferred preferences, environmental observations, transient entities, unverified claims, low-consequence episodes. Loses authority unless confirmed or revalidated.
4. Justified operational retention with a fixed review period: stable preferences, approved procedures, current contractual state.
5. Archival retention: serving prohibited, preservation justified.

Apply purpose limitation before duration: a new use does not silently extend the original purpose. Session scratch state disappears at task end unless promoted; unverified observations decay quickly; stable confirmed preferences get a longer review interval. Forever only when a specific law, archive or enduring product purpose justifies it and review stays possible.

## Forgetting mechanisms, from reversible to final

- Deprioritization and confidence decay: lower rank or trust; reversible; no erasure. For uncertain, refreshable observations. Not for erasure requests, confirmed poison or compromised credentials.
- Mark unverified, disputed or stale: blocks authoritative use, keeps history.
- Archive to cold storage: out of routine serving; archived personal data is still personal data and is not deletion.
- Redaction: removes fields or spans; redact all derivatives or regenerate them.
- Lossy summarization: not a deletion guarantee.
- Soft delete with tombstone: immediately non-serving; quarantine and anti-resurrection marker; not enough when hard deletion is required.
- Hard delete with cascade: removes the payload and derived claims, chunks, vectors, summaries, graph edges, caches, prompts, traces, replicas and vendor copies. For approved erasure, expired data, confirmed poison and compromised memory.
- Crypto-shredding: destroy per-subject or per-tenant keys when selective erasure across immutable storage is a designed requirement; fails if any key copy or plaintext copy survives.
- Parametric unlearning or retraining: only after showing the model itself holds the target; deleting an external record does not remove its influence from weights. Prefer retraining from a dataset without the data where feasible.

## Choosing decay, TTL and staleness

- Fixed TTL when validity has a known boundary (one-time codes, reservations, temporary grants, transient tool results, contractual retention).
- Decay when utility falls smoothly: store initial authority, rate or half-life, last confirmation and reinforcement rules. Retrieval alone does not refresh authority: keep was retrieved apart from was confirmed by an authoritative outcome.
- Access-based retention only for caches and replaceable copies, not as the only policy for personal data or institutional knowledge.
- Staleness budget per relation and memory type: maximum age for direct use, age that requires revalidation, the source allowed to revalidate, and the action when revalidation fails. A stale record may stay as history while barred from current-state answers.
- Eviction: policy first (expired consent, completed purpose, invalid data, erasure requests), then utility (recency, access frequency, verified usefulness, redundancy, storage cost, sensitivity risk, reconstructability). Frequent retrieval never preserves stale or poisoned content indefinitely.

## Deletion and legal states

Keep a deletion graph from source records to chunks, embeddings, summaries, graph nodes and edges, caches, checkpoints, exports, training datasets, adapters and model versions. Deletion starts with a canonical tombstone that makes the memory immediately ineligible, then purges derivatives and permitted backups; search every serving path afterwards. A legal hold suspends scheduled deletion for material in its scope; on release, recompute the original schedule rather than starting a fresh retention period. Response deadlines, exceptions and backup treatment depend on jurisdiction and role, and counsel approves the records schedule; backups may hold deleted data until overwritten only if it is kept beyond use and the person is told.
