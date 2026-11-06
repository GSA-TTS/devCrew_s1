---
created: "2026-11-04T19:14:33Z"
updated: "2026-11-04T19:14:33Z"
---

# Dimension anchors, classification types and topic profiles

Each dimension is scored by answering two questions, Q1 and Q2, each an integer from 1 to 5. Dimension score = floor((Q1 + Q2) / 2). A question that the available text cannot answer is scored 3. Scale meaning: 5 strong evidence, 3 neutral, mixed or inferred default, 1 clear absence or critical gap.

## Perceived Usefulness (PU)

Evidence fields: problem solved, benefits, high-impact flag, development stage, business goals.

Q1. How directly and tangibly does the AI benefit the end users who work with it every day?
- 1: no visible user benefit; only an organizational or management benefit is described.
- 2: indirect benefit; efficiency for the agency, not clearly for the individual user.
- 3: clear user benefit; it lightens a specific task or improves the quality of users' work.
- 4: significant benefit; it substantially cuts time, risk or effort on high-frequency tasks.
- 5: essential benefit; it addresses safety or mission-critical outcomes, or prevents serious operational failure.

Q2. How specific and credible are the outcomes in the problem or benefits text?
- 1: vague or circular; the benefit restates the problem with no measurable claim.
- 2: generic improvement wording with no claim that could be checked.
- 3: a concrete outcome, not quantified.
- 4: a quantified or clearly checkable impact (time saved, error rate reduced, inspections reduced).
- 5: a quantified impact with mission-critical or safety significance.

## Perceived Ease of Use (PEOU)

Evidence fields: classification type (table below), problem solved, system outputs, use case name.

Q1. How much training or domain expertise does the primary end user need to work with the AI?
- 1: advanced technical expertise (data scientist, quantitative analyst, machine learning engineer).
- 2: domain specialist (an analyst or trained operator who interprets scores and flags).
- 3: standard professional training (officer, examiner, administrator).
- 4: minimal training; the user works through a familiar interface (chat, document review, screen display).
- 5: no AI-specific training; the output explains itself to any user.

Q2. How is the output delivered to the user?
- 1: raw model output (probabilities, embeddings, tabular predictions) with no interface layer.
- 2: a score or flag inside another system that needs specialist interpretation.
- 3: a structured report or processed output that needs reading and training to use.
- 4: human-readable text, a summary or a visual display (on-screen highlights, a drafted document).
- 5: an interactive conversational interface or a display that needs no further interpretation.

## Trust

Evidence fields: ATO status, PII, development stage, demographic features, high-impact flag, and any oversight wording in the text. Apply the topic profile's trust scrutiny (table below).

Q1. How well does the documented governance match the stakes of the system?
- 1: severely inadequate; a high-stakes or high-impact system with no documented oversight, ATO or review process.
- 2: insufficient; some deployment evidence but clear documentation gaps for the risk level.
- 3: roughly proportionate; oversight implied by deployment or process wording for the stated stakes.
- 4: adequate; ATO, validation or an explicit human in the loop documented, fitting the risk level.
- 5: clearly sufficient; ATO confirmed, explicit validation and testing, documented human review stages, PII handled appropriately.

Q2. How visible is human oversight of the AI's decisions or recommendations?
- 1: none; fully automated, with no review, correction or escalation path mentioned.
- 2: minimal; automation is the main mode and a human check is only implied.
- 3: moderate; a human reviewer exists, but their authority to override the AI is not stated.
- 4: clear; humans review outputs before action, with an explicit correction path.
- 5: strong; the AI is advisory only and humans keep full, documented decision authority.

## Explainability

Evidence fields: classification type (table below), system outputs, benefits.

Q1. How readable and self-explanatory are the outputs to the intended end user?
- 1: opaque numeric scores or raw probabilities that need an expert to interpret.
- 2: technical labels or flags that need training and domain knowledge.
- 3: structured outputs (ranked lists, categories) that trained staff understand.
- 4: human-readable text or visuals (summaries, translations, on-screen highlights) understood directly.
- 5: a full narrative explanation with its rationale shown to the user next to every output.

Q2. Does the description show that the AI explains why it reached its conclusion?
- 1: no; the output is a score, flag or class with no rationale.
- 2: minimal; a category label or confidence score without explanation.
- 3: partial; supporting context or a label that implies reasoning without stating it.
- 4: meaningful; a rationale or supporting evidence comes with the recommendation.
- 5: full; the AI states its reasoning in a way the user can understand and act on.

## Classification type reference

Context for the PEOU and Explainability questions: how each AI type usually delivers outputs. It frames the answers; it does not replace them.

| Classification | Typical PEOU | Typical Explainability | Interface and outputs |
|---|---|---|---|
| Generative AI | High (4 to 5) | High (4 to 5) | Conversational interface; readable text; users usually review drafts |
| NLP, chatbot or assistant | High (4.5 to 5) | High (4.5 to 5) | Most accessible to users; chatbot answers are transparent |
| NLP, text processing | Moderate to high (3.5 to 4) | Moderate to high (3.5 to 4) | Summaries and classifications; readable but may lack rationale |
| Computer vision | Low to moderate (2.5 to 3) | Moderate (3 to 3.5) | Trained operators interpret outputs; visual overlays help |
| Classical ML | Low to moderate (2.5 to 3) | Low to moderate (2.5 to 3) | Numeric scores read by analysts; not seen by general users |
| Agentic AI | Moderate to high (3.5 to 4) | Moderate (3 to 3.5) | Conversational query interface; outputs depend on the agent's design |
| Reinforcement learning | Low (2 to 2.5) | Low (2 to 2.5) | Opaque optimization outputs; policy decisions not user-facing |

When the classification is undefined, look for type clues in the problem text and the name:
- isolation forest, neural network, deep learning: Classical ML or reinforcement learning.
- summarize, translate, NLP: NLP.
- image, video, facial recognition: computer vision.
- GPT, LLM, generative: Generative AI.
- No clue: treat the type as mid-range when answering the questions.

## Topic area profiles

The topic area adjusts interpretation, Trust scrutiny and the risks to watch.

| Topic area | PU expectation | Trust scrutiny | Key risk |
|---|---|---|---|
| Law Enforcement | High (security mission) | Very high: bias, due process | Governance gap; demographic bias when PII or demographics are present |
| National Security | Very high | Very high | Autonomy, when automation wording has no review |
| Cybersecurity | High (threat detection) | Moderate to high | Automated detection without review |
| Science | Moderate (research) | Low to moderate | Research stage; governance may be absent |
| Service Delivery | Moderate to high (public-facing) | Moderate | User accessibility; PII handling |
| Admin Functions | Moderate (productivity) | Low | Over-automation of administrative decisions |
| HR | Moderate | Moderate | Bias in hiring or workforce decisions |
| Emergency Management | High (crisis context) | High | Reliability under pressure |
| Procurement and Finance | Moderate | Moderate | Audit requirements |
| IT | Low to moderate | Low | Infrastructure tool |
| Health | High (safety) | Very high | Patient safety; health privacy law |
