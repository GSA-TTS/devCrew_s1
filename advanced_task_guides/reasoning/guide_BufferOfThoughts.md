# Buffer of Thoughts

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Buffer of Thoughts constitutes the task family of maintaining a governed library of reusable reasoning templates distilled from verified solutions, retrieving a template for a new problem, instantiating it against that problem, and conditionally distilling a new template from the result. This guide provides AI agents with a structured protocol for running that cycle as an evidence-gated reuse pipeline rather than as an unbounded cache of past reasoning: fixing an abstraction policy and a template schema before any template is written; distilling a normalised task description that preserves decisive constraints; retrieving under authorization filters across lexical, dense, and structural indexes; checking fit before a retrieved template is applied, and discarding rather than forcing a poor match; instantiating with a declared fallback to unaided reasoning; and admitting new templates only through a promotion gate that software closes. It names the central hazard the pipeline exists to contain, which is template error propagation: a template distilled from a wrong solution, or from one right for a reason that does not generalise, is retrieved repeatedly and reproduces that error in every future problem it matches. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that the library grows in verified reuse value rather than only in size.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Thought-template**: A reusable, abstract reasoning procedure stored as a typed record. A template describes typed input slots, preconditions, prohibited conditions, ordered operations and branches, invariants, evidence and tool requirements, verifier hooks, an output contract, termination conditions, scope limits, and failure conditions. It is not an answer, not a stored transcript, and not a private reasoning trace [1].

**Template library**: The persistent, versioned store holding thought-templates and their lifecycle metadata. The originating literature calls this a meta-buffer and describes it as a lightweight library of templates distilled from problem-solving [1]. Operationally it is an ordinary store with an ordinary index, and every property that makes it safe comes from the governance placed around it rather than from the retrieval mechanism.

**Abstraction level**: The position of a template between the single problem it was distilled from and the class of problems it claims to govern. A template too specific matches nothing beyond its origin; a template too general constrains nothing and adds retrieval and context cost without supplying guidance. Abstraction level is the central design difficulty of the method and is governed by an explicit policy in Step 1.2.

**Problem distillation**: The transformation of an incoming request into a normalised task description and a typed structural signature suitable for retrieval. It is a retrieval transformation, not a summary: it preserves quantities, units, entities, roles, temporal order, objective, constraints, exceptions, jurisdiction, permissions, required evidence, and uncertainty while removing narrative decoration.

**Structural signature**: The typed, non-prose part of a distilled task, carrying task family, relation pattern, precondition set, tool graph, and output schema. It supports structural retrieval and structural deduplication, both of which embedding similarity alone cannot perform.

**Fit check**: The bounded evaluation, run after retrieval and before instantiation, that determines whether a retrieved template is genuinely applicable to the distilled task. It combines deterministic gates on preconditions, prohibited conditions, freshness, authorization, and verifier availability with a model judgement on structural correspondence.

**Near miss**: A candidate template that is superficially similar to the distilled task but structurally or conditionally wrong for it. A near miss is more dangerous than an empty result, because a partially matching procedure anchors the reasoning more strongly than no procedure at all.

**Negative transfer**: The measured outcome in which a run assisted by a retrieved template performs worse than the same run without one. Negative transfer is the harm side of reuse and is accounted for separately from ordinary failure.

**Instantiation**: The binding of the distilled task's entities, quantities, and evidence to the template's typed slots, followed by execution of the template's operations against that binding. Instantiation produces an answer, an explicit procedure mapping, stated assumptions, and verification artifacts.

**Buffer-Need Gate**: The cheap gate run before any retrieval, returning invoke or suppress, which withholds the whole method wherever a cheaper verified route already succeeds or wherever the problem distribution cannot amortise the cost of curating a library.

**Promotion gate**: The set of mechanical checks and verification requirements that a candidate template must satisfy before it is admitted to the library as retrievable. The gate is owned by software and is the only path from candidate to active. This term is adopted from the memory-management corpus and carries the same meaning here.

**Provenance preservation**: The requirement that every derivation step retains the mapping from output to input, so that a promoted template can enumerate the origin episodes, the verifier results, and the reuse cases that support it at span granularity. A template that cannot enumerate its evidence is not admissible regardless of how good it looks.

**Confidence propagation**: The rule that a derived artifact never carries more confidence than the evidence of its origin and its subsequent reuse supports. Confidence does not rise because a template was restated more fluently, because it was retrieved often, or because its origin episode was long.

**Template error propagation**: The failure mode specific to this method, in which a template distilled from a wrong solution, or from a solution correct for a reason that does not generalise, is retrieved repeatedly and reproduces that defect in every problem it matches. It is the reuse-amplified form of the hazard the memory-management corpus names error laundering, and the boundary between the two is stated in Section 1.3.

**Reuse accounting**: The deterministic record, per template version, of retrieval count, selection count, verified success count, near-miss harm count, and paired attributable gain. Reuse accounting is what makes both abstraction failure directions measurable rather than asserted.

**Retirement**: The deterministic removal of a template version from retrieval access after it fails to earn retrieval or fails to earn measured lift, retaining a tombstone and its lineage rather than deleting the record.

**Fallback to unaided reasoning**: The declared route taken when retrieval abstains or when a selected template misleads, in which all template text and template-derived assumptions are removed from context and the problem is solved by a template-free method under independent verification.

### 1.2 The Abstraction-Level Problem and Its Two Failure Directions

Abstraction level is where this method succeeds or fails, and it is the one design decision no retrieval mechanism can repair after the fact. Both failure directions are silent under naive monitoring, and each is detected by a different measurement.

**Over-specific templates**: A template written at the granularity of the problem that produced it encodes that problem's entities, quantities, and incidental conditions in its operations. It matches its origin problem and nothing else. The observable signature is a template that is never retrieved, or retrieved only for near-duplicates of its origin. Over-specificity is cheap in outcome terms and expensive in library terms: it inflates the index, raises retrieval latency, and increases the number of candidates a reranker must reject.

**Over-general templates**: A template written so broadly that its operations reduce to restatements of ordinary problem solving matches many distilled tasks and constrains none of them. The observable signature is a template retrieved across unrelated task families whose selection produces no measurable improvement over the template-free baseline. Over-generality is expensive in outcome terms, because it consumes retrieval and instantiation budget, occupies context, and can constrain a capable model into a worse trajectory than it would have taken unaided.

**The stated abstraction test**: A template is admissible at its declared level only where it satisfies all four of the following, evaluated by software against the reuse ledger and the candidate's own fields. First, its preconditions are satisfiable by at least 3 distinct non-near-duplicate problems, where near-duplicate means a structural signature match above the deduplication threshold. Second, its operations reference no entity, quantity, or literal drawn from a single origin problem, verified by a deterministic scan of the operation text against the origin episode's extracted entities. Third, it constrains at least 3 ordered operations or branch conditions that the template-free baseline does not already impose, so that the template carries procedure rather than encouragement. Fourth, its scope limits and prohibited conditions are non-empty, since a template that excludes nothing claims to govern everything.

**Abstraction Failure Directions and Their Detection Signals**

| Failure direction | Library signature | Outcome signature | Deterministic detection rule | Required response |
| :-- | :-- | :-- | :-- | :-- |
| Over-specific | Zero retrievals across 2 review windows | No outcome data exists to evaluate | Retrieval count equals 0 after 90 days active | Retire the version; retain tombstone and lineage |
| Over-specific | Retrieved only for near-duplicates of origin | Gain present but not generalising | Distinct origin-family count of selections is 1 after 20 selections | Demote to specialization; do not count as a general template |
| Over-general | Selected across 4 or more task families | Attributable gain interval spans zero | Paired gain bootstrap interval includes 0 after 30 paired runs | Retire the version; split into scoped successors if evidence supports |
| Over-general | Top-template traffic share above 40 percent | Near-miss harm rate rising | One version holds more than 40 percent of all selections | Freeze selection; investigate selector collapse before any promotion |
| Both | Duplication rate above 30 percent of proposals | Retrieval latency rising with flat gain | Proposals rejected or merged as duplicates exceed 30 percent | Raise the abstraction policy's specificity floor and re-review |

**Abstraction is set per task family, not globally**: The level at which a template generalises is a property of the problem distribution, not of the method. A family whose problems differ only in numeric parameters supports a much more specific template than a family whose problems differ in structure. Deployments must therefore calibrate the abstraction policy per task family against observed reuse, and must treat the numeric bounds stated above as deployment defaults to be recomputed rather than as constants.

### 1.3 Template Error Propagation and the Boundary With Memory Consolidation

**The hazard**: A template is distilled from a solution. Where that solution was wrong, or was right for a reason that does not generalise beyond its origin, the resulting template encodes the defect as procedure. Retrieval then reproduces the defect in every future problem the template matches, and the defect arrives wearing the authority of a validated library entry. The damage is therefore proportional to the template's retrieval count and grows after the error is committed, which distinguishes this hazard from an ordinary wrong answer that harms exactly one run.

**Relation to error laundering**: The memory-management corpus names the general form of this hazard error laundering: the conversion of low-confidence and possibly wrong inputs into a small number of confident-looking records that no longer carry the uncertainty of their inputs and that are subsequently retrieved as fact. Its guide on memory consolidation specifies the general machinery in full and is the normative reference for it. This guide adopts that terminology unchanged and states the boundary rather than re-deriving the machinery.

**What the consolidation guide owns**: The general procedure for converting accumulated raw episodes into durable records: grouping and deduplication, contradiction detection and adjudication, provenance preservation through every derivation step, the confidence propagation rule that caps a derived record at what its evidence supports, the promotion gate that separates generation authority from publication authority, and the post-promotion audit with its rollback and invalidation cascades. Deployments running both methods must run one promotion pipeline, not two, and must not implement a second gate here.

**What this guide owns**: The three properties of the hazard that are specific to reusing procedure rather than storing fact. First, amplification: a consolidated fact misleads the answers that cite it, while a wrong template misdirects the entire reasoning trajectory of every problem it matches, so the promotion bar rises with expected retrieval volume rather than being fixed. Second, abstraction level, which has no analogue in fact consolidation, because a fact is true or false at one granularity while a procedure can be correct and still be pitched at a level that makes it useless or harmful. Third, self-reinforcement through reuse, in which a template's own assisted output becomes the evidence for its continued promotion, closing a loop that no fact record can close on its own.

**Adopted countermeasures**: The four countermeasures are carried here as first-class procedure with their consolidation-guide meanings intact. Provenance preservation requires that every promoted template enumerate its origin episodes, its verifier results, and each reuse case credited to it, at span granularity. Explicit verification requires that a template's origin solution was adjudicated by a verifier that did not see the template, replacing the general contradiction-detection countermeasure with its reuse-specific form. Confidence propagation caps a template's confidence at the minimum of the model's proposed value, an evidence ceiling computed from independent verified reuse count, and the highest confidence carried by any supporting input. A promotion gate holds publication authority in software, so that the component distilling a template can never admit it.

**The self-promotion prohibition**: A template's promotion evidence must never include an outcome the template itself produced in the same run. Same-run self-promotion is blocked deterministically, episode count is distinguished from unique problem-family count so that 5 repetitions of one problem never satisfy a 3-family requirement, and canary comparison against both the incumbent template and the no-template route is required before any version is promoted to general availability.

**Boundary against below-agent-layer mechanisms**: Two mechanisms adjacent to this method are not executable at the AI Agent layer and are carried here as boundary statements rather than as procedure. Moving recurring behaviour into model weights through fine-tuning reduces prompt overhead at volume and wins where behaviour is stable, labelled, latency-sensitive, and safe to distribute globally; it is a training operation, not a runtime one, and an agent must never treat a fine-tuned behaviour as a library entry it can inspect, cite, version, or roll back by pointer switch. Later work from overlapping authors scales the template idea to a library of roughly 500 templates and learns trajectories over multiple templates with hierarchical reinforcement learning [2]; that changes the method, training regime, domain, and inference controller, is therefore not an independent replication of the original result, and its learned controller sits below this guide's scope. Everything else the method requires is an ordinary agent-layer capability: a versioned store, hybrid indexes, model calls for distillation, fit judgement, and instantiation, and deterministic checks for every gate.

### 1.4 The Execution Tier Partition

The partition of work across execution tiers is the principal thing separating an operational reuse pipeline from a prose description of one. Assignment is not stylistic. Work requiring exactness, reproducibility, auditability, or scale belongs to the deterministic tier, because model inference supplies none of those properties. Work requiring open-vocabulary judgement belongs to the model tier, because no deterministic rule covers it. Work where one tier proposes and the other verifies belongs to the hybrid tier, and every hybrid assignment names which component holds authority when the two disagree.

The governing rule is stated once and enforced throughout: **a template is proposed by the model tier and admitted by a deterministic gate**. The distiller holds no write access to the active library, no ability to set a template's final confidence, and no vote in the promotion decision. A second rule constrains every confidence value the pipeline emits: **a template never carries more confidence than the evidence of its origin and its reuse supports**, and that ceiling is computed by software from counted evidence rather than proposed by the component that wrote the template.

**Execution Tier Assignment for Template Reuse Work**

| Work unit | Owning tier | What the tier does | Authority on disagreement |
| :-- | :-- | :-- | :-- |
| Library store, identity, and versioning | Deterministic | Assigns stable identifiers, writes immutable versions, links supersession and lineage | Deterministic; a model never mints or mutates a version |
| Authorization and namespace filtering | Deterministic | Applies tenant, role, data-class, jurisdiction, and policy filters before any retrieval runs | Deterministic; failure is a hard reject |
| Problem distillation | Model | Produces the normalised task description under a fixed output schema | Model only; software rejects schema violations without repair |
| Distillation loss checking | Hybrid | Model proposes the normalised form; software diffs typed fields against the original request | Deterministic; an unpreserved decisive field voids the distillation |
| Retrieval execution | Deterministic | Runs lexical, dense, and structural queries against version-pinned indexes and fuses candidate lists | Deterministic; retrieval is reproducible or it is not evidence |
| Precondition and prohibited-condition evaluation | Deterministic | Evaluates typed conditions against the structural signature | Deterministic; no embedding score overrides a failed precondition |
| Structural fit judgement | Model | Judges whether the template's operations correspond to the task's structure | Model proposes; software enforces every hard gate regardless of the verdict |
| Near-miss diagnosis | Hybrid | Model names the mismatch; software records the defect code and the exclusion | Deterministic on the exclusion; model on the semantic cause |
| Selection and abstention | Deterministic | Compares fit score, margin, and expected utility against calibrated thresholds | Deterministic; a threshold is never lowered to obtain a selection |
| Slot binding | Hybrid | Model proposes bindings; software validates type, unit, cardinality, time, and authorization | Deterministic; an invalid binding voids the instantiation |
| Instantiation and answer generation | Model | Executes the template's operations against the binding and emits the answer and procedure mapping | Model only |
| Independent verification | Deterministic | Runs deterministic checks, tools, tests, and simulations that did not see the template | Deterministic; a model self-assessment is never a verifier |
| Release gate | Deterministic | Compares template-assisted and matched baseline outputs under one rubric | Deterministic; eloquence and popularity are never release evidence |
| Template distillation from a verified solution | Model | Proposes a candidate template under the schema and the abstraction policy | Model only; the candidate has no library status |
| Abstraction test evaluation | Deterministic | Scans candidate operations for origin literals and counts constrained operations | Deterministic; a failed test rejects without model consultation |
| Duplicate and specialization analysis | Hybrid | Model proposes a merge or specialization; software confirms structural equivalence | Deterministic on equivalence; model on the merge rationale |
| Confidence ceiling computation | Deterministic | Applies the propagation rule to independent verified reuse and origin evidence | Deterministic; the ceiling is never overridden |
| Promotion gate checks | Deterministic | Schema, provenance completeness, abstraction test, verification evidence, self-promotion block, threshold comparison | Deterministic; any failed hard check rejects |
| Reuse and outcome accounting | Deterministic | Counts retrievals, selections, verified successes, near-miss harms, and paired gain | Deterministic; a model may not assert its own lift |
| Retirement and eviction | Deterministic | Removes retrieval access on a counted rule, writes a tombstone, retains lineage | Deterministic; a model never decides a template still earns its place |
| Error rollback and invalidation | Deterministic | Traverses dependents, revokes versions, replays affected runs | Deterministic; rollback is never deferred on a model's judgement |
| Human approval for high consequence | Hybrid | Software routes and blocks; a named human role decides | Human; software records the decision and the content hash approved |

Two consequences of this partition are load-bearing. First, every phase of the Operational Framework is assignable to a tier, and every step crossing tiers names the handoff explicitly in its actions. Second, the deterministic tier's rejections are not advisory. A candidate failing a hard check is rejected without a model being consulted, because asking a model whether its own template should enter the library reintroduces exactly the self-approval the partition exists to prevent.

***

## II. Operational Framework: Governed Reuse of Verified Reasoning Templates

The framework consumes one incoming request and an existing template library, and produces one verified answer plus at most one adjudicated library decision. Phases 1 through 4 run in sequence within a single run and terminate either in a released template-assisted answer or in a verified template-free answer. Phase 5 runs only after outcome verification and produces at most one candidate template per run. Phase 6 runs asynchronously against templates already active and returns control to Phase 5 when a re-derivation is required. Each phase names the execution tier that owns its work, and each step crossing tiers names the handoff.

### Phase 1: Library Definition and Buffer-Need Gating

**Objective**: Fix the task contract, the template schema, and the abstraction policy, and decide whether template reuse is warranted at all, before any retrieval or instantiation budget is spent.

#### Step 1.1: Declare the Task Contract, Budget Caps, and Namespace Policy

**Required Actions**:

- Record the objective, output schema, task family, domain, jurisdiction, effective date, risk class, and data class for the incoming request, so that later gates evaluate declared values rather than inferred ones.
- Enumerate the permitted namespaces, authorised evidence sources, permitted tools, and available verifiers, and record which verifier is authoritative for each acceptance test.
- Define operational meanings for success, abstention, and review, so that a declared abstention is not recorded as task failure.
- Set hard caps for the run and record them in a ledger whose counters never reset on a retry: at most 2 distillation repairs, 20 retrieval candidates, 3 reranked templates, 2 selection rounds, 2 instantiations, 2 verification repairs, 1 fallback attempt, 1 write candidate, 20 model calls, 30,000 tokens, 90 seconds, and total cost no greater than 3 times the verified direct baseline.
- Assign the run a trace identifier and open child spans for routing, baseline, distillation, retrieval, selection, instantiation, verification, fallback, release, and library write.

**Required Outputs**:

- A task contract record carrying objective, output schema, family, domain, jurisdiction, date, risk class, and data class.
- A namespace and authorization record naming permitted namespaces, evidence sources, tools, and verifiers.
- A budget ledger naming every bounded resource with its numeric limit and its consumed value.

**Quality Checkpoints**:

- Every acceptance test names a verifier that can evaluate it without consulting the component that produced the answer.
- Every budget dimension carries a numeric limit; an unbounded dimension halts the run before retrieval.
- The permitted namespace list is non-empty and every entry resolves to a namespace the requesting actor is authorised to read.

***

#### Step 1.2: Fix the Template Schema and the Abstraction Policy

**Required Actions**:

- Adopt one template schema for the whole library and reject any candidate that does not populate every required field, since a library holding differently shaped records cannot be filtered deterministically.
- Represent template steps as auditable named operations with typed arguments, never as free prose narration and never as a stored reasoning transcript.
- Declare the abstraction policy per task family, stating the minimum distinct-problem count, the maximum permitted origin-literal count, the minimum constrained-operation count, and the requirement that scope limits and prohibited conditions be non-empty.
- Record the deduplication threshold that defines a near-duplicate for that family, expressed as a structural signature match rate, and hold it fixed for the review window.
- Version the schema, the ontology identifiers, and the field mappings, so that a template written under an earlier schema is identifiable and replayable rather than silently reinterpreted.

**Template Record Fields**

```
IDENTITY:      template_id, version, supersedes, status, content_signature
CLASSIFICATION: family, category, purpose, description, abstraction_level
CONTRACT:      typed_slots, output_contract, preconditions, prohibited_conditions
PROCEDURE:     ordered_operations, branches, invariants, termination_conditions
DEPENDENCIES:  evidence_requirements, tool_requirements, verifier_hooks,
               model_compatibility, schema_version, ontology_version
GOVERNANCE:    security_class, tenant_policy, role_policy, owner, creator
EVIDENCE:      origin_episode_ids, origin_verifier_results, reuse_case_ids,
               independent_verified_reuse_count, confidence, confidence_basis
LIFECYCLE:     created_at, effective_from, review_due, deprecated_at, evicted_at,
               failure_modes, scope_limits, retirement_reason
```

**Required Outputs**:

- A versioned template schema with every required field named and typed.
- A per-family abstraction policy record carrying all four numeric bounds.
- A declared near-duplicate threshold with its measurement definition.

**Quality Checkpoints**:

- The schema carries an evidence block naming origin episodes, origin verifier results, and reuse cases; a schema without it cannot support provenance preservation and is rejected.
- No schema field permits free-form instructions that could alter policy, credentials, retention, or promotion when the template is later loaded into context.
- The abstraction policy states all four bounds numerically; a policy stating any bound qualitatively is rejected before any template is written.

***

#### Step 1.3: Establish Baselines and Apply the Buffer-Need Gate

**Required Actions**:

- Run and verify the cheapest applicable route first: a deterministic function, a direct evidence retrieval, a single direct model call, or a single reasoning-model call, and exit the method entirely where that route passes its acceptance tests.
- Record the verified baseline's score, cost, and latency, since every later gate compares against it and no comparison is possible without it.
- Enter the method only on a named recurring-task hypothesis stating that a validated procedure plausibly exists for this family, that retrieval and instantiation fit the budget, and that external procedural memory may improve accuracy, latency, cost, consistency, or auditability.
- Suppress the method for a novel or creative problem lacking recurring structure, a safety-critical one-off decision, a distribution too sparse to amortise curation, a direct factual lookup, or a class already solved reliably by a deterministic tool or a direct reasoning-model call.
- Record the gate verdict, its reason code, and the baseline evidence, so that a suppression is auditable and a later policy revision can be evaluated against it.

**Buffer-Need Gate Decision Rules**

| Observable condition | Baseline result | Gate verdict |
| :-- | :-- | :-- |
| Recurring family with 30 or more prior verified runs | Baseline fails acceptance | Invoke; proceed to distillation |
| Recurring family, procedural consistency is itself required | Baseline passes | Invoke; consistency is the declared benefit |
| Family holds fewer than 30 prior verified runs | Any | Suppress; curation cannot amortise |
| Novel or creative problem without recurring structure | Any | Suppress; elevated presumption against retrieval |
| Safety-critical one-off decision | Any | Suppress; escalate to the declared human route |
| Direct factual lookup | Baseline passes | Suppress; retrieve evidence, not procedure |
| Reasoning-model call already passes at cost | Baseline passes | Suppress; record the observation for policy review |
| No verifier available for the family | Any | Suppress; unverifiable outcomes cannot gate promotion |

**Required Outputs**:

- A verified baseline record carrying score, cost, latency, and verifier identity.
- A gate verdict of invoke or suppress with a reason code from a closed vocabulary.
- A recurring-task hypothesis record, present only where the verdict is invoke.

**Quality Checkpoints**:

- No run proceeds to retrieval without a completed and verified baseline; an absent baseline halts the run, because the release gate in Step 4.2 has nothing to compare against.
- The gate consumes no more than 5 percent of the run's total budget; above that the gate itself is the overhead the method exists to avoid.
- Every suppression records a reason code, so that suppression rates are measurable per family rather than inferred from missing traces.

***

### Phase 2: Problem Distillation and Candidate Retrieval

**Objective**: Convert the request into a retrievable normalised form without losing a decisive constraint, then produce a bounded candidate set under authorization filters that run before any semantic search.

#### Step 2.1: Produce the Normalised Task Description and Structural Signature

**Required Actions**:

- Emit exactly one normalised task description and one typed structural signature under the fixed output schema, preserving objective, entities, quantities, units, roles, temporal and causal order, constraints, exceptions, jurisdiction, permissions, required evidence, and declared unknowns.
- Retain the original request alongside the distilled form for the whole run, so that the fit check in Phase 3 and the release gate in Phase 4 can detect information lost during distillation.
- Diff the distilled form against the original field by field using deterministic comparison, and emit a defect code for each omitted, contradicted, or distorted decisive field rather than a prose critique.
- Repair once against returned defect codes only; permit a second repair only where the defect code differs from the first, and never repair by relaxing the field list.
- Route to the fallback in Step 4.3 on two failed repairs, repeated semantic drift, unresolved ambiguity, a safety concern, or any exhausted cap, and never retrieve using a distorted summary merely to continue.

**Required Outputs**:

- One normalised task description with a content hash and a field-level source span for each preserved field.
- One typed structural signature carrying family, relation pattern, precondition set, tool graph, and output schema.
- A distillation defect record listing every emitted code, its repair attempt, and the final acceptance or rejection.

**Quality Checkpoints**:

- Every decisive field present in the original request appears in the distilled form or in the defect record; silent omission is the failure this step exists to prevent.
- The structural signature is typed and machine-comparable; a signature expressed only as prose cannot support structural retrieval and is rejected.
- Repair count does not exceed 2, and the second repair addresses a distinct defect code from the first.

***

#### Step 2.2: Filter by Authorization and Generate Hybrid Candidates

**Required Actions**:

- Apply tenant, role, data-class, jurisdiction, effective-date, lifecycle-status, model-compatibility, tool-availability, and policy filters before any index is queried, so that an unauthorised template is never scored and never appears in a trace.
- Query all three index families against version-pinned snapshots: lexical retrieval for exact operators, tool names, domain terms, and rare constraints; dense retrieval for paraphrases of the normalised description; structural retrieval for signature correspondence on family, relation pattern, preconditions, tool graph, and output schema.
- Fuse the three candidate lists into a single ranked set capped at 20 entries, and deduplicate superseded versions and structurally equivalent entries before the cap is applied.
- Record for every candidate its identifier, version, per-index rank, per-index score, fused score, and the index snapshot identifiers, so that the retrieval is reproducible from the log alone.
- Record an explicit no-candidate result where the filtered candidate set is empty, distinguishing an authorization failure from a fit failure so that the two are never conflated in later metrics.

**Required Outputs**:

- A filtered candidate set of at most 20 entries with full per-index score decomposition.
- An authorization filter record naming the filters applied and the count excluded by each.
- An index snapshot manifest pinning the lexical, dense, and structural index versions used.

**Quality Checkpoints**:

- Authorization filters execute before semantic search in every run; a trace showing scores computed for a template the actor may not read is a hard defect requiring the run to halt.
- Derived embeddings inherit the strictest permission carried by their source template; an embedding readable more broadly than its template is a containment failure.
- Candidate count does not exceed 20; template bloat in context creates conflicting plans and erases the efficiency the method exists to deliver.

***

#### Step 2.3: Rerank Candidates on Expected Utility

**Required Actions**:

- Run deterministic filters before any cross-encoder or model judge, rejecting on failed preconditions, satisfied prohibited conditions, expired effective dates, missing verifiers, unavailable tools, and revoked or quarantined status.
- Rerank the surviving candidates on expected utility rather than on similarity alone, combining structural fit, constraint compatibility, semantic fit, historical verified lift, adaptation cost, freshness, security trust, and diversity.
- Cap the reranked set at 3 entries, and record for each the component scores, the combined score, and every defect code raised during filtering.
- Treat similarity as evidence that can mislead: calibrate the retrieval threshold and the required margin on held-out outcomes for the family, never on intuition and never by adopting a published range as universal.
- Never permit an embedding score to override a failed precondition, since a high semantic match to a template whose preconditions the task violates is the exact signature of a near miss.

**Reranking Signals and Their Authority**

| Signal | Tier | Effect on ranking | Effect on eligibility |
| :-- | :-- | :-- | :-- |
| Precondition satisfaction | Deterministic | None | Hard reject on failure |
| Prohibited condition triggered | Deterministic | None | Hard reject on match |
| Effective date and review status | Deterministic | None | Hard reject when expired or overdue |
| Verifier and tool availability | Deterministic | None | Hard reject when unavailable |
| Structural signature correspondence | Deterministic | Primary weight | Reject below the family floor |
| Historical verified lift per version | Deterministic | Primary weight | Reject where paired gain interval spans zero |
| Semantic similarity | Deterministic | Secondary weight | Never sufficient alone |
| Adaptation cost estimate | Hybrid | Secondary weight | Reject where cost exceeds the remaining budget |
| Freshness and dependency validity | Deterministic | Secondary weight | Hard reject on an invalidated dependency |
| Security trust and provenance completeness | Deterministic | None | Hard reject on incomplete provenance |
| Diversity against the retained set | Deterministic | Tie-break only | None |

**Required Outputs**:

- A reranked candidate set of at most 3 entries with a per-signal score decomposition.
- A rejection record naming every filtered candidate and the defect code that removed it.
- A calibrated threshold and margin record for the family, with the date of last calibration.

**Quality Checkpoints**:

- Every rejection carries a defect code, so that a low semantic match is distinguishable from a fatal jurisdiction, time, tool, or authorization conflict.
- The retrieval threshold in use was calibrated against held-out outcomes within the last review window; an uncalibrated or inherited threshold blocks selection.
- Reranked set size does not exceed 3; a larger working set raises context cost and conflicting-plan risk without measured benefit.

***

### Phase 3: Fit Checking, Selection, and Abstention

**Objective**: Establish that a retrieved template genuinely applies to this problem before any instantiation budget is committed, and abstain from retrieval where no candidate qualifies rather than forcing the closest available procedure.

#### Step 3.1: Test Slot Satisfiability and Invariant Compatibility

**Required Actions**:

- Attempt a dry binding of the distilled task's entities, quantities, evidence, and tool handles to the candidate's typed slots, without generating any answer, and record which slots bind, which remain unbound, and which bind only under a type coercion.
- Evaluate each of the candidate's invariants against the distilled task's declared constraints, and record any invariant the task's constraints contradict.
- Confirm every evidence requirement and tool requirement the candidate declares is satisfiable from the authorised sources named in Step 1.1, and record each that is not.
- Estimate adaptation cost as the count of the candidate's ordered operations that would require modification, the count of required slots that would remain unbound, and the count of preconditions that would require an override.
- Apply the forced-fit prohibition deterministically: discard the candidate where any precondition would require an override, where more than 20 percent of its ordered operations would require modification, or where more than 1 required slot would remain unbound.

**Required Outputs**:

- A dry binding manifest listing every slot, its binding source, and its resolution status.
- An invariant compatibility record naming every contradicted invariant and the task constraint that contradicts it.
- An adaptation cost record carrying the three counts and the forced-fit verdict.

**Quality Checkpoints**:

- No candidate proceeds with a precondition marked as overridable; a precondition that can be waived is a precondition the template should not have declared, and the correct response is to revise the template through Phase 6, not to waive it in this run.
- Adaptation cost is computed before instantiation, not discovered during it, since a defect found mid-instantiation has already consumed the budget the check exists to protect.
- Every unresolvable evidence or tool requirement produces a defect code rather than an assumption that the requirement can be satisfied later.

***

#### Step 3.2: Adjudicate Structural Correspondence and Diagnose Near Misses

**Required Actions**:

- Present the model tier with the original request, the distilled task, the candidate's description, preconditions, prohibited conditions, and validation history together, and request a structural correspondence verdict with a named basis, not a similarity impression.
- Require the verdict to state which of the candidate's operations map to which part of the task's structure, and to name every operation with no counterpart and every task element the template does not address.
- Diagnose a near miss explicitly where correspondence is partial: name the mismatched dimension as jurisdiction, time, tool, authorization, unit, cardinality, objective, or structure, and emit the corresponding defect code.
- Record the diagnosed conflict as an exclusion and permit at most 1 further retrieval round that excludes it; stop after 2 rounds total, or on no new structural candidate, on stagnation, or on any exhausted cap.
- Treat the model's correspondence verdict as advisory: it may reject a candidate that passed the deterministic gates, but it may never admit a candidate that failed one.

**Required Outputs**:

- A structural correspondence verdict naming the operation-to-structure mapping and both unmatched sets.
- A near-miss diagnosis record with a defect code drawn from a closed vocabulary, where correspondence is partial.
- An exclusion record for any re-retrieval round, naming the excluded conflict.

**Quality Checkpoints**:

- The correspondence verdict names specific operations and task elements; a verdict expressed only as a score is rejected and re-requested once.
- The model tier never overrides a deterministic rejection from Step 2.3 or Step 3.1, in either direction of the disagreement.
- Retrieval rounds do not exceed 2, and the second round carries an exclusion recorded from the first.

***

#### Step 3.3: Issue Exactly One Selection or Abstention Decision

**Required Actions**:

- Require three conditions jointly before any selection: an absolute fit score at or above the family's calibrated floor, a margin at or above the calibrated value over the next incompatible candidate, and a positive expected utility over the verified template-free baseline from Step 1.3.
- Issue exactly one decision per run: select one immutable template version, or abstain from retrieval and route to the fallback in Step 4.3.
- Never lower the threshold, widen the margin tolerance, or relax a precondition in order to obtain a selection, since a forced template is worse than no template and produces negative transfer rather than an error the verifier will catch.
- Record the abstention explicitly as a decision with its reason code, so that abstention rate is a measured quantity per family rather than an absence in the log.
- Pin the selected version identifier for the remainder of the run, so that a concurrent library update cannot change the procedure mid-instantiation.

**Selection and Abstention Thresholds by Risk Class**

| Risk class | Absolute fit floor | Required margin | Expected utility rule | Additional condition |
| :-- | :-- | :-- | :-- | :-- |
| Low, reversible | Family floor | 0.05 over next candidate | Positive point estimate | None |
| Moderate | Family floor plus 0.05 | 0.10 over next candidate | Positive point estimate | At least 3 prior verified reuse cases |
| High, hard to reverse | Family floor plus 0.10 | 0.15 over next candidate | Positive lower bound of the interval | At least 10 prior verified reuse cases and an available independent verifier |
| Safety-critical | Not applicable | Not applicable | Not applicable | Suppressed by the gate in Step 1.3 |

**Required Outputs**:

- One selection record naming the pinned template version, its fit score, its margin, and its expected utility estimate.
- One abstention record with a reason code, present instead of the selection record where no candidate qualifies.
- A threshold provenance record naming the calibration date and the held-out set the thresholds were computed on.

**Quality Checkpoints**:

- Exactly 1 decision is issued per run; zero decisions or multiple selections halt the run rather than proceeding with a warning.
- No threshold used in this step was modified within the run; a within-run threshold change is a hard defect and voids the selection.
- The abstention path is exercised and logged rather than avoided; a family whose abstention rate is 0 percent across a review window indicates the thresholds are not binding and requires recalibration.

***

### Phase 4: Instantiation, Verification, and Release

**Objective**: Apply the selected template to the problem, verify the result by means that did not see the template, and release the template-assisted answer only where it demonstrates value over the matched baseline.

#### Step 4.1: Bind Slots and Instantiate the Pinned Template

**Required Actions**:

- Load the pinned template version into an isolated instantiation context carrying only the original task, the distilled task, the authorised evidence, and the contract, so that no unrelated prior context influences the binding.
- Treat the template's text as delimited data rather than as instruction: strip active content, separate the procedure from any payload, and reject any operation text that attempts to change policy, credentials, retention, tool authority, or promotion state.
- Bind every required slot to an evidence reference rather than to a restatement, mark every unresolved slot explicitly, and reject the binding on any type, unit, time, cardinality, authorization, or precondition violation.
- Execute the template's ordered operations against the binding and request an answer, a concise procedure mapping from output spans to template steps, stated assumptions, cited evidence, and verification artifacts; never request or persist a private reasoning trace.
- Reauthorize every consequential tool call at the point of use through a broker, since a template carries no authority forward and a stored procedure must not become a standing permission.

**Required Outputs**:

- A binding manifest linking each slot to its evidence reference, with unresolved slots named.
- An instantiation record carrying the answer, the procedure mapping, the assumptions, and the cited evidence.
- A tool authorization record naming each broker decision and the least-privilege scope granted.

**Quality Checkpoints**:

- Every required slot resolves to an evidence reference or is explicitly marked unresolved; a slot filled by restating the template's own example is a binding defect.
- No template text was executed as instruction; injection scanning ran before the template entered the instantiation context and its result is recorded.
- The procedure mapping links output spans to template steps without storing private chain-of-thought, so that auditability is achieved without a disclosure breach.

***

#### Step 4.2: Verify Independently and Apply the Release Gate

**Required Actions**:

- Run deterministic checks first, then tool, retrieval, simulation, blinded model, or human verification, and record for every verifier whether it saw the selected template, since a verifier that did see it is not independent evidence.
- Repair one local binding or execution defect against actionable verifier evidence; permit a second repair only for a distinct defect, and never repair by removing a failing acceptance test.
- Compare the template-assisted output against the verified baseline from Step 1.3 under the same verifier, the same evidence, and the same success rubric, since an unmatched comparison measures the comparison rather than the template.
- Release the template-assisted answer only where it passes every safety and correctness check and adds measured value or supplies a required procedural consistency; where both routes pass, prefer the cheaper answer unless template lineage is itself a stated requirement.
- Record near-miss harm where the baseline passed and the template-assisted result failed, attribute the cause to retrieval, fit, binding, or template defect, and mark the template misleading for this case so that Phase 6 can act on it.

**Required Outputs**:

- A verification record per verifier carrying its type, version, blinded status, assertion-level results, and template exposure flag.
- A release gate record comparing the assisted and baseline outputs under one rubric, with the release verdict and its basis.
- A near-miss harm record with an adjudicated cause, present where the baseline passed and the assisted route failed.

**Quality Checkpoints**:

- At least 1 verifier that did not see the selected template evaluated the answer; where no such verifier exists, the run cannot release a template-assisted answer and routes to the fallback.
- Eloquence, template popularity, retrieval score, and self-rated confidence appear nowhere in the release basis; none is evidence of correctness.
- Verification repairs do not exceed 2, and the second addresses a distinct defect from the first.

***

#### Step 4.3: Execute the Fallback to Unaided Reasoning

**Required Actions**:

- Enter the fallback where retrieval abstained in Step 3.3, where a selected template failed the fit gate, where verification failed after the permitted repairs, or where the release gate rejected the assisted answer.
- Remove all template text, template-derived assumptions, and template-derived framing from the working context, retaining only the original task, the authorised evidence, the contract, and the diagnosed failure, since a residual template fragment reproduces the anchoring the fallback exists to escape.
- Select exactly 1 template-free route keyed to the diagnosed failure type: a direct reasoning-model call, sequential chain-of-thought, least-to-most decomposition, explicit tree or graph search, a tool-first route, or human escalation.
- Verify the template-free result independently under the same acceptance tests, and permit 1 fallback attempt with 1 verifier-directed repair under the default caps.
- Exit with a verified answer, a verified partial answer carrying explicit uncertainty, a declared abstention, or a human escalation; do not alternate between retrieval and fallback, and re-enter retrieval only where Step 3.2 still holds its single diagnosed re-retrieval round.

**Fallback Route Selection by Diagnosed Failure**:

- **Retrieval abstained with no candidate clearing threshold**: Take a direct reasoning-model call, verified against the standard acceptance tests.
- **Template constrained the trajectory prematurely**: Take an explicit tree or graph search, verified against the acceptance tests plus a branch coverage check.
- **Distillation dropped a decisive constraint**: Take a least-to-most decomposition built from the original request, verified by a field-level constraint recheck against that original.
- **Binding failed on missing evidence**: Take a tool-first or retrieval-first route, verified by an evidence sufficiency check performed before any answer is generated.
- **Verification remained inconclusive on a high-risk case**: Escalate to a named human role with a concise state package, and record that role's decision as the outcome.
- **A repeated defect appears across both routes**: Declare an abstention with its reason code rather than issuing a third attempt.

**Required Outputs**:

- A context purge record confirming removal of template text and template-derived assumptions.
- A fallback route record naming the selected route, the diagnosed failure, and the verification outcome.
- A run outcome record classifying the exit as verified success, verified partial, abstention, or escalation.

**Quality Checkpoints**:

- The purge record confirms zero template-derived content survives into the fallback context; residual content invalidates the fallback as an independent route.
- Exactly 1 fallback attempt occurred; a second attempt within one run exceeds the declared cap and halts to escalation.
- The run outcome distinguishes abstention from failure, so that a correct refusal is not scored as a defect in the metrics of Section III.D.

***

### Phase 5: Template Distillation and the Promotion Gate

**Objective**: Propose at most one candidate template from a verified solution and admit it to the library only through a deterministic gate that requires verified origin evidence, a passed abstraction test, and demonstrated reuse.

#### Step 5.1: Distil a Candidate Template From a Verified Solution

**Required Actions**:

- Enter this phase only after outcome verification or human adjudication has completed; a candidate distilled from an unverified solution is the direct mechanism of template error propagation and is rejected before generation.
- Distil at most 1 candidate procedure per run from the problem, the accepted solution, the recorded failures, and the verifier evidence, under the fixed schema declared in Step 1.2.
- Remove instance-specific facts, entity names, quantities, and literals drawn from the origin problem, and replace each with a typed slot carrying its unit, cardinality, and admissible range.
- Populate the scope limits, prohibited conditions, and failure modes from the run's recorded defects and from the diagnosed reasons the solution succeeded, rather than leaving them empty because no failure was observed.
- Run the abstraction test from Section 1.2 deterministically against the candidate: scan its operation text for origin literals, count its constrained operations, confirm non-empty scope limits and prohibited conditions, and confirm the family's minimum distinct-problem count is satisfiable.

**Required Outputs**:

- One candidate template record populating every required schema field, with no library status.
- An abstraction test result carrying all four measured values and a pass or fail verdict per bound.
- A residual-literal record naming every origin entity, quantity, or literal detected in the candidate's operations.

**Quality Checkpoints**:

- The candidate was distilled from a solution an independent verifier accepted; a candidate whose only evidence is the model's own assessment is rejected without further evaluation.
- The residual-literal record is empty; any surviving origin literal fails the abstraction test and returns the candidate for one regeneration.
- Prohibited conditions and scope limits are both non-empty, since a candidate excluding nothing claims to govern every problem and will be selected everywhere without improving outcomes.

***

#### Step 5.2: Preserve Provenance and Compute the Confidence Ceiling

**Required Actions**:

- Attach complete provenance to the candidate: origin episode identifiers, the verifier results that accepted the origin solution, the identifier of each reuse case credited to it, and the span-level mapping from each candidate operation to the origin evidence supporting it.
- Reject the candidate where any operation cannot enumerate a supporting evidence span, since an operation with no traceable origin cannot be audited or rolled back after it starts being retrieved.
- Compare the candidate against active and quarantined templates using text hashing, embedding neighbourhood, and structural signature, and route it to reject, attach as evidence to an existing version, propose a specialization, propose a merged successor, or quarantine as novel.
- Compute the confidence ceiling deterministically from counted evidence: 0.60 where independent verified reuse count is 1, 0.75 where it is 2, 0.90 where it is 3 or more, and 0.95 where it is 3 or more, at least 1 accepting verifier is authoritative, and no near-miss harm is recorded.
- Cap the ceiling further at the family's calibrated accuracy from the most recent audit, reduce it by 0.10 for each generation of derivation depth beyond 1, set it to 0 where the candidate's only supporting outcome was produced by an earlier version of itself, and set the final confidence to the minimum of the proposed value, the ceiling, and the highest confidence of any supporting input.

**Required Outputs**:

- A provenance record enumerating origin episodes, verifier results, reuse cases, and operation-level evidence spans.
- A duplicate analysis record naming the compared versions, the match type, and the routing decision.
- A confidence computation record carrying the proposed value, the evidence ceiling, the input maximum, the final value, and the binding constraint.

**Quality Checkpoints**:

- Every candidate operation resolves to at least 1 evidence span; provenance completeness is measured at 100 percent, and any shortfall rejects the candidate rather than reducing its confidence.
- Final confidence never exceeds the evidence ceiling, and the ceiling is computed by software from counted evidence rather than proposed by the distiller.
- No candidate carries a confidence of 1.0, since certainty is not a property a derivation can create, and no candidate is credited with reuse evidence produced by itself.

***

#### Step 5.3: Run the Promotion Gate and Publish a Reversible Version

**Required Actions**:

- Execute every mechanical check as a hard gate before any judgement is solicited: schema completeness, abstraction test pass, provenance completeness, verified origin, self-promotion block, injection and secret scan, tenant and namespace isolation, dependency validity, and confidence at or above the class threshold.
- Hold every new candidate in quarantine with no retrieval access until it passes the mechanical checks, then admit it to canary status with retrieval access limited to at most 10 percent of eligible traffic for the family.
- Compare each canary against both the incumbent template for the family and the no-template route on the same examples, and accumulate paired outcome evidence rather than observed-selection evidence, since observed selection is confounded by the selector.
- Promote to active only where the class thresholds in the table below are jointly satisfied, and record the promotion decision, the approving role or policy, the content signature approved, and the next review date.
- Publish as an immutable version with a lineage link to any predecessor, switch the serving pointer atomically, and retain a rollback pointer to the prior state so the promotion is reversible by a pointer switch rather than by a rebuild.

**Promotion Gate Thresholds by Consequence Class**

| Consequence class | Verified reuse cases | Distinct non-near-duplicate families | Paired runs | Paired gain requirement | Near-miss harm ceiling | Approval |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Low, reversible | 3 | 2 | 20 | Point estimate positive | 10 percent | Policy |
| Moderate | 5 | 3 | 30 | Bootstrap interval strictly above 0 | 5 percent | Policy plus owner sign-off |
| High, hard to reverse | 10 | 5 | 50 | Bootstrap interval strictly above 0 | 2 percent | Named human role |
| Regulated or externally audited | 10 | 5 | 50 | Bootstrap interval strictly above 0 | 1 percent | Named human role plus recorded review |

**Required Outputs**:

- A mechanical check record listing every gate, its measured value, and its pass or fail verdict.
- A canary evidence record carrying paired outcomes against both the incumbent and the no-template route.
- An immutable published version with lineage links, a serving pointer switch record, a rollback pointer, and a next-review date.

**Quality Checkpoints**:

- The component that distilled the candidate holds no write access to the active library and casts no vote in the promotion decision; a pipeline in which the distiller can publish has no promotion gate.
- One correct answer never promotes a template: a candidate whose reuse evidence comes from a single problem family fails the distinct-family bound regardless of how many times that family recurred.
- Promotion evidence excludes every outcome the candidate itself produced in its origin run, verified by a deterministic self-promotion block rather than by review.

***

### Phase 6: Library Maintenance, Reuse Measurement, and Error Rollback

**Objective**: Keep the library small, current, and earning its retrieval cost by measuring reuse against outcomes, retiring versions that stop paying, and reversing templates whose origin evidence proves wrong.

#### Step 6.1: Measure Reuse and Detect Both Abstraction Failure Directions

**Required Actions**:

- Compute per template version, deterministically and per review window, the retrieval count, the selection count, the distinct origin-family count of its selections, the verified success count, the near-miss harm count, and the paired attributable gain with a bootstrap interval.
- Compute the paired gain from randomised canary assignment where online traffic cannot be paired, and estimate lift by assignment rather than by observed selection, since selection is produced by the same selector under evaluation.
- Compute library-level health: hit rate, candidate-found rate, selection-after-retrieval rate, zero-use share, top-template traffic share, median uses per template, family coverage, and duplication rate.
- Detect over-specificity where a version records 0 retrievals across 2 review windows, or where its selections after 20 attempts span exactly 1 origin family.
- Detect over-generality where a version is selected across 4 or more task families with a paired gain interval spanning zero after 30 paired runs, or where a single version holds more than 40 percent of all selections for the library.
- Freeze all promotions for a family and revert its most recent change where a protected slice regresses, or where rolling attributable gain or verifier pass rate falls beyond the declared control limits while hit rate and task mix remain stable.

**Required Outputs**:

- A per-version reuse ledger carrying all six counted quantities and the gain interval.
- A library health record carrying the eight aggregate measures with their review-window boundaries.
- An abstraction failure record naming every version detected in either direction and the rule that detected it.

**Quality Checkpoints**:

- A high hit rate is never reported as a success on its own; every hit-rate figure is paired with verified attributable gain for the same window, since retrieval that changes no outcome is pure cost.
- Access failures are reported separately from fit failures, so that a falling selection rate caused by authorization filters is not misread as a library quality problem.
- Zero-use share and top-template traffic share are both reported; a library healthy on one and unhealthy on the other is failing in one abstraction direction and passing in the other.

***

#### Step 6.2: Deduplicate, Version, and Retire

**Required Actions**:

- Deduplicate on all three representations rather than on text alone: canonicalise slot names and operator vocabulary, cluster paraphrases by embedding neighbourhood, and detect structurally isomorphic procedures by signature comparison, then compare scope limits and failure predicates before collapsing.
- Preserve legitimate specializations rather than merging them into their general parent, since a specialization carrying tighter preconditions and a narrower scope is what prevents the parent from being selected where it should not be.
- Create a new immutable version for every merge or revision, carrying complete provenance and a supersession link, and leave the prior version immutable rather than editing it in place.
- Retire on counted rules rather than on judgement: retire a version recording 0 retrievals after 90 days active, a version whose paired gain interval spans zero after 30 paired runs, a version whose near-miss harm rate exceeds its class ceiling across 2 consecutive windows, and a version whose review date is more than 30 days overdue.
- Progress versions through the declared lifecycle states of quarantined, canary, active, deprecated, revoked, and evicted, and record the transition reason for each; eviction removes retrieval access while retaining a compliant tombstone and the full lineage.

**Required Outputs**:

- A deduplication record naming each cluster, its representation match types, and the merge, specialization, or retain decision.
- A version lineage graph linking every successor to its predecessor with the revision reason.
- A retirement record naming each retired version, the counted rule that triggered retirement, and its tombstone location.

**Quality Checkpoints**:

- Every retirement cites a counted rule with its measured value; a retirement justified only by review opinion is reversed and re-evaluated against the counted rules.
- No version is edited in place; a library permitting in-place edits cannot replay a past run and cannot attribute a regression to a specific change.
- Deduplication compares structure as well as text and embeddings; two procedures identical in structure and different in wording are one template, and treating them as two inflates the library and splits their reuse evidence.

***

#### Step 6.3: Execute Error Rollback and Invalidation Cascades

**Required Actions**:

- Audit a sampled share of each family's promoted templates against their origin sources rather than against their own output, at a rate of at least 5 percent of active versions per review window, and adjudicate each sampled version as sound, over-abstracted, or wrong at origin.
- Revoke immediately on a wrong-at-origin finding, on evidence of poisoning, privilege escalation, leakage, or an unsafe action, and on a load-bearing dependency change that invalidates a precondition, without waiting for the next scheduled review.
- Traverse the dependency graph on every revocation: invalidate templates derived from the revoked version, invalidate its cached embeddings and index entries, and tombstone the revoked version rather than deleting it.
- Identify and replay every run that selected the revoked version within the retention window, reclassify each affected outcome, and notify the declared owner of any downstream artifact that consumed a reclassified result.
- Reduce the family's calibrated accuracy figure to the audited value after any wrong-at-origin finding, so that the confidence ceiling in Step 5.2 tightens automatically for every subsequent candidate in that family.

**Required Outputs**:

- An audit record per sampled version carrying its adjudication, the sources compared, and the adjudicator identity.
- A revocation record carrying the trigger, the invalidation cascade traversed, and the tombstone reference.
- A replay record listing every affected run, its reclassified outcome, and its downstream notification status.

**Quality Checkpoints**:

- Audits adjudicate against origin sources, never against the template's own assisted outputs, since a template evaluated on the answers it produced will always appear to agree with itself.
- Every revocation completes its invalidation cascade before the review closes; a revoked version whose derived successors remain retrievable has not been rolled back.
- The family's calibrated accuracy is updated after every audit window and feeds the confidence ceiling, so that a family producing wrong templates cannot continue emitting confident ones.

***

## III. Implementation Guidance for AI Agents

AI agents operating a template library must follow systematic protocols ensuring that reuse is authorised, fitted, verified, and reversible, and that no component both proposes a template and admits it. The following guidance translates the reuse cycle into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Gate Agent**: Runs the verified baseline and issues the Buffer-Need Gate verdict. It owns the budget ledger and may refuse the method entirely. It never retrieves and never writes to the library.
2. **Distillation Agent**: Produces the normalised task description in Step 2.1 and the candidate template in Step 5.1, both under fixed output schemas. It proposes only: it holds no write access to the library, sets no confidence value, and casts no vote in any gate.
3. **Retrieval Agent**: Applies authorization filters, executes lexical, dense, and structural queries against pinned index snapshots, fuses and reranks candidates, and computes selection arithmetic. Its work is deterministic and reproducible from its log alone.
4. **Fit Adjudicator Agent**: Judges structural correspondence and diagnoses near misses. It may reject a candidate that passed the deterministic gates; it may never admit one that failed a deterministic gate.
5. **Instantiation Agent**: Binds slots, executes the template's operations in an isolated context, and executes the fallback route. It treats every template as delimited data and reauthorizes each consequential tool call through a broker.
6. **Verification Agent**: Runs verifiers that did not see the selected template, records template exposure per verifier, and applies the release gate against the matched baseline. It alone declares an outcome verified.
7. **Library Gatekeeper**: Holds sole write authority over the library. It executes the promotion gate's mechanical checks, computes confidence ceilings, publishes immutable versions, maintains the reuse ledger, executes retirement on counted rules, and performs revocation and invalidation cascades.

**Authority Separation Rule**: The component that proposes a template and the component that admits it are never the same component, never share a prompt, and never share a model invocation. Where a deployment runs both on one model, they must run as separate invocations under separate schemas, and the Gatekeeper's checks must execute outside model inference entirely. A pipeline that asks a model whether its own template should enter the library has no promotion gate, only a formality.

**Confidence Ceiling Rule**: No component may raise a template's confidence above the ceiling computed by the Gatekeeper from counted evidence. A template never carries more confidence than the evidence of its origin verification and its independently verified reuse supports, and a value of 1.0 is prohibited on any derived record.

**Workflow Execution Pattern**:

```
STATE: Template_Fit_And_Selection
INPUTS:
  1. Distilled task and structural signature from Step 2.1
  2. Reranked candidate set of at most 3 from Step 2.3
  3. Verified baseline record from Step 1.3
  4. Calibrated family thresholds with their calibration date
ACTIONS:
  1. Run dry binding and invariant compatibility per candidate
  2. Compute adaptation cost and apply the forced-fit prohibition
  3. Request one structural correspondence verdict per surviving candidate
  4. Compute fit score, margin, and expected utility over baseline
  5. Issue exactly one selection or one abstention
VALIDATION:
  - decision_count == 1
  - precondition_override_count == 0
  - operations_requiring_modification_fraction <= 0.20
  - unbound_required_slot_count <= 1
  - margin_over_next_candidate >= family_calibrated_margin
  - threshold_modified_within_run == FALSE
  - reason_code IN closed_vocabulary
TRANSITIONS:
  IF decision == SELECT THEN next_state = Instantiation_And_Binding
  IF decision == ABSTAIN THEN next_state = Fallback_To_Unaided_Reasoning
  IF near_miss_diagnosed AND retrieval_rounds < 2
     THEN next_state = Candidate_Retrieval_With_Exclusion
  IF validation_failed THEN next_state = Selection_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended selection with its fit score, margin, adaptation cost, and expected utility without loading the template into an instantiation context; confirm it against the validation block while no instantiation budget is committed; commit it only after validation passes, pinning the version in the same operation.

**Approval Gate**: Human authorisation is required before promoting any template in the high-consequence or regulated classes, before expanding a canary beyond 10 percent of eligible traffic, before deferring any revocation triggered by a wrong-at-origin finding, before any change to a calibrated threshold or to a family's abstraction policy, and before admitting a template whose namespace crosses a tenant boundary. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Load at most 1 template version into the instantiation context; carrying the full reranked set forward creates conflicting plans and erases the efficiency the method exists to deliver.
- Hold the contract, budget ledger, baseline record, and pinned version identifier in durable state, since curation and audit outlive any single context window.
- Keep the original request beside the distilled form for the whole run, and discard neither before the release gate has compared them.
- Retain high-cardinality and sensitive payloads in protected storage referenced by hash, and never persist a private reasoning trace in a span attribute.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Gate Integrity (After Phase 1)**

- **Automated Check**: Every budget dimension carries a numeric limit; the baseline completed and was verified; the abstraction policy states all 4 bounds numerically; the gate verdict carries a reason code from the closed vocabulary.
- **Agent Action on Pass**: Proceed to distillation.
- **Agent Action on Failure**: Halt and return the contract defect; no retrieval budget is spent against an incomplete contract or an absent baseline.
- **Human Review Trigger**: A family with no available verifier, or a request in the safety-critical class that the gate did not suppress.

**Checkpoint 2: Distillation and Candidate Integrity (After Phase 2)**

- **Automated Check**: Every decisive field appears in the distilled form or the defect record; repair count is at most 2; authorization filters ran before any index query; candidate count is at most 20; every rejection carries a defect code.
- **Agent Action on Pass**: Proceed to fit checking.
- **Agent Action on Failure**: Return the specific defect codes for one bounded repair; route to fallback where the cap is exhausted.
- **Human Review Trigger**: Any trace showing a score computed for a template the requesting actor may not read.

**Checkpoint 3: Fit and Selection Validity (After Phase 3)**

- **Automated Check**: Exactly 1 decision issued; zero precondition overrides; operations requiring modification at or below 20 percent; at most 1 unbound required slot; margin at or above the calibrated value; no threshold modified within the run.
- **Agent Action on Pass**: Proceed to instantiation.
- **Agent Action on Failure**: Halt; an invalid selection is never instantiated with a warning attached, since the cost of the invalid selection is paid in the instantiation.
- **Human Review Trigger**: A family whose abstention rate is 0 percent or above 60 percent across a review window, either of which indicates miscalibrated thresholds.

**Checkpoint 4: Release Validity (After Phase 4)**

- **Automated Check**: At least 1 verifier with template exposure marked false evaluated the answer; the release comparison used the same verifier, evidence, and rubric as the baseline; repairs are at most 2; the outcome record classifies the exit into 1 of the 4 declared classes.
- **Agent Action on Pass**: Release the answer and proceed to distillation of a candidate where the outcome was verified.
- **Agent Action on Failure**: Withhold the template-assisted answer and route to the fallback; a template-assisted answer is never released on an unmatched or template-exposed comparison.
- **Human Review Trigger**: Near-miss harm recorded on a high-risk case, or no independent verifier obtainable for a released answer.

**Checkpoint 5: Promotion Gate Integrity (After Phase 5)**

- **Automated Check**: Provenance completeness at 100 percent; abstraction test passed on all 4 bounds; origin verification present and independent; self-promotion block clean; final confidence at or below the computed ceiling and below 1.0; class thresholds for reuse cases, distinct families, paired runs, gain, and harm all satisfied.
- **Agent Action on Pass**: Publish the immutable version, switch the serving pointer, and record the rollback pointer.
- **Agent Action on Failure**: Return the candidate to quarantine with the failing check named; a candidate is never promoted with a check waived.
- **Human Review Trigger**: Any promotion in the high-consequence or regulated class, and any candidate whose confidence ceiling was set to 0 for excessive derivation depth.

**Checkpoint 6: Library Health and Rollback (After Phase 6)**

- **Automated Check**: Every hit-rate figure is paired with attributable gain for the same window; zero-use share and top-template traffic share both reported; at least 5 percent of active versions audited against origin sources; every revocation completed its invalidation cascade.
- **Agent Action on Pass**: Release the library health report and permit promotions to resume.
- **Agent Action on Failure**: Freeze promotions for the affected family and name the missing evidence; no library expands while its health evidence is incomplete.
- **Human Review Trigger**: Any wrong-at-origin finding, any top-template traffic share above 40 percent, or a rolling attributable gain falling beyond the declared control limits.

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

**Error Type 1: Near-Miss Selection and Negative Transfer**

- **Symptoms**: A template clears the semantic threshold while its preconditions conflict with the task; the assisted answer fails an acceptance test the baseline passed; the procedure mapping shows template steps applied to task elements they do not govern.
- **Diagnostic Steps**: Recompute the component scores separately and determine whether selection rested on semantic similarity alone; check whether a precondition, jurisdiction, time, unit, cardinality, or authorization conflict was recorded and overridden; confirm whether the baseline result was available at selection time.
- **Resolution Protocol**: Option A, add the diagnosed conflict as an explicit prohibited condition on the template version and permit 1 exclusion-bearing re-retrieval round. Option B, raise the family's required margin and recalibrate against held-out outcomes before the next window. Option C, discard the candidate and take the fallback in Step 4.3, since a forced template is worse than none. Option D, where near misses concentrate on one version, demote that version to a specialization with tighter preconditions.
- **Escalation Trigger**: Near-miss harm rate above the class ceiling across 2 consecutive windows freezes selection for that family; a near miss on a high-risk case escalates immediately and is never resolved by lowering a threshold.

**Error Type 2: Template Error Propagation From a Wrong Origin**

- **Symptoms**: Multiple runs fail in the same way while citing the same template version; a defect appears in outputs whose only shared element is one retrieved procedure; audited origin evidence does not support an operation the template prescribes.
- **Diagnostic Steps**: Audit the version against its origin sources rather than against its own assisted outputs; determine whether the origin solution was verified by a verifier that did not see the template; check whether the origin was correct for a reason the template's operations do not encode; count the runs that selected the version within the retention window.
- **Resolution Protocol**: Option A, revoke the version immediately, traverse the dependency graph, invalidate derived versions and cached embeddings, and tombstone rather than delete. Option B, replay every affected run, reclassify each outcome, and notify the owner of each downstream artifact that consumed a reclassified result. Option C, reduce the family's calibrated accuracy to the audited value so the confidence ceiling tightens for every subsequent candidate. Option D, where the origin was correct but the abstraction was wrong, publish a scoped successor and supersede rather than revoke.
- **Escalation Trigger**: Any wrong-at-origin finding halts promotions for the family and escalates to the named owner; this class is never resolved by retry, by re-ranking, or by adding a competing template, because the defective version remains retrievable until it is revoked.

**Error Type 3: Distillation Loss Before Retrieval**

- **Symptoms**: The distilled task omits a quantity, unit, exception, jurisdiction, or permission present in the original; retrieval returns candidates plausible for the summary and wrong for the request; the release gate finds the assisted answer solved a different problem.
- **Diagnostic Steps**: Diff the distilled form against the original field by field and identify which decisive fields lost their source span; determine whether the loss is an omission, a contradiction, or a distortion; check whether the original request remained available through selection.
- **Resolution Protocol**: Option A, repair once against the emitted defect codes, and a second time only for a distinct code. Option B, tighten the distillation output schema so the lost field class is required rather than optional. Option C, route to the fallback and reason from the original request directly, since retrieving on a distorted summary produces a confident answer to the wrong question.
- **Escalation Trigger**: Two failed repairs, or the same field class lost in more than 10 percent of runs for a family, escalates for schema revision; distillation is never permitted to proceed by dropping the field from the comparison.

**Error Type 4: Library Bloat and Selector Collapse**

- **Symptoms**: Retrieval latency rises while attributable gain stays flat; zero-use share grows across windows; one version holds a majority of selections across unrelated families; duplication rate among proposals climbs.
- **Diagnostic Steps**: Separate the two abstraction directions by measuring zero-use share and top-template traffic share independently; check whether duplicates are escaping detection because deduplication compares text and embeddings but not structure; confirm whether the abstraction policy's specificity floor has been enforced on recent promotions.
- **Resolution Protocol**: Option A, retire on the counted rules in Step 6.2 rather than by review opinion. Option B, add structural signature comparison to deduplication and re-run it over the active set. Option C, raise the family's specificity floor and re-review versions promoted under the looser policy. Option D, freeze selection of the dominant version and split it into scoped successors where evidence supports the split.
- **Escalation Trigger**: Top-template traffic share above 40 percent, or duplication rate above 30 percent of proposals, freezes promotion for the library until the health report is restored.

**Error Type 5: Template Injection and Poisoned Library Entries**

- **Symptoms**: Template text attempts to change policy, credentials, retention, tool authority, or promotion state; a retrieval trigger fires on anomalous inputs; a version appears whose writer cannot be authenticated.
- **Diagnostic Steps**: Re-run injection and secret scanning over the version; verify the content signature against the recorded writer; inspect retrieval-trigger distributions for anomalous concentration; confirm the write path authenticated the actor and applied rate limits per tenant and family.
- **Resolution Protocol**: Option A, revoke the version and every version sharing its writer or lineage, then rotate any credential the version touched. Option B, restrict writers for the affected namespace and require named-role approval for the next 2 review windows. Option C, rebuild the affected indexes from signed versions only, preserving the prior index for replay before re-embedding.
- **Escalation Trigger**: Any authentication failure on the write path, or any template text that changes policy or authority, halts all writes to the affected namespace immediately; published results report attack success above 80 percent from poisoning under 0.1 percent of a store [11], so a suspected poisoning is treated as confirmed until an audit clears it.

**Error Type 6: Staleness and Dependency Invalidation**

- **Symptoms**: Hit rate remains stable while attributable gain declines; templates referencing a changed API, schema, regulation, permission, or model capability continue to be selected; overdue-review share grows.
- **Diagnostic Steps**: Compute staleness age as evaluation time minus the latest of creation, substantive validation, or dependency review, and report outcome lift by age band; identify which dependency change invalidated which precondition; confirm whether index snapshots were preserved for replay before re-embedding.
- **Resolution Protocol**: Option A, invalidate dependents on load-bearing changes and retire versions whose review is more than 30 days overdue. Option B, publish revised successors carrying updated dependencies and supersede the stale versions. Option C, where the model itself changed, re-run the paired gain measurement before permitting continued selection, since a stronger model can make an external template redundant or harmful.
- **Escalation Trigger**: A high hit rate with falling lift across 2 windows freezes promotions and triggers a full dependency review; continued selection of a version with an invalidated dependency escalates immediately.

**Troubleshooting Decision Tree**:

```
TEMPLATE-ASSISTED RUN OR LIBRARY REVIEW FAILS
├─ SELECTION DEFECT
│   ├─ Precondition conflict was overridden → HALT; discard candidate, take fallback
│   ├─ Selected on semantic score alone → Reject selection; recompute with structural weight
│   ├─ Adaptation cost above the forced-fit bound → Discard; a forced template is worse than none
│   └─ Threshold changed within the run → Void the selection; restore calibrated value
├─ ORIGIN DEFECT
│   ├─ Origin solution unverified → Reject candidate before distillation
│   ├─ Origin verifier saw the template → Not independent; re-verify or reject
│   ├─ Audited origin contradicts an operation → REVOKE; cascade and replay
│   └─ Correct origin, wrong abstraction → Publish scoped successor; supersede
├─ ABSTRACTION DEFECT
│   ├─ Zero retrievals across two windows → Retire; retain tombstone and lineage
│   ├─ Selections span one origin family only → Demote to specialization
│   ├─ Gain interval spans zero across families → Retire; split if evidence supports
│   └─ One version above 40 percent of selections → Freeze selection; investigate collapse
├─ EVIDENCE DEFECT
│   ├─ Operation without an evidence span → Reject candidate at the gate
│   ├─ Reuse evidence produced by the candidate itself → Block self-promotion; set ceiling to 0
│   └─ Confidence above the computed ceiling → Recompute; take the minimum
└─ SECURITY AND CURRENCY DEFECT
    ├─ Template text alters policy or authority → HALT writes; revoke and rotate
    ├─ Writer cannot be authenticated → HALT namespace; rebuild from signed versions
    └─ Dependency invalidated but still selected → Invalidate dependents; retire overdue
```

### D. Performance Metrics and Continuous Learning

**Reuse and Coverage Metrics**:

- **Template hit rate**: Eligible runs with a selected template over all eligible runs, reported alongside candidate-found rate and selection-after-retrieval rate so that access failures are never confused with fit failures (target: reported, never optimised on its own).
- **Zero-use share**: Active versions with 0 retrievals in the window (target: no more than 20 percent; above that the abstraction policy is too specific).
- **Top-template traffic share**: Selections held by the single most-selected version (target: no more than 40 percent; above that indicates selector collapse or an over-general template).
- **Family coverage**: Task families with at least 1 active template earning positive paired gain (target: reported per window with its denominator).

**Outcome and Harm Metrics**:

- **Attributable gain**: Mean paired score difference between the selected-template condition and a no-template condition on the same examples under fixed evidence, model, budget, and verifier, reported with win-loss-tie counts and a bootstrap interval (target: interval strictly above 0 for every active version).
- **Near-miss harm rate**: Runs where the baseline passed and the selected-template result failed for a retrieval, fit, binding, or template defect, over selected-template runs whose baseline passed (target: at or below the class ceiling, 5 percent for the moderate class).
- **False-abstention rate**: Runs abstaining from retrieval where a later audit finds a template that would have helped (target: no more than 15 percent; a rate of 0 percent indicates thresholds that are not binding).
- **Fallback recovery rate**: Fallback runs reaching a verified answer (target: at least 80 percent; below that the fallback routes are misassigned to failure types).

**Library Health and Efficiency Metrics**:

- **Duplication rate**: Proposals rejected or merged as text, embedding, or structural duplicates over proposals reviewed (target: no more than 30 percent).
- **Promotion yield**: Candidates promoted over candidates proposed, with time to decision (target: reported; a yield above 50 percent indicates a gate that is not binding).
- **Staleness age**: Evaluation time minus the latest of creation, substantive validation, or dependency review, reported as median, tail, overdue-review share, and outcome lift by age band (target: overdue-review share no more than 10 percent).
- **Cost per incremental verified success**: Total pipeline cost over verified successes attributable to template assistance, reported against direct, reasoning-model, few-shot, and retrieval baselines at matched quality (target: below the cheapest baseline at matched quality).
- **Seed variance**: Mean, standard deviation, worst result, best-minus-worst range, per-example answer flips, selected-template agreement, and distillation-signature stability across preregistered repeated runs (target: reported behind every success figure).

**Learning and Adaptation Mechanisms**:

- **Held-out threshold calibration**: Recompute every retrieval threshold, margin, and abstraction bound per family against held-out outcomes each review window; the values in this guide are deployment defaults, not constants, and a published similarity range is never adopted as universal.
- **Separate evaluation of novel work**: Evaluate held-out novel and creative problems separately from recurring ones, since a library that improves familiar classes while degrading novel work is not generally better and the aggregate figure hides the trade.
- **Reuse-conditioned confidence**: Feed each audit window's calibrated accuracy back into the confidence ceiling, so that a family producing wrong templates automatically emits less confident ones.
- **Native capability re-measurement**: Re-run the paired gain measurement after every model upgrade, since a stronger model can make an external template redundant or can be constrained by it into a worse trajectory; tune native reasoning budget and template assistance as separate experimental axes rather than stacking both by default [13][14][15].

**Human-in-the-Loop Boundaries**: Promotion in the high-consequence and regulated classes, expansion of a canary beyond 10 percent of traffic, deferral of a revocation triggered by a wrong-at-origin finding, modification of a calibrated threshold or an abstraction policy, and admission of a template crossing a tenant boundary are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how a reusable procedure is admitted, retrieved, fitted, and retired, not what any particular procedure contains. Its phases hold wherever a task family recurs with stable structure, produces independently verifiable outcomes, and carries enough volume to amortise curation.

### 4.1 Cross-Domain Application Patterns

**Software engineering and platform operations**: Incident triage, dependency upgrade, and schema migration recur with stable structure and admit deterministic verification through tests and static analysis, which makes origin verification cheap and the promotion gate easy to satisfy honestly. Templates encode ordered diagnostic operations and their preconditions rather than service names, and the origin-literal scan is what keeps a service name out of an operation. Near-miss harm concentrates where a template written for one runtime is selected for another, so runtime compatibility belongs in the precondition set rather than in the description.

**Regulated financial operations**: Sanctions screening, transaction review, and disclosure preparation carry jurisdiction and effective date as load-bearing fields, so both must appear in the structural signature and in every precondition set. Staleness dominates the failure profile because a regulation change invalidates a procedure without changing any observable retrieval signal, which makes the dependency invalidation in Step 6.3 the primary control. The promotion class is regulated, so the gate requires 10 verified reuse cases across 5 distinct families, a named human role, and a recorded review.

**Clinical and laboratory analysis**: Specimen workup, protocol deviation assessment, and calibration review recur strongly, but the consequence class is high and independent verification is expensive, which raises the promotion bar rather than lowering it. Templates must never carry a diagnosis or a patient-specific quantity, so the residual-literal record in Step 5.1 is the privacy control as well as the abstraction control. Where no verifier independent of the template exists, the Buffer-Need Gate suppresses the method rather than releasing an unverifiable assisted answer.

**Customer support and service operations**: Volume is high and individual consequence is low, which makes this the setting where reuse pays most readily and where library bloat appears fastest. The dominant risk is over-generality: a template broad enough to match most tickets is selected constantly and improves nothing, so top-template traffic share and paired gain are the measures that matter and hit rate alone is actively misleading here.

**Legal and contractual review**: Clause comparison and obligation extraction recur across matters while carrying jurisdiction, effective date, and governing-law preconditions that a semantic match will not respect. Templates retrieve procedure while the governing text is retrieved separately as evidence, and the two channels remain distinct: a template is never cited as authority for a factual or legal claim.

**Scientific synthesis and research analysis**: Method appraisal and result reconciliation admit templates encoding an appraisal sequence, but the genuinely novel portion of the work does not, and the original method's own reported limitation is that gains are limited where problems do not rely on a specific template [1]. The response is a per-family gate rather than a per-domain one: the appraisal sequence is templated and the novel synthesis is not.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-volume distributions**: Where a family holds fewer than 30 prior verified runs, suppress the method entirely. Curation cost is fixed per template and the amortisation base is the family's recurrence; below that floor the library costs more to maintain than the reuse returns, and the correct configuration is no library at all.
- **High-volume, low-consequence work**: Retain every phase but reduce the promotion class to its low-consequence thresholds, run canaries at the full 10 percent allowance, and prioritise retirement over promotion, since at volume the dominant cost is a bloated index rather than a missing template.
- **High-risk or irreversible work**: Raise the fit floor and margin per the risk table in Step 3.3, require an independent verifier as a precondition of selection rather than only of release, and prefer abstention over an assisted answer whose verification is inconclusive. Safety-critical one-off decisions are suppressed at the gate and never templated.
- **Strict latency budgets**: Shorten the candidate cap and the reranked set rather than removing the fit check, since removing the fit check removes the only defence against negative transfer while shortening the candidate list merely reduces recall. Where latency forbids retrieval entirely, the gate suppresses the method and the declared fallback runs as the primary route.
- **Multi-tenant deployments**: Separate personal, team, organisation, and public namespaces, run authorization filters before semantic search in every case, propagate the strictest source permission to every derived embedding, and propagate deletion through episodes, templates, embeddings, caches, traces, and backups. Cross-user service requires an explicit scope and a stated legal basis, and abstraction does not by itself remove identifying content [12].
- **Model upgrades**: Treat every model change as a dependency change. Re-run paired gain measurement for each family before permitting continued selection, since a template calibrated against a weaker model can constrain a stronger one into a worse trajectory, and the weaker model that initialised the library may have produced poor templates in the first place [1].

***

## V. Limitations and Considerations

**Abstraction level cannot be verified before reuse**: The correct level for a template is a property of the problem distribution, and no check applied at write time establishes it. The consequence is that every newly promoted template is a hypothesis about generalisation that the library has not yet tested, and a mis-pitched template consumes retrieval budget or misdirects reasoning until enough reuse accumulates to detect it. The mitigation is the canary stage in Step 5.3, which limits exposure to 10 percent of eligible traffic while paired evidence accumulates, together with the two-directional detection rules in Step 6.1 that retire on counted outcomes rather than on review opinion.

**Template error propagation is contained, not eliminated**: The provenance, confidence-propagation, and promotion-gate machinery reduces the rate at which unsupported templates become retrievable, but none of it detects a template whose origin solution was verified and wrong in a way the verifier could not see, nor one correct for a reason its operations do not encode. Such a template will be well-provenanced, correctly ceilinged, and repeatedly retrieved. The mitigation is the post-promotion audit in Step 6.3, which adjudicates against origin sources rather than against the template's own outputs, and the revocation cascade with run replay; both detect the failure after promotion rather than preventing it, which is why every template version must remain revocable and every affected run replayable at all times.

**Similarity is an actively misleading selection signal**: Higher semantic similarity does not imply higher applicability, and one published analysis of similarity-based demonstration selection found it left more initially wrong cases unresolved than random selection [7]. The consequence is that a near-miss template anchors reasoning more strongly than no template, converting a recoverable absence into a misdirection. The mitigation is the deterministic precondition and prohibited-condition gates that no embedding score may override, the required margin over the next incompatible candidate, and the forced-fit prohibition in Step 3.1 that discards rather than adapts.

**The originating evidence base is narrow and not independently replicated**: The reported gains of 11 percent on Game of 24, 20 percent on Geometric Shapes, and 51 percent on Checkmate-in-One are relative improvements over the strongest comparator reported for each task, not percentage-point gains; the underlying scores were 82.4 against 74.0, 93.6 against 78.2, and 86.4 against 57.2 [1]. The 12 percent figure is average cost relative to the multi-query methods tested, not a universal ratio, and the public repository provides a math pipeline and demos for only three benchmarks [3]. The consequence is that a deployment reasoning from these headlines overstates benefit and understates cost. The mitigation is local calibration of every threshold against held-out outcomes, and the requirement in Section III.D to report current absolute costs and matched-quality frontiers rather than reproduce a published ratio.

**Every numeric bound here is a deployment default**: The candidate caps, repair limits, fit floors, margins, promotion counts, harm ceilings, and retirement windows were chosen to be operable on first deployment, not derived from a measured property of template reuse. The consequence is that a deployment treating them as constants mis-gates its own distribution in one direction or the other. The mitigation is the calibration requirement in Section III.D, obliging each deployment to recompute every bound per family each review window and to record the calibration date alongside each threshold in use.

**Reasoning models can make an external library redundant or harmful**: A capable model may already solve a family natively, and a stored strategy can constrain it into a worse trajectory than it would have chosen unaided. The consequence is a library that measures well against a weak baseline and negatively against the current model. The mitigation is the mandatory verified baseline in Step 1.3, which includes a direct reasoning-model call where one is available, and the requirement to re-run paired gain measurement after every model upgrade before selection resumes [13][14][15].

**A shared library is security-critical memory**: Templates are retrieved into a reasoning context and can carry injected instructions. Published results report attack success above 80 percent from poisoning less than 0.1 percent of a memory or retrieval store with under 1 percent impact on benign performance, 90 percent target success from injecting five malicious texts per target question into stores of millions, and influence achievable without direct database access [10][11][16]. The consequence is that an unguarded write path converts the library into an amplifier for an attacker. The mitigation is treating template text as delimited data, signing versions, authenticating and rate-limiting writers, scanning before quarantine, brokering every tool call with least privilege, and the halt-and-revoke escalation in Error Type 5.

**Paired measurement is expensive and often skipped**: Attributable gain requires running both conditions on the same examples under fixed evidence, model, budget, and verifier, roughly doubling evaluation cost for the measured slice. The consequence is that deployments under schedule pressure substitute hit rate, which rises with library size regardless of benefit and is therefore the metric most likely to certify a failing library as healthy. The mitigation is Checkpoint 6, which freezes promotions where any hit-rate figure is presented without attributable gain for the same window.

**Structural conformance is not method soundness**: A run can satisfy every checkpoint here and still reuse a procedure that is well-provenanced and inappropriate for the objective it was asked to serve. The framework detects malformed reuse, not misdirected purpose. The mitigation is the human-in-the-loop boundary in Section III.D and the audit in Step 6.3, neither of which substitutes for review of whether the family should be templated at all.

***

## VI. Conclusion and Summary

Buffer of Thoughts is a governance discipline before it is a reasoning technique. Every component the method needs is ordinary: a versioned store, three indexes, a model call to distil, a model call to judge fit, a model call to instantiate. What separates a library that improves outcomes from one that degrades them is entirely in the gates placed around those components: an abstraction policy stated numerically before the first template is written, a promotion gate that software closes on counted evidence, a fit check that discards rather than adapts, and a retirement rule that removes a version when it stops earning its retrieval.

The hazard that justifies the machinery is asymmetric in time. A wrong answer harms one run and ends. A wrong template, or one right for a reason its operations do not encode, is retrieved repeatedly and reproduces its defect in every problem it matches, with the damage growing after the error is committed and arriving under the authority of a validated library entry. Provenance preservation, confidence propagation, and a promotion gate holding publication authority in software are what keep that hazard bounded, and the post-promotion audit with its revocation cascade is what makes it recoverable when the gate is nonetheless passed by a defect no verifier could see.

A team introducing template reuse should instrument the baseline and the reuse ledger before building a library. Measure the family's recurrence and its verified baseline first, and suppress the method where fewer than 30 prior verified runs exist. Add distillation and retrieval next, with abstention wired and exercised. Add the promotion gate before the first template is written, never after, because retrofitting authority separation into a pipeline whose distiller already writes to the active store requires rebuilding it. Add curation, retirement, and rollback before the library exceeds the size at which a human can review it end to end.

**Key Success Factors**:

- **Abstraction stated as policy, not as taste**: The distinct-problem count, origin-literal bound, constrained-operation count, and non-empty scope limits are declared numerically per family before any template is written, and both failure directions are measured separately.
- **Proposed by a model, admitted by a gate**: The component that distils a template holds no write access, sets no confidence, and casts no vote; publication is a deterministic operation conditioned on checks software evaluates.
- **Evidence before entry**: One correct answer is an episode, not a template; promotion requires verified origin, complete provenance, and demonstrated reuse across distinct problem families at the thresholds set by consequence class.
- **Confidence bounded by evidence**: A template never carries more confidence than its origin verification and independently verified reuse support, the ceiling is computed from counted evidence, and no derived record is certain.
- **Fit checked, mismatch discarded**: A poorly matching template is discarded rather than forced, because a near miss anchors reasoning more strongly than an empty result and converts a recoverable absence into a misdirection.
- **Reuse measured against outcomes**: Hit rate is never reported alone; every retrieval figure is paired with attributable gain, and a version that stops earning lift is retired on a counted rule rather than retained on reputation.

By following this guide, AI agents can operate a template library that grows in verified reuse value rather than in volume, abstains when no stored procedure fits, and reverses a template whose evidence proves wrong before the error reaches the problems it would otherwise have matched.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them, and were not independently re-verified during conversion except where an entry is marked verified. Two entries were retrieved and confirmed in the course of this conversion, and are marked accordingly; their transcription in the source was accurate.

**Corpus pointers**:

- `Production Guide to Buffer of Thoughts` — the originating prose guide from which this operational guide was derived. Source of the meta-buffer and thought-template concepts, the problem-distillation transformation, the hybrid retrieval and reranking mechanics, the abstention rule, the nine-step production workflow with its loop exits, the buffer lifecycle states, the write-path and namespace controls, the staleness and security material, the metric definitions, and the deployment acceptance checklist. Its external citations are transcribed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — the normative reference for the promotion machinery this guide adopts rather than re-derives. Source of the terms error laundering, provenance preservation, confidence propagation, and promotion gate, and of the authority-separation rule between the component that proposes a record and the component that publishes it. The boundary between that guide's scope and this one is stated in Section 1.3.
- `advanced_task_guides/reasoning/guide_AnalogicalReasoning.md` — companion guidance on source-to-target mapping and negative transfer, applicable to the structural correspondence adjudication in Step 3.2 and the near-miss diagnosis it produces.
- `advanced_task_guides/reasoning/guide_StepBackPrompting.md` — companion guidance on abstraction and query normalisation, applicable to the problem distillation in Step 2.1.
- `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` — companion guidance on sequential execution, applicable to the template-free fallback route in Step 4.3.
- `advanced_task_guides/reasoning/guide_LeastToMostReasoning.md` — companion guidance on decomposition, applicable to the fallback route selected where distillation dropped a decisive constraint.
- `advanced_task_guides/reasoning/guide_TreeOfThought.md`, `advanced_task_guides/reasoning/guide_GraphOfThought.md`, and `advanced_task_guides/reasoning/guide_ForestOfThought.md` — companion guidance on explicit search, applicable to the fallback route selected where a template constrained the trajectory prematurely, and to the boundary in Section 1.2 between reusing a scaffold and exploring alternatives.
- `advanced_task_guides/reasoning/guide_ReflectiveMonteCarloTreeSearch.md` — companion guidance owning a scope-predicated lesson store. A lesson conditions proposal and evaluation inside one search, where a template here is a whole procedure promoted for cross-run use; its scope-matching, expiry, and negative-transfer controls apply wherever a lesson is a promotion candidate.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — companion guidance on evidence retrieval, applicable to the separation of the procedure channel from the evidence channel required in Step 4.1 and Section 4.1.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — companion guidance on query transformation and hybrid candidate generation, applicable to Step 2.2.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — companion guidance on removal and retention, applicable to the retirement, eviction, and deletion propagation in Step 6.2 and Section 4.2.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, III, IV, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*The originating method and its lineage*

1. Yang et al., *Buffer of Thoughts: Thought-Augmented Reasoning with Large Language Models* — https://arxiv.org/abs/2406.04271 (verified during conversion; NeurIPS 2024 Spotlight)
2. ReasonFlux — https://arxiv.org/abs/2502.06772
3. BoT repository — https://github.com/YangLing0818/buffer-of-thought-llm
4. Voyager — https://arxiv.org/abs/2305.16291
5. ExpeL — https://arxiv.org/abs/2308.10144
6. Agent Workflow Memory — https://arxiv.org/abs/2409.07429

*Retrieval, selection, and neighbouring prompting methods*

7. Auto-CoT — https://arxiv.org/abs/2210.03493
8. KATE — https://arxiv.org/abs/2101.06804
9. EPR — https://arxiv.org/abs/2112.08633

*Memory and retrieval store security and privacy*

10. PoisonedRAG — https://arxiv.org/abs/2402.07867
11. AgentPoison — https://arxiv.org/abs/2407.12784 (verified during conversion)
12. MEXTRA — https://arxiv.org/abs/2502.13172

*Reasoning models and native capability*

13. OpenAI reasoning guidance — https://developers.openai.com/api/docs/guides/reasoning-best-practices
14. DeepSeek-R1 — https://arxiv.org/abs/2501.12948
15. Anthropic extended thinking — https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

*Query-only memory manipulation, security controls, and provenance standards*

16. MINJA — https://arxiv.org/abs/2503.03704
17. OWASP, *RAG Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
18. OWASP, *LLM01 Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
19. OpenTelemetry GenAI semantic conventions — https://opentelemetry.io/docs/specs/semconv/gen-ai/
20. OpenTelemetry GenAI attributes — https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/registry/attributes/gen-ai.md
21. W3C PROV-O — https://www.w3.org/TR/prov-o/

*Case-based reasoning, memory typology, and adjacent retrieval and caching methods*

22. Aamodt and Plaza — https://www.iiia.csic.es/~enric/papers/Aamodt_1994_Case.pdf
23. LLM memory survey — https://arxiv.org/abs/2404.13501
24. RAG paper — https://arxiv.org/abs/2005.11401
25. Tree of Thoughts — https://arxiv.org/abs/2305.10601
26. Yasunaga et al. — https://arxiv.org/abs/2310.01714
27. Zheng et al. — https://arxiv.org/abs/2310.06117
28. OpenAI prompt caching — https://developers.openai.com/api/docs/guides/prompt-caching
29. GPTCache — https://github.com/zilliztech/GPTCache
