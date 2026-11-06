# Context Editing and Tool-Result Clearing

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context editing constitutes the task family of mutating a context in place after the exchange has begun: removing or replacing content already rendered into earlier turns, most importantly clearing tool results whose work is finished. Tool results are the largest and fastest-growing consumer of a context budget in tool-using agents, and most are consumed once and never referenced again, so clearing them recovers budget without losing anything provided the clearing is correct. This guide provides AI agents with a structured protocol for establishing that correctness. It specifies the incorporation test that decides which results are clearable and the conservative default of retention where the test is inconclusive; the requirement that externalization complete and return a durability receipt before any removal, because a cleared result is irrecoverable otherwise; the placeholder that must replace every cleared result so the call remains visible and the agent does not re-run it; the structural validation that runs after every edit and reverts it on failure; the cache-boundary rule that prefers rare bulk edits at the oldest positions over continuous small ones; and the re-execution detection that catches the characteristic failure of this pattern. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a smaller rendered request never becomes a less capable one.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Context editing**: The selective mutation of a context after the exchange has begun, altering what an already-rendered turn contributes to the next model call. It is distinguished from selection, which decides what enters a context, and from compression, which reduces the token cost of content judged worth keeping. Editing operates on content that was already admitted, already rendered, and already used.

**Tool-result clearing**: The provider-side or application-side removal of older tool results from the rendered request under a token or tool-use trigger, retaining the most recent results verbatim and leaving the turn structure intact. The definition is adopted unchanged from the sibling compression guidance, which names it as one mechanism on the compression ladder; this guide owns its policy, its safety conditions, and its verification in depth.

**Observation masking**: The replacement of an older tool observation with a placeholder while the surrounding reasoning and action structure is retained. The term is adopted from the sibling compression guidance. Tool-result clearing is the bulk-triggered, policy-driven form of observation masking, and every clearing event in this guide produces a mask rather than a deletion.

**Active model view**: The exact token sequence that reaches the model for the next call after every edit has been applied. It is what the model actually sees and what every measurement in this guide is computed against.

**Canonical transcript**: The append-only, immutable record of what the user, the model, and the tools actually sent and received, held outside the active model view and never edited. The active model view is derived from it; the two are never conflated, and a claim about one is never evidence about the other.

**Clearing candidate**: One completed tool transaction proposed for clearing, identified by its tool name, its call identifier, its result identifier, its rendered token cost, its age in turns, and its terminal status. A candidate is a proposal, not a decision.

**Tool transaction**: The linked pair comprising one tool call and its result, together with any parallel siblings awaiting the same continuation. The transaction is the minimum unit an edit may act upon; splitting one is a structural defect regardless of how many tokens it reclaims.

**Incorporation test**: The deterministic test that establishes whether a candidate's information has already been carried forward, either into durable state through a confirmed write or into a later message that remains in the active model view. A candidate that fails the test is retained.

**Clearability class**: The declared category assigned to every tool before any edit runs, fixing whether its results may be cleared at all, whether they must be externalized first, and whether replay is a permitted recovery route. The five classes are clear-directly, persist-first, retain-recent, protected, and unclassified.

**Protected result**: A tool result that may never be cleared automatically: an unconsumed result, a member of an in-flight or unmatched transaction, an error or denial explaining current state, a side-effect receipt or transaction identifier, an unverified durable-write confirmation, evidence bound to a pending citation, a non-reproducible upload or stream, an authorization or policy decision still governing execution, content under a legal or audit hold, and any candidate whose class is unclassified.

**Clearing placeholder**: The bounded control object written into the active model view in place of a removed result, carrying the clear-event identifier, the tool name and call identifier, the terminal status of the original call, the recovery reference, and the recovery instruction. It is not prose, not a summary, and not evidence.

**Recovery reference**: The durable pointer bound into a placeholder that resolves to the removed bytes: a write handle returned by the externalization contract, a content hash, or a version-pinned replay descriptor. A placeholder without a recovery reference is a deletion with a note attached.

**Write handle**: The compact in-window replacement for released content, comprising the stable identifier, the purpose line, the shape descriptor, the size and version, and the retrieval instruction. The term and its contract are adopted unchanged from the sibling write-patterns guidance and are not re-derived here.

**Durability receipt**: The deterministic tier's confirmation that a write is committed and readable after the boundary, carrying the identifier, the committed version, the commit sequence, and the store location. The term is adopted unchanged from the sibling write-patterns guidance. In this guide the receipt is the sole precondition that permits a clearing event to proceed.

**Residency copy**: Content held simultaneously in the active model view and in the durable store. The residency copy is the safe state between the write and the clearing event, and it is the state that must persist when a receipt does not return.

**Structural validation**: The deterministic check run on the post-edit view confirming that every tool call retains a matching result or placeholder, that no transaction is split, that role alternation and block ordering satisfy the provider's grammar, and that every identifier referenced still resolves. It is run after every edit without exception.

**Revert**: The restoration of the pre-edit view from the retained snapshot when structural validation, continuity probing, or receipt verification fails. A failed edit is undone, never patched forward.

**Continuity probe**: The bounded check, run on the post-edit view before it is sent, asking whether the next planned action still has every fact it requires without reconstructing them from content that has been removed.

**Cache boundary**: The earliest position in the rendered request that an edit changes. Everything at or after that position ceases to match any previously cached prefix. The boundary, not the token count reclaimed, determines what an edit costs.

**Clearing ledger**: The append-only record binding each clear event to the transaction it removed, the placeholder emitted, the recovery reference, the reclaimed token count, the cache boundary, and every later recovery or re-execution attributed to it.

**Re-execution loop**: The failure mode in which an agent, unable to see the outcome of a call it made, issues the same call again, whose result is cleared again on the next trigger, producing unbounded repetition. It is the characteristic failure of this pattern and the reason placeholders are mandatory.

**Clearing precision**: The proportion of cleared results never needed again, computed as cleared results with no subsequent recovery, re-execution, or missing-evidence event divided by all cleared results. It is the metric that governs whether an eligibility policy continues.

**Terminal state**: The declared outcome of one clearing operation: cleared, retained, externalized-and-cleared, reverted, quarantined, or suppressed. An operation ending in none of these is a defect.

### 1.2 Scope Boundary Against the Sibling Operations

Context management offers four operations against a context under pressure: writing state out, selecting what comes back in, compressing what stays, and isolating what never shares a context. Editing is not a fifth family. It is the in-place execution of the write and compression families against content that has already been rendered, and it inherits their contracts rather than replacing them.

**What this guide owns**: The decision that an already-rendered tool result may leave the active model view; the incorporation test that establishes it; the clearability class assigned to every tool before any edit runs; the placeholder that replaces a removed result and the reference bound into it; the structural validation applied to the post-edit view and the revert that follows a failure; the batching rule that governs where and how often an edit cuts; the detection of re-execution loops; and the ledger that makes every removal attributable.

**What the write-patterns guidance owns**: The mechanics of moving content out of the context and into a durable store. Identifier assignment, canonical serialization, the selectable header, the commit transaction, the durability receipt, read-back verification, supersession, and the release contract are stated there. This guide invokes that contract before every clearing event and does not restate it; where the two appear to conflict on whether content may leave the context, the write-patterns contract holds, because a receipt is the only evidence that a removal is reversible.

**What the compression guidance owns**: Summarisation, the preservation manifest, fidelity classes, compression depth, and the measurement of task-outcome retention. Clearing performs no semantic synthesis and generates no summary, so no fidelity class applies to it. Where the meaning of a result is needed but its bytes are not, the operation is compression and is routed there.

**What the umbrella context-management guidance owns**: The partitioned budget, the admission gate, the protected atoms, the assembly order, and the selection ladder that decides which of the four operations a given pressure calls for. This guide assumes the ladder has already selected an in-place edit.

**What the caching guidance owns**: Exact-prefix matching, cache lifetimes, write and read pricing, and break-even arithmetic. This guide carries only the agent-layer consequence of those mechanics, stated in Section 1.4 as a batching rule, and defers everything beneath it.

**Composition rule**: An agent clearing a tool result loads this guide for the eligibility decision and the placeholder contract, and the write-patterns guidance for the externalization that must complete first. An agent deciding whether to clear at all, summarise, or offload loads the umbrella guidance first.

### 1.3 The Execution-Tier Partition

Every unit of work in a clearing operation belongs to exactly one tier. The partition is what makes a removal auditable and a revert possible.

**Deterministic tier**: Software, validators, tokenizers, and storage APIs own clearability-class lookup, candidate enumeration and freezing, rendered token counting before and after the edit, the mechanical half of the incorporation test, externalization confirmation and receipt verification, placeholder construction and reference binding, application of the edit itself, structural validation of the post-edit view, cache-boundary computation and batching arithmetic, snapshot retention and revert, ledger emission, re-execution detection, and every metric in Section III.D. These require exactness, reproducibility, and auditability that model inference does not supply. A deterministic result must reproduce on replay of the same inputs; where it does not, it is a defect rather than a judgement.

**Model tier**: Model inference owns one decision: judging whether a candidate's information has been incorporated into durable state or into a later message, in the cases where no mechanical evidence settles it. This requires reading what a later message asserts and deciding whether it carries the substance of the earlier result, which no deterministic rule covers. The model tier also composes the human-readable purpose line of a placeholder and answers the continuity probe. It produces judgements; it never produces authority.

**Hybrid tier**: The incorporation test is hybrid in one direction: software establishes the mechanical preconditions and the model adjudicates the residual question of substantive incorporation. Policy retuning is hybrid in the other direction: software computes clearing precision and re-execution rates per tool class, and the model proposes which class boundary moved.

**Authority on disagreement**: The deterministic tier holds authority in every disagreement, without exception. Where a model judges a result incorporated and no confirmed write or later message supports it, the result is retained. Where a model judges a result unnecessary and its clearability class is protected, the class governs. Where a model reports that a placeholder is adequate and structural validation fails, the edit reverts. Where a model asserts a token saving, the tokenizer figure governs.

**The prohibited delegations**: The model never assigns a clearability class, never declares a write durable, never authorizes a clearing event, never constructs the recovery reference, never validates message structure, never decides that a failed validation may proceed, and never computes the saving that justifies its own recommendation. A deployment in which any of these reaches the model tier can lose evidence silently, because the only component that knows whether the store accepted the write and the grammar accepted the edit is the one that talked to them.

**Two prohibitions stated as absolutes**: Clearing without a confirmed externalization is prohibited for every candidate whose clearability class is persist-first, and no threshold, no budget pressure, and no model recommendation lifts that prohibition. A structural validation failure reverts the edit; it is never resolved by repairing the post-edit view in place, because a repair applied to a view that failed its grammar produces a second unvalidated state rather than a valid one.

### 1.4 The Four Origins of Clearing Loss

Four distinct failures account for nearly all damage on this path. They are stated together because each has a countermeasure that makes another worse, and a policy tuned against one alone reliably produces another.

**The invisible removal**: A result is removed and nothing marks its position. The call remains visible with no visible outcome, which reads to the model as though the tool was never run or as though it failed silently. The model reissues the call, its result is cleared again at the next trigger, and the loop repeats until a budget or a turn limit ends the run. This is the characteristic failure of the pattern, it consumes more budget than the clearing ever reclaimed, and it is invisible in token-reduction reporting because each cycle does reduce tokens. The countermeasure is the mandatory placeholder in Step 4.1 and the re-execution detection in Step 6.1.

**The premature removal**: A result leaves the active model view before its bytes are durable anywhere else. Recovery is then impossible: the only copy was in the rendered request and the request is gone. This failure is silent at the moment it occurs and surfaces one or more turns later as a citation that cannot be supported, a verification that cannot be run, or a compensating action that cannot be constructed. The countermeasure is the receipt requirement in Step 3.2 and the residency rule: a result stays resident until a receipt names its committed version, and a failed confirmation ends the operation in the retained terminal state.

**The structural break**: An edit removes one half of a tool transaction, or one of several parallel results still awaiting a continuation, or content whose removal leaves role alternation or block ordering outside what the provider accepts. The request is then rejected outright, or accepted and interpreted against a malformed history. The countermeasure is the transaction-atomicity rule in Step 4.3 and the structural validation with revert in Phase 5.

**The cache-boundary inversion**: An edit changes content near the front of the rendered request, so every token after that position ceases to match any cached prefix. The next call pays to re-establish the prefix it had already paid for. A small, frequent edit at an early position can therefore cost several times what it reclaims, while the token-reduction metric records an improvement. The countermeasure is the batching rule below and the accounting in Step 4.3.

**The batching rule**: Editing near the front of a context invalidates everything after it for prefix-reuse purposes, so an edit that saves tokens can cost more than it saves. Clear from the oldest positions, in bulk, and infrequently, rather than continuously in small increments. Expressed as operable defaults: an edit runs only when the eligible reclaim in one event is at least 10 percent of the current rendered request or at least 20,000 tokens, whichever is smaller; no more than 1 clearing event runs per 10 assistant turns; and consecutive events are separated by at least 5 turns of hysteresis so that a threshold oscillating around its trigger does not produce an edit per turn. Every event cuts contiguously from the oldest eligible position forward, so one cache boundary is established per event rather than one per candidate. Where an event's eligible reclaim falls below the floor, the event is suppressed and the reason recorded; suppression is a normal terminal state, not a failure. These are deployment defaults, restated as such in Section V, and each deployment recomputes them against the arithmetic its own caching guidance supplies.

**Why the four must be controlled together**: Tightening eligibility alone raises the rate at which needed evidence is retained until the context overflows. Tightening the receipt requirement alone leaves the context carrying residency copies that defeat the purpose of editing. Batching alone, without placeholders, produces larger and rarer invisible removals rather than fewer of them. The framework in Section II holds all four: the eligibility gate bounds what is removed, the receipt gate bounds when it is removed, the placeholder bounds what the removal looks like, and the batching rule bounds where and how often the cut falls.

***

## II. Operational Framework: Verified In-Place Removal of Consumed Tool Results Under a Reversible Clearing Contract

The framework assumes the umbrella selection ladder has chosen an in-place edit over admission control, summarisation, or delegation to a separate context. Phases 1 through 5 run in order for each clearing event, and Phase 5 either commits the post-edit view or reverts to the pre-edit snapshot. Phase 6 runs on a slower cadence, consuming the ledger the earlier phases produce, and corrects the policy those phases execute.

### Phase 1: Clearing Contract and Eligibility Policy

**Objective**: Fix the editing owner, the per-tool clearability classes, and the numeric triggers before any content is removed, so that eligibility is a declared property rather than a runtime inference.

#### Step 1.1: Declare the Single Editing Owner and the Canonical Transcript

**Required Actions**:

- Enumerate every component between the canonical transcript and the model call that can remove or replace rendered content: framework middleware, history reducers, prompt builders, provider-side editors, session compactors, and retry wrappers.
- Designate exactly 1 owner of removal for each request path, and disable every other component's removal behaviour explicitly rather than relying on its defaults.
- Establish the canonical transcript as an append-only store that no editor may write to, and confirm that it records every call, result, and error with stable identifiers before any edit runs.
- Record the implementation path as provider-native or application-side, and record what the chosen path does and does not expose: whether the post-edit view is returned, whether the placeholder text is configurable, and whether applied-edit counts are reported.
- Replay a fixture set of at least 20 recorded exchanges containing parallel calls, errors, retries, and oversized results, and diff the canonical transcript against the rendered request to confirm that exactly 1 component mutated it.

**Required Outputs**:

- A clearing contract record naming the owner, the disabled components, the implementation path, and the exposure limits of that path.
- A canonical transcript with stable identifiers for every turn, call, result, and clear event.
- An ownership diff report over the fixture set, with the count of components observed to mutate each path.

**Quality Checkpoints**:

- Exactly 1 component mutates the rendered request on every fixture path; a count of 2 or more halts the deployment.
- The canonical transcript is writable only by the recorder and is not reachable by any editor.
- The contract states whether the post-edit view is observable, and where it is not, the record carries an explicit observability-gap marker rather than an assumption of fidelity.

***

#### Step 1.2: Classify Every Tool Into a Clearability Class

**Required Actions**:

- Assign every registered tool exactly 1 clearability class before it is permitted to run, recording for each the reproducibility of its results, whether the underlying source is mutable, whether the call carries a side effect, whether its results serve as citations, and its typical result size in tokens.
- Default every unclassified tool to the protected class, so that adding a tool cannot silently widen eligibility.
- Enumerate the protected result categories independently of tool class, since a single tool can return a clearable result on one call and a protected one on the next: unconsumed results, in-flight or unmatched transactions, errors and denials, side-effect receipts, unverified write confirmations, pending-citation evidence, non-reproducible uploads and streams, live authorization decisions, and anything under hold.
- Record the class assignment with a version identifier, so that a past clearing event can be replayed against the exact policy that produced it.

**Required Outputs**:

- A tool register with 1 clearability class, 1 reproducibility verdict, and 1 side-effect verdict per tool.
- A protected-category list applied per result, independent of tool class.
- A versioned eligibility policy record.

**Quality Checkpoints**:

- Every registered tool carries a class; an unclassified tool resolves to protected and cannot be cleared.
- No tool with a side effect and no tool whose results serve as citations carries the clear-directly class.
- The policy version is recorded on every clearing event, so replay resolves to 1 policy.

***

#### Step 1.3: Fix the Trigger, Retention, and Minimum-Reclaim Thresholds

**Required Actions**:

- Set the activation trigger as a proportion of the usable input budget rather than an absolute token count, defaulting to 60 percent of the budget remaining after the output reserve, so that the trigger transfers across models with different capacities.
- Set the retention floor to the most recent 3 tool transactions, and raise it to cover the longest observed unresolved dependency chain plus 1, where that chain exceeds 3.
- Set the minimum reclaim per event to the batching floor in Section 1.4, so that no event runs that cannot justify the cache boundary it establishes.
- Set an application-side minimum candidate size, defaulting to 500 rendered tokens, below which a result is never a candidate, because the placeholder that would replace it costs a material fraction of what it reclaims.
- Record every threshold with the workload, the model, and the tokenizer it was set against, and mark all four as deployment defaults pending the measurement in Step 6.3.

**Required Outputs**:

- A threshold record carrying the trigger, the retention floor, the minimum reclaim, the minimum candidate size, and the hysteresis interval.
- A binding of each threshold to its workload, model, and tokenizer.
- A declared suppression path for the case where no candidate satisfies the thresholds.

**Quality Checkpoints**:

- The trigger sits at least 1 maximum plausible tool result plus the full output reserve below the hard input ceiling; a trigger that can be crossed and still overflow is a defect.
- The retention floor is at least 3 transactions and at least the longest observed dependency chain plus 1.
- Every threshold names its consequence: crossing the trigger opens Phase 2, and failing the minimum reclaim suppresses the event and records the reason.

***

### Phase 2: Candidate Identification and the Incorporation Test

**Objective**: Establish which results are safe to clear by applying an explicit test to each candidate, and retain every candidate the test does not clearly pass.

#### Step 2.1: Freeze the Candidate Set at the Trigger

**Required Actions**:

- Freeze the candidate set at the moment the trigger fires, keying each candidate by tool-call identifier and result content hash, so that a result arriving mid-evaluation cannot enter or leave the set.
- Exclude from the set every transaction inside the retention floor, every transaction whose tool class is protected, every transaction whose result falls below the minimum candidate size, and every transaction that is in flight or unmatched.
- Order the surviving candidates oldest first, and compute the contiguous prefix of the ordering whose cumulative rendered tokens meet the minimum reclaim, since the event will cut that prefix as one block.
- Snapshot the pre-edit view and record its hash, its rendered token count, and the index of its first candidate block, so that revert restores an exact state rather than a reconstruction.
- Suppress the event and record the reason where the frozen set yields no contiguous prefix meeting the minimum reclaim.

**Required Outputs**:

- A frozen candidate set with tool name, call identifier, result hash, rendered token count, age in turns, and terminal status per entry.
- A pre-edit snapshot with its hash, token count, and first-candidate index.
- An ordered contiguous cut block, or a recorded suppression with its reason code.

**Quality Checkpoints**:

- No candidate in the frozen set is inside the retention floor, protected, below the minimum size, or in flight.
- The pre-edit snapshot hash reproduces the exact rendered request that would have been sent without the edit.
- The cut block is contiguous from the oldest position; a non-contiguous selection is rejected before evaluation begins.

***

#### Step 2.2: Apply the Incorporation Test to Each Candidate

**Required Actions**:

- Apply the incorporation test to every candidate in the cut block: a result is clearable when its information has been incorporated into durable state through a confirmed write, or into a later message that remains in the active model view, and when nothing downstream will need to cite the original bytes.
- Establish the first limb deterministically by resolving the candidate's result hash against the write ledger and confirming that a durability receipt exists naming a committed version whose content hash matches.
- Establish the second limb by locating at least 1 later message inside the retention floor that restates the candidate's operative content, and route the residual judgement of whether the restatement carries the substance to the model tier, which returns incorporated, not-incorporated, or uncertain.
- Establish the third limb deterministically by resolving the candidate against the open-dependency set built in Step 2.3; a candidate bound to any open dependency fails regardless of the first two limbs.
- Record for each candidate the verdict of each limb separately, so that a later precision failure can be attributed to the limb that produced it rather than to the test as a whole.

**Incorporation Test Verdict Matrix**:

| Durable state limb | Later-message limb | Downstream dependency limb | Aggregate verdict |
| :-- | :-- | :-- | :-- |
| Receipt matches result hash | Not required | No open dependency | Clearable |
| No receipt | Model returns incorporated | No open dependency | Clearable, recovery by replay only |
| No receipt | Model returns uncertain | No open dependency | Retain and re-evaluate next event |
| Receipt matches result hash | Not required | Open dependency present | Retain until dependency closes |
| No receipt | Model returns not-incorporated | Any | Retain, route to persist-first |
| Receipt version mismatch | Any | Any | Retain and raise a write defect |
| Limb not evaluated | Any | Any | Retain, record incomplete evaluation |

**Required Outputs**:

- A per-candidate test record carrying 3 limb verdicts and 1 aggregate verdict.
- A model-tier adjudication record for every candidate whose second limb was not settled mechanically, carrying the later message identifier it relied on.
- A clearable subset of the cut block, and a retained subset with reason codes.

**Quality Checkpoints**:

- Every candidate carries a verdict for all 3 limbs; a missing limb verdict resolves the candidate to retained.
- No candidate passes on a model-tier judgement alone where the first limb is available and returned no receipt.
- The aggregate verdict is clearable only where all 3 limbs pass; any other combination retains.

***

#### Step 2.3: Resolve Open Downstream Dependencies and Default to Retain

**Required Actions**:

- Build the open-dependency set before the test runs, enumerating every pending consumer that could require a candidate's exact bytes: an unfinished plan step, an open branch awaiting merge, a scheduled verification, an unresolved citation, an error under diagnosis, an approval awaiting evidence, and any compensating action for a side effect already committed.
- Bind each open dependency to the specific result identifiers it references, and treat a dependency whose references cannot be enumerated as referencing every candidate in the block.
- Apply the conservative default explicitly: where the incorporation test returns uncertain, where a limb could not be evaluated, where a dependency's references are unknown, or where the candidate's class is unclassified, the candidate is retained rather than cleared, and the reason code records which of those conditions applied.
- Re-evaluate retained candidates at the next clearing event rather than discarding the evaluation, since a dependency that was open at one trigger is frequently closed at the next.
- Record the retained volume in tokens, so that a policy retaining most of what it evaluates is visible as such rather than appearing merely conservative.

**Required Outputs**:

- An open-dependency set with per-dependency result references, or an explicit unknown-references marker.
- A retained-candidate list with 1 reason code per entry, drawn from a closed vocabulary.
- A retained-volume figure in rendered tokens for the event.

**Quality Checkpoints**:

- Every uncertain, unevaluated, or unknown-reference condition resolves to retain; no such condition resolves to clear under any threshold pressure.
- Every retained candidate carries a reason code from the closed vocabulary; a free-text reason is rejected.
- Retained candidates re-enter the frozen set at the next trigger rather than being permanently excluded.

***

### Phase 3: Externalization Before Clearing

**Objective**: Make every clearable candidate recoverable before it is removed, since content cleared from a context is gone unless it was externalized first.

#### Step 3.1: Route Persist-First Candidates Through the Externalization Contract

**Required Actions**:

- Route every candidate whose clearability class is persist-first, and every candidate that passed the incorporation test on replay alone but whose source is mutable, through the externalization contract stated in the sibling write-patterns guidance, adopting its write-handle, identifier, and selectable-header requirements without modification.
- Submit the exact rendered result bytes rather than a paraphrase or a summary, and record alongside them the tool name, the canonical call arguments, the authorization scope, the source version or content hash, the retrieval time, and the content type.
- Declare the named reader and the read occasion for each write, using the write-patterns definitions: the reader is the agent after this clearing event, and the read occasion is a recovery reference resolution or a re-execution detection.
- Assign the write class from the write-patterns set, using artifact offload for raw result bytes and structured note only where a distilled record is written in addition to, never instead of, the exact bytes.
- Hold every candidate as a residency copy for the duration of the write, so that a failure at any point leaves the content in the context rather than nowhere.

**Required Outputs**:

- One externalization submission per persist-first candidate, carrying exact bytes and full provenance.
- A named reader and read occasion recorded per submission.
- A residency-copy register listing every candidate currently held in both locations.

**Quality Checkpoints**:

- No submission carries a summary in place of the exact bytes; a paraphrase submitted as an archive is a defect that halts the event.
- Every submission carries a tool name, canonical arguments, source version or content hash, and retrieval time.
- Every persist-first candidate appears in the residency-copy register before any edit is applied.

***

#### Step 3.2: Obtain the Durability Receipt and Verify the Read-Back

**Required Actions**:

- Wait for a durability receipt naming the committed version, the commit sequence, and the store location for each submission, and treat a successful write call without a receipt as an unconfirmed write.
- Verify the read-back by retrieving the committed item and comparing its content hash against the hash recorded at submission, rather than inferring success from the absence of an error.
- Verify that any derivative the recovery reference depends on has caught up, since a handle resolving through an index that has not yet indexed the item is a handle to nothing at the moment it is needed.
- Fail closed on any verification failure: the candidate leaves the clearable subset, its terminal state is retained, and a write defect is raised against the store rather than against the clearing policy.
- Record the receipt identifiers in the clearing ledger before the edit is applied, so that the ledger can be read to establish recoverability without consulting the store.

**Required Outputs**:

- One durability receipt per persist-first candidate, with committed version and commit sequence.
- A read-back verification record with the compared hashes and the derivative watermark consulted.
- An updated clearable subset from which every unconfirmed candidate has been removed.

**Quality Checkpoints**:

- No candidate proceeds to Phase 4 without a receipt whose read-back hash matches the submitted hash; a hash mismatch halts the candidate and raises a defect.
- Clearing without confirmed externalization does not occur for any persist-first candidate; a single occurrence disables automatic clearing for that tool class pending review.
- The ledger records the receipt before the edit, not after, so that a crash between the two leaves evidence of recoverability rather than of removal.

***

#### Step 3.3: Classify Replay Safety and Bound the Re-Fetch Budget

**Required Actions**:

- Classify each clearable candidate's replay safety as deterministic, idempotent-but-mutable, or unsafe, based on whether the tool is read-only, whether the source can be version-pinned, and whether credentials remain valid for the expected task duration.
- Permit replay as the sole recovery route only for candidates classified deterministic, and require externalization for every other candidate regardless of its incorporation-test verdict.
- Prohibit replay entirely for any tool carrying a side effect, so that recovering a cleared result can never re-issue a write, a payment, a message, or a state change.
- Set a re-fetch budget of at most 2 recovery attempts per clear-event lineage and at most 1 recovery per candidate per 10 turns, and record the budget in the placeholder so the model can observe it.
- Record the pinned source version and content hash for every deterministic candidate, so that a replay returning different bytes is detected rather than silently accepted as the original.

**Required Outputs**:

- A replay-safety class per clearable candidate.
- A version-pinned replay descriptor for every candidate whose recovery route is replay.
- A re-fetch budget record bound to each clear-event lineage.

**Quality Checkpoints**:

- No side-effecting tool carries a replay recovery route; recovery for such tools resolves only to the archive.
- Every replay descriptor carries a pinned version or a content hash against which a changed result can be detected.
- The re-fetch budget is numeric, bound to a lineage rather than to a call, and visible in the placeholder.

***

### Phase 4: Placeholder Construction and Cache-Aware Application

**Objective**: Replace each removed result with a control object that records the call and its recovery route, and apply the whole block as one edit at one cache boundary.

#### Step 4.1: Construct the Clearing Placeholder

**Required Actions**:

- Construct 1 placeholder for every removed result, carrying the clear-event identifier, the tool name, the tool-call identifier, the terminal status of the original call, a neutral statement that the payload was removed after use, the recovery reference, the recovery instruction, and the remaining re-fetch budget.
- State the terminal status explicitly as succeeded, failed, denied, or cancelled, so that a removal is never mistaken for a failure and a failure is never mistaken for a removal.
- Bind the recovery reference to the write handle returned by the receipt, or to the version-pinned replay descriptor where the recovery route is replay, and validate that the reference resolves before the placeholder is emitted.
- Include an explicit instruction that the placeholder is not evidence and may not be cited, quoted, or treated as a summary of what was removed.
- Exclude secrets, credentials, full original arguments, and sensitive paths from the placeholder, binding the reference to an opaque identifier instead, since the placeholder is rendered into the model's view and inherits its exposure.
- Bound the placeholder to at most 80 rendered tokens, so that clearing a set of small results cannot cost more in markers than it reclaims in payload.

**Placeholder Field Contract**:

| Field | Content | Consequence if absent |
| :-- | :-- | :-- |
| Clear-event identifier | Opaque identifier binding the marker to the ledger entry | Recovery and re-execution cannot be attributed |
| Tool name and call identifier | The exact identifiers of the original transaction | The model cannot tell which call produced the marker |
| Terminal status | Succeeded, failed, denied, or cancelled | Removal is read as failure and the call is reissued |
| Removal statement | Neutral statement that the payload was removed after use | The call appears never to have completed |
| Recovery reference | Write handle or version-pinned replay descriptor | The removal is irreversible in practice |
| Recovery instruction | How to resolve the reference, and the tool to use | Recovery is attempted by re-execution instead |
| Re-fetch budget | Remaining attempts for this lineage | Recovery attempts are unbounded |
| Non-evidence notice | Statement that the marker may not be cited | The marker is quoted as though it were the result |

**Required Outputs**:

- One validated placeholder per removed result, within the token bound.
- A resolved recovery reference per placeholder, confirmed to resolve before emission.
- A placeholder token total for the event, computed against the target tokenizer.

**Quality Checkpoints**:

- Every placeholder names the call identifier, the terminal status, and a resolving recovery reference; a placeholder missing any of the three is rejected and the candidate is retained.
- No placeholder asserts that content was summarised, that it is safe to ignore, or that the tool was not run.
- Placeholder tokens for the event are at most 15 percent of the tokens the event reclaims; above that, the minimum candidate size is raised before the event proceeds.

***

#### Step 4.2: Batch the Edit Against the Cache Boundary

**Required Actions**:

- Compute the cache boundary as the position of the earliest block the edit will change, and record every token at or after that position as ceasing to match any previously established prefix.
- Compare the reclaim against the boundary cost before applying: an edit is applied only where the reclaimed tokens, multiplied by the number of subsequent calls expected to carry them, exceed the tokens that must be re-established after the boundary.
- Enforce the batching rule from Section 1.4: at most 1 event per 10 assistant turns, at least 5 turns of hysteresis between events, and a contiguous cut from the oldest eligible position so that 1 boundary is established per event.
- Estimate the number of subsequent calls from the observed median remaining turns for the workload rather than from an assumption, and where fewer than 3 subsequent calls are expected, suppress the event and record the reason.
- Where the implementation path is provider-native and the provider applies edits without exposing the boundary, record the boundary as unobserved and estimate it from the position of the oldest cleared transaction, marking the estimate as such.

**Required Outputs**:

- A cache-boundary record with the boundary position, the tokens after it, and whether the position was observed or estimated.
- A per-event batching decision with the reclaim, the expected subsequent calls, and the computed net.
- A suppression record where the net is non-positive.

**Quality Checkpoints**:

- The event establishes exactly 1 cache boundary; an event producing 2 or more boundaries is rejected and re-planned as a contiguous cut.
- No event runs where fewer than 3 subsequent calls are expected to carry the reclaimed tokens.
- The boundary position is recorded as observed or estimated on every event; an unmarked estimate is a defect.

***

#### Step 4.3: Apply the Edit and Account the Reclaimed Budget

**Required Actions**:

- Apply the whole block as 1 atomic edit, replacing each removed result with its placeholder in place, so that no intermediate state is ever rendered.
- Preserve the tool call itself in every case, and clear call arguments only where the arguments dominate the transaction's token cost, a replay descriptor carrying the canonical arguments has been externalized and confirmed, and no downstream dependency references them.
- Preserve transaction atomicity: where a transaction has parallel siblings awaiting the same continuation, clear all siblings or none, and never remove one result of a parallel group.
- Count the post-edit rendered tokens with the target model's tokenizer, and compute the reclaim as pre-edit tokens minus post-edit tokens rather than as the sum of removed payloads, since placeholders offset the difference.
- Write the ledger entry for the event, binding the clear-event identifier to each removed transaction, its placeholder, its recovery reference, its receipt, the reclaim, the boundary, and the policy version.

**Required Outputs**:

- A post-edit view with 1 placeholder per removed result and every tool call intact.
- A tokenizer-exact reclaim figure and post-edit rendered token count.
- A ledger entry per clearing event, linking every removed transaction to its recovery route.

**Quality Checkpoints**:

- Every tool call in the post-edit view has either its original result or exactly 1 placeholder; a call with neither is a structural defect.
- No parallel transaction group is partially cleared.
- Call arguments remain intact unless a confirmed replay descriptor carries them; clearing arguments without that descriptor is prohibited.

***

### Phase 5: Structural Validation, Continuity Probing, and Revert

**Objective**: Confirm that the post-edit view is a valid, usable context before it is sent, and restore the pre-edit snapshot where it is not.

#### Step 5.1: Validate Message-Structure Integrity

**Required Actions**:

- Run structural validation on the post-edit view after every edit without exception, including edits that removed a single result and edits applied by a provider-native path where the post-edit view must be reconstructed locally.
- Check pairing: every tool call resolves to exactly 1 result or exactly 1 placeholder, and every result or placeholder resolves to exactly 1 call. Orphans in either direction fail.
- Check atomicity: no parallel transaction group is partially represented, and no call is edited while its result is still pending.
- Check grammar: role alternation, block ordering, and any content-block constraints the provider enforces are satisfied by the serialized payload, tested against the provider's own validator rather than against an internal model of it.
- Check reference resolution: every identifier the post-edit view still mentions, including those inside placeholders, resolves to something that exists.
- Record the validation verdict with the specific failing check where it fails, so that the failure is attributable to a rule rather than reported as a generic rejection.

**Required Outputs**:

- A structural validation record with 1 verdict per check and 1 aggregate verdict.
- A serialized post-edit payload and its hash, or a reconstructed payload marked as reconstructed where the provider does not expose the edited view.
- A named failing check where the aggregate verdict is fail.

**Quality Checkpoints**:

- All 5 checks run on every edit; a skipped check resolves the aggregate verdict to fail.
- Orphaned calls, orphaned results, and partially cleared parallel groups each produce a fail, never a warning.
- Where the post-edit view is reconstructed rather than observed, the record is labelled as a reconstruction and is never reported as the provider's payload.

***

#### Step 5.2: Run the Continuity Probe on the Post-Edit View

**Required Actions**:

- Run the continuity probe against the post-edit view before it is sent, asking whether the next planned action has every fact it requires from content still present, without reconstructing any of them from what was removed.
- Restrict the probe to the next planned action and its immediate preconditions, bounding it to at most 300 tokens of output, so that the probe does not itself consume the budget the edit reclaimed.
- Require the probe to answer with the specific missing item where it answers no, so that the response identifies a candidate to restore rather than expressing general unease.
- Treat a probe answer of no, or an answer naming an item that was removed in this event, as a continuity failure that triggers Step 5.3.
- Record the probe question, the answer, and the named missing item in the ledger, so that probe accuracy can itself be measured against later recovery events.

**Required Outputs**:

- A continuity probe record with the question, the bounded answer, and any named missing item.
- A continuity verdict of pass or fail for the event.
- A restoration candidate list where the verdict is fail.

**Quality Checkpoints**:

- The probe runs on the post-edit view, never on the pre-edit view, since a probe against the unedited context tests nothing.
- A fail verdict names at least 1 specific missing item; an unspecific fail is treated as a fail and escalated to revert.
- Probe output is at most 300 tokens; an unbounded probe is a defect.

***

#### Step 5.3: Revert on Failure and Record the Terminal State

**Required Actions**:

- Revert the whole edit to the pre-edit snapshot on any structural validation failure, any continuity failure, or any receipt verification failure discovered after the edit was applied, restoring the snapshot rather than patching the post-edit view.
- Confirm the revert by comparing the restored view's hash against the pre-edit snapshot hash, and treat a mismatch as an unrecoverable state that halts the run rather than as a retry condition.
- Narrow the candidate set on a reverted event rather than re-attempting the same block: remove the candidates implicated by the failing check or the named missing item, and permit at most 2 narrowed re-attempts before the event is abandoned and suppression is recorded.
- Assign every clearing operation exactly 1 terminal state from the closed set: cleared, retained, externalized-and-cleared, reverted, quarantined, or suppressed, and record it in the ledger.
- Quarantine, rather than clear, any candidate implicated in 2 consecutive reverts, excluding it from the candidate set for the remainder of the run.

**Required Outputs**:

- A revert record with the failing check, the restored hash, and the comparison verdict.
- A terminal state per clearing operation, drawn from the closed set.
- A quarantine list for the run.

**Quality Checkpoints**:

- A failed validation always reverts; the post-edit view is never repaired in place and never sent with a warning attached.
- The restored view's hash equals the pre-edit snapshot hash; a mismatch halts the run.
- No event re-attempts the identical block more than 2 times; a third attempt is prohibited and the event is suppressed.

***

### Phase 6: Re-Execution Detection and Policy Correction

**Objective**: Detect the loops and losses that clearing causes, bound them, and correct the eligibility policy against measured outcomes rather than against intent.

#### Step 6.1: Detect Re-Execution Against the Clearing Ledger

**Required Actions**:

- Compute a call signature for every tool call as the tuple of tool name, canonicalized argument hash, and, once the result returns, the result content hash, and record it in the ledger on every call.
- Raise a re-execution event when a call signature matching a cleared transaction's signature is issued after that transaction's clear event, and attribute the event to the clear-event identifier rather than to the tool.
- Raise a loop event when the same signature recurs 3 times within 20 assistant turns, or when 2 re-executions of the same clear-event lineage occur without an intervening state change in the task ledger.
- Raise a missing-evidence event when a later verification, citation, or compensating action cannot be completed and its inputs trace to a cleared transaction, whether or not a re-execution occurred.
- Raise a placeholder-confusion event when a model output quotes a placeholder as evidence, asserts content the placeholder does not carry, or requests a recovery the placeholder declares impossible.
- Bind every raised event to the clear-event identifier, the policy version, and the limb of the incorporation test that passed the candidate, so that correction targets the limb that erred.

**Required Outputs**:

- A call-signature record for every tool call in the run.
- Raised events of 4 types, each bound to a clear-event identifier and a policy version.
- An attribution record naming the incorporation-test limb that admitted each implicated candidate.

**Quality Checkpoints**:

- Every tool call carries a signature; a call without one cannot be matched and is a detection gap.
- Every raised event resolves to exactly 1 clear-event lineage; an unattributable event is escalated for manual review.
- Missing-evidence events are raised independently of re-execution, since the most damaging losses produce no repeat call at all.

***

#### Step 6.2: Open the Circuit and Correct the Eligibility Policy

**Required Actions**:

- Open the circuit on the second re-execution of a clear-event lineage: restore the transaction from its recovery reference, mark it protected for the remainder of the run, and prohibit further clearing of that lineage.
- Escalate to the tool class on the third loop event within one run: raise the retention floor for that class by 1 transaction, or move the class from clear-directly to persist-first, and record which correction was applied.
- Disable automatic clearing for a tool class immediately on any missing-evidence event of high severity, defined as one that prevented a completed task, a supported citation, or a compensating action, and hold the class disabled pending review.
- Strengthen the placeholder rather than the threshold on a placeholder-confusion rate above 2 percent of turns containing placeholders, since confusion is a marker defect and raising the trigger conceals it.
- Prohibit widening eligibility as a response to any raised event, and require that every correction move the policy toward retention, never away from it, until Step 6.3 supplies contrary measurement.

**Required Outputs**:

- A circuit-breaker record per opened lineage, with the restoration route used.
- A policy correction record naming the class, the correction applied, and the triggering event.
- A disabled-class register with the review status of each entry.

**Quality Checkpoints**:

- No lineage is cleared after its circuit has opened; a second clearing of an opened lineage is a defect that halts the run.
- Every correction moves the policy toward retention; a correction that widens eligibility in response to a failure is rejected.
- A high-severity missing-evidence event disables its tool class within the same run, not at the next tuning cycle.

***

#### Step 6.3: Measure Clearing Precision and Retune the Thresholds

**Required Actions**:

- Compute clearing precision per tool class and per policy version as cleared results with no subsequent recovery, re-execution, or missing-evidence event divided by all cleared results, over a window of at least 50 clearing events.
- Compute net reclaim as gross tokens removed minus placeholder tokens, minus tokens reintroduced by recovery, minus tokens re-established after each cache boundary, and report it alongside the gross figure rather than instead of it.
- Run a matched comparison against a no-clearing baseline on a frozen replay set of at least 30 long-horizon cases, holding model, tools, and task seeds fixed, and measure completed-task outcome rather than rendered token count alone.
- Retune exactly 1 threshold per cycle, re-measure over a full window, and promote the change only where completed-task outcome is non-inferior, clearing precision is at least 95 percent, and net reclaim is positive.
- Roll back automatically on any regression gate breach: a completed-task outcome decline, any high-severity missing-evidence event, a re-execution rate above 5 percent of cleared results, a negative net reclaim, or any structural validation failure reaching production.
- Repeat the whole measurement after any change to the model, the tokenizer, the tool schemas, the provider's editing behaviour, or the workload distribution, since every threshold in this guide is bound to those.

**Required Outputs**:

- A clearing precision figure per tool class and policy version, over a stated window.
- A net reclaim figure reported beside the gross figure for each policy version.
- A matched comparison record against the no-clearing baseline, with the regression gate verdicts.

**Quality Checkpoints**:

- Clearing precision is at least 95 percent per tool class; below that, the class moves to persist-first or protected before any threshold is loosened.
- Net reclaim is positive; a positive gross figure with a negative net figure blocks promotion.
- Exactly 1 threshold changes per tuning cycle; a multi-threshold change is rejected because its effect cannot be attributed.

***

## III. Implementation Guidance for AI Agents

AI agents editing a context in place must follow systematic protocols ensuring that every removal is authorized, recoverable, visible, structurally valid, and attributable. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Policy Agent**: Owns the clearing contract, the tool register, the clearability classes, and the threshold record. It alone may amend a class or a threshold, and every amendment is versioned. It never evaluates a candidate.
2. **Candidate Agent**: Freezes the candidate set at the trigger, applies exclusions, orders candidates oldest first, computes the contiguous cut block, and takes the pre-edit snapshot. It never removes content.
3. **Adjudication Agent**: Executes the incorporation test, resolving the durable-state and dependency limbs deterministically and issuing the model-tier judgement for the later-message limb only. It returns clearable, retain, or uncertain, and uncertain resolves to retain.
4. **Externalization Agent**: Submits persist-first candidates through the write contract, waits for durability receipts, verifies read-backs and derivative watermarks, and removes every unconfirmed candidate from the clearable subset. It alone may declare a candidate recoverable.
5. **Edit Agent**: Constructs placeholders, computes the cache boundary, applies the block as 1 atomic edit, counts post-edit tokens, and writes the ledger entry. It never decides eligibility.
6. **Validation Agent**: Runs structural validation and the continuity probe on the post-edit view, issues the commit or revert verdict, and restores the snapshot on failure. It holds veto authority over every edit and may not be overridden.
7. **Detection Agent**: Maintains call signatures, raises re-execution, loop, missing-evidence, and placeholder-confusion events, opens circuits, and computes clearing precision and net reclaim. It may disable a tool class without authorization.

**Recoverability Boundary**: No component may remove content from the active model view unless the Externalization Agent has recorded a receipt or the Adjudication Agent has classified the candidate as deterministic-replay. This is a hard constraint applying to every component, including a provider-native editor operating under a configuration this system supplied.

- Treat an enabled provider-native editor as a component that will remove content on its own schedule, and constrain it by excluding every tool whose class is protected or persist-first rather than by intending to intervene at the moment it fires.
- Never rely on a model's report that content was saved; rely on the receipt.
- Never rely on the absence of an error as evidence that an edit was valid; run the validation.

**Workflow Execution Pattern**:

```
STATE: Phase_4_Placeholder_Construction_And_Application
ACTIONS:
  1. Construct one placeholder per clearable candidate
  2. Resolve and verify each recovery reference
  3. Compute cache boundary and expected subsequent calls
  4. Apply contiguous block as one atomic edit
  5. Count post-edit tokens and write ledger entry
VALIDATION:
  - every_removed_result_has_placeholder == TRUE
  - every_recovery_reference_resolves == TRUE
  - parallel_group_partially_cleared == FALSE
  - cache_boundaries_established == 1
  - placeholder_tokens / reclaimed_tokens <= 0.15
TRANSITIONS:
  IF all_validations_pass THEN next_state = Phase_5_Structural_Validation
  ELSE next_state = Phase_5_Revert_Path
```

**Two-Phase Action Pattern**:

1. **Plan**: Freeze the candidate set, run the incorporation test, and emit the proposed cut block with per-candidate verdicts and recovery routes, changing nothing.
2. **Confirm**: Obtain receipts, verify read-backs, and construct placeholders while every candidate remains resident in the context.
3. **Execute**: Apply the edit only after every candidate in the block is confirmed recoverable, then validate and either commit or revert.

**Approval Gate**: Human authorization is required before any of the following, and no threshold or budget pressure substitutes for it: enabling automatic clearing in production for the first time on a workload; moving any tool class from protected or persist-first toward clear-directly; enabling the clearing of tool call arguments; clearing on a request path whose canonical transcript is not durable; and re-enabling a tool class disabled by a high-severity missing-evidence event. The numeric trigger for review is any policy change that raises the expected cleared volume by more than 25 percent, or any measured clearing precision below 95 percent.

**Context Management Requirements**:

- Hold the clearing contract, the tool register, the threshold record, and the ledger in durable state, since a clearing policy must outlive the context it edits.
- Keep the ledger outside the active model view; a ledger rendered into the context grows with every event and becomes the next candidate set.
- Bound the Detection Agent's own consumption and count it against the reclaim, so that detection overhead is visible in the net figure rather than treated as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Ownership Integrity (After Phase 1)**

- **Automated Check**: Exactly 1 component mutates the rendered request across at least 20 fixture paths; every registered tool carries a clearability class; every threshold carries a numeric value and a bound workload, model, and tokenizer.
- **Agent Action on Pass**: Permit clearing events on the declared paths.
- **Agent Action on Failure**: Halt the deployment and return the specific defect; no content is removed under an ambiguous ownership or an incomplete register.
- **Human Review Trigger**: Any path on which 2 or more components mutate the request, or any request path whose canonical transcript is not durable.

**Checkpoint 2: Candidate and Test Integrity (After Phase 2)**

- **Automated Check**: No frozen candidate sits inside the retention floor or carries a protected class; every candidate holds 3 limb verdicts; every uncertain verdict resolved to retain.
- **Agent Action on Pass**: Proceed to externalization.
- **Agent Action on Failure**: Drop the offending candidates from the block and re-evaluate the remainder; never widen the block to compensate for the loss.
- **Human Review Trigger**: More than 20 percent of candidates resolving to uncertain across 10 consecutive events, which indicates a test the deployment cannot execute.

**Checkpoint 3: Recoverability (After Phase 3)**

- **Automated Check**: Every persist-first candidate holds a durability receipt whose read-back hash matches the submitted hash; every replay-route candidate holds a version-pinned descriptor; no side-effecting tool holds a replay route.
- **Agent Action on Pass**: Proceed to placeholder construction.
- **Agent Action on Failure**: Return the unconfirmed candidates to the retained set and raise a write defect against the store.
- **Human Review Trigger**: Any occurrence of a removal without a confirmed receipt, which disables automatic clearing for the affected tool class immediately.

**Checkpoint 4: Marker and Boundary Integrity (After Phase 4)**

- **Automated Check**: Every removed result carries exactly 1 resolving placeholder within 80 tokens; placeholder tokens are at most 15 percent of the reclaim; exactly 1 cache boundary was established; at least 3 subsequent calls are expected.
- **Agent Action on Pass**: Proceed to structural validation.
- **Agent Action on Failure**: Revert the edit and re-plan the block as a contiguous cut with a raised minimum candidate size.
- **Human Review Trigger**: Placeholder tokens exceeding 25 percent of the reclaim on 3 consecutive events.

**Checkpoint 5: Post-Edit Validity (After Phase 5)**

- **Automated Check**: All 5 structural checks pass; the continuity probe returns pass; on a revert, the restored hash equals the pre-edit snapshot hash.
- **Agent Action on Pass**: Commit the post-edit view and send it.
- **Agent Action on Failure**: Revert to the snapshot, narrow the block, and permit at most 2 narrowed re-attempts before suppressing the event.
- **Human Review Trigger**: Any structural validation failure reaching a production request, or any revert whose restored hash does not match.

**Checkpoint 6: Outcome and Policy Integrity (After Phase 6)**

- **Automated Check**: Clearing precision at least 95 percent per tool class over at least 50 events; re-execution rate at most 5 percent of cleared results; net reclaim positive; zero high-severity missing-evidence events.
- **Agent Action on Pass**: Retain the policy version and permit the next single-threshold tuning cycle.
- **Agent Action on Failure**: Roll back to the prior policy version and move the failing class toward retention.
- **Human Review Trigger**: Any high-severity missing-evidence event, or a positive gross reclaim with a negative net reclaim across 2 consecutive windows.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
POLICY_VERSION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Re-Execution Loop After Invisible Clearing**

- **Symptoms**: The same call signature recurs after its transaction was cleared; rendered tokens fall at each event and rise again within a few turns; the task ledger shows no state change between repetitions; token-reduction reporting appears healthy while the run makes no progress.
- **Diagnostic Steps**: Resolve the repeated signature to its clear-event lineage in the ledger; confirm whether a placeholder was emitted at that position and whether its recovery reference resolves; where a provider-native path applied the edit, reconstruct the post-edit view and inspect the marker the provider actually wrote.
- **Resolution Protocol**: Option A, restore the transaction from its recovery reference and mark the lineage protected for the run. Option B, strengthen the placeholder so it names the terminal status and the recovery instruction explicitly, then re-measure the confusion rate. Option C, raise the retention floor for the tool class by 1 transaction so the result survives long enough to be incorporated. Option D, move the class to persist-first so recovery resolves to an archive rather than a repeated call.
- **Escalation Trigger**: Identical re-execution of one lineage is prohibited on the second occurrence, which opens the circuit; 3 loop events in one run disable automatic clearing for the tool class regardless of remaining budget.

**Error Type 2: Unrecoverable Removal**

- **Symptoms**: A citation cannot be supported; a verification cannot be run; a compensating action cannot be constructed; a recovery reference resolves to nothing, to a different version, or to an item whose hash does not match the one recorded.
- **Diagnostic Steps**: Determine whether the candidate was ever externalized, whether a receipt was recorded before the edit, and whether the read-back was verified; where the route was replay, compare the replayed content hash against the pinned version to establish whether the source changed rather than the archive failing.
- **Resolution Protocol**: Option A, restore from the canonical transcript where policy permits it, which is the only route that survives a failed archive. Option B, where the source changed, expose both versions explicitly and invalidate every claim that depended on the original rather than substituting the new bytes. Option C, halt the task, open an incident, and disable the tool class pending review. Option D, move the class to protected permanently where the loss is structural rather than incidental.
- **Escalation Trigger**: Any high-severity occurrence, defined as one preventing a completed task, a supported citation, or a compensating action, disables the class in the same run; this class of error is never resolved by retry, because the bytes are gone.

**Error Type 3: Structural Break in the Post-Edit View**

- **Symptoms**: The provider rejects the request; a tool call appears with no outcome of any kind; one member of a parallel group carries a placeholder while its siblings carry results; role alternation or block ordering fails the provider's validator.
- **Diagnostic Steps**: Run the 5 structural checks individually and identify which failed; confirm whether the failing edit split a transaction, cleared a pending call, or removed a block the grammar requires; where the editor is provider-native, confirm whether the break originated in the local edit or in the provider's own transformation.
- **Resolution Protocol**: Option A, revert to the pre-edit snapshot and re-plan the block so that transactions are atomic. Option B, narrow the block to exclude the implicated transaction and re-attempt at most 2 times. Option C, where breaks recur under a provider-native path, move ownership to an application-side editor so the post-edit view is observable and testable.
- **Escalation Trigger**: A third narrowed re-attempt is prohibited and suppresses the event; any structural failure reaching a production request escalates for review of the validator itself.

**Error Type 4: Placeholder Confusion**

- **Symptoms**: A model output quotes a placeholder as though it were the result; content is asserted that the placeholder does not carry; a removal is described as a tool failure; a recovery is requested that the placeholder declares impossible.
- **Diagnostic Steps**: Compute the confusion rate over turns containing placeholders; inspect the implicated placeholders for a missing terminal status, a missing non-evidence notice, or an unresolvable reference; where the path is provider-native, record the observed marker text, since it is supplied by the provider and is not configurable.
- **Resolution Protocol**: Option A, add the missing field and re-measure. Option B, distinguish removal from failure explicitly in the marker text where the two are being conflated. Option C, move to an application-side editor where the marker text must be controlled and the provider does not permit it.
- **Escalation Trigger**: A confusion rate above 2 percent of turns containing placeholders triggers marker correction; above 10 percent, clearing is suspended for the workload until the rate is re-measured below the lower bound.

**Error Type 5: Cache Thrash and Negative Net Reclaim**

- **Symptoms**: Event frequency rises while cost per completed task rises with it; latency increases after edits; gross reclaim is positive and net reclaim is negative; edits fall at early positions in the rendered request.
- **Diagnostic Steps**: Recompute the cache boundary per event and the tokens re-established after it; segment events by the number of subsequent calls that carried the reclaimed tokens; separate events that established 1 boundary from those that established several.
- **Resolution Protocol**: Option A, raise the minimum reclaim so fewer, larger events run. Option B, extend the hysteresis interval so a threshold oscillating around its trigger does not fire each turn. Option C, cut contiguously from the oldest position only, so 1 boundary is established per event. Option D, disable automatic clearing for the workload and route the pressure to selection or delegation instead.
- **Escalation Trigger**: Negative net reclaim across 2 consecutive measurement windows disables automatic clearing for the workload; a positive gross figure is never accepted as evidence against a negative net figure.

**Error Type 6: Competing Editors and Double Removal**

- **Symptoms**: Identical runs produce different rendered requests; a transaction is removed that the ledger does not record removing; a second component acts on a placeholder as though it were original content; ownership diffs show 2 or more mutators on one path.
- **Diagnostic Steps**: Re-run the fixture set and diff the canonical transcript, the pre-provider payload, and the reconstructed post-edit view; enumerate every middleware, reducer, compactor, and retry wrapper on the path and check its defaults rather than its configuration.
- **Resolution Protocol**: Option A, disable every mutator except the declared owner and re-run the diff. Option B, where 2 owners are genuinely required, partition their domains so they cannot touch the same logical item, and test the composition on fixtures containing parallel calls and errors. Option C, move to a single application-side owner where the provider path cannot be disabled selectively.
- **Escalation Trigger**: Any nonzero undeclared dual-mutation rate blocks release; this class is never resolved by tuning thresholds, because the defect is in ownership rather than in policy.

**Troubleshooting Decision Tree**:

```
CLEARING EVENT PRODUCES A DEFECT
├─ RECOVERY DEFECT
│   ├─ Reference resolves to nothing → Restore from canonical transcript; disable class
│   ├─ Replay returns a different hash → Expose both versions; invalidate dependent claims
│   └─ No receipt recorded before edit → HALT; disable automatic clearing for the class
├─ VISIBILITY DEFECT
│   ├─ Call present with no outcome → Emit placeholder; open circuit on the lineage
│   ├─ Marker quoted as evidence → Add non-evidence notice; re-measure confusion rate
│   └─ Removal read as tool failure → Add terminal status to the marker
├─ STRUCTURE DEFECT
│   ├─ Orphaned call or result → REVERT to snapshot; re-plan as atomic transactions
│   ├─ Parallel group partially cleared → REVERT; clear all siblings or none
│   └─ Provider grammar rejected → REVERT; test against the provider validator
├─ ECONOMICS DEFECT
│   ├─ Several boundaries per event → Re-plan as one contiguous cut from oldest
│   ├─ Fewer than 3 subsequent calls → Suppress the event; record the reason
│   └─ Net reclaim negative twice → Disable clearing for the workload
└─ OWNERSHIP DEFECT
    ├─ Two mutators on one path → HALT release; disable all but the declared owner
    └─ Ledger missing a removal → HALT; treat the path as untrusted until diffed
```

### D. Performance Metrics and Continuous Learning

**Safety Metrics**:

- **Clearing precision**: Cleared results never subsequently recovered, re-executed, or implicated in a missing-evidence event, over all cleared results (target: at least 95 percent per tool class; below 90 percent moves the class to persist-first).
- **Persistence coverage**: Clearing events requiring externalization that held a verified receipt before removal, over all such events (target: 100 percent; any shortfall is a defect, not a rate).
- **Recovery success**: Recovery attempts resolving to content whose hash matches the original, over all recovery attempts (target: at least 99 percent; hash-matched recovery is reported separately from changed-source recovery).
- **Information-loss incidents**: Completed tasks, citations, decisions, or side effects that could not be verified or continued because removed content was unavailable (target: 0 for any workload carrying an audit, citation, or side-effect obligation).
- **Structural validation failure rate**: Edits failing validation over all edits applied (target: below 1 percent; failures reaching a production request target 0).

**Economic Metrics**:

- **Gross reclaim**: Pre-edit rendered tokens minus post-edit rendered tokens, computed with the target tokenizer (reported, never used alone as a success criterion).
- **Net reclaim**: Gross reclaim minus placeholder tokens, minus tokens reintroduced by recovery, minus tokens re-established after the cache boundary (target: positive median and positive tail across a window of at least 50 events).
- **Edit churn**: Clearing events per 100 assistant turns, with median turns between events (target: at most 10 events per 100 turns; higher churn with flat net reclaim indicates cache thrash).
- **Marker overhead ratio**: Placeholder tokens over reclaimed tokens per event (target: at most 15 percent; above 25 percent raises the minimum candidate size).
- **Detection overhead**: Tokens and calls consumed by signature computation, probing, and ledger maintenance, over the net reclaim (target: at most 10 percent; detection is counted against the saving, never treated as free).

**Behavioural Metrics**:

- **Re-execution rate**: Cleared transactions followed by a matching call signature, over all cleared transactions (target: at most 5 percent; above 10 percent suspends clearing for the class).
- **Loop rate**: Clear-event lineages reaching 3 repetitions within 20 turns, over all cleared lineages (target: 0).
- **Placeholder confusion rate**: Turns in which a marker is cited, elaborated, or misread as a failure, over turns containing markers (target: at most 2 percent).
- **Uncertain-verdict rate**: Candidates whose incorporation test returned uncertain, over all candidates evaluated (target: at most 20 percent; a higher rate indicates a test the deployment cannot execute rather than a cautious policy).
- **Completed-task outcome delta**: Edited-run outcome minus matched no-clearing baseline outcome on the frozen replay set (target: non-inferior; any decline blocks promotion regardless of reclaim).

**Log-Pattern Failure Detection**: A repeated call signature after a clear event indicates a missing or unread placeholder. Falling rendered tokens with flat task progress indicates a re-execution loop rather than an efficiency gain. Rising event frequency with rising cost per completed task indicates cache thrash. A recovery attempt immediately following a clear event indicates a retention floor set below the dependency chain. A high uncertain-verdict rate concentrated in one tool indicates a tool whose results are not being incorporated into any durable record. Zero recoveries alongside a rising missing-evidence count indicates that losses are silent rather than absent, which is the more dangerous of the two patterns.

**Learning and Adaptation Mechanisms**:

- **Limb-attributed correction**: Record which limb of the incorporation test admitted every candidate implicated in a later failure, and correct that limb rather than the aggregate threshold.
- **Class migration over threshold change**: Prefer moving a tool class toward retention over loosening or tightening a global threshold, since class membership is attributable and a global threshold is not.
- **Frozen replay set**: Freeze the replay corpus before any threshold is tuned against it, and grow it only by adding cases, never by removing ones a policy fails.
- **Policy versioning**: Version every policy and record the version on every clearing event, so that a past event replays against the exact policy that produced it.
- **Recalibration on environment change**: Recompute every threshold after a change to the model, the tokenizer, the tool schemas, the provider's editing behaviour, or the workload distribution; the values in this guide are deployment defaults, not constants.

**Human-in-the-Loop Boundaries**: Moving a tool class toward clear-directly, enabling the clearing of call arguments, re-enabling a class disabled by a high-severity loss, clearing on a path whose canonical transcript is not durable, and accepting a policy whose completed-task outcome declined are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the removal of already-rendered tool output rather than the content of any particular output. Its phases hold wherever an agent calls tools that return more content than the eventual decision requires, and wherever the record of what was called must survive the removal of what was returned.

### 4.1 Cross-Domain Application Patterns

**Software engineering and infrastructure operations**: File reads, build logs, test output, and search results dominate the budget and are the clearest clear-directly candidates, because a pinned commit makes replay deterministic. The dependency limb dominates here: a failing test's output remains protected while the failure is under diagnosis and becomes clearable the moment a fix is committed and the fix's rationale is written into the task ledger. Command results that changed state, such as a deployment or a migration, carry side effects and never carry a replay route; their receipts remain resident or move to the archive. The characteristic failure is a re-execution loop over a large file read, which is cheap enough to repeat that it escapes notice until the turn budget is exhausted.

**Regulated clinical and pharmaceutical research**: Most tool results serve as evidence for claims that must remain traceable, so the persist-first class is the default rather than the exception, and the clear-directly class is confined to enumerations and lookups that no conclusion cites. The canonical transcript is a regulatory artifact rather than a debugging aid, and its durability gates whether clearing may run at all. Removal from the active model view is never represented as deletion, since retention obligations, audit stores, and provider logs are governed independently of what the next call renders.

**Financial services operations**: Reversibility varies sharply within one run: a quote lookup is reproducible, a ledger posting is not, and a reconciliation result is reproducible only until the underlying period closes. The replay-safety classification therefore carries more weight than the size threshold, and version pinning binds to a period or a statement identifier rather than to a timestamp. Side-effect receipts are permanently protected, because reconstructing a compensating action from a re-run is capable of issuing a second transaction.

**Public-sector case handling**: Case records, correspondence, and prior determinations are frequently non-reproducible, since the retrieval that produced them may not be repeatable by the same authorization later. Externalization is therefore mandatory before any removal, and the recovery reference binds to an opaque case-scoped identifier rather than to a path, so that the placeholder does not itself disclose case detail into the rendered context. Holds and retention rules apply per record and suspend clearing for the records they cover regardless of budget pressure.

**Industrial and field maintenance**: Sensor dumps, telemetry windows, and equipment logs are large, high-frequency, and mostly consumed once, which makes them ideal clearing candidates; but their sources are mutable and often rolling, so a replay minutes later returns a different window. Externalization with a pinned observation interval is the only safe route, and a changed replay is treated as new evidence rather than as recovery of the original. Latency budgets are tight, so the batching rule binds harder here than elsewhere: rare bulk edits are preferred over any per-turn editing.

### 4.2 Scale, Risk, and Latency Adaptation

- **Short sessions and small budgets**: Suppress clearing entirely where the rendered request is expected to stay below 50 percent of the usable budget for the whole run, because every event costs a cache boundary and a marker while reclaiming nothing the run needed.
- **Low-risk reversible workloads**: Permit the clear-directly class, retain the retention floor at 3 transactions, and accept replay as a recovery route for deterministic tools. Clearing precision below 90 percent still moves a class to persist-first, since a cheap loss is still a loss.
- **High-risk or audit-critical workloads**: Default every class to persist-first or protected, require a durable canonical transcript before any event runs, prohibit the clearing of call arguments entirely, and treat any information-loss incident as a run-halting event rather than a rate to be managed.
- **Strict latency budgets**: Raise the minimum reclaim and lengthen the hysteresis rather than removing validation, since validation is cheap relative to a rejected request and a reverted turn. Where latency forbids a continuity probe, suppress clearing rather than clearing unprobed.
- **Long-horizon autonomous runs**: Persist the ledger, the tool register, and the policy version outside the context, re-derive the retention floor from the observed dependency chain at each context boundary, and treat every boundary crossing as a point at which recovery references must be re-verified rather than assumed live.
- **Multi-agent deployments**: Declare the editing owner per request path rather than per agent, since a subagent inheriting a parent's rendered context can otherwise apply a second edit to content the parent already edited. Recovery references must resolve in every context that can receive the placeholder, or the placeholder is a dead pointer in the subagent's context.

***

## V. Limitations and Considerations

**Correctness of clearing cannot be established in advance**: The incorporation test predicts that nothing downstream will cite a result, and that prediction is checked only by the absence of a later failure. A policy can pass every checkpoint in this guide and still remove a result that a later turn needed. The mitigation is the measurement in Step 6.3, which computes clearing precision against observed recoveries and missing-evidence events, together with the conservative default that retains every uncertain candidate, so that error accumulates on the side of retention rather than loss.

**Irreversibility is absolute once the boundary is crossed**: Content removed from the active model view and absent from every durable store cannot be recovered by any later action, and the failure surfaces turns after the event that caused it. The mitigation is the receipt requirement in Step 3.2 and the residency rule, which hold each candidate in both locations until a read-back-verified receipt exists; where a receipt does not return, the operation ends in the retained terminal state and the budget pressure is routed to another operation.

**Provider defaults are vendor-reported and model-specific**: Documented values such as a 100,000-input-token activation trigger, retention of the 3 most recent tool uses, an aggregate minimum-reclaim parameter, tool exclusion lists, and call-argument clearing disabled by default are published by a single provider for a specific strategy identifier under a beta header, and are subject to change with the model, the API version, and the SDK. Reported improvements in agentic evaluations and reported token reductions in long web-search runs originate in that provider's internal evaluations. The mitigation is to treat every such figure as vendor-reported directional evidence, to verify capability at runtime against the current model and header rather than assuming support, and to derive every operating threshold from the deployment's own measurement.

**The thresholds in this guide are deployment defaults**: The activation trigger at 60 percent of usable budget, the retention floor of 3 transactions, the minimum candidate size of 500 tokens, the 80-token placeholder bound, the 15 percent marker overhead ratio, the 10-turn event spacing, the 5-turn hysteresis, the 95 percent precision floor, and the 5 percent re-execution ceiling were chosen to be operable on first deployment, not derived from a measured property of any model. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute them per workload and tool class against observed outcomes.

**Provider-native editing limits observability**: Where the edit is applied server-side, the exact post-edit view is generally not returned, the marker text is not configurable, and applied-edit statistics are the only direct evidence of what happened. Local reconstruction of the edited view is an inference, not an observation. The mitigation is the labelling rule in Step 5.1, which records a reconstructed payload as reconstructed and never as the provider's payload, together with the guidance to move ownership to an application-side editor wherever exact replay or marker control is a hard requirement.

**Clearing is not deletion and must never be represented as such**: Removing content from the rendered request does not remove it from the canonical transcript, the durable store, provider logs, caches, backups, or resumable session state, each of which is governed by a separate retention policy. A deletion request closed by clearing alone is not satisfied. The mitigation is to route every erasure obligation to the lifecycle contract that owns retention and erasure propagation, and to state the distinction in the clearing contract so that no operator infers otherwise.

**Preserving an unedited transcript creates its own exposure**: The canonical transcript that makes clearing reversible is a complete record of every payload the agent ever saw, and its existence enlarges the surface that must be protected. The mitigation is least privilege, purpose limitation, tenant and branch namespacing, opaque identifiers in place of paths inside placeholders, and a declared retention limit on the transcript itself rather than indefinite accumulation.

**Untrusted tool output can attempt to influence the policy**: Tool results are attacker-reachable in many deployments, and a result asserting that it is safe to clear, that an exclusion should be lifted, or that a durable write should be made is an instruction injected into the evaluation path. The mitigation is the tier partition in Section 1.3: clearability classes, exclusions, and receipts are deterministic-tier state that no model-tier judgement and no tool content can alter, and the model tier's single decision is confined to whether a later message restates an earlier result.

**Measurement requires a baseline that costs what it measures**: Establishing that clearing did not degrade outcomes requires matched no-clearing runs over a frozen replay set, which doubles evaluation cost for the workloads most likely to be under schedule pressure. The mitigation is the regression gate in Step 6.3, which withholds promotion of a policy whose completed-task outcome has not been compared against a baseline, and the smaller frozen set of at least 30 cases, which bounds the cost rather than removing the requirement.

***

## VI. Conclusion and Summary

Context editing is a state transformation before it is a token-saving technique. Tool results are the largest and fastest-growing occupant of a tool-using agent's budget, and most of them are read once and never consulted again, so clearing them is the highest-yield operation available against a context under pressure. What makes it safe is not the size of the result nor the age of the turn but four conditions established before anything is removed: that the information has been incorporated somewhere that survives, that the bytes are recoverable from a confirmed durable copy or a deterministic replay, that a placeholder will record the call and its recovery route, and that the post-edit view still satisfies the structure the provider requires.

A deployment introducing clearing should instrument before it edits. Establish the canonical transcript, the tool register, and the ledger; measure how much of the budget tool results actually consume and how often they are consulted after their first use; then enable clearing on the single tool class whose results are largest, most reproducible, and least cited, with every other class protected. Add classes only as measured clearing precision permits, changing 1 threshold per cycle, and treat the first re-execution loop or missing-evidence event as evidence that the eligibility policy is wrong rather than that the threshold is high. A smaller rendered request that completes fewer tasks is not an optimisation.

**Key Success Factors**:

- **Incorporation before removal**: A result leaves the context only where its information has been carried into durable state or into a later message, and an uncertain verdict retains rather than clears.
- **Externalization before clearing**: A durability receipt whose read-back hash matches is the only evidence that permits a removal, because content cleared without one is gone.
- **Visible removal**: Every cleared result leaves a placeholder naming the call, its terminal status, and its recovery route, since an invisible removal invites the re-execution loop that costs more than the clearing saved.
- **Validation with revert**: Structural validation runs on every edit and a failure restores the pre-edit snapshot; a post-edit view is never repaired in place and never sent with a warning attached.
- **Rare bulk cuts from the oldest position**: One contiguous edit establishing one cache boundary, spaced by declared hysteresis, rather than continuous small edits whose gross saving conceals a negative net.
- **Attributable policy**: Every event carries its policy version, its ledger entry, and the test limb that admitted each candidate, so that a later failure corrects the specific rule that produced it.

By following this guide, AI agents can recover the largest single component of a context budget while keeping every removal reversible, visible, structurally valid, and attributable to the policy that authorized it.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them; except where an entry is marked as verified during conversion, they were not independently re-verified, and their titles and locations are reproduced rather than checked.

**Corpus pointers**:

- `Context Editing and Tool-Result Clearing: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the clearing, summarizing, offloading, and retention decision rules, the never-clear-automatically list, the core invariants, the clearing contract fields, the placeholder discipline, the persist-then-clear loop, the threshold tuning and cache break-even loops, the ownership-conflict audit, the message-validity and replay requirements, the logging contract, the metric definitions, the failure-mode taxonomy, and the end-to-end implementation sequence. It carries inline citations to provider documentation and to independent long-context research; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — owns the externalization contract this guide invokes before every clearing event. Source of the write handle, stable identifier, selectable header, durability receipt, release, and residency copy terms, which are adopted unchanged in Section 1.1 and Phase 3.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the umbrella guidance. Source of the four-family operation ladder, the partitioned budget and output reserve, the admission gate, the protected atom list, and the utilization and supersession definitions this guide assumes.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — owns summarisation and the preservation manifest. Source of the tool-result clearing and observation masking definitions adopted in Section 1.1, and the destination for any operation that needs a result's meaning rather than its bytes.
- `advanced_task_guides/context-management/guide_KVCacheAwarePromptConstruction.md` — owns exact-prefix reuse, cache lifetimes, and break-even arithmetic. This guide carries only the agent-layer batching consequence stated in Section 1.4 and defers the underlying mechanics to that guide.
- `advanced_task_guides/context-management/guide_SlidingWindowContext.md` — owns application-managed eviction mechanics, whole-unit boundaries, and message-sequence grammar. Applicable to the structural validation in Step 5.1 and to any deployment where windowing and clearing could both claim ownership of removal.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — owns retention, archive, deletion, and erasure propagation. The destination for every erasure obligation that clearing does not and cannot satisfy, as stated in Section V.
- `advanced_task_guides/context-management/guide_FilesystemAsContext.md` — owns file layout, path contracts, bounded reads, and write scope. Applicable to the durable destinations selected in Step 3.1 and to the recovery references bound in Step 4.1.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — owns cross-stage diagnosis, circuit breakers, and incident response. Applicable to the circuit-breaker and disabled-class mechanics in Step 6.2 and to the escalation triggers in Section III.C.

**External references**:

*Provider documentation for in-place editing, compaction, and memory*

1. Anthropic, *Context editing* — https://platform.claude.com/docs/en/build-with-claude/context-editing (verified during conversion: the strategy identifier, the beta header, the 100,000-input-token default trigger, the default retention of 3 tool uses, the aggregate minimum-reclaim parameter, the tool exclusion list, the call-argument clearing default of false, the applied-edit response fields, and the statement that clearing invalidates cached prompt prefixes and incurs cache-write costs were confirmed against this page)
2. Anthropic, *Context management announcement* — https://www.anthropic.com/news/context-management
3. Anthropic, *Compaction* — https://platform.claude.com/docs/en/build-with-claude/compaction
4. Anthropic, *Memory tool* — https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
5. Anthropic, *Context engineering cookbook: memory, compaction, and tool clearing* — https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools
6. Anthropic, *Claude Platform release notes* — https://platform.claude.com/docs/en/release-notes/overview
7. Anthropic, *Agent SDK hosting guide* — https://platform.claude.com/cookbook/claude-agent-sdk-07-hosting-the-agent
8. OpenAI, *Compaction* — https://developers.openai.com/api/docs/guides/compaction
9. Google, *Interactions API overview* — https://ai.google.dev/gemini-api/docs/interactions-overview
10. Google, *Context caching* — https://ai.google.dev/gemini-api/docs/caching
11. Google, *Live API reference* — https://ai.google.dev/api/live
12. Google, *Live API best practices* — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/live-api/best-practices

*Framework-side editing and message-history mutation*

13. LangChain, *Short-term memory* — https://docs.langchain.com/oss/python/langchain/short-term-memory
14. LangChain, *Built-in middleware* — https://docs.langchain.com/oss/python/langchain/middleware/built-in
15. LangGraph, *Add memory* — https://docs.langchain.com/oss/python/langgraph/add-memory

*Independent long-context and agent evaluation research*

16. Chroma Context Rot — https://www.trychroma.com/research/context-rot
17. LOCA-bench — https://arxiv.org/abs/2602.07962

*Retention and data handling*

18. Anthropic Privacy Center, *How long do you store personal data* — https://privacy.anthropic.com/en/articles/7996866-how-long-do-you-store-personal-data

