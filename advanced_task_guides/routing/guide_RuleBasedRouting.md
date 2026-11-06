# Rule-Based Routing

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Rule-based routing constitutes the task family of directing a request to a bounded handler using an explicit declarative rule set evaluated over trusted features, rather than by model judgement. This guide provides AI agents with a structured protocol for building, verifying, versioning, and retiring a routing table that behaves as a total function: every admissible input reaches exactly one declared destination, the evaluation order that produces that destination is stated rather than inherited from file layout, and the artifact that produced any past decision is recoverable. It specifies a six-phase framework covering the routing contract and destination inventory, rule authoring under declared evaluation semantics, coverage and default-route policy, static conflict and shadowing analysis, change management through shadow evaluation and rollback, and health measurement terminating in an explicit refactor-or-replace decision. It states the execution tier partition in unusually stark terms: the deterministic tier owns rule storage, evaluation, analysis, coverage measurement, versioning, and shadow replay, while the model tier holds only two legitimate roles, proposing candidate rules from observed misroutes and explaining a decision to a human reviewer. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a rule set stays verifiable as it grows and is replaced deliberately when it stops being so.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Rule-based routing**: A control-plane pattern in which a deterministic, declarative rule set inspects trusted features of a request and selects a bounded destination: a model, an agent, a tool, a queue, a human reviewer, a clarification path, a denial, or an explicit default. The rule set decides what should handle the work; it does not perform the work, and it never acquires authority to widen its own scope.

**Routing table**: The complete ordered or indexed collection of rules that a single evaluation consults, together with its declared hit policy, its default entry, and its schema version. The table is the unit of verification, versioning, release, and rollback.

**Rule**: One record pairing a condition over declared input features with a destination reference and metadata: a stable identifier, a version, a distinct priority, an owner, an intent statement, and an expiry date.

**Destination registry**: The versioned inventory of permitted destinations, held outside the rule files. Each entry carries a stable identifier never reused for a different meaning, an owner, inclusion criteria, explicit exclusions, a risk class, permitted data classes, permitted tools, side effects, latency and cost envelopes, a retry policy, a credential reference naming a secret rather than containing one, enabled environments, and a safe fallback. Rules may reference only registry entries, and this is enforced as a build check rather than a convention.

**Hit policy**: The declared semantics governing how many rules may be satisfied and how their results combine. It is a property of the table, not of any rule, and an unset hit policy is a defect rather than a default.

**Evaluation order**: The total order in which candidate rules are considered. Where the hit policy makes order semantically load-bearing, the order must be derived from an explicit priority field rather than from position in a file.

**Specificity**: The subset relation between two rule conditions over the same input space. A condition whose satisfying set is contained in another condition's satisfying set is the more specific of the two. Specificity ordering places the more specific rule earlier in the evaluation order.

**Total function property**: The property that every input vector admissible under the feature contract triggers at least one rule. A table lacking this property has silent gaps whose behaviour is determined by the engine rather than by the author.

**Default route**: The mandatory reachable catch-all entry that receives any input no other rule matched. It is the least-privileged destination in the registry and its arrival rate is a first-class monitored signal.

**Fall-through**: A decision in which no non-default rule matched, or in which a match was produced but not trusted. Fall-through is a recorded outcome class, never an unlabelled path.

**Overlap**: A non-empty intersection between the satisfying sets of two or more rules. Overlap producing the same destination is redundant; overlap producing different destinations is inconsistent and makes behaviour order-dependent.

**Shadowing**: The condition in which one or more preceding rules match every input a later rule would match while selecting a different destination, so the later rule can never fire. A shadowed rule is a correctness defect regardless of traffic volume.

**Unreachable rule**: A rule whose satisfying set is entirely covered by preceding rules under the evaluation order. Shadowing is the case where the covering rules disagree with it; redundancy is the case where they agree.

**Dead rule**: An enabled and reachable rule with zero recorded hits across an observation window large enough to distinguish rarity from death. A dead rule is a maintenance candidate; an unreachable rule is a defect.

**Canonicalization pipeline**: The single versioned transformation applied identically to request inputs and to rule literals before any comparison: Unicode normalization, case folding, whitespace trimming and collapse, removal of zero-width and default-ignorable code points, and optional confusable-skeleton computation for high-risk comparisons.

**Decision contract**: The structured record the rule layer emits and the dispatcher consumes, carrying rule-set revision and content digest, matched rule identifier and version, hit policy applied and its outcome, selected destination identifier, decision source, a controlled reason code, and flags for default and fallback use.

**Shadow evaluation**: Execution of a candidate routing table against recorded or live traffic without acting on its output, joined to production decisions on an input fingerprint, producing a disagreement rate before the table takes effect.

**Route diff**: The report generated on every proposed table change stating how many recorded requests change destination, which requests they are, and which rule pair caused each change.

**Policy gate**: A deterministic evaluation point in the request path returning exactly one of allow, deny, require-approval, or allow-with-constraints, without model inference. Routing selection and policy authorization are separate gates.

**Default-deny posture**: The behaviour applied when no rule grants a request, when a required feature is missing or ill-typed, when the table is staler than its declared bound, or when the evaluation engine is unreachable. The result is the least-privileged destination in every one of those cases.

### 1.2 The Six Routing Decisions and Their Separation

The word routing conceals at least six distinct decisions, and conflating them is the most common structural defect in production routers. They differ in inputs, in authority, in failure consequence, and in correct owner, so they must stay separate in the rule files, in the decision record, and in evaluation.

**Eligibility and policy routing**: Decides whether the work is permitted at all for this principal, tenant, jurisdiction, data class, and contract. It is an authorization decision and holds veto authority over every later decision.

**Intent routing**: Decides what kind of work is requested. It recognises; it never authorizes.

**Capability routing**: Decides which registered handlers are competent for the recognised work, by matching declared requirements against declared capabilities. It is a separate decision from handler selection below, though one discipline owns both: a capability router filters to the eligible set, ranks it, dispatches, and escalates explicitly where nothing qualifies. Producing a scored candidate set and stopping there is the expertise directory's role, not the router's.

**Handler selection**: Chooses among competent candidates on quality, latency, cost, or privacy grounds.

**Provider or transport routing**: Chooses a healthy deployment of an already-approved handler. It may shift traffic between deployments without understanding intent.

**Priority and tenancy routing**: Decides whose work runs first and under which quota.

The separation carries one invariant that no optimisation may relax: a matched rule is not proof of entitlement, and a destination identifier never functions as a capability. An intent rule must never confer authorization merely because it recognised the request. Enforcement belongs at the point of side effect rather than the point of selection, which means the original principal and tenant are bound into every downstream authorization decision and entitlements are re-checked at the handler rather than inherited from the router's own identity. The failure this prevents is the confused-deputy problem, in which a less-privileged entity coerces a more-privileged one into acting on its behalf; a permissive route is precisely that vulnerability, since a resource policy authorizing the calling service rather than the actor who configured it accepts requests from any actor who merely knows a resource name [1].

Three destination values are routinely collapsed into one and must be recorded as distinct fields: the route requested or implied by the caller, the route selected by the rule layer, and the route actually executed. They diverge under policy overrides, health failover, human review, and fallback, and a decision record that cannot distinguish them cannot support forensics.

### 1.3 Evaluation Semantics: Hit Policy, Specificity, and Tie-Breaking

Every rule in a routing table may be individually deterministic while the table as a whole is non-deterministic in practice. The cause is an undeclared evaluation semantics, and it is the most common defect in real routing tables. Three questions must be answered explicitly in the table's own metadata before any rule is written.

**How many rules may match**: The hit policy answers this. The decision-table standard defines seven policies and mainstream engines implement subsets of them; one widely used engine implements five, and where the attribute is unset the default applied is unique [2]. Relying on that default rather than declaring it is a defect, because a table read by a second engine may not share it.

**How a multiple match resolves**: Under unique, at most one rule may be satisfied and a second satisfied rule violates the policy, which makes overlap a loud configuration error rather than a silent tie-break. Under any, several rules may be satisfied but all must produce identical output, and differing outputs violate the policy. Under first, the first satisfied rule in table order wins, which makes file position semantically load-bearing. Under rule order and collect, all matching rules are returned, ordered by position or in arbitrary order respectively [2]. First-match and best-match are therefore not stylistic alternatives: first-match resolves by position and hides overlap, while a priority-ordered best-match resolves by an explicit ranking that a reviewer can inspect.

**How ties break**: Any policy that can return more than one candidate requires a declared total order. Position in a file is not a total order across merges, generated tables, or multi-file bundles. Equal priorities are not a total order either, and at least one engine documents that rules of equal priority run in parallel with no defined sequence. The required construction is an explicit integer priority column with a uniqueness constraint enforced at build time, followed by rule identifier as the final deterministic tie-break.

**Recommended default**: Use unique for mutually exclusive routes, which is the correct choice for one handler per request, because it converts every authoring overlap into a build failure. Use priority-ordered selection where overlap is intentional and specificity ordering is the design. Use first only for short ordered fallback chains under ten entries, and record the acceptance that it hides overlap. Use collect or rule order only where the consumer is a downstream selector that receives a ranked candidate list.

**Specificity comparison**: Specificity is compared as the subset relation between satisfying sets over the declared feature space, dimension by dimension. A later condition that is a subset of an earlier condition with a different destination is dead code. A later condition that is a superset of an earlier one with the same destination makes the earlier rule redundant. Conditions that cross on some dimensions and not others are correlated, which makes behaviour order-dependent and requires explicit priorities rather than positional luck. These five relations, disjoint, exact match, subset, superset, and correlated, are proved distinct and exhaustive in the firewall-policy literature and transfer to routing without modification [3].

### 1.4 The Determinism Contract and Its Boundary Against Learned Routing

A rule-based router earns its place by being reproducible, not by being clever. The determinism contract is the set of properties that make a past decision replayable, and each has a mechanical enforcement point.

**No wall clock inside rules**: Time conditions read an explicit current-time fact supplied as an input feature. A rule that calls a clock cannot be replayed.

**No input or output inside rules**: A single remote lookup converts a processor-bound decision into an input-bound one and destroys both the latency profile and the replay guarantee [4]. Facts requiring retrieval are materialised into the feature vector before evaluation begins.

**No unseeded randomness**: Experiment and cohort assignment derive from a hash of the request identifier and the experiment identifier, so an assignment is recomputable.

**A total order wherever a specification says arbitrary**: Collect returns outputs in arbitrary order [2], sub-expression evaluation order is unspecified in common expression languages [21], and bundle load order carries no guarantee across bundles [22]. Each of these is a place where the router must impose its own order.

**Version-pinned semantics on every decision**: Engine version, table revision and content digest, canonicalization pipeline version, and Unicode version are stamped on the decision record, because confusable skeletons are not stable across Unicode versions [5] and aggregation semantics have changed between decision-table standard versions [23].

The boundary against learned routing follows from this contract rather than from preference. Rules are the binding authority wherever a decision is determined by trusted state the system already holds: authenticated identity, tenant, entitlement tier, contract terms, region and residency zone, data classification, channel, requested path, explicit user selection, modality, token or context length, maintenance state, quota status, and feature-flag treatment. Inferring any of these from text is a category error, and context-length routing is the clearest case, since an encoder truncating at a fixed window cannot see the portion of the prompt that made the request long.

Rules are also the correct instrument wherever the decision is a policy decision. Authorization, tenancy isolation, residency, legal holds, safety gates, spend limits, and irreversible-action approval belong in deterministic evaluation, because a boundary existing only as prose in a prompt produces no audit signal until after it is crossed. The published guidance is explicit that deterministically expressible constraints belong in hard checks while probabilistic controls are reserved for content-shaped risks that determinism cannot reach [6].

Rules are the wrong instrument in four named situations, and Phase 6 exists to detect them. Where the discriminating signal is semantic and surface forms are open-ended, keyword matching is cheap, deterministic, and trivially evaded. Where the behaviour cannot be expressed in software logic without dependence on external data, a learned component is required by definition [7]. Where no two qualified reviewers apply the inclusion and exclusion criteria the same way, author disagreement becomes contradictory rules and then order-dependent behaviour. And where the observed pattern is one rule added to patch each mistake of an upstream component, the result is a correction cascade whose improvement deadlock makes fixing the upstream component produce system-level harm [7].

***

## II. Operational Framework: A Verified Routing Table With Total Coverage and a Reversible Change Path

Phases 1 through 4 build and verify the table. Phase 5 releases it. Phase 6 measures it in production and terminates in a decision to keep, refactor, or replace it, returning to Phase 2 or exiting the technique entirely. The framework assumes the six routing decisions of Section 1.2 have been separated, and it governs one of them at a time.

### Phase 1: Routing Contract and Destination Inventory

**Objective**: Fix what the rule set chooses, what it may never choose, and the exact set of destinations and input features it may reference, so that later verification has a closed universe to verify against.

#### Step 1.1: Declare the Routing Decision and Its Authority Boundary

**Required Actions**:

- Write one sentence stating exactly what this rule set chooses, and one stating what it may never choose.
- Name which of the six routing decisions in Section 1.2 this table makes, and name the separate owner of every other decision the request passes through.
- Identify the accountable human owner of the table and the policy system holding final authority over eligibility.
- Declare the terminal decision types the table may emit: single route, bounded fan-out, clarification, abstention, denial, and human review.
- Halt the commission where selection authority and authorization authority cannot be assigned to separate owners.

**Required Outputs**:

- A one-paragraph routing charter naming the decision, its exclusions, its owner, and its authorizing system.
- A declared terminal decision-type list.
- A statement of which routing decisions are out of scope and who owns them.

**Quality Checkpoints**:

- The charter names exactly 1 of the 6 routing decisions as in scope.
- No terminal decision type on the list confers authorization as a side effect of selection.
- The authorization owner is a different component from the rule evaluator.

***

#### Step 1.2: Build the Versioned Destination Registry

**Required Actions**:

- Enumerate every candidate destination and record inputs, outputs, owner, tools, data access, side effects, risk class, latency envelope, cost envelope, failure modes, credential reference, and safe fallback for each.
- Assign each destination a stable identifier and a version, and prohibit reuse of a retired identifier for a different meaning.
- Remove duplicate or cosmetic destinations; where two entries differ only by a parameter, keep one and expose the parameter through a validated contract.
- Generate the registry as a reviewed change request rather than by direct edit, paging any capability listing to completion so no destination is silently omitted.
- Enforce as a build check that every destination referenced by a rule exists in the registry at the pinned version.
- Flag every destination whose invocation is irreversible, so the approval gate can bind on it.

**Required Outputs**:

- A versioned destination registry with one entry per destination and no unresolved fields.
- A registry schema digest pinned into the routing table's metadata.
- An irreversible-destination list.

**Quality Checkpoints**:

- Every registry entry carries an owner, a risk class, and a safe fallback; an entry missing any of the three is rejected.
- No credential value appears anywhere in the registry; only credential references appear.
- 100 percent of destinations referenced by draft rules resolve to registry entries.

***

#### Step 1.3: Fix the Feature Contract and the Canonicalization Pipeline

**Required Actions**:

- Enumerate the input features rules may reference, typing each one and marking it as trusted state, derived value, or untrusted text.
- Prohibit rule conditions over any feature not on the list, enforced by schema validation.
- Define one canonicalization pipeline and apply it identically to request inputs and to rule literals at compile time.
- Order the pipeline so canonicalization precedes validation, never the reverse, since validating before canonicalizing prevents detection of data that becomes invalid afterwards and can be used to bypass validation entirely [8].
- Execute the pipeline exactly once per request and record its version on the decision record; never decode the same input twice.
- Set and enforce an input length cap at this boundary, recording whether the input was rejected or deterministically truncated.

**Required Outputs**:

- A typed feature contract listing every referenceable feature and its trust class.
- A versioned canonicalization pipeline specification.
- A declared input length cap with its overflow behaviour.

**Quality Checkpoints**:

- No rule condition references a feature absent from the contract.
- Canonicalization runs before every validation, matching, and authorization step, with 0 exceptions.
- Rule literals and request inputs pass through the identical pipeline version, verified by a build-time comparison.

***

### Phase 2: Rule Authoring Under Declared Evaluation Semantics

**Objective**: Produce a routing table whose evaluation semantics are stated in the artifact rather than inferred from engine defaults or file layout, so that two readers and two engines reach the same destination for the same input.

#### Step 2.1: Select the Smallest Adequate Rule Representation

**Required Actions**:

- Start with a two-layer architecture: an exact-match dispatch table keyed on a discriminator such as intent, tenant, or tool for constant-time bucket selection, plus a short ordered rule list per bucket.
- Escalate to a richer representation only against a stated requirement, recording the requirement and the evidence that would justify revisiting the choice.
- Move rules from code to data as soon as non-engineers must change them, or as soon as they must be versioned and audited independently of the service binary.
- Prefer a compiled, sandboxed expression language or a decision table over host-language predicates wherever rule files are edited by more than one team.
- Verify that the chosen engine implements the hit policy the design depends on, since engines implement different subsets and a design depending on an unimplemented policy is not portable [2].
- Compile every predicate at load or reload, cache the compiled programs, and never parse per request.

**Required Outputs**:

- A representation decision record naming the choice, the requirement it satisfies, and the revisit trigger.
- A per-bucket table inventory with a declared width in input columns and a declared row count.
- A compile-at-load configuration with a measured compile duration.

**Quality Checkpoints**:

- No single table exceeds 5 input columns or 500 rows without a recorded exception, because verification cost rises steeply beyond that (Step 4.1).
- The selected engine implements every hit policy the tables declare; a gap halts the selection.
- Predicate parsing occurs 0 times on the request path.

***

#### Step 2.2: Declare the Hit Policy and Assign a Total Order

**Required Actions**:

- Write the hit policy explicitly into every table's metadata and reject any table relying on an engine default.
- Assign every rule a distinct integer priority, enforced by a uniqueness constraint at build time, and use rule identifier as the final tie-break.
- Order rules by specificity where overlap is intentional, placing subset conditions ahead of their supersets.
- Where a policy can return several results, impose the total order in the router rather than consuming the engine's arbitrary order.
- Record, for each table, the reason its hit policy was chosen and what the choice hides: first hides overlap, unique surfaces it as an error, and collect defers resolution to a downstream consumer.
- Prohibit reliance on file position for semantics in any table under source control that more than one author edits.

**Required Outputs**:

- A per-table hit policy declaration with a stated rationale.
- A priority assignment covering 100 percent of rules, with no duplicates.
- A declared tie-break chain terminating in rule identifier.

**Quality Checkpoints**:

- 0 tables carry an unset hit policy.
- 0 pairs of rules within a table share a priority value.
- The evaluation order is reproducible from the table's own fields without reference to file position.

***

#### Step 2.3: Author Rules Against the Determinism Checklist

**Required Actions**:

- Give every rule a stable identifier, a version, an owner, a one-sentence intent statement, and an expiry date.
- Reject any rule containing a clock read, a remote lookup, or unseeded randomness, enforced by a static check rather than by review.
- Restrict conditions over untrusted text to linear-time or automaton matchers, and where a backtracking engine is unavoidable impose both a per-evaluation timeout and an input length cap, treating neither as sufficient alone.
- Cap counted repetitions in any pattern, and prefer one multi-pattern scan over a loop across many patterns.
- Never accept a pattern, a rule expression, or a rule file from an untrusted author, because the pattern rather than the input is the attack surface.
- Match structured typed features in preference to raw text wherever a typed feature carries the same signal.

**Required Outputs**:

- A rule set in which every rule carries all 5 metadata fields.
- A static determinism check integrated into the build.
- A matcher inventory recording the engine class and the timeout for every text condition.

**Quality Checkpoints**:

- 0 rules read a clock, perform input or output, or draw unseeded randomness.
- Every text condition names a matcher with a documented time bound, or carries both a timeout and a length cap.
- Every rule carries an expiry date, so no rule survives indefinitely without review.

***

### Phase 3: Coverage and Default-Route Policy

**Objective**: Make the routing table a total function over the declared feature space, so that every admissible input reaches a declared destination and any input reaching the default is recorded as a measured event rather than an accident.

#### Step 3.1: Prove the Rule Set Is a Total Function

**Required Actions**:

- Compute the uncovered regions of the input space by gap detection over the declared feature contract, treating rules as axis-aligned regions and merging contiguous uncovered areas where the remaining dimensions coincide [9].
- Report every uncovered region as a named gap with its bounding conditions, not as an aggregate count.
- Close each gap either by adding a rule with a declared owner and intent or by an explicit decision that the region routes to the default.
- Write the catch-all as a structurally reachable row using the representation's all-empty or irrelevant-marker construction, so completeness is a property of the artifact rather than of a comment.
- Re-run gap detection on every table change, never only at authoring time.
- Verify that the feature contract itself is total: every declared feature has a defined behaviour for missing, null, and ill-typed values.

**Required Outputs**:

- A coverage report listing 0 unaccounted gaps or an explicit disposition for each.
- A structurally reachable catch-all row in every table.
- A missing-value and type-error disposition for every declared feature.

**Quality Checkpoints**:

- Gap detection reports 0 regions without a disposition; an undisposed region fails the build.
- The catch-all is proved reachable by the analysis rather than asserted by the author.
- Every feature has a declared behaviour for absent and ill-typed values, so an undefined value cannot silently propagate.

***

#### Step 3.2: Specify the Default Route as the Least-Privileged Path

**Required Actions**:

- Make the default entry mandatory in the configuration schema, so a table without one cannot be published.
- Set the default to the least-privileged destination in the registry, and verify that no fall-through, fallback, or failover path can reach a destination more privileged than the request would otherwise have reached.
- Distinguish two failure meanings and choose separately for each: the router could not decide, and the router decided but could not deliver.
- Fail closed on authorization-relevant and safety-relevant routes; fail open only to a conservative safe default for classification quality, routing an unclassifiable request to a restricted human queue rather than to the most capable or most privileged handler.
- Prohibit router unavailability from degrading into a skipped policy gate.
- Bound every loop the default path can enter: clarification turns, fallback depth, fan-out, attempts, elapsed time, and accumulated cost, and refuse the request where any limit or the safe terminal path is absent.

**Required Outputs**:

- A schema in which the default field is required and validated.
- A privilege ordering over registry entries proving the default is minimal.
- A declared limit for each of the 6 bounded quantities.

**Quality Checkpoints**:

- 0 tables validate without a default entry.
- No path from fall-through reaches a destination whose privilege exceeds the request's own, verified by a reachability check over the registry.
- Every bounded quantity carries a numeric limit; a missing limit refuses the request rather than defaulting to unbounded.

***

#### Step 3.3: Instrument Default-Route Arrival and Its Drift Signal

**Required Actions**:

- Record a fall-through flag, a controlled reason code, and the decision source on every decision, separating no rule matched from matched but not trusted.
- Compute coverage as decisions where at least one non-default rule matched divided by all decisions in the window, and fall-through rate as its complement.
- Record the default-route rate at release as the baseline, and monitor it against that baseline rather than against an absolute target, since the correct level differs by table.
- Alert on a relative rise in default-route rate above 25 percent over a 7-day rolling window, and block further rule additions to that table above a 50 percent relative rise until the cause is diagnosed.
- Sample fall-through decisions continuously into the review queue, since they carry the most information about missing rules.
- Anchor every detected change in default-route rate against the deployment log, so a table change and a change in the world are distinguishable.

**Required Outputs**:

- A per-table default-route baseline recorded at release.
- A fall-through sample stream feeding the review queue.
- An alert definition binding the 25 percent and 50 percent relative thresholds to named actions.

**Quality Checkpoints**:

- 100 percent of decisions carry a fall-through flag and a reason code from the controlled vocabulary.
- The reason code distinguishes no-match from untrusted-match, so the rate is actionable rather than merely observed.
- Every default-route rate change point resolves to either a recorded deployment or an open investigation.

***

### Phase 4: Conflict, Shadowing, and Reachability Analysis

**Objective**: Prove mechanically, on every table change, that no rule is unreachable and that every intentional overlap resolves the way its author intended, so that a growing table stays verifiable rather than merely tested.

#### Step 4.1: Run Completeness and Overlap Detection on Every Table Change

**Required Actions**:

- Model each rule as an axis-aligned region over the typed input space and detect overlaps by a recursive sweep over sorted interval bounds, maintaining active intervals and returning only maximal sets of rules with a non-empty intersection [9].
- Run the analysis in continuous integration on every change to a table, its feature contract, or its registry, and never on the request path.
- Budget the analysis against measured cost: across nine generated tables of roughly 500, 1,000, and 1,500 rules by three, five, and seven columns, averaged over five runs on a single core, overlap detection ran between 200 and 30,736 milliseconds and missing-rule detection between 160 and 18,263 milliseconds, with a 1,496-rule seven-column table costing 30,736 milliseconds for overlaps and 18,263 for gaps [9].
- Split any table whose analysis exceeds the continuous-integration budget, since seven dimensions at 1,500 rules already costs tens of seconds and the cost is superlinear in width.
- Classify each overlap as redundant, where the overlapping rules produce the same destination, or inconsistent, where they produce different ones.
- Fail the build on any inconsistent overlap under a unique hit policy, and warn on redundant overlaps with a merge proposal.

**Required Outputs**:

- An overlap report listing maximal sets only, each classified as redundant or inconsistent.
- A gap report listing merged uncovered regions.
- A per-table analysis duration recorded against the continuous-integration budget.

**Quality Checkpoints**:

- Analysis runs on 100 percent of table changes; a change merged without analysis is a process defect regardless of outcome.
- Analysis duration stays under 30 seconds per table; exceeding it triggers the split in Step 6.3.
- Reports name maximal sets rather than pairwise combinations, because reviewers handed every pairwise overlap read none of them.

***

#### Step 4.2: Detect Shadowed, Redundant, and Unreachable Rules

**Required Actions**:

- Compare each earlier rule with each later rule field by field under the declared evaluation order, classifying the pair into exactly one of disjoint, exact match, subset, superset, or correlated [3].
- Mark a later rule as shadowed where preceding rules match every input it would match while selecting a different destination, and treat it as a correctness defect regardless of traffic volume.
- Mark an earlier rule as redundant where a later superset selects the same destination, and propose a merge.
- Mark crossing conditions with different destinations as correlated, and require explicit priorities rather than accepting positional resolution.
- Distinguish rules never evaluated, which are shadowed and unreachable under the evaluation order, from rules evaluated but never matched, which are dead rather than defective; compute the first from the static analysis and the second from the candidate array in the decision record.
- Set the dead-rule observation window to at least three times the reciprocal of the rule's expected hit rate, so a genuinely rare rule is not declared dead.

**Required Outputs**:

- A pairwise relation classification over every table under its declared order.
- A shadowed-rule list, a redundant-rule list, and a correlated-pair list, each with the causing rule pair named.
- A dead-rule list with the observation window recorded beside each entry.

**Quality Checkpoints**:

- The shadowed-rule count is 0 at release; a shadowed rule blocks the build and is deleted rather than reordered around.
- Every correlated pair carries explicit distinct priorities.
- No rule appears on the dead-rule list whose observation window is shorter than 3 divided by its expected hit rate.

***

#### Step 4.3: Gate the Build on the Analysis Verdict and Publish a Route Diff

**Required Actions**:

- Assemble the full gate: schema validation, semantic lint, gap detection, maximal-set overlap detection, shadowing and reachability analysis, unique-identifier and unique-priority checks, registry reference checks, and rule-coverage measurement against a declared floor.
- Add property-based tests generating inputs and asserting that exactly one rule matches under a unique policy, plus differential tests comparing the evaluator against a reference implementation, since static analysis proves properties of the table while property tests catch defects in the evaluator.
- Publish a route diff on every change request stating how many recorded requests change destination, which requests they are, and which rule pair caused each change.
- Require explicit human acceptance of the route diff before merge; an unexamined diff is not an approval.
- Reject any change whose route diff cannot be computed, since an uncomputable diff means the recorded-traffic corpus does not cover the affected region.
- Record the analysis verdict, the tool versions, and the corpus revision alongside the table revision, so a past verdict is reproducible.

**Required Outputs**:

- A single pass or fail gate verdict with per-check evidence.
- A route diff report attached to every change request.
- A recorded analysis provenance block naming tool versions and corpus revision.

**Quality Checkpoints**:

- All 8 gate checks execute on every change; a skipped check fails the gate rather than warning.
- Rule coverage in the test corpus meets the declared floor of at least 90 percent of enabled rules exercised at least once.
- Every merged change carries a route diff with a recorded human acceptance.

***

### Phase 5: Change Management, Shadow Evaluation, and Rollback

**Objective**: Release a verified table as a signed, versioned, reversible artifact whose behaviour on real traffic was measured before it took effect, so that no change reaches production on authoring confidence alone.

#### Step 5.1: Version, Sign, and Distribute the Rule Set as Data

**Required Actions**:

- Treat the table as a released artifact with the same controls as a binary: a schema, a semantic version, a content digest, a signature, a distribution channel, an activation gate, and a rollback path.
- Version the table independently from the service, bumping major for a semantics or schema change requiring router code changes, minor for added rules or destinations, and patch for a threshold adjustment.
- Publish it as an immutable content-addressed artifact and stamp its version and digest onto every decision record, since the version communicates intent to humans while the digest makes replay exact.
- Activate only after signature verification succeeds; on verification failure continue serving the existing revision and report the activation failure, treating a missing signature as a failure rather than as an absent check.
- Implement hot reload with four properties: build and validate the new table completely then swap a pointer without mutating the live table; fall back to last known good on schema or signature failure; stamp the revision on every decision; and export seconds since the last successful fetch so operators know how long a kill switch takes to land.
- Keep version control as the source of truth and the distribution channel as delivery only, so runtime state cannot diverge from the reviewed artifact.

**Required Outputs**:

- A signed, content-addressed table artifact with a semantic version and digest.
- A hot-reload implementation satisfying all 4 declared properties.
- An exported staleness metric with a declared bound.

**Quality Checkpoints**:

- 100 percent of decision records carry both the table version and its content digest.
- An unsigned or schema-invalid artifact activates 0 times; the previous revision continues serving.
- Staleness stays within the declared bound, and a breach alerts rather than silently extending the kill-switch latency.

***

#### Step 5.2: Shadow-Evaluate the Candidate Table Against Recorded Traffic

**Required Actions**:

- Replay both the incumbent and the candidate table over the same recorded inputs, joined on input fingerprint, with side effects mocked, so input variance is removed and only discordant pairs need adjudication.
- Run the candidate in shadow on live traffic while production alone executes, emitting a disagreement metric labelled by rule identifier.
- Treat shadow disagreement rate as the primary pre-release risk metric, because it requires no labels and is available on full traffic.
- Adjudicate every disagreement class rather than every disagreement instance, grouping by the rule pair responsible.
- Continue the shadow window until it covers the relevant traffic cycles, including at least one full weekly cycle where traffic is weekly-periodic.
- Record explicitly that shadow mode cannot measure downstream outcome quality or load interaction, which is why the canary in Step 5.3 is not optional.

**Required Outputs**:

- A paired replay report over the recorded corpus with discordant pairs enumerated.
- A live shadow disagreement rate by rule identifier over a completed observation window.
- An adjudication record for every disagreement class.

**Quality Checkpoints**:

- Every disagreement class is either explained by an intended change or opened as a defect; 0 classes remain unexplained at promotion.
- The shadow window covers at least 1 full traffic cycle.
- Paired replay joins on input fingerprint, so old and new tables are compared on identical inputs rather than on comparable samples.

***

#### Step 5.3: Canary With a Control and Predeclared Rollback Conditions

**Required Actions**:

- Enable the candidate for a small reversible cohort alongside a concurrent control, using sticky assignment derived from a hashed context key so sessions do not flap mid-conversation.
- Gate on router-specific metrics rather than transport error rates alone: route-distribution drift, fall-through and default-route rate, conflict rate, per-route error rate, per-route tail latency, cost per decision, and downstream failure rate.
- Predeclare automatic rollback for any authorization or safety incident, any unacceptable increase in misroute or final-failure rate, any latency or cost breach, elevated fallback depth, and loss of telemetry.
- Stop immediately and without staged reduction on any security boundary breach.
- Canary the artifact rather than pushing it everywhere at once, since pushing configuration through a strongly consistent store that every server watches accelerates deployment at the cost of synchronized failure [10].
- Expand exposure in bounded stages, recalculating the same metrics with unchanged definitions at each stage, because route mix and dependency load change with exposure.

**Required Outputs**:

- A canary configuration with a concurrent control and sticky assignment.
- A predeclared rollback condition set bound to automated triggers.
- A staged expansion plan with per-stage metric recomputation.

**Quality Checkpoints**:

- Rollback executes in 1 step and is exercised at least once before the first production promotion.
- Every rollback condition is automated; a condition requiring human detection is not a rollback condition.
- No promotion stage proceeds without recomputed metrics under identical definitions.

***

### Phase 6: Health Measurement and the Refactor-or-Replace Decision

**Objective**: Measure whether the table is still doing its job at a maintenance cost the organisation can carry, and terminate in an explicit decision to keep it, refactor it, or replace part of it with a learned router.

#### Step 6.1: Publish Routing Metrics With Explicit Denominators

**Required Actions**:

- Define the populations first: an original request is the user-visible unit entering the router, a decision is one evaluation of the table for one request, an attempt is one call to a destination, and a session may contain several requests.
- Report two denominators separately on every quality figure: the labelled population, meaning the adjudicated gold set or audited sample, and the full-traffic population measured by label-free proxies.
- Publish per-route precision and recall alongside both macro and micro averages, since a regression confined to a route carrying half a percent of traffic is invisible in the micro average and obvious in the macro.
- Publish conflict rate as decisions where more than one rule matched divided by all decisions, watching the change after a deployment rather than the level, because a multi-match is an error under unique and normal under priority.
- Publish rule hit share per rule with concentration measures, so a table collapsing onto a handful of rules is visible.
- Track latency as percentiles from a histogram rather than an average, and alert on the ratio of the 99th percentile to the median as well as on the absolute tail, because a rising ratio signals variance injection while absolute latency is still inside objective.
- Record the window, environment, table revision, router version, traffic slice, and label coverage beside every published figure.

**Required Outputs**:

- A metric catalogue in which every metric names its numerator and its denominator.
- A per-route precision and recall table with macro and micro averages.
- A published label coverage figure beside every quality number.

**Quality Checkpoints**:

- 0 published figures lack a stated denominator.
- Gold-set accuracy is never reported as production accuracy; the two carry different denominators and different names.
- Every quality figure carries the table revision it was measured against.

***

#### Step 6.2: Detect Rule-Set Decay by Size, Concentration, and Change Point

**Required Actions**:

- Track table size, input width, analysis duration, and shadowed-rule count as a decay panel reviewed at a fixed cadence rather than on incident.
- Run one cumulative-sum change-point chart per rule on its hourly or daily hit share against a stable reference window, setting the slack at half the shift to be detected and the decision interval at approximately 4 to 5 standard deviations, because this catches slow erosion that absolute-threshold alerts miss entirely [11].
- Monitor three distributions separately: input features, route mix, and confidence where a confidence value exists.
- Use the population stability index on those distributions, interpreting below 0.1 as little to no shift, 0.1 to 0.25 as a moderate shift warranting close monitoring, and 0.25 or above as a significant shift triggering review [12].
- Read the pairing rather than either signal alone: input drift with a stable route mix means the rules are absorbing the change, while a stable input distribution with a shifting route mix means the table or a dependency changed.
- Review every rule against its last-fired timestamp, hit count, owner, and expiry at a fixed cadence, and anchor every detected change point against the deployment log.

**Required Outputs**:

- A decay panel recording size, width, analysis duration, and shadowed-rule count per review cycle.
- A per-rule change-point chart set with declared slack and decision interval.
- A drift report over all 3 distributions with population stability index values.

**Quality Checkpoints**:

- Every change point resolves to either a recorded deployment or an open investigation; an unexplained change point stays open.
- The drift report distinguishes rules-absorbing-change from table-or-dependency-change on every cycle.
- The decay panel is produced on schedule regardless of incident activity, since decay is gradual and incident-driven review misses it.

***

#### Step 6.3: Execute the Refactor, Migrate, or Replace Decision

**Required Actions**:

- Apply the trigger table below on every review cycle and record the resulting verdict, including a verdict of no action.
- Refactor first: delete shadowed rules immediately as correctness defects, merge redundant overlapping rules, propose zero-hit rules for deprecation as ordinary changes, and split any table too wide or too long to verify inside the analysis budget.
- Where refactoring cannot restore verifiability, migrate the affected route class rather than the whole table, keeping high-consequence classes on rules longest.
- Structure any migration as a facade: freeze the table except for incident changes, instrument every decision with rule identifier, version, and input fingerprint, run the candidate router in shadow, move traffic slice by slice by route class, and delete dead rules along the way [13].
- Retain deterministic policy gates through and after any migration; a learned router changes selection, never authorization.
- Where a simpler baseline now performs as well, delete the complexity rather than preserving it.

**Rule-set decay triggers and their mandated response**:

| Observed condition | Threshold | Mandated response |
| :-- | :-- | :-- |
| **Table analysis duration** | Above 30 seconds per table | Split the table by discriminator before any further rule is added |
| **Table width** | Above 5 input columns | Split by domain; verification cost is superlinear in width |
| **Rule count with flat quality** | Order-of-magnitude growth with per-route accuracy flat across 2 review cycles | Migrate the largest route class to a learned tier |
| **Shadowed-rule count** | Above 0 at any release gate | Delete the shadowed rules; correctness defect, never deferred |
| **Change breadth** | A single change touching more than 10 percent of rules | Refactor the representation; the table is encoding a missing feature |
| **Correction cascade** | More than 3 rules whose stated intent is patching one upstream component | Fix the upstream component; the rules are masking its defect |
| **Threshold expiry** | Any hand-set threshold invalidated by an upstream model update | Learn the threshold on held-out data or remove the dependency [7] |
| **Reviewer disagreement** | Inter-reviewer agreement below the level required by the route's risk class | Merge routes, add trusted context, or keep the decision human |

**Required Outputs**:

- A recorded refactor-or-replace verdict per review cycle with the triggering row named.
- A migration plan by route class where a verdict of migrate is reached.
- A deletion record for every rule removed, naming the justification.

**Quality Checkpoints**:

- Every trigger row that fired produced either the mandated response or a recorded, owned exception with an expiry.
- No migration proceeds without the deterministic policy gates preserved intact.
- The verdict is recorded even where it is no action, so the absence of a decision is distinguishable from a decision to wait.

***

## III. Implementation Guidance for AI Agents

AI agents operating a rule-based router must follow systematic protocols ensuring that every decision is reproducible from a recorded artifact, that no rule change reaches production without mechanical verification, and that the router never acquires the authority it dispatches against. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Registry Agent**: Owns the destination registry and the feature contract. It alone may add a destination, and every addition arrives as a reviewed change request rather than a direct edit. It refuses a destination lacking an owner, a risk class, or a safe fallback.
2. **Authoring Agent**: Drafts rules, priorities, and hit-policy declarations. It operates on one table at a time and may never publish. Its output is a proposed table revision plus the rationale for each rule.
3. **Analysis Agent**: Runs schema validation, semantic lint, gap detection, maximal-set overlap detection, shadowing and reachability analysis, and property-based tests. It returns a single pass or fail verdict with per-check evidence and holds veto authority over publication.
4. **Evaluator**: Executes the compiled table for one request under the declared hit policy within a bounded evaluation budget. It performs no input or output, reads no clock, and draws no unseeded randomness.
5. **Dispatcher**: Validates the selected identifier against the registry at the pinned version, checks eligibility for the current principal, tenant, region, and data class, enforces fan-out, attempt, deadline, and cost budgets, and rejects anything unregistered. It fails closed to the safe route.
6. **Release Agent**: Owns versioning, signing, shadow evaluation, canary, and rollback. It may execute a rollback autonomously and may never execute a promotion autonomously.
7. **Instrumentation Agent**: Writes the append-only decision record, enforces the disclosure boundary, and computes the metric set. It may withhold a metric report where a denominator is missing.

**Disclosure Boundary**: The decision record carries metadata and prohibits raw content. Log rule identifiers, table revision and digest, hit policy and outcome, the candidate array with match results, reason codes, latency breakdown, and consumed budgets. Do not persist raw prompts, secrets, or personal data where a bucketed feature or a keyed fingerprint suffices. Treat a fingerprint as personal data for access control and retention, since a hash is pseudonymisation rather than anonymisation and remains re-attributable with additional information.

**Workflow Execution Pattern**:

```
STATE: Table_Revision_Gate
INPUTS:
  1. Proposed table revision from the Authoring Agent
  2. Destination registry at its pinned version
  3. Recorded-traffic corpus at its pinned revision
ACTIONS:
  1. Validate schema and run semantic lint
  2. Run gap detection over the declared feature contract
  3. Run maximal-set overlap detection and classify each set
  4. Run shadowing and reachability analysis under the declared order
  5. Compute the route diff against the recorded corpus
VALIDATION:
  - hit_policy_declared == TRUE
  - uncovered_regions_without_disposition == 0
  - shadowed_rule_count == 0
  - inconsistent_overlaps_under_unique == 0
  - duplicate_priority_count == 0
  - unresolved_registry_references == 0
  - route_diff_computed == TRUE
TRANSITIONS:
  IF all_validations_pass THEN next_state = Await_Route_Diff_Acceptance
  IF shadowed_rule_count > 0 THEN next_state = Authoring_Repair
  IF route_diff_computed == FALSE THEN next_state = Corpus_Extension
  ELSE next_state = Analysis_Failure_Report
```

**Two-Phase Action Pattern**: Emit the proposed table revision, its analysis verdict, and its route diff without activating it; confirm the verdict against the validation block while no traffic is affected; activate only after signature verification and recorded human acceptance of the diff.

**Approval Gate**: Human authorisation is required before publishing any table revision whose route diff changes the destination of more than 1 percent of recorded requests, before any change to the default entry or to a route in the highest risk class, before adding a destination to the registry, and before promoting past the canary stage for any route flagged irreversible. Agents may execute a rollback without authorisation; they may never execute a promotion without it, and a self-approving agent defeats the gate entirely.

**Context Management Requirements**:

- Hold the registry, the feature contract, and the table revision in durable storage rather than in working context, since analysis outlives a single pass.
- Analyse one table per working pass, since analysis cost is superlinear in width and holding several tables at once produces neither better analysis nor a faster gate.
- Write a handoff record naming the table revision, the analysis verdict, the open defect list, and the pending gate at every context boundary.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Integrity (After Phase 1)**

- **Automated Check**: The charter names exactly 1 routing decision; every registry entry carries an owner, risk class, and safe fallback; every declared feature carries a type and a trust class; no credential value appears in any artifact.
- **Agent Action on Pass**: Proceed to rule authoring.
- **Agent Action on Failure**: Halt and return the specific incomplete entries; no rule is authored against an incomplete registry.
- **Human Review Trigger**: Selection authority and authorization authority cannot be separated, or any destination lacks an accountable owner.

**Checkpoint 2: Semantics Declaration (After Phase 2)**

- **Automated Check**: Every table declares a hit policy; 0 duplicate priorities; every rule carries all 5 metadata fields; the static determinism check returns 0 violations.
- **Agent Action on Pass**: Proceed to coverage analysis.
- **Agent Action on Failure**: Return the undeclared or duplicated entries only, not the whole table.
- **Human Review Trigger**: A table requires a hit policy the selected engine does not implement.

**Checkpoint 3: Coverage Totality (After Phase 3)**

- **Automated Check**: 0 uncovered regions without a disposition; the catch-all is proved reachable; every bounded quantity carries a numeric limit; no fall-through path reaches a more privileged destination.
- **Agent Action on Pass**: Proceed to conflict analysis.
- **Agent Action on Failure**: Halt; a table with a silent gap is not published with a warning attached.
- **Human Review Trigger**: An uncovered region whose correct destination cannot be determined by the registry owner.

**Checkpoint 4: Analysis Verdict (After Phase 4)**

- **Automated Check**: All 8 gate checks executed; shadowed-rule count is 0; inconsistent overlaps under a unique policy are 0; rule coverage in the corpus is at least 90 percent; the route diff is computed and accepted.
- **Agent Action on Pass**: Proceed to release.
- **Agent Action on Failure**: Return the failing check with the causing rule pair named; the Analysis Agent's veto is final.
- **Human Review Trigger**: Analysis duration above 30 seconds, or a route diff changing more than 1 percent of recorded requests.

**Checkpoint 5: Release Safety (After Phase 5)**

- **Automated Check**: The artifact is signed and content-addressed; rollback is exercised and completes in 1 step; 0 shadow disagreement classes remain unexplained; the shadow window covers at least 1 full traffic cycle; every rollback condition is automated.
- **Agent Action on Pass**: Promote to the next exposure stage.
- **Agent Action on Failure**: Hold at the current stage and return the unexplained disagreement classes.
- **Human Review Trigger**: Any authorization or safety incident during canary, or loss of telemetry at any exposure level.

**Checkpoint 6: Operating Health (After Phase 6)**

- **Automated Check**: Every published metric names its denominator; the decay panel is current; every change point resolves to a deployment or an open investigation; every fired trigger row produced its mandated response or an owned exception.
- **Agent Action on Pass**: Record the verdict and continue operating.
- **Agent Action on Failure**: Withhold the metric report and name the missing denominators; no promotion decision is taken on a report with an undeclared population.
- **Human Review Trigger**: A refactor-or-replace verdict of migrate, or a default-route rate rise above 50 percent relative to baseline.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
TABLE_REVISION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Non-Deterministic Table Behaviour**

- **Symptoms**: The same input reaches different destinations across replicas, across engine versions, or after an unrelated file reordering; a merge changes routing without changing any condition.
- **Diagnostic Steps**: Read the table's declared hit policy; check whether the engine default is being relied upon; check for duplicate priorities and for any policy returning an unordered collection; check whether evaluation order derives from file position.
- **Resolution Protocol**: Option A, declare the hit policy explicitly and re-run the analysis gate. Option B, add an explicit integer priority column with a uniqueness constraint and sort in the router rather than consuming the engine's order. Option C, split the table so each bucket carries a unique policy, converting overlap into a build failure.
- **Escalation Trigger**: Any divergence observed across replicas on identical inputs halts the release immediately; this class is never resolved by retry or by pinning a single replica.

**Error Type 2: Rising Default-Route Rate**

- **Symptoms**: Default-route rate rises against its recorded baseline; fall-through decisions concentrate in one tenant, one channel, or one input length band; users report generic handling of specific requests.
- **Diagnostic Steps**: Separate no-match from matched-but-not-trusted using the reason code; compare the input feature distribution against the reference window; check whether an upstream producer changed a feature's format or an enumeration's values; anchor the change point against the deployment log.
- **Resolution Protocol**: Option A, where an upstream feature changed shape, repair the feature contract and the canonicalization pipeline rather than adding rules to absorb the new form. Option B, where a genuine new intent has appeared, author rules for it through the ordinary gate. Option C, where the taxonomy no longer fits, return to Step 1.2 and revise the registry before authoring anything.
- **Escalation Trigger**: A 25 percent relative rise over a 7-day window opens an investigation; a 50 percent relative rise blocks further rule additions to that table until the cause is named.

**Error Type 3: Unreachable Rules After Table Growth**

- **Symptoms**: A newly added rule never fires; analysis reports rules never evaluated; a rule's hit count drops to zero without any change to traffic.
- **Diagnostic Steps**: Run the pairwise relation classification and locate the covering rule set; distinguish never-evaluated, which is a static defect, from evaluated-but-never-matched, which is a dead rule; verify the observation window is at least 3 divided by the expected hit rate before declaring death.
- **Resolution Protocol**: Option A, delete the shadowed rule, since a rule that cannot fire carries intent that is not implemented. Option B, where the shadowed rule expresses the correct behaviour, narrow the covering rule and re-run analysis. Option C, where both are correct for different regions, reorder by specificity and assign explicit priorities.
- **Escalation Trigger**: A shadowed-rule count above 0 blocks the release gate; reordering around a shadowed rule without deleting or narrowing it is prohibited.

**Error Type 4: Selection Treated as Entitlement**

- **Symptoms**: A request reaches a destination it is not entitled to; authorization succeeds because the router's own identity was authorized; a fall-through lands in a more capable handler than the request would otherwise have reached.
- **Diagnostic Steps**: Confirm whether authorization was evaluated at the point of side effect or only at the point of selection; confirm whether the original principal and tenant were bound into the downstream decision; check the privilege ordering of every fall-through and failover target.
- **Resolution Protocol**: Option A, move the authorization check into the handler entry path and make it raise rather than return on failure. Option B, bind the original principal into every downstream call and stop authorizing the router's identity. Option C, re-point the default and every failover target to the least-privileged destination and re-run the reachability check.
- **Escalation Trigger**: Any confirmed instance is a security incident, halts the release, and is never resolved by narrowing the rule that produced it; the defect is the missing enforcement point, not the rule.

**Error Type 5: Evaluation Budget Exhaustion**

- **Symptoms**: Router tail latency rises without a rise in traffic; the 99th-percentile-to-median ratio grows while absolute latency remains inside objective; evaluation timeouts appear on a narrow band of inputs.
- **Diagnostic Steps**: Separate normalization, feature extraction, rule evaluation, and dispatch in the latency breakdown; identify whether a remote lookup entered the evaluation path; inspect text conditions for nested quantifiers or overlapping alternation, whose cost roughly doubles per additional near-matching character [14].
- **Resolution Protocol**: Option A, move any materialised fact out of the rule and into the feature vector before evaluation. Option B, replace the backtracking matcher with a linear-time or automaton matcher for that condition. Option C, impose a per-pattern timeout plus an input length cap and a counted-repetition ceiling, treating none of the three as sufficient alone.
- **Escalation Trigger**: Budget exhaustion stops evaluation, records a rule-error reason code, and proceeds to fall-through handling; partial application of a truncated evaluation is prohibited without exception.

**Error Type 6: Stale or Divergent Table Revision**

- **Symptoms**: Replicas disagree on the active revision; a decision record carries a revision no longer present in the artifact store; a kill switch takes longer to land than the declared staleness bound.
- **Diagnostic Steps**: Read seconds since last successful fetch per replica; verify signature verification outcomes; check whether the live table was mutated in place rather than swapped; check whether a decision cache served an entry produced under a superseded digest.
- **Resolution Protocol**: Option A, pin all replicas to the last known good revision and re-run distribution. Option B, invalidate the decision cache on digest change by including the digest in the cache key, so invalidation is automatic. Option C, reduce the poll interval and re-measure the kill-switch latency against the declared bound.
- **Escalation Trigger**: A decision served under a superseded digest is a correctness defect that presents as a performance win; any occurrence halts promotion and triggers a cache-key review.

**Troubleshooting Decision Tree**:

```
ROUTING DEFECT OBSERVED
├─ DETERMINISM DEFECT
│   ├─ Same input, different destinations → HALT release; declare hit policy, add priorities
│   ├─ Duplicate or absent priority → Reject table; enforce uniqueness at build
│   └─ Order derived from file position → Add explicit priority column; re-run analysis
├─ COVERAGE DEFECT
│   ├─ Uncovered region found → Add rule or dispose to default; never publish with a gap
│   ├─ Default rate up 25 percent → Open investigation; separate no-match from untrusted
│   └─ Default rate up 50 percent → Block rule additions until cause is named
├─ REACHABILITY DEFECT
│   ├─ Rule never evaluated → Static defect; delete or narrow the covering rule
│   ├─ Rule evaluated, never matched → Check window >= 3 / expected rate; then deprecate
│   └─ Inconsistent overlap under unique → Fail build; assign explicit priorities
├─ AUTHORITY DEFECT
│   ├─ Selection granted access → Security incident; enforce at point of side effect
│   └─ Fall-through more privileged → Re-point default to least-privileged; re-check
├─ BUDGET DEFECT
│   ├─ Lookup inside a rule → Materialise the fact into the feature vector
│   └─ Matcher blowup on narrow inputs → Replace matcher; add timeout and length cap
└─ REVISION DEFECT
    ├─ Replicas disagree on revision → Pin to last known good; re-run distribution
    └─ Cached decision under stale digest → Add digest to cache key; halt promotion
```

### D. Execution Tier Partition, Metrics, and Continuous Learning

The execution tier partition is the defining property of this technique and is stated here as a finding rather than as a caveat. The deterministic tier owns essentially all of the work, and the model tier is near-empty by design. That asymmetry is the point of rule-based routing: a router whose selection can be influenced by inference at request time has forfeited exactly the reproducibility, auditability, and replayability the technique exists to provide.

**Tier ownership by artifact and operation**:

| Work item | Owning tier | Authority when tiers disagree |
| :-- | :-- | :-- |
| **Rule storage and schema validation** | Deterministic | Deterministic; an invalid artifact never activates |
| **Predicate evaluation at request time** | Deterministic | Deterministic; the model tier has no request-path role |
| **Hit policy application and tie-breaking** | Deterministic | Deterministic; ties break on priority then identifier |
| **Coverage and gap detection** | Deterministic | Deterministic; an undisposed gap fails the build |
| **Overlap, shadowing, and reachability analysis** | Deterministic | Deterministic; the Analysis Agent holds veto |
| **Destination registry validation and dispatch** | Deterministic | Deterministic; unregistered identifiers are rejected |
| **Authorization at the point of side effect** | Deterministic | Deterministic; never delegated under any condition |
| **Versioning, signing, distribution, rollback** | Deterministic | Deterministic; rollback needs no adjudication |
| **Shadow evaluation and route diff** | Deterministic | Deterministic; replay is exact or it is not replay |
| **Metric computation and drift detection** | Deterministic | Deterministic; denominators are counted, not judged |
| **Proposing candidate rules from misroutes** | Model | Deterministic; every proposal enters as a change request |
| **Explaining a decision to a human reviewer** | Model | Deterministic; the record is authoritative over the narrative |
| **Clustering fall-through inputs for triage** | Hybrid | Deterministic; clusters are review input, never rules |
| **Drafting registry entry prose and intent text** | Hybrid | Human owner; the model drafts, the owner accepts |

**The two legitimate model-tier roles**: A model may inspect recorded misroutes, overrides, and fall-through clusters and propose candidate rules, priorities, and taxonomy changes. Every proposal enters the ordinary change request path and is subject to the full analysis gate, the route diff, and human acceptance; nothing a model proposes is applied on its own authority. A model may also render a recorded decision into an explanation a human reviewer can read, drawing only on fields already present in the decision record. Where the explanation and the record disagree, the record is correct.

**The prohibition**: A model never evaluates a rule at request time, never selects among matched rules, never resolves a tie, and never determines the destination when no rule matched. Where a request genuinely requires open-vocabulary judgement, that judgement belongs to a separate learned tier invoked explicitly by a rule, with its output re-validated against the registry and re-authorized before any side effect, and with the deterministic policy gates retained regardless.

**Coverage and health metrics**:

- **Coverage**: Decisions matched by a non-default rule over all decisions (target: at or above the release baseline; a 25 percent relative fall opens an investigation).
- **Default-route rate**: Decisions sourced from the default over all decisions (target: within 25 percent relative to the release baseline).
- **Conflict rate**: Decisions where more than one rule matched over all decisions (target: 0 under a unique policy; watch the change rather than the level otherwise).
- **Shadowed-rule count**: Rules unreachable under the evaluation order (target: 0 at every release gate).
- **Rule coverage in the corpus**: Enabled rules exercised at least once by the test corpus (target: at least 90 percent).

**Correctness and change metrics**:

- **Per-route precision and recall**: Reported with both macro and micro averages and both denominators (target: per-route recall at or above the risk-class floor for that route).
- **Shadow disagreement rate**: Candidate decisions differing from production over shadowed decisions (target: every disagreement class explained before promotion, not a numeric ceiling).
- **Route diff breadth**: Recorded requests changing destination over the corpus (target: below 1 percent without human authorisation).
- **Rollback latency**: Elapsed time from decision to rollback to the last known good revision serving on all replicas (target: within the declared staleness bound).
- **Analysis duration**: Per-table gate runtime (target: below 30 seconds; a breach mandates a split).

**Calibration and drift**: Where a confidence value gates escalation, bin confidence, compute per-bin empirical accuracy over labelled decisions, and set the escalation threshold at the lowest bin still meeting the route-correctness objective, marking sparse bins inconclusive rather than reliable. Recompute calibration after every table change and treat an increase in calibration error as a release blocker even where accuracy is flat, because miscalibration silently moves the fall-through rate.

**Learning and adaptation mechanisms**:

- **Label the informative strata**: Sample fall-through, multi-match and ambiguous outcomes, decisions near the escalation threshold, decisions where the shadow table disagreed with production, and high-confidence decisions carrying negative feedback. Add a random high-confidence stratum, since uncertainty-only review misses confident systematic errors.
- **Treat human overrides as the backbone**: An override of the route is a direct gold label and the highest-value signal. Record its actor and reason, because overrides concentrated in one reviewer skew the gold set.
- **Keep a structural ground truth**: Maintain a predicted destination field that never changes once filled and an assigned field a human may correct; comparing them yields continuous routing accuracy without a separate labelling programme [15].
- **Version the corpus, not just the table**: Freeze a holdout slice no rule author sees, keep an append-only regression pack of past incidents, and pin the corpus revision into every analysis verdict.
- **Recalibrate thresholds per deployment**: Every numeric bound stated here is a deployment default. Recompute it per route class against observed outcomes rather than inheriting it.

**Human-in-the-loop boundaries**: Adding a destination to the registry, changing the default entry, promoting past a canary for an irreversible route, accepting a route diff, approving an emergency out-of-band rule change, and relaxing the disclosure boundary are never automated. One person authoring and publishing a production rule collapses the segregation that change control depends on.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the structure and verification of a decision table rather than the content of any particular decision. Its phases hold wherever a bounded set of destinations exists, a request carries trusted features, and a wrong destination is observable and correctable.

### 4.1 Cross-Domain Application Patterns

**Customer service and case handling**: The registry enumerates queues, specialist teams, self-service flows, and a human review queue. Eligibility rules run first on entitlement tier and contract terms, and intent rules run second over a taxonomy of ten to fifty case types. The dominant defect is taxonomy drift: agreement between two qualified reviewers falls as the taxonomy grows, and identical annotator accuracy produces a much lower agreement statistic on a two-route taxonomy than on a ten-route one, so a chronically low-agreement route is a guideline defect rather than an annotator defect. The response is to merge routes, add discriminating examples, or add an explicit clarify route, because a router cannot be expected to beat human agreement on a boundary humans cannot apply. Reroute rate within a session is the label-free misroute proxy that drives alerting, while adjudicated misroute rate drives release decisions.

**Clinical and safety-critical triage**: Every destination carries a risk class, and the default is a supervised human queue rather than the most capable automated handler. Fail-closed applies to every route with a safety consequence, and router unavailability may never degrade into a skipped policy gate. Record-keeping is a design requirement rather than telemetry: the decision timestamp and duration, the table revision, the input fingerprint with retained normalized features, and the identity of any person verifying the result form the minimum auditable record, and deployer obligations under high-risk regimes require automatically generated logs be retained for at least six months [16]. Human oversight must be effective rather than nominal, which means a per-decision explanation surface, a working override, and a stop function that halts into a safe state [17].

**Financial transaction screening and dispute handling**: Rules carry the binding authority because the decision is a policy decision and an auditor will ask why a specific transaction was handled a specific way. Separation of duties is not optional: documented approval before implementation, testing evidence, and segregation between who authors and who deploys are the controls an audit looks for. The router and its logs must stay outside the cardholder data environment by segmentation, and no rule may copy an account number into a routing key, a log line, or a configuration default. Terminal outcomes such as automatic denial or closure sit closest to the restrictions on solely automated decisions producing legal or similarly significant effects, so those outcomes belong behind a human-intervention path [18].

**Industrial dispatch and logistics**: Destinations are physical resources with capacity, so the registry carries availability windows and the priority and tenancy decision is genuinely separate from the capability decision. The dominant failure is cascading overload: a routing policy that avoids destinations which have served errors concentrates load on the survivors, health-check flapping reduces the participating set, and forwarding a misrouted request destination to destination adds load through parsing and waiting [10]. The correct behaviour is to return a reroute decision to the orchestrator rather than proxying, and to maintain a visited-destination set so failover never cycles.

**Multi-agent software tooling**: The registry is generated from a capability inventory, paged to completion so no capability is silently omitted, and pinned by schema digest so the dispatcher can refuse a capability whose live schema has drifted. The tool inventory is untrusted input, since a compromised provider can change a capability description to attract routing, so rules match allowlisted identifiers and pinned digests rather than free-text descriptions. Declaring the permitted destination graph in advance constrains a mistaken or manipulated decision to a wrong allowed edge rather than an arbitrary one, and making that graph strongly connected through return-to-triage edges makes a misroute recoverable rather than terminal [19].

### 4.2 Scale, Risk, and Latency Adaptation

- **Small stable tables under 50 rules**: Retain the hit policy declaration, the priority column, the default entry, and the analysis gate, and collapse the release path to gate plus route diff plus one-step rollback. Shadow evaluation may be reduced to paired replay over a recorded corpus where live shadow infrastructure is not justified.
- **Large tables above 500 rules**: Split by discriminator before growing further, since analysis cost is superlinear in width and a seven-column table at 1,500 rules already costs tens of seconds to verify [9]. Keep each bucket narrow enough to verify inside the gate budget; this is a hard constraint rather than an aesthetic preference.
- **High-risk or irreversible destinations**: Bind the approval gate before every promotion, require the default to be a supervised queue, and retain every deterministic policy gate through any migration. Prefer abstention and human review over an unverified automated destination.
- **Strict latency budgets**: Compile predicates once and evaluate many, materialise every fact into the feature vector before evaluation begins, and budget the router at a small fraction of the end-to-end tail target. A router performing a single network lookup per decision has left the sub-millisecond regime regardless of how fast its predicates are [4].
- **Multi-tenant deployments**: Include tenant, permission scope, region, taxonomy version, and table digest in every cache key, so invalidation on a table change is automatic and no decision crosses a tenant or authorization boundary. Enforce per-tenant rate limits so one tenant cannot starve a shared destination pool.
- **Regulated deployments**: Keep the compliance copy of the decision record unsampled and append-only in write-once storage under a separate restricted principal, while the analytics tier stays mutable and cheap. Retain redacted metadata far longer than content-bearing fields, so erasure remains executable against the content tier while the audit tier survives.

***

## V. Limitations and Considerations

**Determinism is not correctness**: A table can be complete, non-overlapping, fully reachable, and consistently ordered while sending every request to the wrong destination. The framework verifies the structure of the decision, not the wisdom of the taxonomy. The mitigation is Phase 6, which measures adjudicated per-route quality against a gold set with a stated denominator, and the reviewer-agreement trigger in Step 6.3, which returns a taxonomy no two reviewers can apply to the registry rather than to the rule authors.

**Most numeric thresholds here are deployment defaults**: The 30-second analysis budget, the 5-column and 500-row table bounds, the 25 and 50 percent default-route rise triggers, the 90 percent rule-coverage floor, the 1 percent route-diff authorisation threshold, and the 3-rule correction-cascade trigger were chosen to be operable on first deployment. They are not measured findings. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute them per route class against observed outcomes. Two figures are exceptions and are measured: the verification runtimes in Step 4.1 and the drift interpretation bands in Step 6.2 are taken from the cited sources.

**Some transcribed figures were not re-verified during conversion**: The sub-millisecond predicate-evaluation latencies, the learned-router cost-reduction and accuracy ranges, the character-injection bypass rates, and the regular-expression blowup figures are carried as the originating prose source cited them. Only the decision-table verification runtimes and the hit-policy semantics were retrieved and confirmed during this conversion, and the source's transcription of one comparative reporting figure was found to disagree with the retrieved paper and was replaced with the retrieved values. The mitigation is that no threshold in the Operational Framework depends on an unverified figure; the unverified numbers appear as context for a judgement, never as an acceptance criterion.

**Static analysis cost grows faster than table size**: Overlap and gap detection over an axis-aligned model is affordable but not free, and cost rises steeply with input width. A table that outgrows the gate budget will tempt an operator to skip the gate, which converts a verified artifact into an unverified one silently. The mitigation is the mandatory split at 30 seconds in Step 6.3 and the checkpoint that treats a skipped check as a gate failure rather than a warning.

**Rule sets accrete faster than they are pruned**: Every incident produces pressure to add a rule and none to remove one, so tables grow monotonically unless pruning is scheduled. Past some size no author can predict what a change does. The mitigation is the expiry date required on every rule in Step 2.3, the scheduled decay panel in Step 6.2, and the trigger table in Step 6.3, which converts observed decay into a mandated response rather than a discussion.

**Keyword matching on adversarial text is a weak signal**: Substring and keyword conditions over free text are cheap and deterministic and are also trivially evaded, with published character-injection results reporting complete bypass of at least one commercial classifier using variation selectors. The mitigation is the architectural rule in Step 3.2 that no fall-through or evasion may land in a more privileged destination than the request would otherwise have reached, combined with the requirement that structured typed features be matched in preference to raw text wherever the typed feature carries the same signal.

**A learned router is sometimes the correct answer and this guide cannot make that choice**: Reported routing accuracy for well-configured learned routers sits materially below an oracle, and one benchmark reports that on the majority of its tasks basic routing systems performed no better than a trivial baseline, with retrieval-augmented tasks the exception where routers significantly outperformed it [20]. Savings from learned routing frequently arise from price asymmetry between destinations rather than from being right often. The mitigation is the trigger table in Step 6.3, which names the conditions under which migration is mandated, and the requirement that any migration proceed by route class behind a facade with the deterministic policy gates retained.

**The compliance surface is jurisdiction-dependent and dated material is a real risk**: Record-keeping, oversight, and automated-decision provisions differ by jurisdiction and their application dates have been subject to amendment. The mitigation is to treat the earliest plausible obligation date as the planning date, to verify against the official text before relying on any schedule, and to design the decision record to the strictest applicable requirement, since a record sufficient to reconstruct and contest a decision satisfies looser regimes automatically.

***

## VI. Conclusion and Summary

Rule-based routing is a verification discipline before it is a dispatch technique. Every rule in a table is individually deterministic, and that fact guarantees nothing: a table without a declared hit policy, without a proved catch-all, and without static reachability analysis is non-deterministic in practice, and the defect surfaces as an unexplainable production behaviour months after the rule that caused it was merged. The value of the technique comes from a small number of properties that can be proved mechanically on every change rather than argued at review: the evaluation semantics are stated in the artifact, every admissible input reaches a declared destination, no rule is unreachable, every intentional overlap resolves by an explicit priority, and any past decision is replayable from a recorded revision and digest.

The execution tier partition is unusually lopsided and that is the point rather than a shortcoming. The deterministic tier owns rule storage, evaluation, hit-policy application, coverage and conflict analysis, registry validation, authorization, versioning, distribution, shadow evaluation, rollback, and metric computation. The model tier holds two roles and no others: proposing candidate rules from observed misroutes and overrides, and rendering a recorded decision into an explanation a reviewer can read. A model that evaluates a rule at request time has removed the reproducibility that justified choosing rules in the first place, and a system needing open-vocabulary judgement at that point needs a different technique, invoked explicitly by a rule, with the deterministic policy gates retained around it.

A team adopting this framework should build the destination registry and the feature contract first, ship the smallest table that covers the highest-volume traffic behind a declared unique hit policy, and instrument coverage, default-route rate, and conflict rate before adding a second rule. Add the analysis gate before the table reaches fifty rules, not after it reaches five hundred, because retrofitting reachability analysis onto an accreted table produces a backlog no one will clear. Then let Phase 6 make the growth decision on evidence: a table that stays verifiable, covers its traffic, and carries a maintainable rule count should keep growing, and one that has stopped being verifiable should be split, pruned, or migrated by route class rather than defended.

**Key Success Factors**:

- **Declared semantics over inherited defaults**: The hit policy, the priority order, and the tie-break chain are written in the artifact, so two readers and two engines reach the same destination for the same input.
- **Coverage as a proved property**: The catch-all is structurally reachable and gap detection reports zero undisposed regions, so no input's destination is decided by the engine rather than by an author.
- **Selection is never entitlement**: Authorization is evaluated at the point of side effect against the original principal, and no fall-through, fallback, or failover reaches a destination more privileged than the request would otherwise have reached.
- **Analysis on every change**: Overlap, shadowing, and reachability run in continuous integration on every table change, report maximal sets rather than pairwise combinations, and hold veto authority over publication.
- **Reversibility before exposure**: Every table is signed, content-addressed, shadow-evaluated against recorded traffic, canaried against a control, and rollable back in one step, with the revision and digest stamped on every decision.
- **Scheduled honesty about growth**: Size, width, analysis duration, and shadowed-rule count are reviewed on a cadence against numeric triggers that mandate a split, a prune, or a migration rather than a discussion.

By following this guide, AI agents can operate a routing table whose behaviour is provable before deployment, measurable after it, and reversible at any point, and can recognise on evidence when the table has grown past the size at which rules remain the right instrument.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them, and were not independently re-verified during conversion except where an entry is explicitly marked verified. Three entries were retrieved and confirmed in the course of this conversion, and one transcription discrepancy found during that check is recorded in Section V.

**Corpus pointers**:

- `Robust Rule-Based Routing: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the six routing decisions, the hit-policy treatment, the completeness and shadowing analysis, the canonicalization ordering rule, the destination registry and decision contract, the determinism checklist, the metric denominators, the change-management classes, and the deactivate-or-redesign criteria. Its survey material on rule-engine products, policy languages, gateway topologies, queue primitives, sandboxes, observability field vocabularies, and jurisdictional compliance regimes was compressed into selection criteria and thresholds rather than retained.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/routing/guide_LLMBasedRouting.md` — the sibling routing method deciding by constrained model judgement over a versioned destination registry and a closed destination vocabulary. It is the learned tier the boundary in Section 1.4 points to and the replacement candidate in the Phase 6 refactor-or-replace decision.
- `advanced_task_guides/routing/guide_EmbeddingBasedRouting.md` — the sibling routing method deciding by calibrated nearest-exemplar similarity under a pinned embedding generation. It is the correct instrument in the first of the four situations named in Section 1.4 where rules are the wrong one, an open-ended semantic signal.
- `advanced_task_guides/routing/guide_CapabilityRouting.md` — the sibling routing method matching extracted requirements against declared handler capabilities. It owns the capability and handler-selection decisions of Section 1.2 through to dispatch and the no-eligible-handler escalation, and runs only over candidates the policy gates specified here have already permitted.
- `advanced_task_guides/routing/guide_ContentBasedRouting.md` — the sibling routing method deciding by bounded inspection of payload contents. The trusted features this guide evaluates are never produced by inspection, and it owns the containment of the manufactured routing key that inspection creates.
- `advanced_task_guides/tool-use/guide_AgentControlPlane.md` — companion guidance on control-plane and data-plane separation, policy gates, default-deny posture, and capability descriptors. Its terminology for those concepts is adopted here rather than restated in new terms.
- `advanced_task_guides/tool-use/guide_ToolRetrieval.md` — companion guidance on assembling and pinning a capability inventory, applicable to generating the destination registry in Step 1.2.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on schema versioning and compatible evolution, applicable to the rule-set schema and decision-contract versions in Phase 5.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on telemetry objectives, semantic conventions, sampling, and data lifecycle, applicable to the decision record and metric catalogue in Step 6.1.
- `advanced_task_guides/reasoning/guide_ProactiveClarification.md` — companion guidance on bounded clarification loops, applicable to the clarification path available on fall-through in Step 3.2.
- `advanced_task_guides/policy-risk/guide_SystemSpecificRiskAssessment.md` — companion guidance on assigning and defending a risk class, applicable to the per-destination risk classes in Step 1.2.
- `advanced_task_guides/context-management/guide_ContextStateMachines.md` — companion guidance on declared state transitions and bounded loops, applicable to the visited-destination set and fallback-depth limits in Step 3.2.

**External references**: The numbering below is the numbering used by the inline markers in Sections I through V. Entries carrying no inline marker support material retained in this restructuring without a separately attributable claim.

*Decision-table semantics, verification, and rule-set analysis*

1. AWS, *The confused deputy problem* — https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html
2. Camunda, *DMN decision table hit policy* — https://docs.camunda.io/docs/components/modeler/dmn/decision-table-hit-policy/ (retrieved and verified during conversion: five implemented policies, unique as the unset default, and the age-nineteen first-match example)
3. Al-Shaer and Hamed, *Firewall Policy Advisor for Anomaly Discovery and Rule Editing* — https://dl.ifip.org/db/conf/im/im2003/Al-ShaerH03.pdf
9. Calvanese, Dumas, Laurson, Maggi, Montali and Teinemaa, *Semantics and Analysis of DMN Decision Tables* — https://arxiv.org/html/1603.07466v1 (retrieved and verified during conversion: authors, hardware, table dimensions, five-run averaging, and both runtime ranges)
23. Flowable, *DMN introduction* — https://www.flowable.com/open-source/docs/dmn/ch06-DMN-Introduction
24. Trisotech, *DMN Hit Policy Explained* — https://www.trisotech.com/dmn-hit-policy-explained/
25. Calvanese and colleagues, *A Tool for the Analysis of DMN Decision Tables* — https://ceur-ws.org/Vol-1789/bpm-demo-2016-paper11.pdf
26. Red Hat, *Guided decision table validation and verification* — https://docs.redhat.com/en/documentation/red_hat_decision_manager/7.0/html/designing_a_decision_service_using_guided_decision_tables/guided-decision-tables-validation-con
27. OMG, *DMN 1.3* — https://www.omg.org/spec/DMN/1.3/PDF

*Determinism, evaluation engines, and artifact distribution*

4. Open Policy Agent, *Policy performance* — https://www.openpolicyagent.org/docs/policy-performance
21. Google, *CEL language definition* — https://github.com/google/cel-spec/blob/master/doc/langdef.md
22. Open Policy Agent, *Bundles* — https://www.openpolicyagent.org/docs/management-bundles
28. Google, *cel-go* — https://github.com/google/cel-go
29. GoRules, *zen* — https://github.com/gorules/zen
30. *json-rules-engine* — https://github.com/CacheControl/json-rules-engine

*Input canonicalization and matcher safety*

5. Unicode, *UTS #39* — https://unicode.org/reports/tr39/
8. MITRE, *CWE-180* — https://cwe.mitre.org/data/definitions/180.html
14. Microsoft, *.NET regular expression best practices* — https://learn.microsoft.com/en-us/dotnet/standard/base-types/best-practices-regex
31. Unicode, *UAX #15* — https://unicode.org/reports/tr15/
32. OWASP, *Regular expression Denial of Service* — https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS
33. *Bypassing Prompt Injection and Jailbreak Detection in LLM Guardrails* — https://arxiv.org/html/2504.11168v1

*Routing authority, safety, and reliability*

6. AWS, *Agentic AI Lens* — https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec04-bp01.md
10. Google, *Addressing cascading failures* — https://sre.google/sre-book/addressing-cascading-failures/
19. Microsoft, *Semantic Kernel handoff orchestration* — https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/handoff
34. OpenAI, *Agents SDK handoffs* — https://openai.github.io/openai-agents-python/handoffs/
35. OWASP, *Top 10 for LLM Applications* — https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf
36. Portkey, *Conditional routing* — https://docs.portkey.ai/docs/product/ai-gateway/conditional-routing
37. NIST, *AI 100-2e2025* — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-2e2025.pdf

*Measurement, drift, and change management*

11. NIST/SEMATECH, *CUSUM control charts* — https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm
12. Arthur, *Population Stability Index* — https://docs.arthur.ai/docs/population-stability-index-psi-metrics
13. Microsoft, *Strangler Fig pattern* — https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig
38. Google, *Implementing SLOs* — https://sre.google/workbook/implementing-slos/
39. Stripe, *Canonical log lines* — https://stripe.com/blog/canonical-log-lines
40. Zinkevich, *Rules of Machine Learning* — https://developers.google.com/machine-learning/guides/rules-of-ml

*Learned routing, technical debt, and the replacement decision*

7. Sculley and colleagues, *Hidden Technical Debt in Machine Learning Systems* — https://papers.neurips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf
15. *IBM automated ticket router* — https://onlinelibrary.wiley.com/doi/full/10.1002/aaai.12079
20. Hu, Bieker, Li, Jiang, Keigwin, Ranganath, Keutzer and Upadhyay, *RouterBench: A Benchmark for Multi-LLM Routing System* — https://arxiv.org/abs/2403.12031 (title, author list and the figure of over 405,000 inference outcomes retrieved and verified during conversion; the comparison against the trivial baseline is carried as the prose source stated it and was not confirmed from the abstract page)
41. *RouteLLM* — https://www.lmsys.org/blog/2024-07-01-routellm/
42. *vLLM Semantic Router* — https://arxiv.org/pdf/2603.04444
43. *Xcon* — https://en.wikipedia.org/wiki/Xcon

*Record-keeping, oversight, and contestability*

16. *AI Act Article 26* — https://artificialintelligenceact.eu/article/26/
17. *AI Act Article 14* — https://artificialintelligenceact.eu/article/14/
18. *GDPR Article 22* — https://gdpr-info.eu/art-22-gdpr/
44. *AI Act Article 12* — https://artificialintelligenceact.eu/article/12/
45. AEPD, *Introduction to the hash function as a personal data pseudonymisation technique* — https://www.aepd.es/guides/introduction-to-hash-function-as-personal-data-pseudonymisation-technique.pdf
