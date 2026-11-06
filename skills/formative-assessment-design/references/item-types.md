---
created: "2026-11-04T20:00:01Z"
updated: "2026-11-04T20:00:01Z"
---

# Item types by layer and cognitive level

Use this file when choosing the item type for each row of the assessment map. Levels follow the revised Bloom's taxonomy (Anderson and Krathwohl).

## Cognitive levels

| Level | Typical verbs | What the learner does |
|---|---|---|
| 1 Remember | recall, define, identify | Retrieves facts from memory |
| 2 Understand | explain, describe, classify | Grasps the meaning of information |
| 3 Apply | use, solve, calculate | Uses knowledge in a new situation |
| 4 Analyze | compare, contrast, distinguish | Breaks down relationships |
| 5 Evaluate | judge, justify, assess | Makes and defends a value judgement |
| 6 Create | combine, design, develop | Puts elements together into a new whole |

Write each item to require its target cognitive process. The level is set by the learning objective; actual difficulty also depends on how specific the content is and how mature the learners are, so it is confirmed by piloting.

## Layer 1: knowledge checks

Brief (1 to 5 questions), low-stakes, with immediate feedback, placed right after a concept is introduced and before learners move to applying it.

- Concept completion (Remember): verifies recall of a term or fact just introduced. Formats: fill-in-the-blank, short answer, term matching. Lowest difficulty.
- Definition or explanation (Understand): verifies the learner grasps what the concept means, not only its wording. Formats: a one-sentence explanation, a how-does-X-differ-from-Y question, multiple choice with explanations. Low to moderate difficulty.
- Application to an example (Apply): verifies the learner can use the concept on a concrete case. Formats: a short scenario with a question, a problem to solve, a diagram to identify. Moderate difficulty.
- Discrimination (Analyze): verifies the learner can tell similar concepts apart. Formats: multiple choice with plausible wrong answers, a comparison question. Higher difficulty. Because knowledge checks stay at Remember, Understand or Apply, place discrimination items in the comprehension or exam-style layer.

## Vocabulary exercises

Spread them through the chapter where the terms are taught, not in a separate vocabulary section: terms learned while applying concepts transfer better than terms from an isolated list. A typical flow is matching new terms to their functions in an early section, fill-in-the-blank with terms in context next, discrimination of which terms fit a scenario after that, and using the terms to explain a real-world application near the end.

- Matching: terms to definitions or functions.
- Term in context: a fill-in-the-blank sentence that contrasts two terms.
- Discrimination: which term is closest in meaning to a given term, with a short explanation of why.
- Application: a sentence from professional practice in which the learner supplies the right term for each situation.

## Layer 2: comprehension exercises

Higher-order questions asking for explanation, application or analysis, placed where concepts are integrated. Each gets an exemplary answer or a rubric showing the expected depth.

- Concept explanation: explain in two or three sentences why one thing behaves differently from another.
- Scenario-based comprehension: explain design choices for a described situation, then how the choices change when one condition changes.
- Misconception correction: say why a given statement is incomplete or wrong and what is actually different.
- Integration: connect an earlier chapter's content to this chapter's, for example as a diagram or table the learner builds.

## Layer 3: exam-style practice

Items matching the certification exam's format and difficulty, near the chapter end and cumulative. Common technical exam formats: multiple choice (4 to 5 options, one answer), multiple select (several correct answers required), scenario-based (a complex case analysed before the questions) and performance-based (the learner performs a task, such as configuring or troubleshooting, and a system evaluates it).

Multiple-choice structure:
- Stem: a clear question, avoiding negatives where possible.
- Correct answer: specific and grammatically consistent with the stem.
- Distractors: plausible wrong answers that match the item's difficulty; no all-of-the-above option, which lets learners answer by elimination.
- Rationale: why the correct answer is correct and why each wrong option is wrong.
- Target: professional judgement (analysing symptoms, deciding what to investigate first), not trivial recall.

Scenario-based structure:
- Setup of two or three paragraphs: context, current situation, problem.
- Data: the relevant information, such as logs, error messages or system details.
- Question: what would you do, or what is the cause.
- Options: several valid-looking approaches with one best answer, and a reason given for each option.

Chapter practice test mix (all levels, cumulative): 40% Remember or Understand, 35% Apply, 20% Analyze or Evaluate, 5% Create.

## Difficulty progression

Within a section, items move up the levels: recall of the term, then its meaning, then a realistic calculation or use, then a comparison, then a justified recommendation.

Across a chapter:

| Part of chapter | Levels | Format | Feedback |
|---|---|---|---|
| Early sections | Remember, Understand | Knowledge checks: fill-in-the-blank, true or false, simple recall and application | Corrective and scaffolded |
| Mid sections | Apply | Comprehension exercises: short answer, scenario with a question | Moderate scaffolding |
| Late sections | Analyze, Evaluate | Practice questions in exam format, multiple choice with plausible distractors | Minimal scaffolding; learner works out the approach |
| Chapter review | Create, cumulative | Full mixed-topic practice test with items from this and earlier chapters | Limited feedback; peer discussion |

Knowledge-check frequency by the chapter's place in the book:
- Early, foundational chapters: several checks per section, simple and highly scaffolded, later checks including earlier concepts.
- Middle chapters: 1 or 2 checks per section, needing some thinking and combining several prerequisites.
- Advanced chapters: 1 check per major concept section, complex, needing synthesis, with minimal scaffolding.

An open-ended Evaluate or Create item can turn out easier than intended, because many answers are acceptable. Constrain it: ask for the design and a justification against the named alternatives the chapter taught, with their trade-offs.

## Example (format only)

```text
Section 4.2 Subnet masks (middle chapter, objective 4.2: calculate subnet sizes, Apply)

KC 4.2a  Remember  Fill in the blank: a /24 mask leaves ___ bits for hosts.
         Key: 8
KC 4.2b  Understand  In one sentence, say what a subnet mask tells a host.
         Key: which part of an address is the network and which part is the host
KC 4.2c  Apply  A lab needs 50 usable addresses on one subnet. What is the
         smallest prefix that fits?
         Key: /26 (62 usable hosts)
```
