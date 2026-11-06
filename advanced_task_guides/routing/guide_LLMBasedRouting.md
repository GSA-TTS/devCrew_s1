# LLM-Based Routing

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

LLM-based routing constitutes the task family of using a model call to decide where a request goes: which handler, which specialist agent, which tool chain, or which model tier. This guide provides AI agents with a structured protocol for operating that router as a versioned policy component rather than as a prompt. It specifies a destination registry that fixes a closed vocabulary before any prompt is written, a selection gate that compares the model router against a deterministic baseline on a stated cost ratio and refuses the router where the baseline comes within a declared accuracy margin, a constrained-output contract under which an out-of-vocabulary response falls to a declared default rather than being coerced to the nearest valid destination, a calibration and abstention policy binding low-confidence decisions to a default route or a human reviewer, misroute detection at the handler boundary with re-routing bounded to a fixed attempt budget, and accuracy measurement separated from downstream task success so that a weak handler is not misdiagnosed as a routing fault. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that a router repays the latency and cost it adds to every request it touches.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**LLM-based routing**: A control-plane pattern in which a model examines a request and selects which bounded handler, agent, tool, workflow, model tier, human queue, or refusal path should receive it. The router selects; it never performs the downstream work it is selecting among. Semantic dynamic dispatch over unstructured requests is the distinguishing property, in contrast to event routing on predefined attributes [1].

**Destination**: One addressable endpoint of routing, carrying a stable identifier, an owner, inclusion criteria, exclusion criteria, accepted modalities, a risk class, an allowed tool and data scope, a latency objective, a cost envelope, and a declared fallback. A destination that differs from another only in wording is not a destination and is merged.

**Destination registry**: The versioned, deterministic store holding every destination record and the single source of truth for which identifiers exist. The registry is owned by software, never by a prompt, and the prompt is generated from it rather than maintained beside it.

**Closed destination vocabulary**: The finite enumeration of destination identifiers valid at a stated taxonomy version. A router response naming anything outside this enumeration is invalid by construction, not merely unusual.

**Routing decision**: The typed record the router emits, carrying schema version, taxonomy version, decision type, one primary destination identifier, zero or more secondary identifiers, a confidence value with its method identifier, ranked alternatives where the method supplies them, a controlled reason code, and risk flags.

**Decision type**: One member of a closed set governing what the dispatcher does next: single, multi, clarify, abstain, deny, or human review. Clarify, abstain, deny, and human review are destinations with owners and service levels, not error states.

**Dispatcher**: The deterministic component that validates a routing decision against the registry, enforces authorization, selects a handler, applies budgets, and executes. It never executes an identifier, endpoint, function name, model name, or tool name that the router produced but the registry does not contain.

**Deterministic baseline**: The simplest correct non-model router for the same destination set, built from authenticated metadata fields, exact patterns, and policy predicates. Every model router is measured against it, and the baseline wins ties.

**Router overhead**: The added latency, token cost, and monetary cost the routing call imposes on every request, including validation, retries, and failed attempts. Overhead excluded from measurement is overhead that grows without limit.

**Routing accuracy**: The agreement between the selected primary destination and the adjudicated correct destination on a labelled evaluation set, reported per destination rather than as an aggregate alone.

**Misroute**: A dispatched request that reaches a handler unable to complete it, whether because the request falls outside the handler's inclusion criteria, requires tools the handler does not hold, or requires data the handler may not access. A misroute is a routing failure even where the handler produces fluent output.

**Handler rejection**: The typed record a handler returns in place of a result when it detects that it received a misroute, carrying a rejection reason code, the evidence for the rejection, and zero or more suggested destinations that the dispatcher treats as advisory only.

**Re-route budget**: The bounded number of additional dispatch attempts permitted for one request after a handler rejection, enforced deterministically alongside a visited-destination set so a request cannot circulate.

**Routing confidence signal**: The estimator signal the router emits alongside its decision, defined against the observable event of routing correctness. It is a decision signal, not a probability of correctness, until calibrated on held-out data.

**Calibration gap**: The absolute difference between stated probability and observed frequency across declared bins, aggregated by bin weight. It is the measure that certifies or suspends the routing confidence signal for gating use, and it is computed by the procedure specified in the corpus guide on metacognitive monitoring rather than re-derived here.

**Signal certification**: The recorded status permitting the routing confidence signal to gate an action, granted only after calibration on held-out data and revoked automatically when the bundle changes.

**Bundle**: The versioned set of router model, prompt, taxonomy, registry hash, decoding settings, calibrator, and thresholds to which a certification attaches. Certification transfers with the bundle and with nothing else.

**Selective prediction**: The regime in which the router accepts a subset of requests and abstains on the remainder, characterised by coverage, the accepted fraction, and risk, the error among accepted decisions.

**Taxonomy version**: The identifier of the destination set in force for a decision. It is recorded on every routing decision so that a decision made under one vocabulary is never replayed, cached, or scored under another.

**Stale-vocabulary event**: A recorded occurrence in which a router response names an identifier that the registry no longer contains, or in which a registry entry receives zero traffic across a declared window. Both are drift signals with owners.

**Vocabulary drift**: The divergence between the destination set the prompt enumerates and the destination set the registry holds. It is detected by hash comparison at deployment time, not by inspection.

**Routing span**: The telemetry record covering one routing decision and its child operations, carrying identity, version provenance, privacy-safe input descriptors, candidate and decision data, dispatch data, and outcome labels [14].

### 1.2 The Router Economy and the Boundary Against Rule-Based Routing

**The router is itself a model call**: Every request pays the router's latency, tokens, and money before any work is done, and the router can be wrong about where the work belongs. A routing layer is therefore justified only where the expected saving it produces exceeds the cost it imposes on the whole request population, including the requests it would have routed correctly by accident.

**The cost ratio test**: Router overhead must not exceed 10 percent of the median cost of the destinations it selects among, measured in the same currency and including the router's failed attempts, retries, and validation. Above 10 percent the router is a material tax on cheap destinations, and above 25 percent it is rejected outright and the deterministic baseline is deployed instead. The same bound is applied to latency: added routing latency at the 95th percentile must not exceed 10 percent of the median end-to-end latency of the destination set.

**The headroom test**: A model router is justified only where it beats the deterministic baseline by at least 5 percentage points of routing accuracy on the frozen evaluation set, or by a measured reduction in cost per resolved task of at least 15 percent at equal or better accuracy. Where the baseline comes within 3 percentage points of the model router, the baseline is deployed, because it is cheaper, reproducible, and auditable, and the residual accuracy is not worth an inference call on every request.

**The selection criterion against rule-based routing**: Rules own every destination derivable from trusted structured data. Where the correct destination can be determined from an authenticated metadata field, an API path, an explicit user selection, a tenant or region attribute, a modality flag, a subscription tier, or a stable exact pattern, and that determination covers at least 98 percent of the request population, a rule owns the decision and a model must never be asked to infer a fact already held as trusted data. A model router earns the remaining traffic: requests whose destination depends on open-vocabulary meaning, where inclusion criteria are expressible to human annotators but not as a stable predicate, and where the taxonomy changes faster than a rule set can be maintained. The two are not competing sophistication levels; they are two owners of two disjoint parts of one decision, and a production system runs both, with rules first.

**Rules also own every binding constraint**: Authorization, compliance, data residency, tenancy isolation, payment eligibility, and content prohibition are enforced deterministically before and after the model call. A model output is never authorization [11]. A router may supply a risk signal that policy code consumes; policy code alone decides.

**What the router must never absorb**: The router does not perform the downstream task, does not select a provider deployment, and does not choose a tool by name. Provider and deployment selection is a transport-plane concern that gateways serve, and it runs only after the semantic destination and its policy constraints are known [22][23][24]. Conflating the two produces a system in which an availability decision can silently change a capability decision. Selecting the membership of a multi-agent ensemble is likewise a separate decision from selecting one destination for one request, and is treated as a distinct pattern rather than as a multi-destination routing decision [8].

### 1.3 The Execution Tier Partition

Routing divides across three execution tiers, and the division is the guide's principal structural claim. A router whose validation is performed by the same model that produced the decision has no independent check on its own output.

**Deterministic tier**: Software, schema validators, policy engines, and stores own the destination registry, the closed-vocabulary enumeration, structural and enum validation of every router response, confidence thresholding, fallback selection, re-route counting and the visited-destination set, authorization and tenancy enforcement, cost and latency accounting, cache-context construction, and accuracy measurement. These require exactness, reproducibility, and auditability that inference cannot supply: two evaluations of the same frozen decision set must return identical accuracy figures, and a dispatch made two years ago must be reconstructible from the record. The deterministic tier rejects, rather than repairs, any response that is unparsable, schema-invalid, names an identifier absent from the registry, carries a taxonomy version other than the one in force, exceeds the permitted destination count, or omits a required field.

**Model tier**: Inference owns the routing judgement and nothing else: reading a natural-language request against destination inclusion and exclusion criteria and naming the destination whose criteria it satisfies, together with a decision type, a reason code drawn from a controlled list, and a confidence report against the declared event. The model tier proposes; it never dispatches, never authorizes, never selects its own fallback, and never determines whether its own confidence is sufficient.

**Hybrid tier**: The model proposes and software verifies, or software retrieves and the model adjudicates. Authority is fixed in advance and does not depend on the content of the disagreement. Where a deterministic policy check and a model judgement conflict, the policy check holds and the disagreement is recorded. Where a handler rejection contradicts the router's decision, the rejection holds and the request re-enters the bounded re-route path. Where two model routers of different families disagree and no deterministic signal separates them, neither wins: the request routes to the declared default or to human review, and the disagreement is recorded as an unresolved decision.

**An out-of-vocabulary response is never coerced**: Where the router returns an identifier the registry does not contain, the deterministic tier records a schema-failure event and applies the declared fallback chain. It does not compute a string similarity, an embedding distance, or a nearest match against the valid enumeration, because a nearest match converts a detectable failure into an undetectable one and produces a dispatch no evidence supports.

**Tier Ownership of Routing Artifacts**:

| Routing artifact | Owning tier | Deterministic tier rejects | Model tier may never decide alone |
| :-- | :-- | :-- | :-- |
| Destination registry entries | Deterministic | Entries lacking owner, criteria, risk class, or fallback | Any registry content |
| Closed vocabulary enumeration | Deterministic | Identifiers absent from the registry at the stated version | Membership of the enumeration |
| Router response parsing and validation | Deterministic | Unparsable, schema-invalid, or out-of-vocabulary responses | Validity of its own response |
| Destination selection judgement | Model | Selections outside the enumeration | Nothing; this is the model tier's sole authority |
| Decision type assignment | Hybrid | Types outside the closed set | Whether abstention is permitted for the risk tier |
| Confidence report | Hybrid | Unparsed, out-of-range, or unversioned values | Whether the report may gate a dispatch |
| Confidence thresholding | Deterministic | Thresholds selected on the evaluation partition | Any threshold or its comparison outcome |
| Authorization and tenancy checks | Deterministic | Any dispatch lacking a current authorization decision | Any authorization outcome |
| Fallback selection | Deterministic | Fallbacks that widen scope, tool access, or data class | Which fallback applies |
| Re-route counting and loop prevention | Deterministic | Attempts beyond the declared budget | Whether another attempt is warranted |
| Handler rejection adjudication | Hybrid | Rejections lacking a reason code from the closed list | Whether its own output constitutes completion |
| Cost, latency, and token accounting | Deterministic | Figures omitting retries or failed attempts | Any accounting figure |
| Routing accuracy measurement | Deterministic | Measures computed on data used for threshold selection | Any reported accuracy figure |

### 1.4 The Router Selection Gate

The routing call is not free, and a router with no lever is worse than none because it adds cost without changing behaviour. Agents must run a cheap gate, bounded to 2 percent of the direct-execution budget, returning invoke, suppress, or a named lighter substitute.

**Invocation conditions**: Invoke a model router where all of the following hold materially: inputs are natural-language, multimodal, or context-dependent beyond a stable rule set; at least 2 destinations differ genuinely in capability, risk, cost, or service objective; a wrong destination is detectable and recoverable through rejection, a default, or human review; the added latency and cost fall within the cost ratio test; representative labelled or reviewable traffic exists for evaluation; and destination definitions can be separated from execution permissions.

**Suppression conditions**: Suppress the router where a short deterministic rule, an authenticated metadata field, an API path, or an explicit user choice already identifies the destination; where the decision is an authorization, compliance, residency, or payment determination that must bind deterministically; where only 1 meaningful destination exists; where the taxonomy cannot be explained well enough for independent annotators to label examples consistently; where a routing error is catastrophic and no independent guard, confirmation, or recovery path exists; where the latency budget is tighter than one inference plus dispatch; where traffic volume is too small to measure improvement over the baseline; or where the candidate destinations differ only cosmetically and one parameterised handler serves them all.

**Rejection conditions**: Reject the router outright, rather than deferring it, where no adjudicated label source for routing correctness exists at any latency, because the confidence signal can never be certified and the accuracy figure can never be computed. Reject it where handlers cannot signal a misroute, because a misroute would then be indistinguishable from a poor answer.

**Router Selection Gate Decision Table**:

| Observable condition | Available lever | Gate verdict |
| :-- | :-- | :-- |
| Destination derivable from authenticated field for at least 98 percent of traffic | Deterministic predicate | Suppress; deploy the rule |
| Binding authorization, residency, or payment determination | Policy engine | Suppress; policy code decides |
| Baseline within 3 percentage points of the model router | Deterministic baseline | Suppress; deploy the baseline |
| Router overhead above 25 percent of median destination cost | Deterministic baseline | Suppress; the router cannot repay itself |
| Stable, high-volume, well-separated semantic classes | Encoder and exemplars [3] | Suppress; use embedding routing |
| High volume with stable labels and sufficient training data | Supervised classifier | Suppress; use the classifier |
| Nuanced, evolving, low-to-medium-volume taxonomy | Model inference | Invoke the model router |
| Criteria expressible in prose but not as a stable predicate | Model inference | Invoke the model router |
| Cheap handler result scoreable before escalation | Cascade [6] | Invoke as the escalation decision only |
| Misroute undetectable by any handler | None | Reject; instrument handlers first |
| No adjudicated routing label obtainable | None | Reject; certification is impossible |

**Numeric gate rules**: Invoke only where at least 2 destinations carry distinct inclusion criteria and at least 1 detection path for misroutes exists. Where fewer than 2 destinations remain after cosmetic duplicates are merged, suppress and record the merge. Where estimated router overhead exceeds 25 percent of median destination cost, suppress and record the estimate for the next policy revision. Where the gate suppresses, name the substitute rather than dispatching unrouted: a deterministic rule, an embedding router with an uncertainty path, a supervised classifier, or a single parameterised handler.

***

## II. Operational Framework: Constrained Model Routing Under a Versioned Destination Registry

The framework assumes the selection gate has returned invoke. Phases 1 through 3 build the routing artifact, Phase 4 certifies its confidence signal, Phase 5 governs dispatch and recovery at request time, and Phase 6 measures the deployed router and governs change. Phase 6 returns control to Phase 1 whenever the destination set changes.

### Phase 1: Destination Registry and Routing Contract Establishment

**Objective**: Fix the closed destination vocabulary and the routing decision contract in a deterministic registry before any prompt is written, so that the router selects among destinations that exist rather than among descriptions that drift.

#### Step 1.1: Inventory Destinations and Eliminate Cosmetic Duplicates

**Required Actions**:

- State in one sentence what the router chooses and what it never chooses, separating semantic destination selection from provider deployment selection and from tool argument construction.
- Record for every candidate destination its owner, accepted inputs, produced outputs, allowed tools, data scope, latency objective, cost envelope, known failure modes, and declared fallback.
- Merge any pair of candidate destinations that no independent annotator can separate using a rule of 25 words or fewer, replacing them with 1 parameterised destination.
- Reject any candidate destination that shares an owner, tool set, and data scope with another and differs only in prompt wording.
- Record the merge or rejection reason for every candidate removed, so the decision is auditable when the destination is proposed again.

**Required Outputs**:

- A destination inventory carrying all 9 recorded attributes per surviving entry.
- A merge and rejection record naming every removed candidate and its reason.
- A one-sentence routing scope statement naming what the router never decides.

**Quality Checkpoints**:

- Every surviving destination carries an owner and a declared fallback; entries missing either are removed before the registry is published.
- No two surviving destinations share owner, tool set, and data scope simultaneously.
- The scope statement names provider selection, authorization, and tool argument construction among the decisions the router never makes.

***

#### Step 1.2: Publish the Versioned Destination Registry and Closed Vocabulary

**Required Actions**:

- Assign each destination a stable identifier that is never reused for a different meaning, and record its creation date, status, and deprecation date where applicable.
- Write inclusion criteria, exclusion criteria, and decisive evidence for each destination, phrased so that a human annotator can apply them without consulting the owner.
- Declare precedence for every overlapping pair, so that a request satisfying 2 sets of inclusion criteria has exactly 1 correct destination.
- Publish the registry as a deterministic artifact carrying a taxonomy version and a content hash covering every identifier, criterion, and precedence rule.
- Generate the prompt's destination enumeration from the registry at build time, and record the registry hash inside the generated prompt so divergence is detectable by comparison rather than by reading.

**Destination Registry Entry Template**:

```
DESTINATION_ID:
STATUS:                      active | deprecated | retired
OWNER:
TAXONOMY_VERSION_INTRODUCED:
INCLUSION_CRITERIA:
EXCLUSION_CRITERIA:
DECISIVE_EVIDENCE:
PRECEDENCE_OVER:
PRECEDENCE_UNDER:
ACCEPTED_MODALITIES:
REQUIRED_CONTEXT_FIELDS:
RISK_CLASS:                  low | medium | high | irreversible
ALLOWED_TOOLS:
ALLOWED_DATA_CLASSES:
OUTPUT_CONTRACT:
LATENCY_OBJECTIVE_P95_MS:
COST_ENVELOPE_PER_REQUEST:
REJECTION_REASON_CODES:
DECLARED_FALLBACK:
ALIAS_OF:
```

**Required Outputs**:

- A published registry artifact carrying a taxonomy version, a content hash, and one complete entry per destination.
- A precedence matrix resolving every overlapping destination pair to a single winner.
- A generated destination enumeration carrying the registry hash it was built from.

**Quality Checkpoints**:

- Every overlapping pair has a precedence rule; an unresolved overlap blocks publication because it makes labelling non-deterministic.
- The enumeration's embedded registry hash equals the current registry hash; a mismatch blocks deployment as vocabulary drift.
- No identifier appears in the enumeration whose registry status is retired.

***

#### Step 1.3: Declare the Routing Decision Contract and Output Schema

**Required Actions**:

- Define the routing decision schema carrying schema version, taxonomy version, decision type, primary destination, secondary destinations, confidence value, confidence method identifier, ranked alternatives, controlled reason code, missing-information fields, and risk flags.
- Constrain the primary and secondary destination fields to an enumeration drawn from the registry, so that an invalid identifier is a schema violation rather than a semantic error.
- Declare the maximum number of secondary destinations, defaulting to 3, and the prohibited combinations that the dispatcher rejects outright.
- Declare the closed reason-code list and the closed decision-type set, and prohibit free-form explanation fields and any request for hidden reasoning.
- Declare the terminal default destination that receives every request the router cannot place, and confirm it is reachable without the router.

**Routing Decision Record Schema**:

```
SCHEMA_VERSION:
TAXONOMY_VERSION:
REGISTRY_HASH:
DECISION_TYPE:               single | multi | clarify | abstain | deny | human_review
PRIMARY_DESTINATION:         enum(registry identifiers)
SECONDARY_DESTINATIONS:      list of enum, max 3
CONFIDENCE_VALUE:            0.00 to 1.00
CONFIDENCE_METHOD_ID:
RANKED_ALTERNATIVES:         list of (enum, score), max 3
REASON_CODE:                 enum(controlled list)
MISSING_INFORMATION_FIELDS:
CLARIFICATION_QUESTION:      present only when DECISION_TYPE == clarify
RISK_FLAGS:
REQUIRED_APPROVAL_LEVEL:
```

**Required Outputs**:

- A published decision schema with enumerated destination fields and a version identifier.
- A prohibited-combination list the dispatcher enforces before execution.
- A named terminal default destination with an owner and a service objective.

**Quality Checkpoints**:

- The schema admits no free-text field capable of carrying a destination name; a destination is expressible only as an enumeration member.
- The terminal default is reachable when the router is disabled; a default depending on the router is not a default.
- Every decision type in the closed set has a defined dispatcher behaviour, including deny and human review.

***

### Phase 2: Router Selection Against a Deterministic Baseline

**Objective**: Establish by measurement, not by preference, whether a model router is warranted at all, by building the deterministic baseline first and admitting the model router only where it passes the cost ratio test and the headroom test.

#### Step 2.1: Implement and Measure the Deterministic Baseline

**Required Actions**:

- Implement the simplest correct non-model router over the same registry, using authenticated metadata fields, exact patterns, and policy predicates only.
- Implement a majority-destination baseline that sends every request to the most frequent destination, to establish the floor below which no router is useful.
- Measure both baselines on the frozen evaluation set for routing accuracy overall and per destination, added latency at the 50th and 95th percentiles, and cost per request.
- Record which destinations the rule baseline covers at or above 98 percent recall, since those destinations are removed from the model router's decision space rather than contested.
- Record the residual population the rule baseline cannot place, expressed as a percentage of total traffic, since that population is the only traffic a model router can improve.

**Required Outputs**:

- A baseline measurement record carrying accuracy, per-destination recall, latency percentiles, and cost for both baselines.
- A rule-owned destination list naming destinations removed from the model router's decision space.
- A residual traffic figure stating the percentage of requests a model router would be responsible for.

**Quality Checkpoints**:

- Both baselines are implemented and measured before any router prompt is written; a model router measured against no comparator is rejected.
- Every destination whose rule recall reaches 98 percent is removed from the model router's enumeration and recorded as rule-owned.
- The residual traffic figure is at least 5 percent of total traffic; below that threshold the router cannot repay its per-request cost and the gate returns suppress.

***

#### Step 2.2: Apply the Cost Ratio Test and the Headroom Test

**Required Actions**:

- Estimate router overhead per request as the sum of routing tokens, validation, retries, and failed attempts, priced against a versioned price book rather than a delayed invoice.
- Compute the ratio of router overhead to the median cost of the destinations in the residual decision space, and reject the router where the ratio exceeds 25 percent.
- Compute added routing latency at the 95th percentile as a fraction of median end-to-end latency, and reject the router where it exceeds 10 percent unless the destination set's latency objective explicitly admits more.
- Measure candidate model router accuracy on the frozen evaluation set and compare it against the rule baseline, requiring at least 5 percentage points of improvement or at least 15 percent lower cost per resolved task at equal accuracy, since a router's cost and its quality are evaluated jointly rather than separately [4].
- Record every rejected candidate with its measured figures, so a later proposal to reintroduce it is evaluated against evidence rather than against recollection.

**Router Justification Tests**:

| Test | Computation | Pass condition | Action on breach |
| :-- | :-- | :-- | :-- |
| Cost ratio | Router overhead over median destination cost | At or below 10 percent | Above 10 percent, record as a tax and review; above 25 percent, deploy the baseline |
| Latency ratio | Added p95 routing latency over median end-to-end latency | At or below 10 percent | Shorten the prompt, cache exact matches, or deploy the baseline |
| Headroom | Model router accuracy minus rule baseline accuracy | At or above 5 percentage points | Below 3 points, deploy the baseline; between 3 and 5, deploy only on a measured cost reduction |
| Cost per resolved task | Total cost over end-to-end successes | At or below 85 percent of baseline | Deploy the baseline and record the failed candidate |
| Residual coverage | Traffic the rule baseline cannot place | At or above 5 percent | Suppress the router and extend the rule set |
| Floor check | Model router accuracy minus majority-destination accuracy | At or above 15 percentage points | Halt; the taxonomy is not separable and returns to Step 1.2 |

**Required Outputs**:

- A justification record carrying all 6 test computations with measured values and verdicts.
- A versioned price book identifier recorded against every cost figure.
- A rejected-candidate log with measured figures per rejection.

**Quality Checkpoints**:

- Every cost figure includes retries and failed attempts; a figure counting only successful routing calls is rejected as incomplete.
- All 6 tests carry a measured value rather than an estimate at deployment time; an estimated value is admissible only in the gate, never in the justification record.
- No candidate proceeds on aggregate accuracy alone while breaching the cost ratio, latency ratio, or floor check.

***

#### Step 2.3: Commit the Routing Architecture and Its Fallback Chain

**Required Actions**:

- Compose the deployed architecture as an ordered chain: deterministic policy and tenancy gates, exact-cache lookup over a complete cache context, rule or classifier decision for high-confidence common cases, model router for the ambiguous residual, and clarification, abstention, default, or human review where uncertainty or risk remains.
- Place provider or deployment selection last, after the semantic destination and its policy constraints are fixed [22][23][24].
- Declare the fallback chain by failure class rather than as an exception handler, naming the classification, availability, quality, ambiguity, policy, and overload fallbacks and the destination each resolves to, and document upstream and downstream dependencies, third-party risks, and tested fallback technologies alongside it [13].
- Prohibit any fallback that widens tool scope, data class, privilege, or region relative to the destination it replaces, and record the prohibition as a dispatcher rule.
- Declare per-stage timeouts, a total request deadline, a maximum attempt count, and a maximum accumulated cost, and attach a circuit breaker to every dependency that can fail repeatedly [18].

**Fallback Policy by Failure Class**:

| Failure class | Trigger | Resolution | Bound |
| :-- | :-- | :-- | :-- |
| Classification | Transport error or schema-invalid response | Retry once, then secondary router, then terminal default | 1 retry, 1 secondary attempt |
| Out-of-vocabulary | Identifier absent from the registry | Terminal default; never a nearest match | 0 retries on the same bundle |
| Availability | Destination unhealthy or circuit open | Alternate deployment meeting identical capability, privacy, region, and safety requirements | Circuit-breaker window |
| Quality | Handler rejection or verification failure | Bounded re-route under Phase 5 | 1 re-route attempt |
| Ambiguity | Calibrated confidence below the risk-tier threshold | Clarify where 1 question separates the top 2; otherwise abstain to default | 1 clarification per request |
| Policy | Authorization, residency, or data-class breach | Deny or human review; never a downgrade | 0 retries; terminal |
| Overload | Queue depth or dependency saturation | Shed low-priority traffic, queue bounded work, or return a declared degraded path | Total deadline |

**Required Outputs**:

- A committed architecture specification stating the ordered chain and the owner of each stage.
- A fallback policy record covering all 7 failure classes with triggers, resolutions, and bounds.
- A budget specification naming per-stage timeouts, total deadline, maximum attempts, and maximum accumulated cost.

**Quality Checkpoints**:

- No fallback in the record grants more scope, privilege, or data access than the destination it replaces.
- Every failure class resolves to a named destination or a declared terminal state; no class resolves to unbounded retry.
- The terminal default and the kill switch operate with the router disabled, verified by executing both with the router removed.

***

### Phase 3: Router Prompt and Constrained Output Construction

**Objective**: Produce a router prompt that is a classification policy generated from the registry, and a validation path that admits only responses conforming to the closed vocabulary, so that free text can never reach the dispatcher.

#### Step 3.1: Compose the Routing Policy Prompt With Explicit Trust Boundaries

**Required Actions**:

- Open the prompt by stating that the only task is to select among the supplied destination identifiers, and that no downstream work is to be performed.
- Place trusted policy, destination definitions, and precedence rules before clearly delimited untrusted content, and label the untrusted region so that instructions inside it are data.
- Generate destination definitions from the registry, carrying inclusion criteria, exclusion criteria, and decisive evidence verbatim rather than paraphrased.
- Define clarify, abstain, deny, and human review as first-class outcomes with their own selection criteria, so that abstention is a decision rather than an omission.
- Supply boundary examples for every confusing destination pair, plus near-miss, adversarial, multi-intent, and out-of-scope examples, concentrating examples on decision boundaries rather than on easy cases.
- Set decoding to the lowest available sampling temperature, and record that low temperature is a variance control rather than a guarantee of determinism or calibration.

**Required Outputs**:

- A generated router prompt carrying the registry hash, the prompt name, and a prompt version identifier.
- An example set carrying at least 2 boundary examples per confusing destination pair and at least 10 adversarial examples.
- A trust boundary declaration naming which prompt regions are trusted and which are untrusted.

**Quality Checkpoints**:

- Destination definitions in the prompt match the registry byte for byte at the recorded hash; a paraphrase is a defect because it creates a second source of truth.
- The prompt requests no hidden reasoning, no free-form explanation, and no natural-language justification beyond a controlled reason code.
- Untrusted content is delimited and appears after all policy content; policy placed after untrusted content is rejected before deployment.

***

#### Step 3.2: Enforce Structured Output Against the Closed Vocabulary

**Required Actions**:

- Bind generation to the routing decision schema using the provider's structured-output facility where one exists, and record that constrained generation guarantees conformance to a supplied schema while valid syntax alone does not [2].
- Declare the destination fields as enumerations populated from the registry at build time, so the enumeration and the registry cannot diverge without a hash mismatch.
- Cap the response size, prohibit additional properties, and require the schema version, taxonomy version, and registry hash to be echoed in every response.
- Where the provider offers no constrained generation, apply a deterministic parser and validator with identical rejection semantics, and record the absence of native constraint as a risk in the bundle record.
- Record the sampling parameters, the schema version, and the constraint mechanism on every routing span, since a decision cannot be reproduced without them.

**Required Outputs**:

- A constrained-output configuration record naming the mechanism, schema version, and enumeration source.
- A build-time enumeration artifact carrying the registry hash it was generated from.
- A parser and validator specification with declared rejection semantics.

**Quality Checkpoints**:

- The response schema forbids additional properties; a permissive schema admits fabricated fields and is rejected.
- The echoed registry hash equals the deployed registry hash on every response; a mismatch routes the request to the terminal default and raises a vocabulary drift event.
- Sampling parameters and schema version appear on 100 percent of routing spans; spans missing them are unusable for reproduction and count as instrumentation failures.

***

#### Step 3.3: Validate Every Response and Handle Out-of-Vocabulary Returns Deterministically

**Required Actions**:

- Validate every router response in a fixed order: parseability, schema conformance, taxonomy and registry version match, destination membership in the enumeration, destination count within the declared maximum, prohibited-combination check, reason code membership, and confidence value range.
- Reject the response at the first failing check, record the failing check by name, and apply the classification fallback: at most 1 retry for transport or parse failure, then the terminal default.
- Apply the terminal default without modification where the response names an identifier absent from the registry, and record a stale-vocabulary event carrying the returned string, the taxonomy version, and the bundle identity.
- Prohibit string similarity, embedding distance, edit distance, prefix matching, and any other coercion of an invalid identifier to a valid one, and implement the prohibition as an absent code path rather than a disabled option.
- Prohibit the dispatcher from executing any URL, function name, model name, tool name, or endpoint that appears in the router response but not in the registry entry for the selected destination.

**Validation and Rejection Ladder**:

```
ROUTER RESPONSE RECEIVED
├─ Unparsable → record parse_failure → retry once → terminal default
├─ Schema-invalid → record schema_failure → terminal default
├─ Registry hash mismatch → record vocabulary_drift → terminal default → block deploy
├─ Destination not in enumeration → record out_of_vocabulary → terminal default
│      (no similarity match, no nearest neighbour, no prefix repair)
├─ Destination count above maximum → record fanout_violation → truncate to primary only
├─ Prohibited combination → record combination_violation → terminal default
├─ Reason code outside list → record reason_code_violation → accept destination, null the code
├─ Confidence outside 0.00 to 1.00 → record confidence_invalid → treat as uncalibrated
└─ All checks pass → emit validated routing decision → authorization stage
```

**Required Outputs**:

- A validation result record per request naming every check and its outcome.
- A stale-vocabulary event stream carrying returned strings absent from the registry.
- A dispatcher allowlist derived from the registry, independent of the router response.

**Quality Checkpoints**:

- No code path converts an out-of-vocabulary identifier into a valid destination; the absence is verified by inspection of the dispatcher rather than asserted.
- Schema-failure rate stays at or below 1 percent of routing calls; above 2 percent the bundle is rolled back because the constraint mechanism is not holding.
- Out-of-vocabulary rate stays at or below 0.5 percent; above that figure the prompt and registry are re-synchronised before any further deployment.

***

### Phase 4: Confidence Calibration and Abstention Policy

**Objective**: Convert the router's stated confidence into a signal whose numeric value has a measured meaning, and bind low-confidence decisions to a declared default or a human rather than to a guess.

#### Step 4.1: Declare the Routing Confidence Signal and Its Observable Event

**Required Actions**:

- Declare the observable event the confidence signal predicts, stated as adjudicated agreement between the selected primary destination and the correct destination, and name the label source, its latency, and its error rate.
- Record which mechanism produced each candidate signal, drawn from a closed set: the model's stated confidence, the margin between the top 2 ranked alternatives, provider-returned token probabilities where exposed, agreement across repeated samples at fixed decoding, agreement between the model router and the rule or embedding stage, or downstream verification of the handler's result.
- Attach to every signal a target event, a direction, a valid range, a source, a version, and a validity flag, and reject at parse time any value lacking all 6.
- Prohibit a bare confidence number whose method is unrecorded from entering the routing decision record, since a number without a method cannot be calibrated or compared across bundles.
- Record that self-reported model confidence and embedding similarity are decision signals rather than probabilities of correctness, and that neither may gate an action before certification.

**Required Outputs**:

- A signal declaration record per candidate signal carrying all 6 attributes and its production mechanism.
- An observable event definition naming the label source, its latency, and its measured error rate.
- A rejection rule set naming the parse-time conditions that void a signal.

**Quality Checkpoints**:

- Every declared signal names an observable event with an obtainable label; a signal whose event cannot be labelled is removed rather than carried forward.
- Every confidence value in the decision record carries a confidence method identifier; values without one are treated as absent.
- At least 1 declared signal originates outside the router model, so that agreement between the router and itself is not the only available evidence.

***

#### Step 4.2: Calibrate the Signal and Certify It for Gating Use

**Required Actions**:

- Apply the calibration procedure specified in the corpus guide on metacognitive monitoring rather than re-deriving one, adopting its terminology for signal, estimator signal, calibration gap, certification, bundle, and suspension without substitution.
- Freeze a routing calibration dataset drawn from the deployment population and partition it into 3 disjoint parts: a fitting partition for calibrator parameters, a threshold partition for operating point selection, and an evaluation partition read exactly once per release.
- Fit the calibrator on the fitting partition only, and compute the calibration gap, a proper scoring rule, and the risk-coverage curve on the untouched evaluation partition.
- Report the calibration gap per destination and per declared slice, including language, channel, tenant class, and any protected slice with privacy review, since selective acceptance can improve accepted-case accuracy while worsening disparities for particular groups [10].
- Certify the signal for gating only where the calibration gap is at or below 10 percentage points in every reported slice; record provisional status between 10 and 20 points, permitting gating of reversible low-risk destinations only; suspend the signal above 20 points in any slice.
- Revoke certification automatically on any change to the router model, provider snapshot, decoding settings, prompt version, registry hash, taxonomy version, or calibrator, since certification attaches to a bundle and not to a product name.

**Required Outputs**:

- A fitted calibrator carrying its parameters, fitting partition manifest, and version identifier.
- A calibration report carrying the gap per destination and per slice, a proper scoring rule, and a risk-coverage curve with the production operating point marked.
- A certification record naming status, measured gap per slice, bundle identity, effective date, and approving role.

**Quality Checkpoints**:

- The 3 partitions share 0 example identifiers; any overlap voids every measure computed from them.
- No uncertified signal gates a dispatch; an uncertified value may be logged and shown to a reviewer, and may not be compared against an acceptance threshold.
- Each slice reported separately carries at least 200 labelled examples in the evaluation partition; slices below that count are reported as provisional and may not support certification.
- Certification names the exact bundle measured; a certification carried across a model or prompt change is void and its use is a routing defect.

***

#### Step 4.3: Set Risk-Tiered Acceptance Thresholds and the Abstention Policy

**Required Actions**:

- Select acceptance thresholds on the threshold partition and evaluate them on the untouched evaluation partition, never selecting and evaluating on the same examples.
- Set thresholds by expected harm rather than by aggregate accuracy, so that low-risk reversible destinations accept lower calibrated confidence with automatic fallback, and destinations touching sensitive data, write tools, financial action, safety-critical advice, or external communication require both a higher threshold and a deterministic authorization or human approval.
- Declare the default acceptance thresholds as calibrated probability at or above 0.60 for the low risk tier, 0.80 for the medium tier, and 0.90 for the high tier, with the irreversible tier requiring human approval regardless of confidence.
- Route every decision below its tier threshold to a declared outcome rather than to the highest-scoring destination: clarify where 1 bounded question separates the top 2 alternatives, human review where intent is comprehensible but policy or risk requires judgement, abstain to the terminal default where the request falls outside the taxonomy, and deny where policy prohibits service.
- Record the abstention reason from the closed set of uncertainty, ambiguity, missing information, and safety, since these are separate reasons carrying different remedies [9].
- Verify that error among accepted decisions falls as the abstention rate rises, and treat a flat or rising accepted-case error under increasing abstention as evidence that the signal ranks no better than chance.

**Required Outputs**:

- A threshold record per risk tier carrying the selected value, the partition it was selected on, and the evaluated accepted-case error.
- A risk-coverage report stating coverage at the maximum tolerated accepted-case error and accepted-case error at the operational coverage.
- An abstention policy record mapping each below-threshold condition to a named destination and reason code.

**Quality Checkpoints**:

- Thresholds were selected on the threshold partition and evaluated on the untouched partition; a threshold tuned on the evaluation partition voids the release.
- Every below-threshold condition resolves to a named destination; no request below threshold is dispatched to the highest-scoring destination as a fallback.
- Accepted-case error decreases monotonically as coverage decreases across the reported curve; a non-monotonic curve suspends the signal for gating use.
- Clarification is bounded to 1 question per request; a second clarification escalates to human review or the terminal default.

***

### Phase 5: Dispatch, Misroute Detection, and Bounded Re-Routing

**Objective**: Execute the validated decision under independent authorization, detect at the handler boundary that a request arrived at a destination unable to serve it, and recover through a re-route path that terminates.

#### Step 5.1: Dispatch Under Independent Authorization

**Required Actions**:

- Re-authorize at execution time against the authenticated principal, the requested resource, the proposed action, and the current policy, treating the routing decision as a request rather than as a permission [11].
- Resolve the selected destination against the registry entry current at execution time, and take tool scope, data class, latency objective, and cost envelope from that entry rather than from the router response.
- Treat all user, retrieved, tool, and inter-agent content as untrusted data, and prevent untrusted content from selecting the router model, altering the enumeration, disabling a guardrail, raising a budget, or naming a privileged fallback [12].
- Require explicit confirmation before any destination in the irreversible risk class executes, and separate read capability from write capability at the destination level.
- Decompose a multi-destination decision into bounded subrequests, authorize each independently, preserve the shared trace identifier, cap fan-out at the declared maximum, parallelise only read-only or independent work, and serialise every state-changing subrequest.

**Required Outputs**:

- An authorization decision record per dispatch carrying principal, resource, action, policy version, and outcome.
- A resolved destination record naming the registry entry version that supplied the execution scope.
- A subrequest manifest for multi-destination decisions carrying per-subrequest authorization outcomes.

**Quality Checkpoints**:

- Every dispatch carries an authorization decision made after the routing decision; a dispatch authorized only by the router is a policy defect and halts the run.
- Execution scope derives from the registry entry, not from the router response; any field taken from the response is rejected at review.
- Fan-out never exceeds the declared maximum, and state-changing subrequests never execute in parallel.

***

#### Step 5.2: Detect Misroutes at the Handler Boundary

**Required Actions**:

- Require every destination to implement an admission check that evaluates the received request against its own inclusion and exclusion criteria before producing output, and to return a typed handler rejection rather than an answer where the check fails.
- Constrain the rejection reason to a closed list covering out-of-scope input, missing required context field, unsupported modality, tool unavailable, data class not permitted, capability mismatch, and precondition unmet.
- Require the rejection to carry evidence naming the failing criterion or the missing field, and to treat any suggested destinations as advisory input to the dispatcher rather than as a new routing decision.
- Instrument passive misroute signals alongside the active rejection path, since a handler that cannot recognise a misroute will produce fluent output instead: user rephrase, user correction, handler output failing its declared output contract, downstream verification failure, and human escalation from within the destination.
- Record route correctness and end-to-end success as 2 separate fields on every routing span, so that a weak handler is never diagnosed as a routing fault and a misroute is never excused by a plausible answer.

**Misroute Detection Signals**:

| Signal | Detection point | Latency | Deterministic or model | Action |
| :-- | :-- | :-- | :-- | :-- |
| Handler admission rejection | Destination entry, before output | Immediate | Deterministic | Bounded re-route under Step 5.3 |
| Output contract violation | Destination exit | Immediate | Deterministic | Bounded re-route or terminal default |
| Required context field absent | Dispatcher, pre-execution | Immediate | Deterministic | Clarify, or terminal default |
| Tool or data authorization denial | Authorization stage | Immediate | Deterministic | Deny; never re-route to a wider scope |
| Downstream verification failure | Post-execution check | Seconds | Hybrid | Bounded re-route; escalate on repeat |
| User rephrase or correction | Next turn | Minutes | Deterministic | Label for adjudication; no automatic re-route |
| Human escalation from the destination | Within the handler | Minutes to hours | Human | Adjudicate and label |
| Adjudicated label disagreement | Review queue | Hours to days | Human | Feed the evaluation corpus and drift monitor |

**Required Outputs**:

- A handler rejection contract published for every destination, naming its admission check and its permitted reason codes.
- A misroute event stream carrying detection point, reason code, evidence, and the originating routing decision identifier.
- Paired route-correctness and end-to-end-success fields on 100 percent of routing spans.

**Quality Checkpoints**:

- Every destination implements an admission check and can return a rejection; a destination that cannot reject is not admitted to the registry.
- Every rejection carries a reason code from the closed list and evidence naming the failing criterion; rejections without evidence are treated as handler faults rather than routing faults.
- Route correctness and end-to-end success are recorded separately; a span carrying only end-to-end success cannot support routing measurement and counts as an instrumentation failure.

***

#### Step 5.3: Execute Bounded Re-Routing or Terminal Fallback

**Required Actions**:

- Permit at most 1 re-route attempt per request after a handler rejection, giving a maximum of 2 dispatches in total, and decrement a route-attempt budget carried on the request rather than held in the router.
- Maintain a visited-destination set on the request and prohibit dispatch to any destination already visited, so a request cannot alternate between 2 handlers.
- Recompute the routing decision for a re-route using the rejection evidence as additional context, and exclude the rejecting destination from the enumeration presented for that attempt.
- Treat the suggested destinations in a handler rejection as advisory: they may re-rank candidates and may never introduce an identifier absent from the registry or bypass the confidence threshold for the destination's risk tier.
- Send the request to the terminal default, human review, or a declared degraded path when the re-route budget is exhausted, when the visited set covers every eligible destination, or when the second decision falls below its tier threshold, and never issue a third dispatch on the strength of remaining budget.
- Prohibit re-routing entirely across a policy denial, an authorization failure, or a residency constraint, since those are terminal and re-routing them would search for a permissive handler.

**Re-Route Control Block**:

```
STATE: Handler_Rejection_Received
INPUTS:
  1. Routing decision record with taxonomy version and registry hash
  2. Handler rejection with reason code and evidence
  3. Route-attempt budget and visited-destination set
ACTIONS:
  1. Append rejecting destination to visited set
  2. Decrement route-attempt budget by 1
  3. Recompute decision over enumeration minus visited set
  4. Apply risk-tier confidence threshold to the new decision
VALIDATION:
  - route_attempt_budget >= 0
  - selected_destination NOT IN visited_set
  - rejection_reason_code IN closed_list
  - policy_denial == FALSE
  - calibrated_confidence >= tier_threshold
TRANSITIONS:
  IF all_validations_pass THEN next_state = Authorize_And_Dispatch
  IF route_attempt_budget == 0 THEN next_state = Terminal_Default
  IF policy_denial == TRUE THEN next_state = Deny_And_Record
  IF calibrated_confidence < tier_threshold THEN next_state = Human_Review
  IF validation_failed THEN next_state = Terminal_Default
```

**Required Outputs**:

- A re-route record per attempt carrying the visited set, remaining budget, rejection evidence, and the recomputed decision.
- A terminal outcome record naming which of the 4 terminal states closed the request.
- An accumulated cost figure covering every dispatch, including the rejected one.

**Quality Checkpoints**:

- Total dispatches per request never exceed 2; a third dispatch is a loop-prevention failure and halts the request at the terminal default.
- No destination appears twice in one request's dispatch history.
- Accumulated cost and latency include rejected attempts; figures counting only the successful dispatch understate the router's true overhead and are rejected at review.
- Policy denials, authorization failures, and residency constraints produce 0 re-route attempts.

***

### Phase 6: Accuracy Measurement, Drift Detection, and Vocabulary Change

**Objective**: Measure the deployed router against its baseline on routing quality, efficiency, and end-to-end utility, detect vocabulary and distribution drift, and change the destination set through a versioned procedure that leaves no stale identifier in the prompt.

#### Step 6.1: Measure Routing Accuracy Separately From Downstream Success

**Required Actions**:

- Compute routing accuracy overall and per destination, with precision and recall in both macro and support-weighted forms, and inspect the confusion pairs rather than the average alone.
- Score hierarchical destinations at both the parent and the leaf, score multi-destination decisions by exact set match and by partial set overlap, and score ranked candidates by recall within the top ranked positions.
- Compute abstention coverage, accepted-case error, clarification rate, human-review rate, terminal-default rate, and unnecessary-escalation rate, and report a risk-coverage curve rather than an aggregate accuracy figure alone.
- Compute routing latency and total latency at the 50th, 95th, and 99th percentiles, together with queue delay, retry count, timeout count, schema-failure rate, cache-hit rate, fallback depth, and re-route rate.
- Compute router cost, downstream cost, re-route cost, and total cost per resolved task against a versioned price book, and reconcile estimated cost against billed cost when the invoice arrives.
- Measure end-to-end task success, policy compliance, user correction and rephrase rate, time to resolution, and quality per destination, and never treat a correct route as a resolved task.
- Build the evaluation corpus from a representative stratified sample, a temporal holdout drawn from a later period, boundary examples for every confusing pair, ambiguous and multi-intent inputs, multilingual and long-context inputs, out-of-distribution inputs with no valid destination, rare high-impact safety cases, adversarial injection cases, and dependency-failure cases.

**Required Outputs**:

- A routing quality report carrying per-destination precision and recall, the confusion matrix, and the risk-coverage curve.
- An efficiency report carrying latency percentiles, failure counts, and cost per resolved task with the price book version recorded.
- An end-to-end utility report pairing route correctness with downstream success per destination.

**Quality Checkpoints**:

- Per-destination figures accompany every aggregate; an aggregate reported alone is rejected because a router can improve on average while collapsing on a rare high-risk destination.
- No candidate is promoted that improves average routing accuracy while breaching a per-destination, safety, latency, cost, or slice gate.
- Benchmark figures published elsewhere are never copied into production thresholds, since model pools, prompts, workloads, and prices differ [5][25].
- Each destination reported separately carries at least 200 adjudicated examples; destinations below that count are reported as provisional.

***

#### Step 6.2: Detect Routing Drift and Stale Vocabulary

**Required Actions**:

- Monitor destination frequency shifts, abstention and clarification shifts, confidence and margin distributions, per-destination precision, recall, downstream success and cost over time, confusion pairs, repeated cross-destination transfers, and performance by language, channel, and tenant class.
- Compare the deployed prompt's embedded registry hash against the current registry hash on every deployment and at a fixed interval no longer than 24 hours, and treat any mismatch as vocabulary drift that blocks further deployment.
- Count stale-vocabulary events, defined as router responses naming an identifier the registry no longer contains, and treat any non-zero count on a bundle whose hashes match as evidence that the prompt enumerates a destination the registry has retired.
- Count zero-traffic destinations, defined as registry entries receiving no primary selection across a window of 30 days, and open a deprecation review for each rather than leaving an unused identifier in the enumeration.
- Confirm every suspected drift with delayed labels, review samples, downstream outcomes, or counterfactual tests before acting, since detecting that a distribution changed is a different problem from locating and explaining the change [20].
- Sample both low-confidence cases and randomly selected high-confidence cases for adjudication, because uncertainty-only sampling misses confident systematic errors.

**Required Outputs**:

- A drift monitor record carrying all 8 monitored quantities with their windows and alert thresholds.
- A stale-vocabulary and zero-traffic report naming every affected identifier and its owner.
- An adjudication queue carrying a declared mix of uncertain and randomly sampled confident cases.

**Quality Checkpoints**:

- Stale-vocabulary events number 0 on any bundle whose prompt and registry hashes match; a non-zero count halts deployment and returns to Step 1.2.
- The registry hash comparison runs at least once every 24 hours; a comparison older than that voids the deployment gate.
- No drift alert triggers a change before confirmation by labels, review samples, downstream outcomes, or counterfactual tests; input-distribution movement alone is not failure.
- The adjudication queue draws at least 20 percent of its volume from randomly sampled accepted high-confidence decisions.

***

#### Step 6.3: Execute Versioned Vocabulary Change and Staged Rollout

**Required Actions**:

- Change the destination set only through a versioned proposal naming the operation as add, merge, split, deprecate, retire, or alias, its owner, its migration plan for exemplars and labels, and its rollback point.
- Increment the taxonomy version on every change, publish compatibility rules mapping old identifiers to new ones, and retain the previous version until the observation window closes.
- Regenerate the prompt enumeration from the registry as part of the change rather than editing the prompt, and block release where the regenerated hash does not match the registry.
- Re-run calibration and threshold selection after any change to the destination set, since a certification attaches to a bundle and the taxonomy version is part of that bundle.
- Release routing changes independently from handler changes, through the ordered stages: continuous-integration validation of schema, enumeration, and precedence; artifact freeze covering prompt, model, taxonomy, thresholds, exemplars, price book, and code; offline and adversarial gates; replay of historical traffic with side effects disabled; shadow comparison against production; canary on an eligible low-risk cohort with a concurrent control [19]; and gated expansion under feature flags emitting evaluation telemetry [17].
- Roll back automatically on a safety incident, an authorization error, a wrong-destination rate above the declared gate, an end-to-end regression, a latency breach, or a cost breach, and maintain a kill switch and terminal default that do not depend on the failing router.

**Required Outputs**:

- A taxonomy change record per operation carrying owner, migration plan, compatibility rules, and rollback point.
- A regenerated prompt artifact whose embedded registry hash matches the published registry.
- A rollout record naming each stage, its gate, its measured values, and its verdict.

**Quality Checkpoints**:

- No identifier is reused for a different meaning; reuse voids historical comparability and blocks the change.
- Calibration and thresholds are recomputed after every destination set change; carrying a prior certification across a taxonomy version is a routing defect.
- Write operations are never replayed against live systems; replay executes against mocks, sandboxes, or recorded results.
- Expansion proceeds cohort by cohort, and no cohort is skipped between a successful small canary and full traffic.

***

## III. Implementation Guidance for AI Agents

AI agents operating an LLM-based router must follow systematic protocols ensuring that every dispatch is validated against a registry the router does not own, that confidence gates only after certification, and that recovery from a misroute terminates. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Registry Agent**: Owns the destination registry, the closed vocabulary, precedence rules, and the taxonomy version. It alone may add, deprecate, or retire an identifier, and every change is versioned and hashed.
2. **Selection Agent**: Runs the router selection gate, implements and measures the deterministic baseline, and applies the cost ratio and headroom tests. It may refuse the model router and deploy the baseline instead.
3. **Router Agent**: Emits one routing decision per request under the constrained output schema. It holds the model tier's sole authority and may not dispatch, authorize, select a fallback, or judge its own confidence sufficient.
4. **Dispatcher**: Validates every response against the registry, enforces authorization and tenancy, resolves execution scope from the registry entry, applies budgets, and executes. It rejects rather than repairs, and never executes an identifier the registry does not contain.
5. **Calibration Agent**: Owns the calibration dataset partitions, fits the calibrator, computes the calibration gap per slice, and issues or revokes certification against a named bundle.
6. **Recovery Agent**: Consumes handler rejections, maintains the visited-destination set and the route-attempt budget, and closes the request at a terminal state when the budget is exhausted.
7. **Measurement Agent**: Writes the routing span, computes routing quality, efficiency, and end-to-end utility figures, and runs the drift and stale-vocabulary monitors. It may veto promotion where a gate is unmet.

**Authority Boundary**: A component that produces a value never also decides whether that value is admissible. The Router Agent produces the destination and the confidence; the Dispatcher decides admissibility and the Calibration Agent decides whether the confidence may gate. Where one model performs several roles, each output is still emitted as a separate typed record before the next role reads it, and the operations are logged as distinct events.

**Telemetry Disclosure Boundary**: The routing span carries decision metadata and never hidden reasoning content.

- Record identity and correlation identifiers, version and configuration provenance, privacy-safe input descriptors, candidate and decision data, dispatch and execution data, tool and policy outcomes, and outcome labels [14][15].
- Do not request or persist hidden reasoning from the router; a controlled reason code and the ranked alternatives carry the auditable content.
- Do not place raw prompts, tool arguments, tool results, secrets, or personal data into unrestricted telemetry, since messages, retrieval queries, system instructions, tool arguments, and tool results may carry sensitive information [14].
- Redact or tokenize before export, keep high-cardinality content out of metric labels, and hold protected detail in access-controlled traces.

**Workflow Execution Pattern**:

```
STATE: Routing_Decision_Validation
INPUTS:
  1. Router response with schema version, taxonomy version, registry hash
  2. Current registry enumeration and precedence matrix
  3. Certification record for the active confidence signal
  4. Risk-tier threshold table
ACTIONS:
  1. Parse and schema-validate the response
  2. Compare echoed registry hash against deployed registry hash
  3. Test primary and secondary identifiers for enumeration membership
  4. Apply calibrator and compare against the destination's tier threshold
  5. Resolve execution scope from the registry entry, not from the response
VALIDATION:
  - schema_valid == TRUE
  - registry_hash_match == TRUE
  - destination IN enumeration
  - secondary_destination_count <= 3
  - signal_certification_status IN {certified, provisional}
  - calibrated_confidence >= tier_threshold
  - authorization_decision == PERMIT
TRANSITIONS:
  IF all_validations_pass THEN next_state = Authorize_And_Dispatch
  IF destination NOT IN enumeration THEN next_state = Terminal_Default
  IF registry_hash_match == FALSE THEN next_state = Block_Deployment
  IF calibrated_confidence < tier_threshold THEN next_state = Abstain_Or_Clarify
  IF signal_certification_status == suspended THEN next_state = Human_Review
  IF authorization_decision == DENY THEN next_state = Deny_And_Record
```

**Two-Phase Action Pattern**: Emit the routing decision with its confidence, alternatives, and reason code without dispatching; validate it against the registry, the certification record, and the threshold table while no resource is committed; dispatch only after validation passes, recording the routing span in the same operation.

**Approval Gate**: Human authorisation is required before dispatch to any destination in the irreversible risk class, before any dispatch whose calibrated confidence falls below its tier threshold and whose risk class is high, before promotion of a bundle whose calibration gap exceeds 10 percentage points in any reported slice, and before any taxonomy change that retires an identifier carrying more than 1 percent of traffic. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the registry, thresholds, certification records, and price book in durable state read at decision time, never inlined into a prompt that outlives a version.
- Carry the route-attempt budget, the visited-destination set, and the accumulated cost on the request, so recovery state survives a component boundary.
- Give the router only destination identifiers, generated criteria, and sanitized request content; never credentials, never the tool permission table, and never the authorization policy.
- Count the router's own token consumption toward overhead rather than treating it as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Registry Integrity (After Phase 1)**

- **Automated Check**: Every destination carries all 9 attributes; every overlapping pair carries a precedence rule; the enumeration hash matches the registry hash; the terminal default is reachable with the router disabled.
- **Agent Action on Pass**: Proceed to baseline measurement.
- **Agent Action on Failure**: Halt and return the specific registry defect; no prompt is written against an incomplete registry.
- **Human Review Trigger**: An overlapping pair that no precedence rule can resolve, or a destination whose criteria 2 independent annotators apply inconsistently.

**Checkpoint 2: Router Justification (After Phase 2)**

- **Automated Check**: All 6 justification tests carry measured values; cost ratio at or below 25 percent; headroom at or above 5 percentage points or a measured cost reduction at equal accuracy; residual coverage at or above 5 percent.
- **Agent Action on Pass**: Proceed to prompt construction.
- **Agent Action on Failure**: Deploy the deterministic baseline and record the failed candidate with its figures.
- **Human Review Trigger**: Headroom between 3 and 5 percentage points, where the decision turns on a cost estimate rather than a measurement.

**Checkpoint 3: Output Constraint Integrity (After Phase 3)**

- **Automated Check**: Schema forbids additional properties; destination fields are enumerations generated from the registry; schema-failure rate at or below 1 percent; out-of-vocabulary rate at or below 0.5 percent; no similarity-matching code path exists in the dispatcher.
- **Agent Action on Pass**: Proceed to calibration.
- **Agent Action on Failure**: Halt; an unconstrained router is never deployed behind a validator alone.
- **Human Review Trigger**: Schema-failure rate above 2 percent, or any observed coercion of an invalid identifier to a valid one.

**Checkpoint 4: Certification Validity (After Phase 4)**

- **Automated Check**: The 3 calibration partitions share 0 identifiers; calibration gap at or below 10 percentage points in every reported slice for certified status; thresholds selected on the threshold partition; accepted-case error decreases monotonically as coverage decreases.
- **Agent Action on Pass**: Permit the signal to gate dispatch within its certified risk tiers.
- **Agent Action on Failure**: Suspend the signal, route affected traffic to the terminal default or human review, and name a recalibration owner.
- **Human Review Trigger**: A calibration gap above 20 percentage points in any slice, or a slice regression accompanying an aggregate improvement.

**Checkpoint 5: Dispatch and Recovery Integrity (After Phase 5)**

- **Automated Check**: Every dispatch carries an authorization decision made after routing; total dispatches per request at or below 2; no destination visited twice; accumulated cost includes rejected attempts; 0 re-routes across policy denials.
- **Agent Action on Pass**: Close the request and release the outcome record.
- **Agent Action on Failure**: Halt the request at the terminal default and record the loop-prevention or authorization defect.
- **Human Review Trigger**: Any dispatch executed without a current authorization decision, or any observed third dispatch.

**Checkpoint 6: Measurement and Change Integrity (After Phase 6)**

- **Automated Check**: Per-destination figures accompany every aggregate; stale-vocabulary events at 0 on hash-matched bundles; registry hash comparison within 24 hours; calibration recomputed after the taxonomy change; rollout stages executed in order with recorded gates.
- **Agent Action on Pass**: Promote the bundle and expand exposure by cohort.
- **Agent Action on Failure**: Roll back to the retained previous taxonomy version and name the failing gate.
- **Human Review Trigger**: Any safety incident, any authorization error, or a wrong-destination rate above the declared canary gate.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
BUNDLE_IDENTITY:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Out-of-Vocabulary or Schema-Invalid Router Response**

- **Symptoms**: The response fails to parse, violates the schema, names an identifier absent from the enumeration, exceeds the secondary destination maximum, or omits the echoed registry hash.
- **Diagnostic Steps**: Determine whether the constraint mechanism was applied, whether the enumeration was generated from the current registry, and whether the returned string corresponds to a retired identifier or to an invented one, keying the diagnosis to the failing validation check rather than to the response text.
- **Resolution Protocol**: Option A, retry once for transport or parse failure only, then fall to the terminal default. Option B, where the failure recurs on a specific bundle, roll back to the previous prompt version and re-generate the enumeration from the registry. Option C, where the provider offers no constrained generation, deploy the deterministic parser with identical rejection semantics and record the absent constraint as a bundle risk. Option D, where the returned string matches a retired identifier, treat the event as vocabulary drift and return to Step 1.2.
- **Escalation Trigger**: Schema-failure rate above 2 percent of routing calls, or out-of-vocabulary rate above 0.5 percent, rolls the bundle back regardless of aggregate accuracy. This class is never resolved by matching the invalid identifier to the nearest valid one.

**Error Type 2: Systematic Misroute on a Destination Pair**

- **Symptoms**: One confusion pair dominates the error mass; handler rejections concentrate on a single destination; user corrections cluster on one intent; per-destination recall falls while aggregate accuracy holds.
- **Diagnostic Steps**: Read the confusion matrix rather than the aggregate, test whether 2 independent annotators separate the pair using the published criteria, and determine whether the failure lies in the taxonomy, the examples, the missing context field, or the handler's admission check.
- **Resolution Protocol**: Option A, revise the taxonomy by merging the pair or by sharpening exclusion criteria and precedence, and return to Step 1.2 rather than adding prompt examples. Option B, add boundary examples only where annotators already agree and the model does not. Option C, require the missing context field at the dispatcher, converting the case to a clarify decision. Option D, where the handler's admission check is at fault, repair the check and reclassify the historical events.
- **Escalation Trigger**: A confusion pair carrying more than 20 percent of total routing error, or annotator agreement below 80 percent on that pair, halts prompt iteration and returns the pair to taxonomy review. Prompt tuning is never used to repair a taxonomy humans cannot apply.

**Error Type 3: Miscalibrated Routing Confidence**

- **Symptoms**: High stated confidence precedes handler rejection; accepted-case error fails to fall as abstention rises; the calibration gap widens in one slice while the aggregate holds.
- **Diagnostic Steps**: Recompute the calibration gap segmented by destination, risk tier, language, channel, and tenant class, and determine whether the degradation is confined to one segment or spans the bundle.
- **Resolution Protocol**: Option A, refit the calibrator on fresh fitting data and re-evaluate on an untouched partition. Option B, lower the acceptance threshold for the affected segment and route its traffic to clarification, the terminal default, or human review. Option C, replace the model's stated confidence with a signal originating outside the router, such as top-2 margin from an independent stage or downstream verification. Option D, suspend gating in the segment until recalibration completes.
- **Escalation Trigger**: A calibration gap above 20 percentage points in any slice suspends gating in that slice immediately; a generic threshold is never reused across destinations, risk tiers, or bundles.

**Error Type 4: Re-Route Loop or Budget Exhaustion**

- **Symptoms**: A request accumulates more than 2 dispatches; the same destination appears twice in a dispatch history; accumulated cost exceeds the declared maximum before any handler completes; re-route rate rises without a corresponding fall in end-to-end failure.
- **Diagnostic Steps**: Inspect the visited-destination set and the route-attempt budget on the affected requests, and determine whether the budget was carried on the request or recomputed by a component that lost state across a boundary.
- **Resolution Protocol**: Option A, move the budget and visited set onto the request payload so they survive component boundaries. Option B, exclude the rejecting destination from the enumeration presented for the second attempt, which makes a repeat selection structurally impossible. Option C, reduce the re-route budget to 0 for the affected destination class and send rejections directly to the terminal default. Option D, where rejections concentrate on one destination, treat the cause as Error Type 2 and repair the taxonomy.
- **Escalation Trigger**: Any observed third dispatch halts the request at the terminal default and opens a loop-prevention defect. Re-route rate above 10 percent of dispatched requests escalates for taxonomy review rather than for a budget increase.

**Error Type 5: Vocabulary Drift and Stale Destinations**

- **Symptoms**: The prompt's embedded registry hash differs from the deployed registry hash; the router selects an identifier the registry has retired; a registry entry receives no traffic for 30 days; compatibility rules are absent for a renamed identifier.
- **Diagnostic Steps**: Compare hashes first, then compare the enumeration against the registry entry by entry, and determine whether the divergence originated in a hand-edited prompt, a skipped regeneration, or a registry change deployed without a prompt rebuild.
- **Resolution Protocol**: Option A, regenerate the enumeration from the registry and redeploy, never editing the prompt by hand. Option B, publish compatibility rules mapping the retired identifier to its successor and retain the previous taxonomy version for rollback. Option C, open a deprecation review for the zero-traffic entry, and retire it only after the compatibility rules are published. Option D, where the change is large, run the old and new taxonomies in parallel and compare decisions before switching.
- **Escalation Trigger**: Any hash mismatch blocks deployment until regeneration succeeds; this class is never resolved by editing the prompt to match the registry, because the edit creates a second source of truth.

**Error Type 6: Router Overhead Exceeding Its Benefit**

- **Symptoms**: Router cost exceeds 10 percent of median destination cost; added routing latency at the 95th percentile exceeds 10 percent of median end-to-end latency; the deterministic baseline's accuracy converges on the model router's across releases.
- **Diagnostic Steps**: Recompute overhead including retries, failed attempts, and re-route dispatches, separate router cost from downstream cost in the accounting, and re-measure the baseline on current traffic rather than on the corpus it was first measured against.
- **Resolution Protocol**: Option A, expand the rule baseline to absorb destinations whose rule recall has reached 98 percent, shrinking the model router's decision space. Option B, add exact-match caching over a complete cache context covering tenant, authorization scope, locale, taxonomy version, policy version, and registry hash [21]. Option C, move a stable well-separated subset to an embedding or classifier stage and reserve the model router for the ambiguous remainder. Option D, retire the model router and deploy the baseline.
- **Escalation Trigger**: Cost ratio above 25 percent, or baseline accuracy within 3 percentage points of the model router, retires the model router at the next release. The router is never retained on the expectation that a future prompt revision will restore its advantage.

**Troubleshooting Decision Tree**:

```
ROUTING FAILURE DETECTED
├─ RESPONSE DEFECT
│   ├─ Unparsable or schema-invalid → Retry once → terminal default
│   ├─ Identifier not in enumeration → Terminal default; never a nearest match
│   └─ Registry hash mismatch → Block deployment; regenerate enumeration
├─ DECISION DEFECT
│   ├─ One confusion pair above 20 percent of error → Return pair to taxonomy review
│   ├─ Annotator agreement below 80 percent → HALT prompt tuning; revise criteria
│   └─ Required context field absent → Convert to clarify; cap at 1 question
├─ CONFIDENCE DEFECT
│   ├─ Slice calibration gap above 20 points → Suspend gating in that slice
│   ├─ Accepted-case error flat under rising abstention → Replace the signal source
│   └─ Uncertified signal used to gate → HALT dispatch; route to human review
├─ RECOVERY DEFECT
│   ├─ Third dispatch observed → HALT at terminal default; loop-prevention defect
│   ├─ Destination repeated in history → Exclude visited set from enumeration
│   └─ Re-route across a policy denial → HALT; denials are terminal
├─ VOCABULARY DEFECT
│   ├─ Retired identifier selected → Publish compatibility rules; regenerate prompt
│   └─ Registry entry at zero traffic for 30 days → Open deprecation review
└─ ECONOMIC DEFECT
    ├─ Cost ratio above 25 percent → Retire the router; deploy the baseline
    └─ Baseline within 3 points of the router → Retire the router at next release
```

### D. Performance Metrics and Continuous Learning

**Routing Quality Metrics**:

- **Per-destination recall**: Correctly routed requests over true requests for that destination (target: at least 85 percent for every destination carrying more than 1 percent of traffic; below 70 percent returns the destination to taxonomy review).
- **Wrong-destination rate**: Dispatches whose adjudicated destination differs from the selected one (target: at most 5 percent overall, and at most 1 percent for destinations in the high risk class).
- **Accepted-case error**: Error among decisions accepted above threshold (target: at most 3 percent at the operational coverage; a rise above 5 percent lowers coverage rather than raising the threshold silently).
- **Abstention correctness**: Abstentions that adjudication confirms had no valid destination (target: at least 80 percent; below 60 percent indicates the threshold is set above the signal's discriminating power).
- **Calibration gap**: Stated minus observed correctness, segmented by destination, risk tier, and declared slice (target: at most 10 percentage points per slice; above 20 suspends gating).

**Efficiency Metrics**:

- **Cost ratio**: Router overhead over median destination cost, including retries and re-routes (target: at most 10 percent; above 25 percent retires the router).
- **Added routing latency**: Router latency at the 95th percentile over median end-to-end latency (target: at most 10 percent).
- **Re-route rate**: Requests requiring a second dispatch (target: at most 5 percent; above 10 percent escalates for taxonomy review).
- **Terminal-default rate**: Requests closing at the terminal default (target: at most 5 percent; a rise indicates vocabulary coverage gaps rather than router failure).
- **Cost per resolved task**: Total cost including router, downstream, and re-route costs over end-to-end successes (target: at most 85 percent of the deterministic baseline).

**Integrity Metrics**:

- **Schema-failure rate**: Responses failing parse or schema validation (target: at most 1 percent; above 2 percent rolls the bundle back).
- **Out-of-vocabulary rate**: Responses naming an absent identifier (target: at most 0.5 percent).
- **Stale-vocabulary events**: Retired identifiers selected on a hash-matched bundle (target: 0).
- **Instrumentation completeness**: Routing spans carrying version provenance, paired route-correctness and end-to-end-success fields, and full cost accounting (target: 100 percent).

**Log-Pattern Failure Detection**: Rising terminal-default rate with stable schema-failure rate indicates a coverage gap in the taxonomy rather than a router fault. Rising re-route rate concentrated on one destination pair indicates a taxonomy boundary, not a prompt weakness. High confidence preceding handler rejection indicates miscalibration. Identical retries against one destination indicate a missing circuit breaker [18]. Cache-hit rate rising while accuracy falls indicates a cache context missing a version field. A destination whose end-to-end success falls while its routing recall holds indicates a handler problem that must not be treated as a routing problem.

**Learning and Adaptation Mechanisms**:

- **Adjudicated feedback only**: Corrections enter the evaluation corpus only after adjudication with recorded provenance; production corrections are never fed back into prompts, exemplars, or calibrators unadjudicated.
- **Mixed active-learning sampling**: Sample low-confidence, corrected, defaulted, and escalated cases together with randomly selected accepted high-confidence cases, since uncertainty-only sampling misses confident systematic errors.
- **Blinded candidate comparison**: Where destination choice is evaluated by a model judge, blind the candidate identities and preserve disagreements rather than resolving them silently, and prefer structured evaluator output over parsed free-form prose [16].
- **Bundle versioning**: Version every artifact that a certification attaches to, and evaluate a revised bundle on data collected after the revision rather than on the history that produced it.
- **Threshold recalibration**: Recompute every threshold per destination and risk tier at each release; the values stated in this guide are deployment defaults rather than measured constants.

**Human-in-the-Loop Boundaries**: Human review is a destination with an owner, an eligibility rule, a priority, a maximum waiting time, and a declared behaviour when no reviewer is available. Reviewers receive the request, the proposed destination, the ranked alternatives, the risk flags, the missing-information fields, and the governing policy, and never hidden reasoning. Reviewers record their destination, reason code, policy decision, and whether the taxonomy needs revision. Amendment of a destination's risk class, promotion of a bundle whose calibration gap exceeds 10 percentage points in any slice, retirement of an identifier carrying more than 1 percent of traffic, and any relaxation of the authorization boundary are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the dispatch of work to bounded capabilities rather than the content of any capability. Its phases hold wherever destinations are enumerable, a misroute is detectable, and the routing decision costs less than the work it directs.

### 4.1 Cross-Domain Application Patterns

**Customer service and support operations**: Destinations are intent pipelines, specialist queues, and self-service flows. Rules own tenant, entitlement, language, and channel; the model router owns intent among overlapping categories such as billing dispute against refund request. Misroutes surface as handler rejections and as user rephrase within the same session, and the terminal default is a general agent with a narrow tool scope. The dominant risk is a taxonomy whose boundaries reviewers apply inconsistently, so annotator agreement gates every taxonomy change before any prompt revision.

**Software engineering automation**: Destinations are specialist agents for diagnosis, patching, test authoring, refactoring, and dependency work, plus a refusal path. Handler rejections are cheap and precise here, because an admission check can test for the presence of a failing test, a stack trace, or a target module before work begins. The re-route budget is the principal control, since an agent that accepts an out-of-scope task consumes a full execution before failing.

**Clinical and regulated decision support**: Every destination carries a high or irreversible risk class, so the approval gate binds before dispatch and abstention is preferred over an unverified selection. The registry's data-class and residency fields become enforcement inputs rather than documentation, and the routing span becomes a deliverable for audit rather than a diagnostic aid. Human review is staffed with a declared service level, because an unstaffed review queue converts abstention into indefinite delay.

**Financial operations and payments**: Eligibility, limits, sanctions screening, and residency are rule-owned and never routed by a model. The model router selects among analysis, dispute handling, and advisory destinations only after policy has fixed what the request is permitted to reach. Cost accounting is exact rather than estimated, because the router's own spend is reconciled against invoices and a cost ratio breach retires the router.

**Scientific and research workflows**: Destinations are retrieval, computation, simulation, and synthesis pipelines whose costs differ by orders of magnitude. Cascade behaviour matters most here, since a cheap destination's output can often be scored well enough to decide whether escalation is warranted [6][7]. Vocabulary change is frequent because new instruments and methods arrive continuously, so the taxonomy change procedure runs more often than the calibration procedure.

**Public-sector case handling**: Destinations map to statutory processes whose boundaries are defined externally and cannot be merged for convenience. Precedence rules are therefore inherited rather than designed, and the guide's merge operation is unavailable. Slice reporting by language and channel is mandatory rather than optional, because selective acceptance can improve accepted-case accuracy while worsening outcomes for particular groups [10].

### 4.2 Scale, Risk, and Latency Adaptation

- **Small destination sets under 8 entries**: Collapse Phase 2's classifier and embedding comparisons, retain the deterministic baseline and the cost ratio test, and expect the baseline to win more often than not.
- **Large destination sets above 40 entries**: Route hierarchically, selecting a family first and a leaf second, score both levels separately, and cap the enumeration presented in any single call so the prompt does not grow past the model's reliable attention span.
- **High-risk or irreversible destinations**: Require certification of the confidence signal at the 0.90 tier threshold, bind the approval gate before dispatch, set the re-route budget to 0, and prefer abstention to a second attempt.
- **Strict latency budgets**: Shorten the router prompt and cache exact matches over a complete cache context rather than removing validation, since removing validation removes the only defence against an out-of-vocabulary dispatch. Where latency forbids an inference call entirely, the gate suppresses the router and the deterministic baseline runs with a declared fallback.
- **Multi-tenant deployments**: Partition the cache, the calibration dataset, and every reported slice by tenant, and never reuse a routing decision across tenants, permission scopes, taxonomy versions, or policy versions.
- **High-volume steady traffic**: Move the stable, well-separated portion of the taxonomy to an embedding or classifier stage and reserve the model router for the ambiguous remainder, re-measuring the split each release as the residual shrinks.

***

## V. Limitations and Considerations

**The router taxes every request it touches**: Each routing call adds latency, tokens, and money to requests that would have reached the right destination without it, and the tax scales with traffic while the benefit scales with the ambiguous fraction. The mitigation is the selection gate in Section 1.4 together with the cost ratio and headroom tests in Step 2.2, which retire the router when the deterministic baseline comes within 3 percentage points.

**The stated thresholds are deployment defaults, not measured constants**: The 10 percent cost ratio, the 5 percentage point headroom requirement, the 0.60, 0.80, and 0.90 tier thresholds, the 1 re-route attempt, the 98 percent rule-coverage bound, the 1 percent schema-failure ceiling, the 0.5 percent out-of-vocabulary ceiling, and the 200-example slice minimum were chosen to be operable on first deployment rather than derived from a property of routing systems. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute every threshold per destination and risk tier against observed outcomes.

**The calibration gap bands are inherited, not re-derived**: The 10 and 20 percentage point certification bands are adopted from the corpus guide on metacognitive monitoring so that the two guides name one concept one way. The mitigation is explicit adoption rather than restatement, so a future revision of that procedure propagates here instead of leaving two divergent numbers in the corpus.

**Routing accuracy is not task success**: A router can select correctly and still produce a failed outcome because the destination is weak, and can select incorrectly and still produce a plausible answer. The mitigation is the paired route-correctness and end-to-end-success fields required on every routing span in Step 5.2, which prevent a handler defect from being diagnosed as a routing defect.

**Misroute detection depends on handlers that can reject**: Where a destination produces fluent output for work it cannot do, the misroute is invisible to the active detection path and surfaces only through delayed user signals. The mitigation is the admission-check requirement in Step 5.2, which bars a destination from the registry until it can return a typed rejection, together with the passive signal set that covers the residual.

**Adjudicated routing labels are expensive and often late**: Per-destination measurement at the stated slice minimum requires substantial human adjudication, and deployments under schedule pressure report aggregates instead. The mitigation is the provisional-reporting rule in Step 6.1, which marks under-sampled destinations as provisional rather than allowing an aggregate figure to stand in for them.

**The router is a high-leverage attack surface**: A single manipulated decision can reach a more privileged destination or a weaker safety policy, and injection can arrive indirectly through retrieved pages, files, tool results, or inter-agent messages rather than through the user's text [12]. The mitigation is the trust boundary in Step 3.1, the registry-derived execution scope in Step 5.1, and independent re-authorization at execution time, none of which depend on detecting the injection.

**Transcribed claims were not re-verified except where marked**: The external references in Section VII are carried from the originating prose source as it cited them. Three entries were retrieved and confirmed during this conversion and are marked as such; the remainder are reproduced rather than checked. The mitigation is the explicit marking, so a reader can see which figures rest on retrieval and which on transcription.

***

## VI. Conclusion and Summary

LLM-based routing is a policy discipline before it is a prompting technique. The router is a model call placed in front of every request, so it must earn its place against a deterministic baseline on measured cost and measured accuracy, and it must be retired when the baseline catches up. Its output is only usable because a registry outside the model defines what a valid destination is, and because a dispatcher outside the model refuses anything else. Its confidence is only usable because a calibration procedure has attached a measured meaning to the number, against a named bundle that any change invalidates.

A team introducing a router should build the registry and the deterministic baseline before writing a prompt. Measure the baseline, compute the residual traffic the rules cannot place, and confirm that residual is large enough and the router cheap enough for the arithmetic to work. Add the constrained output contract and the validation ladder, then instrument the routing span with paired route-correctness and end-to-end-success fields. Only then calibrate the confidence signal, set risk-tiered thresholds, and enable abstention. Add bounded re-routing last, and never as a substitute for a taxonomy whose boundaries annotators cannot apply.

**Key Success Factors**:

- **Registry before prompt**: The closed vocabulary lives in a versioned artifact that generates the prompt, so a destination the registry does not hold cannot be dispatched and cannot be enumerated.
- **Baseline before router**: The deterministic baseline is implemented and measured first, wins ties, and reclaims the router's traffic whenever it comes within 3 percentage points.
- **Constrained output with a deterministic fallback**: An out-of-vocabulary response falls to a declared default and is never coerced to the nearest valid destination, because coercion hides a detectable failure.
- **Calibration before gating**: Confidence gates nothing until its calibration gap has been measured on an untouched partition against a named bundle, and certification dies with the bundle.
- **Detectable misroutes with a bounded recovery**: Every destination can reject what it cannot serve, and recovery is capped at 1 re-route with a visited-destination set, so a request terminates rather than circulating.
- **Separate measurement of route and outcome**: Route correctness and end-to-end success are recorded as distinct fields, so a weak handler is never repaired by revising the router.

By following this guide, AI agents can operate a model router as an auditable policy component that sends each request to an eligible destination, declares when it does not know, contains a bad decision within a bounded recovery path, and produces the evidence needed to justify its own continued existence.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them, and were not independently re-verified during conversion, with three exceptions retrieved and confirmed in the course of this work and marked as verified below.

**Corpus pointers**:

- `LLM-Based Routing: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the routing families and their selection criteria, the route contract, the router prompt design rules, the confidence and abstention discipline, the ambiguity and multi-intent handling, the fallback classes, the security controls, the three-layer evaluation methodology, the telemetry field inventory, the caching context, the drift and taxonomy evolution procedure, the rollout sequence, and the human-review design. Its inline citations to routing benchmarks, abstention research, security guidance, observability specifications, and release practice supply the external references listed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — the calibration procedure this guide adopts rather than re-derives. Source of the terminology for signal, estimator signal, observable event, source class, calibration gap, signal certification, bundle, and selective prediction, and of the three-partition calibration dataset and the certification bands used in Phase 4.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on value-of-computation control, applicable to the router selection gate in Section 1.4 and to the cost tests in Phase 2.
- `advanced_task_guides/routing/guide_RuleBasedRouting.md` — the sibling routing method deciding from declared rules over trusted request attributes, producing a verified routing table with total coverage and a reversible change path. It is the deterministic counterpart named throughout Section 1.2 and Phase 2, and the specification of the deterministic baseline every model router here is measured against.
- `advanced_task_guides/routing/guide_EmbeddingBasedRouting.md` — the sibling routing method deciding by calibrated nearest-exemplar similarity under a pinned embedding generation, named as a suppression substitute in Section 1.4 where destination boundaries are semantically stable and exemplars can be curated.
- `advanced_task_guides/routing/guide_CapabilityRouting.md` — the sibling routing method performing requirement-matched handler selection with explicit non-selection. It bears on the destination attributes recorded in Step 1.1, and it composes with this method rather than competing: a model may extract the requirement fields, and capability matching then owns eligibility, ranking, and dispatch.
- `advanced_task_guides/routing/guide_ContentBasedRouting.md` — the sibling routing method deciding by bounded inspection of payload contents. Its detection cascade escalates into the model tier specified here, and it retains authority over the fail-safe direction and terminal disposition applied to the answer.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on telemetry design, applicable to the routing span and field inventory in Section III.A.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on schema versioning, migration, and deprecation management, applicable to the taxonomy change procedure in Step 6.3.

**External references**: The numbering below is the numbering used by the inline markers throughout this guide.

*Routing patterns, benchmarks, and cost-quality evaluation*

1. Amazon Web Services, *Routing and dynamic dispatch patterns, AWS Prescriptive Guidance* — https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/routing-dynamic-dispatch-patterns.html
2. OpenAI, *Introducing Structured Outputs in the API* — https://openai.com/index/introducing-structured-outputs-in-the-api/
3. Aurelio Labs, *Semantic Router* — https://github.com/aurelio-labs/semantic-router
4. *RouteLLM: Learning to Route LLMs with Preference Data* — https://arxiv.org/html/2406.18665v4 (title and metric names verified during conversion)
5. *RouterBench: A Benchmark for Multi-LLM Routing System* — https://arxiv.org/abs/2403.12031 (title and the figure of over 405,000 inference outcomes verified during conversion)
6. *FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance* — https://arxiv.org/abs/2305.05176 (title verified during conversion)
7. *Select-then-Route* — https://aclanthology.org/2025.emnlp-industry.28/
8. *RouteMoA* — https://aclanthology.org/2026.acl-long.558/

*Abstention, selective prediction, and subgroup effects*

9. *Abstention survey* — https://arxiv.org/html/2407.18418v2
10. Stanford AI Lab, *Selective classification analysis* — https://ai.stanford.edu/blog/sc-magnifies-disparities/

*Security, safety, and risk management*

11. OWASP, *AI Agent Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
12. OWASP, *LLM Prompt Injection Prevention Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
13. NIST, *AI RMF Generative AI Profile* — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf

*Observability, evaluation tooling, and release control*

14. OpenTelemetry, *GenAI attributes* — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
15. Langfuse, *Data model* — https://langfuse.com/docs/observability/data-model
16. Arize, *Phoenix evaluations* — https://arize.com/docs/phoenix/evaluation/llm-evals
17. OpenFeature, *Observability specification* — https://openfeature.dev/specification/appendix-d/
18. Microsoft, *Implement the circuit breaker pattern* — https://learn.microsoft.com/en-us/dotnet/architecture/microservices/implement-resilient-applications/implement-circuit-breaker-pattern
19. Google SRE, *Canarying releases* — https://sre.google/workbook/canarying-releases/

*Drift, caching, and provider routing infrastructure*

20. Frontiers in Artificial Intelligence, *Survey on concept drift* — https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1330258/full
21. Microsoft, *Azure Cosmos DB semantic cache overview* — https://learn.microsoft.com/en-us/azure/cosmos-db/gen-ai/semantic-cache
22. LiteLLM, *Routing documentation* — https://docs.litellm.ai/docs/routing
23. OpenRouter, *Auto-router documentation* — https://openrouter.ai/docs/guides/routing/routers/auto-router
24. OpenRouter, *Provider-routing documentation* — https://openrouter.ai/docs/guides/routing/provider-selection

*Routing evaluation formalisation*

25. *RouterEval* — https://aclanthology.org/2025.findings-emnlp.208.pdf
