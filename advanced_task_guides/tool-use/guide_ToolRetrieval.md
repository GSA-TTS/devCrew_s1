# Tool Retrieval

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Tool retrieval constitutes the task family of selecting which tool definitions are placed in an agent's context for one step, rather than admitting an entire authorized catalogue. This guide provides AI agents with a structured protocol for operating a retrieval mechanism over a tool catalogue: a canonical registry that holds the source of truth, a derived and versioned index built from purpose statements, capability terms, parameter semantics, example invocations, and observed successful-use records, an eligibility filter that computes the authorized set before any relevance score exists, a bounded exposed set, and an evaluation harness measuring recall against a labelled request-to-tool set. It specifies the recall asymmetry that defines the problem: a tool that is not retrieved cannot be called and the task fails outright, while a mildly irrelevant retrieved tool costs only budget, so recall dominates precision and the operating point is set against a stated floor rather than balanced. It specifies reindexing triggers, stale-index detection, disambiguation of near-duplicate tools, per-slice measurement so that a rare but critical tool's retrieval failure is not concealed by aggregate figures, and the security consequence that retrieval determines what an agent is able to do in a step. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that narrowing the catalogue improves task outcomes rather than silently removing capability.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Tool retrieval**: The read-time operation of selecting a bounded subset of tool definitions from a larger authorized catalogue and exposing that subset to a model for one step. It produces visibility, never permission.

**Tool catalogue**: The full authorized inventory of tool versions an agent may reach through retrieval without serializing them into context. The term is adopted from the context-management category and is used here unchanged.

**Canonical tool record**: The immutable, versioned registry entry for one tool version, holding a canonical identifier independent of display name, complete input and output schemas, purpose and boundary statements, owner, lifecycle state, authorization metadata, side-effect class, dependency edges, and the digest of the definition. The registry is authoritative; the index is a derived view.

**Retrieval index**: The derived, versioned search structure built from a frozen catalogue snapshot. It holds retrieval documents and their identifiers, never the authoritative definition, and it is rebuilt or refreshed rather than edited in place.

**Retrieval document**: One derived text or vector representation of a single facet of a tool, such as its identity terms, its purpose statement, its parameter semantics, or its example invocations. Multiple retrieval documents map to one canonical tool version, and every document carries the identifier of the version that produced it.

**Eligibility filter**: The deterministic stage that evaluates principal, tenant, delegated scope, purpose, environment, region, lifecycle state, revocation, model compatibility, health, and risk ceiling, emitting allow, deny, or quarantine per tool version. The term is adopted from the context-selection sibling and applies here to tool versions rather than to context units.

**Eligible catalogue**: The intersection of the approved catalogue snapshot with the eligibility filter's allow set for the current principal and step. Retrieval is executed against the eligible catalogue and never against the full catalogue.

**Candidate pool**: The bounded set of tool versions returned by one retrieval branch before fusion, deduplication, and bounding. Pools are formed per branch and per query variant, and every pool is capped by construction.

**Exposed set**: The ordered, bounded set of tool definitions serialized into the tool-definition partition for one step. A tool absent from the exposed set is not callable in that step.

**Tool loadout**: The set of tool definitions admitted into the tool-definition partition for the current step. The term is adopted from the context-selection sibling; the exposed set is the loadout this guide's mechanism produces.

**Deferred definition**: A tool definition present in the catalogue and reachable by search but excluded from the context window until retrieval returns it, so that catalogue size drives retrieval cost rather than prompt cost.

**Capability statement**: The structured expression of what the current step needs a tool to do, naming the desired effect, the object acted upon, the required inputs, the expected output, and the prohibited effects. It is the input to query construction and is never a guess at a tool name.

**Query variant**: One of a bounded set of alternative retrieval queries derived from the same capability statement, such as exact-identifier terms, normalized intent, or a capability hypothesis. Variants are retrieved independently, fused, and deduplicated by canonical identifier.

**Recall floor**: The declared minimum proportion of genuinely required tools that must appear in the exposed set on the labelled evaluation slice, below which a retrieval configuration is not promoted. It is the primary release gate of this method.

**Complete-set recall**: The proportion of multi-tool labelled cases in which every genuinely required tool appears in the exposed set. It is measured separately from single-tool recall because a task requiring three tools fails when any one of them is missing.

**Missed-tool regret**: A decision in which an authorized tool that would have succeeded was never retrieved. The term is adopted from the context-selection sibling and is the failure this method's recall floor exists to bound.

**Near-duplicate cluster**: A set of two or more eligible tool versions whose retrieval documents are similar enough that ranking cannot reliably separate them, and whose behavioural contracts nonetheless differ in scope, data source, write authority, region, units, or cost.

**Disambiguating metadata**: The structured fields attached to each member of a near-duplicate cluster that state the distinction a description alone does not carry, such as authoritative data source, write authority, covered region, unit system, latency class, and the named sibling tool each member should not be confused with.

**Reindexing trigger**: A declared condition that obliges an index refresh, drawn from a closed set covering catalogue change, revocation, list-change notification, embedding or analyzer version change, freshness deadline, and staleness alarm.

**Stale index**: An active index that no longer represents the approved catalogue, detected by a canary query returning a removed or revoked tool version, by a manifest count mismatch, or by an age exceeding the declared freshness objective.

**Index poisoning**: The manipulation of retrieval documents, whether by a compromised publisher, an unreviewed third-party server, or an unvalidated generated expansion, so that a tool wins retrieval it should not win or displaces a tool that should. It is an integrity attack on agent behaviour, not merely a relevance defect.

**Reason code**: A normalised categorical label recorded with every exclusion, retrieval, exposure, and refresh event, drawn from a closed vocabulary so retrieval behaviour is analysable without reading prose logs. The term is adopted from the context-selection sibling.

**Retrieval record**: The immutable per-step log of the capability statement, query variants, catalogue and index versions, eligibility verdict counts, branch candidates, fusion result, exposed set, and selection outcome. It is the artifact this method emits on every step.

### 1.2 The Recall Asymmetry and the Motivating Evidence

**Why retrieval becomes necessary rather than optional**: Admitting every tool definition consumes budget and degrades selection accuracy as the catalogue grows, so beyond a catalogue size the full-admission regime stops being viable. Vendor guidance retrieved during this conversion states the regime boundary directly: retrieval-based tool selection applies where 10 or more tools are available or where tool definitions consume more than 10,000 tokens, and the ability to pick the right tool degrades once available tools exceed the 30 to 50 range; an aggregation of multiple protocol servers, commonly 200 or more tools, is named as a case requiring retrieval without further analysis, and a typical five-server setup is reported to consume roughly 55,000 tokens in definitions before any work begins [1]. Standard full-catalogue calling is stated to remain the better fit below 10 tools, where every tool is used in every request, or where definitions total under 100 tokens [1]. These two facts are separate. Budget pressure is a cost problem and is recoverable; selection degradation is a correctness problem and is not.

**The independent research signal**: Benchmark evidence establishes that the retriever itself can be the binding constraint. ToolRet, verified during this conversion, assembles 7,615 retrieval tasks over a corpus of 43,215 tools and reports that all retrievers in its experiments achieve less than 35 percent Completeness@10 and under 52 percent Recall@10, and that models strong on conventional information-retrieval benchmarks perform poorly on tool retrieval [2]. RAG-MCP, also verified, reports that retrieval more than triples tool selection accuracy, at 43.13 percent against a 13.62 percent baseline, while cutting prompt tokens by over 50 percent [3]. The two results are consistent and jointly define the operating problem: retrieval is worth doing, and a retrieval stage that is not measured is a plausible new single point of failure rather than an improvement.

**The recall asymmetry**: The costs of the two error directions are not comparable. A tool that is not retrieved cannot be called, so the step has no path to success and the task fails outright, usually without the agent being able to name what is missing. A mildly irrelevant tool that is retrieved costs some budget, a small amount of selection attention, and nothing else, provided the execution gate is independent. Recall therefore dominates precision in this method, and the operating point is set accordingly rather than balanced. The guide states one floor and holds it: retrieval hit rate at the declared exposure limit must meet or exceed 0.90 on every labelled slice, and complete-set recall must meet or exceed 0.85 for multi-tool cases, below which the configuration is not promoted. Precision is a budget constraint expressed as the exposure cap, not a competing objective to be traded against recall.

**Boundary with the context-selection sibling**: `advanced_task_guides/context-management/guide_ContextSelection.md` owns the admission of tools alongside every other content type under one bounded context budget: it declares the partitions, sizes them against each other, holds the tokenizer, applies the admission cut, and measures utilization. This guide owns the tool retrieval mechanism itself, its index, and its evaluation. The division is exact. The sibling decides how many tokens the tool-definition partition receives and whether a retrieved definition is admitted; this guide decides which definitions the retrieval stage is able to offer it, and whether that offer contains the tools the step genuinely needs. The budget machinery is not restated here, and the sibling's partition table, admission threshold pairing, and assembly record govern wherever the two touch. Where the exposure bound this guide computes conflicts with the partition bound the sibling holds, the partition bound wins and the displaced definitions are logged as excluded with a reason code.

**Retrieval grants visibility and never permission**: A tool absent from the exposed set is not callable in this step. A tool present in the exposed set is still not authorized to execute. Reauthorization, schema validation, approval, invocation, and result verification are separate controls that run after selection and are not weakened by anything retrieval does.

### 1.3 What the Index Contains

A tool's name and description are written for a human reader or a model reader deciding among a handful of already visible options. They are not retrieval documents. A description optimised for a reader states what the tool is in the vocabulary of the system that owns it, assumes surrounding context the query will not carry, and omits the outcome vocabulary a requester actually uses. Retrieving directly on name and description therefore performs poorly, and the poor performance is systematic rather than incidental: the query describes a desired outcome in ordinary language while the document describes an implementation in owner vocabulary, and the lexical overlap between the two is low. The index must therefore hold more than the catalogue's reader-facing text.

**Index content inventory**:

| Document class | Content indexed | Primary retrieval role |
| :-- | :-- | :-- |
| Purpose | The positive-use statement in outcome language, the intended effect, and the explicit negative-use boundary naming what the tool must not be selected for | Matches outcome-oriented and paraphrased requests |
| Capability terms | Canonical name, namespace, aliases, operation identifiers, entity and object types acted upon, domain vocabulary, and supported verbs | Matches exact identifiers, acronyms, and short technical queries |
| Parameter semantics | Parameter names, descriptions, units, formats, required-versus-optional status, meaningful enumerations, and the representative output shape | Separates tools whose purpose statements are near-identical but whose contracts differ |
| Example invocations | Two to five reviewed request-to-invocation examples in requester language, plus explicitly labelled non-examples drawn from the confusable neighbours | Expands paraphrase coverage and supplies negative evidence |
| Observed successful-use records | Verified prior requests for which this tool version was selected, invoked, and produced a verified postcondition, stored as query text with the outcome label | Grounds retrieval in demonstrated fit rather than described fit |
| Disambiguation fields | Authoritative data source, write authority, covered region, unit system, latency and cost class, and the named siblings this tool is confused with | Separates near-duplicate clusters that no similarity score separates |

Four rules bind the index content. Each document class is indexed separately with field-level provenance rather than concatenated into one blob, because a single vector over an entire schema and documentation set blurs unrelated functions, hides which field matched, and complicates deletion. Observed successful-use records are admitted only where the outcome was independently verified, because unverified usage encodes prior selection errors as evidence and lets popularity manufacture its own justification. Generated expansions, including synthetic queries, are untrusted derived metadata until validated against the actual tool contract, and any generated query requiring an undeclared capability, permission, side effect, parameter, or data source is rejected rather than indexed. No credential, tenant secret, live customer record, private endpoint, or mutable health value is embedded; policy and health are filters and ranking features read from authoritative state, never index content.

**Cold-start handling**: A newly published tool has no observed successful-use records and must not be penalised for their absence, since ranking that requires usage history makes new capability permanently undiscoverable. A new tool version is ranked from its reviewed purpose, capability terms, parameter semantics, and examples alone, and its owner supplies a launch suite of at least 10 labelled requests and at least 3 near-neighbour negatives before the version enters an active index.

### 1.4 Execution Tier Partition

Tool retrieval is a hybrid capability, and its production failures are overwhelmingly misassignments of work across three execution tiers. The partition below is load-bearing rather than descriptive: it establishes what may never be delegated to model inference and what may never be reduced to a rule.

**Deterministic tier**: Work requiring exactness, reproducibility, auditability, or scale that model inference cannot supply. Catalogue snapshot construction, index building and refresh, freshness and staleness detection, eligibility and authorization filtering, retrieval execution across lexical and semantic branches, rank fusion, deduplication by canonical identifier, result-set bounding, definition hydration and digest verification, exposure ordering, and recall measurement all sit here. The deterministic tier may exclude any tool version for any recorded reason and is never overridden by a model verdict.

**Model tier**: Work requiring open-vocabulary judgement that no deterministic rule covers. Interpreting the step's need into a capability statement, phrasing query variants from that statement, and choosing among the retrieved candidates sit here. The model tier proposes; it never commits, never widens its own eligible set, and never supplies an authorization input.

**Hybrid tier**: Work in which a model proposes and software verifies. Near-duplicate disambiguation, bounded re-retrieval, and miss attribution sit here, and each names an authority holder.

**Authorization precedes ranking, and this ordering is absolute**: The eligible catalogue is computed from trusted identity and policy state before any lexical or semantic score is calculated. An unauthorized tool is never retrievable, not merely unranked. The distinction is not stylistic. Retrieving globally and filtering afterwards leaks tool names, descriptions, existence, and scores into logs, reranker inputs, caches, and traces belonging to a principal not entitled to know the tool exists, and it makes a ranking bug into a disclosure. Where the search backend cannot enforce the tenant and entitlement predicate inside the query itself, a physically or cryptographically separate index is built for that boundary rather than relying on post-filtering. The model never supplies tenant identifier, principal identifier, granted scopes, risk ceiling, or environment as a retrieval input.

**Tier assignment and authority**:

| Work unit | Tier | Authority when tiers disagree |
| :-- | :-- | :-- |
| Catalogue snapshot approval and index construction | Deterministic | Deterministic; an index is never built from an unapproved record |
| Reindexing trigger evaluation and refresh execution | Deterministic | Deterministic; a model claim that the index is current is not evidence |
| Staleness and removed-tool leakage detection | Deterministic | Deterministic; a canary failure blocks exposure regardless of relevance |
| Eligibility and authorization filtering | Deterministic | Deterministic; a relevance verdict never overrides a denial or an unresolved check |
| Capability statement derivation from the step's need | Model | Model proposes; a schema validator rejects statements naming no effect and no object |
| Query variant phrasing and expansion | Model | Model, bounded by a variant cap and forbidden from adding capabilities or destinations |
| Lexical and semantic branch execution and fusion | Deterministic | Deterministic |
| Deduplication by canonical identifier and version | Deterministic | Deterministic |
| Near-duplicate cluster detection | Deterministic | Deterministic; clustering is computed from index similarity and contract fields |
| Near-duplicate resolution among exposed candidates | Hybrid | Model selects; the disambiguating metadata and the least-privilege rule bind, and unresolved ambiguity becomes clarification |
| Result-set bounding and exposure ordering | Deterministic | Deterministic; a model request for more tools is a trigger for a bounded escalation, not an exemption |
| Definition hydration and digest verification | Deterministic | Deterministic; a digest mismatch blocks exposure |
| Selection among exposed candidates | Model | Model, restricted to the exposed set; a selection outside it is rejected before execution |
| Bounded re-retrieval after a diagnosed miss | Hybrid | Deterministic round and escalation caps bind; the model supplies the residual capability statement |
| Recall, completeness, and per-slice measurement | Deterministic | Deterministic |

Three handoffs carry the method's risk and must be instrumented explicitly. The catalogue-to-index handoff passes an approved, frozen snapshot and receives a versioned index plus a manifest proving completeness; a record failing validation is quarantined rather than indexed on defaults. The need-to-query handoff passes the step's residual capability need and receives a capability statement and bounded variants; a variant that introduces a capability, permission, or destination absent from the statement is rejected before retrieval runs. The retrieval-to-selection handoff passes the ordered exposed set with hydrated, digest-verified definitions and receives one selection, one clarification request, one bounded expansion request, or one abstention; anything else is a protocol violation and is not executed.

***

## II. Operational Framework: Authorization-Filtered Tool Retrieval Under a Measured Recall Floor

The framework produces three artifacts: the versioned retrieval index with its completeness manifest, emitted once per build or refresh; the retrieval record, emitted once per step; and the retrieval evaluation report, emitted once per release gate. Phases 1 and 2 establish and maintain the index and run on a catalogue cadence. Phases 3 through 5 execute on every step that needs a tool. Phase 6 executes on an evaluation cadence and returns control to Phase 1 or Phase 2 when a recall gate fails.

### Phase 1: Catalogue Declaration and Index Schema Definition

**Objective**: Fix the authoritative tool record, the retrieval document set derived from it, and the authorization and disambiguation metadata each record carries, so that the index is built from an approved catalogue rather than from whatever text a publisher supplied.

#### Step 1.1: Establish the Canonical Tool Record as the Source of Truth

**Required Actions**:

- Assign every tool version a globally unique canonical identifier independent of its display name, together with a namespace expressing ownership, a semantic version, a schema version, and an immutable digest of the definition.
- Record owner, backup owner, source repository or server identity, publisher, review attestation, creation time, last review time, and lifecycle state for every version.
- Record the complete input and output schemas, the positive-use statement, the negative-use boundary, the side-effect class, reversibility, idempotency, required scopes, data classifications, and allowed destinations.
- Record dependency edges naming prerequisites, companion tools, and mutually exclusive tools, with edge type, direction, and version compatibility on each edge.
- Reject any record lacking a canonical identifier, an owner, a lifecycle state, a schema, or a negative-use boundary, and quarantine it rather than admitting it with defaults.
- Store the registry in a transactional store with append-only version history and tombstones, so that a deletion publishes a tombstone and an immediate revocation before any background compaction runs.

**Required Outputs**:

- A canonical tool record per version carrying all mandatory fields and an immutable definition digest.
- A catalogue version identifier with an ordered change sequence and a signed manifest.
- A quarantine list naming every rejected record and the missing field that caused rejection.

**Quality Checkpoints**:

- Every active record carries a canonical identifier, an owner, a lifecycle state, a schema, and a negative-use boundary; the count of active records missing any of these is 0.
- No two active records share an unqualified name within one candidate set, and a collision blocks the catalogue version rather than being resolved by ranking.
- Every deletion in the change sequence is represented by a tombstone and a revocation entry, and a deletion without both fails the catalogue version.

***

#### Step 1.2: Declare the Retrieval Document Set and the Index Schema

**Required Actions**:

- Declare the retrieval document classes to be derived per tool version, covering at minimum purpose, capability terms, parameter semantics, and example invocations, and adding observed successful-use records where verified outcomes exist.
- Bind each derived document to the canonical identifier and version that produced it, and record the transformation version, so that every retrieved item resolves to exactly one authoritative definition.
- Declare a lexical index schema with named fields and per-field weights for canonical name, aliases, namespace, parameter names, and purpose text, so that exact identifiers remain retrievable.
- Declare a semantic index schema naming the embedding model revision, tokenizer, dimensions, normalization, distance function, and any query or document prefix the model requires, and pin all of them for both build and query time.
- Cap each derived document at a declared length, since an unbounded document blurs unrelated functions and lets a single verbose record dominate a candidate pool.
- Reject any document class whose measured contribution to recall on the labelled set is not positive, rather than retaining every representation on the assumption that more evidence helps.

**Retrieval index schema template**:

```
INDEX_VERSION:
CATALOG_VERSION:
CATALOG_MANIFEST_DIGEST:
TRANSFORM_VERSION:
DOCUMENT_CLASSES:      [purpose, capability_terms, parameter_semantics,
                        example_invocations, observed_use, disambiguation]
LEXICAL_SCHEMA:
  ANALYZER_VERSION:
  FIELDS_AND_WEIGHTS:
SEMANTIC_SCHEMA:
  EMBEDDING_MODEL_REVISION:
  TOKENIZER:
  DIMENSIONS:
  NORMALIZATION:
  DISTANCE_FUNCTION:
PARTITION_KEY:         [tenant_boundary, environment, region]
PER_DOCUMENT_FIELDS:   [canonical_id, version, document_class,
                        source_digest, lifecycle_state, indexed_at]
COMPLETENESS_MANIFEST:  [expected_versions, indexed_versions,
                        tombstoned_versions, quarantined_versions]
```

**Required Outputs**:

- A declared document class list with the retrieval role and length cap of each.
- A pinned lexical schema and a pinned semantic schema with every version-bearing field populated.
- A per-document provenance mapping from derived document to canonical version and transformation version.

**Quality Checkpoints**:

- Every derived document resolves to exactly one canonical tool version; an orphaned document blocks the index build.
- The embedding model revision, dimensions, normalization, and distance function are identical at build time and query time; a mismatch blocks the build rather than degrading silently.
- Every retained document class carries a measured recall contribution from the most recent evaluation; a class with no measurement is removed before the next build.

***

#### Step 1.3: Attach Authorization and Disambiguation Metadata to Every Record

**Required Actions**:

- Attach the authorization dimensions the eligibility filter evaluates: tenant and principal entitlement dimensions, required scopes, purpose codes, environment, region and residency constraints, supported models and hosts, protocol versions, and risk ceiling.
- Attach operational state references for lifecycle, revocation, health, circuit state, rate limit, cost estimate, and latency class, holding them as references to authoritative state rather than as indexed values, since they change faster than any index refresh.
- Attach disambiguating metadata to every record: authoritative data source, write authority, covered region, unit system, latency and cost class, and the named sibling tools with which the record is confusable.
- Identify confusable siblings by computing similarity across the purpose and capability documents at build time and by collecting production selection errors, rather than by relying on owner self-report alone.
- Require the owner of each member of a confusable set to state, in one sentence per sibling, the condition under which the sibling is the correct choice instead.
- Length-bound, Unicode-normalize, and field-restrict every publisher-supplied text, and reject any text containing instructions about policy, secrets, other tools, system prompts, or unrelated destinations.

**Required Outputs**:

- An authorization metadata block per tool version covering every dimension the eligibility filter evaluates.
- A disambiguation block per tool version naming its confusable siblings and the discriminating condition for each.
- A publisher text validation report naming every rejected field and its rejection reason.

**Quality Checkpoints**:

- Every active tool version carries a complete authorization metadata block; a version missing any dimension is excluded from the eligible catalogue rather than admitted under a permissive default.
- Every member of a detected confusable set carries a discriminating condition for every other member; an incomplete set blocks promotion of the affected records.
- No publisher-supplied field survives validation while containing an instruction, a policy claim, a secret, or a reference to another tool's behaviour; the surviving count of such fields is 0.

***

### Phase 2: Index Construction, Refresh, and Staleness Control

**Objective**: Build the retrieval index from an approved catalogue snapshot and keep it representative of that catalogue, so that no removed tool remains retrievable and no approved tool becomes undiscoverable.

#### Step 2.1: Build the Versioned Index From an Approved Catalogue Snapshot

**Required Actions**:

- Freeze the source catalogue version, the approved record set, the policy schema version, the transformation version, and the embedding and analyzer model revisions before any document is generated.
- Validate every record for required fields, identifier uniqueness, namespace correctness, schema well-formedness, ownership, lifecycle state, and content limits, quarantining failures rather than indexing them.
- Generate the declared retrieval documents, compute lexical postings and embeddings, and record the source digest for every derived item.
- Build an immutable candidate snapshot and verify indexed version count against expected version count, tenant partition assignment, absence of tombstoned versions, vector dimensionality, and referential integrity from every document to its canonical version.
- Run the labelled evaluation suite and the adversarial ranking suite against the candidate snapshot before it is published, and publish by switching an atomic alias only after every mandatory gate passes.
- Retain the previous index version for rollback, and never permit a revoked tool version to be reachable through the retained version.

**Required Outputs**:

- An immutable index version with a completeness manifest naming expected, indexed, tombstoned, and quarantined version counts.
- A build evaluation report carrying recall, completeness, and adversarial results against the declared gates.
- An atomic alias switch record naming the previous and new index versions and the rollback path.

**Quality Checkpoints**:

- Indexed version count equals expected version count minus tombstoned and quarantined counts; any discrepancy blocks publication.
- Zero tombstoned or revoked versions are reachable in the candidate snapshot, verified by exact-identifier canary query before the alias switches.
- The active index is never mutated outside a published version; an in-place edit of an active index is a release defect and triggers a full rebuild.

***

#### Step 2.2: Operate the Reindexing Trigger Set

**Required Actions**:

- Declare the closed reindexing trigger set: an approved catalogue change, a revocation or deprecation, a server list-change notification, an embedding or analyzer version change, a schema or transformation change, a scheduled freshness deadline, and a staleness alarm.
- Treat a full rebuild as mandatory for an embedding model change, an analyzer change, a schema change, or a transformation change, since mixing vector spaces or analyzers within one index produces incomparable scores; build the replacement in parallel rather than in place.
- Treat an incremental refresh as sufficient for an addition, a content change, a deprecation, or a removal, regenerating only the affected documents under the pinned pipeline.
- On a removal or revocation, publish the tombstone, block the version in the policy layer immediately, then remove every derived document, vector, alias, dependency edge, and cache entry that referenced it, in that order, so that the deny takes effect before the index catches up.
- Treat a list-change notification from an external server as a refresh trigger only; a notification never authorizes an unseen tool, and every newly listed tool passes the Phase 1 validation and approval path before it is indexed.
- Set a maximum index age per risk class, declaring 24 hours as the default freshness objective for standard tools and 1 hour for tools whose authorization or health changes materially within a day.
- Retry a transient refresh failure at most twice, then quarantine the change, raise a staleness alarm, and require an owner decision rather than retrying indefinitely.

**Required Outputs**:

- A trigger evaluation record naming which trigger fired, the change set it covered, and the refresh mode selected.
- A refresh manifest proving that every affected document, vector, edge, and cache entry was regenerated or removed.
- A freshness objective per risk class with the current measured index age against it.

**Quality Checkpoints**:

- Every index change traces to exactly one declared trigger; an untriggered index change is a release defect and blocks promotion.
- An embedding, analyzer, schema, or transformation change never results in an incremental refresh; the count of such in-place changes is 0.
- Measured index age remains within the declared freshness objective for its risk class in at least 99 percent of retrieval decisions; a breach raises a staleness alarm rather than being averaged away.

***

#### Step 2.3: Detect Stale Indexes and Removed-Tool Leakage

**Required Actions**:

- Run an exact-identifier canary query for every tool version removed or revoked in the last 30 days on every refresh and at a scheduled interval of no more than 1 hour, asserting that no removed version is returned.
- Run a semantic canary query built from each removed version's own purpose document, since an exact-identifier check alone does not detect a surviving vector whose identifier was rewritten.
- Compare the completeness manifest of the active index against the current catalogue version on every scheduled check, and treat any missing approved version as an availability defect equal in severity to a leaked removed version.
- Compute index staleness per tool as the interval between the latest approved catalogue change for that tool and its representation in the active index, and report the maximum and the 95th percentile rather than the mean.
- Fail closed on detection: block retrieval of the affected tool class, serve the last known-good snapshot only for non-revoked tools and only within its declared age limit, and mark every retrieval record produced during the degraded interval.
- Record deletion leakage rate and unauthorized exposure rate on every evaluation cycle, and treat both as zero-target gates rather than as metrics to be minimised.

**Required Outputs**:

- A canary result set covering exact-identifier and semantic checks for every recently removed version.
- A staleness report carrying maximum and 95th-percentile index staleness per risk class and the count of approved versions missing from the active index.
- A degraded-interval record naming the affected tool class, the fallback served, and the retrieval records marked.

**Quality Checkpoints**:

- Deletion leakage rate is 0 for the evaluation window; any non-zero value halts promotion and triggers an immediate rebuild.
- Unauthorized exposure rate is 0 for the evaluation window; any non-zero value halts retrieval for the affected boundary until the cause is corrected.
- Catalogue coverage, defined as approved active versions completely represented in the active index divided by approved active versions required in it, is at or above 0.99; below that figure retrieval runs in a marked degraded state rather than silently.

***

### Phase 3: Query Construction From the Step's Capability Need

**Objective**: Convert the step's residual need into a capability statement and a bounded set of query variants, so that retrieval is executed against what the step must accomplish rather than against the surface text of a request.

#### Step 3.1: Derive the Capability Statement From the Step's Residual Need

**Required Actions**:

- State the desired effect using one verb drawn from a closed capability vocabulary covering search, read, calculate, execute, communicate, mutate, and verify, so that the effect is comparable across steps and analysable in logs.
- Name the object acted upon, its type, and any identifier or constraint that narrows it, together with the required inputs already available and the expected output the step consumes next.
- Name the prohibited effects explicitly, since a step needing a read must not retrieve a mutating sibling into the exposed set where a read-only sibling exists.
- List the tools already invoked in this task and whether each remains valid, so that a still-live capability is not re-retrieved as a new need.
- Exclude every credential, secret, protected record, and instruction copied from a prior tool output from the statement, since the statement is embedded, logged, and possibly sent to an external ranking endpoint.
- Emit an explicit no-tool verdict where the step needs no external capability, and route deterministically where workflow state identifies exactly one valid tool, rather than running retrieval in either case.

**Required Outputs**:

- A capability statement naming effect, object, inputs, expected output, and prohibited effects.
- A live-capability list naming already invoked tools and their validity.
- A retrieval-necessity verdict of no tool, deterministic route, full-catalogue admission, or retrieval.

**Quality Checkpoints**:

- The capability statement names exactly one primary effect from the closed vocabulary; a statement naming none or several is returned for decomposition before retrieval runs.
- The statement carries no credential, secret, protected record, or copied instruction; the count of such items is 0.
- The retrieval-necessity verdict follows the regime rule, admitting the full catalogue only below 10 tools and 10,000 tokens of serialized definitions and operating retrieval otherwise.

***

#### Step 3.2: Compose Bounded Query Variants

**Required Actions**:

- Generate at most 4 query variants per capability statement, drawn from exact-identifier terms, normalized intent in outcome language, parameter and contract terms, and a capability hypothesis describing the desired operation without naming a presumed implementation.
- Preserve the raw request text and its hash alongside the variants, so that a rewrite that loses a user constraint is detectable after the fact.
- Prohibit a variant from adding a capability, permission, destination, data source, or user intent absent from the capability statement, and reject any variant that does so before it reaches the index.
- Assign each variant its own identifier and link every variant to one retrieval decision identifier, so that branch results are attributable.
- Stop after one expansion round; generating dozens of correlated variants inflates latency and lets a broad term dominate fusion without adding coverage.
- Retain candidates from both the raw and the rewritten branch where their result sets differ materially, rather than trusting the rewrite alone.

**Required Outputs**:

- A variant set of at most 4 entries with a declared variant class per entry.
- A raw request hash retained beside the variant set.
- A variant validation record naming any rejected variant and the capability, permission, or destination it introduced.

**Quality Checkpoints**:

- Variant count does not exceed 4 per capability statement; a larger set is truncated to the 4 most dissimilar variants with the exclusions recorded.
- No surviving variant introduces a capability, permission, or destination absent from the capability statement; the count of such variants is 0.
- Every variant links to exactly one retrieval decision identifier, so that no branch result is orphaned from its decision.

***

#### Step 3.3: Decompose Compound Needs Into Subgoal Queries

**Required Actions**:

- Decompose a compound request into outcome-bearing subgoals before retrieval, producing one capability statement per unresolved subgoal rather than one query for the whole request.
- Retrieve independently per subgoal, union the candidates, and deduplicate by canonical identifier, so that coverage is assessed per subgoal rather than in aggregate.
- Add dependency neighbours only along typed edges consistent with the task, labelling edge type, direction, version compatibility, and risk on each expansion, and pass every expanded node through the eligibility filter before it joins the candidate set.
- Cap graph expansion at 1 hop from a seed by default, since expanding every neighbour amplifies a single over-connected or poisoned record across the candidate set.
- Defer retrieval for a subgoal whose required capability depends on an unknown state produced by an earlier subgoal, and retrieve again after that state is observed rather than exposing a speculative tool now.
- Record the declared tool cardinality estimate for the request, so that complete-set coverage can be judged against an expectation rather than assumed satisfied by any single hit.

**Required Outputs**:

- A subgoal list with one capability statement per unresolved subgoal.
- A dependency expansion record naming each added node, its edge type, and its eligibility verdict.
- A tool cardinality estimate for the request with the subgoals it covers.

**Quality Checkpoints**:

- Every unresolved subgoal has its own capability statement; a compound request retrieved under one statement is returned for decomposition.
- Graph expansion does not exceed the declared hop limit, and every expanded node carries an eligibility verdict; an unfiltered expansion invalidates the candidate set.
- Coverage is assessed per subgoal, and a candidate set covering some subgoals is reported as partial rather than as a successful retrieval.

***

### Phase 4: Authorization-Filtered Retrieval and Bounded Exposure

**Objective**: Produce an ordered, bounded exposed set drawn only from tools the calling principal is authorized to use, with authorization computed before any relevance score exists.

#### Step 4.1: Compute the Eligible Catalogue Before Any Ranking

**Required Actions**:

- Bind principal, tenant, delegated scopes, purpose, environment, region, data class, model and host pair, risk ceiling, and budgets from trusted state, never from model output and never from the request text.
- Pin the catalogue version, policy version, entitlement snapshot identifier, and index version for the decision, so that every branch of the retrieval runs against one consistent view.
- Intersect the approved catalogue snapshot with the authorization dimensions, the lifecycle and revocation state, the health and circuit state, the model and protocol compatibility, and the risk and cost ceilings, emitting an allow, deny, or quarantine verdict per version with a reason code.
- Execute every retrieval branch against the eligible catalogue only, enforcing the tenant and entitlement predicate inside the query where the backend supports it and using a separate index for the boundary where it does not.
- Prohibit retrieval over the global catalogue followed by post-filtering, since scores, names, and descriptions of denied tools would then reach logs, caches, reranker inputs, and traces belonging to a principal not entitled to know the tools exist.
- Exit as capability unavailable where no eligible tool class can satisfy the capability statement, and never widen the eligible set to improve the appearance of the result.

**Required Outputs**:

- An eligible catalogue identifier with the pinned catalogue, policy, entitlement, and index versions.
- An exclusion census recording the count of denied versions per reason code, carrying no denied tool names.
- An eligibility verdict per candidate version, retained for the retrieval record.

**Quality Checkpoints**:

- The eligible catalogue is computed before any lexical or semantic score exists; a decision in which ranking preceded filtering is void and is re-run.
- No denied tool version appears in any candidate pool, log field, cache entry, ranking input, or trace attribute; the count of such appearances is 0.
- Every exclusion carries a reason code from the closed vocabulary, and an exclusion without one blocks the decision rather than being recorded as unspecified.

***

#### Step 4.2: Execute Retrieval Branches and Fuse Rankings

**Required Actions**:

- Execute a lexical branch and a semantic branch in parallel over the same eligible catalogue and the same pinned index version, since exact identifiers and outcome paraphrases fail in opposite directions and neither branch alone covers both.
- Retrieve between 30 and 100 candidates per branch per variant by default, tuning the depth against measured recall rather than against latency alone.
- Fuse the ranked lists by rank position rather than by raw score, since lexical and vector scores are not comparable without calibration and a direct comparison silently favours whichever scale is larger.
- Deduplicate by canonical identifier and compatible version, preferring one production version unless a migration comparison is deliberately in progress, and preserve namespace-qualified names so that two servers cannot contribute the same unqualified name.
- Fuse and deduplicate to between 20 and 50 candidates before any reranking stage, and rerank only that bounded pool where reranking is enabled and its measured gain justifies its latency, cost, and injection exposure.
- Treat every retrieved description, example, and server hint as untrusted data throughout ranking, isolating it from system instruction and capping any single field's contribution so that repeated keywords cannot dominate a score.
- Record branch identity, depth, filters, candidate identifiers, ranks, scores, latency, and error class per branch, so that a miss is attributable to a named stage rather than to retrieval in general.

**Required Outputs**:

- A per-branch candidate pool with ranks, scores, and latency recorded.
- A fused and deduplicated candidate pool of between 20 and 50 entries.
- A branch attribution record naming the stage at which each finally exposed tool entered the pool.

**Quality Checkpoints**:

- Both branches execute against the same pinned index version and the same eligible catalogue; a version mismatch across branches voids the fusion.
- Fusion combines rank positions rather than uncalibrated raw scores; a direct comparison of lexical and vector scores is a configuration defect.
- No retrieved text is treated as instruction at any ranking stage, and no single field contributes more than its declared score cap.

***

#### Step 4.3: Apply Result-Set Bounds and Emit the Exposed Set

**Required Actions**:

- Apply the declared bounds in order: always-resident definitions first, then still-valid previously used tools, then retrieved candidates, then validated dependency prerequisites, stopping at the exposure cap or the partition token bound, whichever binds first.
- Hold the always-resident set to between 3 and 5 definitions justified by observed invocation frequency in the task class, since a larger always-resident set reintroduces the degradation retrieval exists to avoid.
- Expose between 5 and 12 definitions by default, with 5 as the starting value for a single-subgoal step and the upper bound reserved for compound tasks whose cardinality estimate requires it.
- Fetch the authoritative definition for every exposed candidate by canonical identifier and verify its digest against the catalogue before serialization, since the index holds derived documents and never the authority.
- Order the exposed set deterministically, breaking ties by canonical identifier, so that identical inputs produce identical prompts and the stable prefix is not invalidated by listing order alone.
- Hand the ordered set to the context assembler, which holds the partition bound and the tokenizer, and record any definition displaced by the partition bound as excluded with a reason code rather than silently dropped.
- Present abstention, clarification, and one bounded retrieval-expansion control alongside the exposed set, so that the model has a declared path other than selecting a poorly fitting tool.

**Result-set bounds**:

| Bound | Default value | Consequence when breached |
| :-- | :-- | :-- |
| Always-resident definitions | 3 to 5 | An entry without observed invocation-frequency evidence is deferred at the next review |
| Per-branch retrieval depth | 30 to 100 candidates | A depth set below the measured recall knee is raised before the exposure cap is raised |
| Fused pool before reranking | 20 to 50 candidates | A larger pool is truncated by fused rank with the truncation logged |
| Exposed definitions per step | 5 to 12 | Definitions beyond the cap are excluded with a reason code, never silently dropped |
| Retrieval rounds per decision | at most 3 | The decision exits as capability unavailable or clarification rather than continuing |
| Query rewrites per decision | at most 2 | Further rewriting is prohibited and the decision exits |
| Exposure-cap escalations per decision | at most 2 | Further escalation is prohibited; a wider set is not a substitute for a correct query |
| Dependency expansion depth | 1 hop | A deeper expansion is rejected before eligibility filtering runs |

**Required Outputs**:

- An ordered exposed set with hydrated, digest-verified definitions and an exposure reason per entry.
- A bounds record naming each applied bound, its value, and the entries it excluded.
- A control set offering selection, clarification, one bounded expansion, and abstention.

**Quality Checkpoints**:

- Every exposed definition carries a verified digest matching its canonical version; a mismatch blocks exposure of that entry rather than degrading it to a warning.
- The exposed set is within the exposure cap and within the tool-definition partition bound at every round, and the partition bound governs where the two disagree.
- Every exposed entry traces to a stated capability requirement, an always-resident justification, a still-live prior invocation, or a validated dependency edge; an entry tracing to none of these is removed.

***

### Phase 5: Near-Duplicate Disambiguation and Bounded Miss Recovery

**Objective**: Resolve the ambiguity that retrieval necessarily produces when several tools do similar things, and recover from a diagnosed retrieval miss within declared bounds rather than by widening until something plausible appears.

#### Step 5.1: Detect Near-Duplicate Clusters in the Exposed Set

**Required Actions**:

- Cluster the exposed candidates by similarity across their purpose and capability documents, flagging any pair above the declared near-duplicate threshold as one cluster requiring disambiguation.
- Compare the clustered members on their behavioural contract fields rather than on their descriptions, checking authoritative data source, write authority, covered region, unit system, latency and cost class, and required scopes.
- Classify each cluster as separable, where the contract fields differ on at least one dimension the capability statement constrains, or as unseparable, where no contract field distinguishes the members for this step.
- Treat an unseparable cluster of tools with differing side-effect classes as a catalogue defect rather than a retrieval defect, and record it for owner correction under Phase 6.
- Record the cluster, its members, its classification, and the discriminating dimension in the retrieval record, since ambiguity that is not recorded cannot be corrected.
- Preserve the ambiguity where the capability statement genuinely underdetermines the choice, rather than resolving it by score and presenting one arbitrary member as the answer.

**Required Outputs**:

- A near-duplicate cluster list for the exposed set with member identifiers.
- A per-cluster classification of separable or unseparable with the discriminating dimension named.
- A catalogue defect list naming unseparable clusters whose members differ in side-effect class.

**Quality Checkpoints**:

- Every exposed candidate above the near-duplicate threshold against another exposed candidate belongs to a recorded cluster; an unrecorded near-duplicate pair is a detection failure.
- No cluster is resolved by relevance score alone; resolution cites a contract field or the ambiguity is preserved.
- Every unseparable cluster whose members differ in write authority or side-effect class is raised as a catalogue defect within the same evaluation cycle.

***

#### Step 5.2: Expose Disambiguating Metadata and Apply the Least-Privilege Rule

**Required Actions**:

- Serialize the disambiguating metadata for every member of a separable cluster alongside its definition, so that the choice is made against stated distinctions rather than against description similarity.
- Include, for each clustered member, the one-sentence discriminating condition its owner supplied naming when a sibling is the correct choice instead.
- Apply the least-privilege rule where members are otherwise equivalent for the step: prefer the member with the narrowest scope, the smallest side-effect class, and no write authority where the capability statement names a read.
- Cap the number of exposed members from any one cluster at 3, since exposing an entire cluster consumes the exposure budget with variants of one capability and displaces coverage of other subgoals.
- Prohibit a description or example from carrying the disambiguating claim alone, since publisher-supplied prose is untrusted and a competing publisher can assert the same distinction.
- Record which discriminating dimension the selection cited, so that dimensions that never discriminate can be removed and dimensions that repeatedly fail can be strengthened.

**Required Outputs**:

- A disambiguated exposed set with per-member discriminating conditions serialized.
- A cluster exposure record naming the members exposed, the members withheld, and the withholding reason.
- A selection rationale naming the discriminating dimension the choice relied on.

**Quality Checkpoints**:

- Every exposed clustered member carries at least one structured discriminating field; a member carrying only prose is withheld until its owner supplies the field.
- No cluster contributes more than 3 members to the exposed set, and withheld members are recorded rather than dropped.
- Where the capability statement names a read effect, no exposed member of a cluster carries write authority while a read-only member is available.

***

#### Step 5.3: Diagnose the Miss and Bound Re-Retrieval

**Required Actions**:

- Diagnose the cause before re-retrieving, distinguishing policy exclusion, catalogue absence, stale index, lexical miss, semantic miss, fusion loss, reranker demotion, exposure-cap cutoff, dependency miss, query defect, and genuine ambiguity of the request.
- Never rewrite around a policy exclusion; where authorization or lifecycle removed the tool, return denial or capability unavailable rather than searching for a substitute the principal may not use.
- Distinguish a retrieval miss, in which no acceptable tool was exposed, from a selection error, in which an acceptable tool was exposed and not chosen; widen only for the former and improve disambiguating metadata or descriptions for the latter.
- Re-retrieve with exactly one controlled change per round: a widened branch depth, one added variant, one adjacent namespace, or one validated dependency expansion.
- Enforce the declared bounds of at most 2 rewrites, at most 2 exposure-cap escalations, and at most 3 retrieval rounds per decision, and exit on a repeated candidate-set hash even where rounds remain.
- Exit through a declared terminal state: a confident eligible exposed set, a clarification request where competing candidates imply different intent, a denial where policy caused the absence, or a capability-unavailable verdict where no eligible tool exists.

**Required Outputs**:

- A miss diagnosis naming exactly one primary cause from the closed vocabulary.
- A re-retrieval record naming the single controlled change per round and the round count consumed.
- A terminal state verdict of exposed set, clarification, denial, or capability unavailable.

**Quality Checkpoints**:

- Every re-retrieval carries a recorded diagnosis; re-retrieval without one is prohibited and the decision exits.
- No re-retrieval follows a policy exclusion; the count of policy-driven re-retrievals is 0.
- Round, rewrite, and escalation counts remain within their declared bounds, and a decision reaching a bound exits through a terminal state rather than continuing with a warning.

***

### Phase 6: Evaluation Against a Labelled Set and Catalogue Correction

**Objective**: Measure retrieval against requests labelled with the tools genuinely required, per slice rather than in aggregate, and correct the catalogue and index from the measured misses.

#### Step 6.1: Construct and Version the Labelled Request-to-Tool Set

**Required Actions**:

- Label each case with the request text, the eligible catalogue snapshot it was drawn against, the acceptable tool set, the required complete set for multi-tool cases, the ordered dependencies where they apply, the prohibited tools, and the no-tool label where no tool applies.
- Label the required set by what the request genuinely needs to succeed, verified by an end-state check, rather than by what a current retriever happens to return, since labelling from retriever output makes the measurement circular.
- Include at least 30 cases per declared slice, since a slice smaller than that cannot distinguish a recall floor breach from sampling noise.
- Cover the case families that aggregate measurement conceals: exact-identifier and alias requests, outcome-language paraphrases, terse and long turns, near-neighbour discriminations, multi-tool and dependent-tool tasks, iterative tasks whose later tool is initially unknowable, no-tool tasks, newly published tools with no usage history, deprecated and removed tools, and unauthorized-tool attempts.
- Include adversarial cases covering keyword stuffing, poisoned descriptions, homoglyph names, cross-server name shadowing, hidden instructions in descriptions, and dependency-graph amplification.
- Version the labelled set with a digest, maintain a hidden holdout that is never used for tuning, and add a time-split partition covering tools published after the tuning window.

**Required Outputs**:

- A versioned labelled set with a digest and a declared slice assignment per case.
- A per-slice case census showing at least 30 cases per slice.
- An adversarial case subset with the attack class labelled per case.

**Quality Checkpoints**:

- Every case carries an acceptable set, a required complete set where multi-tool, and a verifiable end-state check; a case without one is removed rather than scored.
- No label was derived from the output of the retriever under evaluation; a label traced to retriever output invalidates its slice.
- Every declared slice holds at least 30 cases, and a slice below that count is reported as unmeasured rather than as passing.

***

#### Step 6.2: Measure Recall, Completeness, and Per-Slice Performance

**Required Actions**:

- Compute recall at the declared exposure cap as the proportion of genuinely required tools appearing in the exposed set, and report it per slice as well as in aggregate.
- Compute complete-set recall as the proportion of multi-tool cases in which every required tool was exposed, since a task needing three tools fails when any one is absent and single-tool recall conceals that failure.
- Compute missed-tool regret as the proportion of decisions in which an authorized tool that would have succeeded was never retrieved, and treat it as the headline failure figure rather than as a secondary metric.
- Separate retrieval failure from selection failure by computing selection accuracy conditional on retrieval, defined as the proportion of decisions selecting an acceptable tool when one was exposed, so that a selection problem is not corrected by widening retrieval.
- Attribute every miss to exactly one stage from the closed cause vocabulary, and report the cause distribution per slice, since two slices can share a recall figure and fail for entirely different reasons.
- Run the paired baselines on every evaluation cycle: full static catalogue where it fits, lexical only, semantic only, fused without reranking, and fused with each candidate reranker, holding catalogue, model, task set, and fixtures constant.
- Report latency at the 50th, 95th, and 99th percentiles per stage rather than as an average, and report cost per verified successful task rather than tokens per request.

**Retrieval gates and their floors**:

| Metric | Floor or ceiling | Consequence when breached |
| :-- | :-- | :-- |
| Retrieval hit rate at the exposure cap, per slice | at or above 0.90 | Descriptions and disambiguating metadata are revised before the exposure cap is raised |
| Complete-set recall, multi-tool slice | at or above 0.85 | The configuration is not promoted; subgoal decomposition is corrected first |
| Missed-tool regret, per slice | at or below 0.02 | Promotion of the retrieval configuration is blocked |
| Selection accuracy conditional on retrieval | at or above 0.85 | Disambiguating metadata is strengthened; the exposure cap is not raised |
| No-tool false-positive rate | at or below 0.05 | The no-tool verdict path is corrected before release |
| Deletion leakage rate | exactly 0 | Release halts and a full rebuild is triggered |
| Unauthorized exposure rate | exactly 0 | Retrieval halts for the affected boundary |
| Security escape rate on adversarial cases | exactly 0 for critical outcomes | Release fails; no aggregate improvement compensates |
| Re-retrieval recovery rate | at or above 0.60 | The miss diagnosis vocabulary is revised rather than the bounds relaxed |

**Required Outputs**:

- A per-slice metric report covering every gate in the table with its measured value.
- A miss cause distribution per slice attributing each miss to one stage.
- A baseline comparison report covering the static catalogue and each retriever ablation.

**Quality Checkpoints**:

- Every gate carries a measured per-slice value; an aggregate figure alone is not a pass, since a rare but critical tool's failure is invisible in an aggregate.
- No slice falls below its recall floor at promotion; a single failing slice blocks promotion regardless of aggregate performance.
- Every miss is attributed to exactly one stage; an unattributed miss blocks the release gate rather than being counted as an ordinary failure.

***

#### Step 6.3: Gate Release and Correct the Catalogue From Measured Misses

**Required Actions**:

- Promote a retrieval configuration only where every per-slice gate passes, every zero-target gate is exactly zero, and the guardrail metrics for latency and cost are non-inferior within their declared bounds.
- Correct a measured miss at its attributed stage: add a lexical alias or a capability term for an identifier miss, revise the purpose statement into outcome language for a semantic miss, add a discriminating field for a near-neighbour miss, and revise the subgoal decomposition for a completeness miss.
- Raise the exposure cap only after description, alias, and metadata corrections have been measured and found insufficient, since a wider set restores the budget and attention costs retrieval exists to avoid.
- Split or rewrite a tool contract rather than generating further descriptive text where the same ambiguity survives 3 correction rounds, since an unseparable pair is a catalogue defect that no retriever resolves.
- Release behind flags in stages: offline evaluation, then shadow retrieval that changes no exposed set, then a read-only canary on a low-risk cohort, then limited execution, randomising at the task or tenant level rather than within a task.
- Roll back on any unauthorized exposure, any returned removed tool, any cross-boundary leak, a material success regression, or a budget breach, restoring the catalogue alias, the retriever configuration, and the model versions together.
- Stop after 5 tuning iterations without held-out improvement and revisit tool boundaries, catalogue text, or index design rather than continuing to tune against the same exposed cases.

**Required Outputs**:

- A promotion decision record naming every gate, its measured value, and the pass or fail verdict.
- A catalogue correction list naming each measured miss, its attributed stage, and the correction applied.
- A staged release record naming the stage reached, the cohort, and the rollback trigger set.

**Quality Checkpoints**:

- No configuration is promoted with a failing slice, a non-zero zero-target gate, or an unattributed miss.
- No exposure-cap increase is applied before the corresponding description, alias, and metadata corrections have been measured; an unmeasured cap increase is reverted.
- Every rollback restores catalogue, retriever configuration, and model versions together, since a partial rollback leaves an untested combination in production.

***

## III. Implementation Guidance for AI Agents

AI agents operating a tool retrieval mechanism must follow systematic protocols ensuring that authorization precedes ranking, that recall is measured rather than assumed, and that every exposed definition traces to an approved catalogue version. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Catalogue Registrar**: Owns the canonical registry, version sequence, tombstones, and signed manifest. It alone admits a record into an indexable lifecycle state, and it rejects any record missing a mandatory field rather than defaulting it.
2. **Index Build Agent**: Owns index construction, refresh, atomic alias publication, and rollback. It operates only on a frozen approved snapshot and never edits an active index in place.
3. **Freshness Monitor**: Owns reindexing trigger evaluation, canary queries, staleness measurement, and the degraded-state declaration. It may block retrieval for a tool class on a canary failure without further authority.
4. **Eligibility Agent**: Owns the eligible catalogue computation from trusted identity and policy state. It runs before any ranking component and emits allow, deny, or quarantine with a reason code. No component may retrieve outside the set it returns.
5. **Query Agent**: Interprets the step's residual need into a capability statement and bounded variants. It operates in the model tier, proposes only, and may not add a capability, permission, or destination.
6. **Retrieval Executor**: Owns branch execution, fusion, deduplication, bounding, definition hydration, digest verification, and exposure ordering. It is the deterministic budget holder for the exposure cap and hands the ordered set to the context assembler.
7. **Evaluation Agent**: Owns the labelled set, per-slice measurement, miss attribution, and the promotion verdict. It may withhold promotion and its verdict is not overridden by an aggregate improvement.

**Untrusted-Metadata Boundary**: Every tool name, description, parameter description, example, server hint, and generated expansion is untrusted data at every stage. This is a hard constraint applying to every component.

- Delimit and label catalogue text as untrusted capability metadata wherever it enters a prompt, and never insert a third-party description into a system instruction.
- Reject any field containing instructions about policy, secrets, other tools, system prompts, or unrelated destinations, and reject hidden, homoglyph, or non-normalized content.
- Cap the score contribution of any single field so that repeated keywords cannot dominate a ranking.
- Treat a description that claims to be mandatory, claims priority over other tools, or describes capabilities the schema does not declare as a poisoning indicator and quarantine the record.

**Workflow Execution Pattern**:

```
STATE: Retrieval_Decision
INPUTS:
  1. Capability statement and variant set from Phase 3
  2. Pinned catalog_version, policy_version, entitlement_snapshot_id, index_version
  3. Eligible catalogue identifier from Step 4.1
ACTIONS:
  1. Execute lexical and semantic branches over the eligible catalogue
  2. Fuse by rank position and deduplicate by canonical identifier
  3. Apply always-resident, prior-tool, dependency, and exposure bounds
  4. Hydrate definitions by canonical id and verify each digest
  5. Detect near-duplicate clusters and attach discriminating fields
VALIDATION:
  - eligibility_computed_before_ranking == TRUE
  - denied_tools_in_any_pool_or_log == 0
  - exposed_count <= exposure_cap
  - exposed_tokens <= tool_partition_bound
  - digest_verified_for_all_exposed == TRUE
  - index_staleness <= freshness_objective
  - retrieval_round <= 3
TRANSITIONS:
  IF all_validations_pass THEN next_state = Model_Selection
  IF acceptable_candidate_absent AND rounds_remaining
     THEN next_state = Miss_Diagnosis_And_Bounded_Re_Retrieval
  IF cause == POLICY_EXCLUSION THEN next_state = Denial
  IF eligible_catalogue_empty THEN next_state = Capability_Unavailable
  IF validation_failed THEN next_state = Retrieval_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended exposed set with its bounds, exclusions, and cluster classifications without serializing it; confirm it against the validation block while no context budget is committed; serialize it only after validation passes, recording the retrieval record in the same operation.

**Approval Gate**: Human authorisation is required before promoting any retrieval configuration whose measured per-slice recall falls below 0.90, before releasing an index built from a catalogue version containing an unreviewed third-party publisher, before any exposure-cap increase above 12 definitions per step, and before any relaxation of the rule that authorization precedes ranking. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the catalogue version, index version, policy version, and entitlement snapshot in durable state, since a retrieval session may outlive one context window and a version drift mid-task changes what is callable.
- Serialize only the minimum complete definitions for the exposed set, and hold the rest of the catalogue as deferred definitions reachable by search rather than as context.
- Record exclusions as reason codes and counts rather than as tool names, so that a retrieval record does not itself become a disclosure of tools the principal may not know exist.
- Count the retrieval mechanism's own token cost, including capability statements, variants, and search results, toward the step's budget rather than treating it as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Catalogue Integrity (After Phase 1)**

- **Automated Check**: Every active record carries a canonical identifier, owner, lifecycle state, schema, negative-use boundary, and complete authorization metadata; no unqualified name collides within a candidate set; every confusable set carries a discriminating condition per member.
- **Agent Action on Pass**: Proceed to index construction.
- **Agent Action on Failure**: Quarantine the deficient records and build from the remainder, recording each exclusion.
- **Human Review Trigger**: More than 5 percent of active records quarantined, or any unseparable cluster whose members differ in write authority.

**Checkpoint 2: Index Completeness (After Phase 2)**

- **Automated Check**: Indexed version count equals expected minus tombstoned and quarantined; zero removed or revoked versions returned by exact-identifier or semantic canary; catalogue coverage at or above 0.99; index staleness within the freshness objective.
- **Agent Action on Pass**: Publish the atomic alias and permit retrieval against the new version.
- **Agent Action on Failure**: Withhold publication, retain the previous version, and rebuild; a revoked tool is blocked in the policy layer immediately regardless of index state.
- **Human Review Trigger**: Any non-zero deletion leakage, or catalogue coverage below 0.99 after one rebuild.

**Checkpoint 3: Query Validity (After Phase 3)**

- **Automated Check**: The capability statement names exactly one primary effect and one object; variant count is at most 4; no variant introduces a capability, permission, or destination absent from the statement; no secret or protected record appears in any variant.
- **Agent Action on Pass**: Proceed to eligibility computation and retrieval.
- **Agent Action on Failure**: Return the statement for decomposition and reject the offending variants; retrieval does not run on an invalid query.
- **Human Review Trigger**: A capability statement that cannot be expressed with one effect from the closed vocabulary after 2 decomposition attempts.

**Checkpoint 4: Exposure Validity (After Phase 4)**

- **Automated Check**: Eligibility was computed before ranking; zero denied tools appear in any pool, log, cache, or trace; exposed count is within the cap and within the partition bound; every exposed definition carries a verified digest; every exposed entry traces to a stated requirement, an always-resident justification, a live prior invocation, or a validated dependency edge.
- **Agent Action on Pass**: Serialize the exposed set and hand control to model selection.
- **Agent Action on Failure**: Halt; an exposure violating authorization or digest verification is never serialized with a warning attached.
- **Human Review Trigger**: Any denied tool appearing in any artifact, or any digest mismatch on an exposed definition.

**Checkpoint 5: Ambiguity Resolution (After Phase 5)**

- **Automated Check**: Every near-duplicate pair belongs to a recorded cluster; no cluster contributes more than 3 exposed members; every exposed clustered member carries a structured discriminating field; round, rewrite, and escalation counts are within bounds.
- **Agent Action on Pass**: Proceed to selection or to the declared terminal state.
- **Agent Action on Failure**: Withhold the members lacking discriminating fields and record the catalogue defect.
- **Human Review Trigger**: The same unseparable cluster recorded on 3 consecutive evaluation cycles.

**Checkpoint 6: Release Readiness (After Phase 6)**

- **Automated Check**: Every per-slice gate meets its floor; every zero-target gate is exactly zero; every miss is attributed to one stage; at least 30 cases per slice; baselines and ablations complete.
- **Agent Action on Pass**: Promote through the staged release sequence.
- **Agent Action on Failure**: Withhold promotion and name the failing slice, its measured value, and its miss cause distribution.
- **Human Review Trigger**: Any failing slice after 2 correction cycles, or any non-zero security escape on a critical adversarial outcome.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
CATALOG_VERSION:
INDEX_VERSION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
SLICE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Silent Retrieval Miss**

- **Symptoms**: The task fails or abstains without naming a missing capability; the model selects a poorly fitting exposed tool; execution returns a deterministic wrong-capability error; missed-tool regret rises in one slice while the aggregate figure holds.
- **Diagnostic Steps**: Replay the decision against the frozen index and the labelled case, and attribute the miss to policy exclusion, catalogue absence, stale index, lexical miss, semantic miss, fusion loss, reranker demotion, exposure cutoff, dependency miss, or query defect.
- **Resolution Protocol**: Option A, add a lexical alias or capability term where the miss was lexical. Option B, revise the purpose statement into outcome language where the miss was semantic. Option C, correct the subgoal decomposition where a dependent tool was never queried for. Option D, raise the exposure cap by a bounded step only after A through C have been measured and found insufficient.
- **Escalation Trigger**: Missed-tool regret above 0.02 in any slice escalates to owner review; a third consecutive miss on the same tool escalates to a contract rewrite rather than further text revision.

**Error Type 2: Stale Index or Removed-Tool Leakage**

- **Symptoms**: A canary query returns a revoked or removed version; the completeness manifest disagrees with the catalogue version; an approved tool is undiscoverable while its record is active; a cached result exposes a tool the policy layer denies.
- **Diagnostic Steps**: Compare the active index manifest against the catalogue change sequence, identify whether the gap is a failed refresh, a partial delta, an unpurged cache, or a retained rollback version, and measure index staleness per affected tool.
- **Resolution Protocol**: Option A, block the affected tool class in the policy layer immediately and purge every derived document, vector, edge, and cache entry. Option B, roll back to the last known-good version and serve it only for non-revoked tools within its age limit. Option C, trigger a full rebuild from the source of truth where an incremental delta cannot be proven complete.
- **Escalation Trigger**: Any non-zero deletion leakage escalates immediately and halts promotion; this class is never resolved by waiting for the next scheduled refresh.

**Error Type 3: Near-Duplicate Confusion**

- **Symptoms**: Selection accuracy conditional on retrieval falls while recall holds; the same pair of tools alternates across similar requests; a mutating tool is chosen where a read-only sibling would have sufficed; the exposed set is dominated by variants of one capability.
- **Diagnostic Steps**: Recompute the cluster from the purpose and capability documents, compare contract fields across members, and determine whether any field discriminates for the requests that failed.
- **Resolution Protocol**: Option A, add the missing discriminating field and the owner's one-sentence condition to every cluster member. Option B, cap the cluster's exposed members and apply the least-privilege preference. Option C, split or rewrite the tool contracts where no field discriminates, since an unseparable pair is a catalogue defect.
- **Escalation Trigger**: The same cluster recorded as unseparable on 3 consecutive evaluation cycles escalates to the tool owners for contract revision; further description generation is prohibited at that point.

**Error Type 4: Index Poisoning and Ranking Manipulation**

- **Symptoms**: A newly published tool wins retrieval across unrelated requests; a description contains high-frequency terms unrelated to its schema, claims to be mandatory, or references other tools; homoglyph or shadowed names appear across sources; adversarial evaluation cases show a rise in escape rate.
- **Diagnostic Steps**: Diff the record's text against its prior approved version, verify publisher authentication and digest pinning, check the field-level score contributions for a single dominating field, and re-run the adversarial ranking suite against the affected namespace.
- **Resolution Protocol**: Option A, quarantine the record, revert to its last approved version, and rebuild the affected index partition. Option B, tighten field normalization and score caps so that repeated terms cannot dominate. Option C, suspend the publisher or source server from the indexable set pending owner attestation.
- **Escalation Trigger**: Any critical adversarial outcome, defined as unauthorized exposure, unauthorized disclosure, or an action taken through a manipulated ranking, escalates immediately and fails the release; this class is never resolved by retuning ranking weights.

**Error Type 5: Authorization Leak Through Post-Filtering**

- **Symptoms**: A denied tool name appears in a log field, a cache key, a reranker input, or a trace attribute; a retrieval cache hit crosses a tenant boundary; scores are recorded for tools the principal cannot invoke.
- **Diagnostic Steps**: Trace the decision pipeline to locate the first stage at which the full catalogue was visible, and verify whether the backend enforced the tenant and entitlement predicate inside the query or only after ranking.
- **Resolution Protocol**: Option A, move the filter inside the query so that ranking never observes a denied tool. Option B, build a physically or cryptographically separate index for the boundary where the backend cannot enforce the predicate. Option C, halt retrieval for the affected boundary and serve a deterministic route until A or B is in place.
- **Escalation Trigger**: Any non-zero unauthorized exposure halts retrieval for the affected boundary immediately; this class is never resolved by redacting logs while leaving the ordering unchanged.

**Error Type 6: Cold-Start Invisibility**

- **Symptoms**: A newly published tool is never retrieved despite matching requests; ranking correlates with invocation history; the time-split evaluation partition shows materially worse recall than the tuning partition.
- **Diagnostic Steps**: Compare the new tool's retrieval documents against those of its established neighbours, and check whether any ranking component consumes usage frequency or historical success.
- **Resolution Protocol**: Option A, remove usage-derived signals from ranking, or restrict them to verified-outcome records only. Option B, require and index the owner's launch suite of at least 10 labelled requests and 3 near-neighbour negatives. Option C, grant bounded exploration in shadow and offline traffic rather than a production popularity boost.
- **Escalation Trigger**: A recall gap above 10 percentage points between the time-split partition and the tuning partition blocks promotion; the gap is never closed by adding usage weight.

**Troubleshooting Decision Tree**:

```
RETRIEVAL DECISION FAILS OR DEGRADES
├─ COVERAGE DEFECT
│   ├─ Required tool absent from exposed set → Attribute stage; correct text, alias, or decomposition
│   ├─ Some subgoals uncovered → Re-decompose; retrieve per subgoal, never one merged query
│   └─ New tool never retrieved → Remove usage-derived ranking; index the launch suite
├─ FRESHNESS DEFECT
│   ├─ Canary returns removed tool → HALT exposure; purge derived artifacts and caches
│   ├─ Approved tool missing from index → Declare degraded state; rebuild from source of truth
│   └─ Index age beyond objective → Trigger refresh; fail closed for high-risk tools
├─ AUTHORIZATION DEFECT
│   ├─ Denied tool in pool, log, or cache → HALT boundary; move filter inside the query
│   ├─ Ranking preceded eligibility → Void the decision; re-run with filtering first
│   └─ Model supplied a policy input → Reject the input; bind from trusted state only
├─ AMBIGUITY DEFECT
│   ├─ Cluster resolved by score alone → Attach discriminating fields; re-expose
│   ├─ Cluster unseparable by any field → Raise catalogue defect; split or rewrite contracts
│   └─ Cluster dominates exposed set → Apply the three-member cap and least-privilege rule
└─ INTEGRITY DEFECT
    ├─ Description carries instruction or policy claim → Quarantine record; revert to approved version
    ├─ Single field dominates ranking → Apply field normalization and score caps
    └─ Digest mismatch on exposed definition → Block that entry; rebuild the partition
```

### D. Performance Metrics and Continuous Learning

**Coverage Metrics**:

- **Retrieval hit rate at the exposure cap**: Decisions exposing at least one acceptable tool, per slice (target: at or above 0.90; below that figure, catalogue text is revised before the cap is raised).
- **Complete-set recall**: Multi-tool cases exposing every required tool (target: at or above 0.85; single-tool recall never substitutes for this figure).
- **Missed-tool regret**: Decisions in which an authorized tool that would have succeeded was never retrieved (target: at or below 0.02 per slice).
- **Catalogue coverage**: Approved active versions completely represented in the active index (target: at or above 0.99).

**Attribution and Quality Metrics**:

- **Selection accuracy conditional on retrieval**: Decisions selecting an acceptable tool when one was exposed (target: at or above 0.85; a shortfall is corrected by disambiguation, never by widening).
- **Retrieval-attributable failure rate**: Failed tasks that would pass with an oracle eligible set (target: at or below 0.05).
- **No-tool false-positive rate**: Gold no-tool cases exposing or calling a task tool (target: at or below 0.05).
- **Re-retrieval recovery rate**: Initial misses recovered within the declared bounds (target: at or above 0.60).
- **Miss attribution completeness**: Misses attributed to exactly one stage (target: 1.00; an unattributed miss blocks the release gate).

**Safety and Efficiency Metrics**:

- **Unauthorized exposure rate** and **deletion leakage rate** (target: exactly 0; either non-zero value halts retrieval or promotion).
- **Security escape rate on adversarial cases** (target: exactly 0 for critical outcomes; no aggregate gain compensates).
- **Index staleness**: Maximum and 95th percentile per risk class against the freshness objective (target: within objective for at least 99 percent of decisions).
- **Definition tokens per step**: Serialized exposed definitions against the full-catalogue baseline, using one tokenizer (target: reported per release; a reduction that costs recall is not an improvement).
- **Retrieval latency**: Reported at the 50th, 95th, and 99th percentiles per stage (target: within the declared step budget; percentiles are never averaged).

**Log-Pattern Failure Detection**: A repeated candidate-set hash across rounds indicates a query defect rather than an insufficient exposure cap. Rising exposure-cap escalations with flat recall indicate that widening is substituting for catalogue correction. A single tool appearing in the exposed set across unrelated capability statements indicates keyword dominance or poisoning. Recall holding while selection accuracy falls indicates near-duplicate confusion rather than a retrieval problem. A time-split partition trailing the tuning partition indicates cold-start suppression. Denied-tool reason codes concentrated in one namespace indicate an entitlement model that no longer matches the catalogue's structure.

**Learning and Adaptation Mechanisms**:

- **Correction at the attributed stage**: Every measured miss produces a correction at the stage it was attributed to, and a correction applied elsewhere is recorded as unvalidated.
- **Labelled-set growth from production misses**: Every production miss confirmed by owner review enters the labelled set with its slice assignment, and the hidden holdout remains untouched by that growth.
- **Description and alias revision before parameter change**: Catalogue text is corrected before retriever parameters are retuned, since text defects reappear under every retriever.
- **Threshold recalibration**: Every numeric bound is recomputed per deployment and per task class against observed outcomes; the values stated here are deployment defaults, not constants.

**Human-in-the-Loop Boundaries**: Approval of a publisher or source server into the indexable set, promotion of a configuration with a failing slice, relaxation of the authorization-before-ranking rule, an exposure cap above 12 definitions per step, and acceptance of an unseparable near-duplicate cluster carrying differing write authority are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs which capabilities become visible to a decision maker, not what any capability does. Its phases hold wherever an authorized inventory exceeds what can be presented at once, entries in that inventory change, and the consequence of omitting one is worse than the consequence of presenting one extra.

### 4.1 Cross-Domain Application Patterns

**Enterprise operations and service desks**: The catalogue aggregates many internal systems, so name collisions across sources and stale entries after a system migration are the dominant failure modes. Namespacing by owning system is mandatory, and the labelled set is weighted toward exact-identifier and alias requests, since requesters name internal systems directly. Near-duplicate clusters form around read-versus-write pairs on the same record type, and the least-privilege preference in Step 5.2 carries most of the disambiguation value.

**Clinical and care-delivery settings**: Authorization varies by care relationship, consent, and jurisdiction rather than by role alone, so the eligible catalogue changes between two requests from the same practitioner. Post-filtering is prohibited outright here because the existence of a capability can itself be disclosive. Recall floors are raised rather than relaxed, since an unretrieved capability presents as an unavailable action at the point of care, and the no-tool false-positive gate matters because an unnecessary action carries clinical cost.

**Industrial operations and field maintenance**: Health, connectivity, and physical state change faster than any index refresh, so operational state is held as a filter reading authoritative state rather than as indexed content. Freshness objectives tighten to the shorter bound, and failing closed for high-risk actuating tools is the default. The dependency graph carries real weight, since a mutating operation typically requires a prior lookup and a subsequent verification tool, and complete-set recall rather than hit rate is the governing gate.

**Regulated financial services**: Almost every consequential action is irreversible in practice, so the retrieval record becomes a deliverable rather than a diagnostic aid. Region, entitlement, and licensing dimensions dominate the eligibility filter, and the adversarial evaluation subset carries the release, since a manipulated ranking that surfaces a wrong instrument is a compliance event rather than a quality defect. Exposure caps are held at the lower end, because a smaller exposed set is easier to justify after the fact.

**Scientific and research computing**: The catalogue grows continuously with newly published methods and instruments, so cold-start invisibility is the dominant failure mode rather than staleness. Usage-derived ranking signals are removed entirely, the launch suite requirement is enforced strictly, and the time-split evaluation partition is the gate that matters. Requests are outcome-oriented and rarely name an implementation, so purpose documents in outcome language carry more recall than capability terms.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small stable catalogues**: Below 10 tools and 10,000 tokens of serialized definitions, admit the full catalogue and retain only the eligibility filter, the freshness trigger, and the labelled set. Operating a retrieval stage here adds a failure mode without a corresponding gain.
- **Large mutable catalogues**: Retain every phase, hold the exposure cap at the lower end of 5 to 12, and weight the labelled set toward near-neighbour and multi-tool slices, since both failure modes grow with catalogue size while aggregate recall can appear stable.
- **High-risk or irreversible action classes**: Raise the recall floor for the affected slice, require a separate index or an in-query predicate for the authorization boundary, fail closed on any freshness or digest defect, and prefer capability-unavailable over a lower-confidence exposure.
- **Strict latency budgets**: Shorten branch depth and disable reranking rather than removing the eligibility filter or the digest verification, since removing those removes correctness while shortening the others removes only headroom. Where latency forbids retrieval entirely, route deterministically from workflow state and record the bypass.
- **Multi-tenant deployments**: Apply the tenant boundary to lexical indexes, vector indexes, dependency edges, caches, traces, evaluation exports, and backups alike, and verify isolation by negative test rather than by configuration review. A boundary enforced only at the final query is not a boundary.
- **Multi-agent deployments**: Give each subagent an eligible catalogue scoped to its delegated purpose rather than inheriting the parent's, propagate principal, tenant, purpose, policy version, and delegation depth, and measure recall per subagent domain, since an aggregate figure across domains conceals a domain with no coverage at all.

***

## V. Limitations and Considerations

**Retrieval introduces a failure mode that full admission does not have**: A correct capability can disappear before the model ever sees it, and the benchmark evidence shows that the retrieval stage can become the binding constraint rather than the improvement, with all evaluated retrievers on a large public tool corpus reported below 52 percent Recall@10 and below 35 percent Completeness@10 [2]. The mitigation is the recall floor in Step 6.2, the per-slice measurement that prevents an aggregate figure from concealing a slice at zero coverage, and the regime rule in Step 3.1 that keeps small catalogues on full admission where retrieval would only add risk.

**Every threshold here is a deployment default rather than a measured constant**: The exposure cap of 5 to 12, the branch depth of 30 to 100, the fused pool of 20 to 50, the recall floor of 0.90, the complete-set floor of 0.85, the regret ceiling of 0.02, the 30-case slice minimum, and the round and rewrite bounds were chosen to be operable on first deployment. The vendor figures in Section 1.2 are the exception and are attributed to a retrieved source. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute every bound per task class and per model revision against observed outcomes, since selection degradation is model-specific and a model change is a re-evaluation trigger.

**Index quality is bounded by catalogue text quality**: No retriever recovers a capability whose purpose statement, parameter descriptions, and examples do not express what it does in the vocabulary a requester uses. Retuning ranking against a text defect produces a configuration that fails again on the next paraphrase. The mitigation is the correction ordering in Step 6.3, which revises text, aliases, and discriminating fields before any parameter or cap change, and the contract-rewrite escalation after 3 unsuccessful correction rounds.

**Recall is verified only against the labelled set**: A measured recall of 0.95 states that the retriever finds the required tools for the requests that were labelled, not for the requests it has never seen. Labels can also omit valid alternatives and thereby understate performance. The mitigation is the hidden holdout, the time-split partition covering tools published after the tuning window, the growth of the labelled set from owner-confirmed production misses, and the prohibition in Step 6.1 on labelling from retriever output, which would make the measurement circular.

**Learned and fine-tuned retrievers are outside this method**: Training a retrieval model on tool-specific labels is reported to improve tool retrieval materially, but training weights is not an agent-layer capability and cannot be executed by an agent following this guide. The mitigation is the agent-layer surrogate this guide specifies: multi-field retrieval documents, validated query expansion, disambiguating metadata, and fusion across branches, all of which are measurable and reversible in a way a trained retriever is not. Where a trained retriever is available, it is treated as one more branch subject to the same eligibility filter, bounds, and per-slice gates.

**Provider-hosted retrieval is not inspectable from the agent layer**: Where a host performs deferral or tool search internally, the agent cannot observe the ranking, the filter application, or the effective ordering. The mitigation is to record which regime the host applied for every request, to re-verify the effective exposed set against the eligible catalogue after the host returns it, and to treat a change in host behaviour as a release change because it can alter which tools are visible.

**Evaluation is expensive and its cost falls where budgets are tightest**: Per-slice measurement, adversarial suites, paired baselines, and repeated stochastic runs multiply evaluation cost, and deployments under schedule pressure tend to report aggregate figures. The mitigation is Checkpoint 6, which withholds promotion where any slice is below its floor or below the 30-case minimum, and reports an under-populated slice as unmeasured rather than as passing.

**Structural conformance is not retrieval correctness**: A deployment can satisfy every checkpoint here and still operate over a catalogue whose tools are wrong for the work. This framework detects a malformed retrieval mechanism, not a malformed capability inventory, and no checkpoint substitutes for owner review of whether the catalogue contains the right tools at all.

***

## VI. Conclusion and Summary

Tool retrieval is a coverage discipline before it is a ranking technique. Its purpose is not to find the most similar tool but to guarantee that the tools a step genuinely requires are present in the small set the model can see, and its correctness is therefore measured by what it fails to expose rather than by what it ranks first. The asymmetry is the whole method: an unretrieved tool ends the task, while an extra retrieved tool costs a little budget and nothing else. A deployment that internalises that asymmetry sets a recall floor, measures it per slice, and corrects the catalogue when the floor is missed. A deployment that treats retrieval as ordinary document search will optimise precision, report a healthy aggregate figure, and quietly lose the rare capabilities that matter most.

A team introducing tool retrieval should build the registry and the labelled set before choosing a retriever. Establish the canonical record and the immutable version scheme, define the eligibility filter against the real entitlement system, and build lexical and semantic baselines before adding fusion, reranking, or expansion. Measure recall per slice against a static full-catalogue baseline, since that baseline diagnoses whether retrieval helps or harms selection rather than merely whether it saves tokens. Only then add reranking, graph expansion, or adaptive bounds. Index infrastructure supplies plumbing, but none of it substitutes for an approved catalogue, a labelled set, and an authorization filter that runs first.

**Key Success Factors**:

- **Authorization before ranking**: The eligible catalogue is computed from trusted state before any score exists, and an unauthorized tool is never retrievable rather than merely unranked.
- **Recall over precision**: The operating point is set by a stated recall floor per slice, and precision is expressed as a bounded exposure cap rather than as a competing objective.
- **The index is not the catalogue**: The registry is authoritative and versioned, the index is derived and replaceable, and every exposed definition is hydrated by canonical identifier and digest-verified before serialization.
- **Indexed for retrieval, not for reading**: Purpose in outcome language, capability terms, parameter semantics, example invocations, and verified successful-use records are indexed separately, because a name and a description alone retrieve poorly.
- **Ambiguity is resolved by metadata, not by score**: Near-duplicate tools carry structured discriminating fields and an owner-supplied condition, and an unseparable pair is corrected in the catalogue rather than ranked around.
- **Measured per slice and maintained on a trigger**: Recall, completeness, and regret are reported per slice against a labelled set, and the index is refreshed on a declared trigger with removed tools verified absent by canary.

By following this guide, AI agents can hold a large and changing tool catalogue outside the context window while retaining the ability to prove, on labelled evidence, that the capabilities each step required were the ones it could see.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. The three entries marked as retrieved during conversion were fetched while this guide was being written, and the figures attributed to them in Sections 1.2 and V are reported from the pages actually retrieved.

**Corpus pointers**:

- `Production Tool Retrieval for AI Agents` — the originating prose guide from which this operational guide was derived. Source of the six-gate mental model, the canonical tool record, the multi-document indexing scheme, the lexical, dense, hybrid, reranking, hierarchy, and graph retrieval treatments, the query construction modes, the candidate budget and escalation rules, the index build and refresh loops, the security and entitlement model, the observability field inventory, the metric formulas, the evaluation and release loops, and the production readiness checklist. It carries inline citations to vendor platform documentation, protocol specifications, vector database documentation, and primary literature on tool retrieval benchmarking, tool poisoning, rank fusion, and long-context behaviour; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — the sibling owning admission of tool definitions alongside every other content type under one bounded context budget. Source of the tool loadout, deferred definition, eligibility filter, candidate pool, reason code, and missed-tool regret terminology adopted here, of the partition sizing and admission machinery this guide does not restate, and of the vendor-reported regime thresholds referenced in Section 1.2.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the umbrella guidance for the context-management category. Source of the context contract, the context budget, and the default partition table within which the tool-definition partition sits.
- `advanced_task_guides/tool-use/guide_ToolUseAndFunctionCalling.md` — the sibling owning contract-bound tool invocation under bounded authority. Governs schema validation, authorization at invocation, approval, execution, retry, and result verification, none of which retrieval performs, and holds the execution gate that this guide's exposed set never satisfies on its own.
- `advanced_task_guides/tool-use/guide_ModelContextProtocol.md` — the sibling owning governed server integration under a pinned capability contract. Governs server admission, protocol revision negotiation, pinning of reviewed definitions, detection of unapproved definition changes, per-server authority scoping, and isolation of server-supplied content as untrusted data, all of which supply the approved records this guide's catalogue and index are built from.
- `advanced_task_guides/tool-use/guide_AgentControlPlane.md` — the sibling owning fleet governance through a non-bypassable decision path. Governs identity registration, deterministic policy evaluation, budgets and quotas, routing, and fleet-scale containment; it is the authority from which the eligibility filter in Step 4.1 reads its policy and entitlement state.
- `advanced_task_guides/tool-use/guide_AgentSkills.md` — the sibling owning governed skill libraries under progressive disclosure and bounded authority. Governs skill contracts, descriptions functioning as selection criteria, admission from approved sources, trigger-based selection, and budgeted loading, which is the same progressive-disclosure discipline applied to procedural packages rather than to tool definitions.
- `advanced_task_guides/tool-use/guide_CodeExecution.md` — the sibling owning bounded execution of untrusted generated code. Governs an execution warrant gate, an isolation boundary stated as six explicit denials, default-deny egress, runtime-enforced resource bounds, reproducibility pinning, and a failure taxonomy separating program errors, timeouts, resource kills, policy denials, and infrastructure faults. A code executor is one catalogue entry this guide may expose, and its warrant gate is a separate decision from exposure.
- `advanced_task_guides/tool-use/guide_MCPToolGateway.md` — the sibling owning a shared intermediary through which many agents reach many upstream servers under central credential custody and per-principal authorization. It owns eligibility and enforcement at that hop where this guide owns ranking, and the bounded subset it exposes is this guide's mechanism applied at the gateway rather than in the client.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — companion guidance on candidate generation, indexing, and hybrid retrieval, applicable to the branch execution and fusion in Step 4.2.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — companion guidance on query formulation and rewriting, applicable to the variant construction in Step 3.2 and the bounded re-retrieval in Step 5.3.

**External references**: The numbering below is the numbering used by the inline markers in Sections I and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Retrieved and verified during conversion*

1. Anthropic, *Tool search tool* — https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool (retrieved and read during this conversion; source of the regime thresholds in Section 1.2, namely retrieval at 10 or more tools or above 10,000 tokens of definitions, selection accuracy degrading above 30 to 50 available tools, aggregation of 200 or more tools across servers, roughly 55,000 definition tokens for a five-server setup, 3 to 5 non-deferred definitions, and a default of 5 results per search)
2. *Retrieval Models Aren't Tool-Savvy: Benchmarking Tool Retrieval for Large Language Models* (ToolRet) — https://arxiv.org/html/2503.01763v1 (title and figures confirmed against the retrieved page during this conversion; 7,615 retrieval tasks over 43,215 tools, all evaluated retrievers below 35 percent Completeness@10 and under 52 percent Recall@10)
3. *RAG-MCP: Mitigating Prompt Bloat in LLM Tool Selection via Retrieval-Augmented Generation* — https://arxiv.org/abs/2505.03275 (title and figures confirmed against the retrieved abstract during this conversion; 43.13 percent against a 13.62 percent baseline, prompt tokens cut by over 50 percent)

*Tool retrieval methods and compositional retrieval*

4. Meta-Tool — https://aclanthology.org/2025.acl-long.1481.pdf
5. TOOL-REX — https://proceedings.iclr.cc/paper_files/paper/2026/file/e54a9889f1048526365ed8fb56c8c8cd-Paper-Conference.pdf
6. ToolQP — https://aclanthology.org/2026.findings-acl.2090/
7. Dependency-graph tool retrieval — https://www.arxiv.org/abs/2508.05152
8. Graph-of-Skills — https://arxiv.org/html/2604.05333v3
9. How Many Tools Should an LLM Agent See? — https://arxiv.org/abs/2605.24660
10. Lost in the Middle — https://arxiv.org/abs/2307.03172

*Retrieval and ranking mechanics*

11. Robertson and Zaragoza — https://dl.acm.org/doi/10.1561/1500000019
12. Elasticsearch, *Reciprocal rank fusion* — https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
13. Sentence Transformers, *Retrieve and rerank* — https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
14. Pinecone, *Implement multitenancy* — https://docs.pinecone.io/guides/index-data/implement-multitenancy
15. Qdrant, *Multitenancy* — https://qdrant.tech/documentation/manage-data/multitenancy/

*Platform and protocol surfaces*

16. OpenAI, *Tool search* — https://developers.openai.com/api/docs/guides/tools-tool-search
17. OpenAI, *Programmatic tool calling* — https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling
18. Claude Code MCP tool search — https://docs.anthropic.com/en/docs/claude-code/mcp
19. Model Context Protocol, *Tools specification, 2026-07-28* — https://modelcontextprotocol.io/specification/2026-07-28/server/tools
20. Model Context Protocol, *Authorization* — https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/authorization
21. Model Context Protocol, *Security best practices* — https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
22. Google, *Gemini function calling* — https://ai.google.dev/gemini-api/docs/function-calling

*Adversarial tool metadata and evaluation suites*

23. MCPTox — https://arxiv.org/abs/2508.14925
24. ToolLLM — https://arxiv.org/abs/2307.16789
25. ToolBench repository — https://github.com/openbmb/toolbench
26. StableToolBench — https://github.com/THUNLP-MT/StableToolBench
27. API-Bank — https://aclanthology.org/2023.emnlp-main.187/
28. BFCL V4 — https://gorilla.cs.berkeley.edu/leaderboard.html
29. ToolSandbox — https://arxiv.org/abs/2408.04682
30. ToolHop — https://aclanthology.org/2025.acl-long.150/
31. PlanBench-XL — https://arxiv.org/pdf/2606.22388
32. OpenTelemetry, *GenAI attributes registry* — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
