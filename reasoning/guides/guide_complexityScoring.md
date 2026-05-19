# Guide: AI Project Complexity Scoring from Brief Descriptions

## Purpose

This guide enables any AI agent to assign complexity scores across 8 dimensions to AI use cases described only in brief text (~5 sentences). It synthesizes the detailed dimension-specific rubrics developed for richly documented use cases into a concise inference process suited for sparse inputs such as government AI inventory records. Please pay close attention to the guide's mechanisms and their limitations.

Scores are 1–5 per dimension (1 = Simple, 5 = Extremely complex). A composite score (average of 8 dimensions) characterizes overall project complexity.

---

## Framework: 8 Dimensions

| # | Dimension | What it measures |
|---|-----------|-----------------|
| 1 | Reasoning | Depth and type of inference the AI must perform |
| 2 | Orchestration | How agents/components coordinate to complete work |
| 3 | Memory | How information is stored, retrieved, and persisted |
| 4 | Perception | Input modalities, signal quality, real-time needs |
| 5 | Tool Calling | External capabilities invoked; side-effect severity |
| 6 | Integration | External systems connected; governance constraints |
| 7 | Error Handling | Failure detection, propagation scope, recovery complexity |
| 8 | Resilience | System's ability to stay functional under failure or attack |

---

## Step-by-Step Process

### Step 1 — Gather all available text

Collect and concatenate text from these fields in priority order:

| Priority | Field | Availability |
|----------|-------|-------------|
| High | `use_case_name` | ~100% |
| High | `problem_solved` | ~84% |
| High | `benefits` | ~82% |
| High | `system_outputs` | ~79% |
| Medium | `classification` (Classical ML, Generative AI, NLP, Computer Vision, Agentic AI, RL) | ~82% |
| Medium | `topic_area` | ~83% |
| Medium | `is_high_impact` | ~85% |
| Medium | `development_stage` (Deployed, Pre-deployment, Pilot, Retired) | ~91% |
| Medium | `agency_bureau` | ~98% |

Before scoring, count the combined word count. Use it to calibrate confidence (Step 6).

---

### Step 2 — Set a baseline from classification

If `classification` is available, use these starting baselines (score vector: Reasoning, Orchestration, Memory, Perception, Tool Calling, Integration, Error Handling, Resilience):

| Classification | Baseline vector |
|----------------|----------------|
| Classical ML | 2, 1, 1, 2, 1, 2, 2, 1 |
| NLP | 2, 1, 1, 2, 1, 2, 2, 1 |
| Computer Vision | 2, 1, 1, 3, 1, 2, 2, 1 |
| Generative AI | 3, 2, 2, 2, 2, 2, 3, 2 |
| Agentic AI | 3, 3, 3, 2, 3, 3, 3, 3 |
| Reinforcement Learning | 3, 2, 2, 2, 1, 2, 2, 2 |
| undefined | 2, 1, 1, 2, 1, 2, 2, 1 |

These baselines represent the modal complexity for the technology type and are adjusted upward or downward in Steps 3 and 4.

---

### Step 3 — Dimension scoring

Score each dimension by answering Q1 and Q2 based on the full description. If the description lacks enough information to answer a question, assign the baseline score from Step 2 for that question.

Final score per dimension = floor((Q1 + Q2) / 2).

Example: Q1=3, Q2=2 → floor((3+2)/2) = floor(2.5) = 2.
Example: Q1=4, Q2=4 → floor((4+4)/2) = floor(4.0) = 4.

---

#### Reasoning

Q1: How many distinct reasoning steps does the AI perform between receiving input and producing its output?
1 = one step (classify, look up, or extract a field); 2 = two steps (retrieve then evaluate against rules or criteria); 3 = three or more steps with conditional logic or reasoning under uncertainty; 4 = multi-step planning, optimization under constraints, or domain-expert-level analysis; 5 = recursive reasoning, novel hypothesis generation, or adversarial/game-theoretic analysis.

Q2: What type of reasoning best describes the core AI task?
1 = pattern matching or keyword rules; 2 = template evaluation or rule checking against known criteria; 3 = probabilistic inference or multi-criteria scoring with uncertain inputs; 4 = causal, counterfactual, or constrained optimization reasoning; 5 = game-theoretic, scientific discovery, or reasoning with fundamentally incomplete information.

---

#### Orchestration

Q1: How many distinct agents or coordinating components does this system appear to have?
1 = single model or tool with no handoffs; 2 = two components in a fixed sequence; 3 = three to five components with conditional routing or a supervisor; 4 = six or more components with dynamic or LLM-driven delegation; 5 = self-organizing, competing, or peer-to-peer agents with no fixed topology.

Q2: How dynamic is the coordination logic between components?
1 = fixed single pipeline, no branching; 2 = simple retry or fixed handoff; 3 = conditional routing based on intermediate output or state; 4 = LLM-driven dynamic routing or role assignment at runtime; 5 = emergent coordination—agents negotiate, compete, or self-organize without a fixed controller.

---

#### Memory

Q1: Over what time span and scope must the AI retain and reuse information?
1 = each request is fully independent—no state retained between calls; 2 = context is maintained within a single session or conversation; 3 = information persists across sessions for compliance, audit trail, or user personalization; 4 = memory is shared and synchronized across multiple agents or organizational teams; 5 = memory is federated across organizational boundaries with strict provenance or compartmentalization controls.

Q2: How sophisticated is the retrieval mechanism needed to access stored information?
1 = no retrieval—fully stateless; 2 = simple lookup from a static store (key-value or fixed corpus); 3 = dynamic search against an updatable knowledge base (vector search or structured queries); 4 = hybrid retrieval with consistency or concurrency requirements; 5 = federated retrieval with cryptographic provenance or adversarial-poisoning defenses.

---

#### Perception

Q1: What types of input data does the system process?
1 = clean structured data or simple text forms with fixed schema; 2 = unstructured documents or a single clean modality (text, audio, or image); 3 = multiple document formats or real-time text streams from heterogeneous sources; 4 = two or more modalities that must be fused (image + text, or sensor telemetry); 5 = adversarial or safety-critical multi-modal inputs in real time with no human fallback.

Q2: How strict are the latency requirements for processing inputs?
1 = batch—hours of delay are acceptable; 2 = near-real-time—minutes of delay are acceptable; 3 = soft real-time—seconds of delay are tolerable with graceful degradation; 4 = hard real-time—sub-second processing with operational consequences for delay; 5 = mission-critical real-time—failure to process on time has safety or irreversible consequences.

---

#### Tool Calling

Q1: What is the most consequential action the AI performs through external tools or APIs?
1 = read-only retrieval or report generation—humans review all outputs before any action; 2 = aggregation across a few systems with minor automated outputs; 3 = writing results, sending notifications, or updating records in operational systems; 4 = controlling physical or digital systems, accessing privileged data, or executing hard-to-reverse digital actions; 5 = autonomous physical actions, infrastructure modification, or irreversible actions without a human approval gate.

Q2: How does the system determine which tools to invoke?
1 = hardcoded single tool call; 2 = fixed sequence of 2–5 tools; 3 = conditional tool selection based on intermediate results; 4 = LLM-driven dynamic selection from a tool registry at runtime; 5 = open-ended tool discovery at runtime or adversarial tool use with no predefined set.

---

#### Integration

Q1: How many distinct external systems, databases, or services does this AI use case connect to?
1 = one internal system; 2 = two to four systems within a single agency; 3 = five to ten systems including federal registries or compliance platforms; 4 = ten to fifteen systems spanning multiple bureaus or agencies; 5 = fifteen or more systems across organizational boundaries with conflicting governance or classification levels.

Q2: How complex are the data governance or regulatory constraints on the data flows?
1 = no governance constraints—internal data only; 2 = standard agency security requirements; 3 = federal compliance such as FedRAMP, ATO, or FISMA; 4 = multi-agency data sharing agreements with strict provenance requirements; 5 = cross-jurisdictional integration with conflicting regulatory regimes or classified-data handling.

---

#### Error Handling

Q1: What is the worst-case consequence of an undetected error in this system's output?
1 = a human reviewer catches all errors before any action is taken; 2 = a minor inconvenience that is easily corrected after the fact; 3 = a compliance or audit finding requiring remediation; 4 = an automated action is taken that is difficult to reverse or has significant operational impact; 5 = a safety-critical, mission-critical, or irreversible real-world consequence.

Q2: How sophisticated must the error detection be to catch failures in this system?
1 = explicit HTTP or API error codes suffice; 2 = input validation and output confidence thresholds; 3 = semantic error detection in AI-generated outputs (hallucination detection, output plausibility checks); 4 = silent failure detection across distributed components or cascading-error prevention; 5 = adversarial injection defense, Byzantine fault detection, or formal verification of correctness.

Note: Error Handling often correlates with Resilience. If one score is high, verify whether the other should also be high.

---

#### Resilience

Q1: How much downtime is operationally acceptable if this system fails?
1 = days—batch or pilot system with no SLA; 2 = same day—daily operational tool; 3 = a few hours—agency-critical tool with a modest uptime requirement; 4 = minutes—mission-critical system requiring 99.9%+ uptime; 5 = near-zero—safety-critical or autonomous system where downtime directly risks human safety or mission failure.

Q2: Can a human intervene to restart or recover the system when it fails?
1 = yes—human restart is the primary and expected recovery method; 2 = yes—but automated retry reduces the frequency of human involvement; 3 = yes—automated checkpoint recovery handles most failures, with human oversight available; 4 = yes—but the system must largely self-recover, with humans involved only for major outages; 5 = no—no human intervention is possible and the system must fully self-reconstitute autonomously.


---

### Step 4 — Apply cross-cutting modifiers

After dimension-specific scoring, apply these global adjustments:

| Condition | Adjustment |
|-----------|-----------|
| `is_high_impact` = "High-impact" | +1 on Error Handling and Resilience (floor at current score) |
| `development_stage` = "Pilot" | Cap Orchestration and Resilience at 3 unless there are strong counter-signals |
| `classification` = "Agentic AI" | Raise Orchestration and Tool Calling to minimum 3 |
| `classification` = "Reinforcement Learning" | Raise Reasoning to minimum 3 |
| `classification` = "Computer Vision" | Raise Perception to minimum 3 |
| Topic involves "national security", "defense", "law enforcement" | Raise Resilience and Error Handling to minimum 3 |
| Topic involves "safety-critical" or "clinical" | Raise Error Handling and Resilience to minimum 4 |
| "autonomous" + no human-in-loop language | Raise Error Handling and Resilience to minimum 4; raise Orchestration to minimum 3 |
| "real-time" + operational context | Raise Resilience to minimum 3 (the question mechanism already captures higher levels) |

Apply modifiers in the order listed; they do not stack on each other unless independently triggered.

---

### Step 5 — Compute composite score

Composite = arithmetic mean of all 8 dimension scores, rounded to one decimal place.

| Composite | Label |
|-----------|-------|
| 1.0–1.5 | Minimal — simple lookup, classification, or batch report |
| 1.6–2.5 | Low — basic pipeline with limited scope |
| 2.6–3.5 | Moderate — multi-step workflow with real-world integration |
| 3.6–4.5 | High — mission-critical, multi-system, with automation |
| 4.6–5.0 | Extreme — fully autonomous, adversarial, or safety-critical |

---

### Step 6 — Assign confidence level

Count "informed dimensions" — dimensions where floor((Q1+Q2)/2) differs from the Step 2 baseline.

| Condition | Confidence |
|-----------|-----------|
| Combined text ≥ 100 words AND ≥ 5 informed dimensions | High |
| Combined text 50–99 words OR 3–4 informed dimensions | Medium |
| Combined text < 50 words OR ≤ 2 informed dimensions | Low |

For Low confidence, report scores as ranges (e.g., "2–3") rather than point estimates. Flag which dimensions had no signal as "inferred from baseline only."

---

### Step 7 — Produce the score record

For each use case, output:

```
ID: [id]
Name: [use_case_name]
Confidence: High / Medium / Low
Signals used: [list the key phrases that drove non-baseline scores]

Dimension Scores:
  Reasoning:      [1–5]
  Orchestration:  [1–5]
  Memory:         [1–5]
  Perception:     [1–5]
  Tool Calling:   [1–5]
  Integration:    [1–5]
  Error Handling: [1–5]
  Resilience:     [1–5]

Composite: [avg] — [Label]

Uncertainty flags: [list dimensions scored from baseline only]
```

---

## Key Principles for Sparse Inputs

1. **Never score higher than the text supports.** When a dimension has no signal, use the baseline. Overestimating from vague language inflates all scores and erodes differentiation.

2. **Autonomy is the strongest amplifier.** Any combination of "autonomous" + absence of human-review language pushes most dimensions up by at least 1. Conversely, "advisory", "recommends", or "analyst reviews" caps Tool Calling, Error Handling, and Orchestration at low levels.

3. **Domain context carries prior probability.** Space, military, clinical, and national security domains have higher operational stakes, which systematically raises Resilience and Error Handling floors. Research/pilot projects lower Resilience and Orchestration ceilings.

4. **Correlated dimensions.** Orchestration and Tool Calling tend to move together. Error Handling and Resilience tend to move together. If one is high, check whether the other should also be high before finalizing.

5. **Report uncertainty explicitly.** A Low-confidence score is not a failure — it is honest. Flag the dimensions inferred from baseline only so downstream consumers know where additional research is needed.

6. **Do not hallucinate specifics.** If the description does not mention multi-agent coordination, do not infer it. If the number of integrated systems is not stated, do not assume a count. Use the lowest defensible score when ambiguous.

---
