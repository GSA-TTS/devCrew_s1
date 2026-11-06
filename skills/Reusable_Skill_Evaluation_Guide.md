# Guide to Evaluating Agents’ Reusable Skills {#guide-to-evaluating-agents’-reusable-skills}

## How to read this guide {#how-to-read-this-guide}

Every claim in this guide carries one of four labels so readers can judge how much weight to put on it:

| Label | Meaning |
| :---- | :---- |
| **\[Fact\]** | Documented in a cited public source. The citation is next to the claim. |
| **\[Practice\]** | Common industry or engineering practice. Widely used, but not a formal requirement and not always backed by controlled studies. |
| **\[Analysis\]** | The author's synthesis of the sources and the example collection. Reasonable people may disagree. |
| **\[Rec\]** | A recommendation based on judgment. Adjust it to your context, risk tolerance and policies. |

The guide is general-purpose. The public GSA-TTS devCrew\_s1 skills collection was used only as an example source for patterns; nothing in the guide depends on it.

Note on scope and access: only public materials were read. No code from any repository was executed, no credentials were used and no private systems were accessed. Some standards (for example ISO/IEC 25010 and ISO/IEC 42001\) are paywalled; only their public abstracts were used.

## 

## Contents {#contents}

[Guide to Evaluating Agents’ Reusable Skills](#guide-to-evaluating-agents’-reusable-skills)

[How to read this guide](#how-to-read-this-guide)

[Contents](#contents)

[1\. Executive summary](#1.-executive-summary)

[2\. Definition and taxonomy](#2.-definition-and-taxonomy)

[3\. What the evidence says, by research question](#3.-what-the-evidence-says,-by-research-question)

[4\. Evaluation framework](#4.-evaluation-framework)

[5\. Evaluation rubric (0–4 scale)](#5.-evaluation-rubric-\(0–4-scale\))

[6\. Comparison table of evaluation dimensions](#6.-comparison-table-of-evaluation-dimensions)

[7\. Testing and evaluation plan](#7.-testing-and-evaluation-plan)

[8\. Risk assessment model](#8.-risk-assessment-model)

[9\. Adoption recommendation process](#9.-adoption-recommendation-process)

[10\. Reviewer workflow](#10.-reviewer-workflow)

[11\. Lightweight vs. rigorous review tracks](#11.-lightweight-vs.-rigorous-review-tracks)

[12\. Templates](#12.-templates)

[13\. Evidence gaps, conflicts and limitations](#13.-evidence-gaps,-conflicts-and-limitations)

[Next steps](#next-steps)

[14\. Source list](#14.-source-list)

## 

## 1\. Executive summary {#1.-executive-summary}

Reusable skills — packaged prompts, code, tool calls, workflows and documentation — let a team solve a problem once and reuse the solution. That reuse is why evaluation matters: a flaw in one skill is copied into every task and agent that invokes it. A January 2026 study of 31,132 public agent skills found that 26.1% contained at least one vulnerability, and that skills bundling executable scripts were about twice as likely to be vulnerable as instruction-only skills ([Liu et al., arXiv:2601.10338](https://arxiv.org/abs/2601.10338)). A separate study confirmed 157 deliberately malicious skills among 98,380 examined ([arXiv:2602.06547](https://arxiv.org/abs/2602.06547)). On the benefit side, a paired benchmark found curated skills raised agent pass rates from 33.9% to 50.5%, with gains varying widely by configuration ([SkillsBench, arXiv:2602.12670](https://arxiv.org/abs/2602.12670)). Skills can help, but not automatically, and the risk applies to AI-enabled and conventional automation alike.

The recommended approach has five parts:

1. **Classify first.** Identify the skill type and assign a risk tier (Low, Moderate, High, Prohibited without authorization). The tier sets review depth.  
2. **Evaluate twelve dimensions** — purpose fit, effectiveness, reliability, safety and misuse, security, privacy, human oversight, transparency and documentation, maintainability and dependencies, ownership and lifecycle, accessibility and usability, and operational fitness — using a 0–4 rubric with explicit blocking rules.  
3. **Demand evidence, not assertions.** Require a labeled test set, a no-skill or prior-version baseline, adversarial tests and named owners before production use.  
4. **Choose a clear outcome:** adopt, adopt with conditions, pilot only, revise and resubmit, reject, or retire.  
5. **Keep evaluating after release.** Monitor outcomes, drift and incidents; re-review on a schedule and after material changes.

Small teams can use a one-to-two-reviewer track for low-risk skills; high-impact skills need independent review, specialist sign-off (security, privacy, legal, records, accessibility) and documented risk acceptance, consistent with federal practice for high-impact AI ([OMB M-25-21](https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf)).

---

## 2\. Definition and taxonomy {#2.-definition-and-taxonomy}

### 2.1 Definition

**\[Rec\] Working definition.** A *skill* is a packaged, reusable capability that a human, software system, AI agent, workflow engine or automation framework can invoke to perform a specific, bounded task. A skill may include instructions or prompts, code or scripts, configuration, tool or API bindings, documentation, examples, tests, metadata, dependencies and operational assumptions. What makes it a skill rather than a one-off script or prompt is that it is (a) packaged for reuse, (b) invoked by others who did not write it, and (c) expected to behave predictably across invocations.

**\[Fact\]** One concrete, open format exists for AI-agent skills: the Agent Skills specification defines a skill as a directory containing at minimum a `SKILL.md` file with YAML front matter (`name`, `description`; optional `license`, `compatibility`, `metadata`, experimental `allowed-tools`) followed by Markdown instructions, with optional `scripts/`, `references/` and `assets/` folders ([Agent Skills specification](https://agentskills.io/specification)). In that format, only the name and description are loaded up front; the body and bundled files load on demand (vendor documentation: [Anthropic engineering post](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills)).

**\[Analysis\]** The same evaluation questions apply to skills that are not in that format — a Zapier-style workflow, a Python package wrapped as an API, a retrieval pipeline, a GitHub Action, or a prompt template in a shared library. The format changes *what artifacts you inspect*, not *what you need to know*.

### 2.2 Example collection observed

**\[Fact\]** The public GSA-TTS devCrew\_s1 `skills/` folder contains 64 Agent Skills grouped into eight categories (agent architecture; LLM application engineering; security, risk and governance; research and evidence; analysis methods; scoring and classification; software projects and documentation; technical writing, education and content). Each skill is a folder with a `SKILL.md` (front matter `name` and a "Load when…" description, then Goal, Procedure and checks), a `references/` folder and, in a few cases, a `scripts/` folder of Python helpers ([devCrew\_s1 skills README](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/README.md)).

Patterns in that collection that informed this guide **\[Analysis, based on the README and the `agent-skill-authoring` skill files\]**:

- **Explicit negative boundaries.** Descriptions state what the skill is *not* for and which neighbor to use instead. This is a good, checkable practice for trigger precision.  
- **Declared cross-skill dependencies.** The README lists skills that other skills point to, including some that are "not in this collection" or "probably general-purpose tools or skills maintained elsewhere" ([README](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/README.md)). Evaluators need to check whether hand-offs resolve in the deployment environment.  
- **Duplicated scripts.** The README notes that "several scripts are duplicated across skills, so a fix in one copy should be applied to the others" ([README](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/README.md)). That is an honest disclosure and also a maintainability risk evaluators should look for elsewhere.  
- **Built-in evaluation criteria.** The collection's `agent-skill-authoring` skill specifies trigger precision/recall, comparison against a no-skill baseline and the previous production version, thresholds declared before running, and a zero release threshold for critical security outcomes ([agent-skill-authoring evaluation reference](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/references/evaluation-and-release.md)). Several of those ideas are adopted below.

### 2.3 Taxonomy of skill types

**\[Rec\]** Classify each skill on two axes: **what it is** (type, below) and **what it can do** (capability level, Section 8). A skill can belong to more than one type; evaluate against every type that applies.

| Type | Typical contents | Evaluation emphasis (what to weigh most) |
| :---- | :---- | :---- |
| **Prompt / instruction skill** | Instructions, examples, templates; no code | Trigger accuracy, output quality vs. baseline, model-version sensitivity, hidden instruction-shaped text, over-confidence in outputs |
| **AI-agent skill (procedural)** | Instructions plus references; may orchestrate other skills | Scope clarity ("one job"), hand-off correctness, context cost, behavior across models, goal hijack resistance |
| **Tool-using assistant skill** | Instructions that call tools (file, shell, browser, email, MCP servers) | Least privilege, consent and approval gates, excessive agency, tool-description poisoning, audit logging |
| **Workflow automation skill** | Triggers, steps, conditions, connectors (may have no AI at all) | Idempotency, error handling, retries, side effects, irreversibility, credentials handling, failure notification |
| **API-backed skill** | Wrapper around an internal or external API | Contract tests, auth model, rate limits, data residency, vendor terms, outage behavior |
| **Data-processing skill** | Parsing, transformation, ETL, cleaning, scoring | Correctness on edge cases, schema validation, data quality, privacy (PII), reproducibility, lineage |
| **Search / retrieval skill** | Query plan, indexes, RAG pipeline, source hierarchy | Retrieval precision/recall, groundedness and citation accuracy, source credibility, injection via retrieved content, freshness |
| **Code-generation / code-analysis skill** | Instructions plus linters, test runners, generators | Compile/test pass rates, security of generated code, sandboxing, license contamination, false-positive/negative rates for analysis |
| **Content drafting / summarization / classification skill** | Templates, style rules, label sets | Factual accuracy, omission rate, bias across groups, label agreement with humans, tone, plain-language and accessibility, records implications |
| **Operational support skill** | Runbooks, triage, incident or ticket handling | Correct escalation, safe defaults under uncertainty, latency, on-call usability, auditability, rollback |

**\[Analysis\] How emphasis shifts.** Instruction-only skills shift risk toward *judgment* (is the output right? does it trigger at the right time?). Skills with scripts or tool access shift risk toward *authority* (what can it touch, change or send?). The empirical finding that script-bundling skills are about 2.12 times more likely to contain vulnerabilities ([arXiv:2601.10338](https://arxiv.org/abs/2601.10338)) supports spending more security review time on executable and tool-using skills — but instruction-only skills are not safe by default: a separate study found agent manipulation through "adversarial instructions embedded in documentation" was one of two dominant malicious strategies ([arXiv:2602.06547](https://arxiv.org/abs/2602.06547)). Non-AI workflow automation can also cause serious harm through bad triggers, missing idempotency or unchecked side effects.

---

## 3\. What the evidence says, by research question {#3.-what-the-evidence-says,-by-research-question}

Short answers here; details are in Sections 4–12.

### Q1. What criteria should be used before adoption or deployment?

- **\[Fact\]** For federal high-impact AI, OMB requires pre-deployment testing, an AI impact assessment (purpose and benefit, data quality, impacts on privacy/civil rights/civil liberties, reassessment schedule, costs, independent review, signed risk acceptance), ongoing monitoring, operator training and human oversight ([OMB M-25-21, Section 4(b)](https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf)). M-25-21 also says risk management "should be proportionate to the anticipated risk from its intended use." The OMB memoranda page as of this research date lists M-25-21 and M-25-22 without indicating they have been superseded, plus M-26-04 (December 11, 2025\) on unbiased AI principles ([OMB memoranda](https://www.whitehouse.gov/omb/information-resources/guidance/memoranda/)).  
- **\[Fact\]** The NIST AI RMF organizes AI risk work into Govern, Map, Measure and Manage functions, and the Generative AI Profile (NIST AI 600-1) adds GenAI-specific risks and actions ([NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework); [NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1)). NIST's page states that AI RMF 1.0 is being revised.  
- **\[Fact\]** GAO's AI accountability framework uses four principles: governance, data, performance and monitoring ([GAO-21-519SP](https://www.gao.gov/products/gao-21-519sp)).  
- **\[Rec\]** Pre-adoption criteria in this guide: purpose fit, effectiveness against a baseline, reliability, safety/misuse, security, privacy, human oversight, documentation, maintainability, ownership, accessibility/usability and operational readiness (Section 4).

### Q2. What criteria should be used after it is in use?

- **\[Fact\]** OMB requires ongoing monitoring designed to detect "unforeseen circumstances, post-deployment system changes, or changes in the context of use or associated data," with periodic human review where feasible ([M-25-21](https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf)). For high-impact AI not performing adequately, agencies "must have a plan to discontinue its use."  
- **\[Practice\]** Site reliability practice monitors the "four golden signals": latency, traffic, errors and saturation ([Google SRE book, ch. 6](https://sre.google/sre-book/monitoring-distributed-systems/)).  
- **\[Rec\]** Post-deployment criteria: task success rate in real use, human override/correction rate, incident and near-miss count, trigger accuracy (for agent skills), cost and latency, drift after model or dependency changes, user satisfaction, and whether the owner is still active (Section 12.5 checklist).

### Q3. What evidence shows a skill is effective?

- **\[Fact\]** Paired comparison against a no-skill condition is the emerging research norm: SkillsBench runs matched no-skill and curated-skill conditions with deterministic verifiers and reports average pass-rate gains of \+16.6 percentage points, but configuration-level gains ranged from \+4.1 to \+25.7 points; focused skills (at most three modules) outperformed larger bundles ([arXiv:2602.12670](https://arxiv.org/abs/2602.12670)).  
- **\[Fact, vendor documentation\]** Anthropic's authoring guidance says to "create evaluations BEFORE writing extensive documentation," establish a no-skill baseline, and "test with all models you plan to use" ([Claude skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).  
- **\[Analysis\]** Effectiveness evidence is credible when it includes: a defined task and success criterion; a representative labeled test set; a baseline; deterministic checks where possible; and human or model judging only with a rubric and measured agreement. A fluent answer, a zero exit code or a model's self-report is not proof of success — a point made explicitly in the devCrew authoring criteria ([evaluation-and-release.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/references/evaluation-and-release.md)).

### Q4. How should evaluators assess safety, security, privacy and misuse?

- **\[Fact\]** OWASP's LLM Top 10 (2025) names prompt injection, sensitive information disclosure, supply chain, data and model poisoning, improper output handling, excessive agency, system prompt leakage, vector/embedding weaknesses, misinformation and unbounded consumption ([OWASP LLM Top 10 2025](https://genai.owasp.org/llm-top-10/)). The OWASP Top 10 for Agentic Applications (2026) adds agent goal hijack, tool misuse, identity and privilege abuse, agentic supply chain, unexpected code execution, memory and context poisoning, insecure inter-agent communication, cascading failures and human-agent trust exploitation, among others ([OWASP Agentic Top 10 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/); risk list as summarized by [Modulos](https://docs.modulos.ai/frameworks/owasp-top-10-agentic/index)).  
- **\[Fact\]** The Model Context Protocol specification states that tools "represent arbitrary code execution and must be treated with appropriate caution," that tool descriptions should be considered untrusted unless from a trusted server, and that hosts must obtain explicit user consent before invoking any tool ([MCP specification](https://modelcontextprotocol.io/specification/2026-07-28)).  
- **\[Fact, vendor documentation\]** Anthropic warns: "Use Skills only from trusted sources," audit all bundled files for unexpected network calls or file access, and "treat like installing software"; it also notes that "even trustworthy Skills can be compromised if their external dependencies change over time" ([Claude Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)).  
- **\[Fact\]** Ecosystem data: Snyk's February 2026 audit of 3,984 skills found 13.4% with at least one critical issue and 36.82% with at least one security flaw (vendor research: [Snyk ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)). An academic study found that over half of confirmed malicious skills came from a single actor using templated brand impersonation ([arXiv:2602.06547](https://arxiv.org/abs/2602.06547)).  
- **\[Fact\]** Automated scanners disagree substantially: across 67,453 registry skills, three scanners' pairwise Jaccard agreement was at most 0.104 and Cohen's κ was 0.045–0.082; 24.3% of skills the registry judged malicious had no positive signal from any scanner ([arXiv:2606.01494](https://arxiv.org/html/2606.01494v1)).  
- **\[Rec\]** Combine (1) human code-and-instruction review, (2) more than one automated scanner, (3) provenance checks, (4) adversarial testing and (5) runtime least privilege. No single scanner result, star count, signature or known author should be treated as proof of safety.

### Q5. How should evaluators assess maintainability, dependencies, versioning and ownership?

- **\[Fact\]** NIST's SSDF (SP 800-218) and its GenAI community profile (SP 800-218A) describe secure development practices, including managing third-party components and provenance ([SSDF](https://csrc.nist.gov/projects/ssdf); [SP 800-218A](https://www.nist.gov/publications/secure-software-development-practices-generative-ai-and-dual-use-foundation-models-ssdf)).  
- **\[Fact\]** SLSA defines build-provenance levels for supply-chain integrity; v1.2 is current ([SLSA](https://slsa.dev/spec/v1.1/levels)). OpenSSF Scorecard runs automated checks such as pinned dependencies, dependency update tooling, SAST and maintenance activity, scoring each 0–10 ([OpenSSF Scorecard](https://github.com/ossf/scorecard)).  
- **\[Fact\]** Semantic Versioning defines MAJOR.MINOR.PATCH increments and requires a declared public API ([SemVer 2.0.0](https://semver.org/)).  
- **\[Analysis\]** For AI skills, the "public API" includes the description/trigger text, input and output contract, required tools and the models it was tested with. A model upgrade can change behavior without any change to the skill file, so the tested-with model list is part of the version.

### Q6. What minimum documentation should every skill include?

See Section 4, Dimension 8, and the template in Section 12.1. **\[Rec\]** Minimum: purpose and non-goals; owner and backup; version and changelog; inputs/outputs and success criteria; required tools, permissions, data and environment; dependencies with versions; known limitations and failure modes; test evidence summary; risk tier; human-oversight points; and how to report problems.

### Q7. What tests or artifacts are expected before production?

See Section 7\. **\[Rec\]** At minimum for Moderate risk and above: a labeled test set covering happy path, edge cases and negative (should-not-trigger) cases; baseline comparison; adversarial/misuse tests; a regression suite; security scan results; a human review record; and a rollback plan.

### Q8. What red flags should block, pause or return a skill?

See Section 4 (per dimension) and the blocking rules in Section 5.3.

### Q9 and Q10. Lightweight vs. rigorous review?

See Section 11\.

---

## 4\. Evaluation framework {#4.-evaluation-framework}

**\[Rec\]** Twelve dimensions. Not every dimension carries equal weight for every skill; the risk tier (Section 8\) and type (Section 2.3) tell you where to focus. Each dimension below lists what to evaluate, why it matters, evidence to request, example questions, red flags and rating guidance (scores refer to the 0–4 rubric in Section 5).

### D1. Purpose and fit

- **What to evaluate:** Is there a clear, bounded job? Is a skill the right mechanism (vs. a plain script, a policy rule, a retrieval system, or nothing)? Does it duplicate an existing skill?  
- **Why it matters:** Vague or overlapping skills trigger at the wrong time and are hard to test. **\[Analysis\]** The devCrew authoring criteria recommend "the smallest container that matches the missing capability" and "No skill" when there is no trustworthy owner, test oracle or rollback path ([agent-skill-authoring SKILL.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/SKILL.md)).  
- **Evidence to request:** Problem statement; intended users; one-sentence completion criterion; list of near-neighbor skills and how this differs; expected benefit.  
- **Example questions:** What happens today without this skill? What would "done correctly" look like? What is explicitly out of scope?  
- **Red flags:** "Use for all coding tasks"-style claims; no stated non-goals; two skills that must always load together; a skill that only wraps an unrestricted shell or API behind friendly prose.  
- **Rating guidance:** 4 \= one clear job, non-goals stated, neighbors distinguished, benefit quantified. 2 \= purpose clear but scope fuzzy or overlap unresolved. 0 \= no articulable job.

### D2. Effectiveness (does it help?)

- **What to evaluate:** Measured improvement over a baseline (no skill, manual process, or prior version) on representative tasks.  
- **Why it matters:** **\[Fact\]** Skill benefits vary widely by model and harness (+4.1 to \+25.7 points in SkillsBench) ([arXiv:2602.12670](https://arxiv.org/abs/2602.12670)), so a demo on one setup does not generalize.  
- **Evidence to request:** Test set description and size; baseline results; skill results; the model(s) and versions tested; scoring method; examples of failures.  
- **Example questions:** Was the test set written before tuning? Who labeled correct answers? Is improvement larger than run-to-run variation?  
- **Red flags:** Only cherry-picked demos; no baseline; evaluation set identical to the examples inside the skill (answer-key leakage); success judged only by the same model that produced the output.  
- **Rating guidance:** 4 \= held-out test set, baseline, repeat runs, improvement clearly exceeds noise on all target models. 2 \= some testing, no baseline or one model only. 0 \= no evidence.

### D3. Reliability and robustness

- **What to evaluate:** Consistency across repeated runs, input variations, malformed inputs, missing data, timeouts and dependency failures. For agent skills, trigger precision and recall.  
- **Why it matters:** LLM outputs are non-deterministic; automation runs unattended. **\[Fact\]** The devCrew criteria define trigger precision (TP/(TP+FP)), recall (TP/(TP+FN)) and over-trigger rate as separate metrics, noting over-trigger rate is "not one minus precision, because the denominators differ" ([evaluation-and-release.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/references/evaluation-and-release.md)).  
- **Evidence to request:** Repeat-run variance; edge-case and malformed-input results; failure-mode handling description; trigger test results.  
- **Example questions:** What happens when an input is empty, huge, in another language, or malformed? Does it fail loudly or silently?  
- **Red flags:** Swallowed exceptions; scripts that return success on failure; retries without limits; behavior that changes run to run on identical input with no tolerance stated.  
- **Rating guidance:** 4 \= documented failure classes with tested recovery, variance measured and acceptable. 2 \= happy path reliable, edge cases untested. 0 \= fails or behaves unpredictably on ordinary inputs.

### D4. Safety and misuse

- **What to evaluate:** Potential for harmful outputs, misuse by users, harmful autonomous actions, over-reliance, and goal hijack.  
- **Why it matters:** **\[Fact\]** OWASP lists excessive agency, misinformation and human-agent trust exploitation as top risks ([OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/); [OWASP Agentic Top 10](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)). NIST AI 600-1 catalogs GenAI risks such as confabulation and information integrity ([NIST AI 600-1](https://doi.org/10.6028/NIST.AI.600-1)).  
- **Evidence to request:** Misuse scenarios considered; red-team or adversarial test results; content safety policy; refusal/escalation behavior.  
- **Example questions:** How could a well-meaning user get a harmful result? How could a malicious user or document redirect it? What does it do when unsure?  
- **Red flags:** No misuse analysis; outputs presented as authoritative with no uncertainty signaling; ability to generate official communications without review.  
- **Rating guidance:** 4 \= misuse cases enumerated and tested, safe defaults under uncertainty, residual risks accepted by an accountable person. 2 \= some consideration, untested. 0 \= known unmitigated harm path.

### D5. Security

- **What to evaluate:** Permissions requested vs. needed; code and instruction content; prompt-injection exposure; secrets handling; network egress; dependency integrity; sandboxing; logging.  
- **Why it matters:** **\[Fact\]** 26.1% of 31,132 public skills studied had at least one vulnerability, with data exfiltration (13.3%) and privilege escalation (11.8%) most common ([arXiv:2601.10338](https://arxiv.org/abs/2601.10338)). A 2026 study reported 104 taint-style vulnerabilities across 11 open-source agents where untrusted skill content reached security-sensitive operations ([TrustProbe, arXiv:2609.39065](https://arxiv.org/html/2609.39065)).  
- **Evidence to request:** Full file inventory; permission/tool manifest; results from at least two scanners; dependency list with pinned versions and provenance; threat model for High risk.  
- **Example questions:** What is the worst thing this skill could do with the permissions it requests? Does any script download and run code at runtime? Can paths escape the workspace? Can retrieved content become instructions?  
- **Red flags:** Obfuscated or encoded content; hidden network calls; credentials in files; unpinned dependencies; runtime `curl | sh`\-style installs; instructions to ignore warnings, disclose secrets, change configuration or self-approve (all listed as security failures in the devCrew criteria S1–S7, [review-criteria.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/references/review-criteria.md)); pre-approved shell, browser or unrestricted HTTP for an untrusted skill.  
- **Rating guidance:** 4 \= least privilege, no findings above low severity across multiple scanners and manual review, sandboxed, pinned, provenance known. 2 \= minor findings with mitigation plan. 0 \= any critical finding, unexplained capability, or malicious indicator. **A score of 0 here always blocks.**

### D6. Privacy and data protection

- **What to evaluate:** What personal or sensitive data the skill reads, stores, transmits or generates; minimization; retention; third-party transmission; legal basis.  
- **Why it matters:** **\[Fact\]** Federal agencies conduct privacy impact assessments when IT collects new information in identifiable form, under Section 208 of the E-Government Act and OMB M-03-22 ([OMB M-03-22](https://obamawhitehouse.archives.gov/omb/memoranda_m03-22/)). OWASP lists sensitive information disclosure as LLM02 ([OWASP](https://genai.owasp.org/llm-top-10/)).  
- **Evidence to request:** Data flow description; data categories; where data goes (including model providers); retention; whether a PIA or privacy threshold analysis is needed.  
- **Example questions:** Does the skill send content to an external model or API? Could it surface one user's data to another? Are logs scrubbed?  
- **Red flags:** PII sent to unvetted third parties; logs containing raw sensitive inputs; no data inventory; memory features that persist user data without disclosure.  
- **Rating guidance:** 4 \= data flows mapped, minimized, privacy review complete where required. 2 \= flows known but not reviewed. 0 \= undisclosed transmission of sensitive data. **Expert review:** privacy office.

### D7. Human oversight and control

- **What to evaluate:** Where humans approve, review or can stop the skill; whether reviewers have enough information to judge; kill switch; escalation.  
- **Why it matters:** **\[Fact\]** M-25-21 requires human oversight, intervention and accountability for high-impact AI, plus training for operators ([M-25-21](https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf)). MCP requires explicit user consent before tool invocation ([MCP specification](https://modelcontextprotocol.io/specification/2026-07-28)).  
- **Evidence to request:** Approval points; what the human sees before approving; stop/rollback mechanism; escalation rules.  
- **Example questions:** Can a human see and stop an action before it is irreversible? Is "approve" a rubber stamp because the reviewer lacks context?  
- **Red flags:** Irreversible external actions without approval; approval prompts that hide what will happen; no way to pause the skill globally.  
- **Rating guidance:** 4 \= oversight proportionate to risk, tested, with a working kill switch. 0 \= autonomous irreversible actions with no oversight.

### D8. Transparency and documentation

- **What to evaluate:** Whether a reviewer who did not write the skill can understand what it does, when to use it, and its limits.  
- **Why it matters:** Reuse depends on others understanding the skill. **\[Fact\]** The Agent Skills spec requires a description that says "what the skill does and when to use it" ([spec](https://agentskills.io/specification)).  
- **Evidence to request:** The documentation set (Section 12.1 minimum fields).  
- **Example questions:** Could a new team member decide from the docs alone whether to use it? Are limitations stated plainly?  
- **Red flags:** Missing owner, version or limitations; documentation that contradicts the code; marketing language instead of behavior.  
- **Rating guidance:** 4 \= all minimum fields present, accurate, plain language. 2 \= core fields present, limitations thin. 0 \= undocumented.

### D9. Maintainability and dependencies

- **What to evaluate:** Code and instruction clarity; size; modularity; dependency count, pinning and health; duplication; test coverage; compatibility declarations.  
- **Why it matters:** **\[Fact\]** OpenSSF Scorecard treats pinned dependencies, dependency update tooling and maintenance activity as security-relevant ([Scorecard](https://github.com/ossf/scorecard)). Vendor guidance recommends keeping a skill's main file under 500 lines and moving detail to directly linked files ([Claude best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).  
- **Evidence to request:** Dependency manifest; SBOM for code-bearing skills; Scorecard or equivalent results for upstream projects; list of duplicated components.  
- **Example questions:** If a dependency breaks or a model is retired, what changes? Are copies of the same script kept in sync?  
- **Red flags:** Unmaintained upstream; dependency on a skill or service not available in the target environment; duplicated code with no sync process; "voodoo constants."  
- **Rating guidance:** 4 \= pinned, healthy dependencies, no unmanaged duplication, compatibility declared. 0 \= unknown or abandoned dependencies in a critical path.

### D10. Ownership, versioning and lifecycle

- **What to evaluate:** Named owner and backup; versioning scheme; changelog; release approval; deprecation and retirement plan.  
- **Why it matters:** **\[Analysis\]** Ownerless skills accumulate silently; their failures go unreported and unfixed. SemVer requires a declared public API to make version numbers meaningful ([SemVer](https://semver.org/)).  
- **Evidence to request:** Owner record; version history; release notes; the models/tools it was tested with per version.  
- **Example questions:** Who fixes it at 4 p.m. on a Friday? What counts as a breaking change? How do users learn about changes?  
- **Red flags:** No owner; owner left the organization; versions changed in place; no changelog.  
- **Rating guidance:** 4 \= owner and backup, semantic versions, changelog, retirement criteria. 0 \= no accountable owner. **A 0 here blocks production adoption.**

### D11. Accessibility, usability and human-centered design

- **What to evaluate:** Whether people who use the skill or its outputs can do so effectively, including people with disabilities; plain language; error messages; fit with real workflows.  
- **Why it matters:** **\[Fact\]** Section 508 covers ICT that federal agencies develop, procure, maintain or use, and its standards define "documents" to include email, spreadsheets, presentations and images ([Section508.gov update](https://www.section508.gov/blog/accessibility-news-the-section-508-Update/); [Section508.gov documents](https://www.section508.gov/test/documents/)). ISO/IEC 25010:2023 defines a product quality model of nine characteristics that includes usability-related characteristics ([ISO/IEC 25010:2023 abstract](https://www.iso.org/cms/%20render/live/en/sites/isoorg/contents/data/standard/07/81/78176.html)).  
- **Evidence to request:** User testing notes; accessibility check results for generated documents or UIs; error message samples.  
- **Example questions:** Do generated documents have headings, alt text and readable tables? Can a non-technical user tell when the skill failed?  
- **Red flags:** Inaccessible outputs used for official purposes; jargon-only errors; workflow that forces users to work around the skill.  
- **Rating guidance:** 4 \= tested with representative users and accessibility checks. 0 \= known inaccessible outputs for public or employee use. **Expert review:** accessibility/508 program.

### D12. Operational fitness

- **What to evaluate:** Performance, cost, rate limits, observability (logs, traces, metrics), incident response, rollback, and compliance/records implications.  
- **Why it matters:** **\[Fact\]** OWASP lists unbounded consumption as an LLM risk ([OWASP](https://genai.owasp.org/llm-top-10/)). OpenTelemetry maintains GenAI semantic conventions for spans, metrics and events, including MCP ([OpenTelemetry GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai)).  
- **Evidence to request:** Latency and cost per run; load test results where relevant; logging design; runbook; rollback steps; records schedule determination if outputs are federal records.  
- **Example questions:** What does one run cost, and what is the worst case? Can we reconstruct what happened in an incident?  
- **Red flags:** No logs or logs with secrets; unbounded loops; no rollback; outputs that are federal records with no retention plan.  
- **Rating guidance:** 4 \= SLOs defined, monitored, runbook and rollback tested. 0 \= cannot observe or stop it in production. **Expert review:** records management for official communications or decisions.

---

## 5\. Evaluation rubric (0–4 scale) {#5.-evaluation-rubric-(0–4-scale)}

### 5.1 Score definitions (apply to every dimension)

| Score | Label | Definition |
| :---- | :---- | :---- |
| **4** | Strong | Criterion fully met with independent or reproducible evidence. No open issues above low severity. |
| **3** | Adequate | Criterion met with credible evidence; minor gaps with a documented, owned fix. |
| **2** | Partial | Some evidence; material gaps that are fixable. Acceptable only for pilots or Low risk with conditions. |
| **1** | Weak | Little evidence or significant unresolved issues. Not acceptable for production. |
| **0** | Absent / failing | No evidence, or evidence of a serious failure (critical vulnerability, harmful behavior, no owner). |
| **N/A** | Not applicable | Dimension genuinely does not apply (state why; e.g., no personal data processed). |

### 5.2 Minimum scores by risk tier

**\[Rec\]** Use minimums, not averages. Averages hide a fatal flaw behind good scores elsewhere.

| Dimension | Low | Moderate | High |
| :---- | :---- | :---- | :---- |
| D1 Purpose and fit | 2 | 3 | 3 |
| D2 Effectiveness | 2 | 3 | 3 |
| D3 Reliability | 2 | 3 | 4 |
| D4 Safety and misuse | 2 | 3 | 4 |
| D5 Security | 3 | 3 | 4 |
| D6 Privacy | 2 (or N/A) | 3 | 4 |
| D7 Human oversight | 2 | 3 | 4 |
| D8 Documentation | 2 | 3 | 3 |
| D9 Maintainability | 2 | 2 | 3 |
| D10 Ownership/lifecycle | 2 | 3 | 3 |
| D11 Accessibility/usability | 2 | 3 | 3 |
| D12 Operational fitness | 1 | 2 | 3 |

These thresholds are a starting point. A team may set stricter values; relaxing them should be a documented risk acceptance.

### 5.3 Blocking rules

**\[Rec\]** Any one of these blocks adoption regardless of other scores:

1. **Security (D5) \= 0**, or any confirmed critical vulnerability or malicious indicator. Consistent with the devCrew criterion that "the release threshold for critical security outcomes is zero" ([evaluation-and-release.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/references/evaluation-and-release.md)).  
2. **Ownership (D10) \= 0** — no accountable owner.  
3. **Privacy (D6) \= 0** — undisclosed transmission of sensitive data.  
4. **Human oversight (D7) ≤ 1** for any skill that takes irreversible external actions.  
5. **Any dimension at 0** for a High-risk skill.  
6. **Behavior does not match documentation** (undisclosed capability) — treat as a security finding.  
7. **Required specialist review not completed** (privacy, legal, records, accessibility, security) where the risk tier or data requires it.

A score of 1 on any dimension means "revise and resubmit" unless the outcome is a tightly bounded pilot with an explicit fix plan.

---

## 6\. Comparison table of evaluation dimensions {#6.-comparison-table-of-evaluation-dimensions}

| Dimension | Key question | Evidence required | Example tests or checks | Red flags | Suggested owner/reviewer |
| :---- | :---- | :---- | :---- | :---- | :---- |
| D1 Purpose and fit | Does it do one clear job that needs a skill? | Problem statement, non-goals, neighbor list | Trigger tests on near-neighbor prompts; duplication search in catalog | Vague scope; overlaps; "use for everything" | Product owner; catalog steward |
| D2 Effectiveness | Is it measurably better than the baseline? | Labeled test set, baseline and skill results, models tested | Paired runs (no-skill vs. skill vs. prior version); blind human rating | Demos only; no baseline; test set leaked into examples | Technical lead; domain expert |
| D3 Reliability | Does it behave consistently and fail safely? | Repeat-run results, edge-case results, failure modes | Repeat N runs; malformed/empty/huge input; timeout injection; trigger precision/recall | Silent failures; swallowed errors; unbounded retries | Technical lead; QA |
| D4 Safety and misuse | Can it cause or be steered toward harm? | Misuse scenarios, red-team results | Adversarial prompts; goal-hijack via documents; over-reliance review | No misuse analysis; authoritative tone with no caveats | AI/automation practitioner; red team |
| D5 Security | What could it do with its permissions, and is that acceptable? | File inventory, permission manifest, scanner results, SBOM, provenance | Manual review of all files; 2+ scanners; secret scan; sandboxed dynamic run; injection tests | Hidden network calls; obfuscation; secrets; unpinned deps; broad pre-approved tools | Security engineer / ISSO |
| D6 Privacy | What personal or sensitive data does it touch and where does it go? | Data-flow diagram, data inventory, PIA/PTA status | PII detection on outputs/logs; cross-user leakage test | Data to unvetted third parties; raw PII in logs | Privacy officer |
| D7 Human oversight | Can humans see, approve and stop consequential actions? | Approval points, kill switch, escalation rules | Attempt irreversible action without approval; test kill switch | Hidden approvals; no stop mechanism | Program owner; governance reviewer |
| D8 Documentation | Can a non-author understand and use it correctly? | Documentation set (min. fields) | Docs-vs-behavior comparison; new-user walkthrough | Missing limits/owner; docs contradict behavior | Technical writer; peer reviewer |
| D9 Maintainability | Can it be updated safely as dependencies and models change? | Dependency manifest, Scorecard results, duplication list | Dependency health check; rebuild from clean env; model-swap test | Abandoned deps; unsynced copies; missing referenced components | Technical lead; platform team |
| D10 Ownership/lifecycle | Who is accountable and how are changes controlled? | Owner record, version history, changelog, retirement criteria | Verify owner active; verify version immutability | No owner; in-place edits; no changelog | Program owner; catalog steward |
| D11 Accessibility/usability | Can intended users, including people with disabilities, use it and its outputs? | Usability notes, accessibility checks | Automated \+ manual accessibility checks on outputs; task-based user test | Inaccessible official outputs; jargon errors | Accessibility/508 coordinator; UX |
| D12 Operational fitness | Can we run, observe, afford and roll it back? | SLOs, cost data, logging design, runbook, records determination | Load/latency test; cost cap test; rollback drill; log review | No logs; unbounded cost; no rollback; unmanaged records | SRE/operations; records officer |

---

## 7\. Testing and evaluation plan {#7.-testing-and-evaluation-plan}

### 7.1 Principles

- **\[Rec\]** Write the test set before tuning the skill (vendor guidance agrees: [Claude best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).  
- **\[Rec\]** Prefer deterministic checks (schema validation, file hashes, database state, compiler/test results, exact-match labels). Use human or model judges only where judgment is unavoidable, with a written rubric.  
- **\[Fact\]** LLM judges have documented biases including position bias, verbosity bias and self-preference ([Zheng et al., MT-Bench](https://arxiv.org/html/2306.05685); [position bias study](https://arxiv.org/html/2406.07791v7)). **\[Rec\]** If you use an LLM judge, randomize order, use a different model family from the one under test where possible, and check agreement against a human-labeled sample.  
- **\[Rec\]** Test on every model and host you plan to deploy on. Re-run after any model change.  
- **\[Analysis\]** Report results by stage for agent skills: discovery (was it available), triggering (did it activate only when appropriate), use (did it follow the procedure and call tools correctly), and outcome (did postconditions pass without prohibited behavior) — the staging used in the devCrew criteria ([evaluation-and-release.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/references/evaluation-and-release.md)).

### 7.2 Test types

| Test type | Purpose | What to include | Expected for tier |
| :---- | :---- | :---- | :---- |
| **Unit / component** | Verify scripts, parsers, templates and validators in isolation | Argument validation, error exits, edge values, deterministic output | All tiers with code |
| **Integration** | Verify the skill with real (or faithful test) tools, APIs, connectors | Contract tests, auth failures, rate limits, timeouts, partial outages | Moderate+ |
| **Scenario-based** | Verify realistic end-to-end tasks | Happy path, each decision branch, ambiguous intent, missing inputs, malformed artifacts | All tiers |
| **Trigger tests (agent skills)** | Verify the skill loads when it should and not otherwise | Paraphrases, terse and long requests, implicit triggers, near-neighbor prompts, no-skill prompts | All agent skills |
| **Adversarial / misuse** | Find ways it can be hijacked or misused | Prompt injection in inputs, retrieved docs, filenames and tool output; jailbreaks; secret-exfiltration attempts; path traversal; excessive-agency probes | Moderate+ (sampled for Low) |
| **Regression** | Prevent previously fixed failures from returning | Frozen suite of past failures plus core scenarios; run on every change and model update | Moderate+ |
| **Human review** | Judge quality where automation cannot | Blind rating with rubric; inter-rater agreement; domain-expert review of a sample | Moderate+; mandatory for High |
| **User acceptance (UAT)** | Confirm it works for real users in real workflow | Task-based sessions with representative users, including assistive-technology users where relevant | Moderate+ |
| **Performance / cost** | Confirm latency, throughput and cost are acceptable | Typical and peak load; worst-case token/cost; cost caps | Where usage or cost matters |
| **Safety and security review** | Independent check of code, instructions, permissions, data flows | Manual review of all files; 2+ scanners; dependency/SBOM review; threat model (High) | All tiers (depth scales) |
| **Monitoring after release** | Detect drift, incidents and misuse | Metrics, sampled output review, incident intake, dependency/model change alerts | All tiers in production |

### 7.3 Suggested acceptance thresholds

**\[Rec\]** Declare thresholds before testing. Illustrative starting points (tune to the task):

- Scenario pass rate: at least the baseline plus a margin larger than repeat-run variation; for High risk, define per-scenario must-pass cases.  
- Critical security and safety cases: **100% pass (zero tolerated failures).**  
- Trigger precision and recall (agent skills): set targets by impact of a wrong trigger; no critical no-skill case may trigger the skill.  
- Regression suite: no previously passing critical case may fail.

### 7.4 Open-source and public testing frameworks

**\[Fact/Practice\]** The tools below are public. Verified descriptions are cited; others are well-established projects named for completeness. Evaluate any tool itself before adopting it, and run untrusted skills only in an isolated sandbox.

| Purpose | Tool | Notes |
| :---- | :---- | :---- |
| LLM / agent evaluation | **Inspect** (UK AI Security Institute) | Open-source evaluation framework with datasets, agents, tools, scorers, sandboxing (Docker, Kubernetes and others) and 200+ pre-built evals ([Inspect](https://inspect.aisi.org.uk/?lang=en-US)) |
| LLM app evals and red teaming | **promptfoo** | Open-source eval framework with red-team generation covering prompt injection, PII leaks, excessive agency, hallucination and more; includes OWASP Agentic mapping ([promptfoo red teaming](https://www.promptfoo.dev/docs/guides/llm-redteaming/); [OWASP Agentic page](https://www.promptfoo.dev/docs/red-team/owasp-agentic-ai/)) |
| LLM unit tests in CI | **DeepEval** | Pytest-style assertions; 50+ metrics including agent/tool-use and RAG metrics ([DeepEval](https://deepeval.com/docs/introduction)). Note: many metrics are LLM-as-judge; validate against human labels. |
| LLM vulnerability scanning | **garak** (NVIDIA) | Probes for hallucination, data leakage, prompt injection, jailbreaks and more ([garak](https://github.com/NVIDIA/garak)) |
| Red-team orchestration | **PyRIT** (Microsoft) | Open-source toolkit for automated scans, multi-turn attacks and human-led testing ([PyRIT](https://github.com/microsoft/PyRIT)) |
| Skill format validation | **skills-ref** | Reference validator for the Agent Skills format; the project states it is "for demonstration purposes only" and "not meant to be used in production" ([skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)) |
| Skill benchmark methodology | **SkillsBench** | Paired no-skill vs. skill evaluation with deterministic verifiers; useful as a design pattern ([SkillsBench repo](https://github.com/benchflow-ai/skillsbench)) |
| Repo/supply-chain health | **OpenSSF Scorecard** | 0–10 automated checks such as pinned dependencies, SAST, maintenance ([Scorecard](https://github.com/ossf/scorecard)) |
| Build provenance | **SLSA** framework | Levels for provenance and build integrity ([SLSA](https://slsa.dev/spec/v1.1/levels)) |
| Telemetry | **OpenTelemetry GenAI conventions** | Standard spans/metrics/events for GenAI and MCP ([OpenTelemetry GenAI](https://github.com/open-telemetry/semantic-conventions-genai)) |
| Conventional code testing | pytest, Hypothesis (property-based), Pact (contract tests), Playwright (UI/e2e), k6 or Locust (load) | **\[Practice\]** Widely used; not individually re-verified in this research |
| Static analysis and secrets | Semgrep, Bandit (Python), gitleaks; Syft/Grype for SBOM and vulnerability matching | **\[Practice\]** Widely used; not individually re-verified in this research |
| Accessibility | axe-core, plus manual testing per Section 508 guidance | **\[Practice\]** Automated tools catch only part of accessibility issues; manual review is still needed |

**\[Fact\] Scanner caution.** Because skill scanners disagree heavily (pairwise κ 0.045–0.082) and some malicious skills evade all three studied scanners ([arXiv:2606.01494](https://arxiv.org/html/2606.01494v1)), treat scanner output as evidence to weigh, not a verdict.

---

## 8\. Risk assessment model {#8.-risk-assessment-model}

### 8.1 Risk factors and scoring

**\[Rec\]** Score each factor 0–3. The factors combine the request's list with themes from M-25-21 (high-impact definition), OWASP excessive agency, and the MCP consent principles.

| \# | Factor | 0 | 1 | 2 | 3 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| F1 | Access to sensitive data | None / public only | Internal, non-sensitive | PII, CUI or confidential business data | Highly sensitive (e.g., health, financial, law enforcement, credentials) |
| F2 | Ability to take external actions | Read-only, output to user only | Writes to local/sandboxed workspace | Writes to shared systems, creates tickets, drafts messages | Sends messages, changes production systems, moves money, grants access |
| F3 | Irreversibility | Fully reversible | Reversible with effort | Partly irreversible | Irreversible (sent, deleted, paid, published) |
| F4 | User population / reach | Individual | Team | Organization | Public or cross-agency |
| F5 | Impact of errors | Trivial | Rework / inconvenience | Material cost, mission impact, reputational harm | Rights, safety, legal or significant financial effect |
| F6 | Autonomy level | Human performs each step | Human approves each action | Human approves batches / exceptions | Fully autonomous |
| F7 | Security exposure | No network, no untrusted input | Trusted inputs only | Processes untrusted content (web, email, uploads) | Untrusted content plus tool/code execution |
| F8 | Legal, policy, compliance implications | None | Internal policy only | Regulated data or records | Statutory obligations, rights determinations |
| F9 | Reliance on LLM reasoning | None (deterministic) | LLM for formatting/drafting with review | LLM decisions reviewed by humans | LLM decisions acted on directly |
| F10 | Tool / API calling | None | Read-only tools | Write tools within scope | Arbitrary tools, shell, browser, or code execution |
| F11 | Official communications | No | Internal drafts | External drafts requiring approval | Sends or publishes official communications |
| F12 | Human oversight (inverse) | Strong review of every output | Review of all consequential outputs | Sampled review | No meaningful review |

### 8.2 Tier assignment

**\[Rec\]** Use both the total and "trigger" factors; a single severe factor can raise the tier.

| Tier | Rule of thumb | Examples |
| :---- | :---- | :---- |
| **Low** | Total ≤ 8 and no factor \= 3 | Formatting helper; read-only summarizer of public documents for an individual, with human review |
| **Moderate** | Total 9–18, or any one factor \= 3 among F4, F7, F9 | Team research assistant processing web content; code-review helper that comments but cannot merge |
| **High** | Total ≥ 19, or any factor \= 3 among F1, F2, F3, F5, F8, F10, F11; or meets the M-25-21 "high-impact" definition (output is a principal basis for decisions with legal, material, binding or significant effect on rights or safety, [M-25-21](https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf)) | Skill that sends external email, modifies production infrastructure, or drafts benefit determinations |
| **Prohibited without special authorization** | F2 \= 3 **and** F3 \= 3 **and** F6 \= 3 (autonomous irreversible action); or unverifiable provenance plus code execution; or uses prohibited by law or agency policy | Autonomous skill that deletes records or makes payments with no human approval; unaudited marketplace skill with shell access on a system holding sensitive data |

**\[Analysis\]** These cut-offs are judgment calls, not validated thresholds. Calibrate them on 10–20 of your own skills, then adjust. The tier sets *review depth*; it is not a substitute for agency high-impact determinations, FISMA categorization, or privacy determinations.

---

## 9\. Adoption recommendation process {#9.-adoption-recommendation-process}

### 9.1 Decision logic

**\[Rec\]**

1. Any blocking rule triggered (Section 5.3)? → **Reject** (if fundamental or malicious) or **Revise and resubmit** (if fixable).  
2. All dimension minimums for the tier met with scores ≥ 3, and no open conditions? → **Adopt as-is**.  
3. Minimums met, but some items need a specific, time-bound fix or operating constraint? → **Adopt with conditions**.  
4. Promising but evidence comes from limited or synthetic testing, or real-world effectiveness is unknown? → **Pilot only**.  
5. For skills already in use: monitoring shows sustained underperformance, an unfixable risk, loss of owner, or a better replacement? → **Retire**.

### 9.2 Outcomes

| Outcome | When appropriate | Typical requirements |
| :---- | :---- | :---- |
| **Adopt as-is** | All tier minimums met; evidence strong; no open conditions; owner and monitoring in place | Release record, monitoring plan, re-review date |
| **Adopt with conditions** | Minimums met; residual issues manageable with explicit constraints | Written conditions (e.g., "read-only connector only," "human approval for all sends," "fix X by date"), condition owner, check date; automatic downgrade to pilot or pause if a condition lapses |
| **Pilot only** | Benefit plausible but unproven in real use; or Moderate/High risk needing real-world evidence | Limited users and data, time limit, success and stop criteria declared up front, enhanced monitoring, no irreversible actions without approval |
| **Revise and resubmit** | Fixable gaps: missing tests, documentation, owner, or a dimension scoring 1; or a blocking finding that can be corrected | Specific findings list tied to dimensions, with what evidence is needed next time |
| **Reject** | Malicious indicators; undisclosed capability; purpose inappropriate or prohibited; risk cannot be mitigated; a non-skill solution is clearly better | Short rationale; record to prevent re-submission of the same artifact without change |
| **Retire existing skill** | Persistent failure against monitoring thresholds; unmaintained dependency or retired model with no migration; owner gone and no successor; superseded; changed policy or law | Deprecation notice, migration path, end date, removal from catalogs, data/log retention handled per records schedule |

**\[Fact\]** For high-impact federal AI, M-25-21 says that if proper risk mitigation is not possible, agencies "must cease the use of the AI" ([M-25-21](https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf)). Build retirement into the process from day one.

---

## 10\. Reviewer workflow {#10.-reviewer-workflow}

**\[Rec\]** Eleven steps. Low-risk skills may compress steps (see Section 11).

| Step | Who | Inputs | Activities | Output / exit criteria |
| :---- | :---- | :---- | :---- | :---- |
| **1\. Intake** | Submitter; catalog steward | Skill package, intake form (Template 12.1 top section) | Register skill, version, owner, intended use; confirm complete package (all referenced files present) | Intake record; package hash/version frozen for review |
| **2\. Initial triage** | Catalog steward or lead reviewer | Intake record | Classify type (2.3) and risk tier (8); check for duplicates; decide review track; identify specialist reviews needed | Tier, track, reviewer assignments |
| **3\. Documentation review** | Peer reviewer | Docs set | Check minimum documentation fields; plain-language readability; docs vs. declared permissions | D1, D8, D10 draft scores; gaps list |
| **4\. Technical review** | Technical lead | All files, tests, dependency manifest | Read every file (including scripts, images and assets); check structure, error handling, dependencies, pinning, duplication; run tests in a sandbox; review effectiveness evidence and baseline | D2, D3, D9, D12 draft scores |
| **5\. Safety, security and privacy review** | Security engineer; privacy officer; others as needed | Permission manifest, data flows, scanner results | Threat model (High); 2+ scanners; secret scan; injection and misuse tests; PIA/PTA determination; legal/records/policy referrals | D4, D5, D6, D7 scores; findings with severity |
| **6\. User testing** | Product owner; UX; accessibility | Pilot environment | Task-based UAT with representative users; accessibility checks on outputs | D11 score; usability findings |
| **7\. Scoring** | Lead reviewer | All findings | Consolidate scores; apply tier minimums and blocking rules; record rationale | Completed evaluation form (12.1) |
| **8\. Decision** | Decision authority (scaled by tier) | Evaluation form, risk worksheet | Choose outcome (Section 9); define conditions | Adoption decision memo (12.4) |
| **9\. Release approval** | Owner \+ approver | Decision memo | Approve exact version (hash); confirm monitoring and rollback ready; publish to catalog with tier and conditions | Release record |
| **10\. Monitoring** | Owner; operations | Monitoring checklist (12.5) | Track metrics, incidents, overrides, cost, dependency/model changes | Monthly/quarterly monitoring notes; incident tickets |
| **11\. Periodic re-evaluation** | Catalog steward | Monitoring data | Re-review on schedule (e.g., Low annually, Moderate semi-annually, High quarterly) and after material change: new major version, model change, permission change, incident, policy change | Continue / adopt with new conditions / pause / retire |

**\[Rec\] Independence.** For High risk, at least one reviewer should not have been involved in building the skill — mirroring M-25-21's requirement for review "by an independent agency reviewer who was not involved in development" for high-impact AI impact assessments ([M-25-21](https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf)).

---

## 11\. Lightweight vs. rigorous review tracks {#11.-lightweight-vs.-rigorous-review-tracks}

### 11.1 Lightweight track (small team; Low risk; some Moderate)

**\[Rec\]**

- **People:** Owner plus one peer reviewer. Escalate to a security or privacy specialist only if triage flags data, network or tool access.  
- **Time:** Typically a few hours per skill (estimate, not measured).  
- **Steps:** Intake and triage → documentation check → read every file → run 10–30 scenario and negative test cases against a no-skill baseline → one automated security scan plus a secret scan → score with the rubric → decision → publish with re-review date.  
- **Ten-question quick screen** (any "no" moves the skill to the standard track):  
  1. Is there a named owner and backup?  
  2. Is the job stated in one sentence, with non-goals?  
  3. Did I read every bundled file, and does behavior match the description?  
  4. Is the skill read-only or limited to a sandboxed workspace?  
  5. Does it avoid sensitive data?  
  6. Does it avoid untrusted content, or treat it strictly as data?  
  7. Are dependencies pinned, with no runtime downloads?  
  8. Does it beat the baseline on a small test set written before tuning?  
  9. Does a human review outputs before they are used for anything consequential?  
  10. Can we disable it immediately?

### 11.2 Standard track (Moderate risk)

All eleven workflow steps, with at least two reviewers (technical and security/privacy), two scanners, a regression suite, UAT with a small group, and an adopt-with-conditions or pilot decision documented in a memo.

### 11.3 Rigorous track (High risk, high-impact, or widely deployed)

**\[Rec\]** In addition to the standard track:

- **Independent review** by a reviewer not involved in development; formal **risk acceptance** signed by an accountable official (consistent with [M-25-21](https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf) for high-impact AI).  
- **Threat model** mapped to OWASP LLM and Agentic Top 10 risk categories ([LLM](https://genai.owasp.org/llm-top-10/); [Agentic](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)) and, where relevant, NIST's adversarial ML taxonomy ([NIST AI 100-2e2025](https://csrc.nist.gov/pubs/ai/100/2/e2025/final)).  
- **Structured red teaming** with documented attack scenarios and a findings report.  
- **Impact assessment** covering purpose and benefit, data quality, privacy/civil rights/civil liberties impacts, reassessment schedule and costs.  
- **Specialist sign-offs** as applicable: cybersecurity/ISSO, privacy, legal/general counsel, records management, Section 508/accessibility, procurement (vendor terms, data rights; see [OMB M-25-22](https://www.whitehouse.gov/omb/information-resources/guidance/memoranda/)), and policy/communications for official communications.  
- **Supply-chain controls:** SBOM, pinned and provenance-verified dependencies, signed releases, Scorecard checks of upstream projects.  
- **Staged rollout:** pilot → limited production → full, with stop criteria at each stage.  
- **Enhanced monitoring:** human sampling of outputs, incident drills, kill-switch tests, quarterly re-review.  
- **Operator training** specific to the skill (M-25-21 requires training for high-impact AI operators).

**\[Analysis\]** For federal systems, map controls to the agency's NIST SP 800-53 baseline. NIST is developing SP 800-53 control overlays that include single-agent and multi-agent use cases; as of October 20, 2026 the project page lists them under the renamed "Control Overlays for Super Intelligence Systems (COSIS)," citing a September 29, 2026 executive order on terminology, and notes previously issued documents were not altered ([NIST COSIS project](https://csrc.nist.gov/Projects/cosis)). Drafts were not final at the research date; check for updates before relying on them.

---

## 12\. Templates {#12.-templates}

### 12.1 Skill evaluation form

```
# Skill Evaluation Form

## A. Intake
- Skill name:
- Version / commit or package hash reviewed:
- Submitted by:            Date:
- Owner:                   Backup owner:
- Intended users and setting:
- One-sentence job / completion criterion:
- Non-goals (what it must not be used for):
- Near-neighbor skills and how this differs:
- Skill type(s) (Section 2.3):
- Runtime / host / models it was tested with:
- Permissions and tools requested:
- Data accessed (categories):
- External services and dependencies (with versions):
- Risk tier (from 12.3):          Review track: Lightweight / Standard / Rigorous

## B. Minimum documentation present? (Y/N, location)
- [ ] Purpose, triggers and non-goals
- [ ] Inputs, outputs and success criteria
- [ ] Required permissions, tools, data, environment
- [ ] Dependencies with versions and provenance
- [ ] Known limitations and failure modes
- [ ] Human-oversight points and how to stop it
- [ ] Test evidence summary (set size, baseline, results, models)
- [ ] Owner, version, changelog, how to report issues
- [ ] Risk tier and any conditions of use

## C. Scores (0–4 or N/A; tier minimum in brackets)
| Dim | Score | Tier min | Evidence (where) | Findings / fix | Reviewer |
|---|---|---|---|---|---|
| D1 Purpose and fit | | | | | |
| D2 Effectiveness | | | | | |
| D3 Reliability | | | | | |
| D4 Safety and misuse | | | | | |
| D5 Security | | | | | |
| D6 Privacy | | | | | |
| D7 Human oversight | | | | | |
| D8 Documentation | | | | | |
| D9 Maintainability | | | | | |
| D10 Ownership/lifecycle | | | | | |
| D11 Accessibility/usability | | | | | |
| D12 Operational fitness | | | | | |

## D. Blocking rules (Section 5.3) — any triggered? Y/N, which:
## E. Specialist reviews required / completed:
- [ ] Security/ISSO  [ ] Privacy  [ ] Legal  [ ] Records  [ ] Accessibility/508
- [ ] Procurement  [ ] Policy/communications  [ ] Other:
## F. Recommended outcome: Adopt / Adopt with conditions / Pilot / Revise / Reject / Retire
## G. Reviewer sign-off (name, role, date):
```

### 12.2 Skill test plan

```
# Skill Test Plan

- Skill / version:            Risk tier:
- Hosts and models under test:
- Baselines: [ ] no-skill  [ ] current manual process  [ ] previous version
- Thresholds (declared before testing):
  - Scenario pass rate target:
  - Critical safety/security cases: 100% pass
  - Trigger precision / recall / over-trigger targets (agent skills):
  - Latency / cost limits:
- Test set: size, source, who labeled, held-out portion:

| ID | Kind | Variant | Setup / input | Expected result or postcondition | Oracle (deterministic / human / model judge) | Pass/Fail | Notes |
|---|---|---|---|---|---|---|---|
| T01 | Unit | | | | | | |
| T02 | Integration | | | | | | |
| T03 | Scenario – happy path | | | | | | |
| T04 | Scenario – missing input | | | | | | |
| T05 | Trigger – near neighbor (should NOT load) | | | | | | |
| T06 | Adversarial – injection in retrieved doc | | | | | | |
| T07 | Adversarial – secret exfiltration attempt | | | | | | |
| T08 | Regression – past failure #__ | | | | | | |
| T09 | Performance – peak load / worst-case cost | | | | | | |
| T10 | Accessibility – generated document | | | | | | |
| T11 | UAT – representative user task | | | | | | |

- Repeat runs per case (for non-deterministic skills):
- Judge controls (if LLM judge): different model family, randomized order, human agreement sample size:
- Environment isolation (sandbox, no production credentials, egress limits):
- Results summary and decision:
```

### 12.3 Risk assessment worksheet

```
# Risk Assessment Worksheet

Skill / version:                Assessor:            Date:

| Factor | Score 0–3 | Rationale |
|---|---|---|
| F1 Sensitive data access | | |
| F2 External actions | | |
| F3 Irreversibility | | |
| F4 Reach / user population | | |
| F5 Impact of errors | | |
| F6 Autonomy | | |
| F7 Security exposure | | |
| F8 Legal/policy/compliance | | |
| F9 Reliance on LLM reasoning | | |
| F10 Tool/API calling | | |
| F11 Official communications | | |
| F12 Lack of human oversight | | |
| **Total** | | |

Escalators (any = 3 in F1, F2, F3, F5, F8, F10, F11 → High): Y/N
Meets agency "high-impact AI" definition? Y/N — basis:
Prohibited-without-authorization conditions (F2=3, F3=3, F6=3; unverifiable provenance + code execution; prohibited use)? Y/N

Assigned tier: Low / Moderate / High / Prohibited without special authorization
Top 3 risks and mitigations:
1.
2.
3.
Residual risk accepted by (name, role, signature, date):
```

### 12.4 Adoption decision memo

```
# Adoption Decision Memo

To:            From:            Date:
Subject: Decision on <skill name> v<version>

1. Decision: Adopt as-is / Adopt with conditions / Pilot only / Revise and resubmit / Reject / Retire
2. Summary of the skill and intended use (2–3 sentences):
3. Risk tier and basis:
4. Key evidence:
   - Effectiveness vs. baseline:
   - Security and privacy review results:
   - User testing:
5. Scores below 3 and how they are addressed:
6. Conditions (if any) — condition, owner, due date, consequence if unmet:
7. Specialist reviews completed:
8. Residual risks and who accepts them:
9. Monitoring plan and re-review date:
10. Rollback / retirement trigger:
Approved by (name, role, signature):
```

### 12.5 Post-deployment monitoring checklist

```
# Post-Deployment Monitoring Checklist — <skill> v<version>
Period:            Reviewer:

Performance and quality
- [ ] Task success rate vs. pre-release baseline (sampled or measured):
- [ ] Human override / correction rate:
- [ ] Sampled output review completed (n = __), issues found:
- [ ] Trigger accuracy (agent skills): wrong-trigger and missed-trigger reports:

Safety, security, privacy
- [ ] Incidents and near misses logged and reviewed:
- [ ] Any blocked injection attempts or anomalous tool calls in logs:
- [ ] Logs checked for secrets or sensitive data leakage:
- [ ] Permission or scope changes since last review:

Dependencies and change
- [ ] Model or host version changes since last review → regression suite re-run?
- [ ] Dependency updates / advisories (SBOM checked):
- [ ] Upstream skill or service availability changes:

Operations
- [ ] Latency, errors, traffic, saturation within targets:
- [ ] Cost within budget; no runaway usage:
- [ ] Kill switch / rollback tested this period (High risk: quarterly):

Governance
- [ ] Owner and backup still active:
- [ ] Conditions of adoption still met:
- [ ] User feedback reviewed; accessibility complaints addressed:
- [ ] Re-evaluation trigger hit? (major version, model change, incident, policy change)

Outcome: Continue / Continue with new conditions / Pause / Retire
```

---

## 13\. Evidence gaps, conflicts and limitations {#13.-evidence-gaps,-conflicts-and-limitations}

- **Effect sizes vary and are moving.** SkillsBench's own reported numbers changed between versions (an earlier version described 86 tasks across 11 domains and 7 configurations; the current abstract reports 87 tasks across 8 domains and 18 configurations) ([earlier version](https://ar5iv.labs.arxiv.org/html/2602.12670); [current abstract](https://arxiv.org/abs/2602.12670)). Treat published averages as directional; measure your own.  
- **Prevalence numbers are not comparable across studies.** Reported vulnerable-skill rates (26.1% in one study, 36.82% "any flaw" in a vendor audit, 157 confirmed malicious in 98,380 in another) use different corpora, definitions and methods ([arXiv:2601.10338](https://arxiv.org/abs/2601.10338); [Snyk](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/); [arXiv:2602.06547](https://arxiv.org/abs/2602.06547)). They show the risk is real, not its exact size for any given catalog. Snyk is a security vendor; its study is vendor research.  
- **Most skill-security research focuses on public marketplaces.** Internally authored skills may have lower malicious risk but the same accidental risks (over-permissioning, injection exposure, stale dependencies). There is little public evidence on internal skill catalogs.  
- **Several sources are preprints.** Many 2026 skill-security and benchmark papers are arXiv preprints and may not yet be peer reviewed.  
- **Vendor documentation is labeled as such.** Anthropic's guidance is useful, platform-specific and not a neutral standard.  
- **Standards are in flux.** NIST states AI RMF 1.0 is being revised ([NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)); NIST's agent-related control overlays are drafts ([COSIS](https://csrc.nist.gov/Projects/cosis)); NIST's AI Agent Standards Initiative (announced February 17, 2026\) has said further deliverables will follow ([NIST CAISI announcement](https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure)). OWASP lists are community consensus documents updated periodically.  
- **LLM-as-judge evaluation is useful but biased.** Documented position, verbosity and self-preference biases mean automated judging needs human calibration ([MT-Bench study](https://arxiv.org/html/2306.05685); [bias survey](https://arxiv.org/html/2604.23178)).  
- **The rubric thresholds and risk cut-offs in this guide are judgment-based**, not empirically validated. Calibrate them with your own skills and revisit after a few review cycles.  
- **Source access limits.** GitHub's web page for the example skills folder could not be fetched directly; the public GitHub API and raw files were used instead. Only the README and the `agent-skill-authoring` skill files were read in detail; other skills were observed only by name and README description. ISO standards were consulted only via public abstracts. Some tools in Section 7.4 are named from general knowledge and were not individually re-verified in this research.  
- **Not legal advice.** Federal requirements cited (M-25-21, Section 508, E-Government Act Section 208\) should be confirmed with agency counsel, privacy, records and accessibility offices for a specific use.

## Next steps {#next-steps}

1. Pilot this guide on 5–10 existing skills across at least three risk tiers; record time spent and where reviewers disagreed.  
2. Calibrate the risk cut-offs and tier minimums from that pilot.  
3. Stand up a shared test-case library (trigger, adversarial, regression) reusable across skills.  
4. Decide catalog-level controls: required fields at intake, version immutability, owner attestation and a re-review calendar.  
5. Identify which specialist offices must sign off for each tier and agree on turnaround expectations with them.

---

## 14\. Source list {#14.-source-list}

Standards, government and frameworks

- NIST AI Risk Management Framework — [https\://www\.nist.gov/itl/ai-risk-management-framework](https://www.nist.gov/itl/ai-risk-management-framework)  
- NIST AI 600-1, Generative AI Profile — [https\://doi.org/10.6028/NIST.AI.600-1](https://doi.org/10.6028/NIST.AI.600-1)  
- NIST SP 800-218 SSDF — [https\://csrc.nist.gov/projects/ssdf](https://csrc.nist.gov/projects/ssdf)  
- NIST SP 800-218A, SSDF Community Profile for GenAI — [https\://www\.nist.gov/publications/secure-software-development-practices-generative-ai-and-dual-use-foundation-models-ssdf](https://www.nist.gov/publications/secure-software-development-practices-generative-ai-and-dual-use-foundation-models-ssdf)  
- NIST AI 100-2e2025, Adversarial ML taxonomy — [https\://csrc.nist.gov/pubs/ai/100/2/e2025/final](https://csrc.nist.gov/pubs/ai/100/2/e2025/final)  
- NIST COSIS (formerly COSAiS) SP 800-53 overlays project — [https\://csrc.nist.gov/Projects/cosis](https://csrc.nist.gov/Projects/cosis)  
- NIST AI Agent Standards Initiative announcement — [https\://www\.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure](https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure)  
- NIST AI 800-1 (initial public draft), Managing Misuse Risk — [https\://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.800-1.ipd.pdf](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.800-1.ipd.pdf)  
- OMB M-25-21 — [https\://www\.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf](https://www.whitehouse.gov/wp-content/uploads/2025/02/M-25-21-Accelerating-Federal-Use-of-AI-through-Innovation-Governance-and-Public-Trust.pdf)  
- OMB memoranda index (M-25-22, M-26-04) — [https\://www\.whitehouse.gov/omb/information-resources/guidance/memoranda/](https://www.whitehouse.gov/omb/information-resources/guidance/memoranda/)  
- OMB M-03-22 (E-Government Act privacy provisions) — [https\://obamawhitehouse.archives.gov/omb/memoranda\_m03-22/](https://obamawhitehouse.archives.gov/omb/memoranda_m03-22/)  
- GAO-21-519SP AI Accountability Framework — [https\://www\.gao.gov/products/gao-21-519sp](https://www.gao.gov/products/gao-21-519sp)  
- CISA Secure by Design — [https\://www\.cisa.gov/resources-tools/resources/secure-by-design](https://www.cisa.gov/resources-tools/resources/secure-by-design)  
- Section508.gov — [https\://www\.section508.gov/blog/accessibility-news-the-section-508-Update/](https://www.section508.gov/blog/accessibility-news-the-section-508-Update/) ; [https\://www\.section508.gov/test/documents/](https://www.section508.gov/test/documents/)  
- ISO/IEC 25010:2023 (abstract) — [https\://www\.iso.org/cms/%20render/live/en/sites/isoorg/contents/data/standard/07/81/78176.html](https://www.iso.org/cms/%20render/live/en/sites/isoorg/contents/data/standard/07/81/78176.html)

Security community and specifications

- OWASP Top 10 for LLM Applications 2025 — [https\://genai.owasp.org/llm-top-10/](https://genai.owasp.org/llm-top-10/)  
- OWASP Top 10 for Agentic Applications 2026 — [https\://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)  
- Model Context Protocol specification — [https\://modelcontextprotocol.io/specification/2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)  
- Agent Skills specification — [https\://agentskills.io/specification](https://agentskills.io/specification)  
- SLSA — [https\://slsa.dev/spec/v1.1/levels](https://slsa.dev/spec/v1.1/levels)  
- OpenSSF Scorecard — [https\://github.com/ossf/scorecard](https://github.com/ossf/scorecard)  
- Semantic Versioning 2.0.0 — [https\://semver.org/](https://semver.org/)  
- OpenTelemetry GenAI semantic conventions — [https\://github.com/open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai)  
- Google SRE book, Monitoring Distributed Systems — [https\://sre.google/sre-book/monitoring-distributed-systems/](https://sre.google/sre-book/monitoring-distributed-systems/)

Research

- Liu et al., Agent Skills in the Wild (arXiv:2601.10338) — [https\://arxiv.org/abs/2601.10338](https://arxiv.org/abs/2601.10338)  
- Malicious Agent Skills in the Wild (arXiv:2602.06547) — [https\://arxiv.org/abs/2602.06547](https://arxiv.org/abs/2602.06547)  
- SkillsBench (arXiv:2602.12670) — [https\://arxiv.org/abs/2602.12670](https://arxiv.org/abs/2602.12670)  
- ClawHub Security Signals: scanner disagreement (arXiv:2606.01494) — [https\://arxiv.org/html/2606.01494v1](https://arxiv.org/html/2606.01494v1)  
- TrustProbe, unsafe chains of trust in skill-based agents (arXiv:2609.39065) — [https\://arxiv.org/html/2609.39065](https://arxiv.org/html/2609.39065)  
- Breck et al., The ML Test Score — [https\://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/)  
- Zheng et al., Judging LLM-as-a-Judge — [https\://arxiv.org/html/2306.05685](https://arxiv.org/html/2306.05685)  
- Position bias in LLM-as-a-Judge — [https\://arxiv.org/html/2406.07791v7](https://arxiv.org/html/2406.07791v7)

Vendor documentation and vendor research (labeled)

- Anthropic, Agent Skills overview (security considerations) — [https\://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)  
- Anthropic, Skill authoring best practices — [https\://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)  
- Anthropic engineering, Equipping agents with Agent Skills — [https\://www\.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills)  
- Snyk, ToxicSkills audit — [https\://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)

Tools

- Inspect (UK AISI) — [https\://inspect.aisi.org.uk/](https://inspect.aisi.org.uk/)  
- promptfoo — [https\://www\.promptfoo.dev/docs/guides/llm-redteaming/](https://www.promptfoo.dev/docs/guides/llm-redteaming/)  
- DeepEval — [https\://deepeval.com/docs/introduction](https://deepeval.com/docs/introduction)  
- garak — [https\://github.com/NVIDIA/garak](https://github.com/NVIDIA/garak)  
- PyRIT — [https\://github.com/microsoft/PyRIT](https://github.com/microsoft/PyRIT)  
- skills-ref — [https\://github.com/agentskills/agentskills/tree/main/skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)  
- SkillsBench repository — [https\://github.com/benchflow-ai/skillsbench](https://github.com/benchflow-ai/skillsbench)

Example collection (used for patterns only)

- GSA-TTS devCrew\_s1 skills README — [https\://github.com/GSA-TTS/devCrew\_s1/blob/master/skills/README.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/README.md)  
- agent-skill-authoring SKILL.md — [https\://github.com/GSA-TTS/devCrew\_s1/blob/master/skills/agent-skill-authoring/SKILL.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/SKILL.md)  
- agent-skill-authoring review criteria — [https\://github.com/GSA-TTS/devCrew\_s1/blob/master/skills/agent-skill-authoring/references/review-criteria.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/references/review-criteria.md)  
- agent-skill-authoring evaluation and release — [https\://github.com/GSA-TTS/devCrew\_s1/blob/master/skills/agent-skill-authoring/references/evaluation-and-release.md](https://github.com/GSA-TTS/devCrew_s1/blob/master/skills/agent-skill-authoring/references/evaluation-and-release.md)