---
created: "2026-11-04T20:24:32Z"
updated: "2026-11-04T20:24:32Z"
---

# Revision passes for a beginner-friendly chapter

The diagnosis table, then the six passes in order, then the reviewer plan. The grouping of the prose techniques into the six passes is this skill's arrangement.

## Diagnosis: draft problems and the pass that fixes each

| Problem | Sign in the draft | Fixed in |
|---|---|---|
| Cognitive overload | One section introduces several new ideas, variants or integration points at once | Pass 1 |
| Disconnected chapter | No links back to prerequisite chapters or forward to applications | Pass 1 |
| Isolated misconceptions | Misconceptions gathered in a separate errors section or sidebar box | Pass 1 |
| Abstract-first presentation | Formal definition before any concrete example | Pass 2 |
| Weak or missing examples | Definitions with little context; few worked examples; no when or why | Pass 2 |
| Missing scaffolding | Content jumps from demonstration to independent work with no guided practice | Pass 2 |
| Fragmented architecture | Sections are a heading followed by parallel bullets or definitions, each item standalone | Pass 3 |
| Minimal connective narrative | Concepts follow each other with no causal words (because, therefore, as a result) | Pass 3 |
| Dense paragraphs | Paragraphs of 8 or more sentences; long sentences | Pass 3 |
| Passive voice dominance | Who does what is hidden behind passive constructions | Pass 3 |
| No visual supports | Complex processes or comparisons explained in text only | Pass 4 |
| Jargon density | Technical terms used without definition; one thing called by several names | Pass 5 |

## Pass 1: Content structure (chapter level)

- One new element per section: each section adds exactly one new dimension of complexity, opens by reviewing what the previous section taught, and stops before the next variant. Split a section that combines several. Close a run of such sections with an integration checkpoint: practice comparing the variants, synthesis questions across the sections, and when to use each.
- Order concepts from simple to complex. When the chapter presents several alternatives (frameworks, variants, approaches), order them by architectural complexity rather than alphabetically, and introduce each by contrast with the one before (we extend this to handle a new case).
- Chapter opening: preview every major section and explain why the sequence matters; state each prerequisite chapter the chapter builds on and what it contributes; turn chapter metadata lists (difficulty, study time, exam weight) into narrative framing near the start that says why each matters. A prerequisite self-assessment stays a checklist.
- Misconceptions: move each one to the place where it naturally arises, say why it feels plausible, and write it as a contrast (this is powerful but carries risk X; however, Y prevents it). Then delete the emptied box or section.
- Bridges: end each major section with 2 to 3 sentences that preview the next section's problem (X enables this; but X has limitation Y; that is where the next section comes in).
- Chapter end: a cumulative problem, a realistic scenario that needs 3 or more of the chapter's concepts and traces them back to the chapters they came from.
- Headings never skip a level.
- Progressive disclosure for dense material: keep the core (definition, primary mechanism, one key example, why it matters) in the main text and self-sufficient; mark extended material (variants, edge cases, related concepts, advanced applications) and deep material (mathematical foundations, research, architectural trade-offs) as optional, with a clear signal of what the reader gains by reading on.

## Pass 2: Scaffolding (section level)

- Section opening: 3 to 4 sentences that give a prerequisite reminder (one sentence linking back to an earlier chapter or section), the current focus, and an application bridge (one sentence on the real-world use). The opening answers why the reader is learning this. Section headings state purpose as well as topic (a concept name plus when it matters).
- Concept order inside a section: a plain, standalone definition with a one-sentence key insight; why it matters; a concrete, familiar example with annotations; a representational view (diagram or pseudocode); then the abstract formulation (formal definition, notation). Do not bury the definition mid-paragraph. Placing the opening framing before the definition is this skill's way of combining the two methods.
- Definition lists of several related terms: rewrite them as one narrative in which each term is defined in context, its rationale is given, and its relation to the others is shown (X is not enough; that is where Y comes in). The section's main concept keeps its upfront definition; this split between upfront and embedded definitions is this skill's reconciliation of the two methods.
- Worked examples: launch each new concept with 2 to 3 worked examples of the same problem type with different surface features, each showing the full reasoning with annotations. Include at least one negative example (where the concept fails or does not apply). Follow with similar problems for guided practice with hints, and only then independent problems. Mix by position in the chapter: opening sections 70% worked examples and 30% problems, middle sections 50% and 50%, end sections 20% and 80%.
- Comparisons: when comparing variants, run the same scenario through each so that only the differences change. For an implementation pattern, show a naive, a better and a production-quality version and say what breaks in each. For alternatives that solve one problem, show how each would solve it, list advantages and disadvantages for that problem, and end with choose X if, Y if.
- When it matters: for each major framework or pattern, add 2 sentences on when to use it and one example of where it fails or is not the best choice.
- Feature lists: rewrite as problem-solution pairs (the problem, then how the tool solves it), with the practical constraint that makes it matter (cost, latency, reliability).
- Analogies: for an abstract concept with no clear mental model, write a 2 to 3 sentence analogy a non-technical reader could follow, and refer back to it later.
- Depth signals: for a concept with several levels, say what first-time learners should grasp, what practitioners building systems need, and what advanced readers must consider.
- Dependency chains of 3 or more concepts: describe the chain in prose (building on this comes that; finally) and add a diagnostic (if X confuses you, review Y).
- Section end: a synthesis question connecting the section to prior learning. Every third section, review questions in a mix of about 70% current chapter, 20% prior chapters and 10% foundations from the first chapter.
- Key takeaways: replace bullet takeaways with a 2 to 3 sentence synthesis that starts with what you have learned, connects the concepts, and ends with when to use them.

## Pass 3: Readability polish (sentence level)

- Lists: 1 to 3 items go inline into prose; 4 to 7 items may stay as a list with an introductory sentence that explains how the items relate; 8 or more become prose with topic sentences, a table or section headings. Keep as lists: prerequisite checklists, step-by-step procedures (numbered), comparison tables and tool parameter specifications.
- Bullets to paragraphs: write 1 to 2 topic sentences that state the relationship among the items, then the items as active-voice prose joined by causal connectors. Test: delete the bullets; if the prose no longer flows, rewrite.
- Transitions: before writing, mark each relationship between ideas as cause, contrast, addition, sequence or example, then write the connector explicitly: because, therefore, as a result, consequently (cause); but, however, by contrast, whereas (contrast); furthermore, moreover, also (addition); then, subsequently, previously (time); for instance, to illustrate, specifically (example). Each paragraph opens with context from the one before. Test: if the transition word can be deleted and the prose still connects, make it more explicit.
- Sentence length: aim for an average of 15 to 20 words and split any sentence over 25 words into 2 or 3. Vary rhythm: when more than 70% of sentences run 12 to 18 words, alternate 2 to 3 longer sentences (18 to 25 words) that explain with 1 to 2 short ones (5 to 8 words) that emphasize.
- Passive voice: convert to active (researchers describe, not it is described); keep passive only when the actor is unknown or blame is being avoided; target at most 10% passive sentences.
- Keep subject and verb close (no long intervening clause) and remove redundancy (the same idea explained twice).
- Vague words (often, sometimes, frequently, generally, many, quite, somewhat): replace with specifics; when no specific is available, use typically, in most cases or commonly.
- Jargon: replace with a plain-language alternative where one exists.
- Paragraphs: one topic each, a topic sentence first, at most 7 sentences.
- Code blocks: precede each with 1 to 2 sentences on what it implements and follow it with 2 to 3 sentences on what to notice and why it matters; explain important logic in the prose, not only in the code.
- Emphasis: bold a key term at its first introduction only, plus important caveats, code terms and critical warnings; italics for a concept being defined; no more than 15% of a paragraph in bold; no all caps, no strings of exclamation marks, no emphasis by color alone.

## Pass 4: Visual enhancement (diagram level)

- Every complex concept gets at least one visual, of the type that matches its purpose: concept diagram (components and relationships), process flowchart (step-by-step operation), comparison matrix (options and trade-offs), hierarchy or taxonomy diagram (classification), sequence diagram (order and timing).
- The caption says what the visual shows and why it matters, never a bare label. Alt text describes the content specifically. Key elements are labelled, never coded by color alone. The text mentions the figure before it appears, and the figure sits next to the text it supports.
- Existing figures: check the type, caption, placement and the mention in the text.

Placeholder for a figure to be drawn (format example):

```text
As Figure 3.2 shows, each failed request moves the breaker one step closer to open.

[Figure 3.2, process flowchart, to be drawn]
Caption: How a circuit breaker moves between closed, open and half-open. It stops
calls to a failing service, then tests whether the service has recovered.
Alt text: Three boxes labelled Closed, Open and Half-open, joined by arrows labelled
failure threshold reached, timeout ends, test call succeeds and test call fails.
```

## Pass 5: Terminology consistency (global)

- Extract every bolded, italicized or technical term.
- Standardize: one name per thing throughout (a model is never also a system, an agent never also an actor), and a term the prior chapters define keeps their definition.
- Give each term's first appearance a definition.
- Term table for the log: Term, Definition as used, Variants replaced, Section of first use.

## Pass 6: Beginner check

For each section, ask:

- Can a beginner follow it with only prior-chapter knowledge, or does it assume knowledge not yet taught?
- Are prerequisite concepts reviewed, not just assumed?
- Would a non-expert understand it? Read it as if aloud to catch awkward phrasing.
- Are the examples relevant to the learner's experience?
- Do the end-of-section questions connect to prior chapters?

## Reviewer plan (for Open items)

Before the chapter is final, 3 to 5 people representing the audience review it:

- Recent learner (has finished the previous chapter): can they follow without other materials; where do they get stuck; which terms confuse them.
- Domain expert: is technical accuracy kept; are misconceptions presented correctly; are simplifications correct, not just simpler.
- Instructional designer: is the scaffolding adequate; do the transitions between sections work; are the learning objectives achievable.
- Copy editor: terminology consistency, clarity of language, readability.

Questions for every reviewer: what was most confusing; which examples helped most; where did you feel lost; would you trust this to teach a colleague; what would you add or remove.
