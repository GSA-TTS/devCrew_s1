# Skills collection

64 Agent Skills, grouped into seven categories. Each skill is a folder with a `SKILL.md` (frontmatter `name` and a
"Load when…" `description`, then Goal, Procedure and checks), a `references/` folder of supporting detail, and in a few
cases a `scripts/` folder of helper code.

44 skills are original to this collection. The 20 marked † were copied from
`agent_skills/perplexity/skills` because the original skills point to them (see
[Cross-skill dependencies](#cross-skill-dependencies)).

## Contents

| Category | Skills |
|---|---|
| [1. Agent architecture](#1-agent-architecture) | 12 |
| [2. LLM application engineering](#2-llm-application-engineering) | 6 |
| [3. Security, risk and governance](#3-security-risk-and-governance) | 9 |
| [4. Research and evidence](#4-research-and-evidence) | 9 |
| [5. Analysis methods](#5-analysis-methods) | 8 |
| [6. Scoring and classification](#6-scoring-and-classification) | 5 |
| [7. Software projects and documentation](#7-software-projects-and-documentation) | 7 |
| [8. Technical writing, education and content](#8-technical-writing-education-and-content) | 8 |

The "Use instead for" column repeats the redirect each skill gives in its own description ("Not for …"), so you can see
which neighbour handles the adjacent job.

---

## 1. Agent architecture

Design and review of the parts of an LLM agent: context, memory, tools, routing, control, state and execution.

| Skill | What it produces | Use instead for |
|---|---|---|
| `agent-context-management-design` | Context-window policy for an agent: sliding windows, tool-result clearing, compaction, subagent isolation, memory blocks or files | Long-term memory → `agent-memory-design`; one bad output → `context-failure-diagnosis` |
| `agent-memory-design` | Long-term memory design: what to keep, representation (episodic, semantic, graph, tiers), write/read paths, consolidation, forgetting, multi-agent stores | Per-request context → `agent-context-management-design`; document RAG → `rag-architecture-design` |
| `agent-tool-use-design` | Tool-use layer for one agent: schemas, descriptions, argument validation, approvals, retries, parallel calls, tool-call evaluation | Hundreds of tools → `tool-retrieval-design`; org-wide policy → `agent-control-plane-design` |
| `tool-retrieval-design` | Narrowing a large or changing tool catalog to the tools shown each turn, how many to show, and how to test it | Individual tool schemas → `agent-tool-use-design`; routing between agents → `agent-routing-design` |
| `agent-routing-design` | Router for a bounded set of models, agents, tools or queues (rules, content, embeddings, LLM classifier, capability matching), with test and rollout | Large tool catalog → `tool-retrieval-design` |
| `agent-control-plane-design` | Production control plane across many agents and teams: registry, discovery, identity, policy, admission checks, audit, kill switches | MCP specifics → `mcp-deployment-design`; one agent's tool schemas → `agent-tool-use-design` |
| `mcp-deployment-design` | Design, review and security of Model Context Protocol servers, clients and gateways: identity, token exchange, policy, tool poisoning, drift | Protocol-neutral control plane → `agent-control-plane-design`; general tool design → `agent-tool-use-design` |
| `agent-state-machine-design` | An agent or LLM workflow as an explicit state machine: states, transitions, guards, retries, crash recovery, and whether a statechart or durable engine fits | Context policies → `agent-context-management-design`; event streaming → `llm-streaming-protocol-design` † |
| `agent-reflection-checkpoint` | Reflection step for an agent: when to reflect, typed schema, grounding in external checks, bounded revise loop, calibration | Choosing a reasoning method → `llm-reasoning-strategy-design`; confidence alone → `llm-confidence-calibration` |
| `code-executing-agent-design` | Agents that run generated code: sandboxing vs code-as-action, isolation, egress, secrets, tool bindings, nested calls, verification | GUI-control agents → `computer-use-agent-design` †; JSON tool contracts → `agent-tool-use-design` |
| `computer-use-agent-design` † | Agents that control a GUI, desktop or browser through screenshots, clicks and keystrokes: targeting, acting, verifying, human hand-over, safety | Agents that act by running code → `code-executing-agent-design` |
| `agent-skill-authoring` | Writing, reviewing and governing an Agent Skill: name and description, one job per skill, bundled references/scripts, trigger tuning, security review, versioning, evaluation | Agent tool schemas and errors → `agent-tool-use-design` |

## 2. LLM application engineering

Building and operating LLM-backed features: retrieval, reasoning, confidence, streaming, caching and failure diagnosis.

| Skill | What it produces | Use instead for |
|---|---|---|
| `rag-architecture-design` | Whether retrieval is needed, which RAG pattern fits (hybrid, GraphRAG, hierarchical, agentic, corrective, Self-RAG, multimodal, modular), build plan and tests | Code-repo search → `codebase-question-retrieval` †; agent memory → `agent-memory-design` |
| `llm-reasoning-strategy-design` | Choice of test-time reasoning method (chain-, tree-, graph-of-thought, step-back, etc.) for a production task, with gates for whether it pays off | Confidence → `llm-confidence-calibration`; self-reflection → `agent-reflection-checkpoint` |
| `llm-confidence-calibration` | Confidence scores, calibration, abstention thresholds and recalibration after model changes | Reasoning method → `llm-reasoning-strategy-design` |
| `context-failure-diagnosis` | A bad output traced to the failing context stage (retrieval, selection, compression, memory, instruction conflict) with a routed repair | Designing context management → `agent-context-management-design`; non-context anomalies → `abductive-hypothesis-ranking` |
| `llm-streaming-protocol-design` † | Streaming output to clients: whether to stream, SSE vs WebSockets vs chunked HTTP, event envelopes, resume, backpressure, partial-output safety | Agent state transitions → `agent-state-machine-design` |
| `prompt-caching-optimization` † | Making provider prompt caching (Anthropic, OpenAI, Gemini) pay off: ordering prompts, tools and history for reuse; whether cache writes pay back | Self-hosted KV-cache serving, or general context design → `agent-context-management-design` |

## 3. Security, risk and governance

Risk assessment, disclosure and injection defences, red-teaming, control effectiveness and policy.

| Skill | What it produces | Use instead for |
|---|---|---|
| `system-risk-assessment` | Risk assessment of one named system (ISO 31000 / NIST style): boundary, register by likelihood and impact, treatment plans | Nonprofit program risks → `nonprofit-risk-register` † |
| `nonprofit-risk-register` † | Risk register for a nonprofit or program: operational, financial, legal, strategic and delivery risks with mitigations | An information system's risks → `system-risk-assessment`; business plan → `nonprofit-business-plan` |
| `information-disclosure-risk` | Disclosure-risk analysis for a system, dataset or publication: what could leak, via which flows, to whom, and which controls and documentation prevent it | General threat-event risk assessment → `system-risk-assessment` |
| `prompt-injection-screening` | Screening record for a fetched document, page, email or dataset before an agent uses it: findings by severity, what to exclude, record and flag. Bundles detection scripts | Planning a red-team exercise → `genai-red-team-plan` † |
| `genai-red-team-plan` † | Red-team plan for a generative AI system: threat model, scope, attack pipeline, findings report | Scorer selection alone → `pyrit-scorer-selection` (not in this collection); one input's injection screen → `prompt-injection-screening` |
| `control-misalignment-forecasting` | Forecast of where current safeguards will stop fitting future threats, with scenarios, ranked misalignments, adaptations and early-warning indicators | Today's control effectiveness → `contextual-control-effectiveness` †; a trend alone → `trend-projection-analysis` |
| `contextual-control-effectiveness` † | How well each control works in different contexts or segments, whether they interact, which to choose where | Forecasting → `control-misalignment-forecasting`; group comparison without controls → `stratified-comparison-analysis` |
| `framework-adoption-assessment` † | Which framework or standard to adopt (NIST CSF, ISO 27001, AI risk frameworks), plus readiness and gaps | Adoption barriers → `adoption-barrier-analysis`; policy comparison → `cross-jurisdiction-policy-comparison` |
| `nonprofit-policy-drafting` † | Nonprofit organizational policy (conflict of interest, whistleblower, safeguarding, data protection, AI use) checked against applicable law and ready for board adoption | Step-by-step procedures → `standard-operating-procedure` |

## 4. Research and evidence

Finding, acquiring, grading, extracting and writing up sources with traceable citations.

| Skill | What it produces | Use instead for |
|---|---|---|
| `arxiv-literature-search` | arXiv search with documented boolean queries and hit counts, screened results and structured notes on kept papers. Bundles IEEE-rendering and source-key scripts | Downloading/converting → `paper-acquisition-conversion` †; standards → `standards-source-discovery` |
| `standards-source-discovery` | Version-pinned, credibility-graded inventory of primary standards and grey literature (IETF RFCs, NIST, OWASP, OpenID, W3C, MCP, vendor research) | arXiv paper search → `arxiv-literature-search`; grading deployment claims → `source-credibility-tiering` |
| `paper-acquisition-conversion` † | Listed papers or standards downloaded and converted into a provenance-tracked Markdown corpus with checksums and an inventory | Searching the literature → `arxiv-literature-search`; finding applicable standards → `standards-source-discovery` |
| `source-credibility-tiering` | Four-tier credibility grading of industry AI deployment claims and their sources | Autonomy/maturity rating → `ai-autonomy-maturity-classification`; finding standards → `standards-source-discovery` |
| `multi-source-research-investigation` | Bounded multi-source report where every claim is cited and checked, with a claim-to-source ledger | Routine reports → `deep-research`; one given claim → `claim-verification` † |
| `claim-verification` † | Facts, figures, dates and quotes in a draft checked, corrected text returned with a ledger of held / corrected / unsupported claims. Bundles `check_quotes.py` | Whole textbook chapters → `textbook-chapter-validation` (not in this collection); new investigations → `multi-source-research-investigation` |
| `knowledge-item-extraction` † | Atomic, typed knowledge items from papers, reports or notes, with claim-level provenance and citation checks | Concept maps → `concept-map-extraction`; deduplication → `knowledge-item-deduplication` (both not in this collection) |
| `state-of-the-art-paper` | Short, fully cited state-of-the-art paper with numbered IEEE citations from an item inventory or evidence table | Extracting the items → `knowledge-item-extraction` †; reviewing others' manuscripts → `research-paper-review` † |
| `research-paper-review` † | Referee review of someone else's manuscript: novelty, methods, statistics, results; major/minor comments, editor notes, recommendation | Preparing your own submission → `acm-journal-manuscript`; grant proposals → `proposal-rigor-review` (both not in this collection) |

## 5. Analysis methods

General-purpose reasoning and comparison methods that work on any domain.

| Skill | What it produces | Use instead for |
|---|---|---|
| `abductive-hypothesis-ranking` | Competing explanations for a surprising observation, ranked, with discriminating tests | Estimating causal effects from data → `causal-inference-analysis` |
| `causal-inference-analysis` | Rigorous test of whether X causes Y from a dataset, experiment or study claim, with confounders and assumptions examined | Brainstorming explanations → `abductive-hypothesis-ranking` |
| `trend-projection-analysis` | Report on how a topic changed over time and where it is heading, with drivers and a projection with stated uncertainty. Bundles `page_dates.py` | Sales/inventory forecasts → `demand-forecasting`; options robust across scenarios → `robust-scenario-decision` † |
| `robust-scenario-decision` † | Decision stress-tested across contrasting futures: robust plan with signposts, triggers and branch playbooks | Upside/base/downside financial models → `scenario-planning`; forecasts → `trend-projection-analysis` |
| `stratified-comparison-analysis` | One set of elements (e.g. risks, tactics) compared across strata of factors such as company size or region | One set vs a baseline → `set-difference-analysis` † |
| `set-difference-analysis` † | What is unique to set A vs baseline B, with each item's mechanism, impact and preconditions | Subgroup comparisons → `stratified-comparison-analysis`; software releases/patches → `lifecycle-patch-comparison` (not in this collection) |
| `cross-jurisdiction-policy-comparison` | Coded comparison matrix of policies/laws across countries, states or agencies, with lessons and adaptation options. Bundles `page_dates.py` | Framework choice → `framework-adoption-assessment` †; unique-to-A analysis → `set-difference-analysis` † |
| `adoption-barrier-analysis` | Why a practice or technology isn't being taken up: typed, scored barriers, root causes, interventions | Choosing a framework to adopt → `framework-adoption-assessment` † |

## 6. Scoring and classification

Rubric-driven ratings of AI use cases, systems and methods.

| Skill | What it produces | Use instead for |
|---|---|---|
| `ai-autonomy-maturity-classification` | Claimed AI/agentic deployments classified on autonomy L0–L5 and maturity M0–M4 with a tag notation (useful for testing "agentic-washing") | Rating source trustworthiness → `source-credibility-tiering` |
| `ai-use-case-complexity-scoring` | AI use cases scored 1–5 on eight complexity dimensions (reasoning, orchestration, memory, perception, tool calling, integration, error handling, resilience) with confidence | General system/task complexity → `system-complexity-rating`; acceptance → `technology-acceptance-scoring` |
| `technology-acceptance-scoring` | Technology Acceptance Model scores (usefulness, ease of use, trust, explainability) for AI use cases from sparse inventory text, with risk flags | Technical complexity → `ai-use-case-complexity-scoring` |
| `system-complexity-rating` | Complexity of a system, process, task or document rated across facets (structure, behaviour, resource hardness, cognitive load) with uncertainty ranges | AI use-case inventory scoring → `ai-use-case-complexity-scoring` |
| `method-maturity-assessment` | Inventory, classification and maturity scoring of a set of methods, ending in a gap analysis and advancement roadmap | External framework choice → `framework-adoption-assessment` †; AI autonomy → `ai-autonomy-maturity-classification` |

## 7. Software projects and documentation

Planning and documenting software work, plus accessibility and code navigation.

| Skill | What it produces | Use instead for |
|---|---|---|
| `software-development-plan` | Ten-section plan for a complex software project: phases, work breakdown with three-point estimates, QA gates, risks, launch | Open-ended goal decomposition → `goal-tree-decomposition` †; one architecture decision → `architecture-decision-records` |
| `goal-tree-decomposition` † | Vague or long-horizon objective turned into a validated goal tree with success criteria, guardrails, dependencies and hand-off contracts | Reusable-method task networks → `htn-task-decomposition`; schedules → `constraint-model-scheduling` (both not in this collection) |
| `architecture-decision-records` | ADRs drafted from requirements or design discussion, or an ADR draft reviewed for one-sided trade-offs and missing links | Whole documentation system → `project-documentation-system` |
| `project-documentation-system` | Docs set-up or reorganization for a software repository: hierarchy, templates, maintenance routine | One ADR → `architecture-decision-records`; business SOP → `standard-operating-procedure` |
| `standard-operating-procedure` | SOP written, reviewed or updated for a process: warrant check, eight-section skeleton, roles, review workflow | Organizational policies → `nonprofit-policy-drafting` †; software docs → `project-documentation-system` |
| `codebase-question-retrieval` † | Where something is implemented, what calls a function, how code works, answered with files, symbols and line ranges | Designing document retrieval systems → `rag-architecture-design` |
| `wcag-accessibility-audit` | WCAG 2.1 audit (A/AA/AAA) of a page, site or HTML/CSS: violations with fixes, manual tests, conformance report (ACR/VPAT) | Usability heuristics and SEO reviews (out of scope) |

## 8. Technical writing, education and content

Condensing, teaching, assessing and visualizing technical material.

| Skill | What it produces | Use instead for |
|---|---|---|
| `technical-content-condensing` | Technical text cut to about 80% of its length without losing concepts or steps, with before/after evidence | Beginner rewrites → `textbook-chapter-revision` †; short summaries → `textbook-chapter-summary` † |
| `textbook-chapter-revision` † | AI-drafted technical chapter revised for beginners: list-like draft into scaffolded, connected prose | Fact-checking → `textbook-chapter-validation`; shortening → `technical-content-condensing`; one concept → `audience-tailored-explanation` (validation and explanation not in this collection) |
| `textbook-chapter-summary` † | 150–300 word end-of-chapter summary or key-takeaways section, or a draft summary checked and fixed | Shortening a whole chapter → `technical-content-condensing`; chapter openings → `textbook-chapter-front-matter` (not in this collection) |
| `technical-tutorial-design` | Tutorial / online lesson / hands-on lab plan: learners, objectives, chunking, media, practice, assessment, accessibility | Textbook-chapter assessment items → `formative-assessment-design` † |
| `formative-assessment-design` † | Knowledge checks, vocabulary and comprehension exercises, and feedback wording for a technical or certification chapter | Case studies/scenarios → `scenario-based-learning-design` (not in this collection); standalone question bank → `multiple-choice-question-writing` † |
| `multiple-choice-question-writing` † | Easy, medium and hard multiple-choice items with misconception-based distractors, answer key and validation plan | Certification exam bank planning → `certification-exam-item-bank` (not in this collection); formative plan → `formative-assessment-design` † |
| `google-forms-creation` | Build plan for a Google Form, application form or self-grading quiz: editor steps, Forms API or Apps Script, question types, answer keys, API limits | Writing the quiz questions → `multiple-choice-question-writing` † |
| `infographic-generation` | Infographic images from a text description or slide deck with notes: cluster plan, image prompts, generated images | Data charts → `chart`; slide files → `slides` |

---

## Cross-skill dependencies

The dependencies in this collection are hand-off pointers: every skill's description ends in "Not for … (other-skill)", and its
"When not to use" section repeats the redirect. No skill calls another skill in its procedure. Each skill still
points to the skill that handles the adjacent job, so those targets need to exist.

### Skills copied in from `agent_skills/perplexity/skills` (†)

All 20 were referenced by the original 44 and were missing. They are byte-for-byte copies (`.DS_Store` excluded).

| Copied skill | Referenced by |
|---|---|
| `claim-verification` | `multi-source-research-investigation` |
| `codebase-question-retrieval` | `rag-architecture-design` |
| `computer-use-agent-design` | `code-executing-agent-design` |
| `contextual-control-effectiveness` | `control-misalignment-forecasting`, `stratified-comparison-analysis` |
| `formative-assessment-design` | `technical-tutorial-design` |
| `framework-adoption-assessment` | `adoption-barrier-analysis`, `cross-jurisdiction-policy-comparison`, `method-maturity-assessment` |
| `genai-red-team-plan` | `prompt-injection-screening` |
| `goal-tree-decomposition` | `software-development-plan` |
| `knowledge-item-extraction` | `state-of-the-art-paper` |
| `llm-streaming-protocol-design` | `agent-state-machine-design` |
| `multiple-choice-question-writing` | `google-forms-creation` |
| `nonprofit-policy-drafting` | `standard-operating-procedure` |
| `nonprofit-risk-register` | `system-risk-assessment` |
| `paper-acquisition-conversion` | `arxiv-literature-search`, `standards-source-discovery` |
| `prompt-caching-optimization` | `agent-context-management-design` |
| `research-paper-review` | `state-of-the-art-paper` |
| `robust-scenario-decision` | `trend-projection-analysis` |
| `set-difference-analysis` | `cross-jurisdiction-policy-comparison`, `stratified-comparison-analysis` |
| `textbook-chapter-revision` | `technical-content-condensing` |
| `textbook-chapter-summary` | `technical-content-condensing` |

### References that remain unresolved

Only the skills the original 44 point to were copied. The copied skills have their own pointers, so some references still
resolve to nothing in this folder.

- **In the Perplexity source but not copied** (reached only through the † skills): `acm-journal-manuscript`,
  `audience-tailored-explanation`, `certification-exam-item-bank`, `concept-map-extraction`, `constraint-model-scheduling`,
  `htn-task-decomposition`, `knowledge-item-deduplication`, `lifecycle-patch-comparison`, `nonprofit-business-plan`,
  `proposal-rigor-review`, `pyrit-scorer-selection`, `scenario-based-learning-design`, `textbook-chapter-front-matter`,
  `textbook-chapter-validation`. Following their own pointers adds 11 more (25 in total); all of them are in the source.
- **In neither collection** (probably general-purpose tools or skills outside the Perplexity set): `deep-research`,
  `research-report` (from `multi-source-research-investigation`), `chart` and `slides` (from `infographic-generation`),
  `demand-forecasting` (from `trend-projection-analysis`), `scenario-planning` (from `robust-scenario-decision`).

### Typical chains (inferred from the hand-off pointers)

- **Literature to paper:** `standards-source-discovery` / `arxiv-literature-search` → `paper-acquisition-conversion` →
  `knowledge-item-extraction` → `state-of-the-art-paper` (with `source-credibility-tiering` for grading and
  `claim-verification` for checking).
- **Agent stack:** `agent-tool-use-design` → `tool-retrieval-design` / `agent-routing-design` → `agent-control-plane-design`
  → `mcp-deployment-design`; `agent-context-management-design`, `agent-memory-design` and `rag-architecture-design` cover context and knowledge.
- **Risk and controls:** `system-risk-assessment` → `information-disclosure-risk`; `contextual-control-effectiveness` →
  `control-misalignment-forecasting` → `trend-projection-analysis`.
- **Software project:** `software-development-plan` ↔ `architecture-decision-records` ↔ `project-documentation-system` ↔
  `standard-operating-procedure`.

## Bundled scripts

Scripts are Python and self-contained inside each skill folder. The multi-part scripts (`*_part1.py`, `*_part2.py`) are
imported by their entry point and must stay beside it. Several scripts are duplicated across skills, so a fix in one copy
should be applied to the others.

| Script | Purpose | Present in |
|---|---|---|
| `render_ieee.py` (+ `_part1`, `_part2`) | Render IEEE reference entries for a Markdown document from a CSV of sources | `arxiv-literature-search`, `state-of-the-art-paper`, `research-paper-review` † |
| `page_dates.py` (+ `_part1`) | Date basis of a web page or document from the dates it states about itself | `cross-jurisdiction-policy-comparison`, `source-credibility-tiering`, `standards-source-discovery`, `trend-projection-analysis` |
| `source_keys.py` | Source keys (`primary_id`), canonical URLs and lineage groups for set, join and dedup of sources | `arxiv-literature-search` |
| `screen_injection.py` (+ `_part1`, `_part2`) | Screen documents, Docling JSON and HTML for embedded instructions aimed at an AI | `prompt-injection-screening` |
| `find_secrets.py` | Find secrets in text by token shape before any of it is quoted | `prompt-injection-screening` |
| `check_quotes.py` | Check that quotes are verbatim in a source and that claims rest on them | `claim-verification` † |
