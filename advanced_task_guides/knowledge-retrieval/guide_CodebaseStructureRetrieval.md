# Codebase Structure Retrieval

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Codebase structure retrieval constitutes the task family of locating the smallest current, authorized, and semantically sufficient set of source artifacts needed to understand, change, review, or investigate a repository, using the structure the codebase actually carries rather than treating source files as undifferentiated prose. This guide provides AI agents with a structured protocol built on one organising rule: where an exact structural operation answers the question, that operation is used, and similarity search is the fallback reserved for genuinely fuzzy questions such as locating code by described behaviour when no symbol name is known. It specifies a retrieval operation inventory naming what each operation answers exactly, its preconditions, and its failure mode when those preconditions fail; a parse-failure degradation ladder, since partial parseability is the normal condition of a real repository; index freshness bounds with invalidation triggers and per-location verification, because a stale symbol index returns confidently wrong locations that are worse than no index; a context expansion rule bounded by an assembly budget; and repository scale thresholds at which the retrieval strategy itself must change. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that agents return verified locations rather than plausible guesses.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Codebase structure retrieval**: Retrieval that resolves a request against the machine-readable structure of a repository: file and module layout, symbol definitions and references, import and call relations, type signatures, tests, build metadata, and version history. It contrasts with prose retrieval, which treats a source file as a sequence of text spans and recovers relevance by lexical or vector similarity alone.

**Structural operation**: A retrieval operation whose result is determined by the code and its build configuration rather than by a similarity score. Definition lookup, reference enumeration, call-hierarchy traversal, import resolution, type-hierarchy expansion, and path-history retrieval are structural operations. Each returns an exact answer or an explicit failure, never a ranked approximation.

**Retrieval unit**: The narrowest meaningful program unit produced by parsing: a function, method, constructor, class, interface, trait, enum, module, namespace, type alias, or top-level declaration, carried together with its signature, type parameters, decorators or annotations, visibility, leading documentation, and attached comments.

**Stable symbol identifier**: A durable identifier binding a retrieval unit to its language, repository, package, container, fully qualified name, and kind, independent of the line span it occupied at any one commit. It is what permits a definition, its references, its tests, and its history to be joined.

**Snapshot identity set**: The tuple that pins a retrieval episode: repository identifier, branch or worktree identifier, indexed commit, query-time repository head, dirty-tree digest, parser and grammar versions, indexer version, and authorization-policy version. No result is admissible without it.

**Index staleness**: The distance between the indexed commit and the query-time head, measured both in commits along the relevant ancestry and in seconds since the index observed its source reference. A commit distance of zero does not excuse a modified working tree.

**Location verification**: The deterministic re-read that confirms a returned location still contains the symbol it claims, performed against the working tree at query time rather than against the index that produced the location.

**Context expansion**: The bounded enlargement of a retrieved match into an interpretable unit: the enclosing definition, its signature, its documentation, and the imports its identifiers depend on.

**Dependency closure**: The task-relative set of additional units required to interpret the primary target, comprising the types, state definitions, configuration, contracts, and called helpers whose absence would leave a material question unresolved.

**Parse state**: The recorded quality of the syntactic analysis behind a unit, drawn from a closed vocabulary: grammar-resolved, grammar-recovered, server-derived, tag-derived, span-derived, or unparsed.

**Edge provenance**: The recorded origin of a relation in the code graph, drawn from a closed vocabulary: compiler-resolved, server-resolved, syntax-derived, text-derived, history-derived, runtime-observed, or heuristic.

**Behavioural query**: A request that names an observable behaviour, concept, or intent without naming any symbol, path, literal, or identifier that exact search could match. Behavioural queries are the only class for which similarity search is the primary route.

**Repository scale class**: The band, computed from source file count and indexed symbol count, that determines which retrieval strategy and which infrastructure tier apply.

**Abstention**: A declared terminal outcome in which the agent reports that the request cannot be answered from the authorized, verifiable evidence available, naming what is missing. Abstention is a success state, not a failure.

### 1.2 The Execution Tier Partition

Codebase retrieval fails most often at the boundary between what software must resolve and what a model may judge. The partition below is binding on every phase of Section II, and every step names the tier that owns it. It adopts the tier vocabulary already used across this category.

**Deterministic tier**: Parsers, language servers, precomputed navigation indexes, lexical and trigram search engines, graph stores, version-control commands, schema validators, and budget services own everything requiring exactness, reproducibility, auditability, or scale. This tier parses source into units and assigns stable symbol identifiers; enforces principal, repository, branch, and path authorization before any search, traversal, cache lookup, or model call; resolves definitions, references, imports, call edges, and type relations; traverses the graph under hop and node bounds; computes and enforces index staleness; verifies every returned location against the working tree; performs all deduplication, ordering, token accounting, and truncation; and computes every metric reported in Sections II and III. Its results are reproducible from the snapshot identity set and the query.

**Model tier**: LLM calls own work requiring open-vocabulary judgement that no deterministic rule covers. This tier interprets an underspecified request into an explicit structural query, naming the operation and its arguments; ranks among candidates the deterministic tier has already certified as structurally valid; judges behavioural relevance where no symbol name is available; reads tests and documentation to infer intent; and drafts the explanation that accompanies the returned evidence. This tier never resolves a symbol, never enforces authorization, never computes a staleness verdict, and never declares its own output verified.

**Hybrid tier**: Work where the model proposes and software verifies, or software retrieves and the model adjudicates. Query formulation is a model proposal that a deterministic router accepts only where the named operation's preconditions hold. Similarity retrieval is a deterministic candidate generator whose output the model may rank but may not extend, and every ranked candidate must survive location verification before it enters an answer. Localization is a model hypothesis that the deterministic tier confirms by reopening the current file.

**Authority on disagreement**: The deterministic tier holds authority in every conflict, without exception. Where a model asserts a symbol lives in a file that the index resolves elsewhere, the index wins. Where a model judges a candidate relevant that the authorization filter excluded, the candidate stays excluded. Where a location fails verification, it is reported as unresolved regardless of the model's stated confidence, and the agent either re-resolves, widens the search, or abstains. Two prohibitions follow and hold everywhere in this guide: a model must never be asked to guess a symbol location that an index can resolve, and a location the index cannot verify is reported as unresolved rather than approximated.

**Tier Ownership by Artifact**:

| Artifact | Owning tier | Rejection rule enforced deterministically |
| :-- | :-- | :-- |
| Snapshot identity set | Deterministic | Any missing field blocks retrieval |
| Retrieval unit and its span | Deterministic | Unit whose parse state is unrecorded is not indexed |
| Stable symbol identifier | Deterministic | Identifier reused across commits without a mapping is rejected |
| Structural query specification | Hybrid | Operation whose preconditions fail is refused, not approximated |
| Definition, reference, and call resolution | Deterministic | Multiple candidates are all returned; a single one is never chosen |
| Edge provenance and confidence | Deterministic | Edge without provenance is not admitted to the graph |
| Similarity candidate set | Deterministic | Candidates outside the authorization scope are never generated |
| Candidate ranking among valid results | Model | Ranking may reorder the set, never extend it |
| Behavioural relevance judgement | Model | Judgement without a verified location is discarded |
| Context expansion boundary | Deterministic | Expansion beyond the cap is truncated at a grammar boundary |
| Location verification verdict | Deterministic | Unverified location is reported as unresolved |
| Assembly token budget | Deterministic | Assembly exceeding the cap is pruned before the model call |
| Answer explanation | Model | Explanation citing an unverified location is rejected |

### 1.3 The Structural Operation Inventory and the Exact-Operation-First Rule

Codebase retrieval is the clearest case in which the deterministic tier dominates. A definition lookup, a reference search, a call-graph traversal, and an import resolution are exact operations with exact answers, available from parsers, language servers, index services, and version control. Embedding similarity over code is an approximation of questions that frequently have precise answers, and a system that reaches for embeddings first has the priority backwards: it will produce agents that guess at answers a parser could have supplied exactly. The sibling guidance in this category records the same position in ladder terms, holding that where a corpus carries machine-parseable structure the structural index substitutes for the lowest retrieval rungs rather than adding to them. That framing is adopted here without modification.

**The exact-operation-first rule**: Agents must select the cheapest structural operation whose preconditions hold and whose result answers the question. Similarity search is invoked only where the request is a behavioural query, where exact keys have been extracted and returned nothing, and where the candidate set it produces will be verified against current source before use. Similarity rank is never evidence of correctness.

**Structural Operation Inventory**:

| Operation | What it answers exactly | Preconditions | Failure mode when a precondition fails |
| :-- | :-- | :-- | :-- |
| Exact literal and identifier search | Every current occurrence of a token | Readable snapshot; ignore rules applied | Returns comment, string, and namesake hits that require kind classification |
| Path and manifest lookup | Module layout, build targets, ownership | Manifests present at the pinned commit | Directory names alone misstate boundaries; build metadata governs |
| Document symbol extraction | Every declaration a file contains | File parses at some rung of the degradation ladder | Descends the ladder; symbol set becomes incomplete and is marked so |
| Definition lookup | Where a symbol is declared | Resolvable symbol; type-aware or precomputed index | Returns all candidates or unresolved; never selects one silently |
| Reference enumeration | Every site referring to a definition | Whole-project index covering all build variants | Under-reports on dynamic dispatch, reflection, and generated code |
| Import and dependency resolution | Which module a name binds to | Lockfile or resolved build graph | Falls back to text-derived edges marked low confidence |
| Call-hierarchy traversal | Incoming and outgoing calls | Compiler- or server-resolved call edges | Yields may-call sets; a single target is never asserted |
| Type-hierarchy expansion | Supertypes, subtypes, implementations | Type-aware index for the language | Refused rather than approximated by name matching |
| Structural pattern query | Sites matching a syntactic shape | Grammar coverage for the language | Silently skips unsupported files unless coverage is asserted |
| Data-flow and taint query | Whether a source reaches a sink | Build-aware whole-program database | Refused; an absent flow is never reported as proof of safety |
| Test association | Which tests exercise a symbol | Test discovery or coverage data | Falls back to naming and path heuristics, marked heuristic |
| Path history and blame | When and why a line changed | Version history at the pinned commit | Misleads after moves, copies, and bulk reformatting |
| Co-change association | Files historically changed together | History window and normalisation rules | Formatting and dependency-bump commits dominate without normalisation |
| Similarity candidate generation | Ranked units resembling a description | Embedding index at a known commit | Returns boilerplate neighbours; results are candidates only |

**Precondition failure is a first-class outcome**: An operation whose preconditions do not hold is refused and recorded, never silently degraded into a weaker operation whose result is presented with the stronger operation's authority. A reference enumeration that cannot cover all build variants reports partial coverage; it does not report a complete reference set. An absent static edge is never evidence that no runtime relation exists.

### 1.4 Repository Scale Classes and Strategy Thresholds

Strategies that work on a small repository fail on a large monorepo, and the failure is silent: the same commands return in a different order of magnitude of time, or return stale results, rather than erroring. Scale is therefore measured before a strategy is selected, and re-measured whenever a threshold is crossed.

**Scale is measured on two axes**: source file count after ignore rules, generated directories, and vendored trees are excluded; and indexed symbol count after parsing. Either axis alone crossing a boundary promotes the repository to the higher class, because a small file count with an enormous generated symbol population behaves like a large repository.

**Repository Scale Classes and Their Strategy Bindings**:

| Class | Source files | Indexed symbols | Required strategy | Threshold that forces promotion |
| :-- | :-- | :-- | :-- | :-- |
| S, small | Under 2,000 | Under 20,000 | Exact search plus direct reads; no persistent index | Cold full-repository exact scan p95 above 2 seconds |
| M, medium | 2,000 to 50,000 | 20,000 to 500,000 | Pinned parser units, symbol inventory, local lexical index, language server where reliable | Whole-repository reparse above 10 minutes, or reference enumeration p95 above 5 seconds |
| L, large | 50,000 to 1,000,000 | 500,000 to 10,000,000 | Precomputed navigation index served to workers, trigram search service, branch-scoped worktrees, incremental invalidation | Single-node index build exceeding available memory or a 60-minute build window |
| XL, monorepo | Above 1,000,000 | Above 10,000,000 | Sharded per-commit immutable artifacts, event-driven reindex with reconciliation, cross-repository symbol resolution | Not applicable; XL is terminal and adds sharding rather than changing class |

**Cost inversion at scale**: At class S the index costs more than it saves, and building one before measuring a failure is waste. At class L and above the absence of an index is disqualifying, because a full scan cannot meet an interactive latency target and a whole-repository reparse cannot keep pace with merge frequency. The strategy therefore inverts across the boundary, and an agent that carries one strategy across it will be either wasteful or wrong.

**Scale-bound budget scaling**: Retrieval budgets in Section II are stated for class M and scale as follows. Class S halves the tool-call and token budgets, because the search space is small enough that exhausting the budget indicates a misformulated query rather than a hard problem. Class L doubles the expansion node budget and holds the hop bound constant, because breadth rather than depth is what large repositories add. Class XL holds class L budgets and adds a mandatory package or build-target scope to every search, since an unscoped query at that size is refused rather than executed.

***

## II. Operational Framework: Exact-Operation-First Code Localization Under Freshness and Verification Control

Phases 1 and 2 establish the snapshot and the index and run once per repository or per index generation. Phases 3 through 5 form the per-request retrieval loop, and Phase 4 may return control to Phase 3 with a revised operation selection. Phase 6 maintains the index between requests and gates every release of a retrieval change. No phase output is admissible without the snapshot identity set fixed in Step 1.1.

### Phase 1: Snapshot Pinning, Authorization, and Scale Classification

**Objective**: Fix the repository identity, authorization boundary, and scale class before any retrieval, so every later result is attributable to a known snapshot and a known policy.

#### Step 1.1: Pin the Snapshot and Record the Identity Set

**Required Actions**:

- Obtain an authorized checkout or worktree isolated from other repositories and from other branches of the same repository.
- Record the repository identifier, branch or worktree identifier, resolved commit, submodule commits, and lockfile digests.
- Compute a dirty-tree digest over modified, added, deleted, and untracked files, and record it separately from the commit.
- Record the parser and grammar versions, indexer version, and authorization-policy version that will govern this episode.
- Reject any retrieval request that arrives without a resolvable commit, and record the rejection reason rather than defaulting to the current head.

**Required Outputs**:

- A snapshot identity set carrying all eight fields named in Section 1.1.
- A dirty-tree digest with the count and paths of modified files.
- A recorded toolchain version inventory covering parsers, indexers, and search services.

**Quality Checkpoints**:

- Every field of the snapshot identity set carries a value; a single missing field blocks retrieval.
- The dirty-tree digest is recorded even where it is empty, so that its absence is distinguishable from a clean tree.
- Branch and worktree identifiers are distinct, so a feature-branch episode cannot be attributed to the default branch.

***

#### Step 1.2: Apply the Authorization Boundary Before Any Retrieval

**Required Actions**:

- Resolve the requesting principal's permitted repositories, branches, and path patterns before the first search executes.
- Apply the authorization filter ahead of lexical search, symbol lookup, graph traversal, cache lookup, context assembly, and any model or embedding call, never after candidates have been generated.
- Partition shared indexes by repository and principal scope where post-filtering could leak candidate counts, identifiers, spans, or embedding neighbourhoods.
- Scan every artifact leaving the sandbox for credentials, and block rather than redact where a match is high confidence.
- Record a per-query denied-candidate count so that the filter's activity is observable rather than assumed.

**Required Outputs**:

- An authorization scope record naming permitted repositories, branches, and path patterns.
- A pre-filter enforcement point inventory listing each retrieval stage and the filter applied at it.
- A secret-scan verdict for the snapshot and for every assembled context.

**Quality Checkpoints**:

- No retrieval stage executes before its authorization filter; a stage without a recorded filter halts the episode.
- Cross-repository traversal is blocked where the target repository is outside the principal's scope, even where an index holds the cross-reference.
- Denied-candidate counts are recorded per query, so a filter that is silently inert is detectable.

***

#### Step 1.3: Classify Repository Scale and Bind the Strategy

**Required Actions**:

- Count source files after applying ignore rules and excluding generated directories, vendored trees, and binary artifacts.
- Count indexed symbols where an index exists, or estimate from a sampled parse of at least 200 files where it does not.
- Assign the repository to class S, M, L, or XL using the higher of the two axes, per Section 1.4.
- Bind the required strategy and the scaled budgets for that class, and record the promotion threshold that would move the repository to the next class.
- Re-measure and reclassify whenever file count or symbol count changes by more than 25 percent since the last classification.

**Required Outputs**:

- A scale classification record naming the class, both measured axes, and the governing axis.
- A bound strategy record naming the required index components and the scaled budget values.
- A recorded promotion threshold with the measurement that would trigger it.

**Quality Checkpoints**:

- Classification uses measured counts, not repository reputation or directory impressions.
- The bound strategy matches the class in Section 1.4; a class L repository served by class S strategy halts before retrieval.
- Reclassification is triggered by a recorded 25 percent drift, not by manual judgement.

***

### Phase 2: Structural Index Construction With Parse-Failure Handling

**Objective**: Produce retrieval units, a symbol inventory, and a typed relation graph in which every entry carries a parse state and every edge carries provenance, so that incompleteness is visible rather than inferred.

#### Step 2.1: Parse Source Into Syntax-Aware Units at Pinned Grammar Versions

**Required Actions**:

- Parse each supported file with a version-pinned grammar, recording the parser name and grammar version alongside every unit, since node types and query behaviour change across grammar releases.
- Create units at the narrowest meaningful declaration boundary, retaining signature, type parameters, decorators or annotations, visibility, leading documentation, and attached comments with the body.
- Retain file-level imports as a separate unit linked to every unit in the file, rather than duplicating them into each unit.
- Assign each unit a stable symbol identifier binding language, repository, package, container, fully qualified name, and kind, and record exact line and byte spans at the indexed commit.
- Split a unit exceeding 8,000 tokens at grammar-defined statement, block, member, or clause boundaries, repeating the parent identifier and signature in every child and preserving source order.

**Required Outputs**:

- A retrieval unit set with parse state, stable symbol identifier, and exact spans per unit.
- A file-level import record linked to the units it governs.
- A split record for every oversized symbol, naming parent identifier, child order, and boundary kind.

**Quality Checkpoints**:

- No unit separates a signature from its body, or a documentation block from the declaration it documents.
- Every unit carries a grammar version; units indexed under an unrecorded grammar are rejected at publication.
- No fixed-size text window is used where a grammar boundary is available, since a window destroys the symbol identity that joins definitions, references, tests, and history.

***

#### Step 2.2: Handle Partial Parseability Through the Degradation Ladder

**Required Actions**:

- Treat partial parseability as the normal condition rather than an exception, since a real repository at any moment contains files mid-edit, files in unsupported languages, generated files, and files using grammar features the pinned version does not cover.
- Descend the degradation ladder one rung at a time per file, recording the resulting parse state: grammar-resolved where the parse is clean; grammar-recovered where error recovery yields usable subtrees; server-derived where document symbols come from a language server; tag-derived where a declaration-only symbol extractor supplies them; span-derived where conservative line ranges of 40 lines either side of an exact hit, snapped to blank-line boundaries, are the only available unit; and unparsed where the file is read whole under a byte cap.
- Descend one rung where recovered error nodes cover more than 20 percent of a file's byte span, since a majority-recovered parse produces unit boundaries that cannot be trusted.
- Prohibit any absence claim from a unit at span-derived or unparsed state: such a unit may support a positive match and may never support a statement that a reference does not exist.
- Halt index publication where more than 5 percent of in-scope source files fail at the grammar rung, and report the grammar or version defect rather than publishing a silently thinned index.

**Required Outputs**:

- A per-file parse state record drawn from the six-value closed vocabulary.
- A repository-level parse coverage figure with the count of files at each rung.
- A degradation event log naming each descent, its trigger, and the resulting confidence.

**Quality Checkpoints**:

- Every file carries a parse state; an unrecorded state is treated as unparsed rather than as clean.
- No absence claim rests on a unit at span-derived or unparsed state.
- Repository parse coverage at the grammar rung is at or above 95 percent, or publication is blocked and the defect reported.

***

#### Step 2.3: Build the Symbol Inventory and the Typed Relation Graph

**Required Actions**:

- Build a symbol inventory keyed by stable identifier, carrying kind, fully qualified name, language, container, package, visibility, signature digest, generated and vendored status, and license provenance.
- Create only node and edge types that a named retrieval question requires, rather than the full schema a language could support, since unused edges carry maintenance cost and no retrieval value.
- Record for every edge its type, source and target identifiers, source span, resolver, resolver version, build variant, and one provenance value from the closed vocabulary in Section 1.1.
- Attach a calibrated confidence per edge type, and represent multiple possible targets as a may-call or may-resolve set rather than selecting one silently.
- Mark generated and vendored code with a distinct label and rank it below first-party code by default, admitting it only where the task names it, a stack frame enters it, or a local wrapper cannot explain the behaviour.

**Required Outputs**:

- A symbol inventory with all eleven attributes populated per entry.
- A typed relation graph in which every edge carries provenance, resolver identity, and confidence.
- A generated-and-vendored classification covering every indexed path.

**Quality Checkpoints**:

- No edge lacking provenance is admitted to the graph; provenance is not defaulted.
- Ambiguous resolution is represented as a candidate set of 2 or more targets, never collapsed to 1.
- The graph is treated as incomplete wherever the code uses dynamic dispatch, reflection, dependency injection, macros, code generation, or runtime patching, and this incompleteness is recorded rather than inferred by a reader.

***

### Phase 3: Query Routing Across the Structural Operation Inventory

**Objective**: Convert a request into the cheapest structural operation whose preconditions hold, reserving similarity search for behavioural queries that no exact key can address.

#### Step 3.1: Extract Exact Keys and Classify the Question

**Required Actions**:

- Extract from the request every symbol, partial symbol, module, package, file, or directory name; every stack frame, exception text, log message, protocol constant, feature flag, environment variable, route, or configuration key; and every dependency name, test identifier, issue identifier, or commit hash.
- Classify the question into exactly one of seven classes: exact-token, symbol-relational, structural-pattern, semantic-property, historical, cross-repository, or behavioural.
- Classify as behavioural only where key extraction returned zero usable keys, since a request carrying any exact key is not behavioural regardless of how it is phrased.
- Record the classification with the extracted key set, so that a misroute is attributable to the classification rather than to the operation.
- Bound classification to 1 model call and 600 planner tokens, and default to exact-token where the model returns an unusable classification.

**Required Outputs**:

- An extracted key set with each key labelled by its kind.
- A question classification drawn from the seven-value vocabulary, with a recorded rationale.
- A recorded classification cost in calls and tokens.

**Quality Checkpoints**:

- The behavioural class is assigned only where the extracted key set is empty.
- Classification consumes no more than 1 model call, so routing overhead cannot dominate the retrieval it governs.
- Every classification names the operation it selects, so an unroutable classification is visible at once.

***

#### Step 3.2: Route to the Cheapest Operation That Answers Exactly

**Required Actions**:

- Map the question class to the operation inventory in Section 1.3, selecting the cheapest operation that answers the question exactly rather than the most capable operation available.
- Confirm the selected operation's preconditions before executing it, and refuse rather than degrade where a precondition fails, recording the refusal and the missing precondition.
- Execute exact-token search first for every class except behavioural, since an identifier, path, error string, test name, or configuration key is deliberately reused across definitions and call sites and is therefore the strongest single signal code offers.
- Rank raw text matches by kind before reading any of them: definition, executable use, test, configuration, documentation, generated artifact, or noise.
- Escalate from text to symbol resolution where an identifier is overloaded, shadowed, aliased, re-exported, or generated, and to a precise query engine where the question states an invariant over syntax, types, control flow, or data flow.

**Operation Routing Table**:

| Question class | Primary operation | Escalation on ambiguity | Similarity permitted |
| :-- | :-- | :-- | :-- |
| Exact-token | Literal and identifier search | Path scoping, then symbol resolution | No |
| Symbol-relational | Definition lookup or reference enumeration | Call and type hierarchy traversal | No |
| Structural-pattern | Structural pattern query | Grammar coverage assertion, then manual scope | No |
| Semantic-property | Data-flow or taint query | Build-aware database, then targeted tests | No |
| Historical | Path history, blame, or co-change | Bisect against a repeatable predicate | No |
| Cross-repository | Manifest and lockfile resolution | External symbol resolution at the pinned version | No |
| Behavioural | Similarity candidate generation | Repository vocabulary, tests, then graph neighbours | Yes, as candidates only |

**Required Outputs**:

- A selected operation with its precondition verdict recorded.
- A kind-classified match set for every text search executed.
- A refusal record for every operation whose preconditions failed, naming the missing precondition.

**Quality Checkpoints**:

- No embedding query is issued for a question class other than behavioural.
- Every executed operation had all preconditions satisfied; a degraded substitution carrying the original operation's authority is a defect.
- Text matches are kind-classified before any file is opened, so read budget is not spent on comment and namesake hits.

***

#### Step 3.3: Execute the Similarity Fallback Only for Behavioural Queries

**Required Actions**:

- Invoke similarity retrieval only where the question class is behavioural, exact key extraction returned nothing, and repository reconnaissance has already supplied the vocabulary the repository actually uses.
- Treat every similarity result as a candidate, never as an answer, and pass the full candidate set through location verification in Step 6.2 before any of it enters an assembled context.
- Cap the candidate pool at 50 units and admit at most 10 after model ranking, since a larger pool spends assembly budget on boilerplate neighbours rather than on evidence.
- Convert every confirmed candidate into an exact key and re-enter Step 3.2, so that the remainder of the episode runs on structural operations rather than on similarity.
- Discard the similarity route and return to repository vocabulary, tests, or graph neighbours where 2 consecutive rounds return only generic utility code, framework scaffolding, or near-duplicate boilerplate.

**Required Outputs**:

- A similarity candidate set of no more than 50 units with the embedding model, revision, and index commit recorded.
- An admitted candidate set of no more than 10 units, each carrying a verification verdict.
- A converted exact-key set derived from confirmed candidates.

**Quality Checkpoints**:

- Similarity rank is never cited as evidence of correctness in any output.
- Every admitted candidate carries a passing verification verdict; unverified candidates are discarded rather than qualified.
- The route is abandoned after 2 zero-yield rounds rather than reformulated indefinitely.

***

### Phase 4: Structural Expansion and Candidate Ranking

**Objective**: Expand from confirmed locations along typed relations under hop and node bounds, and rank only among candidates the deterministic tier has already certified as structurally valid.

#### Step 4.1: Expand Symbol Relations Under a Hop and Node Bound

**Required Actions**:

- Resolve the target by stable symbol identifier, fully qualified name, language, file, and span before expanding anything.
- Expand exactly one relation type per iteration, selected by the question: definitions, references, imports, callers, callees, overrides, implementations, type hierarchy, tests, or build target.
- Bound expansion to 3 hops, 25 new nodes per hop, 100 edges total, 12 tool calls, and 12,000 retrieved tokens for a class M repository, scaling by the rules in Section 1.4.
- Suppress expansion through high-degree hub nodes such as logging utilities, serialization helpers, framework base classes, and central registries unless the task specifically concerns them, since a hub exhausts the node budget without adding task-relevant evidence.
- Label every traversed edge with its provenance and verify it against current source before the units it connects are admitted.

**Required Outputs**:

- An expansion trace naming each hop, the relation type expanded, and the nodes admitted.
- A verified edge set with provenance and confidence per edge.
- A suppressed-hub record naming each node excluded and the degree that triggered exclusion.

**Quality Checkpoints**:

- Expansion halts at 3 hops; a deeper traversal requires an explicit recorded authorisation rather than a silent extension.
- No admitted edge is unverified against current source.
- Hub suppression is recorded, so a wrongly suppressed node is recoverable rather than invisible.

***

#### Step 4.2: Rank Among Structurally Valid Candidates

**Required Actions**:

- Admit to ranking only candidates the deterministic tier has certified: resolved by a structural operation or verified after similarity generation, inside the authorization scope, and passing location verification.
- Present the ranker with the stable identifier, kind, signature, container, parse state, edge provenance, and one-line documentation for each candidate, rather than with raw bodies, so that ranking cost is bounded and comparable.
- Permit the model tier to reorder the candidate set and to judge behavioural relevance where no symbol name is available, and prohibit it from adding any candidate the deterministic tier did not supply.
- Apply deterministic priors before ranking rather than asking the model to weigh them: first-party code above vendored and generated code, definitions above uses, and tests above documentation for behavioural questions.
- Record the pre-ranking and post-ranking orders together, so that a ranking that inverts a strong structural prior is detectable in review.

**Required Outputs**:

- A certified candidate set with the certification basis recorded per entry.
- A ranked order with the pre-ranking order retained alongside it.
- A prior-application record naming which deterministic priors were applied and their effect.

**Quality Checkpoints**:

- The ranked set is a permutation of the certified set; any added member is a defect that halts the episode.
- No candidate is ranked whose location verification verdict is absent or failed.
- Model ranking operates on metadata rather than full bodies, so ranking cost stays below 15 percent of the episode's token budget.

***

#### Step 4.3: Detect Zero-Gain Iterations and Backtrack or Abstain

**Required Actions**:

- Measure information gain per iteration as at least one of: a newly verified definition, caller, test, or entrypoint; a newly discovered exact token; the elimination of a stated hypothesis; or a reduction in the plausible candidate count.
- Declare the iteration zero-gain where none of those four conditions holds, and prohibit repeating the same query, the same directory listing, or the same reformulation after 2 consecutive zero-gain iterations.
- Backtrack on a zero-gain declaration to a different evidence layer: from text to tests, from tests to history, from history to build configuration, or from graph traversal back to exact search.
- Escalate to a heavier index, a build-aware analysis, runtime observation, or a human reviewer only after the cheaper route has failed for a documented reason.
- Abstain where the named artifact does not exist at the pinned snapshot and no rename, move, or history evidence resolves it, and state what was searched rather than returning the nearest match.

**Required Outputs**:

- A per-iteration information-gain verdict with the condition that satisfied it.
- A backtracking record naming the abandoned layer and the layer entered.
- A terminal verdict of resolved, escalated, or abstained, with its supporting evidence.

**Quality Checkpoints**:

- No query is repeated after 2 consecutive zero-gain iterations.
- Every escalation names the cheaper route that failed and the reason it failed.
- Abstention states what was searched and what was missing; a nearest-match result is never returned in place of an abstention.

***

### Phase 5: Result Assembly Under a Context Budget

**Objective**: Assemble the retained units into a minimal reproducible context that is interpretable without being unbounded, preserving every signature, identifier, and span needed to trace a claim back to source.

#### Step 5.1: Apply the Context Expansion Rule to Every Retained Unit

**Required Actions**:

- Expand every retained match to its enclosing named definition, since a bare line match is not interpretable and a whole-file read is not bounded.
- Attach to each expanded unit its signature, type parameters, decorators or annotations, visibility, leading documentation, and the subset of file-level imports whose names the unit's body actually references.
- Attach one level of parent container outline, comprising the container's signature and member list without member bodies, so that the unit's position in its type is visible at bounded cost.
- Stop expansion at the parent container; a second level of ancestry is added only where a recorded uncertainty names it, since unbounded upward expansion is how assembly budgets are exhausted.
- Attach the stable symbol identifier, file path, line span, and source commit to every expanded unit, so every included line remains traceable.

**Context Expansion Rule and Its Budget**:

| Element | Included by default | Budget contribution | Omission consequence |
| :-- | :-- | :-- | :-- |
| Enclosing definition body | Yes | Counted in full | Match is uninterpretable |
| Signature and type parameters | Yes, never truncated | Under 100 tokens | Contract is invisible; a wrong call is proposed |
| Leading documentation | Yes | Capped at 300 tokens per unit | Stated intent is lost |
| Referenced file-level imports | Yes, referenced subset only | Capped at 200 tokens per file | Names resolve to the wrong module |
| Parent container outline | Yes, one level, no bodies | Capped at 400 tokens per unit | Position in the type is invisible |
| Second-level ancestry | Only on a recorded uncertainty | Capped at 400 tokens | Usually none |
| Sibling members | No | Not counted | Usually none |
| Transitive callee bodies | Only where Step 5.2 admits them | Counted in full | Behaviour cannot be traced |

**Required Outputs**:

- An expanded unit set with all five default elements attached per unit.
- A per-unit token accounting broken out by element.
- An expansion exception record naming every unit that received second-level ancestry and the uncertainty that justified it.

**Quality Checkpoints**:

- No retained match appears without its enclosing definition.
- No signature is truncated under any budget pressure; other elements are pruned first.
- Every included line is traceable to a stable identifier, path, span, and commit.

***

#### Step 5.2: Close the Dependency Set and Deduplicate

**Required Actions**:

- Add a dependency only where it resolves an explicit recorded uncertainty about a type, state definition, control-flow branch, configuration value, contract, or expected behaviour, and remove any dependency that resolves none.
- Admit the tests that encode expected behaviour for the primary target, prioritising regression tests introduced alongside the code under investigation, since tests are executable intent where production behaviour is ambiguous.
- Admit history only where intent, regression timing, or ownership is a stated part of the question, and admit it as commit metadata and diff hunks rather than as full patches.
- Deduplicate repeated imports, licence headers, generated fragments, and identical boilerplate across units, and record the duplicate bytes removed.
- Order the assembled context as snapshot identity, repository map or skeleton, primary target, direct dependencies, tests, then history, and preserve source order within any single symbol.

**Required Outputs**:

- A dependency closure with a named uncertainty attached to each admitted member.
- An ordered context manifest naming every included unit, its span, and its source commit.
- A deduplication record with duplicate bytes removed and the strategy applied.

**Quality Checkpoints**:

- Every admitted dependency names the uncertainty it resolves; unattributed dependencies are pruned.
- Same-named symbols from different files are never concatenated without explicit path and qualified-name labels.
- Context ordering is deterministic and reproducible from the manifest.

***

#### Step 5.3: Truncate at Syntax Boundaries Under the Assembly Budget

**Required Actions**:

- Cap assembled source at 24,000 tokens or 30 percent of the model context limit after reserving output and system tokens, whichever is lower, and cap included files at 25 by default for a class M repository.
- Truncate only at grammar-defined statement, block, member, or clause boundaries, never mid-expression, mid-string, or mid-macro.
- Preserve in every truncated unit the signature, stable symbol identifier, file path, line span, and an explicit omitted-range marker naming the byte range removed.
- Replace full bodies with ranked signature skeletons where the closure grows through common infrastructure, retaining full bodies only for the narrow evidence set the answer depends on.
- Restore and re-prune where truncation has removed a signature, a branch predicate, an exception path, or a test assertion, sacrificing lower-value context instead.

**Required Outputs**:

- An assembled context within the token and file caps, with utilisation recorded as a percentage.
- A truncation record listing every omitted range with its unit identifier.
- A signature-preservation verdict covering every truncated unit.

**Quality Checkpoints**:

- Assembly utilisation is at or below 100 percent of the cap; an overflowing assembly is pruned before the model call rather than passed with a warning.
- No truncation removes a signature, branch predicate, exception path, or test assertion.
- Every omitted range carries a marker, so the model tier can request restoration rather than reasoning over a silent gap.

***

### Phase 6: Freshness Maintenance and Location Verification

**Objective**: Keep the index within its staleness bound, verify every returned location against the working tree, and gate every retrieval change on evaluation over pre-fix snapshots.

#### Step 6.1: Maintain Index Freshness Within the Staleness Bound

**Required Actions**:

- Maintain separate identities for repository commit, branch, worktree, dirty overlay, parser build, symbol index, graph build, lexical index, and embedding index, and never let a feature-branch index overwrite a default-branch index.
- Enforce the staleness bound per class: index commit distance at or below 1 commit and 300 seconds for interactive navigation on classes S and M; at or below 5 commits and 900 seconds for classes L and XL. Serving beyond the bound requires either a full verification pass or an explicit staleness declaration in the answer.
- Invalidate on file change the units defined in that file, every incoming and outgoing edge of the symbols it defines, and every unit whose name resolution consumed it, rather than invalidating the file alone.
- Reparse changed ranges where range invalidation is safe, and reparse whole files where grammar state, macros, conditional compilation, build configuration, or generated inputs make range invalidation unreliable.
- Trigger a full rebuild where the change set exceeds 10,000 files, a parser or schema version changes, or a root build configuration changes, and reconcile periodically against authoritative references because change events can be delayed, reordered, or lost.

**Required Outputs**:

- A per-index identity record with its own commit, build time, and version.
- A staleness measurement in commits and in seconds per served query.
- An invalidation record naming the changed files and the derived units and edges invalidated.

**Quality Checkpoints**:

- Every served result carries a staleness measurement; an unmeasured result is treated as stale.
- Publication occurs only where all component indexes identify the same target commit and the same authorization-policy version.
- A partial build failing integrity checks twice retains the last known-good index and marks the new snapshot unavailable rather than serving a mixed state.

***

#### Step 6.2: Verify Every Returned Location Against the Working Tree

**Required Actions**:

- Verify 100 percent of the locations entering an answer, a proposed change, or a cached context; sampling is not permitted, because a stale index returns confidently wrong locations and one wrong location is enough to misdirect a change.
- Read the file at query-time head, confirm the claimed symbol name and kind appear within the recorded span, and accept a drift of up to 50 lines by re-locating the declaration within the same file.
- Re-resolve by stable symbol identifier where the declaration is absent from the file, and search the repository for a move or rename before concluding anything.
- Report the location as unresolved where re-resolution fails, and never substitute the nearest textual match, the previous location, or a similarity neighbour in its place.
- Treat a modified working tree as a separate overlay scoped to the requesting session, never merging its parses silently with the commit index, and return one of three verdicts: verified, verified with dirty overlay, or stale and material.

**Location Verification Verdicts and Their Consequences**:

| Verdict | Condition | Permitted use | Required disclosure |
| :-- | :-- | :-- | :-- |
| Verified | Symbol found at recorded span at query-time head | Any | Commit identity |
| Verified with drift | Symbol found in the same file within 50 lines | Any, with the span updated | Updated span and drift distance |
| Verified with dirty overlay | Symbol found in the modified working tree only | Session-scoped answers | Overlay status and dirty digest |
| Re-resolved | Symbol found elsewhere after move or rename detection | Any, with the new location | Old and new locations |
| Unresolved | Symbol not found at query-time head | None | Reported as unresolved with the search performed |
| Stale and material | Head advanced during the episode and affects the answer | None until re-run | Restart once, then freeze or abstain |

**Snapshot instability handling**: Where the head advances again during verification, invalidate the affected context and restart the verification once. Where the tree remains unstable across 2 restarts, freeze an immutable snapshot or abstain, and never present a result assembled across two different heads.

**Required Outputs**:

- A per-location verification verdict drawn from the six-value vocabulary.
- An updated span set for every location verified with drift or re-resolved.
- A staleness verdict for the episode as a whole, with the commit distance that produced it.

**Quality Checkpoints**:

- Verification coverage is 100 percent of locations entering an answer; partial coverage blocks the answer.
- No unresolved location is replaced by an approximation of any kind.
- No assembled context spans two different heads or silently mixes commit and overlay results.

***

#### Step 6.3: Evaluate on Pre-Fix Snapshots and Gate the Release

**Required Actions**:

- Build the evaluation set from merged, issue-linked, behaviour-changing changes, using the parent commit before each fix as the retrieval snapshot and exposing only material available at that time.
- Record gold modified files and map changed spans back to pre-fix symbols, and remove bulk formatting, vendoring, generated output, dependency-lock churn, and ambiguous multi-purpose changes from the core set or label them as separate slices.
- Evaluate exact-only, symbol-only, similarity-only, graph-only, and hybrid configurations under equal context and tool budgets, so that a claimed gain is attributable to the retrieval strategy rather than to a larger budget.
- Add hard negatives covering same-named symbols, duplicate utilities, stale branches, generated files, and neighbouring repositories outside the authorization scope.
- Split the evaluation set chronologically and by repository, allow at most 5 tuning iterations per release candidate, and change exactly 1 material component between runs.

**Required Outputs**:

- A frozen evaluation set with pre-fix snapshots, gold files, gold symbols, and labelled slices.
- A per-configuration result table covering localization, verification, budget, and end-task metrics.
- A release verdict with the gate results that produced it.

**Quality Checkpoints**:

- No evaluation task exposes material postdating its snapshot; a leak invalidates the result rather than qualifying it.
- Aggregate improvement that conceals a regression in any language, scale class, or clean-versus-dirty slice blocks release.
- A release candidate that improves no primary metric within 5 tuning iterations is rejected and the failed hypothesis recorded.

***

## III. Implementation Guidance for AI Agents

AI agents performing codebase structure retrieval must follow systematic protocols ensuring that every returned location is resolved by a structural operation, verified against current source, and traceable to a pinned snapshot. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Snapshot Agent**: Owns the snapshot identity set, the dirty-tree digest, and the toolchain version inventory. It alone may declare a snapshot pinned, and it refuses every retrieval request lacking a resolvable commit. It operates entirely in the deterministic tier.
2. **Authorization Agent**: Owns the principal scope, the pre-filter enforcement points, and the secret, licence, and injection scans. It may veto any retrieval, traversal, cache read, or model call, and its veto is not overridable by any other component.
3. **Index Agent**: Owns parsing, the degradation ladder, the symbol inventory, the relation graph, invalidation, and index publication. It operates entirely in the deterministic tier and may withhold publication where parse coverage or integrity checks fail.
4. **Routing Agent**: Interprets an underspecified request into a named structural operation with arguments. It operates in the model tier for interpretation and hands the operation to the deterministic router, which alone checks preconditions and executes. It may never resolve a symbol itself.
5. **Retrieval Executor**: Executes structural operations, expands the graph under hop and node bounds, and generates similarity candidates for behavioural queries. It operates in the deterministic tier and returns candidate sets, never answers.
6. **Verification Agent**: Reads current source, issues one of the six location verdicts per location, and computes the episode staleness verdict. It may block an answer and may not be overruled by a ranking or a confidence figure.
7. **Assembly Agent**: Applies the context expansion rule, closes dependencies, deduplicates, orders, and truncates within the budget. It operates in the deterministic tier and prunes before the model call rather than passing an overflow forward.

**Tier Handoff Rule**: Every handoff from the model tier to the deterministic tier carries a named operation and its arguments; every handoff in the reverse direction carries a certified candidate set and its verification verdicts. No handoff carries a location the receiving tier is expected to trust without a verdict.

**Workflow Execution Pattern**:

```
STATE: Structural_Query_Execution
INPUTS:
  1. Snapshot identity set from Step 1.1
  2. Authorization scope record from Step 1.2
  3. Question classification and extracted key set from Step 3.1
  4. Published index manifest from Step 2.3
ACTIONS:
  1. Map question class to the cheapest answering operation
  2. Evaluate the operation's preconditions against the index manifest
  3. Execute the operation or record a precondition refusal
  4. Classify every raw match by kind before opening any file
  5. Verify every candidate location against query-time HEAD
VALIDATION:
  - snapshot_identity_fields_present == 8
  - authorization_filter_applied_before_execution == TRUE
  - operation_preconditions_satisfied == TRUE
  - embedding_route_used == FALSE UNLESS question_class == BEHAVIOURAL
  - verification_coverage_percent == 100
  - index_staleness_within_class_bound == TRUE
TRANSITIONS:
  IF all_validations_pass AND candidates_present
     THEN next_state = Structural_Expansion
  IF all_validations_pass AND candidates_absent AND keys_remaining
     THEN next_state = Query_Reformulation
  IF question_class == BEHAVIOURAL AND exact_routes_exhausted
     THEN next_state = Similarity_Candidate_Generation
  IF verification_coverage_percent < 100 THEN next_state = Verification_Repair
  IF index_staleness_within_class_bound == FALSE
     THEN next_state = Freshness_Repair
  IF validation_failed THEN next_state = Retrieval_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended operation with its arguments, its preconditions, and its expected candidate volume without executing it; confirm the preconditions against the published index manifest while no budget is committed; execute only after that confirmation, recording the operation and its result in the same transaction.

**Approval Gate**: Human authorisation is required before any retrieval that would cross an authorization boundary the principal does not already hold; before serving a result whose index staleness exceeds the class bound by more than 10 commits or 3,600 seconds; before releasing an index configuration whose parse coverage at the grammar rung is below 95 percent; and before any episode projected to exceed 40 percent of the retrieval budget on a single expansion. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the snapshot identity set, authorization scope, and index manifest in durable state, since a retrieval episode may outlive a single context window.
- Carry forward stable symbol identifiers, spans, and verification verdicts rather than source bodies once a unit's claim has been recorded.
- Write a handoff record at every context boundary naming the pinned snapshot, the verified locations, the open hypotheses, the remaining budget, and the next operation.
- Count routing, ranking, and explanation calls toward the episode budget rather than treating model overhead as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Snapshot and Authorization Integrity (After Phase 1)**

- **Automated Check**: All 8 snapshot identity fields present; dirty-tree digest recorded; authorization filter registered at every retrieval stage; scale class assigned from measured counts.
- **Agent Action on Pass**: Proceed to index construction or, where an index exists, to query routing.
- **Agent Action on Failure**: Halt; no retrieval executes against an unpinned snapshot or an unregistered filter.
- **Human Review Trigger**: Any request whose authorization scope cannot be resolved, or any repository whose scale class changes by more than one band between consecutive classifications.

**Checkpoint 2: Index Integrity (After Phase 2)**

- **Automated Check**: Parse coverage at the grammar rung at or above 95 percent; every unit carries a parse state and a grammar version; every edge carries provenance and a resolver version; generated and vendored paths classified.
- **Agent Action on Pass**: Publish the index under a single build identity and proceed.
- **Agent Action on Failure**: Withhold publication, retain the last known-good index, and report the grammar, version, or integrity defect.
- **Human Review Trigger**: Parse coverage below 90 percent, or more than 20 percent of edges resolved as text-derived or heuristic.

**Checkpoint 3: Routing Validity (After Phase 3)**

- **Automated Check**: Exactly 1 question class assigned; the selected operation's preconditions satisfied; no embedding route used outside the behavioural class; every raw match kind-classified before a file was opened.
- **Agent Action on Pass**: Proceed to structural expansion.
- **Agent Action on Failure**: Return to key extraction with the failed precondition named; a degraded substitution is never executed under the original operation's authority.
- **Human Review Trigger**: More than 20 percent of episodes in a task class routing to the behavioural path, which indicates the repository vocabulary is not reaching the router.

**Checkpoint 4: Expansion and Ranking Validity (After Phase 4)**

- **Automated Check**: Hop count at or below 3; node and edge budgets not exceeded; the ranked set is a permutation of the certified set; every admitted edge verified against current source.
- **Agent Action on Pass**: Proceed to result assembly.
- **Agent Action on Failure**: Halt; a ranked set containing a member the deterministic tier did not certify is never assembled.
- **Human Review Trigger**: The same operation issued at 3 consecutive iterations without information gain, or hub suppression excluding a node the task explicitly named.

**Checkpoint 5: Assembly Integrity (After Phase 5)**

- **Automated Check**: Assembly within the token and file caps; every retained match carries its enclosing definition; no signature truncated; every omitted range marked; context ordering reproducible from the manifest.
- **Agent Action on Pass**: Release the assembled context to the model tier.
- **Agent Action on Failure**: Prune to the cap by removing the lowest-value context and re-run the check; an overflowing assembly is never passed forward.
- **Human Review Trigger**: Assembly requiring more than 2 pruning passes, or any pruning that removes a test assertion the question depends on.

**Checkpoint 6: Freshness and Verification (After Phase 6)**

- **Automated Check**: Verification coverage 100 percent; index staleness within the class bound; all component indexes at one commit and one policy version; no context spanning two heads.
- **Agent Action on Pass**: Release the answer with its staleness verdict and evidence manifest.
- **Agent Action on Failure**: Withhold the answer, name the unverified locations, and either re-resolve once or abstain.
- **Human Review Trigger**: Any staleness exposure served to a caller, or a verification failure rate above 5 percent across a rolling window of 100 episodes.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
SNAPSHOT_IDENTITY:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Stale Index Returning Confidently Wrong Locations**

- **Symptoms**: A returned span contains a different symbol than claimed; a definition lookup resolves to a deleted file; reference counts change materially between consecutive identical queries; a proposed change fails to apply at the named location.
- **Diagnostic Steps**: Compare the index commit against query-time head in commits and in seconds; check whether the affected files appear in the invalidation record for the intervening commits; determine whether the drift is a move, a rename, a deletion, or a missed invalidation event.
- **Resolution Protocol**: Option A, re-resolve by stable symbol identifier and re-verify, updating the span. Option B, invalidate the affected files and their dependent symbols, reindex, and re-run the query once. Option C, fall back explicitly to current lexical search over the working tree and label the result as index-unavailable rather than index-derived. Option D, abstain and report the staleness where the answer would drive an irreversible change.
- **Escalation Trigger**: Two consecutive verification failures on the same symbol escalate to a full reindex of the affected package. A verification failure rate above 5 percent across 100 episodes suspends precise navigation for the repository until the invalidation defect is found; this class is never resolved by retrying the same query.

**Error Type 2: Parse Failure and Silent Index Thinning**

- **Symptoms**: A known symbol is absent from the inventory; document symbol extraction returns far fewer declarations than the file contains; reference enumeration reports zero for a symbol that is visibly used; parse coverage falls between index builds without a corresponding source change.
- **Diagnostic Steps**: Read the file's parse state and the rung it settled at; compare grammar version against the version that last parsed the file cleanly; check whether the file uses macros, conditional compilation, code generation, or a language dialect the pinned grammar does not cover.
- **Resolution Protocol**: Option A, descend the degradation ladder one rung and re-extract, recording the reduced confidence. Option B, upgrade or replace the grammar and reindex the affected language, treating the version change as a full-rebuild trigger. Option C, exclude the file from absence claims while retaining it for positive matches. Option D, route the language to a language server or declaration-only extractor and record the coverage reduction.
- **Escalation Trigger**: Parse coverage below 90 percent at the grammar rung blocks index publication and escalates to a toolchain owner. A zero-reference result from a file at span-derived or unparsed state is never reported as an absence.

**Error Type 3: Similarity Route Invoked for an Exact Question**

- **Symptoms**: An embedding query issued for a request containing a symbol, path, or error string; results dominated by generic utility code and framework scaffolding; the returned unit resembles the request but does not contain the named identifier; near-duplicate boilerplate crowding the candidate list.
- **Diagnostic Steps**: Re-run key extraction on the original request and check whether it returned a non-empty key set; inspect the question classification and its recorded rationale; confirm whether exact search was attempted before the embedding call.
- **Resolution Protocol**: Option A, discard the similarity results, re-run exact search over the extracted keys, and re-enter routing. Option B, where keys exist but returned nothing, normalise case and naming convention, then search the tests, error construction sites, route tables, and manifest registrations before considering similarity again. Option C, where the request is genuinely behavioural, retain similarity as candidate generation only and verify every candidate before admission. Option D, tighten the classifier's behavioural condition to require an empty key set.
- **Escalation Trigger**: More than 20 percent of episodes in a task class taking the similarity route escalates the classifier for revision. A similarity result presented as an answer without a verification verdict halts the episode and is never resolved by re-ranking.

**Error Type 4: Expansion Explosion Through Hub Nodes**

- **Symptoms**: The node budget exhausts within 1 hop; the candidate set fills with logging, serialization, configuration, and base-class utilities; two consecutive expansions add no task-relevant evidence; assembled context is dominated by infrastructure unrelated to the question.
- **Diagnostic Steps**: Compute the degree of each expanded node and identify those above the repository's 99th percentile; determine whether the traversal direction was appropriate, since callers of a utility are unbounded while callees of a caller are not; check whether a package or build-target scope was applied.
- **Resolution Protocol**: Option A, suppress nodes above the degree threshold and re-expand, recording the suppression. Option B, reverse the traversal direction, expanding callees where callers exploded. Option C, apply a package or build-target scope and re-expand within it. Option D, abandon traversal and return to exact search over the tokens the first hop revealed.
- **Escalation Trigger**: Two consecutive expansions with zero information gain terminate traversal and return control to Step 3.2. Three hub suppressions in one episode escalate the degree threshold for recalibration against the repository's actual distribution.

**Error Type 5: Assembly Exceeding Budget or Losing Contract**

- **Symptoms**: Assembled tokens above the cap; a truncated signature; an omitted branch predicate or exception path; the model proposing a call that the retrieved signature does not admit; duplicate imports consuming a material share of the budget.
- **Diagnostic Steps**: Read the per-unit token accounting broken out by element and identify which element dominates; check whether the dependency closure admitted members without a named uncertainty; confirm whether deduplication ran before truncation rather than after.
- **Resolution Protocol**: Option A, replace full bodies with ranked signature skeletons for every unit outside the narrow evidence set. Option B, remove dependencies carrying no named uncertainty and re-measure. Option C, split the dominant symbol at grammar boundaries, retaining signature and parent identity in each part. Option D, reduce the file cap and re-rank, accepting a narrower closure over a truncated contract.
- **Escalation Trigger**: More than 2 pruning passes escalates to a narrower question rather than a larger budget. Any truncation removing a signature, branch predicate, exception path, or test assertion halts assembly and is restored before the model call; the budget is never exceeded to avoid making a retrieval decision.

**Error Type 6: Repository Content Treated as Instruction**

- **Symptoms**: An agent action traceable to text inside a comment, docstring, README, issue, commit message, test fixture, package manifest, or continuous-integration file; a tool invocation not derivable from the original request; a policy relaxation following a retrieval.
- **Diagnostic Steps**: Trace the action to the retrieved span that preceded it; read the injection verdict recorded for that span; determine whether retrieved content was delimited from workflow instruction in the assembled context.
- **Resolution Protocol**: Option A, discard the affected episode, restore the pre-retrieval state, and re-run with strict delimitation between trusted instruction and retrieved data. Option B, quarantine the source span and record the injection verdict against its file. Option C, route the action through the approval gate rather than executing it. Option D, restrict the tool set available during retrieval so the requested action is unavailable.
- **Escalation Trigger**: Any executed action traceable to repository content escalates immediately as a security event; this class is never resolved by retry, and no retrieval result is trusted from a snapshot with a confirmed injection until the span is quarantined.

**Troubleshooting Decision Tree**:

```
RETRIEVAL RETURNS A DOUBTFUL RESULT
├─ FRESHNESS DEFECT
│   ├─ Span holds a different symbol → Re-resolve by stable ID; update span
│   ├─ Symbol absent from file → Search for move or rename; else UNRESOLVED
│   ├─ Index behind class bound → Reindex affected files; re-run query once
│   └─ HEAD advanced mid-episode → Restart once; then freeze snapshot or abstain
├─ INDEX DEFECT
│   ├─ Parse coverage below 95 percent → Withhold publication; report grammar defect
│   ├─ Symbol missing from inventory → Descend ladder one rung; mark confidence
│   ├─ Zero references from a low-rung unit → Refuse the absence claim
│   └─ Edge without provenance → Reject the edge; do not default provenance
├─ ROUTING DEFECT
│   ├─ Embedding used with a non-empty key set → Discard; re-run exact search
│   ├─ Operation precondition unmet → Refuse and record; never degrade silently
│   └─ Ambiguous identifier over text hits → Escalate to symbol resolution
├─ EXPANSION DEFECT
│   ├─ Node budget exhausted in one hop → Suppress hubs; scope by build target
│   ├─ Two zero-gain iterations → Terminate traversal; return to exact search
│   └─ Ranked set larger than certified set → HALT; a ranker may not add members
├─ ASSEMBLY DEFECT
│   ├─ Over token cap → Prune to skeletons; never pass an overflow forward
│   ├─ Signature truncated → Restore; prune lower-value context instead
│   └─ Dependency without a named uncertainty → Remove from the closure
└─ TRUST DEFECT
    ├─ Action traceable to repository text → HALT; quarantine span; security event
    └─ Result outside authorization scope → Discard; audit the pre-filter
```

### D. Performance Metrics and Continuous Learning

**Localization and Correctness Metrics**:

- **File-level localization accuracy**: Episodes identifying every file the gold change touched (target: at least 80 percent on the class M evaluation slice).
- **Symbol-level localization accuracy**: Episodes identifying the modified or behaviourally relevant units, not merely their files (target: at least 65 percent, reported separately because file accuracy conceals symbol misses).
- **Resolution precision by edge type**: Resolved definition, reference, call, and type edges confirmed against current source (target: at least 95 percent for compiler-resolved and server-resolved edges, at least 70 percent for syntax-derived edges).
- **Absence-claim precision**: Reported non-existence findings that hold under a build-aware check (target: at least 98 percent; a false absence is the most damaging error this method produces).
- **Abstention precision**: Abstentions correct under later adjudication (target: at least 90 percent).

**Freshness and Verification Metrics**:

- **Staleness exposure rate**: Queries served with a material commit, time, or dirty-overlay mismatch (target: no more than 1 percent; above 5 percent suspends precise navigation).
- **Verification coverage**: Locations entering an answer that carry a verdict (target: 100 percent, with no permitted sampling).
- **Verification failure rate**: Verified locations returning unresolved or re-resolved (target: no more than 5 percent across a rolling window of 100 episodes).
- **Index freshness lag**: Median and 95th-percentile commit distance and seconds between a merge and its reflection in the served index (target: within the class bound from Step 6.1).
- **Parse coverage at the grammar rung**: In-scope source files parsing cleanly (target: at least 95 percent; below 90 percent blocks publication).

**Efficiency and Routing Metrics**:

- **Exact-route share**: Episodes answered without any embedding call (target: at least 80 percent, since a lower share indicates the router is reaching for similarity on questions structure could answer).
- **Tokens per correct localization**: Assembled and retrieved tokens divided by correct localizations (target: below the direct-reading baseline at matched accuracy).
- **Budget utilisation**: Assembly tokens as a share of the cap (target: 60 to 90 percent; consistently below 60 percent indicates the cap is oversized for the workload).
- **Zero-gain iteration rate**: Iterations returning no new verified evidence (target: no more than 20 percent).

**Log-Pattern Failure Detection**: Repeated identical searches indicate a reformulation loop rather than a hard question. A rising share of behavioural classifications indicates that repository vocabulary is not reaching the router. Verification failures clustered in one package indicate a missed invalidation dependency rather than a general staleness problem. Assembly consistently at the cap indicates that dependency closure is admitting members without named uncertainties. Absence claims concentrated in one language indicate that language's index is thinner than its parse coverage figure suggests.

**Learning and Adaptation Mechanisms**:

- **Threshold recalibration**: Recompute the hub degree threshold, the drift tolerance, and the class boundaries per repository from observed distributions; the values in this guide are deployment defaults, not measured constants.
- **Routing memory**: Retain question class, selected operation, outcome, and cost per episode, so the router's operation selection improves against observed history rather than against intuition.
- **Evaluation set refresh**: Add newly merged changes to the evaluation set on a fixed cadence and retire tasks whose repositories have drifted beyond recognition, so that measured gains are not gains against a frozen past.
- **Invalidation audit**: Sample verified locations against a full reindex on a fixed cadence, since an invalidation defect is silent by construction and appears only where the incremental and full indexes disagree.

**Human-in-the-Loop Boundaries**: Authorisation of cross-boundary retrieval, release of an index whose parse coverage is below the publication threshold, acceptance of an absence claim that will drive a security conclusion, and relaxation of the verification coverage requirement are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises beyond source code because its subject is any corpus carrying a machine-parseable structure whose relations are exact. Wherever a corpus has declarations, references, containment, and a version history, the exact-operation-first rule holds and similarity search remains the fallback for questions the structure cannot express.

### 4.1 Cross-Domain Application Patterns

**Software engineering and change localization**: The canonical instance. A defect report names an observable behaviour and a stack frame. Key extraction yields the frame's symbols and the error string, so the question is exact-token rather than behavioural. Exact search resolves the construction site, reference enumeration finds its callers, test association supplies the intent, and path history supplies the regression window. Similarity is never invoked. The dominant residual failure is that the matched symbol is retrieved while the surrounding contract and caller expectation are not, which is what the context expansion rule in Step 5.1 exists to prevent.

**Data engineering and schema estates**: Tables, views, columns, and jobs form a declaration and reference structure equivalent to symbols and call sites. A lineage question asks which jobs write a column, which is a reference enumeration with an exact answer, not a similarity search over query text. Preconditions differ: a resolvable catalogue replaces a resolvable build, and dynamic query construction plays the role dynamic dispatch plays in code, producing may-write sets rather than resolved edges. Freshness is measured against catalogue snapshots rather than commits.

**Infrastructure and policy estates**: Declarative configuration carries containment, reference, and inheritance relations. A question about which environments inherit a rule is a hierarchy expansion, and a question about which resources a policy grants is a structural pattern query. The parse-failure ladder is more active here than in code, because templating and generation are pervasive, so a large share of units settle at recovered or span-derived state and absence claims are correspondingly restricted.

**Legal and regulatory corpora**: Clause numbering, cross-references, defined terms, and amendment history form an exact structure. Locating every clause that references a defined term is a reference enumeration with a precise answer, and treating it as a similarity search over paraphrase produces both misses and confident false positives. The version-history operation maps to amendment tracking, and location verification maps to confirming that a cited clause number still carries the text attributed to it in the current consolidated version.

**Scientific and engineering model repositories**: Model files, parameter sets, and experiment configurations carry declarations, imports, and provenance edges. A question about which experiments consumed a parameter revision is a reference enumeration over provenance, and the freshness discipline is what prevents an answer from citing a superseded revision. The behavioural route applies where an investigator describes an observed effect without naming the component that produces it, which is precisely the case similarity search exists to serve.

### 4.2 Scale, Risk, and Latency Adaptation

- **Class S repositories**: Skip index construction entirely. Retain Phase 1, run Phase 3 with exact search over a direct checkout, and retain Phase 6 verification, which costs almost nothing when the working tree is the index. Building a persistent index here consumes more than it returns and adds a staleness surface that direct reading does not have.
- **Class L and XL repositories**: Retain every phase, require a package or build-target scope on every search, serve navigation from precomputed per-commit artifacts rather than from a live language server, and treat an unscoped query as a refusal rather than a long-running job. Double the expansion node budget and hold the hop bound, since breadth rather than depth is what scale adds.
- **Interactive latency budgets**: Shorten the expansion bound rather than removing verification, since removing verification removes the only guarantee the method offers while shortening expansion merely narrows the evidence. Where latency forbids any index lookup, fall back explicitly to lexical search over the working tree and label the result as index-unavailable.
- **High-risk and irreversible changes**: Require build-aware analysis rather than parse-only resolution before any absence claim, require an independent confirmation for every edge that carries the conclusion, and prefer abstention over an unverified completeness statement. A security conclusion resting on a syntax-derived reference set is not admissible.
- **Polyglot and monorepo estates**: Measure and report every metric per language and per scale slice, since an aggregate figure conceals the language whose grammar coverage collapsed. Rank first-party code above vendored and generated code by default, and resolve across repository boundaries only after local manifests and public interfaces prove insufficient.
- **Fast-moving repositories**: Where merge frequency outpaces the index build, do not build a heavier index. Reduce the staleness bound, widen verification, or fall back to lexical search over the working tree, since an index that cannot keep pace produces confident errors rather than slow answers.

***

## V. Limitations and Considerations

**Static analysis is structurally incomplete**: Dynamic dispatch, reflection, dynamic imports, dependency injection, service locators, macros, templates, conditional compilation, code generation, runtime patching, foreign-function interfaces, remote calls, and framework conventions all create relations that no static index resolves. The consequence is that a reference or call set is a lower bound and never a complete enumeration. The mitigation is the provenance vocabulary in Step 2.3, the may-call representation that forbids silently selecting one target, and the prohibition in Step 2.2 on absence claims from low-rung units; where an unresolved relation could change a patch or a security conclusion, Section III.D routes the question to build-aware analysis, targeted tests, runtime observation, or human review.

**Freshness cannot be guaranteed, only bounded**: Change events are delayed, reordered, and lost; hooks fail; and a working tree can change during an episode. The consequence is that some served result will at some point be stale. The mitigation is that staleness is measured rather than assumed, bounded per scale class, and made irrelevant to correctness by the requirement that 100 percent of locations entering an answer are verified against the working tree at query time, so a stale index costs latency rather than accuracy.

**Verification cost scales with answer breadth**: Verifying every location is affordable for a ten-location answer and expensive for a thousand-location one. The consequence is that broad enumeration questions carry a verification cost proportional to their result size, which can dominate the episode. The mitigation is to narrow the question rather than to sample the verification: an enumeration too large to verify is reported with its unverified count and its scope, and the caller is offered a narrowed query rather than a partially checked list.

**Numeric thresholds here are deployment defaults**: The scale class boundaries, the 95 percent parse coverage gate, the 50-line drift tolerance, the 3-hop and 25-node expansion bounds, the 24,000-token assembly cap, the 20 percent error-node descent trigger, and the staleness bounds were chosen to be operable on first deployment rather than derived from a measured universal property. Several are transcribed from the originating prose source, which presented them as starting points. The consequence is that a deployment adopting them unmodified will be wrong for its repositories in some direction. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute them from observed distributions and to treat the defaults as an initialisation.

**Localization accuracy is measured against historical patches**: An evaluation set built from merged changes scores a system against the location a human chose, and a valid alternative localization scores as a miss. The consequence is that measured accuracy understates capability by an unknown margin. The mitigation is the manual adjudication of a sample of apparent false positives required in Step 6.3, together with the chronological and per-repository splits that detect memorisation.

**Repository content is untrusted input**: Comments, documentation, issues, commit messages, test fixtures, package metadata, and continuous-integration configuration are text an agent retrieves and may be authored to manipulate it. The consequence is that retrieval itself is an attack surface, and retrieval augmentation does not remove it. The mitigation is the delimitation requirement in Section III.A, the injection verdict recorded per span, the least-privilege tool set during retrieval, and the escalation in Error Type 6 that treats any executed action traceable to repository content as a security event rather than a defect.

**Index construction has its own exposure and cost**: An index rich enough to answer navigation questions contains identifiers, spans, and sometimes content from every file it covers, and it must be authorised and scanned as carefully as the source. The consequence is that a shared index is a disclosure surface even where every individual query is authorised. The mitigation is the pre-filter enforcement in Step 1.2, partitioning by principal scope where post-filtering would leak counts or neighbourhoods, and the cost inversion rule in Section 1.4 that forbids building an index a repository's scale does not justify.

**Structural conformance is not correct localization**: An episode can satisfy every checkpoint here, pin its snapshot, verify every location, and still return the wrong region of a codebase because the question was misunderstood. The framework detects malformed retrieval, not misdirected intent, and no checkpoint substitutes for a caller confirming that the returned evidence answers the question actually asked.

***

## VI. Conclusion and Summary

Codebase structure retrieval is a resolution discipline before it is a search technique. A repository is not a corpus of prose that happens to be written in a programming language; it is a structure with declarations, references, containment, dispatch, types, tests, and a version history, and most questions asked of it have exact answers that a parser, a language server, an index, or a version-control command can supply. The organising rule follows directly: where an exact structural operation answers the question, that operation is used, and similarity search is reserved for the narrow class of behavioural questions that name a concept and no identifier. A system that reaches for embeddings first has inverted the priority and will return plausible neighbours where a definition lookup would have returned the answer.

Two disciplines make the exactness real rather than nominal. The first is freshness: an index that has fallen behind returns confidently wrong locations, which is a worse failure than having no index at all, because a wrong location is acted upon while a missing one is investigated. Bounding staleness and verifying every returned location against the working tree at query time converts a stale index from a correctness problem into a latency problem. The second is honest incompleteness: dynamic dispatch, reflection, generation, and runtime patching guarantee that no static relation set is complete, so provenance is recorded per edge, ambiguity is represented as a candidate set rather than resolved silently, and an absence claim is refused wherever the analysis cannot support it.

A team adopting this method should begin at the smallest tier its repository scale permits. Pin the snapshot, apply authorization before retrieval rather than after, and run exact search with direct reading. Measure where that fails, and add only the index component the measured failure names: a parser where text windows split definitions, a symbol index where namesakes and aliases cause misresolution, a precomputed navigation index where latency forces it, and an embedding index only after conceptual-query evaluation demonstrates recall beyond the lexical and symbolic baselines. Verification and snapshot pinning are the two disciplines that belong at every tier, including the smallest.

**Key Success Factors**:

- **Exact operations before similarity**: A definition, reference, import, or call question is answered by the operation that resolves it, and similarity search is the fallback for behavioural questions alone, never the default route.
- **Verified locations only**: Every location entering an answer is confirmed against the working tree at query time, and a location that cannot be verified is reported as unresolved rather than approximated by the nearest match.
- **Bounded, measured freshness**: Index staleness is measured in commits and in seconds against a class-bound target, invalidation follows the dependency rather than the file, and no result is served without its staleness verdict.
- **Visible incompleteness**: Parse state and edge provenance are recorded per unit and per edge, ambiguity is represented rather than resolved silently, and absence is never claimed from an analysis that cannot support it.
- **Interpretable context under a budget**: Every match arrives inside its enclosing definition with its signature, documentation, and referenced imports, and truncation falls on lower-value context before it falls on a signature, a predicate, or an assertion.
- **Scale-bound strategy**: The retrieval strategy and its budgets are selected from measured file and symbol counts, and the strategy that suits a small repository is recognised as disqualifying on a monorepo rather than carried across the boundary.

By following this guide, AI agents can localise code by resolving the structure a repository actually carries, return evidence that is current and traceable to a pinned snapshot, and abstain in the declared cases rather than substituting a confident approximation for an answer a parser could have given exactly.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Bounded searches performed during conversion confirmed four positions in the source as current practice: that a version-pinned incremental parser produces a concrete syntax tree with error recovery rather than a resolved semantic model; that lexical and symbol-index routes remain competitive with or superior to embedding retrieval for code localization under agent harnesses; that the precomputed navigation format has succeeded its predecessor while the predecessor remains specified for legacy consumers; and that incremental invalidation proportional to the change set rather than to repository size is the operative technique at monorepo scale. One entry was verified individually and is marked as such. Those searches did not re-verify any other entry below.

**Corpus pointers**:

- `Structure-Aware Codebase Retrieval Guide` — the originating prose guide from which this operational guide was derived. Source of the exact-search-first decision rule, the infrastructure tiers and their upgrade criteria, the repository reconnaissance inventory, the syntax-aware unit rules and oversized-symbol handling, the language-server and index-based navigation guidance, the code-graph schema with edge provenance and static-analysis limits, the precise-query and version-history retrieval sources, the multi-repository resolution sequence, the eight bounded navigation loops with their entry conditions, budgets, backtracking rules, and exits, the context assembly rules, the staleness and incremental indexing discipline, the security and governance requirements, the evaluation metric families and internal harness construction, the five-level observability field inventory, and the seventeen-step end-to-end workflow. It carries inline citations to parser, protocol, indexer, analysis, benchmark, and security sources; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — the category's architecture-selection guide. Source of the execution tier vocabulary adopted in Section 1.2, of the structured-corpus position that a structural index substitutes for the lowest retrieval rungs rather than adding to them, and of the failure taxonomy whose utilisation class the context expansion rule in Step 5.1 addresses.
- `advanced_task_guides/knowledge-retrieval/guide_GraphRAG.md` — companion guidance on graph index construction, provenance, and traversal bounding, applicable to the relation graph built in Step 2.3 and expanded in Step 4.1.
- `advanced_task_guides/knowledge-retrieval/guide_HierarchicalIndexRetrieval.md` — companion guidance on parent-child expansion and level routing, applicable to the container outline and expansion caps in Step 5.1.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — companion guidance on bounded retrieval loops and evidence-gain budgets, applicable to the zero-gain detection and backtracking in Step 4.3.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — companion guidance on diagnosing and reformulating an underspecified request, applicable to key extraction and question classification in Step 3.1.
- `advanced_task_guides/knowledge-retrieval/guide_CorrectiveRAG.md` — companion guidance on verdict-gated correction of insufficient evidence, applicable to the verification verdicts and their consequences in Step 6.2.
- `advanced_task_guides/knowledge-retrieval/guide_SelfRAG.md` — companion guidance on critique-gated generation, applicable to the prohibition on presenting an unverified location as an answer.
- `advanced_task_guides/knowledge-retrieval/guide_ModularRAG.md` — companion guidance on independently replaceable retrieval stages, applicable to the operation routing table in Step 3.2.
- `advanced_task_guides/knowledge-retrieval/guide_DeepResearchAgent.md` — companion guidance on long-horizon investigation under budget control, applicable to multi-episode localization across a large estate.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops, stuck-state detection, and stopping rules, applicable to the zero-gain and abstention rules in Step 4.3.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the trace and metric instrumentation in Section III.D.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring under constraint, applicable to the freshness lag and verification failure monitoring in Step 6.1.
- `advanced_task_guides/policy-risk/guide_InformationDependencyDisclosureRiskAnalysis.md` — companion guidance on disclosure exposure, applicable to the pre-retrieval authorization and index partitioning requirements in Step 1.2.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on edge-level provenance, applicable to the closed provenance vocabulary required of every edge in Step 2.3.
- `advanced_task_guides/knowledge-graphs/guide_KG_ScalabilityArch.md` — companion guidance on graph scalability, applicable to the repository scale classes and their strategy bindings in Section 1.4.

**External references**: The entries below are transcribed from the originating prose guide's inline citations and its source list, and are retained for auditability. Titles are reproduced as the source carried them and are not expanded. This guide carries no inline numeric markers; the grouping is thematic.

*Parsers and syntax-aware units*

1. Tree-sitter, *Introduction* — https://tree-sitter.github.io/tree-sitter/
2. Tree-sitter, *Advanced Parsing* — https://tree-sitter.github.io/tree-sitter/using-parsers/3-advanced-parsing.html

*Navigation protocols and precomputed index formats*

3. Microsoft, *Language Server Protocol 3.17* — https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/
4. Microsoft, *LSIF 0.6.0* — https://microsoft.github.io/language-server-protocol/specifications/lsif/0.6.0/specification/
5. Sourcegraph, *SCIP repository* — https://github.com/sourcegraph/scip
6. Sourcegraph, *SCIP announcement* — https://sourcegraph.com/blog/announcing-scip
7. Sourcegraph, *Code Navigation* — https://sourcegraph.com/docs/code-search/code-navigation
8. Sourcegraph, *Precise Code Navigation* — https://sourcegraph.com/docs/code-navigation/precise-code-navigation

*Exact and lexical search*

9. Sourcegraph, *Zoekt* — https://github.com/sourcegraph/zoekt
10. *ripgrep Guide* — https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md

*Language servers and symbol extractors*

11. *clangd indexing* — https://clangd.llvm.org/design/indexing
12. *clangd configuration* — https://clangd.llvm.org/config
13. *rust-analyzer manual* — https://rust-analyzer.github.io/book/
14. *gopls documentation* — https://go.dev/gopls/
15. *Pyright documentation* — https://microsoft.github.io/pyright/
16. *Universal Ctags documentation* — https://docs.ctags.io/en/latest/
17. *GNU GLOBAL* — https://www.gnu.org/software/global/

*Precise queries and semantic code graphs*

18. *CodeQL documentation* — https://codeql.github.com/docs/
19. *Semgrep documentation* — https://semgrep.dev/docs/
20. *An Overview of Kythe* — https://kythe.io/docs/kythe-overview.html
21. Meta, *Glean announcement* — https://engineering.fb.com/2024/12/19/developer-tools/glean-open-source-code-indexing/
22. *Glean repository* — https://github.com/facebookincubator/Glean
23. *Stack Graphs repository* — https://github.com/github/stack-graphs (verified during conversion: the repository was archived on 9 September 2025 and is read-only, which is the maintenance risk the source names)

*Repository maps and coding agents*

24. *Aider repository map* — https://aider.chat/docs/repomap.html
25. *AutoCodeRover* — https://arxiv.org/abs/2404.05427
26. *LocAgent* — https://arxiv.org/abs/2503.09089
27. *SWE-agent* — https://arxiv.org/abs/2405.15793
28. *Agentless* — https://arxiv.org/abs/2407.01489
29. *Inside the Scaffold* — https://arxiv.org/abs/2604.03515

*Code retrieval research*

30. *Is Grep All You Need? How Agent Harnesses Reshape Agentic Search* — https://arxiv.org/abs/2605.15184
31. *CodeSearchNet Challenge* — https://arxiv.org/abs/1909.09436
32. *CoIR* — https://arxiv.org/abs/2407.02883
33. *CodeRAG-Bench* — https://code-rag-bench.github.io/

*Benchmarks*

34. *SWE-bench* — https://www.swebench.com/
35. *SWE-bench Original* — https://www.swebench.com/original.html
36. *SWE-bench Verified* — https://www.swebench.com/verified.html
37. *SWE-bench Multimodal* — https://www.swebench.com/multimodal.html
38. *paper by John Yang and colleagues* — https://arxiv.org/abs/2410.03859
39. *SWE-bench Multilingual* — https://www.swebench.com/multilingual.html
40. *Multi-SWE-bench* — https://arxiv.org/abs/2504.02605
41. *SWE-Lancer* — https://arxiv.org/abs/2502.12115
42. *RepoBench* — https://arxiv.org/abs/2306.03091
43. *Long Code Arena* — https://arxiv.org/abs/2406.11612

*Version control and repository governance*

44. *Git blame* — https://git-scm.com/docs/git-blame
45. *Git bisect* — https://git-scm.com/docs/git-bisect
46. GitHub, *CODEOWNERS documentation* — https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
47. GitHub, *linked pull requests and issues* — https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue

*Security, licensing, and supply-chain provenance*

48. GitHub, *fine-grained token permissions* — https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens
49. GitHub, *secret scanning* — https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning
50. OWASP, *LLM01:2025 Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
51. *SPDX License List* — https://spdx.org/licenses/
52. *SPDX 3.0.1 specification* — https://spdx.github.io/spdx-spec/v3.0.1/
53. *SLSA threats overview* — https://slsa.dev/spec/v1.2/threats-overview
