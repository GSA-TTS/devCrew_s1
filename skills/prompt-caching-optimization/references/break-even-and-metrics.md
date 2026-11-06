---
created: "2026-11-04T19:44:52Z"
updated: "2026-11-04T19:44:52Z"
---

# Break-even, metrics and logging

## Baseline before any change

Collect an uncached or pre-optimization trace for representative workloads: prompt tokens by region of the prompt, output tokens, time to first token, total latency, provider, model and version, and actual price. Segment by endpoint, tenant class, task and conversation turn. Do not infer savings from list prices alone when negotiated rates or batch, flex or priority modifiers apply. The baseline is done when the repeated prefix can be named and its length, change frequency, reuse interval and share of input cost are quantified.

## Break-even per cache family

Use actual token counts and contracted prices.

1. One uncached processing of the candidate prefix is one base-input cost unit.
2. Record the write multiplier, the read multiplier, any explicit storage cost, and the expected number of reads before expiry or invalidation.
3. Cached plan = write multiplier + (read multiplier x number of later reads) + storage. Uncached plan = 1 unit for every use (the first use plus each later read).
4. Cache only when the cached total is lower by more than the organization's engineering and risk margin.
5. Recompute after any model, price, TTL, traffic or prompt-volatility change.

Worked arithmetic (multipliers only):

- 1.25 write, 0.1 read: one write plus one read is 1.35 units against 2, so the first successful reuse clears token-price break-even.
- 2 write (1-hour TTL), 0.1 read: one write plus one read is 2.1 against 2, which does not break even; a second read makes it 2.2 against 3.
- For explicit caches with storage (Gemini), add the token-hour storage cost before judging.

For a partial prefix, calculate the cached and uncached regions separately. A hit on 1,000 tokens is not equivalent to a hit on 100,000; do not divide saved dollars by total requests and call it a hit rate.

Caching is not worth the complexity when: the eligible prefix is below the minimum; expected successful reuse before expiry is below break-even; early content is inherently volatile; repeats are spread over incompatible models or regions; output dominates cost and latency; compliance forbids retention or sharing; routing misses erase the gain; or observability cannot verify actual cached tokens.

Saving decomposition: caching removes the ordinary price and prefill work only for the cached input tokens (at the provider's cached rate). It removes no output-token charge and no decode work. Report the split (cached input, uncached input, output) rather than a single percentage.

## Metrics

- Request hit rate: requests with any cached tokens / eligible requests. Use only as a routing symptom.
- Token-weighted cache hit rate: total cached-input tokens / total eligible prefix tokens. Measures how much repeated prefill was reused.
- Read conversion rate: cache-read tokens / (cache-read + cache-write tokens). Reveals prefixes written often but rarely read.
- Cost-weighted cache effectiveness: (uncached counterfactual input cost - actual input, write and storage cost) / uncached counterfactual input cost. The principal economic metric.
- Effective blended input cost per thousand tokens: (actual input + cache-write + cache-read + storage cost) / total input tokens x 1,000.
- Savings per request: uncached counterfactual total cost - actual total cost, with output and external-tool charges unchanged in the counterfactual unless the experiment changes them.
- TTFT delta: matched cold TTFT - warm TTFT for the same prefix length, suffix length, model, route and load bucket; report p50, p95 and p99.
- Invalidation rate by cause: eligible misses attributed to a cause / eligible attempts; also compute lost cached-token value by cause and prioritize by that value.

A high request hit rate can still lose money when storage or write premiums dominate.

## Per-request log fields (hosted provider)

- Trace and request IDs, timestamp, environment, deployment and experiment ID.
- Provider, endpoint, model ID and immutable revision.
- Tenant or cache-sharing-domain pseudonym, session pseudonym, conversation turn, region, route decision reason.
- Total rendered input tokens, eligible prefix tokens, provider cached tokens or equivalent, cache-read tokens, cache-write tokens, ordinary uncached input tokens, output tokens.
- Cache classification: bypass, below minimum, cold write, partial hit, full eligible hit, expired, evicted, routing miss, incompatible configuration, or unknown.
- Breakpoint count and token positions, TTL requested, cache age, cache key class, keyed prefix fingerprint, block fingerprints, tool-bundle version, prompt-template version, memory-block version, context-selection version.
- First divergent block ID and invalidation cause: tool churn, system edit, memory edit, retrieval membership, retrieval reorder, compaction, sliding-window movement, multimodal change, serialization, request setting, TTL, routing, eviction, deployment, or unknown.
- Time to first token, total latency, cancellation or error.
- Base input, cache-write, cache-read, storage and output prices, currency, pricing-version timestamp, actual request cost, uncached counterfactual cost.
- Quality-evaluation version and outcome for sampled requests.

Keep raw prompts out of general telemetry. Prefix fingerprints are keyed hashes scoped to the organization, so they cannot become a dictionary oracle.

## Drift signals to alert on (sustained, not one-off cold starts)

- Token-weighted hit rate falls while request hit rate stays stable.
- Writes rise without more reads.
- A new first-divergence block or tool-bundle hash appears.
- TTL expiry spikes after a change in traffic cadence.
- p95 TTFT regresses at a constant cached-token count.
- Billed cached tokens or storage do not reconcile with response usage.

For every prompt-builder, tool-registry, memory-block, selection, compression, model or routing release, run a cold and warm canary: release only if the first-difference location is expected, the usage fields agree with the predicted hit, and cost, TTFT, output quality and tenant isolation pass. Keep an uncached control cohort.

## Routing and warming

- Cache-family key: tenant boundary, region, model and version, adapter, prompt-template version, tool-bundle version, stable-prefix fingerprint; add an opaque session key for a session. Map equivalent requests to the same worker or the provider's routing hint and watch for hot spots.
- Sticky routing is affinity, not correctness: when the chosen worker is unhealthy or saturated, route elsewhere and accept the miss. Use bounded-load consistent hashing or a cache-aware router with spillover, and measure the hit loss caused by spillover.
- Warm only prefixes with forecast reuse: send one warm request, verify the entry is available, then release dependent fan-out. Rate-limit and deduplicate warmers, cancel them when a template version changes, and never warm every tenant or tool combination. Warm-up cost belongs to the owning workload's ledger.

## Release loop

By cache family, model and route: measure cold and warm requests under the same output settings; compare provider-reported cached tokens, input charges, TTFT, total latency and task quality; rank miss causes by lost cached-token cost; fix the largest avoidable cause and canary it; keep the change only when cost or latency improves without a quality, privacy or reliability regression; repeat until the marginal saving is below the change budget. The provider track is done when a production window meets the cost and TTFT targets, cached usage reconciles to billing, no tenant or retention finding is open, and rollback to the uncached path has been exercised.
