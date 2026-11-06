# Context Engineering Framework Selection

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context engineering framework selection constitutes the task family of deciding which parts of a project's context-management machinery are adopted from an external framework, which are owned by the application, and on what evidence that decision is made. This guide provides AI agents with a structured protocol organised around a closed inventory of eight capabilities that any context-management stack must supply, an obligation class fixing whether a framework must supply each capability, may supply it, or is better left to the application, and an evaluation procedure that establishes fit by measurement on the project's own workload rather than by vendor claim. It specifies a build-versus-adopt determination with numeric triggers, a framework-free reference path held as a control specimen, a frozen benchmark corpus with thresholds declared before results are seen, a fidelity audit that diffs the intended context package against the rendered one, a lock-in assessment scoring what each candidate captures, and an exit rehearsal that must pass before adoption rather than after. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a framework is retained only while measured evidence continues to justify its cost.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Context engineering framework**: Any library, software development kit, runtime, or hosted platform that supplies part of the machinery for assembling, mutating, persisting, delegating, or observing what reaches a model at an inference boundary. The category spans thin provider clients, graph and workflow runtimes, retrieval and ingestion frameworks, memory services, declarative optimizers, typed application boundaries, protocol substrates, and trace and evaluation backends.

**Capability**: One named unit of context-management machinery, drawn from the closed inventory of eight in Section 1.2. Capabilities are the unit of selection. A framework is never adopted as a whole; it is adopted for named capabilities against named acceptance tests.

**Obligation class**: The declared answer, fixed per capability before any candidate is examined, to whether an external framework must supply the capability, may supply it, or is better left to the application. The class governs whether a candidate's absence of the capability is disqualifying, neutral, or preferred.

**Context package**: The complete serialized input for one call, comprising every partition in declared assembly order together with the accounting record that produced it. The term is adopted unchanged from the category's umbrella guidance.

**Partition**: A named region of the context budget reserved for one purpose, carrying a maximum token count, a floor where the purpose is protected, and a declared position in assembly order. Adopted unchanged from the category's umbrella guidance.

**Context budget**: The usable input allowance, computed as total window capacity minus the output reserve and operational headroom. It is an accounted quantity, not an estimate.

**Intent manifest**: The application-authored declaration, produced before any framework renders anything, of the ordered segments intended for one call, each carrying its authority, provenance, target partition, and expected token cost. The intent manifest is the reference against which the rendered context package is diffed.

**Rendered context package**: The exact serialized request as it stands after every framework, adapter, middleware, and provider-client transformation, immediately before transport. A stack that cannot produce this artifact, or a keyed hash over its canonicalized form, cannot be audited.

**Unattributed mutation**: Any difference between the intent manifest and the rendered context package that no declared cause explains. Expected adapter mapping, approved framework injection, and provider-required transformation are attributed differences; everything else is unattributed and blocks release.

**Package fidelity**: The proportion of audited calls whose rendered context package carries zero unattributed mutation. It is the primary evidence that a framework has not silently taken ownership of assembly.

**Reference path**: The framework-free implementation of one representative task, built directly against the provider client, retained for the life of the system as the control specimen for measurement, upgrade comparison, and exit. The reference path is a permanent candidate in every selection, not a throwaway prototype.

**Capability class**: A grouping of candidates that occupy the same abstraction level and supply an overlapping capability set. Candidates are compared within and across classes; named products are instances of a class observed at a stated date, not the classes themselves.

**Assembly record**: The immutable per-call log of what was considered, what was admitted, where it was placed, why, and at what token cost. Adopted unchanged from the category's selection guidance, and the artifact that makes observability of admission testable.

**Handoff record**: The bounded state package written at every context boundary, carrying the contract version, the protected set, the durable-store references, and enough state to rebuild working context. Adopted unchanged from the category's lifecycle guidance.

**Protected atom**: A content element that must survive every eviction, compaction, truncation, and boundary crossing without loss. Adopted unchanged from the category's umbrella guidance.

**Stable prefix**: The leading region of the rendered context package whose bytes do not change across the calls intended to share a cache entry. Adopted unchanged from the category's cache-aware construction guidance.

**Captured asset**: Anything a framework holds that is costly to take elsewhere: a state or checkpoint format, an assembly convention, a memory schema, a trace format, an evaluation dataset store, a prompt or policy registry, or a hosted control-plane feature with no local equivalent.

**Extraction difficulty**: The score from 1 to 5 assigned to each captured asset, where 1 denotes a documented export into an open format and 5 denotes an asset with no export path and no local equivalent.

**Exit path**: The declared, written procedure for removing a framework, naming for each captured asset the export mechanism, the target format, the replay target, and the estimated engineering effort in working days.

**Exit rehearsal**: The executed test in which canonical state is exported from a candidate and replayed through the reference path. It is run before adoption, not after.

**Bill of materials**: The enumerated set of every layer that can alter the rendered context package, each pinned to an exact version: framework, adapters, provider clients, serializers, tokenizers, middleware, memory processors, tool registries, and protocol implementations.

**Trust class**: The provenance-derived label naming the authority of a unit's source. Adopted unchanged from the category's umbrella guidance. A framework never changes a unit's trust class by handling it.

**Reason code**: A normalised categorical label recorded with every capability verdict, mutation classification, gate outcome, and adoption decision, drawn from a closed vocabulary. Free-text rationale is recorded alongside a reason code, never in place of one.

**Adoption verdict**: One value from the closed vocabulary `adopt`, `build`, `defer`, or `reject`, issued once per capability requirement at the end of evaluation, each carrying the measured evidence that produced it.

### 1.2 The Capability Inventory and Its Obligation Classes

The inventory is closed at eight entries and is derived from the specialist guides in this category, which define what context management actually requires. Selection proceeds capability by capability. A framework that supplies six capabilities well and hides one that the project marked framework-must-supply is disqualified on that one, and aggregate scoring never rescues it.

Three obligation classes are available, and exactly one is assigned per capability before any candidate is examined:

- **Framework-must-supply**: The application cannot own the capability without reimplementing the framework's internals, so a candidate that does not expose it is rejected outright.
- **Framework-may-supply**: The capability can be owned either way. The decision falls to the build-versus-adopt determination in Section 1.4 and to measured evidence.
- **Application-owned**: The capability is policy the application must hold, because delegating it moves a correctness decision outside the code that is accountable for it. A framework that performs the capability automatically is acceptable only where the behaviour is named, disableable, and logged.

Assigning a capability to the application-owned class does not release a candidate from obligation. Every capability carries an exposure requirement: the artifact or measurement the framework must make available regardless of who owns the policy. A candidate that owns the policy silently and exposes nothing fails the capability whatever its class.

**Capability Inventory With Obligation Classes and Acceptance Tests**:

| Capability | Obligation class | Framework exposure requirement | Acceptance test |
| :-- | :-- | :-- | :-- |
| Budget partitioning and accounting | Application-owned | Per-partition serialized token counts under the deployed tokenizer, computed before dispatch | Counts reported for 100 percent of partitions match an independent count within 1 percent |
| Admission and selection | Application-owned | An insertion point at which the application decides admission, and no injection of units the application did not admit | Zero unadmitted units appear in the rendered package across the certification corpus |
| Compression with verification | Application-owned | Every automatic summarisation, compaction, history trimming, or tool-result clearing named, disableable, and logged with its inputs and outputs | Each automatic operation is disabled by configuration and the disablement is observable in the rendered package |
| Isolation and delegation | Framework-may-supply | Per-sub-context budget ledger, authority scope, write scope, and a typed result envelope boundary | A delegated unit runs under a declared authority scope and returns a schema-conformant envelope in 100 percent of trials |
| Durable externalization | Framework-may-supply | Canonical state in a documented, exportable schema separable from framework internals | Exported state replays in the reference path with 100 percent of protected atoms intact |
| Boundary handoff | Framework-may-supply | A handoff record from which working state can be rebuilt after a process restart | Reconstruction from the handoff record alone succeeds in 100 percent of restart trials |
| Observability of admission and use | Framework-must-supply | Rendered package capture or keyed hash, per-call assembly record, and export through an open telemetry protocol | At least 95 percent of eligible spans carry identity, version, package hash, token usage, and status fields |
| Cache-aware assembly | Framework-may-supply | Byte-stable stable prefix across logically identical calls, and provider-reported cache-read and cache-write token counts | Prefix hash is identical across at least 95 percent of calls declared to share one cache family |

Two capabilities carry a class the project may not override. Observability of admission and use is framework-must-supply in every deployment, because a stack whose rendered package cannot be inspected cannot be evaluated, audited, upgraded safely, or left. Compression with verification is application-owned in every deployment, because an automatic transformation that discards a protected atom is a correctness failure the framework has no basis to adjudicate. The remaining six classes are set per project and recorded with a reason code.

Architecture-level long context, meaning modified attention mechanisms and bounded-memory model variants, sits below the layer this guide addresses and is out of scope. Frameworks are evaluated on what they do to the context package an agent can construct, inspect, and replay, never on properties of model internals no runtime exposes.

### 1.3 The Execution Tier Partition

The method divides across three execution tiers, and the division is what separates an operational selection from an opinion about tooling. Every phase in Section II is assignable to exactly one tier, and every step that crosses tiers names the handoff and the authority.

**Deterministic tier**: Software, scripts, schema validators, tokenizers, and queries own the capability checklist evaluation, the benchmark harness execution, every measurement reported, the intent-manifest to rendered-package diff, the dependency and version accounting, and the exit rehearsal. This tier owns exactness, reproducibility, and auditability. It rejects any capability verdict lacking an executed acceptance test, any measurement lacking a recorded trial count, any candidate whose rendered package cannot be captured, and any adoption record whose bill of materials carries an unpinned layer.

**Model tier**: An LLM call owns interpreting a project's stated workload into capability requirements, proposing the obligation class for each of the six adjustable capabilities, drafting the stratification of the benchmark corpus, judging qualitative fit between a candidate's abstraction and the team's practices, and proposing the extraction path for each captured asset. This work requires open-vocabulary judgement over natural-language requirements that no deterministic rule covers.

**Hybrid tier**: The model proposes and software verifies in three places. Capability requirement derivation is model-proposed and deterministically checked against the closed inventory, so a requirement outside the eight is rejected rather than admitted. Difference classification in the fidelity audit is model-proposed and deterministically checked against the approved-mutation fixture, so an unrecognised difference is escalated rather than explained away. Exit-path construction is model-proposed and settled by the exit rehearsal, so an export the model believed feasible is not credited until an export actually replays.

**Authority when tiers disagree**: The deterministic tier holds authority in every disagreement without exception. A model judgement that a candidate fits is overridden by a failed acceptance test, a missed numeric bar, or a failed exit rehearsal. A model classification of a package difference as benign is overridden by the absence of that difference from the approved-mutation fixture.

**An adoption decision is never made on model judgement alone.** No adoption verdict is valid without measured evidence produced by the harness on the project's own workload. Vendor documentation, feature matrices, popularity, and model assessment of fit are inputs to candidate identification and to the qualitative fit record; they are never inputs to the adoption verdict. A candidate that no harness has run against the project's own corpus receives the verdict `defer`, never `adopt`.

### 1.4 Build Versus Adopt, and the Dating Rule for Named Products

Much of what a context-engineering framework supplies is a few hundred lines of deterministic bookkeeping: a token ledger, a partition table, an ordered serializer, a checkpoint writer. A team may reasonably prefer to own that code rather than inherit a dependency whose upgrade cadence it does not control. The determination is made per capability, before candidates are examined, and is recorded with its estimate.

**Build-Versus-Adopt Trigger Conditions**:

| Condition observed for one capability | Determination | Consequence for evaluation |
| :-- | :-- | :-- |
| Owned implementation estimated at 400 lines or fewer, no durable service to operate, 2 or fewer new dependencies | Build | Capability removed from the candidate scoring; candidates are not credited for supplying it |
| Estimate between 401 and 1,200 lines | Contested | Decided by exit cost rather than build cost; the lower measured exit cost wins |
| Owned implementation estimated above 1,200 lines | Adopt | Capability enters candidate scoring as a weighted requirement |
| Capability requires operating a durable service the team does not already run | Adopt | Capability enters scoring; operating cost enters total ownership |
| Capability sits on a framework-must-supply obligation that every candidate fails | Build | A thin owned layer is written; selection continues for the remaining capabilities |
| Three or more required capabilities cluster in one candidate at estimates above 1,200 lines each | Adopt | Candidate carries a coherence credit recorded separately from capability scores |
| Capability is regulated evidence, tenant separation, or authorization enforcement | Build | Never delegated to a framework; enforced outside the model in application-owned code |

Build estimates are systematically optimistic. Every estimate above 400 lines is multiplied by 1.5 before the determination is applied, and the raw and adjusted figures are both recorded.

**The dating rule**: Named products are volatile. Feature sets, maintenance ownership, defaults, and licences change on a timescale shorter than most systems live, and a guide organised around product names becomes actively misleading rather than merely stale. This guide therefore organises selection around capability classes, and permits product names only as instances of a class observed at a stated date. Every product name carried anywhere in a selection record must appear with the date on which the observation was made and the source of the observation. A product name never appears as a requirement, a recommendation, or a section heading. Where a selection record names a product, the capability claim attached to it is established by the harness in Phase 4, never by the list that produced the candidate.

***

## II. Operational Framework: Capability-Led Selection Under Measured Evidence and a Rehearsed Exit

The framework runs once per selection decision and again at every scheduled re-evaluation. Phases 1 through 5 are sequential and each consumes the prior phase's artifacts. Phase 6 begins at adoption and runs for the life of the dependency, returning control to Phase 1 whenever a re-evaluation trigger fires. No phase may be skipped on the grounds that a candidate is already in use; an incumbent framework is a candidate like any other and is measured against the reference path on the same corpus.

### Phase 1: Workload Contract and Capability Requirement Derivation

**Objective**: Convert the project's stated needs into a bounded set of capability requirements with obligation classes and executable acceptance tests, so that later evaluation measures declared requirements rather than whatever the candidates happen to offer.

#### Step 1.1: Declare the Workload Contract

**Required Actions**:

- Enumerate the task families the system serves, and for each record the context sources, the expected call volume per day, the p95 latency budget in milliseconds, and the consequence class from low, moderate, or high.
- Record state lifetime per task family: whether context must survive a single call, a session, a process restart, or an indefinite retention period with a deletion obligation.
- Record every tool effect the system may perform, marking each reversible or irreversible, and record the authority scope under which it runs.
- Record data classes, tenant boundaries, residency constraints, retention limits, and deletion obligations, since these determine which capabilities may be delegated at all.
- Record concurrency, recovery objectives, and the model providers in use, including whether provider portability is a hard requirement.
- Halt the selection where any of task families, consequence class, state lifetime, or data classes is unknown; a framework is not selected against an undeclared workload.

**Required Outputs**:

- A workload contract naming every task family with its volume, latency budget, and consequence class.
- A state-lifetime record and a tool-effect record with reversibility marked per entry.
- A data-class record naming tenant boundaries, residency constraints, retention limits, and deletion obligations.

**Quality Checkpoints**:

- Every task family carries a numeric volume figure and a numeric latency budget; a family carrying neither halts the phase.
- Every tool effect is marked reversible or irreversible; unmarked effects are treated as irreversible until classified.
- The contract names at least 1 provider and states whether portability is a hard requirement or a preference.

***

#### Step 1.2: Derive Capability Requirements From the Contract

**Required Actions**:

- Map each contract element to the capabilities in Section 1.2 that it exercises, producing a requirement per capability rather than per contract element.
- Reject any proposed requirement that does not resolve to one of the eight inventory capabilities; the inventory is closed, and a requirement outside it is either a restatement of an existing capability or an application feature that no framework decision governs.
- Mark each capability required, conditional, or not required, and for conditional entries state the contract condition under which the requirement becomes binding.
- Record the consequence class the capability inherits, taken as the highest consequence class among the task families that exercise it.
- Record which specialist guide in this category owns the capability's correctness definition, and import that guide's invariants as constraints on the requirement.

**Required Outputs**:

- A capability requirement record with one entry per inventory capability, marked required, conditional, or not required.
- A consequence class assigned per required capability.
- An owning-guide reference per required capability, naming the invariants imported.

**Quality Checkpoints**:

- Exactly 8 entries appear in the requirement record, one per inventory capability; a shorter record indicates an unexamined capability.
- Every conditional entry names the contract condition that activates it; conditional entries without a condition are promoted to required.
- No requirement is stated that a candidate could satisfy by naming a feature rather than by passing a test.

***

#### Step 1.3: Assign Obligation Classes and Executable Acceptance Tests

**Required Actions**:

- Assign one obligation class per required capability, holding observability of admission and use at framework-must-supply and compression with verification at application-owned in every deployment.
- Attach to every required capability an acceptance test that a script can execute against a candidate and that returns pass or fail without interpretation.
- Attach a numeric bar to every acceptance test, using the inventory defaults in Section 1.2 unless the consequence class justifies a stricter figure, and record any deviation with its reason code.
- Declare which requirements are hard gates, where failure rejects the candidate outright, and which are weighted, where failure reduces a score.
- Verify that at least 1 hard gate exists per capability marked high consequence; a high-consequence capability with only weighted requirements is a scoring artifact rather than a control.

**Required Outputs**:

- An obligation class per required capability with a reason code for every project-set class.
- An acceptance test suite with one executable test and one numeric bar per required capability.
- A hard-gate list separated from a weighted-requirement list.

**Quality Checkpoints**:

- Every acceptance test returns pass or fail without interpretation; tests requiring judgement are rewritten or reassigned to the qualitative fit record.
- Every numeric bar names the action taken when it is breached, and no bar is stated without a consequence.
- Every high-consequence capability carries at least 1 hard gate.

***

### Phase 2: Build-Versus-Adopt Determination

**Objective**: Decide per capability whether the project owns the implementation or admits an external dependency, before candidates are named, so that the candidate set is shaped by the determination rather than the determination by the candidates.

#### Step 2.1: Estimate the Owned-Implementation Cost per Capability

**Required Actions**:

- Estimate for each required capability the size of a deterministic owned implementation in lines, counting only the bookkeeping the capability needs and excluding application domain logic.
- Multiply every estimate above 400 lines by 1.5, and record the raw and adjusted figures separately.
- Record whether the owned implementation would require operating a durable service the team does not already run, and name the service.
- Record the number of new external dependencies the owned implementation would introduce, and the ongoing maintenance surface in engineer-days per quarter.
- Record the capabilities that regulation, tenant separation, or authorization enforcement removes from delegation entirely, since these are built regardless of estimate.

**Required Outputs**:

- A per-capability build estimate carrying raw lines, adjusted lines, new dependency count, and quarterly maintenance days.
- A service-requirement record naming any durable service an owned implementation would oblige the team to operate.
- A non-delegable list naming capabilities that regulation or authorization removes from the candidate set.

**Quality Checkpoints**:

- Every estimate above 400 raw lines carries an adjusted figure computed at the 1.5 multiplier; unadjusted estimates are rejected.
- Every capability on the non-delegable list names the regulation, tenant boundary, or authorization obligation that placed it there.
- No estimate is recorded without naming the bookkeeping it covers.

***

#### Step 2.2: Apply the Adopt Trigger and Record the Determination

**Required Actions**:

- Apply the trigger conditions in Section 1.4 to each capability, producing one determination from build, adopt, or contested.
- Resolve every contested determination by comparing exit cost rather than build cost, deferring the resolution to Phase 5 where the exit cost is not yet estimable and marking it pending.
- Remove every build determination from candidate scoring, so that candidates are neither credited nor penalised for supplying a capability the project has decided to own.
- Record a coherence credit where 3 or more adopt determinations cluster in one capability class, since the integration cost of separate owned implementations is real and unmeasured by per-capability estimates.
- Restate the requirement set as an adoption brief naming only the capabilities that carry an adopt or pending determination.

**Required Outputs**:

- A build-versus-adopt determination per required capability, each with its trigger condition and reason code.
- A pending list naming contested capabilities awaiting exit-cost evidence from Phase 5.
- An adoption brief carrying only the capabilities candidates will be scored on.

**Quality Checkpoints**:

- Every determination names the trigger condition that produced it; determinations without a trigger are re-derived.
- The adoption brief contains no capability carrying a build determination.
- Contested capabilities are marked pending rather than resolved by preference, and no candidate is scored on a pending capability before Phase 5 returns its exit cost.

***

### Phase 3: Candidate Identification and Reference Path Construction

**Objective**: Assemble a bounded candidate set spanning distinct abstraction levels, screen it against hard gates before any measurement is spent, and construct the framework-free reference path that every later measurement is compared against.

#### Step 3.1: Enumerate Capability Classes and Bound the Candidate Set

**Required Actions**:

- Identify the capability classes that could supply the adoption brief, describing each class by the capabilities it typically covers and the abstraction level it occupies, not by the products in it.
- Populate each relevant class with at most 3 candidate instances, recording for each the date of observation and the source of the observation.
- Retain the reference path as a permanent candidate in every class comparison; a selection in which the framework-free option was not carried through to measurement is invalid.
- Cap the total candidate set at 4 entries including the reference path, since comparison cost grows with the corpus multiplied by the candidate count and rarely repays a fifth entry.
- Select candidates from at least 2 distinct abstraction levels, so that the comparison tests whether the abstraction level is right rather than only which product within one level is preferred.

**Capability Classes and Instances Observed in the Source Material as of September 2026**:

| Capability class | Capabilities the class typically covers | Instances named in the source material |
| :-- | :-- | :-- |
| Direct provider client | Assembly, cache-aware construction, observability at the boundary | Provider software development kits used without an orchestration layer |
| Graph and workflow runtime | Isolation and delegation, boundary handoff, durable externalization | LangGraph, Microsoft Agent Framework, Semantic Kernel, CrewAI |
| Retrieval and ingestion framework | Admission and selection, durable externalization | LlamaIndex, Haystack |
| Agent loop software development kit | Isolation and delegation, boundary handoff, observability | OpenAI Agents SDK, Claude Agent SDK, Mastra |
| Prompt-resident memory service | Durable externalization, boundary handoff | Letta |
| Typed application boundary | Admission and selection, budget accounting | Pydantic AI |
| Declarative optimizer | None directly; optimizes assembly parameters | DSPy |
| Trace and evaluation backend | Observability of admission and use | LangSmith, Langfuse, Arize Phoenix, Braintrust, W and B Weave, Ragas, DeepEval, promptfoo |
| Protocol substrate | Boundary handoff, isolation across process boundaries | MCP, A2A, AG-UI, OpenTelemetry |

The instances in the right-hand column are recorded as observations carried by the source material at one date. They are not recommendations, not an exhaustive census, and not capability claims: a product's presence in a row asserts only that the source material positioned it there. Every capability claim about any instance is established by the harness in Phase 4 and is void without it.

**Required Outputs**:

- A capability class inventory describing each relevant class by capability coverage and abstraction level.
- A candidate set of at most 4 entries including the reference path, each carrying an observation date and source.
- An abstraction-level record confirming at least 2 distinct levels are represented.

**Quality Checkpoints**:

- The candidate set contains the reference path; a set without it is rejected before screening.
- Candidate count does not exceed 4, above which measurement cost is not recoverable within a bounded evaluation.
- Every named instance carries an observation date; instances without one are removed rather than dated by assumption.

***

#### Step 3.2: Screen Candidates Against Hard Gates Before Any Benchmark

**Required Actions**:

- Run the three universal screens against every candidate before any corpus is executed: whether the rendered context package can be captured or hashed, whether canonical state can be exported in a documented format, and whether the security, tenant separation, and deletion obligations in the workload contract can be met.
- Reject outright any candidate failing a universal screen, and record the rejection with its evidence rather than carrying the candidate forward at a reduced score.
- Verify the licence and hosted-service terms against the intended deployment model, including modification, redistribution, hosted use, and data handling, and reject any candidate whose current terms do not permit it.
- Record the maintenance signals available for each candidate: release cadence, published compatibility policy, security response record, and the count of interfaces documented as experimental that the adoption brief would depend on.
- Reject any candidate depending on 2 or more experimental interfaces for capabilities marked high consequence.

**Required Outputs**:

- A screening record per candidate with a verdict and evidence on each of the three universal screens.
- A licence and terms verdict per candidate against the intended deployment model.
- A maintenance signal record naming release cadence, compatibility policy, security response, and experimental interface dependencies.

**Quality Checkpoints**:

- Every rejection carries evidence; a candidate is never rejected on reputation or on absence from a documentation search.
- No candidate proceeds to measurement with an unresolved licence verdict.
- Screening consumed no benchmark execution; a screen requiring the corpus is reclassified as a Phase 4 measurement.

***

#### Step 3.3: Construct the Framework-Free Reference Path

**Required Actions**:

- Implement one representative happy path and one representative failure path directly against the provider client, with the application constructing the ordered context package itself.
- Instrument the reference path to emit the intent manifest, the rendered context package or its keyed hash, per-partition token counts, and provider-reported usage including cache-read and cache-write tokens.
- Record the reference path's baseline measurements on the frozen corpus: task success, p50 and p95 latency, input and output tokens, and cost per successful task.
- Retain the reference path under version control for the life of the system, and re-run its baseline at every re-evaluation so that comparisons use a contemporaneous control rather than a historical figure.
- Bound reference path construction to 10 working days; where the happy path cannot be built directly in that window, record which capability made it infeasible, since that capability carries the strongest adopt case in the brief.

**Required Outputs**:

- A framework-free reference implementation covering 1 happy path and 1 failure path.
- A baseline measurement record carrying task success, latency percentiles, token counts, and cost per successful task.
- A construction record naming any capability that made direct implementation infeasible within the bound.

**Quality Checkpoints**:

- The reference path emits the intent manifest and the rendered context package; a reference path without both cannot serve as the fidelity control.
- Baseline measurements were produced on the same frozen corpus every candidate will run, not on an ad hoc set.
- Reference path construction completed within 10 working days, or the overrun is recorded as adopt evidence for the blocking capability.

***

### Phase 4: Evidence-Based Evaluation on the Project's Own Workload

**Objective**: Establish every capability claim by measurement on a frozen corpus drawn from the project's own workload, under thresholds declared before results are seen, so that adoption rests on evidence rather than on documentation.

#### Step 4.1: Freeze the Benchmark Corpus and Declare Thresholds Before Results

**Required Actions**:

- Assemble a corpus of at least 60 cases drawn from the project's own traffic or from realistic constructions of it, spanning at least 8 declared strata with at least 5 cases per stratum.
- Include as strata the ordinary path, long-context cases, tool-heavy cases, interrupted and resumed runs, adversarial and injection cases, no-answer cases, authorization and deletion cases, and provider-error cases.
- Freeze the corpus, the provider models, the tool stubs, the state fixtures, and the scoring functions, and record a corpus version identifier that every later measurement cites.
- Declare every threshold in the measurement table before any candidate runs, and record the declaration with a timestamp, since a threshold set after results are seen measures nothing.
- Declare the repeated-trial count for stochastic cases at no fewer than 3, and declare which strata require cold and warm cache trials separately.

**Measurement Set and Numeric Bars for Candidate Acceptance**:

| Measurement | Definition | Numeric bar | Consequence of breach |
| :-- | :-- | :-- | :-- |
| Package fidelity | Audited calls with zero unattributed mutation, divided by audited calls | At least 99 percent overall; exactly 100 percent on high-consequence strata | Below bar rejects the candidate; this gate is never waived on output quality |
| Task success delta | Candidate task success minus reference path task success on the frozen corpus | No worse than 2 percentage points below the reference path | Below bar rejects the candidate for that capability |
| Framework token overhead | Candidate input tokens minus reference path input tokens on matched cases | No more than 15 percent | Above 15 percent requires a written justification naming the capability bought; above 25 percent rejects |
| Framework latency overhead | Candidate p95 latency minus reference path p95 latency on matched cases | No more than 20 percent | Above 20 percent requires justification; above 40 percent rejects on any latency-bound path |
| Cost per successful task | Total model, framework, retrieval, tool, and storage cost divided by successful tasks | No more than 1.15 times the reference path | Above bar requires the capability credit to be named and quantified |
| Cache preservation | Provider-reported reused prefix tokens divided by expected reusable prefix tokens | At least 90 percent where the candidate claims cache support | Below 70 percent rejects the candidate for high-volume paths |
| State reconstruction | Restart trials in which working state rebuilt from the handoff record alone | Exactly 100 percent | Any failure rejects the boundary-handoff capability |
| Trace completeness | Eligible spans carrying identity, version, package hash, usage, and status fields, divided by eligible spans | At least 95 percent | Below bar rejects the observability capability, which is framework-must-supply |
| Upgrade replay pass rate | Previously passing frozen cases still passing after an in-range version upgrade | At least 98 percent | Below 95 percent rejects the candidate; between 95 and 98 percent defers pending a second upgrade trial |
| Export replay success | Exported runs successfully replayed in the reference path, divided by attempted exports | Exactly 100 percent on protected atoms | Any loss of a protected atom rejects the candidate |

**Required Outputs**:

- A frozen corpus of at least 60 cases across at least 8 strata, carrying a version identifier.
- A declared threshold record timestamped before the first candidate execution.
- A trial protocol naming repeated-trial counts and the strata requiring separate cold and warm cache runs.

**Quality Checkpoints**:

- Corpus size is at least 60 cases with at least 5 per stratum; a thinner corpus produces intervals too wide to separate candidates.
- Every threshold carries a declaration timestamp preceding the first execution; thresholds declared afterwards are void.
- The corpus draws from the project's own workload; a corpus assembled from vendor examples measures the vendor rather than the project.

***

#### Step 4.2: Execute the Harness Across Candidates Under Matched Conditions

**Required Actions**:

- Implement the smallest equivalent path in each candidate, adding no candidate-exclusive feature unless that feature is registered as a separate treatment with its own measurement.
- Run every candidate against the identical frozen corpus, provider models, tool stubs, state fixtures, and network conditions, and record any condition that could not be matched.
- Run cold and warm cache trials, repeated trials at the declared count, concurrency trials, deliberate process restarts, and induced dependency failures, since capability claims that hold only on the ordinary path are not capability claims.
- Attempt one version upgrade inside each candidate's supported range and replay the corpus, so that upgrade friction is measured before commitment rather than discovered after it.
- Change one factor at a time when investigating a result, and re-run the whole affected stratum rather than the failing case alone.

**Required Outputs**:

- A per-candidate measurement record covering every entry in the measurement set, with trial counts and unmatched conditions named.
- An upgrade replay record per candidate carrying the pass rate and the cause of every regression.
- A failure classification per failed case, drawn from application logic, model variance, framework mutation, adapter defect, provider behaviour, scoring error, or infrastructure fault.

**Quality Checkpoints**:

- Every measurement cites the corpus version identifier and a trial count; measurements without both are discarded.
- Candidate implementations are equivalent in scope; a candidate carrying an extra feature is remeasured or the feature is registered as a separate treatment.
- Every failed case carries a classification; unclassified failures block the phase, because an unexplained failure is the most likely place a hidden defect sits.

***

#### Step 4.3: Run the Fidelity Audit and Attribute Every Difference

**Required Actions**:

- Capture four representations per audited call: the intent manifest, the objects passed into the candidate, the rendered context package, and the provider receipt evidence including request identifier and reported usage.
- Canonicalize only representation details declared semantically irrelevant, preserving ordering, roles, content blocks, tool schemas, cache controls, and provider settings.
- Diff the intent manifest against the rendered context package by sequence and segment, and classify every difference as expected adapter mapping, approved framework injection, application defect, version-induced mutation, provider-required transformation, or unattributed mutation.
- Verify authority ordering: framework-injected text may not outrank application policy in the assembled package, and any inversion is a hard failure regardless of measured output quality.
- Recompute per-partition token counts after every attributed difference, and identify the displacement each mutation causes against the declared budget.
- Compare stable-prefix hashes across logically identical calls, identify the first divergent segment for every unexpected miss, and record the invalidation cause.
- Add every approved mutation to a versioned expectation fixture, and block release where any unattributed mutation remains, reducing the framework layer or instrumenting a lower boundary rather than waiving the finding.
- Where policy prohibits storing content, compute keyed hashes over canonicalized segments and retain encrypted samples in a restricted store; never certify a candidate on hashes alone, since a reviewer needs sampled content to explain a difference.

**Required Outputs**:

- A four-representation capture set per audited call, or its keyed-hash equivalent under a content-minimisation policy.
- A difference classification record with a cause assigned to every difference and a first divergent segment for every unexpected cache miss.
- A versioned approved-mutation fixture, and an unattributed-mutation count with its severity per candidate.

**Quality Checkpoints**:

- Unattributed mutation count is 0 on the certification corpus; any residual count blocks the adoption verdict.
- No authority inversion appears in any audited call; a single inversion rejects the candidate.
- Every approved mutation appears in the expectation fixture with a version, so that a later upgrade reintroducing it is detected rather than re-approved.

***

### Phase 5: Lock-In and Exit-Path Assessment

**Objective**: Establish what each candidate captures, how hard it is to take elsewhere, and what removal would cost, and prove the exit by rehearsal before adoption rather than discovering it under duress afterwards.

#### Step 5.1: Inventory Captured Assets and Score Extraction Difficulty

**Required Actions**:

- Enumerate the captured assets per candidate across the four standing categories: state and checkpoint format, assembly conventions, memory schemas, and trace formats.
- Extend the enumeration to the conditional categories present in the deployment: evaluation dataset stores, prompt and policy registries, hosted control-plane features with no local equivalent, and credentials issued by the platform.
- Score extraction difficulty from 1 to 5 per asset, where 1 is a documented export into an open format, 3 is an export requiring an application-written converter, and 5 is an asset with no export path and no local equivalent.
- Record for each asset at difficulty 4 or 5 what specifically resists extraction, since the description determines whether an owned adapter can reduce the score.
- Compute the candidate's lock-in profile as the count of assets at each difficulty level, and never as an average, which conceals a single unextractable asset behind several easy ones.

**Captured Asset Categories and Extraction Evidence Required**:

| Captured asset category | What is at risk | Evidence required before adoption |
| :-- | :-- | :-- |
| State and checkpoint format | Runs and threads unresumable outside the framework | A documented schema and an executed export of at least 10 runs |
| Assembly conventions | Prompts unreproducible when the layer is removed | A rendered package captured for every call class and reproducible from the intent manifest |
| Memory schemas | Accumulated durable memory unreadable elsewhere | An export carrying identity, provenance, version, and retention fields per record |
| Trace formats | Historical evidence lost on migration | Export through an open telemetry protocol preserving identifiers, hierarchy, timing, usage, and status |
| Evaluation dataset store | Regression suite unrunnable against a successor | A dataset export in a documented format with case and version identifiers preserved |
| Prompt and policy registry | Release history and rollback targets lost | An export carrying every version, its author, its activation window, and its release linkage |
| Hosted control-plane feature | Behaviour with no local equivalent to migrate to | A named local substitute, or a recorded decision that the feature is abandoned on exit |

**Required Outputs**:

- A captured asset inventory per candidate covering the four standing categories and every conditional category present.
- An extraction difficulty score from 1 to 5 per asset, with a resistance description for every score of 4 or 5.
- A lock-in profile per candidate expressed as counts by difficulty level.

**Quality Checkpoints**:

- Every candidate carries at least the 4 standing asset categories; an inventory omitting one is incomplete rather than favourable.
- Every score of 4 or 5 names what resists extraction; an unexplained high score cannot be reduced by an owned adapter and is treated as 5.
- The lock-in profile reports counts by level and no averaged figure appears in the adoption record.

***

#### Step 5.2: Execute the Export-and-Replay Exit Rehearsal

**Required Actions**:

- Export canonical state for at least 10 runs spanning at least 3 strata, including 1 interrupted run and 1 run carrying durable memory writes.
- Replay every exported run through the reference path, and compare protected atoms, tool-effect records, and terminal outcomes against the original run.
- Record the export replay success rate on protected atoms, which must be exactly 100 percent, and record every atom lost with the asset category that lost it.
- Export the trace record for the same runs through an open telemetry protocol, and verify that identifiers, span hierarchy, timing, token usage, error status, and evaluation linkage survive the export.
- Time the rehearsal and record the engineering effort actually consumed, since the rehearsal produces the only non-speculative input to the exit cost estimate.
- Repeat the rehearsal for the incumbent framework at every re-evaluation, since an exit path proven at adoption decays as schemas and versions move.

**Required Outputs**:

- An exit rehearsal record covering at least 10 exported runs across at least 3 strata.
- An export replay success rate on protected atoms with every loss attributed to an asset category.
- A trace export verification record naming any field that did not survive.
- A measured rehearsal effort figure in engineer-days.

**Quality Checkpoints**:

- Export replay success on protected atoms is exactly 100 percent; any loss rejects the candidate regardless of every other measurement.
- The rehearsal covered at least 1 interrupted run and at least 1 run carrying durable memory writes, since these are where exports usually fail.
- Rehearsal effort is measured rather than estimated, and the measured figure supersedes any prior estimate.

***

#### Step 5.3: Cost the Exit and Record the Removal Conditions

**Required Actions**:

- Estimate total exit cost in working days from the measured rehearsal effort scaled to full production state volume, adding converter development for every asset at difficulty 3 or above.
- Resolve every contested build-versus-adopt determination from Phase 2 by comparing the exit cost against the adjusted build estimate, choosing build wherever exit cost exceeds the adjusted build estimate.
- Escalate for named human approval any candidate whose exit cost estimate exceeds 20 working days, whose lock-in profile carries any asset at difficulty 5, or that would become the third framework in the stack.
- Write the exit path before adoption, naming per captured asset the export mechanism, the target format, the replay target, and the estimated effort, and store it beside the adoption record rather than in a ticket.
- Declare the removal conditions: the measured thresholds, licence changes, maintenance signals, or workload changes that would oblige a re-evaluation ahead of schedule.

**Required Outputs**:

- An exit cost estimate in working days derived from measured rehearsal effort.
- Resolutions for every contested determination carried forward from Phase 2.
- A written exit path stored with the adoption record, and a declared removal condition set.

**Quality Checkpoints**:

- Every contested determination from Phase 2 is resolved; a pending determination blocks adoption.
- The exit path names an export mechanism per captured asset; an asset with no named mechanism is scored at difficulty 5 and escalated.
- Removal conditions are stated as measurable triggers, not as intentions to review.

***

### Phase 6: Adoption Under Version-Risk Control and Scheduled Re-Evaluation

**Objective**: Commit the decision with its evidence, pin every layer that can alter the context package, gate every upgrade through replay, and return to Phase 1 on a schedule or on a trigger.

#### Step 6.1: Issue the Adoption Verdict and Pin the Dependency Surface

**Required Actions**:

- Issue exactly one adoption verdict per capability requirement from adopt, build, defer, or reject, each citing the measurements that produced it.
- Refuse an adopt verdict for any capability where a hard gate failed, and never average a failed hard gate against passing weighted requirements.
- Record the decision with its rejected alternatives, its measured evidence, its version pins, its owner, its next review date, and its removal conditions.
- Enumerate the bill of materials covering every layer that can alter the rendered context package, pinning each to an exact version rather than a range.
- Register the approved-mutation fixture, the frozen corpus version, the reference path revision, and the exit path as release artifacts subject to the same review as application code.

**Required Outputs**:

- An adoption verdict per capability requirement with cited measurements.
- A decision record naming rejected alternatives, owner, next review date, and removal conditions.
- A bill of materials with exact version pins for every context-altering layer.

**Quality Checkpoints**:

- No capability carries an adopt verdict with a failed hard gate; a single failed hard gate is decisive.
- Every layer in the bill of materials carries an exact version; a range pin fails the checkpoint because a range admits an unreviewed upgrade.
- The decision record names an owner and a review date; a record without both is not a decision.

***

#### Step 6.2: Gate Every Upgrade Through Replay

**Required Actions**:

- Treat every framework, adapter, provider client, serializer, tokenizer, middleware, memory processor, and protocol upgrade as an application behaviour change, never as a routine dependency patch.
- Read migration notes, diff dependency manifests, and render deterministic fixtures without dispatching them, comparing intended and rendered packages before any traffic is involved.
- Re-run the fidelity audit, then replay the frozen corpus covering quality, security, cache, state, resume, deletion, and provider-error strata.
- Run a rotating sample of at least 20 recent production cases alongside the frozen corpus, since a frozen corpus alone cannot detect workload drift.
- Compare package fidelity, unattributed mutation count, cache preservation, token overhead, latency overhead, and cost per successful task against the current release, and block promotion on any hard gate failure.
- Shadow the upgrade, then canary by low-risk stratum, and promote only after canary traffic has covered representative long sessions, tool effects, cache opportunities, and restarts rather than after a fixed elapsed period.

**Required Outputs**:

- A per-upgrade replay record carrying the frozen corpus result, the rotating sample result, and the regression cause for every failure.
- A comparison record against the current release across the six standing measurements.
- A promotion record naming the boundary events canary traffic covered.

**Quality Checkpoints**:

- Upgrade replay pass rate is at least 98 percent; between 95 and 98 percent defers promotion pending a second trial, and below 95 percent blocks the upgrade.
- No upgrade is promoted on elapsed time alone; promotion cites the boundary events observed.
- Every regression carries a cause classification; an unexplained regression blocks promotion regardless of aggregate pass rate.

***

#### Step 6.3: Run the Scheduled Re-Evaluation and Decide Retain, Reduce, Replace, or Remove

**Required Actions**:

- Run the re-evaluation every 90 days, and additionally before any major upgrade, after any incident attributed to the framework layer, after a licence or ownership change, and whenever workload volume or consequence class changes.
- Refresh the workload contract and the capability requirement record, since requirements drift faster than stacks do.
- Re-run the reference path baseline and the incumbent against the frozen corpus and a refreshed rotating sample, so that comparison uses contemporaneous figures.
- Recompute package fidelity, unattributed mutation rate, cache preservation, token and latency overhead, cost per successful task, and the exit cost from a repeated rehearsal.
- Evaluate one credible alternative only where the incumbent misses a requirement, carries unacceptable economics, or has increased its lock-in profile; a re-evaluation is not an occasion to shop.
- Issue exactly one decision from retain, reduce, replace, or remove, and where the decision is replace, migrate by stratum with reconciliation on any dual-write, canary reads before execution, verified deletion, and retirement of old state and credentials.

**Required Outputs**:

- A re-evaluation record carrying refreshed measurements, the repeated exit cost, and the updated lock-in profile.
- One decision from retain, reduce, replace, or remove, with evidence and a next review date.
- A migration plan by stratum where the decision is replace.

**Quality Checkpoints**:

- A retain decision cites measurements taken within the current re-evaluation; no change is a valid decision only when supported by fresh evidence.
- Exit cost was re-measured by rehearsal rather than carried forward from adoption.
- Every re-evaluation closes with an owner, an updated bill of materials, and a scheduled next review date.

***

## III. Implementation Guidance for AI Agents

AI agents running a framework selection must follow systematic protocols ensuring that every capability claim is measured, every difference in the rendered context package is attributed, and every dependency is pinned and rehearsed for removal before it is adopted. The following guidance translates the selection procedure into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Requirements Agent**: Model tier. Interprets the workload contract into capability requirements and proposes an obligation class for each of the six adjustable capabilities. It may not assign a final obligation class, may not declare a hard gate, and may not issue an adoption verdict.
2. **Capability Auditor**: Deterministic tier. Executes the acceptance test suite against each candidate and returns pass or fail with the executed evidence. It rejects any capability verdict presented without an executed test, including one supported by vendor documentation.
3. **Harness Runner**: Deterministic tier. Owns the frozen corpus, the trial protocol, and every reported measurement. It refuses to execute before the threshold declaration carries a timestamp, and it discards any measurement lacking a corpus version identifier and a trial count.
4. **Fidelity Auditor**: Deterministic tier with a model-tier proposal step. Captures the four representations, diffs the intent manifest against the rendered context package, and holds a veto over release. It escalates every difference absent from the approved-mutation fixture rather than accepting a classification.
5. **Lock-In Assessor**: Hybrid tier. The model proposes an extraction path per captured asset; the exit rehearsal settles it. An extraction path that has not been executed contributes no reduction to an extraction difficulty score.
6. **Dependency Registrar**: Deterministic tier. Owns the bill of materials, the version pins, the advisory feed, and the upgrade replay gate. It blocks any promotion whose bill of materials carries a range pin or an unreviewed layer.
7. **Adoption Arbiter**: Issues exactly one adoption verdict per capability requirement, citing the measurements that produced it. It issues `defer` for any capability the harness has not measured on the project's own corpus, and it never converts a failed hard gate into a weighted deduction.

**Tier Handoff Rule**: Every handoff from the model tier to the deterministic tier carries a proposal and its rationale; every handoff back carries an executed result and its evidence. Where the two disagree, the deterministic result stands and the disagreement is recorded with a reason code, since a repeated pattern of model-tier optimism is itself a calibration signal for the next selection.

**Workflow Execution Pattern**:

```
STATE: Phase_4_Evidence_Based_Evaluation
ACTIONS:
  1. Verify threshold_declaration_timestamp precedes first_execution_timestamp
  2. Execute frozen corpus against each candidate under matched conditions
  3. Execute cold and warm cache trials, restart trials, dependency failure trials
  4. Capture intent manifest, framework input, rendered package, provider receipt
  5. Diff manifest against rendered package and classify every difference
  6. Attempt in-range version upgrade and replay corpus
VALIDATION:
  - unattributed_mutation_count == 0
  - authority_inversion_count == 0
  - package_fidelity >= 0.99
  - task_success_delta >= -0.02
  - upgrade_replay_pass_rate >= 0.98
  - every_measurement_cites_corpus_version == TRUE
TRANSITIONS:
  IF all_validations_pass THEN next_state = Phase_5_Lock_In_Assessment
  ELSE IF unattributed_mutation_count > 0 THEN next_state = Fidelity_Escalation
  ELSE next_state = Phase_4_Candidate_Rejection
```

**Approval Gate**: Human authorisation is required, and is never inferred from an absence of objection, before adopting any candidate meeting at least 1 of four triggers: an exit cost estimate above 20 working days; any captured asset scored at extraction difficulty 5; a candidate that would become the third framework in the stack; or any capability marked high consequence whose acceptance test passed at between 95 and 99 percent rather than at the declared bar. Provisioning paid infrastructure, accepting a new licence, issuing production credentials, exporting sensitive content out of the evidence store, and enabling content capture in production traces each require the same authorisation independently of the adoption decision.

**Context Management Requirements**:

- Hold the workload contract, the capability requirement record, the frozen corpus identifier, and the bill of materials in durable state, since a selection outlives any single context window.
- Read candidate documentation in bounded slices and record extracted claims as candidate hypotheses with their observation date, never as established capability.
- Write a handoff record at every context boundary naming completed phases, pending phases, the candidate set, and the declared thresholds, so that a resumed selection does not silently redeclare a threshold after seeing results.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Completeness (After Phase 1)**

- **Automated Check**: Every task family carries a numeric volume and latency budget; every tool effect is marked reversible or irreversible; the requirement record holds exactly 8 entries; every required capability carries an executable acceptance test with a numeric bar.
- **Agent Action on Pass**: Proceed to the build-versus-adopt determination.
- **Agent Action on Failure**: Halt and return the specific contract defect; no candidate is named against an incomplete contract.
- **Human Review Trigger**: Any capability whose obligation class the Requirements Agent proposed at variance with the consequence class it inherited.

**Checkpoint 2: Determination Integrity (After Phase 2)**

- **Automated Check**: Every determination names its trigger condition; every estimate above 400 raw lines carries the 1.5 adjustment; the adoption brief excludes every build determination; non-delegable capabilities name their obligation.
- **Agent Action on Pass**: Proceed to candidate identification.
- **Agent Action on Failure**: Return the determinations lacking a trigger condition and re-derive those entries only.
- **Human Review Trigger**: More than 4 capabilities landing in the contested band, which indicates the estimates are not discriminating.

**Checkpoint 3: Screening Integrity (After Phase 3)**

- **Automated Check**: The candidate set contains the reference path and no more than 4 entries across at least 2 abstraction levels; every candidate carries a verdict on all 3 universal screens; every named instance carries an observation date; the reference path emits both the intent manifest and the rendered context package.
- **Agent Action on Pass**: Proceed to evaluation.
- **Agent Action on Failure**: Halt; a candidate set missing the reference path cannot produce a comparison.
- **Human Review Trigger**: Reference path construction exceeding 10 working days, or every candidate failing one universal screen.

**Checkpoint 4: Evidence Integrity (After Phase 4)**

- **Automated Check**: Threshold declaration precedes first execution; corpus holds at least 60 cases across at least 8 strata; unattributed mutation count is 0; authority inversion count is 0; every measurement cites a corpus version and a trial count; every failed case carries a classification.
- **Agent Action on Pass**: Proceed to lock-in assessment.
- **Agent Action on Failure**: Halt; a threshold declared after results are seen voids the evaluation and the corpus is re-run under a fresh declaration.
- **Human Review Trigger**: Any unattributed mutation on a high-consequence stratum, or any authority inversion in any stratum.

**Checkpoint 5: Exit Readiness (After Phase 5)**

- **Automated Check**: Export replay success on protected atoms is exactly 100 percent; the rehearsal covered at least 10 runs across at least 3 strata including 1 interrupted run; every captured asset carries a named export mechanism; every contested determination is resolved.
- **Agent Action on Pass**: Proceed to adoption.
- **Agent Action on Failure**: Reject the candidate for the capabilities whose state failed to replay; a failed exit rehearsal is never resolved by a plan to build the exporter later.
- **Human Review Trigger**: Exit cost above 20 working days, or any captured asset at extraction difficulty 5.

**Checkpoint 6: Adoption and Version Control (After Phase 6)**

- **Automated Check**: One verdict per capability requirement, each citing measurements; no adopt verdict over a failed hard gate; every bill of materials layer carries an exact version; the decision record names an owner, a next review date, and removal conditions.
- **Agent Action on Pass**: Register the decision and schedule the 90-day re-evaluation.
- **Agent Action on Failure**: Withhold registration and return the verdicts lacking cited evidence.
- **Human Review Trigger**: Any verdict issued as `adopt` on evidence older than the current corpus version, or any range pin surviving in the bill of materials.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
EXECUTION_TIER:
VALIDATION_CRITERIA:
MEASURED_VALUE:
CORPUS_VERSION:
TRIAL_COUNT:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Documented Capability Unreproducible on the Project's Corpus**

- **Symptoms**: A capability the candidate documents passes on vendor examples and fails the acceptance test on the project's strata; the failure concentrates in long-context, tool-heavy, or resumed cases.
- **Diagnostic Steps**: Confirm the acceptance test exercises the capability rather than an adjacent one; confirm the failing stratum differs from the vendor example in a named property; determine whether the failure is configuration, an unsupported combination, or an absent capability.
- **Resolution Protocol**: Option A, reconfigure and re-run the whole affected stratum, recording the configuration as a required deployment setting. Option B, reclassify the capability as absent and re-score the candidate against the adoption brief. Option C, write a thin owned adapter supplying the capability and register it as a build determination, re-running the brief without it.
- **Escalation Trigger**: After 3 configuration attempts against one capability the capability is recorded absent; a documented feature that cannot be reproduced in 3 attempts is not a capability the project can depend on.

**Error Type 2: Unattributed Mutation in the Rendered Context Package**

- **Symptoms**: A difference between intent manifest and rendered package matches no entry in the approved-mutation fixture; a stable-prefix hash diverges across calls declared to share a cache family; injected text appears above application policy in assembly order.
- **Diagnostic Steps**: Identify the first divergent segment; determine which layer in the bill of materials introduced it by rendering the same fixture with layers removed one at a time; check whether the mutation appeared at a specific version boundary.
- **Resolution Protocol**: Option A, where the mutation is attributable and benign, add it to the approved-mutation fixture with a version and re-run the audit. Option B, where the mutation is attributable and displaces budget or inverts authority, disable the responsible behaviour and re-run. Option C, where the mutation is not attributable to any layer, reduce the framework to an adapter or instrument a lower boundary until it is.
- **Escalation Trigger**: Any authority inversion escalates immediately and is never resolved by retry. An unattributed mutation surviving 2 attribution passes blocks release; visibility is never waived because output quality appears acceptable.

**Error Type 3: Model-Tier Requirement Manufacture**

- **Symptoms**: The requirement record carries entries outside the closed inventory; requirements appear that mirror a candidate's feature list rather than the workload contract; obligation classes drift toward framework-must-supply without a consequence class justifying it.
- **Diagnostic Steps**: Trace every requirement to a named contract element; check whether the requirement's wording matches candidate documentation read earlier in the run; recount the requirement record against the 8-entry inventory.
- **Resolution Protocol**: Option A, reject requirements not resolving to an inventory capability and re-derive from the contract alone. Option B, re-derive the requirement record before any candidate documentation is read, so the derivation cannot be anchored by it. Option C, downgrade an unjustified framework-must-supply class to framework-may-supply and record the correction with a reason code.
- **Escalation Trigger**: More than 2 manufactured requirements in one derivation halts the phase and obliges a fresh derivation by a component that has read no candidate material.

**Error Type 4: Version Drift or Breaking Change Mid-Project**

- **Symptoms**: Upgrade replay pass rate below 98 percent; a previously approved mutation reappears with a different shape; a pinned layer resolves to a different build; a documented interface the project depends on is marked experimental or deprecated.
- **Diagnostic Steps**: Diff the dependency manifest against the recorded bill of materials; identify which layer changed; replay the deterministic fixtures without dispatch to isolate rendering changes from behavioural ones; classify each regression by cause.
- **Resolution Protocol**: Option A, hold the pin, record the advisory, and schedule the upgrade into the next re-evaluation window. Option B, where a security advisory forbids holding, upgrade behind shadow and canary with the full replay gate and roll back on any hard gate failure. Option C, where the breaking change removes a capability on a hard gate, invoke the removal conditions and open a replace decision rather than absorbing the change.
- **Escalation Trigger**: Upgrade replay pass rate below 95 percent blocks the upgrade outright. Two consecutive re-evaluations recording a breaking change in the same layer opens a replace decision regardless of the incumbent's other measurements.

**Error Type 5: Exit Rehearsal Fails on Protected State**

- **Symptoms**: Exported runs replay with a protected atom missing; the export carries content but not provenance, version, or retention fields; the trace export loses span hierarchy or evaluation linkage.
- **Diagnostic Steps**: Identify which captured asset category lost the atom; determine whether the loss is in the export, the converter, or the replay target; check whether the loss is confined to interrupted runs or to runs carrying durable memory writes.
- **Resolution Protocol**: Option A, where the loss is in an application-written converter, repair the converter and re-run the rehearsal in full. Option B, where the loss is in the framework's export and a documented alternative export exists, re-run through it and re-score extraction difficulty. Option C, where no export preserves the atom, score the asset at difficulty 5, escalate for approval, and treat the affected capability as build.
- **Escalation Trigger**: Any protected-atom loss rejects the candidate for the affected capability. This class is never resolved by accepting a lower replay rate, because the atoms lost are precisely those the system cannot operate without.

**Error Type 6: Framework Sprawl and Overlapping Capability Ownership**

- **Symptoms**: Two adopted frameworks both mutate the context package; a capability has no single owner; a failure cannot be attributed to a layer; the bill of materials carries adapters whose only purpose is reconciling two frameworks.
- **Diagnostic Steps**: Map each of the 8 capabilities to exactly one owner and identify the capabilities with zero or more than one; count the adapters existing only to bridge frameworks; measure the token and latency overhead attributable to bridging.
- **Resolution Protocol**: Option A, assign each contested capability a single owner and disable the other framework's behaviour for it, verifying by fidelity audit. Option B, remove the framework supplying the fewest adopt-determined capabilities and absorb its capabilities into the reference path. Option C, where both frameworks are load-bearing, insert a protocol boundary between them so the seam is versioned and testable rather than implicit.
- **Escalation Trigger**: More than 1 capability lacking a single owner blocks release. A third framework entering the stack requires the named approval gate in Section III.A regardless of its individual measurements.

**Troubleshooting Decision Tree**:

```
SELECTION OR ADOPTION FAILS A GATE
├─ EVIDENCE DEFECT
│   ├─ Threshold declared after results seen → VOID evaluation; re-declare and re-run corpus
│   ├─ Measurement lacks corpus version or trial count → Discard measurement; re-execute stratum
│   └─ Capability claimed from documentation only → Record as hypothesis; verdict is defer
├─ FIDELITY DEFECT
│   ├─ Unattributed mutation present → Attribute by layer removal; block release until 0
│   ├─ Authority inversion detected → HALT; reject candidate; never resolved by retry
│   └─ Stable prefix diverges unexpectedly → Locate first divergent segment; record cause
├─ REQUIREMENT DEFECT
│   ├─ Requirement outside the closed inventory → Reject; re-derive from contract alone
│   ├─ High-consequence capability without a hard gate → Add gate before scoring
│   └─ Obligation class unjustified by consequence → Downgrade and record reason code
├─ EXIT DEFECT
│   ├─ Protected atom lost on replay → Reject candidate for that capability
│   ├─ Asset with no export mechanism → Score difficulty 5; escalate for approval
│   └─ Exit cost above 20 working days → Escalate; compare against adjusted build estimate
└─ VERSION DEFECT
    ├─ Upgrade replay below 95 percent → Block upgrade; hold pin; schedule re-evaluation
    ├─ Range pin in bill of materials → Block promotion; replace with exact version
    └─ Two breaking changes in one layer → Open replace decision
```

### D. Performance Metrics, Version Risk, and Continuous Learning

**Selection Quality Metrics**:

- **Evidence coverage**: Required capabilities whose verdict cites an executed measurement on the project's corpus, divided by required capabilities (target: 100 percent; any shortfall converts the affected verdicts to defer).
- **Gate discrimination**: Candidates separated by at least 1 hard gate, divided by candidate pairs compared (target: at least 70 percent; below 50 percent indicates the gates are not testing the requirements that matter).
- **Estimate calibration**: Measured exit rehearsal effort divided by the prior estimate, recorded per selection (target: within 1.5; a ratio above 2.0 recalibrates the multiplier for the next selection).
- **Requirement stability**: Capability requirements unchanged between adoption and the first re-evaluation, divided by requirements (target: at least 80 percent; below 60 percent indicates the workload contract was declared too early).

**Operational Metrics**:

- **Package fidelity**: Audited calls with zero unattributed mutation, divided by audited calls (target: at least 99 percent overall and 100 percent on high-consequence strata).
- **Unattributed mutation incidents**: Count per release, reported by severity rather than as a rate, since one authority inversion outweighs many benign whitespace differences (target: 0).
- **Cache preservation**: Provider-reported reused prefix tokens divided by expected reusable prefix tokens on eligible calls (target: at least 90 percent where cache support is claimed).
- **Framework token overhead**: Candidate input tokens minus reference path input tokens on matched cases, attributed to injection, schemas, memory, or reformatting (target: no more than 15 percent).
- **Framework latency overhead**: p95 difference against the reference path, reported separately for local rendering and networked platform calls (target: no more than 20 percent).
- **Cost per successful task**: Total model, framework, retrieval, tool, storage, and evaluation cost divided by successful tasks, counting retries and failed attempts as cost (target: no more than 1.15 times the reference path).

**Dependency and Version Metrics**:

- **Pin completeness**: Context-altering layers carrying an exact version, divided by context-altering layers (target: 100 percent; a range pin blocks promotion).
- **Upgrade regression rate**: Previously passing frozen cases failing after an upgrade, divided by previously passing cases, stratified by cause (target: no more than 2 percent).
- **Advisory latency**: Working days between a security advisory affecting a pinned layer and a decision on it (target: no more than 5).
- **Re-evaluation freshness**: Adopted capabilities whose most recent measurement falls within 90 days, divided by adopted capabilities (target: 100 percent).

**Learning and Adaptation Mechanisms**:

- **Approved-mutation fixture growth**: Record every newly approved mutation with the version that introduced it, so that a later upgrade reintroducing a previously rejected mutation is detected rather than silently re-approved.
- **Estimate history**: Retain build estimates, adjusted estimates, and measured outcomes per selection, and recompute the 1.5 optimism multiplier against observed history rather than treating it as a constant.
- **Rejection memory**: Retain the evidence behind every rejection with its date and version, so a re-evaluation can test whether the rejection still holds rather than repeating the whole harness.
- **Threshold recalibration**: Recompute every numeric bar per workload stratum against observed outcomes; the figures stated in this guide are deployment defaults, not measured constants.

**Human Oversight Boundaries**: Provisioning paid infrastructure, accepting a new licence, issuing production credentials, exporting sensitive content out of the evidence store, enabling content capture in production traces, waiving a fidelity finding, and removing a production framework are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it selects against a capability inventory and a measured corpus rather than against any particular subject matter. Its phases hold wherever a system assembles context for a model, has more than one way to obtain the machinery, and will outlive at least one version of whatever it adopts.

### 4.1 Cross-Domain Application Patterns

**Clinical decision support**: The consequence class is high across nearly every task family, so compression with verification stays application-owned and every automatic summarisation a candidate performs is disabled and verified disabled in the rendered package. Durable externalization carries a deletion obligation, so a candidate whose export omits retention fields fails the memory-schema evidence requirement in Step 5.1 regardless of its other measurements. The frozen corpus weights deletion and authorization strata heavily, and the fidelity audit runs at full content capture inside a restricted evidence store while ordinary traces carry hashes only. Observability is not a diagnostic convenience here; the assembly record is a clinical audit artifact and its export format is a procurement requirement.

**Financial services surveillance and advisory**: Tenant separation and authorization enforcement sit on the non-delegable list in Step 2.1 and are built regardless of estimate, since a framework that enforces a tenant boundary inside the model's context is enforcing nothing. Cache-aware assembly carries an isolation constraint rather than only an economic one: the cache family key must span the tenant boundary, and a cross-tenant prefix reuse is a zero-tolerance finding rather than a measurement below bar. Exit cost dominates the contested band because regulated evidence must remain replayable for a retention period longer than most frameworks' support windows.

**Industrial field operations and maintenance**: Latency budgets are tight and connectivity is intermittent, so boundary handoff is the capability that decides the selection: a candidate whose handoff record cannot rebuild working state after an unplanned disconnection fails the hard gate however good its ergonomics. The corpus weights interrupted and resumed strata above the ordinary path, and the restart trial count rises above the default 3 because the failure is common rather than exceptional. Framework latency overhead is measured on the device profile actually deployed, not on a development machine, since a 20 percent overhead measured on the wrong hardware is not a measurement.

**Public-sector case handling**: Residency constraints and records obligations put durable externalization and observability on hard gates, and a hosted control-plane feature with no local equivalent is scored at extraction difficulty 5 by default rather than by assessment. Procurement cycles are long, so the 90-day re-evaluation carries a second obligation: it produces the evidence a renewal decision needs, and a retain decision without fresh measurement is not defensible to a reviewer outside the team.

**Software engineering tooling**: Task families are diverse and workloads change quickly, so requirement stability is the metric to watch: a project rewriting its capability requirements between adoption and first re-evaluation declared its workload contract too early. Isolation and delegation usually carries the strongest adopt case because owned implementations of sub-context budget ledgers and authority scopes exceed the 1,200-line trigger, while budget partitioning and admission almost always fall under 400 lines and are built. The reference path is cheap to construct here and correspondingly hard to justify skipping.

### 4.2 Scale, Risk, and Consequence Adaptation

- **Prototype scale**: Collapse the corpus to 20 cases across 4 strata and the candidate set to 2 entries including the reference path, but never relax the threshold declaration rule or the exit rehearsal. A prototype that skips the rehearsal ships a dependency nobody has proven removable, which is the condition this guide exists to prevent.
- **Team production scale**: Apply the full corpus, candidate set, and measurement table. Run the fidelity audit on a sampled 5 percent of production calls continuously rather than only at selection, since mutations enter through upgrades rather than through adoption.
- **Regulated or high-scale production**: Raise package fidelity to 100 percent on every stratum rather than only on high-consequence ones, raise the repeated-trial count to at least 5, partition caches and stores by tenant, and require an independent approver for every adoption verdict rather than only for the four gate triggers. Retain canonical packages in an authorized evidence vault while ordinary traces carry hashes, segment counts, classifications, token counts, and references.
- **Low-consequence internal tooling**: Reduce the candidate set to the reference path plus 1 alternative, weight cost per successful task above token overhead, and shorten the re-evaluation interval to 180 days. The exit rehearsal remains mandatory but may cover 5 runs rather than 10.
- **Multi-framework stacks**: Assign each of the 8 capabilities exactly one owner before any measurement begins, and insert a protocol boundary at every seam where two frameworks would otherwise both mutate the context package. Measure bridging overhead separately from framework overhead, because a bridge that costs more than the capability it connects is a signal to remove one side of it.

***

## V. Limitations and Considerations

**The capability inventory is derived, not standard**: The eight capabilities are drawn from the specialist guides in this category rather than from an independent specification, and a different decomposition of the same problem is defensible. The consequence is that a genuine requirement could fall outside the inventory and be rejected in Step 1.2 as manufactured. The mitigation is that the rejection is recorded with its wording, so a requirement rejected repeatedly across selections is evidence that the inventory needs an entry rather than that the requirement was spurious.

**Numeric bars are deployment defaults**: Every figure in the measurement table, every trigger in the build-versus-adopt table, and the 1.5 optimism multiplier were chosen to be operable on first deployment rather than derived from measured properties of any framework population. Applying them unchanged will reject some adequate candidates and admit some marginal ones. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute its bars against observed outcomes and to record the estimate calibration ratio at every selection.

**A benchmark measures the corpus, not the future**: A frozen corpus drawn from present traffic cannot represent workload the project has not yet seen, and a candidate that measures well today can fail on a stratum that appears next quarter. The consequence is that adoption decisions are correct only for the workload measured. The mitigation is the rotating production sample in Step 6.2 and the 90-day re-evaluation in Step 6.3, which refresh both the corpus and the requirement record rather than only the measurements.

**Named products date, and the dating rule only bounds the damage**: The capability-class table records observations carried by the source material at one date. Products merge, are renamed, change ownership, and disappear, and a reader consulting the table later will find entries that no longer correspond to anything. The mitigation is that the table is never load-bearing: it seeds candidate identification only, every capability claim is established by the harness, and a candidate whose entry has become obsolete simply fails to be found rather than causing a wrong decision.

**An exit rehearsal proves a path, not its cost under duress**: The rehearsal exports 10 runs in calm conditions with the framework working. A real exit happens during an incident, a licence change, or a maintenance collapse, with production volumes and without the vendor's cooperation. The consequence is that measured rehearsal effort understates real exit cost. The mitigation is scaling the estimate to full production state volume in Step 5.3 and repeating the rehearsal at every re-evaluation so that decay in the export path is detected before it is needed.

**Build estimates are optimistic in a way the multiplier does not fully correct**: The 1.5 multiplier addresses line-count optimism but not the ongoing cost of owning a capability: the on-call surface, the edge cases discovered in production, and the engineer-days spent on a bookkeeping layer that no longer interests anyone. The consequence is a bias toward build. The mitigation is the quarterly maintenance figure recorded in Step 2.1 and the estimate calibration metric, which surfaces the bias across successive selections rather than within one.

**The model tier can manufacture requirements that flatter a candidate**: Requirement derivation reads a workload contract, but an agent that has also read candidate documentation can produce requirements shaped by what it read. The consequence is a selection that appears evidence-based while its requirements were reverse-engineered from a preferred answer. The mitigation is Error Type 3 in Section III.C, which obliges derivation before candidate material is read and halts the phase after 2 manufactured requirements.

**Capability conformance is not architectural fitness**: A candidate can pass all eight acceptance tests, clear every numeric bar, and still be the wrong abstraction for the team that must operate it. The measurement set detects capability absence and hidden mutation, not a mismatch between an abstraction and the practices of the people on call for it. The mitigation is the qualitative fit record, which is kept explicitly separate from the adoption verdict so that a fit concern is argued in the open rather than smuggled into a score.

***

## VI. Conclusion and Summary

Framework selection is an evidence discipline before it is a technology preference. The question a project can actually answer is not which framework is best, which changes faster than any system can track, but which capabilities the workload requires, who should own each of them, and whether a candidate demonstrably supplies the ones it is being adopted for on the project's own corpus. A selection organised around a closed capability inventory survives the disappearance of every product named in it; a selection organised around product names dates the moment the market moves.

Three commitments carry most of the value. The framework-free reference path is the control specimen without which no overhead figure, no fidelity comparison, and no exit is meaningful, and it costs little relative to what it makes measurable. The declaration of thresholds before results are seen is what separates an evaluation from a rationalisation, and it is cheap to do and impossible to retrofit. The exit rehearsal executed before adoption converts lock-in from a worry into a measured number, and a project that will not spend ten days proving it can leave has already decided to stay whatever happens.

A team introducing this discipline should start where the evidence is cheapest. Capture the rendered context package on the current stack before selecting anything, because a stack whose assembled package cannot be inspected has already failed the one capability that is framework-must-supply in every deployment. Build the reference path next, then the frozen corpus, then the thresholds. Only then examine candidates.

**Key Success Factors**:

- **Capability inventory before candidates**: Requirements are derived from the workload contract and closed at eight entries, so the candidate set is shaped by the requirements rather than the requirements by the candidates.
- **Obligation class per capability**: Whether a framework must supply, may supply, or should not own each capability is fixed before evaluation, so a hidden capability is disqualifying rather than a scoring deduction.
- **Measured evidence on the project's own workload**: No adoption verdict is issued without harness results on a frozen corpus drawn from the project's own traffic, and vendor documentation is never an input to a verdict.
- **Thresholds declared before results**: Every numeric bar carries a declaration timestamp preceding the first execution, and a bar declared afterwards voids the evaluation it was meant to judge.
- **Rendered package fidelity**: The intent manifest and the rendered context package are diffed on every audited call, every difference is attributed, and an unattributed mutation or an authority inversion blocks release regardless of output quality.
- **A rehearsed exit and a pinned dependency surface**: The export-and-replay test passes before adoption, every context-altering layer carries an exact version, and every upgrade passes the replay gate before it reaches traffic.

By following this guide, AI agents can decide what to adopt and what to own on measured evidence, detect when a framework has quietly taken ownership of the assembled context, and retain a dependency only while its measured contribution continues to justify its cost and its exit remains proven.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides that define the capabilities the inventory in Section 1.2 is drawn from. The external references that follow are transcribed from the originating prose guide as it cited them, using the labels that source carried rather than reconstructed publication titles; they were not independently re-verified in the course of this conversion except where an entry is marked as verified. One entry was retrieved during conversion and is marked accordingly. The originating source enumerated a substantially larger set of product documentation references supporting a per-product description of individual frameworks; that material was deliberately not carried into this conversion, because a guide organised around named products dates immediately, and its supporting citations were compressed out with it.

**Corpus pointers**:

- `Context Engineering Frameworks: A Production Guide and Series Router` — the originating prose guide from which this operational guide was derived. Source of the framework-free baseline discipline, the bake-off procedure, the abstraction-leak and payload-diff audit, the logging contract at the framework boundary, the metric definitions, the selection criteria, the regression and drift controls, the maturity progression, and the periodic re-evaluation loop. Its per-framework survey was reorganised into the capability inventory and capability-class structure used here.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the category's umbrella guidance. Source of context package, partition, context budget, protected atom, admission gate, assembly order, trust class, handoff record, and utilization, all adopted unchanged. Owns the budget partitioning and accounting capability in Section 1.2.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — owns the admission and selection capability. Source of assembly record, admission cut, candidate pool, and the distinction between ranking as a proposal and admission as a decision.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — owns the compression with verification capability. Source of preservation manifest, fidelity class, compression depth, and the requirement that a compressed artifact is verified against a preservation contract rather than accepted on ratio.
- `advanced_task_guides/context-management/guide_SemanticContextCompression.md` — companion guidance on meaning-level compression, applicable where a candidate performs semantic summarisation as an automatic behaviour.
- `advanced_task_guides/context-management/guide_ContextEditingAndToolResultClearing.md` — companion guidance on provider-side and application-side removal of older tool results, applicable to the automatic-behaviour disclosure requirement in Section 1.2.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — owns the isolation and delegation capability. Source of isolation contract, task packet, result envelope, authority scope, write scope, and terminal status.
- `advanced_task_guides/context-management/guide_FilesystemAsContext.md` — owns durable externalization to a file namespace. Source of canonical record, write handle, retention class, and scope refusal.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — companion guidance on durable mutation, provenance, and write authorization, applicable to the memory-schema evidence requirement in Step 5.1.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — owns the boundary handoff capability. Source of context boundary, boundary trigger, handoff record, reconstruction test, epoch, and teardown.
- `advanced_task_guides/context-management/guide_ContextStateMachines.md` — companion guidance on execution semantics, guarded transitions, and durable workflow mapping, applicable to candidates in the graph and workflow runtime class.
- `advanced_task_guides/context-management/guide_KVCacheAwarePromptConstruction.md` — owns the cache-aware assembly capability. Source of stable prefix, prefix hash, cache family, eligible prefix tokens, cache-read and cache-write tokens, invalidation cause, and staleness bound.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — companion guidance on the failure modes a framework layer can introduce, applicable to the fidelity audit in Step 4.3.
- `advanced_task_guides/context-management/guide_HierarchicalContextArchitecture.md` — companion guidance on scopes, precedence, and authority resolution, applicable to the authority-ordering check in Step 4.3.
- `advanced_task_guides/context-management/guide_SlidingWindowContext.md` — companion guidance on resident-set movement and eviction, applicable where a candidate performs automatic history trimming.
- `advanced_task_guides/context-management/guide_ContextMemoryBlocks.md` — companion guidance on prompt-resident persistent blocks, applicable to candidates in the prompt-resident memory service class.

**External references**:

*Definitions of context engineering and the write, select, compress, isolate taxonomy*

1. Anthropic — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
2. LangChain documentation — https://docs.langchain.com/oss/python/langchain/context-engineering
3. LangChain — https://www.langchain.com/blog/context-engineering-for-agents

*Telemetry conventions used as the vendor-neutral correlation baseline*

4. OpenTelemetry — https://opentelemetry.io/docs/specs/semconv/
5. OpenTelemetry GenAI attributes — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
6. OpenTelemetry GenAI guidance — https://opentelemetry.io/blog/2026/genai-observability/
7. OpenTelemetry GenAI semantic conventions repository — https://github.com/open-telemetry/semantic-conventions-genai — retrieved and verified during conversion. The repository states that it provides semantic conventions for generative AI, including spans, metrics, and events for generative AI clients, for the Model Context Protocol, and for provider-specific conventions. The general semantic conventions site records that the generative AI conventions have moved to this repository, which is itself an instance of the version and location churn Step 6.1 requires a bill of materials to track.

*Protocol boundaries evaluated as framework-independent seams*

8. MCP specification, revision 2026-07-28 — https://modelcontextprotocol.io/specification/2026-07-28
9. A2A project — https://github.com/a2aproject/a2a
10. AG-UI — https://docs.ag-ui.com/introduction

*Declarative optimization of assembly parameters*

11. DSPy paper — https://arxiv.org/abs/2310.03714
