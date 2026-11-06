# Guide Writing for Agent-Executable Methodology Guides

**Status**: Beta testing

**Change logs**:

- [09/06/2026] - Initialization

***

## Executive Summary

Guide writing constitutes the task family of converting a body of research or an existing prose document into a domain-agnostic, agent-executable methodology guide. This guide provides AI agents with a structured protocol for producing new guides that conform to the house style of the `advanced_task_guides` corpus: a Roman-numbered Operational Framework built from phase and step units, followed by explicit Implementation Guidance for AI Agents. It specifies the mandatory skeleton, the repeating step template, the verbatim section names that must be reproduced, the quantitative envelope a conforming guide must fall within, and the export artifacts that must never be reproduced. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure reproducible, high-quality guide output.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Guide**: A self-contained, structured methodology document that an AI agent can load at runtime and follow to complete a specific class of analytical or design task. A guide is not a tutorial, not an essay, and not a reference article; it is an executable procedure written in prose and structured markdown.

**Task family**: The class of problems a guide addresses, stated as a noun phrase. The task family is the guide's subject and supplies its H1 title. Examples drawn from the corpus: barrier analysis, effectiveness-by-condition analysis, cross-jurisdictional comparative policy analysis.

**Operational Framework**: The section that carries the method itself, decomposed into sequential phases, each phase decomposed into steps. It is the bulk of the document, occupying roughly 50–65% of body words.

**Phase**: A major stage of the method, rendered as `### Phase N: Title`. A conforming guide has 4–9 phases.

**Step**: The atomic repeating unit of work inside a phase, rendered as `#### Step N.M: Title`, where `N` matches the parent phase number. A phase typically contains 2–3 steps.

**Slot**: A bold run-in label that opens a labelled block inside a step, such as `**Objective**:`. Slots are not headings. They are bold text terminated by a colon, sitting on their own line, followed by a blank line and then the block's content.

**Implementation Guidance for AI Agents**: The section that translates the human-oriented method into agent-executable instruction. It is the corpus's identity marker and its title is invariant.

**Conformance envelope**: The quantitative range within which a conforming guide's measurable properties must fall. Stated in Section 1.3.

### 1.2 The Archetype and Its Accepted Variants

The corpus contains four document archetypes. Only one is normative for new guides.

**Operational Framework archetype (normative)**: document status block, Executive Summary, optional foundational concepts section, Operational Framework of phases and steps, Implementation Guidance for AI Agents, domain-transfer section, optional limitations section, conclusion, references. This is the archetype to write.

**Research Brief archetype (non-normative)**: Opens with `## Top-Level Takeaways` bullets, proceeds through Arabic-numbered topic sections, closes with a named application section. Present in five of the knowledge-graph guides. Do not write new guides in this form.

**Engineering Handbook archetype (non-normative)**: Opens with unheaded stakes paragraphs, uses `## Part <Roman>:` sections and heavily language-tagged code fences. Do not write new guides in this form.

**Compact Rubric archetype (non-normative for long-form)**: Opens with `## Purpose`, presents a dimension table, an explicit aggregation formula, and per-dimension `Q1:`/`Q2:` scales. Appropriate only for short scoring guides under 2,500 words, not for methodology guides.

Within the normative archetype, two numbering variants are attested and both are acceptable. Choose one and hold it for the whole document:

- **Roman variant (preferred)**: `## I. Operational Framework`, `## II. Implementation Guidance for AI Agents`, `## III. …`
- **Part variant**: `## Part I: Operational Framework`, `## Part II: Implementation Guidance for AI Agents`

### 1.3 Conformance Envelope

A conforming long-form guide falls within these ranges. Values outside them indicate the guide is under-developed or over-grown.

| Property | Target range | Hard rule |
| :-- | :-- | :-- |
| Body words | 5,000–11,300 observed | Below 4,000 is under-developed; length above the observed range is acceptable where the additional text is procedure rather than narrative |
| H1 headings | 1 | Exactly 1 |
| H2 headings | 5–9 | — |
| H3 headings | 14–29 | — |
| H4 headings | 0–38 | 0 only if the phase is the atomic unit |
| Phases | 4–9 | — |
| Steps per phase | 2–3 | — |
| Markdown tables | 0–6 | Tables are a sparing device |
| Fenced code blocks | 0–12 | All untagged unless recording a data record |
| Horizontal rules | 12–42 | `***` only, never `---` |
| Emoji | 0 | Zero, without exception |
| Second-person pronouns | 0 | The reader is never "you" |

### 1.4 Scope Rules Inherited From the Corpus

The corpus was authored against an explicit specification, preserved verbatim in the unstripped scaffolding of `advanced_task_guides/design-architecture/guide_DesignTechnicalBookStudyPlan.md`. Its constraints are binding on new guides:

- **Be comprehensive in both width and depth.** A guide that names a phase without specifying its actions, outputs, and checkpoints is incomplete.
- **Be concise but do not leave out important details.** Compression is achieved by removing narrative, not by removing procedure.
- **The guide must be general enough to be applied in various domains.** No guide may assume a single industry, employer, product, or architecture.
- **Be instructional, as the guide will be used to guide AI agents.** Every phase must terminate in a verifiable output contract.
- **Do not focus on visual analysis or any visual-related details.** No diagrams-as-images, no colour-dependent instructions, no references to visual inspection as a method.
- **Do not provide codes.** No executable source in any language. Fenced blocks carry pseudocode, ALL-CAPS protocol templates, box-drawing hierarchies, or fill-in document templates. The single attested exception is a `json` fence used to record a log schema.

### 1.5 Prose Register Rules

The corpus's register is uniform and narrow. These rules are binding on every sentence of a new guide.

**Person and address**: Third person throughout. The audience is named as AI agents and referred to in the third person plural. Second-person pronouns do not appear. First-person plural does not appear. A guide never says "you should"; it says "AI agents must".

**Mood and modality**: The framing prose is declarative and modal, using "must" for agent obligations and "should" for recommended practice. The procedural content is bare imperative with the subject elided, so that action bullets begin with a verb. Hedging constructions such as "might consider" or "perhaps" do not appear.

**Bold**: Carries structural work only, in three roles: run-in slot labels terminated by a colon, lead-in terms opening a definitional bullet, and first-column or header cells in tables. Bold is never used for mid-sentence emphasis.

**Italics**: Rare, reserved for publication titles in reference entries and for third-level classification labels where a bold level is already occupied.

**Dashes**: Em-dashes are near-absent from body prose; colons, semicolons, and parentheses carry the same work. Hyphens serve numeric ranges. Em-dashes are permitted as separators in reference entries and as not-applicable markers in table cells.

**Sentence construction**: Short and dense. Two-sentence bold-run-in paragraphs are the norm. Examples are carried in parenthetical clarifications rather than in separate sentences. Narrative, anecdote, and rhetorical questions do not appear.

**Deliverable phrasing**: Output bullets are noun phrases carrying no verb. Action bullets are verb-first imperatives. Checkpoint bullets are present-tense assertions that can be judged true or false.

**Quantification**: The register is saturated with numeric bounds. Every acceptance criterion carries a number, and every number carries a stated consequence for breach.

**Prohibited decoration**: No emoji, no blockquote callouts, no admonition syntax, no horizontal rules other than `***`.

***

## II. Operational Framework: Systematic Guide Construction

### Phase 1: Commission and Scope Definition

**Objective**: Establish the task family, audience, and boundaries of the guide before any drafting begins, so that scope creep is prevented rather than corrected.

#### Step 1.1: State the Task Family as a Noun Phrase

**Required Actions**:

- Write the task family as a single noun phrase in Title Case, without a subtitle, without a colon-and-tagline, and without an article.
- Verify the phrase names a class of tasks, not a single instance and not a tool.
- Reject titles that embed a domain unless the domain is intrinsic to the method.

**Required Outputs**:

- One H1 title string, ready to place at line 1 of the file.
- A one-sentence definition of the task family for reuse in the Executive Summary.

**Quality Checkpoints**:

- Title is a noun phrase, not a sentence or a question.
- Title contains no subtitle, no dash-appended explainer, and no "A Guide to" prefix.
- Title would be recognisable as a method name to a practitioner outside the originating domain.

***

#### Step 1.2: Establish Source Provenance and Evidence Boundary

**Required Actions**:

- Enumerate the source material the guide will be built from, distinguishing primary sources from derived commentary.
- Record which claims are attributable to a source and which are the guide's own synthesis.
- Decide the citation treatment before drafting, selecting one of the three attested treatments in Section 6.3.

**Required Outputs**:

- A source inventory naming each source and its role.
- A declared citation treatment for the document.

**Quality Checkpoints**:

- Every substantive claim planned for the guide traces to an identified source or is explicitly marked as synthesis.
- No citation treatment is selected that the available sources cannot support.

***

#### Step 1.3: Define the Domain-Agnosticism Boundary

**Required Actions**:

- List the domains in which the method must apply, spanning at least three dissimilar sectors.
- Identify every term in the source material that presupposes a specific organisation, product, architecture, or internal vocabulary.
- Produce a substitution list mapping each coupled term to a domain-neutral equivalent.

**Required Outputs**:

- A target domain list of no fewer than three sectors.
- A substitution list of coupled terms and their neutral replacements.

**Quality Checkpoints**:

- No term on the substitution list survives into the draft unreplaced.
- The method remains coherent when read against each named target domain.

***

### Phase 2: Source Analysis and Method Extraction

**Objective**: Recover the underlying procedure from source material that may present it as narrative, so that the procedure can be re-expressed as phases and steps.

#### Step 2.1: Measure Before Reading

**Required Actions**:

- Obtain word and line counts for every source document before opening it.
- Extract the heading skeleton and locate structural landmarks before reading prose.
- Plan a consumption strategy that reads full sections only where the procedure is dense, and samples elsewhere.

**Required Outputs**:

- A per-source measurement record listing words, lines, and heading counts.
- A reading plan naming which regions will be read in full.

**Quality Checkpoints**:

- No source was read in full before being measured.
- The reading plan covers every region containing procedural content.

***

#### Step 2.2: Extract the Latent Procedure

**Required Actions**:

- Identify every action the source instructs the reader to perform, in the order performed.
- Record for each action the precondition that permits it, the artifact it produces, and the test that confirms it succeeded.
- Mark actions the source states as prohibitions rather than instructions; these become checkpoints or limitations, not steps.

**Required Outputs**:

- An ordered action inventory with precondition, artifact, and test recorded for each entry.
- A separate list of prohibitions and failure conditions.

**Quality Checkpoints**:

- Every action in the inventory has a named artifact; actions producing nothing are either merged or removed.
- The inventory read end to end reproduces the source's method without gaps.

***

#### Step 2.3: Cluster Actions Into Phases

**Required Actions**:

- Group consecutive actions that share a common objective and terminate in a coherent deliverable.
- Name each group with an imperative-nominal phrase describing what the phase accomplishes.
- Verify the phase sequence is executable in order, with each phase consuming the prior phase's outputs.
- Split any group exceeding three steps; merge any group of one step into an adjacent phase.

**Required Outputs**:

- A phase list of 4–9 entries, each with a name and a one-sentence objective.
- A phase dependency statement confirming sequential executability.

**Quality Checkpoints**:

- Phase count falls within 4–9.
- Each phase consumes only outputs produced by earlier phases or by the guide's declared inputs.
- No phase name is a noun alone; each names an accomplishment.

***

### Phase 3: Skeleton Construction

**Objective**: Commit the document's heading structure in full before drafting any prose, so that structural conformance is guaranteed rather than retrofitted.

#### Step 3.1: Lay Down the Mandatory Section Sequence

**Required Actions**:

- Write the H1 title at line 1, followed by the document status block, then `## Executive Summary`. The status block is the only content permitted between the H1 and the Executive Summary; nothing else intervenes.
- Add the Operational Framework H2 as the first numbered section, or as the second if a foundational concepts section is warranted.
- Add the Implementation Guidance for AI Agents H2 immediately after the Operational Framework, titled verbatim.
- Add a domain-transfer H2, an optional limitations H2, a conclusion H2, and a references H2.

**Required Outputs**:

- A complete H2 sequence with numbering applied in the chosen variant.

**Quality Checkpoints**:

- `## Executive Summary` is unnumbered and appears exactly once, separated from the H1 only by the document status block.
- The string `Implementation Guidance for AI Agents` appears verbatim as an H2, with no rewording.
- Section numbering is monotonic with no gaps.

***

#### Step 3.2: Expand Phases and Steps

**Required Actions**:

- Write each phase as `### Phase N: Title`, numbering from 1.
- Write each step as `#### Step N.M: Title`, where `N` equals the parent phase number and `M` numbers steps within the phase from 1.
- Where the method's phases are indivisible, omit the step layer entirely and let the phase serve as the atomic unit; apply this decision uniformly across all phases.

**Required Outputs**:

- The full H3 and H4 skeleton with every phase and step named.

**Quality Checkpoints**:

- Every step number's major component matches its parent phase number.
- The step layer is either present for all phases or absent for all phases; mixed treatment is a defect.
- No heading below H4 exists anywhere in the document.

***

#### Step 3.3: Expand the Implementation Guidance Subsections

**Required Actions**:

- Write the three mandatory subsections verbatim, in order: `Structured Execution Protocol`, `Quality Assurance Checkpoints`, `Error Handling and Troubleshooting`.
- Add one further subsection covering learning, performance, human oversight, or documentation, named to fit the method.
- Apply lettered prefixes `A.`, `B.`, `C.`, `D.` to these H3s, or decimal prefixes matching the parent section number; hold one scheme throughout.

**Required Outputs**:

- The Implementation Guidance H3 skeleton with four subsections.

**Quality Checkpoints**:

- All three mandatory subsection names appear verbatim, in the stated order.
- Exactly one additional subsection is present.

***

### Phase 4: Operational Framework Drafting

**Objective**: Populate every step with the fixed slot sequence so that each step terminates in a verifiable output contract.

#### Step 4.1: Apply the Step Slot Template

**Required Actions**:

- Place `**Objective**:` followed by one sentence stating what is accomplished. Attach it either to every phase, immediately below the phase heading, or to every step; both placements are attested, and the chosen placement holds for the whole document.
- Follow with `**Required Actions**:` and a bullet list of imperative instructions, each beginning with a bare verb and eliding the subject.
- Follow with `**Required Outputs**:` and a bullet list of noun-phrase deliverables carrying no verbs.
- Close with `**Quality Checkpoints**:` and a bullet list of assertions stated in the present tense, each verifiable.
- Place `***` on its own line after each step.

**Required Outputs**:

- Every step populated with the actions, outputs, and checkpoints slots, a terminating rule, and an objective at the chosen placement level.

**Quality Checkpoints**:

- The colon sits outside the bold markers in every slot label.
- Action bullets begin with a verb; output bullets do not.
- Checkpoint bullets are assertions that can be judged true or false, not instructions.
- No step ends on prose; every step ends on a checkpoint block followed by `***`.

***

#### Step 4.2: Insert Substantive Sub-Blocks Where Warranted

**Required Actions**:

- Where a step requires a taxonomy, a selection matrix, or a worked schema, introduce it with a bold run-in caption naming the artifact.
- Render comparative or multi-attribute material as a markdown table using the `| :-- |` left-aligned separator row.
- Render procedural or structural material as an untagged fenced block in one of the five permitted genres named in Section 5.4.
- Precede every table and fence with its bold caption line and a blank line.

**Required Outputs**:

- Captioned tables and fences placed inside the steps that require them.

**Quality Checkpoints**:

- Table count for the document falls within 0–6.
- Every table and fence carries a bold caption line.
- No fence contains executable source in a general-purpose programming language.

***

#### Step 4.3: Quantify Every Threshold

**Required Actions**:

- Replace every vague quantifier with a numeric threshold or an explicit range.
- Express thresholds using plain-text operators rather than mathematical typesetting.
- State the consequence attached to each threshold, naming the action taken when it is breached.

**Required Outputs**:

- A draft in which every acceptance criterion carries a number and a consequence.

**Quality Checkpoints**:

- No occurrence of "sufficient", "adequate", "appropriate", or "reasonable" survives as an unqualified acceptance criterion.
- Every numeric threshold names what happens when it is not met.

***

### Phase 5: Implementation Guidance Drafting

**Objective**: Translate the human-oriented method into agent-executable instruction, specifying orchestration, verification, and recovery.

#### Step 5.1: Draft the Structured Execution Protocol

**Required Actions**:

- Open the section with one framing sentence in the third person, naming AI agents as the actor and using a modal obligation.
- Define the orchestration architecture, naming each agent role and the capabilities it requires.
- Specify the control flow between phases, including the condition that permits each transition.
- State the approval gate separating planning from execution, naming the threshold above which human authorisation is required.

**Required Outputs**:

- A named agent role inventory with capabilities per role.
- A phase transition specification with explicit conditions.
- A stated approval gate with its triggering threshold.

**Quality Checkpoints**:

- The framing sentence addresses AI agents in the third person and contains no second-person pronoun.
- Every declared agent role has at least one capability and one owned phase.
- The approval gate names a specific numeric or categorical trigger.

***

#### Step 5.2: Draft the Quality Assurance Checkpoints

**Required Actions**:

- Structure checkpoints as a tiered or phase-bound architecture, with each checkpoint bound to a named phase boundary.
- Give each checkpoint an automated check, an agent action on pass, an agent action on failure, and a human review trigger.
- State the human review trigger as a numeric rule.
- Where a scoring rubric is used, assign explicit weights summing to 100% and supply a 5-point anchor scale with a stated pass threshold.

**Required Outputs**:

- A checkpoint inventory with one entry per phase boundary.
- Pass and fail actions specified per checkpoint.
- A stated aggregate quality threshold.

**Quality Checkpoints**:

- Every phase boundary has at least one checkpoint.
- Every checkpoint distinguishes the halt path from the proceed-with-warning path.
- Rubric weights, where present, sum to exactly 100%.

***

#### Step 5.3: Draft the Error Handling and Troubleshooting Subsection

**Required Actions**:

- Classify errors either by recoverability or by named error type, and apply one scheme consistently.
- Give each error class a symptom set, a diagnostic procedure, and a resolution protocol offering more than one option.
- State an escalation trigger for each error class, expressed as a bounded retry count or a numeric threshold.
- Supply a troubleshooting decision tree as an untagged fenced block using box-drawing characters and arrows, or as an ordered prose ladder.

**Required Outputs**:

- An error taxonomy with symptoms, diagnostics, resolutions, and escalation triggers.
- One troubleshooting decision tree.

**Quality Checkpoints**:

- Every error class carries an escalation trigger with a bound.
- No error class resolves only by retrying without a retry limit.
- The decision tree terminates every branch in either a resolution or an escalation.

***

#### Step 5.4: Draft the Fourth Subsection

**Required Actions**:

- Select the fourth subsection's subject from learning and adaptation, performance metrics, human-in-the-loop integration, or documentation standards, choosing whichever the method most requires.
- Where performance metrics are chosen, group them into three families and attach a numeric target to each metric.
- Where human-in-the-loop is chosen, name the decisions that may not be automated.

**Required Outputs**:

- A completed fourth subsection matching the method's needs.

**Quality Checkpoints**:

- The subsection's subject is not a restatement of the three mandatory subsections.
- Metrics, where present, carry numeric targets.

***

### Phase 6: Closing Sections and Citation Treatment

**Objective**: Complete the domain-transfer, limitations, conclusion, and reference material to the corpus's closing conventions.

#### Step 6.1: Draft the Domain-Transfer Section

**Required Actions**:

- Open with one sentence asserting the framework's generalisability.
- Present adaptation guidance for each target domain named in Step 1.3, as bold-run-in cards or named principles.
- Address scale adaptation, contrasting small-scope and large-scope application.

**Required Outputs**:

- A domain-transfer section covering every target domain named in Phase 1.

**Quality Checkpoints**:

- Every domain named in Step 1.3 appears in this section.
- No domain card presupposes tooling unavailable in the other named domains.

***

#### Step 6.2: Draft Limitations and Conclusion

**Required Actions**:

- Write each limitation as a bold-run-in paragraph naming the problem, its consequence, and its mitigation, in that order.
- Where the method carries ethical exposure, address consent, confidentiality, transparency, and equity.
- Write the conclusion as two to four short paragraphs followed by a `**Key Success Factors**:` list of five to six bold-named items.
- Close with one forward-looking sentence stating what the framework enables.

**Required Outputs**:

- A limitations section with mitigations attached to every limitation.
- A conclusion carrying the Key Success Factors block.

**Quality Checkpoints**:

- No limitation is stated without a mitigation.
- The conclusion introduces no new procedure.

***

#### Step 6.3: Apply the Citation Treatment

**Required Actions**:

- Apply the treatment declared in Step 1.2, selecting from: a numbered author-year reference list; a deferral paragraph naming the source families with a pointer to the research artifact; or a pointer to the originating document.
- Where a numbered list is used, format entries as author, year, title, and italicised publication.
- Where sources are internal corpus documents, cite them by filename and path.

**Required Outputs**:

- A completed references section in the declared treatment.

**Quality Checkpoints**:

- No reference entry is fabricated; every entry corresponds to a source actually consulted.
- No placeholder text survives in the reference list.
- The treatment matches the one declared in Step 1.2.

***

### Phase 7: Conformance Verification and Release

**Objective**: Verify the finished guide against the conformance envelope and the prohibition list before it is committed.

#### Step 7.1: Measure the Draft Against the Envelope

**Required Actions**:

- Count words, headings by level, tables, fences, and horizontal rules.
- Compare every measurement against the envelope in Section 1.3.
- Exclude fenced-block content when counting headings, since comment markers inside fences produce false heading matches.

**Required Outputs**:

- A measurement record with one row per envelope property and a pass or fail verdict.

**Quality Checkpoints**:

- Every envelope property has been measured, not estimated.
- Heading counts exclude false matches originating inside fenced blocks.

***

#### Step 7.2: Run the Prohibition Sweep

**Required Actions**:

- Search for and remove every prohibited artifact named in Section 3.3.
- Confirm zero emoji, zero `---` rules, and zero second-person pronouns.
- Confirm no authoring scaffolding, prompt text, or generation commentary survives anywhere in the file.

**Required Outputs**:

- A prohibition sweep record listing each prohibited pattern and its occurrence count, all zero.

**Quality Checkpoints**:

- Every prohibited pattern returns a zero count.
- The file's first line is the H1 title and nothing precedes it.

***

#### Step 7.3: Register the Guide

**Required Actions**:

- Name the file `guide_<TaskFamily>.md`, using the corpus's existing capitalisation convention and avoiding spaces.
- Place the file in the category subfolder of `advanced_task_guides/` whose subject it shares, selecting from the nine existing categories: `authoring`, `design-architecture`, `knowledge-graphs`, `ontology`, `planning`, `policy-risk`, `research-analysis`, `scoring`, and `specialized`. Create a new subfolder only when no existing category fits, so that the guide's load path is `advanced_task_guides/<subfolder>/guide_<TaskFamily>.md`.
- Add the guide to the subfolder's row in the category table in `advanced_task_guides/README.md`.
- Place the document status block directly after the H1, before the Executive Summary, closed by a `***` rule. The block carries `**Status**:` on one line and `**Change logs**:` followed by one dated bullet per revision, most recent last, in the form `- [MM/DD/YYYY] - <change>`.
- Confirm the guide is self-contained, requiring no external file to be executable.

**Required Outputs**:

- A guide file committed under its category subfolder, and an updated README entry.

**Quality Checkpoints**:

- Filename matches `guide_<TaskFamily>.md` with no space characters.
- The file sits in exactly one category subfolder, and that subfolder's README row lists it.
- Every guide on disk appears in the README table, and every README entry resolves to a file on disk.
- The document status block is present exactly once, sits between the H1 and the Executive Summary, and carries at least one dated change-log entry.
- The guide references no unavailable external artifact as a precondition for execution.

***

## III. Implementation Guidance for AI Agents

AI agents producing methodology guides must follow systematic protocols ensuring structural conformance, evidential honesty, and reproducibility. The following guidance translates the authoring procedure above into agent-executable instructions.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Supervisor Agent**: Owns the guide commission, holds the conformance envelope, and authorises release. Enforces the prohibition list at every handoff.
2. **Source Analysis Agent**: Measures sources before reading, extracts the latent procedure, and produces the action inventory. Never reads a source it has not measured.
3. **Skeleton Agent**: Constructs the complete heading structure and validates numbering before any prose is drafted.
4. **Drafting Agent**: Populates steps with the slot template. Operates on one phase at a time to bound context consumption.
5. **Conformance Agent**: Measures the finished draft, runs the prohibition sweep, and returns a pass or fail verdict with evidence.

**Workflow Execution Pattern**:

```
STATE: Phase_3_Skeleton_Construction
ACTIONS:
  1. Emit full H2 sequence with numbering
  2. Emit H3 phase headings from the phase list
  3. Emit H4 step headings with parent-matched numbering
  4. Emit Implementation Guidance H3 subsections
VALIDATION:
  - mandatory_section_names_present == TRUE
  - step_number_parent_match == TRUE
  - max_heading_depth <= 4
TRANSITIONS:
  IF all_validations_pass THEN next_state = Phase_4_Framework_Drafting
  ELSE next_state = Phase_3_Error_Handling
```

**Two-Phase Action Pattern**:

1. **Plan**: Emit the skeleton and the slot inventory without prose.
2. **Validate**: Confirm structural conformance against Section 1.3 while the document is still cheap to restructure.
3. **Execute**: Draft prose only after the skeleton passes validation.

**Context Management Requirements**:

- Measure every source file before reading it, and read in bounded slices rather than whole files.
- Draft one phase per working pass, appending to the file rather than holding the whole document in working context.
- Where a guide exceeds the context available for a single pass, write a handoff record naming the completed phases, the pending phases, and the committed skeleton.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Scope Integrity (After Phase 1)**

- **Automated Check**: Title is a noun phrase; target domain list contains at least three entries; substitution list is non-empty where source material is project-coupled.
- **Agent Action on Pass**: Proceed to source analysis.
- **Agent Action on Failure**: Halt and return the specific scope defect.
- **Human Review Trigger**: If the source material's domain coupling cannot be resolved by substitution.

**Checkpoint 2: Procedure Completeness (After Phase 2)**

- **Automated Check**: Every action in the inventory carries a precondition, an artifact, and a test; phase count is within 4–9.
- **Agent Action on Pass**: Proceed to skeleton construction.
- **Agent Action on Failure**: Return to source analysis for the incomplete entries only.
- **Human Review Trigger**: If more than 20% of extracted actions lack an identifiable output artifact.

**Checkpoint 3: Structural Conformance (After Phase 3)**

- **Automated Check**: Mandatory section names present verbatim; numbering monotonic; step numbers match parent phases; no heading deeper than H4.
- **Agent Action on Pass**: Proceed to drafting.
- **Agent Action on Failure**: Halt; structural defects must be corrected before prose is written.
- **Human Review Trigger**: If the method resists expression as 4–9 sequential phases.

**Checkpoint 4: Slot Completeness (After Phase 4)**

- **Automated Check**: Every step carries the actions, outputs, and checkpoints slots and terminates in `***`; objective placement is uniform across the document; no step ends on prose.
- **Agent Action on Pass**: Proceed to Implementation Guidance drafting.
- **Agent Action on Failure**: Return the list of steps with missing slots.
- **Human Review Trigger**: If a step genuinely produces no output artifact.

**Checkpoint 5: Release Conformance (After Phase 7)**

- **Automated Check**: All envelope properties within range; all prohibited patterns at zero count; filename convention satisfied.
- **Agent Action on Pass**: Register the guide and update the README.
- **Agent Action on Failure**: Halt; return the failing properties with measured values.
- **Human Review Trigger**: Any envelope property outside range by more than 20%.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
TRIGGER:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
FAIL_ACTION:
RESPONSIBLE_AGENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Source Material Resists Phase Decomposition**

- **Symptoms**: The extracted action inventory has no natural clustering; candidate phases have circular dependencies.
- **Diagnostic Steps**: Confirm the source describes a procedure rather than a taxonomy; check whether the circularity is an iteration loop rather than a dependency cycle.
- **Resolution Protocol**: Option A, express the loop as a terminal phase that returns to an earlier phase under a stated condition. Option B, split the method into a sequential core and an iterative refinement phase. Option C, reclassify the material as unsuited to the Operational Framework archetype and report this.
- **Escalation Trigger**: If three clustering attempts yield no acyclic phase sequence.

**Error Type 2: Project Coupling Survives Substitution**

- **Symptoms**: The draft references an architecture, product, or internal vocabulary absent from the substitution list.
- **Diagnostic Steps**: Sweep for possessive framing and for capitalised internal acronyms; check each against the target domain list.
- **Resolution Protocol**: Option A, replace with the neutral equivalent. Option B, where the term is intrinsic to the method, define it in the terminology subsection. Option C, remove the passage if it carries no domain-general content.
- **Escalation Trigger**: If the method cannot be stated without naming a specific product.

**Error Type 3: Conformance Envelope Breach**

- **Symptoms**: Measured heading counts or device counts fall outside Section 1.3, or word count falls below the lower bound.
- **Diagnostic Steps**: Determine whether the deviation reflects genuine method complexity or drafting bloat; recount headings excluding fenced content.
- **Resolution Protocol**: Option A, if under-length, expand the thinnest phases with actions and checkpoints rather than with narrative. Option B, if the document carries narrative or duplicated framing, remove it, never removing procedure. Option C, if a single guide covers two separable methods, split it into two guides with a stated composition relationship.
- **Escalation Trigger**: Structural counts outside range after one correction pass. Word count above the observed range is not an error and is never resolved by deleting procedure.

**Error Type 4: Fabricated Citation Risk**

- **Symptoms**: Reference entries cannot be traced to a consulted source; placeholder text appears in the reference list.
- **Diagnostic Steps**: Match every reference entry against the Step 1.2 source inventory.
- **Resolution Protocol**: Option A, remove the untraceable entry. Option B, switch to the deferral treatment naming source families rather than individual works. Option C, cite the internal corpus document by path.
- **Escalation Trigger**: Any untraceable entry halts release; this error is never resolved by retry.

**Troubleshooting Decision Tree**:

```
GUIDE FAILS CONFORMANCE
├─ STRUCTURAL DEFECT
│   ├─ Mandatory section name altered → Restore verbatim string
│   ├─ Step number mismatch → Renumber from parent phase
│   └─ Heading deeper than H4 → Convert to bold run-in slot
├─ CONTENT DEFECT
│   ├─ Step ends on prose → Append output and checkpoint slots
│   ├─ Unquantified threshold → Replace with numeric bound and consequence
│   └─ Limitation without mitigation → Add mitigation or remove limitation
├─ SCOPE DEFECT
│   ├─ Domain coupling present → Apply substitution list
│   └─ Fewer than three target domains → Return to Step 1.3
└─ PROVENANCE DEFECT
    ├─ Untraceable citation → HALT, remove or re-treat
    └─ Authoring scaffolding present → Strip to H1 at line 1
```

**Prohibited Artifacts**:

The corpus's machine-generated documents carry export residue that must never be reproduced in a new guide. Each is an artifact of the generation pipeline, not a style choice:

- Export sentinels rendered as a centred HTML division containing a decorative glyph.
- Hidden HTML spans used to bind unreferenced footnotes.
- Vendor logo image tags.
- Raw authoring prompts, prompt fragments, and generation commentary such as a sentence announcing that the guide is about to be produced.
- Bracketed continuation placeholders standing in for unwritten reference entries.
- Escaped ampersands outside code contexts.
- Bare-URL footnote definition blocks presented as a reference list.
- Literal broken constructions left by citation substitution, such as an empty parenthetical example.

### D. Performance Metrics and Continuous Learning

**Conformance Metrics**:

- **Structural pass rate**: Proportion of drafts passing Checkpoint 3 without correction (target: ≥90%).
- **Slot completeness**: Proportion of steps carrying the actions, outputs, and checkpoints slots (target: 100%).
- **Envelope adherence**: Proportion of measured properties within range (target: 100%).

**Quality Metrics**:

- **Threshold density**: Proportion of acceptance criteria carrying a numeric bound (target: ≥95%).
- **Citation traceability**: Proportion of reference entries traceable to the source inventory (target: 100%).
- **Domain coverage**: Number of target domains addressed in the transfer section (target: ≥3).

**Efficiency Metrics**:

- **Rework rate**: Proportion of phases requiring a second drafting pass (target: ≤15%).
- **Context overruns**: Count of drafting passes aborted for context exhaustion (target: 0).

**Learning and Adaptation Mechanisms**:

- **Feedback collection**: Record every conformance failure with its checkpoint, its cause, and its correction.
- **Template refinement**: Where the same slot is repeatedly omitted, add it to the skeleton emitted in Phase 3 rather than relying on drafting discipline.
- **Envelope maintenance**: Recompute the conformance envelope when the corpus grows by more than five guides, since the envelope is derived from the corpus and not fixed a priori.

***

## IV. Domain-Agnostic Application Guidance

This guide is designed for generalisability across the task families the corpus serves. Its procedure does not depend on the subject matter of the guide being written.

**Analytical methods**: Phases map to the analysis pipeline, from scoping through data collection, evaluation, and reporting. The Implementation Guidance section carries the statistical validity checks as quality checkpoints.

**Design and architecture methods**: Phases map to the design lifecycle, from requirement capture through option generation, selection, and validation. Limitations should address the reversibility of design commitments.

**Planning and reasoning methods**: Phases map to the planning loop, from goal capture through decomposition, candidate generation, selection, execution, and replanning. Where the method is iterative, the terminal phase states the condition returning control to an earlier phase, and the checkpoint architecture governs loop termination.

**Knowledge engineering methods**: Phases map from competency question capture through schema construction, validation, and evolution. The domain-transfer section should address vocabulary reuse across knowledge domains.

**Scale adaptation**:

- **Compact guides** (under 2,500 words): Collapse the step layer, retain the phase layer, retain all three mandatory Implementation Guidance subsections, and reduce the fourth subsection to a short metrics list.
- **Long-form guides** (5,000 words and above): Apply the full phase and step nest as specified. Length is bounded by the method's actual procedural content, not by a target figure.
- **Composite methods** exceeding the envelope: Split into two guides with an explicit composition relationship stated in each guide's Executive Summary, rather than exceeding the envelope in one document.

***

## V. Limitations and Considerations

**Derived normativity**: The house style described here is reverse-engineered from the existing corpus, not from an independent standard. Where the corpus is internally inconsistent, this guide selects the majority convention and marks the alternative as accepted. A future corpus may drift from these conventions, and the envelope in Section 1.3 must be recomputed rather than assumed stable.

**Provenance heterogeneity**: A substantial part of the corpus was machine-generated and lightly edited, and carries export residue. This guide separates the intentional structural conventions from that residue, but the separation is a judgement based on artifact analysis. Where a pattern's status is genuinely ambiguous, prefer the cleaner convention.

**Two conventions of contested status**: The `***` horizontal rule and the `| :-- |` table separator prescribed above correlate almost perfectly with the machine-generated portion of the corpus. Of the 23 guides using `***`, 22 are export-derived, and every citation-free hand-authored guide uses `---` instead; the `| :-- |` separator appears in twelve guides and all twelve are export-derived, while hand-authored tables use `| --- |`. These two conventions are therefore prescribed here for consistency with the Operational Framework family a new guide will sit beside, not because their origin is demonstrably editorial. Both render identically in standard markdown, so the choice carries no reader-facing consequence. A future decision to standardise the corpus on `---` and `| --- |` would be well founded, and this guide should be amended rather than treated as an obstacle to it.

**Structural conformance is not quality**: A guide can satisfy every measurement in Section 1.3 and still encode a poor method. The envelope detects malformation, not unsoundness. Method quality remains a matter for review against the source evidence, and no checkpoint in this guide substitutes for that review.

**Citation integrity**: The corpus's dominant citation treatment is a bare-URL footnote block produced automatically. That treatment cannot be reproduced honestly by an agent that did not perform the underlying retrieval. An agent writing a new guide must select a treatment its actual sources support, and must never synthesise reference entries to match the corpus's citation density.

**Domain-agnosticism is asserted, not verified**: The corpus asserts generalisability in its transfer sections, but several guides remain coupled to a specific architecture and internal vocabulary. Substitution as specified in Step 1.3 reduces this risk without eliminating it; genuine verification requires reading the guide against a domain outside the one it was drafted from.

***

## VI. Conclusion and Summary

Guide writing for this corpus is a structural discipline before it is a writing task. The method's quality is carried by the phase and step decomposition, and the guide's usability by an agent is carried by the slot template and the Implementation Guidance section. An author who commits the skeleton before drafting prose, quantifies every threshold, and terminates every step in a verifiable output contract will produce a conforming guide; an author who drafts prose first will produce an essay that resists retrofitting.

**Key Success Factors**:

- **Skeleton before prose**: Structural defects are cheap to fix before drafting and expensive afterwards.
- **Slot discipline**: The four-slot step template is what makes a guide executable rather than merely readable.
- **Numeric thresholds**: Every acceptance criterion carries a number and a stated consequence.
- **Measured conformance**: The envelope is checked by measurement, never by impression.
- **Evidential honesty**: No citation is written that the author's sources do not support, and no artifact of the authoring process survives into the released file.
- **Domain neutrality**: The method is stated so that it holds across at least three dissimilar sectors.

By following this guide, AI agents can convert research material and prose documents into methodology guides that conform to the corpus's house style, remain executable at runtime, and carry the verification machinery needed for reliable autonomous use.

***

## VII. References and Further Reading

This guide is derived from structural analysis of the 31 methodology guides that `advanced_task_guides/` contained at the time the analysis was performed. The directory has since grown to 41 guides distributed across nine category subfolders, so the conventions specified above were derived from a subset of the present corpus. The following corpus documents were analysed directly and serve as the primary evidence for the conventions specified above.

**Primary exemplars of the Operational Framework archetype**:

1. `advanced_task_guides/research-analysis/guide_BarrierAnalysis.md` — the most complete instance of the archetype; carries the full phase and step nest, the glossary section, pseudocode fences, the ASCII decision tree, and the only human-readable numbered reference list in its group.
2. `advanced_task_guides/policy-risk/guide_ControlEffectiveness-by-ConditionAnalysis.md` — the most regular step template; the only guide carrying a worked case study.
3. `advanced_task_guides/policy-risk/guide_Cross-jurisdictionalComparativePolicyAnalysis.md` — the table-heavy variant; source of the weighted quality rubric pattern.
4. `advanced_task_guides/design-architecture/guide_DesignAdaptation.md` — source of the lettered Implementation Guidance subsections and the quality gate table.
5. `advanced_task_guides/design-architecture/guide_FrameworkMappingAdoptionFitAnalysis.md` — the maximal instance; source of the protocol subsection pattern.
6. `advanced_task_guides/policy-risk/guide_InformationDependencyDisclosureRiskAnalysis.md` — the phase-as-atomic-unit variant; source of the checkbox checkpoint treatment.
7. `advanced_task_guides/policy-risk/guide_SystemSpecificRiskAssessment.md` — the `Part I` numbering variant.
8. `advanced_task_guides/research-analysis/guide_Cross-domainAnalogyandTransfer.md` — the no-H4 variant; source of the per-action deliverable pattern.

**Secondary archetypes, analysed for contrast and excluded as non-normative**:

9. `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md`, `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md`, `advanced_task_guides/knowledge-graphs/guide_KG_HumanAIcolab.md`, `advanced_task_guides/knowledge-graphs/guide_KG_ScalabilityArch.md`, `advanced_task_guides/knowledge-graphs/guide_KG_SchemaDesign.md` — the Research Brief archetype.
10. `advanced_task_guides/knowledge-graphs/guide_KG_identifierFairPrinciples.md`, `advanced_task_guides/knowledge-graphs/guide_KG_QualityControl.md` — the Engineering Handbook archetype.
11. `advanced_task_guides/scoring/guide_complexityScoring.md`, `advanced_task_guides/scoring/guide_techAcceptanceScoring.md` — the Compact Rubric archetype; the corpus's most recent additions and the source of the compact-guide guidance in Section IV.

**Authoring specification**:

12. `advanced_task_guides/design-architecture/guide_DesignTechnicalBookStudyPlan.md`, lines 3–17 — unstripped authoring scaffolding preserving the original house-style specification verbatim. The scope rules in Section 1.4 are taken from this source. Note that the presence of this scaffolding in a released file is itself a defect of the kind Section 7.2 exists to prevent.

**Corpus documentation**:

13. `advanced_task_guides/README.md` — states the design intent for guides: self-contained, structured, domain-agnostic, and loadable at runtime.
