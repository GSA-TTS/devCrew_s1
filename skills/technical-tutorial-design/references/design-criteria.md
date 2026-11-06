---
created: "2026-11-04T20:21:15Z"
updated: "2026-11-04T20:21:15Z"
---

# Design criteria by plan section

One section per section of the plan. Each gives the items to draw on when writing that section.

## 1. Learners

Persona components (a persona is a fictional but data-informed profile of one learner group):

- Demographics: role, experience level, industry, geography.
- Technical background: prior knowledge, skills, certifications.
- Goals: what success means to them; career aspirations.
- Motivations: why they are taking the tutorial; expected outcomes.
- Constraints: time availability, device access, learning environment.
- Preferences: solo or collaborative, theory or hands-on, sequential or exploratory.
- Challenges: common misconceptions, learning difficulties, barriers.
- Context: how they will apply the knowledge; the job tasks that need it.

Analysis items: performance gaps and prerequisites; the job tasks that require the skills; environmental constraints (device types, network speed, time availability).

Differentiation paths, when there is more than one learner group:

- Role-based paths: each role focuses on the part of the topic its job needs.
- Experience levels: beginner paths give extensive scaffolding; advanced paths assume prior knowledge.
- Interest-based: learners choose the modules relevant to their goals.
- Time-constrained versions: a condensed fast track for experienced learners; an extended deep dive for novices.

## 2. Objectives

SMART criteria:

- Specific: says precisely what learners will achieve, with an action verb from the taxonomy below.
- Measurable: a quantifiable success criterion or an observable performance indicator.
- Achievable: realistic within the timeframe and the learners' skill level, given prerequisites and resources.
- Relevant: aligned to real-world job tasks, business outcomes or educational standards.
- Time-bound: states the timeframe.

Revised taxonomy of cognitive levels:

| Level | Focus | Typical activities |
|---|---|---|
| Remember | Recall facts, terminology | Definitions, flashcards, lists |
| Understand | Grasp meaning, interpret relationships | Explanations, summaries, comparisons |
| Apply | Use knowledge in new situations | Demonstrations, simulations, case studies |
| Analyze | Break down concepts, identify patterns | Comparative analysis, root cause investigation |
| Evaluate | Make judgments based on criteria | Critical assessment, peer review |
| Create | Synthesize to produce novel solutions | Design projects, problem-solving |

Competency progression: defined competencies (observable skills tied to job roles or certification standards); mastery criteria (rubrics, performance thresholds); multiple assessment opportunities; adaptive paths with prerequisite remediation; flexible pacing. A competency chain runs foundation (prerequisite), intermediate, advanced, expert, each building on the one before.

Format example of a weak and a strong objective:

```text
Weak:   Understand regular expressions.
Strong: By the end of this 15-minute exercise, learners will write a regular
        expression (Apply) that extracts every date from a sample log file and
        passes all twelve provided test strings.
```

## 3. Structure

Chunking process: identify the core concepts learners must understand; order the chunks to build progressively; give each chunk one objective; keep need-to-know content and remove nice-to-know details. Present one core idea per screen or slide.

Hierarchy:

- Level 1: course or module.
- Level 2: topics.
- Level 3: subtopics, one per learning objective.
- Level 4: individual learning activities (video, lab, quiz).

Navigation support: breadcrumb trails, clear section headings and subheadings, a linked table of contents, search, next and previous buttons.

Links and cross-references: link to prerequisite knowledge instead of repeating it; cross-reference related concepts; give just-in-time access to supplementary information; mark which resources are mandatory and which optional.

Scaffolding stages (support fades as learners gain mastery, within the zone between what they can do alone and what they can do with support):

- Early modules: complete code examples, detailed screenshots, step-by-step walkthroughs.
- Intermediate modules: partially completed code that learners finish (Parsons problems, code completion tasks).
- Advanced modules: open-ended challenges where learners design the solution from scratch.

Experiential cycle within a module: concrete experience (hands-on work), reflective observation (what happened and why), abstract conceptualization (link to the underlying principle), active experimentation (learners test variations and predict outcomes).

## 4. Media

Multimedia principles:

| Principle | Apply it by | Pitfall |
|---|---|---|
| Multimedia | Combining words and images | Text only or images only |
| Coherence | Excluding extraneous information | Decorative graphics, background music |
| Signaling | Highlighting key information | Assuming importance is obvious |
| Redundancy | Not duplicating on-screen text as narration | Reading on-screen text aloud |
| Spatial contiguity | Placing text next to its graphic | Labels apart from their images |
| Temporal contiguity | Showing visuals with the narration | Visuals after the verbal explanation |
| Segmenting | Breaking complex animations into steps | Showing the whole process at once |
| Pre-training | Introducing key concepts before the main lesson | Assuming prerequisite knowledge |
| Modality | Delivering words as speech with graphics | On-screen text together with narration |
| Personalization | A conversational tone | Formal, distant language |
| Voice | An engaging human voice | Machine-generated or monotone narration |
| Image | Engaged instructors who gesture | Static images of instructors |

Medium by content: diagrams for architecture and workflows; video for procedures and complex processes; text summaries for reference; interactive elements for practice.

Video practices: clear, conversational, unhurried narration; brief pauses between sections; high-contrast readable text and zoom on detail areas; complex procedures split into logical steps; low on-screen text density, with graphics reinforcing the spoken content; brief moments of humor or personal connection and varied camera angles.

## 5. Practice and labs

Activity types:

- Worked examples: step-by-step solutions to typical problems, moving from high to lower support.
- Parsons problems: learners put scrambled code blocks in order; less typing, same thinking.
- Code completion tasks: partial code with key sections for learners to fill in.
- Sandbox environments: safe spaces to experiment without breaking systems.
- Branching scenarios: each decision leads to a different outcome and feedback.
- Quizzes with immediate feedback: low-stakes checks that clear up misconceptions.

Lab progression:

- Guided: step-by-step commands, automated checks that verify each step, hints when stuck.
- Semi-guided: a template with gaps for learners to fill, outlined success criteria, learners debug.
- Open-ended: requirements only (performance targets, availability, cost constraints); learners choose the architecture, tools and configuration; peer and instructor review gives feedback.

Real-world framing: frame a task as a workplace scenario (a symptom, a time limit, a question about what to check) instead of a bare topic; give chances to apply, troubleshoot and transfer the knowledge to new situations.

Error design: build examples around common misconceptions; use productive failure, where a first approach fails and learners discover the principle; give error-recovery procedures; after a failure, ask what the error means, where to look and how to fix it before giving the correction.

Problem-based cycle (per session, for a group): discuss the problem; identify the questions needed to solve it; brainstorm; analyze and structure findings and gaps; learners set their own learning objectives; independent study; regroup to share findings and synthesize solutions.

Metacognitive prompts: goal setting, planning (resources, strategies, time), monitoring (what is not clear), evaluation (what worked, what did not), adjustment (what to do differently next). Ask what learners already know before they start; ask what was challenging and which strategies helped; model the thinking aloud during a demonstration; offer self-assessment rubrics.

## 6. Assessment and feedback

| | Formative (during learning) | Summative (end of learning) |
|---|---|---|
| Purpose | Monitor progress, find gaps, adjust instruction | Measure achievement, certify competency |
| Character | Low-stakes, frequent, diagnostic | High-stakes, end of module or course |
| Examples | Embedded quizzes, practice labs, reflection prompts, peer feedback | Final projects, exams, capstone labs, portfolio reviews |
| Feedback | Immediate, specific, actionable | Evaluative, may guide future learning |

Feedback characteristics: immediate (soon after the performance); specific (names the exact gap, not vague praise); actionable (gives concrete next steps); growth-oriented (frames errors as learning opportunities); tied to the objective and its success criteria.

Format example of a feedback progression:

```text
Poor:   Wrong. Try again.
Better: Your loop printed nothing because the pattern matched no files.
Best:   Good start: the loop itself is right. It printed nothing because the
        pattern matched no files. Next: (1) print the current folder,
        (2) compare it with the folder in the task, (3) run the loop again.
        This is objective 2, looping over files safely.
```

Spacing plan: revisit core concepts in later modules; make quizzes cumulative; spread hands-on practice over several sessions; add refresher modules weeks after first learning. For retention over about a week, space reviews 1 to 3 days apart; for long-term retention, space reviews at about 10 to 30 percent of the desired retention interval (about 2 to 3 weeks apart for six months).

## 7. Accessibility

WCAG 2.1 principles:

- Perceivable: alt text for images; captions and audio descriptions for video; color contrast of at least 4.5:1 for text; text that resizes without loss of function.
- Operable: everything usable by keyboard (Tab, Enter, arrow keys); visible focus indicators; no time-dependent actions; no seizure-inducing content; skip-navigation links.
- Understandable: plain language with jargon explained; consistent navigation and terminology; help and error recovery; labels and instructions for form inputs.
- Robust: semantic HTML with a proper heading hierarchy; form labels linked to inputs; status messages announced to screen readers.

Accommodations for technical tutorials:

- Video: full transcripts and captions synchronized with the audio.
- Status indicators: not red and green alone; add icons or text labels.
- Code: high-contrast syntax highlighting and adjustable font size.
- Math and formulas: LaTeX or MathML so they render and work with screen readers.
- Diagrams: a text description with each architecture diagram.
- Navigation: clear page structure with a heading hierarchy, breadcrumbs.

Variability options (universal design): several representations (text, video, diagrams, interactive simulations, audio description, glossaries); several means of engagement (links to learner interests, choice of pace, navigation and tools, collaborative and individual options, varied difficulty); several means of expression (written, oral, video, coding or design work; assistive technology; code templates and reference material); sequential or big-picture-first presentation; accelerated, standard and extended paces; both theory and application.

## 8. Build and improvement

Phase activities:

- Planning: define objectives and personas; audience and gap analysis; outline the structure; plan the media assets.
- Design: storyboards for video segments; lesson flow, assessments and feedback; rubrics and grading criteria; labs with objectives, success criteria and recovery procedures.
- Development: write the modules and scripts; produce the media; build quizzes, simulations and labs; assessments and answer keys; instructor or facilitator notes.
- Launch and optimization: deploy to the platform; monitor analytics and feedback; fix critical bugs; plan improvements from the data; keep version control and the update schedule.

Improvement loop: deploy with embedded analytics; collect performance data and feedback; find the bottlenecks where most learners struggle; refine content, examples or scaffolding; redeploy and measure; repeat.

Metrics: completion rate by section; time per module; quiz scores and error patterns; lab success on first attempt, after retry, and abandonment; satisfaction ratings and support-ticket volume; pre and post assessments and retention; usage by assistive technology and keyboard-navigation error rates.

Feedback collection: a clarity question embedded in each section; a post-module understanding rating; an exit question on how learners will apply it; learner interviews; analysis of support tickets for content gaps.

Maintenance: audit content quarterly and update at least yearly; update immediately when the product changes; mark outdated sections with deprecation warnings that point to current versions; re-run every lab regularly against current versions; collect and prioritize reports of inaccuracies; version releases (v1.0, v1.1, v2.0), keep drafts, in-review and published content apart, keep an audit log and archive past versions.
