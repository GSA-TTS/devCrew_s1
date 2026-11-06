# Transactive Memory Systems

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Transactive memory constitutes the task family of building and maintaining the group-level structure by which a multi-agent system knows which agent knows what, so that an arriving query is routed to a competent holder rather than answered by whichever component received it. Its subject is metaknowledge: a governed directory of expertise, not a store of facts. This guide provides AI agents with a structured protocol for declaring a capability taxonomy and directory schema, populating entries from declared capability and observed outcome, serving lookups that return scored candidate holders with their supporting evidence, updating credibility from adjudicated results, decaying and re-verifying claims whose validity window has elapsed, and auditing directory health for concentration and coverage gaps. It specifies an evidence hierarchy in which observed task outcomes outrank declared capability and declared capability outranks self-assessment, a hard rule that an entry carrying no evidence never enters the routable layer, numeric staleness bounds that demote rather than trust unconfirmed claims, and explicit escalation wherever no holder is credited with a needed competence. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that the directory remains an accurate model of the team rather than a fossil of its founding assumptions.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Transactive memory system**: A team-level mechanism that maintains, and acts on, a mapping from classes of work to the holders capable of performing them. It is distinguished from a content store by its subject: it records where competence resides, not what is known.

**Metaknowledge**: Knowledge about the location and reliability of knowledge. The directory is metaknowledge; the artifacts the holders produce are not.

**Expertise directory**: The governed store of directory entries, their evidence, their validity windows, and their version history. It is the single artifact this guide produces and maintains.

**Holder**: Any addressable entity a unit of work can be assigned to: an agent instance, an agent class, a model endpoint, a tool, a data service, a queue worker, or a named human role. Holder type is recorded because credibility arithmetic differs across types.

**Capability class**: A named, stable unit of competence against which evidence accumulates. A capability class is defined by positive examples, counterexamples, required inputs, an output contract, an acceptance test, and a risk class.

**Capability taxonomy**: The versioned controlled vocabulary of capability classes, together with mappings from deprecated terms to current ones.

**Directory entry**: A versioned assertion that one holder possesses one capability class, carrying a credibility score, an evidence set, a validity window, and a layer assignment. An entry is a hypothesis under maintenance, not a fact.

**Evidence class**: The category of support behind an assertion, drawn from a closed vocabulary: observed outcome, controlled test, administrator assignment, provider declaration, peer endorsement, and self-assessment.

**Credibility**: A scalar in the range 0.00 to 1.00 estimating the probability that the holder satisfies the capability class's acceptance test on a task of stated difficulty, carried with an uncertainty interval and a sample count.

**Declared layer**: What a holder or its provider claims. Declarations generate candidate entries and never authorize a route on their own.

**Observed layer**: Summaries of adjudicated outcomes under named cohorts, stratified by capability class, holder version, difficulty, and tenant.

**Effective layer**: The policy-approved subset of entries that lookup may return. Promotion into this layer is gated; the declared layer is never served directly.

**Validity window**: The interval, expressed as `valid_from` and `expires_at`, during which an entry may be served. An entry outside its window is lapsed regardless of its credibility score.

**Staleness bound**: The maximum elapsed time since `last_verified_at` beyond which an entry is demoted. It is a property of the capability class's volatility, not of the holder.

**Lapsed entry**: An entry past its validity window or beyond twice its staleness bound. Lapsed entries are excluded from lookup results and retained for audit.

**Unevidenced entry**: An entry whose evidence set is empty. Unevidenced entries are rejected at write time and never reach the effective layer.

**Competence requirement**: The set of capability classes an arriving query needs, produced by interpreting the query rather than by matching its surface text.

**Lookup**: The directory operation that accepts a competence requirement and returns a ranked candidate set with credibility, evidence references, and eligibility verdicts. Lookup selects nothing; it supplies the input a router selects from.

**Concentration**: The degree to which credited competence is held by few holders, measured across the capability catalogue and across served lookups.

**Bus factor**: The count of credible eligible holders for one capability class. A bus factor of 1 is a single point of failure.

**Mutual ignorance**: The condition in which no holder is credited above the credibility floor for a needed capability class. It is a directory state that must produce an explicit escalation, never a routed guess.

**Coverage gap**: A capability class present in observed task demand but absent from the taxonomy or absent from the effective layer.

**Adjudicated outcome**: A task result whose success or failure was determined by a deterministic acceptance test, an independent verifier, or a named human reviewer. Unadjudicated results never update credibility.

**Independence**: The property that a verifier does not share the model, prompt, retrieval corpus, provider, or premise set of the holder it verifies. Agreement between dependent sources is not corroboration.

### 1.2 The Evidence Hierarchy and the Three Capability Layers

The primary failure mode of a transactive memory system is a directory entry asserted without evidence. A system that believes a holder is expert at something it cannot do will route that work to it indefinitely, because a wrong route produces a failure attributed to the task rather than to the directory. The evidence hierarchy exists to make that belief expensive to hold.

**The hierarchy**: Observed task outcomes rank above declared capability, and declared capability ranks above self-assessment. A holder's own claim about its competence is the weakest admissible evidence class, because it is generated by the same component whose competence is in question and carries no independent test.

**Evidence Classes and Their Admissibility**:

| Evidence class | Default weight | Minimum sample for observed grade | Highest layer it alone can reach |
| :-- | :-- | :-- | :-- |
| Adjudicated production outcome | 0.60 | 10 outcomes | Effective, all risk classes |
| Controlled capability test | 0.25 | 5 held-out tasks | Effective, low and medium risk |
| Administrator assignment | 0.20 | Not applicable | Effective, ownership-defined classes only |
| Provider or card declaration | 0.10 | Not applicable | Declared |
| Peer endorsement | 0.05 | 3 independent endorsers | Declared |
| Self-assessment | 0.05 | Not applicable | Declared |

**Combination rule**: Credibility is the weight-normalised sum of the per-class evidence estimates, computed as the sum over admitted classes of class weight times class estimate, divided by the sum of admitted class weights. Weights are renormalised over classes actually present, so an entry supported only by declaration does not receive an artificially low score; instead the layer cap constrains it. Any entry whose admitted evidence excludes both adjudicated outcome and controlled test is capped at credibility 0.35 and may not be promoted to the effective layer. This cap, not the arithmetic, is what prevents a confident self-report from acquiring a routable score.

**Layer separation**: The declared layer holds what was claimed, with its claimant, timestamp, and scope. The observed layer holds cohort-stratified outcome summaries. The effective layer holds the policy-approved entries lookup may serve. Movement is one-directional and gated: a declaration generates a candidate, a controlled test or accumulated outcomes generates an observed summary, and an approval gate promotes the pair into the effective layer. No path exists from declaration directly to effective.

**Version binding**: Every evidence item is bound to the holder version that produced it, identified by model identifier, prompt or policy version, tool set hash, and data-source set. Evidence produced under one version is discounted to 0.25 of its weight when the holder's version changes, because competence is a property of the configured system, not of its name.

### 1.3 The Execution Tier Partition

The directory is a deterministic artifact operated with model assistance at two narrow points. Assigning each unit of work to a tier is what separates a maintainable directory from a set of opinions about agents.

**Deterministic tier**: Software, schema validators, scheduled jobs, and queries own the directory store and all arithmetic performed on it. The deterministic tier owns the entry store and its version history; the evidence ledger, including admissibility checks and version binding; credibility arithmetic, including weighting, normalisation, uncertainty intervals, and update clamping; staleness evaluation against validity windows and volatility classes; decay application; concentration and coverage metrics; eligibility filtering by tenant, purpose, data class, region, and scope; and the lookup operation itself. These require exactness, reproducibility against a named directory snapshot, and auditability that model inference cannot supply. A lookup executed twice against the same snapshot with the same competence requirement must return the same candidate set in the same order.

**Model tier**: LLM calls own exactly two decisions, both open-vocabulary and neither reducible to a rule. First, interpreting an arriving query to determine which capability classes it requires, including queries that name no capability, use vocabulary absent from the taxonomy, or bundle several competences into one request. Second, judging whether a completed outcome demonstrates the competence that was claimed, which requires reading the artifact against the capability class's acceptance criteria and distinguishing a task completed by the credited competence from one completed by a shortcut, by luck, or by a different competence entirely.

**Hybrid tier**: Credibility updating is the principal hybrid operation. A model may propose a credibility update, stating the capability class, the direction, the magnitude, and the evidence it relies on. A deterministic gate applies it only after verifying that the outcome was adjudicated, that the verifier was independent of the holder, that the capability class identifier exists in the current taxonomy version, that the holder version on the evidence matches the holder version on the entry, and that the proposed magnitude is within the per-update clamp. Where the model and the gate disagree, the gate holds authority and the proposal is recorded as rejected with a reason code. Taxonomy evolution is the second hybrid operation: a model proposes new capability classes from unmatched demand, and a deterministic process admits them only where the proposed class carries an acceptance test, at least 5 observed requests, and no more than 0.80 term overlap with an existing class.

**What the model tier may never decide alone**: promotion of any entry into the effective layer; authorization or scope grants; the numeric credibility value written to the store; whether an entry has lapsed; and whether an escalation may be suppressed. Each is a deterministic evaluation over stored fields, and a model's agreement with it carries no additional weight.

### 1.4 The Directory Gate and Boundaries Against Adjacent Mechanisms

A directory is worth its maintenance cost only under specific conditions. Agents must evaluate the gate before construction and record the verdict, because an unmaintained directory is worse than no directory: it routes confidently and wrongly.

**Gate conditions**: Construct a transactive directory where at least 3 of the following hold. Holders differ materially in validated competence, tools, data access, language, jurisdiction, cost, or authority rather than in role name alone. Task classes recur at least 20 times per capability class per quarter, so evidence can accumulate. No single holder can safely or economically hold all context. Outcomes are adjudicable, so credibility has a signal to learn from. Misrouting carries a measurable cost in quality, latency, or risk.

**Suppression conditions**: Withhold the directory where holders are instances of the same model differing only by role label, since no specialization exists to record; where one holder with a governed tool catalogue can plan across the whole task within its context budget; where ownership is contractual and static, so a deterministic assignment table is cheaper and auditable; or where outcomes cannot be adjudicated, since credibility would then learn from noise. In each suppression case, record the reason and the substitute chosen.

**Boundary against distributed memory architecture**: A companion discipline governs where data lives, covering replication topology, partition keys, consistency models, staleness tokens, and conflict resolution over stored values. This guide governs who knows things and how the directory of that knowledge is built, kept accurate, and queried. The directory is itself data and may be replicated under that discipline, but the questions differ: the distributed-memory question is whether a read observed a converged value, and the transactive question is whether the value the read returned is still a true statement about a holder's competence. A directory can be perfectly consistent across every replica and uniformly wrong.

**Boundary against routing**: The directory produces a scored, evidence-bearing candidate set. A router consumes it and selects, applying load, cost, latency, deadline, parallelism, broadcast, and exploration policy that this guide does not specify. The interface between them is fixed: lookup returns candidates with credibility, uncertainty, sample count, evidence references, freshness, eligibility verdict, and a directory snapshot identifier; the router returns the selected holder and a decision identifier so the outcome can be attributed back to the entry that produced the candidate. Agents must not embed routing policy in the directory, because a directory that optimises for load stops being an accurate record of competence.

**Boundary against a tool catalogue**: A catalogue states which interfaces exist and what they accept. It is a declaration source of evidence class provider declaration, weight 0.10, and nothing more. An advertised tool is not demonstrated competence with that tool, and a holder linked to a data source is not authoritative for that source's business meaning.

**Boundary against a shared workspace**: A blackboard or shared scratchpad carries evolving problem state that many holders read and write. It answers what the team currently believes about the problem. The directory answers which holder should act next. Systems commonly need both, and conflating them produces a workspace that grows without bound and a directory that cannot be audited.

***

## II. Operational Framework: Evidence-Backed Expertise Directory Construction and Maintenance

The framework assumes the directory gate in Section 1.4 has returned construct. Phases 1 and 2 build the directory once. Phases 3 through 5 run continuously in production: Phase 3 serves lookups, Phase 4 consumes their outcomes, and Phase 5 runs on a schedule independent of traffic. Phase 6 runs on a fixed audit cadence and can force a return to Phase 1 where the taxonomy itself is found deficient.

### Phase 1: Capability Taxonomy and Directory Schema Declaration

**Objective**: Fix the vocabulary of competence and the record structure that will carry it, so that evidence accumulates against stable classes rather than against ad hoc labels no two entries share.

#### Step 1.1: Derive the Capability Taxonomy From Observed Task Demand

**Required Actions**:

- Collect a sample of at least 200 real requests spanning at least 2 full workload cycles, and cluster them by the competence each required rather than by the wording each used.
- Name each capability class with a stable identifier, and write for it positive examples, counterexamples, required inputs, an output contract, an acceptance test, a risk class, and a volatility class.
- Reject any candidate class whose acceptance test cannot be evaluated deterministically or by a named reviewer, since credibility cannot accumulate against an unjudgeable class.
- Reject any candidate class projected to receive fewer than 20 requests per quarter, and merge it into its nearest parent, since a class below that rate cannot reach the 10-outcome observed-grade minimum within one staleness bound.
- Separate reasoning competence from tool access and from data authority, recording each as its own class; the ability to read a store is not authority over the meaning of what it holds.
- Version the taxonomy, and maintain a mapping from every deprecated identifier to its replacement.

**Required Outputs**:

- A versioned capability taxonomy of 15 to 120 classes, each carrying all 7 declared attributes.
- A deprecation map from retired identifiers to current ones.
- A demand-coverage record stating what fraction of the sampled requests map to at least 1 class.

**Quality Checkpoints**:

- Every capability class carries an acceptance test that returns pass or fail without interpretation.
- Demand coverage is at least 0.90 of sampled requests; below that the taxonomy is incomplete and Phase 2 does not begin.
- No two classes overlap by more than 0.80 on their positive example sets, measured by term or embedding similarity.
- Every class carries a volatility class of stable, moderate, or volatile, which sets its staleness bound in Step 5.1.

***

#### Step 1.2: Declare the Directory Entry Schema and Its Evidence Fields

**Required Actions**:

- Declare the identity fields every entry carries: holder identifier, holder type, entry version identifier, parent entry version identifier, service version, model identifier, prompt or policy version, tool set identifier, and data-source set identifier.
- Declare the claim fields: capability class identifier, taxonomy version, scope qualifiers covering tenant, purpose, region, language, and data class, plus preconditions, exclusions, and known failure modes.
- Declare the credibility fields: credibility score, uncertainty interval, sample count, last success timestamp, last failure timestamp, and calibration error against declared confidence.
- Declare the temporal fields: `valid_from`, `expires_at`, `last_verified_at`, volatility class, and layer assignment.
- Declare the evidence fields: an evidence reference list, and per reference the evidence class, the asserting principal, the assertion timestamp, the adjudication method, the verifier identifier, the verifier independence score, and the holder version the evidence was produced under.
- Enforce at write time that an entry with an empty evidence reference list is rejected, that layer assignment is never written directly by a proposer, and that every write records a reason code and a superseded entry version.

**Directory Entry Record Template**:

```
ENTRY_VERSION_ID:
PARENT_ENTRY_VERSION_ID:
HOLDER_ID:            HOLDER_TYPE:
HOLDER_VERSION:       model / prompt / tools / data-sources
CAPABILITY_ID:        TAXONOMY_VERSION:
SCOPE:                tenant / purpose / region / language / data-class
CREDIBILITY:          value / interval / sample_count
EVIDENCE_REFS:        [ class, asserter, asserted_at, method, verifier, independence, holder_version ]
VALID_FROM:           EXPIRES_AT:
LAST_VERIFIED_AT:     VOLATILITY_CLASS:
LAYER:                declared | observed | effective
WRITE_REASON_CODE:    APPROVER_ID:
```

**Required Outputs**:

- A directory entry schema carrying all 6 field groups with types and nullability declared.
- A write-time validation rule set including the unevidenced-entry rejection.
- An append-only entry version history keyed by entry version identifier.

**Quality Checkpoints**:

- A write attempt carrying zero evidence references is rejected, and the rejection is recorded rather than silently dropped.
- Every entry version references its parent, so any served entry can be reconstructed as of any past snapshot.
- Layer assignment cannot be set by the same principal that supplied the evidence.

***

#### Step 1.3: Declare the Evidence Classes and Their Combination Rule

**Required Actions**:

- Adopt the closed evidence-class vocabulary and its default weights from Section 1.2, and record any deployment-specific weight change with its justification and effective date.
- Implement the combination rule as weight-normalised aggregation over admitted classes only, so that absent classes neither penalise nor inflate the score.
- Implement the layer cap: an entry lacking both adjudicated outcome and controlled test evidence is capped at credibility 0.35 and is ineligible for the effective layer regardless of how many declarations or endorsements it carries.
- Set the credibility floor for routable candidacy at 0.60 with at least 10 adjudicated outcomes for low and medium risk classes, and at 0.75 with at least 30 adjudicated outcomes plus at least 1 independent verification for high risk classes.
- Compute an uncertainty interval for every credibility score using a smoothed estimator rather than a raw success ratio, so that a holder with 2 successes is not ranked above one with 40 successes and 3 failures.
- Record for every holder an overclaim rate and an underclaim rate, computed as the signed difference between self-assessed and observed success, so that self-assessment can be calibrated rather than merely discounted.

**Required Outputs**:

- An evidence-class register with weights, minimum samples, and layer caps.
- A credibility computation specification producing a score, an interval, and a sample count.
- Per-holder calibration records carrying overclaim and underclaim rates.

**Quality Checkpoints**:

- No entry above credibility 0.35 lacks adjudicated outcome or controlled test evidence.
- Every credibility score is accompanied by an uncertainty interval and a sample count; a bare scalar is rejected by the store.
- Weight changes are versioned, and credibility scores computed under a prior weight version are recomputed before being served.

***

### Phase 2: Directory Population From Declaration and Controlled Outcome

**Objective**: Populate the directory so that every routable entry rests on evidence stronger than a claim, using declarations only to generate candidates and controlled tests to promote them.

#### Step 2.1: Register Holder Identities and Admit Declared Capability

**Required Actions**:

- Issue a stable identifier for every holder, bind it to a cryptographic workload identity, and record holder type, reachable endpoints, and the version tuple of model, prompt, tools, and data sources.
- Ingest declarations from every available source, including provider documentation, published capability cards, tool catalogues, administrator assignment, and holder self-assessment, and label each with its evidence class.
- Map every external skill term onto an internal capability class through the taxonomy, quarantining any term that maps to no class and forwarding it to the coverage-gap queue in Step 6.2.
- Verify the signature and endpoint ownership of every ingested capability card before its declaration is admitted, and reject unsigned cards from outside the trust boundary.
- Write every admitted declaration into the declared layer only, with `layer` set to declared and credibility left uncomputed until Step 2.2 supplies test evidence.
- Record for each self-assessment the holder's stated confidence, so Step 1.3 calibration has a claimed value to compare against.

**Required Outputs**:

- A holder register with identity, type, version tuple, and endpoint references.
- A declared-layer entry set with every declaration labelled by evidence class and asserting principal.
- A quarantine list of unmapped external skill terms.

**Quality Checkpoints**:

- Zero declared-layer entries carry a layer assignment other than declared.
- Every ingested capability card has a verified signature or is recorded as rejected with a reason code.
- Every declaration carries an asserting principal and an assertion timestamp; anonymous declarations are rejected.

***

#### Step 2.2: Promote Declared Claims Through Controlled Capability Tests

**Required Actions**:

- Build a held-out test set per capability class containing at least 5 tasks spanning the declared difficulty range, each carrying a deterministic acceptance test or a named reviewer.
- Execute the test set against every holder whose declared entry names that class, recording per task the verdict, the artifact reference, the holder version, the latency, and the cost.
- Withhold the test set from any process that generates holder prompts, instructions, or tools, and rotate at least 20 percent of it per quarter, so that test performance is not achieved by memorisation.
- Compute an observed-layer summary per holder and capability class, stratified by difficulty band, and compare it against the holder's self-assessed confidence to produce the overclaim and underclaim rates.
- Mark as refuted any declared entry whose observed test success falls below 0.40, retain it with `layer` set to declared and a refuted flag, and exclude it from further promotion until re-tested under a changed holder version.
- Record every test outcome in the evidence ledger with evidence class controlled capability test and its holder version binding.

**Required Outputs**:

- A per-class held-out test set with acceptance tests and difficulty labels.
- Observed-layer summaries carrying success rate, uncertainty interval, and sample count per holder and capability class.
- A refuted-claim list naming each declaration the tests contradicted.

**Quality Checkpoints**:

- Every holder credited with a high risk capability class has been tested on at least 5 held-out tasks in that class; untested high risk claims never reach the effective layer.
- Test set leakage checks pass, with zero overlap between held-out tasks and any task used to configure a holder.
- Overclaim rate is computed for every holder carrying at least 1 self-assessment.

***

#### Step 2.3: Publish the Effective Layer Under an Approval Gate

**Required Actions**:

- Compute credibility for each candidate pairing of holder and capability class using the Step 1.3 combination rule over its admitted evidence.
- Apply the promotion gate deterministically: promote only where credibility meets the floor for the class risk tier, the sample minimum is met, the evidence set contains at least 1 adjudicated outcome or controlled test, the validity window is open, and the entry passes eligibility filtering for at least 1 scope.
- Require named human approval before promoting any entry in a high risk class, any entry granting authority over an irreversible action, and any entry for a holder whose identity was ingested from outside the trust boundary.
- Assign each promoted entry a validity window whose `expires_at` is derived from its volatility class, and stamp `last_verified_at` with the test or outcome timestamp rather than the promotion timestamp.
- Publish an immutable directory snapshot identifier for the promoted set, so any later lookup can be replayed against the exact state that produced it.
- Retain every rejected promotion with its failing condition, so promotion pressure is visible in the Phase 6 audit rather than invisible in retries.

**Required Outputs**:

- An effective-layer entry set with credibility, interval, sample count, validity window, and scope qualifiers.
- A directory snapshot identifier covering the published set.
- A promotion decision log recording approvals, rejections, and failing conditions.

**Quality Checkpoints**:

- Zero effective-layer entries carry an empty evidence set, a credibility below the applicable floor, or a sample count below the applicable minimum.
- Every high risk effective-layer entry carries a recorded human approver identifier.
- The published snapshot is immutable, and any subsequent change produces a new snapshot identifier rather than mutating the existing one.

***

### Phase 3: Lookup, Competence Resolution, and Routing Handoff

**Objective**: Convert an arriving query into a competence requirement, return the eligible credited holders with their evidence, and hand a router a candidate set it can act on or an escalation it cannot ignore.

#### Step 3.1: Resolve the Required Competence From the Query

**Required Actions**:

- Invoke the model tier to read the query and emit a competence requirement naming 1 to 5 capability class identifiers drawn from the current taxonomy version, each with a necessity label of required or optional.
- Require the model to emit, alongside each identifier, the span of the query that motivated it and a confidence value, so that a wrong resolution is diagnosable rather than opaque.
- Validate every emitted identifier against the taxonomy deterministically, rejecting any identifier absent from the current version and any identifier the deprecation map redirects without applying the redirect.
- Where the model emits no identifier, or emits only identifiers the taxonomy rejects, record an unmatched-demand event with the query fingerprint and pass control to Step 3.3 rather than substituting the nearest available class.
- Extract the scope qualifiers deterministically from the request envelope, not from the query text: tenant, purpose, region, language, data class, and deadline.
- Record the resolution with the model identifier, prompt version, and taxonomy version, so a later change in resolution behaviour is attributable.

**Required Outputs**:

- A competence requirement record naming validated capability class identifiers with necessity labels.
- A scope qualifier set extracted from the request envelope.
- An unmatched-demand event where resolution produced no valid identifier.

**Quality Checkpoints**:

- Every emitted capability identifier exists in the current taxonomy version; invented identifiers are rejected at validation, not repaired.
- Scope qualifiers derive from the envelope; a scope value present only in query text is treated as untrusted and ignored.
- No requirement carries more than 5 required classes; beyond that the query is decomposed before lookup rather than matched loosely.

***

#### Step 3.2: Filter Eligibility and Return the Scored Candidate Set

**Required Actions**:

- Read the effective layer against a pinned directory snapshot identifier, and record that identifier on the lookup response so the decision is reproducible.
- Apply eligibility filtering deterministically and before any scoring: tenant scope, purpose allowlist, data class allowlist, region and residency, required scopes, input and output modes, capability taxonomy version compatibility, and holder health state.
- Exclude every lapsed entry, every entry outside its validity window, and every entry whose credibility falls below the floor for the class risk tier, recording each exclusion with its reason code.
- Order surviving candidates by credibility with its uncertainty interval, breaking ties by sample count and then by freshness, and return the ordering as an input rather than a decision.
- Attach to every returned candidate its credibility, uncertainty interval, sample count, `last_verified_at`, evidence class composition, eligibility verdict, and bus factor for the class.
- Emit a lookup response carrying zero candidates as an explicit empty result with a reason distinguishing no credited holder, all credited holders ineligible, and all credited holders lapsed.

**Lookup Response Contract**:

```
LOOKUP_ID:                DIRECTORY_SNAPSHOT_ID:
COMPETENCE_REQUIREMENT:   [capability_id, necessity]
SCOPE:                    tenant / purpose / region / language / data-class
CANDIDATES: [
  HOLDER_ID / ENTRY_VERSION_ID
  CREDIBILITY / INTERVAL / SAMPLE_COUNT
  LAST_VERIFIED_AT / FRESHNESS_STATE
  EVIDENCE_COMPOSITION / ELIGIBILITY_VERDICT
]
EXCLUSIONS:  [holder_id, exclusion_reason_code]
BUS_FACTOR:  per capability_id
EMPTY_REASON: none | no_credited_holder | all_ineligible | all_lapsed
```

**Required Outputs**:

- A lookup response carrying candidates, exclusions, bus factor, and a snapshot identifier.
- An exclusion record naming every filtered holder and its reason code.
- An empty-result classification where no candidate survives.

**Quality Checkpoints**:

- Eligibility filtering precedes scoring in every execution path; a candidate that failed a scope predicate never appears in a ranked list.
- The same competence requirement against the same snapshot returns an identical ordered candidate set.
- Every returned candidate carries a non-empty evidence composition; a candidate without one indicates directory corruption and halts the lookup.

***

#### Step 3.3: Escalate Explicitly Where the Directory Has No Answer

**Required Actions**:

- Treat an empty candidate set as mutual ignorance and raise an explicit escalation carrying the competence requirement, the empty reason, the snapshot identifier, and the excluded holders with their reasons.
- Prohibit substitution: agents must not route to the nearest semantically similar holder, to the highest-credibility holder in an unrelated class, or to a general-purpose holder in the absence of a credited entry.
- Route the escalation to the destination declared for the class risk tier, defaulting to a named human role for high risk classes and to the directory steward queue otherwise, and record the destination with the escalation.
- Where the empty reason is all lapsed, trigger an out-of-band re-verification request under Phase 5 and state the expected time to a usable answer rather than returning silence.
- Where the empty reason is no credited holder, write a coverage-gap record naming the capability class and the query fingerprint, feeding the Phase 6 audit.
- Bound the escalation: if unmet demand for one capability class exceeds 5 percent of lookups over a 7-day window, raise a catalogue-revision request rather than continuing to escalate case by case.

**Required Outputs**:

- An escalation record with requirement, empty reason, snapshot identifier, destination, and exclusion list.
- A coverage-gap record per uncredited capability class.
- A catalogue-revision request where the unmet-demand threshold is breached.

**Quality Checkpoints**:

- Zero lookups terminate in a routed holder that carried no credited entry for a required capability class.
- Every escalation names a destination and a class risk tier; an escalation without a destination is a defect, not a fallback.
- Unmet demand above 5 percent of lookups for any single class over 7 days produces exactly 1 catalogue-revision request rather than repeated identical escalations.

***

### Phase 4: Credibility Update From Observed Outcome

**Objective**: Convert completed work into directory evidence, so that credibility tracks demonstrated competence rather than the assumptions under which the entry was first written.

#### Step 4.1: Capture the Outcome Record and Adjudicate the Verdict

**Required Actions**:

- Capture for every completed unit of work the lookup identifier, the directory snapshot identifier, the entry version identifier of the candidate that was selected, the holder version at execution time, the capability classes claimed, the artifact references, and the consumed budget.
- Adjudicate the verdict through a deterministic acceptance test where the capability class supplies one, through an independent verifier where it does not, and through a named human reviewer for high risk classes.
- Compute a verifier independence score for every adjudication, scoring 0.00 where the verifier shares the holder's model, prompt, retrieval corpus, and provider, and 1.00 where it shares none of them.
- Reject as inadmissible any verdict sourced from user satisfaction alone, from agreement with another holder scoring below 0.50 independence, or from the holder's own assessment of its output.
- Label the outcome with a difficulty band drawn from the capability class's declared range, so that success on trivial instances does not raise credibility as much as success on hard ones.
- Record refusals, timeouts, clarification requests, and schema failures as distinct outcome classes rather than collapsing them into failure, because they carry different implications for credibility.

**Required Outputs**:

- An outcome record joined to the lookup, snapshot, entry version, and holder version that produced it.
- An adjudication verdict with method, verifier identifier, and independence score.
- An outcome class label drawn from the closed vocabulary of succeeded, failed, refused, timed out, clarification required, and schema invalid.

**Quality Checkpoints**:

- Every outcome record resolves to exactly 1 entry version, so credibility is attributed to the claim that was actually served.
- Zero credibility-bearing outcomes carry an independence score below 0.50 without a named human reviewer attached.
- Refusals and timeouts are separable from substantive failures in every downstream aggregation.

***

#### Step 4.2: Judge Whether the Outcome Demonstrates the Claimed Competence

**Required Actions**:

- Invoke the model tier to read the produced artifact against the capability class's acceptance criteria and emit a demonstration verdict of demonstrated, not demonstrated, or out of scope.
- Require the model to state which acceptance criterion each part of the artifact satisfies, so that a pass achieved by a different competence, by a cached result, or by a trivial restatement is distinguishable from a genuine demonstration.
- Require the model to identify the competence actually exercised where it differs from the competence claimed, feeding a reattribution proposal rather than a silent credit.
- Require the model to emit a proposed credibility update carrying direction, magnitude, capability class identifier, and the evidence references it relies on, and to emit no update where the verdict is out of scope.
- Prohibit the model from reading the current credibility value before judging, so that the judgement is of the artifact and not a regression toward the stored score.
- Record the proposal with the judging model identifier and prompt version, so that a systematic judging bias is detectable in the Phase 6 audit.

**Required Outputs**:

- A demonstration verdict per outcome with per-criterion justification.
- A reattribution proposal where the exercised competence differs from the claimed competence.
- A proposed credibility update with direction, magnitude, class, and evidence references.

**Quality Checkpoints**:

- Every demonstration verdict cites at least 1 acceptance criterion by identifier; an unjustified verdict is rejected before it reaches the gate.
- The judging component has no read access to the entry's current credibility at judgement time.
- Out-of-scope verdicts produce zero credibility updates and instead produce coverage-gap records.

***

#### Step 4.3: Apply the Update Through the Deterministic Credibility Gate

**Required Actions**:

- Evaluate every proposed update against the gate conditions in order: the outcome was adjudicated; the verifier independence score is at least 0.50 or a human reviewer is attached; the capability class exists in the current taxonomy version; the holder version on the evidence matches the holder version on the entry; and the proposed magnitude is within the per-update clamp of 0.10.
- Reject any proposal failing a gate condition, record it with the failing condition, and leave the stored credibility unchanged; a rejected proposal never enters as a smaller update.
- Recompute credibility deterministically from the full admitted evidence set rather than applying the proposed delta directly, so the stored value is always reproducible from the ledger.
- Weight each admitted outcome by its difficulty band and by its verifier independence score, so that easy tasks verified by dependent components move the score least.
- Detect and quarantine evidence poisoning before recomputation, flagging reciprocal endorsement loops, a single principal supplying more than 0.40 of one entry's positive evidence, repeated submission of identical task fingerprints, and verifier populations whose independence scores collapse over time.
- Write the recomputed credibility as a new entry version with a write reason code, and demote the entry out of the effective layer in the same transaction where the recomputed value falls below the applicable floor.

**Required Outputs**:

- A gate decision record per proposal with an accept or reject verdict and a reason code.
- A recomputed credibility value with interval and sample count, written as a new entry version.
- A quarantine record for every evidence item excluded as poisoned.

**Quality Checkpoints**:

- Zero stored credibility values were written by a model proposal directly; every value is a deterministic recomputation over the ledger.
- No single update moves credibility by more than 0.10, so one outcome cannot promote or demote an entry alone.
- An entry falling below its floor is demoted in the same transaction as the recomputation, leaving no window in which it remains routable.

***

### Phase 5: Staleness, Decay, and Re-Verification

**Objective**: Prevent the directory from becoming a fossil, by treating every claim as valid only for a bounded period and demoting whatever that period has outlived.

#### Step 5.1: Maintain the Validity Window and Detect Invalidating Change

**Required Actions**:

- Derive `expires_at` from the capability class volatility class rather than from holder preference, and refuse any write that sets a window longer than the class permits.
- Subscribe to holder change events covering model identifier, prompt or policy version, tool set, data-source set, permission scope, and health state, and evaluate each against the entries that reference it.
- On any change to the holder version tuple, discount all evidence produced under the prior version to 0.25 of its weight, recompute credibility, and set a re-verification deadline of 7 days.
- On any permission or scope revocation, remove the affected entries from the effective layer immediately by push invalidation rather than waiting for the validity window to elapse.
- Record `last_verified_at` only on evidence that actually tested the claim, never on a read, a route, a heartbeat, or a successful health check, since none of those observes competence.
- Publish a new directory snapshot on every invalidation batch so that lookups executed after the change cannot resolve against the superseded state.

**Staleness Bounds and Decay by Volatility Class**:

| Volatility class | Staleness bound | Evidence half-life | Lapse threshold | Typical membership |
| :-- | :-- | :-- | :-- | :-- |
| Stable | 90 days | 180 days | 180 days | Ownership, jurisdiction, language, schema authority |
| Moderate | 45 days | 90 days | 90 days | Domain reasoning, analysis, drafting, review |
| Volatile | 14 days | 30 days | 28 days | Tool-dependent work, live data access, external services |

**Required Outputs**:

- Validity windows on every entry, derived from the class volatility class.
- A change-event subscription covering all 6 holder version and permission dimensions.
- An invalidation log recording each push invalidation with its trigger.

**Quality Checkpoints**:

- Zero entries carry a validity window longer than their volatility class permits.
- Every holder version change produces a recomputation and a re-verification deadline within 7 days.
- `last_verified_at` advances only on verification evidence; a deployment in which it advances on routing traffic is misconfigured and halts promotion.

***

#### Step 5.2: Apply Decay and Demote Unconfirmed Claims

**Required Actions**:

- Apply exponential time decay to observed evidence weight using the half-life declared for the volatility class, so an outcome contributes half its original weight after one half-life.
- Retain decayed evidence in the ledger for audit at full fidelity, decaying only its routing weight, so historical performance remains reconstructable.
- Demote by one confidence band any entry whose `last_verified_at` exceeds its staleness bound, marking it provisional and excluding it from high risk lookups while permitting low risk candidacy.
- Lapse any entry whose `last_verified_at` exceeds its lapse threshold, setting `layer` to observed, removing it from lookup results entirely, and recording the lapse with its elapsed interval.
- Prohibit any path by which an entry unconfirmed beyond its staleness bound is served with its undecayed credibility; the demotion is applied at evaluation time even where the scheduled job has not yet run.
- Run the decay and demotion job at least daily, and alarm where a run is missed, since an unrun maintenance job is indistinguishable from a directory that is merely wrong.

**Required Outputs**:

- Decayed routing weights per evidence item with the original weight preserved.
- A demotion log naming each entry demoted to provisional with its elapsed interval.
- A lapse log naming each entry removed from the effective layer.

**Quality Checkpoints**:

- Zero effective-layer entries carry `last_verified_at` older than their lapse threshold.
- Decay affects routing weight only; the evidence ledger retains original weights and timestamps.
- A missed maintenance run produces an alarm within 1 scheduling interval rather than passing silently.

***

#### Step 5.3: Schedule and Execute Re-Verification

**Required Actions**:

- Maintain a re-verification queue ordered by risk tier first, then by served-lookup volume, then by elapsed interval since `last_verified_at`, so that scarce verification effort protects the most consequential and most used entries.
- Re-verify by executing the class's held-out test set, sampling recent adjudicated production outcomes, or commissioning an independent verification task, and record which method was used.
- Cap re-verification cost at 10 percent of the directory's total operating cost, and where the queue cannot be cleared within that cap, lapse the unverified surplus rather than serving it unverified.
- Rotate at least 20 percent of every held-out test set per quarter, and refresh any test set whose pass rate exceeds 0.95 across all holders, since a test everyone passes measures nothing.
- On re-verification, write new evidence bound to the current holder version, advance `last_verified_at`, recompute credibility, and restore the layer assignment where the floor is met.
- Where re-verification fails, demote rather than delete, retaining the entry and its history so the failure informs the concentration and coverage audits.

**Required Outputs**:

- A prioritised re-verification queue with method assigned per entry.
- Refreshed evidence with advanced `last_verified_at` for every re-verified entry.
- A re-verification failure list feeding the Phase 6 audit.

**Quality Checkpoints**:

- Every high risk effective-layer entry has been re-verified within its staleness bound; those that have not are provisional or lapsed.
- Re-verification cost stays within 10 percent of directory operating cost, with the overflow lapsed rather than served.
- No test set is retained unchanged for more than 4 quarters.

***

### Phase 6: Directory Health Audit

**Objective**: Detect the structural pathologies that no single entry reveals, covering over-concentration, coverage gaps, and divergence between what the directory asserts and what the team can actually do.

#### Step 6.1: Measure Concentration and Bus-Factor Exposure

**Required Actions**:

- Compute catalogue concentration as the fraction of capability classes for which a single holder is the highest-credibility eligible candidate, and raise a warning above 0.40 and a block above 0.60.
- Compute served concentration as a Herfindahl-Hirschman index over holder shares of lookups that produced a routable candidate, flagging above 0.25 and blocking new promotions that increase it above 0.40.
- Compute bus factor per capability class as the count of eligible holders meeting the class floor, and record every class whose bus factor is 1 as a single point of failure.
- Raise a redundancy request where classes with bus factor 1 exceed 0.15 of the catalogue, naming the classes and the risk tier of each.
- Rehearse holder removal quarterly by simulating the withdrawal of the highest-concentration holder against the last 30 days of lookups, and report the fraction that would become empty results.
- Prohibit the audit from resolving concentration by lowering a floor; the remedies are cultivating a second holder, decomposing an over-broad capability class, or accepting the exposure with a named owner.

**Directory Health Thresholds**:

| Metric | Warning threshold | Blocking threshold | Action on breach |
| :-- | :-- | :-- | :-- |
| Catalogue concentration | 0.40 | 0.60 | Raise redundancy request; block promotions raising it further |
| Served concentration index | 0.25 | 0.40 | Block promotions that increase the index |
| Bus-factor-1 class share | 0.10 | 0.15 | Name classes and owners; schedule second-holder cultivation |
| Removal-simulation empty rate | 0.10 | 0.20 | Escalate to the named accountable owner |
| Uncredited demand share | 0.02 | 0.05 | Raise catalogue-revision request |
| Effective-layer staleness rate | 0.02 | 0.05 | Halt promotions until re-verification clears the backlog |

**Required Outputs**:

- Concentration measurements for the catalogue and for served lookups.
- A bus-factor register naming every capability class with a single eligible holder.
- A removal-simulation report stating the fraction of recent lookups that would fail.

**Quality Checkpoints**:

- Concentration is computed over eligible candidates rather than over all entries, so scope-filtered holders do not mask exposure.
- Every bus-factor-1 class carries a named accountable owner and a remediation state.
- No concentration breach is closed by adjusting a credibility floor.

***

#### Step 6.2: Measure Coverage Gaps and Mutual Ignorance

**Required Actions**:

- Aggregate unmatched-demand events, out-of-scope demonstration verdicts, and quarantined external skill terms into one coverage-gap ledger keyed by proposed capability class.
- Compute uncredited demand share as lookups producing an empty candidate set divided by all lookups, flagging above 0.02 and raising a catalogue-revision request above 0.05.
- Separate the two causes of an empty set, since they carry different remedies: a taxonomy gap requires a new capability class, while a population gap requires a new or improved holder.
- Invoke the model tier to propose candidate capability classes from clustered unmatched demand, and admit a proposal only where it carries an acceptance test, at least 5 observed requests, and no more than 0.80 term overlap with an existing class.
- Verify that every escalation raised under Step 3.3 reached a destination and was resolved, and treat an unresolved escalation older than the class deadline as an open coverage defect rather than a closed one.
- Report coverage against demand rather than against the catalogue, since a directory can achieve full catalogue coverage while failing most of the work that actually arrives.

**Required Outputs**:

- A coverage-gap ledger separating taxonomy gaps from population gaps.
- Proposed capability classes with acceptance tests and demand counts.
- An escalation-resolution report naming unresolved escalations past deadline.

**Quality Checkpoints**:

- Uncredited demand share is measured against served lookups, not against the catalogue.
- Every proposed capability class carries an acceptance test before admission; proposals without one are rejected, not deferred.
- Zero escalations remain unrouted; an escalation with no destination is a defect recorded against the directory, not against the query.

***

#### Step 6.3: Measure Directory Accuracy Against Adjudicated Ground Truth

**Required Actions**:

- Maintain a labelled evaluation corpus of at least 200 tasks whose eligible holders were adjudicated independently of the directory, refreshed by at least 20 percent per quarter.
- Compute directory precision as adjudicated-correct credited holders divided by credited holders returned, and directory recall as adjudicated-eligible holders returned divided by all adjudicated-eligible holders.
- Run a directory ablation that serves the same holders and budget with credibility removed, and report the difference in successful-task cost; where the ablation matches the directory within 5 percent, the directory is not earning its maintenance and Section 1.4 suppression is reconsidered.
- Run perturbation trials covering a stale entry, a withdrawn holder, a spoofed capability card, a holder version change, a revoked scope, and a poisoned evidence stream, and report the directory's behaviour under each.
- Report every measurement with its cohort, time window, directory snapshot generation, taxonomy version, and label coverage, so that a figure cannot be compared across incomparable states.
- Recompute all thresholds in this guide per deployment against observed outcomes, treating the stated values as starting defaults rather than as measured constants.

**Required Outputs**:

- Precision, recall, and staleness-serving rates with confidence intervals and cohort labels.
- An ablation report comparing directory-served and credibility-blind operation.
- A perturbation report covering all 6 fault classes.

**Quality Checkpoints**:

- Directory precision is at least 0.85 and recall at least 0.80 on the evaluation corpus; below either, promotions halt until the deficit is closed.
- Effective-layer staleness-serving rate is no more than 0.02; above 0.05 the directory is treated as untrusted and lookups return provisional candidates only.
- The ablation was run on the same holders and budget; an ablation that also changes the holder set measures nothing about the directory.

***

## III. Implementation Guidance for AI Agents

AI agents operating an expertise directory must follow systematic protocols ensuring that every routable claim is evidenced, versioned, time-bounded, and reproducible against a named snapshot. The following guidance translates the maintenance discipline above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Directory Steward Agent**: Owns the taxonomy, the entry schema, and the promotion gate. It alone may assign a layer, and every assignment it makes is versioned and attributed. It never supplies evidence for an entry it promotes.
2. **Capability Assessor Agent**: Executes controlled capability tests and re-verification tasks against held-out sets. It writes evidence and never writes credibility, layer assignments, or scope grants.
3. **Competence Resolver Agent**: Interprets arriving queries into competence requirements against the current taxonomy version. It emits identifiers and confidence values, and it never selects a holder.
4. **Outcome Adjudicator Agent**: Judges whether a completed artifact demonstrates the claimed competence, emitting a per-criterion verdict and a proposed credibility update. It has no read access to stored credibility at judgement time.
5. **Credibility Gate**: A deterministic component that validates proposals against evidence rules and recomputes credibility from the ledger. It holds final authority over every stored score and rejects rather than attenuates a failing proposal.
6. **Health Auditor Agent**: Computes concentration, coverage, precision, recall, and staleness metrics on a fixed cadence, and may block promotions where a threshold is breached.

**Separation of Duties**: No component both supplies evidence and promotes the entry that evidence supports. Where one deployment collapses roles onto a single process, the write path must still enforce the separation, rejecting a promotion whose approver identifier matches the asserting principal on any of its evidence references.

**Workflow Execution Pattern**:

```
STATE: Credibility_Update_Evaluation
INPUTS:
  1. Outcome record joined to lookup, snapshot, and entry version
  2. Adjudication verdict with method and independence score
  3. Model-proposed credibility update with evidence references
ACTIONS:
  1. Validate outcome adjudication method against class risk tier
  2. Validate holder version match between evidence and entry
  3. Validate capability id against current taxonomy version
  4. Screen evidence set for poisoning signatures
  5. Recompute credibility from full admitted ledger
VALIDATION:
  - outcome_adjudicated == TRUE
  - verifier_independence >= 0.50 OR human_reviewer_present == TRUE
  - proposed_magnitude <= 0.10
  - evidence_holder_version == entry_holder_version
  - recomputed_from_ledger == TRUE
TRANSITIONS:
  IF all_validations_pass AND recomputed >= class_floor
     THEN next_state = Write_New_Entry_Version
  IF all_validations_pass AND recomputed < class_floor
     THEN next_state = Demote_And_Write_In_Same_Transaction
  IF poisoning_signature_detected THEN next_state = Quarantine_Evidence
  IF validation_failed THEN next_state = Reject_Proposal_With_Reason_Code
```

**Two-Phase Action Pattern**: Emit the intended directory write with its evidence references, computed credibility, and target layer without committing it; validate it against the gate conditions while nothing is stored; commit the new entry version and its snapshot only after validation passes, in one transaction that also carries any demotion the recomputation requires.

**Approval Gate**: Named human authorisation is required before promoting any entry in a high risk capability class, before promoting any entry for a holder whose identity was ingested from outside the trust boundary, before admitting a new capability class into the taxonomy, and before any credibility floor or evidence weight is changed. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the taxonomy, the entry store, and the evidence ledger in durable storage outside any agent's working context, since the directory outlives every session that reads it.
- Pin a directory snapshot identifier for the duration of a lookup and record it on the response, so a decision remains reproducible after the directory has moved on.
- Load into a resolver's context only the capability class identifiers and definitions, never the credibility scores, so that competence resolution is not biased toward whichever holder currently ranks highest.
- Write a handoff record at every context boundary naming the taxonomy version, the snapshot identifier, the pending re-verification queue, and any open coverage gap.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Taxonomy and Schema Integrity (After Phase 1)**

- **Automated Check**: Every capability class carries all 7 attributes and a deterministic acceptance test; demand coverage is at least 0.90; the schema rejects an unevidenced write in a test transaction.
- **Agent Action on Pass**: Proceed to directory population.
- **Agent Action on Failure**: Halt; return the classes lacking acceptance tests and the uncovered demand clusters.
- **Human Review Trigger**: Demand coverage below 0.75, or any high risk class whose acceptance test requires human interpretation.

**Checkpoint 2: Population Evidence Integrity (After Phase 2)**

- **Automated Check**: Zero effective-layer entries with an empty evidence set; every high risk entry tested on at least 5 held-out tasks; every promotion approver distinct from every asserting principal on its evidence.
- **Agent Action on Pass**: Publish the snapshot and open the directory to lookups.
- **Agent Action on Failure**: Withhold the snapshot and demote the failing entries to the declared layer.
- **Human Review Trigger**: Any refuted claim for a holder credited elsewhere with a high risk class.

**Checkpoint 3: Lookup Determinism and Escalation Integrity (After Phase 3)**

- **Automated Check**: Repeated lookups against one snapshot return identical ordered candidate sets; every empty result produced an escalation with a destination; zero routes were served for uncredited capability classes.
- **Agent Action on Pass**: Continue serving and forward outcomes to Phase 4.
- **Agent Action on Failure**: Suspend lookups for the affected capability class and serve escalations only.
- **Human Review Trigger**: Any routed holder found to have carried no credited entry, or uncredited demand above 0.05 for a high risk class.

**Checkpoint 4: Update Admissibility (After Phase 4)**

- **Automated Check**: Every stored credibility value is reproducible from the ledger; no single update exceeded 0.10; zero credibility-bearing outcomes carry independence below 0.50 without a human reviewer.
- **Agent Action on Pass**: Publish the recomputed entry versions and a new snapshot.
- **Agent Action on Failure**: Roll back to the prior entry version and quarantine the proposal set.
- **Human Review Trigger**: A poisoning signature detected on any high risk entry, or a judging model whose proposals are rejected at above 0.30.

**Checkpoint 5: Freshness Integrity (After Phase 5)**

- **Automated Check**: Zero effective-layer entries past their lapse threshold; every holder version change produced a recomputation within 7 days; the maintenance job ran within its scheduling interval.
- **Agent Action on Pass**: Continue normal operation.
- **Agent Action on Failure**: Demote the stale entries immediately at evaluation time, independently of the job schedule.
- **Human Review Trigger**: Staleness-serving rate above 0.05, or a missed maintenance run in 2 consecutive intervals.

**Checkpoint 6: Structural Health (After Phase 6)**

- **Automated Check**: Catalogue concentration below 0.60; served concentration index below 0.40; bus-factor-1 share below 0.15; precision at least 0.85 and recall at least 0.80.
- **Agent Action on Pass**: Release the health report and permit further promotions.
- **Agent Action on Failure**: Block promotions that worsen the breached metric and name the accountable owner.
- **Human Review Trigger**: Any blocking threshold breached, or an ablation showing the directory within 5 percent of credibility-blind operation.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
DIRECTORY_SNAPSHOT_ID:
TAXONOMY_VERSION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Unevidenced Entry Reaching the Effective Layer**

- **Symptoms**: An entry serves lookups with an empty or declaration-only evidence set; credibility above 0.35 with zero adjudicated outcomes and zero controlled tests; a holder consistently selected for a class it has never been tested on.
- **Diagnostic Steps**: Trace the entry version history to the write that set the layer, identify the approver and the asserting principal, and determine whether the write bypassed validation or the validation rule was absent for that path.
- **Resolution Protocol**: Option A, demote the entry to declared, void every credibility update derived from work it was routed, and re-test the claim under Step 2.2. Option B, where the write path lacked the validation, add the rejection rule and re-run it across the whole effective layer as a backfill audit. Option C, where the approver matched an asserting principal, revoke the promotion and treat every other promotion by that principal as suspect.
- **Escalation Trigger**: More than 1 unevidenced entry found in any audit escalates to the accountable directory owner; any unevidenced entry in a high risk class halts all promotions immediately.

**Error Type 2: Directory Staleness and Silent Drift**

- **Symptoms**: Success rates falling for a holder whose credibility is unchanged; `last_verified_at` clustered far in the past; failures concentrated after a known model or tool change; entries lapsing in bulk when the maintenance job finally runs.
- **Diagnostic Steps**: Segment outcomes by holder version and compare pre-change and post-change success; confirm whether the change-event subscription received the version change; check whether `last_verified_at` advanced on routing traffic rather than on verification.
- **Resolution Protocol**: Option A, apply the version discount, recompute, and re-verify within 7 days. Option B, where the subscription missed the change, reconcile holder versions directly from the holder register and treat the gap as a coverage defect in the change pipeline. Option C, where staleness is systemic, shorten the volatility class bound for the affected classes and lapse the backlog rather than serving it.
- **Escalation Trigger**: Staleness-serving rate above 0.05, or 2 consecutive missed maintenance runs, suspends high risk lookups until the backlog clears.

**Error Type 3: Over-Concentration and Bus-Factor Collapse**

- **Symptoms**: One holder top-ranked across most classes; queue depth and latency rising for that holder while others idle; removal simulation producing a large empty rate; broad outage impact from a single holder's failure.
- **Diagnostic Steps**: Recompute catalogue and served concentration separately, since a broad catalogue can conceal narrow traffic concentration; check whether concentration reflects genuine competence or an over-broad capability class that should be decomposed.
- **Resolution Protocol**: Option A, decompose the over-broad class into narrower classes and re-test candidates against each. Option B, cultivate a second holder by directing low risk work to a provisional candidate under supervision until it reaches the sample minimum. Option C, accept the exposure explicitly with a named owner, a documented rationale, and a scheduled review date.
- **Escalation Trigger**: Catalogue concentration above 0.60 or served concentration index above 0.40 blocks further promotions to that holder and escalates to the accountable owner.

**Error Type 4: Mutual Ignorance Answered by a Guess**

- **Symptoms**: Lookups returning candidates whose credited classes do not match the competence requirement; failures concentrated on query types absent from the taxonomy; escalation counts near zero while unmatched-demand events are high.
- **Diagnostic Steps**: Join failed outcomes to their competence requirements and confirm whether the selected holder held a credited entry for every required class; inspect whether a fallback path substituted a general-purpose holder.
- **Resolution Protocol**: Option A, remove the substitution path so that an empty candidate set produces an escalation and nothing else. Option B, admit the missing capability class through the Step 6.2 proposal process and populate it. Option C, where no holder can be cultivated, declare the class out of scope and route its demand to a named human destination permanently.
- **Escalation Trigger**: Any confirmed substitution for a high risk class halts lookups for that class; uncredited demand above 0.05 raises a catalogue-revision request.

**Error Type 5: Poisoned or Correlated Evidence**

- **Symptoms**: Credibility rising without difficulty-weighted improvement; reciprocal endorsement between two holders; verifier independence scores collapsing toward zero; one principal supplying most of an entry's positive evidence; repeated identical task fingerprints.
- **Diagnostic Steps**: Recompute credibility with the suspect evidence excluded and measure the delta; check the verifier population for shared model, prompt, corpus, and provider; inspect task fingerprint distribution for repetition.
- **Resolution Protocol**: Option A, quarantine the suspect evidence, recompute, and demote where the recomputed value falls below the floor. Option B, require an independent verifier at independence 0.75 or above for the affected class until the sample minimum is rebuilt. Option C, where poisoning appears deliberate, revoke the holder's effective entries and treat every entry it endorsed as suspect.
- **Escalation Trigger**: A recomputation delta above 0.15 after exclusion escalates immediately; this class is never resolved by collecting more evidence from the same population.

**Error Type 6: Competence Resolution Failure**

- **Symptoms**: Resolver emitting identifiers absent from the taxonomy; the same query resolving differently across runs; more than 5 required classes emitted per query; resolution confidence high on queries that later fail.
- **Diagnostic Steps**: Compare resolutions across the resolver model version and prompt version; check whether the taxonomy version pinned at resolution matches the one pinned at lookup; measure resolution stability by re-running a fixed query set.
- **Resolution Protocol**: Option A, reject invalid identifiers at validation and record an unmatched-demand event rather than repairing them to the nearest class. Option B, decompose queries emitting more than 5 required classes before lookup. Option C, pin the resolver's model and prompt version and re-baseline resolution stability before the change is promoted.
- **Escalation Trigger**: Resolution stability below 0.90 on the fixed query set, or an identifier-rejection rate above 0.10, suspends automated resolution for high risk classes.

**Troubleshooting Decision Tree**:

```
DIRECTORY DEFECT DETECTED
├─ EVIDENCE DEFECT
│   ├─ Effective entry with empty evidence set → Demote to declared; void derived updates; re-test
│   ├─ Approver matches asserting principal → Revoke promotion; audit that principal's promotions
│   └─ Recomputation delta above 0.15 after exclusion → Quarantine evidence; escalate
├─ FRESHNESS DEFECT
│   ├─ Past staleness bound → Demote to provisional; exclude from high risk lookups
│   ├─ Past lapse threshold → Lapse entry; remove from effective layer
│   └─ Holder version changed → Discount evidence to 0.25; re-verify within 7 days
├─ STRUCTURE DEFECT
│   ├─ Concentration above blocking threshold → Block promotions; decompose class or cultivate holder
│   ├─ Bus factor 1 above 0.15 of catalogue → Raise redundancy request with named owner
│   └─ Ablation within 5 percent of blind operation → Reconsider directory suppression
├─ COVERAGE DEFECT
│   ├─ Empty candidate set → Escalate with reason; never substitute a holder
│   ├─ Uncredited demand above 0.05 → Raise one catalogue-revision request
│   └─ Out-of-scope demonstration verdict → Write coverage gap; issue no credibility update
└─ RESOLUTION DEFECT
    ├─ Identifier absent from taxonomy → Reject; record unmatched demand
    └─ Resolution stability below 0.90 → Pin versions; suspend automated high risk resolution
```

### D. Performance Metrics and Continuous Learning

**Directory Accuracy Metrics**:

- **Directory precision**: Credited holders adjudicated correct over credited holders returned (target: at least 0.85; below it, promotions halt).
- **Directory recall**: Adjudicated-eligible holders returned over all adjudicated-eligible holders (target: at least 0.80).
- **Staleness-serving rate**: Lookups served from entries past their staleness bound over all lookups (target: no more than 0.02; above 0.05 the directory serves provisional candidates only).
- **Evidence-grade coverage**: Effective-layer entries carrying at least 1 adjudicated outcome over all effective-layer entries (target: at least 0.90).
- **Self-report calibration error**: Mean absolute difference between self-assessed and observed success per holder (target: no more than 0.15; above it, self-assessment weight is set to 0.00 for that holder).

**Structural Health Metrics**:

- **Catalogue concentration**: Classes whose top eligible candidate is one holder over all classes (target: no more than 0.40).
- **Served concentration index**: Herfindahl-Hirschman index over holder shares of routable lookups (target: no more than 0.25).
- **Bus-factor-1 share**: Classes with exactly 1 eligible holder over all classes (target: no more than 0.10).
- **Uncredited demand share**: Lookups returning an empty candidate set over all lookups (target: no more than 0.02).
- **Escalation resolution rate**: Escalations resolved within the class deadline over all escalations (target: at least 0.95).

**Maintenance Economy Metrics**:

- **Re-verification cost share**: Verification cost over total directory operating cost (target: no more than 0.10).
- **Directory value margin**: Successful-task cost under credibility-blind operation minus successful-task cost under directory operation (target: positive by at least 5 percent; at or below that margin the directory is not earning its maintenance).
- **Proposal rejection rate**: Model-proposed credibility updates rejected by the gate over all proposals (target: no more than 0.30; above it, the judging prompt or the evidence rules are misaligned).

**Log-Pattern Failure Detection**: Credibility rising with flat difficulty-weighted success indicates evidence inflation. `last_verified_at` advancing without matching verification events indicates a misconfigured freshness stamp. Escalation counts near zero alongside high unmatched demand indicates a substitution path. Verifier independence trending downward indicates a collapsing verifier population. One holder's share of routable lookups rising while its credibility is flat indicates that routing policy, not competence, is driving concentration.

**Learning and Adaptation Mechanisms**:

- **Threshold recalibration**: Recompute every floor, bound, weight, and half-life per deployment against observed outcomes at least quarterly; the values in this guide are starting defaults.
- **Taxonomy evolution**: Admit new capability classes only through the Step 6.2 proposal process, and recompute every affected entry and evaluation slice after a taxonomy version change.
- **Evidence-rule versioning**: Version every change to evidence weights or gate conditions, and recompute stored credibility under the new version before serving it.
- **Holder cultivation**: Direct a bounded share of low risk work, no more than 0.05 of lookups, to provisional candidates under supervision, so that new holders can reach the sample minimum without exposing consequential work to unproven competence.

**Human-in-the-Loop Boundaries**: Promotion of a high risk entry, admission of a new capability class, any change to a credibility floor or evidence weight, acceptance of a bus-factor-1 exposure, and revocation of a holder's effective entries are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the maintenance of a claim about competence, not the content of any competence. Its phases hold wherever work must be assigned to differentiated holders, outcomes can be adjudicated, and a wrong assignment carries a cost.

### 4.1 Cross-Domain Application Patterns

**Software engineering organisations**: Capability classes are drawn from service ownership, language and framework competence, migration classes, and incident response roles, with tool access and repository authority recorded separately from reasoning competence. Volatility is high because dependency versions, service boundaries, and tool sets change continuously, so most classes sit in the moderate or volatile band with staleness bounds of 45 or 14 days. Adjudication is unusually cheap here, since test suites, static analysis, and deployment outcomes supply deterministic acceptance tests, which makes the observed layer strong and the declared layer nearly ornamental. The dominant pathology is concentration: one holder that has absorbed most of the codebase becomes the top candidate everywhere, and the removal simulation is the audit that makes the exposure visible before an absence does.

**Clinical and health service triage**: Capability classes correspond to specialty, procedure authority, jurisdiction of licensure, and language, and the directory includes human roles as first-class holders with capacity and service-level metadata. Risk tiers are steep, so most classes carry the high risk floor of 0.75 credibility, 30 adjudicated outcomes, and mandatory independent verification, and promotion requires named human approval without exception. Mutual ignorance must escalate visibly rather than route to the nearest available holder, because a plausible substitution is the specific harm the directory exists to prevent. Validity windows are bounded by credentialing and licensure expiry rather than by model change, which places most classes in the stable band with hard external expiry dates.

**Financial services and regulated operations**: Authority is contractual and often statutory, so administrator assignment carries unusual weight for ownership-defined classes while remaining incapable of establishing reasoning competence. Scope qualifiers covering tenant, purpose, region, and data class do most of the eligibility filtering, and the exclusion record becomes an audit artifact rather than a diagnostic aid. Every lookup pins a snapshot identifier because a supervisory review will later ask which directory state produced a given assignment. The directory ablation matters here for a defensive reason: where credibility contributes nothing over static assignment, the simpler and more auditable mechanism should be preferred.

**Scientific research consortia**: Capability classes cover instrument access, method competence, dataset authority, and review qualification across institutions that do not share an operator. Declarations arrive from outside the trust boundary, so signature verification and quarantine of unmapped terms carry more of the load than in a single-operator deployment. Adjudication is slow and expensive, since outcomes are judged by peer review over months rather than by tests over seconds, which pushes deployments toward controlled capability tests and long half-lives. Coverage gaps are the characteristic pathology, because new methods appear faster than the taxonomy admits them.

**Industrial and field operations**: Holders are dispatchable crews, equipment, and automated services with hard capacity limits and geographic constraints, so eligibility filtering is dominated by region and availability rather than by competence. Volatility is driven by certification expiry, equipment maintenance state, and shift rotation, and the change-event subscription is the most consequential component, since a lapsed certification must invalidate entries immediately rather than at the next scheduled run. Bus factor is measured against physical presence, and the removal simulation translates directly into a staffing decision.

### 4.2 Scale, Risk, and Trust-Boundary Adaptation

- **Small teams under 10 holders**: Collapse the taxonomy to 15 to 25 classes and run Phases 1, 2, and 5 with Phase 6 quarterly rather than continuously. Retain the unevidenced-entry rejection and the staleness bound without exception, since they are what distinguishes a directory from a roster.
- **Large populations above 200 holders**: Partition the taxonomy by domain and shard the entry store by capability class, retaining one global snapshot identifier so lookups remain reproducible. Concentration must be measured per partition as well as globally, since a globally healthy index can hide a bottleneck inside one domain.
- **High risk deployments**: Apply the 0.75 floor with 30 outcomes and mandatory independent verification, require named human approval on every promotion, and shorten every staleness bound by half. Prefer an escalation to a route wherever the candidate set is thin.
- **Cross-organisation trust boundaries**: Treat every externally ingested declaration as evidence class provider declaration at weight 0.10, verify signatures and endpoint ownership before admission, quarantine unmapped terms, and require locally executed controlled tests before any external holder reaches the effective layer.
- **Low-adjudication environments**: Where outcomes cannot be judged within the staleness bound, lengthen half-lives, lean on controlled capability tests, and lower the directory's ambition to eligibility filtering plus coarse credibility bands rather than fine-grained scores. Where outcomes cannot be adjudicated at all, Section 1.4 suppression applies and a static assignment table is the correct mechanism.

***

## V. Limitations and Considerations

**Every threshold here is a deployment default, not a measured constant**: The credibility floors, staleness bounds, half-lives, concentration limits, weight assignments, and sample minimums were chosen to be operable on first deployment, not derived from a universal property of multi-agent systems. Presenting them as evidence would be false precision. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute them quarterly against observed outcomes and to version every change.

**Adjudication capacity bounds the whole method**: Credibility can only be as good as the outcomes it learns from, and many valuable capability classes have no cheap deterministic acceptance test. Where adjudication is scarce, the observed layer stays thin and the directory drifts back toward being a record of declarations. The mitigation is the controlled capability test in Step 2.2, which substitutes a bounded held-out set for continuous production adjudication, together with the Section 1.4 suppression condition that withholds the directory entirely where nothing can be adjudicated.

**A model judging demonstration shares the failure modes of models generating work**: The Outcome Adjudicator is itself an LLM and can credit a competence that was not exercised, particularly where the artifact is fluent. The mitigation is the deterministic gate in Step 4.3, the independence requirement of 0.50 or a human reviewer, the 0.10 clamp preventing any single judgement from moving routing, and the proposal rejection rate metric that surfaces a systematically misaligned judge.

**Credibility is task-conditional and the taxonomy is always coarser than reality**: A holder competent at one instance of a capability class may fail another instance the class also covers, and no taxonomy granularity fully removes this. Narrowing classes to eliminate it destroys the sample sizes credibility depends on. The mitigation is difficulty-band stratification in Step 4.1, the class-decomposition remedy in the concentration protocol, and the 20-request-per-quarter minimum that prevents classes too narrow to learn from.

**Directory maintenance competes with the work it serves**: Re-verification, testing, and auditing consume the same budget as production tasks, and under schedule pressure the maintenance job is what gets deferred. A deferred maintenance job produces a directory that looks healthy and is not. The mitigation is the 10 percent cost cap in Step 5.3 with mandatory lapsing of the overflow, and the alarm on a missed run in Step 5.2, which makes deferral visible rather than silent.

**Concentration may reflect a genuine and irreducible fact**: Sometimes one holder is simply the only competent party, and the audit's remedies of decomposition and cultivation do not apply. Treating this as a defect to be engineered away produces artificial redundancy that fails under load. The mitigation is the explicit acceptance path in Step 6.1, which requires a named owner, a documented rationale, and a scheduled review rather than either silent tolerance or forced remediation.

**The directory records competence, not intent or safety**: An entry can be accurate about what a holder can do and say nothing about whether it should. Credibility is not authorization, and a high score never substitutes for a scope check. The mitigation is the ordering rule in Step 3.2, which applies eligibility filtering before any scoring, and the Section 1.3 prohibition on the model tier deciding authorization or scope grants.

**Evidence poisoning is adversarially adaptive**: The detection signatures in Step 4.3 catch reciprocal endorsement, principal dominance, fingerprint repetition, and collapsing independence, but an adversary aware of those signatures can shape evidence to avoid them. The mitigation is defence in depth rather than detection alone: the independent verifier requirement, the 0.10 clamp, the separation of duties on promotion, and the periodic ablation that would reveal a directory whose credibility no longer tracks outcomes.

***

## VI. Conclusion and Summary

Transactive memory is a maintenance discipline before it is a coordination technique. Its value comes from a small number of enforced properties: that no claim about a holder's competence is routable without evidence, that every claim carries an expiry, that credibility moves only on adjudicated outcomes weighted by the independence of whoever judged them, and that a question no holder is credited to answer produces an escalation rather than a guess. A team that enforces those four properties will have a directory that stays true; a team that builds the same schema without them will have an increasingly confident record of what its agents could do at the moment the system was configured.

A team introducing a transactive directory should build the taxonomy and the entry schema before populating anything, and should populate from controlled tests rather than from declarations. The declared layer is a candidate generator and nothing more. Once lookups are serving, the outcome path matters more than the lookup path: a directory that answers queries but never learns from what happened next is a static assignment table with extra machinery, and the ablation in Step 6.3 will say so. Maintenance is the part that is skipped and the part that determines whether the system works after its first quarter, which is why the staleness bound demotes automatically at evaluation time rather than waiting for a job that may not have run.

The failure modes worth instrumenting first are the three the audit exists for. An unevidenced entry routes work indefinitely to a holder that cannot do it. Over-concentration turns a single holder into both a bottleneck and a single point of failure, usually without anyone deciding that it should be. Mutual ignorance is the most dangerous of the three, because a system that substitutes the nearest plausible holder for a missing one converts an answerable operational question into a silent quality failure.

**Key Success Factors**:

- **Evidence before routability**: No entry reaches the effective layer with an empty evidence set, and no self-report alone lifts an entry above the 0.35 cap.
- **Bounded validity**: Every claim carries a validity window derived from its capability class volatility, and an unconfirmed claim is demoted at evaluation time rather than trusted until a job runs.
- **Deterministic authority over credibility**: A model may propose an update and read an artifact against acceptance criteria, but the stored score is always a deterministic recomputation over the ledger, clamped so no single outcome moves routing.
- **Explicit ignorance**: An empty candidate set produces an escalation with a named destination, and substitution of a semantically similar holder is prohibited on every path.
- **Structural audit alongside entry-level accuracy**: Concentration, bus factor, and coverage are measured on a fixed cadence, because a directory composed entirely of correct entries can still be a fragile and incomplete model of the team.
- **Separation of duties**: The principal that supplies evidence never approves the promotion that evidence supports, enforced at the write path rather than by convention.

By following this guide, AI agents can maintain a directory of expertise that a router can trust, that names what the team cannot do as clearly as what it can, and that degrades by demotion and escalation rather than by confident misrouting.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, except where an entry is marked as confirmed during research for this conversion. Titles and locations are otherwise reproduced rather than checked.

**Corpus pointers**:

- `Transactive Memory Systems for Multi-Agent AI: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the directory-as-governed-metaknowledge stance, the separation of declared, observed, and effective capability, the evidence-source vocabulary, the capability taxonomy construction rules, the reputation and calibration discipline, the failure-mode catalogue, the logging field inventory, and the evaluation and ablation requirements. It carries inline citations to organizational psychology on transactive memory, to interoperability protocol specifications, and to multi-agent failure and benchmark literature; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_DistributedMemoryArchitecture.md` — the companion guide governing where data lives, covering replication, partitioning, consistency models, and conflict resolution. It owns the storage properties of a replicated directory; this guide owns the accuracy of what the directory asserts. Section 1.4 states the boundary.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — the parent guide covering the overall memory taxonomy within which transactive memory is one team-level class.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on trajectory capture and replay, applicable to the outcome records that supply the evidence in Phase 4.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — companion guidance on decay and deletion policy, applicable to the evidence half-lives and lapse thresholds in Phase 5.
- `advanced_task_guides/memory-management/guide_StructuredMemory.md` — companion guidance on schema-governed stores, applicable to the directory entry schema in Step 1.2.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on schema and vocabulary evolution, applicable to the capability taxonomy versioning and deprecation mapping in Step 1.1.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the outcome, lookup, and directory-write events the metrics in Section III.D are computed from.
- `advanced_task_guides/planning/guide_TaskManagementOrchestration.md` — companion guidance on task lifecycle and assignment, applicable to the router that consumes the lookup response defined in Step 3.2.

**External references**:

*Transactive memory in organizational psychology*

1. Wegner, *Transactive Memory: A Contemporary Analysis of the Group Mind* — https://link.springer.com/chapter/10.1007/978-1-4612-4634-3_9
2. Wegner, Erber, and Raymond, *Transactive Memory in Close Relationships* — https://dtg.sites.fas.harvard.edu/DANWEGNER/pub/Wegner,Erber,&Raymond1991.pdf
3. Hollingshead, *Communication, Learning, and Retrieval in Transactive Memory Systems* — https://www.sciencedirect.com/science/article/pii/S0022103198913580
4. Directory updating, information allocation, and retrieval coordination, *review of transactive memory processes* — https://onlinelibrary.wiley.com/doi/am-pdf/10.1111/tops.12359
5. Liang, Moreland, and Argote, *Group Versus Individual Training and Group Performance* — https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Group_Performance/Liang_et_al_Group_vs_Individ_(1995)_%20PersnltySocialPsychBulltn.pdf
6. Moreland and Myaskovsky, *Exploring the Performance Benefits of Group Training* — https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=aa44796041f06c1623e3c10020ff7a9fa9a64a4b
7. Lewis, *Measuring Transactive Memory Systems in the Field* — https://psycnet.apa.org/record/2003-99635-002

*Multi-agent failure, evaluation, and directory services*

8. Cemri and colleagues, *Why Do Multi-Agent LLM Systems Fail?* — https://arxiv.org/abs/2503.13657 (confirmed during research for this conversion: 14 failure modes across system design, inter-agent misalignment, and task verification, annotated over more than 1,600 traces from 7 frameworks)
9. *Multi-Agent System Failure Taxonomy repository* — https://github.com/multi-agent-systems-failure-taxonomy/MAST
10. *MultiAgentBench* — https://aclanthology.org/2025.acl-long.421/
11. *Scaling behaviour and error amplification in multi-agent systems* — https://arxiv.org/html/2512.08296v1
12. *The AGNTCY Agent Directory Service: Architecture and Implementation* — https://arxiv.org/html/2509.18787 (retrieved during research for this conversion; content-addressed storage, hierarchical taxonomies, and cryptographic signing for capability discovery)
13. *Multi-Agent Transactive Memory* — https://arxiv.org/abs/2606.19911 (retrieved during research for this conversion; population-level storage and retrieval of agent-generated trajectories with producer trust modelling)

*Interoperability, identity, and instrumentation*

14. *Agent2Agent (A2A) Protocol Specification* — https://a2a-protocol.org/latest/specification/
15. *A2A Agent Cards: agent skills and card publication* — https://a2a-protocol.org/latest/tutorials/python/3-agent-skills-and-card/
16. *A2A agent discovery documentation* — https://github.com/a2aproject/A2A/blob/main/docs/topics/agent-discovery.md (retrieved during research for this conversion)
17. *Model Context Protocol architecture* — https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture
18. *FIPA ACL Message Structure Specification* — http://www.fipa.org/specs/fipa00061/SC00061G.pdf
19. *OAuth 2.0 Token Exchange, RFC 8693* — https://www.rfc-editor.org/rfc/rfc8693
20. *OWASP AI Agent Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
21. *OpenTelemetry GenAI semantic conventions* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
22. *Strong eventual consistency and CRDT analysis* — https://fpl.cs.depaul.edu/jriely/papers/2018-esop.pdf
