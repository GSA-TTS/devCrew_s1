---
created: "2026-11-04T19:44:25Z"
updated: "2026-11-04T19:44:25Z"
---

# Backward walk: stage questions, probes and attribution rules

Start with the output and walk backward. Do not begin by rewriting the prompt.

## Before the walk

1. Freeze evidence. The full set: visible output, raw provider response, model and settings, the exact ordered context fingerprint, tool calls and receipts, evaluator results, user correction, timestamps, release versions. Sensitive content stays under the owner's incident policy.
2. Confirm the outcome defect. Decompose the output into claims and actions. Name the first element that is materially wrong, missing, unauthorized, contradictory or unsupported.

## Stage rows (in walk order)

| # | Stage | What to check | How to read the result | Repair owner |
|---|---|---|---|---|
| 1 | Publication and streaming | Did the final verifier pass incorrectly, get skipped, run after emission, or lack the necessary claim? | If so, this stage needs a local repair, but keep walking to find the originating defect. | Processing pipeline (final verification, citation binding) or streaming (partial-output safety) |
| 2 | Generation against assembled context | Is the bad claim entailed, contradicted or absent in the exact context? | Absent: suspect generation hallucination or missing evidence. Present and wrong: suspect upstream context. Both supporting and conflicting evidence present: suspect clash handling or ordering. | Depends on the upstream finding |
| 3 | Pre-flight validation record | Which checks ran, on what inputs, with which verdicts, thresholds and versions? | A skipped, stale or falsely passing check is a prevention-stage failure. | The validation gate's owner |
| 4 | Assembly and sliding window | Reconstruct ordered units, token shares, delimiters, truncation, eviction, pins, tool definitions, provider transformations. | Missing pins, evicted corrective evidence, buried facts, tool overload. | Processing pipeline, selection, sliding window, hierarchy, or prompt and KV cache |
| 5 | Selection and retrieval | Compare the candidate universe with the selected and rejected items: eligibility, filters, ranking, source coverage, freshness, diversity, trust, tool loadout. | Required item absent from the candidate universe: retrieval or index failure. Present but rejected: selection failure. | Processing pipeline (retrieval, index) or selection |
| 6 | Compression and summaries | Compare each derived claim with its immutable source: lost negation, entity attachment, valid time, support multiplicity, cycle count. | A derived claim stronger, reattached or unqualified relative to its source is a compression defect. | Compression or semantic compression |
| 7 | Resident and durable memory | Find the first revision that contains the bad claim; check writer, evidence, approval, scope, promotion, supersession, block rendering. | The first bad revision and its writer locate the write. | Durable-memory write, memory blocks, lifecycle, or hierarchy |
| 8 | Tools and external state | Tool arguments, results, time, identity, idempotency receipts, and whether external state changed between observation and action. | Wrong transition or effect, stale observation. | State machine (transitions, guards, effects, compensation) |
| 9 | Boundaries and adversarial flow | Trace untrusted content, taint, agent handoffs, tenant transitions, tool descriptors, credentials. | If manipulation or boundary escape is plausible, the causal plane is adversarial and the security response applies. | Isolation controls and security response |

## Controlled replay probes

Use the same context and settings when permitted, then compare a focused context, a reordered context and a context with the suspected unit removed. Do not conclude causation from one stochastic pair; repeat across seeds and cases. Do not mutate live context for consequential actions.

| Probe result | Points toward |
|---|---|
| Repeated failure on the same valid context | Model or instruction behaviour |
| Improvement after removing the suspected unit | Confusion or poisoning |
| Improvement after shortening (focused versus full) | Distraction or rot |
| Improvement after reordering | Positional structure |

Other diagnostic tests and their limits:

- Groundedness: decompose the output into atomic claims; for each, record the supporting context units, the entailment verdict, the authority, and whether the claim exceeds the evidence. Judge citation correctness separately from citation presence.
- Contradiction: pair claims by entity, predicate, date, unit and jurisdiction; apply exact checks and temporal logic before any NLI or model adjudication. A generic NLI score does not resolve authority; leave unresolved cases as a conflict set.
- Retrieval sufficiency: derive a requirement list from the task, bind evidence to each requirement, and separate "not found" from "found but low authority", "found but stale" and "found but contradictory". Similarity scores, k, context length and model confidence do not show sufficiency.
- Self-consistency sampling: agreement is not truth; samples can share the same poisoned context.
- Deterministic checks (token fit, role grammar, identifiers, hashes, tool-call pairing, tenant scope) prove conformance, not meaning.
- User corrections, regenerate requests and undo actions are leading signals once bound to the preceding context fingerprint; not every follow-up is a correction.

## Cascade lineage

Trace the failure as a lineage graph, not as one bad prompt. A representative cascade: an unsupported statement is written as an unverified memory; it survives checkpoints and is promoted; recency or access frequency lets it outrank verified evidence at selection; a summary strips its qualifiers; semantic merging attaches it to the wrong entity or time; it becomes a resident block; a shared scope propagates it to descendants; the sliding window evicts the corrective evidence; a cache reuses the bad prefix; tools act on it; streaming delivers a plausible answer before later verification. Breakers belong at each boundary (before durable write, promotion, selection, compression, block rendering, model call, consequential tool call, publication, and after purge), so every breaker the defect passed is a candidate contributing stage.

## Attribution rules

- Root stage: the earliest stage whose output violated its contract. Later stages that failed to detect or contain the defect are contributing stages, not the root.
- "The model hallucinated" names an output symptom, not a system root cause.
- Confidence: `confirmed`, `probable`, `possible` or `unknown`, each with the evidence and the counterevidence.
- Exit: one root-stage attribution, zero or more contributing-stage attributions, a propagation path, a containment state, and a routed repair.
- Minimize and replay: build the smallest fixture that reproduces the failure, and verify the stage-local repair fixes it without breaking adjacent golden cases.

## Format example (attribution block)

Scenario (illustration only): a scheduling agent picked a deprecated calendar tool because many near-duplicate tool definitions were loaded.

```text
Root stage: selection and retrieval (tool loadout included deprecated and duplicate tools)
Contributing stages: pre-flight validation (no tool-count or deprecation check); publication (no verification of the tool used)
Propagation path: tool registry -> selection loads all tools -> assembled context crowded -> generation picks deprecated tool -> action executed
Confidence: probable. Evidence: failure stops when the deprecated tool is removed in replay. Counterevidence: one replay pair only; not yet repeated across seeds.
```
