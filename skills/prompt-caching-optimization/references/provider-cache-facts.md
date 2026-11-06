---
created: "2026-11-04T19:44:52Z"
updated: "2026-11-04T19:44:52Z"
---

# Provider prompt-caching facts (snapshot dated September 6, 2026)

These values are a dated operating snapshot. Prices, models, minimums, usage fields and TTLs change: before using a value in a cost model, re-read the provider's own prompt-caching page and pricing page, cite the page and the date read, and keep a dated copy of the values used. Every value below is per the provider's documentation as of the snapshot date.

## Anthropic

- Modes: top-level automatic caching, and block-level explicit breakpoints.
- Prefix order: tools, then system content, then messages.
- Automatic mode places a breakpoint on the last eligible cacheable block. Explicit mode should mark the last block that stays identical across the requests meant to share state.
- Up to four explicit breakpoints; each searches backward at most 20 blocks for an entry that a previous request actually wrote. Writes occur only at selected breakpoints.
- TTL: 5 minutes by default; a read refreshes it with no new write charge. A 1-hour TTL is available.
- Prices relative to base input: 5-minute write 1.25 times, 1-hour write 2 times, read normally 0.1 times; the official page lists model-specific exceptions.
- Minimum cacheable prefix: model-dependent, from 512 to 4,096 tokens. A request below the minimum silently proceeds without caching, so check the usage response rather than assuming the marker worked.
- Usage fields: `cache_creation_input_tokens` and `cache_read_input_tokens`, besides ordinary input and output usage.
- A cache becomes available only after the first response begins: serialize one warm-up request before a parallel fan-out whose children must hit.
- Isolation: by organization and, on the first-party API and several platforms, by workspace. Exact matching covers text and images.
- Retention: KV representations and hashes stay in memory for the TTL and are then deleted; confirm the platform and data arrangement before sending sensitive material.
- Mode choice:
  - Automatic mode: a normal append-only conversation whose latest eligible block advances by fewer than 20 blocks per turn.
  - Explicit mode: a stable corpus followed by volatile requests; sections with different change rates; or when automatic placement lands on a timestamp or another changing block.
  - Never put a breakpoint only after volatile content and expect the lookback to find an entry at an earlier stable block.

## OpenAI

- Caching is on by default on supported models. The rendered prefix can include provider instructions, developer messages, tool definitions, conversation history and supported multimodal content; exact rendered-prefix identity and relevant settings decide reuse.
- GPT-5.6 and later: minimum visible cacheable prefix 1,024 tokens; writes 1.25 times ordinary input; reads 0.1 times; implicit or explicit breakpoints; up to four writes per request; reads can consider the latest 50 conversation breakpoints. TTL option `prompt_cache_options.ttl` supports `30m`, which is also the default minimum lifetime and is refreshed on reuse.
- Earlier models: generally implicit breakpoints, a 2,048-visible-token minimum, model-dependent cached-input prices and no extra write charge. Retention option `prompt_cache_retention`, commonly `in_memory` or `24h` where supported; availability depends on model and organization policy.
- Usage fields: `usage.input_tokens_details.cached_tokens`; newer responses may also report `cache_write_tokens`.
- Cached state is machine-local and isolated by organization and region; routing may overflow under load. `prompt_cache_key` groups related requests so they are more likely to reach a machine holding the entry; it neither pins a worker nor guarantees a hit.
- Mode choice:
  - Implicit mode first on supported earlier models and on plain append-only conversations.
  - Explicit mode on supported newer models when the application knows the stable boundary and wants to avoid paying to write a volatile suffix.
  - A stable `prompt_cache_key` per reusable prefix or session; shard a hot key if it overloads a worker.
  - Do not use a user identifier alone as the key when many distinct prefixes would collide, and never put secret material into routing keys.

## Google Gemini

- Implicit caching is on by default on Gemini 2.5 and newer models; explicit cache objects are created through the `generateContent` API. The Interactions API supports implicit caching only.
- Minimums: 2,048 input tokens for Gemini 2.5 Pro and Flash; 4,096 tokens for the listed Gemini 3-series models.
- Usage: cached-token usage in `usage_metadata`, with SDK-specific access such as `usage.total_cached_tokens`.
- Explicit caching sends reusable content once, creates a named cache object, and refers to it on later requests. Default TTL 1 hour; the caller may update TTL or expiry time, and no minimum or maximum TTL is documented. Cached content is a prefix and still counts toward the model's token limit.
- Billing for explicit caching: reduced-rate cached tokens on later prompts, plus token-hour storage for the cache lifetime, plus uncached input and output charges.
- Dated list prices (per million tokens, text input; model- and modality-specific):
  - Gemini 2.5 Pro, prompts up to 200,000 tokens: input $1.25, cached input $0.125, storage $4.50 per million token-hours. Above 200,000 tokens, ordinary and cached input double.
  - Gemini 2.5 Flash: input $0.30 (text, image, video), cached input $0.03, storage $1.00 per million token-hours.
- Mode choice:
  - Implicit caching when repetition is opportunistic and no storage commitment is justified.
  - Explicit caching when a large corpus or instruction set will be queried repeatedly over a known interval and the reduced read price outweighs creation and storage.
  - Delete explicit cache objects when the workload finishes; do not leave the 1-hour default on a short batch without computing the storage cost.

## Any other provider or a gateway

- Find, from the provider's own documentation, the minimum cacheable prefix, the write and read prices relative to base input, any storage charge, the TTL and its refresh rule, the breakpoint mechanism, the usage fields that report cached and written tokens, and the isolation boundary. Label each value not found as unknown.
- Never assume cache entries, token accounting, TTLs or hashes carry over between models, providers, regions, versions, adapters or runtimes; treat each as its own cache family.
