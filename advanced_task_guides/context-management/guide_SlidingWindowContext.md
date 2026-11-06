# Sliding Window Context

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Sliding window context constitutes the task family of bounding the resident set sent to a model as a conversation, tool trajectory, document stream, or event feed grows past the budget. A window retains the most recent units of work and drops older ones as new ones arrive, and pure recency is almost always wrong on its own: the task goal, the binding constraints, and the decisions already taken are the oldest content in the window, so a naive window produces an agent that has forgotten what it was asked to do while remembering the last thing it said. This guide specifies the corrective structure: a pinned region admitted by rule and bounded by a hard cap that never slides regardless of age, and a sliding region that does. It specifies the eviction unit, so a boundary that advances by token count cannot cut an item in half and leave a fragment that reads as complete; the externalization contract that must complete before any unit leaves, so eviction is a move rather than a deletion; window-size selection tied to measured task completion rather than to an advertised limit; and the signals that detect an under-sized window. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that recency-based bounding remains recoverable and auditable.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Sliding window**: A bounding discipline that keeps a suffix of the most recent units resident and advances a boundary forward as new units arrive, removing older units to hold the resident set within a declared budget. It is one realisation of the eviction operation defined by the umbrella guidance in this category, specialised to ordered content where position in the sequence is the primary eviction signal.

**Canonical transcript**: The authoritative ordered history of a session, held in a durable store, carrying stable identifiers for sessions, turns, messages, content blocks, tool calls, tool results, artifacts, and anchors. The transcript is never mutated by a window advance.

**Resident set**: The bounded projection of the canonical transcript serialized into one model call. This is the working set as defined by the umbrella guidance, restricted to ordered conversational or trajectory content. The resident set is not the transcript, and absence from the resident set is not absence from the record.

**Pinned region**: The part of the resident set exempt from position-based eviction. Membership is decided by a declared admission rule, not by age, importance judgement, or model preference. Pinned content survives every advance until its declared expiry condition fires or the pin is revoked by its owner.

**Sliding region**: The part of the resident set subject to position-based eviction. Its boundary advances forward as new units arrive and the budget is approached.

**Eviction unit**: The smallest whole element the window may remove. Eviction operates on eviction units and never on token ranges, characters, or fractions of an item. The unit is declared per content class before the first advance.

**Dependency closure**: The set of items that must leave together with a candidate because a provider grammar rule or a task-critical reference binds them: a tool call with its results, a parallel call group with its complete result set, a request with the answer that interprets it, a document chunk with its heading and source label.

**Whole-unit eviction**: The rule that every removal is the removal of one or more complete eviction units together with their dependency closure. A removal that leaves a partial message, a truncated tool result, a severed JSON object, or a broken citation tuple is a defect, not a smaller removal.

**Eviction boundary**: The position in the ordered sequence separating removed units from retained units. The boundary advances monotonically forward; content behind it is not resident.

**Advance**: One committed movement of the eviction boundary, comprising candidate selection, externalization, simulation, validation, and atomic commit. An advance is the only mechanism by which the resident set shrinks.

**Externalization**: The governed movement of content out of the window to a durable store, replacing it with a reference. The term, its contract, and its two-part structure of write and release are adopted unchanged from the write-pattern guidance in this category. Externalization is a write plus a release; a release without a confirmed write loses work.

**Durability receipt**: The deterministic tier's confirmation that a write is committed and readable after the boundary, carrying the identifier, the committed version, and the store location. Adopted from the write-pattern guidance. The receipt is the only evidence that permits release, and therefore the only evidence that permits eviction.

**Write handle**: The compact in-window replacement for released content, carrying the stable identifier, the purpose line, the shape descriptor, the size and version, and the retrieval instruction. Adopted from the write-pattern guidance.

**Boundary anchor**: A bounded record left in the sliding region stating that a contiguous span was removed, which unit types it held, and which write handles recover it. An anchor states that content left and where it can be found; it never states what the content said and is never a summary.

**Recovery reference**: The write handle or handle set an anchor names, through which an evicted span can be retrieved by an authorized tool call. An anchor whose recovery reference does not resolve is an unavailable anchor and must be marked as such.

**Protected atom**: A content element that must survive every eviction without loss: the task objective, the success criteria, the standing and safety constraints, the current plan step, the latest value of every open variable, the unresolved error state, the outstanding approvals, and the side-effect ledger. The term and its membership list are adopted unchanged from the umbrella guidance, and protected atoms are the mandatory core of the pinned region.

**Resident budget**: The token allowance available to the resident set, computed as total window capacity minus the output reserve minus operational headroom. Adopted from the umbrella guidance, where it is the context budget.

**Sliding budget**: The resident budget minus the rendered pinned region. It is the space the sliding region may occupy, and it is the quantity that determines how much history a window actually holds.

**Soft advance threshold**: The predicted resident size at which an advance begins, expressed as a percentage of the resident budget. Advancing is triggered by prediction, never by a provider rejection.

**Post-advance target**: The lower resident size an advance must reach before it commits. The gap between the soft threshold and the target is the hysteresis gap, and it is what prevents an advance on every turn near the boundary.

**Minimum eviction batch**: The smallest quantity of tokens an advance may reclaim, below which the advance is deferred rather than committed. It bounds serialization churn and prefix-cache invalidation.

**Recent-suffix floor**: The minimum number of the most recent eviction units that may never be evicted while the session is active, independent of the token budget. It guarantees that the boundary cannot advance into the live interaction.

**Under-sized window**: The condition in which the sliding budget is too small for the task, observable as repeated work, re-asked questions already answered, re-fetched artifacts already retrieved, and contradiction with decisions already recorded.

**Eviction regret**: The proportion of evicted units later retrieved through their recovery reference or judged necessary after removal. It is the primary correction signal for both window size and eviction order.

**Reason code**: A normalised categorical label recorded with every pin admission, pin rejection, eviction, anchor emission, and deferral, drawn from a closed vocabulary so that window policy is analysable without reading prose logs. Adopted from the umbrella guidance.

### 1.2 The Recency Fallacy and the Two-Region Window

**The fallacy**: A window ordered purely by recency evicts the oldest content first, and the oldest content in an agent session is systematically the most load-bearing. The task goal is stated once, at the start. The binding constraints, the prohibitions, and the acceptance criteria are stated once, at the start. The decisions already taken, the paths already ruled out, and the corrections the user already issued accumulate behind the moving boundary while the recent turns that fill the window are the least consequential material in the session. Pure recency therefore optimises exactly backwards: it preserves the transcript's froth and discards its contract.

**The measured consequence**: One 2026 study of long-horizon agents, retrieved and verified during this conversion, reports that safety-constraint violation rates rose from 0 percent while policy text remained visible to 30 percent after context reduction across seven model families over 1,323 episodes, with one family reaching 59 percent; where the constraint survived the reduction, violation stayed at 0 percent, and where it was dropped, violation reached 38 percent [3]. The failure is not that the model became less capable. The failure is that the constraint left the window and nothing recorded that it had. The same study reports that pinning the control state restored the violation rate to 0 percent in its benchmark, which is the structural claim this guide operationalises.

**The corrective structure**: The resident set is partitioned into two regions with different eviction rules. The pinned region holds content admitted by declared rule and is exempt from position-based eviction entirely. The sliding region holds everything else and advances by recency. Both regions draw on the same resident budget, and the sliding budget is what remains after the pinned region is rendered. The pinned region is not a priority tier and not a high score; it is a categorical exemption, and no relevance model, recency weight, or model preference may cross into it.

**The pinned region is bounded, not unbounded**: An exemption without a cap converts the failure mode rather than removing it. A pinned region permitted to grow starves the sliding region until the window holds a large stable prefix and two turns of live interaction, at which point the agent is again unable to do the work. The pin cap is therefore mandatory, and the state in which pinned content alone approaches the resident budget is the declared failure state of this pattern, handled by the terminal ladder in Step 2.3 rather than by borrowing space from the sliding region or the output reserve.

**Default pin classes and caps**: The classes below are deployment defaults for a general tool-using agent, recalibrated per task class against the measurements in Phase 5 and Phase 6.

| Pin class | Admission rule | Default cap, share of resident budget | Expiry condition |
| :-- | :-- | :-- | :-- |
| Instructions and safety policy | Trusted configuration only; never tool output or retrieved text | 5 to 10 percent | Session end or policy version change |
| Task contract and protected atoms | Deterministic projection of the state object | 8 to 15 percent | Objective closed or superseded |
| Active tool definitions | Schema-validated, reachable from the current plan step | 5 to 15 percent | Tool unreachable from the plan for 3 consecutive advances |
| Open effect and approval ledger | Deterministic projection; every unresolved side effect | 2 to 5 percent | Effect confirmed terminal and recorded durably |
| Current request and acceptance criteria | The live turn, never evictable | 2 to 8 percent | Turn answered and the next turn opens |
| Boundary anchor registry | Emitted by Phase 3 only, aggregated | 1 to 3 percent | Anchor span retrieved or session end |
| Total pinned region | Sum of the above | 40 percent hard ceiling | Not applicable |

**The 40 percent ceiling and its consequence**: Where the rendered pinned region exceeds 40 percent of the resident budget, the configuration fails validation and the run does not proceed to assembly. Where it exceeds 60 percent, the pin-overflow ladder in Step 2.3 runs to its terminal halt rather than to a warning. The reason is arithmetic: below a sliding budget of roughly 40 percent of the resident budget, the recent-suffix floor and the next tool observation together consume the region, and every advance removes content the next turn needs.

### 1.3 The Agent-Layer Boundary and the Model-Internal Referral

Two mechanisms adjacent to this task family sit below the AI Agent layer and cannot be executed by an agent at runtime. Both are named here as background, because misattributing an agent-layer failure to either wastes diagnosis, and because the prose literature on windowing frequently conflates them with message retention.

**Attention sinks and rolling key-value caches**: Reported work on streaming inference found that a rolling key-value cache retaining only the most recent tokens degrades once the sequence exceeds the cache size, and that retaining the key-value states of a small set of initial positions substantially restores performance even where those positions carry no semantic content; the authors named those positions attention sinks [5]. That mechanism operates on key and value tensors inside the serving layer. No agent-invocable tool exposes them, no prompt construction reaches them, and the effect is a property of attention weight accumulation at early positions rather than a property of the content at those positions. An agent must not infer from it that the first user message should be pinned forever, and must not treat an attention sink as semantically important history. Where a deployment self-hosts a model and requires sink-plus-recent serving behaviour, that configuration belongs to the serving layer and is out of scope here.

**Serving-side cache block management**: Block allocation, prefix sharing scope, preemption, recomputation, and out-of-memory handling in a rolling key-value cache are owned by the model server. An agent can observe provider-reported cache-read and cache-write token counts and can hold its serialized prefix byte-stable, and that is the whole of its available control.

**The agent-layer surrogate**: This guide carries the executable form of both. In place of physical cache retention, it specifies whole-unit retention over a declared pinned region and a recency-ordered sliding region at the message and transaction level. In place of physical cache control, it specifies prefix-stability discipline, batched advancement above a minimum eviction batch, and provider-reported cache accounting as the measurement. Prompt caching is an economic optimisation and not a store: cached content still enters the window, still occupies the resident budget, and is still subject to every rule in this guide. Cached tokens are never subtracted from resident occupancy.

**What this guide does not own**: The four-family selection ladder that decides whether a window under pressure should be written out, selected from, compressed, or isolated is owned by the umbrella guidance in this category and is not restated here. This guide assumes the ladder has selected recency-ordered eviction and owns the mechanism from that point: region partition, unit boundaries, externalization before removal, boundary advance, validity, size selection, and under-sizing correction. The durable-store contract behind every eviction is owned by the write-pattern guidance, whose write handle, durability receipt, and release semantics are adopted here without modification. Lossy reduction of retained content is owned by the compression guidance and is the escalation target when sliding is insufficient, not a step in an advance.

### 1.4 Execution Tier Partition

Every unit of work in a window advance belongs to exactly one execution tier, and most production failures of this pattern are misassignments across that partition. The partition is what makes an advance reproducible and a removal recoverable.

**Deterministic tier**: Software, serializers, token counters, schema validators, storage APIs, and linters own the pinned set and its cap arithmetic, eviction unit boundaries and dependency closure construction, token accounting against the resident budget, candidate ordering under the declared policy, externalization and receipt verification, eviction execution, provider-grammar validity linting, anchor emission and handle registration, atomic commit of the new resident version, and telemetry. These require exactness, reproducibility, and auditability that model inference does not supply. A deterministic result must reproduce on replay of the same transcript version and the same policy version; where it does not, it is a defect rather than a judgement.

**Model tier**: Model inference owns proposing that a specific item should be admitted to the pinned region, proposing that a specific item is safe to evict earlier than its recency position would dictate, delimiting the extent of a document or log span where structure alone does not determine it, and composing the purpose line that accompanies a write handle. These require open-vocabulary judgement that no deterministic rule covers. The model tier produces proposals and never produces authority.

**Hybrid tier**: Two handoffs are hybrid. Pin admission is model-proposed and deterministically adjudicated: the model may nominate an item, and software checks the nomination against the admission rule, the class cap, and the total ceiling before admitting it. Early eviction is model-proposed and deterministically executed: the model may mark a unit safe to release before its position requires it, and software still runs the externalization, the closure expansion, and the validity check exactly as it would for a position-triggered removal.

**Authority on disagreement**: The deterministic tier holds authority in every disagreement without exception. Two prohibitions are absolute and are not policy defaults. First, the model never evicts pinned content: a model assertion that a pinned item is no longer needed is a nomination for revocation routed to the pin's declared owner, and it never removes the item from the resident set. Second, eviction without a completed externalization is prohibited: where no durability receipt has returned for a candidate, the candidate is not evicted, the advance defers, and the residency copy is retained.

**Tier ownership by artifact**:

| Artifact | Owning tier | Authority where the tiers disagree |
| :-- | :-- | :-- |
| Pinned set membership, class caps, and the total ceiling | Deterministic | Deterministic; a model claim of importance is a nomination, never an admission |
| Eviction unit boundaries and dependency closure | Deterministic | Deterministic; a closure is expanded, never narrowed on model objection |
| Token counts, thresholds, and hysteresis arithmetic | Deterministic | Deterministic; a model estimate of remaining budget is advisory only |
| Externalization, durability receipt, and release | Deterministic | Deterministic; without a receipt the content stays resident |
| Eviction execution and reason codes | Deterministic | Deterministic; the eviction runs regardless of model objection |
| Provider-grammar validity and sequence linting | Deterministic | Deterministic; an invalid candidate window is never transmitted |
| Anchor emission and recovery-reference registration | Deterministic | Deterministic; an anchor never carries model-written content |
| Window size, soft threshold, and post-advance target | Deterministic | Deterministic; sizes come from measurement, not from preference |
| Nomination of an item for the pinned region | Model | Model proposes; the class cap and the admission rule still bind |
| Nomination of a unit as safe to evict early | Model | Model proposes; externalization and closure still run unchanged |
| Extent delimitation of an unstructured document or log span | Hybrid | Model proposes the extent; deterministic structure checks bind the boundary |
| Under-sizing diagnosis between repetition and mis-pinning | Hybrid | Model reads the repetition evidence; deterministic counters decide the verdict |

***

## II. Operational Framework: A Two-Region Resident Window With Whole-Unit Eviction

The framework assumes the umbrella selection ladder has chosen recency-ordered eviction over compression, retrieval, or isolation, and that eligible, typed context units are available. Phases 1 and 2 are configuration and run once per session or per policy version. Phases 3 and 4 form the advance loop and run whenever the soft threshold is crossed. Phases 5 and 6 run offline against measurement and correct the configuration that Phases 1 and 2 declared.

### Phase 1: Window Declaration and Unit Boundary Definition

**Objective**: Fix the window model, the eviction unit, and the advance thresholds before any content is admitted, so that every later removal is a whole unit executed against a declared arithmetic rather than a reaction to a provider rejection.

#### Step 1.1: Declare the Window Model and Compute the Resident Budget

**Required Actions**:

- Record five distinct capacities and never conflate them: the advertised context limit for the exact model and endpoint, the provider input ceiling after any provider-specific output reservation rule, the operational hard limit the application enforces below that ceiling, the soft advance threshold, and the post-advance target.
- Set the operational hard limit at or below 95 percent of the provider input ceiling, absorbing tokenizer drift, provider changes, and emergency control text.
- Subtract the output reserve, the reasoning reserve where the provider accounts for reasoning tokens, the next-tool reserve, the tokenizer-variance reserve, and the recovery reserve from the operational hard limit to obtain the resident budget; input, output, and reasoning tokens share one accounted total in current provider documentation [6][7].
- Set the output reserve to at least the 95th percentile observed response length for the task class, the next-tool reserve to the 95th percentile rendered tool observation for the loadout, and the variance reserve to at least 3 percent of the operational hard limit.
- Count with the exact serialized request against the target model, using the provider counting endpoint rather than a local character or token estimate, since roles, delimiters, tool schemas, files, and images all occupy the budget [8][9][10].
- Record the cached-token count separately and never subtract it from resident occupancy, because caching changes price and latency rather than what the model is shown.

**Required Outputs**:

- A window model record naming all five capacities with their numeric values, the model identifier, and the serializer version.
- A reserve ledger naming each of the five reserves and its numeric value.
- A resident budget figure and the counting method that produced it.

**Quality Checkpoints**:

- Every one of the five capacities carries a distinct numeric value; a configuration in which the advertised limit is used as the enforcement boundary fails validation.
- Every reserve carries a numeric value derived from an observed percentile or a stated default; an unbounded reserve dimension halts configuration.
- The resident budget was computed from a serialized count against the target model, not from a character estimate.

***

#### Step 1.2: Declare the Eviction Unit and Build the Dependency Closure

**Required Actions**:

- Declare one eviction unit per content class before any advance, choosing the largest unit needed for validity and the smallest unit that reclaims useful space.
- Prohibit token-count-driven boundaries from cutting inside a unit; a boundary that would fall mid-unit moves to the nearest unit edge in the direction that removes more, never in the direction that leaves a fragment.
- Build a dependency graph over units before eviction, binding every tool call to its results, every parallel call group to its complete result set, every request to the answer that interprets it where policy requires turn pairs, and every provider-required reasoning, signature, phase, or continuation item to the transaction it belongs to [11][12][13].
- Mark a unit evictable only where removing its full dependency closure leaves no retained item referring to it in a provider-required or task-critical way.
- Prohibit partial-message trimming by default, and permit it only for a single large self-contained text or document block handled by a structure-aware splitter with a declared overlap policy and a post-split linter [15].

**Required Outputs**:

- An eviction unit declaration table naming the unit for each content class present in the workload.
- A dependency graph over the canonical transcript with closure membership recorded per unit.
- An eligibility flag per unit with the reason code for any unit marked ineligible.

**Quality Checkpoints**:

- Every content class in the workload has exactly one declared eviction unit; an undeclared class halts the advance rather than defaulting to a token range.
- No candidate boundary falls inside a message, a tool call, a tool result, a reasoning item, a JSON object, a citation tuple, or a syntactic construct.
- Every tool call in the closure graph resolves to its complete result set, and every result resolves to its originating call.

***

#### Step 1.3: Declare the Advance Thresholds and the Hysteresis Gap

**Required Actions**:

- Set the soft advance threshold at 70 to 80 percent of the resident budget for ordinary dialogue and at 60 to 70 percent for tool-heavy trajectories, where one observation can exceed several turns.
- Set the post-advance target at least 15 percentage points below the soft threshold, so the hysteresis gap holds at least 3 expected turns of growth before the next advance.
- Set the minimum eviction batch to at least 5 percent of the resident budget, and defer any advance that cannot reach it unless the operational hard limit forces immediate action.
- Set the recent-suffix floor to at least 3 eviction units or the units required to interpret the current request, whichever is larger, and treat the floor as inviolable independent of the token arithmetic.
- Declare the predictive trigger as the sum of the current rendered count, the 90th percentile next-turn growth for the workload stratum, the output reserve, and the recovery reserve, and evaluate it before every model call and before appending any observation above 5 percent of the resident budget.
- Declare semantic advance opportunities in addition to the token trigger: task-phase completion, tool-transaction closure, and document-boundary arrival are clean advance points even below the soft threshold.
- Declare the reactive path as a bounded safety net: on a provider context-length rejection, record the exact error and both counts, never retry the identical request, recount with the provider counter and a raised variance reserve, advance once, and cap retries at 2 before escalating.

**Required Outputs**:

- A threshold record carrying the soft threshold, the post-advance target, the hysteresis gap in turns, the minimum eviction batch, and the recent-suffix floor.
- A predictive-trigger definition naming each term and the percentile that produced it.
- A reactive-path specification with a numeric retry cap and a named escalation target.

**Quality Checkpoints**:

- The hysteresis gap is at least 15 percentage points and covers at least 3 expected turns; a smaller gap fails validation because it produces an advance on nearly every turn.
- The recent-suffix floor is stated as a unit count, not as a token count, so it cannot be eroded by a large observation.
- The reactive path never permits blind character truncation and never permits an identical retry; either occurrence is a zero-tolerance defect.

***

### Phase 2: Pinned-Region Admission and Budget Bounding

**Objective**: Constitute the pinned region by declared rule, bound it by a hard cap, and establish the terminal path for the state in which pinned content alone approaches the resident budget.

#### Step 2.1: Apply the Pin Admission Rule

**Required Actions**:

- Admit an item to the pinned region only where its removal would make the next request unsafe, invalid, or unable to pursue the current objective; age, size, and asserted importance are not admission grounds.
- Admit every protected atom automatically and without nomination: the task objective, the success criteria, the standing and safety constraints, the current plan step, the latest value of every open variable, the unresolved error state, the outstanding approvals, and the side-effect ledger.
- Admit the current request and its acceptance criteria, the tool definitions reachable from the current plan step, and any provider-required continuation or opaque state item.
- Reject nominations for entire policy manuals, complete tool catalogues, historical examples, the full user-preference set, and the first conversational turn nominated on the ground that it is old and was important.
- Route every model nomination through the deterministic admission check, which evaluates the admission rule, the class cap, and the total ceiling before admitting, and record a reason code for each rejection.
- Re-evaluate every conditional pin at each semantic milestone, and revoke pins whose expiry condition has fired.

**Required Outputs**:

- A pinned-set record with one entry per pin.
- A rejection log carrying each declined nomination with its reason code.
- A revocation record naming each pin whose expiry condition fired and the milestone at which it fired.

**Quality Checkpoints**:

- Every protected atom named in the terminology appears in the pinned set; a missing protected atom halts assembly.
- No pin was admitted on a model assertion alone; every admission carries a satisfied admission rule.
- Every conditional pin was re-evaluated at the most recent semantic milestone.

***

#### Step 2.2: Bound the Pinned Region and Register Every Pin

**Required Actions**:

- Assign every pin a pin class, a pin reason, an owner, a creation time, an expiry condition, a rendered token cost, and a priority within its class.
- Enforce a per-class cap and a total ceiling of 40 percent of the resident budget, measured on the rendered serialization rather than on the raw text.
- Recompute the rendered pinned size after every pin admission, revocation, or content update, and recompute the sliding budget as the resident budget minus that figure.
- Fail configuration validation where the rendered pinned region exceeds its total ceiling, where any class exceeds its cap, or where the resulting sliding budget falls below the recent-suffix floor plus the next-tool reserve.
- Prohibit any resolution of a pin-cap breach that takes space from the output reserve, the recovery reserve, or the recent-suffix floor, and prohibit any silent unpinning of a policy, permission, objective, or unresolved-effect item.
- Emit the pinned-size figure, the sliding budget, and the per-class utilisation with every window event, so cap pressure is visible before it becomes a halt.

**Required Outputs**:

- A pin registry with all seven fields populated for every entry.
- A rendered pinned-size figure and a derived sliding-budget figure per advance.
- A per-class cap utilisation record expressed as a percentage of each cap.

**Quality Checkpoints**:

- Every pin carries an owner and an expiry condition; a pin without either is rejected at registration.
- The rendered pinned region is at or below 40 percent of the resident budget, and no class exceeds its own cap.
- The sliding budget is at least the recent-suffix floor plus the next-tool reserve; a smaller sliding budget fails validation rather than proceeding.

***

#### Step 2.3: Execute the Pin-Overflow Ladder and Its Terminal Halt

**Required Actions**:

- Enter the ladder whenever the rendered pinned region reaches 90 percent of its total ceiling, before the ceiling is breached rather than after.
- Run the rungs in order and stop at the first that brings the region below 80 percent of the ceiling: remove expired and duplicate pins; replace an eligible large pinned item with an approved reference or compacted form under the compression guidance; narrow tool definitions to the loadout authorised for the next action; split the task at a semantic boundary; route to an approved larger-context model.
- Record the rung reached, the tokens recovered, and the resulting sliding budget for every ladder execution.
- Halt the run where the ladder exhausts every rung and the protected set alone still exceeds the safe budget, and return a named terminal state rather than proceeding with a degraded window.
- Prohibit demotion of a safety rule, a permission, the current objective, or unresolved effect state by any relevance score, recency weight, or model judgement at any rung.
- Escalate to a human owner where the terminal halt fires twice within one session or three times within one workload stratum in a rolling 24 hours.

**Required Outputs**:

- A ladder execution record naming the rung reached, tokens recovered, and post-ladder sliding budget.
- A terminal-state record where the ladder exhausted, naming the protected set size and the deficit.
- An escalation notice where the repeat threshold fired.

**Quality Checkpoints**:

- The ladder was entered at 90 percent of the ceiling rather than after a breach.
- No rung demoted a safety, permission, objective, or unresolved-effect item; any such demotion is a zero-tolerance defect.
- Every terminal halt returned a named state and a numeric deficit rather than a partial window.

***

### Phase 3: Externalization Before Eviction

**Objective**: Move every unit that will leave the window into a durable store and obtain its recovery reference before the eviction boundary passes it, so that sliding is a move rather than a deletion.

#### Step 3.1: Assemble the Eviction Candidate Set at Whole-Unit Granularity

**Required Actions**:

- Compute the required reduction as the difference between the current rendered count and the post-advance target, never as the difference between the current count and the operational hard limit.
- Draw candidates only from the sliding region, in ascending recency order, and stop the ordered sweep at the recent-suffix floor.
- Expand every selected candidate to its full dependency closure before it enters the candidate set, and record the closure size alongside the candidate.
- Reject any candidate whose closure reaches into the pinned region, and record the rejection with a reason code rather than narrowing the closure.
- Admit an early-eviction nomination from the model tier only where the nominated unit is already in the sliding region, is not a protected atom, and passes the same closure expansion; a nomination never bypasses closure and never reaches pinned content.
- Verify that the candidate set reaches at least the minimum eviction batch, and defer the advance where it does not and the operational hard limit does not force action.
- Prohibit token-count-driven selection from stopping mid-unit: where the reduction target is met partway through a unit, the whole unit is either included or excluded, and the batch takes the arithmetic consequence.

**Required Outputs**:

- An ordered candidate set with one entry per whole eviction unit and its closure membership.
- A required-reduction figure and a projected-reclamation figure for the set.
- A rejection record for every candidate excluded by closure, floor, or ineligibility, each with a reason code.

**Quality Checkpoints**:

- Every candidate is a complete eviction unit together with its complete dependency closure; a partial unit in the candidate set is a zero-tolerance defect.
- No candidate originates in the pinned region, and no closure expansion crosses the region boundary.
- The candidate set either reaches the minimum eviction batch or the advance is recorded as deferred with its reason code.

***

#### Step 3.2: Externalize Every Candidate and Obtain the Durability Receipt

**Required Actions**:

- Submit every candidate unit to the durable store through the deterministic write path defined by the write-pattern guidance, carrying its stable identifier, its extent, its canonical serialization, and its provenance.
- Declare a named reader and a read occasion for each written span, as that guidance requires; for an evicted span the default reader is the same agent after the boundary and the default read occasion is a later reference to the removed material.
- Retain the residency copy in the window until the durability receipt returns for that unit, and treat the interval between the write and the receipt as the safe state rather than as a delay.
- Verify each receipt against the identifier and the committed version before permitting release, and verify read-back for any span carrying an unresolved obligation, an approval, or a side-effect record.
- Refuse the eviction of any unit whose receipt did not return within the configured write timeout of 5 seconds, and defer the advance rather than releasing on an unconfirmed write.
- Where the store is unavailable, halt the advance and hold the current valid resident set; continue only where policy has explicitly declared this content class as permitted irreversible loss, and record that declaration with the event.
- Prohibit any path in which the model tier declares content saved, authorises a release, or computes the saving that justifies its own eviction.

**Required Outputs**:

- One write handle per evicted span, carrying the stable identifier, purpose line, shape descriptor, size, and version.
- A durability receipt record per span with the committed version and store location.
- A deferral or halt record where any receipt failed to return, naming the affected units.

**Quality Checkpoints**:

- Every unit released from the window has a matching durability receipt; a release without a receipt is a zero-tolerance defect and halts the run.
- Every write handle resolves through the retrieval path declared for its store, verified for at least 1 handle per advance.
- No advance proceeded on an unconfirmed write except under an explicitly recorded irreversible-loss declaration.

***

#### Step 3.3: Emit the Boundary Anchor and Register the Recovery Reference

**Required Actions**:

- Emit one aggregate anchor per advance rather than one anchor per evicted unit, naming the removed span by immutable identifiers and by turn or time range, the unit types removed with counts, and the write handles that recover them.
- State the retrieval status explicitly as available, expired, denied, or intentionally disabled, and never imply retrieval where no tool can perform it.
- Prohibit any content claim inside an anchor: an anchor records that a span left and where it is, and never records what the span said, which is the compression guidance's work and carries its preservation manifest.
- Merge the new anchor into the existing anchor registry rather than appending, and cap the registry at 3 percent of the resident budget, compacting the oldest entries into a coarser range record when the cap is reached.
- Suppress the anchor where disclosure of the existence or topic of the removed content is not authorised for the current principal, and record the suppression with a reason code rather than emitting a partial anchor.
- Register every recovery reference in the retrieval index before the advance commits, so a post-boundary reference resolves on its first attempt.

**Required Outputs**:

- One aggregate boundary anchor per advance with span identifiers, type counts, handles, and retrieval status.
- An updated anchor registry within its cap, with a registry compaction record where registry compaction occurred, distinct from the window compaction named by the umbrella guidance.
- A retrieval index entry per recovery reference, confirmed present before commit.

**Quality Checkpoints**:

- Every anchor names at least 1 resolvable recovery reference or is explicitly marked unavailable; an anchor with a dangling reference fails validation.
- No anchor contains a summary, a paraphrase, or any assertion about the content of the removed span.
- The anchor registry is at or below 3 percent of the resident budget after the advance.

***

### Phase 4: Boundary Advance and Validity Enforcement

**Objective**: Move the eviction boundary only through a simulated, linted, coherence-checked candidate window committed atomically, so that no invalid or incoherent resident set is ever transmitted.

#### Step 4.1: Simulate the Advance and Run the Sequence-Validity Linter

**Required Actions**:

- Freeze the transcript head version and acquire an expected-version guard, so a concurrent append cannot race the advance.
- Simulate the removal against a copy of the resident set without mutating the canonical transcript, then serialize the simulated window exactly as it would be transmitted.
- Run the provider-specific validity linter over the serialized candidate, checking permitted roles and content-block types, allowed start and end conditions, system-message placement, alternation and coalescing behaviour, complete call-to-result pairing in both directions, complete parallel result sets, ordering of results after their calls, presence and integrity of required reasoning and continuation items, structural completeness of every content block, and the presence and untruncated state of the current request [11][12][13][14].
- Run the linter at 4 points and reject the request before transmission on any failure: on transcript ingestion, after closure construction, after each proposed removal, and after final serialization.
- Expand a failing candidate to its full dependency closure and re-simulate, or select the next valid batch, and record the failed proposal with its failed rule identifiers.
- Prohibit repair by fabrication: never synthesise a tool result, never invent an outcome for a pending call, and never reconstruct an opaque provider continuation item.
- Recount the serialized candidate with the provider counter after every mutation, and confirm the count is at or below the post-advance target before proceeding.

**Required Outputs**:

- A simulated candidate window with its exact serialized token count.
- A linter report naming every rule evaluated and its verdict.
- A failed-proposal record for each rejected candidate with its failed rule identifiers.

**Quality Checkpoints**:

- The candidate passes 100 percent of provider grammar rules; a candidate failing any rule is never committed and never transmitted.
- No repair action created content that the transcript did not contain.
- The recount was performed on the exact serialized payload after the final mutation, not before it.

***

#### Step 4.2: Run the Boundary Coherence Pass Over the Retained Suffix

**Required Actions**:

- Scan the retained suffix for unresolved pronouns, demonstratives, ellipsis, unnamed entities, and back-references whose antecedent falls behind the new boundary.
- Scan for active constraints, corrections, decisions, and open commitments whose only statement falls behind the new boundary, and treat any such finding as a pin-admission failure in Phase 2 rather than as an eviction problem.
- Scan for artifacts, citations, code symbols, identifiers, and tool outputs that retained units reference and that the boundary would remove without a resolvable handle.
- Promote only the minimum typed referent or pointer already approved under the selection guidance; never manufacture a referent and never write a substitute description of the removed content.
- Maintain a carryover record for any entity or structure opened before the boundary and not yet closed, carrying the identifier, type, canonical name, opening offset, unresolved attributes, and source pointer, and clear it when the structure closes.
- Where a referent cannot be resolved safely, extend the boundary backward by whole units, retrieve the source through its recovery reference, or request clarification; do not commit the advance with an unresolved referent.

**Required Outputs**:

- A coherence report naming every unresolved referent, constraint, and artifact dependency detected.
- A carryover record for every boundary-spanning entity or structure.
- A resolution record naming, for each detected issue, the action taken.

**Quality Checkpoints**:

- Zero active constraints, corrections, or open commitments have their only statement behind the boundary; any occurrence is a pin-admission defect and blocks the advance.
- Every detected unresolved referent was resolved by extension, retrieval, or clarification, never by generation.
- Every boundary-spanning structure carries a carryover record until it closes.

***

#### Step 4.3: Commit the Advance Atomically and Record the Window Event

**Required Actions**:

- Commit the new resident-set version in one atomic operation guarded by the expected transcript version, and abort and re-simulate on a version conflict rather than committing over a concurrent append.
- Leave the canonical transcript unmodified; an advance changes the resident projection only, and durable retention actions are governed separately by the lifecycle guidance.
- Emit exactly one window-advance event per commit, carrying the previous and new window versions, the resident range before and after, tokens before, after, and reclaimed, unit and transaction counts removed, retained first and last sequence identifiers, pinned size, sliding size, pass count, failed-proposal count, and the trigger class.
- Classify the trigger as predictive, semantic-boundary, reactive, or emergency, and report predictive and reactive advances separately in every downstream metric.
- Record cache-eligible tokens before and after, matched-prefix tokens, and the invalidation boundary, since a head advance rewrites the serialized prefix and can invalidate reuse at the layer above it [18][19][20].
- Keep telemetry metadata-only: log identifiers, counts, verdicts, and reason codes, and never log user text, tool payloads, secrets, or protected identifiers in ordinary traces.
- Bound the advance loop at 5 passes, 2 seconds of wall time, or the point at which no safe candidate remains, and escalate to the overflow path rather than looping further.

**Required Outputs**:

- A committed resident-set version with its version identifier and guard result.
- One window-advance event record with the full field set populated.
- A loop-termination record naming the terminating condition where the bound was reached.

**Quality Checkpoints**:

- The canonical transcript is byte-identical before and after the advance.
- Exactly 1 window-advance event exists per committed advance, with no field left unpopulated.
- No advance exceeded 5 passes or 2 seconds; a breach escalates to the overflow path rather than continuing.

***

### Phase 5: Window-Size Selection by Measured Task Completion

**Objective**: Fix the sliding budget at a size derived from measured task completion on the workload rather than from the model's advertised limit, so the window is sized to what the task needs rather than to what the interface accepts.

#### Step 5.1: Establish the Baseline and the Completion Metric

**Required Actions**:

- Declare a task-completion metric that is adjudicated rather than asserted: acceptance tests passed, deliverables meeting stated criteria, or an adjudicated correctness verdict, measured after at least 1 committed advance has occurred in the session.
- Prohibit occupancy, token savings, advance rate, and cache hit rate from serving as the selection objective; each is a cost measure and none of them is evidence that the work succeeded.
- Assemble a frozen evaluation corpus of at least 30 sessions per workload stratum, each running long enough to force at least 3 advances, and carrying controlled instances of early constraints, mid-session corrections, tool bursts, named entities, and back-references.
- Record the advertised context limit for the model in use, and record it as context only: it states what the interface accepts, not what the model uses reliably, and reported evaluations find degradation growing with input length within the advertised limit rather than at it [1][2][22].
- Establish the baseline configuration as a pinned prefix plus a recent suffix at the current sliding budget, and measure completion, cost, latency, eviction regret, and boundary retrieval rate against it.
- Stratify every measurement by task class, tool density, session length in advances, and model version, and report no rate without its numerator, denominator, sample count, and stratum.

**Required Outputs**:

- A task-completion metric definition with its adjudication procedure.
- A frozen evaluation corpus of at least 30 sessions per stratum with its generation record.
- A baseline measurement record covering completion, cost, latency, regret, and retrieval rate per stratum.

**Quality Checkpoints**:

- The completion metric is adjudicated against stated criteria; a metric that reports occupancy or token savings as success fails validation.
- Every corpus session forces at least 3 advances; sessions that never cross a boundary carry no information about window size.
- Every reported figure carries its numerator, denominator, sample count, and stratum.

***

#### Step 5.2: Sweep the Window Size and Locate the Completion Plateau

**Required Actions**:

- Sweep the sliding budget across at least 5 sizes spanning a factor of 4 from the smallest that satisfies the recent-suffix floor, holding the pinned region, the eviction unit, the eviction order, and the model version fixed.
- Vary exactly 1 configuration variable per sweep run, since coupled thresholds cannot be attributed without a designed experiment.
- Plot completion against sliding budget per stratum and locate the plateau: the smallest size beyond which completion improves by less than 2 percentage points per doubling of the budget.
- Record the cost, latency, and cache behaviour at each swept size, and compute cost per successful task rather than cost per call, since a smaller window that fails and retries is not cheaper.
- Reject any swept size at which a zero-tolerance failure occurs, regardless of its completion figure: loss of a protected atom, an accepted invalid sequence, a release without a receipt, or an unresolvable anchor disqualifies the size outright.
- Compare the plateau against the alternatives on the same corpus: full history within a larger tested window, recent suffix only, pinned prefix plus recent suffix, retrieval over evicted history, and verified compaction; adopt sliding only where it wins on cost per successful task at matched completion.

**Required Outputs**:

- A completion-versus-size curve per stratum with at least 5 measured points.
- A named plateau size per stratum with its completion, cost per successful task, and latency.
- A comparative record against at least 3 alternative configurations on the same corpus.

**Quality Checkpoints**:

- At least 5 sizes were measured per stratum and exactly 1 variable changed per run.
- The plateau is defined by the stated 2-percentage-point rule, not by inspection.
- No size carrying a zero-tolerance failure was advanced as a candidate.

***

#### Step 5.3: Fix the Operating Size Below the Plateau and Freeze the Regression Suite

**Required Actions**:

- Set the operating sliding budget at the plateau size, never above it, since additional resident tokens beyond the plateau add cost and measured degradation without adding completion [2].
- Derive the soft advance threshold and post-advance target from the operating size rather than from the advertised limit, preserving the hysteresis gap declared in Step 1.3.
- Record the operating configuration as a versioned policy carrying the sliding budget, thresholds, minimum batch, recent-suffix floor, pin caps, eviction unit set, and the corpus version that produced it.
- Freeze a regression suite drawn from the corpus, covering long-session replays, tool-loop trajectories, boundary probes, provider-conformance transcripts, and adversarial tool histories, and gate every future policy change on it.
- Canary the operating configuration on a narrow traffic cohort until it accumulates at least 100 boundary-crossing sessions, and promote only after 2 independent evaluation runs and the canary meet the predeclared gates.
- Schedule recalibration at every model version change, provider endpoint change, tokenizer change, and workload-mix shift above 20 percent, since each invalidates the corpus that produced the size.

**Required Outputs**:

- A versioned window policy record with every configured value and its corpus version.
- A frozen regression suite with its gate thresholds.
- A canary record with boundary-crossing session count and gate verdicts.

**Quality Checkpoints**:

- The operating sliding budget is at or below the measured plateau; a size chosen from the advertised limit fails review.
- The regression suite covers all 5 named case families; a missing family blocks promotion.
- Promotion followed 2 independent evaluation runs and a canary of at least 100 boundary-crossing sessions.

***

### Phase 6: Under-Sized Window Detection and Policy Correction

**Objective**: Detect at runtime that the sliding budget is too small for the work in progress, discriminate that condition from mis-pinning and from eviction loss, and correct the policy against measurement rather than against impression.

**Under-sizing signal table**: The four signals below are the runtime evidence that a window is too small. Each is computed deterministically from identifiers already recorded by Phase 4, and none requires a model judgement to fire.

| Signal | Deterministic computation | Default trigger | Immediate action |
| :-- | :-- | :-- | :-- |
| Repeated work | Tool calls whose argument hash matches a call already committed in the session, divided by tool calls | Above 10 percent over 20 calls | Raise sliding budget by 1 sweep step; open diagnosis |
| Re-asked questions | Clarification requests whose question identifier matches one already answered in the session | 2 or more per session | Restore the answered-question registry; open diagnosis |
| Boundary retrieval | Retrievals triggered by a reference to evicted content, divided by post-boundary turns | Above 20 percent | Widen the recent-suffix floor; open diagnosis |
| Decision contradiction | Adjudicated conflicts between a current action and a decision recorded behind the boundary | 1 or more per session | Halt and escalate; treat as a protected-atom failure |

#### Step 6.1: Instrument the Four Under-Sizing Signals

**Required Actions**:

- Maintain a session-scoped registry of committed tool-call argument hashes, answered-question identifiers, retrieved artifact identifiers, and recorded decisions, held in the durable store rather than in the window.
- Compute each of the four signals at every turn boundary from those registries, never from a model report of whether it has already done something.
- Compute eviction regret continuously as evicted units later retrieved through their recovery reference or adjudicated necessary, divided by evicted units, stratified by unit type and eviction position.
- Compute advance rate and mean eviction batch together, since a high advance rate with a small batch is thrashing rather than under-sizing and calls for a wider hysteresis gap rather than a larger budget.
- Emit each signal with its numerator, denominator, and window of computation, and alert on the first trigger rather than on a rolling average that hides a single severe session.
- Retain per-signal history across at least 200 sessions per stratum, so a trigger can be compared against the stratum's own base rate.

**Required Outputs**:

- Four instrumented signal streams with numerators, denominators, and trigger states.
- An eviction regret figure stratified by unit type and eviction position.
- A paired advance-rate and batch-size series per stratum.

**Quality Checkpoints**:

- Every signal is computed from durable registries; a signal derived from a model self-report fails validation.
- Every emitted rate carries its numerator, denominator, and computation window.
- The decision-contradiction signal alerts on its first occurrence and is never averaged away.

***

#### Step 6.2: Discriminate Under-Sizing From Mis-Pinning and From Eviction Loss

**Required Actions**:

- Test the mis-pinning hypothesis first: where the lost item is a protected atom, a standing constraint, an open commitment, or an unresolved effect, the defect is a Phase 2 admission failure and enlarging the window does not fix it.
- Test the eviction-loss hypothesis second: where the item was evicted with a valid receipt and a resolvable handle but was never retrieved, the defect is a retrieval or anchor defect and belongs to Phase 3, not to window size.
- Test the under-sizing hypothesis last: where the item was neither pinnable by rule nor usefully retrievable, and its absence causes measured repetition, the sliding budget is too small for the workload.
- Route the model tier only the discrimination reading, presenting the repetition evidence and the candidate hypotheses; the verdict is held by the deterministic counters, and a model opinion never overrides a protected-atom loss classification.
- Distinguish under-sizing from thrashing using the paired advance-rate and batch series, and from provider drift using the preflight estimate error distribution, before proposing any budget change.
- Record the discrimination verdict with its evidence identifiers, so a later correction can be attributed to the condition it was meant to fix.

**Required Outputs**:

- A discrimination verdict per triggered signal, naming one of mis-pinning, eviction loss, under-sizing, thrashing, or provider drift.
- An evidence record binding the verdict to the specific lost item and its window event.
- A correction proposal naming the phase that owns the fix.

**Quality Checkpoints**:

- Every triggered signal carries exactly 1 verdict and its evidence identifiers.
- No protected-atom loss was classified as under-sizing; that misclassification is a zero-tolerance diagnostic defect.
- Thrashing and provider drift were excluded by measurement before any budget change was proposed.

***

#### Step 6.3: Apply the Correction and Re-Measure Against the Frozen Baseline

**Required Actions**:

- Apply exactly 1 correction per cycle, drawn from the phase the verdict named: pin-class admission for mis-pinning, anchor or retrieval repair for eviction loss, sliding budget for under-sizing, hysteresis gap for thrashing, or reserve and counter version for provider drift.
- Bound a sliding-budget increase to 1 sweep step from Step 5.2 per cycle, and re-run the frozen regression suite before the change reaches any traffic.
- Escalate to the overflow path rather than to a further budget increase where the corrected budget would breach the resident budget: unload tools not required for the next action, replace large immutable observations with artifact handles, attempt compaction under the compression guidance, split the task at a semantic boundary, or route to an approved larger-context model [16][17].
- Stop sliding entirely and record the limitation where boundary retrieval remains above 20 percent after 2 correction cycles, since persistent rehydration indicates the representation or the task decomposition is wrong rather than the window size.
- Re-measure completion, cost per successful task, regret, and all 4 signals against the frozen baseline on matched traffic, and roll back any correction that improves a cost measure while degrading completion.
- Version every corrected policy and evaluate it on held-out sessions, so the measurement that motivated the change does not also validate it.

**Required Outputs**:

- A correction record naming the single change applied and the verdict it addressed.
- A post-correction measurement against the frozen baseline on matched traffic.
- A rollback or promotion decision with its gate verdicts.

**Quality Checkpoints**:

- Exactly 1 variable changed per correction cycle; a multi-variable change fails attribution and is rejected.
- Every correction was evaluated on held-out sessions, not on the sessions that motivated it.
- Any correction improving cost while degrading completion was rolled back; token compliance is never accepted as success.

***

## III. Implementation Guidance for AI Agents

AI agents operating a sliding window must follow systematic protocols ensuring that every removal is a whole unit, that every removal is externalized before it leaves, and that the pinned region is bounded rather than merely privileged. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Budget Agent**: Owns the five capacities, the reserve ledger, the resident budget, and the sliding budget. It performs every token count against the provider counter and holds the budget veto; a model estimate of remaining space is advisory only.
2. **Pin Registrar**: Owns the pinned set, the pin classes, the per-class caps, and the 40 percent total ceiling. It alone admits, revokes, and expires pins, and it runs the overflow ladder to its terminal halt. It never accepts a model nomination as an admission.
3. **Unit Builder**: Owns eviction unit boundaries and dependency closure construction over the canonical transcript. It emits whole units only and rejects any request for a sub-unit extent.
4. **Externalization Agent**: Owns the write path to the durable store, receipt verification, write-handle issuance, and release authorisation. It is the only component that may declare a unit safe to remove.
5. **Advance Executor**: Owns candidate ordering, simulation, linting, the coherence pass, atomic commit, and the window-advance event. It never transmits a candidate that failed a rule and never mutates the canonical transcript.
6. **Measurement Agent**: Owns the four under-sizing signals, eviction regret, the size sweep, the frozen regression suite, and the versioned policy record. It proposes configuration changes and never applies them mid-session.

**Prohibited Delegations**: The model tier never evicts pinned content, never authorises a release, never assigns a stable identifier, never declares a write durable, never narrows a dependency closure, and never computes the token saving that justifies its own eviction proposal. A deployment in which any of these reaches the model tier can lose a binding constraint silently, because the only component that knows whether the store accepted the write is the one that talked to the store.

**Workflow Execution Pattern**:

```
STATE: Boundary_Advance
INPUTS:
  1. Frozen transcript head version and expected-version guard
  2. Pinned set version and rendered pinned size from Phase 2
  3. Ordered candidate set with closures from Step 3.1
  4. Durability receipt set from Step 3.2
ACTIONS:
  1. Simulate removal on a copy; serialize exactly
  2. Run provider grammar linter over the serialized candidate
  3. Run boundary coherence pass over the retained suffix
  4. Recount with provider counter against post-advance target
  5. Emit aggregate anchor; register recovery references
VALIDATION:
  - partial_unit_in_candidate_set == FALSE
  - candidates_without_receipt == 0
  - pinned_region_touched == FALSE
  - linter_failed_rules == 0
  - unresolved_referent_count == 0
  - serialized_tokens <= post_advance_target
  - transcript_version == expected_version
TRANSITIONS:
  IF all_validations_pass THEN next_state = Atomic_Commit_And_Event
  IF candidates_without_receipt > 0 THEN next_state = Defer_Advance_Hold_Residency
  IF linter_failed_rules > 0 THEN next_state = Expand_Closure_And_Resimulate
  IF pass_count > 5 OR elapsed > 2s THEN next_state = Overflow_Escalation
  IF transcript_version != expected_version THEN next_state = Reacquire_Guard
```

**Two-Phase Action Pattern**: Emit the intended advance as a simulated candidate carrying its candidate set, projected reclamation, and anchor draft without committing it; validate it against the block above while the canonical transcript is untouched and every residency copy is still held; commit only after validation passes, recording the window-advance event in the same atomic operation.

**Approval Gate**: Human authorisation is required before any of the following, and agents halt at these gates rather than proceeding with a recorded warning: an eviction proceeding under an irreversible-loss declaration; a pin revocation affecting a safety, permission, objective, or unresolved-effect item; a sliding-budget increase above 1 sweep step in a single cycle; a second terminal halt of the pin-overflow ladder within one session; and any policy promotion whose canary accumulated fewer than 100 boundary-crossing sessions.

**Context Management Requirements**:

- Hold the canonical transcript, the pin registry, the anchor registry, the recovery index, and the signal registries in durable state, since the window is a transport and retains nothing after the call.
- Count the advance loop's own serialization and linting cost as overhead and report it against the reclaimed tokens, rather than treating window maintenance as free.
- Write a handoff record at every context boundary naming the window policy version, the pinned set, the anchor registry, the open carryover records, and the next decision, and require explicit acknowledgement by the receiver.
- Hold the serialized prefix byte-stable across advances that do not touch it, batch removals above the minimum eviction batch, and record cache-read and cache-write tokens per advance, since a head advance rewrites the prefix and can invalidate reuse at every layer after the change point [18][19][20].

### B. Quality Assurance Checkpoints

**Checkpoint 1: Window Model Integrity (After Phase 1)**

- **Automated Check**: All 5 capacities carry distinct numeric values; all 5 reserves are bounded; the resident budget derives from a serialized provider count; every content class has exactly 1 declared eviction unit; the hysteresis gap is at least 15 percentage points and 3 expected turns.
- **Agent Action on Pass**: Proceed to pinned-region constitution.
- **Agent Action on Failure**: Halt configuration; no content is admitted against an incomplete window model.
- **Human Review Trigger**: A content class whose eviction unit cannot be declared without permitting mid-item boundaries.

**Checkpoint 2: Pinned-Region Bound (After Phase 2)**

- **Automated Check**: Every protected atom is present; the rendered pinned region is at or below 40 percent of the resident budget; no class exceeds its cap; the sliding budget is at least the recent-suffix floor plus the next-tool reserve; every pin carries an owner and an expiry condition.
- **Agent Action on Pass**: Proceed to the advance loop.
- **Agent Action on Failure**: Run the pin-overflow ladder; where the ladder exhausts, return the terminal state with its numeric deficit.
- **Human Review Trigger**: A terminal halt of the ladder, or a nomination to revoke a safety, permission, objective, or unresolved-effect pin.

**Checkpoint 3: Externalization Completeness (After Phase 3)**

- **Automated Check**: Every candidate is a whole unit with its complete closure; candidates without a durability receipt equal 0; every anchor names at least 1 resolvable recovery reference; the anchor registry is at or below 3 percent of the resident budget.
- **Agent Action on Pass**: Proceed to simulation and validity enforcement.
- **Agent Action on Failure**: Defer the advance, hold every residency copy, and retry the write path once before escalating.
- **Human Review Trigger**: Any release proposed without a receipt, or any store outage lasting beyond 1 deferred advance.

**Checkpoint 4: Advance Validity (After Phase 4)**

- **Automated Check**: 100 percent of provider grammar rules pass; unresolved referent count equals 0; no active constraint has its only statement behind the boundary; the canonical transcript is byte-identical before and after; exactly 1 window-advance event exists.
- **Agent Action on Pass**: Transmit the request and record the outcome against the advance.
- **Agent Action on Failure**: Reject the candidate before transmission, expand the closure, and re-simulate; never transmit a candidate with a warning attached.
- **Human Review Trigger**: A grammar failure recurring after 2 closure expansions, or any detected loss of a protected atom.

**Checkpoint 5: Size Selection Evidence (After Phase 5)**

- **Automated Check**: At least 5 sizes measured per stratum with exactly 1 variable per run; the plateau satisfies the 2-percentage-point rule; the operating size is at or below the plateau; the regression suite covers all 5 case families; the canary carries at least 100 boundary-crossing sessions.
- **Agent Action on Pass**: Promote the versioned window policy.
- **Agent Action on Failure**: Withhold promotion and name the missing evidence; a configuration is never promoted on occupancy or cost figures alone.
- **Human Review Trigger**: A plateau that does not appear within the swept range, indicating the workload needs a different operation family.

**Checkpoint 6: Correction Attribution (After Phase 6)**

- **Automated Check**: Every triggered signal carries exactly 1 verdict with evidence identifiers; exactly 1 variable changed per correction cycle; the correction was evaluated on held-out sessions; no protected-atom loss was classified as under-sizing.
- **Agent Action on Pass**: Version the corrected policy and resume monitoring.
- **Agent Action on Failure**: Roll back the correction and re-open discrimination with the failed attribution recorded.
- **Human Review Trigger**: Boundary retrieval above 20 percent after 2 correction cycles, or any decision contradiction adjudicated against a recorded decision.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
WINDOW_POLICY_VERSION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Pinned-Region Saturation**

- **Symptoms**: The rendered pinned region approaches its ceiling; the sliding budget falls toward the recent-suffix floor; advances reclaim less than the minimum batch; the agent has instructions and state but no room to work.
- **Diagnostic Steps**: Recompute the rendered pinned size per class against its cap; list pins whose expiry condition has fired but which were not revoked; identify duplicate pins and pins admitted by nomination rather than by rule.
- **Resolution Protocol**: Option A, revoke expired and duplicate pins and recompute. Option B, replace an eligible large pinned item with a write handle or a compacted form under the compression guidance. Option C, narrow tool definitions to the authorised near-term loadout. Option D, split the task at a semantic boundary or route to an approved larger-context model.
- **Escalation Trigger**: The ladder reaches its terminal halt twice within one session, or three times within one workload stratum in a rolling 24 hours. This error is never resolved by taking space from the output reserve or the recent-suffix floor.

**Error Type 2: Mid-Item Truncation**

- **Symptoms**: A retained message ends abruptly; a tool result parses as valid but carries a partial payload; a fragment reads as a complete statement while omitting its qualifier, its negation, or its scope.
- **Diagnostic Steps**: Compare each retained unit's extent against its canonical extent in the transcript; verify structural completeness of every content block; confirm that the last committed boundary fell on a declared unit edge.
- **Resolution Protocol**: Option A, restore the last valid resident version and re-run the advance with the boundary snapped to the nearest unit edge. Option B, disable partial trimming for the affected content class and re-declare its eviction unit. Option C, where a large document block genuinely requires splitting, route it through a structure-aware splitter with a declared overlap policy and re-lint.
- **Escalation Trigger**: Any confirmed mid-item truncation halts the run and blocks the policy version; this error is never resolved by retry, because the fragment is indistinguishable from complete content on inspection.

**Error Type 3: Eviction Without Externalization**

- **Symptoms**: A recovery reference does not resolve; an anchor reports available while its handle returns nothing; a post-boundary retrieval fails on content the log records as evicted.
- **Diagnostic Steps**: Match every eviction event against its durability receipt by identifier and committed version; verify the retrieval index entry was registered before commit; check whether an irreversible-loss declaration was recorded for the content class.
- **Resolution Protocol**: Option A, retrieve from the canonical transcript, which the advance never mutated, and re-register the handle. Option B, repair the retrieval index and mark the affected anchors unavailable until re-verified. Option C, where the write genuinely failed and no declaration exists, halt the run, record the loss with its identifiers, and block the store configuration.
- **Escalation Trigger**: Any release confirmed to have occurred without a receipt escalates immediately to a human owner and blocks the policy version; the bounded retry limit is 1 write retry before deferral.

**Error Type 4: Advance Thrashing**

- **Symptoms**: Advance rate rises while mean eviction batch falls; cache hit rate degrades without a prefix change; per-turn latency grows with no growth in resident tokens; the same units are re-serialized on consecutive turns.
- **Diagnostic Steps**: Compare the advance rate against the batch series and against the hysteresis gap in turns; check whether the post-advance target sits within 15 percentage points of the soft threshold; verify that the minimum eviction batch is enforced rather than advisory.
- **Resolution Protocol**: Option A, widen the hysteresis gap by lowering the post-advance target. Option B, raise the minimum eviction batch and defer advances that cannot reach it. Option C, move advancement to semantic boundaries where task-phase closure supplies clean advance points.
- **Escalation Trigger**: More than 1 advance per 2 turns sustained over 20 turns, or a cache hit degradation above 20 percentage points against the matched baseline.

**Error Type 5: Under-Sizing Misdiagnosed as Model Failure**

- **Symptoms**: The agent repeats completed work, re-asks answered questions, or contradicts a recorded decision, and the incident is attributed to model capability rather than to window policy.
- **Diagnostic Steps**: Run the Step 6.2 discrimination in order, testing mis-pinning first, eviction loss second, and under-sizing last; confirm the lost item's classification from the durable registries rather than from a model report.
- **Resolution Protocol**: Option A, where the item is a protected atom, correct pin admission in Phase 2; enlarging the window does not fix an admission defect. Option B, where the item was evicted with a valid handle, repair anchors and retrieval. Option C, where neither holds, raise the sliding budget by exactly 1 sweep step and re-run the regression suite.
- **Escalation Trigger**: A protected-atom loss classified as under-sizing is a zero-tolerance diagnostic defect and halts correction; boundary retrieval remaining above 20 percent after 2 correction cycles escalates to a change of operation family rather than a further budget increase.

**Troubleshooting Decision Tree**:

```
WINDOW ADVANCE FAILS OR SESSION LOSES STATE
├─ CONFIGURATION FAULT
│   ├─ Pinned region at or above ceiling → Run overflow ladder → Terminal halt if exhausted
│   ├─ Sliding budget below floor plus tool reserve → HALT, return numeric deficit
│   └─ Content class without declared unit → HALT, declare unit before advancing
├─ REMOVAL FAULT
│   ├─ Candidate is a partial unit → Snap boundary to unit edge, re-simulate
│   ├─ Closure reaches pinned region → Reject candidate, record reason code
│   └─ Candidate lacks durability receipt → Defer advance, hold residency copy
├─ VALIDITY FAULT
│   ├─ Grammar rule failed → Expand closure, re-simulate (limit 2), else escalate
│   ├─ Unresolved referent detected → Extend backward, retrieve, or clarify
│   └─ Transcript version conflict → Reacquire guard, re-simulate
├─ RECOVERY FAULT
│   ├─ Handle does not resolve → Restore from canonical transcript, re-register
│   └─ Anchor claims content → Strip claim, re-emit as reference only
└─ SIZING FAULT
    ├─ Protected atom lost → Correct pin admission, NOT window size
    ├─ Evicted but never retrieved → Repair anchors and retrieval index
    ├─ Advance rate high, batch low → Widen hysteresis, raise minimum batch
    └─ Repetition persists after both → Raise budget 1 sweep step, re-run suite
```

### D. Performance Metrics and Continuous Learning

**Correctness Metrics**:

- **Protected-retention rate**: Protected atoms present and correct after an advance, divided by protected atoms required before it (target: 100 percent; any loss is a zero-tolerance event that blocks the policy version).
- **Whole-unit compliance**: Committed advances whose every removal was a complete unit with its complete closure, divided by committed advances (target: 100 percent; any partial removal halts the run).
- **Externalization completeness**: Evicted units carrying a matching durability receipt, divided by evicted units (target: 100 percent, excluding units under a recorded irreversible-loss declaration).
- **Validity-pass rate**: Committed candidate windows passing every grammar rule on the first proposal, divided by committed advances (target: at least 95 percent; a lower rate indicates a unit-builder regression).
- **Anchor resolvability**: Anchors whose recovery reference resolves on first attempt, divided by anchors invoked (target: at least 98 percent).
- **Referent-loss rate**: Post-boundary references that cannot be resolved correctly, divided by references whose antecedent crossed or approached the boundary (target: no more than 2 percent).

**Efficiency and Sizing Metrics**:

- **Window utilization**: Exact rendered input tokens divided by the resident budget immediately before the call, reported at p50, p95, and p99 by stratum (target: p95 at or below the soft advance threshold).
- **Advance rate and mean batch**: Committed advances per turn paired with tokens reclaimed per advance (target: no more than 1 advance per 3 turns with a batch at or above the minimum; the pair is reported together or not at all).
- **Hard-overflow rate**: Provider context-limit rejections divided by requests (target: 0; any occurrence indicates the predictive trigger or the variance reserve is wrong).
- **Eviction regret**: Evicted units later retrieved or adjudicated necessary, divided by evicted units, stratified by unit type and eviction position (target: no more than 10 percent; above 20 percent triggers a size review).
- **Boundary retrieval rate**: Retrievals caused by references to evicted content, divided by post-boundary turns (target: no more than 20 percent; a sustained higher rate indicates the operation family is wrong).
- **Cache hit degradation**: Baseline cache hit rate before a policy change minus the candidate rate on matched traffic (target: no more than 10 percentage points; above 20 blocks promotion).
- **Cost per successful task**: Total cost including counting, serialization, linting, storage, index, cache write and miss, retrieval, and added latency, divided by adjudicated successes (target: below the matched full-history and compaction baselines at equal completion).

**Log-Pattern Failure Detection**: Rising advance count with stable input growth indicates threshold or counting drift. Stable advance rate with falling cache hits indicates serialization instability or a shrinking batch. Rising unmatched-call proposals indicates a unit-builder regression. Rising referent failures with stable candidate ordering indicates a boundary coherence failure. Repeated tool calls with matching argument hashes indicate an under-sized sliding budget or a lost action ledger. Growing anchor registry with falling anchor resolvability indicates a retrieval index that is not keeping pace with eviction.

**Learning and Adaptation Mechanisms**:

- **Sweep-derived sizing**: Every operating sliding budget traces to a completion plateau measured on a versioned corpus, and no size is carried forward across a model version change without re-measurement.
- **Regret-driven eviction order**: Unit types with regret above 20 percent are moved later in the eviction order or promoted to a conditional pin class with an expiry, and the change is attributed in the policy version record.
- **Signal base rates**: Each under-sizing signal is compared against its own stratum base rate over at least 200 sessions, so a trigger reflects a change rather than a workload property.
- **Threshold recalibration**: Every numeric bound stated in this guide is a deployment default and is recomputed per task class against observed outcomes, with the recomputation recorded alongside the value it replaced.

**Human-in-the-Loop Boundaries**: Revocation of a safety, permission, objective, or unresolved-effect pin; approval of an irreversible-loss declaration for any content class; promotion of a window policy whose canary carries fewer than 100 boundary-crossing sessions; and acceptance of a residual limitation after a terminal halt are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the bounding of an ordered resident set rather than the content of any particular sequence. Its phases hold wherever content arrives in order, arrives faster than a budget can hold it, and carries obligations stated earlier than the work in progress.

### 4.1 Cross-Domain Application Patterns

**Customer-facing conversational service**: The pinned region carries the service policy, the entitlement scope of the authenticated principal, the open case record, and any commitment already made to the customer. The sliding region carries dialogue turns, evicted in turn pairs so a question never loses the answer that interprets it. The characteristic failure is a promise made in turn 4 and contradicted in turn 40, which the decision-contradiction signal catches on its first occurrence. Anchors are emitted because the customer may refer back, and their retrieval status is stated honestly rather than implied.

**Tool-using engineering agent**: Trajectories grow faster than dialogue because schemas, calls, results, and continuation items accumulate together, and one observation can exceed several turns. The eviction unit is the whole tool transaction, and the pinned region carries the objective, the plan step, the open effect ledger, and the loadout reachable from that step. Large completed observations are externalized to artifact handles while the record that the call occurred is retained, so the agent does not repeat a side-effecting action whose result it can no longer see [17].

**Regulated case review**: Verbatim history is often the deliverable, and the correct verdict is frequently that no window should slide at all. Where the review must compare the complete record in one pass, sliding is prohibited and the work is split, routed to a larger tested window, or restructured into structured state. Where sliding is permitted, every eviction carries a receipt, every anchor is retained as evidence that a span left, and the irreversible-loss declaration is never available.

**Long-document and log analysis**: Windows are structure-aware rather than token-aware: a section, a paragraph, a page, a complete log record, a transaction group, or a stack trace is the unit. Width and stride are chosen separately, with overlap sized only to preserve facts that cross boundaries. A carryover record holds entities opened in one window and closed in another, and a table is never separated from its headers, a clause from its controlling definitions, or an exception from its stack trace.

**Operations and incident response**: Event feeds arrive continuously and the recent suffix genuinely dominates, but the incident's declared severity, the change freeze in force, and the actions already taken are the oldest content in the session and the most consequential. The pinned region carries them, the sliding region carries the event stream, and the recent-suffix floor is set from the observation cadence rather than from a token figure so a burst cannot erode it.

### 4.2 Scale, Risk, and Latency Adaptation

- **Short reversible sessions**: Where the session fits within the resident budget with margin, no window slides. Sliding is an operation selected under pressure, and running it where no pressure exists adds cost, invalidates caches, and creates recovery paths nothing will use.
- **High-risk or irreversible work**: Retain every phase, prohibit the irreversible-loss declaration entirely, raise the anchor resolvability target to 100 percent with pre-commit verification, and bind the approval gate before any pin revocation. Abstention and escalation are preferred over an advance that cannot be recovered.
- **Strict latency budgets**: Advance less often with larger batches rather than removing the linter or the coherence pass, since removing validation removes the guarantee while raising the batch merely changes its frequency. Where latency forbids provider counting on every turn, count locally away from the threshold and provider-count within 10 percentage points of it.
- **Long-horizon autonomous runs**: Persist the pin registry, anchor registry, carryover records, and signal registries outside the window, write a handoff record at every boundary, and re-verify the protected set after every reconstruction so a loss is detected at the boundary that caused it rather than several boundaries later [4].
- **Multi-agent deployments**: Give each agent its own window policy version and its own pinned region, and never share a sliding region across trust domains. Where a parent delegates to a child, the child receives a constructed inbound context under the isolation guidance rather than a slice of the parent's transcript.

***

## V. Limitations and Considerations

**Recency is a weak proxy for value, and the pinned region only bounds the damage**: The sliding region still evicts by position, and position correlates with value imperfectly. A constraint stated mid-session, a correction issued in passing, and a decision recorded without ceremony can all fall behind the boundary while remaining binding. The mitigation is the admission rule in Step 2.1, which admits protected atoms automatically rather than by nomination, together with the boundary coherence pass in Step 4.2, which blocks an advance that would leave an active constraint with no resident statement.

**The pinned region can consume the window it was meant to protect**: Every exemption competes with the work. A deployment that responds to each incident by pinning one more item arrives at a window holding instructions and state with no room to act, which is the declared failure state of this pattern. The mitigation is the 40 percent ceiling, the per-class caps, the mandatory expiry condition on every pin, and the overflow ladder in Step 2.3 that terminates in a halt rather than in a silent unpinning.

**Externalization guarantees recoverability, not recall**: A unit written to a durable store with a resolvable handle is recoverable by a retrieval the agent must decide to perform. Where the agent does not recognise that it needs the removed content, the handle is never invoked and the outcome is identical to loss. The mitigation is the anchor in Step 3.3, which makes the removal visible in the resident set, and the boundary retrieval and repetition signals in Phase 6, which measure how often recognition failed.

**Every threshold stated here is a deployment default**: The 40 percent pin ceiling, the 70 to 80 percent soft threshold, the 15-percentage-point hysteresis gap, the 5 percent minimum batch, the 3-unit recent-suffix floor, the 20 percent boundary retrieval trigger, and the 10 percent regret target were chosen to be operable on first deployment. None is derived from a universal property of language models or of agent workloads. The mitigation is the recalibration obligation in Section III.D and the measured plateau in Phase 5, which oblige each deployment to replace the defaults with values its own corpus produced.

**Window-size measurement is expensive and its corpus expires**: A sweep across 5 sizes and 30 sessions per stratum is a substantial evaluation cost, and every model version change, endpoint change, tokenizer change, or workload shift invalidates the corpus that produced the result. Deployments under schedule pressure therefore tend to inherit a size no longer supported by evidence. The mitigation is the versioned policy record binding each size to the corpus version that produced it, and the scheduled recalibration triggers in Step 5.3 that mark an inherited size as unsupported rather than as current.

**Advertised capacity remains a poor guide and the measured alternative is workload-specific**: Reported evaluations find that content positioned near the beginning or end of a long input is used more reliably than content in the middle, and that degradation grows with input length within advertised limits [1][2][22]. Those findings vary by model, task, distractor structure, and content type, so no single effective-length figure transfers across deployments. The mitigation is to treat the advertised limit as an interface fact only and to derive the operating size from the deployment's own completion plateau.

**Sliding is the wrong operation for several common workloads**: Verbatim full-history comparison, regulatory review, forensic reconstruction, and audit evidence require the complete record in one pass, and a window that has evicted anything cannot supply it. Persistent boundary retrieval indicates the same conclusion by measurement. The mitigation is the prohibition in Section IV for regulated review, the 20 percent boundary retrieval trigger that escalates to a change of operation family after 2 correction cycles, and the umbrella selection ladder that owns the choice among writing, selecting, compressing, and isolating.

**Model-internal cache behaviour is neither observable nor controllable here**: The serving-side key-value cache and the attention computation that produces position effects sit below the agent layer, and their agent-layer surrogates in this guide are approximations rather than equivalents [5]. A deployment that attributes a windowing failure to cache internals will not find the defect, because the defect is nearly always in unit boundaries, pin admission, or externalization. The mitigation is the referral in Section 1.3 and the discrimination order in Step 6.2, which exhausts the agent-layer hypotheses before any internal one is entertained.

**Structural conformance is not task correctness**: An advance can satisfy every checkpoint here and still leave a window that answers the wrong question, because the framework governs what remains resident rather than what the resident content is for. No checkpoint substitutes for adjudicated task completion, which is why Phase 5 makes completion the selection objective and prohibits occupancy and token savings from standing in for it.

***

## VI. Conclusion and Summary

A sliding window is a bounding mechanism, not a memory strategy. Its value comes from a small number of explicit decisions made before any content is removed: which units are exempt from position-based eviction and by what rule, how large that exemption may grow before the configuration fails, what constitutes a whole unit, where the removed content goes before it leaves, and how large the sliding region needs to be for the work actually being done. A system that makes those decisions explicitly can be measured and corrected. A system that keeps the last N units and hopes will drop its own instructions and have no record that it did.

A team introducing this pattern should instrument before it evicts. Establish the canonical transcript with stable identifiers, declare the eviction unit for every content class in the workload, and constitute the pinned region from the protected atoms rather than from a list of items that once seemed important. Add externalization with receipts before adding any eviction at all, so the first removal is already recoverable. Only then configure thresholds, and only after measurement fix the size. The four under-sizing signals cost little to compute and are the difference between a window policy that improves and one that accumulates incidents.

**Key Success Factors**:

- **Two regions with different rules**: The pinned region is a categorical exemption admitted by rule and bounded by a hard cap; the sliding region advances by recency; nothing crosses from one to the other on a score.
- **Whole units only**: Every removal is a complete eviction unit with its complete dependency closure, and a boundary that would fall mid-item moves to a unit edge rather than leaving a fragment that reads as complete.
- **Externalization before eviction**: No unit leaves the window without a durability receipt and a registered recovery reference, and no model component may declare content saved or authorise its release.
- **Bounded exemption with a terminal path**: The pinned region carries per-class caps, a total ceiling, and an overflow ladder that ends in a named halt rather than in a silent demotion of a safety rule, a permission, or an objective.
- **Size from measurement**: The operating sliding budget is the measured completion plateau on the deployment's own corpus, never the model's advertised limit and never a fraction of it chosen by convention.
- **Under-sizing is detected, not inferred**: Repeated work, re-asked questions, boundary retrieval, and decision contradiction are computed from durable registries, discriminated against mis-pinning and eviction loss, and corrected one variable at a time.

By following this guide, AI agents can hold an unbounded stream of work inside a bounded window while retaining the obligations that were stated first, and can show, for any content no longer resident, exactly where it went and how to get it back.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Two entries, marked as verified, were retrieved during this conversion and are not present in the prose source.

**Corpus pointers**:

- `Sliding Window Context Management: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the five-capacity window model, the reserve arithmetic, the pinned and sliding region separation, the pin class fields and overflow ladder, the atomic eviction unit and dependency closure rules, the provider sequence-validity checks, the predictive and reactive advance triggers with hysteresis, the eviction-until-under-budget loop, the anchor and boundary coherence procedure, the overflow escalation ladder, the non-conversation window treatments, the metric definitions, the failure-mode inventory, and the production readiness criteria. It carries inline citations to provider documentation and to research on long-context behaviour; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the category umbrella. Owns the partitioned context budget, the four-family selection ladder, and the protected atom, admission gate, trust class, and reason code definitions adopted unchanged here. This guide assumes the ladder has already selected recency-ordered eviction.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — owns the externalization contract adopted in Phase 3, including the write handle, stable identifier, durability receipt, release, and residency copy semantics used here without modification.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — owns lossy reduction under a preservation manifest, which is the escalation target in Step 6.3 and the pin-overflow ladder, never a step inside an advance.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — owns candidate scoring and admission, which supply the eligibility and ordering inputs consumed by Step 3.1 rather than reimplemented in it.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — owns state lifetime, retention, and the durable disposition of evicted content after this guide's write path terminates.
- `advanced_task_guides/context-management/guide_ContextEditingAndToolResultClearing.md` — companion guidance on provider-native context editing and tool-result clearing, applicable wherever the provider rather than the application performs the removal.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — companion guidance on distraction, contradiction, and staleness detection, applicable to the coherence pass in Step 4.2 and the signal discrimination in Step 6.2.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — owns cross-agent and cross-trust-domain boundaries, applicable to the multi-agent adaptation in Section 4.2.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — source of the working-memory framing and the protected atom membership list that the umbrella guidance adopts and this guide inherits.

**External references**: The numbering below is the numbering used by the inline markers in Sections I through V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Long-context behaviour and position effects*

1. Liu and colleagues, *Lost in the Middle* — https://arxiv.org/abs/2307.03172
2. Chroma, *Context Rot* — https://www.trychroma.com/research/context-rot
22. Google, *Gemini long-context guide* — https://ai.google.dev/gemini-api/docs/long-context

*Constraint retention and structured eviction in long-horizon agents*

3. Chen, *Governance Decay: How Context Compaction Silently Erases Safety Constraints in Long-Horizon LLM Agents* — https://arxiv.org/abs/2606.22528 (retrieved and verified during this conversion)
4. Semenov and Dorofeev, *Beyond Compaction: Structured Context Eviction for Long-Horizon Agents* — https://arxiv.org/abs/2606.11213 (retrieved and verified during this conversion)

*Model-internal mechanism, cited as background only*

5. *StreamingLLM paper* — https://arxiv.org/abs/2309.17453

*Context accounting and token counting*

6. Anthropic, *context-window documentation* — https://docs.anthropic.com/en/docs/build-with-claude/context-windows
7. OpenAI, *conversation-state documentation* — https://developers.openai.com/api/docs/guides/conversation-state
8. Anthropic, *Token Count API* — https://platform.claude.com/docs/en/api/messages/count_tokens
9. OpenAI, *token-counting guide* — https://developers.openai.com/api/docs/guides/token-counting
10. Google, *Gemini token guide* — https://ai.google.dev/gemini-api/docs/tokens

*Transcript grammar, tool transactions, and trimming*

11. Anthropic, *tool-use documentation* — https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
12. OpenAI, *function-calling guide* — https://developers.openai.com/api/docs/guides/function-calling
13. Google, *Gemini function-calling guide* — https://ai.google.dev/gemini-api/docs/function-calling
14. LangGraph, *invalid chat history* — https://langchain-ai.github.io/langgraph/troubleshooting/errors/INVALID_CHAT_HISTORY/
15. LangChain, *trim_messages* — https://python.langchain.com/v0.2/api_reference/core/messages/langchain_core.messages.utils.trim_messages.html

*Provider-side reduction and session management*

16. OpenAI, *compaction guide* — https://developers.openai.com/api/docs/guides/compaction
17. Anthropic, *context-editing documentation* — https://platform.claude.com/docs/en/build-with-claude/context-editing
21. Google, *Gemini Live session management* — https://ai.google.dev/gemini-api/docs/live-api/session-management

*Prompt-prefix caching*

18. OpenAI, *prompt-caching guide* — https://developers.openai.com/api/docs/guides/prompt-caching
19. Anthropic, *prompt-caching documentation* — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching?c=acatex
20. Google, *Gemini context-caching documentation* — https://ai.google.dev/gemini-api/docs/caching

*External memory as an alternative to a larger window*

23. *Mem0 paper* — https://arxiv.org/abs/2504.19413
