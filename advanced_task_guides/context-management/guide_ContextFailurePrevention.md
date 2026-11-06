# Context Failure Prevention

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context failure prevention constitutes the task family of detecting, containing, and remedying the failures caused by what occupies a model's context window, before those failures reach an output or an action. Its organising premise is that "the context is too long" is not one failure but five, and that treating it as one produces a single remedy, summarisation, which repairs only the first of them and actively destroys the evidence needed to detect three others. This guide provides AI agents with a structured protocol that assigns each failure mode an observable detection signal computable from assembly records and logs without a human reading the transcript, a numeric trigger, a remedy distinct from summarisation, and a verification that the remedy resolved the failure rather than relocating it. It covers instrumentation of the assembled context, per-mode detection, mode-specific remediation, containment of poisoning and injection at the window boundary, and correction of the admission policy that produced the failure. It partitions the work across a deterministic tier owning every detection signal, threshold evaluation, supersession record, utilization measurement, and isolation control, and a model tier owning semantic adjudication and eviction proposals, with the rule that a model opinion never overrides a fired detector.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Context failure**: An observable degradation in output or action quality whose cause is the composition of the assembled context rather than the model, the task specification, or the tooling. A failure is attributed to context only when a named detection signal fired on the assembled context for the affected call.

**Failure mode**: One of five mutually exclusive causal classes into which a context failure is classified before any remedy is selected. The five modes are overflow, distraction, contradiction, staleness, and poisoning. The first four are adopted unchanged from the umbrella context-management guidance; poisoning is the extension this guide adds, because content that carries instructions rather than merely wrong claims requires containment rather than correction.

**Detection signal**: A quantity computed by the deterministic tier from the assembly record, the citation binding, and the event log, whose value determines whether a failure mode is present. A detection signal must be computable without any human reading the transcript and without any model asked for an opinion; a quantity that requires either is a diagnostic aid, not a detection signal.

**Numeric trigger**: The declared threshold at which a detection signal is treated as a fired detector, together with the consequence that firing produces. Every signal carries exactly one trigger and one consequence; a signal without a consequence is instrumentation, not detection.

**Assembly record**: The per-call artifact emitted by the assembler naming every unit admitted to the window, in serialization order, with its unit identifier, partition, source identifier and version, trust class, observation and expiry timestamps, scope tuple, token count, position index, and the admission rule that admitted it. Detection is computed against this record, never against the rendered prompt text.

**Utilization**: The proportion of admitted units that a supported output claim, a tool call, or a state update actually cited or consumed. Utilization is measured per partition, per admission rule, and per position band, and it is the only evidence that a unit admitted to the window was used by the model that received it. The definition is adopted from the umbrella guidance.

**Coverage**: The proportion of the task's declared evidence requirements for which at least one eligible unit was admitted. Coverage measures whether the right material was present; utilization measures whether it was used. High coverage with low utilization is the signature of distraction, and the two quantities must never be collapsed into one retrieval score.

**Overflow**: The failure mode in which the window cannot hold what the task needs. Detected by budget arithmetic before the call, never by a provider error after it.

**Distraction**: The failure mode in which admitted but irrelevant content displaces attention from relevant content, so the model uses the wrong material or none of it while the correct material is present. Its attributable subset, in which specific superfluous units or tool schemas can be named as the cause by removal, is diagnosed by ablation rather than treated as a separate mode.

**Contradiction**: The failure mode in which the window holds mutually inconsistent content, both current and authoritative, and the model selects between them arbitrarily and without disclosure.

**Staleness**: The failure mode in which superseded content remains present and is treated as current, so an outdated value drives a decision that a fresh value would have changed.

**Poisoning**: The failure mode in which content admitted to the window carries instructions, or carries a false claim that is then treated as evidence, and thereby acquires an authority its trust class does not grant. Injection is poisoning of adversarial origin; a model-generated inference retrieved back as evidence is poisoning of accidental origin. Both are contained by the same boundary, because the containment does not depend on knowing which occurred.

**Injection**: The delivery of instruction-shaped text into the window through a data-bearing path such as a retrieved document, a tool result, a filename, a code comment, a message body, or a sub-agent response. Direct injection arrives in the principal's own turn; indirect injection arrives inside content the agent fetched on the principal's behalf.

**Scope tuple**: The qualifier set that determines whether two units about the same subject can both be true: entity identifier, predicate, valid-time interval, transaction time, tenant, jurisdiction, unit of measure, and version. Contradiction is defined over scope tuples, not over surface text, because two records that are consistent in a store can contradict once both sit in one window with their scope qualifiers dropped.

**Scope-qualifier retention**: The deterministic check confirming that every scope qualifier present on a unit in its durable store survives into the unit's serialized form. A qualifier dropped at serialization converts a consistent pair of records into a contradictory pair inside the window, and this is the most common origin of in-window contradiction that store-level validation cannot see.

**Supersession ledger**: The per-call record binding every admitted unit to the current canonical version of its source, naming whether the admitted version is current, superseded, or past expiry. Staleness detection is a lookup against this ledger, not a judgement about whether a value looks old.

**Contradiction index**: The candidate-pair structure built over admitted units, keyed on shared entity and predicate, that bounds contradiction detection to pairs that could conflict rather than to all pairs. It exists because exhaustive pairwise comparison is quadratic in admitted units and produces false positives that dominate true ones.

**Trust class**: The provenance-derived label attached to every unit naming the authority of its source, assigned deterministically from the source class and capture channel and never from the content itself. Trust class determines which partition a unit may enter and whether it may instruct. The definition is adopted from the sibling memory-management guidance.

**Isolation mechanism**: The named, contractual arrangement that keeps admitted content in a data position: a fixed delimiter convention, a distinct non-system message role, a standing instruction in the trusted prefix declaring that delimited content is evidence carrying no authority, and enforcement of every consequential effect in the tool-authorization layer rather than in prompt text. The term and its components are adopted from the sibling memory-management guidance.

**Delayed-execution trust boundary**: The security boundary created by persistence, in which external text influences a write at one time and is read back as trusted context at a later time. Session-scoped injection controls do not contain it. This guide owns the window side of that boundary; the memory-management category owns the store side.

**Quarantine**: The state of a unit that is retained and auditable but withheld from admission until an independent validation completes. Quarantine preserves the evidence a later investigation needs, which deletion destroys.

**Remedy relocation**: The outcome in which a remedy clears its triggering signal without changing the failing output, because the failure was moved into a region the signal does not observe. Compaction that folds a stale value into a summary relocates staleness into a form no freshness check can detect. Verification exists to distinguish resolution from relocation.

**Detection budget**: The declared per-call allowance of latency, tokens, and evaluator calls that detection may consume, partitioned across the five modes. It exists because detection is not free and because over-validation introduces its own failures: an adjudicating model can hallucinate, and a large validation prompt suffers the same degradation it was built to detect.

**Prevention-cheap mode**: A failure mode whose occurrence is eliminated by an admission-time rule at lower cost than detecting and repairing it after assembly. Overflow, staleness, and poisoning are prevention-cheap. Distraction and contradiction are not, and the reason is stated in Section 1.3.

**Reason code**: A normalised categorical label recorded with every detection, remedy, exclusion, and quarantine event, drawn from a closed vocabulary so that failure frequency by mode and by admission rule is analysable without reading prose logs.

### 1.2 The Five Modes and the Four Things Each One Requires

The umbrella context-management guidance names four failure modes and owns the selection ladder that responds to budget pressure. This guide owns detection and prevention in depth, and it adds one mode: poisoning, which the four do not cover, because poisoning is not a property of how much content is present or how current it is but of what authority the content acquires once present.

The contribution of this guide is that each mode is specified by four things rather than by a description. A mode without an observable signal cannot be detected by an agent. A signal without a numeric trigger produces a judgement call at every turn. A trigger without a distinct remedy collapses into the general remedy, which is summarisation, and summarisation repairs only overflow. A remedy without a verification cannot be distinguished from relocation of the failure into an unobserved region.

**Per-mode detection and remediation contract**:

| Failure mode | Detection signal computable without reading the transcript | Numeric trigger | Distinct remedy | Verification that the remedy resolved rather than relocated |
| :-- | :-- | :-- | :-- | :-- |
| Overflow | Projected serialized token count per partition and in total, from the assembly record under the target tokenizer | Projected total exceeds 100 percent of the input budget, or any partition exceeds 100 percent of its maximum after its eviction order is exhausted | Enter the umbrella selection ladder at its least costly rung: externalize, then narrow selection, then compress, then isolate | Recomputed projection is at or below 100 percent, every protected atom is still present, and 0 units left the working set without a recorded reason code |
| Distraction | Utilization of admitted units, computed from bound citation identifiers, reported per partition, per admission rule, and per position band | Utilization below 40 percent while coverage exceeds 80 percent, or utilization falling 15 or more percentage points over a 20-turn rolling window while coverage moves less than 5 points | Reduce the admitted unit count, raise the admission threshold, narrow tool definitions to those reachable from the current plan step, and reposition the required unit out of the middle band | Utilization returns above 40 percent and the failed step's output changes in the predicted direction; utilization rising with the output unchanged is relocation and the diagnosis is withdrawn |
| Contradiction | Candidate pairs in the contradiction index whose scope tuples intersect and whose current authoritative values differ, plus the scope-qualifier retention check over every admitted unit | 1 or more intersecting pairs among unexpired authoritative units, or 1 or more units whose serialized form dropped a scope qualifier present in the stored form | Restore the dropped qualifier, surface both units with their authority ranks, apply the declared precedence policy, and escalate where precedence does not resolve | 0 unresolved pairs remain, the resolution is disclosed in the output rather than made silently, and the re-run selects the value the precedence policy names |
| Staleness | Supersession ledger lookup binding each admitted unit to the current canonical version and expiry of its source | 1 or more admitted units past expiry, 1 or more whose admitted source version differs from the current canonical version, or any superseded version present alongside its successor | Evict the superseded version, re-select the current version, and invalidate every cache entry and derived summary keyed to the old version | 0 units past expiry, every cited source version equals the canonical version, and a negative read confirms the old version is no longer servable |
| Poisoning | Instruction-shape verdict recorded as a field on every admitted unit, plus provenance-path termination analysis over every decisive output claim | 1 or more admitted units carrying an imperative addressed to the assistant, a role declaration, a forged delimiter, or a policy assertion; or 1 or more decisive claims whose provenance terminates in the agent's own prior inference with fewer than 2 independent corroborating source identifiers | Contain rather than correct: hold the unit in a data position, quarantine it and its derivatives, revoke the source's admission grant, and re-run the affected calls against the remaining corpus | The same injected unit produces 0 unauthorized effects when the call is replayed with the instruction-shape detector disabled, which is the only evidence that containment rather than detection held |

Two categories in the prose literature are not separate modes here and must not be treated as such. Content that is superfluous and attributable to named units is the attributable subset of distraction, diagnosed by removal ablation rather than by its own signal. Degraded use of information because of where it sits in the sequence is observed through position-conditioned utilization, which is a stratification of the distraction signal rather than a sixth mode. Collapsing either into a new mode would produce a remedy that duplicates the distraction remedy while carrying its own threshold, which is how a taxonomy stops discriminating.

### 1.3 Prevention Versus Recovery and the Allocation of Detection Budget

Detection is not free, and spending it uniformly across five modes wastes most of it. Three of the five modes are eliminated more cheaply by an admission-time rule than by post-assembly detection and repair, and two cannot be eliminated at admission at all, because their defining property does not exist until the content is assembled or until the model has responded.

**Prevention-cheap modes**: Overflow is prevented by arithmetic. Projected token counts are computable from the assembly record before the call at a cost proportional to admitted units and with no model call, and preventing the overflow costs strictly less than paying for a rejected call or, worse, accepting a silently truncated one whose accounting cannot name what left. Staleness is prevented by a timestamp predicate at admission: a unit past its expiry or behind its canonical version is refused entry, which costs one lookup per unit against work that otherwise includes re-selection, cache invalidation, and a repeated call. Poisoning is contained, not detected, by an architectural rule applied once: content enters in a data position with no authority, and every consequential effect is authorized against the calling principal's own grants. That containment costs nothing per call, whereas detection of injection is unreliable in principle and must never be the control that holds.

**Recovery-only modes**: Distraction cannot be prevented by admission policy because utilization is defined by what the model did with the admitted content, and no admission rule can compute that before the call. An estimate of relevance is exactly the estimate that already ran and admitted the unit; asking it again produces no new information. Contradiction cannot be prevented at the store level because each of the two conflicting records is individually consistent within its own scope, and the conflict comes into existence only when both are co-present in one window under a scope tuple that no longer separates them. Store-level validation is structurally blind to this, which is why the detection in this guide runs over admitted content rather than over stored records.

**Default detection budget allocation**: Agents must declare a per-call detection allowance in latency, tokens, and evaluator calls, and partition it as follows for a general tool-using agent: at most 2 percent to overflow projection, at most 5 percent to freshness and supersession lookups, at most 8 percent to instruction-shape scanning, at least 40 percent to utilization measurement and its attribution, and at least 30 percent to the contradiction index and its adjudication. The remainder covers logging and baseline maintenance. These shares are deployment defaults, recalibrated per task class against measured mode frequency, and they are recorded as defaults in Section V rather than presented as measured findings. Where a deployment's measured mode frequency shows one mode below 1 occurrence per 500 turns for 3 consecutive review windows, its share is reduced by half and reallocated to the highest-frequency mode.

**The rule that makes the allocation safe**: Reducing a mode's detection share never reduces its prevention rule. An admission-time freshness predicate runs on 100 percent of candidates regardless of what share staleness detection holds, and the isolation mechanism holds on 100 percent of admitted content regardless of what share instruction-shape scanning holds. Budget is allocated to detection, never to containment.

### 1.4 Execution Tier Partition

Context failure prevention is a hybrid capability whose most consequential misassignment is asking a model to decide something a detector already decided. The deterministic tier owns every detection signal, every threshold evaluation, all supersession bookkeeping, all utilization measurement, and all isolation enforcement, because each requires exactness, reproducibility, and auditability that inference does not supply. The model tier owns the two judgements no rule covers: whether two units whose scope tuples differ are semantically in conflict, and which admitted units to propose for eviction when a partition is contested. The hybrid tier is the handoff, and authority in it is fixed rather than negotiated.

**Two authority rules govern the partition and admit no exception.** First, a detection signal is deterministic, and a model opinion never overrides a fired detector: a model assertion that a stale unit is still current, that a conflicting pair is reconcilable, or that an over-budget assembly will fit is an input to adjudication and never a suppression of the trigger. Second, a detector's clean verdict does not grant authority: an instruction-shape scan that returns no finding does not promote the scanned unit out of its data position, does not raise its trust class, and does not license an effect that the calling principal's own grants do not already permit. Detection reduces the frequency of harm; only containment bounds it.

**Tier ownership by artifact**:

| Artifact | Owning tier | Authority where the tiers disagree |
| :-- | :-- | :-- |
| Assembly record, token projection, and partition bounds | Deterministic | Deterministic; a model estimate of remaining budget is advisory only |
| Utilization measurement and citation binding | Deterministic | Deterministic; utilization is computed from citation identifiers, never asserted by the model that produced the output |
| Supersession ledger, expiry evaluation, and staleness verdicts | Deterministic | Deterministic; a model claim that a value is current is not evidence |
| Contradiction index construction and structured field comparison | Deterministic | Deterministic; conflicting current values are surfaced, never silently reconciled |
| Instruction-shape verdict recorded as a field | Deterministic | Deterministic; the verdict is data recorded on the unit, never a permission acted upon |
| Isolation enforcement, trust-class assignment, and effect authorization | Deterministic | Deterministic; authorization is enforced in the tool layer and is unreachable from prompt content |
| Threshold evaluation and detector firing | Deterministic | Deterministic; a fired detector is not overridable by any model output |
| Quarantine placement and lineage traversal | Deterministic | Deterministic; the traversal runs to completion regardless of model objection |
| Semantic contradiction judgement where scope tuples differ | Model | Model proposes conflict or compatibility; the deterministic precedence policy decides the outcome and unresolved conflict is disclosed |
| Eviction candidate proposal under partition pressure | Model | Model proposes; the protected set and the partition bound bind absolutely |
| Ablation hypothesis naming the suspected distractor | Model | Model names candidates; the measured utilization change decides |
| Remedy selection where two modes are co-present | Hybrid | Model may order equally ranked remedies; the declared ordering rule in Step 4.1 overrides any other ordering |

***

## II. Operational Framework: Instrumented Detection and Mode-Specific Remediation of the Assembled Context

The framework produces a per-call detection record over the assembled context, a mode classification with the unit identifiers that evidence it, a remedy drawn from the mode-specific column rather than from a general ladder, a verification distinguishing resolution from relocation, and a correction applied to the admission rule that produced the failure. Every phase is assignable to an execution tier under Section 1.4, and every step that crosses tiers names the handoff.

### Phase 1: Failure-Mode Taxonomy and Detection-Signal Declaration

**Objective**: Fix the five failure modes, bind exactly one detection signal and one numeric trigger to each, and declare which modes are prevented at admission, so that no failure is diagnosed by impression at runtime.

#### Step 1.1: Adopt the Five-Mode Taxonomy and Bind One Signal to Each Mode

**Required Actions**:

- Adopt the four modes named by the umbrella context-management guidance without renaming them, and add poisoning as the fifth, recording the extension and the evidence supporting it rather than coining a parallel vocabulary.
- Bind exactly one primary detection signal to each mode, and require that the signal be computable by the deterministic tier from the assembly record, the citation binding, and the event log alone.
- Reject any candidate signal that requires a human to read the transcript, that requires a model to render an opinion before the trigger fires, or that is available only after the failure has already reached a user.
- Map every failure description inherited from prose sources onto one of the five modes, and record superfluous-content failures as the attributable subset of distraction and position-dependent failures as a stratification of the distraction signal, not as separate modes.
- Declare for each mode the closed reason-code vocabulary that its detection, remedy, and verification events draw from, so that mode frequency is queryable without prose parsing.

**Required Outputs**:

- A five-mode taxonomy record naming each mode, its definition, and its origin as adopted or extended.
- A signal binding table with one primary detection signal per mode and its computation source.
- A mapping record placing every inherited failure description onto exactly one mode.
- A closed reason-code vocabulary per mode.

**Quality Checkpoints**:

- Exactly 5 modes are declared, and 4 of them carry the umbrella's names unchanged.
- Every mode has exactly 1 primary detection signal; a mode with 0 signals cannot be detected and a mode with 2 produces contradictory triggers.
- 100 percent of declared signals are computable by the deterministic tier without a transcript read and without a model call.
- 0 inherited failure descriptions remain unmapped or are promoted to a sixth mode.

***

#### Step 1.2: Set the Numeric Trigger, the Consequence, and the Baseline Window

**Required Actions**:

- Set one numeric trigger per signal, expressed as a threshold on a computed quantity, and attach to each trigger the single consequence that firing produces.
- Set the rolling baseline window for every signal to 20 turns of the same task class, so a degraded turn is distinguishable from a normal one rather than judged against an absolute expectation the deployment has never met.
- Record every signal on 100 percent of turns whether or not a failure was observed, since a signal recorded only after a complaint has no baseline and cannot establish that the value was abnormal.
- Set the trigger for a newly deployed signal at the value observed at the 90th percentile of its first 100 baseline turns, and refuse to operate the signal in blocking mode until that baseline exists.
- Declare for each trigger whether firing blocks the call, warns and proceeds, or records only, and prohibit the silent downgrade of a blocking trigger to a warning to complete a task.

**Required Outputs**:

- A trigger table with one threshold, one consequence, and one enforcement mode per signal.
- A rolling baseline of each signal over the last 20 turns per task class.
- A baseline sufficiency record naming which signals have reached 100 turns and are eligible for blocking mode.

**Quality Checkpoints**:

- Every signal carries exactly 1 threshold and 1 named consequence; a threshold with no consequence is instrumentation and is recorded as such.
- All 5 signals are computed on 100 percent of turns; a missing signal is an instrumentation defect that halts the diagnosis in Phase 4.
- 0 blocking triggers operate before 100 baseline turns have been recorded for their task class.
- 0 blocking triggers are downgraded to warnings without a recorded policy change and a named owner.

***

#### Step 1.3: Declare the Prevention Rules and Partition the Detection Budget

**Required Actions**:

- Classify each of the five modes as prevention-cheap or recovery-only using the test in Section 1.3, and state for each recovery-only mode the specific reason no admission rule can compute its defining property.
- Write the admission-time prevention rule for each prevention-cheap mode: a token projection refusing an over-budget assembly, a freshness predicate refusing an expired or superseded unit, and a trust-class assignment placing every unit in a data position with no authority.
- Partition the per-call detection allowance across the five modes, allocating the majority to the recovery-only modes and the minority to scanning for modes already contained by an admission rule.
- Fix the invariant that a reduction in a mode's detection share never reduces its prevention rule, and enforce the invariant in the assembler rather than in policy prose.
- Set the recalibration rule: where a mode records fewer than 1 occurrence per 500 turns across 3 consecutive review windows, halve its detection share and reallocate the released budget to the mode with the highest measured frequency.

**Required Outputs**:

- A prevention-versus-recovery classification with a stated reason for each recovery-only mode.
- An admission-time prevention rule per prevention-cheap mode, implemented in the admission gate.
- A detection budget partition in latency, tokens, and evaluator calls, summing to 100 percent of the declared allowance.
- A recalibration rule with its measurement window and reallocation target.

**Quality Checkpoints**:

- Every mode carries a prevention-versus-recovery classification; an unclassified mode causes detection budget to be spent uniformly, which is the defect this step prevents.
- The detection budget partition sums to exactly 100 percent of the declared allowance.
- Prevention rules run on 100 percent of candidates independently of the detection share their mode holds.
- 0 detection budget is allocated to containment; containment is architectural and is not funded from the detection allowance.

***

### Phase 2: Instrumentation of the Assembled Context

**Objective**: Emit the per-call artifacts from which every detection signal is computed, so that detection runs against a structured record of what was assembled rather than against the rendered prompt text.

#### Step 2.1: Emit the Per-Unit Assembly Record in Serialization Order

**Required Actions**:

- Emit one assembly record per model call, listing every admitted unit in serialization order with the field inventory below, and emit it before the call rather than reconstructing it afterward from the prompt string.
- Assign every unit a stable identifier that survives compaction, eviction, and re-selection, so that the same source content admitted on two turns is recognisable as the same unit rather than as two.
- Record the position index and the position band of every unit, dividing the serialized sequence into a leading band covering the first 15 percent of tokens, a middle band, and a trailing band covering the last 15 percent, because position-conditioned utilization is computed against these bands.
- Record the admission rule identifier that admitted each unit, since attribution of a non-utilized unit to its admitting rule is impossible without it and Phase 6 depends on that attribution.
- Compute token counts with the target model's tokenizer after serialization, never from character counts, whose token ratio varies by more than a factor of 3 across languages and modalities.
- Record the exclusion list alongside the admission list, naming what was considered and rejected with its reason code, because a coverage gap is diagnosable only when the rejected candidate is visible.

**Assembly record field inventory**:

```
PER CALL
  call_id, task_class, model_id, tokenizer_version, contract_version
  input_budget_tokens, output_reserve_tokens, projected_total_tokens
  partition_ledger: name, max_tokens, used_tokens, floor, eviction_order_applied
  detection_budget_consumed: latency_ms, tokens, evaluator_calls

PER ADMITTED UNIT
  unit_id, partition, position_index, position_band
  source_id, source_version, canonical_version_at_admission
  trust_class, capture_channel, instruction_shape_verdict
  observed_at, expires_at, transaction_time
  scope_tuple: entity_id, predicate, valid_from, valid_to,
               tenant, jurisdiction, unit_of_measure, version
  scope_qualifiers_stored, scope_qualifiers_serialized
  token_count, admission_rule_id, marginal_utility_estimate

PER EXCLUDED CANDIDATE
  candidate_id, source_id, rejecting_gate, reason_code, token_count
```

**Required Outputs**:

- One assembly record per call carrying every field in the inventory, in serialization order.
- A stable unit identifier per admitted unit, reusable across turns.
- An exclusion list with a reason code per rejected candidate.

**Quality Checkpoints**:

- An assembly record exists for 100 percent of calls; a call without one is undetectable by every signal in this guide and is treated as an instrumentation defect.
- Every admitted unit carries a position band, an admission rule identifier, and a scope tuple; a unit missing any of the three disables one detection signal.
- Token counts are tokenizer-computed on 100 percent of units; 0 counts are estimated from character length.
- The exclusion list is non-empty on any call where a candidate was rejected; a silently discarded candidate is a coverage gap that no later analysis can recover.

***

#### Step 2.2: Bind Citation Identifiers So Utilization Is Computable After the Call

**Required Actions**:

- Require the model to emit the unit identifiers supporting every claim, every tool argument, and every state update, using the identifiers carried in the assembly record rather than restated source titles or quoted text.
- Treat a unit as utilized only where a bound identifier appears in a supported claim, a tool call, or a state update; presence in the window, semantic similarity to the output, and a model assertion that a unit was helpful are none of them evidence of utilization.
- Validate every emitted identifier against the assembly record and classify each as bound, unbound, or fabricated, and treat a fabricated identifier as a poisoning signal rather than as a formatting error.
- Compute utilization as bound-cited units divided by admitted units, and compute it separately per partition, per admission rule, and per position band, since an aggregate figure conceals the band in which the loss occurred.
- Compute coverage independently as the proportion of declared evidence requirements with at least one admitted eligible unit, and never derive coverage from utilization or from a retrieval similarity score.
- Record consumption for units that shape an output without being citable, such as a schema or a standing constraint, under a separate consumed-not-cited class, so that non-citable units do not depress the utilization ratio.

**Required Outputs**:

- A citation binding record per call mapping each output claim, tool call, and state update to its supporting unit identifiers.
- A utilization measurement per partition, per admission rule, and per position band.
- A coverage measurement computed from declared evidence requirements.
- An identifier validation record classifying every emitted identifier as bound, unbound, or fabricated.

**Quality Checkpoints**:

- Utilization is computed from bound identifiers on 100 percent of calls; a utilization figure asserted by the model rather than computed is rejected.
- Coverage and utilization are reported as 2 separate quantities; a single combined retrieval score makes distraction undetectable.
- 0 fabricated identifiers are treated as formatting noise; each is routed to the poisoning signal in Phase 5.
- Every non-citable unit is classified as consumed-not-cited before the utilization ratio is computed.

***

#### Step 2.3: Maintain the Supersession Ledger and the Contradiction Index

**Required Actions**:

- Build the supersession ledger per call by resolving every admitted unit against the current canonical version and expiry of its source at assembly time, recording the verdict as current, superseded, or expired.
- Record supersession lineage rather than overwriting it, so that a superseded version present in the window is identifiable as superseded rather than merely different from its successor.
- Build the contradiction index by generating candidate pairs keyed on shared entity identifier and predicate, and bound the index to pairs whose scope tuples intersect, since exhaustive pairwise comparison is quadratic in admitted units and its false positives dominate its true ones.
- Run the scope-qualifier retention check over every admitted unit, comparing the qualifiers present in the stored form against those present in the serialized form, and flag every unit that dropped one.
- Cap the contradiction index at 500 candidate pairs per call, and where the cap binds, retain pairs by descending authority rank of the units involved rather than by arbitrary order.
- Emit both artifacts before the call, since a contradiction discovered after the response has already influenced it.

**Required Outputs**:

- A supersession ledger with a current, superseded, or expired verdict per admitted unit.
- A contradiction index of scope-intersecting candidate pairs with their authority ranks.
- A scope-qualifier retention record naming every unit whose serialized form dropped a stored qualifier.

**Quality Checkpoints**:

- Every admitted unit carries a supersession verdict; an unresolved verdict is treated as expired rather than as current.
- The contradiction index contains 0 pairs whose scope tuples do not intersect, and at most 500 pairs in total.
- The scope-qualifier retention check runs on 100 percent of admitted units, since a dropped qualifier is the origin of in-window contradiction that store-level validation cannot see.
- Both artifacts are emitted before the model call on 100 percent of calls.

***

### Phase 3: Per-Mode Detection Against Numeric Triggers

**Objective**: Evaluate each mode's detection signal against its declared trigger on every turn, producing a fired or clear verdict per mode with the unit identifiers that evidence it.

#### Step 3.1: Detect Overflow by Projection Before the Call

**Required Actions**:

- Project the serialized token count for the total assembly and for every partition from the assembly record, and compare each against the input budget and the partition maximum before the call is issued.
- Fire the overflow detector where the projected total exceeds 100 percent of the input budget, or where any partition exceeds 100 percent of its maximum after that partition's eviction order has been exhausted.
- Refuse to issue any call whose projection exceeds the budget, and return an overflow verdict carrying the per-partition ledger rather than allowing the provider to truncate or reject it.
- Treat a provider length rejection reaching the agent as evidence that the projection is not running, and route it as an instrumentation defect rather than as an overflow event.
- Prohibit blind truncation from the front or the middle of a serialized package without exception, because truncation removes content the accounting cannot name and converts an observable overflow into an unobservable coverage gap.
- Reference the umbrella guidance for the budget partitioning itself, including partition shares, floors, and eviction orders, and do not restate them here, since a second statement of the partition table is a second source of truth.

**Required Outputs**:

- A projection record per call with the total and per-partition figures against their bounds.
- An overflow verdict of fired or clear with the identifiers of the partitions that breached.
- An instrumentation defect record for every provider length rejection observed.

**Quality Checkpoints**:

- Overflow is detected before the call on 100 percent of occasions; a provider length rejection reaching the agent indicates the projection is not running and halts the deployment for repair.
- 0 calls are issued whose projected total exceeds 100 percent of the input budget.
- 0 units leave the working set through truncation; every removal carries an eviction reason code.
- The partition bounds evaluated here are read from the umbrella contract rather than redeclared.

***

#### Step 3.2: Detect Distraction by Position-Conditioned Utilization

**Required Actions**:

- Compute utilization from the citation binding of the previous call and compare it against the coverage the assembly record claimed, since the diagnostic value of the signal lies in the gap between the two.
- Fire the distraction detector where utilization falls below 40 percent while coverage exceeds 80 percent, or where utilization falls 15 or more percentage points across the 20-turn rolling baseline while coverage moves less than 5 points.
- Confirm distraction rather than assuming it by verifying that the required unit was admitted and uncited, which distinguishes distraction from a selection failure in which the required unit was never admitted and coverage, not utilization, is the deficient quantity.
- Stratify utilization by position band and fire a position-specific verdict where the middle band's utilization falls more than 20 percentage points below the mean of the leading and trailing bands, since the remedy for a positional loss is repositioning rather than removal.
- Attribute non-utilization to specific admitted units by removal ablation in an offline or canary environment, running at least 3 repetitions per candidate to separate a real effect from sampling variation, and never mutating a production context for a consequential live action.
- Record the distraction verdict with the identifiers of the uncited units and their admission rules, not merely with the ratio, since Phase 6 corrects rules rather than ratios.

**Required Outputs**:

- A utilization measurement with its coverage comparison and its position-band stratification.
- A distraction verdict of fired or clear with the identifiers of the uncited admitted units.
- An ablation record naming the candidate distractors and the measured utilization change per candidate.

**Quality Checkpoints**:

- Utilization and coverage are compared as 2 distinct quantities on 100 percent of turns.
- A distraction verdict is never issued where the required unit was absent from the assembly record; that case is recorded as a coverage failure and routed to the selection sibling.
- Every ablation carries at least 3 repetitions; a conclusion drawn from 1 stochastic pair is rejected.
- 0 ablations are run against production context for a consequential live action.

***

#### Step 3.3: Detect Contradiction and Staleness Over Admitted Content

**Required Actions**:

- Evaluate every pair in the contradiction index by deterministic comparison first, comparing keyed numeric, enumerated, temporal, and identifier fields, and resolve every pair the deterministic comparison settles without invoking a model.
- Route only the residue to the model tier: pairs whose scope tuples differ such that compatibility depends on open-vocabulary meaning, and cap that residue at 25 pairs per call so that adjudication cost is bounded.
- Fire the contradiction detector at 1 or more intersecting pairs among unexpired authoritative units, or at 1 or more units failing the scope-qualifier retention check, and record both conditions separately because they carry different remedies.
- Refuse to treat textual difference as contradiction and refuse to treat textual similarity as agreement: two statements differing on a closing time may be compatible once a day-of-week qualifier is restored, and two near-identical statements may conflict where they refer to different entity versions.
- Fire the staleness detector at 1 or more admitted units past expiry, 1 or more whose admitted source version differs from the current canonical version, or any superseded version present alongside its successor, reading all three conditions from the supersession ledger rather than inferring age from content.
- Record both verdicts with the identifiers of the units involved and their authority ranks, and never with a count alone.

**Required Outputs**:

- A contradiction verdict of fired or clear with the pair identifiers, the conflicting field, and the authority ranks.
- A scope-qualifier retention verdict naming every unit that dropped a stored qualifier.
- A staleness verdict of fired or clear with the identifiers of the expired, behind-version, and superseded units.

**Quality Checkpoints**:

- Deterministic comparison runs before model adjudication on 100 percent of candidate pairs; a pair sent to a model that a field comparison would have settled is a budget defect.
- At most 25 pairs per call reach the model tier; above that cap the excess is deferred and recorded rather than adjudicated.
- Every fired verdict carries unit identifiers; a verdict carrying only a count cannot be remedied and is rejected.
- Staleness verdicts are read from the supersession ledger on 100 percent of occasions; 0 verdicts are inferred from how old the content reads.

***

### Phase 4: Mode-Specific Remedy Selection and Application

**Objective**: Apply to each fired mode the remedy the mode requires, in an order that prevents one remedy from destroying the evidence another depends on, and bound the attempt so that a failing remedy terminates rather than repeats.

#### Step 4.1: Order Co-Present Modes Before Selecting Any Remedy

**Required Actions**:

- Refuse the classification "the context is too long" as a diagnosis, since that phrase names only overflow and is routinely applied to all five modes, producing the single remedy that repairs one of them.
- Where more than one detector has fired, apply the declared ordering rule rather than any model-proposed ordering: contain poisoning first, then remedy staleness, then contradiction, then distraction, then overflow.
- Justify the ordering in the record so that it is auditable: poisoning first because an unconstrained instruction can influence every subsequent remedy; staleness and contradiction before distraction because both inflate the admitted unit count that the distraction ratio is measured against; overflow last because the removals performed by the earlier remedies frequently clear it without a ladder entry.
- Withhold every remedy until the mode and its evidencing unit identifiers are recorded, since applying compression to an undiagnosed failure is the defect the whole phase exists to prevent.
- Where two modes are ranked equally by the ordering rule, permit the model tier to propose an order and require the deterministic tier to record which proposal was taken, because an unrecorded ordering makes a later verification failure unattributable.

**Required Outputs**:

- A mode classification per call naming every fired detector and the unit identifiers evidencing each.
- A remedy ordering record with the applied order and its justification.
- A remedy assignment per fired mode drawn from the mode-specific contract in Section 1.2.

**Quality Checkpoints**:

- 0 remedies are applied before the mode is recorded with its evidencing identifiers.
- The declared ordering is applied on 100 percent of multi-mode events; a model-proposed order that contradicts the declared order is discarded and the discard is logged.
- Every fired detector receives a remedy assignment or an explicit deferral with a reason code; a fired detector with neither is an unhandled failure.

***

#### Step 4.2: Apply the Distinct Remedy and Refuse the General One

**Required Actions**:

- Apply the distraction remedy by reducing the admitted unit count rather than the admitted token count: raise the admission threshold by 1 decile of the marginal-utility distribution, narrow tool definitions to those reachable from the current plan step, and drop the lowest-utility units named in the ablation record.
- Apply the positional remedy where the middle-band verdict fired, moving the required unit into the leading or trailing band rather than removing any unit, since the content was present and the deficiency was where it sat.
- Apply the contradiction remedy by restoring the dropped scope qualifier where the retention check fired, and otherwise by surfacing both units with their sources and authority ranks, applying the declared precedence policy, disclosing the resolution in the output, and escalating where precedence does not settle it.
- Apply the staleness remedy by evicting the superseded version, re-selecting the current version from the durable store, and invalidating every cache entry, derived summary, and index projection keyed to the old version.
- Apply the overflow remedy by entering the umbrella selection ladder at its least costly rung, and do not reimplement the ladder here.
- Refuse summarisation as the remedy for distraction, contradiction, or staleness, and record the refusal reason: compaction retains distractors in condensed form so density rises while the distraction persists and becomes harder to detect; it selects one side of a conflict silently and destroys the evidence that a conflict existed; and it blends stale and current values into one statement after which no freshness check can detect the staleness at all.

**Required Outputs**:

- A remedy application record per fired mode naming the specific action taken and the units affected.
- An invalidation record for every cache entry, derived summary, and index projection touched by a staleness remedy.
- A disclosure statement in the output for every contradiction resolved by precedence.

**Quality Checkpoints**:

- 0 distraction, contradiction, or staleness events are remedied by summarisation; each such application is a defect with a recorded reason.
- Every staleness remedy produces an invalidation record; a remedy that evicts the window copy while leaving a derived summary in place has relocated the failure rather than resolved it.
- Every precedence-resolved contradiction is disclosed in the output; a silent resolution is indistinguishable from the arbitrary selection the mode describes.
- Protected atoms survive 100 percent of remedy applications; a remedy that removes an objective, a constraint, or an open variable is reverted.

***

#### Step 4.3: Bound the Remedy Loop and Declare a Terminal State

**Required Actions**:

- Cap remedy attempts at 2 per mode per call, and require that the second attempt change a declared strategy rather than repeat the first, since an unchanged repetition of a deterministic operation cannot produce a different result.
- Declare the terminal-state vocabulary as exactly five values, resolved, contained, abstained, escalated, and deferred, and require every fired detector to end in exactly one of them before the call proceeds.
- Abstain where a blocking trigger remains fired after the attempt cap, stating what is missing, what was attempted, what can safely be concluded, and the next permitted action, and never convert a blocking verdict into a warning to complete the task.
- Escalate to a named human owner where a contradiction remains unresolved between two authoritative sources, where a poisoning containment action would revoke a production grant, or where the same blocking trigger fires on 3 consecutive calls in one task class.
- Record the detection budget consumed by the remedy loop, and abandon further attempts where the loop has consumed more than 25 percent of the per-call latency allowance.

**Required Outputs**:

- A terminal state per fired detector drawn from the five-value vocabulary.
- An abstention record naming the missing element, the attempts made, and the next permitted action.
- An escalation record with a named owner and a bounded response window for every escalated event.

**Quality Checkpoints**:

- 0 fired detectors end without a terminal state; an unterminated detector permits the call to proceed on context the deployment has declared invalid.
- No mode is remedied more than 2 times within one call, and the second attempt differs from the first in a recorded way.
- 0 blocking verdicts are downgraded to warnings to complete a task.
- The remedy loop consumes at most 25 percent of the per-call latency allowance; beyond it the call terminates in abstention rather than continuing to remediate.

***

### Phase 5: Injection and Poisoning Containment at the Window Boundary

**Objective**: Establish that content admitted to the window is data and never instruction, so that an instruction-shaped passage which evades every detector is still inert when it reaches the model.

#### Step 5.1: Admit Every Unit as Data and Assign the Trust Class Deterministically

**Required Actions**:

- Assign every admitted unit a trust class from a closed vocabulary, derived deterministically from the source class and the capture channel and never from the content itself, since a unit that can describe its own authority has no boundary at all.
- Prohibit admitted content from setting or raising its own trust class, its own sensitivity label, its own retention class, or its own authority, and enforce the prohibition in the assembler rather than in a prompt instruction.
- Restrict the instructions-and-policy partition and the tool-definitions partition to trusted configuration, and refuse admission to those partitions from retrieved text, tool output, sub-agent responses, and model-generated inference without exception.
- Cap the authority of any model-generated unit until it is corroborated by at least 2 independent source identifiers whose provenance lineages do not intersect, which is the control that stops an agent retrieving its own earlier inference and treating the retrieval as confirmation.
- Record the boundary against the sibling category explicitly: the memory-management guidance owns admission to the durable store and the delayed-execution trust boundary that persistence creates, while this guide owns admission to the window, and a unit that passed the store's gates is not thereby exempt from the window's.
- Preserve a protected original alongside any sanitized form, because sanitization destroys the evidence a later investigation requires.

**Required Outputs**:

- A trust class assignment per admitted unit with the deterministic rule that produced it.
- A partition eligibility record showing which trust classes were admissible into each partition.
- An authority cap with its corroboration requirement on every model-generated unit.
- A protected original reference for every sanitized unit.

**Quality Checkpoints**:

- Trust class is assigned by the deterministic tier on 100 percent of admissions; a content-derived trust class is a release blocker.
- 0 units raise their own trust class, sensitivity, retention, or authority.
- 0 retrieved, tool-derived, or model-generated units enter the instructions-and-policy or tool-definitions partitions.
- Model-generated units reach full authority only after 2 non-intersecting corroborating lineages are recorded.

***

#### Step 5.2: Enforce the Named Isolation Mechanism and Re-Authorize Every Effect

**Required Actions**:

- Name the isolation mechanism in the deployment contract rather than leaving it implicit, specifying all four components: a fixed delimiter convention, placement in a non-system message role at the lowest available privilege, a standing instruction in the trusted prefix declaring that delimited content is evidence carrying no authority, and enforcement of every consequential effect in the tool-authorization layer.
- Keep trusted instructions, policy, and schemas ahead of every admitted unit in assembly order, and serialize volatile content deterministically after them, so that position never places untrusted text where trusted text is expected.
- Retain the trust class label alongside each unit in the serialized form, so that an approved procedure is distinguishable from a quoted third-party document at the point of reading.
- Re-authorize every tool call, credential use, permission change, and confirmation waiver against the calling principal's own grants after every read, and never against anything an admitted unit asserts.
- Enforce that a detector's clean verdict grants no authority: an instruction-shape scan returning no finding does not promote a unit out of its data position, does not raise its trust class, and does not license any effect the principal's grants do not already permit. Detection reduces how often harm occurs; only the authorization layer bounds how bad it can be.
- Treat detection failure as expected rather than exceptional, and design so that an undetected instruction-shaped passage is inert by position and authorization alone.

**Poisoning admission paths and their containment controls**:

| Admission path | Poisoning origin | Containment control that holds without detection | What a clean detector verdict does not grant |
| :-- | :-- | :-- | :-- |
| Retrieved document or index result | Indirect injection embedded in fetched text | Data position, non-system role, no tool authority derived from content | Does not raise trust class or permit an effect outside the principal's grants |
| Tool result, including filenames, headers, and code comments | Indirect injection in a machine-produced payload | Size-capped, schema-validated, delimited, and never routed to a policy partition | Does not exempt the payload from schema validation or size caps |
| Sub-agent or delegated-agent response | Injection propagated across an isolation boundary | Child scope bounded at dispatch; the parent re-authorizes every effect the child proposes | Does not transfer the child's conclusions into the parent's trusted prefix |
| Model-generated inference retrieved back as evidence | Accidental self-poisoning through circular provenance | Authority cap requiring 2 non-intersecting corroborating lineages | Does not satisfy a corroboration requirement using the agent's own prior output |
| Conversation history carried across a boundary | An earlier accepted instruction persisting into a new window | Handoff record rebuilt from durable state rather than copied from the transcript | Does not make a previously accepted instruction authoritative on re-entry |

**Required Outputs**:

- A named isolation mechanism recorded in the deployment contract with all 4 components specified.
- An authorization record per consequential effect naming the principal grant that permitted it.
- A serialized form retaining the trust class label on every admitted unit.

**Quality Checkpoints**:

- The isolation mechanism is named with all 4 components; an unnamed mechanism cannot be tested and is treated as absent.
- 100 percent of consequential effects are authorized against the calling principal's grants; 0 are authorized against an assertion carried by admitted content.
- 0 units are promoted out of a data position by a clean detector verdict.
- Trusted instructions precede every admitted unit in serialization order on 100 percent of calls.

***

#### Step 5.3: Detect Poisoning Signals and Contain the Affected Lineage

**Required Actions**:

- Record an instruction-shape verdict as a field on every admitted unit, covering imperatives addressed to the assistant, role declarations, forged delimiters, policy assertions, invisible control characters, and active markup, and record the verdict without acting on it as a permission.
- Fire the poisoning detector at 1 or more units carrying an instruction-shape finding, or at 1 or more decisive output claims whose provenance path terminates in the agent's own prior inference with fewer than 2 independent corroborating source identifiers.
- Treat every fabricated citation identifier emitted by the model, meaning an identifier absent from the assembly record, as a poisoning signal rather than as a formatting error, since a fabricated identifier is an unsupported claim wearing a provenance label.
- Contain rather than correct on a fired verdict: quarantine the unit and every derivative that cites it, suspend the source's admission grant, and re-run the affected calls against the remaining corpus rather than editing the hostile content in place.
- Traverse the lineage to completion before declaring containment, covering derived summaries, index projections, cache entries, handoff records, and any durable write the affected calls produced, and hand the store-side traversal to the memory-management procedure that owns it.
- Preserve evidence before removal: never hard-delete a suspect unit ahead of the traversal, because deletion destroys the record needed to size the exposure.

**Required Outputs**:

- An instruction-shape verdict field on 100 percent of admitted units.
- A poisoning verdict of fired or clear with the identifiers of the units and claims involved.
- A quarantine record with the traversed lineage, the suspended source grants, and the named review owner.

**Quality Checkpoints**:

- Every admitted unit carries an instruction-shape verdict recorded as data; 0 verdicts are acted upon as permissions.
- Lineage traversal completes before containment is declared; a partial traversal leaves derivatives serving poisoned content and is recorded as uncontained.
- 0 suspect units are hard-deleted before the traversal completes.
- Every quarantine entry names a review owner and a release condition; an entry with neither becomes permanent storage.

***

### Phase 6: Remedy Verification and Admission-Policy Correction

**Objective**: Establish that each remedy resolved its failure rather than relocating it, attribute every recurrence to the admission rule that produced it, and prove each detector fires by injecting the fault it claims to catch.

#### Step 6.1: Verify That the Remedy Resolved Rather Than Relocated the Failure

**Required Actions**:

- Re-run the mode's detection signal after the remedy and confirm the value returned within its trigger, and treat this as a necessary condition rather than as the verification itself.
- Re-run the failed task step and confirm the output changed in the direction the diagnosis predicted, since a signal that clears while the output stays wrong establishes that the diagnosis was mistaken or that the failure moved.
- Apply the mode-specific relocation test rather than a generic one: for staleness, confirm by negative read that the superseded version is no longer servable from any cache, summary, or index projection; for contradiction, confirm the re-run selects the value the precedence policy names and that the resolution is disclosed; for distraction, confirm the required unit is now cited rather than merely that the ratio improved; for overflow, confirm every protected atom survived and every removal carries a reason code; for poisoning, replay the call with the instruction-shape detector disabled and confirm 0 unauthorized effects.
- Record the verification outcome as resolved, relocated, or unconfirmed, and never count an unconfirmed diagnosis as a resolution.
- Withdraw the diagnosis where the signal cleared and the output did not change, restore the removed units where restoration is safe, and re-enter Phase 3 with the diagnosis reopened.

**Required Outputs**:

- A verification record per remedy carrying the signal before and after, the output change observed, and the relocation test applied.
- A verification outcome of resolved, relocated, or unconfirmed per remedied mode.
- A negative-read confirmation for every staleness remedy and a detector-disabled replay result for every poisoning containment.

**Quality Checkpoints**:

- The triggering signal is within threshold after remediation on at least 90 percent of events; below that rate the remedy assignment itself is reviewed rather than repeated.
- Every remediation carries an observed output change or an explicit note that the diagnosis was not confirmed.
- 100 percent of poisoning containments are verified with the detector disabled; a containment verified only with the detector enabled has demonstrated detection, not containment.
- 0 unconfirmed diagnoses are recorded as resolutions.

***

#### Step 6.2: Attribute Recurrence to an Admission Rule and Revise It

**Required Actions**:

- Attribute every non-utilized unit and every fired detector to the admission rule identifier that admitted the units involved, using the assembly record rather than a reconstruction.
- Treat recurrence as a policy defect rather than an event: where the same mode fires on the same task class 3 times within 20 turns, open an admission-policy revision instead of remedying it a fourth time.
- Rank admission rules by the volume of admitted-but-uncited tokens they produce, and revise the highest-ranked rule first, since the largest contributor to distraction is rarely the rule that looks most permissive.
- Freeze a baseline before revising and re-measure the same task class against it after, so that a revision which trades distraction for a coverage gap is visible rather than counted as an improvement.
- Reject any revision that raises utilization while lowering coverage by more than 5 percentage points, since removing required evidence raises the ratio by shrinking its denominator.
- Recalibrate the detection budget partition on the same cadence, applying the reallocation rule from Step 1.3 to the measured mode frequencies.

**Required Outputs**:

- An attribution record binding every fired detector and every uncited unit to an admission rule identifier.
- A recurrence counter per mode per task class over a rolling 20-turn window.
- An admission-policy revision record with the frozen baseline, the change made, and the post-change measurement.

**Quality Checkpoints**:

- 100 percent of fired detectors are attributed to an admission rule; an unattributed detection cannot correct anything and is treated as an instrumentation gap.
- No mode is remedied more than 3 times for one task class within 20 turns without an admission-policy revision being opened.
- Every revision is measured against a frozen baseline; 0 revisions are accepted on an unmeasured impression of improvement.
- 0 revisions are accepted that lower coverage by more than 5 percentage points.

***

#### Step 6.3: Prove Every Detector by Injecting the Fault It Claims to Catch

**Required Actions**:

- Inject one controlled fault per declared detector into an isolated environment carrying production-equivalent policy, covering at minimum an over-budget assembly, a topically similar irrelevant unit set, a scope qualifier dropped at serialization, a superseded version admitted alongside its successor, and an instruction-shaped passage embedded in a retrieved document.
- Verify for each injection that the intended detector fires before any user-visible output or external effect, and record every detection that arrives late as a miss with a named owner.
- Measure detector precision and recall against the injected set, and estimate false negatives from injection and review rather than from alert volume, since a detector measured only on its own alerts cannot estimate recall.
- Repeat each injection at 3 positions, the leading, middle, and trailing bands, because a detector that fires only where content sits early is not a detector of the mode.
- Verify containment separately from detection for the poisoning injection, running the case with the detector disabled and confirming the injected instruction produces 0 unauthorized effects.
- Prohibit injection into production without explicit authorization, tenant isolation, a kill switch, and unmistakable synthetic markers, and never inject using real secrets or real cross-tenant content.

**Required Outputs**:

- An injection result per declared detector with its fire or miss verdict and the latency to detection.
- A precision and recall measurement per detector against the injected set.
- A containment result demonstrating that an injected instruction is bounded by authorization rather than by detection.

**Quality Checkpoints**:

- Every declared detector has at least 1 injection case; an unproven detector is treated as absent when detection budget is allocated.
- Detector recall against the injected set is at least 0.90 for blocking triggers; below that the trigger is demoted to warning until recall is restored.
- Every injection is repeated at 3 position bands.
- Poisoning containment holds with the detector disabled in 100 percent of injected cases; any unauthorized effect halts release.

***

## III. Implementation Guidance for AI Agents

AI agents operating this framework must hold a strict separation between the components that compute detection signals and the components that render judgement, because the most common production failure of context-failure prevention is a model being asked whether a fired detector was right. The following guidance translates the framework into an executable control structure.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Detection Supervisor Agent**: Owns the five-mode taxonomy, the trigger table, and the detection budget partition. Authorizes trigger demotion and admission-policy revision. Enforces the rule that a fired detector is not overridable, at every handoff.
2. **Instrumentation Agent**: Emits the assembly record, the citation binding, the supersession ledger, and the contradiction index before every call. Never interprets content and never renders a verdict.
3. **Detection Agent**: Computes the five signals from the emitted artifacts and evaluates each against its trigger, producing a fired or clear verdict with evidencing unit identifiers. Operates entirely in the deterministic tier and holds no model call.
4. **Adjudication Agent**: The single model-tier component. Judges semantic contradiction where scope tuples differ, proposes eviction candidates under partition pressure, and names ablation hypotheses. Proposes only; it may never suppress a trigger, alter a threshold, or assign a terminal state.
5. **Remediation Agent**: Applies the mode-specific remedy in the declared order, enforces the 2-attempt cap and the changed-strategy requirement, and assigns a terminal state to every fired detector.
6. **Containment Agent**: Owns trust-class assignment, isolation enforcement, quarantine placement, and lineage traversal. It may quarantine and suspend an admission grant but may never widen a scope or raise a trust class.
7. **Verification Agent**: Runs the mode-specific relocation tests, executes the injection suite, and measures detector precision and recall. Returns a pass or fail verdict with evidence and holds release authority jointly with the supervisor.

**Workflow Execution Pattern**:

```
STATE: Phase_3_Per_Mode_Detection
ACTIONS:
  1. Read assembly record, citation binding, supersession ledger, contradiction index
  2. Project tokens per partition and in total against declared bounds
  3. Compute utilization by partition, admission rule, and position band
  4. Evaluate contradiction index pairs deterministically, then route residue
  5. Resolve every unit against canonical version and expiry
  6. Emit fired or clear verdict per mode with evidencing unit identifiers
VALIDATION:
  - signals_computed_this_turn == 5
  - every_fired_verdict_carries_unit_ids == TRUE
  - model_pairs_adjudicated <= 25
  - baseline_turns_recorded >= 100 for every blocking trigger
TRANSITIONS:
  IF no_detector_fired THEN next_state = Issue_Model_Call
  IF any_detector_fired THEN next_state = Phase_4_Remedy_Ordering
  IF signals_computed_this_turn < 5 THEN next_state = Instrumentation_Defect_Halt
```

**Two-Phase Action Pattern**:

1. **Detect**: Compute all five signals and emit verdicts before any remedy is considered, so that the diagnosis is recorded independently of the remedy that follows it.
2. **Remedy**: Apply the mode-specific action in the declared order, bounded at 2 attempts per mode.
3. **Verify**: Confirm resolution rather than relocation before the terminal state is assigned.

**Approval Gate**: Human authorization is required before any of the following, and agents must halt rather than proceed: suspending a production source's admission grant, demoting a blocking trigger to a warning, accepting an admission-policy revision that lowers measured coverage by any amount, and continuing a task class in which the same blocking trigger has fired on 3 consecutive calls. Below those thresholds an agent may quarantine a unit, abstain, escalate, and re-run a call against the remaining corpus without authorization, because each is reversible and none widens a scope.

**Context Management Requirements**:

- Hold the assembly record and the detection artifacts outside the window as durable state, since detection over the window cannot itself be conducted from inside the window.
- Compute detection signals over identifiers and structured fields rather than over rendered prompt text, so that the detection cost does not scale with the content it examines.
- Write a handoff record at every context boundary naming the fired detectors, their terminal states, the open quarantine entries, and the recurrence counters, since a boundary that discards the counters resets a policy defect to zero.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Taxonomy and Trigger Completeness (After Phase 1)**

- **Automated Check**: Exactly 5 modes declared; exactly 1 primary signal and 1 numeric trigger per mode; every signal computable without a transcript read or a model call; detection budget partition sums to 100 percent.
- **Agent Action on Pass**: Proceed to instrumentation.
- **Agent Action on Failure**: Halt and return the modes lacking a signal, a trigger, or a consequence.
- **Human Review Trigger**: Any proposal to add a sixth mode, or any signal that cannot be computed deterministically.

**Checkpoint 2: Instrumentation Sufficiency (After Phase 2)**

- **Automated Check**: An assembly record exists for 100 percent of calls; every admitted unit carries a position band, an admission rule identifier, a scope tuple, and a supersession verdict; utilization and coverage are emitted as separate quantities.
- **Agent Action on Pass**: Enable detection in recording mode and begin baseline accumulation.
- **Agent Action on Failure**: Halt detection; a signal computed from an incomplete record produces verdicts that cannot be remedied.
- **Human Review Trigger**: More than 5 percent of calls missing an assembly record over a 100-call window.

**Checkpoint 3: Detection Integrity (After Phase 3)**

- **Automated Check**: All 5 signals computed on 100 percent of turns; every fired verdict carries unit identifiers; at most 25 pairs routed to the model tier; 0 calls issued over the projected budget.
- **Agent Action on Pass**: Proceed to remedy ordering.
- **Agent Action on Failure**: Treat as an instrumentation defect and halt the affected task class rather than proceeding on partial detection.
- **Human Review Trigger**: Any provider length rejection reaching the agent, which establishes that projection is not running.

**Checkpoint 4: Remedy Discipline (After Phase 4)**

- **Automated Check**: 0 remedies applied before a mode was recorded; declared ordering applied on 100 percent of multi-mode events; 0 distraction, contradiction, or staleness events remedied by summarisation; every fired detector holds a terminal state.
- **Agent Action on Pass**: Proceed to verification.
- **Agent Action on Failure**: Revert the remedy where reversion is safe, restore the removed units, and reopen the diagnosis.
- **Human Review Trigger**: More than 2 remedy attempts required for one mode within a single call.

**Checkpoint 5: Containment Proof (After Phase 5)**

- **Automated Check**: Isolation mechanism named with all 4 components; 100 percent of consequential effects authorized against principal grants; 0 units promoted by a clean detector verdict; lineage traversal complete for every quarantine.
- **Agent Action on Pass**: Permit consequential actions for the task class.
- **Agent Action on Failure**: Suspend consequential actions and route to containment review; quality remediation alone is insufficient where authority may have been acquired.
- **Human Review Trigger**: Any unauthorized effect observed in a detector-disabled replay, which halts release without exception.

**Checkpoint 6: Verification and Release Conformance (After Phase 6)**

- **Automated Check**: Signal within threshold after remediation on at least 90 percent of events; every declared detector carries at least 1 injection case; detector recall at least 0.90 for blocking triggers; 0 unconfirmed diagnoses counted as resolutions.
- **Agent Action on Pass**: Release the configuration and record the measured baselines.
- **Agent Action on Failure**: Demote the failing blocking triggers to warning mode and hold release until recall is restored.
- **Human Review Trigger**: Detector recall below 0.75 for any mode, or a relocation outcome recorded on more than 10 percent of remedies.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
PHASE_BOUNDARY:
SIGNALS_EVALUATED:
MEASURED_VALUE:
TRIGGER_THRESHOLD:
VERDICT:
FAIL_ACTION_TAKEN:
RESPONSIBLE_AGENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: A Detection Signal Cannot Be Computed**

- **Symptoms**: Fewer than 5 signals recorded for a turn; a utilization figure absent because no citation identifiers were bound; a staleness verdict absent because units carry no expiry field.
- **Diagnostic Steps**: Read the assembly record for the affected call and identify which field inventory entries are missing; check whether the model emitted identifiers at all; confirm the tokenizer version matches the target model.
- **Resolution Protocol**: Option A, restore the missing field at the assembler and replay the affected window in recording mode to rebuild the baseline. Option B, where identifiers cannot be bound because the output format does not carry them, switch the affected task class to a structured output schema that requires them before re-enabling the distraction trigger. Option C, where the field is genuinely unavailable from the source, mark the mode undetectable for that task class, reallocate its detection budget, and record the gap rather than reporting a clear verdict.
- **Escalation Trigger**: More than 5 percent of calls missing any signal across a 100-call window halts the task class for repair.

**Error Type 2: The Signal Clears but the Output Does Not Change**

- **Symptoms**: A remedy returns its triggering signal within threshold while the re-run reproduces the original wrong output; utilization rises immediately after units are removed.
- **Diagnostic Steps**: Determine whether the ratio improved by shrinking its denominator rather than by increasing citation; apply the mode-specific relocation test; confirm the diagnosis named the mode the evidence supports.
- **Resolution Protocol**: Option A, treat the outcome as relocation, restore the removed units, and reopen the diagnosis at Phase 3 with the withdrawn mode excluded. Option B, where a second mode was co-present and unremedied, apply the declared ordering and remedy the earlier mode first. Option C, where no mode's evidence fits, record the failure as not context-attributable and route it out of this framework rather than remedying a mode that did not occur.
- **Escalation Trigger**: A relocation outcome on more than 10 percent of remedies over a 50-remedy window triggers review of the remedy assignments themselves.

**Error Type 3: The Contradiction Detector Floods With False Positives**

- **Symptoms**: Candidate pair volume approaches the 500-pair cap on ordinary calls; adjudication consumes its whole budget share; conflicts are reported between statements that qualifiers reconcile.
- **Diagnostic Steps**: Inspect the pair generator's keying to confirm it requires shared entity and predicate and intersecting scope tuples; sample flagged pairs and classify each as a true conflict, a qualifier artifact, or a version artifact.
- **Resolution Protocol**: Option A, tighten the pair generator to require scope-tuple intersection on valid time and unit of measure before a pair is admitted to the index. Option B, run the scope-qualifier retention check first and repair dropped qualifiers, since a qualifier artifact is a serialization defect rather than a conflict. Option C, where the flood is dominated by version artifacts, resolve staleness first, which removes superseded units from the index before pairs are generated.
- **Escalation Trigger**: Precision below 0.50 across 100 adjudicated pairs demotes the contradiction trigger to warning mode until the generator is repaired.

**Error Type 4: Containment Is Found to Depend on Detection**

- **Symptoms**: A detector-disabled replay produces an unauthorized effect; an admitted unit is observed influencing a tool allowlist, a confirmation rule, or its own trust class.
- **Diagnostic Steps**: Trace the effect to the authorization decision that permitted it and determine whether that decision consulted admitted content; confirm the isolation mechanism's four components are all present; check whether the effect was authorized against the calling principal's grants.
- **Resolution Protocol**: Option A, move the authorization decision into the tool layer so that it is unreachable from prompt content, and re-run the replay. Option B, route the untrusted source through a component that reads it and holds no tool authority, emitting only a constrained structured proposal that the privileged component authorizes independently. Option C, where neither is available in time, suspend consequential actions for the task class and permit read-only operation until containment is proven.
- **Escalation Trigger**: Any unauthorized effect in a detector-disabled replay halts release immediately; this error is never resolved by retry and never by strengthening the detector.

**Error Type 5: The Distraction Remedy Trades Utilization for Coverage**

- **Symptoms**: Utilization rises after an admission threshold increase while task success falls; abstentions rise; the required unit appears in the exclusion list rather than the admission list.
- **Diagnostic Steps**: Compare coverage before and after the revision against the frozen baseline; identify which admission rule the excluded required unit was rejected by; confirm the rejection reason code.
- **Resolution Protocol**: Option A, revert the threshold increase and instead narrow the tool definitions and remove the specific units the ablation record named, since a targeted removal does not shrink coverage. Option B, exempt units satisfying a declared evidence requirement from the threshold, so the threshold governs discretionary admissions only. Option C, where the coverage loss is unavoidable at any threshold, accept the lower utilization and record that the task class is coverage-bound rather than distraction-bound.
- **Escalation Trigger**: Coverage falling more than 5 percentage points below the frozen baseline reverts the revision automatically and requires supervisor authorization to reapply.

**Troubleshooting Decision Tree**:

```
CONTEXT-ATTRIBUTED FAILURE OBSERVED
├─ NO DETECTOR FIRED
│   ├─ Fewer than 5 signals recorded → Instrumentation defect; halt task class
│   ├─ All 5 clear and output wrong → Not context-attributable; route out
│   └─ Signal near but below trigger → Recalibrate threshold against baseline
├─ ONE DETECTOR FIRED
│   ├─ Overflow → Enter umbrella ladder; verify protected atoms survived
│   ├─ Distraction → Reduce unit count or reposition; verify required unit cited
│   ├─ Contradiction → Restore qualifier or apply precedence; verify disclosure
│   ├─ Staleness → Evict and invalidate; verify by negative read
│   └─ Poisoning → Quarantine lineage; verify with detector disabled
├─ MULTIPLE DETECTORS FIRED
│   ├─ Poisoning among them → Contain first; re-detect before any other remedy
│   └─ Otherwise → Apply declared order; record the order taken
└─ REMEDY APPLIED AND FAILURE PERSISTS
    ├─ Signal cleared, output unchanged → Relocation; restore units, reopen
    ├─ Signal still fired, attempt 1 → Change strategy; attempt 2 permitted
    ├─ Signal still fired, attempt 2 → Abstain with typed reason
    └─ Third consecutive call fired → ESCALATE to named owner
```

### D. Performance Metrics and Continuous Learning

**Detection Metrics**:

- **Signal completeness**: Proportion of turns on which all 5 signals were computed (target: 1.00).
- **Detector recall against injected faults**: Proportion of injected faults whose intended detector fired before output or effect (target: at least 0.90 per blocking trigger).
- **Detector precision**: Proportion of fired verdicts confirmed as true failures on adjudication (target: at least 0.70; below 0.50 the trigger is demoted to warning).
- **Pre-call detection share**: Proportion of failures detected before the model call rather than after (target: at least 0.60, since overflow, contradiction, staleness, and poisoning are all pre-call detectable and only distraction is not).

**Remediation Metrics**:

- **Resolution rate**: Proportion of remedies whose signal returned within threshold and whose output changed as predicted (target: at least 0.90).
- **Relocation rate**: Proportion of remedies whose signal cleared without an output change (target: at most 0.10).
- **General-remedy misuse**: Count of distraction, contradiction, or staleness events remedied by summarisation (target: 0).
- **Containment independence**: Proportion of injected poisoning cases producing 0 unauthorized effects with the detector disabled (target: 1.00).

**Policy-Correction Metrics**:

- **Attribution completeness**: Proportion of fired detectors bound to an admission rule identifier (target: 1.00).
- **Recurrence rate**: Occurrences of the same mode on the same task class within a rolling 20-turn window (target: at most 3 before a revision is opened).
- **Coverage stability under revision**: Change in measured coverage after an admission-policy revision (target: no decrease greater than 5 percentage points).

**Learning and Adaptation Mechanisms**:

- **Threshold recalibration**: Recompute each trigger against its 20-turn rolling baseline on a fixed cadence, and never adjust a threshold to reduce alert volume without a corresponding precision measurement.
- **Injection suite growth**: Add every confirmed production failure to the injection suite as a minimized case, so that a mode which escaped once is proven caught thereafter.
- **Budget reallocation**: Apply the Step 1.3 reallocation rule to measured mode frequencies each review window, and record that the resulting shares are deployment defaults rather than findings.

***

## IV. Domain-Agnostic Application Guidance

The framework generalises because its five modes are properties of assembled content rather than of subject matter, and because every detection signal is computed from identifiers, timestamps, scope fields, and citation bindings that any domain can supply. What varies across domains is which mode dominates, which trigger must block rather than warn, and how much detection budget the consequence of a failure justifies.

### 4.1 Cross-Domain Application Patterns

**Clinical and care-delivery settings**: Staleness dominates, because a superseded medication list, allergy record, or result value is indistinguishable from a current one once both are prose in a window. The supersession ledger is the load-bearing artifact, the staleness trigger blocks rather than warns, and the scope tuple must carry valid-time and unit-of-measure fields, since a dose expressed in a different unit is a contradiction that surface comparison misses. Coverage may never be traded for utilization here, so the Step 6.2 revision rule operates with a 0-point coverage tolerance rather than 5.

**Financial services and regulated advice**: Contradiction dominates, because product terms, eligibility rules, and rate schedules are scoped by jurisdiction, tenure, and effective date, and each is individually consistent in its own store. The scope-qualifier retention check is the primary control, the precedence policy must be declared from the regulatory hierarchy rather than from source recency, and every precedence-resolved conflict must be disclosed in the output because an undisclosed resolution is a compliance defect independent of whether it was correct.

**Legal and cross-jurisdictional analysis**: Contradiction and staleness co-occur, since a superseded provision and a differently scoped provision present identically. The declared remedy ordering matters most here: staleness is remedied first so that superseded units leave the contradiction index before pairs are generated, which prevents an amended provision being adjudicated as a live conflict with its own successor.

**Industrial operations and field maintenance**: Overflow and staleness dominate, because telemetry and procedure documents are large and sensor observations expire quickly. The freshness predicate at admission carries most of the load, expiry intervals are set from the physical process rather than from a default, and the overflow projection must reserve for tool output whose size is not known until the tool returns.

**Software engineering agents**: Distraction dominates, because retrieval over a repository admits many topically similar files of which few are relevant, and tool registries grow until schemas crowd out working state. Position-conditioned utilization and tool-definition narrowing to plan-step-reachable tools carry the remedy, and the ablation record is the artifact that identifies which admitted files were never cited.

**Customer-facing support and knowledge assistance**: Poisoning dominates, because content arrives from tickets, uploaded documents, and third-party pages that no party controls. Containment rather than detection is the whole discipline: the isolation mechanism must be named in the contract, and consequential effects such as refunds, account changes, and outbound messages must be authorized against the principal's grants rather than against anything the content asserts.

### 4.2 Scale, Risk, and Latency Adaptation

**Low-risk, low-latency deployments**: Run all 5 signals in recording mode and operate only overflow and staleness as blocking triggers, since both are computable from arithmetic and timestamp comparison at negligible cost. Sample the utilization measurement at 1 turn in 10 rather than every turn, and defer contradiction adjudication to an asynchronous pass. Detection should consume at most 3 percent of per-call latency at this tier.

**High-consequence or irreversible-action deployments**: Operate all 5 triggers in blocking mode, run contradiction adjudication synchronously before any consequential tool call, and require the detector-disabled containment replay to pass before the task class is permitted to act at all. Detection may consume up to 20 percent of per-call latency, and abstention is preferred to any remedy attempt beyond the first where the action is irreversible.

**High-volume deployments**: Hold the per-call cost constant by computing every signal over structured fields rather than content, capping the contradiction index at 500 pairs and model adjudication at 25, and sampling ablation to a canary population rather than running it in the serving path. Baselines must be stratified by task class, model version, and tenant, because a single pooled baseline hides a regression confined to one stratum.

**Long-horizon and multi-turn deployments**: Recurrence counters, quarantine entries, and rolling baselines must survive every context boundary in the handoff record, since a boundary that resets them converts a persistent policy defect into an unending sequence of first occurrences. Verification must re-run at the horizon the deployment actually operates rather than at a short demonstration length, because failure composition shifts as horizon grows.

***

## V. Limitations and Considerations

**Utilization is a proxy for use, not a measurement of attention**: Citation binding records which units the model referenced in its output, which is not the same as which units influenced it. A unit can shape an answer without being cited, and a cited unit can be decorative. The consequence is that the distraction signal carries both false negatives and false positives, and a low utilization figure is evidence of a problem rather than proof of one. Mitigation is the two-part verification in Step 6.1, which requires an output change alongside the signal change, and the consumed-not-cited class, which removes non-citable units from the denominator before the ratio is computed.

**Every numeric threshold in this guide is a deployment default**: The 40 percent utilization floor, the 80 percent coverage comparison, the 20-turn baseline, the 500-pair index cap, the 25-pair adjudication cap, the 2-attempt remedy limit, the 3-occurrence recurrence rule, the 0.90 recall target, and the detection budget shares are operable on first deployment and are not measured findings from any evaluation. The consequence is that a deployment which adopts them without recalibration will over-trigger in some task classes and under-trigger in others. Mitigation is the recalibration procedure in Step 1.2, which requires 100 baseline turns before a trigger operates in blocking mode, and the reallocation rule in Step 1.3.

**Contradiction detection is bounded and structurally incomplete**: The contradiction index is keyed on shared entity and predicate and capped at 500 pairs, so a conflict expressed only in unstructured prose between units sharing no extractable key will not generate a candidate pair. The consequence is that the contradiction signal has a recall ceiling that no threshold adjustment raises. Mitigation is to route the highest-consequence task classes through a structured extraction step that produces keyed fields before assembly, accepting the extraction cost where the conflict cost justifies it, and to record contradiction recall as bounded rather than reporting a clear verdict as an absence of conflict.

**Detection machinery is subject to the failures it detects**: An adjudicating model call receives its own context window, and a large adjudication prompt suffers the same length-related degradation the framework exists to catch. The consequence is that scaling adjudication to more pairs reduces its reliability per pair. Mitigation is the 25-pair cap, deterministic comparison ahead of model adjudication so that the model sees only the irreducible residue, and inclusion of the adjudication path in the injection suite so that its own failure rate is measured rather than assumed.

**Injection detection is unreliable in principle and must never hold**: Every published instruction-shape control has been evaded by inputs constructed against it, and this guide assumes evasion rather than treating it as exceptional. The consequence is that any deployment whose safety depends on a detector firing is unbounded in its worst case. Mitigation is the containment architecture in Phase 5, in which a clean detector verdict grants no authority and the detector-disabled replay in Step 6.3 is the only accepted proof of containment.

**Position bands are a coarse surrogate for a mechanism no tool exposes**: Leading, middle, and trailing bands approximate position effects that arise inside the model's attention computation, which no runtime tool can read. The consequence is that a position-conditioned verdict identifies where content sat, not why it was underused, and repositioning may not help in tasks whose position sensitivity differs from the general pattern. Mitigation is to treat the positional remedy as a hypothesis validated by the same output-change test as every other remedy, and to withdraw it where repositioning clears the band statistic without changing the output.

**Mode co-presence weakens attribution**: Where three detectors fire on one call, the declared ordering determines which remedy is applied first and therefore which mode receives credit for the resolution. The consequence is that measured mode frequency is biased toward modes remedied early in the order. Mitigation is to record every fired detector and its terminal state rather than only the mode that resolved the failure, and to read frequency from fired-detector counts rather than from resolution counts.

**The framework does not diagnose non-context failures**: A wrong output caused by an unclear task specification, a defective tool, or a model limitation will produce five clear verdicts. The consequence is that agents may loop on context remedies for a failure context did not cause. Mitigation is the explicit route-out branch in the decision tree, which records a failure as not context-attributable when all five signals are clear, and the Error Type 2 resolution that withdraws a diagnosis rather than substituting another mode.

***

## VI. Conclusion and Summary

Context failure prevention is a measurement discipline before it is a remediation discipline. The failure that agents actually suffer is not that context grows too large but that five distinct pathologies are collapsed into one description, after which one remedy is applied to all of them. Summarisation resolves overflow. Against distraction it preserves the distractors in denser form; against contradiction it selects one side silently and destroys the record that a conflict existed; against staleness it blends the outdated value into a statement no freshness check can inspect; and against poisoning it carries the instruction forward in compressed form while removing the provenance that would have contained it. Each of those outcomes clears the symptom that prompted the remedy, which is why the practice persists.

The corrective is structural. Each mode receives an observable signal computable by software from the assembly record, a numeric trigger with a stated consequence, a remedy that is not summarisation, and a verification that distinguishes resolution from relocation. Three of the five modes are then eliminated at admission rather than detected after assembly, and the detection budget concentrates on the two that cannot be: distraction, whose defining quantity does not exist until the model has responded, and contradiction, which does not exist until two individually consistent records sit in one window under a scope tuple that no longer separates them.

Poisoning is governed by a different logic from the other four. It is contained rather than corrected, because content admitted to the window is data and never instruction, and because a detector's clean verdict grants no authority. The only accepted evidence of containment is that an injected instruction produces no unauthorized effect when the detector is switched off.

**Key Success Factors**:

- **Five modes, not one**: Detection begins by refusing the single description that produces the single remedy, and no diagnosis proceeds without a named mode and its evidencing unit identifiers.
- **Signals computed, never asserted**: Every trigger is evaluated by the deterministic tier from structured records, and a model opinion never overrides a fired detector.
- **Prevention where it is cheaper**: Overflow, staleness, and poisoning are eliminated by admission rules, leaving the detection budget for the two modes that admission cannot reach.
- **Containment above detection**: Authority is bounded in the tool-authorization layer, so that an undetected instruction is inert rather than merely unnoticed.
- **Verification against relocation**: A remedy is accepted only when the signal clears and the output changes, since a cleared signal alone is equally consistent with the failure having moved.
- **Correction of the rule, not the event**: Recurrence is attributed to the admission rule that produced it and answered with a measured policy revision rather than a fourth remedy.

Applied consistently, this framework converts context failure from a category diagnosed by impression after a user complains into a set of measured conditions detected before a call is issued, remedied by mode, and proved by injection.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, and were not independently re-verified during conversion except where an entry is marked as verified; those marked entries were retrieved during the research performed for this conversion. Where the prose source cited a work by a bare label, that label is reproduced rather than expanded into a full publication title.

**Corpus pointers**:

- `Context Failure Prevention: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the failure taxonomy, the causal-plane distinction, the cascade across reusable representations, the pre-flight validation checks, the detection techniques and their decision rules, the abstention and bounded-retry policy, the circuit-breaker semantics, the backward diagnostic procedure, the recovery patterns, the fault-injection loop, and the logging field inventory. It carries inline citations to primary literature on context failure, long-context degradation, positional effects, groundedness and contradiction evaluation, agent guardrails, and reliability engineering; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the umbrella guide for this category. Owner of the four-mode taxonomy adopted here, of the context budget partitioning referenced in Step 3.1, and of the selection ladder that the overflow remedy enters. This guide extends that taxonomy by one mode and owns detection and prevention in depth.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — companion guidance on bounded admission and candidate scoring, applicable to the admission-rule attribution and policy revision in Step 6.2.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — companion guidance on externalization and supersession control, applicable to the supersession ledger in Step 2.3 and the invalidation record in Step 4.2.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — companion guidance on compression and preservation manifests, applicable wherever the overflow remedy reaches the compression rung and to the refusal of compaction as a remedy for the other modes.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — companion guidance on isolation boundaries and sub-agent scoping, applicable to the containment controls in Phase 5.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — companion guidance on context boundaries and handoff, applicable to the survival of recurrence counters and quarantine entries across boundaries.
- `advanced_task_guides/context-management/guide_FilesystemAsContext.md` — companion guidance on externalized context stores, applicable to the durable location of assembly records and detection artifacts.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — source of the injection boundary that keeps admitted content data rather than instruction, of the named isolation mechanism and its components, and of the terminal-state discipline adopted in Step 4.3.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — source of the delayed-execution trust boundary, the quarantine semantics, and the containment measure requiring that an injected write be bounded by authorization with the detector disabled.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — source of the admission gate stages and of the treatment of instruction-bearing text as data, applicable to Step 5.1.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — companion guidance on expiry and supersession at the store level, applicable to the staleness prevention rule in Step 1.3.
- `advanced_task_guides/knowledge-retrieval/guide_CorrectiveRAG.md` — companion guidance on retrieval-quality correction, applicable where a distraction verdict is reclassified as a coverage failure in Step 3.2.

**External references**:

*Context failure taxonomy and long-context degradation*

1. Breunig — https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html
2. Chroma, *Context Rot: How Increasing Input Tokens Impacts LLM Performance* — https://www.trychroma.com/research/context-rot (title verified during conversion)
3. Liu and colleagues, *Lost in the Middle* — https://arxiv.org/abs/2307.03172
4. *The Long-Horizon Task Mirage* — https://arxiv.org/html/2604.11978v1 (verified during conversion)
5. Cemri and colleagues, *MAST* — https://arxiv.org/abs/2503.13657

*Groundedness, contradiction, and self-consistency evaluation*

6. RAGChecker — https://arxiv.org/abs/2408.08067
7. Chen and colleagues, *RefNLI* — https://aclanthology.org/2025.findings-naacl.450/
8. SelfCheckGPT — https://arxiv.org/abs/2303.08896

*Adversarial context, guardrails, and containment*

9. OWASP GenAI Security Project — https://owasp.org/www-project-top-10-for-large-language-model-applications/
10. OWASP Gen AI Security Project, *LLM01:2025 Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/ (retrieved during conversion)
11. *Design Patterns for Securing LLM Agents against Prompt Injections* — https://arxiv.org/abs/2506.08837 (retrieved during conversion)
12. OpenAI guardrails and human review — https://developers.openai.com/api/docs/guides/agents/guardrails-approvals
13. OpenAI practical guide — https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf

*Context engineering and reliability practice*

14. Anthropic, context-engineering guidance for AI agents — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
15. Microsoft Azure Architecture Center, circuit-breaker pattern — https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
16. Google SRE, error-budget policy — https://sre.google/workbook/error-budget-policy/
