# Semantic Memory Networks

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Semantic memory constitutes the task family of maintaining a governed store of general facts and concepts, abstracted away from the particular episodes that produced them and organised as canonical entities joined by declared relation types. This guide provides AI agents with a structured protocol for operating that store: declaring an ontology and a relation registry against competency questions, extracting candidate assertions and admitting them only through a deterministic evidence gate, resolving surface forms to canonical identities reversibly, detecting and resolving contradictions through validity-interval arithmetic rather than overwrite, executing scope-constrained queries and bounded traversals, and maintaining the store against staleness, over-generalisation, and contradiction accumulation. It specifies an execution tier partition in which the model tier proposes assertions and the deterministic tier admits them, so that no assertion enters the store without provenance and a validity interval. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that a store of general facts remains attributable, point-in-time answerable, reversible, and erasable rather than accumulating plausible statements whose truth conditions nobody recorded.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Semantic memory**: The governed collection of assertions, concepts, identities, categories, and relations an agent can reuse independently of the particular episode in which each was learned. It answers what is believed to be true, about which entity, under which qualifying scope, during which interval, and on whose evidence.

**Assertion**: The atomic unit of the store: a typed proposition binding a canonical subject, a declared predicate, and a canonical object or typed literal, carrying a scope qualifier set, a validity interval, a provenance set, a confidence value with its method, and an immutable version identifier. An assertion is never edited in place; a correction produces a successor version.

**Semantic record**: An assertion together with every field required to evaluate it later. The distinguishing property against an episode is the truth form: an episode asserts that an occurrence took place at a time, and a semantic record asserts that a proposition holds across an interval.

**Relation type**: A registered predicate carrying a natural-language definition, a domain class, a range class or literal datatype, direction, cardinality expectation, temporal behaviour, functionality, identity implication, an evidence class, and a version. Only registered relation types may appear in an admitted assertion.

**Scope qualifier**: A declared dimension that narrows the context in which an assertion holds, such as tenant, jurisdiction, product version, environment, population segment, or unit system. A scope dimension declared on a relation type is either bound to a value or explicitly marked unbound with a recorded justification; it is never silently absent.

**Validity interval**: The half-open pair `valid_from` and `valid_to` stating when the proposition holds in the represented world, at a recorded precision that never exceeds the precision of the supporting evidence. An open `valid_to` is permitted only alongside a populated `next_verification_at`.

**Transaction interval**: The pair `transaction_from` and `transaction_to` stating when the store treated a given assertion version as current. Validity and transaction intervals together permit a late correction to change present belief without rewriting what was believed yesterday.

**Provenance set**: The ordered references linking an assertion to the evidence establishing it: source identifiers, source versions, evidence spans or record keys, supporting episode identifiers, and the provenance family each belongs to. An assertion with an empty provenance set is inadmissible.

**Provenance family**: The equivalence class of evidence sharing an upstream origin, such as one document, one crawl, one reporter, or one syndication chain. Support counts are computed over families, not over raw items, because repeated copies of one origin are not independent corroboration.

**Evidence class**: The admission regime a relation type declares, governing how much evidence an assertion of that type requires. Three classes are used: authoritative, observational, and inferred.

**Canonical entity**: A stable, opaque identifier with a mutable human label, an entity class, declared identity criteria, and a set of scoped source mappings. Canonical identity is never an embedding vector, never a display name, and never a mutable classification.

**Entity resolution**: The staged procedure of blocking, pair scoring, threshold decision, and clustering that binds surface mentions and source records to canonical entities. Its decisions are recorded as reversible operations, never as destructive rewrites.

**Contradiction**: A relation between two admitted assertions that cannot both hold, established mechanically on typed fields by predicate functionality, value incompatibility, and validity-interval overlap, or established semantically by adjudication where the conflict is not expressible on typed fields.

**Supersession**: The resolution in which a later assertion closes the validity interval of an earlier one rather than deleting it, producing a successor version and a recorded supersession link.

**Over-generalisation**: The defect in which an assertion true only under a particular value of a scope dimension is stored with that dimension unbound, and is then retrieved in a context where it is false.

**Staleness**: The condition of an assertion that was true when admitted, has passed its declared reverification horizon, and has not been reverified. Staleness is a property of the record's age against its volatility class, not of its confidence value.

**Graph generation**: An immutable, versioned publication of the store together with every derivative built from it: lexical indexes, dense indexes, materialised inferences, and community summaries. Serving switches between generations by atomic alias change.

**Competency question**: A question the store must answer, stated with the entities, relation types, temporal interpretation, expected evidence, allowable uncertainty, access scope, and latency budget it requires. A class or relation serving no competency question, validation rule, access rule, or migration need is deferred rather than declared.

### 1.2 The Boundary Against Episodic Memory and the Consolidation Pipeline

Semantic memory sits inside a family of memory systems that already have operational guides in this corpus. Its boundaries must be stated sharply, because the commonest defect in a deployed store is a record that belongs to a neighbour and was filed here.

**Against episodic memory**: An episode is a situated record asserting that an occurrence took place, carrying actors, actions, observations, order, outcome, and source trace. A semantic record asserts that a proposition holds, carrying a scope qualifier set and a validity interval. The test is the truth form. A record stating that a principal selected one option on a named date is an episode, and it remains one however often it recurs. A record stating that the principal prefers that option, within the procurement context, from that date onward, is a semantic record, and it requires evidence that no single occurrence supplies. Capture, segmentation, indexing, and retention of episodes are governed by `guide_EpisodicMemory.md` and are not restated here. Episodes are not superseded by the assertions derived from them; they remain as the evidence a later dispute is settled against.

**Against the consolidation pipeline**: The procedure that groups episodes, deduplicates them, detects contradictions among them, generates an abstracted candidate, and gates its promotion is governed by `guide_MemoryConsolidation.md`. That pipeline terminates in a promoted candidate with lineage. This guide begins where that candidate arrives. The two gates are distinct: consolidation asks whether a candidate is a faithful abstraction of its supporting episodes, and this guide asks whether the candidate is admissible as a general fact into a typed store that already holds other facts. A candidate can pass the first and fail the second, because the second additionally requires a registered relation type, resolved canonical endpoints, a computable validity interval, bound scope qualifiers, and no unresolved contradiction against the existing store.

**Sources other than episodes**: A semantic store also admits assertions that never passed through an episode, including registry records, structured feeds, contract terms, and document extractions. Consolidation does not cover these. The admission gate in Phase 2 applies uniformly to both origins, which is why it is specified here rather than delegated.

**The abstraction path, stated once**: An occurrence is recorded as an episode under the episodic guide. Consolidation groups episodes sharing an entity, a predicate, and a validity period, collapses duplicates, resolves contradictions within the group, and emits a candidate with its supporting set and its lineage. This guide's admission gate then binds the candidate to a registered relation type, resolves subject and object to canonical entities, computes the validity interval from the supporting evidence rather than from the promotion timestamp, binds every scope dimension the relation type declares, evaluates the evidence against the relation type's evidence class, and either writes an immutable assertion version or rejects with a reason code. Nothing crosses this boundary implicitly, and no assertion enters the store without provenance and a validity interval.

**Against working, procedural, and parametric memory**: Working memory holds bounded state for the current control loop and never becomes a durable assertion without a separate write decision. Procedural memory holds reviewed, versioned ways of acting; a semantic relation such as an accepted-format assertion may be a precondition of a procedure, but an executable workflow needs ordered actions, authorisation, validators, and failure branches that no assertion carries. Parametric promotion, moving a stable regularity into model weights, is not an agent-layer operation and sits outside this guide's scope. Where a deployment elects it, the agent layer's role is limited to producing the approved external assertion set, its lineage, and its retirement plan; volatile facts, personal profiles, disputed assertions, credentials, prices, inventories, and deletion-sensitive knowledge are never candidates for it, because a fact inside weights cannot be cited, corrected by supersession, or erased on request.

**The three failure modes carried as first-class procedure**: Over-generalisation, staleness, and contradiction accumulation are not incidental risks. Each receives a detection method with a numeric trigger and a remedy in Phase 6, and each is carried into the error taxonomy in Section III.C. A store lacking all three controls reads as correct at admission and degrades silently, because every one of these defects is invisible to a spot check of an individual record and visible only against scope, against time, and against the rest of the store.

### 1.3 Execution Tier Partition and Authority Rules

The method executes across three tiers, and the partition is binding on every phase in Section II. Work requiring exactness, reproducibility, auditability, or scale belongs to the deterministic tier, because model inference supplies none of those properties. Work requiring open-vocabulary judgement over natural language belongs to the model tier, because no deterministic rule covers it. Work where one tier proposes and the other verifies belongs to the hybrid tier, and every hybrid assignment names which component holds authority on disagreement.

**The governing rule, stated once**: the model tier proposes an assertion and the deterministic tier admits it. The proposing component holds no write access to the published store, no ability to set an assertion's final confidence, no authority to bind or unbind a scope dimension, and no vote in the admission decision. Admission is a deterministic operation conditioned on checks that software evaluates against the relation registry, the provenance set, and the existing store.

**Deterministic tier**: Software, schema validators, queries, and lifecycle jobs own schema and relation-type enforcement, scope-dimension binding checks, validity-interval arithmetic and precision rules, transaction-interval maintenance, contradiction detection between typed assertions, support counting over provenance families, threshold comparison at every gate, canonical identifier minting, merge and split execution with derivative invalidation, graph traversal under budget, query execution and result capping, staleness computation against volatility class, generation publication, and deletion propagation. This tier rejects, without consulting a model, any candidate carrying an unregistered predicate, an unresolved endpoint, an empty provenance set, an absent validity interval, an interval whose precision exceeds its evidence, an unbound scope dimension lacking a recorded justification, or a support count below the relation type's evidence class.

**Model tier**: LLM calls own entity and relation extraction from unstructured text, canonical-name resolution proposals where surface strings differ and no deterministic key matches, contradiction adjudication where the conflict is semantic rather than mechanical, scope-qualifier proposal where the qualifying context is stated only in prose, query intent classification and rewriting, path relevance judgement within an already-eligible candidate set, and explanation drafting from a computed justification. The model tier is never permitted to decide alone whether an assertion is admitted, what an assertion's validity interval is, whether a merge executes, whether a contradiction is resolved, whether an eligibility predicate is waived, or whether an assertion is deleted.

**Hybrid tier**: The model proposes and software verifies, or software retrieves and the model adjudicates. Extraction, entity resolution, contradiction resolution, retrieval ranking, and over-generalisation review all sit here.

**Execution Tier Assignment and Authority**

| Work unit | Owning tier | Authority when tiers disagree |
| :-- | :-- | :-- |
| Relation-type registration and versioning | Deterministic | Deterministic; the registry is versioned configuration, never model output |
| Schema and shape validation of a candidate | Deterministic | Deterministic; an invalid candidate is rejected, never repaired by generation |
| Mention detection and relation extraction | Model | Model only; software rejects schema violations without repair |
| Evidence-span attachment | Hybrid | Deterministic; a span that does not resolve to a stored source voids the assertion |
| Scope-dimension binding | Hybrid | Model proposes a value; software rejects the candidate where a declared dimension is neither bound nor justified |
| Validity-interval computation | Deterministic | Deterministic; the interval is derived from evidence timestamps, never from a model estimate |
| Interval precision assignment | Deterministic | Deterministic; precision never exceeds the coarsest supporting source |
| Support counting over provenance families | Deterministic | Deterministic; a model may not assert independence |
| Evidence-gate decision | Deterministic | Deterministic; a failed gate rejects without a model being consulted |
| Blocking and candidate generation for resolution | Deterministic | Deterministic; blocking rules are versioned configuration |
| Canonical-name resolution where strings differ | Hybrid | Model proposes; software admits only above the calibrated auto-merge threshold |
| Merge and split execution | Deterministic | Deterministic; the model tier has no merge authority |
| Contradiction detection on typed fields | Deterministic | Deterministic; predicate functionality and interval overlap are computed, not judged |
| Contradiction detection in free-text assertions | Hybrid | Model proposes pairs; software confirms both members exist and are active |
| Contradiction adjudication | Model | Model proposes a verdict; software enforces the resolution rule and the halt condition regardless of the verdict |
| Supersession and interval closure | Deterministic | Deterministic; an assertion is never overwritten on a model's recommendation |
| Confidence proposal | Model | Model proposes; software computes the ceiling and takes the minimum |
| Authorization and scope filtering before expansion | Deterministic | Deterministic; a model-proposed relaxation is a policy breach and halts the query |
| Graph traversal and budget enforcement | Deterministic | Deterministic; hop, node, edge, token, and wall-clock budgets are hard |
| Generated query admission | Hybrid | Model drafts; the parser allowlist, cost estimate, and read-only credential decide |
| Path relevance ranking | Model | Model ranks within the eligible set; deterministic completeness checks may remove an entry |
| Staleness computation and decay | Deterministic | Deterministic; retrieval frequency never extends a horizon |
| Over-generalisation audit | Hybrid | Software computes the scope-collapse statistic; a model or human adjudicates the flagged assertion |
| Pruning, migration, and generation publication | Deterministic | Deterministic; a model never decides that a rebuild is unnecessary |
| Deletion execution and verification | Deterministic | Deterministic; the model tier has no delete authority |

**The standing rule on disagreement**: Where the tiers disagree about whether the store already contains something, the deterministic tier holds authority, because it reads recorded state rather than generating it. Where they disagree about what a passage of text means, the model tier proposes and the deterministic tier decides whether the proposal is admissible against the registry, the evidence gate, and the contradiction check. No disagreement is resolved by re-prompting the model until it agrees, because a model consulted about whether its own output should be admitted reintroduces exactly the self-approval the partition exists to prevent.

### 1.4 The Entry Gate: When a Semantic Store Is Warranted

A typed, versioned, bitemporal store is expensive to build and more expensive to maintain. Agents must run a cheap gate, bounded to 2 percent of the direct-execution budget, returning semantic-store, substitute, or none.

**Invocation conditions**: Open a semantic store where at least one of the following holds materially: relationship structure between entities determines the answer; shared identifiers must hold across sources or agents; a controlled vocabulary must be enforced; point-in-time truth must be answerable, meaning the store must be able to state what was believed to hold on a past date; multi-hop retrieval must be explainable by citing its intermediate steps; or facts must be reused by more than one agent without each re-deriving them. The strongest case combines several of these, because each alone is often served more cheaply by a simpler store.

**Suppression conditions**: Withhold the store where questions are direct passage lookups against already authoritative documents, where records have stable rows, constraints, and aggregations with few variable-length traversals, or where the complete bounded evidence fits in context and reuse is rare. Withhold it where the deployment cannot satisfy the maintenance obligations in Phase 6, because an unmaintained store of general facts is worse than no store: it answers confidently from records nobody reverified.

**Named substitutes**: Where the gate suppresses the store, name the substitute rather than proceeding without one. Lexical or dense passage retrieval suffices where evidence passages are already authoritative. Relational storage suffices where transactions, permissions, and aggregates dominate and traversal is shallow. Long-context reading suffices for one bounded corpus where order and wording outweigh indexing. An episodic store suffices where the requirement is to recall what happened rather than what is true.

**Representation Selection Under the Gate**

| Dominant requirement | Adequate representation | What the choice does not supply |
| :-- | :-- | :-- |
| Passage evidence already authoritative | Lexical or dense passage retrieval | No identity, no validity interval, no contradiction detection |
| Rows, constraints, aggregates, shallow joins | Relational store with typed claim tables | Traversal ergonomics beyond fixed join depth |
| Variable-length paths, neighbourhood expansion, edge properties | Labeled property graph | Formal semantics; relation meaning stays application-level |
| Cross-system machine-checkable meaning, federation, named graphs | Triple store with a formal ontology | Entity quality, truth maintenance, or fast arbitrary traversal |
| Large class hierarchy with classification value | Restricted ontology profile plus a rule engine | Expressivity beyond the chosen profile |
| Bounded corpus, rare reuse, wording matters | Long-context reading | Reuse across sessions; cost is paid per call |

**Numeric gate rules**: Open the store only where at least 1 invocation condition holds and at least 1 declared consumer will issue queries against it. Where fewer than 5 registered relation types are required and no competency question needs a traversal of 2 hops or more, suppress and record the estimate, because a store of that shape is a table. Where a measured baseline over the same frozen corpus shows the simplest adequate substitute within 3 percentage points of the graph configuration on answer quality at matched latency, suppress and record the comparison, because the graph is not earning its maintenance cost. Where the deployment cannot execute reversible merge, reversible supersession, and deletion propagation, suppress and record the missing capability.

**Least-powerful adequate representation**: Where the gate returns semantic-store, select the weakest representation that answers the declared competency questions. A glossary with stable identifiers, a relation registry, and structural validation answers many question sets at a fraction of the cost of a formal ontology. Formalising a distinction before anyone owns its definition locks ambiguity into code and creates migration work without improving answers. Escalate representation only when a competency question fails against the current one and the failure is recorded.

***

## II. Operational Framework: Governed Assertion of General Facts Under Scope and Validity Constraints

The framework assumes the entry gate has returned semantic-store. Phases 1 through 3 establish the store and admit assertions into it. Phase 4 keeps the admitted set internally consistent. Phase 5 serves queries against it. Phase 6 runs on a schedule and returns control to Phase 2 or Phase 4 whenever an audit trigger fires.

### Phase 1: Ontology and Relation-Type Declaration

**Objective**: Fix the classes, relation types, scope dimensions, and evidence classes the store will enforce, so that admission is a mechanical check against a registry rather than a judgement made per assertion.

#### Step 1.1: Derive Competency Questions and the Query Contract

**Required Actions**:

- Enumerate the questions the store must answer and the decisions each supports, drawn from declared consumers rather than from the source material's vocabulary.
- State for each question the entities, relation types, temporal interpretation, expected evidence, allowable uncertainty, access scope, and latency budget it requires.
- Mark each question as point-in-time or current-state, since a point-in-time question obliges the store to retain superseded assertion versions rather than only their successors.
- Record the maximum traversal depth each question needs, and reject any question whose depth exceeds 4 hops without a decomposition into staged retrievals.
- Freeze the question set as a versioned regression suite before any class or relation is declared.

**Required Outputs**:

- A competency question set of at least 8 entries, each carrying entities, relation types, temporal interpretation, evidence expectation, access scope, latency budget, and maximum depth.
- A partition of the set into point-in-time and current-state questions.
- A versioned competency regression suite with expected answers for a labelled corpus.

**Quality Checkpoints**:

- Every question names at least 1 relation type and 1 entity class; a question naming neither is a passage lookup and is routed to the substitute named in Section 1.4.
- At least 1 question is point-in-time; where none is, bitemporal storage is not yet justified and the store is declared current-state only.
- No question requires a traversal deeper than 4 hops without a recorded decomposition.

***

#### Step 1.2: Declare Classes, Relation Types, and Scope Dimensions

**Required Actions**:

- Declare each class with explicit membership criteria and identity criteria, stating what makes two records the same entity and what change leaves identity intact.
- Declare each relation type with its natural-language definition, domain class, range class or literal datatype, direction, cardinality expectation, functionality, temporal behaviour, evidence class, and declared scope dimensions.
- Mark a relation type functional only where the world or an authoritative system guarantees at most one value per subject per interval, since functionality is what makes mechanical contradiction detection possible in Phase 4.
- Declare the scope dimensions each relation type carries, and mark each dimension mandatory or optional; a mandatory dimension left unbound at admission rejects the candidate.
- Assign each relation type a volatility class of volatile, semi-stable, stable, or immutable, with its reverification interval, and reject any relation type carrying no volatility class.
- Reject any proposed class, relation type, or scope dimension serving no competency question, validation rule, access rule, or migration need.

**Required Outputs**:

- A relation registry with every field populated per relation type, under a single registry version.
- A class inventory with membership and identity criteria per class.
- A scope dimension inventory with mandatory or optional status per relation type.
- A volatility class assignment with a reverification interval per relation type.

**Quality Checkpoints**:

- Every registered relation type carries a domain, a range, an evidence class, a volatility class, and at least 1 competency question that requires it.
- Every relation type used by a point-in-time question carries a temporal behaviour of interval-valued rather than instantaneous.
- No relation type is declared symmetric, transitive, or inverse of another without a stated logical justification, because a false declaration of any of the three propagates values across the store silently.
- Every mandatory scope dimension is enforced by a validator; a dimension declared but unenforced counts as undeclared.

***

#### Step 1.3: Select the Representation and Version the Schema

**Required Actions**:

- Select the least-powerful representation from the table in Section 1.4 that answers every competency question, and record the questions that would fail against the next weaker option.
- Pin the exact version of every specification the representation depends on, including graph data model, query language, and constraint language, since implementation conformance varies between versions and between products.
- Separate the schema artifacts and version them independently: the class and relation registry, the structural constraint set, the extraction output schema, and the query template set.
- Establish a migration contract requiring, for every registry release, example instances, negative examples, competency regression results, an inferred-delta estimate, an index rebuild plan, and a rollback plan.
- Publish the initial graph generation identifier and bind every derivative index to it.

**Required Outputs**:

- A representation decision record naming the selection, the rejected alternatives, and the failing questions that forced the selection.
- A pinned specification manifest naming every dependency and its exact version.
- Four independently versioned schema artifacts under one registry release identifier.
- A migration contract and an initial graph generation identifier.

**Quality Checkpoints**:

- The selected representation is the weakest option under which the competency regression suite passes; a stronger selection carries a recorded failing question.
- Every specification dependency carries an exact version; a floating version reference blocks the release.
- Every derivative index records the graph generation it was built from; an index with no generation binding is unpublishable.
- A rollback plan exists and has been executed once against a non-production generation before the first admission.

***

### Phase 2: Extraction and Admission Under the Evidence Gate

**Objective**: Convert candidate propositions from text, episodes, and structured feeds into admitted assertions, admitting none that lacks a registered relation type, resolved endpoints, provenance, a validity interval, and evidence meeting its declared class.

#### Step 2.1: Extract Candidates in Typed Stages

**Required Actions**:

- Preserve the immutable source reference, source version, character or token offsets, language, and retrieval authorisation before any extraction call is issued.
- Decompose extraction into separate stages rather than one call: mention detection, coreference, entity linking, relation extraction, temporal normalisation, scope-qualifier extraction, and modality and negation detection.
- Supply the extractor an allowlist of registered classes and relation types with definitions, domain and range, positive examples, counterexamples, allowed qualifiers, and an explicit unsupported outcome that the extractor is required to use rather than guess.
- Require each candidate to carry subject mention, predicate, object mention or literal, supporting span, modality, negation, temporal expression, source speaker, extraction confidence, and an assertion-type label of quoted, observed, source-asserted, or model-inferred.
- Validate in fixed order: output schema first, structural constraints second, registry conformance third, domain rules last, and reject at the first failure without repair.

**Candidate Record Template**:

```
CANDIDATE_ID:
SUBJECT_MENTION:        SUBJECT_CANDIDATE_IDS:
PREDICATE:              REGISTRY_VERSION:
OBJECT_MENTION_OR_LITERAL:   OBJECT_DATATYPE:
SCOPE_BINDINGS:         [dimension=value | dimension=UNBOUND(justification)]
TEMPORAL_EXPRESSION:    NORMALISED_INTERVAL:   INTERVAL_PRECISION:
MODALITY:               NEGATION:
ASSERTION_TYPE:         quoted | observed | source_asserted | model_inferred
EVIDENCE_SPANS:         SOURCE_ID:   SOURCE_VERSION:   PROVENANCE_FAMILY:
EXTRACTOR_CONFIDENCE:   EXTRACTOR_VERSION:   PROMPT_VERSION:
UNSUPPORTED_FLAG:
```

**Required Outputs**:

- A candidate set in the fixed record template, one record per proposed assertion.
- A rejection log naming each rejected candidate, the failing validation stage, and its reason code.
- A per-stage measurement record covering mention, linking, relation, temporal, and scope stages separately.

**Quality Checkpoints**:

- Every candidate carries at least 1 evidence span that resolves to a stored source version; a candidate whose span does not resolve is rejected, not repaired.
- No candidate carries an unregistered predicate; predicate coverage against the registry is 100 percent by construction of the allowlist.
- Stage-level measurements exist for every stage; a single end-to-end score is rejected because it makes the failing stage undiagnosable.
- Candidates flagged unsupported are counted and never silently dropped, since the unsupported rate is the extractor's calibration signal.

***

#### Step 2.2: Score the Evidence and Apply the Admission Gate

**Required Actions**:

- Assign each candidate the evidence class its relation type declares, and evaluate it against that class only.
- Count support over provenance families rather than over evidence items, so that repeated copies of one origin contribute 1 to the count.
- Compute a confidence ceiling deterministically from independent family count, source authority for the relation type, calibrated extractor accuracy for that relation type and source class, span entailment, and temporal parse confidence; take the minimum of the ceiling and any model-proposed value.
- Search the existing store for the same proposition, its negation, an incompatible value under a functional predicate, and an overlapping interval, and route any hit to Phase 4 before admission rather than after.
- Reject and record, without consulting a model, every candidate failing a hard check: unregistered predicate, unresolved endpoint, empty provenance set, absent validity interval, precision exceeding evidence, unbound mandatory scope dimension, or support below class.

**Evidence Classes and Admission Thresholds**

| Evidence class | Typical relation types | Minimum admission evidence | Confidence ceiling |
| :-- | :-- | :-- | :-- |
| Authoritative | Registry identifiers, completed transactions, contract terms, statutory status | 1 observation from a source holding declared authority for that relation type, with source version pinned | 0.98 |
| Observational | Dispositions, preferences, capabilities, associations, operational properties | 3 or more supporting items across 2 or more independent provenance families, spanning 2 or more distinct occasions, with 0 unresolved contradictions | 0.85 |
| Inferred | Rule-derived and ontology-derived assertions | Every premise already admitted and active, plus rule version and justification identifier | Minimum premise confidence minus 0.05 per derivation step |

**Required Outputs**:

- An admission decision per candidate carrying verdict, evidence class, independent family count, computed ceiling, final confidence, and reason code.
- A conflict referral list naming every candidate routed to Phase 4 and the assertions it conflicts with.
- A rejected-candidate ledger retained for calibration, with the source retained as retrievable text.

**Quality Checkpoints**:

- Every admitted assertion's final confidence is at or below its computed ceiling; a value above the ceiling is a gate defect and halts the batch.
- No observational assertion is admitted on evidence drawn from a single provenance family, regardless of how many items that family contains.
- Every rejection carries a reason code from a closed vocabulary; an uncoded rejection is unusable for calibration and blocks the run.
- Zero admitted assertions carry an empty provenance set or an absent validity interval, verified by query rather than by inspection.

***

#### Step 2.3: Commit the Assertion With Provenance and Validity Interval

**Required Actions**:

- Compute the validity interval from the supporting evidence, setting `valid_from` to the earliest evidence establishing the proposition and `valid_to` to the earliest evidence closing it, never to the promotion timestamp.
- Record interval precision at the coarsest precision any supporting source carries, and never manufacture a finer precision than the evidence supports.
- Set `next_verification_at` from the relation type's volatility class for every assertion whose `valid_to` is open, and reject the write where the field is null.
- Write the assertion as an immutable version carrying subject, predicate, object, scope bindings, both intervals, provenance set, confidence and its method, registry version, and graph generation, and publish derivative index entries in the same transaction or not at all.
- Emit an admission event carrying the candidate identifier, the decision, the evidence counts, and the resulting version identifier, so the whole path from source to assertion is replayable.

**Required Outputs**:

- Immutable assertion versions with both intervals, provenance, scope bindings, and confidence populated.
- A transactional publication record binding each assertion version to a graph generation and its derivative index entries.
- An append-only admission event stream sufficient to replay every write.

**Quality Checkpoints**:

- Zero assertions carry a `valid_from` equal to their `transaction_from` where the supporting evidence carries an earlier date; equality in that case indicates the promotion timestamp was used and halts the batch.
- Every open-ended assertion carries a populated `next_verification_at`; a null value rejects the write.
- Interval precision is never finer than the coarsest supporting source, verified by a comparison query over the batch.
- Derivative index entries and canonical writes share one transaction; a partial publication is rolled back rather than reconciled later.

***

### Phase 3: Entity Resolution and Canonicalization

**Objective**: Bind every surface mention and source record to a canonical entity through a staged, calibrated, and fully reversible procedure, so that identity errors are correctable rather than permanent.

#### Step 3.1: Generate Candidates by Blocking and Score With Interpretable Features

**Required Actions**:

- Mint stable, opaque canonical identifiers and keep human labels mutable; never encode a name, a mutable classification, or a tenant secret into an identifier, and never treat an embedding vector as identity.
- Preserve every source identifier in a scoped mapping carrying source system, namespace, validity interval, confidence, and evidence, so that a later split can restore the original binding.
- Generate candidate pairs by high-recall blocking on normalised authoritative identifiers, phonetic and lexical keys, geography, date ranges, and graph neighbourhoods, targeting blocking recall of at least 0.98 against an adjudicated pair set.
- Score each candidate pair on independently interpretable features: authoritative identifier agreement, name similarity, address or locator overlap, temporal compatibility, class compatibility, relational context overlap, and source reliability, recording each feature value with the decision.
- Route pairs where surface strings differ and no deterministic key matches to the model tier for a canonical-name resolution proposal, and carry that proposal as one scored feature rather than as a verdict.

**Required Outputs**:

- A canonical identifier per resolved entity with class, identity criteria version, and mutable label.
- A scoped source mapping set covering every source record contributing to the entity.
- A scored candidate pair set with per-feature values, blocking rule identifiers, and feature vector version.

**Quality Checkpoints**:

- Blocking recall against the adjudicated pair set is at least 0.98; below that, matching accuracy cannot be interpreted because true pairs never reached the scorer.
- Every scored pair records its feature values individually; a bare similarity score is rejected because it cannot be audited or recalibrated.
- No canonical identifier encodes a mutable attribute, verified by pattern check across the identifier space.
- A model-proposed name resolution never appears as the sole feature behind a merge decision.

***

#### Step 3.2: Decide Merge, Review, or Non-Match Against Calibrated Thresholds

**Required Actions**:

- Calibrate the score distribution on an adjudicated pair set stratified by entity class, source, popularity, and language, and set three thresholds producing auto-merge, human review, and non-match bands.
- Set the auto-merge threshold at the score above which the measured false-merge rate on the adjudicated set is at most 0.5 percent, and never lower it to raise graph connectivity.
- Require human approval, regardless of score, for any merge that would expose a restricted attribute across a boundary, authorise an action, cross a tenant boundary, or create more than 50 new inferred assertions.
- Evaluate cluster-level as well as pairwise error, since a single false bridge can collapse two large clusters that pairwise metrics score as one error.
- Use a strict identity relation only where substitution holds under every interpretation; prefer explicitly weaker mapping relations such as exact-match, close-match, possibly-same-as, and source-record-for wherever certainty or intended substitution is narrower.

**Required Outputs**:

- A threshold set with three bands, its calibration corpus reference, and its version.
- A resolution decision per pair carrying decision type, score, threshold version, feature values, and reason codes.
- A human review queue populated by the review band and by the mandatory-approval conditions.

**Quality Checkpoints**:

- Measured pairwise F1 on the held-out adjudicated set is at least 0.90 and cluster-level F1 at least 0.85; below either, resolution stays in review-only mode and no auto-merge executes.
- Measured false-merge rate at the auto-merge threshold is at most 0.5 percent, recomputed on every threshold change.
- No merge crossing a tenant boundary executes automatically under any score.
- The strict identity relation appears only where a recorded justification of full substitutability exists.

***

#### Step 3.3: Execute Reversible Merge and Split With Derivative Invalidation

**Required Actions**:

- Execute a merge as a new entity version or equivalence decision that retains both prior records, recording which attributes and edges were redirected, which remained source-scoped, and the exact inverse operation.
- Execute a split by restoring prior lineage, reassigning assertions and derivatives to the correct canonical entities, recomputing affected embeddings and materialised inferences, invalidating affected caches, and reopening every contradiction decision that depended on the merged identity.
- Cascade invalidation deterministically: every assertion, inference, index entry, summary, and cached answer referencing a changed canonical identifier is marked stale and rebuilt against the new generation before serving resumes.
- Record for every resolution operation a rollback operation identifier and verify the rollback executes on a non-production copy before the operation is applied in production for a high-impact entity.
- Inject known false bridges into the evaluation corpus on a recurring schedule and measure correction propagation lag from split execution to last derivative rebuilt.

**Required Outputs**:

- Reversible merge and split records with redirected and retained inventories and an inverse operation reference.
- An invalidation cascade record listing every dependent artifact and its rebuild status.
- A correction propagation measurement per injected false bridge.

**Quality Checkpoints**:

- Every merge and split carries an executable inverse; an operation without one is blocked before execution.
- Zero stale derivatives serve after a split completes, verified by querying the serving generation for references to retired identifiers.
- Correction propagation lag from split to last rebuilt derivative is at most 24 hours; a longer lag suspends auto-merge until the cascade is fixed.
- Every contradiction decision that depended on a reversed merge is reopened rather than left resolved.

***

### Phase 4: Contradiction Detection and Validity-Interval Resolution

**Objective**: Keep the admitted set internally consistent by detecting conflicting assertions mechanically, classifying each conflict before resolving it, and resolving through interval arithmetic and supersession rather than destructive overwrite.

#### Step 4.1: Detect Conflicts Deterministically on Typed Assertions

**Required Actions**:

- Run detection on every admission and on a scheduled sweep across the active set, since a conflict can arise between two assertions neither of which is new when a merge changes their subjects.
- Detect mechanically on typed fields: same subject, same functional predicate, incompatible object values, and overlapping validity intervals under compatible scope bindings.
- Compute value incompatibility per datatype using declared tolerance, so that numeric values within a declared tolerance and normalised string values are not reported as conflicts.
- Compute interval overlap explicitly rather than by timestamp comparison, and treat an open `valid_to` as extending to the query time rather than to infinity when evaluating overlap against a closed interval.
- Route to the model tier only the residue that typed detection cannot express, and require the model to return a pair of existing assertion identifiers that software then confirms are both present and active.

**Conflict Classification**

| Classification | Mechanical signature | Resolution owner |
| :-- | :-- | :-- |
| Duplicate | Same subject, predicate, object, scope, and interval | Deterministic; collapse and merge provenance sets |
| Corroboration | Same proposition from a distinct provenance family | Deterministic; increment independent support, do not create a version |
| Temporal succession | Same subject and functional predicate, different objects, adjacent or abutting intervals | Deterministic; close the earlier interval, link supersession |
| Scope difference | Same subject and predicate, different objects, different values on a declared scope dimension | Deterministic; retain both, bind the dimension on each |
| Resolvable contradiction | Overlapping intervals, incompatible values, one source holding declared authority | Deterministic; authority rule selects, loser is demoted with a link |
| Unresolved dispute | Overlapping intervals, incompatible values, no authority difference and no scope difference | Hybrid; model adjudicates, software enforces the halt rule |

**Required Outputs**:

- A contradiction case per detected conflict carrying case identifier, member assertion identifiers, conflict type, overlap interval, and detection method.
- A mechanically classified subset resolved without model involvement.
- A residual queue of cases requiring adjudication.

**Quality Checkpoints**:

- Detection runs on 100 percent of admissions and on a sweep at least every 24 hours; a store detecting only at write time misses conflicts created by merges.
- Every case records whether it was detected mechanically or proposed by a model, since the two carry different reliability and different audit obligations.
- No model-proposed conflict enters the queue without software confirming both members exist and are active.
- Numeric conflicts within declared tolerance are not raised; a tolerance-free comparison floods the queue and trains reviewers to dismiss cases.

***

#### Step 4.2: Adjudicate the Semantic Residue Under Explicit Outcomes

**Required Actions**:

- Present the adjudicator both assertions with their full provenance sets, scope bindings, intervals, confidences, and source authorities, and require a verdict drawn from a closed outcome vocabulary.
- Require the verdict to name one of: genuine contradiction, scope difference with the missing dimension named, temporal succession with the boundary date named, measurement difference within tolerance, or insufficient evidence to decide.
- Prohibit resolution by recency alone where the disagreement is not temporal, and prohibit resolution by count where an authoritative source is the governing rule for that relation type.
- Return a scope-difference verdict to Phase 2 as a re-scoping instruction rather than resolving it here, since the correct repair is to bind the missing dimension on both assertions.
- Escalate to a named human role every case where both assertions carry authoritative evidence class, where the case touches a restricted attribute, or where adjudication has already been reversed once.

**Required Outputs**:

- An adjudication record per case carrying verdict, named outcome, rationale code, evidence added, adjudicator identity, and timestamp.
- A re-scoping instruction set returned to Phase 2 for scope-difference verdicts.
- An escalation queue for cases meeting the mandatory human conditions.

**Quality Checkpoints**:

- Every verdict comes from the closed outcome vocabulary; a free-text verdict is rejected and the case is reopened.
- No case is resolved by recency where the conflict type is not temporal succession, verified by cross-checking rationale codes against conflict types.
- Adjudication reversal rate is at most 10 percent of resolved cases over any 30-day window; above that, the adjudication prompt and the authority rules are revised before further automated resolution.
- Cases with two authoritative sources reach a human in 100 percent of instances.

***

#### Step 4.3: Resolve Through Interval Arithmetic and Supersession

**Required Actions**:

- Resolve temporal succession by closing the earlier assertion's `valid_to` at the later assertion's `valid_from`, writing a successor version, and recording a supersession link in both directions.
- Resolve authority-governed contradictions by demoting the losing assertion to a non-serving status that retains it, its provenance, and the resolution rationale, never by deletion.
- Resolve scope differences by binding the discriminating dimension on both assertions and leaving both active, so that retrieval under a bound scope returns exactly one.
- Hold unresolved disputes in an explicit disputed status that suppresses both members from default retrieval and returns them together, with the dispute declared, when a query explicitly requests disputed content.
- Halt admission of new assertions on any relation type whose unresolved contradiction rate exceeds 3 percent of its active assertions, and hold the halt until the rate returns below 1 percent.

**Required Outputs**:

- Successor assertion versions with closed intervals and bidirectional supersession links.
- A demotion record per authority-resolved case naming the rule version that decided it.
- A disputed set with retrieval suppression applied and a declared release condition.
- A per-relation-type contradiction rate series with halt status.

**Quality Checkpoints**:

- Zero assertions are destructively overwritten; every correction produces a successor and retains its predecessor, verified by version-count query.
- Unresolved contradiction rate is at most 1 percent of active assertions per relation type in steady state; above 3 percent the admission halt is active and recorded.
- Time from case creation to resolution is at most 7 days at the 95th percentile; a longer tail moves the relation type to disputed-by-default.
- Every disputed assertion is suppressed from default retrieval, verified by querying the serving path rather than the canonical store.

***

### Phase 5: Query, Traversal, and Scope-Constrained Retrieval

**Objective**: Answer a question from the store with a bounded, attributable subgraph whose every member is eligible under the requesting scope and valid at the requested time, or abstain.

#### Step 5.1: Classify the Query and Bind Scope Before Expansion

**Required Actions**:

- Classify the query before retrieval into entity lookup, taxonomy navigation, relationship path, point-in-time state, comparison, thematic summary, contradiction review, or generated-query request, since each class carries a different budget and a different ranking rule.
- Resolve mentions to candidate canonical entities and carry ambiguity forward as a candidate set rather than collapsing it to a single best match.
- Bind the requested validity time explicitly, defaulting to the query timestamp, and record the bound value with the query so the answer is reproducible.
- Apply tenant, principal, purpose, region, sensitivity, consent, validity, dispute, and deletion filters before any expansion, never after ranking, so that an ineligible assertion is never scored, cached, or counted.
- Bind every scope dimension the query context supplies, and treat an assertion whose declared dimension is unbound as ineligible for a scope-bound query unless its unbound justification explicitly covers the requested value.

**Required Outputs**:

- A classified query record carrying class, resolved entity candidate set, bound validity time, and bound scope values.
- An eligibility-filtered candidate space with pre-filter and post-filter counts recorded.
- A budget assignment for the query class covering hops, nodes, edges, tokens, and wall-clock.

**Quality Checkpoints**:

- Eligibility filtering precedes expansion in 100 percent of queries, verified by comparing pre-filter and post-filter counts in the query log.
- Every query records its bound validity time; a query without one is not reproducible and is rejected.
- An assertion with an unbound mandatory scope dimension never satisfies a scope-bound query, verified by an adversarial query in the regression suite.
- Ambiguous mentions produce a candidate set, not a silent single binding; a collapsed set is reported as an ambiguity defect.

***

#### Step 5.2: Generate Candidates Across Routes and Bound the Traversal

**Required Actions**:

- Use complementary routes rather than one: keyed lookup for authoritative attributes, lexical search for exact names, codes, and rare identifiers, dense retrieval for paraphrased concepts, and graph traversal for typed neighbours, constrained paths, and justifications.
- Treat an embedding neighbour as a retrieval hint and never as a domain assertion; a dense neighbour edge is never written into the store as a relation.
- Enforce hard traversal budgets: 3 hops, 200 nodes, 500 edges, a declared context token budget, and 5 seconds of wall-clock at the 95th percentile, with the query truncated and marked partial rather than allowed to exceed them.
- Fuse only calibrated scores and retain each route's contribution, so a later audit can attribute a wrong answer to the route that produced it.
- Treat any generated query as untrusted: generate against a retrieved schema slice only, parse to a syntax tree, allowlist operations and predicates, estimate cost, execute under read-only least-privilege credentials with an enforced result cap and a 10-second timeout, and compare the returned types against the question.

**Required Outputs**:

- A per-route candidate set with route-attributed scores and generation identifiers for every index consulted.
- A traversal record naming hops taken, nodes and edges visited, and whether any budget bound truncated the search.
- A generated-query record carrying the syntax tree hash, allowlist verdict, cost estimate, and execution outcome.

**Quality Checkpoints**:

- Zero generated queries execute with write privileges, unbounded path patterns, or an absent result cap; any of the three is a security defect that halts the query path.
- Every candidate carries its originating route; an unattributed candidate is dropped before ranking.
- Budget truncation is reported to the caller as a partial result, never silently returned as complete.
- No dense-retrieval neighbour appears as an edge in the canonical store, verified by provenance-type query.

***

#### Step 5.3: Assemble an Attributable Subgraph or Abstain

**Required Actions**:

- Rank paths by relation relevance, endpoint match, validity at the bound time, source authority, premise confidence, path length, specificity, evidence independence, and dispute status.
- Penalise generic hub nodes, repeated aliases, duplicate provenance families, uncertain identity links, assertions past their reverification horizon, and paths crossing an unauthorised boundary.
- Select a coherent subgraph rather than isolated top-scoring assertions, including entity definitions, decisive assertions, scope qualifiers, supporting and conflicting evidence, and minimal justifications for any inferred member.
- Budget the assembled context in fixed order: authoritative evidence first, then contradictions and exceptions, then supporting neighbourhood, and truncate from the end rather than proportionally.
- Abstain and state what is missing where required evidence does not fit the budget, where every candidate is past its reverification horizon, or where the answer would rest on a disputed assertion; decompose and retrieve in stages before abstaining where the question permits it.

**Required Outputs**:

- A ranked, deduplicated subgraph with per-member citation identifiers and validity status.
- A justification set for every inferred member naming rule version, premises, and derivation depth.
- An abstention record naming the missing evidence where the query abstains.

**Quality Checkpoints**:

- Every returned assertion carries a citation resolving to its provenance set; an uncitable member is removed from the answer rather than returned unattributed.
- Every returned assertion is valid at the bound time; a member outside its interval is a retrieval defect and fails the query.
- Contradictions and exceptions relevant to the answer appear in the assembled context in 100 percent of cases where they exist, since suppressing them produces a confident wrong answer.
- Abstention is available and exercised; a store with a measured abstention rate of 0 percent over 1,000 queries is presumed to be answering from insufficient evidence.

***

### Phase 6: Maintenance, Staleness Audit, and Pruning

**Objective**: Detect and repair the three degradation modes that admission cannot catch, and keep the store, its derivatives, and its schema in a publishable and reversible state.

#### Step 6.1: Run the Staleness Audit and Reverification Schedule

**Required Actions**:

- Compute, on a schedule no less frequent than daily, the set of active assertions whose `next_verification_at` has passed, partitioned by relation type and volatility class.
- Attempt reverification against the original source class first and an equivalent-authority alternative second, recording the attempt, its outcome, and the new horizon whether or not it succeeded.
- Close the validity interval of any assertion whose reverification finds the proposition no longer holds, writing a successor rather than deleting, and record the closure date from the evidence rather than from the audit run.
- Demote retrieval eligibility, rather than confidence, for assertions past horizon and not reverified, since demoting confidence corrupts the calibration record while demoting eligibility only changes what is served.
- Prohibit retrieval frequency from extending a horizon; a frequently retrieved unreverified assertion is a higher risk than a rarely retrieved one, not a lower one.

**Required Outputs**:

- A staleness cohort report per relation type carrying past-horizon count, active count, and staleness ratio.
- A reverification outcome record per attempt carrying method, verdict, new horizon, and evidence reference.
- An eligibility demotion set with restoration conditions.

**Quality Checkpoints**:

- Staleness ratio, defined as past-horizon active assertions over active assertions, is at most 5 percent per relation type; above 10 percent the relation type is demoted to review-only retrieval until the sweep clears.
- Every assertion with an open `valid_to` carries a future `next_verification_at` after each audit run; a null or past value that survives an audit is an audit defect.
- Interval closures record an evidence-derived date, not the audit timestamp, verified by comparison query.
- Retrieval counts never appear as an input to horizon computation, verified by inspecting the decay policy version in force.

***

#### Step 6.2: Run the Over-Generalisation and Contradiction Audits

**Required Actions**:

- Compute the scope-collapse statistic for every active assertion with an unbound declared dimension: the fraction of its supporting evidence items sharing a single value on that dimension.
- Flag for review every assertion where the statistic is at or above 0.90 on any declared dimension while that dimension remains unbound, since the evidence supports the narrow proposition and the store holds the broad one.
- Repair a flagged assertion by binding the dimension to the observed value and writing a successor, not by deleting it, and route the broader proposition back to Phase 2 where broader evidence is expected to arrive.
- Sample admitted assertions on a recurring schedule, at a rate of at least 1 percent per relation type per 30 days, and adjudicate each against its cited evidence for both faithfulness and scope.
- Track the contradiction rate, the unresolved backlog age, and the adjudication reversal rate per relation type, and treat a rising backlog as an admission-rate problem rather than a reviewer-throughput problem.

**Required Outputs**:

- An over-generalisation flag set with the scope-collapse statistic and the implicated dimension per flagged assertion.
- A re-scoping successor set and a returned-candidate set routed to Phase 2.
- An audit sample record with per-assertion faithfulness and scope verdicts.
- A contradiction health series per relation type covering rate, backlog age, and reversal rate.

**Quality Checkpoints**:

- Over-generalisation rate, defined as flagged assertions over active assertions, is at most 2 percent per relation type; above 5 percent, admission for that relation type halts until the scope dimensions are made mandatory and the backlog is repaired.
- Every flagged assertion is repaired by binding and supersession, never by unqualified deletion, verified by successor-link presence.
- Audit sampling covers every relation type at the declared rate; an unsampled relation type is reported as unmeasured rather than assumed clean.
- Contradiction backlog age at the 95th percentile is at most 7 days, matching the Phase 4 resolution bound.

***

#### Step 6.3: Prune, Migrate, and Republish Generations

**Required Actions**:

- Run scheduled structural checks for orphan entities, unreachable evidence, duplicate entities, oversized identity components, constraint violations, degree outliers, broken provenance links, invalid intervals, and materialised inferences whose premises changed.
- Prune by separating canonical assertions from occurrences, evidence, aliases, and derived artifacts, archiving cold evidence only where it remains recoverable under the retention policy, and retaining enough lineage to reproduce authority and deletion dependencies.
- Treat every schema or registry change as a data migration: produce old-to-new mappings, rewrite rules, an unresolved-case queue, compatibility views, structural validation, an inferred-delta report, an index rebuild plan, and a rollback plan.
- Publish a new immutable graph generation, rebuild every lexical index, dense index, materialisation, and summary against it, validate counts and the competency regression suite, then switch serving aliases atomically; never mix index, schema, and entity mappings from different generations.
- Execute erasure by traversing from subjects and sources through mentions, entities where lawful, assertions, evidence, dense vectors, summaries, caches, evaluation fixtures, inferences, exports, and backups, issuing tombstones first and rebuilding derivatives after, and record every lawful exception applied.

**Required Outputs**:

- A structural health report with one row per check and a count.
- A migration record carrying mappings, delta counts, regression pass rate, rebuild identifiers, cutover time, and rollback deadline.
- A generation manifest binding canonical state to every derivative built from it.
- A deletion record per request with per-target status and verified purge times.

**Quality Checkpoints**:

- Competency regression pass rate against a new generation is at least 95 percent of the prior generation's; below that, the alias switch is blocked and the generation is discarded.
- Every derivative in the serving path names the same generation identifier; a mixed-generation serving path is a hard defect and triggers rollback.
- Tombstoned assertions stop serving within 60 seconds of tombstone issue, verified by querying the serving path rather than the canonical store.
- Verified purge across every derivative completes within the declared service level, and any target that cannot be purged is recorded with its residual risk rather than closed.

***

## III. Implementation Guidance for AI Agents

AI agents operating a semantic store must follow systematic protocols ensuring that every assertion is attributable, scoped, time-bounded, reversible, and erasable. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Registry Agent**: Owns the class inventory, relation registry, scope dimension declarations, volatility classes, and evidence classes. It alone may version the registry, and every version carries a migration contract. It never extracts, never admits, and never resolves.
2. **Extraction Agent**: Runs the typed extraction stages against an allowlist and emits candidate records in the fixed template. It holds no write access to the published store and cannot alter the registry, the thresholds, its own confidence calibration, or the allowlist it was given.
3. **Admission Agent**: Evaluates the evidence gate deterministically, counts support over provenance families, computes confidence ceilings, and writes immutable assertion versions with both intervals. It is the only component that may publish an assertion.
4. **Resolution Agent**: Executes blocking, pair scoring, threshold decisions, merges, splits, and invalidation cascades. It routes name-resolution proposals to the model tier and mandatory-approval merges to a human role.
5. **Consistency Agent**: Runs contradiction detection on admission and on sweep, classifies conflicts, routes the residue for adjudication, executes interval closure and supersession, and enforces the per-relation-type admission halt.
6. **Retrieval Agent**: Classifies queries, binds validity time and scope, enforces eligibility before expansion, executes bounded traversal, assembles the subgraph, and issues abstentions.
7. **Maintenance Agent**: Runs the staleness, over-generalisation, structural, and economic audits, executes pruning and migration, publishes generations, and performs deletion propagation with verification.

**Authority Rule**: The Extraction Agent and any model component proposing an assertion, a name resolution, or a contradiction verdict hold proposal authority only. The Admission Agent, the Resolution Agent, and the Consistency Agent hold decision authority and act on the registry, the thresholds, and the recorded state. No proposal is escalated by re-prompting.

**Workflow Execution Pattern**:

```
STATE: Phase_2_Admission_Gate
ACTIONS:
  1. Bind candidate to registry version and validate schema, shape, registry, domain rules
  2. Resolve subject and object to canonical entities or reject as unresolved
  3. Count independent provenance families and compute the confidence ceiling
  4. Compute validity interval and precision from supporting evidence
  5. Query existing store for duplicate, negation, functional conflict, interval overlap
VALIDATION:
  - registered_predicate == TRUE
  - endpoints_resolved == TRUE
  - provenance_family_count >= evidence_class_minimum
  - validity_interval_present == TRUE AND precision <= coarsest_source_precision
  - mandatory_scope_dimensions_bound_or_justified == TRUE
  - final_confidence <= computed_ceiling
TRANSITIONS:
  IF conflict_detected THEN next_state = Phase_4_Contradiction_Handling
  ELSE IF all_validations_pass THEN next_state = Phase_2_Commit
  ELSE next_state = Phase_2_Rejection_Ledger
```

**Two-Phase Write Pattern**:

1. **Propose**: The model tier emits candidate records under the fixed template with spans, scope proposals, and temporal expressions.
2. **Verify**: The deterministic tier resolves endpoints, counts families, computes intervals and ceilings, and checks the existing store, rejecting at the first hard failure without repair.
3. **Commit**: Canonical write and derivative publication occur in one transaction bound to a graph generation.

**Approval Gate**: A named human role must approve, before execution, any merge crossing a tenant boundary, any merge exposing a restricted attribute, any merge creating more than 50 new inferred assertions, any contradiction case where both members carry authoritative evidence class, any registry release changing a relation type's functionality or cardinality, and any deletion exception invoked against an erasure request. Below these triggers, execution proceeds automatically and is recorded.

**Context Management Requirements**:

- Hold the registry, thresholds, and generation manifest in durable state, since the store outlives any context window.
- Process admission in batches bound to a snapshot rather than streaming against a moving store, so that contradiction detection is evaluated against a fixed state.
- Write a handoff record at every context boundary naming the registry version, the generation, the pending queues, and the open audit triggers.
- Never load the store into context to answer a question; retrieve a bounded subgraph and cite it.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Registry Integrity (After Phase 1)**

- **Automated Check**: Every relation type carries domain, range, evidence class, volatility class, and at least 1 requiring competency question; every mandatory scope dimension has an enforcing validator; the competency suite is versioned and passes against a labelled corpus.
- **Agent Action on Pass**: Open admission against the registry version.
- **Agent Action on Failure**: Halt; no assertion is admitted against an incomplete registry.
- **Human Review Trigger**: Any relation type declared symmetric, transitive, or inverse, and any registry release changing functionality or cardinality.

**Checkpoint 2: Admission Integrity (After Phase 2)**

- **Automated Check**: 100 percent of admitted assertions carry a registered predicate, resolved endpoints, a non-empty provenance set, a validity interval within evidence precision, bound or justified mandatory scope dimensions, and a confidence at or below the computed ceiling.
- **Agent Action on Pass**: Publish the batch to the current generation.
- **Agent Action on Failure**: Roll back the batch and return the failing records with reason codes; a partially admitted batch is never published.
- **Human Review Trigger**: More than 20 percent of candidates in a batch rejected on the same reason code, indicating an extraction or registry defect rather than source noise.

**Checkpoint 3: Identity Integrity (After Phase 3)**

- **Automated Check**: Blocking recall at least 0.98; pairwise F1 at least 0.90; cluster F1 at least 0.85; measured false-merge rate at the auto-merge threshold at most 0.5 percent; every merge and split carries an executable inverse.
- **Agent Action on Pass**: Enable auto-merge within the calibrated band.
- **Agent Action on Failure**: Disable auto-merge and route the full band to review; resolution continues in review-only mode.
- **Human Review Trigger**: Any merge crossing a tenant boundary, exposing a restricted attribute, or creating more than 50 inferred assertions.

**Checkpoint 4: Consistency Integrity (After Phase 4)**

- **Automated Check**: Unresolved contradiction rate at most 1 percent per relation type; 95th-percentile resolution time at most 7 days; adjudication reversal rate at most 10 percent over 30 days; zero destructive overwrites.
- **Agent Action on Pass**: Continue admission at full rate.
- **Agent Action on Failure**: Halt admission for the affected relation type until the rate returns below 1 percent.
- **Human Review Trigger**: Any case where both members carry authoritative evidence class, and any case reversed more than once.

**Checkpoint 5: Retrieval Integrity (After Phase 5)**

- **Automated Check**: Eligibility filtering precedes expansion in 100 percent of queries; every returned assertion is valid at the bound time and carries a resolving citation; zero generated queries executed with write privileges or unbounded paths; budget truncation reported as partial.
- **Agent Action on Pass**: Release the answer with its citation set.
- **Agent Action on Failure**: Withhold the answer and return an abstention naming the failing check.
- **Human Review Trigger**: Any eligibility bypass, any cross-tenant path returned, and any answer resting on a disputed assertion.

**Checkpoint 6: Maintenance Integrity (After Phase 6)**

- **Automated Check**: Staleness ratio at most 5 percent per relation type; over-generalisation rate at most 2 percent per relation type; competency regression pass rate at least 95 percent of the prior generation; single generation identifier across the serving path.
- **Agent Action on Pass**: Switch serving aliases to the new generation.
- **Agent Action on Failure**: Block the alias switch, discard the candidate generation, and continue serving the prior one.
- **Human Review Trigger**: Staleness ratio above 10 percent, over-generalisation rate above 5 percent, or any purge target that cannot be verified.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
REGISTRY_VERSION:
GRAPH_GENERATION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Over-Generalisation**

- **Symptoms**: An assertion retrieved in one context is correct and in another is false; the scope-collapse statistic is at or above 0.90 on a declared dimension left unbound; a repair applied in one tenant, environment, or product version is applied everywhere; the same relation type generates repeated user corrections that each look like one-off errors.
- **Diagnostic Steps**: Compute the scope-collapse statistic per declared dimension for the implicated relation type; determine whether the supporting evidence spans more than 1 value on the dimension; check whether the dimension is declared optional when the world makes it mandatory.
- **Resolution Protocol**: Option A, bind the dimension to the observed value and write a successor, retaining the narrow assertion and returning the broad proposition to Phase 2. Option B, promote the dimension from optional to mandatory in the registry and re-audit every active assertion of that relation type. Option C, retire the relation type where no scoping makes it reliable, and retain the supporting evidence as retrievable text.
- **Escalation Trigger**: Over-generalisation rate above 5 percent for a relation type halts admission for that type; a rate above 5 percent recurring after one repair pass escalates to registry review, since the defect is in the declaration rather than in the records.

**Error Type 2: Stale Assertions Serving as Current**

- **Symptoms**: Answers cite assertions whose supporting evidence predates a known change; past-horizon assertions appear in served subgraphs; reverification attempts fail without changing eligibility; frequently retrieved records are the oldest in their cohort.
- **Diagnostic Steps**: Recompute the staleness ratio per relation type and volatility class; check whether `next_verification_at` is populated on every open-ended assertion; confirm no retrieval-frequency term entered the horizon computation.
- **Resolution Protocol**: Option A, run the reverification sweep and demote eligibility for every unreverified past-horizon assertion. Option B, shorten the volatility class interval for the relation type where the observed change rate exceeds the assumed one. Option C, convert the relation type to authoritative evidence class and source it from a system of record instead of extraction.
- **Escalation Trigger**: Staleness ratio above 10 percent demotes the relation type to review-only retrieval; a ratio above 10 percent surviving two sweeps escalates, because the failure is in the reverification path rather than in the schedule.

**Error Type 3: Contradiction Accumulation**

- **Symptoms**: The unresolved backlog grows across sweeps; mutually exclusive assertions are both served and retrieval returns whichever ranks higher; adjudication reversals rise; answers change between queries with no intervening write.
- **Diagnostic Steps**: Compute contradiction rate, backlog age, and reversal rate per relation type; determine whether the growth is in mechanical conflicts, indicating a functionality declaration problem, or in adjudicated residue, indicating an authority rule problem.
- **Resolution Protocol**: Option A, halt admission for the relation type and clear the backlog before resuming. Option B, declare the missing authority rule so that resolvable contradictions stop entering the adjudication queue. Option C, suppress both members from default retrieval under disputed status until resolved, so a wrong answer is replaced by a declared dispute.
- **Escalation Trigger**: Unresolved contradiction rate above 3 percent halts admission automatically; a backlog whose 95th-percentile age exceeds 14 days escalates to human review of the authority rules, and is never resolved by raising adjudication throughput alone.

**Error Type 4: Identity Contamination**

- **Symptoms**: One entity accumulates implausible degree or attribute breadth; two previously distinct clusters answer as one; a split leaves derivatives referencing retired identifiers; private attributes appear against the wrong subject.
- **Diagnostic Steps**: Inspect identity component size growth per sweep; trace the merge decisions that joined the component and their feature values; determine whether a strict identity relation was asserted where a weaker mapping was warranted.
- **Resolution Protocol**: Option A, split at the offending merge, restore lineage, and run the full invalidation cascade. Option B, replace the strict identity assertion with an explicitly weaker mapping relation and re-evaluate dependent inferences. Option C, raise the auto-merge threshold for the entity class and move the affected band to review.
- **Escalation Trigger**: Any contamination exposing a restricted attribute escalates immediately and suspends auto-merge for the entity class; this class is never resolved by re-running the matcher at the same threshold.

**Error Type 5: Untrusted Content Entering the Store**

- **Symptoms**: A new source rapidly dominates answers for a relation type; instruction-like content appears in evidence spans; a low-authority source asserts a relation type reserved for authoritative sources; a targeted set of queries degrades while aggregate quality holds.
- **Diagnostic Steps**: Measure per-source admission share and retrieval dominance over a rolling window; evaluate attack success separately on targeted and non-targeted queries, since aggregate monitoring conceals targeted manipulation; confirm the extraction component holds no registry, policy, or threshold write access.
- **Resolution Protocol**: Option A, quarantine the source, suspend its assertions from retrieval, and re-audit everything admitted from it. Option B, raise the evidence class for the affected relation type so a single source can no longer establish it. Option C, revoke the source's authority declaration and require independent corroboration for all its future candidates.
- **Escalation Trigger**: Any admitted assertion traced to content that attempted to alter policy, schema, or permissions escalates immediately as a security incident; retrieval-dominance by a single new provenance family above 30 percent for a relation type within 7 days triggers automatic quarantine.

**Error Type 6: Generated Query Executing Beyond Its Mandate**

- **Symptoms**: A generated query returns rows from outside the requesting scope; execution time or result size exceeds the class budget; a query parses cleanly but binds the wrong entity or omits the temporal filter; write operations appear in generated text.
- **Diagnostic Steps**: Compare the syntax tree against the allowlist and the schema slice supplied; check whether the temporal filter and scope predicates are present in the executed form; verify the credential in use is read-only and least-privilege.
- **Resolution Protocol**: Option A, reject the query and fall back to a reviewed query template for the question class. Option B, narrow the schema slice supplied to the generator so the wrong predicate is not nameable. Option C, replace generation for the class with an application interface exposing only parameterised operations.
- **Escalation Trigger**: Any generated query that executed with write privileges, crossed a tenant boundary, or ran without a result cap halts the generated-query path for the deployment pending review; this class is never resolved by regenerating the query.

**Troubleshooting Decision Tree**:

```
STORE RETURNS A WRONG OR UNATTRIBUTABLE ANSWER
├─ SCOPE DEFECT
│   ├─ Scope-collapse >= 0.90 on unbound dimension → Bind dimension; write successor
│   ├─ Dimension optional but world-mandatory → Promote in registry; re-audit relation type
│   └─ Rate above 5 percent after repair → HALT admission; escalate to registry review
├─ TIME DEFECT
│   ├─ Assertion past horizon and served → Demote eligibility; run reverification sweep
│   ├─ valid_from equals transaction_from with earlier evidence → Recompute interval from evidence
│   └─ Ratio above 10 percent after two sweeps → Escalate; reverification path is broken
├─ CONSISTENCY DEFECT
│   ├─ Both members served, higher rank wins → Apply disputed status; suppress both
│   ├─ Mechanical conflicts growing → Fix functionality declaration in registry
│   └─ Unresolved rate above 3 percent → HALT admission for the relation type
├─ IDENTITY DEFECT
│   ├─ Component growth implausible → Split at offending merge; run invalidation cascade
│   ├─ Strict identity asserted on partial match → Replace with weaker mapping relation
│   └─ Restricted attribute exposed → HALT auto-merge for class; escalate immediately
├─ PROVENANCE DEFECT
│   ├─ Citation does not resolve → Remove member from answer; quarantine assertion
│   └─ Support counted over items not families → Recount; re-evaluate against evidence class
└─ TRUST DEFECT
    ├─ New source dominance above 30 percent → Quarantine source; re-audit admissions
    ├─ Instruction-like content in evidence span → HALT batch; security incident
    └─ Generated query wrote or crossed tenant → HALT generated-query path; escalate
```

### D. Performance Metrics and Continuous Learning

**Store Quality Metrics**:

- **Admission precision**: Sampled admitted assertions judged faithful to their cited evidence and correctly scoped (target: at least 95 percent for authoritative relation types, at least 90 percent for observational).
- **Provenance completeness**: Admitted assertions whose every citation resolves to a stored source version (target: 100 percent; any shortfall is a defect, not a rate).
- **Over-generalisation rate**: Active assertions flagged by the scope-collapse audit over active assertions (target: at most 2 percent per relation type; above 5 percent halts admission).
- **Staleness ratio**: Past-horizon active assertions over active assertions (target: at most 5 percent per relation type; above 10 percent demotes to review-only).
- **Unresolved contradiction rate**: Open contradiction cases over active assertions (target: at most 1 percent per relation type; above 3 percent halts admission).

**Identity and Retrieval Metrics**:

- **Pairwise and cluster F1**: Resolution accuracy on the held-out adjudicated set (target: at least 0.90 pairwise, at least 0.85 cluster).
- **False-merge rate at threshold**: Incorrect auto-merges over auto-merges (target: at most 0.5 percent).
- **Multi-hop path recall**: Queries whose returned subgraph contains every assertion on the adjudicated answer path (target: at least 0.80 for questions of 2 hops or more).
- **Point-in-time accuracy**: Point-in-time questions answered with the assertion valid at the bound time (target: at least 0.95; this metric alone distinguishes a bitemporal store from a current-state one).
- **Attribution correctness**: Answers whose every claim is supported by a cited assertion valid at the bound time (target: at least 0.95).
- **Abstention precision**: Abstentions correct under later adjudication (target: at least 0.90).

**Efficiency and Economics Metrics**:

- **Cost per attributable answer**: Total store cost, including adjudication, migration, and deletion, over accepted attributable answers (target: below the strongest substitute baseline at matched quality).
- **Write amplification**: Bytes stored across canonical, evidence, alias, index, materialisation, and summary layers per admitted assertion (target: monitored per generation; a rise above 25 percent between generations triggers a pruning review).
- **Traversal budget breach rate**: Queries truncated by a budget bound (target: at most 5 percent; a higher rate indicates budgets set below the competency questions' needs).

**Learning and Adaptation Mechanisms**:

- **Calibration from the rejection ledger**: Recompute extractor precision and confidence calibration per relation type and source class from adjudicated admissions and rejections, and revise the extraction prompt or the evidence class rather than the threshold alone.
- **Registry evolution from audit evidence**: Where an over-generalisation audit repeatedly flags one dimension, promote that dimension to mandatory in the registry, since a recurring record-level defect is a declaration defect.
- **Volatility recalibration**: Recompute each relation type's volatility class from observed supersession intervals, and shorten the reverification horizon where the observed change rate exceeds the assumed one.
- **Threshold recalibration**: Recompute resolution and admission thresholds per entity class and relation type on every registry release; the values stated in this guide are deployment defaults, not constants.
- **Baseline re-measurement**: Re-run the substitute baselines named in Section 1.4 against the current frozen corpus at least every 180 days, since a store that has stopped outperforming its substitute should be retired rather than maintained.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how a general fact is admitted, scoped, timed, and retired rather than what any particular fact says. Its phases hold wherever entities recur across sources, relations between them carry decision weight, and propositions change on a timescale longer than one interaction.

### 4.1 Cross-Domain Application Patterns

**Regulated supply and procurement**: Relation types cover certification, approval, supersession of standards, and supplier relationships. Almost every relation type is authoritative evidence class, sourced from registries rather than extraction, which raises admission precision and shifts cost to integration. Point-in-time questions dominate, since the operative question is what held on an order date rather than what holds now, and the store must therefore retain superseded versions. Scope dimensions are jurisdiction and product family; over-generalisation across jurisdictions is the characteristic failure, and binding jurisdiction as a mandatory dimension is the characteristic repair.

**Clinical and life-science knowledge**: Relation types cover indication, contraindication, interaction, and mechanism. Evidence classes split sharply: regulatory status is authoritative and single-source, while a mechanistic association is observational and requires independent families. Validity intervals are long but not infinite, and the volatility class must reflect guideline revision cycles rather than publication dates. Identity contamination is the highest-severity error, because a false merge between two similarly named substances propagates into every dependent inference; auto-merge thresholds are set conservatively and human approval is mandatory for merges touching restricted attributes.

**Software and infrastructure operations**: Relation types cover dependency, compatibility, ownership, and deprecation. Volatility is high and horizons are short, often 7 days, so the staleness audit rather than the admission gate is the load-bearing control. Scope dimensions are environment and version; an assertion true of one release stored without its version binding is the canonical over-generalisation, and it manifests as a repair applied correctly in one environment and destructively in another. Traversal depth is genuinely needed here, since impact questions traverse dependency chains.

**Customer and account knowledge**: Relation types cover entitlement, preference, contact role, and account structure. Entitlements are authoritative and sourced from a system of record; preferences are observational and require repeated, independent support across occasions, which is exactly where a single episode most often becomes a false general fact. Deletion propagation is a compliance obligation rather than a hygiene task, and the store's design is constrained by it: every derivative must be rebuildable, and no assertion about a person may live anywhere that cannot be traversed from the subject.

**Public-sector and legal policy**: Relation types cover obligation, exemption, jurisdiction, and amendment. Bitemporal storage is not optional, because a question about a past obligation must be answerable as it stood, including where the store's own belief was later corrected. Authority rules are explicit and hierarchical, so most contradictions resolve deterministically; the residue reaching adjudication is small and consequential, and every case with two authoritative sources escalates to a human by design.

### 4.2 Scale, Risk, and Volatility Adaptation

- **Small stores under 10,000 assertions**: Retain the registry, the evidence gate, validity intervals, and the contradiction check; collapse resolution to deterministic key matching with a review queue, and run all three audits weekly rather than daily. The controls that may be dropped are the ones about scale, never the ones about truth.
- **Large stores above 10 million assertions**: Partition audits by relation type and run them continuously rather than as one sweep; sample rather than enumerate for the over-generalisation audit at a rate that yields at least 400 assertions per relation type per cycle; publish generations incrementally with per-partition alias switches.
- **High-volatility domains**: Shorten reverification horizons before loosening admission, since a store that admits readily and reverifies slowly is a store of confident stale facts. Where the observed change rate makes reverification impossible at cost, move the relation type to query-time lookup against the system of record and store only the identifier binding.
- **High-risk and irreversible decisions**: Raise the evidence class for every relation type feeding the decision, require at least 1 authoritative source per served assertion, mandate human approval on every contradiction case, and prefer abstention over an answer resting on an assertion past its reverification horizon.
- **Multi-agent shared stores**: Assign write authority to the Admission Agent alone; give every other agent read access under its own scope bindings. Contradictions between agents' proposals are the normal case rather than an exception, which makes the Phase 4 halt rules the primary safeguard against a shared store degrading faster than any single agent could degrade it.
- **Strict latency budgets**: Shorten traversal budgets and precompute the common paths as materialised inferences bound to a generation; never remove eligibility filtering to gain latency, since an ineligible result returned quickly is a policy breach rather than a fast answer.

***

## V. Limitations and Considerations

**Thresholds here are deployment defaults, not measured constants**: Every numeric bound in this guide, including the 0.90 scope-collapse trigger, the 2 percent and 5 percent over-generalisation rates, the 5 percent and 10 percent staleness ratios, the 1 percent and 3 percent contradiction rates, the 0.5 percent false-merge rate, the resolution F1 floors, and the traversal budgets, was chosen to be operable on first deployment rather than derived from a universal property of knowledge stores. The mitigation is the recalibration requirement in Section III.D, which obliges every deployment to recompute thresholds per relation type and entity class against its own adjudicated outcomes, and to record the recomputed values as the operative ones.

**Detection of over-generalisation depends on declaring the dimension**: The scope-collapse audit can only flag a dimension the registry declares. A qualifying context nobody thought to declare is invisible to the audit and will produce exactly the failure the audit exists to catch. The mitigation is the competency-question discipline in Phase 1 together with the registry-evolution mechanism in Section III.D, which promotes a dimension to mandatory once the audit or a human review has implicated it, and re-audits the relation type retrospectively.

**Validity intervals are only as good as their evidence timestamps**: An interval computed from evidence whose own dating is imprecise, absent, or wrong will be confidently wrong at a precision the store records as exact. The mitigation is the precision rule in Step 2.3, which forbids a precision finer than the coarsest supporting source, together with the checkpoint that fails a batch where `valid_from` equals `transaction_from` in the presence of earlier evidence.

**Contradiction detection is complete only over typed fields**: Mechanical detection catches conflicts expressible as functional predicates, incompatible values, and overlapping intervals. A conflict between two free-text assertions, or between assertions in different relation types that jointly imply an impossibility, reaches detection only through model proposal and only where the proposal is generated. The mitigation is the scheduled sweep, the disputed status that suppresses both members rather than ranking them, and the explicit acknowledgement in the metric set that contradiction rate measures detected contradictions rather than existing ones.

**A store can be internally consistent and externally wrong**: Every control in this guide governs the relation between an assertion and its evidence, its scope, its time, and the rest of the store. None governs whether the evidence was true. A store fed consistently by a mistaken or manipulated source will pass every checkpoint here. The mitigation is the evidence-class requirement for independent provenance families, the source-dominance quarantine trigger in Section III.C, and the recognition that aggregate quality monitoring does not detect targeted manipulation, which is why attack success must be measured separately on targeted and non-targeted queries.

**Graph structure is not proof of truth**: A node, an edge, a dense-retrieval neighbour, a repeated statement, and a model's stated confidence are each evidence about the store rather than evidence about the world. The mitigation is the separation of assertion type into quoted, observed, source-asserted, and model-inferred, the prohibition on writing retrieval hints as relations, and the requirement that every inferred assertion carry its rule version, premises, and justification so it can be invalidated when a premise changes.

**Maintenance cost is the dominant lifetime cost**: Adjudication, migration, index rebuilds, deletion propagation, and incident response exceed the cost of initial construction in a store that lives longer than a year. Deployments that budget for construction alone accumulate the backlogs this guide's halt rules then convert into admission stoppages. The mitigation is the cost-per-attributable-answer metric, the 180-day baseline re-measurement, and the explicit gate rule that a store no longer outperforming its substitute is retired rather than maintained.

**Erasure is bounded by what the derivative graph can reach**: Deletion propagates only to targets the dependency traversal names. Dense vectors, summaries, exports, evaluation fixtures, and backups are the recurring gaps, and inferred assertions and embeddings remain a linkage risk even after their sources are removed. The mitigation is the requirement that every derivative be rebuildable from canonical records, that tombstones precede derivative deletion, and that any target that cannot be verified as purged is recorded with its residual risk rather than closed as complete.

***

## VI. Conclusion and Summary

A semantic store is a governed claim system before it is a graph. Its value comes from a small number of properties that simpler stores do not supply: a stable identity for each entity, a declared meaning for each relation, an explicit scope under which each proposition holds, an interval over which it holds, a provenance set establishing it, and a reversible path back out. A store holding all six answers a point-in-time question, survives a correction, and can be erased on request. A store holding none of them is a collection of plausible sentences whose truth conditions nobody recorded, and it degrades in exactly the three ways this guide treats as first-class: facts stored without their qualifying scope, facts that were true and silently are not, and mutually exclusive facts that retrieval resolves by ranking.

A team introducing a semantic store should build the registry and the gate before building the graph. Declare the competency questions, the classes, the relation types with their evidence classes and volatility classes, and the scope dimensions. Measure the simplest adequate substitute on the same frozen corpus and record the margin. Admit assertions through the deterministic gate from the first write rather than retrofitting provenance and intervals later, because a store admitted without them cannot be repaired without re-deriving every record from sources that may no longer exist. Add resolution, then contradiction handling, then bounded retrieval, then the audits, and only then consider a formal ontology, a reasoner, generated queries, or corpus-wide summarisation, each against a competency question that fails without it.

**Key Success Factors**:

- **Registry before records**: Classes, relation types, evidence classes, volatility classes, and scope dimensions are declared and enforced before the first assertion is admitted, so admission is a mechanical check rather than a per-record judgement.
- **Proposal and admission are separate powers**: The model tier proposes an assertion and the deterministic tier admits it; no component decides whether its own output should be published, and no disagreement is settled by re-prompting.
- **Every assertion carries scope, interval, and provenance**: An assertion without a bound or justified scope, a validity interval within its evidence's precision, and a resolving provenance set is rejected, not repaired.
- **Correction by supersession, never by overwrite**: A changed fact closes an interval and writes a successor; the predecessor, its evidence, and the rationale that demoted it all survive, which is what makes a point-in-time answer and a rollback possible.
- **The three degradation modes are audited, not assumed absent**: Over-generalisation, staleness, and contradiction accumulation each carry a computed statistic, a numeric trigger, a halt rule, and a repair that binds or closes rather than deletes.
- **Reversibility end to end**: Merges, splits, resolutions, migrations, and generations each carry an executable inverse and a verified invalidation cascade, so an error found late is correctable rather than permanent.

By following this guide, AI agents can maintain a store of general facts whose every answer names the evidence it rests on, the scope it holds under, and the interval it was valid across, and whose degradation is detected by measurement rather than discovered by a wrong decision.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion except where an entry is explicitly marked as confirmed during conversion research, and their titles and locations are otherwise reproduced rather than checked.

**Corpus pointers**:

- `Semantic Memory Networks for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the claim-versus-fact stance, the promotion criteria across memory systems, the representation selection rules, the competency-question discipline, the reversible identity requirement, the schema-guided extraction staging, the bitemporal and provenance model, the conservative inference constraints, the bounded-subgraph retrieval discipline, the maintenance and erasure obligations, the trust-boundary controls, the telemetry field inventory, and the fourteen-step operational workflow. It carries inline citations to specifications, tooling documentation, benchmarks, and primary literature; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — the sibling governing the situated record. Owns episode definition, boundary specification, capture, temporal and contextual indexing, outcome labelling, and episode retention. The boundary against it is stated in Section 1.2 and is not restated in the phases.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — the sibling governing the pipeline that turns grouped episodes into promoted candidates. Owns grouping, deduplication, intra-group contradiction handling, abstraction, and the promotion gate. This guide takes its output as an input at the Phase 2 admission gate.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — companion guidance on decay, retention classes, and deletion, applicable to the reverification schedule and pruning steps in Phase 6.
- `advanced_task_guides/memory-management/guide_StructuredMemory.md` — companion guidance on schema-bound memory representations, applicable to the representation selection in Step 1.3.
- `advanced_task_guides/memory-management/guide_TemporalKnowledgeGraphMemory.md` — the sibling owning the graph form that carries time on its edges, the independence of the two time axes, and the semantics of a point-in-time query. This guide owns the ontology, the entity resolution, and the assertion-level validity interval; that guide is the destination where Step 1.3 concludes that a full bitemporal graph is warranted.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the operation contract for a single read and a single write, including gate ordering, idempotency, and terminal states; applicable to the assertion commit in Step 2.3 and the generation republication in Step 6.3.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — the general treatment of memory systems and their observability, applicable to the telemetry the checkpoints in Section III.B require.
- `advanced_task_guides/knowledge-graphs/guide_KG_SchemaDesign.md` — companion guidance on graph schema construction, applicable to the class and relation declarations in Step 1.2.
- `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md` — companion guidance on blocking, matching, and clustering, applicable to every step of Phase 3.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on provenance modelling, applicable to the provenance set and evidence-family counting in Phase 2.
- `advanced_task_guides/knowledge-graphs/guide_KG_QualityControl.md` — companion guidance on graph quality measurement, applicable to the audits in Phase 6.
- `advanced_task_guides/ontology/guide_ontology_CompetancyQuestions.md` — companion guidance on eliciting and formulating competency questions, applicable to Step 1.1.
- `advanced_task_guides/ontology/guide_ontology_CQ2Onto.md` — companion guidance on deriving ontology commitments from competency questions, applicable to Step 1.2.

**External references**:

*Representation, specifications, and constraint languages*

1. W3C, *RDF 1.2 Concepts and Abstract Data Model* — https://www.w3.org/TR/rdf12-concepts/ (confirmed during conversion research: published as a Candidate Recommendation Snapshot on 7 April 2026, introducing triple terms in object position; implementations must pin the version they target)
2. ISO, *ISO/IEC 39075:2024 Information technology — Database languages — GQL* — https://www.iso.org/standard/76120.html (confirmed during conversion research as published; Cypher conformance is partial and product-specific)
3. Neo4j, *Cypher Manual* — https://neo4j.com/docs/cypher/
4. Memgraph, *Differences in Cypher implementations* — https://memgraph.com/docs/querying/differences-in-cypher-implementations
5. Kuzu, *Documentation* — https://kuzudb.github.io/docs
6. W3C, *SPARQL 1.1 Overview* — https://www.w3.org/TR/sparql11-overview/
7. W3C, *OWL 2 Profiles* — https://www.w3.org/TR/owl2-profiles/
8. W3C, *SKOS Simple Knowledge Organization System Reference* — https://www.w3.org/TR/skos-reference/
9. W3C, *Shapes Constraint Language (SHACL)* — https://www.w3.org/TR/shacl/
10. *Shape Expressions (ShEx)* — https://shex.io/
11. *JSON Schema specification* — https://json-schema.org/specification
12. schema.org, *Schemas* — https://schema.org/docs/schemas.html
13. *Basic Formal Ontology* — https://bfo-ontology.github.io/
14. *Common Core Ontologies* — https://commoncoreontology.github.io/cco-webpage/
15. Baader and colleagues, *The Description Logic Handbook* — https://redirect.cs.umbc.edu/courses/graduate/691/fall17/01/papers/DescriptionLogicHandbook.pdf

*Identity, provenance, and truth maintenance*

16. W3C, *PROV-O: The PROV Ontology* — https://www.w3.org/TR/prov-o/
17. W3C workshop paper on the misuse of strict identity assertions in linked data — https://www.w3.org/2009/12/rdf-ws/papers/ws21
18. *Nanopublication Guidelines* — https://nanopub.net/guidelines/working_draft/
19. Ontotext, *GraphDB RDF-star documentation* — https://graphdb.ontotext.com/documentation/11.5/rdf-sparql-star.html
20. *An overview of end-to-end entity resolution for big data* — https://arxiv.org/html/2008.04443v3
21. OEG, *OOPS pitfall catalogue* — https://oops.linkeddata.es/catalogue.jsp

*Extraction, confidence, and reasoning*

22. *A survey on knowledge graphs and hallucination in large language models* — https://arxiv.org/abs/2311.07914
23. *A survey of confidence estimation and calibration in large language models* — https://aclanthology.org/2024.naacl-long.366/
24. *HermiT OWL Reasoner* — http://www.hermit-reasoner.com/
25. *ELK Reasoner* — https://www.cs.ox.ac.uk/isg/tools/ELK/
26. *The Vadalog system: Datalog-based reasoning for knowledge graphs* — https://arxiv.org/abs/1807.08709
27. Stardog, *Inference engine documentation* — https://docs.stardog.com/inference-engine/
28. *Predictive multiplicity of knowledge graph embeddings* — https://arxiv.org/abs/2408.08226

*Retrieval, benchmarks, and evaluation*

29. Microsoft, *GraphRAG local search* — https://microsoft.github.io/graphrag/query/local_search/
30. Microsoft, *GraphRAG global search* — https://microsoft.github.io/graphrag/query/global_search/
31. LlamaIndex, *Property graph index guide* — https://developers.llamaindex.ai/python/framework/module_guides/indexing/lpg_index_guide/
32. Neo4j, *GraphRAG for Python* — https://neo4j.com/docs/neo4j-graphrag-python/current/
33. *Graphiti* — https://github.com/getzep/graphiti
34. *RAG vs. GraphRAG: A systematic evaluation and key insights* — https://arxiv.org/abs/2502.11371 (confirmed during conversion research: reports task- and configuration-dependent trade-offs rather than a uniform advantage for graph retrieval)
35. *GraphRAG-Bench* — https://arxiv.org/abs/2506.02404
36. *A survey of graph retrieval-augmented generation* — https://arxiv.org/abs/2501.13958
37. *LC-QuAD 2.0* — https://jens-lehmann.org/files/2019/iswc_lcquad2.pdf
38. *2WikiMultiHopQA* — https://arxiv.org/abs/2011.01060
39. *MuSiQue* — https://arxiv.org/abs/2108.00573
40. *CronQuestions* — https://aclanthology.org/2021.acl-long.520/
41. *TimeQuestions* — https://pure.mpg.de/rest/items/item_3493795_2/component/file_3493796/content?download=true

*Temporal validity, staleness, and security*

42. Rasmussen and colleagues, *Zep: A temporal knowledge graph architecture for agent memory* — https://arxiv.org/abs/2501.13956 (retrieved during conversion research; describes bitemporal edge validity with invalidation rather than deletion)
43. Chao and colleagues, *STALE: Can LLM agents know when their memories are no longer valid?* — https://arxiv.org/abs/2605.06527 (retrieved during conversion research; identifies implicit conflict, where a later observation invalidates an earlier memory without explicit negation, as an under-measured failure mode)
44. Xi and colleagues, *On the security risks of knowledge graph reasoning* — https://www.usenix.org/conference/usenixsecurity23/presentation/xi
45. *Membership inference attacks on knowledge graph embeddings* — https://arxiv.org/abs/2104.08273
46. Information Commissioner's Office, *Right to erasure guidance* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/

*Tooling and infrastructure*

47. Apache, *Jena Fuseki* — https://jena.apache.org/documentation/fuseki2/
48. Amazon, *Neptune graph query languages* — https://docs.aws.amazon.com/neptune/latest/userguide/access-graph-queries.html
49. Stanford, *Protege* — https://protege.stanford.edu/
50. *Blazegraph database repository* — https://github.com/blazegraph/database
