# Capability Routing

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Capability routing constitutes the task family of directing a bounded unit of work to a handler on the basis of what that handler can demonstrably do, by converting the request into an explicit set of required capabilities and matching that set against the capabilities the handler population is credited with. This guide provides AI agents with a structured protocol for declaring a capability vocabulary and requirement schema, extracting requirements from an arriving request, filtering the handler population to those eligible on every required capability, ranking the eligible set under fit, credibility, and load, dispatching under a re-authorization gate, and reporting outcomes back to the expertise directory that supplied the candidates. It treats the no-eligible-handler condition as a first-class terminal outcome rather than as a fallback to the least badly ranked handler, and treats that condition as coverage-gap evidence the handler population owes an answer to. It specifies conjunctive matching over required capability classes, ordinal comparison of declared proficiency levels, a numeric load and concentration penalty applied only after eligibility is settled, demotion rather than trust for stale declarations, and bounded escalation wherever requirement extraction or matching fails. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a routing decision is reproducible against a pinned catalogue snapshot and attributable after the fact.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Capability routing**: A control-plane discipline that converts a request into a typed requirement object, filters a bounded handler population against that object's hard constraints, ranks the surviving candidates, and dispatches exactly one selection or one explicit non-selection. It decides which competent handler receives the work; it does not decide what work exists.

**Handler**: Any addressable entity a unit of work can be dispatched to: a model endpoint, an agent instance, a tool, an API operation, a workflow, a queue, or a named human role. A handler is the same entity the expertise directory records as a holder; the two terms name one entity under two roles, the directory's subject and the router's target.

**Capability class**: A named, stable unit of competence against which evidence accumulates, defined by positive examples, counterexamples, required inputs, an output contract, an acceptance test, and a risk class. The term, its definition, and its governance belong to the expertise directory and are consumed here unchanged.

**Capability taxonomy**: The versioned controlled vocabulary of capability classes, together with mappings from deprecated terms to current ones. The router reads the taxonomy and never extends it.

**Expertise directory**: The governed store recording which handler is credited with which capability class, at what credibility, on what evidence, and within what validity window. It is an input to capability routing and is produced by a separate discipline.

**Directory entry**: A versioned assertion that one handler possesses one capability class, carrying a credibility score, an evidence set, a validity window, and a layer assignment.

**Effective layer**: The policy-approved subset of directory entries that lookup may return. The router consumes only this layer and has no read path to declared or observed entries.

**Lookup**: The directory operation that accepts a competence requirement and returns a ranked candidate set with credibility, evidence references, freshness state, and eligibility verdicts. Lookup selects nothing; it supplies the input the router selects from.

**Requirement object**: The typed record produced from one request, enumerating every capability class the work needs with a necessity label, every hard constraint the handler must satisfy, every soft preference used for ranking, and the provenance and confidence of each field. It is the router's sole statement of what the request demands.

**Competence requirement**: The subset of the requirement object naming capability class identifiers with necessity labels. The term is the directory's, and the router emits it in the directory's shape so that lookup can consume it without translation.

**Necessity label**: One member of a closed pair governing how a capability class enters matching. A class labelled required must be satisfied by the selected handler; a class labelled optional contributes to fit and never to eligibility.

**Proficiency level**: The ordinal band at which a capability class is held or demanded, drawn from a four-point scale: 0 absent, 1 basic, 2 standard, 3 advanced. Levels are compared by ordinal inequality and are never averaged, summed, or traded against another class.

**Hard constraint**: A predicate over a handler and the requirement object that must return pass for the handler to be eligible. Hard constraints cover required capability classes and their proficiency levels, schema and modality compatibility, capacity and context limits, tenant and region scope, data class, prohibited effects, deadline feasibility, cost ceiling, and freshness limits.

**Soft preference**: A scored attribute used to order handlers that have already passed every hard constraint. Soft preferences never restore an ineligible handler and never compensate for a failed hard constraint.

**Constraint verdict**: One member of a closed four-valued set recorded for every applicable hard constraint against every candidate: pass, fail, unknown, or not applicable. Unknown is neither pass nor fail and never resolves to pass by default.

**Eligible handler**: A handler for which every applicable hard constraint returned pass under the pinned catalogue snapshot. Eligibility is a conjunction, not a score.

**Qualified set**: The set of eligible handlers surviving filtering for one request. Its size is the primary diagnostic for requirement extraction quality.

**Fit**: The scalar in the range 0.00 to 1.00 measuring how completely an eligible handler covers the requirement object's optional classes and how far its proficiency levels exceed the demanded minima. Fit orders eligible handlers; it never creates eligibility.

**Credibility**: The scalar in the range 0.00 to 1.00 the directory attaches to an entry, estimating the probability that the handler satisfies the capability class's acceptance test on a task of stated difficulty. The router reads credibility and never writes it.

**Utilization**: The current in-flight work assigned to a handler divided by its declared concurrency limit, expressed in the range 0.00 to 1.00 and carrying an observation timestamp and an expiry.

**Dispatch share**: The fraction of dispatched requests for one capability class that reached one handler over a trailing observation window. It is the router-side measurement of concentration.

**Concentration**: The degree to which credited competence, or dispatched work, is held by few handlers. The directory measures it over the capability catalogue; the router measures it over served dispatches and reports the result back.

**Bus factor**: The count of eligible handlers meeting the class floor for one capability class. A bus factor of 1 is a single point of failure and is recorded on every dispatch that depends on it.

**No-eligible-handler outcome**: The terminal routing result recorded when the qualified set is empty. It is one of the router's permitted outcomes, carries a reason code and an escalation destination, and is never replaced by dispatch to a handler that failed a hard constraint.

**Mutual ignorance**: The directory condition in which no holder is credited above the credibility floor for a needed capability class. It is the directory-side name for one cause of the no-eligible-handler outcome.

**Coverage gap**: A capability class present in observed demand but absent from the taxonomy or absent from the effective layer. The router detects coverage gaps and reports them; the directory owns their remedy.

**Under-specified requirement**: A requirement object whose hard constraints leave more than the declared upper bound of the handler population eligible, indicating that the extraction failed to capture a discriminating demand.

**Over-specified requirement**: A requirement object that yields an empty qualified set while at least one handler failed on exactly one liftable, non-safety constraint, indicating that the extraction imposed a demand the request did not make.

**Dispatcher**: The deterministic component that validates the routing decision against the effective layer, re-authorizes the selected handler against current policy, binds least-privilege credentials, and invokes the handler. The router selects; the dispatcher executes.

**Routing decision record**: The typed, versioned record the router emits for every request, carrying the requirement object hash, the catalogue snapshot identifier, per-candidate constraint verdicts, rank components, the terminal outcome, and the reason code.

**Routing correctness**: The agreement between the selected handler and the adjudicated acceptable handler set on a labelled evaluation corpus. It is measured separately from task success, because a correct selection can fail in execution and an incorrect selection can succeed by accident.

**Misroute**: A dispatched request that reached a handler lacking a required capability class at the demanded proficiency level, whether because matching erred or because the directory entry was wrong.

### 1.2 Matching Semantics and the Constraint Trichotomy

Matching semantics must be declared before any handler is evaluated, because the same catalogue and the same request produce different selections under different semantics, and an undeclared semantics is discovered only through misroutes.

**Conjunctive semantics over required classes**: A handler is eligible only where it is credited, in the effective layer, with every capability class the requirement object labels required, each at or above the demanded proficiency level. Required-class coverage is therefore exactly 1.00 or the handler is ineligible. No arithmetic combination of partial coverage produces eligibility, and no quantity of optional-class coverage substitutes for a missing required class.

**Ordinal level comparison**: A capability class carries a demanded level and a credited level on the same four-point ordinal scale. The comparison is credited level greater than or equal to demanded level, evaluated per class. Levels are not averaged across classes, not converted to a percentage, and not offset against credibility: a handler credited at level 1 for a class demanded at level 2 fails that constraint regardless of its credibility on the class.

**Credibility as a floor, not a substitute**: Each risk class declares a credibility floor that a candidate entry must meet to be eligible: 0.50 for low risk, 0.65 for medium risk, and 0.80 for high risk. An entry below its floor is ineligible on that class. Above the floor, credibility enters ranking. Credibility never lifts a failed level comparison and a level surplus never lifts a failed floor.

**Optional classes and partial coverage**: Classes labelled optional never gate eligibility. Their coverage enters fit, which orders the qualified set. A request whose optional coverage matters more than its required coverage has been extracted wrongly and is returned to Phase 2 rather than routed.

**Unknown is never pass**: Where a hard constraint cannot be evaluated because the evidence is missing, absent from the entry, or past its freshness limit, the verdict is unknown. Unknown excludes the candidate from the qualified set for that request, and triggers clarification, a bounded verification probe, or escalation according to the constraint's declared branch. Converting unknown to pass is the single most damaging defect available to a matcher, because it produces a confident dispatch on no evidence.

**Constraint Kinds and Their Handling**:

| Constraint kind | Role in matching | Failure handling | May a soft score compensate |
| :-- | :-- | :-- | :-- |
| Required capability class and level | Eligibility conjunct | Candidate excluded, reason code recorded | Never |
| Policy, tenant, region, data class | Eligibility conjunct, evaluated first | Candidate excluded before any scoring | Never |
| Prohibited effect, write authority | Eligibility conjunct | Candidate excluded, escalation on high risk | Never |
| Schema, modality, capacity, protocol | Eligibility conjunct | Candidate excluded, reason code recorded | Never |
| Deadline and cost ceiling | Eligibility conjunct against declared envelope | Candidate excluded or degradation offered | Never |
| Freshness limit on the entry | Eligibility conjunct on lapse, demotion otherwise | Lapsed excluded; stale demoted in ranking | Never on lapse |
| Optional capability class | Fit component | Fit reduced, candidate retained | Not applicable |
| Credibility above floor | Fit and rank component | Below floor excluded; above floor ranked | Not applicable |
| Utilization and dispatch share | Rank penalty only | Penalty applied; hard exclusion above ceiling | Not applicable |

### 1.3 The Execution Tier Partition

Capability routing is a deterministic decision operated with model assistance at one narrow point. Assigning each unit of work to a tier is what separates an auditable router from a prompt that names some agents.

**Deterministic tier**: Software, schema validators, policy engines, and queries own the capability index built from the effective layer; the requirement schema and its validation; matching of requirement fields to capability classes; eligibility filtering across every hard constraint; the four-valued verdict record; all ranking arithmetic including fit, credibility weighting, the load penalty, the concentration penalty, and tie-breaking; snapshot pinning; dispatch and its re-authorization; budget enforcement; and the no-eligible-handler escalation with its reason code and destination. These require exactness, reproducibility against a named snapshot, and auditability that model inference cannot supply. The same requirement object evaluated twice against the same snapshot must produce the same qualified set in the same order and the same terminal outcome.

**Model tier**: LLM calls own exactly one decision: interpreting an arriving request into the capability classes it requires, where no deterministic parse exists. This covers requests stated in natural language, requests that name no capability, requests using vocabulary absent from the taxonomy, and requests bundling several competences into one sentence. The model emits candidate class identifiers with the request span that motivated each and a per-field confidence, and emits nothing else that reaches a decision.

**Hybrid tier**: Requirement extraction is the principal hybrid operation. The model proposes capability class identifiers and inferred constraint values; deterministic validation admits an identifier only where it exists in the current taxonomy version, admits an inferred constraint value only where it does not contradict a trusted field from the authenticated request envelope, and rejects everything else with a reason code. Where the model and the validator disagree, the validator holds authority and the proposal is recorded as rejected. Degradation is the second hybrid operation: a model may propose which preapproved relaxation best serves the request, and a deterministic gate admits it only where the relaxation appears in the approved degradation catalogue for that requirement class and where consent requirements are satisfied.

**Tier Ownership of Routing Artifacts**:

| Artifact | Owning tier | Authority on disagreement |
| :-- | :-- | :-- |
| Capability index over the effective layer | Deterministic | Deterministic, exclusively |
| Requirement object schema and validation | Deterministic | Deterministic, exclusively |
| Capability class identifiers inferred from prose | Hybrid | Deterministic validator |
| Trusted constraint fields from the request envelope | Deterministic | Deterministic, exclusively |
| Constraint verdicts and the qualified set | Deterministic | Deterministic, exclusively |
| Fit, credibility, load, and concentration arithmetic | Deterministic | Deterministic, exclusively |
| Selection of the degradation to offer | Hybrid | Deterministic gate |
| Dispatch, re-authorization, credential binding | Deterministic | Deterministic, exclusively |
| No-eligible-handler outcome and its reason code | Deterministic | Deterministic, exclusively |
| Outcome adjudication feeding the directory | Hybrid | Deterministic gate in the directory |

**What the model tier may never decide alone**: whether a handler is eligible; the numeric rank of any candidate; whether a hard constraint may be relaxed; whether an escalation may be suppressed; which credential the dispatcher binds; and whether a stale entry may be treated as fresh. Each is a deterministic evaluation over stored fields, and a model's agreement with it carries no additional weight.

**The best-effort prohibition**: A handler lacking a required capability class, or credited below the demanded proficiency level, or below the risk class credibility floor, is never selected as a best-effort fallback. Ranking operates strictly inside the qualified set. Where the qualified set is empty the router emits the no-eligible-handler outcome, and a deployment in which the least badly ranked ineligible handler receives the work is misconfigured, not degraded.

### 1.4 The Routing Gate and Boundaries Against Adjacent Mechanisms

**Gate conditions**: Construct a capability router where at least 3 of the following hold. The handler population contains at least 3 handlers differing in validated competence rather than in role label alone. Requests impose demands that can be represented as typed constraints and checked against declared fields. An expertise directory exists with an effective layer, evidence, and freshness state. Misrouting carries a measurable cost in quality, latency, risk, or rework. The handler population changes independently of the router, so a static assignment table would drift.

**Suppression conditions**: Suppress the router where one handler could serve every request within its declared envelope; where trusted request metadata already determines the destination deterministically, in which case a rule set is cheaper and more auditable; where declarations cannot be kept current, since matching then runs on fiction; or where outcomes cannot be adjudicated, since routing correctness would have no signal. Record the suppression reason and the substitute chosen.

**Boundary against the expertise directory**: The directory owns which handler knows or can do what, the evidence hierarchy placing observed outcomes above declared capability above self-assessment, credibility updates from adjudicated outcomes, staleness bounds and re-verification, and concentration and coverage health. That discipline states the lookup contract and explicitly declines to specify a router. This guide specifies the router and consumes the directory through that contract: lookup returns candidates with credibility, uncertainty, sample count, evidence references, freshness state, eligibility verdict, and a snapshot identifier, and the router returns the selected handler and a decision identifier so the outcome can be attributed back to the entry that produced the candidate. Agents must not embed routing policy in the directory, and must not maintain a second competence store inside the router.

**Boundary against rule-based routing**: A deterministic rule set owns every destination derivable from trusted structured fields, and owns every binding constraint on authorization, compliance, residency, and tenancy. Capability routing runs after those gates and only over the candidates they permit. Where the correct handler is a function of an authenticated metadata field alone, a rule is the correct mechanism and a capability match is overhead.

**Boundary against model-based routing**: A model router reads a request and names a destination directly. Capability routing uses model inference only to produce requirement fields, which deterministic matching then evaluates against declared capabilities. The two compose: a model may extract the requirement, and the capability matcher decides eligibility.

**Boundary against planning and composition**: Routing chooses a qualified handler for a bounded unit of work. Planning decomposes a goal and decides which units exist. Where no single handler covers every required class but a set could, the router emits a composition proposal as a distinct outcome and hands it to the planning discipline; it does not average partial coverage into a false full match and it does not dispatch a partial handler on the assumption that the remainder will be handled later.

**Boundary against authorization**: Capability answers whether a handler could satisfy the contract. Authorization answers whether this principal may perform this action on this resource now. The two are separate verdicts computed by separate components, and a capability match never widens authority.

***

## II. Operational Framework: Requirement-Matched Handler Selection With Explicit Non-Selection

The framework assumes the routing gate in Section 1.4 has returned construct and that an expertise directory with a populated effective layer exists. Phase 1 runs once per catalogue version and on every taxonomy change. Phases 2 through 5 run per request in order. Phase 6 runs asynchronously on completed work and on a fixed audit cadence, and can force a return to Phase 1 where the vocabulary itself is found deficient.

### Phase 1: Capability Vocabulary and Requirement Schema Declaration

**Objective**: Fix the vocabulary the router may reference, the shape of the requirement object it must produce, and the matching and ranking semantics it will apply, so that no per-request decision invents its own terms.

#### Step 1.1: Bind the Capability Vocabulary to the Directory Taxonomy

**Required Actions**:

- Import the capability taxonomy from the expertise directory at a pinned taxonomy version, and record that version on every artifact the router publishes.
- Enumerate the closed set of capability class identifiers the router may reference, and reject at load time any identifier absent from the pinned version.
- Apply the directory's deprecation map on import, rewriting every deprecated identifier to its current successor and recording the rewrite, rather than carrying both forms.
- Record, per capability class, its risk class and its credibility floor, taking the floors from Section 1.2 unless the directory declares stricter values, in which case the stricter value holds.
- Build the capability index over the effective layer only, keyed by capability class identifier and returning handler identifiers with credited level, credibility, freshness state, and entry version.
- Prohibit any router-local capability record: where the router needs a competence fact the directory does not carry, raise a taxonomy request rather than storing the fact.

**Required Outputs**:

- A pinned taxonomy version identifier with its deprecation map applied.
- A closed capability class vocabulary with risk class and credibility floor per class.
- A capability index over the effective layer with entry versions recorded.

**Quality Checkpoints**:

- Every identifier the router can emit exists in the pinned taxonomy version; unknown identifiers are rejected at load, not repaired at match time.
- The capability index reads the effective layer exclusively; a build that reads declared or observed entries halts.
- Zero competence facts are stored outside the directory.

***

#### Step 1.2: Declare the Typed Requirement Schema and Its Provenance Classes

**Required Actions**:

- Define the requirement object as a typed schema carrying required and optional capability classes with demanded proficiency levels, hard constraint fields with units and comparison operators, soft preference fields, and a risk class.
- Assign every field a provenance class from a closed set: envelope for values read from the authenticated request envelope, stated for values the requester supplied in the request body, inferred for values a model proposed, and default for values the schema supplies when nothing else does.
- Establish provenance precedence deterministically: envelope outranks stated, stated outranks inferred, and inferred outranks default. An inferred value must never overwrite an envelope value, and a conflict between the two is recorded and resolved in favour of the envelope.
- Require a confidence value in the range 0.00 to 1.00 on every inferred field, and require the request span that motivated it, so that a wrong inference is diagnosable rather than opaque.
- Express every numeric constraint with an explicit unit and comparison operator, and reject schema instances carrying bare adjectives such as fast or cheap in a constraint position.
- Compute a stable requirement object hash over the normalised field set, and carry it on the decision record so that identical requests are recognisable across runs.

**Requirement Object Contract**:

```
REQUIREMENT_ID:            SCHEMA_VERSION:      TAXONOMY_VERSION:
RISK_CLASS:                low | medium | high
REQUIRED_CAPABILITIES: [ capability_class_id, demanded_level(0-3) ]
OPTIONAL_CAPABILITIES: [ capability_class_id, demanded_level(0-3) ]
HARD_CONSTRAINTS: [
  field_id / operator / value / unit
  provenance: envelope | stated | inferred | default
  confidence (inferred only) / source_span (inferred only)
]
SOFT_PREFERENCES:  [ field_id, direction, weight_ref ]
BUDGETS:           deadline_ms / cost_ceiling / attempt_limit / clarification_limit
DEGRADATION:       permitted_levels | none
UNRESOLVED_FIELDS: [ field_id, blocking(true|false) ]
REQUIREMENT_HASH:
```

**Required Outputs**:

- A versioned requirement object schema with provenance classes and precedence declared.
- A validator rejecting untyped constraint values and unresolved required fields.
- A requirement object hash definition covering the normalised field set.

**Quality Checkpoints**:

- Every constraint field carries a unit and a comparison operator; a field carrying a bare adjective fails validation.
- Provenance precedence is enforced by the validator, so an inferred value cannot overwrite an envelope value in any execution path.
- Every inferred field carries a confidence value and a source span; an inferred field missing either is rejected.

***

#### Step 1.3: Declare the Matching Semantics and the Versioned Rank Weight Vector

**Required Actions**:

- Declare the matching semantics explicitly as conjunctive over required capability classes, with ordinal level comparison and credibility floors per risk class, and record the declaration as a versioned configuration artifact rather than as code comments.
- Declare the rank weight vector with its component weights summing to exactly 1.00, its normalisation windows, and its missing-value rule per component.
- Set the deployment default weights to fit 0.35, credibility 0.30, load 0.20, and cost or latency headroom 0.15, and require that any change to the vector pass the replay gate in Phase 6 before activation.
- Declare the deterministic tie-break sequence as an ordered list, defaulting to higher credibility, then higher evidence freshness, then lower utilization, then lower dispatch share, then lower expected cost, then stable handler identifier.
- Declare the qualified set size bounds used to detect extraction defects, defaulting to a lower bound of 1 and an upper bound of 8 or 25 percent of the eligible handler population, whichever is smaller.
- Prohibit hiding a policy rule inside a weight: any predicate that must always hold is a hard constraint and is declared as one.

**Required Outputs**:

- A versioned matching semantics declaration naming conjunction, ordinal comparison, and floors.
- A rank weight vector with weights summing to 1.00 and normalisation windows declared.
- A deterministic tie-break sequence and declared qualified set size bounds.

**Quality Checkpoints**:

- Rank weights sum to exactly 1.00; a vector that does not sum to 1.00 fails activation.
- The tie-break sequence terminates in a stable identifier, so no two runs over one snapshot can order the qualified set differently.
- Zero policy predicates appear as weights; every always-true requirement is a declared hard constraint.

***

### Phase 2: Requirement Extraction From the Request

**Objective**: Convert one arriving request into a validated requirement object whose specificity is measured rather than assumed, because an under-specified requirement matches too many handlers and an over-specified one matches none.

#### Step 2.1: Populate Trusted and Derived Requirement Fields Deterministically

**Required Actions**:

- Read every field available from the authenticated request envelope first: tenant, principal, purpose, region, residency, data class, entitlement, approval state, deadline, and cost ceiling, and mark each with provenance envelope.
- Derive every field computable by rule from trusted inputs, including payload size, input and output modality, media types, language tag where an authenticated locale exists, and effect class where the requested operation is enumerated, and mark each with provenance stated or default as the derivation warrants.
- Populate budget fields from policy rather than from the request body, so that a requester cannot widen the attempt, clarification, or cost limits by asserting them.
- Freeze every envelope field before any model call, so that no inferred value can contend with a trusted one.
- Record which required schema fields remain unresolved after deterministic population, marking each as blocking or non-blocking against the declared risk class.
- Short-circuit to matching where deterministic population resolves every required field, and record that no model call was made, since a request fully determined by trusted metadata must not pay inference cost.

**Required Outputs**:

- A partially populated requirement object carrying every deterministically resolvable field with provenance.
- An unresolved field list with blocking status per field.
- A short-circuit flag recording whether the model tier was invoked.

**Quality Checkpoints**:

- Every envelope field is frozen before the first model call; a deployment in which a model call precedes envelope population halts.
- Budget fields derive from policy in every execution path; a budget asserted in the request body is ignored and the attempt is logged.
- Requests fully resolved deterministically bypass the model tier, and the bypass rate is reported.

***

#### Step 2.2: Invoke the Model Tier for Open-Vocabulary Requirement Inference

**Required Actions**:

- Invoke the model tier only for fields the deterministic pass left unresolved, supplying the request text, the unresolved field list, and the closed capability class vocabulary at the pinned taxonomy version.
- Constrain the model to emit a structured response naming 1 to 5 required capability classes and 0 to 5 optional classes, each with a demanded proficiency level, a necessity label, a source span, and a confidence value.
- Reject deterministically every emitted identifier absent from the pinned vocabulary, and never substitute the nearest available class for a rejected identifier; a rejected identifier makes the field unresolved, not approximate.
- Reject any emitted value that contradicts a frozen envelope field, record the contradiction with both values, and retain the envelope value.
- Cap model-tier invocation at 1 call per request under normal operation and at 2 calls where a targeted clarification returned new information, and treat a third call as a budget breach that terminates extraction.
- Record the model identifier, prompt version, decoding settings, taxonomy version, and full response on the decision record, so that a change in extraction behaviour is attributable to a named bundle.
- Emit an unmatched-demand event carrying the request fingerprint where the model produces no admissible identifier, and pass control to the no-eligible-handler path rather than routing on a guess.

**Required Outputs**:

- A completed requirement object with inferred fields carrying confidence and source spans.
- A rejection record naming every emitted identifier the vocabulary refused and every contradiction with a frozen field.
- An unmatched-demand event where inference produced no admissible identifier.

**Quality Checkpoints**:

- Zero capability class identifiers outside the pinned vocabulary reach the requirement object.
- No inferred value survives where it contradicts a frozen envelope field; the contradiction is recorded in every such case.
- Model-tier invocations per request do not exceed 2; a third invocation terminates extraction with a budget-breach reason code.

***

#### Step 2.3: Measure Requirement Specificity and Repair Extraction Defects

**Required Actions**:

- Execute a dry-run eligibility count against the capability index before ranking, returning only the size of the qualified set and the per-constraint elimination counts.
- Classify the requirement as under-specified where the qualified set exceeds 8 handlers or 25 percent of the eligible handler population, whichever is smaller, and record the constraint fields that eliminated no candidate.
- Classify the requirement as over-specified where the qualified set is empty and at least 1 handler failed on exactly 1 hard constraint whose provenance is inferred or default, and record that constraint as the single blocking field.
- Repair an under-specified requirement by promoting a discriminating optional class to required only where the request text supports the promotion, or by asking 1 targeted clarification within the clarification budget; never repair it by selecting arbitrarily from an oversized set.
- Repair an over-specified requirement by re-evaluating the single blocking inferred or default field against the request text, and by removing it only where its provenance is inferred or default; a blocking field with envelope provenance is never removed and the request proceeds to the no-eligible-handler path.
- Bound repair at 1 cycle per request: a requirement still under-specified or over-specified after 1 repair proceeds to Phase 3 as it stands, with the specificity verdict recorded on the decision record.

**Requirement Specificity Bands and Actions**:

| Qualified set size | Band | Action | Escalation on second occurrence |
| :-- | :-- | :-- | :-- |
| 0 with 1 liftable inferred blocker | Over-specified | Re-evaluate the single blocking field | Route to no-eligible-handler path |
| 0 with no liftable blocker | Genuinely unserved | Emit no-eligible-handler outcome | Coverage-gap record to the directory |
| 1 to 8, at most 25 percent of population | Well-specified | Proceed to eligibility matching | Not applicable |
| Above 8 or above 25 percent of population | Under-specified | Promote a class or clarify once | Proceed with the verdict recorded |
| Equal to the full eligible population | Vacuous | Halt extraction, raise an extraction defect | Suspend the extraction bundle |

**Required Outputs**:

- A specificity verdict per request with the qualified set size and per-constraint elimination counts.
- A repair record naming the field promoted, clarified, or removed, and its provenance.
- An extraction defect record where the requirement eliminates no candidate at all.

**Quality Checkpoints**:

- Every requirement carries a specificity verdict before ranking begins.
- Zero envelope-provenance constraints are removed by repair in any execution path.
- Repair cycles per request do not exceed 1; a second cycle is a defect and the verdict is recorded instead.

***

### Phase 3: Eligibility Matching Against Declared Capabilities

**Objective**: Reduce the handler population to those that satisfy every hard constraint under a pinned snapshot, recording a four-valued verdict per candidate and constraint so that every exclusion is explainable.

#### Step 3.1: Retrieve the Authorized Candidate View Under a Pinned Snapshot

**Required Actions**:

- Issue one lookup to the expertise directory carrying the competence requirement and the scope qualifiers, and pin the returned directory snapshot identifier on the decision record.
- Complete all matching for one request against a single pinned snapshot; where the snapshot changes mid-decision, either finish under the pin and re-authorize at dispatch, or restart within the attempt budget, and never combine fields drawn from two snapshots.
- Apply the caller's permitted disclosure scope before any candidate is enumerated, so that a handler the principal may not see never appears in a candidate list or an exclusion reason visible to that principal.
- Filter out handlers whose runtime health state is unavailable, draining, suspended, or circuit-open, recording the health generation and its observation timestamp, and never treat liveness as evidence of competence.
- Record the candidate count at three stages, before policy filtering, after policy filtering, and after health filtering, so that a collapse in candidates is attributable to a named stage.
- Refuse to proceed where the lookup response carries no snapshot identifier, since a decision that cannot name its snapshot cannot be reproduced or audited.

**Required Outputs**:

- A pinned candidate view carrying directory entries with credibility, credited level, freshness state, and evidence references.
- A three-stage candidate count with the health generation and its timestamp.
- A disclosure-scoped exclusion list carrying reason codes.

**Quality Checkpoints**:

- Every decision record names exactly 1 directory snapshot identifier.
- Candidates outside the caller's disclosure scope appear in no list returned to that caller, including exclusion lists.
- Health state is consumed as an eligibility filter and never as a competence signal; a deployment that ranks on liveness is misconfigured.

***

#### Step 3.2: Evaluate Hard Constraints to a Four-Valued Verdict

**Required Actions**:

- Evaluate constraints in a fixed order for every candidate: policy and scope predicates first, then required capability class membership, then proficiency level comparison, then credibility floor, then schema, modality, capacity, and protocol compatibility, then deadline and cost feasibility, then freshness.
- Record for every candidate and every applicable constraint one verdict from the closed set pass, fail, unknown, or not applicable, together with the observed value, the required value, the evidence reference, and a reason code.
- Terminate evaluation for a candidate at its first fail, recording the failing constraint, so that evaluation cost is bounded and the exclusion reason is unambiguous.
- Treat a missing declared field, an evidence reference the directory cannot resolve, and a value past its hard freshness limit as unknown rather than as fail, so that a repairable gap is distinguishable from a genuine mismatch.
- Exclude every candidate carrying at least 1 unknown on an applicable hard constraint from the qualified set, and record it separately from candidates excluded on fail, since the two carry different remedies.
- Compute the qualified set as the conjunction of pass verdicts across every applicable hard constraint, and refuse to admit any candidate for which a required capability class was not evaluated.

**Candidate Qualification Record**:

```
DECISION_ID:              SNAPSHOT_ID:           REQUIREMENT_HASH:
CANDIDATE: handler_id / entry_version_id / credited_level / credibility
VERDICTS: [
  constraint_id / pass | fail | unknown | not_applicable
  observed_value / required_value / operator
  evidence_ref / reason_code
]
FIRST_FAIL:               constraint_id | none
UNKNOWN_COUNT:            integer
QUALIFIED:                true | false
FRESHNESS_STATE:          current | provisional | lapsed
EVALUATION_LATENCY_MS:
```

**Required Outputs**:

- A per-candidate qualification record carrying a verdict for every applicable constraint.
- A qualified set containing only candidates whose applicable constraints all returned pass.
- Two separated exclusion lists, one for fail and one for unknown, each with reason codes.

**Quality Checkpoints**:

- Policy and scope predicates are evaluated before any capability comparison in every execution path.
- Zero candidates enter the qualified set carrying an unknown verdict on an applicable hard constraint.
- Every candidate in the qualified set has an explicit pass recorded for every required capability class; an unevaluated required class halts the decision.

***

#### Step 3.3: Apply Freshness Demotion and Lapse Exclusion

**Required Actions**:

- Read the freshness state the directory attached to each entry rather than recomputing staleness locally, since the staleness bounds, evidence half-lives, and lapse thresholds are the directory's declared property of the capability class volatility and not of the router.
- Exclude from the qualified set every entry the directory marked lapsed, recording the exclusion with the lapse reason, because a lapsed entry is not a weaker claim but an expired one.
- Demote rather than trust every entry the directory marked provisional, applying a credibility multiplier of 0.50 to that entry's contribution to the rank score, and recording the demotion on the decision record.
- Prohibit any provisional entry from being selected for a requirement whose risk class is high; where the qualified set for a high risk requirement contains only provisional entries, treat the set as empty and proceed to the no-eligible-handler path.
- Where the qualified set for a low or medium risk requirement contains only provisional entries, dispatch is permitted, and the router must raise an out-of-band re-verification request to the directory naming the entries relied upon.
- Never advance an entry's verification timestamp on the basis of a routing event, a dispatch, or a successful execution, since none of those is a verification of the claim and the directory owns that field.

**Required Outputs**:

- A qualified set with lapsed entries excluded and provisional entries demoted.
- A demotion record naming each provisional entry, its multiplier, and its elapsed interval.
- Re-verification requests raised for every provisional entry actually dispatched to.

**Quality Checkpoints**:

- Zero lapsed entries appear in any qualified set.
- Zero high risk requirements are served by a provisional entry in any execution path.
- No routing event writes to any directory freshness field; the router's writes to the directory are outcome records alone.

***

### Phase 4: Ranking the Qualified Set Under Fit, Credibility, and Load

**Objective**: Order the qualified set by a versioned, reproducible score that accounts for coverage, demonstrated competence, and current load, so that the best-matching handler does not become a bottleneck or a single point of failure.

#### Step 4.1: Compute the Fit and Credibility Components

**Required Actions**:

- Compute required-class fit as 1.00 for every member of the qualified set, since conjunctive eligibility has already established full required coverage, and record it as a constant rather than as a discriminator.
- Compute optional-class coverage as the count of optional capability classes the handler is credited with at or above the demanded level, divided by the total count of optional classes in the requirement object, returning 1.00 where the requirement object names no optional class.
- Compute level headroom as the mean, across required classes, of the difference between credited level and demanded level, divided by 3, clamped to the range 0.00 to 1.00, so that a handler credited well above the demand ranks above one credited exactly at it.
- Compute the fit component as 0.60 times optional-class coverage plus 0.40 times level headroom, and record both inputs so that a fit value is decomposable.
- Compute the credibility component as the minimum credibility across the required capability classes, not the mean, so that a handler weak on one required class cannot be rescued by strength on another, then multiply by 0.50 where the entry is provisional.
- Attach the uncertainty interval and sample count the directory supplied to every credibility value used, and mark any component computed from fewer than 10 adjudicated outcomes as low-evidence.

**Required Outputs**:

- A fit component per candidate with optional coverage and level headroom recorded separately.
- A credibility component per candidate computed as the minimum across required classes.
- A low-evidence flag on every component derived from fewer than 10 adjudicated outcomes.

**Quality Checkpoints**:

- Credibility aggregates by minimum across required classes in every execution path; a deployment using the mean is misconfigured and halts promotion of its weight vector.
- Every fit value is reproducible from its two recorded inputs.
- Every candidate carries an uncertainty interval and a sample count alongside its credibility component.

***

#### Step 4.2: Apply the Load and Concentration Penalties

**Required Actions**:

- Read utilization per candidate as in-flight work divided by declared concurrency limit, require an observation timestamp and an expiry on the value, and treat a utilization observation older than 30 seconds as expired.
- Treat an expired or absent utilization observation as 0.50 rather than as 0.00, so that a handler whose load signal has gone missing is not preferred over one that reports honestly.
- Compute the load penalty as the quantity utilization minus 0.60, divided by 0.40, clamped to the range 0.00 to 1.00, so that no penalty applies below 60 percent utilization and the full penalty applies at 100 percent.
- Exclude from the qualified set, rather than penalise, any candidate whose utilization is at or above 0.95, whose circuit is open, or whose declared queue depth exceeds the requirement object's deadline at the handler's observed service rate, and record the exclusion as a capacity fail.
- Compute dispatch share per candidate as the count of requests for the same capability class dispatched to that handler over the trailing 1,000 dispatches for the class, divided by 1,000, and apply an additional concentration penalty of 0.15 where dispatch share exceeds 0.40.
- Block selection of any candidate whose dispatch share for the class exceeds 0.60 while at least 1 other eligible candidate exists, dispatch to the next ranked candidate, and record a concentration block event; where no other eligible candidate exists, dispatch and record a bus-factor-1 dependency instead.

**Rank Score Components and Their Numeric Rules**:

| Component | Default weight | Range | Numeric rule | Behaviour on missing value |
| :-- | :-- | :-- | :-- | :-- |
| Fit | 0.35 | 0.00 to 1.00 | 0.60 times optional coverage plus 0.40 times level headroom | Optional coverage 1.00 where no optional class is named |
| Credibility | 0.30 | 0.00 to 1.00 | Minimum credibility across required classes, times 0.50 if provisional | Candidate is ineligible, not defaulted |
| Load headroom | 0.20 | 0.00 to 1.00 | 1.00 minus the load penalty, where load penalty is (utilization minus 0.60) divided by 0.40, clamped | Utilization assumed 0.50 when the observation is expired or absent |
| Cost and latency headroom | 0.15 | 0.00 to 1.00 | Normalised remaining margin against the requirement object's ceiling and deadline | Treated as 0.00, never as full headroom |
| Concentration penalty | Subtracted | 0.00 or 0.15 | 0.15 subtracted where trailing dispatch share for the class exceeds 0.40 | Share assumed 0.00 below 200 recorded dispatches |

**Required Outputs**:

- A load penalty per candidate with the utilization value, its timestamp, and its expiry state.
- A dispatch share per candidate over the trailing 1,000 dispatches for the capability class.
- Capacity exclusions and concentration block events recorded with reason codes.

**Quality Checkpoints**:

- Load never creates eligibility and never removes a hard-constraint failure; it enters the score and the capacity exclusion only.
- Every candidate at or above 0.95 utilization is excluded rather than penalised in every execution path.
- No candidate above 0.60 dispatch share for a class is selected while another eligible candidate exists.

***

#### Step 4.3: Resolve the Ranking and Break Ties Deterministically

**Required Actions**:

- Compute the rank score as the weighted sum of fit, credibility, load headroom, and cost and latency headroom under the pinned weight vector, then subtract the concentration penalty, and clamp the result to the range 0.00 to 1.00.
- Record every component value, the weight vector version, and the normalisation window on the decision record, so that a selection is reconstructable without re-running the request.
- Apply the declared tie-break sequence in order wherever the top two rank scores differ by less than 0.02, terminating in the stable handler identifier so that ordering is total.
- Require a separation margin of at least 0.05 between the top-ranked and second-ranked candidate for high risk requirements; below that margin, apply the tie-break sequence and record a low-margin selection, and where the requirement's risk class demands it, route to human review instead of dispatching.
- Flag as a low-confidence selection any top-ranked candidate whose credibility component is marked low-evidence, and require either a bounded verification probe or human approval before dispatch for high risk requirements.
- Prohibit any resampling loop that re-runs extraction or ranking in search of a preferred winner; ranking executes exactly once per requirement object and snapshot pair.

**Required Outputs**:

- An ordered qualified set with per-candidate component values and the weight vector version.
- A selection record naming the top-ranked handler, the runner-up, and the separation margin.
- A low-margin or low-confidence flag where the declared thresholds are breached.

**Quality Checkpoints**:

- The same requirement object against the same snapshot yields the same ordered qualified set in every run.
- Every high risk selection carries either a separation margin of at least 0.05 or a recorded human review disposition.
- Ranking executes exactly once per requirement object and snapshot pair; a second execution is a defect.

***

### Phase 5: Dispatch and the No-Eligible-Handler Outcome

**Objective**: Convert the ranking into exactly one terminal outcome, either a bound and re-authorized dispatch or an explicit non-selection that names its reason and its destination.

#### Step 5.1: Re-Authorize and Bind the Selected Handler

**Required Actions**:

- Re-authorize the selected handler against current policy at dispatch time using the authenticated principal, the target resource, the action, the purpose, the data scope, the effect class, the tenant, and the region, and treat the eligibility verdict computed during matching as insufficient on its own.
- Re-check the pinned snapshot against the current directory state, and where the selected entry has been superseded, invalidated, or lapsed since pinning, discard the selection and re-enter Phase 3 within the attempt budget.
- Bind the dispatch to the selected entry version, the handler deployment identity, the requirement object hash, an idempotency key, the remaining deadline, and the remaining cost ceiling, and record the binding before invocation.
- Issue a short-lived, audience-restricted, least-privilege credential scoped to the approved operation alone, and never pass an ambient or broad credential to the handler on the grounds that it holds the required capability.
- Obtain explicit confirmation before dispatching any request whose effect class is destructive, externally visible, or irreversible, and record the confirming principal and timestamp.
- Emit exactly one dispatch per request; a request that produces two dispatches without an approved hedging or composition contract is a defect that halts the router.

**Required Outputs**:

- An authorization verdict recorded at dispatch time, distinct from the eligibility verdict.
- A dispatch binding naming entry version, deployment identity, idempotency key, and residual budgets.
- A credential scope identifier recorded on the decision record, never the credential itself.

**Quality Checkpoints**:

- Every dispatch carries an authorization verdict evaluated at dispatch time, not one carried forward from matching.
- Zero credentials recorded in telemetry; only the credential scope identifier appears.
- Exactly 1 dispatch is emitted per request in the absence of an approved hedging or composition contract.

***

#### Step 5.2: Emit the No-Eligible-Handler Outcome Explicitly

**Required Actions**:

- Treat an empty qualified set as a terminal routing outcome in its own right, carrying a reason code, the requirement object hash, the snapshot identifier, the full exclusion list with per-candidate first-fail constraints, and a named escalation destination.
- Classify the reason deterministically into one member of a closed set, distinguishing no handler credited with a required class, all credited handlers ineligible on policy or scope, all credited entries lapsed, all credited handlers at capacity, and requirement unresolved.
- Prohibit substitution absolutely: no dispatch may be made to the handler that failed the fewest constraints, to the highest-credibility handler in an unrelated class, or to a general-purpose handler in the absence of a credited entry for every required class.
- Offer only preapproved degradations, each naming the specific requirement it relaxes, its expected impact, and whether fresh consent is required, and never relax a policy, authorization, residency, effect, or safety constraint under any degradation.
- Where the reason is no credited handler, write a coverage-gap record naming the capability class and the request fingerprint, and deliver it to the expertise directory, since the population gap is directory health information the router observes and the directory remedies.
- Where the reason is all lapsed, raise an out-of-band re-verification request to the directory and state the expected time to a usable answer rather than returning silence.
- Bound the escalation: where empty-set outcomes for one capability class exceed 2 percent of lookups over a 7-day window, raise a warning, and where they exceed 5 percent, raise exactly 1 catalogue-revision request rather than continuing to escalate case by case.

**No-Eligible-Handler Reason Codes and Destinations**:

| Reason code | Detection rule | Default destination | Directory feedback emitted |
| :-- | :-- | :-- | :-- |
| no_credited_handler | Capability index returns 0 entries for a required class | Directory steward queue; named human role at high risk | Coverage-gap record naming the class |
| all_ineligible_on_policy | Every candidate first-failed a policy or scope predicate | Policy owner queue | None; the population is adequate |
| all_lapsed | Every candidate excluded on lapse | Directory steward queue | Re-verification request per entry |
| all_at_capacity | Every candidate excluded at utilization 0.95 or above | Operations queue | Concentration and bus-factor report |
| requirement_unresolved | Extraction produced no admissible identifier | Requester clarification, then human review | Unmatched-demand event |
| below_credibility_floor | Every candidate credited below the risk class floor | Named human role | Coverage-gap record naming the class |

**No-Eligible-Handler Escalation Record**:

```
DECISION_ID:            SNAPSHOT_ID:          REQUIREMENT_HASH:
OUTCOME:                no_eligible_handler
REASON_CODE:            one of the closed set
RISK_CLASS:             low | medium | high
REQUIRED_CLASSES:       [ capability_class_id, demanded_level ]
EXCLUSIONS: [ handler_id, first_fail_constraint_id, reason_code ]
DEGRADATION_OFFERED:    level | none        CONSENT_STATE:
DESTINATION:            queue or named role
DIRECTORY_FEEDBACK:     coverage_gap | reverification | unmatched_demand | none
UNMET_DEMAND_SHARE_7D:  value per capability class
```

**Required Outputs**:

- A no-eligible-handler outcome record with reason code, exclusions, and destination.
- A coverage-gap record or re-verification request delivered to the directory as the reason code dictates.
- A catalogue-revision request where the 7-day unmet demand threshold is breached.

**Quality Checkpoints**:

- Zero requests terminate in a dispatch to a handler that failed a hard constraint.
- Every no-eligible-handler outcome names both a reason code and a destination; an outcome without a destination is a defect, not a fallback.
- Unmet demand above 5 percent for a single capability class over 7 days produces exactly 1 catalogue-revision request rather than repeated identical escalations.

***

#### Step 5.3: Execute Bounded Recovery Within the Attempt Budget

**Required Actions**:

- Retry a failed dispatch only where the failure is transient, the operation is idempotent or safely deduplicated, and the attempt budget permits, capping retries at 2 per request.
- Fail over only to a candidate that passed the same hard constraints under the same pinned snapshot, and never to a candidate that was excluded, since availability recovery must not become a capability downgrade.
- Maintain a visited set across attempts and stop on any of: repeated failure from the same reason code, an open circuit, an authorization denial, a superseded entry version, a deadline breach, a cost ceiling breach, or the attempt limit.
- Cap total recovery cost at 30 percent of the requirement object's cost ceiling and total recovery latency at 25 percent of its deadline, and terminate to the no-eligible-handler path where either cap is reached.
- Emit a composition proposal, rather than a dispatch, where no single candidate covers every required class but a set of candidates jointly does, and hand the proposal to the planning discipline with the per-class candidate lists attached.
- Terminate every request in exactly one of five outcomes: dispatched, degraded and dispatched, composition proposed, escalated as no-eligible-handler, or abstained, and record which.

**Required Outputs**:

- A recovery trace naming every attempt, its handler, its reason code, and the residual budget after it.
- A composition proposal with per-class candidate lists where joint coverage exists.
- Exactly 1 terminal outcome per request, drawn from the closed set of 5.

**Quality Checkpoints**:

- Retries per request do not exceed 2, and no failover targets a candidate excluded under the pinned snapshot.
- Recovery consumes no more than 30 percent of the cost ceiling and 25 percent of the deadline.
- Every request carries exactly 1 terminal outcome; a request with 0 or 2 recorded outcomes is a defect that halts the router.

***

### Phase 6: Outcome Verification and Directory Feedback

**Objective**: Establish whether the routing decision was right using observed outcomes, attribute failures to the correct layer, and return competence and coverage evidence to the directory rather than accumulating it inside the router.

#### Step 6.1: Verify the Result Against the Requirement Object

**Required Actions**:

- Validate the returned result against the requirement object's output contract, checking schema conformance, required outcome fields, declared effects, provenance, and policy compliance before the result is released to the requester.
- Adjudicate task success by a deterministic acceptance test where one exists, by an independent verifier where it does not, and by a named human reviewer for high risk classes, and record which method was used.
- Require independence of the verifier from the handler, meaning a different model, prompt, retrieval corpus, provider, and premise set, and record any dependency that could not be removed, since agreement between dependent sources is not corroboration.
- Record the adjudicated verdict, the capability classes the work actually exercised, and whether the work was completed by the credited competence rather than by a shortcut or by a different competence entirely.
- Mark as unadjudicated every outcome for which no acceptance test, verifier, or reviewer produced a verdict, and exclude unadjudicated outcomes from every downstream credibility or correctness computation.
- Sample at least 2 percent of confidently successful routed requests for random audit in addition to all failures, since reviewing only failures misses confident systematic misrouting.

**Required Outputs**:

- A contract validation record per completed request with per-field verdicts.
- An adjudicated outcome record naming the method, the verifier, and its independence status.
- A random audit sample of at least 2 percent of confident successes.

**Quality Checkpoints**:

- Zero unadjudicated outcomes reach any credibility or correctness computation.
- Every high risk outcome carries a named human reviewer or an independent verifier with recorded independence status.
- The random audit sample meets or exceeds 2 percent of confidently successful requests in every reporting window.

***

#### Step 6.2: Attribute the Failure to the Correct Layer

**Required Actions**:

- Separate routing correctness from task success in every report, since a correct selection can fail in execution and an incorrect selection can succeed by accident, and a single blended score cannot locate which layer failed.
- Classify every failed request into exactly 1 layer from a closed set: extraction, where the requirement object misstated the demand; matching, where an eligible handler existed and was not selected; directory, where the entry that authorised the candidate was wrong; ranking, where an eligible handler was selected but a materially better one was available; dispatch, where authorization or binding failed; and execution, where the selected handler was competent and still failed.
- Attribute a misroute to the directory rather than to the router where the selected handler was credited with every required class at the demanded level and nonetheless lacked the competence, and deliver the adjudicated outcome to the directory so its credibility gate can act.
- Attribute a misroute to extraction where the adjudicated required class set differs from the extracted one, and record the specific class added or removed, since this is the dominant failure mode of the method.
- Compute routing correctness on the labelled corpus as the proportion of requests whose selected handler falls within the adjudicated acceptable set, reported per capability class with sample counts and never aggregated across classes without them.
- Deliver every adjudicated outcome to the directory as an outcome record naming the entry version relied upon, the decision identifier, the verdict, and the independence status, and write nothing to the directory's credibility fields directly.

**Required Outputs**:

- A failure attribution per failed request naming exactly 1 layer.
- Routing correctness and task success reported separately, per capability class, with sample counts.
- Outcome records delivered to the directory carrying entry version, decision identifier, verdict, and independence status.

**Quality Checkpoints**:

- Zero reports blend routing correctness and task success into one figure.
- Every failed request carries exactly 1 attributed layer; a request with 0 or 2 attributions is returned for adjudication.
- The router writes no credibility value to the directory in any execution path; it delivers outcome records only.

***

#### Step 6.3: Report Coverage Gaps, Concentration, and Weight Drift

**Required Actions**:

- Aggregate coverage-gap records, unmatched-demand events, and below-floor outcomes into 1 ledger keyed by proposed or existing capability class, and deliver it to the directory on a cadence no longer than 7 days.
- Compute served concentration as a Herfindahl-Hirschman index over handler shares of dispatched requests, flag above 0.25, and block weight vector changes that would raise it above 0.40, matching the thresholds the directory applies to its own health audit so that the two measurements are comparable.
- Report every capability class whose bus factor is 1 alongside the count of dispatches that depended on it in the window, since a single point of failure carrying heavy traffic is a different exposure from one carrying none.
- Replay the last 30 days of decision records against any proposed weight vector, taxonomy version, or matching semantics change, and report the proportion of decisions whose selected handler changes; require human approval above 5 percent and block activation above 20 percent without a named accountable owner.
- Recalibrate the weight vector only through the replay gate, never by online adjustment on live traffic, and version every activated vector with the replay report that justified it.
- Prohibit closing a concentration finding by lowering a credibility floor or by weakening a hard constraint; the admissible remedies are cultivating a second eligible handler, decomposing an over-broad capability class, or accepting the exposure with a named owner.

**Required Outputs**:

- A coverage-gap ledger delivered to the directory at least every 7 days.
- A concentration report with the served index, per-class bus factors, and dependent dispatch counts.
- A replay report per proposed configuration change stating the proportion of decisions that change.

**Quality Checkpoints**:

- Coverage-gap reporting reaches the directory within 7 days of the gap being observed.
- Zero weight vector changes activate without a replay report over at least 30 days of decision records.
- No concentration finding is closed by adjusting a credibility floor or relaxing a hard constraint.

***

## III. Implementation Guidance for AI Agents

AI agents operating a capability router must follow systematic protocols ensuring that every dispatch is traceable to a pinned snapshot, that every non-selection is explicit, and that no model output reaches a decision without deterministic validation. The following guidance translates the framework above into agent-executable instructions.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Routing Supervisor Agent**: Owns the routing configuration, holds the matching semantics declaration and the weight vector version, enforces the best-effort prohibition at every handoff, and authorises activation of a new configuration. Requires read access to the effective layer, write access to the routing configuration store, and no dispatch authority of its own.
2. **Requirement Extraction Agent**: Populates envelope and derived fields deterministically, invokes the model tier only for unresolved fields, validates every emitted identifier against the pinned taxonomy, and computes the specificity verdict. Requires the closed capability vocabulary, the request envelope, and a bounded model call budget of 2 per request.
3. **Eligibility Matching Agent**: Issues the directory lookup, pins the snapshot, evaluates hard constraints to four-valued verdicts, and produces the qualified set with separated fail and unknown exclusion lists. Requires read access to the effective layer and to the policy engine, and holds no write authority anywhere.
4. **Ranking Agent**: Computes fit, credibility, load, and concentration components under the pinned weight vector, applies the tie-break sequence, and emits the ordered qualified set with a separation margin. Requires the utilization feed, the dispatch share window, and the weight vector version.
5. **Dispatch Agent**: Re-authorizes at dispatch time, binds entry version, deployment identity, idempotency key, and residual budgets, issues the least-privilege credential, and executes bounded recovery. Holds the only dispatch authority in the system.
6. **Escalation Agent**: Emits no-eligible-handler outcomes with reason codes and destinations, delivers coverage-gap records and re-verification requests to the directory, and raises catalogue-revision requests at the declared thresholds. Requires write access to the escalation queues and to the directory's feedback interface only.
7. **Feedback and Audit Agent**: Adjudicates outcomes, attributes failures to layers, computes routing correctness and concentration, and runs the replay gate on proposed configuration changes. Holds no authority to activate a configuration.

**Workflow Execution Pattern**:

```
STATE: Phase_3_Eligibility_Matching
ACTIONS:
  1. Issue directory lookup, pin snapshot_id
  2. Apply disclosure scope, then policy, then health filters
  3. Evaluate hard constraints in declared order per candidate
  4. Record four-valued verdict, stop candidate at first fail
  5. Exclude lapsed entries, demote provisional entries by 0.50
VALIDATION:
  - snapshot_id_present == TRUE
  - unknown_verdicts_in_qualified_set == 0
  - required_class_pass_recorded_for_all_qualified == TRUE
  - high_risk_requirement_served_by_provisional == FALSE
TRANSITIONS:
  IF qualified_set_size >= 1 THEN next_state = Phase_4_Ranking
  IF qualified_set_size == 0 THEN next_state = Phase_5_No_Eligible_Handler
  IF snapshot_changed_during_evaluation THEN next_state = Phase_3_Restart
  ELSE next_state = Phase_3_Error_Handling
```

**Two-Phase Action Pattern**:

1. **Qualify**: Establish the qualified set by conjunction, with no scoring performed and no ranking artifact created.
2. **Validate**: Confirm that every qualified candidate carries a pass on every required class and that no unknown survives, while the decision is still reversible.
3. **Rank and dispatch**: Score only the validated qualified set, then dispatch exactly one selection or emit exactly one non-selection.

**Approval Gate**:

Human authorisation is required before any of the following: activating a weight vector, taxonomy version, or matching semantics change whose replay alters more than 5 percent of the last 30 days of decisions; dispatching a high risk requirement whose only eligible candidates are provisional or low-evidence; dispatching where the top-two separation margin is below 0.05 on a high risk requirement; and accepting any degradation that changes the requested effect class. Below these triggers agents proceed autonomously and record the disposition.

**Context Management Requirements**:

- Load the capability index by capability class identifier rather than enumerating the full effective layer, so that context consumption scales with the requirement object and not with the handler population.
- Hold one pinned snapshot per request and discard it at the terminal outcome; never carry a snapshot across requests.
- Record decision records to durable storage as they are produced, so that an interrupted run loses at most 1 request's decision.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Vocabulary Integrity (After Phase 1)**

- **Automated Check**: Every capability class identifier the router can emit exists in the pinned taxonomy version; rank weights sum to exactly 1.00; the tie-break sequence terminates in a stable identifier; zero competence facts are stored outside the directory.
- **Agent Action on Pass**: Activate the configuration and admit requests.
- **Agent Action on Failure**: Halt activation and return the failing identifiers or the weight sum, with no partial activation permitted.
- **Human Review Trigger**: Any proposed vocabulary change that removes a capability class currently referenced by more than 1 percent of the last 30 days of decisions.

**Checkpoint 2: Extraction Specificity (After Phase 2)**

- **Automated Check**: Every requirement object carries a specificity verdict; every inferred field carries confidence and a source span; zero envelope fields were overwritten by inference; model-tier invocations per request do not exceed 2.
- **Agent Action on Pass**: Proceed to eligibility matching.
- **Agent Action on Failure**: Return the request to extraction for exactly 1 repair cycle, then proceed with the verdict recorded.
- **Human Review Trigger**: Under-specified or over-specified verdicts exceeding 10 percent of requests over a 24-hour window, which indicates an extraction bundle defect rather than request variance.

**Checkpoint 3: Qualification Soundness (After Phase 3)**

- **Automated Check**: Exactly 1 snapshot identifier per decision; zero unknown verdicts inside the qualified set; every qualified candidate carries a recorded pass for every required class; zero lapsed entries present; zero high risk requirements served by provisional entries.
- **Agent Action on Pass**: Proceed to ranking.
- **Agent Action on Failure**: Halt the request and emit an error outcome; a qualification defect is never resolved by proceeding to ranking on a partial set.
- **Human Review Trigger**: Unknown-verdict exclusions exceeding 15 percent of candidate opportunities for any capability class over 7 days, which indicates missing directory evidence rather than handler unsuitability.

**Checkpoint 4: Ranking Reproducibility (After Phase 4)**

- **Automated Check**: The ordered qualified set is byte-identical on re-execution against the same snapshot and requirement hash; every component value and the weight vector version are recorded; no candidate above 0.60 dispatch share was selected while another eligible candidate existed.
- **Agent Action on Pass**: Proceed to dispatch.
- **Agent Action on Failure**: Halt and report the non-reproducible component, since a router that cannot reproduce its own ordering cannot be audited.
- **Human Review Trigger**: Low-margin selections, defined as a top-two separation below 0.05, exceeding 20 percent of high risk requests over 7 days.

**Checkpoint 5: Terminal Outcome Integrity (After Phase 5)**

- **Automated Check**: Exactly 1 terminal outcome per request from the closed set of 5; zero dispatches to candidates carrying a fail verdict; every no-eligible-handler outcome names a reason code and a destination; zero credentials present in telemetry.
- **Agent Action on Pass**: Release the result and emit telemetry.
- **Agent Action on Failure**: Halt the router for the affected capability class; a dispatch to an ineligible candidate is an incident, not a degradation.
- **Human Review Trigger**: Any single occurrence of a dispatch to a candidate carrying a fail verdict, and any capability class whose no-eligible-handler share exceeds 5 percent over 7 days.

**Checkpoint 6: Feedback Completeness (After Phase 6)**

- **Automated Check**: Zero unadjudicated outcomes in correctness computations; every failed request carries exactly 1 attributed layer; coverage-gap records delivered within 7 days; the random audit sample meets 2 percent of confident successes.
- **Agent Action on Pass**: Publish the reporting window and deliver the ledger to the directory.
- **Agent Action on Failure**: Withhold the reporting window and name the missing adjudications rather than reporting on partial coverage.
- **Human Review Trigger**: Adjudication coverage below 60 percent of completed requests for any high risk capability class over 30 days.

**Aggregate Release Threshold**:

A routing configuration is releasable only where all 6 checkpoints pass and the following hold on the sealed evaluation corpus: routing correctness at or above 0.85 per capability class with at least 30 labelled requests per class; misroute rate at or below 0.02; dispatches to ineligible candidates exactly 0; and no-eligible-handler outcomes correctly classified into their reason codes at or above 0.90. A configuration missing any of these is not released, and the shortfall is reported with its measured value rather than waived.

### C. Error Handling and Troubleshooting

**Error Type 1: Under-Specified Requirement Matching Too Many Handlers**

- **Symptoms**: The qualified set repeatedly equals or approaches the full eligible population; per-constraint elimination counts show constraint fields that eliminate no candidate; routing correctness is low while task success is high, because any handler could do the work.
- **Diagnostic Steps**: Inspect the per-constraint elimination counts for fields with zero eliminations across the window; compare the extracted required class set against the adjudicated set on the labelled corpus; check whether the taxonomy's classes are broader than the demands the traffic makes.
- **Resolution Protocol**: Option A, promote a discriminating optional class to required where the request text supports it, and re-run extraction once. Option B, ask 1 targeted clarification within the clarification budget, then re-extract. Option C, raise a taxonomy request to decompose the over-broad capability class, since a class that everyone holds discriminates nothing.
- **Escalation Trigger**: Under-specified verdicts exceeding 10 percent of requests over 24 hours, or any single request whose qualified set equals the full eligible population, which suspends the extraction bundle.

**Error Type 2: Over-Specified Requirement Matching Nothing**

- **Symptoms**: Empty qualified sets accompanied by exclusion lists in which most candidates first-failed on the same constraint; that constraint's provenance is inferred or default rather than envelope; no-eligible-handler share rises without any change to the handler population.
- **Diagnostic Steps**: Identify the single most frequent first-fail constraint over the window and read its provenance distribution; re-run the affected requests with that field removed and compare qualified set sizes; confirm the demanded proficiency level against the adjudicated demand.
- **Resolution Protocol**: Option A, re-evaluate the single blocking inferred field against the request text and remove it where the text does not support it. Option B, lower the demanded proficiency level to the adjudicated level where the extraction inflated it. Option C, where the blocking field has envelope provenance, accept the empty set and emit the no-eligible-handler outcome, since the constraint is trusted and the population genuinely cannot serve the request.
- **Escalation Trigger**: The same inferred constraint blocking more than 5 percent of requests over 7 days, which suspends that field's inference rule pending review.

**Error Type 3: Stale or Lapsed Declaration Relied Upon**

- **Symptoms**: Misroutes concentrated on handlers whose entries carry old verification timestamps; adjudicated failures on classes where credibility remains high; provisional entries appearing in high risk qualified sets.
- **Diagnostic Steps**: Join misroutes to the freshness state recorded on the decision record; check whether the demotion multiplier was applied; verify that no routing event advanced a directory verification field; confirm the directory's lapse exclusions reached the router.
- **Resolution Protocol**: Option A, apply the 0.50 demotion multiplier at evaluation time rather than relying on a scheduled directory job, so that a missed job cannot produce an undemoted score. Option B, raise out-of-band re-verification requests for every provisional entry dispatched to, and suspend high risk dispatch on those classes until the directory clears them. Option C, treat the class as uncovered and emit no-eligible-handler outcomes, which is preferable to a confident dispatch on expired evidence.
- **Escalation Trigger**: Any high risk dispatch to a provisional entry, and effective-layer staleness above 5 percent for any class, which halts dispatch for that class.

**Error Type 4: Concentration on a Single Best-Matching Handler**

- **Symptoms**: Dispatch share for one handler exceeds 0.40 on a capability class; the served concentration index exceeds 0.25; latency degrades under load while alternative eligible handlers sit idle; a single handler's withdrawal would empty a large share of qualified sets.
- **Diagnostic Steps**: Compute per-class dispatch share and the served index over the trailing window; check whether the load penalty is being computed from expired utilization observations defaulted to 0.00 rather than 0.50; identify classes whose bus factor is 1 and their dependent dispatch counts.
- **Resolution Protocol**: Option A, verify and repair the utilization feed, since a missing load signal disables the penalty that prevents concentration. Option B, apply the concentration penalty and the 0.60 dispatch share block, dispatching to the next ranked eligible candidate. Option C, report the bus-factor-1 exposure to the directory with a named accountable owner, since cultivating a second eligible handler is a directory remedy and not a routing one.
- **Escalation Trigger**: Served concentration index above 0.40, or bus-factor-1 classes exceeding 15 percent of the referenced catalogue, which blocks weight vector changes until the exposure is owned.

**Error Type 5: Best-Effort Fallback to an Ineligible Handler**

- **Symptoms**: Dispatches recorded against candidates carrying a fail verdict; no-eligible-handler share near zero in a population that cannot plausibly cover all demand; misroutes whose selected handler was never credited with a required class.
- **Diagnostic Steps**: Join every dispatch to its candidate qualification record and count dispatches whose selected handler carries a first-fail constraint; inspect the code path that constructs the ranking input for any use of the exclusion list.
- **Resolution Protocol**: Option A, halt the router for the affected capability class immediately, since this defect produces confident wrong answers rather than visible failures. Option B, rebuild the ranking input from the qualified set alone and add an assertion that the ranking input and the exclusion list are disjoint. Option C, where the fallback was configured deliberately, remove the configuration and record the removal, since a best-effort fallback is not a permitted operating mode.
- **Escalation Trigger**: Any single occurrence, which is an incident rather than a rate, and which halts the affected capability class without retry.

**Error Type 6: Model-Tier Identifier Invention**

- **Symptoms**: Extraction emits capability class identifiers absent from the pinned taxonomy; rejection records rise after a model or prompt change; unmatched-demand events rise without a change in traffic.
- **Diagnostic Steps**: Compare the rejected identifier set against the taxonomy's deprecation map to distinguish invention from staleness; check whether the prompt enumerates the current vocabulary; confirm the bundle version recorded on the decision record.
- **Resolution Protocol**: Option A, refresh the vocabulary enumeration supplied to the model and re-run extraction once. Option B, apply the deprecation map where the identifier is an obsolete form rather than an invention. Option C, roll back to the previously certified extraction bundle and record the rollback, since an extraction bundle that invents identifiers cannot be repaired at match time.
- **Escalation Trigger**: Rejected identifiers exceeding 5 percent of emitted identifiers over 24 hours, which suspends the extraction bundle and reverts to the last certified one.

**Troubleshooting Decision Tree**:

```
ROUTING OUTCOME IS WRONG
├─ NO HANDLER WAS SELECTED
│   ├─ Qualified set empty, blocker is inferred → Re-evaluate the field once, then escalate
│   ├─ Qualified set empty, blocker is envelope → Emit no_eligible_handler with destination
│   ├─ Every candidate lapsed → Request re-verification, state time to answer
│   └─ Every candidate at capacity → Operations queue, report concentration
├─ THE WRONG HANDLER WAS SELECTED
│   ├─ Selected candidate carried a fail verdict → HALT class, rebuild ranking input
│   ├─ Extracted class set differs from adjudicated → Attribute to extraction, repair bundle
│   ├─ Entry was credited but incompetent → Attribute to directory, deliver outcome record
│   └─ Better eligible candidate existed → Attribute to ranking, run the replay gate
├─ TOO MANY HANDLERS QUALIFIED
│   ├─ A constraint eliminated nothing → Promote a class or clarify once
│   └─ Qualified set equals population → Suspend extraction bundle
└─ THE SAME HANDLER TAKES EVERYTHING
    ├─ Utilization feed expired → Repair feed, default utilization to 0.50
    ├─ Dispatch share above 0.60 with alternatives → Block and dispatch next ranked
    └─ Bus factor equals 1 → Report exposure to the directory with a named owner
```

### D. Performance Metrics and Continuous Learning

Every metric below carries an explicit denominator, because a routing figure without a population is uninterpretable. Report the time window, the traffic slice, the taxonomy version, the weight vector version, the directory snapshot range, and the label coverage alongside every quality metric.

**Matching Quality Metrics**:

- **Qualification precision**: Candidate opportunities the router marked eligible that adjudication confirms were eligible, divided by all labelled candidate opportunities the router marked eligible (target: at or above 0.90 per capability class).
- **Qualification recall**: Truly eligible candidate opportunities the router marked eligible, divided by all labelled truly eligible candidate opportunities (target: at or above 0.85 per capability class).
- **Routing correctness**: Requests whose selected handler falls within the adjudicated acceptable set, divided by labelled requests that had at least 1 acceptable handler (target: at or above 0.85, reported per class with at least 30 labelled requests).
- **Misroute rate**: Dispatched requests reaching a handler lacking a required class at the demanded level, divided by dispatched requests with known outcomes (target: at or below 0.02).
- **Ineligible dispatch count**: Dispatches to a candidate carrying a fail verdict, counted absolutely (target: exactly 0; any occurrence is an incident).

**Outcome and Coverage Metrics**:

- **No-eligible-handler share**: Requests terminating with an empty qualified set, divided by all requests (monitoring metric, with a warning at 0.02 and a catalogue-revision request at 0.05 per capability class over 7 days).
- **Reason code accuracy**: No-eligible-handler outcomes whose recorded reason code matches adjudication, divided by adjudicated no-eligible-handler outcomes (target: at or above 0.90).
- **Coverage-gap delivery latency**: Median elapsed time from a coverage gap being observed to its record reaching the directory (target: at or below 7 days).
- **Extraction specificity rate**: Requests receiving a well-specified verdict, divided by all requests reaching the specificity check (target: at or above 0.90).
- **Task success by capability class**: Known-outcome requests in the class satisfying the terminal contract, divided by known-outcome dispatched requests in the class (reported separately from routing correctness, never blended).

**Operational and Fairness Metrics**:

- **Served concentration index**: Herfindahl-Hirschman index over handler shares of dispatched requests (warning at 0.25, blocking at 0.40).
- **Bus-factor-1 class share**: Capability classes with exactly 1 eligible handler, divided by classes the router referenced in the window (warning at 0.10, blocking at 0.15).
- **Routing overhead share**: Router latency and cost from requirement processing start to validated selection, divided by the median end-to-end cost of the handlers selected among (target: at or below 0.10).
- **Adjudication coverage**: Completed requests carrying an adjudicated verdict, divided by completed requests (target: at or above 0.60 for high risk classes).
- **Replay stability**: Proportion of the last 30 days of decisions whose selected handler is unchanged under a proposed configuration (human approval below 0.95, blocking below 0.80 without a named owner).

**Learning and Adaptation Mechanisms**:

- **Feedback direction**: Observed outcomes update the expertise directory's credibility through its own gate; they never update a router-local competence estimate, because a router that learns competence privately becomes a second, unaudited directory.
- **Configuration learning**: The router's own learning is confined to the weight vector, the tie-break sequence, and the extraction bundle, each changed only through the replay gate with a recorded justification.
- **Corpus maintenance**: Add every adjudicated misroute, every no-eligible-handler outcome, and every under-specified or over-specified verdict to the labelled corpus, and refresh at least 20 percent of the corpus per quarter so that it tracks current traffic rather than founding traffic.
- **Sealed holdout discipline**: Maintain a sealed final holdout partition never used for tuning, and open it only for release decisions, recording each opening.

***

## IV. Domain-Agnostic Application Guidance

The framework is designed for generalisability across any setting in which work must reach a competent handler and the handler population is larger than one. Its procedure does not depend on the nature of the work, only on the existence of declared capabilities and adjudicable outcomes.

### 4.1 Cross-Domain Application Patterns

**Clinical care coordination**: Capability classes name procedures, specialties, licensure scopes, language competence, and equipment dependencies. Required-class conjunction is non-negotiable because a partially credentialed clinician is not a partial match but an ineligible one, and the no-eligible-handler outcome is the referral. Proficiency levels map to credentialing tiers, credibility floors are set at the high risk value of 0.80 for any class with an irreversible effect, and staleness bounds follow credential expiry rather than router preference. Concentration reporting matters more than ranking refinement, because a single credentialed holder for a class is a service continuity exposure.

**Regulated financial operations**: Capability classes name instrument types, jurisdictions, authorisation limits, and reconciliation competences. Policy and scope predicates dominate eligibility and are evaluated first, so most exclusions occur before any capability comparison. Cost ceilings and deadlines are contractual rather than advisory, and degradation is almost always prohibited, so the no-eligible-handler outcome routes to a named human role rather than to a relaxed dispatch. Audit reconstruction from the decision record is the binding requirement, which makes snapshot pinning and component recording non-optional.

**Industrial field service and maintenance**: Capability classes name equipment families, certifications, tool availability, and site access. Load is a physical constraint rather than a soft preference, so the utilization exclusion at 0.95 corresponds to a technician's committed schedule, and geographic containment is a hard constraint evaluated before capability. Dispatch share caps prevent one qualified technician absorbing every request for a rare equipment family, which is both a burnout risk and a bus-factor exposure.

**Public-sector casework**: Capability classes name benefit programmes, language competence, accessibility accommodations, and delegated decision authority. Fairness of distribution across caseworkers is a stated objective, so the concentration penalty carries greater weight than in throughput-oriented settings. The no-eligible-handler outcome is a documented coverage gap with statutory consequences, which makes reason code accuracy and escalation destination correctness the primary quality metrics.

**Software incident response**: Capability classes name systems, runtimes, data stores, and remediation authorities. Freshness bounds are short because tool access and system ownership change frequently, so provisional demotion is the common case rather than the exception. Composition proposals are frequent, since an incident often requires several competences that no single responder holds, and the boundary against planning is exercised on most severe incidents.

### 4.2 Scale, Risk, and Population Adaptation

- **Small populations** (fewer than 10 handlers): Reduce the under-specification upper bound from 8 to 3 handlers, since 8 candidates from a population of 10 discriminates nothing. Expect bus factor 1 on most classes and report it rather than attempting to rank around it. The concentration penalty has little room to operate and should be reported rather than enforced.
- **Large populations** (more than 200 handlers): Retrieve candidates by capability class index rather than by full enumeration, cap the retrieved candidate set at 50 before constraint evaluation, and order retrieval by credibility so that truncation removes the weakest candidates first. Report the truncation on the decision record, since a truncated candidate view can produce a false no-eligible-handler outcome.
- **High risk work**: Raise the credibility floor to 0.80, prohibit provisional entries entirely, require a top-two separation margin of at least 0.05, and route every low-margin or low-evidence selection to human review. Prohibit degradation without fresh consent.
- **Low latency budgets**: Bypass the model tier wherever deterministic population resolves every required field, cache the capability index by class identifier with the snapshot in the key, and cap routing overhead at 10 percent of the median handler cost. Never reduce latency by skipping eligibility evaluation.
- **Sparse outcome data**: Where fewer than 10 adjudicated outcomes exist for a class, mark every credibility component low-evidence, widen the human review trigger to all high risk selections in that class, and prioritise the class in the directory's re-verification queue rather than tuning weights on noise.

***

## V. Limitations and Considerations

**Requirement extraction is the dominant failure mode**: The method's accuracy is bounded by the quality of the requirement object, and the requirement object is produced partly by open-vocabulary inference. An under-specified requirement leaves the whole population eligible and reduces routing to an arbitrary pick; an over-specified one empties the qualified set and produces a false coverage gap that misdirects directory investment. Mitigation is the specificity measurement in Step 2.3, which makes the defect visible before ranking rather than after adjudication, together with the bounded single repair cycle and the escalation triggers at 10 percent under-specification and 5 percent single-field blocking.

**Declared capability is a claim, not a demonstration**: A handler credited from a declaration, a manifest, or a benchmark result may not hold the competence on the traffic the router actually sends. The source guide states, citing research on agent benchmark protocol validity that was retrieved and confirmed during this conversion, that a benchmark supports a capability claim only where success still requires the intended capability, and that agents may exploit public solutions, leakage, or alternate paths that invalidate the inference. The consequence is confident misrouting that presents as task failure rather than as routing failure. Mitigation is structural rather than internal to the router: eligibility reads only the directory's effective layer, whose evidence hierarchy places observed outcomes above declared capability above self-assessment, and the router returns adjudicated outcomes so that credibility tracks demonstrated rather than asserted competence.

**Every threshold in this guide is a deployment default**: The credibility floors of 0.50, 0.65, and 0.80; the load penalty knee at 0.60 utilization and exclusion at 0.95; the dispatch share penalty at 0.40 and block at 0.60; the weight vector of 0.35, 0.30, 0.20, and 0.15; the qualified set bounds of 1 to 8; the separation margin of 0.05; and the demotion multiplier of 0.50 are operable defaults chosen for first deployment, not measured findings. The consequence of treating them as evidence is misplaced confidence in a tuned system. Mitigation is the replay gate in Step 6.3, which requires 30 days of decision records and a stated change proportion before any of them moves, and the requirement that every activated vector carries the replay report that justified it.

**Load signals are stale by construction**: Utilization is observed at one moment and consumed at another, and a handler's load can change materially within the observation window. The consequence is a ranking that penalises a handler that has already drained or favours one that has already filled. Mitigation is the 30-second expiry, the deliberate assumption of 0.50 rather than 0.00 for expired observations so that a missing signal is not rewarded, and the hard capacity exclusion at 0.95 which does not depend on fine-grained accuracy.

**Conjunctive matching under-serves composable work**: Requiring one handler to hold every required class produces empty qualified sets wherever the population is specialised and the request is broad, even though a set of handlers could jointly serve it. The consequence is a no-eligible-handler outcome that overstates the coverage gap. Mitigation is the composition proposal outcome in Step 5.3, which detects joint coverage and hands it to the planning discipline, and the requirement that composition proposals be reported separately from genuine coverage gaps so that directory investment is not misdirected.

**Concentration remedies are organisational, not algorithmic**: The load and concentration penalties redistribute work among handlers that already exist; they cannot create a second competent handler where only one exists. The consequence is that a bus factor of 1 persists through every ranking adjustment and is made worse by any attempt to fix it inside the router. Mitigation is the explicit prohibition on closing a concentration finding by lowering a credibility floor, and the requirement that bus-factor-1 exposure be reported to the directory with a named accountable owner, where the admissible remedies of cultivating a second handler or decomposing an over-broad class actually live.

**The router inherits every directory error**: A wrong entry produces a wrong dispatch that the router cannot detect at match time, because the router has no independent view of competence and is prohibited from building one. The consequence is that directory accuracy caps routing accuracy. Mitigation is the failure attribution in Step 6.2, which separates directory error from matching error so that remediation reaches the correct layer, and the delivery of adjudicated outcomes to the directory's credibility gate rather than to a router-local store.

**Every quality number is bounded by adjudication coverage**: Routing correctness, qualification precision, and misroute rate are computed only over requests whose outcome was adjudicated, and adjudication is expensive. The consequence is that a favourable metric may describe an unrepresentative slice. Mitigation is the mandatory reporting of label coverage alongside every quality metric, the 2 percent random audit of confident successes which prevents review from concentrating on failures, and the 60 percent adjudication coverage trigger for high risk classes.

**Source claims transcribed without independent re-verification**: The external claims in this guide are drawn from the originating prose source. Two were retrieved and confirmed during conversion: the agent benchmark protocol validity paper and the tool specification stating that servers declare a tools capability with a list-change notification and that clients must treat tool annotations from untrusted servers as untrusted. The remainder, including the protocol, standards, resilience, and evaluation references in Section VII, are carried as the source stated them. The consequence is that a dated or misattributed claim in the source propagates here. Mitigation is that no operational threshold in this guide depends on an unverified external claim; the thresholds are defaults declared above, and the external references support framing rather than arithmetic.

***

## VI. Conclusion and Summary

Capability routing is a filtering discipline before it is a ranking discipline. Its correctness is carried by the conjunction over required capability classes and by the refusal to let any score, preference, or load signal compensate for a failed hard constraint. Its usability is carried by the requirement object, which is where the method most often fails, and by the specificity measurement that makes that failure visible before a handler is chosen rather than after the work has gone wrong.

The two decisions that most distinguish a sound router from an unsound one are both refusals. The first is the refusal to dispatch to the least badly ranked ineligible handler when nothing qualifies, which converts a silent misroute into an explicit outcome carrying a reason code, a destination, and coverage-gap evidence the handler population owes an answer to. The second is the refusal to trust a declaration that has outlived its verification window, which is handled by demotion rather than by exclusion for low and medium risk work and by exclusion for high risk work.

Ranking exists to choose among handlers that are already known to be competent, and its principal job beyond fit is to prevent the best-matching handler from becoming the only handler. The load and concentration rules give that job numeric form, and the reporting path returns concentration and coverage findings to the expertise directory, where the remedies actually live.

**Key Success Factors**:

- **Conjunction before score**: A handler missing a required capability class at the demanded level is ineligible, and no ranking arithmetic ever reaches it.
- **Measured specificity**: Every requirement object carries a specificity verdict before matching, because an unmeasured requirement fails silently in both directions.
- **Explicit non-selection**: The no-eligible-handler outcome is a terminal result with a reason code and a destination, never a fallback to whichever handler ranked least badly.
- **Demotion over trust**: A declaration past its staleness bound is demoted by a stated multiplier and barred from high risk work, and a lapsed one is excluded outright.
- **Load in the rank, not in the gate**: Utilization and dispatch share penalise and exclude on capacity, and never create eligibility or excuse a failed constraint.
- **Feedback to the directory, not to the router**: Observed outcomes update credibility where the evidence hierarchy governs it, so the router never becomes a second, unaudited record of who can do what.

By following this guide, AI agents can convert arriving requests into explicit capability demands, dispatch only to handlers credited with meeting them, and surface the gaps in the handler population as reportable evidence rather than as confident mismatches.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, and were not independently re-verified during conversion except where an entry is marked as retrieved and confirmed. Two entries were retrieved during conversion and are marked accordingly; the remainder reproduce the source's titles and locations rather than checking them.

**Corpus pointers**:

- `Robust Capability Routing: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the capability declaration layers, the hard, soft, and unknown constraint trichotomy, the four-valued constraint verdict, the qualified-set-before-scoring rule, the no-qualified-candidate and degradation ordering, the composition and planning boundary, the denominator-explicit metric definitions, and the twelve-step runtime flow. Its registry, descriptor publication, ontology, and provider lifecycle material is not carried here, since the expertise directory guide named below owns it.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_TransactiveMemory.md` — the expertise directory discipline that supplies this guide's input. Owns the capability taxonomy and directory schema, the evidence hierarchy placing observed outcomes above declared capability above self-assessment, the three capability layers and their promotion gate, credibility arithmetic and its update gate, staleness bounds with decay and re-verification, and the concentration, bus-factor, and coverage-gap health audit. It states the lookup contract this guide consumes and explicitly declines to specify a router; the terminology used here for capability class, directory entry, effective layer, credibility, freshness state, mutual ignorance, bus factor, and coverage gap is taken from it unchanged.
- `advanced_task_guides/routing/guide_RuleBasedRouting.md` — the deterministic sibling, covering verified routing tables with total coverage, hit policies, default-deny posture, and a reversible change path. It owns every destination derivable from trusted structured fields, which capability routing runs after rather than duplicates.
- `advanced_task_guides/routing/guide_LLMBasedRouting.md` — the model-based sibling, covering constrained model routing under a versioned destination registry, closed destination vocabularies, calibrated routing confidence, and selective prediction. Its constrained-decoding and vocabulary-validation discipline applies to the model-tier requirement extraction in Step 2.2.
- `advanced_task_guides/routing/guide_EmbeddingBasedRouting.md` — the sibling routing method deciding by calibrated nearest-exemplar similarity under a pinned embedding generation. It selects on semantic proximity to curated exemplars where this guide selects on declared and evidenced capability, and the two are alternatives rather than composable stages.
- `advanced_task_guides/routing/guide_ContentBasedRouting.md` — the sibling routing method deciding by bounded inspection of payload contents. Its extraction phase is one source of the requirement fields Phase 2 here consumes; a declared capability is never inferred from payload text.

**External references**:

*Capability declaration and agent protocols*

1. A2A Project, *A2A Agent Skills and Agent Card* — https://a2a-protocol.org/latest/tutorials/python/3-agent-skills-and-card/
2. A2A Project, *A2A specification* — https://github.com/a2aproject/A2A/blob/main/docs/specification.md
3. Model Context Protocol, *MCP tools specification* — https://modelcontextprotocol.io/specification/2025-06-18/server/tools — retrieved and confirmed during conversion; the page states that servers supporting tools must declare a `tools` capability carrying an optional `listChanged` property, and that clients must consider tool annotations untrusted unless they come from trusted servers.
4. Model Context Protocol, *MCP lifecycle* — https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle
5. Model Context Protocol, *MCP ToolAnnotations* — https://csharp.sdk.modelcontextprotocol.io/api/ModelContextProtocol.Protocol.ToolAnnotations.html
6. Model Context Protocol, *MCP security best practices* — https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices
7. Invariant Labs, *Invariant Labs tool-poisoning analysis* — https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks

*Interface contracts, constraint evaluation, and workload identity*

8. OpenAPI Initiative, *OpenAPI Specification 3.1.1* — https://spec.openapis.org/oas/v3.1.1.html
9. JSON Schema, *JSON Schema validation specification* — https://json-schema.org/draft/2020-12/json-schema-validation
10. Google, *Google OR-Tools constraint optimization* — https://developers.google.com/optimization/cp
11. IETF, *RFC 8707* — https://datatracker.ietf.org/doc/html/rfc8707
12. SPIFFE, *SPIRE concepts* — https://spiffe.io/docs/latest/spire-about/spire-concepts/
13. SPIFFE, *SPIFFE workload registration* — https://spiffe.io/docs/latest/deploying/registering/

*Load, tail latency, resilience, and staged release*

14. Google Research, *The Tail at Scale* — https://research.google/pubs/the-tail-at-scale/
15. Microsoft, *Microsoft Circuit Breaker pattern* — https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
16. Google SRE, *Google SRE canary guidance* — https://sre.google/workbook/canarying-releases/

*Capability evidence, evaluation, and telemetry*

17. Shao and colleagues, *Do Agent Benchmarks Measure Capability? Protocol Validity in the Age of Agentic AI* — https://arxiv.org/html/2607.22368v1 — retrieved and confirmed during conversion; the source guide cited this work by its short title alone, and the full title and identifier were checked against the page.
18. Google Research, *Model Cards for Model Reporting* — https://research.google/pubs/model-cards-for-model-reporting/
19. NIST, *NIST Generative AI Profile* — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
20. NIST, *NIST AI measurement and evaluation* — https://www.nist.gov/ai-measurement-and-evaluation
21. OpenTelemetry, *OpenTelemetry GenAI attributes* — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
