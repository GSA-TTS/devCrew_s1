# Modular Retrieval-Augmented Generation

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Modular retrieval-augmented generation constitutes the task family of building a retrieval system as a set of independently replaceable stages joined by declared contracts, rather than as a fixed pipeline whose structure is implicit in its code. Its subject is the contract and the composition rule, not any particular arrangement of stages: the routing loop, the grading-and-repair pattern, the self-assessment pattern, the graph index, and the query rewriting stage are all arrangements this discipline composes, versions, evaluates, and retires. This guide provides AI agents with a structured protocol covering the module interface contract and the invariants that survive every boundary, the pipeline manifest as a versioned and inspectable artifact, per-stage evaluation under a one-change isolation rule with a stated significance bar, detection of upstream output-distribution shift against downstream stages calibrated on the old distribution, and controlled rollout with armed rollback. It specifies an execution tier partition in which deterministic software owns contract enforcement, configuration resolution, budget accounting, provenance propagation, and evaluation arithmetic, while model inference owns only the judgement a given stage encapsulates. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a result is attributable to a configuration and a regression is attributable to a stage.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Modular retrieval-augmented generation**: A retrieval system expressed as a computational graph whose nodes are replaceable stages carrying declared contracts, permitting a stage to be swapped, reordered, bypassed, or configured per query class without editing its neighbours [1]. Wrapping each function in a class is not modularity; independent replaceability demonstrated by a passing substitution test is.

**Stage**: The unit of replacement and of attribution. A stage owns one critical function of the retrieval path, carries one contract, is registered under one identity, and produces one span. The six conventional top-level stages are indexing, pre-retrieval, retrieval, post-retrieval, generation, and orchestration [1].

**Operator**: One concrete implementation step inside a stage. Several operators may execute in one process under one stage contract. Promoting every operator to a separately deployed service adds failure modes without adding replaceability.

**Module contract**: The declared statement of what a stage accepts, what it emits, what it may consume from the budget, what errors it may raise, what security context it requires, and which upstream contract versions it accepts. The contract is the interface; the implementation behind it is interchangeable only to the extent the contract is complete.

**Contract version**: The semantic version of the interface a stage presents, incremented under the major, minor, and patch rules for incompatible changes, backward-compatible additions, and backward-compatible fixes respectively [9].

**Behaviour version**: The version of what a stage does rather than what it accepts, covering model identifier, prompt digest, threshold set, index manifest, and parameter set. A behaviour change with an unchanged contract version is the most common cause of an undetected regression.

**Pipeline manifest**: The immutable, versioned configuration artifact declaring every node, every edge, every resolved artifact digest, every budget, and every policy version for one composed pipeline. A run that cannot be reproduced from its manifest is not attributable.

**Compiled plan hash**: The digest computed over the fully resolved manifest after every mutable reference has been replaced by a pinned digest. Two runs sharing a compiled plan hash executed the same configuration; two runs that differ in it are not comparable without stating what changed.

**Provenance chain**: The unbroken link from source version to document to chunk to admitted text to cited claim, carried in stage outputs as stable identifiers and content digests rather than as list positions. A break anywhere converts a supported claim into an unsupported one.

**Budget ledger**: The deterministic account of wall time, tokens, context occupancy, monetary cost, tool calls, concurrency, fan-out, and iterations, decremented as stages execute and enforced outside model discretion. Every stage receives an allocation; no stage may exceed it or extend a deadline it inherited.

**Boundary invariant**: A property asserted at every stage boundary regardless of which implementations occupy the stages, such as provenance preservation, deadline monotonicity, identifier stability, and declared score semantics. Invariants are what make a swap safe; their absence is what makes a swap silently destructive.

**Registry**: The version-controlled inventory of approved implementations, each carrying identity, digest, supported contract versions, capabilities, required scopes, trust tier, resource class, health endpoint, evaluation report reference, and deprecation state. Resolution of a stage to an implementation happens through the registry, never through an ambient lookup.

**Substitution test**: The bounded admission procedure a candidate implementation must pass before it becomes eligible for a stage, covering schema conformance, security behaviour, deterministic golden cases, error paths, quality on the target slice, latency and cost envelopes, score-semantics compatibility, state migration, cache invalidation, and demonstrated rollback.

**Topology**: The declared control-flow shape connecting stages: linear, conditional, branching with a named join rule, looping under a bounded iteration count, or a bounded hybrid in which a planner selects from an approved catalogue of subgraphs.

**Join rule**: The declared condition under which a branching topology proceeds, drawn from a closed set: all required branches complete, a minimum count completes, the first valid result arrives, the best-scoring result arrives, or a deadline-bounded partial set is accepted.

**Router**: The stage that selects among eligible downstream paths. It is evaluated on route accuracy, coverage, calibration, and regret, where regret is the difference between the chosen path's measured outcome and the best eligible path's measured outcome under offline counterfactual comparison.

**Change isolation**: The evaluation discipline permitting exactly one stage, implementation, or parameter set to differ between a baseline run and a candidate run over the same frozen cases. Two simultaneous changes destroy attribution and are treated as an unevaluated release.

**Ablation run**: A paired run in which one stage is bypassed or replaced by the simplest valid operator, used to measure that stage's marginal contribution rather than to improve the pipeline.

**Output-distribution fingerprint**: The per-edge summary of what an upstream stage emits, comprising item count, score quantiles, null and warning rates, token counts, and identifier novelty, computed over a fixed sentinel query set. It is the detector for the recalibration failure mode defined in Section 1.2.

**Recalibration event**: An upstream behaviour change that moves an output-distribution fingerprint beyond a declared bound, marking every downstream stage carrying a threshold fitted against the previous distribution as uncalibrated until re-fitted or isolated behind an adapter.

**Slice**: A named subset of the evaluation set sharing a property that stages treat differently, such as exact identifiers, multilingual queries, tables, recent updates, multi-hop questions, access-controlled documents, or adversarial inputs. Adoption decisions are made per slice because an aggregate conceals total failure on one.

**Degraded response**: A response produced after a declared fallback executed, labelled with the missing branches and the fallback taken. Degradation is a smaller truthful capability, never the silent removal of a safeguard.

**Declared abstention**: A terminal outcome stating what is known, what is missing, what was attempted, and what would resolve the gap, in place of an answer. An abstention permitted by the contract is not a failure.

### 1.2 The Composition Discipline and Its Boundary Against Neighbouring Patterns

**What this guide owns**: Modular composition is the discipline underneath the named retrieval architectures, not another architecture beside them. Its subject is the module contract, the invariants that hold across every boundary, the manifest recording which implementations were composed, the evaluation procedure attributing a change to a stage, and the release procedure admitting or reverting a stage. Any specific arrangement of stages is an instance this discipline governs.

**Boundary against neighbouring patterns**: Each neighbouring pattern is a topology or a stage that this discipline composes.

- **Agentic retrieval** is a looping topology whose control decisions depend on observed state. This guide supplies the manifest bounding its loop, the budget ledger it decrements, and the contracts its tools present; it does not specify the loop's stopping rule.
- **Corrective retrieval** is a conditional topology in which a grading stage routes to a repair path. This guide supplies the verdict field in the grading stage's output contract and the join rule for the repair branch; it does not specify the grading thresholds.
- **Self-assessing retrieval** is a generation-stage pattern producing per-segment verdicts. This guide requires those verdicts to appear in the stage's declared output schema rather than in prose; it does not specify the critique procedure.
- **Graph-backed retrieval** is one retrieval-stage implementation whose index is a graph. This guide requires it to present the same retrieval contract as a lexical or dense implementation so that routing between them is a configuration change; it does not specify extraction or schema design.
- **Query transformation** is one pre-retrieval stage implementation. This guide requires its constraint-preservation check at the stage boundary; it does not specify the rewriting strategy.
- **General retrieval engineering**, covering parsing, chunking, hybrid fusion parameters, reranking, and citation verification mechanics, is consumed here as stage behaviour under a contract rather than duplicated inside each stage.

**Why composition is the failure surface**: A composed system fails in ways no single stage exhibits. Three failure modes are specific to composition. Contract erosion occurs where a replaced stage drops a field its neighbour required. Attribution loss occurs where several stages change together and no measurement can say which caused the observed delta. Silent recalibration occurs where an upstream stage changes its output distribution while a downstream stage retains thresholds fitted against the previous one. All three are invisible to end-to-end accuracy alone, and all three are detectable by the mechanisms specified in Sections II and III.

**Provenance and budget are the first casualties**: Recomposition drops exactly the fields no single stage consumes for its own purpose. Provenance identifiers, authorization decisions, content digests, policy versions, and remaining-deadline values pass through most stages untouched and are therefore the fields a new implementation omits without any local test failing. This guide makes both classes first-class contract fields and asserts them at every boundary rather than at the pipeline's ends.

**Composition carries a standing cost**: Every added stage adds a contract to maintain, a version to track, an evaluation to run, a failure mode to contain, and an operational surface to monitor. A stage retained without a measured failure slice that it closes is a defect, and Phase 6 requires its retirement.

### 1.3 The Decomposition Gate: Conditions for Modularisation and Suppression

Decomposition is not free, and agents must run a cheap gate before splitting any stage. The gate is bounded to 2 percent of the implementation budget and returns decompose, suppress, or defer.

**Decompose conditions**: Return decompose where at least 2 of the following hold. Distinct query classes require different corpora, retrievers, generators, or verification policies, measured as a gap of at least 10 percentage points on the primary metric between those classes under one configuration. Components must be upgraded or reverted independently because their release cadences differ. Separate owners hold separate service-level objectives for separate stages. An experiment requires holding every stage constant but one. The workload requires conditional, parallel, iterative, multi-corpus, or multi-agent execution. Compliance requires auditable boundaries with source-specific credentials. Traffic, latency, or cost requires independent scaling or resource isolation.

**Suppress conditions**: Return suppress where one corpus, one retrieval method, one prompt, and one generator meet every contract requirement; where no labelled evaluation set and no per-stage observability exist, since decomposition without measurement produces complexity without attribution; where the system is a short-lived prototype whose stages will not be replaced; where the operating team cannot run versioned contracts, distributed traces, and declared failure policies; or where a network boundary would consume more of the latency and reliability budget than the separation returns.

**Defer conditions**: Return defer where the need is plausible but unmeasured. The deferred path is an in-process linear pipeline built against the same typed contracts a modular system would use, so that a later split becomes a deployment change rather than a rewrite.

**Decomposition Gate Table**:

| Observable condition | Measured evidence required | Gate verdict |
| :-- | :-- | :-- |
| Query classes need different corpora or retrievers | Class gap of 10 points or more on the primary metric | Decompose the retrieval stage |
| Stages carry different release cadences | Two or more independent release records | Decompose along the ownership line |
| Experiment requires holding all but one stage constant | Frozen evaluation set exists | Decompose the stage under test |
| Compliance requires per-source credentials | Named policy obligation | Decompose along the credential boundary |
| One stage saturates a resource the others do not | Measured saturation above 70 percent | Decompose for independent scaling |
| Single corpus and method meet every gate | Contract satisfied on all slices | Suppress; keep one linear pipeline |
| No labelled evaluation set or per-stage traces | Attribution impossible | Suppress; build measurement first |
| Network hop exceeds the latency headroom | Hop cost above 20 percent of remaining budget | Suppress; keep the stage in process |
| Need plausible but unmeasured | No slice evidence yet | Defer; use typed in-process contracts |

**Numeric gate rules**: Decompose a stage only where at least 2 decompose conditions hold and a labelled evaluation set covering the affected slice exists. Where a candidate boundary would introduce a network hop consuming more than 20 percent of the remaining end-to-end latency budget, keep the stage in process and record the deferral. Component modularity and deployment modularity are separate decisions: replaceable code does not require a remote service, and the default is one deployable service holding several stages.

### 1.4 The Execution Tier Partition

The partition below is binding. Every phase of Section II is assignable to a tier, and every step mixing tiers names its handoff. In a modular system the partition is what keeps a stage swap from becoming a policy change.

**Deterministic tier**: Software, schema validators, digest functions, counters, configuration tooling, and registries own the following, because each requires exactness, reproducibility, auditability, or scale that model inference cannot supply. Module contract enforcement, comprising input validation before every stage executes and output validation before any downstream stage consumes the result. Configuration resolution and versioning, comprising registry lookup, digest pinning, manifest compilation, and compiled plan hashing. Budget accounting across stages, comprising allocation, decrement, deadline propagation, and refusal of any call whose measured cost profile cannot complete within what remains. Provenance propagation, comprising identifier stability, content digests, authorization decision references, and lineage fields carried across every boundary. Evaluation arithmetic, comprising paired deltas, confidence intervals, significance tests, distribution fingerprints, and gate verdicts. Authorization, tenant isolation, egress restriction, and artifact admission. Retry, circuit, cancellation, and fallback control.

**Model tier**: LLM calls own only the judgement a given stage encapsulates, because that judgement requires open-vocabulary understanding no deterministic rule covers. Interpreting an ambiguous request into an explicit information need. Proposing query rewrites, decompositions, and expansions. Judging topical relevance and sufficiency beyond lexical overlap. Adjudicating whether a passage entails a claim. Classifying a query into a route label where deterministic features are insufficient. Synthesising an answer from admitted text. This tier never enforces a budget, never resolves a configuration, never declares its own output supported, and never selects an implementation.

**Hybrid tier and the authority rule**: The model proposes and the deterministic tier disposes. A model-proposed route is admitted only where policy, capability, health, and budget filters all pass. A model-proposed rewrite is admitted only where a deterministic constraint checker confirms preservation of entities, negation, dates, units, tenant scope, and jurisdiction. A model-proposed plan in a hybrid topology is admitted only after compilation into a bounded plan drawn from approved subgraphs. Where the two tiers disagree, the deterministic tier holds authority without exception. A model may narrow a route set, decline a path, or declare an abstention early; a model may never raise a ceiling, extend a deadline, add an implementation, relax an invariant, or convert a contract violation into a warning.

**Contract violation halts rather than degrades**: A stage that emits output failing its declared schema, dropping a required provenance field, or exceeding its declared budget produces a halt with a recorded error class, not a repaired result. Orchestration must never silently patch an invalid stage output, because a repaired violation is an undetectable defect while a halted one is a fixable release blocker. Only quality and availability failures are eligible for a declared fallback; contract, policy, and integrity failures fail closed.

**Tier Ownership by Artifact**:

| Artifact | Owning tier | Rejection rule enforced deterministically |
| :-- | :-- | :-- |
| Module contract schema and version | Deterministic | Output missing a required field halts the run |
| Provenance and lineage fields | Deterministic | A stage emitting evidence without source identity and digest is rejected |
| Budget ledger and deadline | Deterministic | A child deadline later than its parent is rejected |
| Pipeline manifest and compiled plan hash | Deterministic | A manifest retaining a mutable tag refuses to execute |
| Registry resolution and artifact admission | Deterministic | An unsigned or unpinned implementation is refused |
| Route label selection | Hybrid | A label outside the declared set, or ineligible under policy, is discarded |
| Query rewrite and decomposition | Hybrid | A rewrite altering entity, negation, date, unit, or scope is rejected |
| Relevance and sufficiency judgement | Hybrid | A judgement over a candidate the model added itself is rejected |
| Answer synthesis | Model | Not applicable |
| Evaluation deltas and significance verdicts | Deterministic | A verdict from an uncalibrated model judge is refused |
| Rollback trigger evaluation | Deterministic | A trigger overridden without a recorded approval is refused |

***

## II. Operational Framework: Contract-Bound Composition of Independently Replaceable Retrieval Stages

The framework assumes the decomposition gate in Section 1.3 has returned decompose or defer. Phases 1 through 3 establish the contracts, the inventory, and the configuration. Phase 4 attributes measured change to a stage. Phase 5 governs compatibility across stage versions. Phase 6 releases and operates the composition, returning control to Phase 4 whenever a target is missed.

### Phase 1: Module Contract and Invariant Declaration

**Objective**: Fix what every stage must accept, what it must emit, and which properties hold at every boundary, before any stage is built or replaced, so that a swap cannot silently break a neighbour.

#### Step 1.1: Declare the System Contract and the Boundary Envelope

**Required Actions**:

- State the question classes the system serves, the tenants and corpora it may reach, the authority hierarchy among sources, the required freshness, the output form, the material-claim policy, and the conditions under which a declared abstention is the correct outcome.
- Set end-to-end ceilings for wall time, tokens, context occupancy, monetary cost, concurrency, evidence items, and fan-out, and reserve a fixed share for policy checks, joins, serialisation, and the response path before allocating anything to stages.
- Name the critical slices whose failure blocks release, and attach a hard gate to each, expressed as a metric, a threshold, and the action taken on breach.
- Record the risk tier, the authorization context, the data classifications in scope, the permitted regions, and the permitted egress destinations.
- Declare the reserve share withheld from every stage allocation, set to at least 15 percent of the end-to-end latency budget, so that a slow stage cannot consume the verification and response path.

**Required Outputs**:

- A system contract record naming question classes, corpora, authority hierarchy, freshness requirement, and abstention conditions.
- An end-to-end budget declaration with a numeric ceiling for every bounded dimension and a named reserve share.
- A critical-slice inventory with one hard gate per slice.
- A security envelope naming risk tier, classifications, regions, and permitted egress.

**Quality Checkpoints**:

- Every budget dimension carries a numeric ceiling; an unbounded dimension halts contract acceptance.
- Every critical slice carries a hard gate whose breach names a specific action.
- The declared reserve is at least 15 percent of the end-to-end latency budget; a smaller reserve is rejected because joins and verification cannot be scheduled inside it.

***

#### Step 1.2: Specify the Module Interface Contract

**Required Actions**:

- Define, for every stage, a closed input schema and a closed output schema in a typed schema language, naming required fields, nullability, maximum item and byte counts, ordering guarantees, locale, and time semantics [7].
- Attach an identity block to every contract carrying stage type, stage identifier, implementation identifier, module version, contract version, and artifact digest.
- Attach a request-context block carrying run identifier, trace identifier, span identifier, parent span identifier, tenant identifier, pseudonymous principal identifier, authorization scope digest, policy version, purpose, risk tier, and absolute deadline.
- Attach a control block carrying timeout, cancellation token, idempotency key, retry eligibility, cache policy, maximum fan-out, and the stage's token, cost, and resource-class allocation.
- Attach an error block carrying a machine-readable error class drawn from a closed vocabulary, a retryability flag, a blame category, a partial-result policy, and a statement of whether fallback is permitted for that class.
- Attach a compatibility block naming accepted upstream contract versions, the emitted contract version, capability flags, deprecation date, and migration notes.
- Declare score semantics explicitly wherever a stage emits a score, naming direction, range, and whether the score is calibrated, so that no downstream stage compares scores across implementations without a declared normalisation.

**Contract Slot Template**:

```
STAGE_CONTRACT
  IDENTITY: stage_type, stage_id, implementation_id, module_version,
            contract_version, artifact_digest
  CONTEXT:  run_id, trace_id, span_id, parent_span_id, tenant_id,
            principal_id, authorization_scope_hash, policy_version,
            purpose, risk_tier, deadline_at
  INPUT:    closed_schema, required_fields, max_items, max_bytes,
            ordering_guarantee, locale, time_semantics, input_digest
  OUTPUT:   closed_schema, stable_ids, provenance, score_semantics,
            completeness_state, warnings, output_digest
  CONTROL:  timeout_ms, cancellation_token, idempotency_key,
            retry_eligible, cache_policy, max_fanout, token_budget,
            cost_budget, resource_class
  ERROR:    error_class, retryable, blame_category,
            partial_result_policy, fallback_permitted
  SECURITY: data_classification, allowed_regions, permitted_egress,
            required_scopes, retention_class, redaction_policy
  COMPAT:   accepted_upstream_contract_versions, emitted_contract_version,
            capability_flags, deprecation_date, migration_notes
```

**Required Outputs**:

- One contract document per stage carrying all eight blocks populated.
- A closed error-class vocabulary shared across every stage.
- A declared score-semantics statement for every stage emitting a score or confidence value.

**Quality Checkpoints**:

- Every contract carries all eight blocks; a contract missing the security or compatibility block is rejected before registration.
- Every error class in every contract belongs to the shared closed vocabulary; a free-text error string is rejected.
- No stage emits an uninterpreted score; a score without declared direction, range, and calibration status is rejected.

***

#### Step 1.3: Declare the Cross-Boundary Invariants

**Required Actions**:

- Declare provenance preservation as an invariant: every evidence unit crossing any boundary carries source identifier, version, content digest, exact span, tenant identifier, corpus identifier, policy version, and authorization decision reference, and a stage may narrow the set of evidence units but may never strip those fields from a unit it forwards.
- Declare budget monotonicity as an invariant: a stage inherits a remaining allocation, may consume part of it, may shorten a deadline for a child, and may never extend a deadline, raise a ceiling, or return a larger remaining allocation than it received.
- Declare identifier stability as an invariant: identity is carried by stable identifiers and content digests, never by list position, and any transformation records lineage through a derived-from identifier list and a transformation version.
- Declare validation placement as an invariant: inputs are validated before a stage executes and outputs before a downstream stage consumes them, so that a defect is attributed to the stage that produced it.
- Declare idempotency as an invariant: a stage is either idempotent under its idempotency key or declares retries prohibited, and no third state is permitted.
- Declare partial-result honesty as an invariant: a stage returning an incomplete result marks which parts are complete, and a downstream stage consumes a partial result only where its own contract permits that class.
- Specify the enforcement point for each invariant as a deterministic assertion executed at the boundary, and specify halt as the response to violation.

**Required Outputs**:

- An invariant register naming each invariant, its enforcement point, its assertion, and its violation response.
- A boundary assertion suite executable against any pair of adjacent stages.
- A provenance field list marked as mandatory in every stage output schema.

**Quality Checkpoints**:

- Every declared invariant has an executable assertion at a named boundary; an invariant asserted only in prose is not an invariant.
- Every invariant violation response is halt with a recorded error class; no invariant permits a repaired or warned continuation.
- The provenance field list appears as required in 100 percent of stage output schemas.

***

### Phase 2: Stage Inventory and Capability Registration

**Objective**: Establish a measured baseline, split only the boundaries the evidence justifies, and admit implementations to a registry through a substitution test, so that every stage has at least one interchangeable occupant.

#### Step 2.1: Establish the Baseline and Identify Justified Boundaries

**Required Actions**:

- Implement an in-process linear pipeline with one corpus, one retrieval method, one evidence selector, and one generator, using the typed contracts declared in Step 1.2 rather than untyped calls.
- Record the baseline manifest, the baseline traces, and the baseline scores per slice on the frozen evaluation set, so that every later comparison has a fixed reference.
- Apply the decomposition gate from Section 1.3 to each candidate boundary and record the verdict with its supporting evidence.
- Name, for each stage admitted by the gate, its owner, its contract, its dependencies, its side effects, and its service-level objective.
- Keep operators co-located inside a stage unless a deployment boundary is separately justified by scaling, security, failure containment, or ownership.

**Required Outputs**:

- A baseline pipeline manifest with per-slice scores and traces retained.
- A gate decision record for every candidate boundary with the verdict and its evidence.
- A stage inventory naming owner, contract, dependencies, side effects, and objective per stage.

**Quality Checkpoints**:

- The baseline runs end to end and produces a score for every slice in the critical-slice inventory; an unmeasured baseline blocks decomposition.
- Every admitted boundary cites at least 2 satisfied decompose conditions from Section 1.3.
- Every stage in the inventory has exactly 1 named owner; a stage without an owner is merged into an adjacent stage.

***

#### Step 2.2: Register Approved Implementations With Capability Metadata

**Required Actions**:

- Create a version-controlled registry entry for every approved implementation carrying stage identifier, implementation identifier, artifact digest, module version, and the list of supported contract versions.
- Record capabilities, modalities, languages, corpus types, and maximum input and output sizes for each entry.
- Record required scopes, trust tier, permitted data classifications, permitted regions, and permitted egress destinations for each entry.
- Record latency class, cost class, concurrency limit, health endpoint, and resource pool for each entry.
- Record determinism properties, statefulness, idempotency, cacheability, and side effects for each entry.
- Record owner, support contact, deprecation state, rollout status, last security review, evaluation report reference, approved slices, known limitations, and fallback chain for each entry.
- Resolve implementations through the registry in a fixed order: contract compatibility, then authorization and residency, then required capability and health, then remaining deadline and budget, then feature-flag and experiment assignment, then the pinned implementation or approved weighted variant, recording the resolved entry and digest in the run manifest.
- Prohibit ambient lookup: a stage may consume only dependencies its contract declares, and runtime registration from untrusted input is refused.

**Required Outputs**:

- A registry containing one entry per approved implementation with all seven metadata groups populated.
- A resolution order specification with the six filters applied in the declared sequence.
- A per-run resolution record naming the entry and digest selected for every stage.

**Quality Checkpoints**:

- Every registry entry carries an artifact digest and at least 1 supported contract version; an entry pinned to a mutable tag is refused.
- Every stage has at least 1 eligible implementation and, for stages under active experimentation, at least 2, since a stage with 1 occupant is not replaceable.
- No stage acquires a dependency absent from its contract; a detected ambient lookup halts the run.

***

#### Step 2.3: Run the Substitution Test Before Admission

**Required Actions**:

- Validate schema and contract conformance for the candidate, including behaviour on empty, malformed, adversarial, multilingual, oversized, timed-out, and cancelled inputs.
- Verify that the candidate preserves required authorization propagation, tenant isolation, provenance fields, redaction behaviour, and deletion propagation.
- Execute the deterministic golden case set and the error-path set, requiring 100 percent pass on both.
- Measure the candidate on the target slice against the incumbent and require the adoption bar defined in Step 4.2 to be met before eligibility.
- Measure p95 and p99 latency, token use, monetary cost, and concurrency behaviour against the stage's declared allocation, rejecting any candidate whose p95 exceeds its allocation.
- Confirm score or confidence semantics are either compatible with the incumbent or isolated behind a declared adapter, and record which.
- Confirm the candidate reads required checkpoint state or that a migration exists, that its caches can be cold-started or invalidated safely, and that shadow comparison and immediate reversion are both demonstrated.
- Refuse the label of replaceable to any candidate whose adoption requires untracked prompt edits, a full index rebuild without dual-read support, incompatible persisted state, or a coordinated release of every consumer.

**Required Outputs**:

- A substitution test report with a pass or fail verdict against each of the nine criteria.
- A score-semantics compatibility statement naming either direct compatibility or the adapter used.
- A demonstrated reversion record showing the incumbent restored within the declared rollback window.

**Quality Checkpoints**:

- All 9 substitution criteria return pass; a single failure blocks registry admission.
- Golden case and error-path pass rates are both 100 percent; any failure blocks admission regardless of aggregate quality gain.
- Reversion to the incumbent completed within the declared rollback window during the test; an untested reversion path blocks admission.

***

### Phase 3: Pipeline Composition as Versioned Configuration

**Objective**: Express the composed pipeline as an immutable, inspectable manifest that validates and compiles before execution, so that a result is attributable to a configuration rather than to code structure.

#### Step 3.1: Author the Immutable Pipeline Manifest

**Required Actions**:

- Record manifest identity as pipeline identifier, pipeline version, manifest digest, creation timestamp, owner, environment, and change reference.
- Record every node with its stage identifier, implementation identifier, contract version, model version, prompt digest, policy version, and artifact digest.
- Record every edge with its condition, join semantics, loop limit, timeout, retry policy, fallback target, and cancellation propagation rule.
- Record input and output mappings, required capabilities, tenant and corpus selectors, cache policies, and resource classes per node.
- Record global and per-node ceilings for latency, tokens, cost, evidence items, concurrency, fan-out, and iterations.
- Record the corpus manifest, index manifest, feature-flag snapshot, secrets references, and evaluation dataset version bound to this pipeline version.
- Record random seeds where the runtime honours them and record an explicit nondeterminism note for every component where it does not.
- Restrict environment overlays to deployment facts such as endpoints, replica counts, and secret references, and prohibit an overlay from changing retrieval depth, model, prompt, threshold, policy, or topology.

**Required Outputs**:

- One immutable pipeline manifest per environment with all eight record groups populated.
- An overlay specification listing the permitted overlay keys and no others.
- A fully resolved manifest with its digest recorded against the approved release.

**Quality Checkpoints**:

- Every node names a pinned artifact digest; a node referencing a mutable tag blocks manifest acceptance.
- Every component whose output is nondeterministic carries an explicit nondeterminism note; an unmarked nondeterministic component invalidates later attribution.
- No overlay key falls outside the permitted list; an overlay altering behaviour is rejected as a manifest change requiring its own release.

***

#### Step 3.2: Validate and Compile the Manifest Before Execution

**Required Actions**:

- Parse the manifest against a pinned schema and refuse execution on any parse failure.
- Resolve every node through the approved registry and refuse any implementation absent from it.
- Check contract compatibility for every edge, confirming that the upstream emitted contract version appears in the downstream accepted list.
- Check the graph for missing inputs, unreachable nodes, unbounded cycles, ambiguous joins, and duplicate side effects.
- Confirm that the sum of child budgets does not exceed the parent budget on every dimension, and that the declared reserve from Step 1.1 remains unallocated.
- Confirm that identity, authorization scope, policy version, deadline, and trace context propagate across every edge.
- Resolve exact artifact digests and compute a compiled plan hash over the fully resolved plan.
- Refuse execution where any mutable reference survives resolution, and record the refusal with the offending node.

**Manifest Validation Sequence**:

```
VALIDATE_MANIFEST
  1. parse_against_pinned_schema        -> FAIL: refuse, report parse error
  2. resolve_nodes_via_registry         -> FAIL: refuse, report unknown implementation
  3. check_edge_contract_compatibility  -> FAIL: refuse, report version pair
  4. check_graph_wellformedness         -> FAIL: refuse, report cycle or ambiguous join
  5. check_budget_sum_within_parent     -> FAIL: refuse, report overallocated dimension
  6. check_context_propagation          -> FAIL: refuse, report severed edge
  7. resolve_digests_and_hash_plan      -> EMIT: compiled_plan_hash
  8. assert_no_mutable_reference        -> FAIL: refuse, report node and tag
  PASS CONDITION: steps 1 through 8 all succeed
  ON ANY FAILURE: execution does not begin; no partial pipeline runs
```

**Required Outputs**:

- A validation report with a verdict for each of the eight checks.
- A compiled plan hash bound to the run record.
- A refusal record naming the offending node for every failed validation.

**Quality Checkpoints**:

- All 8 validation checks pass before any node executes; a partial pipeline never runs on a failed manifest.
- The compiled plan hash appears in every run record; a run without one is excluded from evaluation comparisons.
- Child budget sums remain at or below the parent on 100 percent of dimensions.

***

#### Step 3.3: Select the Topology and Bound Its Control Flow

**Required Actions**:

- Select the least complex topology meeting measured requirements, escalating from linear only where a named failure slice justifies the escalation.
- Apply deterministic predicates for tenant, permissions, language, document type, and explicit user mode before invoking any learned or model-based router, and reserve the router for cases the predicates leave unresolved.
- Declare the join rule for every branching topology from the closed set, cap total candidates, deduplicate before ranking, and cancel branches once the join condition is satisfied.
- Give every loop an entry condition, a state delta requirement, an evidence-gain check, a maximum iteration count, a state-hash repetition check, and an explicit exit reason.
- Distinguish the three fusion decisions and configure them separately: candidate fusion combining ranked results, evidence fusion deduplicating and allocating context, and answer fusion combining independently generated conclusions.
- Prefer a deterministic acyclic graph wherever valid paths are knowable before execution, and permit planner-selected control flow only where the number or order of steps cannot be predetermined and a measured slice improvement justifies the added variance.
- Where planner-selected control flow is used, restrict the planner to approved stage capabilities, compile its proposal into a bounded plan before execution, prohibit creation of endpoints, credentials, scopes, or egress destinations, and enforce depth, node count, fan-out, wall time, token, and cost ceilings outside the model.

**Topology Selection Table**:

| Topology | Observable condition that justifies it | Mandatory bound |
| :-- | :-- | :-- |
| Linear | Stable workload; one path meets every gate | None beyond stage budgets |
| Conditional | Query classes differ by 10 points or more on the primary metric | Conservative default route on low router confidence |
| Branching and fan-out | Parallel sources add complementary recall or independent corroboration | Declared join rule, per-branch budget, candidate cap |
| Looping | One pass fails materially and another iteration can add new evidence | Iteration ceiling, evidence-gain floor, state-hash repetition check |
| Bounded hybrid | Step order unknowable in advance on a measured slice | Approved subgraph catalogue, compiled plan, external ceilings |

**Required Outputs**:

- A declared topology with its justifying failure slice named.
- A join specification for every branch point and a bound specification for every loop.
- A fusion configuration distinguishing candidate, evidence, and answer fusion.

**Quality Checkpoints**:

- Every topology escalation above linear names the failure slice it addresses; an unjustified escalation is reverted at the next release gate.
- Every branch point declares exactly 1 join rule from the closed set, and every loop declares an iteration ceiling; an unbounded branch or loop blocks manifest validation.
- No fusion step averages scores from stages with undeclared or incompatible score semantics.

***

### Phase 4: Per-Stage Evaluation Under Change Isolation

**Objective**: Attribute every measured change to exactly one stage by permitting exactly one difference per evaluation cycle, so that modularity delivers its central benefit rather than merely its cost.

#### Step 4.1: Freeze the Evaluation Set and the Baseline Run

**Required Actions**:

- Version the evaluation set and split it into a tuning portion used for iteration and a held-out portion reserved for release gating, and never optimise against the held-out portion.
- Label every case with its query, authoritative sources, answer-bearing spans, acceptable answer or required abstention, risk tier, and slice labels.
- Execute the incumbent pipeline over the frozen cases and retain per-case outputs, per-stage spans, per-stage inputs and outputs, and the compiled plan hash.
- Record per-stage input quality and output quality for every case, so that a later stage comparison can distinguish a weak stage from a stage supplied with weak input.
- Declare the primary metric per stage class before any candidate is measured, so that the metric is not selected after seeing results.
- Retain the baseline run identifier as the reference for every subsequent paired comparison in this pipeline version.

**Stage Metric Assignment**:

| Stage class | Primary metric | Secondary metrics |
| :-- | :-- | :-- |
| Pre-retrieval and query transformation | Downstream retrieval recall lift | Constraint preservation rate, added latency |
| Retrieval | Recall at the admitted cut | Rank of first relevant span, freshness, unauthorized-hit rate |
| Fusion | Incremental relevant evidence admitted | Source diversity, duplicate ratio, rank stability |
| Reranking | Ranking quality lift over first-stage order | Harmful demotion rate, latency, cost |
| Compression and selection | Answer-bearing span preservation | Token reduction, qualification loss, citation alignment |
| Generation | Groundedness and citation precision | Correctness, abstention correctness, schema validity |
| Routing | Route regret against the best eligible path | Coverage, calibration error, policy violation rate |
| Orchestration | End-to-end utility per unit cost | Loop gain, fallback success, budget compliance |

**Required Outputs**:

- A versioned evaluation set with a declared tuning and held-out split.
- A baseline run record with per-case outputs, per-stage spans, and the compiled plan hash.
- A declared primary metric per stage class, fixed before comparison.

**Quality Checkpoints**:

- The held-out portion is at least 30 percent of labelled cases and has never been used for tuning; a contaminated split invalidates every release gate computed from it.
- Every critical slice carries at least 30 labelled cases, below which paired comparison on that slice is reported as underpowered rather than as a result.
- Every stage has exactly 1 declared primary metric fixed before any candidate run.

***

#### Step 4.2: Execute the One-Change Cycle With Paired Comparison

**Required Actions**:

- Change exactly one stage, one implementation, or one parameter set per evaluation cycle, holding every other node, digest, prompt, index manifest, seed, and policy version constant.
- Execute the candidate over the identical frozen cases in the identical order, producing a candidate run record with its own compiled plan hash.
- Compute per-case paired deltas on the primary metric for the target slice, and compute 95 percent confidence intervals by bootstrap resampling with at least 10,000 resamples.
- Apply a paired significance test appropriate to the metric, using a paired test for binary outcomes and a signed-rank test for continuous scores, and record the resulting p-value.
- Apply the adoption bar: a stage replacement is adopted only where the paired improvement on the target slice's primary metric is at least 3 percentage points, the 95 percent confidence interval on the paired delta excludes zero, the p-value is below 0.05, and no critical slice regresses by more than 1 percentage point.
- Apply the higher bar for additive changes: where the change increases pipeline node count rather than replacing an occupant, require at least 5 percentage points on the target slice, matching the admission threshold used for a new retrieval architecture, because a new stage carries a permanent operational cost that a swap does not.
- Record latency, token, and cost deltas alongside the quality delta, and reject any change whose quality gain arrives with a p95 latency or cost increase exceeding the stage's declared allocation.
- Cap tuning at 5 cycles per hypothesis on the tuning portion; after 5 cycles without meeting the bar, revise the hypothesis rather than continuing to tune.

**Required Outputs**:

- A paired comparison record naming baseline run, candidate run, changed stage, and changed version.
- A statistics record carrying the point delta, the confidence interval, the p-value, and the per-slice deltas.
- An adoption verdict citing the bar applied and every criterion's measured value.

**Quality Checkpoints**:

- Exactly 1 difference exists between the baseline and candidate compiled plans; a comparison across 2 or more differences is recorded as unevaluated and blocks adoption.
- The adoption verdict cites all 4 adoption criteria with measured values; a verdict citing only an aggregate improvement is rejected.
- No adopted change regresses any critical slice by more than 1 percentage point, regardless of aggregate gain.

***

#### Step 4.3: Attribute the Measured Change to a Stage

**Required Actions**:

- Run an ablation for the stage under test, bypassing it or replacing it with the simplest valid operator, and record its marginal contribution against the full pipeline on the same frozen cases.
- Run interaction tests pairing the changed stage with at least the immediately upstream and immediately downstream alternatives, since a stage's contribution is conditional on what feeds it and what consumes it.
- Compare a router against an oracle-route baseline that selects the best eligible path per case, and report regret rather than classification accuracy alone.
- Localise a failure to the earliest stage whose output fails its own quality metric, and distinguish input failure, stage failure, orchestration failure, and interaction failure before proposing a remedy.
- Mark an attribution as confounded, and refuse to report it as causal, wherever the compared runs differ in upstream input, downstream policy, corpus snapshot, or evaluation set version.
- Refuse causal attribution from production correlation alone, since a reranker measures weak when retrieval supplied no relevant candidates and a generator measures strong when a router sent it easier cases.
- Store per-case paired outcomes with baseline run identifier, candidate run identifier, ablation identifier, changed stage and version, dataset version, seed, quality delta, latency delta, cost delta, and confidence interval.

**Required Outputs**:

- An ablation record stating the stage's marginal contribution with a confidence interval.
- An interaction record covering the changed stage against upstream and downstream alternatives.
- A failure localisation record naming the earliest failing stage and its failure class.

**Quality Checkpoints**:

- Every adopted stage carries a current ablation record; a stage whose bypass costs less than 3 percentage points on every slice is a retirement candidate under Step 6.3.
- Every attribution claim states whether it is controlled or confounded; an unqualified causal claim from production correlation is rejected.
- Interaction tests cover at least 1 upstream alternative and 1 downstream alternative for every adopted change.

***

### Phase 5: Cross-Stage Compatibility and Recalibration Detection

**Objective**: Detect the case in which an upstream stage changes what it emits while a downstream stage retains thresholds fitted against the previous distribution, which is the silent failure mode of modular systems.

#### Step 5.1: Version Contracts and Behaviour Separately

**Required Actions**:

- Apply semantic versioning to every public stage contract, requiring a major version for incompatible changes, a minor version for backward-compatible additions, and a patch version for backward-compatible fixes [9].
- Version behaviour separately from syntax, incrementing the behaviour version whenever the model, prompt, tokenizer, index manifest, scoring function, or default threshold set changes, even where the schema is unchanged.
- Declare, per stage, which downstream stages hold a fitted dependency on its output distribution, so that a behaviour change has a known blast radius before it ships.
- Support at most 2 adjacent major contract versions concurrently during a migration, unless an external consumer or a regulatory obligation requires a longer window.
- Add a compatibility adapter only where it preserves declared semantics; where it cannot, run the versions in parallel instead and route traffic by manifest rather than by adapter.
- Retire a version only after traffic, persisted state, cache entries, and the rollback window no longer depend on it.

**Required Outputs**:

- A version register carrying contract version and behaviour version per stage implementation.
- A fitted-dependency map naming, for each stage, the downstream stages calibrated against its output.
- A migration plan naming the concurrent versions, the adapter or parallel-run decision, and the retirement condition.

**Quality Checkpoints**:

- Every behaviour change increments the behaviour version; a model, prompt, index, or threshold change shipped under an unchanged version blocks release.
- No more than 2 adjacent major contract versions run concurrently without a recorded exception.
- Every stage emitting a score has a populated fitted-dependency map, including the empty case stated explicitly.

***

#### Step 5.2: Detect Upstream Output-Distribution Shift

**Required Actions**:

- Define a fixed sentinel query set of at least 200 cases spanning every critical slice, executed on a schedule and before every release, whose purpose is distribution measurement rather than quality measurement.
- Compute an output-distribution fingerprint per edge over the sentinel set, carrying admitted item count, score quantiles at the 10th, 50th, and 90th percentiles, null and warning rates, token counts, and the share of identifiers not present in the previous run.
- Compare the candidate fingerprint against the approved release fingerprint on every monitored dimension and compute a population stability index over the score distribution.
- Declare a recalibration event where any of the following holds: a monitored score quantile moves by more than 0.10 in normalised units, the population stability index exceeds 0.25, admitted item count changes by more than 20 percent, null or warning rate changes by more than 5 percentage points, or identifier novelty exceeds 30 percent.
- Distinguish the four drift classes and record which applies: declared drift from an approved manifest change, deployment drift where the running configuration differs from the approved manifest, dependency drift where a remote model, service, index, or plugin changed beneath an unchanged name, and data drift where query or corpus distributions moved.
- Run a scheduled drift job comparing active digests against the release manifest and executing the sentinel set, and block promotion on any undeclared drift.
- Where a provider cannot supply immutable model revisions, record response fingerprints, treat the endpoint as nondeterministic in the manifest, and require periodic regression runs plus a declared fallback.

**Recalibration Trigger Table**:

| Monitored dimension | Declared bound | Action on breach |
| :-- | :-- | :-- |
| Score quantile shift at p10, p50, or p90 | 0.10 in normalised units | Mark downstream fitted stages uncalibrated |
| Population stability index over score distribution | 0.25 | Mark downstream fitted stages uncalibrated |
| Admitted item count change | 20 percent | Re-fit downstream selection caps and evidence budgets |
| Null or warning rate change | 5 percentage points | Re-examine upstream error handling before release |
| Identifier novelty against previous run | 30 percent | Verify index cutover and cache invalidation |
| Undeclared deployment or dependency drift | Any occurrence | Block promotion and restore the approved manifest |

**Required Outputs**:

- A sentinel set of at least 200 cases with per-edge fingerprints retained per release.
- A fingerprint comparison report per edge with a breach verdict per monitored dimension.
- A drift classification record naming the drift class for every detected change.

**Quality Checkpoints**:

- Every edge whose upstream stage emits a score carries a fingerprint for the current release; a missing fingerprint blocks promotion.
- Every fingerprint breach produces a named action; a breach recorded without an action is a release blocker.
- Undeclared deployment or dependency drift blocks promotion in 100 percent of occurrences and is never waived at the pipeline level.

***

#### Step 5.3: Recalibrate or Isolate the Affected Downstream Stage

**Required Actions**:

- Mark every downstream stage on the affected edge as uncalibrated on a recalibration event, and treat its fitted thresholds as invalid until re-fitted, regardless of whether end-to-end scores moved.
- Re-fit affected thresholds on the tuning portion of the evaluation set under the new upstream distribution, and re-run the held-out evaluation before promotion.
- Where re-fitting is not possible within the release window, isolate the downstream stage behind a declared normalisation adapter that maps the new distribution onto the old, and record the adapter as a temporary artifact with an expiry date no more than 90 days out.
- Prefer rank-based fusion over score-based fusion wherever the upstream score scales are not jointly calibrated, since ranks survive a distribution shift that raw scores do not.
- Re-run the substitution test from Step 2.3 for the downstream stage after re-fitting, since its behaviour version has changed even though its implementation has not.
- Treat an index rebuild, an embedding model change, or a scoring function change as a recalibration event by default, without waiting for a fingerprint breach to confirm it.
- Record the recalibration in the version register as a behaviour version increment on the downstream stage, so that later attribution can distinguish it from an implementation change.

**Required Outputs**:

- An uncalibrated-stage list produced on every recalibration event.
- A re-fitting record naming the new thresholds, the tuning cases used, and the held-out result.
- An adapter register entry with an expiry date for every temporary normalisation adapter in service.

**Quality Checkpoints**:

- No stage marked uncalibrated reaches production; promotion is blocked until re-fitting or declared isolation completes.
- Every temporary normalisation adapter carries an expiry date within 90 days; an expired adapter blocks the next release.
- Every recalibration increments the downstream behaviour version; a silent re-fit is treated as undeclared drift.

***

### Phase 6: Controlled Rollout, Rollback, and Retirement

**Objective**: Release a composition change through staged exposure with armed automatic reversion, and remove stages that no longer earn their operational cost.

#### Step 6.1: Gate the Release Through Shadow and Canary

**Required Actions**:

- Treat any change to a manifest, stage artifact, prompt, model, threshold, index, policy, or registry entry as a release requiring the full gate.
- Build the release by resolving dependencies to immutable digests, validating schemas, compiling the pipeline, and producing a signed release manifest with a decision record.
- Run unit, contract, compatibility, property, and error-path tests, then deterministic golden cases and the smoke evaluation set, requiring 100 percent pass before proceeding.
- Run authorization, tenant-isolation, injection-containment, poisoning, secrets, and egress tests, and fail closed on any failure.
- Run the full offline paired evaluation and the ablations from Phase 4 against the approved baseline, and run load, concurrency, timeout, circuit, fallback, cache, and recovery tests.
- Deploy the candidate with no user traffic, replay approved traces with sensitive content removed or protected, and shadow live traffic without using candidate output.
- Compare quality proxies, error classes, latency percentiles, cost, route distribution, and security decisions between shadow and incumbent before any user exposure.
- Canary to a small authorized cohort behind a feature flag, hold exposure for a fixed observation window of at least 24 hours and at least 1,000 requests per critical slice, and increase exposure only after both bounds are satisfied.
- Keep the previous pipeline version, index aliases, and cache namespace available for the full rollback window.

**Required Outputs**:

- A signed release manifest with a decision record naming the approver.
- A shadow comparison report covering quality proxies, errors, latency, cost, routes, and security decisions.
- A canary record naming cohort size, observation window, per-slice request counts, and the exposure decision.

**Quality Checkpoints**:

- All contract, golden case, and security suites return 100 percent pass before shadow traffic begins.
- The canary observation window meets both the 24-hour and the 1,000-request-per-critical-slice bounds before exposure increases.
- The previous version, its index aliases, and its cache namespace remain restorable throughout the rollback window; an unrestorable predecessor blocks promotion.

***

#### Step 6.2: Arm Automated Rollback Triggers

**Required Actions**:

- Arm an automatic rollback on any authorization failure, cross-tenant result, or integrity failure, with no threshold and no waiting period.
- Arm an automatic rollback on any contract incompatibility detected in production traffic.
- Arm an automatic rollback on a groundedness or citation regression exceeding 1 percentage point on any critical slice.
- Arm an automatic rollback on a p95 or p99 latency, error rate, timeout rate, or cost breach of the declared budget for that release.
- Arm an automatic rollback on a route distribution shift exceeding 20 percent against the shadow baseline, or a fallback rate exceeding twice the incumbent rate.
- Arm an automatic rollback on stale evidence beyond the corpus freshness objective, or a circuit-open rate above its declared release threshold.
- Verify that a manifest reversion restores the prior compiled plan hash exactly, and prohibit a feature flag from combining incompatible persisted state or index formats without a migration plan.
- Prohibit promotion on aggregate quality improvement alone where any critical slice regressed, and prohibit canarying a schema-breaking change to consumers that cannot negotiate versions.

**Required Outputs**:

- An armed trigger set with a numeric threshold and an action for every trigger.
- A verified reversion record showing the prior compiled plan hash restored.
- A migration plan for every change touching persisted state or index format.

**Quality Checkpoints**:

- Every trigger carries a numeric or categorical condition and an automatic action; a trigger requiring human interpretation is not armed and does not count.
- Reversion restores the prior compiled plan hash exactly; an approximate reversion is treated as a new release requiring its own gate.
- Security, integrity, and cross-tenant triggers carry no threshold and no delay.

***

#### Step 6.3: Operate, Detect Drift, and Retire Unearned Stages

**Required Actions**:

- Monitor per-stage and pipeline metrics by slice, tenant, route, risk tier, and release, rather than in aggregate alone.
- Review open circuits, fallback invocations, degraded responses, route drift, configuration drift, and cache correctness on a fixed cadence, at least weekly.
- Convert every confirmed production failure into a labelled regression case in the tuning portion, and promote a case to the held-out portion only at the next evaluation set version.
- Re-run the ablation set on a fixed cadence, at least quarterly, and mark every stage whose bypass costs less than 3 percentage points on every critical slice as a retirement candidate.
- Retire a retirement candidate unless its owner records a named failure slice it closes within one release cycle, and remove its contract, registry entry, and monitoring on retirement.
- Descend the topology where a simpler arrangement now meets every gate, because a corpus change, a model change, or an upstream improvement closed the gap the complexity was added to close.
- Record every retirement with its evidence, so that a later proposal to reintroduce the stage begins from the measurement that removed it.

**Required Outputs**:

- A per-slice operating metric report on the declared cadence.
- A refreshed ablation record per stage on the declared cadence with a retirement verdict.
- A retirement record naming the removed stage, its evidence, and the artifacts removed with it.

**Quality Checkpoints**:

- Every stage carries an ablation record no older than one quarter; a stale record makes the stage a retirement candidate by default.
- Every retirement candidate is either retired or justified by a named failure slice within 1 release cycle.
- Confirmed production failures appear as labelled regression cases within 1 release cycle of confirmation.

***

## III. Implementation Guidance for AI Agents

AI agents composing retrieval pipelines must follow systematic protocols ensuring that every stage boundary is validated, every configuration is resolved and hashed before execution, and every measured change is attributable to one stage. The following guidance translates the composition discipline into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the stage contracts, the invariant register, and the closed error vocabulary. It alone may amend a contract, and every amendment increments a version. It never executes a stage.
2. **Registry Agent**: Owns the implementation registry and the substitution test. It admits, pins, deprecates, and refuses implementations, and it resolves each stage to exactly one digest per run.
3. **Composition Agent**: Owns the pipeline manifest, its validation sequence, and the compiled plan hash. It refuses execution on any validation failure and never runs a partial pipeline.
4. **Execution Orchestrator**: Runs the compiled plan, enforces the budget ledger, propagates identity, authorization, deadline, and trace context, and issues cancellations. It may not repair an invalid stage output.
5. **Evaluation Agent**: Owns the frozen evaluation set, the paired comparison arithmetic, the ablation and interaction runs, and the adoption verdict. It refuses a comparison across more than one difference.
6. **Calibration Agent**: Owns the sentinel set, the per-edge fingerprints, and the recalibration event. It marks downstream stages uncalibrated and blocks their promotion until re-fitting completes.
7. **Release Agent**: Owns shadow, canary, armed triggers, and reversion. It executes rollback without consulting a model and reports the trigger that fired.

**Trust and Data Handling Boundary**: Retrieved content, remote stage output, plugin metadata, and tool descriptions are untrusted data in every component.

- Retrieved text may never alter a route, a budget, a tool permission, a policy, a credential, or an egress destination.
- Secrets live in a secrets manager and never in manifests, prompts, traces, or stage outputs.
- Logs carry digests and redacted fields by default; raw prompts, evidence, and outputs require an explicit content-logging policy.
- A protocol boundary is a trust boundary: identity, scope, purpose, deadline, and classification are propagated and independently enforced on the far side, and credentials are scoped to the remote capability rather than forwarded broadly.

**Workflow Execution Pattern**:

```
STATE: Stage_Boundary_Transition
INPUTS:
  1. Upstream stage output with declared contract version
  2. Downstream stage contract and accepted version list
  3. Budget ledger remaining allocation and inherited deadline
ACTIONS:
  1. Validate upstream output against its declared output schema
  2. Assert provenance fields present on every forwarded evidence unit
  3. Assert deadline_child <= deadline_parent and budget_remaining >= 0
  4. Check emitted_contract_version IN accepted_upstream_versions
  5. Record span with stage identity, digests, costs, and decisions
VALIDATION:
  - output_schema_valid == TRUE
  - provenance_fields_complete == TRUE
  - deadline_monotonic == TRUE
  - budget_within_allocation == TRUE
  - contract_version_accepted == TRUE
  - calibration_state != UNCALIBRATED
TRANSITIONS:
  IF all_validations_pass THEN next_state = Downstream_Stage_Execution
  IF contract_or_provenance_failure THEN next_state = Halt_With_Error_Class
  IF budget_exhausted THEN next_state = Declared_Abstention_Or_Degraded
  IF quality_or_availability_failure THEN next_state = Declared_Fallback
  IF calibration_state == UNCALIBRATED THEN next_state = Block_Promotion
```

**Two-Phase Action Pattern**: Resolve and compile the manifest, emitting the compiled plan hash and the resolved digest set without executing any node; validate that plan against the eight checks in Step 3.2 while no resource is committed; execute only after validation passes, binding the compiled plan hash to the run record in the same operation.

**Approval Gate**: Human authorisation is required before promoting any change that alters a security control, a data classification, an egress destination, or a tenant isolation boundary; before promoting a release whose critical-slice regression exceeds 1 percentage point; before any adapter expiry extension; and before any exposure increase beyond 25 percent of traffic for a stage whose behaviour version changed in this release. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the manifest, budget ledger, resolution record, and fingerprint set in durable state, since a pipeline may outlive a single context window.
- Carry evidence forward as identifiers and digests rather than as full payloads once a claim is verified, retaining the reference and discarding the bulk.
- Write a handoff record at every context boundary naming the compiled plan hash, the executed nodes, the remaining budget per dimension, and the pending stages.
- Count orchestration overhead against the budget rather than treating it as free, and report it as a share of total run cost.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Integrity (After Phase 1)**

- **Automated Check**: Every stage contract carries all 8 blocks; every error class belongs to the closed vocabulary; every invariant has an executable boundary assertion; the declared reserve is at least 15 percent of the latency budget.
- **Agent Action on Pass**: Proceed to stage inventory and registration.
- **Agent Action on Failure**: Halt and return the incomplete contract; no stage is built against a partial contract.
- **Human Review Trigger**: An invariant that cannot be expressed as an executable assertion, or a stage in the highest risk tier.

**Checkpoint 2: Registration Integrity (After Phase 2)**

- **Automated Check**: Every registry entry carries an artifact digest and supported contract versions; every stage under experimentation has at least 2 eligible implementations; all 9 substitution criteria pass for each admitted candidate.
- **Agent Action on Pass**: Proceed to composition.
- **Agent Action on Failure**: Refuse admission and return the failing criteria; a partially passing candidate is not admitted with a waiver.
- **Human Review Trigger**: A candidate failing only the security or deletion-propagation criterion, which is never waived automatically.

**Checkpoint 3: Manifest Validity (After Phase 3)**

- **Automated Check**: All 8 manifest validation steps pass; no mutable reference survives resolution; child budget sums remain within the parent on 100 percent of dimensions; every branch declares a join rule and every loop an iteration ceiling.
- **Agent Action on Pass**: Permit execution and bind the compiled plan hash.
- **Agent Action on Failure**: Refuse execution entirely; a partial pipeline never runs on a failed manifest.
- **Human Review Trigger**: A topology escalation above linear with no named failure slice.

**Checkpoint 4: Attribution Integrity (After Phase 4)**

- **Automated Check**: Exactly 1 difference between baseline and candidate compiled plans; adoption verdict cites all 4 criteria with measured values; held-out split uncontaminated; every critical slice carries at least 30 cases.
- **Agent Action on Pass**: Record the adoption verdict and proceed to compatibility checking.
- **Agent Action on Failure**: Record the cycle as unevaluated and block adoption; a multi-change comparison is never reported as an attribution.
- **Human Review Trigger**: A proposed adoption whose target-slice gain meets the bar while another critical slice regresses between 0.5 and 1 percentage points.

**Checkpoint 5: Calibration Integrity (After Phase 5)**

- **Automated Check**: Every scored edge carries a current fingerprint; every breach carries a named action; no stage marked uncalibrated is present in the release; every temporary adapter carries an unexpired date.
- **Agent Action on Pass**: Proceed to release gating.
- **Agent Action on Failure**: Block promotion and return the uncalibrated stage list.
- **Human Review Trigger**: A recalibration event with no available re-fitting window, requiring an adapter decision.

**Checkpoint 6: Release Integrity (After Phase 6)**

- **Automated Check**: Contract, golden case, and security suites at 100 percent pass; canary window meets both the 24-hour and 1,000-request bounds; every trigger armed with a numeric condition; reversion restores the prior compiled plan hash exactly.
- **Agent Action on Pass**: Increase exposure per the declared ramp.
- **Agent Action on Failure**: Roll back to the approved manifest and report the failing gate.
- **Human Review Trigger**: Any security, integrity, or cross-tenant trigger firing, and any rollback executed more than once against the same candidate.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
COMPILED_PLAN_HASH:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Contract Erosion After a Stage Swap**

- **Symptoms**: A downstream stage reports missing fields; citations stop resolving; authorization decision references disappear from evidence units; end-to-end quality falls while every stage-local test passes.
- **Diagnostic Steps**: Compare the emitted output schema of the replaced stage against the previous version field by field, and run the boundary assertion suite from Step 1.3 against the affected edge.
- **Resolution Protocol**: Option A, restore the dropped fields in the replacement and re-run the substitution test. Option B, revert to the incumbent and re-admit the candidate only after the provenance assertion passes. Option C, where the field is genuinely obsolete, retire it through a major contract version with the downstream consumers migrated first.
- **Escalation Trigger**: Any dropped provenance, authorization, or policy field halts the run immediately; this class is never resolved by retry and never mitigated by a downstream repair.

**Error Type 2: Attribution Loss From Simultaneous Changes**

- **Symptoms**: A measured delta cannot be assigned to a stage; the baseline and candidate compiled plan hashes differ in more than one node; a regression appears after a release bundling several changes.
- **Diagnostic Steps**: Diff the two compiled plans and enumerate every differing node, digest, prompt, threshold, and index manifest.
- **Resolution Protocol**: Option A, decompose the release into single-change cycles and re-run each against the same frozen cases. Option B, bisect the change set by compiled plan hash, halving the differing node set per run. Option C, revert the whole bundle and re-admit changes individually.
- **Escalation Trigger**: After 3 bisection rounds without isolating the cause, revert to the last approved manifest and escalate to the stage owners of every differing node.

**Error Type 3: Silent Recalibration Across a Boundary**

- **Symptoms**: Admitted item counts move without a code change; a reranker or threshold stage admits far more or far fewer candidates; quality falls on one slice while the upstream stage's own metrics improve.
- **Diagnostic Steps**: Compute the per-edge fingerprint against the approved release and evaluate every trigger in the recalibration table; confirm whether the upstream behaviour version changed.
- **Resolution Protocol**: Option A, re-fit the downstream thresholds under the new distribution and re-run the held-out evaluation. Option B, isolate the downstream stage behind a declared normalisation adapter with an expiry date within 90 days. Option C, replace score-based fusion with rank-based fusion so that the downstream stage no longer depends on absolute score scales.
- **Escalation Trigger**: A second recalibration event on the same edge within one release cycle escalates to the upstream stage owner for a versioning review; an expired adapter blocks the next release outright.

**Error Type 4: Unbounded Composition**

- **Symptoms**: Fan-out grows without a cap; a loop repeats without new evidence; branch cancellations do not fire; the budget ledger reaches zero before generation; orchestration overhead exceeds the stage cost it governs.
- **Diagnostic Steps**: Inspect the manifest for a missing join rule, a missing iteration ceiling, or a missing cancellation propagation rule, and check whether a state hash repeated within the run.
- **Resolution Protocol**: Option A, restore the missing bound in the manifest and refuse execution until validation passes. Option B, reduce the topology one level, from looping to conditional or from conditional to linear, for the affected route. Option C, terminate the run through a declared abstention carrying the supported partial result.
- **Escalation Trigger**: Orchestration overhead above 25 percent of run cost triggers a topology review; above 40 percent the composition is reverted to the last configuration that met the budget.

**Error Type 5: Configuration Drift and Irreproducible Runs**

- **Symptoms**: Two runs sharing a pipeline version produce different results; a run record carries no compiled plan hash; a remote model or index changed beneath an unchanged name; a mutable tag appears in an active manifest.
- **Diagnostic Steps**: Compare active digests against the release manifest, execute the sentinel set, and classify the drift as declared, deployment, dependency, or data drift.
- **Resolution Protocol**: Option A, restore the approved manifest and re-run the sentinel set to confirm the fingerprints return. Option B, pin the drifting dependency to an immutable revision, or where none exists, record response fingerprints and mark the endpoint nondeterministic. Option C, publish a new release capturing the change as declared drift with its own evaluation.
- **Escalation Trigger**: Undeclared deployment or dependency drift blocks promotion immediately; a second occurrence on the same dependency within one quarter escalates to a dependency replacement decision.

**Error Type 6: Boundary Security Failure**

- **Symptoms**: Evidence appears from a corpus outside the authorization scope; a cross-tenant identifier surfaces in a cache or trace; retrieved content changes a route or a tool argument; an unpinned or unsigned artifact executes; an unapproved egress destination is contacted.
- **Diagnostic Steps**: Identify the stage version, compiled plan hash, registry record, affected runs, tenants, caches, and derived artifacts, preserving digests and traces before any change.
- **Resolution Protocol**: Option A, halt the run, block output and side effects, open the affected circuit, and quarantine the stage or corpus. Option B, roll back to the last approved manifest, revoke credentials, and invalidate derived caches and summaries. Option C, repair artifact admission or policy enforcement and re-run the contract, authorization, adversarial, and regression suites before restoration.
- **Escalation Trigger**: Every confirmed authorization, cross-tenant, integrity, secret, or unapproved-egress incident escalates to security and data owners on first occurrence, with at most 1 automated remediation attempt; degradation around a failed security control is prohibited.

**Troubleshooting Decision Tree**:

```
COMPOSED PIPELINE FAILS A GATE
├─ BOUNDARY DEFECT
│   ├─ Output fails downstream schema → HALT; return error class; revert stage
│   ├─ Provenance field missing → HALT; never repair downstream
│   └─ Child deadline exceeds parent → Reject edge; recompile manifest
├─ ATTRIBUTION DEFECT
│   ├─ More than one node differs → Mark unevaluated; decompose into single changes
│   ├─ Held-out split contaminated → Rebuild split; invalidate gate verdicts
│   └─ Slice under 30 cases → Report underpowered; do not adopt
├─ CALIBRATION DEFECT
│   ├─ Fingerprint breach on a scored edge → Mark downstream uncalibrated; re-fit
│   ├─ Adapter past expiry → Block release; re-fit or replace
│   └─ Score fusion across uncalibrated scales → Switch to rank fusion
├─ CONTROL DEFECT
│   ├─ Missing join rule or loop ceiling → Refuse manifest; restore the bound
│   ├─ Budget exhausted before generation → Declared abstention with partial result
│   └─ Overhead above 40 percent of run cost → Revert to the simpler topology
├─ CONFIGURATION DEFECT
│   ├─ Mutable tag in active manifest → Refuse execution; pin the digest
│   └─ Undeclared deployment drift → Block promotion; restore approved manifest
└─ SECURITY DEFECT
    ├─ Cross-tenant or unauthorized evidence → HALT; quarantine; escalate
    └─ Retrieved content altered control state → HALT; separate control from content
```

### D. Performance Metrics and Continuous Learning

**Composition Integrity Metrics**:

- **Contract validation pass rate**: Stage invocations whose input and output both validate (target: 100 percent; any failure is a halt, not a warning).
- **Provenance completeness**: Evidence units crossing a boundary with every mandatory provenance field present (target: 100 percent).
- **Manifest reproducibility**: Runs carrying a compiled plan hash resolvable to pinned digests (target: 100 percent; a run without one is excluded from evaluation).
- **Budget compliance**: Stage invocations completing within their declared allocation on every dimension (target: at least 99 percent; breaches are recorded per dimension).
- **Orchestration overhead**: Control-plane cost over total run cost (target: no more than 25 percent; above 40 percent triggers a topology review).

**Attribution and Quality Metrics**:

- **Change isolation rate**: Evaluation cycles carrying exactly one difference (target: 100 percent; a lower rate means attribution is being lost).
- **Attribution confidence**: Adopted changes whose paired confidence interval excluded zero (target: 100 percent).
- **Ablation currency**: Stages carrying an ablation record no older than one quarter (target: at least 95 percent).
- **Router regret**: Difference between the chosen path's outcome and the best eligible path's outcome under offline counterfactual comparison (target: no more than 5 percent of achievable utility; report by slice, never as accuracy alone).
- **Critical-slice floor**: Lowest per-slice primary metric across the critical-slice inventory (target: above the declared hard gate for every slice; an aggregate improvement never compensates a floor breach).

**Operational Metrics**:

- **Recalibration detection latency**: Releases between an upstream behaviour change and its recalibration event being raised (target: 0; a shift detected only after a downstream quality regression counts as a detection failure).
- **Fallback rate and success**: Invocations taking a declared fallback, and the share producing a contract-valid degraded result (target: fallback rate below twice the incumbent; fallback success at least 90 percent).
- **Rollback correctness**: Rollbacks restoring the prior compiled plan hash exactly (target: 100 percent).
- **Cache correctness**: Cache hits passing reauthorization and freshness recheck (target: 100 percent; a stale or unauthorized hit is a security defect, not a performance defect).
- **Stage retirement rate**: Retirement candidates resolved within one release cycle (target: at least 90 percent; unresolved candidates accumulate as unearned complexity).

**Learning and Adaptation Mechanisms**:

- **Regression case accrual**: Every confirmed production failure becomes a labelled case in the tuning portion within 1 release cycle, and enters the held-out portion only at the next evaluation set version.
- **Registry hygiene**: Implementations with no traffic and no approved slice for 2 consecutive quarters are deprecated, since registry size is itself an operational risk.
- **Threshold recomputation**: Every numeric threshold in this guide is recomputed per deployment against observed outcomes; the values stated here are deployment defaults rather than measured constants.
- **Fingerprint history**: Per-edge fingerprints are retained across releases so that a gradual shift below the single-release bound is detectable as a trend.

**Human-in-the-Loop Boundaries**: Amendment of a security control, a data classification, an egress allowlist, or a tenant isolation boundary; extension of a normalisation adapter past its expiry; promotion of a release with a critical-slice regression; and any waiver of a substitution test criterion are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how retrieval stages are contracted, composed, versioned, and attributed rather than what any stage retrieves. Its phases hold wherever a retrieval path has more than one replaceable component, a labelled evaluation set, and a cost for adding complexity.

### 4.1 Cross-Domain Application Patterns

**Regulated financial and insurance operations**: Boundaries follow credential and audit lines, because different source systems carry different entitlements and different retention obligations. The retrieval stage decomposes per source system so that each carries its own credential and its own authorization decision reference, and cross-corpus fusion is admitted only where the principal is authorized for every input and the output policy states how restrictions combine. Derivatives such as summaries inherit the strictest applicable restriction of their supporting evidence. The manifest becomes a compliance artifact: a supervisor asks which configuration produced a given answer, and the compiled plan hash answers it.

**Clinical and scientific evidence synthesis**: Authority hierarchy dominates, so the post-retrieval stage decomposes into separate selection and provenance stages, and the fusion configuration never permits a majority vote to override an authoritative source. Behaviour versioning is strict because a guideline revision changes what a correct answer is: the corpus manifest and the policy version are release-gating fields rather than metadata. Ablation is run per evidence class, since a stage that helps on trial literature may harm on regulatory documents.

**Industrial operations and field support**: Latency ceilings are hard and connectivity is intermittent, so the topology stays linear on the common path with a conditional branch only for the measured minority of queries requiring a remote corpus. Fallback chains are declared in advance and exercised in test rather than discovered in an incident, and a degraded response names the branches it lost. Budget allocation is per route rather than global, so a rare expensive path cannot consume the deadline of the common cheap one.

**Software engineering and internal developer platforms**: Stage boundaries follow index type, because a structural index over symbols and a text index over documentation have different freshness, different rebuild costs, and different failure modes. Recalibration detection matters most here, since index rebuilds are frequent and a rebuild changes score distributions without changing any code. Registry hygiene is enforced aggressively because implementation proliferation is the common failure and retired stages leave contracts behind.

**Public-sector service delivery**: Tenant and jurisdiction isolation is enforced before retrieval rather than filtered after generation, and shared indexes are used only where negative tests show no cross-tenant results, metadata leakage, count disclosure, cache collision, or timing side channel. Evaluation sets are versioned per jurisdiction because a policy change in one does not license a threshold change in another. Abstention is a first-class outcome, since an unsupported answer carries a higher cost than a declared gap.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small scope, low risk**: Keep one deployable service holding every stage, use typed in-process contracts, store the manifest as a version-controlled file, and run the evaluation set from local files. The composition discipline is retained in full; only the deployment topology collapses. Orchestration overhead above 10 percent of direct execution cost indicates the decomposition gate should have returned suppress.
- **Large scope, many owners**: Split along ownership lines first and scaling lines second, since a boundary without an owner accumulates unattributed defects. Require a registry entry with a security review date, publish per-stage service-level objectives, and run cross-stage compatibility checks on a schedule rather than only at release.
- **High risk or irreversible downstream action**: Retain every phase, require a deterministic acyclic topology wherever paths are knowable, bind the approval gate before any exposure increase, and prefer abstention over a degraded answer. Fallback from an access-controlled corpus to model memory is prohibited without exception.
- **Strict latency budgets**: Shorten stage allocations rather than removing validation, because removing a boundary assertion removes attribution while shortening an allocation preserves it. Run a cheap gate before an expensive stage only where the gate has high recall for cases needing the expensive path, and cancel branches whose completion cannot affect the join.
- **Cross-organisational composition**: Where a stage is owned by another party, treat the protocol boundary as a trust boundary, negotiate schema and capability versions before sending sensitive content, allowlist endpoints, bound bytes, items, calls, and task duration, require structured evidence artifacts with source identifiers and digests rather than prose conclusions, and verify returned citations locally [10][11].

***

## V. Limitations and Considerations

**Thresholds here are deployment defaults, not measured constants**: Every numeric bound in this guide, including the 3 and 5 percentage point adoption bars, the 0.25 population stability index, the 0.10 quantile shift, the 20 percent item-count change, the 30 percent held-out share, the 30-case slice floor, the 24-hour canary window, the 25 and 40 percent overhead thresholds, and the 90-day adapter expiry, was chosen to be operable on first deployment rather than derived from a universal property of retrieval systems. The mitigation is the recomputation requirement in Section III.D, obliging each deployment to re-derive its thresholds against observed outcomes and to record the derivation alongside the manifest.

**Modularity buys attribution at the cost of complexity**: Each boundary adds a contract, a version, an evaluation, a failure mode, and a monitoring surface, and the total cost is paid continuously while the benefit is realised only when a stage is actually replaced. The mitigation is the decomposition gate in Section 1.3, which requires 2 measured conditions before a split, and the quarterly ablation and retirement rule in Step 6.3, which removes stages whose bypass costs less than 3 percentage points.

**Change isolation slows delivery**: The one-change rule means a release bundling five improvements requires five evaluation cycles, and teams under schedule pressure bundle changes and lose attribution. The mitigation is to run isolation cycles on the tuning portion in parallel where infrastructure permits, and to treat a bundled release as unevaluated rather than as evaluated with a caveat, so that the cost of bundling falls on the release decision rather than on later debugging.

**Attribution remains conditional on neighbours**: A stage's measured contribution holds only for the pipeline it was measured in, because a reranker measures weak when retrieval supplied no relevant candidates and a generator measures strong when a router sent it easier cases. Recent controlled ablation work found a rule-based adaptive router underperforming a fixed hybrid retrieval configuration it was intended to replace, by 1.8 exact-match points, illustrating that a component justified in isolation can lose against a simpler neighbour arrangement [3]. The mitigation is the interaction testing requirement in Step 4.3 and the explicit confounded marking, which prevents a conditional result from being reported as a general property.

**Distribution fingerprints detect shift, not harm**: A fingerprint breach establishes that an upstream stage changed what it emits, not that the change degrades results, and a stable fingerprint does not prove a downstream stage is still well calibrated. The mitigation is to treat a breach as a recalibration obligation rather than a rollback trigger, and to pair fingerprint monitoring with the held-out evaluation, since neither detects the other's failures.

**Telemetry conventions for this domain are unstable**: The generative-AI semantic conventions maintained for shared observability moved to a dedicated repository and, as verified during this conversion, every span, metric, and attribute in that set remained at development status rather than stable as of mid-2026 [12]. Field names may therefore change beneath an unchanged instrumentation library. The mitigation is to pin the convention version in the manifest, to carry retrieval-specific fields in an internal namespace, and to treat a convention upgrade as a release requiring its own gate.

**Score comparability across implementations is not guaranteed**: Scores from different retrievers, rerankers, or embedding models occupy different scales, and a threshold fitted on one does not transfer to another; embedding model upgrades in particular are recalibration events sold as infrastructure swaps [4]. The mitigation is the declared score semantics requirement in Step 1.2, the preference for rank-based fusion in Step 5.3, and the prohibition on averaging uncalibrated scores.

**Structural conformance is not a sound composition**: A pipeline can satisfy every checkpoint in this guide and still compose stages that do not serve the question class it was built for. The framework detects malformed composition, not misdirected purpose, and no checkpoint substitutes for review of the system contract against the actual information need.

***

## VI. Conclusion and Summary

Modular retrieval-augmented generation is a composition discipline before it is an architecture. Its value does not come from having many stages; it comes from being able to state what each stage promises, to resolve a run to one inspectable configuration, to attribute a measured change to one stage, and to remove a stage when its contribution can no longer be measured. A system that decomposes without contracts acquires the cost of modularity and none of its benefit, and a system that decomposes without change isolation acquires stages it can neither improve nor retire.

A team adopting this discipline should build the typed contracts before the boundaries. Implement an in-process linear pipeline against the contracts a modular system would use, freeze an evaluation set, and record a baseline whose per-slice scores and per-stage spans are retained. Split only the stage whose replacement, scaling, ownership, security, or experimentation need is measured. Add routing, branching, or looping one at a time, each naming the failure slice it closes and each proved by a paired comparison over the same frozen cases. Release through shadow and canary with armed reversion, and re-run the ablation set on a schedule so that complexity retained without evidence is removed rather than inherited.

**Key Success Factors**:

- **Contract before boundary**: What a stage accepts, emits, may spend, and must preserve is declared before the stage exists, so that replacement is a configuration decision rather than a rewrite.
- **Provenance and budget survive every hop**: The fields no single stage consumes for itself are asserted at every boundary, because those are the fields recomposition drops without any local test failing.
- **Configuration is an artifact**: A run is attributable to an immutable manifest and a compiled plan hash, and a manifest carrying a mutable reference does not execute.
- **One change per cycle**: Attribution is the benefit modularity exists to deliver, and it is destroyed by any comparison across two simultaneous differences.
- **Shift detection precedes regression**: An upstream distribution change marks downstream fitted stages uncalibrated before a quality metric moves, because a shift discovered through a regression was discovered too late.
- **Complexity is retired, not accumulated**: A stage whose bypass costs nothing measurable is removed, and its contract, registry entry, and monitoring go with it.

By following this guide, AI agents can compose retrieval systems whose stages are genuinely replaceable, whose results are reproducible from a declared configuration, and whose regressions are traceable to the single change that caused them.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular stages and topologies. The external references that follow are transcribed from the originating prose guide as it cited them; except where an entry is marked as verified during conversion, they were not independently re-verified, and their titles and locations are reproduced rather than checked.

**Corpus pointers**:

- `Modular RAG: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the six-stage taxonomy, the module contract field inventory, the invariant list, the declarative manifest and validation sequence, the topology and fusion vocabulary, the registry and resolution order, the substitution test criteria, the cache classes, the budget allocation procedure, the failure taxonomy and fallback rules, the drift classes, the trace field inventory, the security controls, and the release and rollback procedure. Its inline citations to primary specifications, framework documentation, and benchmarking literature are the basis of the external references listed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — the category overview. Source of the retrieval contract, evidence standard, material claim, admitted text, slice, index manifest, and provenance chain terminology adopted here, and of the selection ladder on which modular composition is one rung.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — the looping topology this guide composes. Source of the run contract, budget ledger, evidence ledger, and declared abstention terminology, and of the stopping rules this guide bounds but does not specify.
- `advanced_task_guides/knowledge-retrieval/guide_CorrectiveRAG.md` — the conditional grading and repair topology, whose verdict vocabulary populates the grading stage's output contract referenced in Section 1.2.
- `advanced_task_guides/knowledge-retrieval/guide_SelfRAG.md` — the generation-stage self-assessment pattern, whose per-segment verdicts this guide requires in a declared output schema.
- `advanced_task_guides/knowledge-retrieval/guide_GraphRAG.md` — one retrieval-stage implementation whose index is a graph, required here to present the same retrieval contract as any other implementation.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — one pre-retrieval stage implementation, whose constraint-preservation check is enforced at the boundary specified in Section 1.4.
- `advanced_task_guides/knowledge-retrieval/guide_HierarchicalIndexRetrieval.md` — a post-retrieval expansion pattern subject to the evidence-budget and token-cap allocations declared in Step 1.1.
- `advanced_task_guides/knowledge-retrieval/guide_MultimodalRAG.md` — a retrieval-stage family whose modality capabilities are registered as the capability metadata described in Step 2.2.
- `advanced_task_guides/knowledge-retrieval/guide_LatentKnowledgeRetrieval.md` — a retrieval-stage family whose route may return no admitted text at all, required here to declare that capability in Step 2.2 and to present the same retrieval contract as a corpus-backed implementation.
- `advanced_task_guides/knowledge-retrieval/guide_DeepResearchAgent.md` — the long-horizon composition whose planner-selected control flow this guide bounds through the approved subgraph catalogue in Step 3.3.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on schema versioning and migration, applicable to the contract evolution rules in Step 5.1.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design and instrumentation, applicable to the span and fingerprint fields in Phases 4 and 5.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring under constraint, applicable to the drift job and operating cadence in Step 6.3.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on control decisions under a value-of-computation rule, applicable to the topology escalation and retirement decisions in Phases 3 and 6.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, IV, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Modular composition and evaluation of retrieval systems*

1. Gao et al., *Modular RAG: Transforming RAG Systems into LEGO-like Reconfigurable Frameworks* — https://arxiv.org/html/2407.21059v1 (author list and the routing, scheduling, and fusion decomposition verified during conversion)
2. Gao et al., *Retrieval-Augmented Generation for Large Language Models: A Survey* — https://arxiv.org/html/2312.10997v5
3. *Dissecting Agentic RAG: A Component Ablation for Multi-Hop QA with a Local 7B Model* — https://arxiv.org/abs/2606.21553 (paired significance testing, bootstrap intervals, and the router result cited in Section V verified during conversion)
4. *Drift-Adapter: A Practical Approach to Near Zero-Downtime Embedding Model Upgrades in Vector Databases* — https://arxiv.org/pdf/2509.23471 (retrieved during conversion in support of the recalibration failure mode)
5. Cao et al., *LEGO-GraphRAG: Modularizing Graph-based Retrieval-Augmented Generation for Design Space Exploration* — https://www.vldb.org/pvldb/vol18/p3269-cao.pdf
6. Li et al., *RAGPerf: An End-to-End Benchmarking Framework for Retrieval-Augmented Generation Systems* — https://arxiv.org/html/2603.10765v1

*Interface, versioning, and configuration specifications*

7. *JSON Schema specification* — https://json-schema.org/specification
8. *OpenAPI Specification 3.2.0* — https://spec.openapis.org/oas/v3.2.0.html
9. *Semantic Versioning 2.0.0* — https://semver.org/

*Cross-boundary protocols*

10. *Model Context Protocol specification, version 2026-07-28* — https://modelcontextprotocol.io/specification/2026-07-28 (confirmed as the current revision during conversion)
11. *Agent2Agent Protocol specification* — https://github.com/a2aproject/A2A/blob/main/docs/specification.md

*Observability, reproducibility, and evaluation tooling*

12. *OpenTelemetry Generative AI semantic conventions* — https://github.com/open-telemetry/semantic-conventions-genai/tree/main/docs/gen-ai (development status as of mid-2026 verified during conversion)
13. *MLflow, ML Experiment Tracking* — https://mlflow.org/docs/latest/ml/tracking/
14. *RAGAS documentation* — https://docs.ragas.io/en/stable/

*Orchestration frameworks and resilience patterns*

15. LangGraph, *Workflows and agents* — https://docs.langchain.com/oss/python/langgraph/workflows-agents
16. LangGraph, *Persistence* — https://docs.langchain.com/oss/python/langgraph/persistence
17. *LlamaIndex developer documentation* — https://developers.llamaindex.ai/python/framework/
18. LlamaIndex, *Workflows* — https://www.llamaindex.ai/workflows
19. Haystack, *Pipelines* — https://docs.haystack.deepset.ai/docs/pipelines
20. Haystack, *Serializing Pipelines* — https://docs.haystack.deepset.ai/docs/serialization
21. Haystack, *Pipeline Loops* — https://docs.haystack.deepset.ai/docs/pipeline-loops
22. DSPy, *How Do I Use an Optimizer?* — https://dspy.ai/learn/optimization/optimizers/
23. DSPy, *Tutorial: Retrieval-Augmented Generation* — https://dspy.ai/tutorials/rag/
24. Martin Fowler, *Circuit Breaker* — https://martinfowler.com/bliki/CircuitBreaker.html

*Security guidance*

25. OWASP, *Retrieval-Augmented Generation Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
