---
created: "2026-11-04T19:43:59Z"
updated: "2026-11-04T19:43:59Z"
---

# Failure taxonomy: observed pathology and causal plane

Classify a suspected failure on two axes and keep them apart. The pathology names what is present in the context ("contradiction"); the causal plane explains how it arrived ("a write-stage process failure"). Assign one or more pathologies and exactly one causal plane, and mark security suspicion separately.

## Axis 1: observed pathology

| Pathology | What it is | Distinguishing signals and tests |
|---|---|---|
| Context poisoning | A false claim, hallucination, corrupted state or malicious assertion enters a reusable context surface and is repeatedly treated as evidence. | Persistence and reuse: a one-turn unsupported sentence is a generation error; it becomes poisoning once written to memory, copied into a summary, promoted into a block, indexed, handed to another agent or cached as authoritative. Deliberate poisoning is a security incident, not only a quality defect. |
| Context distraction | Accumulated context makes the model over-focus on supplied history and underuse its own reasoning. | Not the same as overflow: the request can fit the window and still do worse. Signals: repeated plans, copying of prior conclusions, falling novelty, needless reference to old turns, better results under a smaller-context ablation. |
| Context confusion | Superfluous or irrelevant material, often too many overlapping tool definitions, influences the answer or tool decision. | Attributable to particular unnecessary items or schemas (distraction is a global competition caused by accumulated context). Removal ablations tell the two apart. |
| Context clash | Context units cannot all be true or controlling under the same scope, time, identity and authority (documents, memories, instructions, tool descriptions, earlier attempts, other agents' results). | Textual difference is not clash: qualifiers of time or condition may reconcile two statements, and near-identical sentences may clash if they refer to different entity versions. Check identity, valid time, transaction time, jurisdiction, units and authority. |
| Context rot (effective-context degradation) | Measured degradation as input length grows, often well before the advertised maximum and unevenly. | An empirical envelope, not one cause: shows as abstention, hallucination, omission, miscopying or misplaced output. There is no universal safe token limit; compare against a curve specific to the model, version, task and context composition. |
| Positional loss | Needed information is present but its location reduces its use. | Position effects depend on task and structure; diagnose with controlled reorder tests, not folklore. |
| Context insufficiency | A required premise, tool, permission, state fact or source is absent. | Causes: failed retrieval, over-aggressive selection, eviction, stale indexes, isolation that is too strict, a source outage. A fluent answer cannot repair missing evidence; the agent should have abstained. |
| Integrity and protocol failure | Context is malformed, incomplete, mis-scoped, misordered or no longer bound to its source. | Examples: orphaned tool result, invalid continuation item, cross-tenant cache hit, summary with a dangling pointer, context fingerprint that does not match the recorded components. Dangerous cases stay syntactically valid. |
| Goal and trajectory drift | Goal drift: the objective, completion criteria or constraints change implicitly during a long run. Trajectory drift: an early error changes later observations so downstream steps are locally reasonable but globally wrong. | Grows with horizon: history-error accumulation, subplanning errors, forgetting. |
| Silent plausible failure | A plausible output, valid status and normal latency, yet wrong, stale, unsupported or based on unauthorized context. | Ordinary monitors see success. Found by semantic outcome sampling, provenance and groundedness checks, counterfactual ablations, user-correction signals and trace-level stage attribution. |

## Axis 2: causal plane

| Plane | Arises from | Diagnose with | Repair goes to |
|---|---|---|---|
| Content | What the context says: a claim false, stale, contradictory, adversarial, unsupported, misattributed or missing a qualifier. | Claims and their lineage, compared against authoritative sources, time, entity and scope. | The stage that owns the source or its representation: durable-memory writes, selection, compression, semantic compression, resident memory blocks, lifecycle. |
| Structure | How usable material is arranged: excessive length, poor ordering, weak delimiters, duplicate crowding, tool-schema overload, broken role sequences, a critical fact in a weak position. | Token and composition metrics, reorder tests, removal ablations, provider grammar checks, effective-context curves. | Selection, sliding window, compression, hierarchy (scope and precedence), prompt or KV cache, processing pipeline. |
| Process | A stage did the wrong operation or skipped a required one: a parser emitted garble, a selector omitted a dependency, a compressor removed a negation, a checkpoint restored the wrong branch, an invalidation job missed an index, a retry repeated an unchanged bad strategy. | Stage inputs, outputs, versions, decisions and postconditions. | The stage that owns the failed operation. |
| Adversarial | An attacker exploits a content, structure or process weakness to change instructions, memory, tool behaviour, authorization or downstream state. | Untrusted-content flow, taint, handoffs, tenant transitions, tool descriptors, credentials. Transient prompt injection is an input attack; memory poisoning is a persistent integrity attack with a longer blast radius. | Isolation controls (quarantine, taint, least privilege, sandboxing) plus the security incident process; quality recovery alone is not enough. |
