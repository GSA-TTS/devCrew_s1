# Context Write Patterns

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context write patterns constitute the task family of moving state out of a model's context window into durable storage, so that the window carries a reference instead of the content and the state survives a context boundary. This guide provides AI agents with a structured protocol governing the write decision itself, the format and addressability contract that makes an externalized item retrievable without a full scan, the durability confirmation that must return before the in-context copy is released, the supersession and compaction rules that stop an evolving state from accumulating near-identical records, and the read-back verification and utilization measurement that establish whether a write ever repaid its cost. It specifies a default-deny write policy in which every write declares a named reader and a named read occasion, an identifier-stability rule that keeps one logical item addressable across all its versions, numeric triggers for offload, compaction, staleness, and retirement, and an execution-tier partition assigning proposal to the model tier and identifier assignment, serialization, durability confirmation, supersession bookkeeping, and token accounting to the deterministic tier. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that externalization reduces window pressure without losing work or creating retrieval noise.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Externalization**: The governed movement of content from the context window to a durable store, replacing the content in the window with a reference. Externalization is a write plus a release; a write without a release saves nothing, and a release without a confirmed write loses work.

**Context window**: The token sequence accepted by one model call. It is a transport, not a store. It retains nothing after the call and its capacity is address space rather than memory.

**Context boundary**: Any point at which the current window ends and a later call cannot see what preceded it: a compaction, a session close, a process restart, a subagent handoff, a tool-result clearing pass, or a scheduled continuation. Surviving a boundary is the only reason a write pattern exists.

**Write candidate**: One bounded unit of window content proposed for externalization, carrying its extent, its proposed class, its proposed reader, its proposed read occasion, and its measured token cost.

**Write class**: The declared category governing a candidate's threshold, lifetime, addressability requirement, and confirmation strength. The five classes are scratch state, task ledger, artifact offload, structured note, and durable memory proposal.

**Named reader**: The specific consumer declared to require the written content later: the same agent after a boundary, a named subagent, a named downstream phase, a human reviewer, or an audit process. "Someone might need it" is not a named reader.

**Read occasion**: The declared condition under which the named reader will retrieve the content, expressed as an event, a phase entry, a query pattern, or a validity window. A write whose read occasion cannot be stated is not written.

**Write handle**: The compact in-window replacement for released content, comprising the stable identifier, the purpose line, the shape descriptor, the size and version, and the retrieval instruction. The handle is what the window carries after the release.

**Stable identifier**: The opaque, tenant-scoped name of one logical written item, assigned by the deterministic tier and never changed for the life of the item. Versions change; identifiers do not.

**Addressability**: The property of a written item being retrievable by identifier, by declared purpose, or by a declared field, without reading the item in full and without scanning the store. An unaddressable write is a leak, not a save.

**Selectable header**: The bounded, structured prefix of a written item carrying identifier, class, purpose, reader, read occasion, schema version, extent, observation time, expiry, and supersession links. Selection reads the header; the body is read only after selection.

**Canonical store**: The single authoritative system holding immutable versions, current pointers, tombstones, provenance, and idempotency claims for written items. Every other store is derived from it.

**Derivative**: Any store rebuildable from the canonical store, including lexical indexes, vector indexes, graph projections, summaries, and caches. A derivative is never authoritative and never the source of a durability guarantee.

**Durability receipt**: The deterministic tier's confirmation that a write is committed and readable after the boundary, carrying the identifier, the committed version, the commit sequence, the store location, and the derivative status of every projection the read occasion depends on. The receipt is the only evidence that permits release.

**Release**: The removal of externalized content from the window, leaving the write handle in its place. Release is a separate operation from the write and is permitted only after the receipt returns.

**Residency copy**: Content held simultaneously in the window and in the store. A residency copy is the safe state between the write and the release, and it is the state that must be maintained when a receipt does not return.

**Supersession**: The replacement of one version of a logical item by a newer authoritative version under the same identifier. The superseded version leaves the current pointer immediately and survives only as lineage.

**Write series**: The ordered set of versions committed under one identifier. A write series that grows without compaction is the mechanism by which later reads retrieve an obsolete version.

**Write amplification**: The number of physical durable mutations, embedding calls, index updates, and queue messages caused by one logical externalization. Amplification is the cost side of the write decision.

**Staleness**: The condition of a read-back returning a version whose expiry has passed or whose validity interval no longer covers the read occasion. Staleness is detected against declared times, not inferred by judgement.

**Utilization**: The proportion of written items that a named reader actually retrieved at or before the declared read occasion. Utilization is the measurement that closes the loop on the write decision.

**Handoff manifest**: The bounded package assembled at a context boundary, listing every live write handle, the protected atoms that may not be externalized, the next action, and the state version, and requiring explicit acknowledgement by the receiver.

**Protected atom**: A state element that must remain resident in the window and may never be externalized alone: the current objective, the standing constraints, the active step, the unresolved error state, and the outstanding approvals. Protected atoms may be mirrored to the store but are never released from the window.

**Terminal state**: A declared outcome that ends a write operation: committed, released, retained, rejected, quarantined, superseded, or degraded. An operation ending in none of these is a defect.

### 1.2 Scope Boundary Against the Sibling Categories

Context management offers four operations against a window under pressure: writing state out, selecting what comes back in, compressing what stays, and isolating what never shares a window. The category's umbrella guidance treats those four as a selection ladder and states which operation a given pressure calls for. This guide does not restate that ladder. It owns the write operation in depth and assumes the ladder has already selected it.

**What this guide owns**: The decision to move content out of the window; the declaration of a named reader and a read occasion; the format and addressability contract a written item must satisfy; the durability confirmation that permits release of the in-context copy; identifier stability and supersession across a write series; the numeric triggers for offload, compaction, staleness, and retirement; read-back verification; token accounting that quantifies what the write saved; and failure handling across context boundaries.

**What the memory-management category owns**: The semantics of the durable store itself. Record schemas and their admission gates, episode boundaries and trajectory capture, semantic claim modelling and identity resolution, consolidation of many episodes into fewer durable records, promotion gates and confidence ceilings, retention classes, tombstone and erasure mechanics, forgetting policy, and the residency and eviction rules of a bounded working state are stated there. This guide supplies the reason content leaves the window and the contract for moving it; those guides supply what happens to it once it is a record.

**How the boundary is enforced in practice**: A write in this guide terminates at the durable store's admission interface and does not reach past it. Where a durable memory proposal is the write class, this guide's obligation ends when the proposal is submitted with its provenance and its receipt returns; whether the proposal is admitted, at what confidence, under which retention class, and with which supersession semantics is decided by the memory-management contract. No admission threshold, consolidation rule, or retention period from that category is restated here, and no window-side decision is delegated to it.

**Composition rule**: An agent externalizing state loads this guide for the write decision and the release contract, and the relevant memory-management guide for the store's behaviour. Where the two appear to conflict on whether content may be released, this guide holds, because release is a window operation and its failure loses work that no store policy can recover.

### 1.3 The Execution-Tier Partition

Every unit of work in an externalization belongs to exactly one tier. The partition is what makes a write auditable and a release safe.

**Deterministic tier**: Software, storage APIs, serializers, and validators own identifier assignment, canonical serialization and content hashing, schema and header validation, the commit transaction, durability confirmation and receipt emission, read-back probing, supersession bookkeeping and current-pointer advancement, write-series compaction, expiry enforcement, derivative watermark tracking, the token accounting that computes what the release saved, retry classification, and telemetry emission. These require exactness, reproducibility, and auditability that model inference does not supply. A deterministic result must reproduce on replay of the same inputs; where it does not, it is a defect rather than a judgement.

**Model tier**: Model inference owns deciding what is worth writing, delimiting the candidate's extent, naming the reader and the read occasion, classifying the write class, and composing the summary or note written in place of the raw content. These require open-vocabulary judgement and synthesis that no deterministic rule covers. The model tier produces proposals; it never produces authority and never produces a durability guarantee.

**Hybrid tier**: Externalization as a whole is hybrid in one direction: the model proposes a write and the deterministic tier commits it, confirms it, and returns a receipt. Retirement is hybrid in the other direction: software retrieves the utilization record for a write class and the model adjudicates whether a low-utilization class carries a reader the measurement failed to observe.

**Authority on disagreement**: The deterministic tier holds authority in every disagreement, without exception. Where a model asserts that content was saved and no receipt exists, the content was not saved and the in-context copy is retained. Where a model proposes an identifier, the proposal is discarded and an identifier is assigned. Where a model reports a token saving, the accounting figure governs. Where a model judges a stale record current, the expiry governs.

**The prohibited delegations**: The model never assigns an identifier, never declares a write durable, never authorizes a release, never advances a current pointer, never deletes a superseded version, and never computes the saving that justifies its own write. A deployment in which any of these reaches the model tier can lose work silently, because the only component that knows whether the store accepted the write is the one that talked to the store.

### 1.4 The Two Origins of Write-Path Loss

Two distinct failures account for most damage on this path, and they pull in opposite directions.

**The unread write**: Content is externalized that no reader ever retrieves. It costs a commit, an index update, storage, and, most damaging, retrieval noise: later selections must discriminate against it, and a near-duplicate of a live item can be selected in place of the live one. The unread write saves nothing, because the window pressure it relieved would have been relieved by discarding the content outright. The countermeasure is the read-occasion declaration in Step 1.1 and the utilization measurement in Step 5.2, which retire a class whose reads never arrive.

**The premature release**: The in-context copy is discarded before durability is confirmed. The window then holds a handle to content that is absent, partially written, or visible only in a derivative that has not caught up. This failure is unrecoverable, because the only copy was in the window and the window is gone. It is also silent at the moment it occurs, surfacing one boundary later as a handle resolving to nothing. The countermeasure is the receipt requirement in Step 3.2 and the residency rule: content remains resident until a receipt names its committed version, and a failed confirmation ends the operation in the retained terminal state rather than the released one.

**Why both must be controlled together**: Tightening the write decision alone raises the rate at which needed state is discarded rather than written. Tightening the release alone leaves the window carrying residency copies that defeat the purpose of writing. The framework in Section II holds both: the decision gate bounds what is written and the receipt gate bounds when it is released, and neither is permitted to compensate for the other.

***

## II. Operational Framework: Verified Externalization of Context State Across Boundaries

The framework assumes a write operation has been selected for a specific unit of window content. Phases 1 through 3 form the write path proper and run in order for every candidate. Phase 4 runs whenever a written item changes. Phase 5 runs on a schedule independent of any single write. Phase 6 runs at every context boundary and on every detected write-path fault.

### Phase 1: Write Decision and Read-Occasion Declaration

**Objective**: Decide whether a unit of window content is written out at all, and bind every accepted write to a named reader, a named read occasion, and a class budget, so that content never read back is never written.

#### Step 1.1: Apply the Externalization Test

**Required Actions**:

- Delimit the candidate as a contiguous unit of window content with a stated start, end, and measured token cost; a candidate spanning unrelated subjects is split before evaluation.
- Test durability need first: confirm the content must survive at least 1 named context boundary. Content needed only within the current window is retained, not written.
- Name at least 1 specific reader and at least 1 specific read occasion, each stated as an identified consumer and an identified triggering event, phase entry, query pattern, or validity window.
- Estimate the externalization ratio as candidate tokens divided by projected handle tokens, and reject the candidate where the ratio falls below 4 to 1.
- Confirm the content is not reconstructible more cheaply than it is retrievable: where an authoritative source can regenerate it for less than the projected retrieval cost, record the source reference and discard the content instead.
- Confirm the candidate is not a protected atom; protected atoms may be mirrored but never released, and a mirror is recorded as such rather than as an externalization.

**Externalization Test Gates**:

| Gate | Pass condition | Action on failure |
| :-- | :-- | :-- |
| Durability need | Content must survive at least 1 named boundary | Retain in window; record no-write with reason |
| Named reader | At least 1 identified consumer declared | Reject; a write with no reader is prohibited |
| Read occasion | At least 1 event, phase, query, or validity window declared | Reject; record as unstatable occasion |
| Externalization ratio | Candidate tokens divided by handle tokens at or above 4 to 1 | Reject; the handle costs more than it saves |
| Cheaper reconstruction | No authoritative source regenerates it below retrieval cost | Discard content; store the source reference only |
| Protected-atom status | Candidate is not a protected atom | Mirror without release; record as a mirror |

**Required Outputs**:

- A candidate record carrying extent, measured token cost, projected handle cost, and computed externalization ratio.
- A reader and read-occasion declaration naming the consumer and the triggering condition for each.
- A gate result set with a pass or fail verdict and a reason code per gate.

**Quality Checkpoints**:

- Every accepted candidate carries at least 1 named reader and at least 1 named read occasion; a candidate carrying neither is rejected before any store is contacted.
- The externalization ratio is computed from measured token counts, never estimated by the proposing model; an uncomputed ratio blocks the write.
- No protected atom appears in the accepted set; a protected atom found there halts the operation and is reclassified as a mirror.

***

#### Step 1.2: Classify the Write Class and Bind Its Budget

**Required Actions**:

- Assign exactly 1 write class from scratch state, task ledger, artifact offload, structured note, and durable memory proposal; a candidate matching two classes is split.
- Apply the class offload trigger: artifact offload fires automatically at 20,000 tokens for a single tool result or artifact, and window-pressure offload fires at 85 percent of the model's input capacity.
- Set the class lifetime: scratch state expires at task close, task ledger at task close plus the declared audit window, artifact offload at 24 hours by default, structured note at its declared review date, and durable memory proposal at the retention class the store assigns.
- Bind the per-class write budget covering maximum writes per task, maximum bytes per task, maximum embedding calls, and maximum handle tokens resident in the window.
- Cap the resident handle registry at 5 percent of window capacity; above that ceiling, compact the registry into a single index handle before any further write is accepted.

**Write Class Contract**:

| Write class | Automatic offload trigger | Addressability requirement | Confirmation strength |
| :-- | :-- | :-- | :-- |
| Scratch state | None; proposal only | Identifier and purpose | Commit acknowledgement |
| Task ledger | Any state transition | Identifier, purpose, per-item status fields | Commit acknowledgement plus read-back |
| Artifact offload | 20,000 tokens in one result | Identifier, purpose, shape, extent, preview | Commit acknowledgement plus read-back |
| Structured note | Milestone or phase close | Full selectable header | Commit acknowledgement plus read-back |
| Durable memory proposal | Milestone or explicit instruction | Full selectable header plus provenance | Store admission response plus read-back |

**Required Outputs**:

- A class assignment with the trigger that fired and the lifetime applied.
- A per-class budget record naming each bounded dimension and its numeric limit.
- A handle registry measurement stating current resident handle tokens as a percentage of window capacity.

**Quality Checkpoints**:

- Every candidate carries exactly 1 class; a candidate with zero or two classes halts before commit.
- Every class budget dimension carries a numeric limit; an unbounded dimension blocks writes in that class.
- Resident handle tokens do not exceed 5 percent of window capacity; a breach forces registry compaction before the next write.

***

#### Step 1.3: Record the No-Write Decision and Its Reason

**Required Actions**:

- Emit a no-write record for every rejected candidate, carrying the failed gate, the reason code, the candidate extent, and the disposition of the content.
- Apply the standing prohibitions: never write content whose only consumer is the current model call, content reproducible from a current system of record, filler and restated context, unverified inference presented as fact, credentials or secrets, or content the requester has asked not to retain.
- Distinguish do-not-persist from do-not-use: rejected content remains available for the current authorized task and is discarded at the window boundary rather than suppressed immediately.
- Route any candidate whose rejection is contested to the retirement adjudication in Step 5.3 rather than resolving it by rewriting the reader declaration.
- Count no-write decisions by reason code so that a rising unstatable-occasion rate is visible as an extraction defect rather than as prudence.

**Required Outputs**:

- A no-write record per rejected candidate with failed gate, reason code, and content disposition.
- A prohibition sweep result confirming zero secrets and zero unconsented personal content among accepted candidates.
- A reason-code distribution for the task, reported alongside the accepted write count.

**Quality Checkpoints**:

- Every rejected candidate has a recorded reason code drawn from a closed vocabulary; an uncoded rejection is a telemetry defect.
- No accepted candidate contains a credential, token, key, or authentication cookie; any detection halts the write and quarantines the candidate.
- The no-write record states the content's disposition explicitly, so that a discarded candidate is distinguishable from one held in the window.

***

### Phase 2: Write Format and Addressability Contract

**Objective**: Give every accepted candidate a stable identifier, a canonical serialization, and a selectable header, so that the written item can be found and judged relevant later without being read in full and without scanning the store.

#### Step 2.1: Assign the Stable Identifier and Canonicalize the Payload

**Required Actions**:

- Obtain the identifier from the deterministic tier, scoped to tenant, principal, task, and branch, and opaque with respect to any mutable label such as a filename, a title, or a summary line.
- Reuse the existing identifier where the candidate updates a logical item already written; a new identifier is assigned only where the item is genuinely new, and an identifier is never reassigned to different content.
- Canonicalize the payload before hashing: normalize Unicode, whitespace, timestamp precision, numeric units, null representation, and field ordering, so that equivalent input serializes identically.
- Compute the content hash over the canonical form and attach it to the candidate as the exact-duplicate key.
- Detect exact duplicates against the current pointer for the identifier before any commit is attempted, and terminate the operation as superseded-no-change where the hash matches.
- Record the schema version and the serializer version with the payload, so that a later read can determine whether the item is readable by the current reader.

**Required Outputs**:

- A stable identifier bound to the logical item and recorded as new or reused.
- A canonical payload with its content hash, schema version, and serializer version.
- An exact-duplicate verdict against the identifier's current pointer.

**Quality Checkpoints**:

- The identifier is opaque and does not encode a mutable label; an identifier derived from a title or path is rejected, because renaming the label would break every handle pointing at it.
- Equivalent payloads produce identical hashes on replay; a hash that varies across serializations of the same content blocks the write.
- An update to an existing logical item reuses the existing identifier; a new identifier for an updated item halts the operation as an identifier-stability breach.

***

#### Step 2.2: Emit the Selectable Header and the Bounded Body

**Required Actions**:

- Emit a selectable header carrying identifier, write class, purpose, named reader, read occasion, schema version, extent, observation time, expiry, current-pointer version, and supersession links.
- State the purpose as a single declarative line naming what the item is for, not what it contains; a purpose that restates the first line of the body supplies no selection value.
- Bound the header to 40 lines or 400 tokens, whichever is smaller, so that selection over a large store remains cheap.
- Attach a shape descriptor naming the body's structure, its field names where structured, its item count where enumerable, and its unit conventions.
- Emit a preview of the body's first 10 lines alongside the header, so that a reader can reject an irrelevant item without a body read.
- Keep the body immutable once committed; every change produces a new version under the same identifier rather than an edit in place.
- Store large evidence by reference: where the body exceeds the class byte budget, write the evidence as a separate addressed item and carry its identifier in the header.

**Selectable Header Template**:

```
WRITE_ID:
WRITE_CLASS:
PURPOSE:
NAMED_READER:
READ_OCCASION:
SCHEMA_VERSION:
SHAPE:
EXTENT_TOKENS:
EXTENT_BYTES:
OBSERVED_AT:
COMMITTED_AT:
EXPIRES_AT:
CURRENT_VERSION:
SUPERSEDES:
SUPERSEDED_BY:
EVIDENCE_REFS:
CONTENT_HASH:
PREVIEW:
```

**Required Outputs**:

- A populated selectable header within the stated size bound.
- A canonical immutable body, or an evidence reference where the body exceeds the class byte budget.
- A body preview of at most 10 lines.

**Quality Checkpoints**:

- Every header field is populated or carries an explicit unknown marker; a blank field is a validation failure, not a default.
- The header alone is sufficient to decide relevance for the declared read occasion; a header requiring a body read to judge relevance fails the addressability contract.
- Header size does not exceed 40 lines or 400 tokens; an oversized header is compacted before commit, never truncated after it.

***

#### Step 2.3: Construct and Register the Write Handle

**Required Actions**:

- Construct the handle from the identifier, the purpose line, the shape descriptor, the extent, the committed version, and the retrieval instruction naming the exact call that returns the body.
- Bound the handle to 200 tokens; a handle exceeding that ceiling is reduced by shortening the purpose line and the shape descriptor, never by dropping the identifier or the retrieval instruction.
- Register the handle in an explicit in-window registry rather than embedding it in prose, so that the registry can be enumerated, measured, and compacted as a unit.
- Order the registry by read occasion proximity, so that handles whose occasions are imminent remain visible where the window is truncated from the tail.
- Recompute the projected saving as candidate tokens minus handle tokens, and record it against the operation for the accounting in Step 3.3.
- Withhold the handle from the window until the receipt returns; an unconfirmed handle in the registry is indistinguishable from a confirmed one and invites premature release.

**Required Outputs**:

- A handle within the 200-token ceiling carrying identifier, purpose, shape, extent, version, and retrieval instruction.
- A registry entry ordered by read-occasion proximity.
- A projected saving figure recorded against the operation identifier.

**Quality Checkpoints**:

- Every handle names the exact retrieval call; a handle describing where content lives without naming how to fetch it fails the contract.
- Handle size does not exceed 200 tokens, and the measured externalization ratio at commit remains at or above the 4 to 1 floor asserted in Step 1.1.
- No handle enters the registry before its receipt returns; a registry entry without a receipt reference halts the release.

***

### Phase 3: Durability Confirmation and Safe Release

**Objective**: Commit the write through a deterministic path, obtain a receipt proving the content is present and readable after the boundary, and release the in-context copy only after that receipt returns.

#### Step 3.1: Commit Through the Deterministic Path

**Required Actions**:

- Derive the idempotency key from the logical intent rather than the transport attempt, combining tenant, namespace, identifier, operation class, and content hash, and reuse the same key across every retry of the same intent.
- Submit the canonical payload, the selectable header, and the expected current-pointer version in one request, so that a concurrent write is rejected rather than silently overwritten.
- Commit the item version, the current-pointer advance, the provenance record, and the derivative outbox event in a single transaction; a commit that writes the item without the outbox event produces derivatives that never catch up.
- Reject and re-read on an expected-version mismatch rather than forcing the write, and return the candidate to Step 2.1 for re-canonicalization against the newer version.
- Return the prior result unchanged where the idempotency key already carries a committed result with an identical content hash, and reject as an idempotency conflict where the key exists with a different hash.
- Classify every failure as retryable or terminal at the point of failure: transport, timeout, and contention faults are retryable; schema, authorization, budget, and policy faults are terminal and are never retried unchanged.

**Required Outputs**:

- A commit result carrying identifier, committed version, commit sequence, and store location.
- An idempotency record binding the key to that result.
- A failure classification with a reason code where the commit did not succeed.

**Quality Checkpoints**:

- Retries of one logical write share one idempotency key; a fresh key per attempt is a defect that produces duplicate versions under one identifier.
- The item version and the outbox event commit atomically; a commit acknowledging the item alone is treated as failed and the in-context copy is retained.
- A terminal failure is never retried with unchanged input; a repeated identical attempt against a schema or policy rejection halts the operation.

***

#### Step 3.2: Obtain the Durability Receipt and Verify Read-Back

**Required Actions**:

- Require a receipt naming the identifier, the committed version, the commit sequence, the store location, and the watermark of every derivative the declared read occasion depends on.
- Verify that each dependent derivative's watermark is at or beyond the commit sequence; where a read occasion depends on a lexical or vector index, a canonical commit alone does not satisfy the receipt.
- Perform one read-back probe by identifier before release, comparing the returned content hash, version, and header fields against the committed values.
- Perform a second probe against the declared read occasion's actual retrieval path where that path differs from an identifier lookup, so that an item committed but not selectable is caught before the copy is discarded.
- Bound confirmation to 3 attempts and a declared deadline; on exhaustion, terminate the operation in the degraded state, keep the content resident, and record the unconfirmed identifier for reconciliation.
- Never infer durability from the absence of an error: a timeout is queried against the idempotency key, never assumed to be a failure and never assumed to be a success.

**Receipt Sufficiency Rules**:

| Declared read occasion | Sufficient receipt | Insufficient receipt |
| :-- | :-- | :-- |
| Retrieval by identifier after a boundary | Canonical commit sequence plus identifier probe | Store acknowledgement without a probe |
| Selection by purpose or field across a store | Lexical derivative watermark at or beyond commit sequence | Canonical commit alone |
| Semantic selection over many items | Vector derivative watermark plus a probe returning the item | Embedding call issued but unverified |
| Handoff to a named subagent | Probe executed under the receiving principal's scope | Probe executed under the writer's scope |
| Audit or human review | Canonical commit plus provenance completeness check | Derivative visibility alone |

**Required Outputs**:

- A durability receipt carrying committed version, commit sequence, and per-derivative watermarks.
- A read-back probe result comparing returned hash, version, and header fields against committed values.
- A confirmation verdict of confirmed, pending, or degraded with an attempt count.

**Quality Checkpoints**:

- Every release is preceded by a receipt whose watermarks cover every derivative the read occasion depends on; a partial receipt permits no release.
- The read-back probe returns the exact committed content hash; a hash mismatch quarantines the item and blocks the release.
- Confirmation halts after 3 attempts and terminates as degraded; an unbounded confirmation loop consumes budget while the copy remains resident and the window remains full.

***

#### Step 3.3: Release the In-Context Copy and Account the Saving

**Required Actions**:

- Replace the released extent with its handle in one operation, so that the window never passes through a state carrying neither the content nor the handle.
- Release only the exact extent the receipt covers; content adjacent to the confirmed extent stays resident until it carries a receipt of its own.
- Retain the residency copy and record a retained terminal state wherever the verdict is pending or degraded, and surface the retained extent as window pressure that has not been relieved.
- Compute the realized saving as released tokens minus handle tokens, measured after the replacement rather than projected before it, and attribute it to the write class.
- Record the operation's write amplification as the count of physical mutations, embedding calls, index updates, and queue messages the single logical write produced.
- Emit the write event carrying operation identifier, class, identifier, version, gates passed, receipt fields, realized saving, amplification, and terminal state.

**Required Outputs**:

- A window state in which the released extent is replaced by its registered handle.
- A saving record carrying released tokens, handle tokens, realized saving, and write class.
- A write event record with the full field set and a declared terminal state.

**Quality Checkpoints**:

- No extent is released without a confirmed receipt naming its version; a release under a pending verdict is the premature-release failure and is blocked unconditionally.
- Realized saving is measured after replacement, and a realized ratio below the 4 to 1 floor is recorded as a negative outcome for the class rather than discarded.
- Every write operation terminates in exactly 1 declared terminal state; an operation with no terminal state is a defect that leaves the residency question unanswered.

***

### Phase 4: Supersession, Compaction, and Staleness Control

**Objective**: Keep an evolving item addressable under one identifier as it changes, bound the number of versions a read can encounter, and ensure a read-back returns the version the read occasion requires rather than an older one.

#### Step 4.1: Supersede Rather Than Rewrite

**Required Actions**:

- Commit every change to a written item as a new version under the existing identifier, and advance the current pointer in the same transaction, so that no interval exists in which the identifier resolves to nothing.
- Write the supersession links in both directions: the new version names its predecessor, and the predecessor is marked superseded by the new version.
- Close the predecessor's validity interval where evidence supports a change in the represented world, and leave it open where only the system's knowledge changed; the two are recorded as separate times and never conflated.
- Refresh every resident handle for the identifier to the new version at the moment the pointer advances, so that the window never carries a handle naming a version the current pointer no longer serves.
- Prohibit destructive overwrite for every class above scratch state: a correction appends a version and preserves its predecessor as lineage rather than editing it in place.
- Reject any change proposing a new identifier for an item that already has one, and route it to the merge path in Step 4.2 rather than allowing two identifiers for one logical item.

**Required Outputs**:

- A new version committed under the existing identifier with an advanced current pointer.
- Bidirectional supersession links between the new version and its predecessor.
- A handle-refresh record naming every resident handle updated to the new version.

**Quality Checkpoints**:

- One logical item carries exactly 1 identifier for its lifetime; a second identifier for the same item is an addressability defect and forces a merge.
- The current pointer advance and the version commit occur in one transaction; a pointer advanced separately can name a version that is not readable.
- No resident handle survives a pointer advance naming a superseded version; a stale handle in the window causes a read-back to retrieve an obsolete body.

***

#### Step 4.2: Compact the Write Series at the Numeric Trigger

**Required Actions**:

- Count the write series length per identifier continuously, and fire compaction when any of three triggers is met: 5 superseded versions that no read has served, 20 total versions under one identifier, or 3 consecutive versions whose canonical payloads differ by less than the class materiality threshold.
- Fire a merge instead of a compaction where 2 or more distinct identifiers carry headers agreeing on purpose, named reader, and read occasion and whose bodies are near-identical; merge under the older identifier and redirect the newer identifier as an alias rather than deleting it.
- Compact by retaining the current version, the earliest version, every version a read has served, every version carrying a correction, and every version referenced by a live handle, and by collapsing the remainder into a lineage summary naming the collapsed version range and its content hashes.
- Never compact provenance records, correction events, supersession links, audit entries, or any version a retention obligation covers; a compaction that removes them is a defect regardless of storage pressure.
- Rebuild the affected derivatives from the canonical store after compaction, and verify each derivative's watermark against the post-compaction commit sequence before serving resumes.
- Record the compaction as a write event with its own operation identifier, so that compaction cost enters write amplification rather than being accounted as free maintenance.

**Compaction and Merge Triggers**:

| Observed condition | Threshold | Action |
| :-- | :-- | :-- |
| Superseded versions never served by a read | 5 under one identifier | Compact the unserved range into a lineage summary |
| Total versions under one identifier | 20 | Compact and re-verify derivatives |
| Consecutive near-identical versions | 3 within one task | Coalesce into 1 version; raise the class write threshold |
| Distinct identifiers with matching header triple | 2 or more | Merge under the older identifier; alias the newer |
| Resident handle registry share of window | Above 5 percent | Compact the registry into an index handle |
| Derivative watermark lag after compaction | Any lag at serve time | Block serving from that derivative until rebuilt |

**Required Outputs**:

- A compaction record naming the trigger, the retained versions, the collapsed range, and the lineage summary.
- A merge record naming the surviving identifier, the aliased identifier, and the redirected handles.
- A derivative verification result covering every rebuilt projection.

**Quality Checkpoints**:

- Compaction preserves every version a read served, every correction, and every retention-covered version; a collapsed range containing any of them halts the operation.
- After a merge, the aliased identifier continues to resolve to the surviving item; an identifier that resolves to nothing after a merge breaks every handle written before it.
- Compaction cost is recorded against write amplification; uncounted maintenance conceals the true cost of a write class.

***

#### Step 4.3: Enforce Freshness and Detect Stale Read-Backs

**Required Actions**:

- Stamp every written item with an observation time and an expiry derived from its class lifetime, and record the validity interval separately from the commit time.
- Evaluate expiry deterministically at read-back: an item whose expiry has passed is returned marked expired, and the marking is never suppressed by a model judging the content still current.
- Compare the returned version against the identifier's current pointer at every read-back, and raise a stale-version event where the returned version is not current.
- Block a stale item from influencing an irreversible action; a read-back returning an expired or non-current version routes to refresh or to escalation rather than into the decision.
- Refresh by re-reading the current version where the identifier still resolves, and by returning to Phase 1 where the underlying content must be re-derived from a source.
- Track the staleness rate per write class as stale read-backs divided by read-backs, and treat a rate above 5 percent as a class defect requiring a lifetime or trigger change rather than a per-read correction.

**Required Outputs**:

- A freshness stamp per item carrying observation time, expiry, and validity interval.
- A stale-read event record per detected staleness, naming identifier, returned version, current version, and read occasion.
- A per-class staleness rate with numerator, denominator, and window.

**Quality Checkpoints**:

- Expiry is evaluated by the deterministic tier at every read-back; a freshness judgement made by the model is a prohibited delegation under Section 1.3.
- No expired or non-current item reaches an irreversible action; a detection blocks the action and escalates rather than proceeding with a warning.
- Class staleness rate remains at or below 5 percent; a breach triggers a lifetime revision for the class before further writes in that class are accepted.

***

### Phase 5: Read-Back Verification and Utilization Measurement

**Objective**: Establish by measurement whether written items are retrievable after a real boundary and whether declared readers actually retrieve them, and retire write classes whose reads never arrive.

#### Step 5.1: Run the Post-Boundary Retrieval Probe

**Required Actions**:

- Sample at least 10 percent of committed writes per class, and never fewer than 5 per class per operating day, for a probe executed after an actual context boundary rather than at commit time.
- Execute each probe through the declared read occasion's retrieval path and under the named reader's authorization scope, so that a scope failure surfaces as a probe failure rather than as a runtime outage.
- Compare the returned item against the committed record on identifier, current version, content hash, header completeness, and preview fidelity.
- Verify that a probe issued with a purpose or field query, not an identifier lookup, returns the item within the first 10 results; an item retrievable only by identifier fails the addressability contract for occasions declared as selection.
- Record a probe failure as a defect against the write class rather than against the individual item, since a systematic addressability fault affects every item the class produced.
- Bound the probe budget to 2 percent of the class's total write cost, so that verification does not become the dominant expense of the pattern.

**Required Outputs**:

- A probe result set covering the sampled writes with pass or fail per comparison dimension.
- A per-class addressability verdict distinguishing identifier retrievability from selection retrievability.
- A probe cost figure expressed as a percentage of class write cost.

**Quality Checkpoints**:

- Every probe runs after a real boundary and under the named reader's scope; a probe run in the writing context proves nothing about survival.
- Items declared for selection are returned within the first 10 results of a purpose or field query; a failure blocks further writes in the class until the header contract is corrected.
- Probe cost remains at or below 2 percent of class write cost; a breach reduces the sample rate rather than removing the probe.

***

#### Step 5.2: Measure Utilization and Retire Unread Write Classes

**Required Actions**:

- Compute utilization per write class over a rolling window of 50 writes as items retrieved by a named reader at or before the declared read occasion, divided by items committed in that class.
- Compute net saving per class as realized saving minus retrieval cost minus write amplification cost, expressed in tokens and in physical mutations.
- Apply the retirement ladder: utilization below 20 percent raises the class threshold and narrows its trigger; utilization below 5 percent suspends the class; negative net saving over a full 50-write window suspends the class regardless of utilization.
- Separate a class that is never read from a class that is read but not at the declared occasion, since the first is retired and the second has its read occasion restated.
- Record retrieval noise as the count of superseded, expired, or retired items appearing in selection results for live queries, and treat a rising count as evidence that unread writes are displacing live ones.
- Route a contested retirement to adjudication where a named reader exists whose retrievals the measurement could not observe, such as an audit process reading outside the instrumented path.

**Required Outputs**:

- A per-class utilization figure with numerator, denominator, and rolling window.
- A per-class net saving figure in tokens and physical mutations.
- A retirement decision per class of retain, threshold-raised, suspended, or adjudication-pending.

**Quality Checkpoints**:

- Every rate is reported with its numerator, denominator, window, and class; a bare percentage is rejected as unauditable.
- A class below 5 percent utilization is suspended rather than tolerated; continuing to write into it converts window pressure into retrieval noise without relief.
- Net saving is computed including amplification and retrieval cost; a saving figure counting only released tokens overstates the benefit of every class.

***

#### Step 5.3: Tune the Write Thresholds Against Measured Outcomes

**Required Actions**:

- Change exactly 1 threshold per tuning cycle, holding the trigger set, the class definitions, and the extraction prompt constant, so that an observed change is attributable.
- Replay the same recorded candidate set against the changed threshold before applying it to live traffic, and compare utilization, net saving, staleness, and probe pass rate on the identical input.
- Require the improvement to hold across 2 independent samples before the threshold is adopted, and revert on the first sample that fails.
- Diagnose a falling utilization with stable write volume as a reader or occasion declaration defect, and a rising write volume with stable utilization as an extraction verbosity defect; the two have different corrections.
- Version every threshold change with its measured justification, and record the prior value so that a regression can be reverted without reconstruction.
- Re-derive class lifetimes from the observed distribution of read-occasion arrival times rather than from the defaults, once at least 50 read-backs per class have been observed.

**Required Outputs**:

- A tuning record naming the single changed threshold, its prior value, its new value, and the replay comparison.
- A two-sample confirmation result with the adopt or revert decision.
- A versioned threshold table with measured justifications per entry.

**Quality Checkpoints**:

- Exactly 1 threshold changes per cycle; a multi-variable change produces no attributable result and is rejected before replay.
- No threshold is adopted on a single sample; adoption requires the improvement to hold twice on independent data.
- Class lifetimes are re-derived from observed read-occasion arrival times once 50 read-backs exist; continuing on defaults past that point is recorded as an open calibration item.

***

### Phase 6: Boundary Crossing and Fault Containment

**Objective**: Carry the written state across a context boundary through an explicit manifest, reconstitute the next window from handles under a bounded budget, and contain writes that were lost, partially committed, or orphaned.

#### Step 6.1: Assemble the Handoff Manifest at the Boundary

**Required Actions**:

- Enumerate 100 percent of live handles at the boundary, including handles whose read occasion has not yet arrived, and exclude every handle whose item is superseded, expired, retired, or tombstoned.
- Carry the protected atoms inline in the manifest rather than as handles, since an unresolvable handle to the objective or the standing constraints leaves the receiver unable to act at all.
- Record every write whose confirmation verdict is pending or degraded, with its resident extent, so that the receiver knows which content exists only in the window it is about to lose.
- Resolve every pending write before the boundary completes: confirm it, re-commit it, or carry its content inline in the manifest; a pending write crossing a boundary as a handle is the premature-release failure delayed by one step.
- Name the exact next action and the state version, and require the receiver to acknowledge the manifest explicitly before the prior window is released.
- Bound the manifest to 10 percent of the receiving window's capacity, and compact the handle registry into an index handle where the bound is exceeded.

**Handoff Manifest Template**:

```
MANIFEST_ID:
STATE_VERSION:
SCHEMA_VERSION:
BOUNDARY_TYPE:
SENDING_PRINCIPAL:
RECEIVING_PRINCIPAL:
PROTECTED_ATOMS_INLINE:
LIVE_HANDLES:
PENDING_WRITES_INLINE:
DEGRADED_WRITES:
RETIRED_HANDLES_EXCLUDED:
NEXT_ACTION:
MANIFEST_TOKENS:
ACKNOWLEDGEMENT_REQUIRED:
```

**Required Outputs**:

- A manifest enumerating every live handle, every protected atom inline, and every unresolved write.
- A pending-write resolution record showing each pending write confirmed, re-committed, or carried inline.
- An explicit receiver acknowledgement bound to the manifest identifier and state version.

**Quality Checkpoints**:

- No pending or degraded write crosses the boundary as a handle alone; its content is carried inline or the boundary is blocked.
- Protected atoms appear inline in the manifest; a protected atom represented only as a handle fails the manifest validation.
- The prior window is released only after an explicit acknowledgement; an unacknowledged manifest halts the boundary crossing.

***

#### Step 6.2: Reconstitute the Receiving Window From Handles

**Required Actions**:

- Load the manifest, validate its schema and state version, and reject a manifest whose version is older than the receiver's own state.
- Resolve handles lazily: fetch a body only when its read occasion arrives, and hold the header and preview in the window until then.
- Bound total reconstitution to 30 percent of the receiving window's capacity, and where the bound would be exceeded, resolve handles in read-occasion order and leave the remainder unresolved rather than truncating bodies.
- Verify each resolved body against its handle's committed version and content hash before the content influences any decision.
- Halt on an unresolvable handle rather than proceeding without it: an identifier that no longer resolves, a version the current pointer no longer serves, or a scope failure each terminate resolution and escalate with the identifier named.
- Re-register every unresolved handle in the receiving window's registry, so that the next boundary carries them forward rather than dropping them silently.

**Required Outputs**:

- A validated manifest load result with a schema and state-version verdict.
- A resolution record per handle stating resolved, deferred, or unresolvable with a reason code.
- A receiving-window registry carrying every deferred and unresolved handle.

**Quality Checkpoints**:

- Reconstitution consumes no more than 30 percent of the receiving window; a breach defers the remainder rather than truncating resolved bodies.
- Every resolved body matches its handle's committed version and content hash; a mismatch quarantines the item and blocks its use.
- An unresolvable handle halts and escalates; proceeding without it converts a detectable fault into a silent gap in the task state.

***

#### Step 6.3: Contain Lost, Partial, and Orphaned Writes

**Required Actions**:

- Reconcile at every boundary and on a fixed schedule: compare the write event log against the canonical store and each derivative's watermark, and list identifiers that are missing, duplicated, unserved, or version-mismatched.
- Classify each fault as a lost write, where a confirmed receipt exists but the item does not resolve; a partial write, where the canonical item exists but a required derivative has not caught up; or an orphaned write, where an item exists that no handle, manifest, or reader references.
- Recover a lost write by re-committing from the residency copy where one survives, and by declaring the content unrecoverable and escalating where it does not; never fabricate a replacement body.
- Recover a partial write by replaying the outbox event and re-verifying the derivative watermark, and block reads that depend on that derivative until the watermark clears.
- Retire an orphaned write by tombstoning it from selection after 1 full class lifetime with no reference, and preserve its lineage rather than deleting the record outright.
- Bound recovery to 3 attempts per identifier and a declared deadline, after which the identifier is escalated with its fault class, its last known version, and the readers whose occasions it will miss.

**Required Outputs**:

- A reconciliation report listing every mismatched identifier with its fault class.
- A recovery record per fault stating the action taken and the resulting terminal state.
- An escalation record for every identifier exceeding the recovery bound.

**Quality Checkpoints**:

- Every reconciliation cycle ends with each mandatory identifier matched, excluded by an approved degraded state, or escalated; an empty queue is not evidence of consistency.
- Unrecoverable content is declared unrecoverable and escalated; a reconstructed body presented as the original is a fabrication and is prohibited.
- Recovery halts after 3 attempts per identifier; an unbounded recovery loop consumes budget while the affected read occasions pass unserved.

***

## III. Implementation Guidance for AI Agents

AI agents externalizing context state must follow systematic protocols ensuring that every write is proposed by a model, committed by a deterministic path, confirmed before release, and measured against whether a reader ever retrieved it. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Candidate Agent**: Delimits candidate extents, names the reader and the read occasion, proposes the write class, and composes the note or summary written in place of raw content. It never assigns an identifier, never commits, and never authorizes a release.
2. **Policy Gate**: Evaluates the six externalization gates, assigns the write class, enforces class budgets and the handle registry ceiling, and emits the no-write record with its reason code. It is deterministic and its verdict is final.
3. **Write Executor**: Assigns the stable identifier, canonicalizes and hashes the payload, validates the selectable header, derives the idempotency key, and commits the version, the pointer advance, the provenance record, and the outbox event in one transaction.
4. **Confirmation Agent**: Collects the receipt, checks every dependent derivative watermark, runs the read-back probe, and holds the sole authority to declare a write confirmed. It may refuse a release.
5. **Release Controller**: Performs the content-for-handle replacement, computes realized saving and write amplification, and emits the write event with its terminal state. It acts only on a confirmed verdict.
6. **Series Custodian**: Owns supersession links, current-pointer advancement, compaction and merge triggers, expiry evaluation, and derivative rebuilds. It alone may collapse a version range.
7. **Utilization Analyst**: Runs post-boundary probes, computes utilization and net saving per class, and proposes retirement. Software supplies the measurement; a model adjudicates only contested retirements.

**The Release Invariant**: The in-context copy is never discarded before the Confirmation Agent returns a receipt naming the committed version and the watermarks the declared read occasion depends on. This is a hard constraint binding every component.

- A write proposed by a model and acknowledged by no store is a proposal, never a save, and is never reported as one.
- A timeout is resolved by querying the idempotency key, never by assuming success and never by assuming failure.
- A pending or degraded verdict keeps the content resident and terminates the operation as retained, and the unrelieved window pressure is surfaced rather than concealed.
- Where confirmation cannot be obtained within 3 attempts, the operation escalates with the identifier and the resident extent named.

**Workflow Execution Pattern**:

```
STATE: Durability_Confirmation_And_Release
INPUTS:
  1. Commit result with identifier, version, and commit sequence
  2. Declared read occasion and its derivative dependency set
  3. Resident extent with measured token cost
ACTIONS:
  1. Collect receipt fields and per-derivative watermarks
  2. Execute identifier probe and occasion-path probe
  3. Compare returned hash, version, and header against committed values
  4. Compute realized saving and write amplification
VALIDATION:
  - receipt_present == TRUE
  - dependent_watermarks_at_or_beyond_commit_sequence == TRUE
  - probe_hash_match == TRUE
  - realized_externalization_ratio >= 4
  - confirmation_attempts <= 3
TRANSITIONS:
  IF all_validations_pass THEN next_state = Release_And_Account
  IF confirmation_attempts > 3 THEN next_state = Retain_And_Escalate
  IF probe_hash_match == FALSE THEN next_state = Quarantine_Item
  IF validation_failed THEN next_state = Retain_Resident_Copy
```

**Two-Phase Action Pattern**: Emit the intended release with its extent, its handle, and its receipt reference without executing it; confirm it against the validation block while the content is still resident; execute the replacement only after validation passes, recording the write event in the same operation.

**Approval Gate**: Human authorization is required before any release exceeding 25 percent of the current window in one operation, before any write committed over an expected-version conflict, before suspending or retiring a write class, before compacting a version range containing a correction or a retention-covered version, and before declaring written content unrecoverable. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the handle registry, the class budget ledger, and the pending-write list in durable state, since the write path outlives any single window.
- Keep the resident handle registry at or below 5 percent of window capacity, compacting it into an index handle at the ceiling.
- Count the write path's own overhead, including probes, receipts, and manifests, against the saving it produces, rather than treating verification as free.
- Write a handoff manifest at every context boundary and require explicit acknowledgement before the prior window is released.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Write Decision Integrity (After Phase 1)**

- **Automated Check**: Every accepted candidate carries a named reader, a named read occasion, a computed externalization ratio at or above 4 to 1, and exactly 1 write class; every rejected candidate carries a reason code; no accepted candidate contains a credential or an unconsented personal field.
- **Agent Action on Pass**: Proceed to formatting and addressing.
- **Agent Action on Failure**: Reject the candidate and record the failed gate; no store is contacted for a candidate that failed a gate.
- **Human Review Trigger**: More than 30 percent of candidates in one task rejected for an unstatable read occasion, which indicates a task-decomposition defect rather than a prudent policy.

**Checkpoint 2: Addressability Conformance (After Phase 2)**

- **Automated Check**: Identifier is opaque and stable; header is fully populated within 40 lines and 400 tokens; shape descriptor and 10-line preview present; handle within 200 tokens and naming an exact retrieval call.
- **Agent Action on Pass**: Proceed to commit.
- **Agent Action on Failure**: Halt before commit; an unaddressable item committed is a leak that later selection must discriminate against.
- **Human Review Trigger**: An item whose read occasion cannot be judged from the header alone after 2 header revisions.

**Checkpoint 3: Durability and Release Safety (After Phase 3)**

- **Automated Check**: Receipt present with committed version and commit sequence; every dependent derivative watermark at or beyond that sequence; probe hash matches; release extent equals receipt extent; terminal state declared.
- **Agent Action on Pass**: Release the extent and emit the write event.
- **Agent Action on Failure**: Retain the residency copy, terminate as retained or degraded, and surface the unrelieved window pressure.
- **Human Review Trigger**: Any release executed without a matching receipt, and any confirmation exhausting all 3 attempts.

**Checkpoint 4: Series Integrity (After Phase 4)**

- **Automated Check**: One identifier per logical item; bidirectional supersession links present; no resident handle naming a superseded version; compaction preserved every served version, correction, and retention-covered version; class staleness rate at or below 5 percent.
- **Agent Action on Pass**: Resume normal writes in the class.
- **Agent Action on Failure**: Block further writes in the affected class and repair the series before accepting new versions.
- **Human Review Trigger**: Any compaction proposing to collapse a correction, and any identifier merge affecting handles already carried across a boundary.

**Checkpoint 5: Utilization Adequacy (After Phase 5)**

- **Automated Check**: Probe sample at or above 10 percent per class; selection-declared items returned within the first 10 results; utilization and net saving reported with numerator, denominator, and window; retirement ladder applied.
- **Agent Action on Pass**: Retain the class and record the measured thresholds.
- **Agent Action on Failure**: Raise the class threshold at utilization below 20 percent; suspend the class at utilization below 5 percent or negative net saving.
- **Human Review Trigger**: A retirement contested on the grounds of an uninstrumented reader, and any class suspended twice in 3 measurement windows.

**Checkpoint 6: Boundary Crossing Completeness (After Phase 6)**

- **Automated Check**: Manifest enumerates 100 percent of live handles; protected atoms inline; zero pending writes represented as handles; explicit acknowledgement recorded; reconstitution at or below 30 percent of the receiving window; reconciliation report closed.
- **Agent Action on Pass**: Release the prior window and continue.
- **Agent Action on Failure**: Block the boundary until pending writes are resolved or carried inline.
- **Human Review Trigger**: Any unrecoverable lost write, and any manifest exceeding 10 percent of the receiving window after registry compaction.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Premature Release**

- **Symptoms**: A handle resolves to nothing, to an older version, or to an item visible only to the writing principal; the failure surfaces one boundary after the release rather than at it.
- **Diagnostic Steps**: Compare the release event's receipt reference against the commit log, determine whether a receipt existed at all, and check whether the receipt covered the derivative the read occasion used.
- **Resolution Protocol**: Option A, re-commit from a surviving residency copy or from an upstream artifact and re-verify. Option B, regenerate the content from its authoritative source where one exists, marking the new item as regenerated rather than original. Option C, declare the content unrecoverable, escalate with the affected read occasions named, and re-plan the task without it.
- **Escalation Trigger**: Any release found to have executed without a matching receipt escalates immediately for control review; this class is never resolved by retrying the release.

**Error Type 2: Unread Write Accumulation**

- **Symptoms**: Write volume rises while utilization falls; selection results carry superseded, expired, or retired items; net saving per class turns negative while released tokens look healthy.
- **Diagnostic Steps**: Segment utilization by class, trigger, and reader; separate items never read from items read outside the declared occasion; measure retrieval noise as the share of selection results that are not live.
- **Resolution Protocol**: Option A, raise the class threshold and narrow its trigger so fewer candidates qualify. Option B, restate the read occasion where reads arrive but not at the declared time. Option C, suspend the class and route its candidates to retention in the window or to outright discard.
- **Escalation Trigger**: Utilization below 5 percent, or negative net saving across a full 50-write window, suspends the class without further retries.

**Error Type 3: Identifier Instability**

- **Symptoms**: Two identifiers resolve to substantially the same item; a handle carried across a boundary no longer resolves; a read returns an older version than the one a handle names.
- **Diagnostic Steps**: Compare header triples of purpose, named reader, and read occasion across recent identifiers; check whether an identifier was derived from a mutable label; trace whether the current pointer advanced without a handle refresh.
- **Resolution Protocol**: Option A, merge under the older identifier and alias the newer, redirecting every handle. Option B, reassign identifiers from the opaque generator where a label-derived identifier is in use, retaining the old identifier as a permanent alias. Option C, refresh every resident handle from the current pointer and re-issue the manifest.
- **Escalation Trigger**: A merge affecting handles already carried across a boundary requires approval before execution; an identifier that resolves to nothing after a merge halts all writes in the namespace.

**Error Type 4: Derivative Lag at the Read Occasion**

- **Symptoms**: An item is retrievable by identifier but absent from purpose or semantic selection; probe pass rates split sharply between the two retrieval paths; reads succeed for the writer and fail for a named subagent.
- **Diagnostic Steps**: Compare each derivative's watermark against the item's commit sequence, inspect the outbox relay for backlog and replay counts, and confirm the probe ran under the reader's authorization scope.
- **Resolution Protocol**: Option A, replay the outbox events and re-verify the watermark before serving resumes. Option B, block reads that depend on the lagging derivative and serve by identifier only until it clears. Option C, rebuild the affected derivative partition from the canonical store.
- **Escalation Trigger**: Lag exceeding the read occasion's arrival time for any item, or 3 failed replays for one identifier, escalates with the derivative and the backlog depth named.

**Error Type 5: Handle Registry Overgrowth**

- **Symptoms**: Resident handle tokens exceed 5 percent of window capacity; window pressure persists after releases; handles for occasions long past remain registered.
- **Diagnostic Steps**: Enumerate the registry by read-occasion proximity and by age, and separate handles whose occasions have passed from those still pending.
- **Resolution Protocol**: Option A, compact the registry into a single index handle naming the store and the query pattern rather than each item. Option B, drop handles whose read occasions have passed and whose items are retrievable by query. Option C, raise the write threshold for the class producing the most registry entries.
- **Escalation Trigger**: Registry above 5 percent after 2 compaction attempts blocks further writes until the class thresholds are revised.

**Error Type 6: Stale Read-Back Reaching a Decision**

- **Symptoms**: A retrieved item's expiry has passed or its version is not current; a decision cites content the current pointer no longer serves; staleness rate for a class exceeds 5 percent.
- **Diagnostic Steps**: Compare the returned version against the current pointer and the returned expiry against the read time, and determine whether the class lifetime or the refresh path is at fault.
- **Resolution Protocol**: Option A, refresh from the current version and re-run the decision. Option B, shorten the class lifetime where expiries are systematically optimistic. Option C, block the class from irreversible actions until the staleness rate returns below 5 percent.
- **Escalation Trigger**: A stale item reaching an irreversible action escalates immediately; this class is never resolved by having a model reassess whether the content still looks current.

**Troubleshooting Decision Tree**:

```
WRITE PATH FAULT DETECTED
├─ RELEASE DEFECT
│   ├─ Handle resolves to nothing → Re-commit from residency copy; else declare unrecoverable
│   ├─ Release without matching receipt → HALT; escalate for control review
│   └─ Released extent exceeds receipt extent → Restore the uncovered extent; re-confirm
├─ ADDRESSABILITY DEFECT
│   ├─ Item found by identifier only → Repair header; rebuild lexical derivative
│   ├─ Header requires body read to judge → Rewrite purpose line; re-probe
│   └─ Two identifiers for one item → Merge under older; alias the newer
├─ UTILIZATION DEFECT
│   ├─ Utilization below 20 percent → Raise class threshold; narrow trigger
│   ├─ Utilization below 5 percent → Suspend the class
│   └─ Reads arrive off-occasion → Restate the read occasion; keep the class
├─ CONSISTENCY DEFECT
│   ├─ Derivative watermark behind commit → Replay outbox; block dependent reads
│   ├─ Version conflict on commit → Re-read; re-canonicalize; never force
│   └─ Orphaned item with no reference → Tombstone after 1 class lifetime; keep lineage
└─ FRESHNESS DEFECT
    ├─ Expired item returned → Refresh from current version; re-run the decision
    └─ Stale item reached irreversible action → HALT; escalate; block the class
```

### D. Performance Metrics and Continuous Learning

**Write-Decision Metrics**:

- **Write utilization**: Items retrieved by a named reader at or before the declared read occasion, over items committed, per class over a rolling 50-write window (target: at least 40 percent; below 20 percent raises the threshold, below 5 percent suspends the class).
- **No-write accuracy**: Correctly rejected candidates over adjudicated rejected candidates (target: at least 90 percent, with the unstatable-occasion reason code reported separately).
- **Realized externalization ratio**: Released tokens over handle tokens, measured after replacement (target: at least 10 to 1; below 4 to 1 is a failed write).
- **Net saving per class**: Realized saving minus retrieval cost minus amplification cost, in tokens and physical mutations (target: positive median per class).

**Durability and Consistency Metrics**:

- **Release safety**: Releases preceded by a matching receipt over total releases (target: 100 percent; any shortfall is a zero-tolerance event).
- **Post-boundary probe pass rate**: Probes returning the committed version and hash over probes executed (target: at least 99 percent).
- **Selection retrievability**: Selection-declared items returned within the first 10 results of a purpose or field query, over selection-declared items probed (target: at least 95 percent).
- **Derivative freshness**: Dependent derivatives at or beyond their item's commit sequence at read time, over reads requiring a derivative (target: at least 99 percent).
- **Write amplification**: Physical mutations, embedding calls, index updates, and queue messages per logical accepted write (target: no more than 6; a rising figure at flat logical volume indicates index churn).

**Series and Freshness Metrics**:

- **Identifier stability**: Logical items carrying exactly 1 identifier over logical items audited (target: 100 percent).
- **Series length**: Versions per identifier at the compaction trigger (target: no more than 20; a series reaching the bound repeatedly indicates the class writes too often).
- **Staleness rate**: Read-backs returning an expired or non-current version over read-backs, per class (target: no more than 5 percent).
- **Retrieval noise**: Superseded, expired, or retired items appearing in live selection results over selection results inspected (target: no more than 2 percent).

**Learning and Adaptation Mechanisms**:

- **Occasion calibration**: Re-derive each class lifetime from the observed distribution of read-occasion arrival times once 50 read-backs exist, rather than holding the deployment defaults indefinitely.
- **Single-variable tuning**: Change 1 threshold per cycle, replay the recorded candidate set, and adopt only where the improvement holds across 2 independent samples.
- **Reason-code review**: Track the no-write reason-code distribution over time; a rising unstatable-occasion share indicates poor task decomposition, and a rising cheaper-reconstruction share indicates the write class duplicates a system of record.
- **Class retirement memory**: Retain suspended classes with their measured justification, so that a later proposal to reinstate one is evaluated against the evidence that suspended it.

**Human-in-the-Loop Boundaries**: Declaring written content unrecoverable, releasing an extent without a receipt, compacting a range containing a correction, merging identifiers whose handles have crossed a boundary, and reinstating a suspended write class are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the movement of state out of a bounded window rather than the meaning of any particular state. Its phases hold wherever a task exceeds one context window, produces content a later step must read, and pays a cost for carrying that content forward.

### 4.1 Cross-Domain Application Patterns

**Software engineering and code maintenance**: Tool results dominate the window, and most exceed the offload trigger on their own. Build logs, test output, dependency trees, and file contents are written as artifact offloads addressed by identifier with a shape descriptor naming the command, the exit status, and the failing region. The read occasion is usually a specific diagnostic step, so the header carries the failure signature and the handle carries the retrieval instruction. Utilization here is high for failing outputs and near zero for passing ones, which makes the retirement ladder productive: a class writing every successful build result is suspended within one measurement window.

**Research and evidence synthesis**: The window fills with retrieved sources rather than tool output. Each source is written as a structured note whose header carries the claim it supports, the named reader as the synthesis step that will cite it, and the read occasion as the drafting of the section it belongs to. Addressability by purpose matters more than addressability by identifier, because the reader arrives with a claim rather than a name, so selection retrievability is the binding probe. The compaction trigger fires often, since a source note is revised as understanding of the claim changes, and identifier stability keeps the citation intact across revisions.

**Regulated decision support and audit**: Write classes carry retention obligations, and the compaction rules bind hardest: no version that a decision cited, that carries a correction, or that a retention obligation covers may be collapsed. The receipt requirement is strengthened, since an item invisible to the audit path is not durable for the occasion that matters even where it is canonically committed. The write event log becomes a deliverable rather than a diagnostic aid, and the approval gate on unrecoverable content is exercised rather than theoretical.

**Field and industrial operations**: Observations arrive from instruments and human reports over long horizons, and the boundary is frequently a shift handover rather than a context compaction. The handoff manifest carries most of the value: protected atoms inline, live handles enumerated, and explicit acknowledgement by the receiving operator. Freshness dominates, since an instrument reading past its expiry is not a judgement call, and the staleness rate is the metric that governs whether a class lifetime was set correctly.

**Customer-facing conversational service**: Volume is high and per-item value is low, so the write decision is where the leverage sits. Most turn content fails the durability-need gate outright, and the classes that survive are narrow: an unresolved obligation, a stated correction, a commitment with a deadline. Utilization measurement is cheap here because read occasions are frequent, which makes this the domain where the retirement ladder converges fastest.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-volume single-agent work**: Collapse to two classes, scratch state and artifact offload, and confirm by commit acknowledgement plus one identifier probe. Skip derivative watermarks where no selection path exists. Where realized saving stays below 4 to 1 across a task, the window was never under enough pressure to justify the pattern.
- **High-volume multi-agent work**: Enforce the full class contract, run probes under each named subagent's scope rather than the writer's, and treat the handle registry ceiling as binding, since several agents writing into one namespace overgrow it faster than one.
- **High-risk or irreversible work**: Require the read-back probe on 100 percent of writes rather than a sample, block every expired or non-current item from irreversible actions, and exercise the approval gate before any compaction touching a cited version.
- **Strict latency budgets**: Move confirmation off the critical path by writing asynchronously and holding the residency copy until the receipt returns, rather than by releasing early. Latency is never a reason to release without a receipt; it is a reason to defer the release.
- **Long-horizon autonomous runs**: Persist the handle registry, the class budget ledger, and the pending-write list outside the window, write a manifest at every boundary, and run reconciliation at each boundary rather than only on a schedule, so a lost write is found one boundary after it occurs rather than at the end of the run.

***

## V. Limitations and Considerations

**Most numeric thresholds here are deployment defaults**: The 4 to 1 externalization floor, the 200-token handle ceiling, the 400-token header bound, the 5 percent registry ceiling, the 5 and 20 version compaction triggers, the 20 and 5 percent retirement rungs, the 5 percent staleness ceiling, the 30 percent reconstitution bound, and the 3-attempt confirmation limit were chosen to be operable on first deployment, not derived from a measured property of write paths. The offload trigger of 20,000 tokens for a single tool result and the window-pressure trigger at 85 percent of input capacity are observed defaults in a published agent harness rather than universal constants. The mitigation is Step 5.3 and the occasion-calibration mechanism in Section III.D, which oblige each deployment to re-derive its thresholds from observed read-occasion arrival times once 50 read-backs per class exist.

**Utilization is measurable only where reads are instrumented**: A class read by an audit process, a human reviewer, or an external system outside the instrumented path will appear unused and will be retired incorrectly. The mitigation is the adjudication route in Step 5.2, which requires a contested retirement naming an uninstrumented reader to be resolved by review rather than by the measurement alone, and the class retirement memory in Section III.D, which preserves the evidence for a later reinstatement.

**Confirmation costs what it saves on small writes**: A receipt, a watermark check, and a probe carry latency and tokens that can exceed the saving on a small extent. This is why the 4 to 1 floor exists, but the floor is a ratio and does not bound the absolute overhead. The mitigation is the class contract in Step 1.2, which assigns commit acknowledgement alone to scratch state, and the probe budget ceiling of 2 percent of class write cost in Step 5.1.

**The pattern relieves window pressure without reducing total cost**: Externalization moves tokens out of the window but adds commits, index updates, embeddings, probes, and retrievals. A deployment measuring only released tokens will conclude the pattern is free. The mitigation is the net saving metric in Section III.D, which subtracts retrieval and amplification cost, and the requirement in Step 3.3 that amplification be counted per logical write.

**Written content is a delayed-influence surface**: Content externalized from a window and retrieved later can carry instructions, and the retrieval reintroduces it into a window with the appearance of the agent's own prior state. This guide does not carry the trust-labelling and injection controls that govern admitted content. The mitigation is to preserve the source class and trust label through the write and the read-back, and to apply the memory-management category's injection and trust-boundary controls at the point content re-enters the window; this guide's contribution is that the header carries the labels those controls need.

**Identifier stability constrains later reorganisation**: Committing to one identifier per logical item for its lifetime is what makes handles durable, and it also makes a later decision to split an item expensive, since every handle written before the split names the merged identity. The mitigation is the alias rule in Step 4.2, which keeps a retired identifier resolvable rather than deleting it, so that an old handle degrades to a redirect rather than to a failure.

**Conformance is not sufficiency**: A deployment can satisfy every checkpoint here and still write the wrong content, because the reader and the read occasion are model-tier judgements the deterministic tier can validate for presence but not for correctness. The framework detects unaddressable, unconfirmed, unread, and stale writes; it does not detect a well-formed write of content that was never the right content. Human review of what a class writes remains necessary, and no checkpoint substitutes for it.

***

## VI. Conclusion and Summary

Writing context out is an accounting discipline before it is a storage technique. Its value comes from four commitments that are cheap to state and expensive to omit: that nothing is written without a named reader and a named read occasion, that everything written is addressable by something other than a full scan, that the in-context copy is never discarded before a receipt proves the content survives the boundary, and that a class whose reads never arrive is retired rather than tolerated. A system holding those four will relieve window pressure and keep its work; a system holding none of them will convert window pressure into storage cost, retrieval noise, and occasional silent loss.

A team introducing the pattern should instrument before it externalizes. Measure what actually fills the window, by source and by size, and record which of that content a later step reads. Add one write class covering the largest measured consumer, usually tool results, with a receipt requirement and an identifier probe from the first day. Measure utilization over 50 writes before adding a second class. Only then add structured notes, durable memory proposals, semantic selection, and the derivative watermarks those occasions require. A harness may supply offload triggers and file abstractions, but none of them supplies the read-occasion declaration or the utilization measurement, and without those the pattern writes steadily and reads rarely.

**Key Success Factors**:

- **Declared reader and occasion**: No content leaves the window without a named consumer and a named condition under which that consumer retrieves it, so an unread write is prevented rather than discovered.
- **Addressability before commit**: Every item carries a stable opaque identifier, a purpose line, and a header sufficient to judge relevance without a body read, so selection never requires a scan.
- **Receipt before release**: The in-context copy is discarded only after a durability receipt names the committed version and the watermarks the read occasion depends on, and a pending verdict keeps the content resident.
- **One identifier per logical item**: Change produces a new version under the existing identifier with bidirectional supersession links, so handles stay valid and later reads reach the current version.
- **Bounded series**: Compaction fires at declared version counts and near-identical thresholds, preserving every served version, correction, and retention-covered version, so a read cannot retrieve an obsolete record from an unbounded series.
- **Measured utilization**: Every class reports utilization and net saving with numerator, denominator, and window, and the retirement ladder suspends a class whose reads do not arrive.

By following this guide, AI agents can move state out of a bounded window without losing it, address it so that later steps find it cheaply, and demonstrate by measurement that each write class repaid the cost of writing it.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. One entry, marked as such, was retrieved directly during conversion research and its figures are quoted from the page as fetched. The originating source cited substantially more external material than appears here, covering ontology and graph write validation, privacy law at write time, and memory-poisoning defence; that material supports sections this conversion delegated to other categories and is not carried forward.

**Corpus pointers**:

- `Context Write Patterns: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the write-path invariants, the write-policy gates and the do-not-write list, the scratchpad and structured-note contracts, the write triggers, the record envelope, the deduplication and supersession rules, the bitemporal distinction, the idempotent write protocol and transactional outbox, the projection and reconciliation loop, the write-amplification accounting, the metric definitions, and the failure-mode inventory.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the category umbrella treating write, select, compress, and isolate as a selection ladder. It states which operation a given window pressure calls for; this guide assumes the ladder has already selected the write operation.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — the sibling owning what returns to the window. The addressability contract in Phase 2 exists to make selection cheap, and the selection guide states how the returned set is bounded and ranked.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — the sibling owning reduction of content that remains in the window, as distinct from the write-series compaction in Step 4.2, which reduces versions in the store.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — the sibling owning separation of content across windows, applicable to the subagent handoff cases in Phase 6.
- `advanced_task_guides/context-management/guide_FilesystemAsContext.md` — the sibling owning the file-tree substrate a write frequently lands on: directory and naming contracts, path resolution, bounded reads, and safe mutation sequences. This guide decides eligibility, format, and durability confirmation; that guide decides placement, naming, and mutation mechanics once those decisions are taken.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — the operation contract for the durable store, including the admission gates, idempotency and version semantics, canonical-store and derivative roles, the consistency token and watermark model, and the terminal-state vocabulary this guide adopts.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — the residency and eviction rules of a bounded working state, including the protected-atom, handoff-record, checkpoint, and supersession terminology this guide adopts.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — the transformation of many episodes into fewer durable records, including the provenance-link, validity-interval, and promotion-gate semantics that govern a durable memory proposal after it leaves this guide's scope.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — retention, tombstoning, and erasure of durable records, applicable to items this guide retires or tombstones in Step 6.3.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — the category overview placing the read and write operations, working memory, and consolidation in relation to one another.

**External references**:

*Context engineering and externalization practice*

1. Anthropic, *Effective context engineering for AI agents* — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
2. Anthropic, *memory tool* — https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
3. Anthropic, *context-engineering cookbook* — https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools
4. LangChain, *Context engineering in Deep Agents* — https://docs.langchain.com/oss/python/deepagents/context-engineering — retrieved and verified during conversion; source of the 20,000-token offload trigger, the 10-line preview, and the 85 percent window-pressure trigger quoted in Step 1.2 and Section V.
5. LangMem, *delayed processing* — https://langchain-ai.github.io/langmem/guides/delayed_processing/

*Durable commit, idempotency, and cross-store consistency*

6. *Transactional Outbox pattern* — https://microservices.io/patterns/data/transactional-outbox.html
7. AWS Prescriptive Guidance, *transactional outbox* — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html
8. *Idempotent Consumer pattern* — https://microservices.io/post/microservices/patterns/2020/10/16/idempotent-consumer.html
9. Martin Fowler, *Bitemporal History* — https://martinfowler.com/articles/bitemporal-history.html

*Write-path cost and memory-system evaluation*

10. *Agent Memory: Characterization and System Implications* — https://arxiv.org/html/2606.06448v1
11. *Are We Ready for an Agent-Native Memory System?* — https://arxiv.org/html/2606.24775v1
12. *MemoryAgentBench* — https://arxiv.org/abs/2507.05257
13. *Mem0 paper* — https://arxiv.org/abs/2504.19413
