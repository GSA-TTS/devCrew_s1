# Technical Acceptance Scoring Guide for Federal AI Use Cases

## Purpose and Scope

This guide enables an AI agent to score Technology Acceptance Model (TAM) dimensions for federal AI use cases that contain only brief descriptions. The scores are probabilistic proxies — not survey-based measurements — intended for portfolio-level analysis, governance gap detection, and prioritization. They identify where to focus deeper human review, not approve or reject individual systems.

The scoring is designed for the normalized OMB inventory format. Fields are grouped by typical availability in the 2025 inventory:

**Primary** (84–100% available): `use_case_name`, `problem_solved`, `benefits`, `development_stage`, `is_high_impact`, `biz_goals`

**Secondary** (79–83% available): `system_outputs`, `classification`, `topic_area`

**Sparse** (36–47% available): `have_ato`, `has_pii`, `contracting_usage`, `has_custom_code`, `data_description`, `demographic_features`

---

## TAM Dimensions

Four dimensions are scored on a **1–5 scale** (integers or half-points):

| Dimension | What it measures |
|---|---|
| PU (Perceived Usefulness) | How strongly users will believe this AI improves mission outcomes or job performance |
| PEOU (Perceived Ease of Use) | How effortless interacting with the AI will feel to intended end users |
| Trust | Trustworthiness based on governance documentation and risk management evidence |
| Explainability | How interpretable and transparent the AI's outputs are to users |

Scale anchors: **5** = strong evidence, **3** = neutral/mixed/inferred default, **1** = clear absence or critical gap.

---

## Scoring Rules by Dimension

Each dimension is scored by answering two LLM questions, each producing an integer 1–5. Final score per dimension = floor((Q1 + Q2) / 2). If a question cannot be answered from the available text, score that question at 3 (neutral).

### Perceived Usefulness (PU)

Q1: How directly and tangibly does this AI benefit the end users who interact with it daily?
1 = no discernible user benefit — only organizational or management benefit described; 2 = indirect user benefit — efficiency that helps the agency but not clearly the individual user; 3 = clear user benefit — reduces a specific task burden or improves work quality for users; 4 = significant user benefit — substantially reduces time, risk, or effort on high-frequency tasks; 5 = essential user benefit — addresses safety, mission-critical outcomes, or prevents serious operational failure.

Q2: How specific and credible are the outcomes described in the problem or benefits text?
1 = vague or tautological — benefits restate the problem with no measurable claim; 2 = generic improvement language with no verifiable claim; 3 = concrete outcome stated but not quantified; 4 = quantified or clearly verifiable impact (time saved, error rate reduced, inspections reduced); 5 = high-stakes quantified impact with mission-critical or safety significance.

### Perceived Ease of Use (PEOU)

Consult the Classification Type reference table below for typical interface and output characteristics of the AI's type before answering.

Q1: How much training or domain expertise would the primary end user need to interact with this AI effectively?
1 = advanced technical expertise required (data scientist, quant, or ML engineer level); 2 = domain specialist expertise required (analyst or trained operator who interprets scores and flags); 3 = standard professional training required (officer, examiner, administrator); 4 = minimal training — user interacts via a familiar interface (chat, document review, screen display); 5 = no AI-specific training needed — output is fully self-explanatory to any user.

Q2: How is the AI's output delivered to the user based on the description?
1 = raw model output (probability scores, embeddings, or tabular predictions) with no interface layer; 2 = system-integrated score or flag requiring specialist interpretation; 3 = structured report or processed output needing reading and training to use; 4 = human-readable text, summary, or visual display (highlights on screen, drafted document); 5 = interactive conversational interface or fully self-explanatory display requiring zero additional interpretation.

### Trust

Q1: How well does the documented governance match the stakes of this AI system?
1 = governance severely inadequate — high-stakes or high-impact system with no documented oversight, ATO, or review process; 2 = governance insufficient — some deployment evidence but clear documentation gaps for the risk level; 3 = governance roughly proportionate — oversight implied by deployment or process language for the described stakes; 4 = governance adequate — ATO, validation, or explicit human-in-loop documented appropriate for the system's risk level; 5 = governance clearly sufficient — ATO confirmed, explicit validation and testing language, human review stages documented, PII handled appropriately.

Q2: How transparent is the human oversight over this AI's decisions or recommendations?
1 = no oversight language — fully automated with no mention of review, correction, or escalation pathway; 2 = minimal oversight — automation is the primary mode with only an implied human check; 3 = moderate oversight — a human reviewer exists but their authority to override AI is not stated; 4 = clear oversight — humans review AI outputs before action is taken, with an explicit correction pathway; 5 = strong oversight — AI is purely advisory and humans retain full documented decision authority.

### Explainability

Consult the Classification Type reference table below for typical output transparency characteristics of the AI's type before answering.

Q1: How readable and self-explanatory are this AI's outputs to the intended end user?
1 = opaque numeric scores or raw probability values requiring expert interpretation; 2 = technical labels or flags that require training and domain knowledge to interpret; 3 = structured outputs (ranked lists, classification categories) understandable to trained staff; 4 = human-readable text or visual outputs (summaries, translations, highlights on screen) directly understandable; 5 = complete narrative explanation with explicit rationale visible to the end user alongside every output.

Q2: Does the description indicate that the AI explains why it reached its conclusion?
1 = no — output is a score, flag, or classification with no rationale; 2 = minimal — a category label or confidence score without any explanation; 3 = partial — supporting context or category label that implies reasoning without stating it; 4 = meaningful — rationale or supporting evidence accompanies the recommendation; 5 = full — the AI explicitly explains its reasoning in a way the end user can understand and act on.

---

## Classification Type Reference

Use this table as contextual framing when answering PEOU and Explainability questions. The typical ranges reflect how these AI types commonly deliver outputs to users.

| Classification | Typical PEOU | Typical Explainability | Interface and output characteristics |
|---|---|---|---|
| Generative AI | High (4–5) | High (4–5) | Conversational interface; text outputs are readable; users typically review drafts |
| NLP (chatbot/assistant) | High (4.5–5) | High (4.5–5) | Most user-accessible; chatbot responses are transparent |
| NLP (text processing) | Moderate–high (3.5–4) | Moderate–high (3.5–4) | Summaries, classifications — readable but may lack rationale |
| Computer Vision | Low–moderate (2.5–3) | Moderate (3–3.5) | Outputs need interpretation by trained operators; visual overlays help explainability |
| Classical ML | Low–moderate (2.5–3) | Low–moderate (2.5–3) | Numeric scores; analysts consume outputs; not visible to general users |
| Agentic AI | Moderate–high (3.5–4) | Moderate (3–3.5) | Conversational query interface; outputs depend on agent design |
| Reinforcement Learning | Low (2–2.5) | Low (2–2.5) | Optimization outputs opaque; policy decisions not user-facing |

When `classification` = undefined, scan `problem_solved` and `use_case_name` for type clues: "isolation forest", "neural network", "deep learning" → Classical ML/RL; "summarize", "translate", "NLP" → NLP; "image", "video", "facial recognition" → Computer Vision; "GPT", "LLM", "generative" → Generative AI.

---

## Topic Area Profiles

Topic area modifies the overall interpretation and flags. Adjust Trust scrutiny accordingly:

| Topic Area | PU expectation | Trust scrutiny | Key risk |
|---|---|---|---|
| Law Enforcement | High (security mission) | Very high — bias, due process | Governance gap, demographic bias if has PII/demographics |
| National Security | Very high | Very high | Autonomy risk if automation language present with no review |
| Cybersecurity | High (threat detection) | Moderate–high | Automated detection without review |
| Science | Moderate (research) | Low–moderate | R&D stage, may not have governance |
| Service Delivery | Moderate–high (public-facing) | Moderate | User accessibility, PII handling |
| Admin Functions | Moderate (productivity) | Low | Over-automation of administrative decisions |
| HR | Moderate | Moderate | Bias in hiring/workforce decisions |
| Emergency Management | High (crisis context) | High | Reliability under pressure |
| Procurement/Finance | Moderate | Moderate | Audit requirements |
| IT | Low–moderate | Low | Infrastructure tool |
| Health | High (safety) | Very high | Patient safety, HIPAA |

---

## Handling Sparse Data

**When `problem_solved` is undefined:** Answer all questions conservatively, defaulting to 3 for each unanswerable question. Set confidence = Low. Use `use_case_name` as a proxy — infer from the name alone, with low confidence.

**When `classification` is undefined:** Infer type from `problem_solved` and `use_case_name` text for contextual framing (see Classification Type Reference table). If inference is not possible, treat as mid-range when answering questions.

**When both `benefits` and `system_outputs` are undefined:** Answer PU and Explainability questions conservatively — score both at 3 or below. Note the sparsity in the confidence report.

**When all governance fields (`have_ato`, `has_pii`, `contracting_usage`) are undefined:** Answer Trust Q1 and Q2 conservatively: undefined governance documentation should yield scores of 1–2 for Q1. For deployed systems, Q2 may rise to 2 (operational review implied even without documentation). Do not assume ATO=Yes.

**When any sparse field is undefined:** Do not interpret undefined as "No" — treat it as unknown and apply domain-reasonable defaults as described in this section. A missing `have_ato` does not mean ATO was denied; a missing `has_pii` does not mean there is no PII.

**Minimum viable scoring** (use_case_name + problem_solved only, everything else undefined): Answer PU questions from problem text only; for all other dimensions, answer both questions at 3 (neutral). Confidence = Low. This case is suitable for portfolio flagging only, not for individual decision-making.

---

## End-to-End Scoring Process

Follow these steps for each use case:

**Step 1 — Assess confidence.** Count defined primary and secondary fields and assign a confidence level:
- **High**: 5+ primary/secondary fields defined
- **Medium**: 3–4 primary/secondary fields defined
- **Low**: Fewer than 3 primary/secondary fields defined, or most text fields contain "undefined"

**Step 2 — Note the AI classification type** from `classification`. If undefined, infer from text (see Classification Type Reference table). Use this as contextual framing for PEOU and Explainability questions.

**Step 3 — Score PU.** Answer Q1 and Q2 from `problem_solved`, `benefits`, `is_high_impact`, `development_stage`, `biz_goals`. Final PU = floor((Q1 + Q2) / 2).

**Step 4 — Score PEOU.** Answer Q1 and Q2 informed by classification type and text in `problem_solved`, `system_outputs`, `use_case_name`. Final PEOU = floor((Q1 + Q2) / 2).

**Step 5 — Score Trust.** Answer Q1 and Q2 from `have_ato`, `has_pii`, `development_stage`, `demographic_features`, `is_high_impact`, and any oversight language in text. Final Trust = floor((Q1 + Q2) / 2).

**Step 6 — Score Explainability.** Answer Q1 and Q2 informed by classification type and `system_outputs`/`benefits` text. Final Explainability = floor((Q1 + Q2) / 2).

**Step 7 — Check for risk flags** (see Risk Pattern Flags section). Flag regardless of scores.

**Step 8 — Compute overall TAM score**: simple mean of all 4 final dimension scores. This is a portfolio triage number only; always report individual dimension scores.

---

## Risk Pattern Flags

Apply these flags independently of the numeric scores. A flagged case should be prioritized for human review.

| Flag | Trigger condition |
|---|---|
| GOVERNANCE GAP | `is_high_impact` = High-impact AND `topic_area` = Law Enforcement AND `have_ato` = undefined |
| AUTONOMY RISK | `classification` = Agentic AI AND description lacks oversight/review language AND (`is_high_impact` = High-impact OR `topic_area` = Law Enforcement) |
| DEMOGRAPHIC BIAS RISK | `demographic_features` ≠ [] AND `topic_area` = Law Enforcement — flag regardless of Trust score; demographic data in law enforcement targeting carries inherent bias risk |
| TRANSPARENCY DEFICIT | `is_high_impact` = High-impact AND Explainability ≤ 2 |
| VALUABLE BUT HARD TO USE | PU ≥ 4 AND PEOU ≤ 2 — candidate for UX/training investment |
| PII OVERSIGHT GAP | `has_pii` = Yes AND `have_ato` ≠ Yes AND Trust < 3 |
| AUTOMATED HIGH-STAKES | description contains "automatically runs" or "fully automated" with no review language AND (`is_high_impact` = High-impact OR `topic_area` in [Law Enforcement, Health]) |

---

## Scoring Output Format

For each use case, output a structured record:

```
ID: [use_case_id]
Name: [use_case_name]
Confidence: [High/Medium/Low]

Scores:
  PU:             [1-5]
  PEOU:           [1-5]
  Trust:          [1-5]
  Explainability: [1-5]
  Overall (mean): [1-5]

Flags: [GOVERNANCE GAP | AUTONOMY RISK | DEMOGRAPHIC BIAS RISK | TRANSPARENCY DEFICIT | VALUABLE BUT HARD TO USE | PII OVERSIGHT GAP | AUTOMATED HIGH-STAKES | None]

Scoring rationale:
  PU:             [1 sentence — Q1 and Q2 scores with key evidence]
  PEOU:           [1 sentence — Q1 and Q2 scores with key evidence]
  Trust:          [1 sentence — Q1 and Q2 scores with key evidence]
  Explainability: [1 sentence — Q1 and Q2 scores with key evidence]
```

---

## Limitations

These scores are proxies derived from limited text and categorical metadata. They cannot replace TAM surveys, behavioral data, or direct user research. Use them for:
- Portfolio-level triage (identifying where to focus governance attention)
- Detecting risk pattern clusters (e.g., high-impact law enforcement systems with undefined governance)
- Tracking directional change year-over-year as inventories are updated

Do not use individual scores to approve, reject, or rank specific AI projects without supplementing with additional evidence.
