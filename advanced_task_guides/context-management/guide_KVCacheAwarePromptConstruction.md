# Cache-Aware Prompt Construction

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Cache-aware prompt construction constitutes the task family of assembling model requests so that a provider's prompt cache can reuse the work already done on an unchanged leading region, and of proving that reuse happened rather than assuming it. This guide provides AI agents with a structured protocol covering cacheable-region identification, stable-prefix construction under byte-identity enforcement, breakpoint placement where a provider exposes it, cache-family keying and warm-up sequencing, invalidation-cause attribution against a closed vocabulary, cost-weighted and token-weighted measurement against numeric targets, and a staleness bound that prevents a stable prefix from carrying content the run has outgrown. It states plainly that the underlying key-value cache is model-internal and unreachable, that the executable subject is prefix stability and placement discipline, and that the deterministic tier owns nearly the whole method. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that reuse is measured from provider-reported cache-token counts rather than inferred, and so that a saving is never purchased with a correctness defect.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Key-value cache**: The serving-side structure holding attention keys and values for tokens a model has already processed, retained so that generating each further token does not require recomputing the whole prefix. It is internal to the inference runtime and is never addressable by a calling agent.

**Prompt cache**: A managed reuse layer a provider offers over that internal state, keyed on the exact rendered bytes of a request's leading region. It is the only part of the mechanism an agent interacts with, and it is reached by construction, not by an API that reads or writes cache contents.

**Prefill**: The phase that processes the input request and produces the first output token. A prompt-cache hit removes repeated prefill work, so its visible effect is a lower time to first token and a lower input charge.

**Decode**: The phase that produces each token after the first. Caching removes no decode work and no output-token charge; a saving claimed against output tokens is a measurement error.

**Stable prefix**: The leading region of the rendered request whose bytes do not change across the calls intended to share cache state. The term is used here in the sense established by the context lifecycle guidance in this corpus, and the two uses refer to the same artifact.

**Epoch**: One continuous span of a run served by a single stable prefix. An epoch ends when the prefix must legitimately change; a new epoch pays one cold write rather than continuing under a stale identity.

**Prefix hash**: A keyed hash computed over the final rendered prefix bytes after serialization, recorded per request and compared across requests to detect divergence. It is computed over what goes on the wire, never over the source objects from which the request was assembled.

**Cache breakpoint**: A provider-exposed marker declaring the position at which cache state should be written. Providers that expose breakpoints bound their number per request; providers that do not expose them cache the longest eligible common prefix implicitly.

**Cache family**: The set of requests eligible to share one cache entry, identified by a key spanning tenant boundary, region, model and version, adapter, prompt-template version, tool-bundle version, and prefix hash. Two requests differing in any of those dimensions can never share state, whatever their text.

**Eligible prefix tokens**: The count of leading tokens that could in principle have been served from cache on a given request, used as the denominator of the token-weighted reuse metric.

**Cache-read tokens**: The provider-reported count of input tokens served from an existing entry. This figure, not a latency impression or a cost estimate, is the ground truth that reuse occurred.

**Cache-write tokens**: The provider-reported count of input tokens written to a new entry, normally billed at a premium above the base input rate.

**Invalidation cause**: A label from a closed vocabulary attributing an unexpected miss to a single first divergence or infrastructure condition, recorded on every eligible miss so that repair targets the producer rather than the symptom.

**Staleness bound**: The maximum age permitted for any fact carried inside the stable prefix, declared per cache family, beyond which the prefix must be rebuilt even though rebuilding forfeits reuse.

### 1.2 The Model-Internal Mechanism and the Agent-Layer Surrogate

**What is model-internal and unavailable**: The key-value cache itself is a set of tensors held by the inference runtime. Its allocation policy, block layout and fragmentation behaviour, eviction order, numeric precision, and placement between accelerator memory and host memory are properties of that runtime. A guide addressed to agents cannot instruct them to configure, size, evict from, quantize, offload, or inspect any of it, because no prompting interface, tool call, HTTP request, or script available at the agent layer reaches those structures. Guidance of that kind belongs to a serving team operating its own inference workers, and it is excluded from this guide rather than restated in weaker form.

**What the agent genuinely controls**: Whether the cache is hit. Reuse is governed by exact-prefix identity, and prefix identity is entirely a function of construction: what the agent places at the front of the request, whether those bytes are identical across calls, whether tool definitions and instruction strings are regenerated or reordered between turns, where a breakpoint is placed when the provider exposes one, and whether the agent appends to history rather than rewriting it. These are ordinary agent decisions with large and measurable cost consequences, and they are the executable subject of this guide.

**Why the surrogate is faithful**: The two layers meet at one rule. A cache entry represents processed state for an ordered sequence of bytes, so reuse stops at the first position where a later request diverges. An agent that never sees a tensor can still determine, exactly and in advance, the position of that first divergence, because it produced the bytes. Construction discipline is therefore not an approximation of cache management; it is the whole of the caller's half of the contract.

**What the surrogate cannot deliver**: Cache-aware construction cannot reduce output-token cost, cannot make irrelevant context useful, cannot preserve behaviour across a rewrite that changes meaning, and cannot guarantee a hit. Providers route requests across machines, expire entries on a timer, and apply minimum prefix lengths below which a marked request silently proceeds uncached. An agent may render a perfect prefix and still miss, which is why measurement in Phase 5 is mandatory and why a design that only pays off under a guaranteed hit must not be deployed.

**Terminology discipline**: An application memory store, a semantic response cache keyed on meaning, and a provider prompt cache keyed on bytes are three different things with three different correctness properties. A prompt cache is an ephemeral acceleration artifact and never authoritative state; deletion of a record from a durable store is not accomplished by waiting for a cache entry to expire.

### 1.3 Volatility Ordering and the Cacheable-Region Partition

The method rests on partitioning a request into regions by change frequency and rendering them in ascending order of volatility, so that the boundary between reusable and non-reusable content falls as late as possible.

**Canonical volatility order**: Requests must be rendered least volatile first, in this sequence: provider-required content and model selection; tool definitions with their names, descriptions, and schemas; system or developer instructions; shared static corpus, examples, and policy text; slower-changing project or tenant context; append-only conversation and tool history; current retrieved evidence and mutable memory blocks; and finally per-request material such as the current question, a timestamp, a nonce, a trace string, or a deadline.

**Authority outranks reuse**: This ordering is subordinate to instruction precedence and safety. Untrusted retrieved text is never moved ahead of trusted instructions to gain a hit, an unauthorised tool is never exposed to preserve a bundle hash, and a required deletion or scope change is never delayed because it would force a cold write. Where the two conflict, authority wins and the cold write is accepted and recorded.

**Region partition table**:

**Table 1: Request regions by change frequency and cache treatment**

| Region | Typical change interval | Placement | Cache treatment |
| :-- | :-- | :-- | :-- |
| Tool definitions and schemas | Per release | Position 0 | Inside stable prefix; version-pinned and order-frozen |
| System and developer instructions | Per release | After tools | Inside stable prefix; rendered from a pinned template version |
| Shared corpus, examples, policy text | Days to weeks | After instructions | Inside stable prefix where it exceeds the provider minimum |
| Project or tenant context | Hours to days | After corpus | Inside stable prefix only where the staleness bound permits |
| Conversation and tool history | Per turn | After context | Append-only; breakpoint advances with the tail |
| Retrieved evidence and memory blocks | Per turn or per edit | After history | Outside the stable prefix by default |
| Question, timestamp, identifiers, nonce | Per request | Last | Never inside any cached region |

**The minimum-length gate**: Every provider states a minimum cacheable prefix below which a marked request silently proceeds without caching and reports zero written tokens. Agents must measure the eligible prefix with the target model's tokenizer and treat a prefix below the stated minimum plus a 20 percent margin as non-cacheable. Padding a prefix with meaningless tokens to cross a minimum is prohibited, because the padding is billed on every request and can alter behaviour; the admissible remedy is moving genuinely reusable instructions or examples earlier.

**When the method should not be applied at all**: Cache-aware construction is not warranted where the eligible prefix falls below the minimum, where prefixes are mostly unique across requests, where expected reuse before expiry falls below the break-even threshold in Step 5.3, where output tokens dominate cost and latency, where retention policy forbids provider-side storage of the material, or where the deployment cannot observe provider cache-token fields and therefore cannot verify any claimed saving. In those cases the correct output of Phase 1 is a recorded decision not to cache, with instrumentation retained so the decision can be revisited.

### 1.4 Execution Tier Partition and the Near-Empty Model Tier

This method is unusual in the corpus: it is almost entirely deterministic. Prefix construction is a serialization problem, byte identity is a hash comparison, breakpoint placement is arithmetic over declared boundaries, and reuse is an integer reported by the provider. None of that admits open-vocabulary judgement, and treating any of it as a model decision introduces nondeterminism into the one thing that must be deterministic.

**Table 2: Tier ownership by artifact**

| Artifact or decision | Owning tier | Authority on disagreement |
| :-- | :-- | :-- |
| Volatility classification of a named input | Hybrid | Deterministic; a model proposal is advisory and a declared classification governs |
| Assembly order and the prefix and suffix split | Deterministic | Deterministic; ordering is policy, never a per-request preference |
| Serialization canonicalisation and tool ordering | Deterministic | Deterministic; a nondeterministic serializer is a defect, not a variation |
| Prefix hash and byte-identity assertion | Deterministic | Deterministic; a differing hash without an epoch increment halts the call |
| Breakpoint position and count | Deterministic | Deterministic; computed from declared boundaries and the provider's limits |
| Cache-family key derivation | Deterministic | Deterministic; isolation dimensions are policy inputs |
| Cache-token accounting and metric computation | Deterministic | Deterministic; provider-reported integers are the only admissible evidence |
| First-divergence localisation | Deterministic | Deterministic; a byte diff over the overlapping region, not an inference |
| Attribution of a divergence to an upstream producer | Hybrid | Deterministic where the diff names a field; the model tier only proposes a candidate producer for an unlocalised cause |
| Whether a semantic rewrite preserves meaning | Model | Model proposes; a deterministic evaluation gate accepts or rejects |
| Whether prefix content has become stale | Hybrid | Deterministic on the declared staleness bound; the model tier may flag suspected staleness earlier but may not extend the bound |

**What the deterministic tier rejects unconditionally**: a request whose prefix hash differs from the epoch's recorded hash without an epoch increment; a tool bundle serialized in a non-deterministic order; a breakpoint placed after per-request content; a cache-family key omitting the tenant or region dimension; a claimed saving unsupported by provider-reported cache-read tokens; a stable prefix carrying a value that changes per request; and a retention or sharing setting that widens the cache boundary beyond the declared isolation domain.

**What the model tier is never permitted to decide alone**: whether two prefixes are equivalent, whether a miss is acceptable, whether a breakpoint is well placed, whether a saving occurred, or whether a boundary may be crossed. Semantic equivalence is precisely the property that does not produce a cache hit, so a model judgement of similarity carries no weight in this method. The model tier's only genuine work is proposing volatility classifications for unfamiliar inputs, proposing which of several candidate producers introduced an unlocalised divergence, and judging whether a rewrite that would improve reuse preserves meaning. Every one of those proposals is verified deterministically before it takes effect. This near-emptiness is a finding about the method rather than an omission from the guide.

***

## II. Operational Framework: Verified Prefix Reuse Under a Declared Staleness Bound

The framework produces one governed cache design per workload: a region partition with a declared stable prefix, a recorded prefix hash asserted on every call, a breakpoint plan within the provider's limits, a cache-family key bounded by the isolation domain, an attribution record for every eligible miss, a metric set reconciled against billing, and a staleness bound that fixes when reuse must be surrendered. Phases 1 through 3 construct; Phase 4 diagnoses; Phases 5 and 6 measure and govern. Phase 4 returns control to Phase 2 whenever an attributed cause names a construction defect.

### Phase 1: Cacheable-Region Identification and Baseline Measurement

**Objective**: Determine whether a reusable prefix exists, measure it against the provider's minimum and the workload's reuse distribution, and record a decision to cache or not to cache before any prompt-assembly code is changed.

**Owning tier**: Deterministic, with a hybrid handoff at volatility classification where an input's change frequency is not already declared by its producer.

#### Step 1.1: Inventory Prompt Inputs and Classify Them by Change Frequency

**Required Actions**:

- Trace the assembly path for every request class, and enumerate each input that flows into tool definitions, system or developer content, and the message sequence.
- Record for each input its producer, its declared change interval, whether its serialization is deterministic, and whether it varies by tenant, session, or request.
- Classify every input into one of four bands: fixed for the life of a release, changing per session, changing per turn, and changing per request.
- Refer an input whose change interval is undeclared to the model tier for a proposed classification, and accept that proposal only after observing the input across at least 20 consecutive rendered requests.
- Mark every input that reaches the front of the rendered request while sitting in the per-turn or per-request band, since each such input caps the reusable prefix at its own position.

**Required Outputs**:

- An input inventory listing producer, change band, serialization determinism, and scope for every input.
- A ranked list of front-positioned volatile inputs, ordered by the number of prefix tokens each one strands.
- A record of every classification proposed by the model tier and the observation count that confirmed it.

**Quality Checkpoints**:

- Every input in the inventory carries a change band; an unclassified input blocks progress to Phase 2.
- No input classified as fixed varies across the 20 observed renderings; a single variation reclassifies it downward.
- The stranded-token figure for each front-positioned volatile input is computed with the target model's tokenizer, not estimated from character length.

***

#### Step 1.2: Establish the Uncached Baseline and the Reuse Distribution

**Required Actions**:

- Capture a representative trace of at least 200 requests per request class, recording rendered input tokens, output tokens, time to first token, total latency, provider, model identifier and version, and the actual contracted price applied.
- Compute, over that trace, the length of the longest common leading region across requests within each cache family, and the distribution of intervals between requests sharing it.
- Segment the trace by endpoint, tenant class, task type, and conversation turn index, since a workload's reuse profile is rarely uniform across those axes.
- Record the share of total request cost attributable to input tokens, separating it from output-token cost, since caching acts only on the former.
- Derive contracted prices from the billing agreement in force rather than from published list prices, and record the pricing-version timestamp beside every figure.

**Required Outputs**:

- A baseline trace record with per-request token, latency, model-version, and cost fields.
- A per-family reuse profile stating shared-prefix length, reuse interval distribution, and reuse count before expiry.
- An input-cost share figure per request class.

**Quality Checkpoints**:

- The baseline covers at least 200 requests per class and spans at least one full traffic cycle, so that a burst-only or idle-only sample does not set the profile.
- Shared-prefix length is measured on the final rendered wire representation, not on the source objects.
- Every cost figure carries a pricing-version timestamp; an undated price is not admissible evidence in Step 5.3.

***

#### Step 1.3: Record a Cache or No-Cache Decision Against the Minimum-Length Gate

**Required Actions**:

- Compare each family's shared-prefix length against the provider's stated minimum cacheable prefix for the exact model in use, and require the measured length to exceed that minimum by at least 20 percent.
- Compare each family's expected reads before expiry against the break-even threshold for the retention option under consideration, requiring at least 2 expected reads for a short-lived entry and at least 3 for a long-lived entry whose write premium is higher.
- Record a no-cache decision, with its reason, wherever the minimum-length gate fails, the reuse count falls below break-even, retention policy forbids provider-side storage, or cache-token fields are not observable in the deployment.
- Retain instrumentation on families carrying a no-cache decision, so the decision can be revisited when traffic shape or prompt structure changes.
- Prohibit token padding as a remedy for a short prefix, and record instead which reusable instructions or examples could be relocated earlier to raise the shared length legitimately.

**Required Outputs**:

- A per-family decision record stating cache or no-cache, the governing gate, and the measured values on both sides of it.
- A relocation candidate list for families failing the minimum-length gate.
- A revisit trigger per no-cache decision, expressed as a named change in traffic or prompt structure.

**Quality Checkpoints**:

- Every family carries an explicit decision; an absent decision is treated as no-cache and blocks breakpoint placement.
- No decision to cache rests on a shared-prefix length within 20 percent of the provider minimum.
- No family is padded to cross a minimum, and no relocation candidate moves untrusted or unauthorised content forward.

***

### Phase 2: Stable-Prefix Construction and Byte-Stability Enforcement

**Objective**: Render the request in ascending volatility order with deterministic serialization, then bind the result to a recorded prefix hash so that any later divergence is detected before the call is issued rather than inferred afterwards from a bill.

**Owning tier**: Deterministic throughout. Ordering, serialization, and hashing admit no model judgement, and a model-proposed reordering is accepted only after a deterministic equivalence gate confirms it changes no rendered byte outside the intended region.

#### Step 2.1: Render the Request in Ascending Volatility Order

**Required Actions**:

- Emit the rendered request in the canonical order stated in Section 1.3, placing provider-required content and tool definitions first and per-request material last.
- Move every input classified in Step 1.1 as per-turn or per-request behind the last intended breakpoint, and record the token count recovered by each relocation.
- Replace any dynamic value interpolated into instruction text with an equivalent value carried after the stable region, so that no instruction string is rebuilt per request.
- Where a provider supports an operator instruction delivered after the accumulated history rather than by editing leading instruction content, use that channel for any mid-run instruction change, since editing leading content invalidates the entire following region.
- Preserve append-only history: never rewrite a prior tool result, never normalise older messages on a later turn, and never insert new content ahead of existing history.

**Required Outputs**:

- A rendered request whose region boundaries match the declared partition.
- A relocation ledger naming each moved input and the prefix tokens it recovered.
- A statement of the operator-instruction channel used for mid-run instruction changes.

**Quality Checkpoints**:

- No timestamp, session identifier, trace string, nonce, counter, or per-request identifier appears anywhere ahead of the last breakpoint.
- The rendered order is non-decreasing in volatility band from the first byte to the last breakpoint.
- History is append-only across consecutive turns: the previous request's rendered message region reappears unchanged as a leading region of the next.

***

#### Step 2.2: Canonicalise Serialization and Freeze the Tool Bundle

**Required Actions**:

- Serialize every structured element with a declared encoding, a fixed key order, fixed number formatting, and normalised line endings, so that a semantically identical element is byte-identical on every rendering.
- Sort tool definitions and their schema keys by a stable rule, and emit them from a versioned bundle carrying a bundle identifier and a bundle hash rather than assembling them per request.
- Prohibit iteration over unordered collections anywhere in the assembly path, and prohibit generated tool descriptions whose text is produced by a model at request time.
- Batch tool-schema and instruction-template releases into declared versions rather than shipping single-definition changes repeatedly within a traffic window, since each change ends the epoch for every family that includes the bundle.
- Where tool availability legitimately varies by authorisation, partition into distinct cache families rather than exposing an unauthorised tool to preserve one bundle hash.

**Required Outputs**:

- A canonical serialization specification covering encoding, key ordering, number formatting, and line endings.
- A versioned tool bundle with an identifier, a hash, and a frozen ordering.
- A family partition mapping each authorisation profile to its own cache family.

**Quality Checkpoints**:

- Two renderings of the same logical request from cold process state produce byte-identical output; a difference indicates a nondeterministic serializer and halts release.
- The tool bundle hash is stable across at least 50 consecutive renderings within one release.
- No cache family spans two authorisation profiles, and no tool appears in a bundle the requesting principal is not entitled to invoke.

***

#### Step 2.3: Hash the Rendered Prefix and Assert Byte Identity Before Every Call

**Required Actions**:

- Compute a keyed hash over the final rendered prefix bytes, after serialization and immediately before transmission, and record it with the request.
- Record alongside it a block-level hash sequence covering each region of the prefix, so that a later divergence can be localised to a region without retaining the prefix text.
- Compare the prefix hash against the hash recorded for the epoch on every subsequent call in the family, and halt the call where the hashes differ without an accompanying epoch increment.
- Scope the hash key to the organisation and rotate it under a documented migration, so that stored fingerprints cannot function as a dictionary against which prefix content is guessed.
- Exclude breakpoint markers themselves from the hashed bytes, since a marker that advances with the conversation tail differs legitimately between adjacent requests and is not a divergence.

**Required Outputs**:

- A per-request prefix hash and block-level hash sequence.
- An epoch record binding a family to its frozen prefix hash, its pinned template and bundle versions, and its model identifier.
- A key-rotation procedure for the hashing key.

**Quality Checkpoints**:

- The prefix hash is identical across every call within an epoch; a differing hash without an epoch increment halts the call rather than issuing it.
- The hash is computed over transmitted bytes, and never over the source objects from which the request was assembled.
- No raw prefix text and no sensitive payload is written to general telemetry; block-level hashes, byte lengths, and token counts carry the diagnostic load instead.

***

### Phase 3: Breakpoint Placement, Family Keying, and Warm-Up Sequencing

**Objective**: Place cache markers at declared stability boundaries within the provider's limits, bound the set of requests permitted to share an entry, and order the first requests of a fan-out so that dependent calls read an entry that already exists.

**Owning tier**: Deterministic. Placement is arithmetic over declared boundaries and provider limits; keying is a policy join; sequencing is a scheduling rule.

#### Step 3.1: Place Breakpoints at Declared Stability Boundaries

**Required Actions**:

- Place a marker on the last block of the stable region shared by every request in the family, rather than at the end of the whole request, so that per-request material is never written to an entry no later request will read.
- Where sections change at different intervals, place one marker at each boundary, subject to the provider's per-request maximum, which is commonly 4 markers.
- Where the provider places a marker automatically on the last eligible block, verify that the automatic position lands ahead of per-request content, and switch to explicit placement wherever it does not.
- Where a single turn appends many positions, place an intermediate marker at least every 15 positions, because a provider's backward search for an existing entry is bounded and commonly reaches at most 20 blocks.
- Order markers so that any longer-lived entry precedes any shorter-lived entry, and never mark a block that carries content the provider excludes from caching.

**Required Outputs**:

- A breakpoint plan naming each marker's position, the boundary it serves, and the retention option applied.
- A marker-count record showing usage against the provider's per-request maximum.
- A statement of whether automatic or explicit placement governs each family, with the reason.

**Quality Checkpoints**:

- No marker sits after per-request content; a marker in that position produces a write on every request and a read on none.
- Marker count per request does not exceed the provider's stated maximum, and no boundary carries more than 1 marker.
- No turn appends more than 20 positions past the previous entry without an intermediate marker.

***

#### Step 3.2: Derive the Cache-Family Key and Bound Its Sharing Domain

**Required Actions**:

- Derive the family key from tenant or trust domain, region, model identifier and immutable version, adapter identity, prompt-template version, tool-bundle version, and prefix hash, and treat any request differing in one of those dimensions as belonging to a different family.
- Add an opaque session key where reuse is session-scoped, and never derive that key from a user identifier alone where many distinct prefixes would collide onto one routing target.
- Partition by tenant and trust domain by default, and permit cross-principal sharing only for reviewed content whose exposure is acceptable to every principal in the domain, recorded as an explicit approval.
- Exclude secrets, personal identifiers, and raw request text from family keys, routing hints, and metric labels.
- Where the provider exposes a routing hint that groups related requests, supply the family key's stable portion and monitor for a single hot key concentrating load, sharding it when it does.

**Required Outputs**:

- A family key specification naming every dimension and its source.
- A sharing-domain declaration per family, with an approval record for any cross-principal family.
- A hot-key monitoring rule with a sharding trigger.

**Quality Checkpoints**:

- The key includes tenant, region, model version, and prefix hash; omission of any of the four blocks deployment.
- No family permits cross-principal reuse without a recorded approval naming the reviewed content.
- No key, routing hint, or metric label carries a secret, a personal identifier, or raw request text.

***

#### Step 3.3: Sequence Warm-Up Ahead of Dependent Fan-Out

**Required Actions**:

- Issue one request per family to create the entry, and release dependent parallel requests only after that first response has begun, since an entry is not readable while it is still being written.
- Restrict warming to families with forecast reuse, and never warm every combination of tenant, tool bundle, and template speculatively, because each warm request costs a write premium.
- Deduplicate concurrent warm jobs on the family key, rate-limit the warmer, and cancel outstanding warm jobs whenever a template or bundle version changes.
- Where a fork or side computation must share the parent's entry, copy the parent's leading regions verbatim and append fork-specific content after the last marker, rather than rebuilding those regions independently.
- Charge warm-up cost and entry occupancy to the owning workload's ledger rather than treating it as free overhead.

**Required Outputs**:

- A warm-up plan naming which families are warmed, on what trigger, and at what rate limit.
- A fork construction rule requiring verbatim reuse of the parent's leading regions.
- A warm-up cost line in the owning workload's ledger.

**Quality Checkpoints**:

- No fan-out of 2 or more dependent requests is released before the warming response has begun; premature release costs one cold write per lane.
- Warm jobs are deduplicated on the family key and cancelled on a version change.
- Every forked request's leading regions are byte-identical to the parent's; a rebuilt fork prefix is a construction defect.

***

### Phase 4: Invalidation Detection, Localisation, and Upstream Repair

**Objective**: Detect a miss from provider-reported counts, localise the first divergence inside the region two requests share, attribute it to one cause from a closed vocabulary, and repair the producer rather than the symptom.

**Owning tier**: Deterministic for detection and localisation; hybrid for attribution, where the model tier may propose a candidate producer only when the diff fails to name a field, and the deterministic tier confirms the proposal by replay.

#### Step 4.1: Detect the Miss From Provider-Reported Cache Counts

**Required Actions**:

- Read the provider's cache-read and cache-write token fields on every response, and treat those integers as the sole evidence that reuse occurred or failed.
- Compute expected reads for each request from the family's recorded shared-prefix token count, and raise an eligible-miss event whenever observed reads fall below 90 percent of that expectation.
- Recognise the healthy steady-state signature for an append-only loop: reads covering the whole accumulated prefix and growing turn over turn, writes covering only the newly appended region, and full-price input tokens covering only the tail past the last marker.
- Treat writes approaching the full request size on every request as a distinct symptom, since it indicates either an upstream prefix rewrite or an entry pushed outside the provider's backward search window.
- Rule out the two conditions that produce byte-identical requests with repeated writes before diffing payloads: a turn appending more positions than the backward search covers, and a provider-side transformation of prior-turn content that the caller did not perform.

**Required Outputs**:

- A per-request cache-accounting record with read, write, and uncached input token counts.
- An eligible-miss event stream with expected and observed read counts attached.
- A signature classification per family: healthy, write-dominated, or read-collapsed.

**Quality Checkpoints**:

- Every response's cache fields are recorded; an unrecorded response cannot support a savings claim in Phase 5.
- Total prompt size reconciles as uncached input plus written tokens plus read tokens on every request; a mismatch indicates an accounting defect rather than a cache defect.
- No family is declared healthy on latency observation alone; a latency improvement without a nonzero read count is not evidence of reuse.

***

#### Step 4.2: Localise the First Divergence Inside the Overlapping Region

**Required Actions**:

- Retrieve the most recent request in the family that produced an eligible read, and compare it against the missing request across the region the two are expected to share.
- Compare block-level hashes first, then bytes within the single divergent block, and report the position of the first difference inside the overlapping region rather than the position of any difference.
- Strip breakpoint markers before comparing, since a marker that advances with the tail differs legitimately and is not the invalidator.
- Confirm the compatibility dimensions before attributing to content: model identifier and version, region, endpoint, adapter, retention mode, and family key must match, and the request must have arrived inside the entry's lifetime.
- Where the provider exposes a server-side divergence report, enable it on every request in the family rather than retrofitting it after a miss, since a report keyed on a prior request requires that prior request to have carried the same instrumentation.

**Required Outputs**:

- A first-divergence record naming the block identifier, the byte offset within the block, and the two hashes.
- A compatibility verdict covering model, version, region, adapter, retention mode, family key, and entry age.
- A localisation method record stating whether the position came from a byte diff or a provider divergence report.

**Quality Checkpoints**:

- Localisation reports the first difference within the shared region; a difference in the legitimately new tail is never reported as an invalidator.
- Compatibility dimensions are confirmed before any content attribution; a model-version change is never attributed to a template edit.
- No raw prefix is logged for diagnosis; comparison runs against retained hashes, or against payloads held under restricted, audited access for the duration of the investigation only.

***

#### Step 4.3: Attribute the Cause and Repair the Producer

**Required Actions**:

- Assign each eligible miss exactly one cause from the closed vocabulary: tool-bundle change, instruction-template change, memory-block edit, retrieval membership change, retrieval reordering, compaction, window advancement, multimodal content change, serialization nondeterminism, request-setting change, marker placement, entry expiry, routing, capacity eviction, or unattributed.
- Repair the producer that introduced the divergence rather than the rendered symptom: a nondeterministic serializer is fixed at the serializer, a regenerated description is fixed at the template, an injected identifier is relocated at the assembly path.
- Where the change is legitimate and must stand, increment the epoch, write a new epoch record with the new prefix hash and pinned versions, and accept one cold write rather than suppressing the change.
- Replay a cold and warm pair after every repair, and close the finding only when provider-reported reads recover to at least 90 percent of the expected count.
- Rank open causes by lost cache-read token value rather than by event count, and address the highest-value cause first.

**Required Outputs**:

- An attribution record per eligible miss carrying one closed-vocabulary cause.
- A repair record naming the producer changed and the replay evidence closing the finding.
- A cause ranking ordered by lost cache-read token value.

**Quality Checkpoints**:

- Every eligible miss carries exactly one cause; a miss with two assigned causes is unresolved and stays open.
- Unattributed causes account for no more than 10 percent of eligible misses; above that threshold payload diffing is mandatory before any further tuning.
- No finding is closed without a replayed cold and warm pair showing recovered reads.

***

### Phase 5: Cache-Metric Accounting and Break-Even Adjudication

**Objective**: Convert provider-reported counts into token-weighted and cost-weighted measures, compare them against declared targets, and retain or revert the configuration on measured economics rather than on hit-rate impressions.

**Owning tier**: Deterministic. Every metric is an arithmetic function of provider-reported integers and dated contracted prices; no figure in this phase originates in a model judgement.

#### Step 5.1: Record the Per-Request Accounting Fields

**Required Actions**:

- Log per request, as structured events: request and trace identifiers; provider, endpoint, model identifier and immutable version, and adapter identity; tenant pseudonym, session pseudonym, region, and turn index; total rendered input tokens, eligible prefix tokens, cache-read tokens, cache-write tokens, uncached input tokens, and output tokens.
- Log the cache classification for each request from a closed set: below minimum, cold write, partial read, full eligible read, expired, routing miss, incompatible configuration, or bypassed.
- Log the breakpoint count and positions, the retention option requested, entry age, family key class, prefix hash, block hashes, and the pinned tool-bundle and template versions.
- Log base input price, write price, read price, storage price where a provider charges for retained entries, currency, and the pricing-version timestamp, together with the actual request cost and the uncached counterfactual cost.
- Keep raw prompts, secrets, and personal identifiers out of these events, and scope every fingerprint to the organisation.

**Required Outputs**:

- A per-request structured event carrying identity, token, classification, placement, and price fields.
- A closed cache-classification vocabulary applied to 100 percent of eligible requests.
- An uncached counterfactual cost per request computed from the same dated price table.

**Quality Checkpoints**:

- Every eligible request carries a classification from the closed set; an unclassified request is excluded from all metrics rather than silently counted as a hit.
- The counterfactual holds output-token and external-tool charges constant, so that a measured saving is attributable to input reuse alone.
- No event carries raw prompt text, a secret, or an unpseudonymised principal identifier.

***

#### Step 5.2: Compute Token-Weighted and Cost-Weighted Effectiveness

**Required Actions**:

- Compute token-weighted reuse as cache-read tokens divided by eligible prefix tokens, and hold a steady-state target of at least 70 percent for append-only multi-turn families, with a value below 40 percent triggering the Phase 4 audit.
- Compute read conversion as cache-read tokens divided by the sum of read and write tokens, and hold a target of at least 0.75, with a value below 0.50 indicating prefixes repeatedly written and rarely read.
- Compute cost-weighted effectiveness as the uncached counterfactual input cost minus actual input, write, and storage cost, divided by the uncached counterfactual input cost, and treat this as the governing economic figure.
- Compute the time-to-first-token delta between matched cold and warm requests at equal prefix length, suffix length, model, route, and load bucket, and report it at the 50th, 95th, and 99th percentiles.
- Report request hit rate only as a routing symptom, and never as an economic measure, since ten reads on a 1,000-token prefix can be worth less than one missed read on a 100,000-token prefix.

**Required Outputs**:

- A metric set per family and model covering token-weighted reuse, read conversion, cost-weighted effectiveness, and the time-to-first-token delta at three percentiles.
- A blended effective input cost per thousand tokens, computed as total input, write, read, and storage cost divided by total input tokens.
- A reconciliation between metric-derived cached tokens and the provider's billing statement.

**Quality Checkpoints**:

- Token-weighted reuse meets or exceeds 70 percent for steady-state append-only families; below 40 percent the family returns to Phase 4 before any further tuning.
- Read conversion meets or exceeds 0.75; below 0.50 the breakpoint plan is rebuilt in Step 3.1 rather than adjusted.
- Metric-derived cached tokens reconcile to billing within 2 percent; a wider gap halts savings reporting until the discrepancy is explained.

***

#### Step 5.3: Adjudicate Break-Even and Retain or Revert

**Required Actions**:

- Express each family's economics in base-input units: one uncached processing of the candidate prefix is 1 unit, a write costs the provider's write multiplier, and each later read costs the provider's read multiplier, plus any storage charge for a retained entry.
- Compare the cached plan against the uncached plan over the family's observed reuse count before expiry, and retain the configuration only where the cached plan is lower by more than the declared engineering and risk margin.
- Compute partial-prefix families on their cached and uncached regions separately, and never divide total saved cost by total request count and report the quotient as a hit rate.
- Require cost-weighted effectiveness of at least 30 percent for a retained configuration, and revert any family below 10 percent to the uncached path.
- Recompute the adjudication whenever the model, the contracted price, the retention option, the traffic cadence, or the prompt's volatility profile changes, and record the recomputation date.

**Required Outputs**:

- A per-family break-even record stating write multiplier, read multiplier, storage charge, observed reuse count, and the two plan totals.
- A retain or revert decision with the measured cost-weighted effectiveness attached.
- A recomputation trigger list naming every input whose change invalidates the adjudication.

**Quality Checkpoints**:

- Every retained family shows cost-weighted effectiveness of at least 30 percent measured over a full traffic cycle, not over a warm window alone.
- No family is retained on list prices where contracted prices differ, and no price without a version timestamp enters the calculation.
- The uncached path remains exercisable, and a reversion has been executed at least once per family before the configuration is treated as production-ready.

***

### Phase 6: Freshness Governance and Release Control

**Objective**: Bind every stable prefix to a declared staleness bound, price each context operation that would break reuse against the reuse it destroys, and gate every prompt-assembly release behind a replayed cold and warm pair.

**Owning tier**: Hybrid. The staleness bound and the release gate are deterministic; the model tier may flag suspected staleness before the bound expires and may judge whether a proposed rewrite preserves meaning, and neither judgement takes effect without deterministic confirmation.

#### Step 6.1: Declare and Enforce a Staleness Bound on the Stable Prefix

**Required Actions**:

- Declare, per cache family, the maximum age permitted for any fact carried inside the stable prefix, and derive that bound from the fastest-decaying content the prefix contains rather than from the average.
- Exclude from the stable prefix any content whose authoritative version can change faster than the declared bound, and carry it after the last marker instead, accepting that it is processed at full price on every request.
- End the epoch and rebuild the prefix when the bound expires, when an authoritative source publishes a superseding version, or when a policy, authorisation, or scope change requires it, whichever comes first.
- Treat a required deletion, revocation, or scope reduction as immediate: purge or increment the family key at once rather than waiting for an entry's natural expiry, since expiry is an optimisation timer and not a deletion mechanism.
- Record every rebuild with its trigger, so that a family whose bound is repeatedly reached early can have its partition corrected rather than its bound extended.

**Required Outputs**:

- A per-family staleness bound with the decaying content that set it named.
- An exclusion list of content held outside the stable prefix on freshness grounds.
- A rebuild log carrying the trigger and the resulting epoch increment for each rebuild.

**Quality Checkpoints**:

- No fact inside a stable prefix exceeds the family's declared bound; an exceeded bound halts further calls in that epoch rather than degrading to a warning.
- No required deletion, revocation, or scope change is deferred to preserve reuse.
- A family reaching its bound more than 3 times in one traffic cycle is re-partitioned in Phase 1 rather than granted a longer bound.

***

#### Step 6.2: Price Context Operations Against the Reuse They Destroy

**Required Actions**:

- Evaluate every operation that edits, reorders, compacts, or drops content ahead of an existing marker as a change with two costs: the tokens it saves on each future request, and the cache-read tokens it forfeits from the first post-change request onward.
- Compute the tradeoff in base-input units over the expected remaining turns within the entry's lifetime, and adopt the change only where cumulative future savings exceed the forfeited read value plus the write premium on the rebuilt prefix.
- Batch non-urgent edits to leading content into a single epoch increment rather than applying them individually, and advance a window in useful batches with hysteresis rather than one message at a time.
- Keep selection ordering deterministic with stable tie-breaking, so that a re-scored set producing the same members in a different order does not force a rebuild.
- Override the economics without calculation whenever relevance, authority, safety, or correctness requires the change, and record the forfeited reuse as a cost of correctness rather than suppressing the change.

**Required Outputs**:

- A per-operation tradeoff record stating tokens saved per future request, forfeited read tokens, expected remaining turns, and the resulting verdict.
- A batching policy for edits to leading content, with a hysteresis threshold for window advancement.
- A deterministic ordering rule for selected material, with the tie-breaking key named.

**Quality Checkpoints**:

- No operation ahead of a marker is applied without a recorded tradeoff verdict or a recorded correctness override.
- Selection reordering that changes no member composition produces no prefix change; an ordering-only rebuild indicates a nondeterministic ranking and returns to Step 2.2.
- Every correctness override is recorded with its forfeited read value, so that reuse loss is visible rather than hidden.

***

#### Step 6.3: Gate Every Prompt-Assembly Release Behind a Cold and Warm Replay

**Required Actions**:

- Replay a cold request followed by a warm request inside the entry's lifetime for every affected family before releasing any change to prompt assembly, tool registry, instruction template, memory blocks, selection, compaction, model, tokenizer, or routing.
- Require the warm request to report cache-read tokens of at least 90 percent of the predicted shared-prefix length, and block the release where it does not.
- Compare cached and uncached outputs on the release candidate, and block the release on any quality regression outside the task's declared evaluation tolerance, since a saving purchased with a behaviour change is not a saving.
- Retain an uncached control cohort in production, so that a later regression can be attributed to caching rather than to model or traffic drift.
- Store a dated copy of the provider limits, prices, retention options, and usage-field names relied on by the configuration, and re-read the provider documentation at every release, since minimums, prices, fields, and lifetimes change.

**Required Outputs**:

- A release gate record per family carrying the replayed pair, the predicted and observed read counts, and the quality comparison.
- An uncached control cohort definition with its sampling rate.
- A dated provider-behaviour snapshot bound to the release.

**Quality Checkpoints**:

- No release proceeds where the warm replay reports reads below 90 percent of the predicted shared-prefix length.
- No release proceeds on a quality regression outside declared tolerance, and no isolation or retention finding remains open at release.
- Every release carries a dated provider snapshot; a configuration resting on an undated snapshot is treated as unverified.

***

## III. Implementation Guidance for AI Agents

AI agents constructing cache-aware prompts must follow systematic protocols ensuring that prefix identity is asserted before a call rather than diagnosed after a bill, that every claimed saving traces to a provider-reported integer, and that no reuse decision overrides authority, freshness, or isolation. The following guidance translates the construction discipline into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Partition Agent**: Owns the input inventory and the volatility classification. Produces the region partition and the cache or no-cache decision per family. It may not place markers and may not modify assembly code.
2. **Assembly Agent**: Renders the request in the declared order, applies the canonical serialization, and emits the versioned tool bundle. It alone writes to the assembly path, and it may not vary ordering per request.
3. **Integrity Agent**: Computes the prefix hash and block hashes, compares them against the epoch record, and halts any call whose hash differs without an epoch increment. It holds veto authority over transmission.
4. **Placement Agent**: Computes marker positions from declared boundaries and the provider's stated limits, and derives the cache-family key. It may not add a marker after per-request content under any instruction.
5. **Accounting Agent**: Reads provider cache fields, computes the metric set, reconciles against billing, and issues the retain or revert verdict. It is the only component permitted to assert that a saving occurred.
6. **Attribution Agent**: Localises first divergences, assigns one closed-vocabulary cause per eligible miss, and routes the repair to the producing component. It may propose a candidate producer only where the diff fails to name a field.
7. **Freshness Agent**: Holds the staleness bound per family, forces epoch increments on expiry or revocation, and blocks any deferral of a required deletion. Its bound is never extended by another component.

**Evidence Boundary**: Reuse is asserted only from provider-reported cache-read token counts. Latency improvement, cost movement, prompt similarity, and model judgement are inadmissible as evidence of a hit. A family whose deployment cannot observe those counts is recorded as unverified and its savings are reported as zero.

**Workflow Execution Pattern**:

```
STATE: Pre_Transmission_Integrity_Check
INPUTS:
  1. Rendered request bytes from the Assembly Agent
  2. Epoch record with frozen prefix hash and pinned versions
  3. Breakpoint plan with marker positions and provider limits
ACTIONS:
  1. Compute prefix hash over transmitted bytes, markers excluded
  2. Compute block hash sequence over each declared region
  3. Compare prefix hash against the epoch record
  4. Verify marker positions precede all per-request content
  5. Verify eligible prefix tokens exceed provider minimum by 20 percent
VALIDATION:
  - prefix_hash == epoch_record.prefix_hash OR epoch_incremented == TRUE
  - markers_after_volatile_content == 0
  - marker_count <= provider_max_breakpoints
  - eligible_prefix_tokens >= provider_minimum * 1.20
  - family_key_dimensions_present == {tenant, region, model_version, prefix_hash}
  - raw_prefix_in_telemetry == FALSE
TRANSITIONS:
  IF all_validations_pass THEN next_state = Transmit_And_Record_Usage
  IF prefix_hash_mismatch AND change_legitimate THEN next_state = Epoch_Increment
  IF prefix_hash_mismatch AND NOT change_legitimate THEN next_state = Assembly_Repair
  IF eligible_prefix_below_minimum THEN next_state = Transmit_Uncached
  IF validation_failed THEN next_state = Construction_Error_Handling
```

**Two-Phase Action Pattern**: Emit the rendered request and its computed hashes without transmitting; confirm the validation block while no charge has been incurred; transmit only after validation passes, recording the accounting event in the same operation.

**Approval Gate**: Human authorisation is required before enabling a paid retention option on a family, before changing a data-retention mode, before permitting reuse across principals or trust domains, before sending material classified above the deployment's declared sensitivity tier through a provider cache, and before any release whose projected write premium exceeds 15 percent of the family's total input cost. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the epoch record, prefix hash, pinned versions, and family key in durable state, since a run may outlive a single working context and a rebuilt in-memory prefix is a divergence.
- Retain block hashes and token counts rather than prefix text, so that a later divergence is localisable without holding sensitive payloads.
- Write a handoff record at every context boundary naming the family key, epoch, prefix hash, marker plan, and accumulated cache metrics.
- Count the agent's own construction and hashing overhead against the family's measured saving rather than treating it as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Partition Integrity (After Phase 1)**

- **Automated Check**: Every input carries a change band; every family carries a cache or no-cache decision; every caching decision shows a shared prefix exceeding the provider minimum by at least 20 percent; the baseline covers at least 200 requests per class.
- **Agent Action on Pass**: Proceed to prefix construction.
- **Agent Action on Failure**: Halt and return the unclassified inputs or the families failing the minimum-length gate; no assembly code is changed against an incomplete partition.
- **Human Review Trigger**: A family whose material is classified above the deployment's declared sensitivity tier, or a workload where no contracted price is available.

**Checkpoint 2: Byte Stability (After Phase 2)**

- **Automated Check**: Two renderings from cold process state are byte-identical; the tool bundle hash is stable across at least 50 renderings; no per-request value appears ahead of the last marker; history is append-only across consecutive turns.
- **Agent Action on Pass**: Proceed to placement.
- **Agent Action on Failure**: Halt and return the first divergent field; a nondeterministic serializer is repaired before any marker is placed.
- **Human Review Trigger**: A tool bundle whose composition must vary by authorisation profile within one family.

**Checkpoint 3: Placement and Isolation (After Phase 3)**

- **Automated Check**: No marker follows per-request content; marker count is within the provider's maximum; the family key carries tenant, region, model version, and prefix hash; no key or label carries a secret or personal identifier; dependent fan-out is gated on warm confirmation.
- **Agent Action on Pass**: Proceed to production traffic under measurement.
- **Agent Action on Failure**: Halt; a misplaced marker produces a permanent write surcharge and is never released with a warning.
- **Human Review Trigger**: Any proposed cross-principal sharing domain, or any routing hint derived from a principal identifier.

**Checkpoint 4: Attribution Completeness (After Phase 4)**

- **Automated Check**: Every eligible miss carries exactly one closed-vocabulary cause; unattributed causes are at most 10 percent of eligible misses; every closed finding carries a replayed cold and warm pair.
- **Agent Action on Pass**: Proceed to metric adjudication.
- **Agent Action on Failure**: Reopen the findings lacking attribution and run payload diffing over the overlapping region only.
- **Human Review Trigger**: Unattributed causes above 10 percent after one diffing pass, or a divergence that recurs after a repair.

**Checkpoint 5: Economic Validity (After Phase 5)**

- **Automated Check**: Token-weighted reuse is at least 70 percent for steady-state append-only families; read conversion is at least 0.75; cost-weighted effectiveness is at least 30 percent; metric-derived cached tokens reconcile to billing within 2 percent.
- **Agent Action on Pass**: Retain the configuration and publish the metric report.
- **Agent Action on Failure**: Revert families below 10 percent cost-weighted effectiveness to the uncached path and return the remainder to Phase 4.
- **Human Review Trigger**: A billing reconciliation gap above 2 percent, or a savings claim that cannot be traced to provider-reported reads.

**Checkpoint 6: Freshness and Release (After Phase 6)**

- **Automated Check**: Every family carries a staleness bound; no fact in a stable prefix exceeds it; every release carries a replayed pair showing reads at or above 90 percent of prediction; a dated provider snapshot is attached.
- **Agent Action on Pass**: Release, retaining the uncached control cohort.
- **Agent Action on Failure**: Block the release and name the failing gate; a stale prefix is never released as a cost optimisation.
- **Human Review Trigger**: Any deferral of a required deletion or revocation, or any family reaching its staleness bound more than 3 times in one traffic cycle.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
FAMILY_KEY_CLASS:
EPOCH:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Silent Non-Caching Below the Provider Minimum**

- **Symptoms**: Markers are present and correctly ordered, no error is returned, and written tokens are reported as zero on every request; measured cost matches the uncached baseline exactly.
- **Diagnostic Steps**: Recount the eligible prefix with the target model's tokenizer, compare against the provider's stated minimum for that exact model identifier, and confirm the minimum applied is the model's own rather than one inherited from a sibling model, since minimums are not monotonic across a provider's generations.
- **Resolution Protocol**: Option A, relocate genuinely reusable instructions or examples earlier so the shared region legitimately exceeds the minimum by 20 percent. Option B, record a no-cache decision for the family and remove the markers, since an unread write is a pure surcharge. Option C, consolidate several short families into one family sharing a common preamble, where authority and isolation permit it.
- **Escalation Trigger**: Padding is prohibited outright and this class is never resolved by adding tokens; a family that cannot reach the minimum through relocation after 2 attempts is recorded as no-cache.

**Error Type 2: Write on Every Request With No Corresponding Read**

- **Symptoms**: Written tokens appear on every request while read tokens remain at or near zero; read conversion sits below 0.50; blended input cost exceeds the uncached baseline.
- **Diagnostic Steps**: Determine whether the marker sits after per-request content, whether the automatic placement has walked onto a volatile block, whether each request belongs to a distinct family because the key includes a per-request dimension, and whether concurrent requests are all writing the same entry simultaneously.
- **Resolution Protocol**: Option A, move the marker to the last block of the shared region and re-replay the cold and warm pair. Option B, switch from automatic to explicit placement where automatic placement lands after volatile content. Option C, remove the per-request dimension from the family key, or gate the fan-out on warm confirmation where the cause is concurrency.
- **Escalation Trigger**: A configuration paying a write premium on more than 20 percent of requests for 2 consecutive traffic cycles is reverted to the uncached path pending redesign.

**Error Type 3: Prefix Divergence From an Upstream Producer**

- **Symptoms**: Read tokens collapse abruptly at a release boundary or drift downward over days; the prefix hash differs from the epoch record; written tokens approach full request size.
- **Diagnostic Steps**: Confirm compatibility dimensions first, then compare block hashes against the most recent reading request, then diff bytes inside the single divergent block over the overlapping region only, with markers stripped.
- **Resolution Protocol**: Option A, repair the producer where the divergence is unintended: fix the serializer, pin the template, relocate the injected value. Option B, increment the epoch and accept one cold write where the change is legitimate and must stand. Option C, partition the family where the change applies to only part of the traffic, so that unaffected traffic keeps its entry.
- **Escalation Trigger**: A divergence recurring after repair, or an unattributed rate above 10 percent after one diffing pass, escalates for assembly-path review; this class is never resolved by retrying the same request.

**Error Type 4: Reuse Purchased With Stale Content**

- **Symptoms**: Reuse metrics are healthy while task quality declines; outputs cite superseded policy, revoked entitlements, or outdated reference material; the affected content sits inside the stable prefix.
- **Diagnostic Steps**: Compare each fact inside the stable prefix against its authoritative source version and its declared staleness bound, and identify whether the bound was exceeded, was never declared, or was set from the average rather than the fastest-decaying content.
- **Resolution Protocol**: Option A, end the epoch immediately, rebuild the prefix, and accept the cold write. Option B, relocate the fast-decaying content behind the last marker permanently, accepting full-price processing on every request. Option C, shorten the family's staleness bound and re-partition in Phase 1 where the bound is repeatedly reached early.
- **Escalation Trigger**: Any observed use of revoked, deleted, or superseded content escalates immediately as a correctness incident; reuse is never restored before the content is corrected, and a shorter bound is never traded for a higher reuse figure.

**Error Type 5: Unauthorised or Over-Broad Cache Sharing**

- **Symptoms**: A family key omits an isolation dimension; identical text from two principals resolves to one entry; a routing hint or metric label carries a principal identifier; retention behaviour does not match the declared policy.
- **Diagnostic Steps**: Enumerate the family key's dimensions against the declared isolation domain, inspect keys and labels for identifiers, and confirm the provider's stated isolation boundary and retention behaviour against the dated snapshot bound to the release.
- **Resolution Protocol**: Option A, add the missing dimension and increment the family key, forcing a cold write across the affected traffic. Option B, disable reuse for the affected material and route it uncached. Option C, restrict the sharing domain to reviewed content only, with a recorded approval naming that content.
- **Escalation Trigger**: Any suspected cross-principal reuse of non-reviewed content halts the family immediately and escalates; this class is never resolved by monitoring and is never traded against a cost target.

**Error Type 6: Routing and Expiry Losses That Construction Cannot Fix**

- **Symptoms**: Reads are intermittent at unchanged prefix bytes; misses cluster after traffic-cadence changes, deployments, or load spikes; entry age at miss clusters near the retention limit.
- **Diagnostic Steps**: Separate expiry from routing by comparing entry age at miss against the retention limit, and compare miss clustering against deployment and load timelines rather than against prompt changes.
- **Resolution Protocol**: Option A, supply the provider's routing hint keyed on the stable portion of the family key, and shard a hot key that concentrates load. Option B, extend the retention option where the break-even in Step 5.3 supports the higher write premium. Option C, warm the family on a schedule just inside the retention limit where traffic gaps exceed it, subject to the warm-up cost ledger.
- **Escalation Trigger**: Routing affinity never overrides overload protection or failover; where honouring affinity would breach a latency objective, the miss is accepted and recorded, and a persistent routing loss above 25 percent of eligible requests returns the family to break-even adjudication.

**Troubleshooting Decision Tree**:

```
EXPECTED READ DID NOT OCCUR
├─ NO ENTRY WAS EVER WRITTEN
│   ├─ Written tokens zero, markers present → Recount prefix; below minimum → record no-cache
│   ├─ Marker sits after volatile content → Move marker to end of shared region
│   └─ Fan-out issued before warm confirmation → Gate release on first response
├─ ENTRY WRITTEN BUT NEVER READ
│   ├─ Family key carries a per-request dimension → Remove dimension; re-key
│   ├─ Automatic placement walked onto volatile block → Switch to explicit placement
│   └─ Turn appended past the backward search window → Add intermediate marker every 15 positions
├─ ENTRY EXISTED BUT PREFIX DIVERGED
│   ├─ Compatibility dimension changed → Attribute to model, region, or adapter; not to content
│   ├─ Divergence inside shared region → Repair producer; do not patch the rendered output
│   └─ Change legitimate → Increment epoch; accept one cold write
├─ REUSE HEALTHY BUT OUTPUT WRONG
│   ├─ Stale fact inside stable prefix → HALT; end epoch; rebuild before restoring reuse
│   └─ Revoked or deleted content still served → HALT; purge and re-key immediately
├─ ISOLATION DEFECT
│   ├─ Missing key dimension → HALT family; add dimension; re-key
│   └─ Identifier in key, hint, or label → Remove; rotate the hashing key
└─ INFRASTRUCTURE LOSS
    ├─ Entry age near retention limit → Extend retention or schedule a warm, per break-even
    └─ Miss clusters with load or deploys → Supply routing hint; accept miss over SLO breach
```

### D. Performance Metrics and Continuous Learning

**Reuse Metrics**:

- **Token-weighted reuse**: Cache-read tokens over eligible prefix tokens (target: at least 70 percent for steady-state append-only families; below 40 percent triggers the Phase 4 audit).
- **Read conversion**: Read tokens over the sum of read and write tokens (target: at least 0.75; below 0.50 indicates prefixes written and never read).
- **Attribution completeness**: Eligible misses carrying exactly one closed-vocabulary cause (target: 100 percent, with unattributed causes at most 10 percent).
- **Prefix stability**: Calls whose prefix hash matches the epoch record without an epoch increment (target: 100 percent; any shortfall is an assembly defect rather than a tuning opportunity).

**Economic Metrics**:

- **Cost-weighted effectiveness**: Uncached counterfactual input cost minus actual input, write, and storage cost, over the counterfactual (target: at least 30 percent for a retained family; below 10 percent forces reversion).
- **Write premium share**: Write cost over total input cost (target: no more than 15 percent; above that share the breakpoint plan is rebuilt).
- **Blended effective input cost**: Total input, write, read, and storage cost over total input tokens, per thousand tokens (target: below the uncached baseline at matched output quality).
- **Billing reconciliation gap**: Absolute difference between metric-derived and billed cached tokens over billed cached tokens (target: no more than 2 percent; a wider gap suspends savings reporting).

**Latency and Freshness Metrics**:

- **Time-to-first-token delta**: Matched cold minus warm time to first token at equal prefix length, suffix length, model, route, and load bucket, reported at the 50th, 95th, and 99th percentiles (target: a positive delta at the 95th percentile, with no regression at unchanged read counts).
- **Epoch rebuild rate**: Epoch increments per traffic cycle per family (target: no more than 3; a higher rate indicates the partition, not the bound, is wrong).
- **Staleness breaches**: Facts observed inside a stable prefix past the declared bound (target: 0; a single breach is a correctness incident).

**Log-Pattern Failure Detection**: Written tokens on every request with flat read tokens indicate a marker after volatile content. Token-weighted reuse falling while request hit rate holds steady indicates that reads have moved to short prefixes and the large ones are missing. A new first-divergence block identifier appearing at a release boundary indicates an upstream producer changed. Rising misses at unchanged prefix bytes after a load-balancer change indicate a routing loss rather than a construction defect. Entry age at miss clustering near the retention limit indicates a cadence problem, not a prefix problem. Reuse improving while task quality declines indicates a staleness breach and is investigated before the saving is reported.

**Learning and Adaptation Mechanisms**:

- **Cause-ranked backlog**: Rank open invalidation causes by lost cache-read token value rather than event count, and retire the highest-value cause first.
- **Producer hardening**: Where the same producer appears in 2 or more attributed divergences, fix determinism at that producer rather than adding compensating logic to the assembly path.
- **Threshold recalibration**: Recompute every threshold stated here against the deployment's own observed distributions; the values given are operable defaults, not measured constants.
- **Snapshot refresh**: Re-read provider limits, prices, retention options, and usage-field names at every release, and treat a configuration resting on a snapshot older than one release cycle as unverified.

**Human-in-the-Loop Boundaries**: Enabling a paid retention option, changing a data-retention mode, widening a sharing domain across principals or trust domains, sending material above the declared sensitivity tier through a provider cache, and extending a staleness bound are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how a request is assembled rather than what the request is about. Its phases hold wherever a workload issues repeated model calls that share a leading region, a provider reports how much of that region was reused, and the shared region carries content whose freshness matters.

### 4.1 Cross-Domain Application Patterns

**Regulated financial operations**: The stable prefix carries a control catalogue, jurisdictional rules, and a fixed tool bundle for ledger and reference lookups, all of which change on a release cadence rather than per request. The staleness bound is set by the fastest-decaying element, typically a rate table or an entitlement list, so that element is deliberately excluded from the prefix and processed at full price on every request. Cross-principal sharing is refused by default because two clients' prompts can be textually identical while their entitlements differ, and the family key therefore carries the client boundary even where it costs reuse. The break-even calculation is performed on contracted rather than list prices, since negotiated pricing changes the read and write multipliers that govern the whole adjudication.

**Clinical decision support**: The prefix carries protocol text, formulary references, and a stable instruction set; patient-specific material never enters it, both because it changes per request and because it must not be written to a provider-side entry. The staleness bound is short and enforced hard, since a superseded protocol reused from an entry is a correctness failure rather than a saving. Release gating is strict: the cold and warm replay is accompanied by an output comparison, because a configuration that reuses correctly but changes recommendation text is rejected regardless of its economics.

**Software engineering agents**: This is the highest-value common case. The loop carries a long instruction set, a frozen tool bundle, accumulated conversation and tool results, and a small new observation per turn, so the reusable fraction grows across a session. The dominant failure is a tool bundle rebuilt per request or a capability-discovery result reordered between turns, either of which invalidates every following region. Compaction and window advancement are priced against the reads they forfeit, and the saving is reported as removed input prefill only, never as a proportion of total request cost, since output-token generation is untouched.

**Customer operations and support**: Traffic is bursty, sessions are short, and many requests share one policy corpus across many principals. The design question is whether the corpus can be shared beyond one principal at all, which is an isolation decision rather than an economic one. Where sharing is refused, the corpus is still cached per principal and the reuse profile is driven by session length rather than by corpus size. Warming is targeted at the small number of families with forecast reuse, never at every combination of principal and template.

**Scientific and archival research assistance**: Shared corpora are large, change rarely, and are queried repeatedly, which is the most favourable profile the method encounters. The risks invert: the staleness bound is long, so the practical hazard is an entry outliving a corrected source rather than an entry expiring too soon. Explicit retention with a longer lifetime is often justified here, but only after the storage charge some providers apply to retained content is entered into the break-even calculation, since a long-lived entry on a short batch can cost more than it saves.

### 4.2 Scale, Risk, and Sensitivity Adaptation

- **Low-volume or exploratory workloads**: Run Phase 1 and record a decision, then stop. Below roughly 200 requests per family per traffic cycle the measurement machinery costs more than the reuse it would confirm, and an unverified saving is not a saving.
- **High-volume steady traffic**: Apply every phase, hold the full metric set, and prefer the shortest retention option, since continuous traffic refreshes an entry on its own and a longer lifetime buys only a higher write premium.
- **Bursty traffic with long idle gaps**: The retention option and the warming schedule become the governing decisions rather than prefix construction, which is already correct. Adjudicate a scheduled warm against a longer retention option on measured gap length rather than on preference.
- **High-sensitivity material**: Treat the cache boundary as a data boundary. Refuse cross-principal sharing, keep identifiers out of keys and labels, confirm the provider's stated retention behaviour against a dated snapshot, and accept a lower reuse figure as the cost of the boundary. Where a timing difference between hit and miss is itself informative to an observer, partition rather than obscure, since partitioning removes the channel and jitter only widens it.
- **Multi-provider or gateway deployments**: Run the method independently per provider and per model. Entries, token accounting, retention semantics, minimums, and usage-field names are never portable across providers, models, versions, regions, or adapters, and a metric aggregated across two providers hides which one is failing.

***

## V. Limitations and Considerations

**The mechanism is not reachable and the surrogate is not equivalent**: This guide governs whether a cache is hit, not how a cache behaves. Allocation, eviction, precision, and placement remain properties of an inference runtime no agent can address, so a workload whose real constraint is serving capacity will not be helped by anything here. The mitigation is the explicit scope statement in Section 1.2 and the entry decision in Step 1.3, which record a no-cache verdict rather than producing construction advice for a problem construction cannot solve.

**A hit can never be guaranteed**: Providers route across machines, expire entries on a timer, apply minimum prefix lengths silently, and change all three without notice. A correctly rendered prefix can still miss. The mitigation is that every saving is measured in Phase 5 from reported counts rather than predicted, and that Step 5.3 requires the uncached path to remain exercisable and to have been exercised at least once before a configuration is treated as production-ready.

**Reuse trades against freshness, and a stale prefix is a defect rather than a saving**: The same property that makes a prefix cacheable, its unchanging bytes, makes it a place where superseded content can persist. A family showing excellent reuse metrics while serving a revoked entitlement or a withdrawn protocol has not saved money; it has produced wrong output more cheaply. The mitigation is the staleness bound in Step 6.1, enforced as a halt rather than a warning, together with the rule that a required deletion or revocation is executed immediately and never deferred to preserve an entry.

**Vendor figures are vendor-reported, model-specific, and dated**: The minimum prefix lengths, marker limits, backward-search bounds, retention options, price multipliers, and usage-field names described in this guide are behaviours providers publish about particular models at particular times. They are not universal properties of prompt caching, they differ between models from the same provider, and at least one provider's minimums are not monotonic across its own generations. The mitigation is Step 6.3, which binds a dated provider snapshot to every release and requires the documentation to be re-read rather than recalled.

**Most numeric thresholds here are deployment defaults**: The 20 percent margin above a provider minimum, the 70 percent token-weighted reuse target, the 0.75 read conversion floor, the 30 percent cost-weighted retention threshold, the 15 percent write-premium ceiling, the 10 percent unattributed-cause allowance, the 2 percent billing reconciliation tolerance, the 90 percent release-gate threshold, and the 200-request baseline size were chosen to be operable on first deployment rather than derived from a measured property of any particular workload. The multipliers governing break-even and the provider limits governing placement are the exception: those are transcribed from provider documentation and were confirmed against the providers' own pages during conversion. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute its thresholds against observed distributions.

**Measurement machinery has a cost of its own**: Hashing every prefix, retaining block hashes, logging a full accounting event per request, and replaying cold and warm pairs at every release consume compute, storage, and engineering attention. On low-volume families that cost exceeds the reuse it verifies. The mitigation is the scale adaptation in Section 4.2, which stops the method at Phase 1 below roughly 200 requests per family per cycle, and the requirement in Section III.A that construction overhead is counted against the measured saving rather than treated as free.

**Instrumentation carries its own exposure**: A record detailed enough to localise a divergence is detailed enough to leak the content that diverged. The mitigation is the fingerprint discipline in Step 2.3 and Step 5.1: keyed hashes scoped to the organisation, block-level hashes and token counts in place of prefix text, rotation under a documented migration, and raw payload access only under restricted, audited retrieval for the duration of an investigation.

**Cache boundaries are trust boundaries and reuse pressure works against them**: Every isolation dimension added to a family key reduces reuse, so there is a standing incentive to remove one. Published research has reported statistical evidence of cross-user cache sharing at API providers, and timing differences between hits and misses have been demonstrated as an information channel in shared serving. Current provider documentation may assert stronger isolation than a given study observed. The mitigation is to treat documentation as the contract, to partition by principal and trust domain by default, to require a recorded approval naming the reviewed content before any cross-principal family exists, and to design sensitive workloads so that they remain correct even if an implementation's sharing behaviour changes.

**Structural conformance is not a good prompt**: A family can satisfy every checkpoint here and still carry an instruction set that produces poor output. This method optimises the cost of processing a prefix; it says nothing about whether that prefix should contain what it contains. No checkpoint in this guide substitutes for evaluation of the prompt's content against the task.

***

## VI. Conclusion and Summary

Cache-aware prompt construction is an assembly discipline before it is a cost optimisation. The mechanism it exploits sits inside an inference runtime and is unreachable, but the property that governs whether the mechanism engages, exact identity of the leading bytes, is produced entirely by the caller. An agent that renders least volatile content first, serialises deterministically, freezes its tool bundle, hashes what it transmits, and compares that hash before every call has already captured most of the available benefit. An agent that places markers without doing those things has bought a write premium and nothing else.

Three claims recur in this method and each is a measurement rather than an assumption. Reuse happened only where the provider reports read tokens. A saving occurred only where the cost-weighted comparison against a dated uncached counterfactual says so. A prefix is still correct only where every fact inside it sits within its declared staleness bound. A deployment that asserts any of the three without its evidence is reporting an impression, and impressions in this method are systematically optimistic, because a caching failure is silent: requests keep succeeding and only the bill changes.

A team adopting the method should instrument before restructuring. Capture a baseline, measure the shared region and the reuse interval, and record a cache or no-cache decision per family; several families will correctly receive a no-cache verdict, and recording that verdict is a successful outcome rather than a failure to optimise. Then fix ordering and determinism, which are free and which no marker can compensate for. Only then place markers, key the families, and gate releases on a replayed pair. The two decisions that must never be automated at any stage are widening a sharing domain and extending a staleness bound, because each converts a cost improvement into a correctness or isolation risk that the metric set is not built to detect.

**Key Success Factors**:

- **Construction before configuration**: Ordering, determinism, and append-only history govern reuse; a marker placed on an unstable prefix improves nothing and costs a premium on every request.
- **Byte identity asserted, not assumed**: The prefix hash is computed over transmitted bytes and compared before every call, so a divergence halts a request rather than surfacing later as an unexplained charge.
- **Provider counts as the only evidence**: Reuse, savings, and release readiness rest on reported cache-token integers reconciled to billing, never on latency impressions, prompt similarity, or model judgement.
- **Weight by tokens and by cost**: Ten reads on a short prefix can be worth less than one missed read on a long one, so request hit rate is a routing symptom and cost-weighted effectiveness is the verdict.
- **Freshness outranks reuse**: A stable prefix carrying superseded content is a correctness defect, and a required deletion, revocation, or scope change is executed immediately at the price of a cold write.
- **Isolation is not negotiable against economics**: Tenant, trust domain, region, model version, and adapter enter every family key, and cross-principal sharing exists only for reviewed content under recorded approval.

By following this guide, AI agents can construct requests whose reusable region is stable by design, prove reuse from evidence a provider actually reports, and surrender that reuse deliberately whenever freshness, authority, or isolation requires it.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source, re-scoped from key-value cache engineering to the agent-layer discipline of cache-aware prompt construction. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, with titles and locations reproduced rather than reconstructed; where a bare label is all the source carried, the bare label is reproduced. Two entries were retrieved and confirmed during this conversion and are marked as such. The remainder were not independently re-verified. All references to self-hosted serving infrastructure carried by the prose source were removed with the material they supported, since that material sits below the agent layer.

**Corpus pointers**:

- `KV Cache and Prompt Caching: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the exact-prefix reuse rule, the volatility ordering, the tool-definition churn analysis, the baseline, restructuring, invalidation-audit, break-even, routing and warming, and measurement loops, the multi-turn decomposition, the cross-operation invalidation economics, the per-request log field inventory, the metric definitions, and the cache-sharing and timing-channel controls. Its self-hosted serving track was excluded as unreachable from the agent layer.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — owns stage transitions, epoch boundaries, initialisation records, and prefix budgeting across a run. The terms stable prefix and epoch are used here in that guide's sense; it states when a prefix must be rebuilt, and this guide states what that rebuild costs in forfeited reuse.
- `advanced_task_guides/context-management/guide_ContextEditingAndToolResultClearing.md` — owns the clearing of tool results and other in-place context edits. Its edits fall ahead of an existing marker, so the tradeoff pricing in Step 6.2 governs when they are applied.
- `advanced_task_guides/context-management/guide_HierarchicalContextArchitecture.md` — owns scope, inheritance, and instruction precedence. Its precedence rules are authoritative over the volatility ordering in Section 1.3 wherever the two conflict.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — owns tenant, trust, and capability boundaries. Its controls are the source of the isolation dimensions required in the cache-family key in Step 3.2.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — owns admission and ranking of candidate material. Its deterministic tie-breaking is what prevents an ordering-only change from forcing a prefix rebuild.
- `advanced_task_guides/context-management/guide_ContextCompression.md` and `advanced_task_guides/context-management/guide_SemanticContextCompression.md` — own representation change and fidelity. Compaction replaces a leading region and therefore forces a cold write, which Step 6.2 prices against the tokens the replacement saves.
- `advanced_task_guides/context-management/guide_SlidingWindowContext.md` — owns resident-set policy and window advancement. Its hysteresis rules bound how often window movement ends an epoch.
- `advanced_task_guides/context-management/guide_ContextMemoryBlocks.md` — owns agent-visible prompt-resident state. A block edit ahead of a marker is one of the closed-vocabulary invalidation causes in Step 4.3.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — owns durable writes and provenance. It is the authority for the rule in Section 1.2 that a provider cache is never a memory store and never evidence of deletion.
- `advanced_task_guides/context-management/guide_ContextStateMachines.md` — owns legal transitions and recovery. Cache write, read, expiry, and bypass are observations and effects within its states, never states of their own.
- `advanced_task_guides/context-management/guide_ContextEngineeringFrameworks.md` — owns framework selection, the framework-free baseline, and the abstraction-leak and payload-diff audit at a library boundary. The payload diffing that Step 4.3 makes mandatory once unattributed causes exceed their threshold is that guide's procedure, and a serialization nondeterminism introduced by an assembly library is diagnosed there rather than repaired here.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — owns ingestion, retrieval, reranking, and prompt assembly end to end. This guide constrains that assembly's ordering wherever cache economics apply.

**External references**:

*Provider prompt-caching behaviour and pricing*

1. Anthropic, *Anthropic prompt caching* — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
2. Anthropic, *Anthropic API and data retention* — https://docs.anthropic.com/en/docs/build-with-claude/zero-data-retention
3. OpenAI, *OpenAI prompt caching* — https://platform.openai.com/docs/guides/prompt-caching (retrieved and confirmed during conversion; the minimum visible cacheable prefix, the cached-token usage field, the routing-key semantics, the write and read multipliers, the retention options, and the per-request write and read breakpoint limits were checked against the live page, which now redirects to a relocated address)
4. Google, *Gemini context caching* — https://ai.google.dev/gemini-api/docs/caching (retrieved and confirmed during conversion; implicit caching enabled by default on the stated model generations, the per-model minimum input token thresholds, and the cached-token usage field were checked against the live page)
5. Google, *Gemini explicit context caching* — https://ai.google.dev/gemini-api/docs/generate-content/caching
6. Google, *Gemini API pricing page* — https://ai.google.dev/gemini-api/docs/pricing

*Serving-side mechanism, retained only as background for Section 1.2*

7. PagedAttention paper — https://arxiv.org/abs/2309.06180
8. POD-Attention paper — https://arxiv.org/abs/2410.18038

*Cache sharing as an information channel*

9. *The Early Bird Catches the Leak* — https://arxiv.org/html/2409.20002v1
10. *Auditing Prompt Caching in Language Model APIs* — https://arxiv.org/abs/2502.07776
