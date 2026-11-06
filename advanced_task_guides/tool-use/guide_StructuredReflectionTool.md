# Structured Reflection Tool

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Structured reflection tool use constitutes the task family of exposing self-assessment as an explicit, schema-constrained tool an agent invokes, rather than leaving it implicit in generated prose. This guide provides AI agents with a structured protocol for declaring a typed reflection contract, binding its invocation to orchestrator-controlled triggers, validating the returned record before any component reads it, and consuming the resulting verdict under a deterministic gate that the verdict alone can never satisfy. It specifies the closed vocabularies for verdicts, defect classes, severities, and proposed actions; the cross-field invariants under which an unparseable or out-of-vocabulary record is rejected rather than salvaged; a per-run invocation budget with a recorded skip decision; a bounded reflect-revise-reverify loop terminated by no-improvement and anti-oscillation rules; an escalation path for verdicts carrying no admissible action; and a metric set measuring whether reflection changes outcomes at all. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that a reflection call earns its cost rather than decorating a decision already made.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Structured reflection tool**: A declared, versioned, non-side-effecting tool an agent invokes to obtain a typed assessment of a named subject. It is defined by its contract, not by its transport: the same contract may compile to a provider tool schema, a structured-output response format, or a sub-agent call.

**Reflection record**: The complete typed object returned by one invocation, carrying identity, subject reference, trigger, verdict, defects, evidence references, coverage, confidence, proposed action, stop decision, and provenance. A record missing any decision-relevant field is rejected, not repaired by inference.

**Reflection verdict**: One value drawn from a closed vocabulary summarising the record's conclusion. It is a proposal from the model tier and never an authorization.

**Subject**: The artifact the reflection assesses, drawn from a closed set: plan, tool result, proposed action, draft answer, code patch, retrieval set, or final candidate. Every record names exactly one subject.

**Subject digest**: The content hash binding a record to the exact bytes it assessed. A record whose subject digest does not match the current candidate is stale and is discarded rather than reused.

**Trigger class**: The declared reason an invocation occurred, drawn from a closed set: mandatory policy gate, verifier failure, low calibrated confidence, tool error, anomaly, plan checkpoint, pre-action, pre-release, sampled audit, or human request. Every invocation records exactly one.

**Defect**: One identified fault in the subject, carrying an identifier, a defect class, a severity class, an affected span reference, a requirement identifier, at least one evidence reference or an explicit unsupported marker, and a proposed correction.

**Defect class**: The category of a defect, drawn from a closed vocabulary of eighteen entries listed in Step 1.1. A class outside the vocabulary is a validation failure, not a novel finding.

**Severity class**: The blocking weight of a defect, drawn from critical, high, medium, low, or informational. Critical blocks unconditionally; informational never forces a revision by itself.

**Evidence reference**: A pointer to an artifact outside the reflection, carrying an identifier, a producing verifier, an immutable location, a content digest, a creation time, and a source class. A reference that does not resolve invalidates the defect that cites it.

**Evidence level**: The strength tier of an evidence reference. Level 0 is an introspective assertion citing no external observation. Level 1 is a referenced observation naming a resolvable artifact whose interpretation may still be wrong. Level 2 is an independently verified fact confirmed by a trusted verifier such as a passing test, a policy-engine decision, an exact-state comparison, or a human decision.

**Source class**: The provenance label attached to every signal and every evidence reference, drawn from a closed set: same model, independent model, deterministic test, primary source, environment, or human. The term is adopted from the corpus's monitoring guidance and carries the same meaning here.

**External signal**: A signal whose value could not have been produced by the object layer, because it originates in a deterministic check, a retrieved primary source, an environment response, an independent model family, or a human. Externality is a property of provenance, not of confidence.

**Coverage record**: The enumeration of requirement identifiers checked, requirement identifiers not checked, and a reason for each omission. A pass verdict carrying an unchecked critical requirement is invalid regardless of its other contents.

**Proposed action**: The single next step the record recommends, drawn from a closed set of nine entries listed in Step 1.1. A record whose proposed action is absent, or whose proposed action is not admissible under current policy and budget, is recorded as an escalation rather than as a note.

**Admissible action**: A proposed action that the orchestrator's current policy, authority, and budget state permit. Admissibility is computed deterministically before the action is read, not argued for by the record.

**Stop decision**: The record's continue-or-stop flag, its machine-checkable stop reason, its iteration index, and the remaining budget it observed. It informs the controller and does not bind it.

**Deterministic gate**: The software barrier between a verdict and a consequential action, comprising required verifier states, evidence freshness, authorization, approval, budget, and policy. A model-generated pass never satisfies it.

**Change hypothesis**: The declaration accompanying every revision, naming the targeted defect identifiers, the intended change, the verifier expected to move, and the protected invariants that must not regress. A revision without one is refused.

**Best verified candidate**: The highest-scoring candidate that passed every mandatory verifier, retained separately from the most recent candidate. Runs terminate by returning this artifact, never the last one produced.

**Oscillation signature**: The canonical fingerprint of a defect set and revision diff, used to detect repeated states, content reversion, and alternating verdicts across iterations.

**Null-effect reflection**: An invocation whose verdict changed no decision, produced no revision, and closed no defect. A tool whose null-effect share exceeds the threshold in Step 6.3 is pure overhead and is retuned or retired.

**Reflection log**: The append-only record carrying one entry per invocation, per validation outcome, per consumed verdict, and per resulting transition, correlated by trace, task, candidate, and revision identifiers. Every metric in Phase 6 is computable from it without re-derivation.

**Invocation budget**: The per-run numeric ceiling on reflection calls, revision cycles, evidence rounds, escalation levels, tokens, wall time, and cost. Exhaustion is a declared exit, not an error.

### 1.2 Why the Tool Boundary Changes the Properties of Reflection

Self-assessment expressed as generated prose and self-assessment expressed as a tool call describe the same cognitive act, and they are not the same engineering object. Making reflection a declared tool changes four properties, and those four properties are why this guide sits in the tool-use family rather than among the reasoning patterns.

**The output is typed and validated rather than free text**: A reflection returned as prose must be parsed by a reader, and every reader parses it differently. A reflection returned against a declared schema arrives as fields with closed vocabularies, so a validator decides whether the record is usable before any component interprets it. The distinction is load-bearing because a reflection tool returning free text has given up its main advantage and retains only its cost.

**The invocation is logged and countable**: Prose self-assessment has no invocation boundary, so it cannot be counted, budgeted, sampled, or suppressed. A tool call has one call site, one identifier, and one entry in the reflection log, which makes the questions in Phase 6 answerable: how often reflection ran, on which triggers, and how often its verdict changed anything.

**The cost is attributable**: Tokens spent inside a generated answer cannot be separated from the answer. Tokens spent inside a declared call can. Attributable cost is the precondition for the marginal-value comparison in Step 6.2, and without it a deployment cannot establish whether reflection is worth its overhead against the alternatives of no reflection, deterministic verification alone, or a stronger producer model.

**A controller can gate on the result**: A typed verdict drawn from a closed vocabulary is machine-comparable, so a state machine can branch on it deterministically. Prose cannot be branched on without a second model call to classify it, which reintroduces the untyped problem one layer up.

**Origin and the contract gap**: The pattern originates in a no-op tool placed in the model-visible tool schema and called mid-trajectory between a tool result and the next action, creating a checkpoint for policy review and constraint checking in long tool-call chains. In its original form the schema carried one required string field, which is a model-visible scratchpad and not a typed quality contract: it defines no defect classes, no evidence references, no machine-enforceable verdicts, no required next action, and no stop decision. The provider reported that a think tool with an optimized domain prompt reached 0.570 pass^1 on the tau-bench airline domain against 0.370 for the stated baseline, and 0.812 against 0.783 in the retail domain for the tool alone, and later added a December 2025 note recommending improved extended thinking instead of a dedicated think tool in most cases [1]. Those figures were confirmed against the cited page during this conversion. They are provider-reported results for one model, one scaffold, one benchmark, and one period, and they establish that a mid-trajectory checkpoint can help, not that a scratchpad string is a production contract. This guide keeps the placement and replaces the scratchpad with a typed record.

**The self-assessment limit, carried over and not re-argued**: A model assessing its own output shares the blind spots that produced it. Prompting a model to reconsider without new information can leave performance unchanged or degrade it [2], and reflection-specific capability remains limited, particularly in meta-reflection, across evaluated models and prompting strategies [3]. The operational consequence is fixed and applies to every phase below: a reflection verdict is a proposal and never a verification. Adding a schema to a self-assessment improves its handling and does not improve its epistemic standing.

**What a verdict may and may not gate**: A verdict may gate reversible, internally scoped work: whether to spend one more revision cycle, which defect to target next, whether to request a named piece of evidence, whether to route to an independent capability, and whether to stop early on a low-risk task. A verdict may never, alone, release a final answer to a user in a regulated or high-impact context, authorize an irreversible or externally visible action, waive a policy decision, substitute for a deterministic verifier that exists, or certify that an artifact is correct. Every consequential decision requires at least one external signal at Level 2 for each critical invariant, and Level 0 confidence never compensates for missing verification.

**Boundary against neighbouring corpus guides**: The corpus splits this territory across three guides, and the split is deliberate.

- **Metacognitive monitoring** owns monitoring signals, their computable definitions, and the calibration procedure, including the finding that a model's stated confidence tracks fluency more than accuracy. This guide consumes a calibration profile and does not re-derive one; a confidence value arriving without a current profile is advisory only.
- **Meta-reasoning** owns the control loop that consumes typed signals and issues transitions such as continue, verify, repair, switch, branch, escalate, and stop. This guide hands a validated verdict to that loop and does not duplicate its transition semantics.
- **Tool use and function calling** owns the general contract, authorization, and validation machinery for any tool. This guide specialises that machinery for one tool whose subject is the agent's own work.

***

### 1.3 The Execution Tier Partition

Reflection divides across three execution tiers, and the division is the difference between a governed assessment and a model narrating its own approval. Every artifact below has exactly one owning tier.

**Deterministic tier**: Software, scripts, schema validators, policy engines, and APIs own schema validation, closed-vocabulary enforcement, cross-field invariant checking, evidence-reference resolution and digest matching, invocation counting and budget enforcement, the gate evaluation, the loop-termination rules, and the reflection log. These require exactness, reproducibility, and auditability that inference cannot supply: two validators reading the same record must return the same verdict on its admissibility, and a gate decision must be reconstructible from the log years later. The deterministic tier rejects rather than repairs any record that fails to parse, carries a value outside a declared vocabulary, violates a cross-field invariant, cites an evidence reference that does not resolve or whose digest does not match, or arrives under a schema version that is not registered.

**Model tier**: Inference owns only the content of the assessment: identifying which defects are present in the subject, classifying each into the declared vocabulary, writing the concise description and the proposed correction, selecting the verdict and the proposed action from their closed sets, and reporting a confidence value against the declared event. In every case the model tier proposes and never decides. Its output enters the record as typed values carrying a source class of same model or independent model, is subject to the same validation as any other tool result, and acquires authority over a consequential decision only through an external signal that the model did not produce.

**Hybrid tier**: The model proposes and software verifies, or software retrieves and the model adjudicates. Authority is fixed in advance and does not depend on the content of the disagreement: where a deterministic verifier and a reflection verdict conflict, the verifier holds, and the disagreement is recorded as a reflection event rather than resolved by re-invoking the tool. Where two model judgements conflict and no deterministic check exists, neither wins; the case routes to escalation and the disagreement is recorded as unresolved.

**Tier Ownership of Reflection Artifacts**:

| Reflection artifact | Owning tier | Deterministic tier rejects | Model tier may never decide alone |
| :-- | :-- | :-- | :-- |
| Tool contract and schema registration | Deterministic | Contracts missing any mandatory field or version digest | Any contract element |
| Trigger evaluation and gate placement | Deterministic | Invocations with no recorded trigger class | Whether an invocation is required |
| Observation packet assembly | Deterministic | Packets carrying secrets, prior verdicts, or producer identity under blinding | Packet contents or bounds |
| Defect identification and classification | Model | Classes outside the declared vocabulary | Whether a defect blocks |
| Verdict and proposed action selection | Model | Values outside the closed vocabularies | Whether the action executes |
| Record schema and invariant validation | Deterministic | Unparseable records and invariant violations | Any admissibility outcome |
| Evidence reference resolution | Deterministic | References that do not resolve or whose digests mismatch | Whether evidence is sufficient |
| Confidence value and its profile binding | Hybrid | Confidence with no current calibration profile | Whether confidence crosses a threshold |
| Gate evaluation for a consequential action | Deterministic | Gates satisfied by a verdict alone | Any gate outcome |
| Revision adoption or rollback | Hybrid | Adoptions with no change hypothesis or re-verification | Whether a revision is adopted |
| Loop termination and escalation routing | Deterministic | Continuations past a declared budget ceiling | Whether the loop continues |
| Reflection log and metric computation | Deterministic | Entries lacking trace, subject digest, or trigger fields | Any logged value or metric |

**A reflection verdict never authorizes a consequential action on its own**: This is the partition's controlling rule. The model tier may report that authorization appears present, that every test appears to pass, or that a policy appears satisfied; only the authorization service, the test runner, and the policy engine may decide. Where a reflection record attempts to set an approval, authorization, consent, or policy field, the deterministic tier strips the field, records a contract violation, and treats the record as an escalation.

### 1.4 The Invocation Gate: When a Reflection Call Is Warranted

Reflection costs a call, and reflecting after every step is expensive and often uninformative. Agents must run a cheap deterministic gate, bounded to 1 percent of the direct-execution budget, returning invoke, suppress, or a named lighter substitute. The gate is evaluated by the orchestrator and is never delegated to the model whose work is under assessment.

**Invocation conditions**: Invoke where at least one of the following holds: the next step is irreversible, externally visible, privileged, costly, or difficult to undo; a long tool chain has produced information that changes constraints or invalidates the plan; a mandatory verifier has failed and its output must be interpreted before repair; the task carries material safety, legal, financial, security, or operational cost; an intermediate result carries low calibrated confidence, conflicting evidence, missing required fields, or anomalous tool behaviour; a plan checkpoint requires an explicit continue, replan, or escalate decision; a candidate must satisfy a rubric, citation requirement, or policy before release; or the deployment requires a machine-queryable record of what was checked and why a transition occurred.

**Suppression conditions**: Suppress where a deterministic verifier decides the question outright through a schema, type checker, unit test, solver, signature, constraint, or postcondition, and run the verifier instead. Suppress where the next action is read-only and a mistake carries negligible cost. Suppress where no verification signal exists, because reflection would restate the same uncertain belief in a typed wrapper. Suppress where latency dominates and paired evaluation shows no material quality gain. Suppress where the candidate is already objectively correct and the expected regression risk of revision exceeds the expected benefit.

**Rejection conditions**: Reject reflection outright, rather than suppressing it pending later use, where no admissible action would follow any verdict, because a record that cannot change a revision, an evidence request, a route, or a stop adds ceremony without control. Reject it where the record would require retaining reasoning content or data that policy forbids. Reject it where a pass would be consumed as a compliance certification, a security approval, or evidence that hidden reasoning was faithful, none of which a reflection record can supply.

**Invocation Gate Decision Table**:

| Observable condition | Available control lever | Gate verdict |
| :-- | :-- | :-- |
| Irreversible or externally visible action pending | Deterministic gate plus approval path | Invoke; verdict is advisory within the gate |
| Mandatory verifier failed with a diagnosable output | Bounded revision cycle | Invoke; target the named defect |
| Long tool chain changed constraints | Replan path available | Invoke at the plan checkpoint |
| Pre-release candidate under a rubric or citation rule | Revision or escalation | Invoke; require Level 2 evidence per critical claim |
| Deterministic verifier fully decides correctness | Verifier | Suppress; run the verifier |
| Read-only next action, negligible impact | Not applicable | Suppress; proceed and log the skip |
| Strict latency budget, no measured quality gain | Existing checks | Suppress; log the policy reason |
| No verification signal of any kind obtainable | None | Suppress; record the missing signal |
| No admissible action would follow any verdict | None | Reject; remove the call site |

**Numeric gate rules**: Invoke only where at least 1 invocation condition holds and at least 1 admissible action exists that the verdict could select. Where fewer than 2 distinct proposed actions are admissible under current policy and budget, suppress and record the reason, because the record would have no branch to take. Where estimated reflection overhead exceeds 20 percent of the direct-execution budget and the task sits in the lowest risk tier, suppress and record the estimate for the next policy revision. Where the gate suppresses, name the substitute rather than proceeding unassessed: a deterministic verifier, a retrieval-and-entailment check, an existing calibrated threshold, or a stronger producer model. Every suppression writes a skip entry to the reflection log carrying the trigger that was evaluated, the rule that fired, and the substitute named, so that skipped cases remain countable and samplable.

***

## II. Operational Framework: Typed Self-Assessment Under Bounded Invocation and External Gating

The framework assumes the invocation gate has returned invoke for at least one call site in the run. Phases 1 and 2 are declaration work performed once per deployment and re-performed on any contract change. Phases 3 through 5 execute per invocation and form a bounded loop: Phase 4 either releases control to the workflow or returns to Phase 3 with a revised candidate, and Phase 5 terminates any path that Phase 4 cannot close. Phase 6 runs alongside the loop and completes before a deployment is promoted.

### Phase 1: Reflection Tool Contract Declaration

**Objective**: Fix the typed record, its closed vocabularies, and its cross-field invariants before any invocation occurs, so that an unusable response is rejected by a validator rather than interpreted by a reader.

#### Step 1.1: Declare the Typed Record Fields and Their Closed Vocabularies

**Required Actions**:

- Declare 15 mandatory field groups: identity, subject, trigger, applicable requirements, verdict, defects, evidence, coverage, confidence, uncertainty, proposed action, stop decision, change hypothesis, summary, and provenance.
- Populate identity with a reflection identifier, schema version, trace identifier, span identifier, task identifier, attempt identifier, candidate identifier, parent reflection identifier, and trigger event identifier, so that every record joins to exactly one trace and one subject.
- Bind the subject group to one subject type from the closed set of 7 entries and one content-addressed subject digest, and forbid a record naming more than one subject.
- Declare the verdict vocabulary as exactly 7 entries and forbid a generic boolean, because uncertainty and missing evidence are operationally distinct from failure.
- Declare the defect vocabulary as exactly 18 entries: factual error, logical error, unsupported claim, citation mismatch, requirement omission, policy violation, authorization missing, security risk, privacy risk, schema error, tool error, stale data, test failure, inconsistency, ambiguity, unsafe side effect, cost or budget risk, and unknown.
- Declare the severity vocabulary as exactly 5 entries with written organisational definitions, and state that critical blocks unconditionally while informational never forces a revision alone.
- Declare the proposed-action vocabulary as exactly 9 entries and require target identifiers and bounded parameters wherever the action names an object.
- Cap every array and string: at most 25 defects per record, at most 10 evidence references per defect, and at most 1,200 characters of free-text summary across the whole record.
- Forbid free-text fields from carrying decision weight, and state that a validator reads only typed fields.

**Verdict Vocabulary and Its Blocking Weight**:

| Verdict | Meaning | May gate alone | Required accompaniment |
| :-- | :-- | :-- | :-- |
| Pass | No unresolved blocking defect found | Reversible internal steps only | Complete coverage record with zero unchecked critical requirements |
| Pass with warnings | Non-blocking findings under a documented acceptance rule | Reversible internal steps only | A named risk-acceptance rule identifier per warning |
| Revise | At least one actionable defect with a permitted repair | Never | At least 1 defect, a target candidate, a change hypothesis, and a verifier to rerun |
| Gather evidence | A named invariant cannot be judged on current evidence | Never | The missing evidence identifiers and a permitted retrieval or verification action |
| Escalate | Judgement requires a capability the reflector lacks | Never | A destination class and an escalation reason code |
| Block | Policy, security, authorization, or unrecoverable correctness failure | Never; the policy engine decides | The blocking defect identifiers at critical severity |
| Abstain | The subject cannot be evaluated with available evidence | Never | An abstention reason from the closed set |

**Proposed-Action Vocabulary and Admissibility**:

| Proposed action | Consumed by | Admissibility precondition |
| :-- | :-- | :-- |
| Continue | Deterministic gate | Every mandatory verifier passing and budget remaining |
| Revise candidate | Revision loop | Change hypothesis present and revision budget remaining |
| Rerun verifier | Verifier adapter | Named verifier registered and not rate limited |
| Gather specific evidence | Evidence service | Named evidence obtainable within the evidence-round budget |
| Replan | Control layer | Replanning permitted at the current workflow state |
| Call stronger critic | Escalation router | Escalation level below the declared ceiling |
| Request human review | Review queue | Queue capacity available and the case within retention policy |
| Rollback | Revision store | A best verified candidate exists to restore |
| Terminate | Control layer | A declared exit condition applies |

**Required Outputs**:

- A reflection record schema declaring all 15 field groups with types, ranges, and required flags.
- Four closed vocabularies covering verdicts, defect classes, severity classes, and proposed actions, each with a written definition per entry.
- A size-limit table stating the array and string cap for every unbounded field.

**Quality Checkpoints**:

- Every decision-relevant field is required rather than optional; no verdict, action, or severity is inferable from free text.
- Every vocabulary is closed and enumerated; no entry is defined as other or miscellaneous except the single declared unknown defect class.
- No field permits the reflector to set an approval, authorization, consent, policy, or verifier-result value.
- Every array and string carries a numeric cap, so a record cannot exhaust the consuming context.

***

#### Step 1.2: Declare the Cross-Field Invariants and the Rejection Rule

**Required Actions**:

- Declare the invariants that types alone cannot enforce, beginning with the 7 verdict invariants stated in the vocabulary table above.
- Require that a pass or pass-with-warnings verdict carries zero unresolved defects at critical or high severity, zero unchecked critical requirements, and a passing state for every configured mandatory verifier.
- Require that a revise verdict names at least 1 defect, a target candidate identifier, a change hypothesis, and the verifier expected to move.
- Require that every defect at critical or high severity carries at least 1 evidence reference at Level 1 or Level 2, and that a defect carrying only Level 0 assertions is marked unsupported and cannot block.
- Require that every evidence reference resolves and that its content digest matches the stored artifact before the record is consumed.
- Require that the record's subject digest matches the digest of the current candidate, and reject any record bound to an earlier revision.
- Make abstain mandatory where the reflector cannot evaluate the subject with available evidence, and forbid coercion of an unevaluable subject into a pass or a block.
- State the rejection rule without exception: a record that fails to parse, carries a value outside a declared vocabulary, violates any invariant, or cites an unresolvable reference is rejected, and no component reads any part of it.
- Forbid salvage by inference: prohibit regex extraction, nearest-vocabulary-match repair, default substitution for a missing field, and any second model call whose purpose is to interpret a malformed record.
- Permit exactly 1 schema-repair attempt in which the validation errors are returned to the reflector, and forbid counting a successful format repair as evidence that the verdict is correct.

**Required Outputs**:

- An invariant catalogue with one entry per rule, its triggering fields, and its rejection message.
- A rejection policy stating the disposition of every failure class and naming the single permitted repair attempt.
- A validator specification implementable by two independent teams to identical results.

**Quality Checkpoints**:

- Every invariant is checkable from the record and its referenced artifacts alone, with no model call required.
- No rejection path leads to partial consumption; a rejected record contributes nothing but a log entry and a counter increment.
- The repair budget is exactly 1 attempt, after which the invocation resolves to abstain and routes to escalation.
- Out-of-vocabulary values are rejected rather than mapped, so a novel label never enters the log as a recognised class.

***

#### Step 1.3: Register, Version, and Compile the Contract

**Required Actions**:

- Register the contract under a stable name with a semantic version, an owner, a status, a risk tier, and an immutable digest covering the schema, the vocabularies, the prompt, and the tool description.
- Record the allowed models, the allowed placements, and the trigger classes the contract is registered for, and reject an invocation from any placement not listed.
- Compile the canonical internal record to each target provider surface, whether a tool schema, a structured-output response format, or a sub-agent contract, and reject a target that cannot preserve the closed vocabularies, the evidence identifiers, the refusal path, the schema version, or a mandatory approval pause.
- Version vocabularies and their semantics explicitly, and forbid silent redefinition of an existing entry, above all the meaning of pass.
- Restrict changes within a major version to additive, backward-compatible edits, and require a major version increment for any removal, narrowing, or semantic change.
- Validate every stored record against the schema version recorded at its creation, and migrate into a derived view rather than rewriting history.
- Declare the tool non-side-effecting and forbid it from invoking itself, from calling any tool that mutates state, and from appearing in its own observation packet.

**Required Outputs**:

- A registry entry carrying name, version, owner, status, risk tier, allowed models, allowed placements, trigger classes, and digest.
- A compilation record per target surface stating which contract elements were preserved and which the surface cannot express.
- A version policy distinguishing additive changes from breaking changes, with the migration rule for stored records.

**Quality Checkpoints**:

- The registered digest reproduces the exact schema, vocabularies, prompt, and description in use at every invocation.
- No compiled target silently drops a closed vocabulary, an evidence identifier, or the refusal path; a target that cannot carry them is rejected rather than degraded.
- The tool's declared side-effect class is read-only, and no registered placement permits it to reach a state-mutating capability.
- Every stored record names the schema version it was validated against, and no historical record has been rewritten to a later version.

***

### Phase 2: Invocation Policy and Budget Declaration

**Objective**: Fix when the tool is called, how often it may be called, and who decides, so that reflection is placed where a verdict can change something rather than distributed evenly across a trajectory.

#### Step 2.1: Declare Mandatory, Adaptive, and Prohibited Trigger Conditions

**Required Actions**:

- Partition every call site into exactly one of 3 policies: mandatory, adaptive, or prohibited, and record the rule that assigned it.
- Declare mandatory triggers for the highest-value placements only: before an irreversible or externally visible action, before a final release under a rubric or citation requirement, after a mandatory verifier failure, and at a declared plan checkpoint where dependencies or constraints have changed.
- Declare adaptive triggers with numeric activation conditions: calibrated confidence below the task-class routing threshold, 2 or more trusted signals in conflict, an anomaly or out-of-distribution score above its declared bound, 2 consecutive tool errors of the same error class, or a sampling rate for audit.
- Set the audit sampling rate at 1 to 5 percent of otherwise-skipped call sites, so suppressed cases retain a measurable false-skip estimate.
- Declare prohibited placements explicitly: after every trivial read, inside the reflection tool's own execution, at any point where the record could reach a state-mutating capability, and at any site where no proposed action would be admissible.
- Forbid reflection after every step as a default policy, and require a paired evaluation before any deployment raises a call site from adaptive to mandatory.
- Bind each trigger to the trigger-class vocabulary from Step 1.1, so that every invocation logs exactly 1 machine-comparable reason.
- State the anti-recursion rule: a reflection record may never trigger another reflection on the same subject digest without an intervening revision or new evidence artifact.

**Required Outputs**:

- A trigger inventory listing every call site, its policy, its activation condition, and its trigger class.
- A prohibited-placement list naming each excluded site and the rule that excluded it.
- A sampling policy stating the audit rate and the population it samples from.

**Quality Checkpoints**:

- Every call site carries exactly 1 policy assignment; an unassigned site is a contract defect and blocks deployment.
- Every adaptive trigger names a numeric activation condition rather than a qualitative judgement.
- No mandatory trigger exists at a site where the deterministic gate would decide the same question without the record.
- The anti-recursion rule is enforced by the orchestrator and is not stated only in the prompt.

***

#### Step 2.2: Set the Per-Run Invocation Budget and the Skip Record

**Required Actions**:

- Set a per-run ceiling on reflection calls, defaulting to 3 for ordinary tasks and 6 for high-value tasks with strong deterministic verification, and require task-class evaluation evidence before any higher ceiling.
- Set separate ceilings on revision cycles, defaulting to 2 for ordinary tasks and 3 for high-value strongly verifiable tasks, on evidence-gathering rounds at 2, and on automated escalation levels at 2.
- Set token, wall-time, and monetary ceilings for the reflection subsystem separately from the task budget, so reflection overhead is measurable rather than absorbed.
- Reserve at least 25 percent of the total run budget for final verification and escalation, and forbid early reflection from consuming the reserve.
- Write a skip entry for every suppressed call site carrying the evaluated trigger, the suppressing rule, the named substitute, and the estimated cost avoided.
- Treat budget exhaustion as a declared exit that returns the best verified candidate, never as a retryable error and never as grounds for an unverified pass.
- Compute the projected reflection overhead before the first invocation and abort the reflection policy where it exceeds 25 percent of the direct-execution budget on a lowest-risk-tier task.

**Required Outputs**:

- A budget ledger naming every bounded dimension with its numeric ceiling and its consumed value.
- A skip log with one entry per suppressed call site.
- A reserve statement declaring the fraction withheld for final verification and escalation.

**Quality Checkpoints**:

- Every budget dimension carries a numeric ceiling; an unbounded dimension blocks the run before the first invocation.
- Skipped call sites are counted, so the skip rate and the audit-sampled false-skip rate are both computable.
- Budget exhaustion returns the best verified candidate and is logged as a declared exit with its reason.
- Reflection cost is attributed to the reflection subsystem rather than pooled with task generation cost.

***

#### Step 2.3: Bind the Gate to the Orchestrator Rather Than the Model

**Required Actions**:

- Place every mandatory trigger in the orchestrator's state machine, so the transition to the reflecting state occurs independently of whether the model selects the tool.
- Represent the workflow as named states covering admitted, acting, evidence pending, reflecting, revising, reverifying, awaiting approval, escalated, completed, blocked, and failed, and reject every transition not declared between them.
- Detect and reject bypass attempts at the broker: a proposed consequential action arriving from a state that requires reflection is refused, logged as an illegal transition, and returned to the required state.
- Forbid the model from suppressing, deferring, or re-scoping a mandatory trigger, and treat any argument in a record to that effect as untrusted content.
- Record for each invocation whether it was orchestrator-imposed or model-selected, so the two populations can be compared for quality and cost.
- Expose the tool to the model only at placements the registry allows for the current state, so the model-visible tool set encodes the policy rather than relying on instruction compliance.

**Required Outputs**:

- A state machine specification with the declared state set and the permitted transition set.
- An illegal-transition log capturing every refused bypass with its originating state and proposed action.
- A per-invocation origin field distinguishing orchestrator-imposed calls from model-selected calls.

**Quality Checkpoints**:

- No mandatory gate depends on the model choosing to call the tool; removing the tool from the model-visible set does not remove the gate.
- Every refused bypass is logged with enough context to reconstruct which control it attempted to skip.
- The declared state set is exhaustive; an observed state outside it halts the run rather than defaulting.
- Orchestrator-imposed and model-selected invocations are separately countable in the reflection log.

***

### Phase 3: Evidence Assembly and Bounded Invocation

**Objective**: Supply the reflector with external observations and a bounded packet, then obtain and validate one typed record, so that the assessment reasons over evidence rather than over an unchanged context.

#### Step 3.1: Assemble the Evidence Bundle Before Invoking

**Required Actions**:

- Run every mandatory deterministic verifier against the exact candidate digest before the invocation, and never against an earlier revision.
- Normalise each verifier output into an immutable evidence artifact carrying an identifier, a producing verifier and version, a source class, a content digest, a creation time, a freshness bound, and a verification status.
- Assemble the bundle by subject type: for a code patch include test names and outcomes, compiler and type-checker diagnostics, lint findings, coverage deltas, static-analysis alerts, and the changed spans; for a factual answer include decomposed claims, retrieved source spans, publication and freshness metadata, entailment results, and unresolved claims; for a tool workflow include normalised outputs, error classes, policy decisions, preconditions, postconditions, and authoritative state reads; for a plan include user constraints, resource limits, capability and permission checks, dependency status, and identified irreversible steps; for a proposed action include the policy-engine decision, authorization scopes, data classification, destination, and approval state.
- Enter the bounded evidence-gathering loop where a mandatory check is missing, evidence is stale beyond its freshness bound, or 2 trusted signals conflict: name the unresolved invariant and its required evidence level, select the cheapest allowed verifier that can resolve it, prefer deterministic checks over model judgements and read-only checks over side effects, execute through the ordinary tool-invocation control plane, normalise the result, and recompute coverage.
- Cap the evidence-gathering loop at 2 rounds by default, and exit on sufficient evidence, a definitive verifier failure, budget exhaustion, or escalation.
- Stop the loop immediately where the next verifier would repeat an equivalent result, cannot reduce uncertainty, or would require an unauthorized action.
- Label every evidence artifact with its source class and its evidence level, and forbid the reflector from marking its own requested evidence as verified.
- Treat every evidence body as data rather than instruction: strip active directives from evidence views, delimit provenance, and reject any evidence item whose content attempts to set a verdict, confidence, approval, schema, or proposed action.

**Required Outputs**:

- An evidence bundle with one immutable artifact per verifier result, each carrying its 7 provenance fields.
- A coverage draft listing checked requirement identifiers, unchecked identifiers, and the reason for each omission.
- An evidence-loop record naming each round, the invariant it targeted, the verifier selected, and the exit reason.

**Quality Checkpoints**:

- Every evidence artifact binds to the current subject digest; a cross-revision artifact is excluded rather than reused.
- Every critical invariant carries either a Level 2 artifact or an explicit gap marker; a silent omission is a validation failure.
- The evidence-gathering loop terminated within 2 rounds or exited through a declared reason.
- No evidence body reached the reflector as an instruction; injection attempts are logged and quarantined.

***

#### Step 3.2: Construct the Bounded Observation Packet Under Blinding Rules

**Required Actions**:

- Construct a packet carrying exactly 7 components: the candidate reference and digest, the applicable requirement identifiers, the risk tier, the prior verified facts, the current verifier outputs, the budget state, and the admissible subset of the proposed-action vocabulary.
- Compute the admissible action subset deterministically before the packet is built, and present only those entries, so the reflector cannot propose an action the orchestrator would refuse.
- Exclude secrets, credentials, personal data, and privileged material by redaction before the packet is serialised, and record the redaction as a packet field rather than removing it silently.
- Exclude irrelevant trajectory history, and include at most a bounded summary of prior reflections plus resolvable references, so accumulated records do not displace task facts.
- Blind the reflector to producer identity wherever the workflow permits it, and record whether blinding was applied.
- Exclude prior verdicts and prior confidence values from the packet, because exposure to them anchors the assessment and manufactures agreement that is social rather than evidential.
- Cap the packet at a declared token bound and truncate evidence bodies to referenced spans rather than dropping evidence items, so coverage stays complete when the bound binds.
- Record the packet digest, so the record can be reproduced and the invocation replayed.

**Required Outputs**:

- One observation packet per invocation with its 7 components and its content digest.
- A redaction record naming each removed class and the field it occupied.
- A blinding record stating whether producer identity, prior verdicts, and prior confidence were withheld.

**Quality Checkpoints**:

- The packet contains no proposed action outside the admissible subset computed by the orchestrator.
- No secret, credential, or privileged item appears in the packet or in any telemetry derived from it.
- Prior verdicts and prior confidence values are absent unless a documented requirement records why they were needed.
- The packet digest is recorded and the invocation is reproducible from it.

***

#### Step 3.3: Invoke the Tool and Validate the Returned Record

**Required Actions**:

- Invoke the registered tool with the packet, recording the invocation identifier, the trigger class, the origin field, the schema version, the prompt version, the model snapshot, and the sampling configuration.
- Set low stochasticity where the provider supports it, and record the setting without claiming deterministic semantics, because provider updates, distributed execution, and tool data can change results.
- Store the raw provider envelope separately from the normalised record, so a parsing defect is distinguishable from a content defect.
- Validate in a fixed order: syntax, schema conformance, closed-vocabulary membership, size caps, cross-field invariants, evidence-reference resolution and digest match, subject-digest match, and refusal detection.
- Reject on the first failure and record the failing check by name, rather than accumulating a list and consuming the record anyway.
- Allow exactly 1 schema-repair attempt returning the validation errors to the reflector, and resolve the invocation to abstain where the repair also fails.
- Strip and log any approval, authorization, consent, policy, or verifier-result field the record attempted to set, and mark the record as a contract violation.
- Bind the reported confidence to a current calibration profile identifier; where no current profile exists for the bundle, mark the confidence advisory and forbid it from crossing any routing threshold.
- Increment the invocation counter and charge the call against the budget ledger before any downstream component reads the record.

**Required Outputs**:

- One normalised reflection record, or one rejection entry naming the failing check.
- A raw provider envelope stored under the invocation identifier.
- A validation trace listing each check in order with its outcome and duration.

**Quality Checkpoints**:

- No component consumed any part of a rejected record; the rejection produced a counter increment and a log entry only.
- Exactly 1 repair attempt was permitted, and a successful repair was not recorded as evidence about the verdict's correctness.
- Every confidence value is either bound to a current calibration profile or marked advisory.
- The invocation was charged to the budget ledger before the verdict was read.

***

### Phase 4: Verdict Consumption Under a Deterministic Gate

**Objective**: Combine a validated verdict with independent verifier state and policy to select exactly one transition, so that the record informs the decision without ever constituting it.

#### Step 4.1: Evaluate the Deterministic Gate Independently of the Verdict

**Required Actions**:

- Evaluate the gate from verifier state, evidence freshness, authorization, approval, budget, and policy alone, and compute its outcome before the verdict is read, so the gate result cannot be influenced by the record.
- Require, for any consequential action, that every mandatory verifier passes, that every critical invariant carries current Level 2 evidence, that authorization and approval are valid for the exact destination, that no blocking defect remains open, and that budget and policy permit the action.
- Treat the verdict as one input among several, and record the gate outcome and the verdict outcome as separate fields so their agreement rate is measurable.
- Where the gate refuses and the verdict passes, refuse the action and record a pass-against-gate disagreement; never resolve the conflict by re-invoking the tool.
- Where the gate permits and the verdict blocks or escalates, halt the action and route to Phase 5, because a stop proposal is honoured even where the gate would have allowed the step.
- Restrict what a verdict may gate alone to reversible, internally scoped decisions: which defect to target, whether to spend one further revision cycle, whether to request a named evidence item, whether to route to an independent capability, and whether to stop early on a lowest-risk-tier task.
- Forbid a verdict from alone releasing a final answer in a regulated or high-impact context, authorizing an irreversible or externally visible action, waiving a policy decision, substituting for an available deterministic verifier, or certifying correctness.
- Permit a conditional gate for lower-risk tasks in which a calibrated pass above a task-class threshold skips a second critic, only where every deterministic check passes and the skipped population is sampled online at the audit rate from Step 2.1.
- Derive every threshold from held-out data and an explicit loss trade-off across false pass, false block, escalation, latency, and review cost, and forbid a single global threshold across risk tiers.

**Required Outputs**:

- A gate evaluation record listing each gate input, its measured state, and the composite outcome.
- A transition record naming the single selected transition, its trigger, and the rule that selected it.
- A disagreement record for every case where the gate outcome and the verdict diverge.

**Quality Checkpoints**:

- The gate outcome is computed and logged before the verdict is read; a gate that reads the record first is a control defect that halts the run.
- No consequential action proceeded on a verdict alone; every such action carries a complete gate record.
- Exactly 1 transition was selected; zero or multiple transitions halt the run rather than defaulting to continue.
- Every threshold in use names the held-out dataset and loss trade-off that produced it.

***

#### Step 4.2: Execute the Admissible Action and Record the Change Hypothesis

**Required Actions**:

- Recompute admissibility at execution time rather than trusting the subset computed at packet construction, because budget and policy state may have moved.
- Record any verdict whose proposed action has become inadmissible as an escalation rather than as a note, and route it to Phase 5.
- Save the pre-revision candidate as the rollback baseline before any revision begins, and preserve the best verified candidate separately from the most recent one.
- Select 1 defect or 1 coherent group of defects per revision, and forbid rewriting unrelated content that no defect names.
- Record the change hypothesis before generating the revision: the targeted defect identifiers, the intended change, the verifier expected to move, the direction it should move, and the protected invariants that must not regress.
- Produce the revision as a child candidate with a new candidate identifier, an exact diff, and a parent link, and never overwrite the parent.
- Rerun every verifier the change could affect plus the regression checks covering the protected invariants, and adopt the revision only where every blocking check passes and the predefined improvement delta is met.
- Roll back automatically where the child fails any check the parent passed, and record the rollback with the failing check.
- Link every actionable defect to either a revision that targeted it or an explicit recorded disposition, so a critique that changed nothing is visible rather than absorbed.

**Required Outputs**:

- A change hypothesis record per revision with its 5 declared fields.
- A parent-child candidate pair with an exact diff and comparable objective scores.
- A defect disposition table linking every actionable defect to a revision or a recorded acceptance.

**Quality Checkpoints**:

- No revision proceeded without a change hypothesis; a revision request lacking one is refused rather than inferred.
- Every adopted revision passed the protected-invariant regression set, and every failed child was rolled back automatically.
- Diff scope is contained within the spans the targeted defects name; an over-broad diff is rejected and regenerated once.
- Every actionable defect carries a disposition, so the null-effect share in Step 6.3 is computable.

***

#### Step 4.3: Enforce the No-Improvement and Anti-Oscillation Rules

**Required Actions**:

- Compute a canonical defect signature and a revision-diff fingerprint after every cycle, so repeated states are detectable without comparing prose.
- Stop the loop where the objective score fails to improve by the declared minimum meaningful delta across 2 consecutive revisions, where the same defect signature recurs twice, or where a revision reverts a change made in the previous 2 iterations without new evidence.
- Stop the loop where states repeat, where an A-to-B-to-A content reversion occurs, or where verdicts alternate between the same 2 values without a new evidence artifact entering the bundle.
- Forbid re-invocation on an unchanged subject digest with an unchanged evidence bundle, because the same model over the same context has no new information to apply.
- Forbid re-invocation whose only purpose is to obtain a more favourable verdict, and detect it as a repeat invocation whose packet digest matches a prior packet digest.
- Charge every cycle against the revision ceiling from Step 2.2 and terminate at exhaustion rather than requesting an extension.
- Return the best verified candidate on every exit path, and never return the most recent candidate merely because it is the most recent.
- Record the loop exit reason from a closed set: verified pass, no improvement, repeated defect signature, oscillation detected, budget exhausted, escalation, or safe fallback.

**Required Outputs**:

- A per-cycle record carrying the defect signature, the diff fingerprint, the objective score, and the adoption decision.
- A loop exit record naming the reason from the closed set and the returned candidate identifier.
- A repeat-invocation counter distinguishing legitimate re-invocations from packet-digest repeats.

**Quality Checkpoints**:

- The loop terminated within the declared revision ceiling on 100 percent of runs; an unbounded loop is a control defect, not a cost overrun.
- No invocation ran against an unchanged subject digest and an unchanged evidence bundle.
- The returned artifact is the best verified candidate, and the record states how it compares with the most recent one.
- Every exit reason is drawn from the closed set; a free-text exit reason is rejected.

***

### Phase 5: Escalation on Unresolvable Verdicts

**Objective**: Route every verdict that no admissible action can close to an independent capability or a human, so that an unresolvable assessment terminates in an accountable decision rather than in a note nobody consumes.

#### Step 5.1: Detect the Unresolvable Verdict Conditions

**Required Actions**:

- Declare the 7 unresolvable conditions: the record verdict is abstain; the record verdict is escalate; a critical defect persists across the revision ceiling; 2 trusted signals conflict and no verifier can adjudicate; calibrated confidence sits below the task-class routing threshold; the proposed action is inadmissible under current policy, authority, or budget; or the record was rejected twice by validation.
- Detect each condition deterministically from the record, the gate state, and the budget ledger, and never by asking the model whether escalation is warranted.
- Record an inadmissible proposed action as an escalation rather than as a note, and name both the proposed action and the specific precondition that failed.
- Distinguish an abstention from a failure in the outcome record, so an honest abstention is not scored as a task failure and abstention precision remains measurable.
- Preserve the current best verified candidate and the complete evidence bundle at the moment of detection, so the escalation carries the state that produced it.
- Forbid retry after a policy block or a deterministic invalidity, because neither class is resolvable by repetition.

**Required Outputs**:

- An escalation trigger record naming the condition, its measured values, and the detection rule.
- A preserved state package carrying the best verified candidate, the diff history, the defect set, the evidence bundle, and the policy results.
- An abstention record distinguishing unevaluable subjects from failed subjects.

**Quality Checkpoints**:

- Every escalation names exactly 1 triggering condition from the declared set of 7.
- No escalation decision was delegated to the model whose record triggered it.
- The preserved package is sufficient to reconstruct the decision without re-running the task.
- Abstentions are separated from failures in every metric that reports task success.

***

#### Step 5.2: Route Through Bounded Independent Capability

**Required Actions**:

- Escalate first to the least costly independent capability that addresses the specific failure: a specialised deterministic checker, a differently prompted and blinded critic, a different model family, a domain tool, or retrieval of a primary source.
- Establish independence by provenance rather than by call count: 2 invocations of the same base model under the same prompt family share a training lineage and produce correlated errors, so their agreement is recorded as correlated failure and never as confirmation.
- Blind every escalated critic to producer identity, prior verdicts, and prior confidence, and record whether blinding was achievable.
- Reverify any proposed correction with the original objective checks rather than with the escalated capability's own assessment.
- Cap automated escalation at 2 levels by default, and forbid bouncing between models beyond that cap.
- Create a human-review item at the cap or wherever policy requires accountable judgement, carrying the candidate, the diff, the defect set, the evidence bundle, the policy results, and the recommended options.
- Type the human-review request with an assignment target, a service-level target, an expiry, and a resume token, so a stalled review terminates rather than blocking indefinitely.
- Record a stronger model's higher confidence without better evidence as an unsuccessful escalation, because confidence is not the quantity the escalation was raised to obtain.

**Required Outputs**:

- An escalation ladder record naming each level, the capability invoked, its source class, and its outcome.
- An independence assessment stating whether each escalated signal was external and why.
- A typed human-review request with its assignment, expiry, and resume token where the ladder reached its cap.

**Quality Checkpoints**:

- Every escalated capability carries a source class, and no same-model agreement was counted as independent confirmation.
- Automated escalation stopped at 2 levels; a third automated level is a control defect that routes to human review instead.
- Every human-review request carries an expiry, and expired requests resolve to a declared safe fallback.
- No escalation was recorded as successful on the basis of confidence alone.

***

#### Step 5.3: Terminate Through a Declared Exit and Capture the Outcome

**Required Actions**:

- Terminate only through a declared exit: verified pass, accepted partial result, safe fallback, human decision, rollback to the best verified candidate, budget exhaustion, or terminal block.
- Re-read authoritative state immediately before any irreversible action, confirm evidence freshness against its declared bound, validate idempotency and destination, obtain required approval, and rerun policy, so a stale gate is not executed against a changed world.
- Execute every side effect through the ordinary tool-invocation control plane, and never from the reflection subsystem.
- Verify, before releasing a final answer, required coverage, factual support, citation entailment and freshness, policy, privacy, and output schema.
- Withhold raw reasoning content and internal reflection records from any released artifact unless a reviewed product requirement permits a sanitised assessment summary.
- Record the final artifact, the environment state, the human or user outcome, grader results, incidents, rollbacks, and delayed ground truth, and join each to every reflection and revision in the trace.
- Create a memory candidate only from a reflection whose defect and repair were externally validated, store it with applicability conditions, counterexamples, an owner, and an expiry, and never promote a raw record to a global instruction.
- Update calibration inputs only after the declared ground-truth rule is satisfied, and never on the strength of a verdict alone.

**Required Outputs**:

- An outcome record naming the exit condition, the returned candidate, and the join keys to every reflection in the trace.
- A pre-action revalidation record for every irreversible action, listing the 5 refreshed checks.
- A memory candidate set containing only externally validated defect-repair pairs with their applicability conditions.

**Quality Checkpoints**:

- Every run terminated through 1 of the 7 declared exits; an undeclared termination is a control defect.
- Every irreversible action carries a revalidation record timestamped after the last gate evaluation.
- No released artifact carries raw reasoning content or an unsanitised reflection record.
- No memory candidate exists whose defect and repair lack external validation.

***

### Phase 6: Reflection Log and Outcome Measurement

**Objective**: Instrument the tool so that its invocation rate, its verdict quality, and its effect on outcomes are computable from the log, and retire the tool where the measurement shows it changes nothing.

#### Step 6.1: Maintain the Reflection Log With Correlation Rules

**Required Actions**:

- Write one append-only entry per invocation, per validation outcome, per consumed verdict, per revision, per escalation, and per skipped call site.
- Carry the 9 identity fields on every entry: trace identifier, task identifier, attempt identifier, candidate identifier, subject digest, reflection identifier, trigger event identifier, schema version, and bundle identifier.
- Bind every reflection entry to exactly 1 subject digest and exactly 1 trigger event, and reject an entry that names more than one of either.
- Link every defect to its evidence references or mark it explicitly Level 0, and link every revision to the defect identifiers it targeted and to its parent and child candidates.
- Bind every verifier result to the exact candidate digest it ran against, and join every final outcome back to every reflection in the trace.
- Forbid correlation by timestamp alone, because concurrent traces and retried attempts produce spurious joins.
- Record decision metadata and prohibit hidden reasoning content: log verdicts, defect classes, severities, evidence identifiers, coverage lists, confidence values, calibration profile identifiers, proposed actions, transition outcomes, token counts, latencies, and costs, and do not request or persist private chain-of-thought from any component.
- Replace raw sensitive payloads with content digests and governed references, and apply redaction before the entry is written rather than at query time.
- Retain the raw provider envelope under access control and separately from the normalised entry, so a parsing investigation does not require broad log access.

**Reflection Log Entry Template**:

```
ENTRY_TYPE:            invocation | validation | consumption | revision | escalation | skip
TRACE_ID:
TASK_ID:
ATTEMPT_ID:
CANDIDATE_ID:
SUBJECT_DIGEST:
REFLECTION_ID:
TRIGGER_EVENT_ID:
TRIGGER_CLASS:
INVOCATION_ORIGIN:     orchestrator_imposed | model_selected
SCHEMA_VERSION:
BUNDLE_ID:
PACKET_DIGEST:
VERDICT:
DEFECT_IDS:
DEFECT_CLASSES:
SEVERITIES:
EVIDENCE_IDS:
EVIDENCE_LEVELS:
CHECKED_REQUIREMENT_IDS:
UNCHECKED_REQUIREMENT_IDS:
CONFIDENCE:
CALIBRATION_PROFILE_ID:
PROPOSED_ACTION:
ACTION_ADMISSIBLE:
GATE_OUTCOME:
TRANSITION_SELECTED:
DEFECT_DISPOSITIONS:
LOOP_EXIT_REASON:
VALIDATION_OUTCOME:
REJECTED_CHECK_NAME:
INPUT_TOKENS:
OUTPUT_TOKENS:
LATENCY_MS:
COST:
OUTCOME_JOIN_KEY:
```

**Required Outputs**:

- An append-only reflection log with one entry per event type and the 9 identity fields on every entry.
- A correlation specification stating the join keys between reflections, revisions, verifier results, and outcomes.
- A disclosure record confirming that no hidden reasoning content and no raw sensitive payload was persisted.

**Quality Checkpoints**:

- Every metric in Step 6.2 is computable from the log without re-running any task or re-deriving any value.
- Every entry carries all 9 identity fields; an entry missing one is rejected at write time rather than backfilled.
- No log entry carries private chain-of-thought, a raw credential, or an unredacted sensitive payload.
- Skipped call sites appear in the log, so the denominator for skip-rate and false-skip metrics is complete.

***

#### Step 6.2: Compute the Reflection-Value Metric Set

**Required Actions**:

- Compute schema-valid rate as reflection outputs passing syntax and semantic validation on the first attempt divided by all invocations, and treat a declining rate as a contract or model-version defect.
- Compute critical-defect recall as adjudicated critical defects detected divided by all adjudicated critical defects, reported separately from overall recall, because a high aggregate recall can hide a missed blocking defect.
- Compute false-pass rate as pass verdicts whose subject ultimately failed divided by all pass verdicts with mature ground truth, and false-block rate as block or revise verdicts on ground-truth-correct subjects divided by all ground-truth-correct subjects.
- Compute the pass-success gap as reflection pass rate minus actual task success rate on the same mature cohort, and treat a large positive gap as evidence of self-congratulatory passing.
- Compute revision improvement rate as adopted revisions improving the objective score by at least the declared delta divided by all attempted revisions, and regression-from-revision rate as revisions failing a protected invariant or reducing the score beyond tolerance divided by all attempted revisions.
- Compute defect closure rate as defects verified resolved divided by defects targeted by an adopted revision.
- Compute evidence-grounded defect rate as detected defects carrying at least 1 resolving Level 1 or Level 2 reference divided by all detected defects, and critical evidence coverage as critical requirements carrying current Level 2 evidence divided by all applicable critical requirements.
- Compute reflection token overhead, latency overhead, and cost overhead against a matched no-reflection baseline, and report cost per successful task with and without reflection using randomised or matched cohorts.
- Declare for every metric the cohort, task class, model and prompt version, ground-truth maturity window, sample count, and confidence interval, and never pool incomparable regimes into one figure.
- Delegate confidence calibration measurement and threshold fitting to the corpus's monitoring guidance rather than re-deriving them here, and consume the resulting profile identifier as an input.

**Required Outputs**:

- A metric report carrying the 14 named measures with their declared cohorts and sample counts.
- A paired-baseline comparison against no reflection, deterministic verification alone, and a stronger producer model.
- A cost-per-successful-task figure computed on matched cohorts rather than per-call cost.

**Quality Checkpoints**:

- Every metric names its cohort, sample count, and maturity window; an unqualified aggregate is rejected.
- Critical-defect recall is reported separately from aggregate recall in every report.
- Cost is reported per successful task, not per call, so a cheap call producing no successes is visible as expensive.
- No calibration measure is computed here that the monitoring guidance already defines; the profile identifier is consumed rather than recomputed.

***

#### Step 6.3: Detect Null-Effect Reflection and Retune or Retire

**Required Actions**:

- Compute the null-effect share as invocations whose verdict changed no transition, produced no revision, and closed no defect divided by all valid invocations.
- Compute the reflection theater rate as actionable records followed by neither a linked corrective action nor an explicit recorded disposition divided by all actionable records.
- Treat a null-effect share above 70 percent at a call site as evidence that the site is pure overhead, and either retune its trigger to a narrower condition or remove it.
- Treat a null-effect share above 90 percent across every call site as grounds for retiring the tool for that task class, and record the retirement with its measurement.
- Treat a reflection theater rate above 10 percent as a consumption defect rather than a reflector defect, and repair the transition rules that discard actionable output.
- Detect confidence inflation as reported confidence rising across iterations without a corresponding accuracy change or a new evidence artifact, and disallow any threshold crossing produced only by repeated self-assessment.
- Detect judge optimisation as divergence between the reflector's score and deterministic, human, or delayed outcome scores, and stop optimising against any single static rubric.
- Detect context bloat as reflection tokens rising as a share of task tokens while quality by iteration declines, and enforce the packet bound from Step 3.2 rather than raising it.
- Compare the audit-sampled skipped population against the invoked population at least once per release, so a suppression rule that hides real defects is detectable.
- Re-run the full measurement on every change to the model, prompt, schema, trigger policy, defect taxonomy, verifier set, or promoted memory lesson, and roll back on regression.

**Required Outputs**:

- A per-call-site null-effect report with the retune or retire decision recorded against each site.
- A detector report covering theater, confidence inflation, judge optimisation, and context bloat with their measured values.
- A skipped-population comparison stating the estimated false-skip rate and its sample size.

**Quality Checkpoints**:

- Every call site whose null-effect share exceeds 70 percent has a recorded retune or retire decision.
- Reflection theater above 10 percent triggers repair of the consumption path rather than a change to the reflector prompt.
- Confidence increases unaccompanied by new evidence never move a case across a routing threshold.
- The measurement is re-run on every bundle change, and no configuration is promoted on unchanged-bundle evidence.

***

## III. Implementation Guidance for AI Agents

AI agents operating a structured reflection tool must follow systematic protocols ensuring that every record is validated before it is read, every invocation is counted against a budget, and every consequential action is authorised outside the record. The following guidance translates the tool contract into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Registrar**: Owns the schema, the 4 closed vocabularies, the invariant catalogue, and the version policy. It alone may register or retire a contract version, and every registration carries an immutable digest.
2. **Trigger Controller**: Evaluates the invocation gate, assigns the trigger class, imposes mandatory gates from the state machine, and writes the skip entry for every suppressed site. It never delegates a gate decision to the reflector.
3. **Evidence Service**: Runs verifiers against the current candidate digest, normalises outputs into immutable artifacts, assigns source classes and evidence levels, enforces freshness, and refuses to let any model mutate an artifact.
4. **Reflection Broker**: Builds the bounded observation packet, computes the admissible action subset, applies redaction and blinding, invokes the tool, and runs the ordered validation sequence. It is the only path to the tool.
5. **Gate Evaluator**: Computes the deterministic gate from verifier state, evidence freshness, authorization, approval, budget, and policy before the verdict is read, and selects exactly 1 transition per consumption event.
6. **Revision Manager**: Holds the rollback baseline and the best verified candidate, enforces the change hypothesis requirement, computes defect signatures and diff fingerprints, and applies the no-improvement and anti-oscillation rules.
7. **Instrumentation Agent**: Writes the append-only reflection log, enforces the disclosure boundary, computes the metric set, and may withhold a metric report where a disclosure breach is detected.

**Reasoning Disclosure Boundary**: The instrumentation protocol permits decision metadata and prohibits hidden reasoning content, and this constraint binds every component above.

- Log verdicts, defect classes, severities, evidence identifiers, coverage lists, confidence values, calibration profile identifiers, proposed actions, transition outcomes, token counts, latencies, and costs.
- Do not require, request, or persist private chain-of-thought from any model or component; the contract requires concise typed conclusions and resolvable references, not unrestricted internal transcripts.
- Do not store raw sensitive payloads where a content digest or a governed reference suffices.
- Where a component cannot justify a decision without exposing hidden reasoning, record the decision as unjustified and escalate rather than relaxing the boundary.

**Workflow Execution Pattern**:

```
STATE: Reflection_Consumption
INPUTS:
  1. Normalised reflection record from Step 3.3
  2. Evidence bundle with source classes from Step 3.1
  3. Gate evaluation record from Step 4.1
  4. Budget ledger from Step 2.2
ACTIONS:
  1. Confirm record passed all ordered validation checks
  2. Recompute admissible action subset from current policy and budget
  3. Read verdict and proposed action from typed fields only
  4. Select exactly one transition from gate outcome and verdict
VALIDATION:
  - record_validation_outcome == PASSED
  - verdict IN closed_vocabulary
  - proposed_action IN closed_vocabulary
  - subject_digest == current_candidate_digest
  - evidence_references_resolved == TRUE
  - gate_outcome_computed_before_verdict_read == TRUE
  - transition_count == 1
  - reasoning_trace_persisted == FALSE
TRANSITIONS:
  IF verdict IN {PASS, PASS_WITH_WARNINGS} AND gate_outcome == PERMIT
     THEN next_state = Execute_Or_Release
  IF verdict == REVISE AND revision_budget_remaining > 0
     THEN next_state = Revision_Cycle
  IF verdict == GATHER_EVIDENCE AND evidence_rounds_remaining > 0
     THEN next_state = Evidence_Gathering
  IF verdict IN {ESCALATE, ABSTAIN, BLOCK} OR action_admissible == FALSE
     THEN next_state = Escalation_Ladder
  IF validation_failed THEN next_state = Record_Rejection_Handling
```

**Two-Phase Action Pattern**: Emit the intended transition with its trigger, its gate inputs, and its budget charge without executing it; confirm it against the validation block while no resource is committed; commit it only after validation passes, writing the consumption entry in the same operation.

**Approval Gate**: Human authorisation is required before any transition executing an irreversible or externally visible action, before any release in the highest risk tier lacking Level 2 evidence for every critical invariant, before raising a per-run invocation ceiling above 6, and before promoting any reflection-derived lesson into durable procedural memory. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the contract registry, the budget ledger, the evidence bundle, and the candidate history in durable state, since a run may outlive a single context window.
- Keep immutable artifacts out of the active prompt, and carry a bounded summary plus resolvable references instead of the full reflection history.
- Write a handoff record naming the contract version, the consumed budget, the best verified candidate, the open defect set, and the next trigger at every context boundary.
- Count the reflection subsystem's own context consumption toward overhead rather than treating it as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Completeness (After Phase 1)**

- **Automated Check**: All 15 field groups are declared and required; all 4 vocabularies are closed and enumerated at 7, 18, 5, and 9 entries; every array and string carries a numeric cap; no field permits an approval, authorization, consent, or policy value; the registry entry carries an immutable digest.
- **Agent Action on Pass**: Proceed to invocation policy declaration.
- **Agent Action on Failure**: Halt and return the missing element; no invocation occurs against an incomplete contract.
- **Human Review Trigger**: Any request to add an open-vocabulary field, or any target surface that cannot preserve a closed vocabulary.

**Checkpoint 2: Invocation Policy Integrity (After Phase 2)**

- **Automated Check**: Every call site carries exactly 1 policy assignment; every adaptive trigger names a numeric activation condition; every budget dimension carries a numeric ceiling; the reserve for final verification is at least 25 percent; the state machine rejects every undeclared transition.
- **Agent Action on Pass**: Proceed to evidence assembly.
- **Agent Action on Failure**: Halt and return the unassigned site or unbounded dimension.
- **Human Review Trigger**: A per-run invocation ceiling above 6, or a projected reflection overhead above 25 percent of the direct-execution budget.

**Checkpoint 3: Record Admissibility (After Phase 3)**

- **Automated Check**: The record parsed; every value sits inside its declared vocabulary; every cross-field invariant holds; every evidence reference resolves with a matching digest; the subject digest equals the current candidate digest; at most 1 repair attempt was consumed.
- **Agent Action on Pass**: Release the record to the gate evaluator.
- **Agent Action on Failure**: Reject the record whole, increment the rejection counter, and resolve the invocation to abstain after the single permitted repair.
- **Human Review Trigger**: A schema-valid rate below 90 percent across 20 consecutive invocations on one bundle.

**Checkpoint 4: Gate Independence (After Phase 4)**

- **Automated Check**: The gate outcome was computed and logged before the verdict was read; exactly 1 transition was selected; no consequential action proceeded on a verdict alone; every revision carries a change hypothesis and a re-verification result; the loop terminated within its declared ceiling.
- **Agent Action on Pass**: Proceed to the selected transition or to termination.
- **Agent Action on Failure**: Halt the run; an action authorised by a verdict is never executed with a warning attached.
- **Human Review Trigger**: Any gate-versus-verdict disagreement on an irreversible action, or 3 consecutive revisions with no adopted improvement.

**Checkpoint 5: Escalation Completeness (After Phase 5)**

- **Automated Check**: Every escalation names exactly 1 condition from the declared set of 7; the preserved package carries candidate, diff, defects, evidence, and policy results; automated escalation stopped at 2 levels; every human-review request carries an expiry and a resume token; the run terminated through 1 of the 7 declared exits.
- **Agent Action on Pass**: Release the outcome record and close the run.
- **Agent Action on Failure**: Reclassify the termination as a bounded failure and report the missing element.
- **Human Review Trigger**: Any inadmissible proposed action recorded on a highest-risk-tier task, or any expired human-review request resolved by fallback.

**Checkpoint 6: Measurement Sufficiency (After Phase 6)**

- **Automated Check**: All 9 identity fields present on 100 percent of log entries; no disclosure breach; every metric names its cohort, sample count, and maturity window; critical-defect recall reported separately; the null-effect share computed per call site.
- **Agent Action on Pass**: Release the metric report and permit promotion of the bundle.
- **Agent Action on Failure**: Withhold the report and name the missing field; no bundle is promoted on incomplete instrumentation.
- **Human Review Trigger**: A null-effect share above 90 percent across all call sites, a false-pass rate above the declared release threshold, or any disclosure breach.

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

**Error Type 1: Record Rejection Loop**

- **Symptoms**: Repeated validation failures on the same bundle; out-of-vocabulary values in the verdict, defect class, or action fields; arrays exceeding declared caps; unresolved evidence references.
- **Diagnostic Steps**: Separate syntax failures from semantic failures using the ordered validation trace; determine whether the failing check is new since the last contract or model version change; confirm the compiled target still preserves the closed vocabularies.
- **Resolution Protocol**: Option A, return the validation errors once and accept the repaired record if it validates. Option B, recompile the contract to the target surface and confirm vocabulary preservation. Option C, pin the prior model snapshot and re-run the measurement before accepting the new one. Option D, resolve the invocation to abstain and route to escalation.
- **Escalation Trigger**: A second rejection on the same invocation resolves to abstain; a schema-valid rate below 90 percent across 20 consecutive invocations suspends the bundle.

**Error Type 2: Self-Congratulatory Pass**

- **Symptoms**: A high pass rate alongside a materially lower task success rate on the same mature cohort; passes carrying only Level 0 evidence; unchecked critical requirements inside a pass; confidence rising across iterations without new evidence.
- **Diagnostic Steps**: Compute the pass-success gap on the mature cohort, segment it by task class and bundle, and check whether the producer identity was visible to the reflector.
- **Resolution Protocol**: Option A, enforce the coverage invariant so a pass with any unchecked critical requirement is rejected outright. Option B, require Level 2 evidence per critical invariant before a pass may gate anything. Option C, blind the reflector to producer identity and re-measure. Option D, route a sample of passes to a blinded independent capability and compare.
- **Escalation Trigger**: A pass-success gap above 15 percentage points on a mature cohort suspends verdict-based gating for that task class until re-measurement.

**Error Type 3: Null-Effect Reflection**

- **Symptoms**: Verdicts that change no transition; actionable defects with no linked revision and no recorded disposition; identical verdicts across every invocation at one call site; reflection cost rising with flat outcome metrics.
- **Diagnostic Steps**: Compute the null-effect share and the reflection theater rate per call site; determine whether the cause is a reflector producing no actionable output or a consumption path discarding it.
- **Resolution Protocol**: Option A, repair the transition rules where the theater rate exceeds 10 percent, because the defect is in consumption rather than in the reflector. Option B, narrow the trigger condition at the site where the null-effect share exceeds 70 percent. Option C, retire the call site and record the measurement that justified it. Option D, retire the tool for the task class where the share exceeds 90 percent across all sites.
- **Escalation Trigger**: A null-effect share above 90 percent across all call sites blocks promotion of the configuration; this class is never resolved by raising the invocation ceiling.

**Error Type 4: Revision Regression and Oscillation**

- **Symptoms**: A child candidate failing a check the parent passed; the same defect signature recurring; A-to-B-to-A content reversion; verdicts alternating between the same 2 values; rising iteration count with an unchanged evidence bundle.
- **Diagnostic Steps**: Compare parent and child objective scores and protected-invariant results; recompute the defect signature and diff fingerprint; confirm whether any new evidence artifact entered the bundle between cycles.
- **Resolution Protocol**: Option A, roll back to the best verified candidate automatically and record the failing check. Option B, narrow the revision to the named defect spans where the diff scope exceeded them. Option C, stop the loop under the no-improvement rule and escalate with the diff history. Option D, freeze revision and route to an independent capability.
- **Escalation Trigger**: 2 consecutive revisions without the minimum meaningful improvement stop the loop; a repeated defect signature or a detected oscillation escalates immediately and is never resolved by a further cycle.

**Error Type 5: Injected or Hallucinated Evidence**

- **Symptoms**: Evidence identifiers that do not resolve; digests that do not match; cited test names, policy clauses, or source spans that do not exist; evidence bodies containing directives such as an instruction to mark a subject as passing.
- **Diagnostic Steps**: Resolve every reference and compare digests; trace each artifact to its producing verifier and source class; scan evidence bodies for directive content before they enter the packet.
- **Resolution Protocol**: Option A, reject the record whole, because an unresolved reference invalidates the defect that cites it. Option B, quarantine the offending artifact and re-run the verifier that should have produced it. Option C, strip directive content at the packet boundary and record an injection attempt. Option D, escalate where the injected content targeted an approval, authorization, or policy field.
- **Escalation Trigger**: Any evidence body attempting to set a verdict, confidence, approval, or action is a security event that halts the transition and escalates; it is never resolved by re-invoking the tool.

**Error Type 6: Gate Bypass and Illegal Transition**

- **Symptoms**: A consequential action proposed from a state requiring reflection; a mandatory trigger with no corresponding invocation entry; a verdict consumed before the gate outcome was computed; an approval field present in a normalised record.
- **Diagnostic Steps**: Replay the illegal-transition log against the declared state set; confirm whether the gate is imposed by the state machine or only stated in the prompt; check whether the tool was exposed at a placement the registry does not allow.
- **Resolution Protocol**: Option A, refuse the action, return control to the required state, and log the attempt. Option B, move the gate from the prompt into the orchestrator where instruction compliance was the only control. Option C, restrict the model-visible tool set so the placement policy is structural rather than advisory. Option D, halt the run where the bypass reached a state-mutating capability.
- **Escalation Trigger**: Any bypass that reached a side effect halts the deployment pending review; retry after a policy block is prohibited in every case.

**Troubleshooting Decision Tree**:

```
REFLECTION CALL PRODUCES A PROBLEM
├─ RECORD DEFECT
│   ├─ Fails to parse or out-of-vocabulary value → Reject whole; one repair, then abstain
│   ├─ Cross-field invariant violated → Reject whole; never salvage by inference
│   └─ Subject digest mismatch → Discard as stale; re-run verifiers on current candidate
├─ EVIDENCE DEFECT
│   ├─ Reference unresolved or digest mismatch → Invalidate the citing defect; reject record
│   ├─ Evidence body carries a directive → Strip, log injection attempt, escalate
│   └─ Critical invariant lacks Level 2 evidence → Block the gate; enter evidence loop
├─ VERDICT-CONSUMPTION DEFECT
│   ├─ Gate read the verdict first → HALT; recompute gate independently
│   ├─ Verdict alone gated a consequential action → HALT; require external signal
│   ├─ Proposed action inadmissible → Record as escalation, never as a note
│   └─ Zero or multiple transitions selected → HALT; reissue exactly one
├─ LOOP DEFECT
│   ├─ Child fails a check the parent passed → Roll back to best verified candidate
│   ├─ Repeated defect signature or reversion → Stop; escalate with diff history
│   └─ Two revisions without minimum delta → Stop; return best verified candidate
└─ VALUE DEFECT
    ├─ Theater rate above 10 percent → Repair the consumption path, not the prompt
    ├─ Null-effect share above 70 percent at a site → Retune trigger or retire the site
    └─ Null-effect share above 90 percent overall → Retire the tool for the task class
```

### D. Performance Metrics and Continuous Learning

**Contract and Validation Metrics**:

- **Schema-valid rate**: Records passing syntax and semantic validation on the first attempt over all invocations (target: at least 95 percent; below 90 percent across 20 consecutive invocations suspends the bundle).
- **Repair consumption rate**: Invocations consuming the single permitted repair over all invocations (target: no more than 5 percent).
- **Contract violation rate**: Records attempting to set an approval, authorization, consent, or policy field over all valid records (target: 0; any occurrence is logged and reviewed).
- **Evidence resolution rate**: Cited evidence references resolving with a matching digest over all cited references (target: 100 percent; anything lower rejects the record).

**Verdict Quality Metrics**:

- **Critical-defect recall**: Adjudicated critical defects detected over all adjudicated critical defects (target: at least 90 percent, reported separately from aggregate recall).
- **False-pass rate**: Pass verdicts whose subject ultimately failed over all passes with mature ground truth (target: below the declared release threshold for the task class; a rising trend blocks promotion).
- **Pass-success gap**: Reflection pass rate minus actual task success rate on the same mature cohort (target: no more than 15 percentage points; above that suspends verdict-based gating).
- **Evidence-grounded defect rate**: Detected defects carrying at least 1 Level 1 or Level 2 reference over all detected defects (target: at least 80 percent).
- **Critical evidence coverage**: Critical requirements carrying current Level 2 evidence over all applicable critical requirements (target: 100 percent before any consequential gate).

**Value and Efficiency Metrics**:

- **Null-effect share**: Invocations changing no transition, producing no revision, and closing no defect over all valid invocations (target: no more than 40 percent; above 70 percent at a site retunes or retires it).
- **Reflection theater rate**: Actionable records followed by neither a linked corrective action nor a recorded disposition over all actionable records (target: no more than 10 percent).
- **Revision improvement rate**: Adopted revisions meeting the minimum delta over all attempted revisions (target: at least 50 percent).
- **Regression-from-revision rate**: Revisions failing a protected invariant or reducing the objective score beyond tolerance over all attempted revisions (target: no more than 5 percent).
- **Reflection cost overhead**: Reflection subsystem cost over total task cost, including verifier and review cost (target: no more than 25 percent; above 40 percent triggers policy review).
- **Cost per successful task**: Total cohort cost over successful outcomes, reported with and without reflection on matched cohorts (target: at or below the no-reflection baseline at matched quality).

**Log-Pattern Failure Detection**: Identical verdicts at one call site across every invocation indicate a trigger placed where no variation exists. Rising confidence across iterations with an unchanged evidence bundle indicates confidence inflation. Reflection tokens rising as a share of task tokens while quality by iteration declines indicates context bloat. Divergence between the reflector's score and deterministic or delayed outcome scores indicates optimisation against the rubric rather than against the task. Agreement between a producer and a critic sharing a base model indicates correlated failure rather than confirmation. A high skip rate alongside audit-sampled defects in the skipped population indicates a suppression rule that is hiding real faults.

**Learning and Adaptation Mechanisms**:

- **Outcome-validated promotion**: Only reflections whose defect and repair were externally validated become memory candidates, and no raw record enters a global instruction.
- **Layered memory**: Retain episodic records per trace, semantic aggregates over recurring defect classes, and procedural lessons that change prompts, verifier selection, or workflows; only the third layer requires review, versioning, held-out evaluation, and a revocation path.
- **Narrow lessons**: Draft each lesson with applicability conditions, counterexamples, an evidence count, an observed effect size, an owner, and an expiry, and test it on cases where applying it would be harmful before promotion.
- **System-layer repair**: Where a critique recurs, fix the missing tool, ambiguous requirement, defective schema, or misplaced gate at its own layer rather than teaching the model to narrate around it.
- **Threshold recalibration**: Recompute every threshold per task class against observed outcomes; the values stated in this guide are deployment defaults, not constants.

**Human-in-the-Loop Boundaries**: Release of a final artifact in the highest risk tier, authorisation of an irreversible or externally visible action, any exception to a policy the engine has blocked, promotion of a procedural lesson into durable memory, a per-run invocation ceiling above 6, and relaxation of the disclosure boundary are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the contract around an assessment rather than the content of any particular assessment. Its phases hold wherever a task produces a checkable artifact, admits at least one external verifier, and carries a consequence for acting on a defective result.

### 4.1 Cross-Domain Application Patterns

**Software engineering**: The subject types are code patch and tool result, and the evidence bundle is unusually strong: test outcomes, compiler and type-checker diagnostics, lint findings, coverage deltas, static-analysis alerts, and dependency and secret scans are all Level 2 signals produced by deterministic verifiers. The gate is correspondingly strict, because a verifier exists for almost every critical invariant and the suppression rule in Section 1.4 applies wherever it does. Reflection earns its call after a verifier failure, where the diagnostic output must be interpreted before a bounded repair, and at the pre-merge checkpoint where protected invariants must be re-run. The revision loop is the dominant path, and the regression-from-revision metric is the controlling measure, because an over-broad patch that breaks an unrelated test is the characteristic failure.

**Regulated financial and administrative operations**: Most consequential actions are irreversible in practice and externally visible, so the pre-action gate binds before every one of them and the verdict is advisory within it. The defect classes that matter are authorization missing, policy violation, requirement omission, and stale data, and each requires a Level 2 artifact from a policy engine, an authorization service, or an authoritative state read rather than from the reflector. Separation of duties applies at the highest risk tier: the model instance that produced the candidate does not also reflect on it, approve it, and execute it. The reflection log becomes a deliverable to an auditor rather than a diagnostic aid, which raises the disclosure boundary from a preference to a requirement.

**Scientific and evidence synthesis work**: The subject is a draft answer or a retrieval set, and the strongest available evidence is Level 1 rather than Level 2: retrieved source spans, publication and freshness metadata, and entailment results resolve but remain interpretable. Citation mismatch and unsupported claim dominate the defect distribution. The evidence-gathering loop runs more often than the revision loop, because the productive response to an unsupported claim is usually retrieval of a primary source rather than rewriting. Release requires that every material claim carries a resolvable citation whose entailment was checked, and abstention on an unresolvable claim is preferred over a confident synthesis.

**Industrial operations and logistics**: Reversibility varies within a single run, since a provisional allocation is reversible while a dispatched shipment is not, so the gate binds per action class rather than per task. The environment supplies frequent Level 2 signals through authoritative state reads, which makes the freshness bound the critical field: a gate evaluated against a state read from several minutes earlier is stale, and Step 5.3 requires the re-read immediately before execution. Latency pressure is high, so most call sites are adaptive rather than mandatory, and the skip log plus the audit sample carry the assurance that suppression is not hiding faults.

**Customer-facing service workflows**: The subject is a proposed action or a final candidate, and the characteristic risk is sycophancy: a reflector exposed to a persuasive user claim or a prior approval may converge for social reasons rather than evidential ones. The blinding rules in Step 3.2 are therefore load-bearing here rather than optional, and prior verdicts and producer confidence are withheld in every invocation. Policy and entitlement checks are deterministic and sit entirely outside the record, so a verdict may select which clarification to request and may never decide whether an entitlement applies.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Collapse to a single adaptive call site at the pre-release checkpoint, retain the full schema and rejection rule, and set the invocation ceiling at 1. Reflection overhead above 10 percent of direct-execution cost indicates the gate in Section 1.4 should have suppressed the call.
- **High-risk or irreversible work**: Retain every phase, require Level 2 evidence for every critical invariant, bind the approval gate before each action, enforce separation of duties between producer and reflector, and prefer abstention over an unverified release.
- **Strict latency budgets**: Narrow trigger conditions rather than removing validation, since removing validation removes the tool's only advantage while narrowing triggers reduces its cost. Where latency forbids any invocation, the gate suppresses and a deterministic verifier runs with a declared fallback.
- **High-volume low-margin workloads**: Move most sites to sampled audit, set the sampling rate at the low end of the 1 to 5 percent range, and rely on the skipped-population comparison in Step 6.3 to detect a suppression rule that is hiding defects.
- **Long-horizon autonomous runs**: Persist the contract registry, budget ledger, evidence bundle, and candidate history outside working context, write a handoff record at every context boundary, and re-run the pre-action revalidation at each handoff so a stale gate is not inherited.
- **Multi-agent deployments**: Assign the reflector to a component distinct from the producer, establish independence by provenance rather than by call count, and treat agreement between components sharing a base model as correlated failure until an independence test says otherwise.

***

## V. Limitations and Considerations

**Self-assessment shares the blind spots that produced the output**: A model evaluating its own work is drawing on the same parameters, the same context, and the same errors that generated the candidate, and prompting it to reconsider without new information can leave performance unchanged or degrade it [2]. The consequence is that a typed verdict is a proposal whose epistemic standing is unchanged by its schema. The mitigation is the gating restriction in Step 4.1: a verdict alone gates only reversible internally scoped decisions, and every consequential decision requires an external signal at Level 2 for each critical invariant.

**Schema validity is not semantic correctness**: Structured output and constrained decoding guarantee that a record parses and that its fields sit inside their vocabularies, and they guarantee nothing about whether the assessment is true. The consequence is a well-formed record that confidently misclassifies a defect and propagates further than a malformed one would. The mitigation is the invariant catalogue in Step 1.2, which requires resolvable evidence for every blocking defect, plus the plausibility discipline of comparing verdict outcomes against verifier outcomes and logging every disagreement rather than resolving it by re-invocation.

**Reflection can degrade a correct answer**: A revision loop applied to an already-correct candidate has more ways to break it than to improve it, and the risk grows with each cycle. The consequence is measurable regression on cases that needed no intervention. The mitigation is the retained best verified candidate, the protected-invariant regression set, the automatic rollback when a child fails a check the parent passed, and the requirement that the evaluation suite contain correct candidates the system must leave unchanged.

**Independence is asserted more easily than established**: Two calls are not independent merely because there are two of them; a shared base model, prompt family, context, or training lineage produces correlated errors and shared blind spots. The consequence is agreement mistaken for confirmation, which is the most expensive failure available because it raises confidence while adding no information. The mitigation is the source class label on every signal, the blinding rules in Step 3.2, and the rule in Step 5.2 that same-model agreement is recorded as correlated failure rather than as an external signal.

**Thresholds here are deployment defaults, not measured findings**: The invocation ceiling of 3, the revision ceiling of 2, the 2-round evidence loop, the 2-level escalation cap, the 70 and 90 percent null-effect bounds, the 10 percent theater bound, the 15-point pass-success gap, and the 20 and 25 percent overhead bounds were chosen to be operable on first deployment rather than derived from a universal property of reflection systems. The consequence is that a deployment inheriting them uncritically will be miscalibrated for its own task distribution. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute every threshold per task class against observed outcomes.

**Provider benchmark evidence is narrow**: The reported improvement from a mid-trajectory checkpoint tool covers one model, one scaffold, one benchmark family, and one period, and the same source later recommended improved extended thinking in place of a dedicated tool in most cases [1]. The consequence is that a deployment citing those figures as a general warrant will over-invest in reflection where a stronger producer model or an integrated reasoning mode would have been cheaper. The mitigation is the paired-baseline requirement in Step 6.2, comparing reflection against no reflection, deterministic verification alone, and a stronger producer model on the deployment's own task classes.

**Most external claims here are transcribed rather than re-verified**: This guide is an operational restructuring of a prose source, and the references in Section VII are reproduced as that source cited them. Three entries were retrieved and confirmed during conversion and are marked as such; the remainder were not. The consequence is that a figure or finding carried here may be stated more narrowly or more broadly in its original than the transcription suggests. The mitigation is that no threshold in this guide depends on an unverified external figure: every numeric bound is either a stated deployment default or derives from the verified entries.

**Instrumentation carries its own exposure**: A log rich enough to compute the metric set is rich enough to leak candidate content, evidence bodies, and user data. The consequence is that a well-instrumented deployment can create a disclosure problem it did not previously have. The mitigation is the disclosure boundary in Section III.A, which prohibits retention of hidden reasoning content, requires redaction before write rather than at query time, and replaces raw payloads with content digests and governed references.

**Contract conformance is not usefulness**: A deployment can satisfy every checkpoint in this guide while invoking a tool whose verdicts change nothing. The framework detects a malformed or ungoverned reflection, not a pointless one. The mitigation is Step 6.3, which makes the null-effect share a first-class measure and requires retirement rather than retuning where it exceeds 90 percent across all call sites.

***

## VI. Conclusion and Summary

A structured reflection tool is a contract discipline before it is a reasoning technique. Its value comes from the properties the tool boundary supplies and prose self-assessment cannot: a typed output a validator can reject, an invocation a budget can count, a cost a comparison can attribute, and a verdict a state machine can branch on. A deployment that keeps those four properties and enforces them outside the model gains a governable sensor. A deployment that accepts free text, calls the tool everywhere, absorbs its cost into task generation, and lets a pass proceed on its own has paid for a scratchpad and called it a control.

A team introducing the pattern should build in a fixed order. Declare the schema, the closed vocabularies, and the rejection rule first, because a record that cannot be rejected cannot be trusted. Integrate the deterministic verifiers and the evidence service next, because reflection improves by improving evidence rather than by asking the same model to think harder over unchanged context. Add the state machine, the budgets, the no-improvement rule, and the rollback path before the reflector itself, so the tool arrives behind controls rather than in front of them. Launch in shadow mode, then in sampled advisory mode, and gate on a verdict only after the measurement in Phase 6 shows that reflection changes outcomes at all.

**Key Success Factors**:

- **Typed or nothing**: A reflection returning free text has surrendered the property that justified making it a tool; an unparseable or out-of-vocabulary record is rejected whole, never salvaged by inference.
- **Proposal, never verification**: A verdict gates reversible internal decisions and never authorizes a consequential action; every critical invariant carries an external signal the reflector did not produce.
- **Placed, not sprinkled**: Reflection runs at declared triggers under a per-run ceiling, every suppression is logged with its substitute, and the orchestrator rather than the model decides whether a gate applies.
- **Actionable or escalated**: Every record names a proposed action from a closed set, and a verdict whose action is inadmissible is recorded as an escalation rather than as a note nobody consumes.
- **Bounded change**: Revisions target named defects under a change hypothesis, re-run protected invariants, roll back on regression, and stop on no improvement, repeated signatures, or oscillation, always returning the best verified candidate.
- **Measured effect**: The null-effect share, the theater rate, and cost per successful task decide whether the tool stays, and a call site that changes nothing is retired rather than defended.

By following this guide, AI agents can convert an implicit habit of self-assessment into a declared, budgeted, and auditable tool whose contribution to outcomes is measured rather than assumed.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, and they were not independently re-verified in the course of this conversion except where an entry is marked as verified. Entries 1, 2, and 3 were retrieved during conversion and their figures, titles, and findings confirmed against the pages themselves; every other entry reproduces the source's label and location without re-checking.

**Corpus pointers**:

- `Production Structured Reflection for AI Agents` — the originating prose guide from which this operational guide was derived. Source of the typed record field inventory, the verdict and defect vocabularies, the schema invariants, the evidence-level scheme, the verification-gathering loop, the gating and escalation loops, the reflect-revise-reverify loop with its no-improvement and anti-oscillation rules, the failure-mode catalogue, the logging field inventory, the metric formulas, and the release checklist. It carries inline citations to primary literature on self-correction, self-refinement, tool-grounded critique, evaluator bias, calibration, and agent evaluation; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — owns monitoring signals, their computable definitions, and the calibration procedure, including the finding that a model's stated confidence tracks fluency more than accuracy. This guide consumes a calibration profile identifier from that specification and does not re-derive calibration; the terms source class, external signal, correlated failure, and bundle are adopted from it unchanged.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — owns the control loop that consumes typed signals and issues transitions. This guide hands a validated verdict to that loop and does not duplicate its transition semantics.
- `advanced_task_guides/tool-use/guide_ToolUseAndFunctionCalling.md` — the general tool contract, authorization, and pre-call and post-call validation machinery that this guide specialises for one tool whose subject is the agent's own work.
- `advanced_task_guides/tool-use/guide_AgentControlPlane.md` — companion guidance on a non-bypassable decision path for a fleet of agents, applicable to the orchestrator-imposed gating in Step 2.3.
- `advanced_task_guides/tool-use/guide_MCPToolGateway.md` — companion guidance on mediated tool access and centralised credential custody, applicable to the verifier adapters invoked in Step 3.1.
- `advanced_task_guides/tool-use/guide_CodeAsAction.md` — companion guidance on reviewable action programs and reconciled effects, applicable to the pre-action revalidation in Step 5.3.
- `advanced_task_guides/tool-use/guide_ComputerUse.md` — companion guidance on a bounded observe-act-verify loop, applicable to the evidence assembly in Phase 3.
- `advanced_task_guides/reasoning/guide_ChainOfVerification.md` — companion guidance on separating an answer from its verification, applicable to the claim decomposition and entailment checks in the evidence bundle.

**External references**: The numbering below is the numbering used by the inline markers in Sections I and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*The originating tool pattern*

1. Anthropic think-tool report — https://www.anthropic.com/engineering/claude-think-tool (verified during conversion: the airline-domain figures of 0.570 against 0.370 pass^1, the retail-domain figures of 0.812 against 0.783, and the December 2025 update recommending extended thinking in most cases were confirmed against the page)

*Self-correction, self-refinement, and their limits*

2. *Large Language Models Cannot Self-Correct Reasoning Yet* — https://arxiv.org/abs/2310.01798 (verified during conversion: title, authorship, and the abstract's statement that models struggle to self-correct without external feedback and can degrade after self-correction)
3. *Reflection-Bench: Evaluating Epistemic Agency in Large Language Models* — https://arxiv.org/abs/2410.16270 (verified during conversion: seven evaluated dimensions, sixteen models, three prompting strategies, and the stated limitation in meta-reflection; the source cited this work by the bare label Reflection-Bench)
4. When Can LLMs Actually Correct Their Own Mistakes? — https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00713/125177/When-Can-LLMs-Actually-Correct-Their-Own-Mistakes
5. Reflexion — https://arxiv.org/abs/2303.11366
6. Self-Refine — https://arxiv.org/abs/2303.17651
7. CRITIC — https://arxiv.org/abs/2305.11738
8. Chain-of-Verification — https://arxiv.org/abs/2309.11495
9. Anthropic Constitutional AI — https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback

*Evaluator bias, sycophancy, and reward hacking*

10. Pride and Prejudice — https://aclanthology.org/2024.acl-long.826/
11. LLM Evaluators Recognize and Favor Their Own Generations — https://arxiv.org/abs/2404.13076
12. Spontaneous Reward Hacking in Iterative Self-Refinement — https://arxiv.org/abs/2407.04549
13. MT-Bench and Chatbot Arena — https://arxiv.org/abs/2306.05685
14. Towards Understanding Sycophancy — https://arxiv.org/abs/2310.13548
15. Small Language Models Need Strong Verifiers to Self-Correct Reasoning — https://aclanthology.org/2024.findings-acl.924/

*Calibration and faithfulness*

16. Just Ask for Calibration — https://aclanthology.org/2023.emnlp-main.330/
17. Anthropic faithfulness study — https://www.anthropic.com/research/reasoning-models-dont-say-think

*Search, sampling, and test-time compute*

18. Self-Consistency — https://arxiv.org/abs/2203.11171
19. Tree of Thoughts — https://arxiv.org/abs/2305.10601
20. Graph of Thoughts — https://arxiv.org/abs/2308.09687
21. Scaling LLM Test-Time Compute Optimally — https://arxiv.org/abs/2408.03314

*Structured output, schema, and provider reasoning mechanics*

22. Claude thinking documentation — https://platform.claude.com/docs/en/build-with-claude/extended-thinking
23. OpenAI reasoning guide — https://developers.openai.com/api/docs/guides/reasoning
24. OpenAI function calling — https://developers.openai.com/api/docs/guides/function-calling
25. OpenAI Structured Outputs — https://developers.openai.com/api/docs/guides/structured-outputs
26. Gemini function calling — https://ai.google.dev/gemini-api/docs/function-calling
27. Gemini structured outputs — https://ai.google.dev/gemini-api/docs/structured-output
28. JSON Schema validation specification — https://json-schema.org/draft/2020-12/json-schema-validation

*Frameworks and orchestration mechanics*

29. AutoGen reflection — https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/reflection.html
30. LangGraph reflection tutorial — https://langchain-ai.github.io/langgraph/tutorials/reflection/reflection/
31. Microsoft human-in-the-loop workflows — https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop
32. Microsoft workflow observability — https://learn.microsoft.com/en-us/agent-framework/workflows/observability

*Security and governance*

33. OWASP AI Agent Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
34. NIST AI 600-1 — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf

*Evaluation, benchmarks, and observability*

35. Anthropic agent evals — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
36. tau-bench — https://arxiv.org/abs/2406.12045
37. SWE-bench Verified — https://www.swebench.com/verified.html
38. OpenAI evals — https://developers.openai.com/api/docs/guides/evals
39. Inspect eval logs — https://inspect.aisi.org.uk/eval-logs.html
40. OpenTelemetry GenAI conventions — https://opentelemetry.io/docs/specs/semconv/gen-ai/
