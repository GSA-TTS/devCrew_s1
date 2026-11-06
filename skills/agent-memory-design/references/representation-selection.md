---
created: "2026-11-04T23:57:22Z"
updated: "2026-11-04T23:57:22Z"
---

# Choosing function, representation and tier for each memory

Use this file to fill the Function, Representation, Deciding criterion and Tier columns of the inventory table. Classify every memory by function first, then choose the least powerful representation that answers its questions.

## What to establish for each candidate before choosing

For each candidate, establish (and cite the deciding ones in the Deciding criterion column): function (working state, episode, semantic claim, procedure); expected volatility; who uses it; sensitivity; provenance needs; deletion needs; how often it is reused; whether exact wording or values matter; harm if wrong. If these are unknown, do not persist the memory.

## Function

- Working memory: bounded state for the current task (goal, plan, open variables, recent tool results, checkpoint). Shortest lifetime. It does not become durable because it appeared in a prompt; the end-of-task action is discard, and promotion needs a separate write decision with evidence, scope, sensitivity and retention class.
- Episodic memory: what happened (actor, action, object, result, time, environment, source trace), in order, with observation kept apart from interpretation. An episode can support a statement about one event, not a general rule or preference.
- Semantic memory: claims about entities and relationships independent of one episode. Each claim needs source lineage, valid time, transaction time, confidence and supersession state. Promote an episode-derived claim only when its subject is resolved, the relation is allowed, the time scope is explicit, evidence suffices for the risk and counterevidence was searched; a behavioural preference normally needs repeated, diverse support or direct confirmation.
- Procedural memory: how to do a task (policies, workflows, tool sequences, validators, recovery steps). Store as versioned, reviewable artifacts with preconditions, ordered actions, authorization, validators and failure branches; an external runbook stays the authoritative form even if a model later internalizes it.

## Representation: choose when, avoid when

- Bounded context or checkpoint. Choose for transient task state, complete material that fits comfortably, order-dependent reading, low reuse. Avoid as durable memory: an ever-growing transcript is not memory, and advertised context length is not usable capacity.
- Typed record (rows or validated documents with typed fields). Choose when consumers need exact filters, joins, aggregates, constraints, deterministic updates, field-level access control or point-in-time answers: verified profile attributes, preferences with exceptions, task constraints, workflow status, approved decisions, eligibility facts. Avoid when typing is premature: ambiguous narratives, disputed chronology, nuanced motivations, fast-changing concepts. Keep the raw text or episode with provenance and extract a narrow record only when a decision needs it. Keep unknown distinct from not applicable, withheld or not asked; a default is not evidence.
- Free-text note with a structured envelope. Choose for nuanced notes, rationales, meeting passages, evolving vocabulary, unresolved claims, open-ended future questions, or when a human must inspect and edit what is remembered. One note holds one subject, decision, preference or conflict, names its referents, time and scope, and keeps qualifiers. Keep verbatim text when exact wording, attribution, a promise, a requirement, a correction or a disputed claim matters.
- Episode (append-only event log with episode views). Choose when sequence, action, observation, tool result and outcome must stay reconstructable for audit, replay, causality or learning from cases. An episode is the smallest replayable unit with a goal or state change, its preconditions, the agent's choices and an evaluable outcome; a task is a useful default boundary, with sub-episodes for long tasks. Do not write every raw event unless audit, safety or replay requires it.
- Semantic graph. Choose when durable identity, relation semantics, variable-length traversal, cross-source integration or explainable multi-hop retrieval is a measured requirement. A lightweight entity tag on text is enough until competency questions repeatedly need traversal. Use a formal ontology only when independent systems must share machine-checkable meanings and owners can define them; a triple store when global identifiers, open-world integration and standards-based exchange dominate; a labelled property graph when traversal ergonomics dominate. A graph is the wrong answer when passage retrieval suffices, when the need is transactions, permissions and aggregates (use relational storage), or when one bounded corpus fits in context.
- Temporal graph or bitemporal records. Use valid time (when a claim was true in the world) and transaction time (when the system knew it) for any claim whose history matters. A temporal graph is justified when changing relationships and point-in-time traversal are central; otherwise implement the same semantics in bitemporal relational records. Timestamped documents in a vector store fit only when passages are the product and coarse time filtering is tolerable; they cannot answer what was believed when.
- Document retrieval over a corpus. Choose for large, current, private, attributable, tenant-scoped or deletable collections and when answers must cite evidence. Start with canonical documents, metadata filters and lexical or exact lookup; add embeddings when paraphrase recall needs them, and a vector database only when scale, filtered search, concurrency or availability exceed an in-process or relational index. A vector is an index key, not the memory: keep the source.
- Parametric (fine-tuning, adapters, direct edits). Choose fine-tuning or adapters only for stable behaviour and domain patterns that have already worked as an external, reviewable artifact; direct weight editing only for a small, bounded set of well-specified changes on an open-weight model with every edit evaluated and reversible. Do not place volatile facts, personal profiles, disputed claims, credentials, prices, inventories or deletion-sensitive knowledge in weights.
- Compressed latent memory, learned memory modules and soft prompts trade away evidence access, citation and selective deletion; treat them as research or model-architecture choices, not a replacement for a canonical store.

## Hybrid rules

- A hybrid fits most durable agents: working state in checkpoints, episodes in an append-only store, current facts in a temporal semantic store, procedures in versioned runbooks, retrieval for evidence, parameters for stable capability.
- Do not add stores to match a diagram; avoid hybrid complexity when one bounded context or one relational store meets the measured need. Every added index brings synchronization, access-control, deletion and observability work.
- Declare one canonical source per field; indexes, embeddings, summaries and graph projections are derived and rebuildable. Do not mix records of different tenants or trust classes in one retrieval pool, and do not let a summary be the only copy of exact evidence.
- Graph plus vectors: the vector index finds semantically related text and candidate entities; the graph expands from those entities along relationships and provenance; both feed the answer.

## Tier (serving placement)

Function and tier are independent; a memory can move between tiers over its life.

- Core: always resident in the model input. Only controlling instructions, tool contracts, policy, the current request, a small identity block, pinned facts that are verified and currently applicable, and pointers to active goals. Admit only items that are verified, compact, broadly useful, safe to repeat and costly to miss. Every pin needs an owner, reason, expiry and review date; model self-pinning does not bypass these.
- Working set: current task state, unresolved obligations, recent decisions, compact tool results, the resume checkpoint. Lifetime of one task or workflow. Checkpoint before compaction.
- Warm: canonical records plus lexical and vector indexes and scoped caches within the interactive latency budget. Warm does not mean trustworthy or eligible.
- Cold: old transcripts, large artifacts, source documents, retired checkpoints, kept for audit, legal, replay or rare recovery, with a searchable warm catalog. Use it only when delayed answers or background fetch are acceptable.
- Promotion makes a copy faster or more influential; it never changes truth or authority. Demote with hysteresis: a stronger score to enter a tier than to stay, a minimum residence time and a cool-down.
