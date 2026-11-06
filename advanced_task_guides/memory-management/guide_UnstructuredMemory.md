# Unstructured Agent Memory

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Unstructured agent memory constitutes the task family of storing free-form content that no schema constrains, and retrieving it by approximate similarity rather than by exact predicate. Its contents are notes, transcript passages, document fragments, summaries, observations, captions, and self-authored instruction files whose bodies remain natural language or native media. This guide provides AI agents with a structured protocol for admitting such content under a governed metadata envelope, chunking it without severing a claim from its qualifier, embedding and indexing it under a pinned model version, collapsing near-duplicates without laundering a material difference, retrieving it under eligibility filters applied before ranking, and invalidating, compacting, and deleting it with verification. It specifies the selection rule that decides whether a memory belongs in a free-form store or a typed one, the promotion path by which a record with stable fields leaves the free-form store, four decay modes with numeric detection triggers, and an execution tier partition assigning chunking, hashing, clustering, index maintenance, and retention enforcement to deterministic software while reserving summarization, salience judgement, semantic deduplication, and contradiction detection for model inference under deterministic gates.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Unstructured memory**: Durable agent memory whose body is free-form natural language or native media, carrying no enforced content schema that dictates which claims or fields the body must contain. The body is unconstrained; the envelope around it is not.

**Governed envelope**: The structured metadata attached to every unstructured record, covering identity, version, scope, purpose, audience, source, authority, sensitivity, validity time, and lifecycle state. The envelope is the enforcement surface; the body is the evidence.

**Record**: One logical memory, identified by a stable identifier and materialised as an ordered series of immutable versions. A record is edited by appending a version, never by overwriting a body.

**Chunk**: A derived retrieval unit produced by splitting a record body, carrying exact offsets back into an immutable source version. A chunk is addressable and rankable; it is not an independent truth and is never cited without its source pointer.

**Representation**: A vector or lexical posting derived from a chunk, bound to a named model identifier and an immutable model revision. Representations produced by different revisions are not comparable.

**Index generation**: A monotonically numbered build of a lexical or vector index, pinned to exactly one embedding revision, one analyzer configuration, and one metadata filter schema version. Serving traffic addresses a generation through an alias.

**Eligibility**: The property of a record being permitted for a given request, determined by tenant, principal, subject, purpose, audience scope, sensitivity, validity time, and deletion state. Eligibility is evaluated before relevance; a similar but ineligible result is a defect, not a partial success.

**Assertion mode**: A closed-vocabulary label recording how a body relates to its evidence, drawn from quotation, direct statement, observation, inference, paraphrase, summary, and reflection. It prevents a derived body from acquiring the authority of its inputs.

**Author type**: A closed-vocabulary label recording who produced a body, drawn from user, human operator, external publisher, tool, agent, and summarizer. Agent-authored bodies carry proposal status until corroborated outside their own descendant chain.

**Near-duplicate cluster**: A set of records or chunks whose pairwise similarity exceeds the near-duplicate threshold, holding one canonical member and zero or more occurrence links. A cluster is a retrieval unit and a governance unit; its members are never independently counted as corroboration.

**Material difference span**: A character range in which two candidate duplicates disagree on a qualifier, quantity, negation, time, scope, or attribution. The presence of one material difference span blocks a merge.

**Derivative depth**: The number of transformation hops separating a body from a primary source, incremented by each summarization, caption, transcription, or translation. Depth bounds the distance error can travel before a source-grounded rebuild is required.

**Canonical source**: The immutable stored original, or a lawful immutable pointer to it, from which every chunk, representation, caption, transcript, and summary is rebuildable. Deletion of a canonical source obliges deletion or invalidation of every descendant.

**Tombstone**: A durable deletion marker consulted at serving time, committed before physical removal begins, so a record stops being retrievable in advance of its copies being purged.

### 1.2 The Representation Selection Rule and the Promotion Path

Unstructured memory is the default landing place for observation, because observation arrives as language before a stable ontology exists. It is not the default resting place. A companion structured store holds records whose fields are stable, and the two stores must not silently duplicate one another.

**The selection rule**: A memory belongs in the unstructured store where the content has no stable schema, where wording, hedging, narrative, modality, or unresolved disagreement carries value, and where future questions are open-ended. A memory belongs in a typed store where the content is a stable attribute, a constraint, a permission, a monetary value, a unit-bearing quantity, an exact validity interval, or an input to an aggregate or a join. Where both descriptions fit, the memory is written to the unstructured store and a typed projection is derived from it, with the projection carrying an evidence pointer back to the source span.

**Cost of the choice**: The unstructured store accepts unforeseen facts without migration and pays for that in four currencies. Retrieval is approximate, so recall carries no completeness guarantee. Correctness is unverifiable by constraint, so no schema check catches a reversed negation or a swapped unit. Uniqueness is unenforced, so the same fact accumulates in many wordings. Erasure is diffuse, so one transcript propagates into chunks, vectors, captions, summaries, caches, and evaluations that must each be reached.

**Representation Selection Matrix**:

| Content property | Store | Retrieval mode | Verification available |
| :-- | :-- | :-- | :-- |
| No stable field set; wording is evidence | Unstructured | Approximate similarity | Source span comparison only |
| Stable attribute, permission, or quantity | Typed | Exact predicate | Schema and constraint checks |
| Sequence of action, observation, and outcome | Episodic | Trajectory replay | Event trace reconstruction |
| Durable identity and relationship traversal | Graph | Path query | Cardinality and type constraints |
| Bounded, low-reuse, order-sensitive material | Working context | Direct inclusion | None; content is transient |

**The promotion path**: An unstructured record is promoted to a typed record when it satisfies all four promotion conditions. First, the same field set is extractable from at least 5 distinct records with no field-level disagreement. Second, at least 3 distinct requests in the observed workload required an exact predicate, an aggregate, or a join over that field set. Third, an extraction pass over a held-out sample achieves at least 95 percent field-level agreement with human labels. Fourth, a named owner accepts the typed schema and its update path. Promotion writes the typed record, retains the unstructured record as the evidence body, and links the two by identifier. Promotion never deletes the source body, because the typed projection preserves the fields and discards the qualifiers.

**The demotion condition**: A typed field whose extraction agreement falls below 90 percent across two consecutive review cycles is demoted, meaning the typed projection is withdrawn and the field is answered from the unstructured body until agreement recovers. Serving a typed field at low agreement is worse than serving prose, because the typed answer carries an unearned appearance of exactness.

### 1.3 The Four Decay Modes

An unstructured store degrades in production along four paths. Each is detectable by measurement, each carries a numeric trigger, and each has a remedy that must be scheduled rather than improvised.

**Near-duplicate accumulation**: The same fact is written many times in slightly different words, and the resulting cluster dominates retrieval by sheer count rather than by authority. Detection compares chunk pairs by MinHash over 5-gram shingles and reports estimated Jaccard similarity. Trigger: any cluster whose members occupy more than 30 percent of a top-20 result set, or any cluster exceeding 5 members carrying no material difference span, or a store-wide near-duplicate rate above 15 percent of chunks at estimated Jaccard 0.80 or above. Remedy: collapse the cluster to one canonical member with occurrence links, apply a per-cluster retrieval cap of 2 members, and route the admission policy that produced the cluster to recalibration.

**Silent staleness**: Content remains retrievable long after it stopped being true, because no schema exists against which to check it and prose carries no visible expiry. Detection compares each record's last verification timestamp against a volatility class horizon, and cross-checks new writes against existing records on the same subject for implicit supersession. Trigger: any record past its verification horizon by more than 100 percent of the horizon length, any subject whose records disagree on a current-state claim, or a stale-answer rate above 5 percent on a time-shifted evaluation slice. Remedy: demote retrieval weight to at most 0.5 of nominal at the horizon, mark the record as requiring revalidation before it may support an action, and surface the age with every returned span.

**Boundary severance**: A chunk boundary splits a claim from its qualifier, so retrieval returns a fragment whose meaning is reversed or unconditioned relative to the source. A negation, an exception clause, a scope restriction, or an attribution left on the far side of a boundary is the common form. Detection samples chunks and tests whether the chunk alone answers its own claim without contradicting the source passage. Trigger: a severance rate above 2 percent of sampled chunks, or an answer-span containment rate below 95 percent on the labelled corpus. Remedy: re-chunk on natural boundaries, expand to neighbouring chunks at retrieval time, prepend a generated context header, and reject as non-self-contained any chunk whose referents cannot be resolved from lawful local context.

**Embedding version drift**: Part of a corpus is re-embedded under a new model revision while the remainder is not, and the two populations are scored against one another as though their distances were comparable. Detection compares the embedding revision recorded on every representation against the revision pinned to the index generation serving it. Trigger: any non-zero count of representations whose recorded revision differs from the generation's pinned revision, or coverage below 100 percent of eligible records in a generation being promoted. Remedy: block the mixed generation from serving, complete the migration into a separate generation built from a canonical snapshot, and switch the serving alias atomically only after coverage and evaluation gates pass.

### 1.4 Execution Tier Partition

Every operation in this framework is owned by exactly one tier, and every handoff between tiers is named. The partition is the difference between a store that degrades predictably and one that degrades invisibly.

**Deterministic tier**: Owns chunking execution against declared boundary rules; content hashing and fingerprint computation; near-duplicate clustering by threshold; offset, checksum, and lineage bookkeeping; index construction, generation numbering, and alias switching; embedding version pinning and coverage accounting; eligibility filtering; rank fusion; retention timer evaluation; tombstone commitment; and deletion verification across every derivative. This tier rejects any write lacking a complete envelope, any chunk lacking valid offsets into an existing source version, any representation whose embedding revision differs from the target generation's pinned revision, any merge lacking a preserved provenance record, and any retrieval whose eligibility predicates were evaluated after ranking rather than before.

**Model tier**: Owns summarization and compaction; salience and future-utility judgement at admission; atomic note rewriting; context header generation; semantic deduplication where lexical fingerprints fail to separate a paraphrase from an independent observation; contradiction and supersession detection between records on the same subject; and interpretation of ambiguous retrieval results. This tier is never permitted to decide alone that content may be deleted, that a merge may be applied, that a record's authority may be raised, that an eligibility predicate may be relaxed, or that a tool action is authorised by remembered text.

**Hybrid tier**: Covers the operations where a model proposes and software disposes. The model proposes a merge; the deterministic gate applies it only where the proposal carries zero material difference spans, both members share a compatible scope, and a provenance record naming every merged version is written in the same transaction. The model proposes an invalidation; the gate applies it only where the superseding record carries equal or greater source authority, an overlapping validity interval, and a preserved copy of the invalidated version. The model proposes a summary; the gate publishes it only where answer-preservation and factual-consistency thresholds pass. In every disagreement, the deterministic tier holds authority: a model proposal that fails a gate is recorded with its reason code and discarded, never applied with a warning attached.

***

## II. Operational Framework: Governed Free-Form Memory From Admission to Verified Deletion

The framework assumes a canonical store, an object store for native evidence, at least one lexical index, and a labelled evaluation corpus already exist. Phases 1 through 3 run on the write path, Phase 4 runs on both the write and maintenance paths, Phase 5 runs on the read path, and Phase 6 runs continuously and gates every deletion. No phase may be skipped for a record that reaches broad retrieval; a record admitted without a complete envelope is quarantined rather than served.

### Phase 1: Content Admission and Note Construction

**Objective**: Decide what enters durable memory, in what wording, and under what envelope, so that the store grows by admitted evidence rather than by accumulated transcript.

#### Step 1.1: Score the Candidate Against the Admission Policy

**Required Actions**:

- Score every candidate separately on remember intent, future utility, novelty, decision impact, source authority, stated confidence, recurrence, volatility, sensitivity, reconstructability from other sources, and expected storage and review cost.
- Reject candidates whose expected reuse does not justify their retention risk, including greetings, acknowledgements, repeated filler, transient drafting exchanges, abandoned guesses, and secrets with no allowed processing purpose.
- Record the admission decision, every component score, the policy version, and reason codes for both acceptance and rejection.
- Attach delayed labels to each admitted record once observed, covering later retrieval, use in an answer, adjudicated usefulness, adjudicated harm, correction within the review window, and user-requested deletion.
- Recalibrate component weights against delayed labels at least once per 30 days or once per 1,000 admitted records, whichever comes first.

**Required Outputs**:

- An admission decision record per candidate, carrying component scores, policy version, and reason codes.
- A rejection log carrying the same fields, retained so write recall remains computable.
- A calibration report stating write precision, write recall, and the correlation between salience score and realised use.

**Quality Checkpoints**:

- Write precision, measured as adjudicated-useful records over admitted records, is at least 0.70; a lower value halts broad admission and routes the policy to recalibration.
- Write recall, measured as admitted useful candidates over all useful candidates, is at least 0.60; a lower value indicates the policy is discarding evidence the workload needs.
- Every rejection carries a reason code, because an unlogged rejection makes write recall uncomputable.
- Salience is never treated as a truth score or a permission score; admission never raises a record's authority.

***

#### Step 1.2: Construct an Atomic, Self-Contained Note

**Required Actions**:

- Preserve verbatim wording where exact phrasing, attribution, legal meaning, a commitment, a requirement, a correction, a disputed claim, or an unusual formulation is likely to matter.
- Paraphrase only where the source is repetitive, the wording carries no independent value, and the shorter body retains subject, time, qualifiers, authority, and provenance.
- Confine one note to one subject, decision, observation, preference, rationale, or conflict, and split any candidate blending a preference, a requirement, and a tool instruction merely because they co-occurred.
- Resolve pronouns, deictic time expressions, and implicit scope into explicit named referents before the body is stored, and retain hedges such as an unverified marker or a project-limited qualifier inside the body rather than as external commentary.
- Set author type and assertion mode from the closed vocabularies, and record every source identifier and span the body depends on.

**Required Outputs**:

- A note body interpretable without its originating conversation.
- An author type and assertion mode value drawn from the closed vocabulary.
- A source pointer set naming every source version and span the body depends on.

**Quality Checkpoints**:

- Self-containment sampling shows at least 95 percent of notes interpretable without their originating context; below that, note construction reverts to extractive form until the rate recovers.
- No note body carries an unresolved pronoun bearing on its claim; such notes are rewritten or rejected before indexing.
- Quantities, deadlines, identifiers, negations, and quoted commitments are stored extractively; an abstractive body carrying one of these is admitted only where a fidelity check and a source link both survive.

***

#### Step 1.3: Apply the Envelope, Redaction, and Trust Labelling

**Required Actions**:

- Populate the governed envelope in full before the body reaches any index, covering identity and version fields, scope fields, source fields, and governance fields.
- Treat a null scope field as unresolved rather than as global, and assign an explicit global scope only where policy permits it and a named owner has approved it.
- Run secret, personal-data, malware, active-markup, invisible-character, and instruction-like-content detection before the body enters broad memory, recording detector version, input representation, decision, and redaction spans.
- Label remembered content as data rather than instruction, delimit it in every prompt that carries it, and re-authorise every tool action independently of anything the body says.
- Derive every derivative record under the strongest restriction present on any of its sources, unless a documented transformation justifies a weaker one.

**Required Outputs**:

- A complete envelope record per memory version, with no unresolved scope field.
- A detector decision record per admitted body, naming detector versions and redaction spans.
- A trust label and an injection risk score attached to every indexed chunk.

**Quality Checkpoints**:

- Envelope completeness is 100 percent for records reaching broad retrieval; an incomplete envelope routes the record to quarantine rather than to an index.
- Personal-data detection recall on the labelled corpus is at least 0.95 per category and per language; below that, the affected class is quarantined pending review rather than indexed.
- Instruction-like content is quarantined or stored with a raised injection risk score, and no writable memory body is loaded as policy, permission, or tool configuration.
- Agent-authored bodies carry author type agent with an assertion mode of inference, summary, or reflection, and none inherits the authority of its inputs.

***

### Phase 2: Chunking and Boundary Preservation

**Objective**: Split bodies into retrieval units that answer their own claims while preserving exact addressability into an immutable source, so citation, correction, re-chunking, and erasure all remain possible.

#### Step 2.1: Freeze the Canonical Source and Record Exact Offsets

**Required Actions**:

- Store the canonical body, or a lawful immutable pointer to it, before any chunking runs, and compute a content checksum over the exact bytes chunked.
- Record for every chunk the source identifier, source version identifier, offset start and end, page or region coordinates where applicable, speaker identifier and time offsets for spoken sources, section path, and the identifiers of the preceding and following chunks.
- Number chunks by ordinal within their source version, so a re-chunking run produces a new set rather than mutating an existing one.
- Bind every chunk to exactly one source version, and invalidate the whole chunk set when that source version is superseded, corrected, or deleted.

**Required Outputs**:

- A chunk record set carrying complete offsets, neighbour links, and a source checksum.
- A chunking run record naming chunker name, chunker version, strategy, target size, actual size, overlap, and boundary type.

**Quality Checkpoints**:

- Citation offset validity is 100 percent, meaning every stored offset range resolves to the recorded text in the recorded source version; one invalid offset blocks the run from being indexed.
- Every chunk carries neighbour identifiers, because neighbour expansion is the primary repair for a severed boundary.
- No chunk survives whose source version has been deleted or superseded without invalidation.

***

#### Step 2.2: Select Boundaries and Test Self-Containment

**Required Actions**:

- Prefer natural boundaries over fixed windows: one curated atomic note, one paragraph or short section, one speaker turn or coherent exchange, one page region or image, one audio segment, or one video scene.
- Treat a fixed token window as the measured baseline rather than the default, and admit a more expensive strategy only where an ablation on the labelled corpus shows it improves answer-span containment or downstream task success.
- Test every sampled chunk for boundary severance by checking whether a negation, an exception clause, a scope restriction, a unit, or an attribution bearing on its claim falls outside the chunk.
- Reject as non-self-contained any chunk whose referents cannot be resolved from lawful local context, and re-cut it or expand it to its neighbours rather than indexing it.
- Record the severance judgement, the ablated strategies, and the retained strategy with its measured margin.

**Chunking Strategy Ablation Matrix**:

| Strategy | Primary gain | Primary risk | Admission condition |
| :-- | :-- | :-- | :-- |
| Fixed window | Predictable cost and size | Severs claims mid-sentence | Baseline; always measured |
| Natural boundary | Preserves discourse units | Highly variable unit size | Default where boundaries are detectable |
| Overlap window | Recovers boundary-straddling claims | Duplicated storage and result flooding | Overlap above 0 only where severance exceeds 2 percent |
| Semantic split | Topic-coherent units | Boundary instability across runs | Measured gain exceeds model cost |
| Context header | Restores document-level referents | Generated text mistakable for source | Header stored and cited separately |
| Parent expansion | Full context at read time | Higher read token cost | Read budget admits the expanded parent |

**Required Outputs**:

- A retained chunking strategy with its ablation record and measured margin over the baseline.
- A severance sample report stating the rate and the classes of severed qualifier observed.
- A rejected-chunk list carrying rejection reason codes.

**Quality Checkpoints**:

- Boundary severance rate on the sampled set is at most 2 percent; above that, the strategy is re-cut on natural boundaries before any index build proceeds.
- Answer-span containment on the labelled corpus is at least 95 percent; below that, overlap or parent expansion is enabled and re-measured.
- Overlap above 0 is justified by a measured severance reduction, because overlap otherwise duplicates storage and floods result sets with the same claim.

***

#### Step 2.3: Generate and Segregate Context Headers

**Required Actions**:

- Generate a short document-aware header of 50 to 100 tokens describing where the chunk sits in its source, and prepend it for both dense and lexical indexing.
- Store the header separately from the source text, recording header text, generating model, prompt version, covered source version, and a faithfulness check result.
- Cite only source text; never present a generated header, caption, transcript, or summary as words the source contained.
- Rebuild every header whose source version, chunk boundaries, or generating model has changed, and mark headers built from a superseded source version as invalid until rebuilt.

**Required Outputs**:

- A context header record per chunk, carrying model, prompt version, source version, and faithfulness result.
- A header invalidation queue listing headers whose inputs have changed.

**Quality Checkpoints**:

- Header faithfulness sampling shows at most 2 percent of headers asserting a fact absent from the covered source version; above that, header generation is suspended and existing headers are rebuilt.
- No citation returned to a caller resolves to header text rather than to a source span.
- Header token length stays within 50 to 100 tokens, because longer headers displace source signal in both the embedding and the lexical posting.

***

### Phase 3: Embedding, Index Construction, and Version Pinning

**Objective**: Build lexical and vector indexes whose every representation is traceable to one pinned model revision, so that scores remain comparable and a model change becomes a planned migration rather than a silent corruption.

#### Step 3.1: Pin the Representation Identity

**Required Actions**:

- Record for every representation the embedding model identifier, an immutable model revision, the dimension, the numeric type, the normalisation applied, the distance metric, the input hash, and a vector checksum.
- Treat the model revision as immutable rather than as a mutable alias, because a provider updating a model behind a stable name changes the space without changing the name.
- Pin exactly one embedding revision, one analyzer configuration, and one metadata filter schema version to each index generation, and refuse any write whose representation revision differs from the generation's pin.
- Record for each generation the covered source versions, the tombstone generation applied, and the reason a re-embedding run was started.
- Build the lexical index first and measure it as the standalone baseline, adding dense retrieval only where a measured paraphrase or conceptual-match gap justifies its cost.

**Required Outputs**:

- A representation record per chunk carrying model identifier, revision, dimension, metric, and checksum.
- An index generation manifest naming the pinned revision, analyzer configuration, filter schema version, and covered source versions.
- A lexical baseline measurement against which dense retrieval is justified.

**Quality Checkpoints**:

- Representation revision equals the serving generation's pinned revision for 100 percent of vectors; a non-zero mismatch count blocks the generation from serving.
- No two vectors from different revisions are compared as though their distances were calibrated; cross-revision comparison is a defect, not an approximation.
- Dense retrieval is enabled only where it improves recall at k over the lexical baseline by at least 5 percentage points on the labelled corpus.

***

#### Step 3.2: Construct the Index Generation and Verify Coverage

**Required Actions**:

- Build each generation from a canonical snapshot rather than from an existing index, so a corrupted or partial prior state cannot propagate.
- Replay writes, corrections, and tombstones issued during the build, and re-verify coverage after the replay completes.
- Verify that every eligible record is represented in the generation, or that every exclusion appears in a documented exclusion set with a reason code.
- Confirm that compound metadata filters behave correctly under approximate search, because approximate candidate generation can drop eligible results when a selective filter interacts with it.
- Expose serving traffic to a generation only through an alias, and never allow application code to address a generation directly.

**Required Outputs**:

- A completed index generation with a coverage report stating covered, excluded, and pending counts.
- A documented exclusion set naming every uncovered eligible record and its reason.
- A filter behaviour test report covering selective, compound, and negated predicates.

**Quality Checkpoints**:

- Coverage of eligible records is 100 percent, or every gap appears in the exclusion set; an undocumented gap blocks promotion of the generation.
- Selective-filter recall on the labelled corpus is at least 0.95 relative to an exhaustive scan; below that, the approximate search is reconfigured or an exact path is used for filtered queries.
- The serving alias points to exactly one generation at a time, so no request can be answered from two spaces at once.

***

#### Step 3.3: Execute an Embedding Migration as a Versioned Cutover

**Required Actions**:

- Freeze the outgoing model and generation at the start of the migration, and create the incoming generation as a separate build rather than as an in-place rewrite.
- Dual-write incoming content to both generations for the duration of the migration, so the new generation does not fall behind the change stream.
- Evaluate the incoming generation on recall at k, precision at k, filtered recall, multilingual robustness, tail latency, and storage cost before any traffic moves.
- Switch the serving alias atomically once coverage and evaluation gates pass, and retain the outgoing generation for rollback for at least 14 days after cutover.
- Leave canonical bodies untouched during a migration, because rewriting a note to change its vectors destroys provenance for a reason unrelated to content.

**Required Outputs**:

- A migration record naming outgoing revision, incoming revision, coverage figures, and evaluation deltas.
- An atomic alias switch event with its timestamp and the generation it selected.
- A retained rollback generation with its expiry date.

**Quality Checkpoints**:

- The incoming generation reaches 100 percent eligible coverage before the alias switches; a partial cutover is the drift failure this step exists to prevent.
- Recall at k on the incoming generation is within 2 percentage points of the outgoing generation or better; a larger regression blocks the switch.
- The rollback generation remains intact and addressable for at least 14 days; deleting it earlier removes the only remedy for a regression discovered in production.

***

### Phase 4: Deduplication, Merge, and Contradiction Handling

**Objective**: Collapse repeated content into canonical clusters and surface genuine disagreement, so that retrieval ranks by authority and evidence rather than by how many times a claim was written down.

#### Step 4.1: Fingerprint and Cluster Candidates

**Required Actions**:

- Compute a content hash over the normalised body and collapse exact matches without model involvement.
- Compute MinHash signatures over 5-gram shingles and generate near-duplicate candidates by locality-sensitive hashing, recording estimated Jaccard similarity for every pair.
- Compute a secondary fingerprint suited to edit-like variation, and generate embedding-based candidates only for pairs that lexical fingerprints fail to separate.
- Cluster candidates at an estimated Jaccard threshold of 0.80 for near-duplicate review and 0.95 for automatic collapse, and record the threshold version with every decision.
- Measure store-wide duplicate concentration and per-cluster retrieval share on a recurring schedule rather than only at ingestion.

**Required Outputs**:

- A fingerprint record per chunk naming method, method version, and signature.
- A candidate pair list with lexical similarity, dense similarity, and the threshold version applied.
- A duplicate concentration report stating store-wide near-duplicate rate and the largest cluster's retrieval share.

**Quality Checkpoints**:

- Store-wide near-duplicate rate at estimated Jaccard 0.80 or above stays at or below 15 percent of chunks; above that, curation is scheduled and admission precision is reviewed.
- No cluster occupies more than 30 percent of any top-20 result set; a breach applies the per-cluster retrieval cap immediately and queues the cluster for merge review.
- Candidate generation is deterministic and reproducible from the recorded fingerprints, so a clustering decision can be replayed and audited.

***

#### Step 4.2: Adjudicate the Relationship Class

**Required Actions**:

- Classify every candidate pair into exactly one class from the closed vocabulary: exact duplicate, near duplicate, refinement, temporal update, corroboration, contradiction, or independent observation.
- Extract material difference spans for every pair, covering disagreement on qualifier, quantity, negation, time, scope, or attribution, and attach the spans to the decision record.
- Route pairs that lexical fingerprints cannot separate to a model judgement, and require the model to return the class, the material difference spans, and a reason code rather than a bare similarity verdict.
- Detect implicit supersession, where a later record makes an earlier record false without negating it in words, by comparing records that share a subject and an overlapping validity interval.
- Preserve corroboration and contradiction as distinct outcomes, because collapsing a contradiction into a duplicate is the failure that makes a store confidently wrong.

**Relationship Class Decision Rules**:

| Observed condition | Class | Deterministic gate verdict |
| :-- | :-- | :-- |
| Content hashes equal | Exact duplicate | Collapse automatically; no review |
| Jaccard at or above 0.95, zero difference spans | Near duplicate | Collapse; write provenance record |
| Jaccard 0.80 to 0.95, zero difference spans | Near duplicate | Collapse after model confirmation |
| Any material difference span present | Refinement or update | Retain both; link and order by validity time |
| Same subject, overlapping validity, opposed claims | Contradiction | Retain both; surface together; never merge |
| Same claim, independent sources | Corroboration | Retain both; count once toward evidence weight |
| Shared premise or descendant chain | Not corroboration | Retain; suppress from independence counting |

**Required Outputs**:

- A relationship decision record per candidate pair naming class, difference spans, threshold version, and decider identity.
- A contradiction register listing unresolved opposed claims with their subjects and validity intervals.
- An independence assessment marking which agreeing records share a premise or a descendant chain.

**Quality Checkpoints**:

- Merge pair precision on the labelled corpus is at least 0.98, because a false merge silently deletes a qualifier that may be the whole point of the record.
- Merge pair recall is at least 0.85; a lower value leaves the accumulation decay mode unaddressed and is corrected by lowering the review threshold, never by lowering the precision bar.
- No pair carrying a material difference span is classified as a duplicate; such a classification is rejected by the gate regardless of similarity score.
- Records sharing a descendant chain never count as independent corroboration, so a self-authored note cannot confirm itself through republication.

***

#### Step 4.3: Apply the Merge Under a Deterministic Gate

**Required Actions**:

- Accept a merge as a proposal only, and apply it in a single transaction that writes the canonical member, the occurrence links, and a provenance record naming every merged version.
- Reject any proposal whose members disagree on tenant, purpose, audience scope, sensitivity class, or retention class, because a merge across scopes is a policy breach wearing the costume of a cleanup.
- Retain every merged version as an immutable record rather than deleting it, so the merge is reversible and the discarded wording remains auditable.
- Assign the canonical member the strongest source authority present in the cluster and the earliest observation time, and record both selections with reason codes.
- Record a rollback identifier with every merge, and sample at least 5 percent of automatic merges for human review each cycle.

**Required Outputs**:

- A canonical cluster record with occurrence links to every merged version.
- A provenance record naming merged version identifiers, the selection rule applied, and the rollback identifier.
- A merge review sample with human labels and an observed false-merge rate.

**Quality Checkpoints**:

- Provenance is preserved through 100 percent of merges; a merge that cannot name its inputs is rolled back rather than accepted.
- Every merge is reversible from its rollback identifier for at least 90 days; an irreversible merge is a deletion and is governed by Phase 6 instead.
- Observed false-merge rate on the review sample stays at or below 2 percent; above that, automatic collapse is suspended and every merge routes to review.
- No merge crosses a tenant, purpose, audience, sensitivity, or retention boundary.

***

### Phase 5: Policy-First Retrieval and Reranking

**Objective**: Return the smallest set of eligible, attributable spans that answers the request, with disagreement surfaced rather than resolved by rank.

#### Step 5.1: Apply Eligibility Before Ranking

**Required Actions**:

- Bind tenant, principal, subject, session, task, project, purpose, audience scope, sensitivity ceiling, validity time, and trust requirement from authenticated context rather than from anything the model produced.
- Evaluate every eligibility predicate as a hard filter before any lexical or dense scoring runs, and record candidate counts both before and after the filter.
- Consult the tombstone set on the serving path, so a deleted record stops being retrievable in advance of its copies being purged.
- Permit the model to narrow scope within an authorised set and never to widen it, so a request cannot reach another tenant by phrasing.
- Overlay recent canonical writes that have not yet reached an index, so a just-written record is not invisible for the duration of an indexing lag.

**Required Outputs**:

- An eligibility filter record naming every predicate applied, its value, and the filter schema version.
- Candidate counts before and after policy filtering.
- A tombstone check result per returned candidate.

**Quality Checkpoints**:

- Cross-tenant leakage measures exactly 0 on the adversarial evaluation slice; any non-zero result halts the read path rather than lowering a threshold.
- Every returned candidate passed a tombstone check in the same request; a stale cache hit is treated as a leakage class, not as a latency optimisation.
- Eligibility predicates were applied before ranking in 100 percent of requests, verified from the logged candidate counts rather than asserted.

***

#### Step 5.2: Generate and Fuse Candidates Across Routes

**Required Actions**:

- Route exact names, quoted wording, identifiers, rare terms, and negation-bearing queries to the lexical index, and route paraphrases and conceptual matches to the dense index.
- Fuse ranked lists by reciprocal rank fusion with a recorded rank constant, defaulting to 60, rather than by comparing lexical and dense scores that share no scale.
- Retain lexical score, dense score, recency, salience, authority, freshness, scope compatibility, duplicate penalty, and injection risk as separate logged features rather than folding them into one opaque number.
- Apply the per-cluster retrieval cap of at most 2 members and a per-source cap, so a near-duplicate cluster cannot occupy the result set by count.
- Prevent recency from defeating an older authoritative statement, and prevent retrieval frequency from raising the standing of a self-authored note.

**Required Outputs**:

- A per-route candidate list with rank, score, and route identifier.
- A fusion record naming the method, the rank constant, component ranks, and the fused rank.
- A per-candidate feature vector with every scoring feature logged separately.

**Quality Checkpoints**:

- Post-filter recall at k on the labelled corpus meets the declared minimum for the workload, and a shortfall is corrected by route or boundary changes rather than by raising k.
- No single near-duplicate cluster contributes more than 2 members to the fused list.
- Every feature contributing to rank is separately logged, so a ranking regression is attributable to a feature rather than to the fusion as a whole.

***

#### Step 5.3: Rerank, Diversify, and Assemble the Answer Context

**Required Actions**:

- Rerank only a bounded candidate set, defaulting to at most 50 candidates, so tail latency stays governed while ordering improves.
- Diversify the selection across sources, dates, topics, and trust classes before assembly, and prefer a minimal exact span carrying enough surrounding context to preserve referents, negation, conditions, and time.
- Reserve context budget for policy, task state, the request, surfaced conflicts, and the answer, and record the exact position at which each selected span was placed.
- Return with every span its source pointer, author type, assertion mode, observed and validity times, freshness, authority, and links to any conflicting record.
- Abstain or request clarification where no eligible span clears threshold, the required authority is absent, referents remain ambiguous, evidence is stale beyond the request's bound, an unresolved conflict changes the answer, or injection risk cannot be contained.

**Required Outputs**:

- An assembly record naming selected candidates, dropped candidates with reason codes, diversity clusters, source caps, and context positions.
- A returned evidence set in which every span carries its citation and provenance fields.
- An abstention record with its reason code where no answer was returned.

**Quality Checkpoints**:

- Citation support, measured as returned claims whose cited span entails them, is at least 0.95; below that, the assembly returns spans without an asserted answer.
- Every surfaced conflict is presented as a conflict rather than resolved silently by rank order.
- Increasing k is never used as a remedy for poor selection, because a longer context degrades utilisation rather than improving it.

***

### Phase 6: Invalidation, Compaction, Retention, and Verified Deletion

**Objective**: Keep the store's contents current, bounded, and erasable, so that age, volume, and derivation do not quietly convert a memory system into an unaccountable archive.

#### Step 6.1: Detect Staleness and Apply Invalidation

**Required Actions**:

- Assign every record a volatility class with an explicit verification horizon, and set a next review timestamp for consequential or volatile content.
- Compare each record's last verification timestamp against its horizon on a recurring schedule, and demote retrieval weight to at most 0.5 of nominal once the horizon passes.
- Detect implicit supersession by comparing new writes against existing records sharing a subject and an overlapping validity interval, and route detected supersession to the invalidation gate.
- Apply an invalidation only where the superseding record carries equal or greater source authority, an overlapping validity interval, and a preserved copy of the invalidated version.
- Never count retrieval frequency as verification, because a note that is read often is popular rather than confirmed.

**Required Outputs**:

- A volatility class and verification horizon per record.
- An invalidation decision record naming the superseding version, the authority comparison, and the preserved prior version.
- A staleness report stating the count and share of records past their horizon.

**Quality Checkpoints**:

- Records past their horizon by more than 100 percent of its length are demoted or queued for revalidation; none continues to serve at nominal weight.
- Stale-answer rate on the time-shifted evaluation slice is at most 5 percent; above that, horizons are shortened for the affected volatility class.
- Every invalidated version is preserved rather than overwritten, so an incorrect invalidation is recoverable.

***

#### Step 6.2: Compact Without Laundering Error

**Required Actions**:

- Build the held-out answer-preservation question set before any compaction runs, sampling common, rare, temporal, contradictory, multilingual, and adversarial details.
- Maintain a must-preserve set covering exact names, identifiers, quantities, deadlines, quotations, and negations, and verify its retention in the compacted body.
- Answer the held-out questions from raw evidence and from the compacted view under the same model and the same budget, and compare supported answer units, entities, values, citations, abstentions, and exposed contradictions.
- Cap derivative depth at 3 hops from a primary source, record the source versions a summary derives from, and rebuild from sources rather than from the prior summary once the cap is reached.
- Invalidate every descendant summary when a source is corrected or deleted, and never continue rolling summarisation after the raw evidence is gone.

**Required Outputs**:

- A held-out question set with answers from both raw and compacted views.
- A compaction record naming source versions, derivative depth, must-preserve item outcomes, and omitted source spans.
- A publication decision with its gate results attached.

**Quality Checkpoints**:

- Answer preservation on the held-out set is at least 0.95 of the raw-evidence baseline; below that, the summary is not published and the sources are retained.
- Must-preserve item retention is 100 percent; a single dropped identifier, quantity, or negation blocks publication.
- Derivative depth never exceeds 3; a deeper chain is rebuilt from sources, because repeated compaction amplifies an early error that later generations can no longer see.
- No summary is treated as more authoritative than its strongest independent source.

***

#### Step 6.3: Enforce Retention and Verify Deletion Across Every Derivative

**Required Actions**:

- Enumerate the full derivative graph for every deletion target, covering raw assets, chunks, extracted text, captions, transcripts, embeddings, lexical postings, summaries, self-authored files, caches, checkpoints, exports, evaluation sets, replicas, and backups.
- Commit a serving tombstone before physical removal begins, so the record stops being retrievable while purging proceeds.
- Verify deletion by keyed lookup, lexical search, vector search, cache probe, prior-generation probe, and a restoration test against a backup, recording the verification method and result for each target.
- Where immediate backup deletion is impractical, record the target as unavailable for restoration and schedule its purge, rather than reporting the deletion as complete.
- Enforce retention timers deterministically on a schedule, and treat an expired record as ineligible at serving time even before its physical removal completes.

**Required Outputs**:

- A deletion request record naming requester, approver, legal basis, and any exception code.
- A per-target deletion record with dependency path, index generation, status, attempt count, verification method, and residual findings.
- A residual risk statement for any target whose purge is scheduled rather than complete.

**Quality Checkpoints**:

- Serving residual hits after tombstone commitment measure exactly 0; a non-zero result is a leakage incident, not a pending task.
- Deletion propagation reaches 100 percent of enumerated derivatives within the declared policy window; an unreached derivative escalates rather than expiring quietly.
- Every deletion is verified by at least 3 distinct methods, because a single keyed lookup cannot detect a copy living in a vector index or a cache.
- Derived personal data, including embeddings and summaries, is deleted alongside its source; deleting only the transcript is an incomplete erasure.

***

## III. Implementation Guidance for AI Agents

AI agents operating an unstructured memory store must follow systematic protocols ensuring that every body is traceable to a source, every retrieval is eligible before it is relevant, and every destructive operation is verified rather than assumed. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Admission Agent**: Scores candidates, constructs atomic notes, and populates the envelope. It may reject a candidate outright and may never index a body carrying an incomplete envelope. Owns Phase 1.
2. **Chunking Agent**: Executes boundary selection, records offsets and neighbour links, and generates and validates context headers. It may reject a chunk as non-self-contained. Owns Phase 2.
3. **Index Agent**: Pins representation identity, builds generations, verifies coverage, and performs alias switches. It alone may promote or roll back a generation, and it refuses any representation whose revision differs from the pin. Owns Phase 3.
4. **Curation Agent**: Fingerprints, clusters, adjudicates relationship class, and proposes merges and invalidations. It proposes only; it never applies a merge or an invalidation itself. Owns Phase 4 proposal work and Step 6.1 detection.
5. **Retrieval Agent**: Binds eligibility from authenticated context, generates and fuses candidates, reranks, diversifies, and assembles. It may narrow scope and may never widen it. Owns Phase 5.
6. **Lifecycle Agent**: Enforces retention timers, gates compaction publication, commits tombstones, and verifies deletion across the derivative graph. It alone may authorise a physical removal. Owns Phase 6 enforcement.
7. **Governance Gate**: A deterministic component, not a model, that admits or rejects every proposal from the Curation Agent and every publication from a compaction run. It holds authority in any disagreement with a model tier proposal.

**Tier Assignment by Phase**: Phase 1 is hybrid, with the model scoring salience and rewriting notes while software enforces envelope completeness and detector outcomes. Phase 2 is deterministic in execution and model-assisted in header generation. Phase 3 is wholly deterministic; no model judgement participates in pinning, coverage, or cutover. Phase 4 is hybrid, with the model classifying relationships and the Governance Gate applying them. Phase 5 is deterministic in filtering and fusion and model-assisted in interpretation. Phase 6 is hybrid in compaction and wholly deterministic in retention enforcement and deletion verification.

**Workflow Execution Pattern**:

```
STATE: Merge_Proposal_Adjudication
INPUTS:
  1. Candidate pair list with lexical and dense similarity from Step 4.1
  2. Material difference spans and proposed class from Step 4.2
  3. Envelope fields for both members
ACTIONS:
  1. Verify scope compatibility across tenant, purpose, audience, sensitivity, retention
  2. Verify material_difference_span_count for the proposed pair
  3. Verify a provenance record naming every merged version is present
  4. Verify a rollback identifier has been allocated
VALIDATION:
  - proposal_source == curation_agent AND applier == governance_gate
  - material_difference_span_count == 0
  - scope_fields_compatible == TRUE
  - provenance_record_present == TRUE
  - rollback_identifier_present == TRUE
TRANSITIONS:
  IF all_validations_pass THEN next_state = Apply_Merge_In_Single_Transaction
  IF material_difference_span_count > 0 THEN next_state = Retain_Both_And_Link
  IF scope_fields_compatible == FALSE THEN next_state = Reject_And_Log_Policy_Breach
  IF validation_failed THEN next_state = Merge_Error_Handling
```

**Two-Phase Action Pattern**: Emit every destructive operation as a proposal carrying its inputs, its class, and its rollback identifier without executing it; validate the proposal against the gate while nothing is committed; apply it only after validation passes, writing the provenance record in the same transaction as the change.

**Approval Gate**: Human authorisation is required before any merge affecting more than 100 records in one operation, before any deletion of a canonical source under legal hold or with an unreachable derivative, before any alias switch that moves more than 25 percent of serving traffic to a generation whose recall regressed at all, and before any relaxation of an eligibility predicate. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the envelope, the cluster registry, the index generation manifest, and the deletion ledger in durable state, because a memory store outlives every context window that touches it.
- Process curation, re-chunking, and re-embedding in bounded batches with a recorded resume point, so an interrupted maintenance run resumes rather than restarts.
- Never load a memory body into a prompt without its trust label and delimiters, and never let a loaded body change tool policy.
- Count context assembled from memory against the request's token budget explicitly, so retrieval cost is visible rather than absorbed.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Admission Integrity (After Phase 1)**

- **Automated Check**: Envelope completeness is 100 percent; every candidate carries an admission decision and reason code; detector recall on the labelled corpus is at least 0.95 per category; write precision is at least 0.70.
- **Agent Action on Pass**: Release the record to chunking.
- **Agent Action on Failure**: Quarantine the record and return the failing field or score; no incomplete record proceeds to an index.
- **Human Review Trigger**: Write precision below 0.60, or any detector recall below 0.90 in a category carrying regulated personal data.

**Checkpoint 2: Boundary Integrity (After Phase 2)**

- **Automated Check**: Citation offset validity is 100 percent; boundary severance rate is at most 2 percent; answer-span containment is at least 95 percent; header faithfulness failures are at most 2 percent.
- **Agent Action on Pass**: Release the chunk set to embedding and indexing.
- **Agent Action on Failure**: Re-cut on natural boundaries or enable neighbour expansion, and re-measure the sample rather than the whole corpus.
- **Human Review Trigger**: Severance rate above 5 percent, or any severance class that reverses the meaning of a regulated or safety-relevant claim.

**Checkpoint 3: Representation Consistency (After Phase 3)**

- **Automated Check**: Zero representations whose revision differs from the generation pin; eligible coverage is 100 percent or fully documented in the exclusion set; selective-filter recall is at least 0.95; recall at k is within 2 percentage points of the outgoing generation.
- **Agent Action on Pass**: Switch the serving alias atomically and start the rollback retention clock.
- **Agent Action on Failure**: Block the generation from serving and continue the migration; a partial generation never serves traffic.
- **Human Review Trigger**: Any recall regression above 5 percentage points, or any exclusion set covering more than 1 percent of eligible records.

**Checkpoint 4: Curation Integrity (After Phase 4)**

- **Automated Check**: Merge pair precision is at least 0.98; observed false-merge rate on the review sample is at most 2 percent; provenance is present for 100 percent of merges; no merge crosses a scope boundary.
- **Agent Action on Pass**: Commit the cluster registry update and release the canonical members to retrieval.
- **Agent Action on Failure**: Roll back the affected merges by their rollback identifiers and suspend automatic collapse for the affected class.
- **Human Review Trigger**: False-merge rate above 2 percent, or any merge proposal spanning more than 100 records.

**Checkpoint 5: Retrieval Integrity (After Phase 5)**

- **Automated Check**: Cross-tenant leakage is exactly 0; eligibility predicates preceded ranking in 100 percent of requests; citation support is at least 0.95; no cluster contributes more than 2 members to a result set.
- **Agent Action on Pass**: Return the evidence set with its provenance fields.
- **Agent Action on Failure**: Halt the read path for the affected route and return an abstention rather than a partially filtered result.
- **Human Review Trigger**: Any non-zero leakage result, or citation support below 0.90 on a high-risk slice.

**Checkpoint 6: Lifecycle Integrity (After Phase 6)**

- **Automated Check**: Answer preservation is at least 0.95 of baseline; must-preserve retention is 100 percent; derivative depth is at most 3; serving residual hits after tombstone commitment are exactly 0; deletion propagation reaches 100 percent of enumerated derivatives within the policy window.
- **Agent Action on Pass**: Publish the compacted view or close the deletion request.
- **Agent Action on Failure**: Withhold publication and retain the sources, or reopen the deletion request naming the unreached derivative.
- **Human Review Trigger**: Any residual serving hit, any unreached derivative at the policy window boundary, or any deletion blocked by a legal hold.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
EXECUTION_TIER:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Near-Duplicate Accumulation Dominating Retrieval**

- **Symptoms**: One claim appears in many wordings across the top-20 result set; store-wide near-duplicate rate rises across cycles; retrieval precision falls while recall holds; a cluster's retrieval share grows without any new source entering.
- **Diagnostic Steps**: Compute per-cluster retrieval share over the last measurement window, compare cluster growth against admission volume for the same subject, and confirm whether cluster members carry material difference spans or are genuine restatements.
- **Resolution Protocol**: Option A, apply the per-cluster retrieval cap of 2 members immediately, which bounds the symptom while the cause is fixed. Option B, collapse the cluster to a canonical member with occurrence links under the Governance Gate, preserving every merged version. Option C, raise the admission novelty weight for the subject class so restatements stop entering. Option D, where members disagree, reclassify the cluster as refinement or contradiction and stop treating it as duplication at all.
- **Escalation Trigger**: Store-wide near-duplicate rate above 25 percent, or a false-merge rate above 2 percent while attempting to reduce it, escalates to human curation review; the class is never resolved by lowering the merge precision bar.

**Error Type 2: Stale Content Serving as Current**

- **Symptoms**: Answers reflect a superseded state; two records on one subject disagree with no ordering between them; users correct the same fact repeatedly; stale-answer rate rises on the time-shifted evaluation slice.
- **Diagnostic Steps**: Segment staleness by volatility class and subject, determine whether the superseding write was never made, was made but not detected as superseding, or was detected but blocked at the invalidation gate for lack of authority.
- **Resolution Protocol**: Option A, shorten the verification horizon for the affected volatility class and demote past-horizon records immediately. Option B, run supersession detection over the affected subject set and route the results to the invalidation gate. Option C, surface both records as a conflict rather than allowing rank to select one. Option D, where currency cannot be established, abstain and state what is known and what requires revalidation.
- **Escalation Trigger**: Stale-answer rate above 10 percent on any slice, or any stale record having supported an irreversible action, escalates immediately; retrieval frequency is never accepted as evidence of currency.

**Error Type 3: Boundary Severance Reversing a Claim**

- **Symptoms**: A returned span asserts something the source qualifies or negates; citation support falls while retrieval recall holds; answers become confidently wrong on conditional or negated content.
- **Diagnostic Steps**: Locate the severed qualifier by comparing the returned chunk against its neighbours in the source version, and classify the severance as negation, exception, scope, unit, or attribution.
- **Resolution Protocol**: Option A, expand the returned span to its neighbours at read time, which repairs the symptom without a re-index. Option B, re-chunk the affected sources on natural boundaries and rebuild their representations. Option C, prepend a context header restoring the missing document-level referent. Option D, reject the chunk as non-self-contained and answer from the parent passage.
- **Escalation Trigger**: Severance rate above 5 percent, or any severance that reversed a safety, legal, or financial claim, escalates and blocks further indexing of the affected source class until re-cut.

**Error Type 4: Embedding Version Drift Across a Corpus**

- **Symptoms**: Retrieval quality drops for a subset of content with no change in queries; distances cluster differently for records embedded in different windows; a generation's representation count exceeds its coverage count.
- **Diagnostic Steps**: Compare every representation's recorded revision against the serving generation's pin, and identify whether the mismatch originates in a partial re-embedding run, a provider updating a model behind a stable name, or a dual-write that reached only one generation.
- **Resolution Protocol**: Option A, roll the alias back to the last fully covered generation, which restores comparability immediately. Option B, rebuild the incoming generation from a canonical snapshot and replay the change stream before switching again. Option C, quarantine the mismatched subset from serving and re-embed it into the pinned revision. Option D, where the provider revision cannot be pinned, replace the model with one exposing an immutable revision identifier.
- **Escalation Trigger**: Any non-zero mismatch count in a serving generation escalates and blocks that generation from traffic; this class is never resolved by re-running the same partial migration.

**Error Type 5: Self-Referential Corroboration**

- **Symptoms**: Confidence in a claim rises with no new external source; agreeing records trace to one agent-authored ancestor; a summary is cited as evidence for the note it summarised.
- **Diagnostic Steps**: Trace every agreeing record to its author type, assertion mode, and descendant chain, and determine whether agreement survives removal of the shared ancestor.
- **Resolution Protocol**: Option A, suppress descendant records from independence counting and re-evaluate the evidence weight. Option B, retrieve a primary source outside the chain before the claim may support an action. Option C, cap the authority of agent-authored bodies so they can inform but never authorise. Option D, carry the claim forward with an explicit unsupported marker.
- **Escalation Trigger**: Any high-consequence action resting on agreement that fails the independence test escalates immediately; this class is never resolved by retrieving more copies.

**Error Type 6: Incomplete Erasure Across Derivatives**

- **Symptoms**: A deleted record's content is recoverable from a vector index, a cache, a summary, a self-authored file, an evaluation set, or a restored backup; deletion status reports complete while a residual probe returns a hit.
- **Diagnostic Steps**: Re-enumerate the derivative graph from the canonical source, compare the enumerated set against the deletion ledger, and identify which derivative class was created after the ledger was built.
- **Resolution Protocol**: Option A, reopen the deletion request naming the unreached derivative and re-run verification across all methods. Option B, rebuild the derivative enumeration from lineage records rather than from a static list, so newly created derivative classes are captured. Option C, where a backup cannot be purged immediately, mark the target unavailable for restoration and schedule the purge with a recorded residual risk.
- **Escalation Trigger**: Any serving residual hit after tombstone commitment, or any derivative unreached at the policy window boundary, escalates as an incident; a deletion is never closed on a single verification method.

**Troubleshooting Decision Tree**:

```
MEMORY STORE FAILS A CHECKPOINT
├─ ACCUMULATION DEFECT
│   ├─ Cluster share above 30 percent of top-20 → Apply per-cluster cap; queue merge review
│   ├─ Store-wide duplicate rate above 15 percent → Schedule curation; raise novelty weight
│   └─ False-merge rate above 2 percent → Suspend auto-collapse; route every merge to review
├─ CURRENCY DEFECT
│   ├─ Record past horizon by 100 percent → Demote weight; require revalidation before action
│   ├─ Two records disagree on current state → Surface as conflict; never resolve by rank
│   └─ Supersession blocked for low authority → Retain both; escalate for authority ruling
├─ BOUNDARY DEFECT
│   ├─ Qualifier outside chunk → Expand to neighbours; re-cut on natural boundaries
│   ├─ Offset does not resolve → Block index build; rebuild chunk set from source version
│   └─ Header asserts unsourced fact → Suspend header generation; rebuild headers
├─ REPRESENTATION DEFECT
│   ├─ Revision mismatch in serving generation → HALT serving; roll alias back
│   ├─ Coverage below 100 percent at cutover → Block switch; complete migration
│   └─ Filtered recall below 0.95 → Reconfigure approximate search; use exact filtered path
├─ EVIDENCE DEFECT
│   ├─ Agreement shares a descendant chain → Suppress from independence count
│   └─ Summary cited as source → Reject citation; return the primary span
└─ ERASURE DEFECT
    ├─ Residual serving hit after tombstone → HALT; treat as leakage incident
    └─ Derivative unreached at window boundary → Reopen request; re-enumerate from lineage
```

### D. Performance Metrics and Continuous Learning

**Content Quality Metrics**:

- **Write precision**: Adjudicated-useful records over admitted records (target: at least 0.70).
- **Write recall**: Admitted useful candidates over all useful candidates (target: at least 0.60).
- **Note self-containment**: Sampled notes interpretable without originating context (target: at least 95 percent).
- **Envelope completeness**: Records reaching broad retrieval with every required field populated (target: 100 percent).

**Store Health Metrics**:

- **Near-duplicate rate**: Chunks in clusters at estimated Jaccard 0.80 or above (target: at most 15 percent; above 25 percent escalates).
- **Merge pair precision and recall**: Correct merge decisions against labels (targets: at least 0.98 precision and at least 0.85 recall).
- **Boundary severance rate**: Sampled chunks severing a qualifier from its claim (target: at most 2 percent).
- **Representation revision mismatch**: Vectors whose revision differs from the serving pin (target: exactly 0).
- **Staleness share**: Records past their verification horizon and still at nominal weight (target: exactly 0).
- **Derivative amplification**: Stored derivative bytes over canonical source bytes (target: at most 3 times; a higher ratio indicates the store is mostly restatement).

**Retrieval and Lifecycle Metrics**:

- **Post-filter recall and precision at k**: Measured after eligibility filtering, never before (targets declared per workload and held constant across releases).
- **Citation support**: Returned claims entailed by their cited span (target: at least 0.95).
- **Cross-tenant leakage**: Ineligible results returned under adversarial evaluation (target: exactly 0).
- **Answer preservation**: Held-out question accuracy from the compacted view over the raw baseline (target: at least 0.95).
- **Deletion propagation completeness**: Enumerated derivatives reached within the policy window (target: 100 percent).
- **Cost per successful memory-assisted task**: Total storage, embedding, retrieval, review, and deletion cost over accepted successes (target: below the strongest simpler baseline at matched quality).

**Learning and Adaptation Mechanisms**:

- **Delayed-label calibration**: Recalibrate admission weights against observed usefulness rather than against a model's confidence at write time.
- **Threshold recomputation**: Recompute similarity, horizon, and cap thresholds per content class; the values stated here are deployment defaults, not measured constants.
- **Failure-to-rule conversion**: Convert every confirmed decay incident into a scheduled detection rather than into a reminder, so the same failure is caught by measurement next time.
- **Baseline maintenance**: Re-run the no-memory, bounded-context, lexical-only, and typed-store baselines whenever content mix, model, index, or policy changes materially, so the store's advantage remains demonstrated rather than assumed.

**Human-in-the-Loop Boundaries**: Relaxation of an eligibility predicate, approval of a merge spanning more than 100 records, deletion of a canonical source under legal hold, promotion of an index generation with any recall regression, and any change granting a memory body authority over tool policy are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how free-form content is admitted, addressed, compared, and retired, not what the content is about. Its phases hold wherever an agent accumulates language or media it will later need to find again, and wherever no stable schema can be imposed at the moment of capture.

### 4.1 Cross-Domain Application Patterns

**Clinical and care documentation**: Notes carry hedged observation, negation, and temporal qualification that a typed record cannot hold, so the unstructured store is the primary evidence layer. Boundary severance is the dominant risk, because separating a finding from its negation or its laterality reverses clinical meaning; severance sampling therefore runs on every chunking change rather than on a schedule. Near-duplicate accumulation arrives through copied-forward text, so the per-cluster retrieval cap binds tightly and cluster growth is measured against admission volume per subject. Erasure is regulated and diffuse, so the derivative enumeration in Step 6.3 is built from lineage records rather than from a maintained list.

**Legal and contractual analysis**: Exact wording is the evidence, so admission preserves verbatim text and the model tier is barred from paraphrasing an operative clause. Merges are rare and heavily gated, because two clauses differing by one qualifier are not duplicates in any sense the domain recognises. Citation support carries the highest weight of any retrieval metric, and an answer without a resolvable span is withheld rather than offered with a caveat. Retention is driven by legal hold, which overrides every timer in Phase 6.

**Software engineering and operations knowledge**: Content volatility is high and verification horizons are short, so staleness rather than duplication is the dominant decay mode. A convention that was true two releases ago is the characteristic failure, and it arrives without any record explicitly negating it. Self-authored instruction files are common here and carry the self-referential corroboration risk directly, so agent-authored bodies stay separated from human-authored conventions and neither is loaded as enforced configuration.

**Scientific and research synthesis**: Sources are heterogeneous, multilingual, and unevenly authoritative, so source authority and independence assessment carry more weight than recency. Contradiction is a first-class outcome rather than an error, and the contradiction register is a deliverable. Compaction is used sparingly, because a summary that smooths a disagreement destroys the finding the synthesis exists to report; derivative depth is held at 1 for any body supporting a reported conclusion.

**Customer support and account history**: Volume is high and per-record value is low, so admission precision matters more than recall and the store would otherwise become a transcript archive. Duplicate accumulation is severe, because the same issue is described repeatedly by different people. Tenant isolation is the binding safety property, and the exactly-zero leakage requirement in Step 5.1 is the gate that decides whether the store may serve at all.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small stores below 10,000 chunks**: Run lexical retrieval alone, hash-based exact deduplication, and a single index generation. Dense retrieval and semantic deduplication are admitted only where an ablation shows the lexical baseline missing recall the workload needs; at this scale their cost usually exceeds their gain.
- **Large stores above 1,000,000 chunks**: Locality-sensitive hashing becomes mandatory rather than optional for near-duplicate candidate generation, curation runs continuously rather than in cycles, and re-embedding is planned as a resumable batched migration with dual writes rather than as a single operation.
- **High-risk or regulated content**: Retain every phase, hold verification horizons at half their nominal length, require a primary source outside the descendant chain before any claim supports an action, and prefer abstention over an answer whose eligibility or currency cannot be established.
- **Strict latency budgets**: Reduce the reranked candidate set and the assembled context rather than removing the eligibility filter, because the filter is the safety boundary and the reranker is an ordering improvement. Where latency forbids reranking entirely, serve fused results with the per-cluster cap applied and record the degraded mode.
- **Multi-tenant deployments**: Bind the tenant predicate outside model control in every route, including caches, overlays, rerankers, evaluation harnesses, and prior index generations, and test leakage against each of them separately, since a single unfiltered route defeats every other correct one.

***

## V. Limitations and Considerations

**Retrieval is approximate and offers no completeness guarantee**: Similarity ranking can miss an eligible record that answers the request, and no amount of threshold tuning converts approximate retrieval into a guarantee. The consequence is that absence of a retrieved record is never evidence that no such record exists. The mitigation is the abstention rule in Step 5.3, which requires the agent to state that no eligible span cleared threshold rather than to answer as though the store were empty, together with the lexical route that preserves exact-term recall the dense route loses.

**Correctness cannot be verified by constraint**: No schema check catches a reversed negation, a swapped unit, or a misattributed quotation inside a free-form body, so the store can hold a confidently wrong record indefinitely. The consequence is that error detection depends entirely on comparison against a source span or on human adjudication. The mitigation is the extractive-storage requirement for quantities, deadlines, identifiers, negations, and commitments in Step 1.2, and the citation support threshold in Step 5.3, which withholds an answer whose cited span does not entail it.

**Every numeric threshold here is a deployment default**: The similarity thresholds, cluster caps, severance rates, coverage requirements, and horizon multipliers were selected to be operable on first deployment, not derived from a measured property of any particular corpus. The consequence is that a store adopting them unchanged will be either too permissive or too strict for its content mix. The mitigation is the threshold recomputation requirement in Section III.D, which obliges each deployment to recompute every bound per content class against observed outcomes before treating it as settled.

**Deduplication and fidelity trade against one another**: Raising merge recall to control accumulation raises the risk of collapsing a refinement or a contradiction into a duplicate, and a false merge destroys a qualifier that may carry the entire meaning of the record. The consequence is that neither metric can be maximised alone. The mitigation is the asymmetric gate in Step 4.2, which holds merge precision at 0.98 and corrects recall shortfalls by lowering the review threshold rather than the precision bar, together with the reversibility requirement in Step 4.3.

**Model-tier judgement is being asked to detect its own failure modes**: Contradiction detection, semantic deduplication, and summarisation are performed by the same class of component that produced many of the bodies being judged, and self-assessment shares the blind spots that generated the content. The consequence is that a model-only pipeline can converge on a confident, internally consistent, and wrong store. The mitigation is the tier partition in Section 1.4, which admits model output only as a proposal, and the independence assessment in Step 4.2, which prevents a descendant from corroborating its ancestor.

**Compaction is irreversible loss presented as maintenance**: A summary that passes every automatic gate may still have dropped the detail a future question needed, and no automatic metric fully establishes that a summary is supported by its source. The consequence is that storage reduction can quietly reduce future task success. The mitigation is the answer-preservation gate in Step 6.2, the must-preserve set, the derivative depth cap of 3, and the archival preference in favour of deletion wherever wording, rare detail, native media, or audit value makes loss unacceptable.

**Erasure completeness is asserted more often than it is verified**: Personal data derived from a deleted source persists in embeddings, summaries, caches, exports, evaluation sets, and backups, and a deletion reported as complete after a single keyed lookup is routinely wrong. The consequence is regulatory and reputational exposure that surfaces only when someone probes. The mitigation is the multi-method verification requirement in Step 6.3, the tombstone-before-purge ordering, and the scheduled-purge disclosure for backups that cannot be reached immediately.

**Governance conformance is not usefulness**: A store can satisfy every checkpoint in this guide, leak nothing, duplicate nothing, and still fail to help, because it admitted content the workload never needed. The consequence is a well-governed archive rather than a memory system. The mitigation is the baseline comparison in Section III.D, which requires the store to beat the strongest simpler alternative on task success and cost before it is treated as earning its place.

***

## VI. Conclusion and Summary

Unstructured memory is a governance discipline before it is a retrieval technique. Its defining trade is explicit: the body accepts content no schema anticipated, and in exchange the system gives up exact retrieval, constraint-based verification, enforced uniqueness, and cheap erasure. A deployment that accepts the first half of that trade without building for the second half produces a store that grows, duplicates, ages, and leaks, and that discovers each of those only when a user notices a wrong answer.

The four decay modes are what separate a store that lasts from one that is quietly abandoned. Near-duplicate accumulation converts repetition into apparent consensus. Silent staleness serves a superseded state with no visible marker. Boundary severance returns a fragment whose meaning reverses its source. Embedding version drift makes distances incomparable without changing a single visible field. None of the four announces itself, each is detectable by a measurement stated in this guide, and each has a remedy that must be scheduled rather than improvised after an incident.

A team introducing unstructured memory should start with one canonical text store, object storage for native evidence, a strict scope envelope, lexical retrieval, exact source offsets, redaction, and a labelled evaluation corpus. Embeddings, vector services, hybrid fusion, rerankers, semantic deduplication, context headers, self-editing files, and recursive summarisation are each added only after an ablation shows a measured gap the simpler configuration could not close. Typed projections take the fields that stabilise, episodes keep what happened, graphs keep relationships, and working context keeps what is bounded and used once.

**Key Success Factors**:

- **Envelope before body**: Scope, purpose, audience, source, authority, sensitivity, and validity are populated before any content reaches an index, because the envelope is the enforcement surface a free-form body cannot supply.
- **Eligibility before relevance**: Hard predicates are evaluated before any scoring runs, and a similar but ineligible result is a defect rather than a near miss.
- **Proposal before application**: The model tier proposes merges, invalidations, and summaries; a deterministic gate applies them, holds authority in every disagreement, and preserves provenance through each one.
- **Addressability before derivation**: Every chunk, vector, caption, transcript, and summary resolves to an exact span in an immutable source version, so citation, correction, re-chunking, and erasure all remain possible.
- **Measured decay before remediation**: Each of the four decay modes carries a numeric trigger that fires from routine measurement, so degradation is caught by instrumentation rather than by a complaint.
- **Verified deletion before closure**: A deletion is closed only when the derivative graph has been re-enumerated and probed by multiple methods, because derived personal data outlives the transcript it came from.

By following this guide, AI agents can hold content that no schema anticipated while still being able to explain why each record was written, who may retrieve it, which exact source supports it, how much was lost in every transformation, when it stops being current, and how every copy of it will be erased.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, and were not independently re-verified in the course of this conversion, except where an entry is marked as confirmed during the research performed for this restructuring.

**Corpus pointers**:

- `Contextual Unstructured Memory for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the governed envelope field families, the representation selection criteria, the write content policy, the chunking and offset discipline, the policy-first retrieval sequence, the compaction and answer-preservation treatment, the failure-mode inventory, the telemetry field inventory, and the staged build loop. Its inline citations to primary literature on chunking, contextual retrieval, deduplication, factual consistency, recognition models, privacy regulation, and memory benchmarking supply the external references listed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on the overall memory architecture into which this content layer fits, including the store taxonomy referenced by the selection rule in Section 1.2.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on trajectory and event storage, applicable wherever the selection rule in Section 1.2 routes a sequence of action, observation, and outcome away from the free-form store.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on consolidation, applicable to the compaction and derivative-depth treatment in Step 6.2.
- `advanced_task_guides/memory-management/guide_AttentionBasedMemoryRetrieval.md` — companion guidance on retrieval scoring and selection, applicable to the candidate generation and reranking steps in Phase 5.
- `advanced_task_guides/memory-management/guide_StructuredMemory.md` — the representation this guide is defined against by the selection rule in Section 1.2. It owns content queryable by exact predicate, joinable, and validatable against a schema before admission; this guide owns bodies no schema constrains and the metadata envelope carried alongside them.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — owns retention policy, the separation of utility forgetting from obligation erasure, and the coverage proof a case requires; applicable to the four decay modes in Section 1.3 and the verified deletion across derivatives in Step 6.3.
- `advanced_task_guides/memory-management/guide_LatentMemoryNetworks.md` — owns encoder selection, the representation fingerprint, approximation tuning, and index generation lifecycle; applicable to the representation pinning in Step 3.1 and the migration cutover in Step 3.3, which this guide states as requirements rather than as method.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — companion guidance on bounded in-context state, applicable to the working-context row of the selection matrix in Section 1.2.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on schema evolution, applicable to the promotion and demotion path in Section 1.2.
- `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md` — companion guidance on entity resolution and duplicate adjudication, applicable to the clustering and merge steps in Phase 4.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on provenance and evidence lineage, applicable to the source pointer and merge provenance requirements in Phases 2 and 4.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the decision records every phase of this framework emits.

**External references**: Entries 1 through 19 are transcribed from the originating prose guide. Entries 20 through 23 were retrieved during the research performed for this restructuring and their content was confirmed at the time of retrieval.

*Chunking, contextual retrieval, and hybrid ranking*

1. Anthropic, *Contextual Retrieval in AI Systems* — https://www.anthropic.com/engineering/contextual-retrieval
2. *Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models* — https://arxiv.org/abs/2409.04701
3. Liu and colleagues, *Lost in the Middle: How Language Models Use Long Contexts* — https://arxiv.org/abs/2307.03172
4. Elastic, *Reciprocal Rank Fusion* — https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
5. SQLite, *FTS5 Full-Text Search Extension* — https://www.sqlite.org/fts5.html
6. pgvector, *Open-Source Vector Similarity Search for Postgres* — https://github.com/pgvector/pgvector

*Deduplication and near-duplicate detection*

7. *Scalable Near-Duplicate Detection for Clinical Notes Using MinHash and Locality-Sensitive Hashing* — https://arxiv.org/abs/1704.05617
8. *SemDeDup: Data-Efficient Learning at Web-Scale Through Semantic Deduplication* — https://arxiv.org/abs/2303.09540

*Summarization fidelity and memory evaluation*

9. Kryscinski and colleagues, *Evaluating the Factual Consistency of Abstractive Text Summarization* — https://arxiv.org/abs/1910.12840
10. *QAFactEval: Improved QA-Based Factual Consistency Evaluation for Summarization* — https://arxiv.org/abs/2112.08542
11. *LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory* — https://arxiv.org/abs/2410.10813
12. *MemoryAgentBench: Evaluating Memory in LLM Agents* — https://arxiv.org/abs/2507.05257
13. *A Survey of Memory in Large Language Model Agents* — https://arxiv.org/abs/2602.06052
14. *Anatomy of Agentic Memory* — https://arxiv.org/abs/2602.19320

*Content safety, provenance, and privacy*

15. OWASP, *LLM01: Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
16. *Bad Memory: Persistent Injection in Agent Memory Files* — https://arxiv.org/abs/2607.14611
17. Microsoft, *Presidio: Data Protection and De-Identification SDK* — https://data-privacy-stack.github.io/presidio/
18. W3C, *PROV-O: The PROV Ontology* — https://www.w3.org/TR/prov-o/
19. Information Commissioner's Office, *Right to Erasure* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/

*Retrieved and confirmed during this restructuring*

20. Qdrant, *Embedding Model Migration* — https://qdrant.tech/documentation/tutorials-operations/embedding-model-migration/
21. Microsoft, *Hybrid Search Scoring in Azure AI Search* — https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking
22. OpenSearch, *Introducing Reciprocal Rank Fusion for Hybrid Search* — https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/
23. *STALE: Can LLM Agents Know When Their Memories Are No Longer Valid?* — https://arxiv.org/abs/2605.06527
