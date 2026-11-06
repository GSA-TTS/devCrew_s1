# Context Memory Blocks

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context memory blocks constitute the task family of governing named, bounded, persistent regions of the context window that the agent itself reads and rewrites. A block is a durable slot rendered into every applicable inference without a retrieval decision, holding small state such as an agent's operating identity, a verified user profile, the active objective, or accumulated project conventions. The distinguishing property is self-editing: the same component that reads the region also proposes its replacement, with no external process mediating, which is the source of both the pattern's value and its characteristic failures. This guide provides AI agents with a structured protocol covering block registration under a declared schema, a dual size bound and a stated edit policy, deterministic assembly into the reserved region, a propose-validate-commit-or-rollback loop in which the model never holds commit authority, bound enforcement that rejects rather than truncates, scheduled reconciliation against the durable source of truth, provenance binding, and confidence marking that keeps an inferred claim distinguishable from an observed one. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a region the agent rewrites on its own authority remains bounded, traceable, and reversible.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Memory block**: A named, bounded, addressable, persistent unit of state whose rendered value occupies a reserved region of the context window on every applicable inference. A block carries an identifier, a declared purpose, a value schema, a size bound, an edit policy, an invariant set, and an independently versioned value. It is edited in place through typed operations rather than appended to as a stream.

**Residency**: The property that a block is present on every applicable inference without a retrieval decision being made. Residency is what separates a block from a durable memory record: both survive the session, but only the block is charged against the context budget and exposed to every inference by default.

**Reserved block region**: The partition of the context budget allocated to the rendered block set, bounded as a token count and accounted before the call rather than discovered on rejection. The region is a partition in the sense used by the context-management umbrella guidance, and it competes with every other partition.

**Block contract**: The machine-validated record declaring everything about a block that is not its value: identifier, label, description, value schema, byte bound, token bound, edit policy, owner, scope, template lineage, trust class, sensitivity class, render position, review cadence, and removal threshold. The contract is host-controlled and versioned separately from the value.

**Block description**: The operational instruction that tells the model how to read and edit the value: what belongs, what must never be stored, the evidence threshold for an update, the invariants an edit must preserve, and the action taken when capacity is insufficient. The description is a control surface, not a label expansion, and an agent that can rewrite its own description has closed a loop around its own constraints.

**Edit policy**: The declared mutability mode of a block, drawn from a closed set: read-only, append-only, targeted-update, rewriteable, and approval-gated. The policy names which typed operations are admissible, not merely whether the block is writable.

**Size bound**: The dual limit every block carries: a serialized byte or character maximum and a rendered-token maximum computed with the deployed tokenizer. A character limit alone is not a context-budget guarantee, because serialization and tokenization differ across renderers and models. A block without a size bound grows until it crowds out every other partition, which is this pattern's characteristic failure.

**Invariant set**: The declared list of properties that must hold in every committed value of a block: fields that must be present, fields that may never be removed, value ranges, required provenance coverage, and forbidden content classes. The invariant set is what a validator checks; a property stated only in the description and not in the invariant set is unenforced.

**Proposed edit**: A typed record naming the block identifier, the expected current version, the operation, the patch or candidate value, the reason, the evidence references, the initiating run, and an idempotency key. A proposal is an input to validation. It is never a state change.

**Commit authority**: The exclusive right to advance a block's current pointer, held by the deterministic tier. The model tier proposes and never commits. Text the model emits that resembles an updated block is output, not a mutation.

**Block revision**: One immutable serialization of a block value, addressed by a version identifier that never changes meaning, and carrying predecessor version, content hash, schema version, actor, reason, validation result, and timestamps. A change produces a new revision rather than mutating an existing one.

**Current pointer**: The mutable reference naming which revision of a block is rendered. Advancing the pointer is the only sanctioned form of update, and a rollback advances it to a new revision whose value matches a known-good predecessor rather than erasing the intervening ones.

**Renderer**: The deterministic function that serializes the attached block set into the reserved region with stable ordering, explicit delimiters, unambiguous escaping, and per-block metadata naming the label, value version, trust class, and read-only status. The renderer is versioned, because a renderer change alters token counts without any value changing.

**Provenance**: The verifiable path from a claim in a block back to what produced it: the source identifier, the source class, the capture timestamp, and the extraction or inference that derived the field. Provenance is what allows a wrong entry to be corrected at its origin rather than merely deleted from the block.

**Source class**: The categorical label distinguishing quoted source, direct observation, tool output, model inference, and approved procedure. Source class governs trust and confidence marking, never relevance.

**Confidence marking**: The obligation that block content derived by inference carries an explicit marker distinguishing it from content derived by observation, together with the evidence reference supporting it. A block is written in the agent's own voice and read back as established fact; without marking, a confidently phrased guess is indistinguishable from a verified value on every subsequent turn.

**Durable source of truth**: The authoritative system outside the block holding the canonical value of a fact the block restates: a record system, a task store, a repository, a memory store, or an approved configuration. A block is a projection of that source, never its replacement.

**Self-edit drift**: The accumulated distortion produced when a block is repeatedly rewritten from its own prior value rather than from evidence. Each rewrite is faithful to the last and the chain diverges from the source, so drift is invisible in any single diff and visible only against the durable source or a behavioural baseline.

**Reconciliation**: The scheduled comparison of a block's current value against the durable sources behind its fields, resolving every disagreement in favour of the source and recording the correction as a revision. Reconciliation is a bounded periodic operation, not an opportunistic one.

**Behavioural probe**: A fixed task executed against three variants of the same configuration, with the current block, with the last known-good block, and with the block absent, used to detect influence changes that a textual diff does not reveal.

**Overflow**: The condition in which a validated candidate value exceeds a block's byte bound, its token bound, or the reserved region's bound. Overflow is detected before commit by arithmetic, and it is a rejection, never a silent truncation.

**Condense-in-place**: The bounded procedure that produces a complete smaller candidate value for one block under a preservation manifest, validated for protected-field retention before it may replace the current value.

**Protected field**: A field of a block value that must survive every condensation, rewrite, and rollback without loss. Protected fields are named in the contract and are the primary subject of post-commit verification.

**Attributed use**: The proportion of turns on which an output claim, a decision, or a tool argument is traceable to a rendered block, measured from citation identifiers rather than asserted. Automatic rendering counts as a read, so read counts alone are not evidence of usefulness.

**Ablation lift**: The paired difference in task quality, safety, or continuity between runs with a block rendered and runs with it removed, measured on identical cases. A block that shows no lift and no documented omission risk has not earned its residency.

**Shared block**: A block attached to more than one agent, so one committed edit becomes visible to every attached agent on its next inference. A shared writable block is a broadcast mutation surface and carries the blast radius of every reader.

**Block template**: The versioned definition fixing a block's label, description, schema, default bound, edit policy, validators, and render position for a class of agents, from which instances are created either by copy on instantiate or by reference on render.

### 1.2 Scope Boundary Against the Sibling Categories

This guide owns exactly one thing: the in-window durable slot and the discipline that governs the agent rewriting it. Every neighbouring capability is owned elsewhere, and this guide invokes those owners rather than redefining them.

**Against the memory-management category**: The durable stores are owned there. Working memory owns the task-scoped state object that governs one reasoning episode and is discarded when the episode closes; a block is not that object, and a block that carries episode-local scratch state has taken on working memory's job without working memory's disposal rule. Memory read and write operations own the canonical store, record versions, current pointers, idempotency keys, admission gates, and tombstones for durable memory; a block inherits those mechanics for its own revision history rather than inventing a second set. Memory consolidation owns evidence-gated promotion of raw episodes into durable memory; a block never receives content by consolidation directly, only a compact projection of what consolidation has already committed. Memory forgetting owns retention, decay, and erasure obligations; a block that overflows invokes that policy rather than deciding locally what to discard.

**Against the context-management umbrella**: Budget partitioning is owned there. The reserved block region is one partition among several, and its bound is set by the umbrella's budget arithmetic rather than by this guide. This guide supplies the partition's internal governance: what may occupy it, how large each occupant may be, and who may change an occupant.

**Against the write, select, compress, and isolate patterns**: Externalization discipline, admission of retrieved material, verified lossy reduction, and trust and tenant boundaries are owned by those guides. A block edit inherits the write path's extraction, deduplication, contradiction, and provenance controls. A condense-in-place operation invokes compression's preservation manifest and fidelity tests. A shared block requires an isolation review before any second agent is attached. A true block bypasses per-turn selection by construction, which is precisely why its content must justify permanent residency.

**Against hierarchical context architecture**: Scope precedence, inheritance, and conflict resolution are owned there. This guide states only how block templates and instances participate in that hierarchy and that a block is lower-authority context whenever it conflicts with a system, developer, legal, or tool-authorization rule.

**The single sentence that fixes the boundary**: Those guides own the durable stores and the assembly rules; this guide owns the in-window durable slot, its bounds, and the self-edit loop that mutates it.

### 1.3 The Residency Gate: Admitting and Refusing a Block

Permanent tokens require permanent utility. A block is charged on every applicable inference whether or not it is used, and every defect in it is exposed to every inference. Agents must therefore run a residency gate before any block is registered, returning admit, refuse, or a named alternative.

**Admission conditions**: Admit a candidate only where all of the following hold: the state is needed across turns or sessions; omission on an applicable turn materially reduces correctness, continuity, safety, or coordination; the useful representation is small and boundable; the content has one owner, one purpose, one schema, and one update cadence; exposure to every inference in the block's scope is authorized; the expected benefit exceeds the recurring token and cache-invalidation cost; and any model-proposed edit can be validated and reversed.

**Refusal conditions**: Refuse the candidate where the work is one-shot or stateless; where the content is a corpus, manual, transcript, or log; where a fact is cheap to retrieve and conditions a minority of turns; where an authoritative record must never be model-edited, such as a balance, an entitlement, a legal holding, an audit record, or a security policy; where secrets or sensitive personal data are not strictly necessary on every inference; where the state is a high-volume stream or a volatile counter; where contention requires transactional database semantics; where the value is deterministically derivable from an authoritative system; or where the candidate exists only because retrieval is inadequate.

**Residency Gate Decision Table**:

| Observable candidate property | Alternative that covers it | Gate verdict |
| :-- | :-- | :-- |
| Small, stable, needed on most applicable turns | None cheaper | Admit as a block |
| Large or rarely needed knowledge | Permission-aware retrieval | Refuse; retrieve on demand |
| Exact operational record that must not be model-edited | System of record with a read-only projection | Refuse; render a freshness-labeled projection |
| Episode-scoped plan, open variables, and error state | Working state object | Refuse; use working memory |
| Raw experience requiring audit fidelity | Immutable transcript or event log | Refuse; keep a pointer only |
| High-contention counter or assignment | Transactional store | Refuse; derive a read-only aggregate |
| Secret, credential, or regulated identifier | Secret store with scoped access | Refuse without exception |
| Cross-turn free-form notes with measured benefit | None, but bound is required | Admit as a task-scoped, aggressively bounded block |
| Content added because retrieval is weak | Fixed retrieval | Refuse; repair retrieval |

**Numeric gate rules**: Admit only where the candidate is projected to condition at least 40 percent of applicable turns and its rendered value fits within 5 percent of the context budget at the declared bound. Where the projected applicable-turn share is below 40 percent, refuse and route the candidate to retrieval. Where the whole reserved block region would exceed 15 percent of the context budget, refuse the marginal candidate and re-run the ablation review in Step 6.3 before admitting anything further. Where fewer than 3 evaluation cases exist on which the candidate's presence changes an output, refuse and record the missing evidence, because residency cannot be justified against an unmeasured benefit.

### 1.4 Execution Tier Partition

Every unit of work in this method belongs to exactly one tier, and the partition is what makes a self-editing region auditable rather than merely convenient.

**Deterministic tier**: Software, storage APIs, validators, and the renderer own block registration and contract storage, size-bound computation with the deployed tokenizer, invariant validation, authorization, concurrency checks, the commit transaction, post-commit verification, rollback, reconciliation scheduling, provenance binding, telemetry emission, and the ablation and drift measurements. These require exactness, reproducibility, and auditability that inference does not supply. A deterministic result must reproduce on replay of the same inputs; where it does not, it is a defect and not a judgement.

**Model tier**: Model inference owns proposing block content, judging what is worth retaining when a block is under capacity pressure, drafting the condensed candidate, phrasing a confidence marker, and adjudicating whether a low-lift block carries an omission risk the measurement did not observe. These require open-vocabulary judgement and synthesis that no rule covers. The model tier produces proposals and never produces authority.

**Hybrid tier**: The self-edit loop is hybrid in one direction: the model proposes an edit and the deterministic tier validates, commits, verifies, and returns evidence of the outcome. Reconciliation is hybrid in the other direction: software retrieves the durable source value and the model explains a divergence it cannot resolve mechanically, after which the source value is written regardless of the explanation.

**Authority on disagreement**: The deterministic tier holds authority in every disagreement, without exception. Where a model asserts an edit succeeded and no committed version exists, no edit occurred. Where a model judges a candidate value small enough, the tokenizer count governs. Where a block and its durable source disagree, the source wins and the block is corrected. Where a model argues that an invariant should yield to a better value, the invariant binds and the proposal is rejected.

**The prohibited delegations**: The model never advances a current pointer, never edits its own block description, size bound, edit policy, invariant set, permissions, or template ancestry, never decides that an over-bound value may be truncated to fit, never declares reconciliation complete, and never computes the ablation lift that justifies its own block.

**Tier ownership by artifact**:

| Artifact | Owning tier | Authority where the tiers disagree |
| :-- | :-- | :-- |
| Block contract, size bounds, and edit policy | Deterministic | Deterministic; a model request to widen a bound is an administrative change, not an edit |
| Rendered token counts and reserved-region accounting | Deterministic | Deterministic; a model estimate of block size is advisory only |
| Invariant validation and rejection verdicts | Deterministic | Deterministic; a rejected proposal produces no state change |
| Concurrency check, commit, and post-commit verification | Deterministic | Deterministic; commit state is read from the store, never inferred |
| Rollback selection and revision lineage | Deterministic | Deterministic; rollback creates a revision and never erases one |
| Reconciliation scheduling and source comparison | Deterministic | Deterministic; the durable source value replaces the block value |
| Provenance binding and source-class assignment | Deterministic | Deterministic; an unsourced claim is marked inferred, never promoted |
| Candidate block content and retention judgement | Model | Model proposes; the invariant set and the bound still bind absolutely |
| Condensed candidate value under capacity pressure | Model | Model drafts; the protected-field check may reject the draft |
| Confidence phrasing for an inferred claim | Model | Model phrases; the deterministic tier enforces that a marker is present |
| Divergence explanation during reconciliation | Hybrid | Model explains; the source value is written regardless |
| Retirement of a low-lift block | Hybrid | Model may assert an unmeasured omission risk; the measured lift governs after one review cycle |

***

## II. Operational Framework: Registered Self-Editing Slots Under Bounded Residency and Verified Commit

The framework assumes the residency gate in Section 1.3 has returned admit for at least one candidate. Phases 1 and 2 establish and assemble the block set. Phase 3 is the self-edit loop and runs on every proposed change. Phase 4 runs whenever Phase 3 detects a bound breach. Phase 5 runs on a schedule independent of any edit. Phase 6 runs continuously alongside the others and gates whether a block keeps its residency.

### Phase 1: Block Registration and Contract Declaration

**Objective**: Register every block with a declared purpose, schema, edit policy, size bound, and invariant set before any value exists, so that the first commit is validated against a contract rather than accepted on plausibility.

#### Step 1.1: Declare the Block Purpose, Schema, and Edit Policy

**Required Actions**:

- Assign an immutable identifier and a stable label that names an address rather than a value, such as an identity, profile, objective, or conventions slot.
- State the purpose as the decisions the block may influence and the omission failures it prevents, naming at least 1 decision it changes.
- Define the value schema with typed fields, and separate instruction-bearing fields from factual fields so that authority is visible in the structure rather than inferred from phrasing.
- Select exactly 1 edit policy from read-only, append-only, targeted-update, rewriteable, and approval-gated, defaulting to the most restrictive policy that supports the stated purpose.
- Partition the candidate content by owner, authority, sensitivity, scope, and update cadence, and split into separate blocks wherever any one dimension differs materially.
- Write the block description as an operational contract stating what belongs, what is forbidden, the evidence threshold for an update, and the action taken when capacity is insufficient.

**Block Set Catalogue**:

| Block class | Typical content | Default edit policy | Primary risk if unbounded |
| :-- | :-- | :-- | :-- |
| Operating identity | Role, mission, communication stance, behavioural invariants | Approval-gated | Autobiographical accumulation and sycophantic drift |
| User profile | Verified durable preferences with provenance and freshness | Targeted-update | Inference of unverified or protected traits |
| Active objective | Goal, acceptance criteria, phase, blockers, next action | Targeted-update | Divergence from the authoritative task record |
| Working constraints | Project or task rules that apply across most turns | Read-only | Duplication of higher-authority policy |
| Task scratchpad | Free-form cross-turn notes for one task | Rewriteable, task-scoped | Unreviewed dumping ground |
| Learned procedures | Short evaluated operational lessons | Approval-gated | Single-trajectory success rewriting general procedure |
| Project conventions | Naming, formatting, and interface conventions | Read-only | Peer edits without review |
| Coordination ledger | Compact shared handoff entries | Append-only | Broadcast corruption across attached agents |

**Block Contract Template**:

```
BLOCK_ID:
LABEL:
PURPOSE:
DECISIONS_INFLUENCED:
VALUE_SCHEMA_VERSION:
EDIT_POLICY:
BYTE_BOUND:
TOKEN_BOUND:
INVARIANT_SET_REF:
PROVENANCE_REQUIREMENT:
CONFIDENCE_MARKING_RULE:
OWNER:
SCOPE:
TRUST_CLASS:
SENSITIVITY_CLASS:
RENDER_POSITION:
TEMPLATE_ID_AND_VERSION:
RECONCILIATION_INTERVAL:
REVIEW_CADENCE:
REMOVAL_THRESHOLD:
```

**Required Outputs**:

- A registered block contract carrying every field of the contract template with no field left empty.
- A typed value schema separating instruction-bearing fields from factual fields.
- A block description stating allowed content, forbidden content, evidence threshold, and overflow action.

**Quality Checkpoints**:

- Every registered block carries exactly 1 edit policy drawn from the closed set of 5; a block with no declared policy is not renderable.
- Every block names at least 1 decision it changes; a block naming none is refused at registration.
- No block mixes 2 update cadences or 2 authority levels in one value; mixed blocks are split before registration completes.

***

#### Step 1.2: Set the Dual Size Bound and the Reserved Region Budget

**Required Actions**:

- Set a byte or character bound and a rendered-token bound for every block, computing the token bound with the tokenizer and renderer actually deployed.
- Derive the token bound from the block's task content rather than from a framework ceiling, and set it no higher than the largest observed useful value plus 30 percent headroom.
- Sum the token bounds of the attached block set, add the renderer's delimiter and metadata overhead, and record the total as the reserved block region.
- Compare the reserved region against the context budget declared by the umbrella budget partitioning, and reject the newest registration where the region would exceed 15 percent of that budget.
- Record the renderer version and tokenizer identity alongside both bounds, so that a change to either forces recomputation rather than silent drift.
- Cap the attached block count at 12 for a single agent, above which renderer overhead and precedence complexity exceed the benefit of further separation.

**Required Outputs**:

- A dual bound per block, expressed in bytes or characters and in rendered tokens.
- A reserved block region total stated in tokens and as a percentage of the context budget.
- A recorded renderer version and tokenizer identity bound to both limits.

**Quality Checkpoints**:

- Every block carries both bounds; a block with only a character limit is treated as unbounded and is not renderable.
- The reserved block region is at most 15 percent of the context budget; a breach blocks the newest registration rather than shrinking an existing bound silently.
- The attached block count is at most 12; exceeding it halts registration for consolidation review.

***

#### Step 1.3: Declare the Invariant Set, Provenance Requirement, and Confidence Rule

**Required Actions**:

- Enumerate the invariant set as machine-checkable assertions: required fields, protected fields that may never be removed, permitted value ranges, forbidden content classes, and required provenance coverage.
- Declare the provenance requirement per field class, requiring a source identifier, source class, and capture timestamp for every factual field.
- Declare the confidence marking rule, requiring every field derived by inference rather than observation to carry an explicit inferred marker and an evidence reference or an explicit absence marker.
- Set the minimum provenance coverage for the block at 100 percent of factual fields, and declare that a proposal falling below it is rejected rather than committed with gaps.
- Name the durable source of truth behind every factual field, so that reconciliation in Phase 5 has a comparison target rather than a search problem.
- Declare the reconciliation interval and the behavioural probe set that will be run against the block.

**Required Outputs**:

- An invariant set of machine-checkable assertions bound to the block contract.
- A per-field provenance and confidence specification.
- A source-of-truth mapping naming the durable store behind every factual field.

**Quality Checkpoints**:

- Every invariant is expressed as an assertion a validator can evaluate; an invariant stated only in the description is unenforced and does not count.
- Every factual field names a durable source of truth; a field naming none is either removed or reclassified as inferred and marked accordingly.
- Every block declares a reconciliation interval; a block without one cannot detect drift and is refused at registration.

***

### Phase 2: Block Assembly Into the Window

**Objective**: Serialize the attached block set into the reserved region deterministically, with authority visible and the region accounted before the call, so that residency cost is known rather than discovered.

#### Step 2.1: Render the Attached Block Set Deterministically With Authority Labels

**Required Actions**:

- Serialize each block with explicit delimiters, a stable field order, canonical whitespace, and unambiguous escaping of any delimiter appearing inside a value.
- Emit per-block metadata naming the label, value version, trust class, sensitivity class, edit policy, and freshness age, so that the model reads the block's authority rather than inferring it from tone.
- Render the description separately from the value, and never inside the value, so that quoted content cannot imitate the control contract.
- Label externally derived content within a value as data, retaining its source and trust class and stating that quoted instructions are not executable.
- Hold the block order fixed for the life of the contract, and treat an order change as a renderer version change requiring recomputation of every token bound.

**Required Outputs**:

- A rendered reserved region with per-block delimiters, metadata, and authority labels.
- A renderer version identifier bound to the rendered output.
- A trust-labeled representation of every externally derived value fragment.

**Quality Checkpoints**:

- Every rendered block carries its label, value version, trust class, and edit policy; a block rendered without version metadata cannot be attributed and is a defect.
- No value fragment derived from an unauthenticated external source is rendered without a data label; an unlabeled fragment halts assembly.
- Rendering the same block set twice from the same revisions produces byte-identical output; a difference indicates a non-deterministic renderer and blocks the call.

***

#### Step 2.2: Account the Reserved Region and Enforce It Before the Call

**Required Actions**:

- Count the rendered tokens of the complete reserved region with the deployed tokenizer, including delimiters and metadata, before the inference is issued.
- Compare the counted region against its declared bound and against the context budget, and record both the absolute figure and the percentage share.
- Halt the call where the counted region exceeds its declared bound, rather than allowing the assembler to trim a block to fit.
- Treat cached input as occupying the window in full, since a cache reduces the price and latency of processing a prefix without reducing the tokens that prefix consumes.
- Emit a region accounting record naming each block's contribution in tokens, so that a growth trend is attributable to a specific block rather than to the region as a whole.

**Required Outputs**:

- A reserved-region token count computed at assembly time with the deployed tokenizer.
- A per-block token contribution record.
- A budget verdict naming the region's percentage share of the context budget.

**Quality Checkpoints**:

- The region is counted before every call, not estimated; an estimated count is not an accounting record.
- The counted region is at or below its declared bound; a breach halts the call and raises a bound-enforcement event under Phase 4.
- Cached tokens are counted toward window occupancy; treating a cache hit as free occupancy is a defect that surfaces later as unexplained overflow.

***

#### Step 2.3: Order Blocks for Prefix Stability Without Deferring a Correctness Edit

**Required Actions**:

- Place invariant tool definitions and system instructions ahead of every block, since a prefix change invalidates the cached suffix that follows it.
- Order the block set from least to most frequently edited, placing read-only and approval-gated blocks before targeted-update and rewriteable blocks where authority and provider formatting permit.
- Place the most frequently edited block as late in the reserved region as its authority allows, immediately before dynamic turn content.
- Batch non-urgent edits so that one logical update produces one prefix change, and cap deferral of a batched edit at 1 turn.
- Commit a correctness-critical or safety-critical edit immediately, and never defer it to preserve cache reuse.
- Measure realised cache reuse from reported cached-token counts rather than assuming a block is cached, and attribute only the incremental reuse lost to the edit that caused it.

**Required Outputs**:

- A declared render order with each block's position justified by its edit frequency and authority.
- A cache-invalidation estimate per edit, expressed as tokens in the suffix that lost reuse.
- A measured cache reuse record drawn from reported cached-token counts.

**Quality Checkpoints**:

- Blocks appear in non-decreasing order of edit frequency wherever authority permits; an inversion is recorded with the authority reason that forced it.
- No safety-critical or correctness-critical edit is deferred for cache economy; a deferral of such an edit is an incident, not an optimisation.
- Cache reuse is reported from measured cached-token counts; an assumed cache hit is not evidence and does not enter the cost record.

***

### Phase 3: Proposed-Edit Validation and Commit

**Objective**: Convert a model-proposed change into either a verified committed revision or a rejection with no state change, so that self-editing can never silently degrade a block that was previously correct.

#### Step 3.1: Compose a Typed Proposal Against the Current Revision

**Required Actions**:

- Fetch the current revision, hash, description, schema, bounds, and edit policy from the store before composing anything; never edit from the copy rendered in the window, which may be one or more revisions stale.
- Confirm that an allowed update trigger has fired and that the candidate content has cleared the write path's extraction, deduplication, contradiction, and provenance controls.
- Select the least destructive operation the change permits: append for an independent ledger entry, targeted replace for one known field or span, and full rewrite only where reorganisation or condensation is genuinely required.
- Emit a typed proposal carrying the block identifier, the expected version, the operation, the patch or candidate value, the reason, the evidence references, the initiating run, and an idempotency key.
- Mark every proposed field as observed or inferred, attaching the evidence reference for an observed field and the derivation for an inferred one.
- Route the proposal to the background editing principal rather than the interactive path where the change is a reorganisation, a consolidation, or a review that no current turn depends on.

**Edit Proposal Record**:

```
PROPOSAL_ID:
BLOCK_ID:
EXPECTED_VERSION:
EXPECTED_HASH:
OPERATION:            append | targeted_replace | rewrite
TARGET_FIELD_OR_SPAN:
CANDIDATE_VALUE_OR_PATCH:
REASON:
UPDATE_TRIGGER:
EVIDENCE_REFERENCES:
FIELD_MARKING:        observed | inferred, per field
SOURCE_CLASS:
INITIATING_RUN_ID:
IDEMPOTENCY_KEY:
ARCHIVAL_PERMITTED:   true | false
```

**Required Outputs**:

- A typed edit proposal carrying every field of the proposal record.
- A recorded expected version and hash naming the revision the proposal was composed against.
- A per-field observed or inferred marking with its supporting reference.

**Quality Checkpoints**:

- The proposal names an expected version fetched from the store within the same operation; a proposal composed against a rendered copy is rejected before validation.
- The selected operation is the least destructive one that achieves the change; a full rewrite proposed where a targeted replace suffices is returned for recomposition.
- Every proposed field carries an observed or inferred marking; an unmarked field fails composition and never reaches the validator.

***

#### Step 3.2: Validate the Proposal Against Schema, Bounds, and the Invariant Set

**Required Actions**:

- Authorize the proposal against tenant, agent, scope, operation, and sensitivity, denying by default where attachment or ownership is ambiguous.
- Parse and normalize the candidate, then validate encoding, schema conformance, required fields, immutable fields, and forbidden field classes.
- Evaluate the block's declared invariant set against the complete post-edit value rather than against the patch, since an append that satisfies every field rule can still remove a protected field through a schema-level side effect.
- Simulate the render: serialize the full attached block set with the candidate in place, count tokens with the deployed tokenizer, and check both the block bound and the reserved-region bound.
- Screen for prompt-injection and instruction-laundering patterns, secrets, credentials, regulated identifiers, cross-scope references, unsupported factual claims, missing provenance, and self-flattering or identity-altering language.
- Compare the semantic distance between the current value and the candidate against the stated edit reason, and reject a change whose magnitude exceeds what the reason accounts for.
- Compare the expected version against the current pointer, and on mismatch reload and rebase a targeted edit once, retry a commutative append under its idempotency key, or route the conflict to review.

**Required Outputs**:

- An authorization verdict with the policy that produced it.
- A validation report naming each check, its verdict, and the failing assertion where applicable.
- A simulated render measurement naming the post-edit block size and reserved-region size.

**Quality Checkpoints**:

- Validation evaluates the complete post-edit value against the invariant set; validating the patch alone is a defect that admits protected-field loss.
- A failed validation produces a rejection and no state change; a degraded block is never accepted with a warning attached.
- Automatic rebase is attempted at most 1 time for a targeted edit before the conflict is escalated; unbounded rebase cycling is prohibited.

***

#### Step 3.3: Commit Atomically, Verify, and Roll Back on Failed Verification

**Required Actions**:

- Create the immutable revision and advance the current pointer in a single transaction, writing the audit event before the success acknowledgement is returned.
- Read back the committed revision, verify its hash, re-render it, and re-count its tokens against the bound.
- Run the block's post-commit invariant assertions and its fast behavioural probes, comparing results against the pre-commit baseline.
- Create a rollback revision to the last known-good value where any post-commit check fails, quarantine the failed proposal, and raise an alert at the block's risk level.
- Return the committed version identifier or the rejection reason to the proposing agent, so that the model's belief about the block's state comes from the store rather than from its own tool-call intent.
- Invalidate or re-evaluate every derivative built from the block, including summaries, caches, and derived blocks, whenever a rollback follows a suspected poisoning or a protected-invariant breach.

**Required Outputs**:

- A committed immutable revision with predecessor version, hash, actor, reason, and validation result, or a rejection record with no state change.
- A post-commit verification record covering hash, render, bound, invariants, and probe results.
- A rollback revision and incident record where verification failed.

**Quality Checkpoints**:

- Every edit terminates in exactly 1 of 4 states: committed and verified, rejected with no state change, conflicted and queued or rebased, or rolled back with an incident record; an unknown commit state is never an acceptable exit.
- The proposing agent receives the committed version identifier or the rejection reason; an edit is never treated as successful on the strength of the proposal alone.
- A rollback creates a new revision naming the reverted versions; erasing a bad revision destroys the evidence the incident review requires and is prohibited.

***

### Phase 4: Bound Enforcement and Overflow Disposition

**Objective**: Dispose of every candidate value that exceeds a bound through a declared path that preserves the current value, so that capacity pressure never resolves itself as silent loss.

#### Step 4.1: Reject the Over-Bound Proposal and Classify the Overflow

**Required Actions**:

- Reject the direct commit without changing the current value whenever the simulated render exceeds the block bound or pushes the reserved region above its declared share.
- Classify the overflow by its cause: growth of legitimate new state, accumulation of superseded entries, paraphrase expansion without new information, or a block whose declared bound was set below its real requirement.
- Identify and freeze the protected fields, active commitments, unresolved items, provenance pointers, and exact strings that must survive any subsequent reduction.
- Remove deterministic waste before any model-drafted reduction is attempted: obsolete formatting, duplicated rendering metadata, and entries already superseded under an explicit schema rule.
- Record the overflow event with the candidate size, the bound, the overage, and the classification, so that a recurring class is visible as a design defect rather than as a series of incidents.

**Overflow Disposition Table**:

| Overflow classification | Permitted disposition | Prohibited response |
| :-- | :-- | :-- |
| Superseded entries accumulated | Deterministic removal under the schema's supersession rule | Retaining both versions and trimming the tail |
| Paraphrase expansion without new information | Condense-in-place under a preservation manifest | Accepting the expansion and widening the bound |
| Legitimate new state exceeding a correct bound | Demotion of the lowest-value content through lifecycle policy | Truncating the oldest content to make room |
| Legitimate new state exceeding an undersized bound | Administrative bound revision with re-accounting of the region | Automatic bound expansion by the editing agent |
| Content that never justified residency | Removal of the block and routing to retrieval | Splitting the block to evade the region bound |
| No verified candidate fits | Refusal of the write and owner escalation | Committing an unverified condensation |

**Required Outputs**:

- A rejection record naming the candidate size, the breached bound, and the overage in tokens.
- An overflow classification drawn from the closed set in the disposition table.
- A protected-field manifest listing what any reduction must preserve exactly.

**Quality Checkpoints**:

- The current value is unchanged after an over-bound rejection; a partially applied edit is a defect regardless of how much of it validated.
- Every overflow carries a classification from the closed set; an unclassified overflow cannot be routed and halts the edit.
- Deterministic waste removal precedes any model-drafted reduction; drafting a condensation before removing superseded entries wastes the reduction budget on content that should not exist.

***

#### Step 4.2: Execute a Verified Condense-in-Place Attempt

**Required Actions**:

- Invoke the compression discipline owned by the context-compression guidance, supplying the current value, the candidate, and the protected-field manifest as a preservation manifest.
- Require the reduction to produce one complete candidate value rather than a stream of partial in-place edits, so that the result can be validated as a whole.
- Validate the condensed candidate for protected-field retention, schema conformance, invariant satisfaction, provenance coverage, and both bounds, comparing against the pre-condensation revision.
- Run the block's behavioural probes against the condensed candidate and reject any candidate whose probe results diverge from the pre-condensation baseline beyond the declared tolerance.
- Commit the verified candidate under compare-and-swap, recording every archived or removed item and its destination in a displacement manifest.
- Cap condensation attempts at 3 per overflow event, using a less destructive schema-level strategy on each successive attempt, and stop rather than continuing to redraft.

**Required Outputs**:

- One complete condensed candidate value per attempt.
- A validation record covering protected-field retention, invariants, provenance, and both bounds.
- A displacement manifest naming every archived or removed item and its destination.

**Quality Checkpoints**:

- Every protected field named in the manifest appears in the condensed candidate exactly; a missing protected field rejects the candidate regardless of how well the remainder reads.
- Condensation attempts do not exceed 3 per overflow event; a fourth attempt is prohibited and routes the event to Step 4.3.
- A candidate that fits both bounds but fails verification is treated as a failure; fitting is not evidence of fidelity.

***

#### Step 4.3: Escalate an Unresolvable Overflow to Demotion, Split, or Removal

**Required Actions**:

- Preserve the current revision and refuse the write explicitly where no verified candidate fits within the attempt cap.
- Invoke the memory-forgetting and lifecycle policy owned elsewhere to demote or archive content that no longer justifies residency, rather than inventing a local eviction rule.
- Propose a split by coherent function where the block has accumulated 2 or more distinct purposes, and never split merely to place the same content under 2 bounds.
- Propose an administrative bound revision only where the block's real requirement was measured and the reserved region can absorb the increase within its 15 percent share.
- Propose removal of the block and replacement by retrieval where the overflow classification is content that never justified residency.
- Alert the named owner with the overflow history, the attempted dispositions, and the recommended redesign, and hold the block in proposal-only mode until the owner responds.

**Required Outputs**:

- An explicit write refusal with the current revision preserved and named.
- A redesign recommendation naming demotion, split, bound revision, or removal.
- An owner alert carrying the overflow history and the recommended action.

**Quality Checkpoints**:

- No bound is widened automatically; a bound change is an administrative operation requiring owner approval and region re-accounting.
- A split produces blocks with distinct purposes, owners, and cadences; a split that reproduces the same purpose twice is rejected as bound evasion.
- The block remains in proposal-only mode until the owner responds; continuing autonomous edits against a block that cannot accept them accumulates rejections without progress.

***

### Phase 5: Drift Reconciliation Against Durable Sources

**Objective**: Correct the accumulated divergence between a repeatedly self-edited block and the durable sources behind its claims, on a declared interval, with the source holding authority in every disagreement.

#### Step 5.1: Trigger Reconciliation on the Declared Interval and on Named Events

**Required Actions**:

- Run reconciliation for every block after at most 25 committed edits or 24 hours of continuous residency, whichever occurs first, and after at most 10 committed edits for any block classified as high-impact.
- Run reconciliation immediately on any of these events: a drift metric breaching its threshold, a change to the model, tokenizer, renderer, or template, a rollback following a suspected poisoning, or an incident linking an output to a block.
- Switch the block to proposal-only mode for the duration of the reconciliation, so that the value being compared does not move during the comparison.
- Load the current value, the last approved baseline, the intervening revision chain, the contract, the evidence references, and every derivative built from the block.
- Record the reconciliation start with the triggering rule, so that an interval that is repeatedly pre-empted by event triggers is visible as an unstable block rather than as normal operation.

**Reconciliation Record**:

```
RECONCILIATION_ID:
BLOCK_ID:
TRIGGER:              interval_edits | interval_time | drift_metric |
                      component_change | incident
CURRENT_VERSION:
BASELINE_VERSION:
EDITS_SINCE_BASELINE:
FIELDS_COMPARED:
FIELDS_AGREEING:
FIELDS_DIVERGENT:
FIELDS_UNSOURCED:
DIVERGENCE_DISPOSITION: source_written | field_removed | marked_inferred
PROBE_RESULT:         pass | fail, per probe
OUTCOME:              baseline_reset | rollback | frozen
```

**Required Outputs**:

- A reconciliation event record naming the trigger and the versions compared.
- A block held in proposal-only mode for the duration of the comparison.
- A loaded evidence set covering the current value, the baseline, and the revision chain between them.

**Quality Checkpoints**:

- No block exceeds 25 committed edits or 24 hours of residency without a reconciliation; exceeding either bound suspends autonomous edits on that block.
- The block is in proposal-only mode while reconciliation runs; a value that changes mid-comparison invalidates the comparison and forces a restart.
- Every reconciliation names its trigger from the closed set; an untriggered reconciliation cannot be distinguished from an ad hoc rewrite.

***

#### Step 5.2: Reconcile Every Factual Field Against Its Durable Source

**Required Actions**:

- Retrieve the current value of every factual field from the durable source of truth named in the block contract, and compare it against the value held in the block.
- Write the source value into the block wherever the two disagree, without exception; a block claim never overrides its named source, and the model's explanation of a divergence is recorded but does not change the outcome.
- Remove or reclassify any field whose named source no longer holds a value for it, marking it inferred with an explicit absence-of-evidence marker rather than leaving it as an unqualified assertion.
- Recompute provenance coverage and confidence marking across the whole value, and reject any field that has lost its evidence reference through an intervening rewrite.
- Compute the structural diff, the semantic distance from the approved baseline, protected-field changes, unsourced-claim fraction, provenance loss, churn, and sensitivity changes, and publish each component rather than only their composite.
- Attribute every change to one of five causes: justified new state, harmless rewording, renderer or tokenizer sensitivity, poisoning, and unsupported drift, and route the last two to incident handling rather than to acceptance.

**Required Outputs**:

- A per-field reconciliation verdict naming agreement, divergence with the source value written, or reclassification.
- A published drift component set with each component's value and threshold.
- A cause attribution for every change since the baseline.

**Quality Checkpoints**:

- Every divergence between a block field and its durable source resolves in favour of the source; a divergence resolved in favour of the block is a defect regardless of the block's internal consistency.
- Provenance coverage after reconciliation is 100 percent of factual fields; a field that cannot be sourced is reclassified as inferred, never retained as fact.
- Drift components are published individually; a severe protected-field violation concealed inside an averaged composite defeats the measurement.

***

#### Step 5.3: Probe Behaviour and Reset the Baseline or Restore a Known-Good Revision

**Required Actions**:

- Run the fixed behavioural probe set three ways, with the reconciled block, with the last approved baseline block, and with the block absent, holding model, tools, prompts, and data constant.
- Include probes for counter-sycophancy, injection following, stale-fact influence, tool-parameter drift, and authority precedence, since a textual diff can appear benign while influence has changed.
- Accept the reconciled value and reset the approved baseline only where every source comparison resolved and every probe result falls within the declared tolerance.
- Roll back to the last known-good revision where any probe fails, quarantine the suspect revisions, and inspect every shared or derived block built from the block under review.
- Re-run the probes after a rollback, and where behaviour remains changed, rebuild the derived context and investigate the model, cache, tool, and external-state changes rather than declaring the incident closed.
- Keep the block frozen in read-only mode where a high-impact difference remains unexplained after rollback and re-probing.

**Required Outputs**:

- A three-way probe result set with current, baseline, and absent variants.
- Either a reset approved baseline or a restored known-good revision with an incident record.
- A derivative inspection record naming every shared or derived block examined.

**Quality Checkpoints**:

- Acceptance requires both a resolved source comparison and passing probes; text that reads correctly is not evidence that influence is unchanged.
- Probes are re-run after every rollback; a rollback whose effect on behaviour was never measured is an assumption, not a remediation.
- An unexplained high-impact difference leaves the block frozen; restoring write access to a block whose behaviour is not understood repeats the incident.

***

### Phase 6: Provenance, Instrumentation, and Residency Review

**Objective**: Make every block claim traceable to its origin, every block event measurable, and every block's continued residency conditional on demonstrated benefit.

#### Step 6.1: Bind Provenance and Enforce Confidence Marking on Rendered Content

**Required Actions**:

- Bind every factual field to a stable evidence reference at commit time, comprising the source identifier, the source class, the capture timestamp, and the extraction or inference that produced it.
- Render the marking with the value rather than storing it only in the contract, so that the distinction between an observed fact and an inferred one is visible on the turn the model reads it.
- Render a freshness age beside every field carrying a declared validity interval, and mark a field past its expiry as stale rather than removing it silently.
- Reject at validation any factual field whose evidence reference is absent, and require an inferred field to carry either a derivation reference or an explicit absence-of-evidence marker.
- Emit internal block citations as a stable reference comprising the block identifier, the value version, and the field path, so that an output claim can be traced to the exact revision that supplied it.
- Treat an internal block citation as an attribution aid and never as a substitute for the external evidence citation a factual claim requires.

**Required Outputs**:

- A per-field evidence binding stored with the revision and rendered with the value.
- A rendered confidence and freshness marking for every field.
- Internal block citations resolvable to a block identifier, value version, and field path.

**Quality Checkpoints**:

- Every rendered factual field carries an observed or inferred marker; an unmarked field is read as established fact and is a defect.
- Every factual field carries an evidence reference or an explicit absence marker; a field with neither fails validation and is never committed.
- An internal block citation resolves to an existing revision and field path; an unresolvable citation invalidates the attribution it was written to support.

***

#### Step 6.2: Instrument Block Events and Compute the Block Metric Set

**Required Actions**:

- Log every proposal, rejection, commit, conflict, rollback, overflow, reconciliation, and administrative change with the block identifier, version before and after, sizes against bounds, operation, reason, evidence references, actor, run identifier, authorization verdict, validation results, concurrency result, latency, and cache-invalidation estimate.
- Log every render with the block identifier, value version, rendered position, tokens, reserved-region total, cache eligibility and outcome, freshness age, trust class, and whether the output relied on, cited, or contradicted the block.
- Keep block values and diffs in a separately protected audit store, and place only hashes, counts, classifications, and authorized references in general telemetry.
- Compute per block, per template version, and per time window: capacity utilization, prompt share, attributed-use rate, edit acceptance rate, conflict rate, rollback rate, overflow rate, drift components, staleness exposure, edit churn, and cache-invalidation cost.
- Retain counts and denominators with every ratio, since a rate computed on a handful of turns is not evidence and a rate without a denominator cannot be compared across windows.
- Prefer attributed-use and verified-use over read counts, because automatic rendering registers a read on every applicable turn whether or not the block influenced anything.

**Required Outputs**:

- An append-only block event log covering edits, renders, and administrative changes.
- A computed metric set per block with counts and denominators retained.
- A separation record showing which fields are in protected audit storage and which are in general telemetry.

**Quality Checkpoints**:

- Every committed revision has a corresponding audit event written before the success acknowledgement; an acknowledged commit with no event is an instrumentation defect.
- No block value or diff appears in general telemetry; a sensitive value in a broad trace is an exposure incident regardless of the block's usefulness.
- Every reported rate carries its numerator and denominator; a bare percentage is not admissible as evidence in the residency review.

***

#### Step 6.3: Run the Paired Ablation Review and Retire Unearned Blocks

**Required Actions**:

- Run the evaluation set with the complete block set, then remove exactly 1 block at a time while holding model, tools, prompts, and data constant.
- Measure task quality, safety, continuity, token cost, latency, and cache metrics for each ablation, reporting paired differences with confidence intervals rather than single-run figures.
- Retire or demote any block whose ablation lift is not positive at the declared confidence level and which carries no documented omission risk accepted by its owner.
- Replace residency with conditional retrieval where a block helps only a narrow class of turns, defined as a class covering less than 40 percent of applicable turns.
- Redesign the description, authority, or schema of a block that produces regressions, rather than compensating for it with additional prompting.
- Repeat the loop until every resident block clears its declared minimum lift threshold and the complete set clears the reserved-region bound, and record the review date, owner, and next removal threshold.

**Required Outputs**:

- A paired ablation result per block with confidence intervals on quality, safety, and continuity.
- A retirement, demotion, or retention decision per block with its supporting measurement.
- An updated review record naming the owner, the review date, and the removal threshold.

**Quality Checkpoints**:

- Every resident block has a positive measured ablation lift or a documented and owner-accepted omission risk; residency without either is unjustified and the block is removed.
- Ablations change exactly 1 block per run; removing several at once cannot attribute the resulting change to any of them.
- The review record names a next review date and a removal threshold; a block with no scheduled review accumulates cost without a mechanism that ends it.

***

## III. Implementation Guidance for AI Agents

AI agents operating memory blocks must follow systematic protocols ensuring that a region they both read and rewrite remains bounded, validated, traceable, and reversible. The following guidance translates the framework above into agent-executable instruction, and its organising rule is that the component proposing a block value is never the component that commits it.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Registry Component**: Owns block contracts, size bounds, invariant sets, edit policies, template lineage, and the source-of-truth mapping. It alone may change a contract, and every change is versioned and requires owner approval. It refuses to register a block lacking a bound, an invariant set, or a reconciliation interval.
2. **Assembly Renderer**: Serializes the attached block set deterministically, emits authority and trust metadata, counts the reserved region with the deployed tokenizer, and holds the budget veto. It halts the call when the region exceeds its bound and never trims a block to fit.
3. **Proposal Agent**: Model-tier component that composes candidate values, selects the least destructive operation, marks each field observed or inferred, and emits the typed proposal. It never advances a pointer, never edits a contract, and never treats its own output as committed state.
4. **Validation Gate**: Deterministic component that authorizes, parses, validates schema and invariants over the complete post-edit value, simulates the render, screens for injection and sensitive content, and checks concurrency. It returns accept or reject and never returns accept with a warning.
5. **Commit Authority**: Owns the atomic transaction that writes the immutable revision and advances the current pointer, the post-commit verification, the rollback revision, and the evidence returned to the Proposal Agent. It is the only component that knows whether an edit occurred.
6. **Reconciliation Component**: Owns the interval and event schedule, retrieves durable source values, resolves every divergence in favour of the source, runs the three-way behavioural probes, and either resets the baseline or restores a known-good revision.
7. **Instrumentation Component**: Writes the append-only event log, enforces the separation between protected audit storage and general telemetry, computes the metric set, and runs the ablation harness. It may withhold a release where an instrumentation gap prevents the residency review.

**Workflow Execution Pattern**:

```
STATE: Block_Edit_Proposed
INPUTS:
  1. Current revision, hash, contract, and invariant set from the registry
  2. Typed edit proposal from the Proposal Agent
  3. Reserved-region accounting from the Assembly Renderer
ACTIONS:
  1. Authorize actor, scope, operation, and sensitivity
  2. Validate schema and invariants over the complete post-edit value
  3. Simulate render and count tokens against both bounds
  4. Screen for injection, secrets, and unsupported claims
  5. Compare expected version against the current pointer
VALIDATION:
  - authorization_verdict == ALLOW
  - invariant_violations == 0
  - post_edit_block_tokens <= block_token_bound
  - reserved_region_tokens <= region_token_bound
  - provenance_coverage_factual_fields == 100
  - unmarked_inferred_fields == 0
  - expected_version == current_pointer
TRANSITIONS:
  IF all_validations_pass THEN next_state = Atomic_Commit_And_Verify
  IF expected_version != current_pointer THEN next_state = Rebase_Once_Or_Queue
  IF bound_exceeded THEN next_state = Overflow_Disposition
  IF invariant_violations > 0 THEN next_state = Reject_No_State_Change
```

**Two-Phase Action Pattern**: Emit the typed proposal with its expected version, operation, reason, and evidence without applying it; confirm it against the validation block while no revision exists and no pointer has moved; commit it only after validation passes, writing the audit event in the same operation that advances the pointer.

**Approval Gate**: Human authorisation is required before any change to a block contract, bound, edit policy, invariant set, permission, or template ancestry; before the first attachment of any block to a second agent; before any edit to an identity, security, compliance, or shared-policy block; and before any bound revision that would raise the reserved region above 15 percent of the context budget. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold contracts, revisions, and pointers in durable storage outside the window, since a block outlives every context in which it is rendered.
- Fetch the current revision from the store at the start of every edit, never from the rendered copy, which is stale by construction whenever a background writer is active.
- Give a background or asynchronous editing agent its own principal, its own block allowlist, expected-version commits, its own budget, and its own trace; asynchrony is not a trust property.
- Count the reserved region toward the context budget on every call, including turns on which no block is used, since residency charges whether or not it pays.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Registration Integrity (After Phase 1)**

- **Automated Check**: Every block carries both bounds, exactly 1 edit policy, a machine-checkable invariant set, a reconciliation interval, and a named durable source for every factual field; the attached block count is at most 12.
- **Agent Action on Pass**: Permit attachment and proceed to assembly.
- **Agent Action on Failure**: Refuse registration and return the missing contract fields; no block is rendered against an incomplete contract.
- **Human Review Trigger**: A factual field for which no durable source of truth exists, or an identity, security, or compliance block at first registration.

**Checkpoint 2: Assembly Integrity (After Phase 2)**

- **Automated Check**: The rendered region is byte-identical across two renders of the same revisions; every block carries label, version, trust class, and edit policy metadata; the counted region is at or below both its declared bound and 15 percent of the context budget.
- **Agent Action on Pass**: Issue the inference.
- **Agent Action on Failure**: Halt the call and raise a bound-enforcement event; the assembler never trims to proceed.
- **Human Review Trigger**: A reserved region above 15 percent of the context budget after one consolidation attempt.

**Checkpoint 3: Edit Validity (After Phase 3)**

- **Automated Check**: Exactly 1 terminal state per edit from the set of committed and verified, rejected, conflicted, or rolled back; 0 invariant violations in any committed revision; provenance coverage at 100 percent of factual fields; the proposing agent received a committed version or a rejection reason.
- **Agent Action on Pass**: Release the new revision for rendering.
- **Agent Action on Failure**: Roll back to the last known-good revision and quarantine the proposal.
- **Human Review Trigger**: More than 2 rollbacks on one block within 50 committed edits, or any rollback attributed to suspected poisoning.

**Checkpoint 4: Overflow Disposition (After Phase 4)**

- **Automated Check**: The current value is unchanged after every rejected over-bound proposal; every overflow carries a classification from the closed set; condensation attempts per event are at most 3; every condensed commit carries a displacement manifest.
- **Agent Action on Pass**: Resume normal edit mode.
- **Agent Action on Failure**: Refuse the write, preserve the current revision, and hold the block in proposal-only mode.
- **Human Review Trigger**: A third overflow event on one block within 30 days, or any proposal to widen a bound.

**Checkpoint 5: Reconciliation Validity (After Phase 5)**

- **Automated Check**: No block exceeds 25 committed edits or 24 hours of residency without reconciliation; every divergence resolved in favour of the durable source; provenance coverage restored to 100 percent; probes run three ways against current, baseline, and absent variants.
- **Agent Action on Pass**: Reset the approved baseline and restore normal edit mode.
- **Agent Action on Failure**: Restore the known-good revision, freeze the block, and inspect derived and shared blocks.
- **Human Review Trigger**: An unexplained high-impact behavioural difference surviving a rollback and re-probe.

**Checkpoint 6: Residency Justification (After Phase 6)**

- **Automated Check**: Every resident block carries a positive paired ablation lift or an owner-accepted omission risk; every rate carries its denominator; no block value or diff appears in general telemetry; every block has a next review date and a removal threshold.
- **Agent Action on Pass**: Retain the block set and publish the metric report.
- **Agent Action on Failure**: Retire or demote the unjustified blocks and re-run the region accounting.
- **Human Review Trigger**: Any block retained on an omission-risk argument for 2 consecutive review cycles without measured lift.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
BLOCK_ID:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Unbounded Block Growth**

- **Symptoms**: Capacity utilization and edit churn rise together while attributed use and ablation lift fall; the reserved region grows without a corresponding change in task outcomes; overflow events recur on the same block.
- **Diagnostic Steps**: Classify the current value by field origin, separating superseded entries, paraphrase expansion, and genuinely new state; compare the block's declared purpose against the purposes its fields actually serve.
- **Resolution Protocol**: Option A, remove superseded entries under the schema's supersession rule and re-measure. Option B, split the block by coherent function where 2 or more distinct purposes are present. Option C, demote the lowest-value content through lifecycle policy and replace it with a retrieval path. Option D, retire the block where the growth is content that never justified residency.
- **Escalation Trigger**: A third overflow event on one block within 30 days escalates to owner redesign; automatic bound expansion is prohibited and is never an available resolution.

**Error Type 2: Silent Content Loss on Self-Edit**

- **Symptoms**: A protected field, an active commitment, or a provenance pointer is absent after a commit that reported success; the model repeats a question whose answer the block previously held; a rewrite reads fluently and is shorter than the value it replaced.
- **Diagnostic Steps**: Diff the committed revision against its predecessor field by field, confirm whether the invariant set contained an assertion covering the lost field, and determine whether validation ran against the patch rather than the complete post-edit value.
- **Resolution Protocol**: Option A, roll back to the last verified revision and add the missing assertion to the invariant set. Option B, restrict the block's edit policy from rewriteable to targeted-update so that whole-value replacement requires approval. Option C, add the lost field to the protected-field manifest so that every condensation validates its retention.
- **Escalation Trigger**: Any loss of a field named in the protected-field manifest halts autonomous edits on that block until the invariant gap is closed; this class is never resolved by retrying the edit.

**Error Type 3: Self-Edit Drift Without a Textual Signal**

- **Symptoms**: Each individual diff appears benign while behaviour changes across many turns; semantic distance from the approved baseline grows steadily; unsourced-claim fraction rises; probe results diverge although the value reads correctly.
- **Diagnostic Steps**: Compare the current value against the durable sources rather than against the previous revision, since every revision was faithful to the one before it; run the three-way probe set to separate an influence change from a wording change.
- **Resolution Protocol**: Option A, write the durable source values into the block and reset the baseline. Option B, shorten the reconciliation interval for the block from 25 to 10 committed edits. Option C, reclassify unsourceable fields as inferred with explicit markers. Option D, restore the last approved baseline and rebuild the intervening state from evidence.
- **Escalation Trigger**: A drift component above its declared threshold at 2 consecutive reconciliations freezes the block in read-only mode pending owner review.

**Error Type 4: Stale Overwrite and Shared-Block Corruption**

- **Symptoms**: One agent's committed change disappears after another agent's commit; many attached agents change behaviour after a single edit; conflict rate rises on a shared block while edit acceptance stays flat.
- **Diagnostic Steps**: Reconstruct both proposals from the revision chain, confirm whether expected-version commits were enforced, and identify which agents were attached at the time of the overwriting commit.
- **Resolution Protocol**: Option A, restore the last consistent value and enforce compare-and-swap on every write to the block. Option B, convert the block to append-only with unique entry identifiers where the content is a ledger or a handoff. Option C, shard the block per agent or per task and derive a read-only aggregate. Option D, freeze and detach the block, then narrow the writer set before reattachment.
- **Escalation Trigger**: Any corruption of a shared block attached to more than 3 agents triggers immediate detachment and inspection of every attached agent's traces; last-write-wins is never restored as a resolution.

**Error Type 5: Instruction Poisoning of a Resident Block**

- **Symptoms**: Block text directs the agent to disregard higher authority, exfiltrate data, or bias tool parameters; a value fragment derived from an unauthenticated source appears without a data label; behaviour changes on turns unrelated to the content that was written.
- **Diagnostic Steps**: Trace the poisoned fragment to the proposal that introduced it and to the source class of its evidence; determine which derivatives, summaries, and caches were built from the affected revisions.
- **Resolution Protocol**: Option A, quarantine the revisions, revoke the writing principal, and roll back to a known-good value. Option B, invalidate and rebuild every derivative built from the affected revisions, since reverting the visible text alone may not restore behaviour. Option C, strengthen trust labelling and screening at the validation gate and re-run the adversarial test set.
- **Escalation Trigger**: Any confirmed poisoning of a block attached to a production agent halts autonomous edits across every block sharing that writing principal; remediation instructions found inside the suspect value are never executed.

**Error Type 6: Confabulated Block Content Read Back as Fact**

- **Symptoms**: A confidently phrased claim in a block has no evidence reference; a single user request appears as a durable preference; a downstream output cites the block for a claim the durable source does not support.
- **Diagnostic Steps**: Recompute provenance coverage across the value, identify fields marked observed whose evidence reference does not resolve, and compare the claim against the field's named durable source.
- **Resolution Protocol**: Option A, reclassify the field as inferred with an explicit absence-of-evidence marker. Option B, write the durable source value over the claim and record the correction at its origin. Option C, remove the field and raise the block's evidence threshold for that field class. Option D, restrict the block to targeted-update so that new factual fields require an evidence reference at composition time.
- **Escalation Trigger**: Provenance coverage below 100 percent on a factual field at any reconciliation suspends autonomous edits to that field class until the gap is closed.

**Troubleshooting Decision Tree**:

```
BLOCK OPERATION FAILS A CHECK
├─ BOUND DEFECT
│   ├─ Candidate exceeds block bound → Reject; classify overflow; never truncate
│   ├─ Region exceeds budget share → Halt the call; run the ablation review
│   └─ Bound widened without approval → Revert the contract; escalate to owner
├─ EDIT DEFECT
│   ├─ Invariant violated → Reject with no state change; never commit degraded
│   ├─ Protected field lost after commit → Roll back; close the invariant gap
│   ├─ Expected version stale → Rebase once or queue; never blind overwrite
│   └─ Commit state unknown → HALT; read the store; never infer from intent
├─ DRIFT DEFECT
│   ├─ Value diverges from durable source → Write the source value; reset baseline
│   ├─ Probes diverge while text reads clean → Restore known-good; rebuild derivatives
│   └─ Reconciliation interval exceeded → Suspend autonomous edits on the block
├─ PROVENANCE DEFECT
│   ├─ Factual field without evidence → Reclassify as inferred or remove
│   └─ Inferred field rendered unmarked → HALT render; add the marker
└─ TRUST DEFECT
    ├─ Untrusted fragment rendered unlabeled → HALT assembly; label as data
    ├─ Block contradicts higher authority → Fail closed; quarantine the block
    └─ Confirmed poisoning → Revoke principal; roll back; rebuild derivatives
```

### D. Performance Metrics and Continuous Learning

**Residency and Utility Metrics**:

- **Ablation lift**: Paired quality difference with and without the block on identical cases (target: positive at the declared confidence level; non-positive lift with no accepted omission risk retires the block).
- **Attributed-use rate**: Turns with an output claim, decision, or tool argument traceable to the block, over turns on which it was rendered (target: at least 40 percent; below 20 percent triggers a conversion to retrieval).
- **Capacity utilization**: Rendered tokens over the block's token bound, reported as median and 95th percentile (target: median between 30 and 80 percent; a persistent median below 30 percent indicates an oversized bound).
- **Prompt share**: Reserved-region tokens over total input tokens on applicable turns (target: at most 15 percent; a breach blocks new registrations).

**Edit Integrity Metrics**:

- **Edit acceptance rate**: Committed proposals over validly received proposals, broken down by rejection cause (target: at least 70 percent; a sharp fall without a workload change indicates a contract or description defect).
- **Rollback rate**: Revisions rolled back within the observation window over committed revisions (target: at most 2 percent; above 5 percent suspends autonomous edits on the block).
- **Conflict rate**: Proposals rejected or rebased for a stale expected version over write attempts, segmented by private and shared blocks (target: at most 5 percent on private blocks; a higher rate on a shared block indicates the writer set is too wide).
- **Overflow rate**: Proposals breaching a bound over total proposals, with condense success, demotion, and refusal reported separately (target: at most 5 percent; a higher rate indicates a bound derived from a ceiling rather than from the task).
- **Provenance coverage**: Factual fields carrying a resolvable evidence reference over all factual fields (target: 100 percent; any shortfall is a validation defect, not a tolerance).

**Drift and Cost Metrics**:

- **Semantic distance from baseline**: Normalized distance between the current value and the approved baseline, published per component (target: below the block's declared threshold; 2 consecutive breaches freeze the block).
- **Unsourced-claim fraction**: Fields marked observed whose evidence reference does not resolve, over all observed fields (target: 0 percent).
- **Staleness exposure**: Rendered turns on which a field was past its declared validity interval, over rendered turns (target: at most 5 percent).
- **Edit churn**: Changed rendered tokens per block per 100 applicable turns (target: below the block's declared threshold; high churn with low ablation lift indicates the wrong abstraction).
- **Cache-invalidation cost**: Estimated tokens in the reusable suffix that lost eligibility because a block prefix changed, validated against reported cached-token counts (target: attributed per edit; an unattributed aggregate is not actionable).

**Learning and Adaptation Mechanisms**:

- **Rejection-cause feedback**: Record every rejection with its failing assertion, and where one assertion produces more than 20 percent of rejections for a block, revise the description rather than the validator, since the description is what the proposing agent reads.
- **Bound recalibration**: Recompute each token bound from the observed 95th percentile of useful values plus 30 percent headroom at every review cycle, rather than holding the registration-time figure indefinitely.
- **Probe-set expansion**: Add a behavioural probe for every incident class observed in production, so that the reconciliation probe set grows against real failures rather than anticipated ones.
- **Threshold recalibration**: Recompute every threshold per deployment against observed outcomes; the values stated here are deployment defaults, not measured constants.

**Human-in-the-Loop Boundaries**: Changes to a block contract, bound, edit policy, invariant set, permission, or template ancestry; the first attachment of a block to a second agent; edits to identity, security, compliance, and shared-policy blocks; acceptance of a residual omission risk in place of measured lift; and relaxation of the provenance or confidence-marking requirement are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs a structural property of an agent's prompt rather than the content of any particular task. Its phases hold wherever an agent carries small state across turns, edits that state on its own initiative, and can be held to a bound and a source of truth.

### 4.1 Cross-Domain Application Patterns

**Software engineering and repository automation**: Blocks carry the active objective, the acceptance criteria, and a short set of project conventions covering naming, formatting, and interface rules. The conventions block is read-only for ordinary agents and edited only through a reviewed change, because a convention the agent may rewrite is a convention that erodes over a long session. The objective block reconciles against the issue tracker, which holds the authoritative task record; where the block says a subtask is complete and the tracker says it is open, the tracker wins and the block is corrected. The characteristic failure is a scratchpad block that accumulates every intermediate finding until it crowds the reserved region, which the ablation review retires.

**Clinical and care coordination support**: Blocks carry a compact care-plan objective and a small set of standing precautions, and never carry clinical facts that the record system holds. Every factual field names the record system as its durable source and reconciles at the shortest interval the deployment permits, because a stale value here changes a recommendation. Confidence marking is load-bearing: a preference inferred from one conversation must never render as an established clinical fact, and the absence-of-evidence marker is the mechanism that keeps the distinction visible on every subsequent turn. All blocks are approval-gated, and none is shared across care teams without an isolation review.

**Financial services and regulated advisory work**: Blocks carry the client's declared objectives and constraints, never balances, entitlements, or holdings, which remain in the system of record and reach the window only as a read-only freshness-labeled projection. The event log is a deliverable rather than a diagnostic aid, so every proposal, rejection, commit, and rollback is retained with its actor, reason, and evidence. The approval gate binds before any edit to a constraints block, because a weakened constraint is indistinguishable in the rendered text from a constraint that was never present.

**Field operations and logistics coordination**: Blocks carry the current assignment, its acceptance conditions, and a bounded coordination ledger shared across the agents working one route or one incident. The ledger is append-only with unique entry identifiers and idempotency keys, since concurrent writers are the norm rather than the exception. Volatile counters and live positions stay outside the block system entirely and are read from their services, because a resident value that changes every minute invalidates the prefix on every turn and is stale by the time it is read.

**Education and long-horizon tutoring**: Blocks carry a learner profile of durable, consented preferences and a compact record of the current learning objective. The profile is the clearest case for the confidence-marking rule, because an inference about a learner drawn from a single session will otherwise render as an established trait for months. Reconciliation compares the profile against assessment results held in the learning record, and the assessment record wins. Blocks are private by default and are never attached to a second agent without an explicit consent basis.

### 4.2 Scale, Risk, and Concurrency Adaptation

- **Single-agent, low-risk work**: Run 2 to 4 blocks with a combined bound at or below 8 percent of the context budget, reconcile at the 25-edit interval, and keep every block private. A single-agent deployment still requires the propose-validate-commit separation, because the risk it controls is the agent's own rewrite rather than another writer.
- **High-risk or irreversible work**: Make every block approval-gated or read-only, reduce the reconciliation interval to 10 committed edits, require a behavioural probe pass before every baseline reset, and hold the block frozen rather than accepting an unexplained difference. Prefer a refused write over an unverified condensation in every case.
- **Multi-agent deployments**: Treat every shared block as a broadcast mutation surface, cap the writer set at the smallest number that achieves the coordination, enforce compare-and-swap on every write, and provide freeze and detach controls that operate without a deployment. Prefer sharding into per-agent blocks with a derived read-only aggregate over a single shared writable block wherever contention appears.
- **Long-horizon autonomous runs**: Persist contracts, revisions, and pointers outside the window, re-fetch the current revision at every context boundary rather than carrying the rendered copy across, and run a reconciliation at each boundary so that drift is detected rather than inherited by the next context.
- **Latency-constrained deployments**: Move reorganisation, consolidation, and review edits to a background editing principal with its own allowlist and expected-version commits, and keep the interactive path to append and targeted-replace operations only. Never remove the validation gate to save latency, since the gate is the only thing separating a proposal from a mutation.
- **Cost-constrained deployments**: Place the most frequently edited block last in the reserved region, batch non-urgent edits with a deferral cap of 1 turn, and measure realised reuse from reported cached-token counts. Where a block's cache-invalidation cost exceeds its measured ablation lift for 2 consecutive review cycles, convert it to retrieval.

***

## V. Limitations and Considerations

**Self-editing concentrates authorship and review in one component**: The agent proposing a block value is the same agent that will read it, so the ordinary separation between an author and a reviewer is absent by construction. A confidently written error therefore propagates on every subsequent turn without meeting any independent check. The mitigation is the tier partition in Section 1.4 and the validation gate in Step 3.2, which place commit authority outside the model and reject a proposal that fails an invariant rather than accepting a degraded value.

**Drift is invisible in any single diff**: Each rewrite is faithful to the value it replaced, so a chain of individually reasonable edits can diverge arbitrarily far from the evidence without any one edit appearing wrong. Textual review of recent revisions will not detect it. The mitigation is the reconciliation schedule in Phase 5, which compares against durable sources rather than against the previous revision, and the three-way behavioural probe in Step 5.3, which detects influence changes that a diff does not show.

**Bounds are defaults, not measured constants**: The 15 percent reserved-region share, the 12-block attachment cap, the 25-edit reconciliation interval, and the 40 percent applicable-turn admission threshold were chosen to be operable on first deployment rather than derived from a general property of agent systems. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute bounds from the observed 95th percentile of useful values and to recompute thresholds against observed outcomes.

**Validation is defence in depth, not proof of safety**: Screening for injection, secrets, and unsupported claims reduces the rate at which harmful content enters a block without establishing that none does, and persistent memory has become a recognised attack surface precisely because its contents survive the session that introduced them. The mitigation is the combination of least-privilege writing principals, write-rate limits, quarantine, independent behavioural probes, and the rule that possession of block text is never sufficient authorization for an external action.

**Provenance can be recorded and still be wrong**: An evidence reference establishes where a claim came from, not that the claim is true, and a reference can resolve to a source that was itself mistaken. The mitigation is reconciliation against the durable source of truth rather than against the recorded reference, together with the requirement that a field whose source no longer supports it is reclassified as inferred rather than silently retained.

**Confidence marking depends on the model's own self-report**: The distinction between an observed field and an inferred one is proposed by the component least able to audit it, and a model that misclassifies its own inference as an observation produces a marked value that is wrong in the marking as well as the content. The mitigation is that the deterministic tier enforces the presence of a marker and the resolvability of the evidence reference, so an unsupported observed field fails validation regardless of how it was labelled.

**Ablation evidence is expensive and often skipped**: Paired ablations multiply evaluation cost, and deployments under schedule pressure retain blocks on the strength of an omission-risk argument that no measurement supports. The mitigation is Checkpoint 6, which permits an omission-risk retention for at most 2 consecutive review cycles before measured lift is required.

**Cache economics can pull against correctness**: Placing a frequently edited block late and batching edits reduces cost, and the same reasoning applied one step further argues for deferring a correction. The mitigation is the explicit rule in Step 2.3 that no correctness-critical or safety-critical edit is deferred for cache economy, and the classification of such a deferral as an incident rather than an optimisation.

**Structural conformance is not sound content**: A block set can satisfy every bound, invariant, and checkpoint here and still hold a well-formed, well-sourced, and unhelpful projection of the wrong state. The framework detects malformed and drifting blocks, not a mistaken judgement about what deserves residency, and no checkpoint substitutes for the residency gate being applied honestly at registration.

***

## VI. Conclusion and Summary

Memory blocks are a governance discipline before they are a memory technique. What makes the pattern distinct is that the agent is both the reader and the writer of the same region, with no external process between the two, and that single property generates every risk the framework above exists to bound: a value that grows until it crowds the window, a rewrite that silently removes what was correct, a chain of faithful edits that has drifted away from the evidence, and a guess that reads as an established fact because nothing marks it otherwise.

Each of those risks has one structural answer. Growth is answered by a dual bound enforced by arithmetic before the call, with rejection rather than truncation as the response to a breach. Silent loss is answered by validating a proposed replacement against a declared invariant set over the complete post-edit value, with the deterministic tier holding commit authority and a failed validation producing no state change. Drift is answered by scheduled reconciliation against the durable source of truth, on a stated interval, with the source winning every disagreement. Confabulation is answered by provenance binding and confidence marking, so that an inferred claim renders as inferred on every turn it is read.

A team introducing blocks should begin with one block, in proposal-only mode, against a frozen evaluation set. Establish the baseline without the block, measure the ablation lift with it, and enable narrow typed edits only after the validation gate, the rollback path, and the reconciliation schedule are exercised against adversarial cases. Add a second block only when the first has cleared a review cycle on measured evidence. A block store, a renderer, and a set of tools supply the mechanism, but none of them supplies the bound, the invariant set, or the source of truth that make self-editing safe.

**Key Success Factors**:

- **Bounded by construction**: Every block carries a byte bound and a rendered-token bound computed with the deployed tokenizer, and a candidate that exceeds either is rejected rather than trimmed.
- **Commit authority outside the model**: The model proposes an edit and never commits one; an edit is treated as successful only when the store returns a committed version.
- **Invariants over impressions**: Validation evaluates a declared invariant set against the complete post-edit value, and a failed validation rejects the edit rather than accepting a degraded block.
- **The source wins**: Reconciliation runs on a stated interval, compares against the durable source of truth rather than the previous revision, and resolves every disagreement in favour of the source.
- **Marked provenance**: Every factual field carries a resolvable evidence reference and every inferred field carries an explicit marker, so a guess is never read back as an established fact.
- **Residency earned by measurement**: Every resident block holds a positive paired ablation lift or an owner-accepted omission risk, and a block that holds neither is retired.

By following this guide, AI agents can operate a region of their own context that they rewrite on their own initiative while keeping that region bounded, traceable, reversible, and answerable to evidence outside itself.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. The single entry marked as verified during conversion was retrieved directly while confirming current architecture paradigms.

**Corpus pointers**:

- `Memory Block Architecture: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the residency definition, the architectural invariants, the block contract fields, the description-as-control-contract treatment, the block set catalogue, the edit-validate-commit-or-rollback loop, the condense-in-place procedure, the shared-block concurrency patterns, the drift audit, the logging field inventory, the metric definitions, the failure taxonomy, and the production readiness criteria. Its inline citations to framework documentation and to research on memory poisoning and self-modifying agents are transcribed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the umbrella guidance for this category. Owns the context budget, its partitioning, the admission gate, trust classes, and reason codes. The reserved block region in Phase 2 is one partition under its budget arithmetic, and its terminology is adopted unchanged here.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — owns externalization, write handles, supersession, and freshness enforcement. A block edit inherits its extraction, deduplication, contradiction, and provenance controls rather than restating them.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — owns read-time admission of retrieved material across partitions. A block bypasses per-turn selection by construction, which is what the residency gate in Section 1.3 exists to justify.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — owns verified lossy reduction under a declared preservation manifest. Invoked by the condense-in-place procedure in Step 4.2.
- `advanced_task_guides/context-management/guide_SemanticContextCompression.md` — owns representation-changing compression and its fidelity tests, applicable where a condensation rewrites rather than removes.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — owns trust, tenant, agent, and branch boundaries. Its review is required before any block is attached to a second agent.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — owns memory tiers, promotion, demotion, retention, and archival. Invoked when a block overflows or when content no longer justifies residency.
- `advanced_task_guides/context-management/guide_HierarchicalContextArchitecture.md` — owns scope precedence, inheritance, and conflict resolution. Governs how block templates and instances participate in the hierarchy and how a block-versus-policy conflict resolves.
- `advanced_task_guides/context-management/guide_SlidingWindowContext.md` — owns moving resident sets, eviction, and window assembly. Blocks form a reserved resident region rather than a sliding history, and the two occupy the same budget.
- `advanced_task_guides/context-management/guide_KVCacheAwarePromptConstruction.md` — owns exact-prefix reuse, the closed vocabulary of invalidation causes, and break-even arithmetic. The render-position ordering, the edit-batching rule, and the cache-invalidation cost metric used here apply its economics to a block edit; the rule that no correctness-critical or safety-critical edit is deferred for cache economy overrides that arithmetic.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — owns detection and remediation of assembled-context failure modes, applicable to distraction and contradiction arising from an oversized or stale reserved region.
- `advanced_task_guides/context-management/guide_FilesystemAsContext.md` — owns file-backed context with a declared layout and enforced write scope, the coarser-grained alternative considered at the residency gate.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — owns the task-scoped working state object, the protected atom, and the decision view. Its terminology is adopted here, and it holds the episode-scoped state that a block must not absorb.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the canonical store, record versions, current pointers, idempotency keys, and admission gates. The revision and pointer mechanics in Phase 3 follow its model.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — owns evidence-gated promotion of raw episodes into durable memory. A block receives a projection of what consolidation has already committed, never raw episodes.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — owns retention, decay, and erasure obligations. Invoked in Step 4.3 rather than replaced by a local eviction rule.
- `advanced_task_guides/memory-management/guide_StructuredMemory.md` — owns schema-governed memory records under deterministic admission, applicable to the value schema and invariant set declared in Phase 1.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — owns governed memory selection, admission, and retrieval across the memory tiers a block projects from.

**External references**:

*Resident block architecture and framework implementations*

1. Letta, *Letta memory blocks* — https://docs.letta.com/v1-sdk/memory/memory-blocks/
2. Letta, *Letta archival memory* — https://docs.letta.com/v1-sdk/memory/archival-memory/
3. Letta, *Letta context hierarchy* — https://docs.letta.com/v1-sdk/memory/context-hierarchy
4. Letta, *Letta shared memory* — https://docs.letta.com/v1-sdk/memory/shared-memory/
5. Letta, *Letta sleep-time agents* — https://docs.letta.com/guides/agents/sleep-time-agents/
6. *MemGPT paper* — https://arxiv.org/abs/2310.08560

*Retrieval-oriented and store-backed alternatives*

7. Mem0, *Mem0 documentation* — https://docs.mem0.ai/introduction
8. Zep, *Zep memory documentation* — https://help.getzep.com/v2/memory
9. LangChain, *LangChain memory concepts* — https://docs.langchain.com/oss/python/concepts/memory
10. LangChain, *LangGraph memory overview* — https://docs.langchain.com/oss/python/concepts/memory
11. LangChain, *LangMem hot-path memory* — https://langchain-ai.github.io/langmem/hot_path_quickstart/
12. *SelfMem* — https://arxiv.org/html/2607.03726v1

*File-scoped and provider-managed context alternatives*

13. Anthropic, *Claude Code memory* — https://docs.anthropic.com/en/docs/claude-code/memory
14. *AGENTS.md specification* — https://agents.md/
15. Anthropic, *Anthropic memory tool* — https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
16. Anthropic, *Anthropic context editing* — https://platform.claude.com/docs/en/build-with-claude/context-editing
17. OpenAI, *OpenAI conversation state* — https://developers.openai.com/api/docs/guides/conversation-state
18. OpenAI, *OpenAI compaction* — https://developers.openai.com/api/docs/guides/compaction

*Window accounting and prompt-cache placement*

19. Anthropic, *Anthropic context windows* — https://docs.anthropic.com/en/docs/build-with-claude/context-windows
20. Anthropic, *Anthropic prompt caching* — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
21. OpenAI, *OpenAI prompt caching* — https://platform.openai.com/docs/guides/prompt-caching

*Poisoning, drift, and persistent-memory risk*

22. *Memory Injection Attack* — https://arxiv.org/abs/2601.05504
23. *MEMDRIFT* — https://arxiv.org/abs/2605.24941
24. *Self-modifying agent identity drift* — https://arxiv.org/html/2604.14717v2
25. OWASP Gen AI Security Project, *OWASP Top 10 for Agentic Applications* — https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/ (verified during conversion; establishes memory and context poisoning as a named category in the 2026 agentic application risk list)
