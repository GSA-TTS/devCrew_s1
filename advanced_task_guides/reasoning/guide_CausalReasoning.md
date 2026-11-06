# Causal Reasoning

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Causal reasoning constitutes the task family of establishing what a change to one variable does to another, as distinct from establishing what is observed alongside what. This guide provides AI agents with a structured protocol that treats a causal claim as inadmissible until its basis is named: a controlled experiment, a natural experiment, an identification strategy with its assumptions recorded, or domain knowledge encoded as an explicit causal structure. It specifies a three-level query classification separating association, intervention, and counterfactual questions; an evidence-class ladder stating what each level demands; a structure-elicitation procedure producing nodes, directed edges, and a per-edge assumption registry as inspectable artifacts rather than prose; an adversarial confounder enumeration treating a common cause as the default hypothesis for any proposed link; a bounded identification loop that must certify before estimation begins; and a release gate combining refutation, unmeasured-confounding sensitivity, and causal lineage. It partitions execution so that a language model proposes structures, confounders, and mechanisms while deterministic software records assumptions, checks acyclicity, labels evidence class, and downgrades any claim whose asserted level exceeds the evidence supporting it. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a fluent causal narrative is never mistaken for an identified effect.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Causal reasoning**: Reasoning about what an outcome would be under a change to some variable, why an outcome occurred, or what would have occurred under a different action. It is distinguished from prediction by its target: a predictive model estimates a pattern in the observed distribution, while a causal analysis defines a target under an intervention, states the assumptions connecting that target to available data, identifies it, estimates it, and tests how the conclusion moves when the assumptions or the data are perturbed.

**Query level**: The rung of the causal hierarchy at which a question sits, drawn from a closed three-valued vocabulary: association, intervention, or counterfactual. Every task carries exactly one declared query level, fixed before any structure is proposed.

**Association claim**: A statement about what is observed together, such as a conditional distribution, a correlation, a regression coefficient, or a feature-importance ranking. An association claim asserts nothing about what a change would produce.

**Interventional claim**: A statement about the outcome distribution when a variable is actively set to a value rather than merely observed at that value.

**Counterfactual claim**: A statement about an alternate world for a specific unit or context, conditional on what actually occurred for that unit. Counterfactual claims are cross-world quantities and are not implied by interventional identification alone.

**Stated basis**: The named ground on which a causal claim rests, drawn from a closed four-valued vocabulary: a controlled experiment, a natural experiment, an identification strategy with its assumptions recorded, or domain knowledge encoded as an explicit causal structure. A claim carrying no entry from this vocabulary is not a causal claim.

**Evidence class**: The label naming what kind of evidence supports a claim, drawn from a closed seven-valued ordered vocabulary defined in Section 1.3. The label is assigned by deterministic software from the artifacts on record, never by the component that generated the claim.

**Level-evidence check**: The deterministic test asserting that a claim's declared query level does not exceed the maximum level its recorded evidence class supports. It is the guide's principal enforcement mechanism.

**Downgrade**: The mandatory relabelling applied when the level-evidence check fails. The claim is re-emitted at the highest level its evidence supports, with a reason code and the missing requirement attached. A downgrade is a change to the claim, not a caveat appended to it.

**Causal structure**: The explicit artifact carrying nodes, directed edges, and the assumption each edge and each absent edge rests on. It is stored, versioned, and hashed, so that it can be inspected, challenged, and diffed rather than inferred from prose.

**Node**: One modelled variable, carrying a definition, an ontology identifier, a unit, an allowed value range, a measurement process, a data field or a latent marker, a time index, a missingness meaning, a manipulability flag, and a privacy class.

**Directed edge**: An asserted direct causal dependence between two nodes relative to the modelled variable set, carrying a source node, a target node, a temporal lag, an optional asserted sign, a mechanism statement, provenance, a proposing actor, a reviewing actor, and an acceptance status.

**Non-edge**: An asserted absence of direct causal dependence. Non-edges carry the same registration burden as edges, because exclusion restrictions do identification work and an unrecorded exclusion is an unexamined assumption.

**Assumption registry**: The versioned store linking every assumption to the edges, estimands, datasets, and diagnostics it affects, together with its category, its owner, its evidence, its testability, its status, and the consequence of its failure.

**Confounder**: A common cause of both the treatment and the outcome. Confounding is the default hypothesis for any proposed causal link in this guide, not an exception to be raised where a reviewer happens to think of one.

**Collider**: A variable caused by two or more modelled variables. Conditioning on a collider or on a descendant of a collider opens a non-causal path and induces selection bias, which is why adjusting for every available covariate is prohibited.

**Mediator**: A variable on a directed path from treatment to outcome. Adjusting for a mediator removes part of the total effect and answers a different question than the one usually asked.

**Forbidden control**: Any covariate the identification strategy prohibits from entering the adjustment set, including mediators, colliders, descendants of treatment, and selection variables. The forbidden-control list is emitted by the identification engine and enforced by the estimation tier.

**Estimand**: The precisely defined target quantity, naming the population, the unit, the treatment versions, the comparator, the outcome, the time zero, the follow-up horizon, the aggregation, and the effect scale. An accurate estimate of one estimand does not answer a request for another.

**Identification**: The question of whether the target estimand is uniquely determined by the available observational or experimental distributions under the stated structure and assumptions. Identification precedes estimation and no estimator repairs its failure.

**Estimation**: The question of how to infer an already identified quantity from finite, noisy data.

**Identification certificate**: The machine-readable record emitted before any estimator is fitted, carrying the target estimand, the structure version, the data regimes available, the assumptions invoked, the identifying functional or adjustment set, the forbidden-control list, the unsupported assumptions, and the engine result.

**Consistency**: The assumption connecting an observed outcome to the outcome that would have arisen under the treatment actually received, which requires that treatment versions be unambiguous.

**Exchangeability**: The assumption that, conditional on the chosen covariates, treatment assignment is independent of the relevant potential outcomes.

**Positivity**: The requirement that every compared treatment has a non-zero probability of occurring at every covariate profile in the target population. Positivity failure is a data property, not a modelling preference, and it is not repaired by extrapolation.

**Interference**: The condition in which one unit's treatment affects another unit's outcome. Unmodelled material interference invalidates the estimand rather than merely widening its interval.

**Markov equivalence class**: The set of structures encoding the same conditional independences. Observational data commonly identify only the class, so a single favoured structure returned by a discovery algorithm is a hypothesis and not a finding.

**Refutation**: A deterministic test whose expected result is known in advance under the stated assumptions, such as a placebo treatment, a dummy outcome, a random common cause, or a data-subset perturbation. A refutation cannot confirm a causal claim; it can only fail to overturn it.

**Sensitivity threshold**: A quantified statement of how strong an unmeasured confounder would have to be to overturn the conclusion, reported for the point estimate and for the confidence limit nearest the null.

**Abstention**: A declared terminal outcome in which the system returns the association it can support, names the specific missing assumption, variable, or design, and issues no causal claim. Abstention is a success state of this framework, not a failure.

**Causal lineage**: The append-only record linking the task contract, structure versions, assumption versions, identification certificate, dataset snapshots, estimator configurations, refutation results, downgrades, and approvals for one run.

### 1.2 The Three Query Levels and What Each Demands

The three levels are ordered, and the ordering is strict: the evidence sufficient for one level is necessary but never sufficient for the level above it. Agents must classify the incoming question into exactly one level before proposing any structure, because the level fixes the evidence the run must obtain and the outputs the run is permitted to emit.

**Level 1, association**: The question asks what is observed together. Its evidence demand is a measured joint or conditional distribution over named recorded fields, with the sampling frame, the inclusion criteria, and the selection process recorded alongside it. Observational data alone satisfy this level. The permitted surface forms are limited: an association claim may not be phrased with an interventional verb, and the deterministic tier rejects any claim whose text carries a verb from the closed interventional list (causes, increases, reduces, drives, improves, worsens, prevents, produces, leads to) while its evidence class supports only association.

**Level 2, intervention**: The question asks what happens if a variable is actively set rather than passively observed. Its evidence demand is one of three artifacts: a controlled experiment in which assignment is under analyst control, a natural experiment whose as-if-random variation has passed its design-specific falsification tests, or an identification certificate naming a strategy together with every assumption that strategy invokes. Answering a level-2 question from purely observational evidence without a named identification strategy is prohibited without exception. The prohibition is not a preference for experiments: much of observational causal inference exists precisely to identify interventional quantities from observational distributions under explicit assumptions, and the rule requires only that those assumptions be named, recorded, and owned rather than assumed silently.

**Level 3, counterfactual**: The question asks what would have happened for a specific unit or context had a different action been taken, conditional on what actually occurred. Its evidence demand is everything level 2 demands, plus a structural model that determines the requested cross-world quantity, plus the three-step computation executed against that model: abduction updates beliefs about the exogenous disturbances from the observed case, action replaces the structural mechanism for the intervened variable, and prediction propagates the modified model while preserving the abducted background state. Where the cross-world quantity is not determined by the model and the available data, the permitted outputs are the corresponding population interventional quantity, a partial-identification bound, a model-dependent simulation carrying that label, or abstention. Collapsing these four into a single counterfactual answer is a defect.

**Question well-formedness**: A level-3 question must name the intervention, the unit or context, and the time at which the alternative action would have been taken. A question of the form asking whether some factor caused an outcome, with no intervention named, is underspecified and is rejected at intake rather than answered. Attribution questions must additionally declare whether the target is a contributing, necessary, or sufficient cause, since those are different quantities with different identification requirements.

**Prediction routing**: Where the question concerns forecasting under an unchanged process, ranking, classification, or ordinary feature importance, the run terminates at intake and routes to predictive modelling. Wrapping a predictive artifact in causal vocabulary is the most common way an unsupported causal claim enters a system, and the intake classifier exists to stop it.

### 1.3 The Stated-Basis Rule and the Evidence-Class Ladder

A language model asked a causal question produces a fluent causal story whether or not the evidence supports one, because causal language is abundant in the text such models are trained on. Fluency therefore carries no information about identification, and no downstream check that inspects only the wording of a claim can separate the two cases. The framework's response is a single hard rule.

**The stated-basis rule**: A causal claim is admissible only where its basis is named from the closed four-valued vocabulary: a controlled experiment, a natural experiment, an identification strategy with its assumptions recorded, or domain knowledge encoded as an explicit causal structure. A causal claim with no stated basis is an association claim wearing causal words. It is relabelled as an association claim and re-emitted at that level. It is never retained as a causal claim with a qualifier attached.

**Evidence classes and the query levels they support**:

| Evidence class | What must be on record | Maximum supported query level |
| :-- | :-- | :-- |
| **E0 Unsupported assertion** | A proposition with no data reference and no registered structure | None; emitted as a hypothesis only |
| **E1 Observed association** | A measured distribution over named fields, with sampling frame and selection process recorded | Association |
| **E2 Registered structure** | An explicit causal structure with every edge and non-edge registered and owned, but no identification certificate | Association; intervention only as a labelled model-dependent simulation |
| **E3 Observational identification** | An identification certificate naming a strategy, its identifying functional or adjustment set, its forbidden controls, and its assumptions | Intervention |
| **E4 Natural experiment** | E3 plus as-if-random variation and passed design-specific falsification tests | Intervention, for the population the design identifies |
| **E5 Controlled experiment** | Analyst-controlled assignment, a pre-declared analysis, and passed randomisation-integrity checks | Intervention, for the randomised population |
| **E6 Counterfactual identification** | E3, E4, or E5 plus a structural model determining the requested cross-world quantity | Counterfactual |

**The level-evidence check**: For every claim, the deterministic tier asserts that the declared query level does not exceed the maximum level the recorded evidence class supports. The check runs on the machine-readable claim record, not on its prose rendering, and it runs before release rather than as a review comment.

**Downgrade protocol**: A failed check produces a downgrade, applied automatically and recorded in lineage with a reason code. A level-2 claim resting on E1 or E2 is re-emitted at association level with reason code NO_IDENTIFICATION and the missing strategy named. A level-3 claim resting on E3, E4, or E5 is re-emitted at intervention level with reason code NO_CROSS_WORLD, or, where a structural simulation was actually run, re-emitted as a model-dependent simulation carrying that label. Any claim resting on E0 is suppressed as a claim and emitted as a hypothesis with reason code NO_BASIS. A prose caveat never substitutes for a downgrade: 100 percent of released claims carry a machine-readable level field and evidence-class field, and 0 released claims may rely on a natural-language qualifier to convey their level. Downgrade rate is reported rather than minimised, because a system optimising for a low downgrade rate is a system that has learned to overclaim upstream.

### 1.4 The Execution-Tier Partition

The framework divides work across three execution tiers, and the division is load-bearing rather than advisory. Every phase in Section II is assignable to a tier, and every step that crosses tiers names the handoff.

**Deterministic tier**: Software, scripts, graph engines, schema validators, and statistical libraries own everything requiring exactness, reproducibility, or auditability. This tier owns structure representation, storage, versioning, hashing, and diffing; acyclicity and temporal-order checking; assumption recording with owner, status, and expiry; d-separation testing and identification-engine execution; the forbidden-control list and its enforcement inside every estimator fit; overlap and positivity computation; estimator fitting and uncertainty computation; refutation execution and sensitivity computation; evidence-class labelling per claim; the level-evidence check and the downgrade it triggers; and lineage logging and release-gate evaluation. The deterministic tier rejects any structure containing an unexplained cycle, any estimator configuration containing a forbidden control, any claim whose declared level exceeds its evidence class, and any release lacking a certificate, a passed refutation battery, and a sensitivity threshold.

**Model tier**: Language-model inference owns everything requiring open-vocabulary judgement over natural language. This tier proposes candidate variables and their definitions; proposes candidate directed edges and non-edges together with the mechanism each asserts; proposes candidate common causes, selection mechanisms, treatment versions, interference channels, and measurement processes; translates domain narratives, retrieved literature, and incident records into structured proposals; generates competing structures, negative-control candidates, and alternative explanations for an observed pattern; and renders the released result into plain language. Every model output entering the run is a proposal carrying a provenance record, never a decision.

**Hybrid tier**: The model proposes a causal claim, and a deterministic check verifies that the claim's recorded evidence class supports the level asserted, downgrading it where the check fails. The same pattern governs structure acceptance, where the model proposes an edge and the graph engine tests whether the resulting structure remains acyclic and whether the edge is required for identification; confounder handling, where the model enumerates candidate common causes and the engine classifies each as adjustable, forbidden, or unresolved; and result communication, where the model drafts the narrative and the deterministic tier verifies that every causal verb in it maps to a claim record whose level supports that verb.

**Authority on disagreement**: The deterministic tier holds authority on every question of structure validity, identification status, evidence class, query level, numeric value, and release. The model tier holds authority on no release-affecting question. A model assertion that a structure is correct, that an effect is identified, that a confounder is absent, or that a refutation passed has no standing without the corresponding deterministic artifact.

**Tier ownership by artifact**:

| Artifact | Proposing tier | Deciding tier | Never decided by the model tier |
| :-- | :-- | :-- | :-- |
| **Candidate node set and definitions** | Model | Deterministic schema validation against the data dictionary | Whether a variable is measured |
| **Directed edges and non-edges** | Model | Deterministic acyclicity, temporal-order, and ontology checks | Whether an edge enters the released structure |
| **Candidate confounders** | Model | Deterministic role classification against the structure | Whether a confounder can be ruled out |
| **Identification strategy** | Model shortlist | Formal identification engine | Whether the estimand is identified |
| **Adjustment set and forbidden controls** | Not proposed | Identification engine, enforced at fit time | Any membership decision |
| **Point estimate and interval** | Not proposed | Statistical library | Any numeric value |
| **Refutation and sensitivity results** | Not proposed | Refutation harness | Whether a refutation passed |
| **Claim level and evidence class** | Model draft level | Level-evidence check | The final level of any released claim |

***

## II. Operational Framework: Identified Causal Claims Under Stated-Basis Enforcement

The framework assumes intake has classified the question as causal rather than predictive. Phases 1 through 4 run in sequence and gate one another: no structure is elicited before the contract is fixed, no identification is attempted before the structure is validated, and no estimator is fitted before a certificate exists. Phase 5 and Phase 6 may return control to Phase 2, Phase 3, or Phase 4 under the bounded re-modelling rules stated in Step 6.3, and every return preserves the failed artifacts rather than replacing them.

### Phase 1: Query Classification and Causal Task Contract

**Objective**: Fix the query level, the target quantity, and the evidence regime available before any structure is proposed, so that the run's permitted outputs are bounded by declaration rather than discovered at release.

#### Step 1.1: Classify the Query Level and Route Non-Causal Questions Out

**Required Actions**:

- Parse the incoming question into one of four intake verdicts: association, intervention, counterfactual, or predictive.
- Route every predictive verdict out of this framework to predictive modelling, recording the routing decision and its reason.
- Reject any counterfactual question that fails well-formedness, returning the missing element rather than an answer; a well-formed counterfactual question names the intervention, the unit or context, and the time of the alternative action.
- Require any attribution question to declare whether its target is a contributing, necessary, or sufficient cause, and treat an undeclared attribution question as underspecified.
- Record the declared level in a machine-readable field that later steps read, rather than inferring it from the question text a second time.

**Required Outputs**:

- One intake verdict record carrying the declared query level and its justification.
- A routing decision for every non-causal question, naming the destination method.
- A rejection record for every ill-formed question, naming the missing element.

**Quality Checkpoints**:

- Exactly 1 query level is declared per run; a run carrying 0 or more than 1 declared level halts before Phase 2.
- Every predictive question is routed out; 0 predictive questions reach structure elicitation.
- Every counterfactual question on record names an intervention, a unit or context, and a time.

***

#### Step 1.2: Fix the Causal Task Contract

**Required Actions**:

- Record the unit, the population, the treatment or intervention, the treatment versions, the comparator, the outcome, the time zero, the follow-up window, the aggregation, and the effect scale.
- Name the estimand family explicitly, distinguishing an average effect over the whole population from an average over the treated, from a conditional effect varying by covariates, from a local effect over the subpopulation a design identifies, from a direct or indirect effect, and from a dynamic-regime effect.
- Record the intended action the answer will inform, the decision owner, and the risk tier, drawn from a closed vocabulary of at least three tiers.
- Record the latency cap, the monetary cap, and the compute cap, each as a number, and the behaviour on exhaustion.
- Declare the abstention behaviour: what is returned, to whom, and in what form, where no causal claim survives the release gate.
- Freeze the contract under a version identifier and hash before Phase 2 opens.

**Required Outputs**:

- A versioned causal task contract record with every field populated.
- A named estimand with its family, population, and effect scale.
- A budget ledger naming each bounded resource and its numeric limit.

**Quality Checkpoints**:

- Treatment versions and outcome timing are unambiguous; an ambiguous treatment version halts the run, because a contrast between undefined interventions cannot be estimated.
- Every budget dimension carries a numeric limit; an unbounded dimension halts the run.
- The estimand names a population and an effect scale, so that an estimate answering a different target is detectable by comparison rather than by reading.

***

#### Step 1.3: Decide Between Experiment, Observation, and Abstention

**Required Actions**:

- Assess whether a randomised experiment is ethical, legal, operationally feasible, adequately powered, and representative of the target decision; where all five hold, route to experiment design rather than observational analysis.
- Enumerate the data regimes actually available: randomised assignment, natural or quasi-experimental variation, longitudinal observational records, cross-sectional observational records, and domain knowledge alone.
- Record for each regime the highest evidence class it could support, using the ladder in Section 1.3.
- Compare the highest achievable evidence class against the declared query level, and halt the run at this step where the achievable class cannot support the level.
- Where the achievable class cannot support the level, return the specific missing design, variable, or assumption rather than a best-effort number.
- Restrict the run to hypothesis elicitation, candidate structures, and a measurement plan where the only available input is unstructured text with no validated data and no formal engine.

**Required Outputs**:

- A feasibility record covering the five experiment criteria with a verdict on each.
- A data-regime inventory with the maximum evidence class achievable from each regime.
- A go, route-to-experiment, or abstain decision with its reason code.

**Quality Checkpoints**:

- The maximum achievable evidence class is recorded before any structure is elicited, so that an unachievable level is caught at cost near zero rather than after estimation.
- A run whose achievable evidence class supports a lower level than declared either lowers the declared level or abstains; it never proceeds at the declared level in the expectation that identification will appear later.
- Every abstention record names a specific missing assumption, variable, or design, and 0 abstention records consist only of a statement that the data were insufficient.

***

### Phase 2: Causal Structure Elicitation and Assumption Registration

**Objective**: Convert implicit causal beliefs into an explicit, versioned artifact of nodes, directed edges, and non-edges, each carrying the assumption it rests on and an owner, so that the structure can be inspected and challenged rather than argued about in prose.

#### Step 2.1: Propose the Candidate Structure as an Explicit Artifact

**Required Actions**:

- Retrieve domain evidence covering mechanisms, prior experiments, measurement definitions, ontologies, and incident records, recording for each retrieved item a document identifier, a version, a location, a timestamp, an access decision, a content hash, and the cited span.
- Instruct the model tier to propose a time-ordered structure naming observed nodes, latent nodes, selection nodes, the treatment, mediators, the outcome, and measurement nodes as distinct node types.
- Require at least 2 competing structures wherever the domain admits a substantively different account, and preserve every competing structure rather than selecting one at this step.
- Supply causal discovery output, where a validated engine is available, as an additional proposal source only, recording the algorithm, its assumptions, its score, and the bootstrap edge-selection frequency for every proposed edge.
- Mark every discovered edge whose bootstrap selection frequency falls below 0.60 as unresolved, and never treat a discovery output as a finding, since observational data commonly determine only a Markov equivalence class rather than a single structure.
- Treat every retrieved claim and every model proposal as evidence to assess rather than as an edge to accept, and treat retrieval frequency as no evidence of edge strength.

**Required Outputs**:

- A candidate structure set with 1 to 4 entries, each versioned and hashed.
- A node inventory with type, definition, ontology identifier, unit, measurement process, time index, and data field or latent marker per node.
- A retrieval evidence set with full provenance per item.

**Quality Checkpoints**:

- Every node maps to a data field or carries an explicit latent marker; 0 nodes remain unmapped and unmarked.
- Every discovery-proposed edge carries an algorithm, an assumption set, and a bootstrap frequency; discovery output carrying none of these is rejected as a proposal source.
- Competing structures are preserved rather than merged, so that structural uncertainty remains visible to Phase 4.

***

#### Step 2.2: Register Every Edge and Non-Edge with an Owned Assumption

**Required Actions**:

- Record for every directed edge the source node, the target node, the structure version, the relation type, the temporal lag, the asserted sign where one is claimed, the mechanism statement, the provenance, the proposing actor, the reviewing actor, the confidence category, and the acceptance status.
- Record every non-edge with the same fields, because an exclusion restriction does identification work and an unrecorded exclusion is an unexamined assumption.
- Assign every assumption a category drawn from the closed set of consistency, exchangeability, positivity, no-interference, exclusion, monotonicity, faithfulness, functional form, missingness, transportability, and measurement validity.
- Assign a named owner and a review date to every assumption that is required for identification, and record the consequence of the assumption's failure.
- Record for each assumption whether it is testable from the available data, and where it is, name the diagnostic that will test it in Phase 5.
- Version the registry alongside the structure, so that an edge change invalidates every descendant artifact that consumed it.

**Required Outputs**:

- An assumption registry with one record per edge, per non-edge, and per design assumption.
- An owner assignment covering 100 percent of identification-critical assumptions.
- A testability classification per assumption with a named diagnostic where testable.

**Structure record template**:

```
EDGE_ID:
STRUCTURE_VERSION:
SOURCE_NODE:
TARGET_NODE:
RELATION_TYPE:
TEMPORAL_LAG:
MECHANISM_STATEMENT:
ASSUMPTION_IDS:
ASSUMPTION_CATEGORY:
REQUIRED_FOR_IDENTIFICATION:
PROVENANCE:
PROPOSING_ACTOR:
REVIEWING_ACTOR:
BOOTSTRAP_FREQUENCY:
CONFIDENCE_CATEGORY:
ACCEPTANCE_STATUS:
FAILURE_CONSEQUENCE:
```

**Quality Checkpoints**:

- 100 percent of identification-critical assumptions carry an owner, a provenance record, a status, and a review date; any gap blocks entry to Phase 4.
- Every accepted edge and every accepted non-edge carries at least 1 assumption record; an edge with no assumption is a belief rather than a modelled claim and is rejected.
- Assumption categories are drawn from the closed set; a free-text category is rejected at registration.

***

#### Step 2.3: Run Deterministic Structure Validation

**Required Actions**:

- Execute an acyclicity check over every candidate structure, and reject any structure containing a cycle that is not represented explicitly as a temporal, cyclic, or equilibrium construct.
- Execute a temporal-order check asserting that no edge points backward in recorded time and that every lag is consistent with the declared time zero and follow-up window.
- Execute a schema and ontology check asserting that every node identifier resolves, that units and value ranges are consistent across edges, and that no two nodes silently denote the same measured field.
- Run at least 2 adversarial review rounds in which reviewers are asked specifically for omitted common causes, interference channels, unmodelled treatment versions, measurement processes, feedback loops, and selection mechanisms.
- Terminate elicitation when 2 consecutive review rounds add 0 critical nodes and 0 critical edges, and cap the loop at 3 structure revisions, 2 retrieval rounds, and 1 domain escalation.
- On cap exhaustion without convergence, preserve every competing structure and carry structural uncertainty forward to Phase 4 rather than selecting a favourite.

**Required Outputs**:

- A validation report with a pass or fail verdict per check per candidate structure.
- An adversarial review log naming each round, its reviewers, and the nodes and edges it added.
- An approved candidate structure set, or an abstention record where no structure passes validation.

**Quality Checkpoints**:

- 0 unexplained cycles survive into Phase 3; a cycle without an explicit temporal or equilibrium representation halts the run.
- Every candidate structure passes the schema, ontology, and temporal-order checks before Phase 3 opens.
- Elicitation terminated either on the 2-consecutive-quiet-round condition or on a stated cap, and the terminating condition is recorded.

***

### Phase 3: Confounder Enumeration and Covariate Role Classification

**Objective**: Treat a common cause as the default explanation of any proposed causal link, challenge every link before it is accepted, and cap the achievable evidence class where a confounder cannot be ruled out.

#### Step 3.1: Enumerate Candidate Common Causes Adversarially

**Required Actions**:

- Open every proposed treatment-outcome link with the default hypothesis that the association it predicts is produced by a common cause, and require the link to survive challenge before it is accepted.
- Instruct the model tier to enumerate at least 5 candidate common causes for each treatment-outcome pair, naming for each one the mechanism by which it would affect treatment and the mechanism by which it would affect the outcome.
- Obtain candidates from at least 2 independent proposal sources, such as a model proposal and a domain reviewer, or a model proposal and a retrieval pass over prior studies, and record the source class of each candidate.
- Enumerate selection mechanisms separately from confounders, naming what determines sample membership and whether membership depends on treatment, outcome, or both.
- Enumerate measurement processes separately, naming for treatment and outcome whether the recorded field is the construct or a proxy for it, and what the error structure of that proxy is.
- Enumerate interference channels separately, naming any route by which one unit's treatment could affect another unit's outcome.

**Required Outputs**:

- A candidate confounder inventory with at least 5 entries per treatment-outcome pair, each carrying two mechanism statements and a source class.
- A selection-mechanism inventory and an interference-channel inventory.
- A measurement record per treatment and outcome variable naming construct, proxy, and error structure.

**Quality Checkpoints**:

- Every accepted treatment-outcome link has completed a challenge round; 0 links are accepted without one.
- Candidate confounders derive from at least 2 independent source classes; a single-source enumeration is recorded as incomplete and blocks Phase 4.
- Fewer than 5 candidates for a pair triggers a second enumeration pass before the link may be accepted.

***

#### Step 3.2: Classify Every Covariate as Adjustable, Forbidden, or Unresolved

**Required Actions**:

- Locate every candidate covariate in the approved structure and derive its role from the structure rather than from its name or its apparent predictive value.
- Classify each covariate into exactly 1 disposition: required in the adjustment set, optional, forbidden, or unresolved because the variable is unmeasured and no acceptable proxy exists.
- Emit the forbidden-control list as a machine-readable artifact consumed by every downstream estimator fit, so that a forbidden covariate cannot enter a model through a configuration change.
- Reject the practice of adjusting for every available covariate, and record any request to do so as a defect rather than a preference.
- Record for each unresolved covariate whether a measured proxy exists, what its expected fidelity is, and what residual bias remains after the proxy is used.

**Covariate role and its adjustment disposition**:

| Role in the structure | Adjustment disposition | Consequence of the wrong disposition |
| :-- | :-- | :-- |
| **Pre-treatment common cause of treatment and outcome** | Required where measured | Omission leaves confounding bias of unknown sign |
| **Affects treatment, excluded from the outcome path** | Excluded from the adjustment set | Adjustment can amplify residual confounding bias |
| **Mediator on a directed path from treatment to outcome** | Forbidden where the target is a total effect | Adjustment removes part of the effect being estimated |
| **Collider on a path between treatment and outcome** | Forbidden | Adjustment opens a non-causal path and induces selection bias |
| **Descendant of treatment** | Forbidden | Adjustment blocks part of the treatment process |
| **Selection indicator determining sample membership** | Modelled explicitly, never adjusted implicitly | Ignoring it leaves selection bias with no diagnostic |
| **Outcome predictor unrelated to treatment** | Optional | No bias effect; large sets may worsen overlap |
| **Unmeasured common cause with no acceptable proxy** | Not adjustable | Caps the achievable evidence class at E2 unless a design neutralises it |

**Required Outputs**:

- A covariate disposition table covering 100 percent of candidate covariates.
- A machine-readable forbidden-control list bound to the structure version.
- An unresolved-confounder ledger with proxy availability and residual bias per entry.

**Quality Checkpoints**:

- Every covariate carries exactly 1 disposition derived from the structure; a disposition justified by predictive performance is rejected.
- The forbidden-control list is enforced at fit time rather than at review time; an estimator configuration containing a forbidden control fails before it runs.
- Temporal precedence alone never justifies a required disposition, since reverse causation, common causes, selection, and measurement timing can all preserve temporal order while defeating the intended claim.

***

#### Step 3.3: Resolve, Bound, or Downgrade on Unresolved Confounders

**Required Actions**:

- Attempt resolution of each unresolved confounder in a fixed order: obtain the measurement, substitute a validated proxy, adopt a design that neutralises the confounder, restrict the target population to a stratum where the confounder is constant, or narrow the estimand.
- Cap resolution attempts at 2 per unresolved confounder, and record the attempted remedies and their outcomes.
- Where resolution fails and no design neutralises the confounder, cap the achievable evidence class at E2 and apply the downgrade protocol from Section 1.3 to every claim that would have depended on it.
- Record the downgrade with reason code UNRESOLVED_CONFOUNDER, naming the confounder, its two mechanism statements, and the measurement or design that would resolve it.
- Never resolve an unresolved confounder by adding an assumption that exists only because it produces identification, and record any such proposal as a defect.
- Carry the surviving association claim forward with its full provenance rather than discarding it, so that the run returns usable information alongside its refusal to make a causal claim.

**Required Outputs**:

- A resolution record per unresolved confounder naming the attempted remedies and the outcome.
- A downgrade record for every claim capped by an unresolved confounder.
- A remediation request naming the specific measurement or design that would lift the cap.

**Quality Checkpoints**:

- 0 claims proceed to Phase 4 at intervention level while an unresolved confounder remains unaddressed by measurement, proxy, design, restriction, or estimand change.
- Every downgrade names the confounder and the remedy that would lift it; a downgrade with no named remedy is incomplete.
- No assumption enters the registry at this step whose sole justification is that it restores identification.

***

### Phase 4: Identification Strategy Selection and Certification

**Objective**: Determine whether the declared estimand is uniquely determined by the available distributions under the approved structure, and emit a machine-readable certificate before any estimator is fitted.

#### Step 4.1: Select an Identification Strategy in Priority Order

**Required Actions**:

- Query a formal identification engine for each approved structure and the exact declared estimand, rather than accepting a model-generated identification argument.
- Attempt strategies in priority order: randomised assignment first, then valid backdoor adjustment, then frontdoor identification, then instrumental-variable designs, then regression discontinuity, difference-in-differences, and synthetic control, then longitudinal g-methods for time-varying treatment with confounding affected by prior treatment, then partial-identification bounds.
- Test every conditional-independence claim the strategy relies on mechanically through a d-separation check over the structure, and reject any independence claim asserted only in natural language.
- Record for the selected strategy the exact population it identifies, which may be narrower than the declared target population.
- Halt and return to Step 1.2 where the identified population differs from the declared target population, rather than reporting a local quantity as though it were a population average.

**Identification strategies and what each invokes**:

| Strategy | Variation exploited | Assumptions invoked | Population identified |
| :-- | :-- | :-- | :-- |
| **Randomised assignment** | Analyst-controlled assignment | Consistency, no interference, a declared adherence target | The randomised population |
| **Backdoor adjustment** | Measured pre-treatment covariates | Conditional exchangeability on the adjustment set, positivity, consistency | The target population where overlap holds |
| **Frontdoor adjustment** | A fully mediating measured mechanism | Complete mediation, no unblocked mediator-outcome confounding, no unmediated direct effect | The target population |
| **Instrumental variable** | Variation reaching the outcome only through treatment | Relevance, exclusion, independence, and monotonicity | Compliers, not the whole population |
| **Regression discontinuity** | Assignment around a fixed threshold | Continuity at the cutoff, absence of precise manipulation | Units near the cutoff |
| **Difference-in-differences** | Outcome change across treated and comparison groups | A defensible counterfactual trend, with staggered adoption handled beyond a naive two-way fixed-effect specification | Treated units over the studied window |
| **Synthetic control** | A weighted comparison built from a donor pool | Credible donor pool, adequate pre-treatment fit, no interference among donors | The treated aggregate |
| **Longitudinal g-methods** | Sequential exposure under time-varying confounding | Sequential exchangeability, consistency, and positivity at each time point | The target population under a declared regime |
| **Partial identification** | Whatever the data support without a point target | Only the stated shape restrictions | The target population, as an interval |

**Required Outputs**:

- A strategy attempt log recording each strategy tried, its engine verdict, and its failure reason where it failed.
- A selected strategy with its identifying functional or adjustment set and its identified population.
- A mechanical d-separation result for every independence claim the strategy invokes.

**Quality Checkpoints**:

- The identification verdict originates from a formal engine; a model-generated proof is never accepted as a verdict.
- The identified population is recorded and compared against the declared target; a mismatch halts rather than being carried as a footnote.
- Instrumental-variable, discontinuity, and synthetic-control results are recorded as local quantities, and 0 local quantities are released under a population-average label.

***

#### Step 4.2: Emit and Verify the Identification Certificate

**Required Actions**:

- Emit a machine-readable certificate carrying the estimand identifier, the structure version and hash, the assumption-set version, the data regimes available, the strategy, the identifying functional or adjustment set, the forbidden-control list, the unsupported assumptions, the identified population, and the engine version.
- Bind the certificate to the exact structure hash, so that any subsequent edge change invalidates it automatically rather than silently.
- Record every assumption the strategy invokes that is untestable from the available data, and mark it for sensitivity analysis in Step 6.2.
- Assign the run's evidence class from the certificate and the data regime, using the ladder in Section 1.3, and write it into the claim record.
- Block entry to Phase 5 for any estimand lacking a certificate, and treat the absence of a certificate as a terminal condition for that estimand rather than a warning.

**Identification certificate template**:

```
CERTIFICATE_ID:
ESTIMAND_ID:
STRUCTURE_VERSION:
STRUCTURE_HASH:
ASSUMPTION_SET_VERSION:
DATA_REGIMES_AVAILABLE:
STRATEGY:
IDENTIFYING_FUNCTIONAL:
ADJUSTMENT_SET:
FORBIDDEN_CONTROLS:
ASSUMPTIONS_INVOKED:
UNTESTABLE_ASSUMPTIONS:
IDENTIFIED_POPULATION:
ENGINE_NAME_AND_VERSION:
ASSIGNED_EVIDENCE_CLASS:
RESULT:
```

**Required Outputs**:

- One identification certificate per estimand, bound to a structure hash.
- An untestable-assumption list flagged for sensitivity analysis.
- An assigned evidence class written into the claim record.

**Quality Checkpoints**:

- 100 percent of estimands entering Phase 5 carry a certificate; 0 estimators are fitted without one.
- Every certificate is bound to a structure hash, so a structure revision invalidates it without human intervention.
- The assigned evidence class is derived from the certificate and the data regime, never from the confidence of the component that proposed the claim.

***

#### Step 4.3: Handle Identification Failure Within Bounded Fallbacks

**Required Actions**:

- Diagnose the specific cause of an identification failure, distinguishing an unmeasured confounder, a positivity failure, an invalid exclusion, an unmodelled selection mechanism, an unmodelled interference channel, and a misdeclared estimand.
- Attempt at most 2 substantively distinct fallbacks per estimand, drawn from adding an actually measured covariate, switching to a valid natural-experiment design, narrowing the target population to restore overlap, redefining the estimand, or requesting an experiment.
- Cap the phase at 3 total strategies per estimand, counting the initial attempt and both fallbacks.
- Prohibit adding an assumption solely because it produces identification, and prohibit switching regressors as a response to non-identification, since neither changes what the data determine.
- On exhaustion, exit to one of four terminal states: data collection, experiment design, a bounded conclusion using partial identification, or explicit abstention with the missing requirement named.
- Record the terminal state and its reason code in lineage, and preserve every failed strategy attempt rather than deleting it.

**Required Outputs**:

- A failure diagnosis naming the specific cause rather than the symptom.
- A fallback log with at most 2 entries per estimand and their outcomes.
- A terminal-state record naming one of the four permitted exits.

**Quality Checkpoints**:

- No estimand exceeds 3 identification attempts; the fourth attempt is refused rather than approved with a note.
- 0 assumptions are added whose only support is that identification follows from them.
- Every exhausted estimand terminates in one of the 4 declared exits, and none terminates in a best-effort estimate.

***

### Phase 5: Data Audit, Estimation, and Claim Generation

**Objective**: Confirm that the data support the certified strategy, produce estimates under redundant estimators, and emit each claim through the level-evidence check that downgrades it where its evidence is insufficient.

#### Step 5.1: Audit Data and Design Against the Certificate

**Required Actions**:

- Freeze a versioned data snapshot with a content hash, and verify provenance, permitted use, unit integrity, treatment and outcome timestamps, missingness, censoring, duplicates, cluster structure, and leakage against it.
- Compute overlap globally and within every decision-critical slice named in the contract, summarising the treatment-probability distribution and the tail behaviour of any weights the strategy implies.
- Halt where the estimated treatment probability falls outside the interval 0.05 to 0.95 for more than 5 percent of the target population, and either narrow the population, change the estimand, or abstain.
- Halt where more than 1 percent of implied weights exceed a factor of 10 relative to the median weight, since extreme weights indicate that the comparison rests on a small number of units.
- Run design-specific checks: manipulation testing and density continuity for discontinuity designs, pre-trend testing for difference-in-differences, donor-pool quality and pre-treatment fit for synthetic control, and instrument strength and exclusion plausibility for instrumental-variable designs.
- Freeze all preprocessing before any outcome is inspected, and never use outcome data to tune the design.

**Required Outputs**:

- A data audit report with a verdict per audited property.
- An overlap report covering the whole target population and every decision-critical slice.
- A design diagnostic report with a verdict per design-specific check.

**Quality Checkpoints**:

- Preprocessing is frozen before outcome inspection; any outcome-informed design change invalidates the run and returns it to Phase 4.
- Overlap supports the declared population, or the population is narrowed and the estimand record is updated to match.
- At most 1 data repair cycle runs at this step; a second failure triggers re-identification or abstention and never authorises extrapolation into unsupported covariate regions.

***

#### Step 5.2: Estimate with Redundant Estimators

**Required Actions**:

- Fit 1 transparent baseline estimator and at least 1 further estimator whose dependence on nuisance models differs, so that a shared misspecification does not produce agreement by construction.
- Enforce the certificate's adjustment set and forbidden-control list at fit time, and fail any configuration that includes a forbidden control before it executes.
- Apply sample splitting or cross-fitting where the estimator requires it, cluster-aware uncertainty where units are dependent, and hyperparameter selection declared before fitting.
- Record per estimator the library and version, the method, the configuration hash, the outcome and treatment models, the covariates, the folds, the random seed, the trimming rule, the convergence status, the covariate balance before and after, the weight quantiles, the effective sample size, the point estimate, the standard error, and the interval.
- Cap the loop at 3 primary estimators and 1 hyperparameter repair per estimator, and preserve every rejected estimator with its rejection reason.
- Compare estimators only where they target the same estimand and the same population, and never average incompatible targets to manufacture the appearance of stability.

**Required Outputs**:

- An estimator inventory with a full configuration record and diagnostic set per entry.
- A stability report covering sign agreement, maximum absolute difference, maximum relative difference, and interval overlap.
- A rejection log preserving every discarded estimator and its reason.

**Quality Checkpoints**:

- At least 2 estimators with different nuisance dependence produced a result, or the run records why only 1 was feasible.
- Sign agreement across estimators targeting one estimand is 100 percent, and maximum relative difference does not exceed 25 percent against a declared non-zero denominator rule; breach routes the estimand to Phase 6 refutation with a disagreement flag.
- 0 estimator fits contain a forbidden control, verified mechanically rather than by review.

***

#### Step 5.3: Generate the Claim and Run the Level-Evidence Check

**Required Actions**:

- Emit each result as a machine-readable claim record carrying the declared query level, the assigned evidence class, the stated basis, the estimand, the identified population, the estimate, the interval, the assumptions invoked, and the untestable assumptions.
- Execute the level-evidence check on the claim record, asserting that the declared level does not exceed the maximum level the evidence class supports.
- Apply the downgrade protocol from Section 1.3 on failure, re-emitting the claim at the supported level with its reason code and its missing requirement, rather than attaching a qualifier to the original claim.
- Scan the natural-language rendering for interventional verbs and confirm that each maps to a claim record whose level supports that verb, rejecting the rendering where it does not.
- Label every counterfactual output as an identified population quantity, a partial-identification bound, a model-dependent simulation, or a qualitative scenario, and never merge these categories.
- Record the downgrade, where one occurred, in lineage with the claim identifier, the original level, the final level, and the reason code.

**Claim record template**:

```
CLAIM_ID:
DECLARED_QUERY_LEVEL:
ASSIGNED_EVIDENCE_CLASS:
STATED_BASIS:
CERTIFICATE_ID:
ESTIMAND_ID:
IDENTIFIED_POPULATION:
POINT_ESTIMATE:
UNCERTAINTY_INTERVAL:
ASSUMPTIONS_INVOKED:
UNTESTABLE_ASSUMPTIONS:
LEVEL_EVIDENCE_CHECK:
DOWNGRADE_APPLIED:
DOWNGRADE_REASON_CODE:
FINAL_QUERY_LEVEL:
```

**Required Outputs**:

- A claim record per result with every field populated.
- A level-evidence check verdict per claim.
- A downgrade record per failed check naming the original level, the final level, and the missing requirement.

**Quality Checkpoints**:

- 100 percent of claims carry a declared level, an assigned evidence class, and a stated basis; a claim missing any of the three is suppressed rather than released with a note.
- 0 released claims carry a declared level exceeding their evidence class, verified by the check rather than by reading.
- Every interventional verb in the released text maps to a claim record supporting that verb; an unmapped verb blocks release of the rendering.

***

### Phase 6: Refutation, Sensitivity Analysis, and Release

**Objective**: Attempt to overturn every surviving claim through tests whose expected results are known in advance, quantify how strong an unmeasured confounder would have to be to reverse the conclusion, and gate release on the full record.

#### Step 6.1: Execute the Refutation Battery

**Required Actions**:

- Run the negative-control family of refuters: a placebo treatment substituted for the real treatment, a dummy outcome substituted for the real outcome, an injected random common cause, and a negative-control exposure or outcome chosen to be causally irrelevant to the target pathway while sharing its relevant biases.
- Run the perturbation family: repeated data-subset refutation, bootstrap resampling, alternative defensible adjustment sets, and leave-one-cluster-out analysis where units cluster.
- Run the design-specific falsifications the certificate names, such as pre-trend tests, cutoff-density tests, donor-pool substitution, and over-identification tests where the design supplies more instruments than parameters.
- Declare the expected result and the pass rule for each refuter before it runs, and record the observed statistic, the interval, and the effect shift after it runs.
- Classify each refuter as critical or supporting, and record criticality before results are known, so that a critical failure cannot be diluted by a large number of supporting passes.
- Classify every failure by its cause into estimator failure, data failure, structure failure, assumption failure, or design failure, and route it accordingly.

**Required Outputs**:

- A refutation inventory with type, configuration, seed, expected result, pass rule, observed statistic, and verdict per entry.
- A criticality assignment recorded before execution.
- A failure classification per failed refuter naming its cause.

**Quality Checkpoints**:

- A placebo-treatment or dummy-outcome estimate passes only where its interval covers the null or its absolute magnitude is at most 10 percent of the primary estimate; a larger value is a critical failure.
- An injected random common cause shifts the primary estimate by at most 10 percent; a larger shift is a critical failure.
- Data-subset refutation across 50 draws at 80 percent sampling returns an estimate inside the primary interval for at least 90 percent of draws; below that threshold the estimand is routed to re-modelling.
- Critical refutation pass rate is 100 percent; a single critical failure blocks release regardless of the supporting pass count.

***

#### Step 6.2: Quantify Unmeasured-Confounding Sensitivity

**Required Actions**:

- Compute a sensitivity threshold stating how strong an unmeasured confounder's association with treatment and with outcome would have to be to move the conclusion to the null, and report it for both the point estimate and the confidence limit nearest the null.
- Select one sensitivity model per major bias family and one complement, and record which bias each model addresses, since distinct sensitivity models are not interchangeable and must not be collapsed into a single score.
- Compare the computed threshold against the strongest measured confounder association recorded in the assumption registry, and treat a threshold below that value as a failed sensitivity check.
- Where no measured comparator exists, apply the deployment default threshold of 1.25 on the association scale for claims in the highest risk tier, and record that the default was used rather than a domain-derived value.
- Apply design-appropriate sensitivity procedures for matched designs, and record the bound at which the conclusion changes sign or crosses the decision boundary.
- Report every sensitivity result directly, and never summarise a family of sensitivity models into a single robustness number.

**Required Outputs**:

- A sensitivity report with one threshold per bias family, stated for the estimate and the nearest confidence limit.
- A comparison record placing each threshold against measured confounder associations or against the recorded default.
- A decision-boundary statement naming the confounding strength at which the recommended action would change.

**Quality Checkpoints**:

- Every untestable assumption flagged in Step 4.2 has at least 1 sensitivity result addressing it; an unaddressed untestable assumption blocks release.
- Sensitivity thresholds are reported per bias family; 0 releases carry a single collapsed robustness score in place of the family results.
- Use of the 1.25 default rather than a domain-derived comparator is recorded explicitly in the release record.

***

#### Step 6.3: Apply the Release Gate and Bound Re-Modelling

**Required Actions**:

- Enter re-modelling only on a declared trigger: a critical refutation failure, estimator disagreement beyond the Step 5.2 tolerance, a non-null critical negative control, an overlap collapse, or new domain evidence contradicting the structure.
- Change only the diagnosed component during re-modelling, preserving the failed structure, certificate, and estimates in lineage rather than replacing them.
- Cap re-modelling at 2 complete cycles, and on exhaustion report the robust subset of conclusions, any justified bounds, and an explicit abstention from the unsupported causal claim.
- Evaluate the release gate over 10 conditions: an approved contract, a versioned structure and assumption set, an identification certificate, passed data and design diagnostics, at least 2 valid estimators within tolerance, a 100 percent critical refutation pass, a passed sensitivity comparison, a completed level-evidence check, a privacy and permitted-use review, and a named action authority.
- Require qualified human review before release for medical, legal, employment, credit, and policy decisions, for every level-3 claim, for every release relying on the recorded sensitivity default, and for every claim released after a downgrade.
- Return with the release the estimand in plain language, the estimate and its uncertainty, the identified population and time window, the core assumptions, the diagnostics, the sensitivity threshold, the unresolved alternatives, and whether the evidence is experimental, quasi-experimental, or observational.

**Required Outputs**:

- A release record covering all 10 gate conditions with a verdict on each.
- A re-modelling log naming the trigger, the changed component, and every invalidated descendant artifact.
- A released answer carrying its level, its basis, and its uncertainty, or an abstention record naming the missing requirement.

**Quality Checkpoints**:

- All 10 release conditions pass; a release with 9 passes and 1 documented exception is refused rather than approved with a caveat.
- Re-modelling did not exceed 2 complete cycles, and 0 failed analyses were deleted from lineage.
- A population-average estimate is never converted into deterministic individual advice; a release phrased as individual advice is blocked at this gate.

***

## III. Implementation Guidance for AI Agents

AI agents performing causal reasoning must follow systematic protocols ensuring that every causal claim carries a named basis, that the deterministic tier holds authority over identification and release, and that a claim exceeding its evidence is downgraded automatically rather than qualified in prose. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Intake and Contract Agent**: Classifies the query level, routes predictive questions out, rejects ill-formed counterfactual and attribution questions, and owns the versioned causal task contract, the estimand, the risk tier, and the budget ledger. It alone may amend the contract, and every amendment is versioned.
2. **Structure Proposal Agent**: Operates in the model tier. Proposes nodes, directed edges, non-edges, mechanisms, competing structures, candidate common causes, selection mechanisms, interference channels, and negative-control candidates. It proposes only, and its outputs carry provenance rather than authority.
3. **Graph Engine**: Operates in the deterministic tier. Performs acyclicity, temporal-order, ontology, and schema validation; executes d-separation tests; queries identification; emits the adjustment set, the forbidden-control list, and the certificate; and binds each certificate to a structure hash.
4. **Estimation Agent**: Operates in the deterministic tier. Freezes the data snapshot, audits provenance and timing, computes overlap and weight diagnostics, fits estimators under the certificate's constraints, and refuses any configuration containing a forbidden control.
5. **Refutation Agent**: Operates in the deterministic tier. Declares expected results and criticality before execution, runs the negative-control, perturbation, and design-specific families, computes sensitivity thresholds per bias family, and classifies each failure by cause.
6. **Claim Adjudicator**: Runs the level-evidence check on every claim record, applies the downgrade protocol, verifies that every interventional verb in the released rendering maps to a supporting claim record, and holds release authority. It may veto a release that any other component considers complete.
7. **Instrumentation Agent**: Writes the append-only causal lineage, enforces the disclosure boundary, and computes the metric set. It may withhold a release where lineage is incomplete.

**Reasoning Disclosure Boundary**: The instrumentation protocol preserves causal artifacts and prohibits retention of hidden reasoning content. This is a hard constraint applying to every component.

- Preserve the structure version, the assumption registry, the estimand, the identification certificate, the estimator configuration, the diagnostics, the refutation and sensitivity results, the downgrade record, and the decision record.
- Do not require, request, or persist private reasoning transcripts from any model component; the adjudicator requires artifacts and verdicts, not internal narration.
- Do not log raw sensitive rows as span attributes; store large artifacts in access-controlled object storage referenced by identifier and hash.
- Treat structures as sensitive material, since latent-variable hypotheses can expose protected attributes or organisational weaknesses.

**Execution Isolation**: Statistical code generated during a run executes in an ephemeral sandbox with no secrets, denied network egress, an allowlisted package set, read-only inputs, resource limits, and a recorded environment hash. Retrieved content is treated as untrusted data and never as instruction.

**Workflow Execution Pattern**:

```
STATE: Claim_Adjudication
INPUTS:
  1. Claim record set from Step 5.3
  2. Identification certificate bound to a structure hash
  3. Refutation and sensitivity results from Phase 6
ACTIONS:
  1. Recompute evidence class from certificate and data regime
  2. Compare declared query level against maximum supported level
  3. Apply downgrade where the comparison fails
  4. Map every interventional verb in the rendering to a claim record
VALIDATION:
  - stated_basis IN {experiment, natural_experiment, identification_strategy, structure}
  - declared_level <= max_supported_level(evidence_class)
  - certificate_structure_hash == current_structure_hash
  - critical_refutation_pass_rate == 1.0
  - unmapped_interventional_verbs == 0
  - reasoning_trace_persisted == FALSE
TRANSITIONS:
  IF all_validations_pass THEN next_state = Release_Gate
  IF declared_level > max_supported_level THEN next_state = Downgrade_And_Reemit
  IF certificate_hash_mismatch THEN next_state = Phase_4_Recertification
  IF critical_refutation_failed THEN next_state = Phase_6_Remodelling
  ELSE next_state = Abstention_Record
```

**Two-Phase Action Pattern**: Emit the intended claim with its declared level, its stated basis, and its evidence class without releasing it; validate it against the block above while no commitment has been made; release it only after validation passes, recording the adjudication in the same operation.

**Approval Gate**: Human authorisation is required before releasing any counterfactual claim, before releasing any claim in the highest risk tier, before releasing any claim whose sensitivity threshold falls below the recorded comparator or below the 1.25 default, before overriding an abstention, and before any single estimation pass projected to consume more than 40 percent of the remaining compute budget. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the contract, the structure, the assumption registry, and the certificate in durable storage, since a causal run commonly outlives one context window.
- Reference artifacts by identifier and hash rather than restating them, so that a stale copy cannot circulate alongside a revised original.
- Write a handoff record at every context boundary naming the contract version, the structure version, the certificate status, the completed phases, and the open triggers.
- Invalidate every descendant artifact automatically when a structure or assumption version changes, rather than relying on a component to notice the change.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Intake and Contract Integrity (After Phase 1)**

- **Automated Check**: Exactly 1 query level is declared; the estimand names a population, treatment versions, a comparator, an outcome, a time zero, a horizon, and an effect scale; every budget dimension carries a numeric limit; the maximum achievable evidence class is recorded and supports the declared level.
- **Agent Action on Pass**: Proceed to structure elicitation.
- **Agent Action on Failure**: Halt and return the contract defect; no elicitation effort is spent against an incomplete contract.
- **Human Review Trigger**: A declared level the available data regimes cannot support, or any task in the highest risk tier.

**Checkpoint 2: Structure Integrity (After Phase 2)**

- **Automated Check**: 0 unexplained cycles; 100 percent of nodes mapped to a data field or marked latent; 100 percent of edges and non-edges carrying an assumption record; 100 percent of identification-critical assumptions carrying an owner and a review date; the terminating condition of the elicitation loop recorded.
- **Agent Action on Pass**: Proceed to confounder enumeration.
- **Agent Action on Failure**: Return the specific unmapped nodes, unregistered edges, or unowned assumptions; re-run elicitation for those entries only.
- **Human Review Trigger**: A cycle that cannot be represented as a temporal or equilibrium construct, or exhaustion of the 3-revision cap without convergence.

**Checkpoint 3: Confounding Challenge Completeness (After Phase 3)**

- **Automated Check**: At least 5 candidate common causes per treatment-outcome pair from at least 2 source classes; every covariate carrying exactly 1 disposition derived from the structure; the forbidden-control list emitted and bound to the structure version; every unresolved confounder carrying a resolution record.
- **Agent Action on Pass**: Proceed to identification.
- **Agent Action on Failure**: Re-run enumeration for the deficient pairs, or apply the evidence-class cap and downgrade the affected claims.
- **Human Review Trigger**: An unresolved confounder with no proxy and no available design, where the decision cannot be deferred.

**Checkpoint 4: Identification Validity (After Phase 4)**

- **Automated Check**: A certificate exists for every estimand entering estimation; each certificate is bound to the current structure hash; every independence claim carries a mechanical d-separation result; the identified population matches the declared target or the estimand was updated; at most 3 strategy attempts were made.
- **Agent Action on Pass**: Proceed to the data audit.
- **Agent Action on Failure**: Halt the estimand; route it to data collection, experiment design, bounded conclusions, or abstention.
- **Human Review Trigger**: An identification result relying on an assumption marked untestable and unowned, or a proposal to add an assumption that only restores identification.

**Checkpoint 5: Estimation and Claim Validity (After Phase 5)**

- **Automated Check**: Overlap within the declared bounds for at least 95 percent of the target population; extreme weight share at most 1 percent; at least 2 estimators with different nuisance dependence; sign agreement at 100 percent and maximum relative difference at most 25 percent; 0 forbidden controls in any fit; 100 percent of claims carrying a level, an evidence class, and a stated basis.
- **Agent Action on Pass**: Proceed to refutation.
- **Agent Action on Failure**: Route the estimand to refutation with a disagreement flag, narrow the population, or return to identification.
- **Human Review Trigger**: Estimator disagreement that survives one repair, or an overlap failure that would require restricting the population below the decision's minimum useful scope.

**Checkpoint 6: Release Integrity (After Phase 6)**

- **Automated Check**: Critical refutation pass rate at 100 percent; at least 1 sensitivity result per untestable assumption; sensitivity threshold at or above the recorded comparator or the 1.25 default; all 10 release conditions passing; lineage complete with 0 deleted failed analyses; 0 disclosure breaches.
- **Agent Action on Pass**: Release the answer with its level, basis, population, uncertainty, and sensitivity threshold.
- **Agent Action on Failure**: Withhold release, name the failed condition, and return either the robust subset with bounds or an abstention record.
- **Human Review Trigger**: Any critical refutation failure, any release relying on the sensitivity default, any counterfactual claim, and any claim released after a downgrade.

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

**Error Type 1: Fluent Causal Narrative Without a Basis**

- **Symptoms**: A claim uses interventional verbs while its record carries evidence class E0, E1, or E2; the supporting text describes a mechanism at length but names no experiment, no design, and no adjustment set; confidence in the narrative rises as its detail rises rather than as its evidence changes.
- **Diagnostic Steps**: Read the claim record rather than the prose, locate the stated-basis field, and confirm whether a certificate identifier resolves to a certificate bound to the current structure hash.
- **Resolution Protocol**: Option A, obtain the missing basis by completing identification and re-emitting the claim. Option B, downgrade the claim to association level with reason code NO_IDENTIFICATION and return the measurement or design that would lift it. Option C, emit the mechanism as a registered hypothesis in the structure, which makes it inspectable and testable rather than persuasive.
- **Escalation Trigger**: This class is never resolved by rewording, by adding a hedge, or by regenerating the explanation; a second occurrence for the same estimand escalates to the decision owner with the missing requirement attached.

**Error Type 2: Unresolved Confounding**

- **Symptoms**: A candidate common cause survives enumeration with no measurement, no acceptable proxy, and no design that neutralises it; the estimate moves materially when a plausible proxy is added; the sensitivity threshold falls below the strongest measured confounder association.
- **Diagnostic Steps**: Locate the confounder in the registry, confirm both of its mechanism statements, and determine whether any available design, restriction, or estimand change removes its influence.
- **Resolution Protocol**: Option A, obtain the measurement or a validated proxy and re-certify. Option B, switch to a design whose identifying variation is unaffected by the confounder. Option C, restrict the target population to a stratum where the confounder is constant. Option D, cap the evidence class at E2 and downgrade every dependent claim.
- **Escalation Trigger**: 2 failed resolution attempts cap the evidence class automatically; a request to release at intervention level despite the cap escalates and is never granted by an automated component.

**Error Type 3: Adjustment-Set Contamination**

- **Symptoms**: A mediator, collider, descendant of treatment, or selection indicator appears in a fitted model; the estimate changes sign when one covariate is removed; adjusting for a larger covariate set is proposed as a robustness improvement.
- **Diagnostic Steps**: Re-derive each covariate's role from the structure, compare the fitted covariate list against the certificate's adjustment set and forbidden-control list, and identify the specific contaminating variable.
- **Resolution Protocol**: Option A, remove the forbidden covariate and refit under the certified adjustment set. Option B, where the covariate is genuinely required for a different target, redefine the estimand and re-certify, since a controlled direct effect and a total effect are different quantities. Option C, where the role is genuinely ambiguous, preserve competing structures and report the estimate under each.
- **Escalation Trigger**: Any fit that reaches release with a forbidden control indicates that enforcement runs at review time rather than fit time, which escalates as a control-plane defect rather than an analysis error.

**Error Type 4: Identification Failure Presented as an Estimation Problem**

- **Symptoms**: Estimators are switched, regularisation is tuned, or covariates are added in response to an unstable or implausible result; the certificate is absent, stale, or bound to a superseded structure hash; the discussion concerns model fit rather than identifying assumptions.
- **Diagnostic Steps**: Confirm certificate presence and hash binding, then determine whether the instability is a variance problem under a valid identification or a bias problem under an invalid one.
- **Resolution Protocol**: Option A, return to Phase 4 and attempt a substantively distinct identification strategy within the 3-attempt cap. Option B, adopt partial-identification bounds and release an interval rather than a point. Option C, request the experiment or the measurement that would identify the target.
- **Escalation Trigger**: A second estimator change proposed without a new certificate halts the estimand; no estimator repairs non-identification, so retry is prohibited as a resolution for this class.

**Error Type 5: Estimator Disagreement Beyond Tolerance**

- **Symptoms**: Sign disagreement across estimators targeting one estimand; relative difference above 25 percent; non-overlapping intervals; extreme weights concentrated in a small subset of units.
- **Diagnostic Steps**: Confirm that every compared estimator targets the same estimand and the same population, then partition the disagreement into overlap failure, nuisance-model misspecification, and estimand mismatch.
- **Resolution Protocol**: Option A, narrow the population to the region of common support and re-estimate. Option B, replace the estimator whose nuisance diagnostics fail, retaining the rejected fit in lineage. Option C, escalate to the refutation loop and treat the disagreement as evidence about the structure rather than about the software.
- **Escalation Trigger**: Disagreement surviving 1 repair per estimator routes the estimand to re-modelling; averaging incompatible estimands to produce a stable number is prohibited at every stage.

**Error Type 6: Discovery Output Treated as a Finding**

- **Symptoms**: A single structure returned by a search algorithm is carried forward as the approved structure; orientation is asserted for edges whose bootstrap frequency is below 0.60; benchmark performance is cited as evidence of causal competence with no contamination control.
- **Diagnostic Steps**: Check whether the algorithm's output is an equivalence class, whether its assumptions hold in the data, and whether the evaluation used private, symbol-renamed, or temporally split problems.
- **Resolution Protocol**: Option A, carry the whole equivalence class forward and report results under each member. Option B, supply background knowledge, temporal order, and impossible edges as explicit constraints and re-run the search. Option C, use the discovery output solely to prioritise expert review and experiments, which is the role it can support.
- **Escalation Trigger**: Any release whose structure rests on discovery output alone, with no domain review and no interventional evidence, is blocked and escalated to the decision owner.

**Troubleshooting Decision Tree**:

```
RELEASE GATE DETECTS A PROBLEM
├─ BASIS DEFECT
│   ├─ No stated basis on record → Downgrade to association; return missing requirement
│   ├─ Certificate hash stale → Recertify against current structure or halt estimand
│   └─ Interventional verb unmapped to a claim → Block rendering; regenerate from records
├─ STRUCTURE DEFECT
│   ├─ Unexplained cycle present → HALT; represent temporally or reject structure
│   ├─ Edge without an assumption record → Register with owner or remove edge
│   └─ Single discovered DAG asserted → Carry equivalence class; add constraints
├─ CONFOUNDING DEFECT
│   ├─ Unresolved common cause, no proxy → Cap evidence class at E2; downgrade
│   ├─ Forbidden control inside a fit → Refit under certified adjustment set
│   └─ Sensitivity below comparator → Withhold release; report bound and threshold
├─ ESTIMATION DEFECT
│   ├─ Overlap outside declared bounds → Narrow population or abstain
│   ├─ Estimator disagreement past tolerance → Route to refutation; never average
│   └─ Design falsification failed → Reclassify design; return to identification
└─ LINEAGE DEFECT
    ├─ Failed analysis deleted → HALT release; restore from append-only log
    └─ Reasoning transcript persisted → Purge, re-instrument, and re-run adjudication
```

### D. Performance Metrics and Continuous Learning

**Basis and Identification Metrics**:

- **Level-evidence violation rate**: Released claims whose declared level exceeded their evidence class (target: 0; any occurrence is a control-plane defect rather than an analysis error).
- **Basis coverage**: Released causal claims carrying a stated basis from the closed four-valued vocabulary (target: 100 percent).
- **Assumption coverage**: Identification-critical assumptions carrying an owner, provenance, status, and review date (target: 100 percent), with testable-assumption coverage additionally requiring an executed diagnostic (target: at least 90 percent).
- **Identification success rate**: Estimands identified and approved over eligible causal tasks, stratified by task family, structure version, data regime, and strategy, reported alongside the fraction identified only after a fallback.
- **False-identification rate**: Identification verdicts contradicted on benchmark cases with known answers (target: 0).
- **Downgrade composition**: Downgrades by reason code, reported rather than minimised, since a falling downgrade rate can indicate improved upstream discipline or suppressed enforcement and the two are distinguished only by their reason-code mix.

**Estimate Quality and Robustness Metrics**:

- **Estimate stability**: Computed only among estimators targeting one estimand and one population, reporting sign agreement (target: 100 percent), maximum relative difference (target: at most 25 percent), interval overlap, and between-estimator standard deviation.
- **Critical refutation pass rate**: Passed critical refutations over completed critical refutations (target: 100 percent), reported separately from the supporting pass rate so that a critical failure is never diluted.
- **Sensitivity margin**: Distance between the computed sensitivity threshold and the strongest measured confounder association, reported per bias family and never collapsed into one score.
- **Structure recovery metrics**: Where discovery is used, structural Hamming distance, skeleton precision and recall, orientation precision and recall, equivalence-class-aware accuracy, intervention prediction error, and bootstrap edge frequency, stratified by node count, density, sample size, hidden confounding, and scaling.
- **Experimental agreement**: Agreement between observational estimates and randomised estimates of the same quantity, wherever both exist, reported as the primary external validity check.
- **Contamination status**: Recorded per benchmark, with private, newly generated, symbol-renamed, and temporally split problems maintained so that benchmark familiarity is never reported as causal competence.

**Efficiency Metrics**:

- **Cost per released claim**: Wall time, compute, tool calls, model tokens, and monetary cost per attempted task, per identified estimand, per valid estimate, and per passed release.
- **Loop consumption**: Structure revisions, retrieval rounds, identification attempts, estimator fits, refutation rounds, and re-modelling cycles per run, each compared against its declared cap.
- **Human review load**: Reviewer time per release, stratified by risk tier, so that a gate consuming more review than it prevents in error is detected.

**Learning and Adaptation Mechanisms**:

- **Assumption outcome tracking**: Record whether each registered assumption was later contradicted by an experiment, a new measurement, or a failed refutation, and use the record to calibrate confidence categories rather than to justify them.
- **Structure reuse with review**: Retain approved structures per domain as starting proposals, and require the full adversarial challenge in Step 2.3 on every reuse, since a reused structure carries its original blind spots.
- **Threshold recalibration**: Recompute every numeric bound in this guide per domain and per task family against observed outcomes; the stated values are deployment defaults, not measured constants.
- **Negative-control library**: Accumulate validated negative-control exposures and outcomes per domain, recording for each the bias it shares with the target pathway and the pathway it is known to be irrelevant to.

**Human-in-the-Loop Boundaries**: Authorising a treatment, determining legal liability, deploying a consequential policy from an observational estimate, amending a hard constraint in the contract, overriding an abstention, releasing a counterfactual claim, and relaxing the disclosure boundary are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the relationship between a claim and its basis rather than the content of any particular claim. Its phases hold wherever a decision changes an exposure, a policy, an allocation, or a configuration, and the question concerns the outcome under that change.

### 4.1 Cross-Domain Application Patterns

**Clinical and health services**: The query level is usually intervention, and the estimand distinguishes an average effect over an eligible population from an average over the treated. Structure elicitation draws on published mechanisms and on clinician review, and the confounding challenge concentrates on indication, severity, and access, each of which affects both treatment receipt and outcome. Positivity is the binding constraint in practice, because contraindicated patients have zero probability of some treatments and the target population must be narrowed accordingly. Release requires clinical expertise, validated outcome definitions, and patient-specific review, and a population average is never converted into individual advice at this gate.

**Software reliability and incident diagnosis**: The query level is usually counterfactual, and the framework's well-formedness rule does most of the work at intake: a question asking whether a change caused an outage is rejected, while a question asking whether the outage would have occurred had a specific deployment been rolled back at a specific time is modelable. Deployment systems supply strong temporal ordering and frequently supply staged or canary variation that qualifies as a natural experiment. The dominant failure is treating a predictive alert as a lever, since an alert downstream of the failure is useless to manipulate; the manipulability flag on each node exists to catch this.

**Public policy and programme evaluation**: The query level is intervention, the treatment is often assigned at an aggregate level, and difference-in-differences, regression discontinuity, and synthetic control are the common strategies. Interference between units is material rather than negligible, because a policy in one jurisdiction affects behaviour in its neighbours, so the interference-channel inventory in Step 3.1 is load-bearing. Subgroup support and transportability must be reported explicitly, because an average welfare improvement can redistribute harm across groups, and affected-domain review is required before release.

**Commercial product and experimentation**: Randomised assignment is usually feasible, so the framework routes to experiment design at Step 1.3 and enters at evidence class E5. The residual work is the estimand and the audit rather than identification: treatment versions multiply as features ship, interference travels through shared inventory and social connections, attrition is differential, and repeated inspection inflates false positives. Heterogeneous-effect targets used for allocation require validation of both the heterogeneity and the decision value it implies, since a conditional effect model that ranks units well may still misprice the action.

**Industrial process and manufacturing engineering**: Physical mechanism supplies unusually strong structural knowledge, so evidence class E2 is often well justified and the structure carries genuine exclusion restrictions rather than convenient ones. Time-varying treatment with confounding affected by prior treatment is the norm, since a control setting responds to the state it produced, and ordinary regression adjustment blocks part of the treatment process. Longitudinal methods are therefore the default strategy family, and the run records sequential exchangeability and positivity at each time point rather than once.

### 4.2 Scale, Risk, and Evidence-Regime Adaptation

- **Low-risk reversible decisions**: Collapse the loop to a single structure revision and a single fallback, retain the certificate requirement and the level-evidence check, and permit a single estimator where a second is not feasible, recording that fact. The stated-basis rule never relaxes, because it costs almost nothing and prevents the framework's dominant failure.
- **High-risk or irreversible decisions**: Retain every phase, require at least 2 estimators, require a sensitivity result per untestable assumption, bind the approval gate before release, and prefer abstention over an unverified claim. Medical, legal, employment, credit, and policy decisions sit here by default rather than by assessment.
- **Experiment-rich environments**: Enter at evidence class E5, spend the saved identification effort on the audit, the interference inventory, and the multiplicity controls, and remember that randomisation protects assignment rather than every analysis choice made afterwards.
- **Observation-only environments**: Expect most runs to terminate in a downgrade or an abstention, and treat that as correct behaviour. Value is delivered by naming the specific missing measurement or design, which converts a refusal into a research agenda.
- **Text-only environments**: Where no validated data and no formal engine are available, restrict the run to hypothesis elicitation, candidate structures, assumption enumeration, and a measurement plan. No claim above evidence class E2 may be emitted, and the framework's output is a design rather than an estimate.
- **Large structure and high dimension**: Partition the structure by decision-critical subgraph rather than modelling every recorded field, since an adjustment set derived from a structure nobody reviewed is not more defensible than one derived from a small structure that was reviewed.

***

## V. Limitations and Considerations

**Fluency carries no information about identification**: A language model asked a causal question produces a coherent causal story whether or not the evidence supports one, because causal language saturates the text such models are trained on. The consequence is that no reviewer, human or automated, can separate a supported claim from an unsupported one by reading it, and detail makes the unsupported case more persuasive rather than less. The mitigation is the stated-basis rule in Section 1.3 together with the level-evidence check in Step 5.3, which adjudicate the claim record rather than the prose and downgrade automatically, so that persuasiveness has no path to release.

**Identification assumptions are largely untestable**: Exchangeability, exclusion, and the absence of unmeasured confounding are assumptions about what is not in the data, and no diagnostic computed from the data confirms them. The consequence is that every observational result is conditional on claims the analysis cannot verify. The mitigation is the assumption registry in Step 2.2, which records each assumption with an owner and a failure consequence, and the sensitivity requirement in Step 6.2, which converts an untestable assumption into a quantified statement of how strong a violation would have to be to change the conclusion.

**Discovery returns equivalence classes rather than structures**: Observational distributions commonly determine only the set of structures encoding the same conditional independences, and hidden variables, selection, measurement error, cycles, non-stationarity, and low power further limit orientation. The consequence is that a single structure returned by a search is a hypothesis presented with the surface form of a finding. The mitigation is the 0.60 bootstrap-frequency threshold in Step 2.1, the requirement to preserve competing structures, and the rule in Error Type 6 that discovery output may prioritise expert review and experiments but may not stand alone at release.

**Downgrading creates institutional pressure**: A framework that converts an expected causal answer into an association claim will be experienced as obstruction, and the pressure to relax the check falls on whoever operates it. The consequence is that the enforcement mechanism erodes precisely where it matters most, in high-stakes runs under schedule pressure. The mitigation is that every downgrade returns the specific measurement, design, or assumption that would lift it, converting a refusal into an actionable request, and that downgrade composition by reason code is a reported metric so that quiet relaxation becomes visible.

**Numeric thresholds here are deployment defaults**: The bootstrap frequency of 0.60, the overlap interval of 0.05 to 0.95, the 5 percent population tolerance, the 1 percent extreme-weight share, the 25 percent estimator-disagreement tolerance, the 10 percent placebo and random-common-cause shifts, the 90 percent subset-stability rate, and the 1.25 sensitivity default were chosen to be operable on first deployment rather than derived from a measured property of causal systems. The consequence is that a deployment inheriting them unchanged may gate too loosely in one domain and too tightly in another. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute every bound per domain and task family against observed outcomes.

**Benchmark performance is contaminated by construction**: Public causal benchmarks, their templates, their solutions, and the papers discussing them appear in training and retrieval corpora. The consequence is that reported accuracy on a public benchmark measures familiarity as much as competence. The mitigation is the contamination-status requirement in Section III.D, which maintains private problems, newly generated mechanisms, symbol-renamed variants, held-out domains, and temporal splits, and records contamination status alongside every reported figure.

**Framework conformance is not causal soundness**: A run can satisfy every checkpoint here, hold a valid certificate, and still rest on a structure that omits the mechanism that actually generates the data. The consequence is that the framework detects unsupported claims and malformed procedure, not a wrong model of the world. The mitigation is the adversarial review requirement in Step 2.3, the preservation of competing structures, and the experimental-agreement metric, none of which substitutes for domain review of the structure itself.

**Instrumentation carries its own exposure**: A lineage record complete enough to support adjudication is complete enough to reveal sensitive personal data and organisational weaknesses, and a structure containing latent-variable hypotheses can expose protected attributes. The consequence is that the audit trail becomes a disclosure risk proportional to its usefulness. The mitigation is the disclosure boundary in Section III.A, which prohibits retention of hidden reasoning content, requires content references in place of raw payloads, and classifies structures as sensitive artifacts under access control.

**Transcribed evidence was not uniformly re-verified**: This guide is an operational restructuring of a prose source, and most of the external works that source cites were carried across as it cited them rather than retrieved again. The consequence is that a transcription error in the original propagates here. The mitigation is that 4 of the source's citations were retrieved and confirmed during conversion and are marked as such in Section VII, and that every remaining entry is presented as transcribed rather than asserted as verified.

***

## VI. Conclusion and Summary

Causal reasoning is an evidence discipline before it is a reasoning technique. The difficulty is not that causal questions are hard to answer fluently; they are unusually easy to answer fluently, which is precisely the problem. A system that generates causal explanations on demand will produce them at the same rate and with the same confidence whether the underlying evidence identifies an effect or contains nothing but co-occurrence. The framework above responds by refusing to adjudicate claims on their wording. A claim is admissible only where its basis is named, its assumptions are registered and owned, its identification is certified by an engine rather than argued by a generator, and its declared level survives a mechanical comparison against the evidence class its artifacts support.

A team adopting this framework should begin with the enforcement mechanism rather than with the analysis machinery. Instrument the claim record, the evidence class, and the level-evidence check first, and run them over existing causal claims already in circulation. The resulting downgrade inventory is the honest baseline, and it will usually be larger than expected. Add the structure artifact and the assumption registry next, since they convert arguments about causation into diffs over a versioned object. Add the identification engine, the estimation redundancy, and the refutation battery afterwards. Adding the statistical machinery first produces precise estimates of quantities nobody certified, which is the failure this framework exists to prevent.

**Key Success Factors**:

- **A named basis or no causal claim**: Every causal claim states a controlled experiment, a natural experiment, an identification strategy with its assumptions, or an explicit causal structure; a claim naming none of these is relabelled as an association claim rather than qualified.
- **Level bounded by evidence**: The three query levels demand strictly increasing evidence, an intervention question is never answered from observational data without a named identification strategy, and the comparison is enforced mechanically before release.
- **Confounding as the default hypothesis**: Every proposed link is challenged with candidate common causes before acceptance, and an unresolved confounder caps the evidence class and downgrades the claim rather than appearing as a caveat.
- **Structure as an inspectable artifact**: Nodes, directed edges, non-edges, and the assumption behind each are versioned, hashed, owned, and reviewable, so that a disagreement about causation becomes a disagreement about a specific edge.
- **Identification before estimation**: A certificate bound to a structure hash precedes every estimator fit, and no estimator, regulariser, or covariate change is accepted as a remedy for non-identification.
- **Abstention as a success state**: A run that returns the supported association, the specific missing measurement or design, and no causal claim has succeeded, and the framework reports that outcome rather than concealing it.

By following this guide, AI agents can produce causal conclusions whose basis a reviewer can inspect, whose level is bounded by the evidence that supports it, and whose refusals name what would be needed to lift them.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them and were not independently re-verified during conversion, except for the 4 entries explicitly marked as verified, whose titles, authorship, and reported figures were retrieved and confirmed while this guide was being written.

**Corpus pointers**:

- `Production Guide to Causal Reasoning` — the originating prose guide from which this operational guide was derived. Source of the three-level distinction, the identification-before-estimation separation, the identification certificate, the graph-construction and assumption-elicitation loop, the identification and estimation loops with their caps, the refutation and sensitivity loop, the re-modelling loop, the release gate, the causal lineage field inventory, the log-derived quality and efficiency metrics, and the failure-mode inventory. It carries inline citations to primary literature on graphical causal models, potential outcomes, quasi-experimental design, longitudinal methods, causal discovery, sensitivity analysis, and language-model causal evaluation; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/reasoning/guide_ChainOfVerification.md` — companion guidance on auditing a candidate answer claim by claim. Source of the evidence-class and abstention terminology adopted here, which this guide reuses rather than coining parallel terms for.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — companion guidance on measuring whether a process is working. Source of the source-class, external-signal, and correlated-failure terminology used in the confounder enumeration and refutation steps.
- `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` — companion guidance on controlling reasoning effort and intermediate steps, named by the prose source as a complement to causal work.
- `advanced_task_guides/reasoning/guide_SelfConsistency.md` — companion guidance on agreement across independent samples, applicable to the estimator-redundancy rule in Step 5.2 and to the treatment of agreement that shares a common premise.
- `advanced_task_guides/reasoning/guide_AbductiveReasoning.md` — the sibling guide covering inference to the best explanation: a minimum-breadth hypothesis set no single candidate can satisfy, a checklist of mundane candidate classes, a discrimination score admitting only tests that separate competing hypotheses, a registered falsifier per surviving candidate, and a termination rule keyed to a separation margin rather than to the leader's absolute score. The boundary is the question asked: that guide ranks competing explanations of what was observed and routes interventional questions here, while this guide establishes what a change to one variable does to another. Its treatment of a common cause as a standing rival hypothesis is the same move as the adversarial confounder enumeration required here, applied to explanations rather than to edges.
- `advanced_task_guides/reasoning/guide_AnalogicalReasoning.md` — companion guidance on transferring relational structure from a source case to a target under a recorded mapping and an explicit register of where the correspondence breaks. It is the in-category counterpart to the cross-domain transfer guide cited below, applicable wherever a structure or estimate established in one population is proposed for another: its disanalogy register is where the transportability assumptions are recorded rather than assumed.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops and declared exit conditions, applicable to the caps and terminal states in Phases 2, 4, and 6.
- `advanced_task_guides/research-analysis/guide_StratifiedComparative_n_FactorVariationAnalysis.md` — a pre-existing corpus guide whose headings cover stratified comparative and factor-variation analysis, relevant to conditional-effect targets and slice-level overlap reporting.
- `advanced_task_guides/research-analysis/guide_Cross-domainAnalogyandTransfer.md` — a pre-existing corpus guide whose headings cover transferring a method across domains, relevant to the transportability considerations in Section IV.

**External references**:

*Foundations and canonical texts*

1. Pearl, Glymour, and Jewell, *Causal Inference in Statistics: A Primer* — https://bayes.cs.ucla.edu/PRIMER/
2. Hernán and Robins, *Causal Inference: What If* — https://miguelhernan.org/whatifbook
3. Pearl and Mackenzie, *The Book of Why* — https://www.basicbooks.com/titles/judea-pearl/the-book-of-why/9780465097609/

*Design, identification, and estimation*

4. Rubin, *For Objective Causal Inference, Design Trumps Analysis* — https://projecteuclid.org/journals/annals-of-applied-statistics/volume-2/issue-3/For-objective-causal-inference-design-trumps-analysis/10.1214/08-AOAS187.full
5. Angrist, Imbens, and Rubin — https://dash.harvard.edu/entities/publication/73120378-82c1-6bd4-e053-0100007fdf3b
6. Rosenbaum and Rubin — https://academic.oup.com/biomet/article-abstract/70/1/41/240879
7. Imai, Keele, and Tingley — https://pubmed.ncbi.nlm.nih.gov/20954780/
8. van der Laan and Rubin — https://biostats.bepress.com/ucbbiostat/paper213/
9. Imbens and Lemieux — https://dash.harvard.edu/entities/publication/73120378-8039-6bd4-e053-0100007fdf3b
10. Abadie — https://www.aeaweb.org/articles?id=10.1257/jel.20191450
11. Mansournia and colleagues — https://pmc.ncbi.nlm.nih.gov/articles/PMC7429147/
12. VanderWeele and Ding — https://dash.harvard.edu/entities/publication/73120378-fbd5-6bd4-e053-0100007fdf3b
13. Lipsitch, Tchetgen Tchetgen, and Cohen — https://pmc.ncbi.nlm.nih.gov/articles/PMC3053408/

*Causal discovery and its evaluation*

14. Shimizu and colleagues — https://www.jmlr.org/papers/volume7/shimizu06a/shimizu06a.pdf
15. Zheng and colleagues — https://arxiv.org/abs/1803.01422
16. Meek — https://arxiv.org/abs/1302.4972
17. Reisach and colleagues, *Beware of the Simulated DAG* — https://proceedings.neurips.cc/paper/2021/hash/e987eff4a7c7b7e580d659feb6f60c1a-Abstract.html
18. Kaiser and Sipos — https://arxiv.org/abs/2104.05441

*Language models and causal tasks*

19. Kiciman, Ness, Sharma, and Tan, *Causal Reasoning and Large Language Models: Opening a New Frontier for Causality* — https://arxiv.org/abs/2305.00050 (title and authorship verified during conversion)
20. Jin and colleagues, *CLadder: Assessing Causal Reasoning in Language Models* — https://arxiv.org/abs/2312.04350 (title verified during conversion)
21. Jin and colleagues, *Can Large Language Models Infer Causation from Correlation?* — https://arxiv.org/abs/2306.05836 (title verified during conversion; the abstract states that seventeen evaluated models achieve close to random performance)
22. Zečević and colleagues, *Causal Parrots* — https://arxiv.org/abs/2308.13067

*Tooling and instrumentation*

23. PyWhy, *DoWhy* — https://github.com/py-why/dowhy
24. DoWhy documentation — https://www.pywhy.org/dowhy/v0.8/
25. DoWhy, *Refuting Effect Estimates* — https://www.pywhy.org/dowhy/v0.11/user_guide/refuting_causal_estimates/refuting_effect_estimates/index.html (page title and refuter families verified during conversion)
26. EconML documentation — https://www.pywhy.org/EconML/
27. CausalML documentation — https://causalml.readthedocs.io/en/latest/
28. causal-learn documentation — https://causal-learn.readthedocs.io/en/latest/
29. Center for Causal Discovery, Tetrad tools — https://www.ccd.pitt.edu/tools/
30. DAGitty — https://www.dagitty.net/
31. bnlearn — https://www.bnlearn.com/
32. OpenTelemetry, *GenAI semantic conventions* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
