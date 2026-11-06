---
created: "2026-11-04T19:44:52Z"
updated: "2026-11-04T19:44:52Z"
---

# Stable-prefix layout and invalidation audit

## The exact-prefix rule

A cache entry is the model state after an ordered prefix. Changing a token, image, tool schema, relevant request setting or serialization detail early in that prefix can stop reuse at the first divergence; everything after it is written again. Semantically equivalent but token-different text does not hit.

## Order of the rendered request (least to most volatile)

1. Provider-required content and model selection.
2. Stable tool definitions, names, descriptions and schemas.
3. Stable system or developer instructions.
4. Shared static corpus, examples, policies or document content.
5. Slower-changing project or tenant context.
6. Append-only conversation and tool history.
7. Current retrieved evidence or memory blocks that may change.
8. Per-request message, timestamp, random identifier, nonce, deadline, trace text or other volatile data.

This order is subordinate to instruction authority and safety: never move untrusted retrieved text ahead of trusted instructions to gain a hit.

## Canonicalization rules

- Canonicalize only where semantics and the provider's rendering permit it.
- Freeze tool order; use deterministic JSON key order and number formatting; normalize line endings; keep template versions explicit.
- Do not silently trim, rewrap, reorder, translate or regenerate stable text.
- Hash the final rendered prefix, not the source objects it was assembled from.

## Tool-definition churn

Tool definitions sit near the start, so a change there invalidates all later instructions and history. Typical causes: a generated description, nondeterministic schema order, a capability-discovery result, a per-user tool list, a changed enum.

- Use a versioned tool bundle; sort tools and schema keys deterministically.
- Split a small stable core from optional tools only if the provider's required ordering and the safety policy allow it.
- Batch schema releases rather than changing one definition many times a day.
- On every miss record the tool-bundle id, tool-bundle hash, tool order and the first differing tool path.
- If per-user authorization changes tool availability, never expose an unauthorized tool to keep a cache: authorization dominates reuse.

## Prompt-restructuring loop

Repeat until the stable-prefix boundary stops moving, or safety or quality blocks further movement:

1. Render two or more requests expected to reuse context.
2. Tokenize or compare the final wire representation and find the first divergence.
3. Classify it: required, avoidable volatility, serialization noise, tool churn, memory edit, retrieval reorder, compaction, or routing mismatch.
4. Move avoidable volatile content later; canonicalize only semantics-preserving noise; freeze stable tool and instruction versions.
5. Place an explicit breakpoint on the last identical eligible block when supported; otherwise make sure the common prefix exceeds the provider minimum.
6. Re-render and compare again.
7. Send a cold request, wait until its cache is available, then send a warm request inside the TTL.
8. Accept the change only if the usage fields show the expected read and output quality is unchanged within the task's evaluation tolerance.

Do not pad meaningless tokens to cross a minimum unless measured savings exceed the added token cost and the padding cannot alter behaviour; prefer moving genuinely reusable instructions or examples into the prefix.

## Invalidation-audit loop (for each unexpected miss)

Compare the current request with the most recent eligible hit of the same cache family.

1. Confirm model, provider, region, endpoint, adapter, retention mode and cache key.
2. Confirm the request arrived inside the TTL and, where relevant, at an eligible worker.
3. Compare token IDs or canonical rendered blocks from the start to the first difference.
4. Attribute the first difference to one cause: tool definition, system template, memory block, retrieval selection or order, compaction, sliding-window movement, image or document identity, reasoning or output configuration, serialization, breakpoint placement, TTL expiry, routing, eviction or capacity, or unknown.
5. Fix the upstream producer, not the symptom. If the change is legitimate, version the cache family and accept a cold write.
6. Replay the cold and warm pair; close the finding only when provider-reported cached tokens recover.

Never log raw sensitive prefixes for debugging. Log a keyed fingerprint, block-level fingerprints, byte and token lengths, and the first differing block identifier.

## Multi-turn agents

An agent loop reuses its unchanged history each turn and prefills only the appended delta, so the cached fraction grows over the session.

- Keep history append-only: do not rewrite earlier tool results, normalize old messages every turn, insert a current timestamp at the top, or regenerate tool descriptions.
- When a tool bundle or policy must change, start a new cache version on purpose and measure the cold-write event.

## Context-management operations that move the first changed token

Evaluate the full downstream prefix affected by the first changed token, in base-input equivalents, over the expected remaining turns and the TTL.

- Memory-block edit: an early block edit invalidates that block and everything after it. Batch non-urgent edits; place more volatile blocks later when authority permits.
- Sliding-window advance: dropping an early span changes the prefix. Advance in useful batches with hysteresis, not one message at a time.
- Compaction or semantic compression: a shorter replacement saves future input but makes the prefix cold from the first replaced token.
- Selection reorder: a new ordering can invalidate an identical set. Keep stable tie-breaking and deterministic grouping; reorder only when the expected quality gain or token reduction exceeds the cache loss.
- Lifecycle or policy change: deletion, scope change or revoked access must invalidate or partition reuse at once. Never delay a required change to keep a hit.

Worked example (format only). A window slide would drop 4,000 tokens from each later request but moves an early point that otherwise allows a 30,000-token read at 0.1 times base. On the next request, losing the read costs about 30,000 minus 3,000, that is 27,000 base-token equivalents (before any write premium), against 4,000 saved. The change loses at once; it pays back only if enough later turns inside the TTL each save the 4,000.
