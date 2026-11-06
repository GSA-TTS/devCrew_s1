# Context State Machines

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context state machines constitute the task family of governing the contents of a model's context window by an explicit declared control state rather than by an accumulation of conversation history. An agent occupies exactly one named state; that state determines which partitions are populated, which tool definitions are exposed, which instructions apply, and which transitions to other states are legal. The distinctive property is that context composition becomes a lookup rather than an open-ended assembly decision: the same state with the same input references produces the same context package, so a window becomes reproducible and a bad output becomes attributable to a state definition instead of to chance. This guide specifies six phases covering state inventory and context-profile declaration, transition and guard specification, tool-surface binding, runtime transition handling with illegal-transition and cycle detection, fallback-state entry with escalation, and replay-based audit that corrects state definitions. It fixes the authority split: a deterministic control plane owns the state register, guard evaluation, transition execution, tool-surface enforcement, cycle detection, and the assembly lookup, while the model tier proposes transitions and does the work inside a state. It states the cost of the method, which is rigidity wherever real work does not fit the declared states, and it makes that cost measurable through a declared fallback state and a numeric escalation trigger.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Context state machine**: A versioned declaration of named control states, legal transitions between them, guard predicates admitting each transition, and a context profile attached to each state. It governs which information is admitted to the window and which tools are callable at each point of a run. It does not make model reasoning deterministic; it makes the window surrounding that reasoning deterministic.

**Control state**: One named, stable condition of a run, carrying a context profile, a tool loadout, an instruction set, a declared set of legal outgoing transitions, a deadline, a visit cap, and a terminal status where applicable. Exactly one control state is active per run at any decision boundary, or one active state per declared concurrent region where regions are used.

**Context window**: The token sequence accepted by one model call. It is a transport, not a store. This definition is adopted unchanged from the context-management and working-memory guidance and is load-bearing throughout.

**Partition**: A named region of the context budget reserved for one purpose, carrying a maximum token count, a floor where the purpose is protected, an admission rule, and an eviction order. The definition and the default partition table are adopted from the umbrella context-management guidance and are not restated here.

**Context package**: The complete serialized input for one model call, comprising every partition in declared assembly order together with the accounting record naming what was admitted, what was excluded, and why. The term is adopted unchanged from the umbrella guidance.

**Context profile**: The per-state declaration naming which partitions are populated in that state, the token bound on each, the admission rule and source binding for each, the assembly order, and the instruction set that applies. It is the part of a state definition that converts assembly into lookup.

**Context assembler**: The deterministic component holding the deployed tokenizer, the partition ledger, and the sole authority to place a unit into the outgoing context package. The term is adopted unchanged from the context-selection guidance. Under a state machine the assembler takes the active state identifier as its first argument and reads the context profile rather than negotiating composition per call.

**Assembly lookup**: The deterministic function mapping an active state identifier, a pinned machine version, and a resolved input reference set to one context package. It admits no wall-clock read, no random draw, and no model call, so that repeating it on the same arguments reproduces the same bytes.

**Tool loadout**: The set of tool definitions admitted into the tool-definition partition for the current step, distinguished from the tool catalog, which is the full authorized inventory. The term is adopted unchanged from the context-selection guidance. A state binds exactly one tool loadout.

**Authority scope**: The closed set of tools, operations, resources, destinations, and credentials available in the active state, together with their expiry. The term is adopted unchanged from the context-isolation guidance, including its rule that the scope is computed by the deterministic tier and is never proposed, widened, or self-selected by the model.

**State transition**: The only authorized route from one active control state to another, carrying a stable identifier, a source state, a trigger, one or more guards, a target state, a carry set, a drop set, and an effect record. It is distinct from the lifecycle stage transition defined in the context-lifecycle guidance, which governs a run's progression through time; a state transition governs which context profile becomes active next.

**Trigger**: The named, typed occurrence that offers a transition for evaluation: a model proposal, a tool result, a validator verdict, a timer expiry, an approval, a cancellation, or an internal completion signal. A trigger offers a transition; it never performs one.

**Guard**: A side-effect-free predicate evaluated by the deterministic tier against an immutable snapshot taken at the moment of evaluation, returning admit or deny with a reason code. A transition without a guard is a suggestion, not a machine, and fails static validation.

**Carry set**: The enumerated set of state fields, artifact references, and protected atoms that survive a named transition into the target state's window. **Drop set**: the enumerated complement that does not. Every transition declares both; an undeclared field is treated as dropped.

**Illegal transition attempt**: A proposed move for which no declared transition exists from the active state, or for which every declared candidate transition is denied by its guards. It is recorded, refused, and counted; it never resolves by selecting a nearby state.

**Non-progressing cycle**: A repeated traversal of the same set of states in which the declared progress measure does not improve between successive entries into the cycle's entry state. It is detected by the deterministic tier from the transition journal, not inferred by the model.

**Progress measure**: One numeric quantity per cyclic region that must strictly improve across successive visits: requirements covered, open subtasks closed, validation errors remaining, or evidence gaps resolved. A cyclic region without a declared progress measure fails static validation.

**Fallback state**: The single declared state entered when the run encounters a situation the state graph does not model. It carries its own context profile and a deliberately narrow tool loadout, and its purpose is to produce a defined behaviour rather than to leave the agent in a state whose tools cannot help.

**State register**: The authoritative record of the active state, its version, its entry cause, its visit count, and its deadline, held in a transactional store outside the window. The active state is read from the register, never inferred from conversation text.

**Machine definition**: The immutable, versioned artifact carrying every state, context profile, tool loadout, transition, guard, progress measure, and terminal status. A run pins one machine version at start and is never resolved against a moving latest.

**Transition journal**: The append-only record of every transition attempt, carrying the source state, trigger, guard verdicts, selected transition, carry and drop sets, resulting state, and the assembly hash of the context package produced on entry.

**Assembly hash**: The digest of the serialized context package produced by the assembly lookup, recorded on every state entry. Two runs entering the same state with the same input reference set and the same machine version must produce equal hashes.

### 1.2 Composition as Lookup and What It Costs

**The substitution**: Without a state machine, the question at each turn is open-ended: which of everything available should occupy the window now. With a state machine, the question is closed: what does the profile for state S declare. The first question has no reproducible answer and no owner; the second is a table read with a single deterministic owner.

**The reproducibility property**: Because the active state and the machine version fully determine the profile, and the profile plus the resolved input references fully determine the package, a run's window at any point can be rebuilt from three recorded values. This is what makes replay possible and what makes a defect attributable. A window assembled from accumulated history cannot be rebuilt, so a bad output cannot be separated from an unlucky ordering of prior turns.

**The tool-surface benefit**: Binding a tool loadout to a state is the most immediately valuable consequence. A tool not exposed in the active state is not callable, so entire classes of misuse become unreachable rather than discouraged. Current practice scopes tool surfaces per task and per sub-agent instead of loading a full catalog into every call, and a state machine supplies the scoping key.

**The cost, stated plainly**: Rigidity. Real work encounters situations the declared states do not model, and a machine with no defined behaviour for those situations leaves an agent occupying a state whose tools cannot advance the task. The method is only safe where the escape hatch in Phase 5 is declared, instrumented, and monitored, and where its frequency is treated as evidence about the machine rather than as noise.

**The second cost**: State proliferation. Every distinction encoded as a state multiplies the definitions to be maintained and verified. A distinction that changes only payload data belongs in a typed field; a distinction that changes legal transitions, tool loadout, admitted partitions, or deadlines belongs in a state.

### 1.3 The Tier Partition

**Deterministic tier**: Owns the state register, guard evaluation, transition execution, tool-surface enforcement, cycle detection, the assembly lookup, the transition journal, and static validation of the machine definition. It requires exactness, reproducibility, and auditability that model inference cannot supply. It rejects undeclared transitions, guard-denied transitions, calls to tools outside the active loadout, transitions whose carry set is undeclared, and any attempt to write the state register directly.

**Model tier**: Owns proposing a transition and performing the open-vocabulary work inside a state: interpreting evidence, drafting, classifying, synthesising, and selecting among admitted material. It is never permitted to decide alone that a transition is legal, to widen its own tool surface, to write the state register, or to declare a cycle terminated.

**Hybrid tier**: Transition selection. The model proposes exactly one transition label drawn from an allowlist supplied in the active state's instruction set; the deterministic tier evaluates the guards and admits or refuses. Where the two disagree, the deterministic tier holds authority without exception, and the model's proposal is recorded with the denial reason rather than overridden.

**The authority sentence**: A model proposes a transition and a deterministic guard admits it. Structured output conformance proves that a proposal is well formed; it never proves that the proposal is legal, authorized, or safe.

### 1.4 Entry Gate: When a Context State Machine Is Warranted

The machine carries definition, validation, and maintenance cost. Agents must run a gate before adopting it, bounded to 5 percent of the projected build effort, returning adopt, adopt-minimal, or decline.

**Adoption conditions**: Adopt where at least two of the following hold: the work has 4 or more phases whose legal ordering is known in advance; different phases require materially different tool loadouts; at least one phase authorizes an irreversible or consequential action; the window must be reproducible for audit or regression testing; or runs exceed a single context window and must resume from a recorded position.

**Decline conditions**: Decline where the next useful action cannot be enumerated economically, where all effects are read-only and reversible, where the whole task fits one window and one tool loadout, or where the declared states would merely rename each model turn. In those cases a fixed assembly policy with one tool loadout is cheaper and no less safe.

**Adopt-minimal**: Where exploration dominates but a small number of hard boundaries exist, wrap the exploratory loop in a machine of 3 to 5 states covering planning, acting, verifying, and terminal outcomes, and bind the consequential tools to a single gated state rather than modelling the exploration itself.

**Numeric gate rule**: Where fewer than 4 states can be named without inventing distinctions that change no tool loadout, no partition set, and no legal ordering, the gate returns decline and records the enumeration attempt. Where more than 12 states are named before decomposition into submachines, the gate returns adopt with a mandatory decomposition step, because a flat machine above 12 states has been observed to exceed what static validation output can be read and maintained against.

***

## II. Operational Framework: State-Determined Context Composition

The framework assumes the entry gate has returned adopt or adopt-minimal. Phases 1 through 3 are design-time and produce an immutable machine definition. Phase 4 is the runtime loop. Phase 5 handles situations the definition does not model. Phase 6 runs after execution and returns corrections to Phases 1 through 3, so the machine improves against recorded evidence rather than against opinion.

### Phase 1: State Inventory and Context Profile Declaration

**Objective**: Produce a bounded set of named control states, each carrying a context profile complete enough that the context package for that state can be assembled by lookup rather than by negotiation.

#### Step 1.1: Enumerate Control States From Obligations, Tool Boundaries, and Failure Modes

**Required Actions**:

- Enumerate candidate states from three sources in order: external obligations the run must satisfy, points at which the required tool loadout changes, and failure modes that require a distinct context and a distinct set of legal moves.
- Reject any candidate whose only difference from an existing state is payload data, and record it instead as a typed field on the existing state.
- Retain a candidate only where it changes at least one of: the populated partition set, the tool loadout, the instruction set, the set of legal outgoing transitions, or the deadline.
- Cap the flat state count at 12 excluding terminal states and the fallback state; decompose any larger inventory into submachines with typed entry and exit contracts.
- Declare every terminal state explicitly, drawing its status from the closed vocabulary `succeeded`, `partial`, `failed`, `blocked`, `timed_out`, and `policy_denied`, adopted unchanged from the context-isolation guidance.
- Assign each non-terminal state an owner, a deadline, and a visit cap of no more than 5 entries per run.

**State Retention Test**:

| Candidate differs by | Encode as | Rationale |
| :-- | :-- | :-- |
| Populated partition set | Control state | Changes what the assembly lookup returns |
| Tool loadout | Control state | Changes what is callable and is the primary safety lever |
| Instruction set or output schema | Control state | Changes the contract the model is held to |
| Legal outgoing transitions | Control state | Changes the reachable graph |
| Deadline or visit cap | Control state | Changes the runtime bound enforced |
| Field value, counter, or accumulated text | Typed field | Changes no admission rule and no authority |
| Boolean flag combination | Control state or region | Combinations create untested configurations |

**Required Outputs**:

- A state inventory of 4 to 12 non-terminal states, each with an identifier, an owner, a deadline, and a visit cap.
- A terminal state set with one declared status value per terminal state.
- A rejection record naming every candidate collapsed into a typed field and the retention test it failed.

**Quality Checkpoints**:

- Every retained state changes at least one of the five retention criteria; states failing all five are absent from the inventory.
- The non-terminal state count is between 4 and 12; a larger count carries a decomposition record naming its submachines.
- Every terminal status is drawn from the closed vocabulary; an undeclared or free-text status halts definition.

***

#### Step 1.2: Declare the Context Profile for Each State

**Required Actions**:

- Declare, for each state, which partitions are populated, in what assembly order, and with what token maximum and protected floor per partition.
- Bind each populated partition to a named source: a durable store handle, a retrieval query identifier, a state field, or a static configuration reference. A partition without a source binding cannot be assembled by lookup.
- State the admission rule per partition, naming which trust classes and sensitivity classes may enter, and reuse the admission gate defined in the umbrella context-management guidance rather than defining a second gate.
- Declare the protected atom set that must be present in the state regardless of budget pressure, drawn from the membership list adopted from the working-memory guidance.
- Declare the instruction set version and the output schema identifier that apply in the state, and pin both to the machine version.
- Verify the sum of partition maxima plus the output reserve does not exceed the context budget for the deployed model, and record the residual headroom.

**State Definition Record**:

```
STATE_ID:
MACHINE_VERSION:
OWNER:
DEADLINE_SECONDS:
VISIT_CAP:
CONTEXT_PROFILE:
  PARTITION_ORDER:        [ordered list of partition names]
  PARTITION_BOUNDS:       [name -> max_tokens, floor_tokens]
  SOURCE_BINDINGS:        [name -> store handle | query id | state field | config ref]
  ADMISSION_RULES:        [name -> trust classes, sensitivity classes]
  PROTECTED_ATOMS:        [enumerated set]
  ASSEMBLY_ORDER_HASH:
INSTRUCTION_SET_VERSION:
OUTPUT_SCHEMA_ID:
TOOL_LOADOUT_ID:
AUTHORITY_SCOPE_ID:
PROGRESS_MEASURE:        [name, direction, required delta]
LEGAL_OUTGOING:          [transition ids]
TERMINAL_STATUS:         [value or NONE]
```

**Required Outputs**:

- One state definition record per state, with every context profile field populated.
- A partition budget table per state showing maxima, floors, output reserve, and residual headroom.
- A source binding inventory naming every store handle, query identifier, and configuration reference the machine depends on.

**Quality Checkpoints**:

- Every populated partition carries a source binding; an unbound partition halts definition because it cannot be assembled deterministically.
- Partition maxima plus output reserve are at or below the context budget in every state; a state over budget is rejected before any transition is specified.
- Every state carries a protected atom set; an empty set is permitted only in terminal states.
- No state omits the instruction set version or the output schema identifier.

***

#### Step 1.3: Fix the Assembly Lookup and Its Determinism Contract

**Required Actions**:

- Implement the assembly lookup as a pure function of the active state identifier, the pinned machine version, and a resolved input reference set, and prohibit any other argument.
- Resolve every input reference to an immutable version identifier before assembly begins, so that a source changing mid-run cannot silently alter the package.
- Prohibit wall-clock reads, random draws, unordered set iteration, and model calls inside the lookup; where a timestamp is required by the instruction set, admit it as a resolved input reference rather than reading it during assembly.
- Compute and record an assembly hash over the serialized context package on every state entry, using the deployed tokenizer's serialization rather than a re-rendered approximation.
- Prove determinism before release by assembling each state 3 times from identical arguments and comparing hashes; any inequality blocks release of the machine version.

**Required Outputs**:

- An assembly lookup specification naming its three arguments and its prohibited inputs.
- An input reference resolution record binding every source to an immutable version identifier per run.
- A determinism proof record listing, per state, 3 assembly hashes and their equality verdict.

**Quality Checkpoints**:

- The lookup accepts exactly 3 arguments; an implementation reading any fourth input fails the determinism contract.
- All 3 repeated assemblies produce equal hashes for 100 percent of states; a single inequality blocks release and names the non-deterministic input.
- Every input reference carries an immutable version identifier at resolution time; an unversioned reference is rejected before assembly.

***

### Phase 2: Transition and Guard Specification

**Objective**: Convert the state inventory into a machine by declaring, for every legal move, its trigger, its guard set, and its exact effect on the window, so that no move occurs that a deterministic predicate did not admit.

#### Step 2.1: Specify Each Transition With Trigger, Guard, Carry Set, and Drop Set

**Required Actions**:

- Enumerate transitions from each source state by asking which triggers the state may legally receive, and declare one transition per source state and trigger type pair.
- Name the trigger type for each transition, drawn from the closed set: model proposal, tool result, validator verdict, timer expiry, approval decision, cancellation, or internal completion signal.
- Attach at least 1 guard to every transition; a transition carrying 0 guards fails static validation and is never released.
- Declare the carry set explicitly by field identifier, naming what survives into the target state's window, and declare the drop set as its complement so that neither is inferred.
- Declare the effect record for each transition: which partitions are cleared, which are repopulated from source, which protected atoms are re-anchored, and whether an external effect is authorized.
- Assign a priority integer to every transition leaving a state so that two simultaneously eligible transitions resolve by declaration rather than by iteration order.
- Give every transition a stable identifier and a version, and pin both to the machine version.

**Transition Definition Record**:

```
TRANSITION_ID:
MACHINE_VERSION:
SOURCE_STATE:
TRIGGER_TYPE:            [model_proposal | tool_result | validator_verdict |
                          timer_expiry | approval | cancellation | completion]
TRIGGER_SCHEMA_ID:
GUARD_IDS:               [ordered, minimum 1]
TARGET_STATE:
PRIORITY:                [integer, unique within source state]
CARRY_SET:               [field ids surviving into target window]
DROP_SET:                [field ids not surviving]
EFFECT_RECORD:
  PARTITIONS_CLEARED:    [names]
  PARTITIONS_REPOPULATED:[names, source bindings]
  PROTECTED_REANCHORED:  [atom ids]
  EXTERNAL_EFFECT:       [effect class or NONE]
REASON_CODE_ON_DENY:
```

**Required Outputs**:

- One transition definition record per legal move, with carry set and drop set enumerated by field identifier.
- A priority table per source state showing unique integers across its outgoing transitions.
- A trigger schema inventory binding each trigger type to a validated schema identifier.

**Quality Checkpoints**:

- Every transition carries at least 1 guard; the count of zero-guard transitions is 0.
- Every field in every state's carry set is either present in the source state's profile or resolvable from a durable store; an unresolvable carry field halts definition.
- No two outgoing transitions from one state share a priority integer; a collision halts definition rather than being broken arbitrarily at runtime.
- Carry set and drop set together account for 100 percent of the source state's declared fields.

***

#### Step 2.2: Define Guard Predicates as Deterministic, Versioned Functions

**Required Actions**:

- Implement each guard as a side-effect-free predicate over an immutable snapshot comprising the state register entry, the resolved input reference set, the trigger payload, and the policy version pinned to the run.
- Order guard evaluation so that authorization and deny rules run before any condition depending on model output, and record the first denial rather than evaluating the remainder.
- Prohibit any guard from calling a model, reading a wall clock, issuing a network request, or mutating state; a guard requiring external data receives that data as a resolved input reference.
- Assign each guard a reason code from a closed vocabulary, so that a denial is machine-classifiable rather than a free-text message.
- Version each guard independently of the transition that uses it, and record which guard versions a machine version binds.
- Classify each guard as structural, authorization, budget, evidence, or progress, and require that every transition authorizing an external effect carries at least 1 authorization guard and at least 1 evidence guard.

**Guard Class Inventory**:

| Guard class | Evaluates | Denial consequence |
| :-- | :-- | :-- |
| Structural | Trigger schema, field presence, target state validity | Refuse and record malformed trigger |
| Authorization | Principal, tenant, authority scope, approval binding | Refuse and record policy denial; never retried unchanged |
| Budget | Remaining tokens, tool calls, elapsed time, visit count | Refuse and route to the declared budget path |
| Evidence | Required references present, versions current, validator verdicts | Refuse and route to an evidence-gathering state |
| Progress | Progress measure delta across the cyclic region | Refuse and route to cycle handling in Step 4.3 |

**Required Outputs**:

- One guard specification per guard, naming its class, its snapshot inputs, its reason codes, and its version.
- A guard-to-transition binding table showing which guard versions each machine version pins.
- An evaluation order declaration placing authorization and deny rules ahead of model-dependent conditions.

**Quality Checkpoints**:

- No guard reads any input outside the declared immutable snapshot; a guard with an undeclared input fails release.
- Every transition authorizing an external effect carries at least 1 authorization guard and at least 1 evidence guard.
- Every denial returns a reason code from the closed vocabulary; a free-text denial is rejected by the journal writer.

***

#### Step 2.3: Validate the Graph Statically Before Release

**Required Actions**:

- Run reachability analysis from the declared start state and report any state not reachable and any state from which no terminal state is reachable.
- Confirm every non-terminal state carries at least 1 outgoing transition and that every terminal state carries 0 ordinary outgoing transitions.
- Detect every cycle in the graph and confirm each carries a declared progress measure, a visit cap, and at least 1 exit transition whose guard does not depend on the cycle's own output.
- Confirm no transition targets a state absent from the inventory and no guard references a field absent from the source state's profile.
- Confirm the fallback state declared in Phase 5 is reachable from 100 percent of non-terminal states.
- Record the validation report as an artifact bound to the machine version, and block release on any failure rather than on a subset of failures.

**Required Outputs**:

- A static validation report naming unreachable states, dead transitions, terminal states with outgoing edges, unbounded cycles, dangling targets, and unreachable fallback paths.
- A reachability matrix showing, per state, whether at least 1 terminal state is reachable.
- A release verdict of pass or fail bound to the machine version.

**Quality Checkpoints**:

- Unreachable state count is 0, dangling transition target count is 0, and zero-guard transition count is 0.
- Every cycle carries a progress measure, a visit cap, and at least 1 progress-independent exit; a cycle failing any of the three blocks release.
- The fallback state is reachable from 100 percent of non-terminal states; a state with no fallback path blocks release.
- The validation report is attached to the machine version; an unattached report is treated as absent.

***

### Phase 3: Tool-Surface Binding and Authority Separation

**Objective**: Bind exactly one tool loadout and one authority scope to each state and enforce both outside the model, so that a tool not exposed in the active state is not callable rather than merely discouraged.

#### Step 3.1: Bind One Tool Loadout to Each State

**Required Actions**:

- Select, for each state, the minimum tool set that can advance the task from that state, and cap the loadout at 8 tool definitions; a state requiring more is decomposed into two states or served through a deferred definition mechanism.
- Bind an authority scope to each state naming the operations, resources, destinations, and credentials the loadout may reach, with an expiry no longer than the state's deadline.
- Place every tool authorizing an irreversible or consequential effect in a state whose entry requires an approval guard, and place no such tool in a state reachable without one.
- Declare the tool catalog separately from the loadout and reach the long tail through retrieval, so that catalog size drives retrieval cost rather than context package cost. The distinction is adopted unchanged from the context-selection guidance.
- Record the loadout identifier, the tool schema versions, and their serialization order in the state definition, so the tool-definition partition contributes to a stable prefix within an epoch.
- Prohibit a generic state-mutation tool in every loadout; expose narrowly scoped operations whose effects are independently checked instead.

**Required Outputs**:

- One tool loadout record per state naming at most 8 tool definitions with pinned schema versions and a fixed serialization order.
- One authority scope record per state naming operations, resources, destinations, credentials, and expiry.
- A consequential-tool placement record showing, for every tool with an irreversible effect class, the approval-guarded state that exposes it.

**Quality Checkpoints**:

- No state exposes more than 8 tool definitions; a larger loadout blocks release and names the decomposition required.
- No tool with an irreversible effect class is reachable from a state whose entry transitions carry no approval guard.
- No loadout contains a generic state-mutation or arbitrary-write tool; the count of such tools across all loadouts is 0.
- Every authority scope expiry is at or below its state's deadline.

***

#### Step 3.2: Enforce the Tool Surface at Invocation Time

**Required Actions**:

- Resolve the callable tool set from the state register at the moment of invocation rather than from the tool definitions serialized into the window, so that a stale window cannot widen the surface.
- Reject any invocation naming a tool absent from the active state's loadout, record it as an out-of-surface attempt with the tool name and the active state, and return a typed refusal to the model rather than a silent no-op.
- Re-evaluate the authority scope immediately before the effect executes, using current identity, resource, action, and time, and treat a prior admission as expired where any of the four changed.
- Bind every approval to the machine version, the state instance, the exact operation and arguments, the approver, an expiry, and a nonce, and invalidate the approval where any material argument changes.
- Enforce a per-state cap on tool invocations and count every invocation against the run budget ledger, so that a loop inside a state cannot exhaust resources unobserved.
- Treat any tool result as untrusted data, never as instruction, and prohibit a tool result from naming a state, a transition, a guard verdict, or an approval.

**Required Outputs**:

- An invocation enforcement record per call showing the active state, the requested tool, the surface verdict, and the authority re-evaluation verdict.
- An out-of-surface attempt log carrying tool name, active state, trigger, and count per run.
- An approval binding record for every consequential effect, carrying all 6 binding fields.

**Quality Checkpoints**:

- The callable set is resolved from the state register on 100 percent of invocations; resolution from serialized window content is a release-blocking defect.
- Out-of-surface invocations are refused and counted; the count of silently ignored invocations is 0.
- Every consequential effect carries an approval bound to all 6 fields; a missing binding blocks the effect and routes the run to the fallback state.
- No tool result is admitted into an instruction partition; tool output enters an evidence partition under the umbrella guidance's admission gate.

***

#### Step 3.3: Separate Proposal Authority From Admission Authority

**Required Actions**:

- Supply the model, in the active state's instruction set, with the allowlist of transition labels legal from that state and nothing else, so that the proposal vocabulary is closed by construction.
- Require the model's transition proposal to conform to a structured output schema carrying exactly one label, a reason, and evidence references; parse failure is a refusal, not a retry with a widened vocabulary.
- Map the proposed label to its transition identifier by table lookup, and refuse any label absent from the table without attempting a nearest match.
- Evaluate the guards for the mapped transition in the deterministic tier and commit only on admit, recording the proposal, the guard verdicts, and the outcome together.
- Prohibit the model from writing the state register, from selecting its own tool loadout, from extending its own deadline, and from declaring a cycle terminated; enforce all four in the dispatcher rather than in the prompt.
- Where the model proposes a legal transition whose guard denies it, return the reason code to the model within the same state and permit at most 2 further proposals before the illegal-attempt handling in Step 4.2 applies.

**Authority Assignment**:

| Decision | Proposing party | Admitting party | Authority on disagreement |
| :-- | :-- | :-- | :-- |
| Which transition to take next | Model tier | Deterministic guard | Deterministic tier |
| Whether a guard's condition holds | Deterministic tier | Deterministic tier | Deterministic tier |
| Which tools are callable now | Deterministic tier | Deterministic tier | Deterministic tier |
| What content answers the task in a state | Model tier | Validator in the state's schema | Validator |
| Whether a cycle is making progress | Deterministic tier | Deterministic tier | Deterministic tier |
| Whether to enter the fallback state | Deterministic tier | Deterministic tier | Deterministic tier |

**Required Outputs**:

- A per-state transition allowlist embedded in the instruction set and pinned to the machine version.
- A structured proposal schema declaring one label field, one reason field, and one evidence reference list.
- A proposal adjudication record per checkpoint carrying the proposed label, the mapped transition, the guard verdicts, and the commit outcome.

**Quality Checkpoints**:

- Every proposal is matched to a transition by exact table lookup; the count of nearest-match resolutions is 0.
- The model never widens its own tool surface; the count of loadout changes originating from model output is 0.
- Schema conformance is treated as necessary and not sufficient; every conformant proposal still passes guard evaluation before commit.
- No more than 2 further proposals are accepted after a guard denial within one state entry before illegal-attempt handling applies.

***

### Phase 4: Runtime Transition Handling and Anomaly Detection

**Objective**: Execute the machine one guarded transition at a time, refusing every move no guard permits and detecting state cycles that consume budget without advancing the declared progress measure.

#### Step 4.1: Execute One Guarded Transition per Trigger

**Required Actions**:

- Read the active state and its expected version from the state register under a lease or an expected-version constraint before evaluating any candidate.
- Enumerate only the transitions declared for the active state and the received trigger type; an undeclared pair produces an illegal transition attempt under Step 4.2 rather than a search for a plausible target.
- Evaluate guards in the declared order, stopping at the first denial and recording its reason code with the guard version that produced it.
- Where 2 or more transitions remain eligible, select by declared priority; where priorities are equal, refuse with an ambiguity reason code rather than choosing by iteration order.
- Apply the carry set and the drop set exactly as declared, clear and repopulate partitions per the effect record, and run the assembly lookup for the target state.
- Commit the successor state version, the transition result, and the assembly hash in one atomic operation, and append the transition journal entry in the same commit.
- Increment the target state's visit count and re-check its deadline and visit cap before releasing control to the model tier.

**Workflow Execution Pattern**:

```
STATE: Transition_Evaluation
INPUTS:
  1. Active state and expected version from the state register
  2. Trigger with validated schema and producer identity
  3. Pinned machine version and guard version bindings
ACTIONS:
  1. Enumerate transitions declared for (active_state, trigger_type)
  2. Evaluate guards in declared order; stop at first denial
  3. Resolve remaining candidates by declared priority
  4. Apply carry set and drop set; repopulate partitions from source bindings
  5. Run assembly lookup for target state; compute assembly hash
VALIDATION:
  - declared_transition_exists == TRUE
  - denied_guard_count == 0
  - eligible_transition_count == 1
  - carry_set_fields_resolved == TRUE
  - target_visit_count <= visit_cap
  - assembly_hash_recorded == TRUE
TRANSITIONS:
  IF all_validations_pass THEN commit_successor AND next_state = target_state
  IF declared_transition_exists == FALSE THEN next_state = Illegal_Attempt_Handling
  IF denied_guard_count > 0 THEN next_state = Guard_Denial_Handling
  IF eligible_transition_count > 1 THEN next_state = Ambiguity_Halt
  IF target_visit_count > visit_cap THEN next_state = Cycle_Handling
```

**Required Outputs**:

- One transition journal entry per attempt carrying source state, trigger, guard verdicts, selected transition, carry and drop sets, target state, and assembly hash.
- A state register commit record showing the expected version read and the successor version written.
- A partition effect record showing what was cleared, what was repopulated, and from which source binding.

**Quality Checkpoints**:

- Exactly 1 transition commits per accepted trigger; a commit count of 0 or greater than 1 halts the run.
- Every commit is atomic across state, journal entry, and assembly hash; a partial commit is treated as a failed transition and the prior state is retained.
- Every target state entry records an assembly hash; a missing hash blocks the subsequent model call.
- The eligible transition count is 1 at commit; an ambiguity halt is never resolved by picking the first candidate.

***

#### Step 4.2: Refuse and Account for Illegal Transition Attempts

**Required Actions**:

- Refuse any attempted move for which no declared transition exists from the active state and trigger type, and refuse any move whose every candidate transition was guard-denied.
- Retain the active state unchanged on refusal; never infer a nearby state, never partially apply a carry set, and never emit an effect.
- Return a typed refusal to the model tier carrying the reason code, the guard that denied, and the unchanged allowlist of legal labels for the active state, so that the next proposal is better informed rather than merely repeated.
- Record every refusal in the transition journal with the proposing party, the requested target, the reason code, and the attempt ordinal within the current state entry.
- Enter the fallback state on the 3rd consecutive illegal attempt within one state entry, or on the 2nd consecutive illegal attempt where the active state authorizes a consequential effect.
- Classify refusals into four causes before aggregation: malformed proposal, policy denial, missing evidence, and machine gap, because only the fourth is evidence that the state graph is wrong.

**Illegal Attempt Response Ladder**:

| Attempt ordinal in one state entry | Response | Recorded classification |
| :-- | :-- | :-- |
| 1 | Refuse; return reason code and allowlist | Provisional |
| 2 | Refuse; re-anchor protected atoms; re-serialize allowlist | Provisional |
| 3 | Refuse; enter fallback state; preserve journal | Confirmed machine gap or model defect |
| Any, in a consequential state | Refuse; enter fallback on the 2nd | Confirmed; effect never attempted |

**Required Outputs**:

- A refusal record per illegal attempt carrying cause classification, attempt ordinal, and unchanged state version.
- A per-run illegal attempt count broken down by the 4 causes.
- A fallback entry event where the ordinal threshold was reached, naming the triggering attempt.

**Quality Checkpoints**:

- The active state is byte-identical before and after a refusal; any state change on refusal is a release-blocking defect.
- No effect executes on a refused transition; the count of effects emitted under refusal is 0.
- Every refusal carries one of the 4 cause classifications; unclassified refusals are excluded from machine-fit analysis rather than counted as machine gaps.
- Fallback entry occurs at the 3rd consecutive illegal attempt, or the 2nd in a consequential state; a run continuing past those thresholds is a control defect.

***

#### Step 4.3: Detect and Break Non-Progressing State Cycles

**Required Actions**:

- Compute the declared progress measure on entry to every state that participates in a cycle, and record its value with the state instance identifier.
- Declare a cycle non-progressing where the same state is entered 3 times within one run and the progress measure fails to improve by its required delta across 2 consecutive entries.
- Declare a tight loop where 2 consecutive transitions return to the same state with an identical assembly hash, which indicates the window is being rebuilt unchanged and no new information has entered.
- Apply a bounded response on detection: checkpoint the run, refuse further transitions into the cycle, and route to the declared cycle exit whose guard does not depend on the cycle's own output; where no such exit is enabled, enter the fallback state.
- Enforce the per-state visit cap of 5 independently of progress detection, so that a slowly improving measure cannot justify unbounded traversal.
- Record the cycle's member states, entry count, progress values, and exit route, and treat the record as an input to Phase 6 rather than as a transient runtime warning.

**Required Outputs**:

- A cycle detection record naming member states, entry ordinals, progress measure values, and detection verdict.
- A bounded response record naming the checkpoint identifier and the exit route taken.
- A per-run tight-loop count keyed by state and assembly hash.

**Quality Checkpoints**:

- Every cyclic state records a progress measure on entry; a missing value is treated as non-improving rather than as unknown.
- The 3-entry, 2-consecutive-non-improvement signature triggers the bounded response in 100 percent of detections; a detection without a response is a control defect.
- The visit cap of 5 is enforced regardless of progress; a 6th entry halts the run and enters the fallback state.
- Identical consecutive assembly hashes on return to a state are recorded as tight loops and are never permitted to repeat more than twice.

***

### Phase 5: Fallback State Entry and Escalation

**Objective**: Give every situation the state graph does not model a defined behaviour, so that an unmodelled condition produces a bounded, recorded outcome rather than an agent occupying a state whose tools cannot help.

#### Step 5.1: Declare the Fallback State and Its Context Profile

**Required Actions**:

- Declare exactly 1 fallback state per machine, reachable from 100 percent of non-terminal states, and prohibit a second fallback because two escape hatches produce two untested behaviours.
- Give the fallback state a context profile that admits the run's protected atoms, the transition journal summary, the refusal or detection record that caused entry, and nothing drawn from the state whose failure triggered entry.
- Give the fallback state the narrowest tool loadout in the machine, capped at 3 tool definitions, and exclude every tool with an irreversible effect class.
- Declare exactly 3 legal outgoing transitions from the fallback state: return to a named recovery state under a guard requiring the blocking condition to be resolved, terminate with status `blocked`, and escalate to a human owner.
- Set a fallback deadline no longer than 25 percent of the run's total deadline, so that an unresolved fallback terminates rather than persisting.
- Design the fallback state to fail closed: absent an admitted outgoing transition before its deadline, it terminates with status `blocked` rather than returning to the graph.

**Required Outputs**:

- One fallback state definition with a context profile, a loadout of at most 3 tools, 3 declared outgoing transitions, and a deadline.
- A reachability proof showing a fallback path from every non-terminal state.
- A fail-closed declaration naming the terminal status applied on deadline expiry.

**Quality Checkpoints**:

- Exactly 1 fallback state exists per machine; a second fallback blocks release.
- The fallback loadout contains at most 3 tools and 0 tools with an irreversible effect class.
- The fallback state is reachable from 100 percent of non-terminal states.
- Deadline expiry in the fallback state produces terminal status `blocked`; a silent return to the graph is a release-blocking defect.

***

#### Step 5.2: Enter the Fallback State on Declared Unmodelled Conditions

**Required Actions**:

- Enumerate the entry conditions as an explicit, closed list rather than treating the fallback as a general exception handler, so that entry is a modelled event with a recorded cause.
- Enter the fallback on any of: the 3rd consecutive illegal transition attempt within one state entry; the 2nd such attempt in a state authorizing a consequential effect; a non-progressing cycle with no enabled progress-independent exit; a 6th entry to any state; a state deadline expiry with no timeout transition declared; an assembly lookup failure caused by an unresolvable source binding; or an authority scope expiry with no approval path.
- Carry into the fallback exactly the protected atom set, the journal summary, and the causing record; drop the failing state's evidence partitions, because the material that produced the impasse is not the material that resolves it.
- Record the entry cause using a closed vocabulary of the 7 declared conditions, so that entry frequency can be attributed to a specific machine defect.
- Preserve the pre-entry state version and the full transition journal, so that the run can be replayed against the state definition that failed.
- Notify the run owner on entry where the run authorizes a consequential effect, without waiting for the deadline.

**Fallback Entry Condition Inventory**:

| Entry condition | Numeric trigger | Most likely defect |
| :-- | :-- | :-- |
| Consecutive illegal attempts | 3 in one state entry | Missing transition or over-tight guard |
| Illegal attempt in consequential state | 2 in one state entry | Missing approval path |
| Non-progressing cycle | 3 entries, 2 non-improving | Progress measure or exit guard wrong |
| Visit cap breach | 6th entry to one state | Cycle without an enabled exit |
| Deadline expiry, no timeout transition | 1 occurrence | Undeclared timeout handling |
| Unresolvable source binding | 1 occurrence | Stale or deleted store handle |
| Authority scope expiry, no approval path | 1 occurrence | Loadout placed in the wrong state |

**Required Outputs**:

- A fallback entry event carrying the entry condition, the numeric trigger observed, the pre-entry state version, and the journal summary reference.
- A carried-content manifest showing the protected atoms and the causing record admitted, and the partitions dropped.
- An owner notification record where the run authorized a consequential effect.

**Quality Checkpoints**:

- Every fallback entry names one of the 7 declared conditions; an entry recorded as other or unknown is a defect in the entry-condition list.
- The failing state's evidence partitions are absent from the fallback window; their presence indicates the impasse material was carried forward.
- The pre-entry state version and journal are preserved on 100 percent of entries; a lost journal makes the entry unattributable and unusable in Phase 6.

***

#### Step 5.3: Escalate When the Machine Does Not Fit

**Required Actions**:

- Treat fallback frequency as the primary measurement of machine fit, and compute it over a rolling window of at least 50 completed runs so that a single unusual run cannot move the verdict.
- Escalate for machine redesign where fallback entry exceeds 15 percent of runs in the window, where any single entry condition accounts for more than 30 percent of entries, or where any run records 2 or more fallback entries.
- Escalate immediately, without waiting for the window, where a fallback entry is caused by an unresolvable source binding or an authority scope expiry, because both indicate a definition that no longer matches its environment.
- Package an escalation as the entry condition distribution, the 5 most frequent source states at entry, the refusal cause breakdown from Step 4.2, and the specific transitions or guards implicated, not as a raw transcript.
- Suspend adoption of the machine for new consequential runs where the fallback rate exceeds 25 percent, and route those runs to a simpler fixed policy until a corrected machine version passes static validation.
- Record every escalation against the machine version, so that a redesign can be evaluated against the version it replaced rather than against an unversioned baseline.

**Required Outputs**:

- A machine fit report carrying the fallback rate, the entry condition distribution, the source state ranking, and the window size.
- An escalation package naming the implicated transitions, guards, and states with their versions.
- A suspension record where the 25 percent threshold was crossed, naming the fixed policy substituted.

**Quality Checkpoints**:

- The fallback rate is computed over at least 50 runs; a rate reported on a smaller sample is labelled provisional and never triggers suspension alone.
- Escalation occurs at 15 percent fallback rate, at 30 percent single-condition concentration, or at 2 fallback entries in one run; a machine exceeding any threshold without an escalation record is unmonitored.
- Unresolvable source bindings and authority scope expiries escalate on first occurrence; batching them into the rolling window is a defect.
- Every escalation names specific transitions, guards, or states; an escalation naming only a rate is not actionable and is returned for detail.

***

### Phase 6: Replay Audit and State Definition Correction

**Objective**: Log the state, its inputs, and the resulting assembly together so that a bad output is attributable to a named state definition, and feed confirmed attributions back into the machine as versioned corrections.

#### Step 6.1: Log State, Inputs, and Assembly Together

**Required Actions**:

- Write one journal record per state entry carrying the state identifier, the machine version, the state instance identifier, the entry cause, the resolved input reference set with immutable version identifiers, the assembly hash, the tool loadout identifier, and the instruction set version.
- Write one journal record per transition attempt carrying the source state, the trigger and its producer, every guard verdict with its guard version, the selected transition, the carry and drop sets, and the commit outcome.
- Record the three replay arguments together and never separately, because a state identifier without its input reference set and machine version cannot reproduce a window.
- Default to metadata-only logging: record content references, versions, and hashes rather than partition payloads, and store payloads in a separately authorized vault where retention is required.
- Prohibit persistence of hidden model reasoning; record the proposal label, the reason field, the evidence references, and the parse verdict, and treat a request for unrestricted internal transcripts as a boundary breach.
- Key every record by run, state instance, and attempt ordinal so that records order deterministically without depending on write time.

**Journal Record Field Inventory**:

```
RUN_ID:
MACHINE_VERSION:
STATE_INSTANCE_ID:
STATE_ID:
ENTRY_CAUSE:                [transition id | fallback condition | run start]
ENTRY_SEQUENCE:
INPUT_REFERENCE_SET:        [ref id -> immutable version id]
ASSEMBLY_HASH:
PARTITIONS_POPULATED:       [name -> admitted units, tokens, excluded count]
TOOL_LOADOUT_ID:
AUTHORITY_SCOPE_ID:
INSTRUCTION_SET_VERSION:
PROGRESS_MEASURE_VALUE:
VISIT_COUNT:
DEADLINE_REMAINING:
TRANSITION_ATTEMPTS:
  ATTEMPT_ORDINAL:
  TRIGGER_TYPE / PRODUCER:
  PROPOSED_LABEL / PARSE_VERDICT:
  GUARD_VERDICTS:           [guard id, version, verdict, reason code]
  SELECTED_TRANSITION_ID:
  CARRY_SET / DROP_SET:
  COMMIT_OUTCOME:
EXIT_REASON:
```

**Required Outputs**:

- An append-only journal carrying one entry record per state instance and one attempt record per transition attempt.
- A replay argument triple per state instance: state identifier, machine version, and resolved input reference set.
- A disclosure conformance record confirming zero persisted reasoning traces and zero raw payloads outside the authorized vault.

**Quality Checkpoints**:

- Every state entry record carries all 3 replay arguments; a record missing any one is unusable and counted as a logging defect.
- Every guard verdict carries its guard version; a verdict recorded without a version cannot be attributed after a guard change.
- The count of persisted hidden reasoning traces is 0; a single occurrence halts journal release and triggers re-instrumentation.
- Records order deterministically by run, state instance, and attempt ordinal without reference to write timestamps.

***

#### Step 6.2: Replay Runs and Verify Assembly Determinism

**Required Actions**:

- Replay a recorded run by supplying its journaled replay arguments to the assembly lookup and comparing each produced assembly hash against the recorded hash.
- Return recorded model outputs, tool results, and validator verdicts during replay rather than regenerating them, so that a hash mismatch is attributable to the assembly path and not to model variance.
- Sample at least 5 percent of completed runs for replay, and replay 100 percent of runs that entered the fallback state or recorded an illegal transition attempt.
- Treat any assembly hash mismatch as a zero-tolerance defect, halt promotion of the machine version, and identify the non-deterministic input by bisecting the input reference set.
- Fork rather than replay where regeneration is wanted: label the fork a counterfactual with a new lineage identifier, and never merge counterfactual results into a replay verdict.
- Replay every recorded run against the machine version it pinned, and never against a later version, because a mismatch under a different definition proves nothing about the original run.

**Required Outputs**:

- A replay report per sampled run carrying per-state hash comparisons and an overall match verdict.
- A non-determinism attribution record naming the input, guard, or source binding responsible for any mismatch.
- A counterfactual register keeping forked runs separate from replay verdicts.

**Quality Checkpoints**:

- The assembly hash match rate is 100 percent across replayed runs; any mismatch blocks promotion of the machine version.
- No model call, tool call, or external request occurs during replay; a live call during replay invalidates the replay verdict.
- At least 5 percent of completed runs and 100 percent of fallback or illegal-attempt runs are replayed in each release window.
- Every replay names the machine version it targets, and that version equals the version the original run pinned.

***

#### Step 6.3: Attribute Defects to State Definitions and Correct Them

**Required Actions**:

- Attribute every observed bad output to one of four sources before proposing a correction: the state's context profile admitted the wrong material, the tool loadout was wrong for the work, a guard was too tight or too loose, or the state graph lacked a needed state.
- Use the journal to test each attribution deterministically: compare the assembly hash and admitted partition contents against what the task required, compare the loadout against the tools the fallback or refusal records show were wanted, and compare guard verdicts against the transitions that were repeatedly proposed and denied.
- Reject an attribution that cannot be tested against a journal record, and route it to observation rather than to a machine change, so that definitions are not edited on impression.
- Express every correction as a new machine version carrying a changed profile, loadout, guard, or state set, and never as an in-place edit to a version that runs are pinned to.
- Route in-flight runs to the version they pinned and start new runs on the corrected version; where an in-flight run cannot continue under its pinned version, terminate it with status `blocked` rather than reinterpreting its state under a new definition.
- Re-run Phase 2 static validation and Step 1.3 determinism proof against every corrected version before release, and compare fallback rate on the first 50 runs against the version replaced.

**Defect Attribution Table**:

| Observed symptom | Journal evidence | Attributed to | Correction |
| :-- | :-- | :-- | :-- |
| Model answered from wrong material | Admitted partition contents lack the required reference | Context profile | Add source binding or admission rule |
| Model could not act despite correct material | Refusal records name a tool absent from loadout | Tool loadout | Move the tool into the state, or split the state |
| Legal work repeatedly refused | Repeated denials by one guard version | Guard too tight | Relax the predicate or add a transition |
| Consequential effect reached without review | Approval binding absent on committed effect | Guard too loose | Add an authorization guard |
| Fallback entered on a recurring situation | Entry condition concentrated on one source state | Missing state | Add the state with its own profile and loadout |
| Same output regardless of state | Equal assembly hashes across distinct states | Redundant state | Collapse into a typed field |

**Required Outputs**:

- A defect attribution record per investigated output, naming its source, its journal evidence, and its testability verdict.
- A machine version increment carrying the corrections and their static validation and determinism proof results.
- A version comparison record showing fallback rate and illegal attempt rate over the first 50 runs of the corrected version against the version replaced.

**Quality Checkpoints**:

- Every correction traces to at least 1 journal record; corrections without journal evidence are 0 in the released version.
- No machine version is edited in place; the count of in-place edits to a pinned version is 0.
- Every corrected version passes static validation and the 3-assembly determinism proof before release.
- The corrected version's fallback rate over its first 50 runs is at or below the replaced version's rate; a higher rate reverts the change.

***

## III. Implementation Guidance for AI Agents

AI agents operating a context state machine must follow systematic protocols ensuring that the active state is authoritative, that every window is reproducible from recorded arguments, and that no move occurs which a deterministic guard did not admit. The following guidance translates the six phases into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Definition Agent**: Builds and versions the machine definition, including states, context profiles, tool loadouts, transitions, guards, and progress measures. It owns Phases 1 through 3 and may not modify a version any run has pinned.
2. **Validation Agent**: Runs static graph validation and the determinism proof, and issues the pass or fail release verdict bound to a machine version. It may veto release and never issues a partial pass.
3. **Dispatcher**: Holds the state register, enumerates declared transitions, evaluates guards in declared order, resolves priority, and commits successor state, journal entry, and assembly hash atomically. It is the only component permitted to write the state register.
4. **Context Assembler**: Executes the assembly lookup for the entered state, admits units through the umbrella admission gate, enforces partition bounds, and computes the assembly hash. It holds the tokenizer and the partition ledger and admits no model preference above a partition bound.
5. **Task Executor**: Performs the open-vocabulary work inside the active state and emits exactly one structured transition proposal per checkpoint. It calls only tools in the active loadout and never writes the register, widens a loadout, or extends a deadline.
6. **Audit Agent**: Replays sampled runs, compares assembly hashes, attributes defects to state definitions, and computes the machine fit report. It may withhold promotion of a machine version and may suspend adoption at the declared fallback rate.

**Authority Rule**: The Task Executor proposes and the Dispatcher admits. Where the two disagree the Dispatcher holds authority without exception, and the proposal is recorded with its denial reason rather than overridden. No component other than the Dispatcher writes the state register, and no component other than the Context Assembler places a unit into an outgoing context package.

**Workflow Execution Pattern**:

```
STATE: State_Entry_And_Assembly
INPUTS:
  1. Target state id and pinned machine version from the committed transition
  2. Resolved input reference set with immutable version identifiers
  3. Carry set delivered by the transition; drop set already discarded
ACTIONS:
  1. Read the target state's context profile from the pinned machine definition
  2. Populate declared partitions from their source bindings in assembly order
  3. Apply the admission gate per partition; record admitted and excluded counts
  4. Serialize the tool loadout in its fixed order into the tool-definition partition
  5. Compute the assembly hash over the serialized context package
  6. Append the state entry journal record with all three replay arguments
VALIDATION:
  - unbound_partition_count == 0
  - partition_tokens_within_bounds == TRUE
  - protected_atoms_present == TRUE
  - loadout_size <= 8
  - assembly_hash_recorded == TRUE
  - visit_count <= visit_cap
TRANSITIONS:
  IF all_validations_pass THEN next_state = Model_Work_Within_State
  IF unbound_partition_count > 0 THEN next_state = Fallback_Entry
  IF protected_atoms_present == FALSE THEN next_state = Assembly_Halt
  IF visit_count > visit_cap THEN next_state = Cycle_Handling
```

**Two-Phase Action Pattern**: Emit the proposed transition with its label, reason, and evidence references without applying any carry set or effect; evaluate the guards while no partition has been cleared and no effect committed; apply the carry set, run the assembly lookup, and commit only after every guard admits, recording the proposal and the verdicts in the same operation.

**Approval Gate**: Human authorisation is required before any transition into a state whose loadout carries an irreversible effect class, before any release of a machine version whose static validation reports 1 or more findings, before any suspension override where the fallback rate exceeds 25 percent, and before any change to a guard classified as authorization. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the state register, the transition journal, and the input reference resolution record in durable stores, since a run may span many context windows and the register is authoritative across all of them.
- Serialize the tool-definition partition in a fixed order so that the loadout contributes to a stable prefix within an epoch, adopting the stable prefix and epoch definitions from the context-lifecycle guidance.
- Write a handoff record at every context boundary carrying the active state, the machine version, the input reference set, the progress measure value, and the visit count, so that the state survives the boundary rather than being re-inferred.
- Charge the machine's own overhead, comprising guard evaluation, journal writes, and assembly hashing, to the run budget rather than treating it as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: State Inventory Integrity (After Phase 1)**

- **Automated Check**: Non-terminal state count is between 4 and 12; every state passes at least 1 retention criterion; every populated partition carries a source binding; partition maxima plus output reserve are within the context budget in 100 percent of states; the 3-assembly determinism proof passes for every state.
- **Agent Action on Pass**: Proceed to transition specification.
- **Agent Action on Failure**: Halt and return the offending states with their failing criterion; no transition is specified against an incomplete inventory.
- **Human Review Trigger**: A state count above 12 after decomposition, or a state whose required material cannot be bound to any durable source.

**Checkpoint 2: Machine Validity (After Phase 2)**

- **Automated Check**: Zero-guard transitions are 0; unreachable states are 0; dangling transition targets are 0; priority collisions are 0; every cycle carries a progress measure, a visit cap, and a progress-independent exit; the fallback state is reachable from 100 percent of non-terminal states.
- **Agent Action on Pass**: Proceed to tool-surface binding.
- **Agent Action on Failure**: Halt release and return the full validation report; a subset of failures is never waived.
- **Human Review Trigger**: A cycle for which no progress measure can be defined, or a state from which no terminal state is reachable.

**Checkpoint 3: Surface Containment (After Phase 3)**

- **Automated Check**: No loadout exceeds 8 tools; generic state-mutation tools are 0; every irreversible-effect tool sits in an approval-guarded state; every authority scope expiry is at or below its state deadline; callable sets resolve from the register on 100 percent of invocations.
- **Agent Action on Pass**: Proceed to runtime execution.
- **Agent Action on Failure**: Block deployment and name the offending loadout and state; an over-wide surface is never accepted with a monitoring commitment.
- **Human Review Trigger**: A tool with an irreversible effect class required in a state that cannot carry an approval guard.

**Checkpoint 4: Runtime Control Validity (Continuous, After Phase 4)**

- **Automated Check**: Exactly 1 transition commits per accepted trigger; effects emitted under refusal are 0; every refusal carries 1 of the 4 cause classifications; the visit cap of 5 is enforced; tight loops do not repeat more than twice.
- **Agent Action on Pass**: Continue the run.
- **Agent Action on Failure**: Halt the run and preserve the journal; an invalid control decision is never executed with a warning attached.
- **Human Review Trigger**: An ambiguity halt caused by equal priorities, or a partial commit across state, journal, and hash.

**Checkpoint 5: Fallback Discipline (After Phase 5)**

- **Automated Check**: Exactly 1 fallback state exists; its loadout is at most 3 tools with 0 irreversible-effect tools; every entry names 1 of the 7 declared conditions; deadline expiry produces terminal status `blocked`; the pre-entry journal is preserved on 100 percent of entries.
- **Agent Action on Pass**: Release the machine fit report.
- **Agent Action on Failure**: Withhold the report and name the unclassified entries; an entry recorded as unknown is a defect in the condition list, not a data gap.
- **Human Review Trigger**: A fallback rate above 15 percent, a single condition above 30 percent of entries, or 2 fallback entries in one run.

**Checkpoint 6: Replay and Attribution (After Phase 6)**

- **Automated Check**: Assembly hash match rate is 100 percent; live model or tool calls during replay are 0; at least 5 percent of runs and 100 percent of fallback or illegal-attempt runs were replayed; persisted reasoning traces are 0; every correction traces to at least 1 journal record.
- **Agent Action on Pass**: Promote the machine version.
- **Agent Action on Failure**: Block promotion and name the non-deterministic input or the untraceable correction.
- **Human Review Trigger**: Any assembly hash mismatch, or any correction proposed without journal evidence.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
MACHINE_VERSION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: State Drift Between Register and Window**

- **Symptoms**: The model acts as though a different state is active; a tool is requested that the previous state exposed; instructions from a superseded state appear in output; the register and the serialized instruction set version disagree.
- **Diagnostic Steps**: Compare the instruction set version and tool loadout identifier in the last assembly record against the register entry for the same state instance; determine whether a carry set delivered stale instruction content, whether a partition was repopulated from a cached package, or whether a boundary crossing lost the register read.
- **Resolution Protocol**: Option A, discard the window and re-run the assembly lookup from the register, since the register is authoritative and the window is a transport. Option B, add the drifted field to the transition's drop set so it cannot survive the move. Option C, where the drift crossed a context boundary, correct the handoff record to carry the active state and machine version explicitly.
- **Escalation Trigger**: Drift detected in 2 runs within one release window escalates to a definition review, because a carry set that leaks instruction content is a definition defect rather than a runtime accident.

**Error Type 2: Legal Work Blocked by an Over-Tight Guard**

- **Symptoms**: The same transition is proposed and denied repeatedly by one guard version; fallback entries concentrate on one source state; the refusal cause breakdown is dominated by policy denial for work the run is authorized to do.
- **Diagnostic Steps**: Group denials by guard identifier and version, and determine whether the denial reflects a genuine authorization boundary, a missing evidence reference the run could obtain, or a predicate that encodes an assumption the environment no longer satisfies.
- **Resolution Protocol**: Option A, add a transition to an evidence-gathering state whose exit guard the run can satisfy, rather than relaxing the blocking guard. Option B, relax the predicate where the denial is provably not an authorization boundary, and record the relaxation against a new machine version. Option C, split the source state so that the blocked work occupies a state whose loadout and guards fit it.
- **Escalation Trigger**: One guard version accounting for more than 30 percent of denials in a 50-run window escalates for definition review; an authorization guard is never relaxed without human approval regardless of denial volume.

**Error Type 3: Assembly Non-Determinism**

- **Symptoms**: Replay produces an assembly hash unequal to the recorded hash; two runs entering the same state with the same input reference set produce different packages; output quality varies between runs the journal records as identical.
- **Diagnostic Steps**: Bisect the input reference set to isolate the varying source; check the lookup for wall-clock reads, random draws, unordered iteration over sets or maps, and any model call; confirm every reference resolved to an immutable version rather than to a moving pointer.
- **Resolution Protocol**: Option A, promote the varying input to a resolved reference supplied as an argument, so the variation is recorded rather than hidden. Option B, impose a total order on any iteration whose order was previously incidental. Option C, where the source itself is genuinely mutable, pin a snapshot version at run start and record the pin.
- **Escalation Trigger**: Any hash mismatch blocks promotion of the machine version immediately; 2 mismatches traced to distinct causes escalate to a review of the determinism contract rather than to a third individual fix.

**Error Type 4: Tool Surface Escape Attempt**

- **Symptoms**: Invocations name tools absent from the active loadout; a tool result or a retrieved document names a state, a transition, or an approval; a proposal label falls outside the state's allowlist; a request appears to widen the authority scope.
- **Diagnostic Steps**: Trace the requested tool and the proposing content to their source; determine whether the request originated in the instruction set, in model output, or in untrusted retrieved or tool-delivered text; check whether the allowlist serialized into the window matched the register.
- **Resolution Protocol**: Option A, refuse and return the typed refusal with the unchanged allowlist, which is the default path. Option B, quarantine the source content, revoke any delegated credential issued in the state, and re-enter the state with the offending partition excluded. Option C, where the tool is genuinely needed, add it to a new state with its own approval guard rather than widening the existing loadout.
- **Escalation Trigger**: Any escape attempt traceable to untrusted retrieved or tool-delivered content escalates immediately for a security review; the count of loadout widenings performed in response to model requests is 0 without exception.

**Error Type 5: Non-Progressing Cycle**

- **Symptoms**: A state is entered 3 or more times with a flat progress measure; consecutive returns to a state carry identical assembly hashes; budget consumption rises while the journal records no change in admitted references.
- **Diagnostic Steps**: Compare progress measure values across entries; determine whether the measure is wrong for the cycle, whether the exit guard depends on the cycle's own output, or whether the repopulated partitions are identical because the source binding returns a cached result.
- **Resolution Protocol**: Option A, route to the declared progress-independent exit. Option B, replace the progress measure with one the cycle can actually move, since a measure that never changes cannot detect anything. Option C, add an exit whose guard depends on an external validator rather than on the cycle's own output.
- **Escalation Trigger**: The 3-entry, 2-non-improvement signature triggers the bounded response on every occurrence; a 6th entry to any state halts the run and enters the fallback state regardless of the measure.

**Error Type 6: Machine Misfit and Fallback Saturation**

- **Symptoms**: Fallback entries exceed 15 percent of runs; one entry condition dominates; runs record 2 or more fallback entries; operators describe routine work as not fitting any state.
- **Diagnostic Steps**: Rank source states at fallback entry, break down entry conditions, and separate the 4 refusal causes so that machine gaps are distinguished from malformed proposals and genuine policy denials.
- **Resolution Protocol**: Option A, add the missing state with its own context profile and loadout where entries concentrate on one recurring situation. Option B, merge or widen states where entries scatter across many source states without a common cause, since scattering indicates the decomposition is too fine. Option C, suspend the machine for consequential runs and route them to a fixed policy while a corrected version is built and validated.
- **Escalation Trigger**: A fallback rate above 25 percent suspends adoption for consequential runs; a rate above 15 percent escalates for redesign; unresolvable source bindings and authority scope expiries escalate on first occurrence rather than on a rate.

**Troubleshooting Decision Tree**:

```
DISPATCHER DETECTS A PROBLEM
├─ TRANSITION DEFECT
│   ├─ No declared transition for (state, trigger) → Refuse; return allowlist; count attempt
│   ├─ Every candidate guard-denied → Refuse; return reason code; count attempt
│   ├─ Two eligible transitions, equal priority → HALT on ambiguity; require definition repair
│   └─ Third consecutive refusal in one entry → Enter fallback; preserve journal
├─ ASSEMBLY DEFECT
│   ├─ Partition has no source binding → Enter fallback; escalate on first occurrence
│   ├─ Protected atoms absent after carry → HALT; re-anchor from durable store
│   ├─ Partition bound exceeded → Evict per declared order; never borrow the output reserve
│   └─ Replay hash mismatch → Block promotion; bisect input reference set
├─ SURFACE DEFECT
│   ├─ Tool outside active loadout requested → Refuse; return typed refusal
│   ├─ Request traced to untrusted content → Quarantine source; revoke credentials; escalate
│   └─ Approval binding missing on effect → Block effect; enter fallback
├─ PROGRESS DEFECT
│   ├─ Three entries, two non-improving → Route to progress-independent exit
│   ├─ Identical consecutive assembly hashes → Record tight loop; break after two
│   └─ Sixth entry to one state → HALT; enter fallback
└─ FIT DEFECT
    ├─ Fallback rate above 15 percent → Escalate for machine redesign
    ├─ Fallback rate above 25 percent → Suspend adoption for consequential runs
    └─ Single condition above 30 percent of entries → Add or merge the implicated state
```

### D. Performance Metrics and Continuous Learning

**Reproducibility and Audit Metrics**:

- **Assembly hash match rate**: Replayed state entries whose hash equals the recorded hash, over replayed state entries (target: 100 percent; any mismatch blocks promotion).
- **Replay coverage**: Completed runs replayed, over completed runs (target: at least 5 percent overall and 100 percent of fallback or illegal-attempt runs).
- **Journal completeness**: State entry records carrying all 3 replay arguments, over state entry records (target: 100 percent; below 100 percent the run is unattributable).
- **Attribution rate**: Investigated bad outputs attributed to a named state definition with journal evidence, over investigated bad outputs (target: at least 80 percent; a lower rate indicates the journal field set is too thin).

**Control Validity Metrics**:

- **Illegal attempt rate**: Refused transition attempts, over transition attempts, broken down by the 4 causes (target: below 5 percent, with machine gaps below 1 percent).
- **Ambiguity rate**: Attempts with 2 or more eligible transitions at equal priority, over attempts (target: 0; any occurrence is a definition defect).
- **Out-of-surface invocation rate**: Tool invocations naming a tool outside the active loadout, over invocations (target: below 1 percent; any instance traced to untrusted content is zero-tolerance).
- **Non-progressing cycle rate**: Runs recording the cycle signature, over runs entering a cyclic region (target: below 10 percent).
- **Commit integrity**: Transitions committing state, journal entry, and hash atomically, over commits (target: 100 percent).

**Fit and Cost Metrics**:

- **Fallback rate**: Runs entering the fallback state, over completed runs, over a window of at least 50 runs (target: below 15 percent; above 25 percent suspends consequential adoption).
- **State utilization**: States entered at least once in a representative window, over declared states (target: at least 80 percent; unentered states are candidates for removal).
- **Loadout utilization**: Tools invoked at least once from a state, over tools declared in that state's loadout (target: at least 50 percent; a lower figure indicates an over-wide surface).
- **Machine overhead**: Tokens, latency, and cost consumed by guard evaluation, journal writes, and assembly hashing, over total run cost (target: no more than 10 percent).
- **Definition churn**: Machine versions released in a window, over windows (target: declining across successive windows; rising churn indicates the state decomposition has not stabilised).

**Learning and Adaptation Mechanisms**:

- **Journal-bound corrections**: Change a state definition only where a journal record supports the attribution; an impression without a record is routed to observation, never to an edit.
- **Version-paired evaluation**: Compare every corrected version against the version it replaced on fallback rate, illegal attempt rate, and loadout utilization over the first 50 runs of each.
- **Threshold recalibration**: Recompute every numeric threshold per deployment against observed distributions; the values here are deployment defaults, not measured constants.
- **State pruning**: Remove states whose utilization is 0 across 2 consecutive windows and whose removal leaves every terminal state reachable, since an unentered state still carries validation and maintenance cost.

**Human-in-the-Loop Boundaries**: Relaxation of an authorization guard, placement of an irreversible-effect tool in a new state, override of a suspension at a fallback rate above 25 percent, promotion of a machine version whose static validation reports findings, and in-place modification of a version any run has pinned are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs which information and which capabilities are available at each point of a run, not the content of any particular run. Its phases hold wherever the legal ordering of work is partly known in advance, the required tool set changes between phases, and a window must be reconstructible after the fact.

### 4.1 Cross-Domain Application Patterns

**Regulated financial operations**: The gate returns adopt because the ordering of intake, verification, authorization, execution, and settlement is fixed by obligation rather than by preference. States separate evidence gathering from authorization, and the execution loadout carrying payment or transfer tools sits behind an approval guard that binds the approval to the exact operation, its arguments, its amount, and an expiry. The journal becomes a deliverable rather than a diagnostic aid, because a supervisor asks which state authorized an action and against which definition, and the replay argument triple answers that question directly.

**Clinical documentation and care coordination**: States correspond to intake, history review, assessment, plan drafting, and handoff, and each admits a different evidence partition under a different sensitivity rule. The context profile is the mechanism that keeps material out of the window rather than a policy that discourages its use: a state whose profile does not populate a partition cannot expose that partition's content, which is a structural property rather than an instruction the model may misread. The fallback state carries only protected atoms and routes to a named human role, because an unmodelled clinical situation is escalated rather than improvised.

**Industrial field service and dispatch**: The environment supplies frequent external triggers, so states are short-lived and transitions are dominated by tool results and timer expiries rather than by model proposals. Reversibility varies within one run, since a provisional assignment is reversible while a dispatched crew is not, so the irreversible-effect tools occupy one approval-guarded state and the remainder occupy states reachable without approval. Visit caps and progress measures carry most of the control weight here because retry against a flaky field system is the dominant failure mode.

**Software engineering and release management**: States separate investigation, change drafting, validation, and release, and the loadout changes sharply between them: read and search tools in investigation, write tools in drafting, execution tools in validation, and deployment tools only in an approval-guarded release state. The tight-loop signature is the most valuable detector in this domain, because an agent rebuilding an identical window and re-running an identical failing check is the characteristic waste pattern.

**Public-sector case adjudication**: The legal ordering of steps and the evidence standard for each are declared externally, so the machine encodes an existing procedure rather than inventing one. Guards evaluate whether the declared evidence for a determination is present and current, and a determination reached without that evidence is refused rather than flagged. Replay supports the appeal path: the state, the admitted material, and the definition version together reconstruct what was before the decision-maker.

**Scientific and research pipelines**: States separate question framing, source retrieval, extraction, synthesis, and reporting, and the progress measure is requirement coverage rather than elapsed effort. The cycle detector matters because retrieval and synthesis form a natural loop that can consume unbounded budget while covering no new requirement, and the progress-independent exit is a coverage validator external to the synthesis itself.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Collapse to the adopt-minimal shape of 3 to 5 states with one gated state for consequential tools, retain the fallback state and the journal, and drop cycle detection where no cyclic region exists. Machine overhead above 10 percent of run cost indicates the gate should have returned decline.
- **High-risk or irreversible work**: Retain every phase, bind every irreversible-effect tool behind an approval guard, replay 100 percent of runs rather than a 5 percent sample, and prefer terminal status `blocked` over an unverified completion.
- **Strict latency budgets**: Reduce the number of states rather than removing guards, since removing guards removes the machine while reducing states removes only granularity. Where latency forbids a durable register write per transition, batch journal writes but never batch the register commit, because the register is what makes the active state authoritative.
- **Long-horizon autonomous runs**: Persist the register, journal, and input reference resolution outside working context, write a handoff record at every context boundary carrying the active state and machine version, and re-run the determinism proof at each version change so drift is detected rather than inherited.
- **Multi-agent deployments**: Give each agent its own machine and its own register, and treat a sub-agent's completion as a trigger offered to the parent machine rather than as authority to change the parent's state. Assign single-writer ownership per state field; where two agents write one field, declare a deterministic merge rule and never permit last-write-wins for approvals, permissions, or effects.
- **Concurrent regions within one run**: Where independent concerns genuinely progress in parallel, declare orthogonal regions with exactly one active state each, declare a join rule and a merge rule per shared field before the fan-out, and cap the parallel branch count so that the reachable configuration set stays enumerable by static validation.

***

## V. Limitations and Considerations

**Rigidity is the method's structural cost**: A machine admits only what its states model, so work that does not fit the declared states is blocked rather than improvised. The consequence is that a machine built from an incomplete understanding of the work converts variety into refusals. The mitigation is the fallback state in Phase 5, which gives every unmodelled situation a defined behaviour, together with the escalation thresholds that treat fallback frequency as evidence about the machine rather than as noise about the runs.

**State proliferation raises cost faster than it raises control**: Every additional state multiplies definitions, guards, validation output, and maintenance surface, and a machine can become harder to reason about than the work it governs. The consequence is that a nominally safe machine is deployed without anyone having read its validation report. The mitigation is the retention test in Step 1.1, the 12-state cap before mandatory decomposition, and the state pruning rule in Section III.D that removes states with 0 utilization across 2 consecutive windows.

**A reproducible window is not a reproducible output**: The assembly lookup guarantees that the same state with the same inputs produces the same context package; it guarantees nothing about the model's response to that package. The consequence is that a run can be perfectly replayable and still produce a different answer on a fresh generation. The mitigation is to record model outputs, tool results, and validator verdicts and return them during replay, and to keep counterfactual forks in a separate register so that regeneration is never mistaken for replay.

**Every numeric threshold here is a deployment default**: The 12-state cap, the 8-tool loadout limit, the 3-attempt and 3-entry signatures, the 5-visit cap, the 15 and 25 percent fallback rates, the 5 percent replay sample, and the 10 percent overhead ceiling were chosen to be operable on first deployment, not derived from measurement. The consequence is that a deployment adopting them uncritically may block legitimate work or permit waste. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute thresholds against observed distributions and to record the recomputation against a machine version.

**Fallback rate measures fit only where the entry conditions are complete**: The 7 declared entry conditions cover the impasses this framework anticipates, and a situation outside them may surface as a stalled run rather than as a fallback entry. The consequence is a machine that appears to fit better than it does. The mitigation is the rule that a fallback entry recorded as unknown is treated as a defect in the condition list, and the requirement that stalled runs reaching a state deadline with no timeout transition enter the fallback rather than expiring silently.

**Deterministic guards can encode an environment that has changed**: A guard is a fixed predicate over a snapshot, and an environment that moves beneath it produces confident, well-formed refusals of work that is now legitimate. The consequence is a machine that degrades quietly rather than failing loudly. The mitigation is the escalation on unresolvable source bindings and authority scope expiries at first occurrence, and the 30 percent single-guard denial concentration trigger that routes a dominant guard to definition review.

**The journal is rich enough to be a disclosure hazard**: A record complete enough to reconstruct a window is complete enough to leak the material that window carried. The consequence is that an audit capability becomes an exposure surface. The mitigation is metadata-only logging by default, content references and hashes in place of payloads, payload retention only in a separately authorized vault, and the prohibition on persisting hidden model reasoning, with a single occurrence halting journal release.

**Structural validity is not correct purpose**: A machine can pass every static check, replay perfectly, and hold a fallback rate near zero while modelling the wrong procedure. The framework detects malformed control, not misdirected work, and no checkpoint here substitutes for human review of whether the declared states describe what should happen.

***

## VI. Conclusion and Summary

A context state machine trades flexibility for reproducibility. It replaces the open-ended question of what should occupy the window now with a table read against a declared state, and it replaces a general tool catalog with a loadout bound to that state. The gain is that a window becomes rebuildable from three recorded values, that a defect becomes attributable to a named definition, and that an entire class of tool misuse becomes unreachable rather than discouraged. The loss is flexibility, and the loss is real: work outside the declared states is refused, not accommodated.

The method is therefore only as good as its escape hatch and its measurement. A machine with a fallback state, seven declared entry conditions, and a monitored fallback rate treats its own misfit as evidence and corrects against it. A machine without one converts every unmodelled situation into an agent occupying a state whose tools cannot help, which is worse than the accumulation of history it replaced.

A team adopting the pattern should build the register, the journal, and the assembly lookup before building an elaborate graph. Start with 4 to 6 states, one gated state holding every consequential tool, a fallback state, and a determinism proof. Collect 50 runs, read the fallback rate and the refusal cause breakdown, and add states only where entries concentrate. Formal analysis, durable workflow engines, and model checking earn their cost later, where concurrency, long duration, or regulatory exposure make test coverage insufficient on its own.

**Key Success Factors**:

- **Composition is a lookup, not a negotiation**: The active state and the machine version determine the context profile, and the profile plus resolved input references determine the package, so the same state with the same inputs yields the same window.
- **Proposal and admission are separated**: A model proposes exactly one transition from a closed allowlist and a deterministic guard admits it; schema conformance is never mistaken for legality, and the model never widens its own tool surface.
- **Every transition carries a guard and a declared effect**: A transition names its trigger, its guard set, what is carried across, and what is dropped; a transition without a guard fails static validation rather than running as a suggestion.
- **The escape hatch is declared, narrow, and measured**: One fallback state with at most 3 tools, seven closed entry conditions, a fail-closed deadline, and numeric escalation at 15 percent, 30 percent concentration, or 2 entries in one run.
- **Loops and illegal moves have numeric signatures**: Three consecutive refusals in one state entry, three entries with two non-improvements, identical consecutive assembly hashes, and a sixth visit each carry a bounded response rather than a warning.
- **The journal makes correction possible**: State, inputs, and assembly are logged together, replay verifies the assembly hash, and no state definition changes without a journal record supporting the attribution.

By following this guide, AI agents can make the contents of a context window a declared property of a named state rather than an artefact of accumulated history, so that a window can be rebuilt, a defect can be attributed, and a capability can be withheld structurally rather than by instruction.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them, using the labels that guide carried; they were not independently re-verified in the course of this conversion except where an entry is marked as verified. The list carries no inline markers, because the operational form attributes material to phases and steps rather than to individual sentences.

**Corpus pointers**:

- `Context State Machines: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the state, event, guard, action, invariant, and terminal-state contracts, the transition evaluation order, the formal model selection criteria, the concurrency and merge semantics, the failure-mode and bounded-recovery inventory, the observability field inventory, the metric definitions, and the production readiness checklist. Its external citations are transcribed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the umbrella guidance for the category. Source of the partition, context package, context budget, output reserve, admission gate, assembly order, and protected atom definitions adopted unchanged here.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — companion guidance on read-time admission. Source of the context assembler, tool loadout, tool catalog, deferred definition, and admission threshold terms adopted in Phases 1 and 3.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — companion guidance on bounded delegation. Source of the authority scope rule and the closed terminal status vocabulary used by terminal states and the fallback state.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — companion guidance on the time dimension of context. Source of the epoch, stable prefix, context boundary, and handoff record terms, and the owner of lifecycle stage transitions, which are distinct from the state transitions specified here.
- `advanced_task_guides/context-management/guide_KVCacheAwarePromptConstruction.md` — companion guidance on exact-prefix reuse and its economics. The fixed serialization order required of the tool-definition partition in Step 3.1 and restated in Section III exists to serve it, and cache write, read, expiry, and bypass are observations and effects within the states specified here rather than states of their own.
- `advanced_task_guides/context-management/guide_HierarchicalContextArchitecture.md` — companion guidance on scope, inheritance, and delegation, applicable to the multi-agent adaptation in Section 4.2.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — companion guidance on context failure modes, applicable to the drift, staleness, and contradiction symptoms in Section III.C.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — companion guidance in the memory-management category. Source of the protected atom membership list and the handoff record content classes referenced in Phases 1 and 5.
- `advanced_task_guides/planning/guide_PlanExecuteDecoupling.md` — companion guidance on separating plan formation from execution, applicable to the proposal and admission split in Step 3.3.
- `advanced_task_guides/planning/guide_TaskManagementOrchestration.md` — companion guidance on orchestrating multi-step work across agents, applicable to the control plane components in Section III.A.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on telemetry and event schema design, applicable to the journal record field inventory in Step 6.1.

**External references**:

*Formal models of state, hierarchy, and concurrency*

1. Harel, statecharts paper — https://www.wisdom.weizmann.ac.il/~harel/papers/Statecharts.pdf
2. W3C, *SCXML* — https://www.w3.org/TR/scxml/
3. van der Aalst and colleagues, workflow-net soundness — https://research.tue.nl/files/3361919/636105.pdf
4. Lamport, *TLA+* home and tools — https://lamport.azurewebsites.net/tla/tla.html

*Event sourcing, durable execution, and workflow engines*

5. Martin Fowler, *Event Sourcing* — https://martinfowler.com/eaaDev/EventSourcing.html
6. Martin Fowler, *CQRS* — https://martinfowler.com/bliki/CQRS.html
7. Temporal, *Workflow Execution* — https://docs.temporal.io/workflow-execution
8. Temporal, *Event History* — https://docs.temporal.io/workflow-execution/event
9. Temporal, *Worker Versioning* — https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning
10. AWS, *Step Functions error handling* — https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html
11. AWS, *Parallel workflow state* — https://docs.aws.amazon.com/step-functions/latest/dg/state-parallel.html
12. AWS, *Map workflow state* — https://docs.aws.amazon.com/step-functions/latest/dg/state-map.html
13. AWS, *Step Functions versions and aliases* — https://docs.aws.amazon.com/step-functions/latest/dg/concepts-cd-aliasing-versioning.html
14. AWS, *Step Functions redrive* — https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html
15. Restate, *Key concepts* — https://docs.restate.dev/foundations/key-concepts
16. Inngest, *How functions are executed* — https://www.inngest.com/docs/learn/how-functions-are-executed
17. Microsoft Azure, *Saga pattern* — https://learn.microsoft.com/en-us/azure/architecture/patterns/saga

*Graph orchestration and agent architecture*

18. LangGraph, *Graph API* — https://docs.langchain.com/oss/python/langgraph/graph-api
19. LangGraph, *Use subgraphs* — https://docs.langchain.com/oss/python/langgraph/use-subgraphs
20. LangGraph, *Persistence* — https://docs.langchain.com/oss/python/langgraph/persistence
21. LangGraph, *Interrupts* — https://docs.langchain.com/oss/python/langgraph/interrupts
22. Anthropic, *Building effective agents* — https://www.anthropic.com/engineering/building-effective-agents
23. OpenAI, *Structured Outputs* — https://developers.openai.com/api/docs/guides/structured-outputs

*Security, verification, testing, and observability*

24. OWASP, *LLM06:2025 Excessive Agency* — https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
25. AgentDojo — https://arxiv.org/html/2406.13352
26. Agentproof — https://arxiv.org/html/2603.20356v1
27. Event-driven checking for agentic systems — https://arxiv.org/html/2509.20364v1
28. Hypothesis, *Stateful testing* — https://hypothesis.readthedocs.io/en/latest/stateful.html
29. OpenTelemetry, *GenAI agent spans* — https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/

*Retrieved and verified during conversion*

30. Anthropic, *Effective context engineering for AI agents* — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
31. LangChain, *Context overview* — https://docs.langchain.com/oss/python/concepts/context
