---
created: "2026-11-04T23:58:31Z"
updated: "2026-11-04T23:58:31Z"
---

# Write path and read path

Use this file to fill the Write decided by column and the Write path and Read path parts.

## Who decides a write

- Deterministic (the default): checkpoint persistence, append-only audit events, tool outcomes, confirmed user corrections, TTL, tombstones, index publication, cache invalidation, mandatory retrieval before regulated decisions. Do not deterministically infer preferences or general claims from ambiguous dialogue; require confirmation or keep the episode.
- Model-proposed: when remembering is part of the agent's judgment (the user says remember this, the agent must choose a namespace, or the query is too contextual for fixed routing). Expose narrow operations (propose, search, correct, request forgetting); the memory service, not the model, enforces schema, authorization, version preconditions, retention and deletion. A tool call is an intent, not a commit. Not for compliance records, payments, security policy, credentials, access grants, authoritative tool state or every turn.
- User-requested: an explicit remember, correct or forget request; commit it synchronously.
- The practical default is hybrid: code captures sources and applies hard policy, a model proposes candidates, validators normalize, authorize, deduplicate and commit, workers build derivatives.

## Write requirements

Do not write every turn. A write needs an allowed purpose, authorized subject, source class, memory type, sensitivity classification, retention class and evidence pointer. For high-impact facts or procedures, require independent verification or human approval.

Agent-written memory is a proposal: record that the agent authored it and whether it is an inference or summary, list its sources, and do not count later retrieval of the note as confirmation. Raise its authority only with a source outside its own descendant chain. Keep organization policy and security rules read-only, separate from writable learned notes, and let humans inspect, correct, disable or delete learned notes.

## Write stages

1. Capture the source (turn, episode, confirmed statement, tool output, workflow transition, cross-agent message) with an immutable identifier and content hash, without granting it authority. Keep quoted source, observation, model inference and approved procedure apart.
2. Generate candidates: synchronously only when the next turn needs the memory, otherwise queue. Constrain extraction to allowed memory types with an explicit none result; require supporting span, subject, value, negation, time expression and confidence method.
3. Normalize identities, timestamps, units and aliases while keeping the original; never erase negation, uncertainty, speaker or time scope.
4. Deduplicate in two passes: exact duplicates by scoped content hash or natural key, then near duplicates classified as duplicate, corroboration, refinement, contradiction or independent occurrence. High similarity alone is not a merge reason; keep occurrence count apart from independent-source support.
5. Admit and authorize: check the principal may write this tenant, subject, namespace, purpose and sensitivity class; detect secrets, personal data, instruction-like content and cross-tenant identifiers; redact, quarantine or reject by policy. Score salience from separate features (explicit intent, task relevance, future utility, novelty, outcome severity, authority, recurrence, volatility, sensitivity risk, cost); salience is neither truth nor permission.
6. Validate schema and conflict against current canonical records: classify duplicate, corroboration, temporal succession, scope difference, correction or unresolved conflict. Use optimistic concurrency (expected parent version, compare-and-set).
7. Commit the canonical version, current-pointer or tombstone change, lineage, audit decision and one outbox event per derivative in one transaction, before acknowledging. Make the write idempotent with a stable operation identifier.
8. Publish derivatives (lexical index, embeddings, graph projection, summaries, cache invalidation) asynchronously from the outbox. A failed embedding does not roll back a valid canonical memory; a failed canonical commit must not leave a searchable derivative.
9. Retry transient failures with bounded backoff; do not retry validation, authorization or conflict failures unchanged; move repeated failures to quarantine, never drop them silently.

Operations: ADD when no equivalent record exists; UPDATE appends a new immutable version of the same identity; DELETE writes an immediately enforced tombstone and schedules purge; NOOP when the candidate is already represented, below the admission threshold or loses a conflict. Prefer append for episodes, observations, corrections and disputed claims; an upsert is only for an explicitly single-valued current view and is implemented as a new version plus a pointer move. Do not overwrite.

Synchronous or asynchronous: commit canonically and synchronously for explicit remember or correction requests, immediate subsequent reads, and authorization or safety changes; run extraction, embeddings, summaries and consolidation asynchronously. Report accepted, committed, indexed or failed; never say remembered when the write is only queued.

## Read path

1. Bind the read contract from authenticated context, not model arguments: tenant, principal, purpose, allowed namespaces and memory types, requested valid time, maximum staleness, consistency mode, token budget, deadline.
2. Keep the original query; resolve relative times, aliases and identifiers; split multi-part questions. Use query rewrites only for known recall gaps, bounded in number.
3. Filter eligibility before ranking: tenant, subject, purpose, consent, region, sensitivity, validity interval, retention, trust, quarantine, tombstone, agent authority. Never search globally and redact afterwards.
4. Generate candidates by route: exact lookup for stable IDs and current pointers; lexical search for names, quotations, codes, rare terms and negation; dense retrieval for paraphrase; structured queries or graph traversal for dates, types, ownership and relations; a recent overlay for committed but not yet indexed records. Prefer one retriever when queries are exact, the corpus small or extra routes add no task success.
5. Fuse rankings (reciprocal rank fusion is a simple baseline); rerank a bounded set only when recall is adequate and precision is the bottleneck; cap near duplicates per source, episode, entity and time window; keep independent corroboration and contradictions.
6. Keep score components separate (relevance, lexical, semantic, temporal fit, freshness, importance, authority, confidence) with penalties for duplication, staleness, low trust and poisoning risk. Recency does not override an authoritative older fact; importance does not rescue an unauthorized record.
7. Return each memory with its identifier, version, span, source, valid and transaction time, trust and sensitivity labels, freshness and conflict links.
8. Surface conflicts together. Abstain when no eligible evidence passes threshold, a required authoritative source is missing, staleness exceeds the bound, a conflict cannot be resolved, or the budget runs out before the minimum evidence.

Temporal reads declare both axes: current (now on both axes), historical world (what is now believed true at time Y), as-of belief (what the system believed at time X), or dual-axis. A path through a temporal graph is valid only if all its edges were valid at the same time.

## Conflict precedence

Separate identity conflicts from change over time and true disagreement first. Then: an authenticated user correction outranks an inferred preference; an authoritative system of record outranks conversation; newer valid-time evidence outranks older only when the fact really varies over time; human-reviewed policy outranks model-generated summaries. Keep both claims, mark the relation as supersedes, contradicts or coexists, and record who resolved it and why. Similarity score alone never resolves a conflict.

A genuine change closes the old valid interval and opens a new one; a correction closes the wrong version's transaction interval and inserts the corrected version, keeping the old one for audit. Do not physically delete a claim because it became false; close it and link its successor.
