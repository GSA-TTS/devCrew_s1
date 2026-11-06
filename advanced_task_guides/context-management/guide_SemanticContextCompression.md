# Semantic Context Compression

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Semantic context compression constitutes the task family of reducing the rendered token cost of context by changing how meaning is represented rather than by deleting content at a position. Its operations are abstraction, densifying paraphrase, cross-item redundancy merging, and the replacement of extended passages with anchored propositional content. This guide provides AI agents with a structured protocol for performing that reduction safely: a six-phase framework covering candidate qualification with software-enforced exclusion of protected content classes, method selection by content type, anchored semantic reduction, cross-item merging behind a deterministic material-difference gate, meaning-preservation verification through a probe harness with numeric pass thresholds and stated sample sizes, and outcome measurement returning corrections to policy. It states which content classes are never eligible for semantic reduction and must travel verbatim or by reference, namely identifiers, quantities with units, quoted material, legal and contractual language, code, and anything that will later be cited. It fixes the execution tier partition in which the model tier performs abstraction and proposes equivalence while the deterministic tier enforces exclusion, executes verification, and holds the admission verdict. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that reduction which preserves meaning is demonstrated by measurement rather than asserted by the compressor that produced it.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Semantic compression**: A lossy reduction in which at least one decision is made over a meaning representation rather than over surface form. Deciding that two differently worded passages assert the same thing, replacing a narrated sequence with the propositions it establishes, and raising a set of specific observations to the generalisation they share are semantic decisions. Shortening text by deleting low-probability tokens is not, regardless of whether a language model performed the deletion.

**Propositional content**: The set of atomic, independently testable assertions a passage establishes, each stated in a concise self-contained form. Proposition-level units are the working currency of this guide because they can be enumerated, anchored to a source span, compared for equivalence, and probed individually. Reported work on retrieval granularity found that indexing by propositions outperformed passage-level units on retrieval and on downstream question answering under a fixed computation budget [1].

**Abstraction**: The replacement of several specific propositions with one more general proposition that entails a weaker claim than the set it replaces. Abstraction is the highest-yield semantic operation and the most destructive, because the discarded specificity is exactly what a later step may require and the resulting text carries no marker that it was ever more specific.

**Densifying paraphrase**: The restatement of one proposition in fewer tokens without changing what it asserts. Paraphrase preserves propositional content by design and preserves exact wording by no design at all, which is why it is prohibited over any region whose wording carries decision weight.

**Extraction**: The retention of a subset of original spans verbatim, discarding the remainder. Extraction is not semantic compression, it is span-level selection, and it is preferred over semantic compression wherever the value of a region resides in specific spans rather than in their aggregate, because it introduces no assertion that lacks a source span.

**Truncation**: The removal of a contiguous region by position, without reference to what the region asserts. Truncation loses everything in the removed region and nothing outside it, so its loss is total, bounded, and locatable. Semantic compression trades that predictability for a higher retention of propositional content per token, and takes on in exchange a loss that is distributed, partial, and invisible in the output.

**Verbatim-carry class**: A content class that is never eligible for semantic reduction and must be carried through the operation byte-identical or replaced by a reference to a durable copy. The membership list is fixed in Section 1.2 and is enforced by deterministic detection and masking, never by an instruction to the compressor.

**Anchor**: An opaque, reversible placeholder token substituted for a verbatim-carry span before the compressible region reaches the model tier, and reinstated with the original bytes after generation. An anchor removes the opportunity to paraphrase protected content rather than discouraging it.

**Claim anchor**: The source span identifier attached to every proposition in a reduced artifact, binding the assertion to the location that supports it. A proposition without a claim anchor is a hypothesis the compressor introduced, not compressed evidence.

**Material difference**: A discrepancy between two apparently redundant items in any field whose change alters what the item asserts: entity association, identifier, numeric value, unit, tolerance, polarity, modality, validity interval, version, jurisdiction, scope, attribution, or condition structure. A single material difference blocks a merge irrespective of any similarity score or model equivalence judgement.

**Merge witness**: The record written for every accepted merge, naming the members, the field-by-field comparison that found no material difference, the bidirectional entailment verdict, the retained canonical rendering, and the path back to every member. A merge without a witness is irreversible and is refused.

**Support ledger**: The accounting of how many distinct provenance families assert a merged claim, kept alongside the raw member count. The independent support count is adopted unchanged from the memory-consolidation vocabulary through the general compression guidance, and it binds here because collapsing two independent attestations into one destroys corroboration while presenting as duplicate removal.

**Meaning-preservation probe**: A question constructed from the uncompressed original, carrying a deterministic answer key derived from a specific source span, and answered against the compressed artifact alone with the original withheld. Probes are the operational test that meaning survived; the readability of the artifact is not evidence of anything.

**Probe pass rate**: Probes answered correctly against the compressed artifact divided by probes retained in the denominator after control filtering. It is the acceptance metric of this guide, and it is computed by deterministic grading wherever the answer key admits it.

**Control run**: The execution of the probe set against the uncompressed original before the compressed artifact is scored. A probe that fails against the original is defective, is removed from the denominator, and is logged as a probe defect rather than as a compression success.

**Abstraction-level creep**: The failure mode in which each successive semantic pass raises the artifact one rung of generality, so that a lineage of individually acceptable reductions terminates in a topic list that asserts nothing checkable. It is the semantic-specific expression of the cumulative degradation the general compression guidance bounds by compression depth.

**Enumeration collapse**: The replacement of an explicit list by a count word or vague quantifier, destroying the member count, the member identities, and the completeness of the list in one substitution that reads as a harmless summary.

**Qualifier attrition**: The progressive loss of negations, hedges, modal verbs, conditions, exceptions, and attributions across semantic passes. It is the mechanism by which error laundering occurs, and the term error laundering is adopted unchanged from the general compression guidance rather than redefined here.

**Semantic operation ladder**: The ordering of semantic operations from least to most destructive: typed projection, densifying paraphrase, cross-item merge, proposition-set reduction, and abstraction. Entry at the least destructive rung that meets the declared budget is mandatory, and skipping rungs requires a recorded reason code.

**Typed projection**: The reduction of prose to a declared schema of fields, entities, relations, and qualifiers, discarding material the schema does not carry. Projection is lossy with respect to the discarded material and lossless with respect to the declared contract, which is why the contract is named before the transformation runs and the overflow is logged rather than dropped silently.

**Conditioning task**: The declared question family, output contract, and decision the compressed artifact must support. Meaning is relative to it: a date is central to a timeline and irrelevant to topic classification, and no reduction can be judged safe without it.

**Loss budget**: The declared, enumerated set of content the operation is permitted to lose, stated before generation and expressed as content classes rather than as a token target. A loss budget stated only as a compression ratio permits the compressor to choose what disappears.

**Terms adopted without redefinition**: preservation manifest, preservation set, protected atom, zero-tolerance class, fidelity class, compression depth, regeneration, error laundering, uncompressed baseline, replay set, task-outcome retention, compression ratio, redundancy class, independent support count, consequence class, trust class, rollback, reference substitution, and reason code. All are defined by the general context compression guidance in this category, and this guide uses them with those definitions and adds no variants.

### 1.2 What Semantic Compression Preserves and What It Destroys

**The governing asymmetry**: Semantic compression preserves what a passage asserts and destroys how the passage said it. Propositional content and the relations among propositions survive well, because they are what an abstractive compressor is optimised to carry. Exact wording, quantitative precision, and provenance-bearing detail do not, because nothing in the operation obliges them to and nothing in the output reveals their absence. The loss is selected rather than random, and its class is predictable even where its instance is not. That asymmetry makes an enumerated exclusion list enforceable and an instruction to preserve important details worthless.

**Preservation behaviour by content class**

| Content class | Behaviour under semantic reduction | Required treatment |
| :-- | :-- | :-- |
| Propositional content and claims | Preserved reliably at one pass; attrition begins at the second | Compressible with claim anchors retained |
| Relations among propositions | Preserved where explicitly rendered; lost where implied by adjacency | Compressible only where relations are rendered as typed statements |
| Topical and thematic structure | Preserved; usually the last content to degrade | Compressible |
| Decision rationale | Preserved in outline; the discriminating alternative is commonly dropped | Compressible only where alternatives are enumerated in the output |
| Exact wording and phrasing | Destroyed by construction | Verbatim-carry or reference |
| Quantities, units, tolerances, and ranges | Rounded, unit-stripped, or re-associated to the wrong entity | Verbatim-carry |
| Stable identifiers | Truncated, normalised, or silently corrected to a plausible neighbour | Verbatim-carry |
| Negation, modality, hedging, and conditions | Attrited progressively; the artifact reads more certain than its input | Verbatim-carry for the marker; compressible for the surrounding clause |
| Attribution and provenance detail | Dissolved into the artifact's own voice | Verbatim-carry or reference |
| Enumerations and list completeness | Replaced by a count word or a vague quantifier | Verbatim-carry where completeness is load-bearing |
| Quoted material and attributed speech | Paraphrased into indirect report, destroying the quotation | Verbatim-carry |
| Legal, contractual, and regulatory language | Restated into ordinary prose with a different scope | Verbatim-carry |
| Code, configuration, commands, and queries | Rewritten into descriptions that do not execute | Verbatim-carry or reference |

**The verbatim-carry class**: Seven classes are never semantically compressed under any budget pressure, in any consequence tier, and regardless of the conditioning task. They travel byte-identical or as a reference to a durable copy: stable identifiers of every kind, including versions, digests, paths, ports, ticket keys, and account references; quantities with their units, tolerances, and entity associations; quoted material and directly attributed speech; legal, contractual, regulatory, and policy language; code, configuration, commands, queries, and structured records; safety constraints, permissions, and prohibitions; and any content that a downstream step will cite, reproduce, or present as evidence. The first six are recognisable by pattern and schema. The seventh is declared by the conditioning task in Step 1.3 and is the one an agent most often omits, because the citation requirement usually arises after the compression that destroyed the ability to satisfy it.

**Exclusion is enforced by software, not by instruction**: A compressor told to preserve identifiers exactly preserves most of them. The residue is a defect rate that scales with volume and is undetectable in the artifact. The enforceable form replaces every detected verbatim-carry span with an anchor before the region reaches the model, so the protected bytes are never in the compressor's input and cannot be rewritten, and reinstates them after generation by exact substitution. Detection recall is therefore the only variable that matters, and the deterministic detectors are versioned, tested against a golden case set, and extended by every production miss.

**Semantic similarity is not evidence of preservation**: A high embedding similarity establishes that an artifact and its source discuss the same subject, not that a negation survived or that a number kept its unit and its entity. The general compression guidance permits similarity as a triage signal and prohibits it as an acceptance criterion, and that prohibition is inherited here without relaxation.

### 1.3 Scope, the Agent-Layer Boundary, and the Boundary With the General Compression Guide

**What sits below the agent layer**: Learned and model-internal compression is named here as background only, because an agent cannot execute it and misattributing an agent-layer failure to it wastes diagnosis. Approaches that train a model to distil prompts into reusable compressed tokens [9], that encode long context into memory slots consumed by a compatible decoder [10], that build recursive summary vectors used as soft prompts [11], and that project a retrieval embedding into a model token through a trained bridge [12] all require a compressor trained jointly with the serving model, a serving stack that accepts non-text inputs, and versioned invalidation of the latent artifacts on every checkpoint change. A survey of prompt compression records that soft encoders are commonly tied to one decoder, may require retraining after a model upgrade, and can cost nearly as much as processing the original prompt [13]. Web research during this conversion confirmed that soft prompts remain non-transferable to API-served models. No prompting, tool call, or script reaches that surface, so the material is a declared referral rather than an instruction.

**Two adjacent families that are not this method**: Learned token pruning retains natural-language tokens and decides retention by classification over surface tokens [14]; it is a rung of the general compression ladder and is not latent compression, and labelling it as such misassigns both its costs and its failure modes. Vector-level compression, covering supported dimension truncation, scalar, product, and binary quantization, and index structure selection, reduces index memory, bandwidth, and search cost; it reduces rendered prompt tokens only where a later retrieval or rendering step returns less text. It is therefore out of scope here and belongs to retrieval infrastructure. A vector compression ratio is never reported as a prompt compression ratio.

**The agent-layer surrogate that is executable**: Semantic compression in this guide is text in and text out, or structured record in and structured record out. Its exclusion contract lives outside the model in a detector-enforced partition rather than inside the compressor's judgement. Its meaning-preservation evidence is a probe run scored deterministically rather than a reading of the artifact. Every phase below is executable through prompting, tool calls, file and store operations, and token accounting available to an ordinary agent runtime.

**Boundary with the general compression guidance**: The general context compression guidance in this category owns the compression operation and its governance. It owns the preservation manifest and its construction, the mechanical preservation check, the admission verdict, compression-depth accounting and the depth ceiling, regeneration from depth-zero sources, reference substitution as the reversible alternative, rollback, and the replay measurement against the uncompressed baseline. None of that machinery is restated here, and no threshold stated here relaxes one stated there. This guide owns the semantic method specifically: how meaning-preserving reduction is performed, how it is distinguished from truncation and from extraction, which content classes it may never touch, how cross-item redundancy is merged without discarding a material difference, how the survival of meaning is tested rather than assumed, and where the method fails. Where the two guides both bear on a step, the general guidance holds authority, and this guide's outputs enter its preservation manifest and its verification as inputs.

**Boundary with the other siblings**: The umbrella context-management guidance selects the compress family for a pressure event, and this guide is entered only after that selection and after the general guidance has routed the candidate to a semantic technique. Context selection patterns owns what earns a slot in the window, and semantic compression is never used to answer a relevance question. Context write patterns owns durable writes, entity resolution, graph mutation, shape validation, and provenance records, so the typed projection in this guide emits candidate records into that guide's controls rather than committing them. Context isolation patterns owns splitting work across separate windows, which is the structural alternative when no safe semantic reduction remains.

### 1.4 Execution Tier Partition

Semantic compression is a hybrid capability, and its production failures are almost entirely misassignments of work across execution tiers. The single rule that carries the method is this: the model tier proposes a reduction and the deterministic tier admits it, and a compressed artifact enters the working set only after the deterministic probe run and the material-difference gate have both passed. There is no path that admits an artifact with a warning attached, because the next inference reads the artifact and not the warning.

The deterministic tier owns protected-class detection, anchor substitution and reinstatement, token accounting, candidate blocking, material-difference field comparison, support-ledger arithmetic, probe harness execution and scoring, and the rollback path, because each requires exactness, reproducibility, and auditability that inference cannot supply. The model tier owns abstraction and densifying paraphrase, the proposal that two items are equivalent, and the drafting of probe questions, because condensing open-vocabulary content and recognising that two differently worded passages assert the same thing are covered by no deterministic rule. In every hybrid cell the deterministic component holds authority when the two disagree.

**Tier ownership by artifact**

| Artifact | Owning tier | Authority where the tiers disagree |
| :-- | :-- | :-- |
| Verbatim-carry detection and the region partition | Deterministic | Deterministic; a model assertion that a span is safe to paraphrase never removes its anchor |
| Anchor substitution before generation and reinstatement after | Deterministic | Deterministic; a reduced artifact with an unreinstated anchor is rejected outright |
| Rendered token counts before and after, and the realised reduction | Deterministic | Deterministic; a model estimate of tokens saved is advisory only |
| Merge candidate generation by blocking key | Deterministic | Deterministic; similarity search runs inside blocks and never across them |
| Material-difference field comparison | Deterministic | Deterministic; a mismatch on any gated field blocks the merge regardless of the equivalence proposal |
| Support ledger and independent support count | Deterministic | Deterministic; support is counted from provenance records, never asserted |
| Probe answer keys, probe execution, and deterministic grading | Deterministic | Deterministic; the compressor never grades its own artifact |
| Probe pass rate and the admission verdict | Deterministic | Deterministic; the verdict is admit or discard and nothing else |
| Rollback execution and invalidation of derived artifacts | Deterministic | Deterministic; rollback runs regardless of model objection |
| Abstraction, densifying paraphrase, and artifact drafting | Model | Model drafts; the probe run may discard the draft entirely |
| Equivalence and restated-claim proposals | Model | Model proposes; the material-difference gate decides |
| Probe question drafting for open-vocabulary regions | Model | Model drafts; every probe requires a deterministic answer key before it enters the set |
| Open-vocabulary probe grading within its permitted share | Model | Model grades; disagreement between graders resolves to fail |
| Semantic operation selection within the ladder | Hybrid | Model may propose a rung; the ladder ordering and entry conditions bind absolutely |
| Conditioning-task and loss-budget declaration | Hybrid | Model states the next decision's needs; declared policy defaults bind, and the stricter treatment wins |

**What the deterministic tier rejects outright**: An artifact containing an unreinstated anchor or an anchor reinstated with bytes that differ from the source; an artifact whose probe pass rate falls below the threshold for its consequence class; an artifact failing any protected-class probe; an artifact answering a probe that the source does not support; a merge whose members differ on any gated field; a merge lacking a witness record; an artifact whose rendered token count exceeds its declared output budget; and an artifact asserting a proposition that carries no claim anchor.

**What the model tier is never permitted to decide alone**: Whether a span belongs to a verbatim-carry class, whether its own artifact preserved meaning, whether two items differing on a gated field are the same item, whether a probe may be removed from the denominator, whether a loss budget may be widened after generation, and whether a semantic policy continues after a threshold breach.

***

## II. Operational Framework: Meaning-Preserving Reduction Under a Verified Probe Gate

The framework produces one auditable artifact per semantic compression event: a reduced representation carrying claim anchors, an anchor reinstatement report, a merge witness set where cross-item merging ran, a probe run with its pass rate and per-class breakdown, and a route back to the frozen original. Phase 1 runs after the general compression guidance has selected a semantic technique and frozen the candidate. Phases 2 through 5 run once per candidate and terminate in admission or rollback. Phase 6 runs asynchronously over completed events and returns corrections to Phases 1 and 2. The framework does not restate the preservation manifest construction, the mechanical preservation check, the depth ceiling, or the rollback mechanics owned by that guidance; it supplies the semantic operation, the exclusions it must respect, and the evidence that meaning survived it.

### Phase 1: Candidate Qualification and Protected-Class Exclusion

**Objective**: Establish that semantic reduction is the correct operation for this candidate, remove every content class it may not touch from the compressor's reach by software, and declare the task the reduction is conditioned on before any generation occurs.

#### Step 1.1: Confirm Semantic Reduction Is the Correct Operation for the Candidate

**Required Actions**:

- Confirm the candidate has been frozen with a version identifier and a content digest by the general compression guidance, and refuse to operate on a live buffer, since the probe run in Phase 5 requires an immutable comparand.
- Compare the candidate against the three cheaper reductions in order and record why each was insufficient: deterministic normalisation of representation overhead, exact and structural duplicate removal, and extraction of the spans that carry the value.
- Prefer extraction over semantic reduction wherever the region's value resides in specific spans, since extraction introduces no assertion lacking a source span and its loss is locatable.
- Prefer reference substitution over semantic reduction wherever the content is recoverable on demand and the next decision needs only a handle to it, delegating the execution to the write patterns controls.
- Estimate the realised reduction as rendered source tokens minus projected artifact tokens, and refuse the event where the projection falls below 20 percent of the candidate's rendered tokens, since the probe harness and merge gate cost more than a smaller saving returns.
- Refuse the event outright where the candidate consists wholly of verbatim-carry classes, and route it to reference substitution or isolation instead.

**Required Outputs**:

- A qualification verdict naming the frozen candidate version and digest.
- A cheaper-reduction record naming each of the three alternatives and the reason it was insufficient.
- A projected reduction figure in rendered tokens and as a percentage of the candidate.

**Quality Checkpoints**:

- The candidate carries a frozen version identifier and digest; an unfrozen candidate halts the event.
- All 3 cheaper reductions were evaluated and their insufficiency recorded; an unevaluated alternative halts the event.
- The projected reduction is at least 20 percent of rendered candidate tokens; below that the event is refused and the refusal is logged with a reason code.
- No candidate composed entirely of verbatim-carry content proceeds past this step.

***

#### Step 1.2: Detect and Anchor Every Verbatim-Carry Span

**Required Actions**:

- Run the versioned deterministic detectors over the frozen candidate for all six pattern-recognisable verbatim-carry classes: identifiers, quantities with units, quoted and directly attributed material, legal and contractual language, code and structured records, and safety constraints, permissions, and prohibitions.
- Run a model pass afterwards over the same candidate proposing spans the detectors did not recognise, and admit every proposal into the protected partition without adjudication, since over-protection costs tokens while under-protection costs correctness.
- Substitute an opaque anchor for every protected span before any region reaches the compressor, and record the anchor identifier, the exact byte range, the source span identifier, and the class that triggered protection.
- Attach to each anchor the scope of the qualifier or association it carries, so that a unit stays bound to its value and a negation stays bound to its clause when the surrounding prose is rewritten.
- Partition the remainder into compressible regions, and mark any region whose protected density exceeds 40 percent of its rendered tokens as not worth compressing, routing it to verbatim carry.

**Required Outputs**:

- An anchor table with one row per protected span carrying its identifier, byte range, source span identifier, and protection class.
- A compressible region partition with rendered token counts per region.
- A detector version record and a per-class recovery count.
- A model proposal record naming the spans no detector recognised.

**Quality Checkpoints**:

- Every protected span carries an anchor and a byte range; a protected span identified without a byte range is a detection defect and halts the step.
- No protected byte appears in any payload sent to the model tier; a single leaked protected byte halts the event and opens a detector review.
- No span is removed from the protected partition on a model assertion that it is safe to paraphrase.
- Every region whose protected density exceeds 40 percent is routed to verbatim carry rather than compressed.

***

#### Step 1.3: Bind the Conditioning Task and Declare the Loss Budget

**Required Actions**:

- State the conditioning task as a question family, an output contract, and the decision the artifact must support, and record it in structured state that the probe builder in Step 5.1 reads.
- Declare the loss budget as an enumerated list of content classes the operation may lose, never as a token target alone, since a ratio permits the compressor to choose what disappears.
- Add to the verbatim-carry partition every element the conditioning task will require to be cited, reproduced, or quoted downstream, since this class is declarative rather than detectable.
- Set the output token budget and the consequence class, and inherit the acceptance thresholds, the depth ceiling, and the rollback target from the preservation manifest the general compression guidance has already fixed for this candidate.
- Write the reduction record before generation begins, so that the declared budget cannot be widened after a failing artifact is produced.

**Semantic Reduction Record**

```
REDUCTION_ID:
CANDIDATE_VERSION_ID:
CANDIDATE_CONTENT_DIGEST:
MANIFEST_ID:                  reference to the preservation manifest held by the general guidance
CONSEQUENCE_CLASS:            low | moderate | high
TRUST_CLASS:
CONDITIONING_TASK:
  QUESTION_FAMILY:
  OUTPUT_CONTRACT:
  DOWNSTREAM_DECISION:
  CITATION_REQUIRED_ELEMENTS:
LOSS_BUDGET_CLASSES:
  - CLASS:
    PERMITTED_LOSS:           full | partial | none
PROTECTED_PARTITION:
  - ANCHOR_ID:
    PROTECTION_CLASS:         identifier | quantity | quotation | legal | code | constraint | citation_target
    SOURCE_SPAN_ID:
    BYTE_RANGE:
COMPRESSIBLE_REGIONS:
  - REGION_ID:
    RENDERED_TOKENS:
    SEMANTIC_STRUCTURE:       narrative | enumerative | argumentative | repetitive_set | record_set
    SELECTED_RUNG:
OUTPUT_TOKEN_BUDGET:
PROBE_SET_SIZE_REQUIRED:
PROBE_PASS_THRESHOLD:
MAX_ATTEMPTS:
ROLLBACK_TARGET_VERSION_ID:
HUMAN_APPROVAL_REQUIRED:
```

**Required Outputs**:

- A conditioning task record with its question family, output contract, downstream decision, and citation-required elements.
- A loss budget enumerated by content class with a permitted-loss value per class.
- A completed semantic reduction record written to durable state before generation.

**Quality Checkpoints**:

- The loss budget names content classes; a budget expressed only as a target ratio is rejected.
- Every citation-required element named by the conditioning task appears in the protected partition.
- The reduction record exists in durable state before any generation call is issued; a record reconstructed after generation is a governance defect.
- The consequence class and thresholds match those already fixed in the preservation manifest; a locally relaxed threshold halts the event.

***

### Phase 2: Compression Method Selection by Content Type

**Objective**: Assign each compressible region the least destructive semantic operation that meets its share of the output budget, so that abstraction is reached only where cheaper meaning-preserving operations have been shown insufficient.

#### Step 2.1: Classify Each Compressible Region by Semantic Structure

**Required Actions**:

- Assign each region exactly one semantic structure from five values: narrative, where the meaning is a sequence of events; enumerative, where the meaning is a list whose completeness matters; argumentative, where the meaning is a claim supported by reasons; repetitive set, where many items assert overlapping content; and record set, where the content is already field-structured.
- Default to the structure whose safe operations are most restrictive wherever the classification is contested, since a misclassified enumerative region loses its completeness silently.
- Measure the redundancy density of every repetitive set as the proportion of items sharing a blocking key with at least one other item, since this figure predicts the available saving from Phase 4 more reliably than region size.
- Record for each region the proportion of its rendered tokens occupied by anchors, since a region dense with anchors yields little to abstraction and much to reference substitution.
- Refuse the narrative structure for any region whose ordering carries procedural or causal weight unless the selected operation renders the ordering explicitly.

**Required Outputs**:

- A region classification record with one semantic structure value per region.
- A redundancy density figure per repetitive set.
- An anchor density figure per region.

**Quality Checkpoints**:

- Every compressible region carries exactly one semantic structure value; an unclassified region does not proceed.
- Contested classifications resolved to the more restrictive value, and the contest is recorded.
- Redundancy density is computed from blocking keys rather than from a similarity score.

***

#### Step 2.2: Enter the Semantic Operation Ladder at the Least Destructive Rung

**Required Actions**:

- Enter the ladder at the least destructive rung whose projected reduction meets the region's share of the output budget, and record a reason code wherever a rung is skipped.
- Select typed projection for record sets and for any region whose downstream consumer has a stable field contract, declaring the schema and logging the overflow rather than discarding it silently.
- Select densifying paraphrase for regions whose propositions are already distinct and whose cost is verbosity rather than repetition.
- Select cross-item merging for repetitive sets whose redundancy density is at least 0.30, since below that figure the merge gate costs more than the collapse returns.
- Select proposition-set reduction, which discards propositions the conditioning task does not require while keeping the survivors anchored, before considering abstraction.
- Select abstraction last, only for regions where the conditioning task asks a global question, and never for enumerative regions whose completeness is load-bearing.

**Semantic operation ladder and its entry conditions**

| Rung | Operation | Entry condition | What it destroys | Prohibited for |
| :-- | :-- | :-- | :-- | :-- |
| 1 | Typed projection to a declared schema | Downstream consumer has a stable field contract | Everything the schema does not carry, which is logged as overflow | Regions whose relevant concepts are not known in advance |
| 2 | Densifying paraphrase | Propositions are distinct and phrasing is verbose | Exact wording only | Any region carrying quotation or contractual language |
| 3 | Cross-item redundancy merge | Redundancy density at or above 0.30 | Duplicate renderings; never the support ledger | Sets whose source independence cannot be established |
| 4 | Proposition-set reduction | Conditioning task is narrow and stable | Propositions outside the task frame, recoverable only from source | Regions whose future question family is unknown |
| 5 | Abstraction to a general claim | Conditioning task asks a global question | Specificity, quantities, and enumeration completeness | Enumerative regions and any region feeding a citation requirement |

**Required Outputs**:

- A rung assignment per region with its entry condition satisfied and recorded.
- A skip record naming every rung bypassed and the reason code for the bypass.
- A projected reduction per region at the selected rung.

**Quality Checkpoints**:

- No region was assigned a rung whose entry condition is unsatisfied; an unsatisfied entry condition halts the assignment.
- Every skipped rung carries a reason code from the closed vocabulary; an unexplained skip is a policy defect.
- No enumerative region whose completeness is load-bearing was assigned rung 5.
- No region feeding a citation-required element was assigned rung 4 or rung 5.

***

#### Step 2.3: Fix the Target Reduction and the Rendering Contract

**Required Actions**:

- Set a per-region target reduction rather than one global ratio, since a uniform ratio applies the same destruction to a dense record set and a repetitive log.
- Cap the target reduction at 70 percent of rendered region tokens for moderate consequence regions and at 50 percent for high consequence regions, and treat a request above the cap as a signal to substitute a reference rather than to compress harder.
- Declare the rendering contract for the artifact: every proposition carries a claim anchor, every retained qualifier is rendered explicitly rather than implied, every merged group carries its independent support count, and every anchor is reinstated verbatim.
- Require the artifact to carry an explicit not-stated marker for any field the conditioning task expects and the source does not supply, so that absence is distinguishable from omission.
- Record the projected total artifact size and confirm it against the output token budget before generation, since an artifact discovered over budget after generation has already spent the compressor's cost.

**Required Outputs**:

- A per-region target reduction with its cap applied.
- A rendering contract statement bound to the reduction record.
- A projected artifact size checked against the output token budget.

**Quality Checkpoints**:

- No region target exceeds 70 percent for moderate consequence or 50 percent for high consequence; a higher request routes to reference substitution.
- The rendering contract requires a claim anchor on every proposition; a contract permitting unanchored propositions is rejected.
- The projected artifact size is at or below the output token budget before any generation call.

***

### Phase 3: Anchored Semantic Reduction Execution

**Objective**: Perform the selected reduction on each compressible region so that every surviving assertion is bound to a source span and every protected byte returns unchanged.

#### Step 3.1: Decompose Compressible Regions Into Anchored Propositions

**Required Actions**:

- Decompose each compressible region into minimal, independently testable propositions, splitting a conjunction only where each result remains true on its own [1].
- Bind every proposition to the exact source span that supports it, and mark propositions whose support spans a boundary so the parent span travels with them.
- Copy anchors into the propositions that reference them rather than expanding them, so that a quantity, an identifier, or a quotation remains an opaque token throughout the reduction.
- Preserve every semantic operator explicitly: negation and its scope, modality, hedging, attribution, conditions, exceptions, and temporal bounds, each rendered as a field rather than left in the prose.
- Refuse to generate any bridging proposition that the span does not entail, and mark unresolved references rather than resolving them from context the span does not carry.
- Segment on structural boundaries first, using headings, list items, records, turns, and timestamps, and use model-based boundary detection only where structure is insufficient, since reported evaluation found the computational cost of semantic chunking not justified by consistent gains over fixed-size chunking across document retrieval, evidence retrieval, and retrieval-based answer generation [7].

**Required Outputs**:

- A proposition set with one source span identifier per proposition.
- A semantic operator record per proposition carrying polarity, modality, attribution, condition, and temporal bounds as separate fields.
- An unresolved reference list naming propositions whose antecedent the span does not supply.

**Quality Checkpoints**:

- Every proposition carries a claim anchor; an unanchored proposition is discarded rather than carried forward.
- Every anchor appearing in a proposition matches its anchor table entry by identifier; a rewritten anchor halts the step.
- No proposition asserts more than its supporting span; source-to-proposition support is tested before the proposition enters the set.
- Semantic operators are recorded as fields; operators surviving only inside prose are treated as absent.

***

#### Step 3.2: Apply the Selected Operation Under Anchor and Qualifier Retention

**Required Actions**:

- Apply the rung selected in Step 2.2 to the proposition set of each region, and never apply a rung the region was not assigned.
- Preserve the semantic operator fields through every operation, since qualifier attrition rather than proposition loss is the dominant failure mode and its result reads as increased confidence rather than as damage.
- Render an explicit count and, where the budget permits, an explicit member list wherever an enumeration is reduced, so that enumeration collapse is impossible by construction.
- Retain disagreement rather than averaging it: where propositions conflict, emit a conflict set naming both assertions and their anchors, and never emit a smoothed statement that no source made.
- Cap generation attempts at 2 per region, and on a second failure route the region to extraction or reference substitution rather than to a third generation at a higher target.
- Where a hierarchy of abstraction levels is built, retain the lower levels rather than discarding them once a parent is generated, since retrieval at the level the question requires is the property that makes the hierarchy useful [8].

**Required Outputs**:

- A reduced proposition set or rendered region per compressible region.
- A conflict set per region where contradictory propositions were present.
- An attempt record naming the generation count per region and the disposition of failures.

**Quality Checkpoints**:

- Every semantic operator field present before the operation is present after it; a lost operator field fails the region.
- Every reduced enumeration carries an explicit count; a count word substituted for a list fails the region.
- No conflict was resolved by producing a statement absent from every member.
- No region received more than 2 generation attempts before being routed to a different treatment.

***

#### Step 3.3: Reinstate Anchors and Render the Reduced Artifact

**Required Actions**:

- Reinstate every anchor by exact byte substitution from the anchor table, and compare the reinstated bytes against the frozen source byte for byte rather than by normalised comparison.
- Reject the artifact where any anchor identifier remains unreinstated, appears more than once when the source carried it once, or is absent when the source carried it, since each condition indicates the compressor manipulated a protected token.
- Render each proposition with its claim anchor visible to the downstream consumer, so that the artifact can be cited and rehydrated rather than only read.
- Carry the trust class of every source region into the artifact unchanged, and refuse to render any proposition derived from untrusted content in a form that presents as an instruction or an authority.
- Recount the artifact's rendered tokens with the target model's tokenizer after serialization, and report the realised reduction against the projection recorded in Step 2.3.
- Emit an atomic-fact decomposition of the artifact alongside it, since evaluating a mixed-quality generation as the proportion of atomic facts supported by evidence localises an unsupported assertion that a whole-artifact judgement cannot [2].

**Required Outputs**:

- A rendered artifact with claim anchors and reinstated protected spans.
- An anchor reinstatement report with a per-anchor byte-equality verdict.
- A realised reduction figure in rendered tokens with its projection delta.
- An atomic-fact decomposition of the artifact for use by the verification in Phase 5.

**Quality Checkpoints**:

- Every anchor reinstated with bytes identical to the frozen source; a single mismatched byte rejects the artifact.
- Anchor multiplicity in the artifact equals anchor multiplicity in the source for every anchor identifier.
- The artifact's trust class equals the maximum trust class of its sources and never exceeds it.
- The rendered token count is at or below the output token budget; an over-budget artifact is rejected rather than trimmed in place.

***

### Phase 4: Cross-Item Redundancy Merging With Material-Difference Detection

**Objective**: Collapse items that assert the same thing into one rendering while proving that no member differed on any field whose change alters what the item asserts, and while preserving the evidence that several sources said it.

#### Step 4.1: Generate Merge Candidates by Blocking Before Similarity

**Required Actions**:

- Partition items into blocks before any similarity computation, keying on tenant, access scope, trust class, canonical entity, predicate family, validity time bucket, document version, and polarity, since a pair that cannot merge must never become a candidate.
- Run similarity search only inside a block, and treat the similarity threshold purely as a recall knob governing how many candidates reach the gate, never as an acceptance criterion.
- Cap candidate pairs at 25 per item and refuse all-pairs comparison at any scale, since comparison cost grows quadratically while the yield does not.
- Record for every candidate pair the block that produced it, the similarity score, the embedding model and revision, and the preprocessing version, so that a recalibration after a model change can be scoped rather than global.
- Recalibrate the candidate threshold after any change to the embedding model, tokenizer, normalisation, language mix, or corpus composition, and treat a silent provider model update as a version change once outputs shift.

**Required Outputs**:

- A block assignment record with the key fields that produced each block.
- A candidate pair set with a similarity score and its model and preprocessing versions.
- A candidate generation report naming the pairs-per-item cap and the pairs suppressed by it.

**Quality Checkpoints**:

- No candidate pair crosses a block boundary; a cross-block candidate is a blocking defect and halts the merge.
- No item generated more than 25 candidate pairs.
- Every candidate carries the embedding model revision that scored it; an unversioned score does not enter the gate.
- No merge was admitted anywhere in this step, since this step generates candidates only.

***

#### Step 4.2: Run the Material-Difference Gate Before Any Merge

**Required Actions**:

- Compare every candidate pair field by field across the gated fields before considering any equivalence proposal, and block the merge on a mismatch in any single field regardless of how the pair scored.
- Treat a mismatch on a gated field as evidence that the pair is two facts rather than one, and record the pair as a distinguished pair rather than as a failed duplicate, since the distinction carries information the corpus should retain.
- Require bidirectional entailment for every pair the field comparison passes, and where one item entails the other without the converse, preserve both under a specificity relation rather than merging, since the more specific item carries content the general one does not.
- Aggregate entailment evidence over decomposed pairs rather than over whole items, since aggregation design materially affects consistency detection and a whole-item judgement conceals which clause diverged [3].
- Route every merge in the high consequence class to human approval, and audit at least 10 percent of accepted merges in the moderate class against the source items.
- Reverse any merge on discovery of a material difference, using the merge witness, and re-run the affected probe set rather than patching the merged rendering in place.

**Gated fields and the consequence of a mismatch**

| Gated field | Why a mismatch is material | Consequence of a mismatch |
| :-- | :-- | :-- |
| Canonical entity and identifier | The same statement about two entities is two facts | Block; record as a distinguished pair |
| Numeric value, unit, and tolerance | A rounded or unit-stripped value is a different quantity | Block; escalate where the values differ by more than the declared tolerance |
| Polarity and negation scope | Merging an assertion with its denial destroys both | Block; record as a conflict set |
| Modality, certainty, and hedging | A hedged claim merged into an asserted one launders the uncertainty | Block; retain the weaker claim separately |
| Validity interval and version | Facts equivalent except for valid time are not duplicates | Block; retain both with supersession recorded |
| Jurisdiction, scope, and audience | A scoped rule merged into a general one over-applies it | Block; retain both with scope rendered |
| Attribution and source authority | Attribution is the content in an attributed claim | Block; retain both attributions |
| Condition and exception structure | A conditional obligation merged into an unconditional one changes the obligation | Block; retain the condition |
| Permission and prohibition direction | Direction reversal inverts an access decision | Block; escalate immediately |

**Required Outputs**:

- A per-pair field comparison verdict naming every gated field tested.
- A bidirectional entailment verdict for every pair passing the field comparison.
- A distinguished pair record for every pair blocked by a material difference.
- A specificity relation record for every pair related by one-directional entailment.

**Quality Checkpoints**:

- All 9 gated fields were tested on every candidate pair; an untested field blocks the merge.
- No merge was admitted on a similarity score, on a model equivalence assertion, or on a one-directional entailment.
- Every high consequence merge carries a human approval record.
- At least 10 percent of accepted moderate consequence merges were audited against their source items in the reporting window.

***

#### Step 4.3: Render the Merged Group and Preserve the Support Ledger

**Required Actions**:

- Render one canonical statement per merged group and retain the pointer to every member, since the merge compresses the rendering and never the evidence set.
- Compute the independent support count as the number of distinct provenance families asserting the claim, and keep it separate from the raw member count, since many copies of one syndicated origin are one attestation.
- Record first and last observation times, the distinct source count, and every dissenting member, so that corroboration, frequency, and disagreement survive an operation whose purpose was to remove repetition.
- Prefer a real member over a synthesised statement as the canonical rendering wherever one member is both central and complete, since a synthesised centre is a rendering that no source asserted and cannot be cited.
- Write a merge witness for every accepted merge naming the members, the field comparison result, the entailment verdict, the canonical rendering, and the reversal path, and refuse any merge for which a witness cannot be written.
- Refuse to merge where source independence cannot be established, and record the refusal, since a merge that inflates one source into apparent consensus is more damaging than the tokens it saved.

**Required Outputs**:

- A canonical rendering per merged group with pointers to every member.
- A support ledger carrying the independent support count, distinct source count, observation window, and dissent list.
- A merge witness set with one entry per accepted merge.
- A refusal record for groups whose independence could not be established.

**Quality Checkpoints**:

- Every merged group retains a pointer to every member; a member reachable only through the canonical rendering is a lost record.
- The independent support count is reported separately from the raw member count in every rendered group.
- Every accepted merge carries a witness sufficient to reverse it; a merge without a reversal path is rejected.
- No group whose members share one syndicated origin is rendered with a support count above 1.

***

### Phase 5: Meaning-Preservation Verification Under Numeric Gates

**Objective**: Establish by measurement rather than by reading that the compressed artifact still answers the questions the original answered, and discard it where it does not.

#### Step 5.1: Construct the Probe Set From the Frozen Original

**Required Actions**:

- Build every probe from the frozen original and never from the compressed artifact, since a probe written from the artifact tests only that the artifact is self-consistent and will pass an artifact that lost everything.
- Attach a deterministic answer key to every probe, drawn from a specific source span and expressed as an exact string, a numeric value with its unit, an enumerated set, or a boolean, so that grading is comparison rather than judgement.
- Size the probe set by consequence class: at least 12 probes for low consequence, at least 20 for moderate, and at least 40 for high, and treat these as floors that scale with region count rather than as targets.
- Include at least 1 probe per protected class present in the candidate, at least 2 relation probes testing which value belongs to which entity, at least 2 qualifier probes testing a negation or a condition, and at least 3 abstention probes whose correct answer is that the source does not say.
- Draft open-vocabulary probes with a model where a deterministic key cannot be constructed, and cap this share at 20 percent of the set, since question generation and answerability classification materially affect the outcome of a question-based factuality evaluation and both must be versioned and tested [5].
- Combine at least 2 verification families over the artifact, pairing the probe run with claim-support checking, since reported benchmark work finds question-based and entailment-based approaches strong and complementary rather than interchangeable [4][6].

**Probe Set Record**

```
PROBE_SET_ID:
REDUCTION_ID:
SOURCE_VERSION_ID:                 the frozen original, never the artifact
CONSEQUENCE_CLASS:
REQUIRED_SIZE:
PROBES:
  - PROBE_ID:
    CLASS:                         protected | relation | qualifier | enumeration | abstention | general
    QUESTION:
    ANSWER_KEY:
    KEY_TYPE:                      exact_string | numeric_with_unit | enumerated_set | boolean | open
    SOURCE_SPAN_ID:
    GRADER:                        deterministic | model
CONTROL_RUN_RESULT:
CONTROL_FAILURES_REMOVED:
SCORED_DENOMINATOR:
PASS_THRESHOLD:
```

**Required Outputs**:

- A probe set meeting its size floor with a class label and answer key per probe.
- A coverage report showing at least 1 probe per protected class present.
- A grader assignment per probe with the model-graded share computed.

**Quality Checkpoints**:

- Every probe traces to a source span in the frozen original; a probe without a span is removed before the run.
- The probe count meets or exceeds the floor for the consequence class; a short set halts verification.
- The model-graded share is at most 20 percent; a larger share halts verification until deterministic keys are supplied.
- No probe was constructed by reading the compressed artifact.

***

#### Step 5.2: Execute the Control Run and Score the Compressed Run

**Required Actions**:

- Run the probe set against the uncompressed original first, and remove from the denominator any probe the original itself fails, recording each removal as a probe defect rather than as a compression success.
- Halt verification and rebuild the probe set where more than 15 percent of probes fail the control run, since a set that the original cannot satisfy measures the probe builder rather than the compression.
- Run the probe set against the compressed artifact alone, with the original withheld from the answering context, since an answerer holding both measures nothing about the artifact.
- Grade deterministic probes by exact or canonically normalised comparison, requiring a numeric probe to match on value, sign, unit, entity association, and time scope jointly, and treat a value-only match as a failure.
- Grade the model-graded share with a model distinct from the compressor, run 2 independent gradings per probe, and resolve any disagreement to fail rather than to a tie-break.
- Score abstention probes as failures wherever the artifact supplies an answer, since a confabulated answer to a question the source does not address is a more damaging outcome than a missing one.

**Probe class requirements and pass thresholds**

| Probe class | Minimum count | Pass threshold | Consequence of breach |
| :-- | :-- | :-- | :-- |
| Protected | 1 per protected class present | 1.00 in every consequence class | Discard the artifact; open a detector review |
| Relation | 2 | 1.00 for high, at least 0.95 otherwise | Discard; regenerate with relations rendered explicitly |
| Qualifier | 2 | 1.00 for high, at least 0.95 otherwise | Discard; regenerate with operator fields enforced |
| Enumeration | 1 per reduced enumeration | 1.00 in every consequence class | Discard; restore the explicit member list |
| Abstention | 3 | Confabulation count exactly 0 | Discard; lower the rung and regenerate |
| General | Balance to the size floor | 0.90 low, 0.95 moderate, 1.00 high | Discard and regenerate at a lower target |

**Required Outputs**:

- A control run result with the probes removed and the reason for each removal.
- A compressed run result with a per-probe verdict and a per-class pass rate.
- An overall probe pass rate with its scored denominator stated.

**Quality Checkpoints**:

- The control run completed before the compressed run; a compressed run scored without a control is void.
- Control removals are below 15 percent of the drafted set; above that the set is rebuilt rather than trimmed.
- Every numeric probe was graded on all 5 properties jointly; a value-only match is recorded as a failure.
- The original was withheld from the answering context for 100 percent of compressed-run probes.

***

#### Step 5.3: Issue the Admission Verdict and Route Failures

**Required Actions**:

- Admit the artifact only where every class threshold and the overall threshold are met, and pass it to the general compression guidance for its preservation check and admission, since this guide's verdict is necessary and not sufficient.
- Discard the artifact on any breach, restore the frozen version named in the rollback contract, and invalidate every derived artifact and cache entry keyed to the discarded candidate.
- Classify the failure before regenerating, into anchor breach, qualifier attrition, enumeration collapse, unsupported assertion, merge over-collapse, or budget overrun, and select the correction the class implies rather than regenerating identically.
- Regenerate at a lower rung of the ladder, at a lower target reduction, or with a stricter rendering contract, and stop after 2 regeneration attempts, routing the candidate to extraction, reference substitution, or isolation rather than to a third attempt.
- Return a typed reduction-unsatisfied outcome where no safe semantic operation remains, and never widen the loss budget or remove a protected class to make a failing artifact pass.
- Add every production failure to the probe set as a permanent case keyed to its failure class, so that the harness grows against observed loss rather than against anticipated loss.

**Required Outputs**:

- An admission verdict with the per-class rates that produced it.
- A rollback record naming the restored version, the invalidation scope, and the failure class, written for every rejected artifact.
- A typed reduction-unsatisfied outcome with its remaining options where the loop exits without an admitted artifact.

**Quality Checkpoints**:

- No artifact is admitted with a recorded warning; the verdict is admit or discard and nothing else.
- Every rejected artifact is logged with the same field set as an admitted one, so rejection rate by rung and content class is measurable.
- The working set after a rejection is byte-identical to the frozen version named in the rollback contract.
- No protected class was removed and no loss budget widened to make a failing artifact pass.

***

### Phase 6: Outcome Measurement and Semantic Policy Correction

**Objective**: Establish whether the admitted artifacts changed downstream outcomes, attribute any change to a named semantic operation, and correct or retire the policy that produced it.

#### Step 6.1: Measure Downstream Outcome and Attribute Semantic Loss

**Required Actions**:

- Measure task outcome against the uncompressed baseline on the frozen replay set held by the general compression guidance, and never against a second compressed run, since two compressed runs agreeing establishes only that the compressor is consistent.
- Stratify the measurement by rung, by semantic structure, and by content class, since an aggregate figure conceals a rung that is safe for narrative regions and destructive for enumerative ones.
- Attribute every outcome change to a named operation by re-running the failing case with one rung disabled at a time, rather than attributing loss to compression in general.
- Report the realised reduction and the outcome retention together, since a reduction figure reported alone governs nothing; a reported agent framework achieving a 26 to 54 percent reduction in peak token usage did so while measuring task success in the same evaluation [24]. Classify each observed loss against the three failure positions a 2026 survey of agent context compression distinguishes, separating a wrong decision about what to compress from loss during the transformation and from failure to recover information afterwards, since the three carry different corrections [25].
- Compute the net economics of the semantic operation including compressor, probe harness, merge gate, audit, and regeneration cost, and treat verification as a charged cost rather than as overhead outside the ledger.

**Required Outputs**:

- A task-outcome retention figure per rung, semantic structure, and content class.
- An attribution record naming the operation responsible for each outcome change.
- A net economics figure including harness and audit cost.

**Quality Checkpoints**:

- Every retention figure carries its denominator and its stratum; an aggregate reported without strata does not satisfy this step.
- Every outcome change is attributed to a named rung; unattributed loss opens an attribution run rather than a policy change.
- Verification cost appears in the net economics ledger; a ledger omitting it overstates the saving.

***

#### Step 6.2: Track Compounding Loss Across a Semantic Lineage

**Required Actions**:

- Record the semantic operation applied at every event on a lineage and increment compression depth as the general compression guidance defines it, since a semantic pass is a compression pass and is counted identically.
- Defer the depth ceiling, the regeneration trigger, and the quarantine of an over-depth artifact to that guidance, and never define a local ceiling that permits a further semantic pass it would refuse.
- Verify every artifact against its immutable depth-zero source rather than against its parent, since verifying against a parent validates the copy rather than the content.
- Track three semantic-specific degradation signals across the lineage and report them into the general guidance's drift series: qualifier attrition rate, computed as operator fields lost per event; anchor attrition rate, computed as claim anchors lost per event; and abstraction-level creep, computed as the change in mean proposition generality per event.
- Open a policy review on a monotonic rise in any of the three signals across 3 consecutive events on one lineage, even where each individual event passed its probe gate.
- Prefer regeneration from source combined with the new raw delta over re-reducing an existing artifact, since the first re-derives only what changed and the second re-derives everything at a higher generality.

**Required Outputs**:

- A per-lineage semantic operation history with compression depth per event.
- A three-signal degradation series with the delta per event.
- A review verdict for any lineage breaching the monotonic-rise rule.

**Quality Checkpoints**:

- Compression depth is computed by the general guidance's rule; a locally defined depth is a governance defect.
- Every verification comparand is a depth-zero source; a verification run against a parent artifact does not count toward this checkpoint.
- A monotonic rise across 3 consecutive events opens a review regardless of the absolute value of the latest measurement.

***

#### Step 6.3: Correct or Retire the Semantic Policy

**Required Actions**:

- Apply the tolerance rule held by the general compression guidance rather than restating one, and treat this step's output as an input to that rule rather than as an independent authority.
- Retire a rung for a content class where its stratified task-outcome retention falls below the class threshold across 2 consecutive measurement windows, and record the retirement with its evidence.
- Tighten the detectors, the gated field list, or the probe class floors in response to a named failure class rather than by lowering the target reduction alone, since a lower ratio hides a defect that returns at the next budget pressure.
- Version the detector set, the rung policy, the gated field list, the rendering contract, and the probe class floors together, and evaluate a new version on a held-out replay split rather than on the cases that motivated the change.
- Treat every refusal to compress as a first-class logged outcome, since a deployment that never refuses is not applying the entry conditions in Phase 1.
- Re-run the golden case set covering identifiers, quantities, negations, enumerations, attributions, conflicting claims, and near-duplicates differing on one gated field on every change to a compressor model, prompt version, embedding model, tokenizer, or detector set.

**Required Outputs**:

- A policy correction record naming the change, its trigger, and its evidence.
- A retirement record for any rung withdrawn from a content class.
- A golden case result set keyed to the versions that produced it.

**Quality Checkpoints**:

- Every correction names the failure class it addresses; a correction applied without a named class is unevaluable.
- Refusals are counted and reported; a refusal count of 0 across a reporting window opens an entry-condition review.
- The golden case set was re-run on 100 percent of compressor, prompt, embedding, tokenizer, and detector changes before the change reached production traffic.

***

## III. Implementation Guidance for AI Agents

AI agents performing semantic compression must follow systematic protocols ensuring that protected content never reaches the compressor, that every equivalence claim is adjudicated by deterministic comparison, and that meaning preservation is demonstrated by a scored probe run before any artifact enters the working set. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Exclusion Detector**: Runs the versioned verbatim-carry detectors, collects the model tier's additive proposals, substitutes anchors, and reinstates them by exact byte comparison. It never summarises, and it never removes a span from the protected partition on a model assertion.
2. **Region Planner**: Classifies semantic structure, assigns ladder rungs against their entry conditions, sets per-region targets under the caps, and declares the rendering contract. It holds no generation capability.
3. **Semantic Compressor**: Decomposes regions into anchored propositions and applies the assigned rung. It holds no admission authority, never adjudicates its own output, never expands an anchor, and never executes a tool.
4. **Merge Adjudicator**: Generates candidates by blocking, runs the gated field comparison and the bidirectional entailment test, writes merge witnesses, and maintains the support ledger. Its block on a material difference cannot be overridden by any component.
5. **Probe Harness**: Builds the probe set from the frozen original, runs the control run and the compressed run, grades deterministically, and issues the meaning-preservation verdict. Its verdict binds over every other component in this guide.
6. **Lineage and Outcome Auditor**: Records semantic operations and depth, computes the three degradation signals, runs the stratified replay measurement, and may retire a rung for a content class without the compressor's agreement.

**Authority rule**: The Semantic Compressor proposes and the Probe Harness disposes, and the Exclusion Detector's partition binds both. No component may install an artifact the Harness discarded, no component may amend the protected partition or the loss budget after generation has begun, and no component may merge a pair the Adjudicator blocked. Disagreements are recorded with a reason code and resolved to the stricter treatment.

**Trust boundary**: Semantic processing does not neutralise hostile content. An injected instruction can be extracted as a salient proposition, become the canonical rendering of a merged group, and persist in a derived artifact, so retrieval-augmented framing is not a mitigation for prompt injection and untrusted content must be segregated, validated, and monitored [15]. Access scope and trust class are block keys in Step 4.1 rather than filters applied after similarity search, since cross-tenant leakage and poisoning in embedding-mediated stores are addressed by permission-aware partitioning before retrieval [18]. No component may execute an instruction found in the content it compresses.

**Workflow Execution Pattern**:

```
STATE: Meaning_Preservation_Verification
INPUTS:
  1. Frozen source version identifier and digest from Step 1.1
  2. Anchor table and reinstatement report from Step 3.3
  3. Rendered artifact with claim anchors from Step 3.3
  4. Merge witness set and support ledger from Step 4.3
  5. Probe set with deterministic answer keys from Step 5.1
ACTIONS:
  1. Execute the control run against the uncompressed original
  2. Remove control failures from the denominator and record each
  3. Execute the compressed run with the original withheld
  4. Grade deterministic probes on all key properties jointly
  5. Grade the model share with a non-compressor model, twice
VALIDATION:
  - control_failure_share <= 0.15
  - protected_probe_pass_rate == 1.00
  - enumeration_probe_pass_rate == 1.00
  - abstention_confabulation_count == 0
  - overall_probe_pass_rate >= threshold_for_consequence_class
  - model_graded_share <= 0.20
  - unreinstated_anchor_count == 0
  - unwitnessed_merge_count == 0
TRANSITIONS:
  IF all_validations_pass THEN next_state = Route_To_General_Preservation_Check
  IF any_validation_fails AND attempts < 2 THEN next_state = Rollback_And_Regenerate_Lower_Rung
  IF any_validation_fails AND attempts >= 2 THEN next_state = Route_To_Extraction_Or_Reference
  IF control_failure_share > 0.15 THEN next_state = Rebuild_Probe_Set
  IF no_safe_operation_remains THEN next_state = Typed_Reduction_Unsatisfied
```

**Two-Phase Action Pattern**: Emit the protected partition, the rung assignments, the per-region targets, and the rendering contract without generating anything; confirm them against the ladder entry conditions and the reduction caps while no tokens have been spent; generate only after that confirmation passes. Installing the artifact is a third, separate operation occurring only after the probe verdict and the general guidance's preservation check, and it writes the lineage record in the same transaction.

**Approval Gate**: Human authorisation is required before any merge in the high consequence class, before any rung 5 abstraction over a region feeding a citation-required element, before any change to the verbatim-carry membership list, before admitting an artifact whose overall probe pass rate sits between 0.90 and the threshold for its consequence class, and before retiring a probe class floor. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the anchor table, the reduction record, the merge witnesses, and the probe set in durable state, since a semantic compression event frequently spans the context boundary it exists to survive.
- Reduce from durable state and source references rather than from the transcript, so that superseded values and abandoned reasoning are not carried forward as current propositions.
- Bound the compressor's, the adjudicator's, and the harness's own token consumption and charge it to the event's net economics rather than treating verification as free.
- Write a handoff record at every context boundary naming the reduction identifier, the artifact version, the compression depth, the probe verdict, and the recovery path, and require explicit acknowledgement by the receiver.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Qualification and Exclusion Integrity (After Phase 1)**

- **Automated Check**: The candidate is frozen with a digest; all 3 cheaper reductions were evaluated; projected reduction is at least 20 percent; every protected span carries an anchor with a byte range; zero protected bytes appear in any model payload.
- **Agent Action on Pass**: Proceed to method selection.
- **Agent Action on Failure**: Halt the event; an exclusion defect is never corrected after generation because the protected bytes have already been exposed.
- **Human Review Trigger**: Any leaked protected byte, or a detector recall below 0.98 on the golden case set for the candidate's content class.

**Checkpoint 2: Method Selection Validity (After Phase 2)**

- **Automated Check**: Every region carries one semantic structure and one rung; every rung's entry condition is satisfied; no skipped rung lacks a reason code; no target exceeds the 70 percent or 50 percent cap.
- **Agent Action on Pass**: Proceed to reduction execution.
- **Agent Action on Failure**: Return the offending regions for reassignment; no generation call is issued against an invalid assignment.
- **Human Review Trigger**: Any rung 5 assignment over a region feeding a citation-required element, or more than 30 percent of regions assigned rung 5.

**Checkpoint 3: Reduction and Reinstatement Integrity (After Phase 3)**

- **Automated Check**: Every proposition carries a claim anchor; every anchor reinstated byte-identical; anchor multiplicity matches the source; every semantic operator field present before the operation is present after; rendered tokens within budget.
- **Agent Action on Pass**: Proceed to redundancy merging where a merge rung was assigned, otherwise to verification.
- **Agent Action on Failure**: Discard the artifact and regenerate at a lower rung; never repair an anchor breach in place.
- **Human Review Trigger**: A second consecutive anchor breach on the same content class, or an operator field loss rate above 2 percent.

**Checkpoint 4: Merge Safety (After Phase 4)**

- **Automated Check**: Zero cross-block candidates; all 9 gated fields tested per pair; zero merges admitted on similarity or one-directional entailment; every accepted merge carries a witness; independent support count reported separately from member count.
- **Agent Action on Pass**: Proceed to verification.
- **Agent Action on Failure**: Reverse the affected merges from their witnesses and re-run the field comparison; a merge without a witness is treated as data loss and escalated.
- **Human Review Trigger**: Any merge in the high consequence class, any admitted merge later found to differ on a gated field, or an over-merge rate above 1 percent in the audit sample.

**Checkpoint 5: Meaning-Preservation Verdict (After Phase 5)**

- **Automated Check**: Control run completed with removals below 15 percent; protected, enumeration, and abstention classes at their thresholds; overall pass rate at or above the consequence-class threshold; model-graded share at most 20 percent.
- **Agent Action on Pass**: Route the artifact to the general compression guidance for its preservation check and admission.
- **Agent Action on Failure**: Discard, roll back to the frozen version, classify the failure, and regenerate at most twice before routing to a different treatment.
- **Human Review Trigger**: An overall pass rate between 0.90 and the class threshold, or 2 consecutive discards on one candidate.

**Checkpoint 6: Outcome and Lineage Integrity (After Phase 6)**

- **Automated Check**: Retention reported per stratum with denominators; every outcome change attributed to a named rung; depth computed by the general guidance's rule; the three degradation signals recorded per event; verification cost present in the ledger.
- **Agent Action on Pass**: Release the measurement report and permit the policy version to continue.
- **Agent Action on Failure**: Withhold the report and name the missing evidence; no rung is promoted to a new content class on aggregate figures alone.
- **Human Review Trigger**: A monotonic rise in any degradation signal across 3 consecutive events, or a stratified retention below the class threshold in 2 consecutive windows.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
REDUCTION_ID:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Unsupported Assertion Introduced by Abstraction**

- **Symptoms**: A proposition in the artifact carries no claim anchor; a general claim entails more than the propositions it replaced; a probe answered from the artifact contradicts the source span.
- **Diagnostic Steps**: Decompose the artifact into atomic claims and test each against the frozen source, locating the rung at which the unsupported claim first appears in the lineage rather than inspecting only the final artifact.
- **Resolution Protocol**: Option A, discard and regenerate at rung 4 with the abstraction disabled for the region. Option B, retain the abstraction and append the specific propositions it generalised, accepting the token cost. Option C, route the region to extraction, retaining the original spans verbatim.
- **Escalation Trigger**: A second unsupported assertion on the same content class within one reporting window retires rung 5 for that class pending review; this error is never resolved by regenerating at the same rung.

**Error Type 2: Qualifier Attrition and Confidence Inflation**

- **Symptoms**: Negations, hedges, modal verbs, conditions, or attributions present in the source are absent from the artifact; the artifact asserts as fact what the source attributed to a party; qualifier probes fail while general probes pass.
- **Diagnostic Steps**: Compare the operator field record produced in Step 3.1 against the operator fields recoverable from the artifact, and determine whether the loss occurred at decomposition, at reduction, or at rendering.
- **Resolution Protocol**: Option A, add the affected operator class to the verbatim-carry partition so the marker is anchored rather than paraphrased. Option B, regenerate with the rendering contract requiring each operator as an explicit field. Option C, suspend abstractive rungs for the content class and use typed projection with an operator field per record.
- **Escalation Trigger**: An operator field loss rate above 2 percent across a reporting window suspends rungs 4 and 5 for the class; a loss of a permission or prohibition direction escalates immediately and is never resolved by retry.

**Error Type 3: Silent Over-Merge of a Materially Different Pair**

- **Symptoms**: One canonical rendering has members differing on entity, quantity, unit, polarity, validity interval, version, jurisdiction, or attribution; an audit finds a merged group whose members answer a probe differently; support counts rise without new sources.
- **Diagnostic Steps**: Reverse the merge from its witness, re-run the gated field comparison field by field, and determine whether the failure was a missing block key, an untested field, or a gate bypassed on a similarity score.
- **Resolution Protocol**: Option A, add the discriminating field to the block key so the pair never becomes a candidate. Option B, add the field to the gated list and re-run the comparison across the affected corpus partition. Option C, suspend the merge rung for the content class and render the members separately.
- **Escalation Trigger**: An over-merge rate above 1 percent in the audit sample suspends the merge rung for the class; a single over-merge involving a permission, an identifier, or a legal obligation escalates immediately.

**Error Type 4: Enumeration Collapse and Provenance Dissolution**

- **Symptoms**: A list is rendered as a count word or a vague quantifier; the artifact can no longer support a citation the conditioning task requires; independent support counts are absent from a merged group.
- **Diagnostic Steps**: Compare the enumeration probe results and the citation-required element list against the artifact, and determine whether the element was absent from the protected partition or was protected and then dropped at rendering.
- **Resolution Protocol**: Option A, add the element to the protected partition and regenerate, since a citation-required element is declarative and detectors do not find it. Option B, render the enumeration as an explicit member list under an increased output budget. Option C, substitute a reference to the durable original for the enumeration and carry only the count.
- **Escalation Trigger**: Any citation failure in a high consequence artifact escalates immediately; 2 enumeration collapses on one content class retire abstractive rungs for that class.

**Error Type 5: Probe Set Contamination or Defect**

- **Symptoms**: The control run fails more than 15 percent of probes; probe pass rates are uniformly high while downstream outcomes degrade; probes reference content present only in the artifact.
- **Diagnostic Steps**: Trace every probe to its source span in the frozen original, and confirm that no probe was drafted after the artifact existed and that the model-graded share is within its cap.
- **Resolution Protocol**: Option A, rebuild the set from the original with deterministic keys, discarding the contaminated probes. Option B, lower the model-graded share by supplying deterministic keys for open probes. Option C, replace the grading model with one distinct from both the compressor and the prior grader and re-run.
- **Escalation Trigger**: A second contaminated set on one policy version halts semantic compression for the content class until the harness is rebuilt; a passing probe run is never accepted from a set that failed its control run.

**Error Type 6: Injection Survives Semantic Extraction**

- **Symptoms**: An instruction appears as a proposition, becomes the canonical rendering of a merged group, or acquires a trust class above its source; anomalous neighbourhoods produce sudden cluster dominance from one submitter.
- **Diagnostic Steps**: Trace the proposition to its source span and trust class, and determine whether the escalation occurred at extraction, at merging, or at rendering. Small poison sets are sufficient to dominate targeted retrieval, and targeted attacks are designed to leave aggregate quality metrics unchanged, so aggregate figures do not clear this class [16][17].
- **Resolution Protocol**: Option A, quarantine the lineage, classify instruction speech acts separately from descriptive content, and re-run extraction under a non-executing contract. Option B, cap the share of any merged group's support drawn from one submitter, domain, or origin. Option C, rebuild the affected corpus partition and rotate its derived artifacts where integrity is uncertain.
- **Escalation Trigger**: Any trust class escalation escalates immediately and is never resolved by retry; a single instruction rendered as a proposition in a high consequence artifact halts the policy for the class.

**Troubleshooting Decision Tree**:

```
SEMANTIC COMPRESSION FAILS A GATE
├─ EXCLUSION DEFECT
│   ├─ Protected byte reached the model → HALT event; detector review; regenerate from source
│   ├─ Anchor unreinstated or byte-mismatched → Discard artifact; regenerate at a lower rung
│   └─ Citation-required element unprotected → Add to protected partition; regenerate
├─ REDUCTION DEFECT
│   ├─ Proposition without a claim anchor → Discard the proposition; re-run decomposition
│   ├─ Operator field lost → Anchor the operator class; regenerate under the strict contract
│   └─ Enumeration rendered as a count word → Restore the member list or substitute a reference
├─ MERGE DEFECT
│   ├─ Gated field mismatch found after merge → Reverse from witness; add field to block key
│   ├─ Merge admitted on a similarity score → Reverse; suspend the rung for the class
│   └─ Merge without a witness → Treat as data loss; ESCALATE
├─ VERIFICATION DEFECT
│   ├─ Control failures above 15 percent → Rebuild the probe set from the original
│   ├─ Model-graded share above cap → Supply deterministic keys before scoring
│   └─ Two consecutive discards → Route to extraction, reference, or isolation
└─ TRUST DEFECT
    ├─ Instruction rendered as a proposition → Quarantine lineage; ESCALATE
    └─ Artifact trust class above source → Discard; recompute trust from provenance
```

### D. Performance Metrics and Continuous Learning

**Meaning-Preservation Metrics**:

- **Protected-class probe pass rate**: Protected probes answered correctly over protected probes scored (target: 1.00; any failure halts the policy for the class).
- **Overall probe pass rate**: Probes answered correctly over the scored denominator (target: at least 0.90 low, 0.95 moderate, 1.00 high consequence).
- **Confabulation count**: Abstention probes answered rather than declined (target: exactly 0).
- **Operator field retention**: Operator fields present after reduction over operator fields recorded before it (target: at least 0.98; below that, abstractive rungs are suspended for the class).
- **Claim anchor coverage**: Propositions carrying a claim anchor over propositions rendered (target: 1.00).

**Merge and Redundancy Metrics**:

- **Over-merge rate**: Accepted merges judged non-equivalent on audit over accepted merges audited (target: at most 1 percent overall and 0 on any gated field involving identifiers, permissions, or legal obligations).
- **Under-merge rate**: True equivalent pairs left separate over true equivalent pairs (target: reported rather than minimised, since false merges are the costlier error in every consequence class).
- **Independent support preservation**: Distinct provenance families retained after merging over families present before (target: 1.00).
- **Candidate efficiency**: Candidate pairs evaluated over items processed (target: at most 25; a higher figure indicates a block key is too coarse).

**Reduction and Economics Metrics**:

- **Realised reduction**: Rendered source tokens minus rendered artifact tokens over rendered source tokens (target: at least 20 percent, reported alongside outcome retention and never alone).
- **Stratified task-outcome retention**: Compressed replay score over uncompressed baseline score per rung and content class (target: at least 0.98; below 0.95 retires the rung for the class).
- **Net semantic value**: Avoided input cost minus compressor, harness, merge gate, audit, and regeneration cost (target: positive; negative across 3 windows retires the technique for the class).
- **Discard rate**: Artifacts rejected at the probe gate over artifacts generated (target: at most 15 percent; a higher rate indicates targets are set beyond what the content supports).

**Instrumentation**: Emit per-event telemetry joining source version, reduction identifier, rung, anchor counts, merge witnesses, probe results, token counts, and cost. Generative-AI semantic conventions supply a base for model and token attributes, over which the fields above require an application-specific schema [23]. Never write protected raw content into an unrestricted telemetry store.

**Learning and Adaptation Mechanisms**:

- **Failure-keyed probe growth**: Add every production failure to the probe set as a permanent case keyed to its failure class, so the harness grows against observed loss.
- **Detector extension**: Extend the verbatim-carry detectors with every missed span and re-measure recall on the golden case set before the change reaches production.
- **Per-class threshold recalibration**: Recompute every threshold in this guide per content class against observed outcomes; the values stated here are deployment defaults, not measured constants.
- **Rejected-attempt analysis**: Log every discarded artifact with the same field set as an admitted one, since discard patterns by rung are the fastest signal that a target is set wrong.
- **Refusal accounting**: Treat do-not-compress decisions as first-class logged outcomes; a deployment that never refuses is not applying the entry conditions.

**Human-in-the-Loop Boundaries**: Changing the verbatim-carry membership list, approving a high consequence merge, admitting an artifact below its class threshold, retiring a probe class floor, and relaxing the requirement that verification precede admission are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how meaning is re-represented rather than what the meaning concerns. Its phases hold wherever content exceeds a budget, the content is worth keeping, and a later step will depend on a detail that a rewrite might dissolve.

### 4.1 Cross-Domain Application Patterns

**Clinical and care documentation**: Quantities with units, medication identifiers, negated findings, and attributed patient report dominate the verbatim-carry partition, so anchor density is high and the available reduction is low. The characteristic failure is qualifier attrition, since a negated finding rewritten without its negation inverts the record. Typed projection is the safe rung, abstraction is refused, and every artifact feeding a decision is scored at the high consequence floor of 40 probes at a pass rate of 1.00.

**Legal and contract review**: Contractual language is verbatim-carry by class, so the compressible surface is the surrounding narrative rather than the instrument. Cross-item merging is high-yield across clause libraries and high-risk within them, because two clauses differing only in jurisdiction, effective date, or a numeric cap score as near-identical. Jurisdiction, validity interval, and condition structure are carried as blocking keys rather than as post-hoc checks.

**Software engineering and incident response**: Log and trace sets have the highest redundancy density, so the merge rung supplies most of the saving. Identifiers, stack frames, commands, and configuration are verbatim-carry, and the characteristic failure is enumeration collapse, in which seven distinct failures become a statement that several services degraded. Merged groups retain observation times and distinct source counts, since frequency and spread are what an incident summary exists to convey.

**Financial and regulatory reporting**: Quantities, periods, and entity associations carry the meaning, and the relation probe class does most of the verification work because a correct number attached to the wrong period passes every value-only check. Typed projection with shape validation is the preferred rung, since omissions and constraint violations become observable rather than silent [21], and derivation records preserve which source supported which figure [22].

**Scientific and evidence synthesis**: Corroboration is the content, so the support ledger rather than the rendering carries the value. Independent support counts must survive merging, dissent must be rendered rather than smoothed, and copies from one syndicated origin must never present as consensus. Where a hierarchy of abstraction levels is built over a large corpus, community-level summaries improve comprehensiveness for global questions while remaining lossy derived artifacts that the lower levels must stay available to support [19][20].

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Use the 12-probe floor, permit rungs 1 through 4, and audit 5 percent of merges. Where harness cost exceeds 15 percent of the avoided input cost, the event should have been refused at Step 1.1.
- **High-risk or irreversible work**: Use the 40-probe floor with a pass rate of 1.00, refuse rung 5 entirely, route every merge to approval, and prefer reference substitution over any reduction whose loss budget names a content class the decision may need.
- **Small candidates**: Below 2,000 rendered tokens the harness and gate cost dominate; prefer extraction or reference substitution, since verification cost does not scale down with the candidate.
- **Large repetitive corpora**: Blocking is the scaling mechanism, not similarity search. Maintain block keys as a first-class schema, and treat a block producing more than 25 candidates per item as under-specified rather than as grounds for a higher similarity threshold.
- **Strict latency budgets**: Reduce probe count toward the class floor rather than removing classes, since removing the protected or abstention class removes the checks that catch the dominant failures. Where latency forbids the floor, refuse the compression and substitute a reference.
- **Long-horizon autonomous runs**: Persist the anchor table, merge witnesses, and probe sets outside working context, and re-run the probe set after every regeneration.

***

## V. Limitations and Considerations

**Verification cost is proportional to the safety it buys**: A 40-probe harness with deterministic keys, a control run, and two-grader adjudication costs a substantial fraction of what the compression saves, and on small or single-use candidates it costs more. The mitigation is the 20 percent reduction floor in Step 1.1 and the small-candidate rule in Section 4.2, which refuse the operation rather than run it unverified.

**Probe coverage is a sample, not a proof**: A probe set establishes that the sampled content survived and infers the rest. A 20-probe set detects a per-probe loss rate of 0.15 with probability above 0.95, and a 40-probe set detects a rate of 0.08 with probability above 0.96, but neither detects a single lost detail that no probe happened to address. The mitigation is the per-class floors, which force coverage of the classes where loss is most damaging rather than leaving coverage to a random draw, and the failure-keyed probe growth in Section III.D, which converts every observed miss into permanent coverage.

**All thresholds here are deployment defaults**: The 20 percent reduction floor, the 0.30 redundancy density entry condition, the 70 and 50 percent reduction caps, the 40 percent anchor density limit, the 25-candidate cap, the 15 percent control-failure limit, the 20 percent model-graded share, and every probe floor and pass rate were chosen to be operable on first deployment rather than derived from a measured property of any corpus. The mitigation is the per-class recalibration requirement in Section III.D, which obliges each deployment to recompute them against observed outcomes and to record the recomputation.

**Detection recall bounds the exclusion guarantee**: Software-enforced exclusion is only as good as its detectors, and a verbatim-carry span they do not recognise reaches the compressor as if no protection existed. The mitigation is the additive model pass in Step 1.2, whose proposals are admitted without adjudication, the golden case set measuring detector recall per content class, and the human review trigger below 0.98 recall.

**The citation-required class cannot be detected**: Whether a downstream step will need to cite a passage is a property of a future task, not of the text. The mitigation is the declarative route in Step 1.3, which requires the conditioning task to enumerate citation-required elements, and the refusal of rungs 4 and 5 over any region feeding one. Both fail where the conditioning task is stated incompletely, which is why an unknown future question family is an entry condition against semantic compression rather than a managed risk.

**Merging cannot establish source independence**: The support ledger counts distinct provenance families, but syndication, republication, and shared upstream sources defeat the count wherever provenance is shallow. The mitigation is the refusal in Step 4.3 to merge where independence cannot be established, trading the token saving for the corroboration signal.

**Semantic operations do not sanitise hostile content**: Extraction, merging, and abstraction can all promote an injected instruction into a durable proposition, and targeted poisoning is designed to leave aggregate metrics unchanged. The mitigation is the trust boundary in Section III.A, which makes access scope and trust class block keys rather than post-retrieval filters, forbids any component from executing content it compresses, and requires targeted canaries as the detection mechanism.

**A passing probe run is not a preserved artifact**: This guide's verdict is necessary and not sufficient. An artifact that satisfies every probe here can still breach the preservation manifest, exceed the depth ceiling, or fail the mechanical check owned by the general compression guidance. The mitigation is the routing in Step 5.3, which passes an artifact onward for that check rather than installing it, and the prohibition on any threshold here relaxing a threshold there.

***

## VI. Conclusion and Summary

Semantic compression is an exclusion discipline before it is a rewriting technique. What makes a reduction safe is not the quality of the abstraction but what the abstraction was never allowed to touch and what was measured afterwards. An agent that partitions the candidate first, anchors every protected span before the compressor sees it, and admits the result only on a scored probe run produces reductions whose loss is bounded and known. An agent that instructs a model to summarise faithfully produces fluent artifacts whose losses are invisible in exactly the evidence a reviewer would consult.

The method's savings and its risks arrive from the same place. Most of the token reduction comes from cross-item redundancy merging, and so does most of the damage, because two items differing on one gated field score as near-identical and merge into a rendering that silently discards the difference. Blocking before similarity, comparing every gated field deterministically, requiring bidirectional entailment, and preserving the support ledger separate a merge that removed a duplicate from one that destroyed a fact.

A team introducing semantic compression should build the detectors and the probe harness before the compressor: instrument an uncompressed baseline, measure detector recall on a golden case set, then validate the harness with a control run. Only then enable rung 2 and add rungs one at a time behind stratified outcome measurement. Rung 5 is the last enabled and the first retired.

**Key Success Factors**:

- **Exclusion by software**: Protected content is anchored out of the compressor's input, never left to an instruction the compressor is asked to honour.
- **Least destructive rung first**: The ladder is entered where the budget is met, and abstraction is reached only after cheaper meaning-preserving operations are shown insufficient.
- **Deterministic merge adjudication**: Similarity generates candidates and never admits them; a mismatch on any gated field blocks the merge irrespective of any score or model judgement.
- **Measured meaning preservation**: A probe set built from the original, filtered by a control run, and graded deterministically is the evidence that meaning survived; the artifact's readability is not.
- **Corroboration preserved through collapse**: The rendering is compressed and the evidence set is not, so independent support counts, dissent, and observation windows survive every merge.
- **Governance inherited, not restated**: The preservation manifest, the depth ceiling, the mechanical preservation check, and rollback belong to the general compression guidance, and nothing here relaxes them.

By following this guide, AI agents can reduce context by re-representing meaning rather than by deleting text, and can demonstrate with a scored, reproducible test that the meaning a later step will depend on is still there.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, including its bare labels where it supplied no title, and were not independently re-verified except where an entry is marked otherwise. Three marked exceptions exist: one whose full title was confirmed during this conversion, and two retrieved during it that the prose source does not carry.

**Corpus pointers**:

- `Semantic Context Compression: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the semantic unit taxonomy, the representation contract, the core invariants, the deduplication and threshold-calibration material, the clustering and representative-selection rules, the schema-guided and graph projection material, the fidelity metric definitions, the evaluation and drift procedures, the security controls, and the failure-mode inventory. The external references listed below are transcribed from its inline citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — owner of the general compression operation and its governance: the preservation manifest, the fidelity classes, the mechanical preservation check, compression-depth control and regeneration, reference substitution, rollback, and the replay measurement. Nineteen terms are adopted from it without redefinition, and this guide's probe verdict feeds its admission decision rather than replacing it.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the umbrella guidance for this category. Source of the context contract, the budget partition, and the operation ladder that selects the compress family before this guide is entered.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — owner of what earns a slot in the window; semantic compression is never a relevance filter.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — owner of durable writes, entity resolution, graph mutation, shape validation, and provenance records. Rung 1 emits candidate records into those controls rather than committing them.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — owner of splitting work across separate windows, selected when no safe semantic reduction remains under Step 5.3.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — owner of the retention transitions determining when content becomes eligible for reduction or eviction.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — companion guidance on failure modes reduction can create or conceal, applicable to Section III.C.
- `advanced_task_guides/context-management/guide_HierarchicalContextArchitecture.md` — owner of scope, inheritance, and routing across context levels, applicable to the abstraction hierarchies in Step 3.2.
- `advanced_task_guides/context-management/guide_SlidingWindowContext.md` — owner of resident-set policy and eviction, the positional alternative to meaning-level reduction.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — origin of the independent support count, error laundering, provenance link, and generation depth vocabulary used here through the general compression guidance.
- `advanced_task_guides/knowledge-retrieval/guide_GraphRAG.md` — owner of the query-time subgraph and community-summary mechanics referenced but not specified here.
- `advanced_task_guides/knowledge-retrieval/guide_HierarchicalIndexRetrieval.md` — owner of the index-layer structure carrying the vector-level compression re-scoped out in Section 1.3.

**External references**: The numbering below is the numbering used by the inline markers in Sections I through IV. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Retrieval granularity and proposition units*

1. Chen and colleagues, *Dense X Retrieval: What Retrieval Granularity Should We Use?* — https://aclanthology.org/2024.emnlp-main.845/ (full title confirmed during this conversion)

*Atomic-fact decomposition and factual-consistency measurement*

2. FActScore — https://aclanthology.org/2023.emnlp-main.741/
3. SummaC — https://arxiv.org/abs/2111.09525
4. TRUE — https://arxiv.org/abs/2204.04991
5. QAFactEval — https://aclanthology.org/2022.naacl-main.187/
6. Ragas — https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/

*Segmentation as an enabler of proposition extraction*

7. ACL Anthology, 2025 Findings of NAACL evaluation of semantic chunking against fixed-size chunking — https://aclanthology.org/2025.findings-naacl.114/

*Hierarchical summarisation*

8. RAPTOR — https://arxiv.org/abs/2401.18059

*Learned latent compression named as below the agent layer*

9. Gist Tokens — https://arxiv.org/abs/2304.08467
10. ICAE — https://arxiv.org/abs/2307.06945
11. AutoCompressors — https://arxiv.org/abs/2305.14788
12. xRAG — https://arxiv.org/abs/2405.13792
13. Prompt Compression Survey — https://arxiv.org/html/2410.12388v2
14. LLMLingua-2 — https://arxiv.org/abs/2403.12968

*Adversarial exposure of semantic pipelines*

15. OWASP Prompt Injection — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
16. PoisonedRAG — https://arxiv.org/abs/2402.07867
17. AgentPoison — https://neurips.cc/virtual/2024/poster/94715
18. OWASP Vector and Embedding Weaknesses — https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/

*Graph-mediated summarisation, schema validation, and provenance*

19. GraphRAG paper — https://arxiv.org/abs/2404.16130
20. Microsoft GraphRAG — https://microsoft.github.io/graphrag/index/overview/
21. W3C SHACL — https://www.w3.org/TR/shacl/
22. W3C PROV-DM — https://www.w3.org/TR/prov-dm/

*Telemetry conventions*

23. OpenTelemetry — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/

*Agent context compression measurement, retrieved during this conversion*

24. Kang and colleagues, *ACON: Optimizing Context Compression for Long-horizon LLM Agents* — https://arxiv.org/abs/2510.00615 (retrieved and title confirmed during this conversion; source of the 26 to 54 percent peak token reduction figure)
25. *Context Compression for LLM Agents: A Survey of Methods, Failure Modes, and Evaluation* — https://www.preprints.org/frontend/manuscript/098fda1d1490b8885d002521dbc08afa/download_pub (title and three-position failure taxonomy identified in search during this conversion; the manuscript itself was not fetched)

