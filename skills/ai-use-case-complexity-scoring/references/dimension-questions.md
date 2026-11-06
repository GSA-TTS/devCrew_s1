---
created: "2026-11-04T19:06:26Z"
updated: "2026-11-04T19:06:26Z"
---

# Dimension questions: Q1 and Q2 scales

Answer Q1 and Q2 for each dimension from the use case's combined text. If the text gives no evidence for a question, that question takes the dimension's baseline value. Dimension score = floor((Q1 + Q2) / 2); for example Q1 = 3, Q2 = 2 gives floor(2.5) = 2.

## 1. Reasoning (depth and type of inference)

Q1. How many distinct reasoning steps lie between input and output?
1 one step (classify, look up or extract a field); 2 two steps (retrieve, then evaluate against rules or criteria); 3 three or more steps with conditional logic or reasoning under uncertainty; 4 multi-step planning, optimization under constraints or domain-expert-level analysis; 5 recursive reasoning, novel hypothesis generation or adversarial / game-theoretic analysis.

Q2. What type of reasoning is the core task?
1 pattern matching or keyword rules; 2 template evaluation or rule checking against known criteria; 3 probabilistic inference or multi-criteria scoring with uncertain inputs; 4 causal, counterfactual or constrained-optimization reasoning; 5 game-theoretic, scientific discovery or reasoning with fundamentally incomplete information.

## 2. Orchestration (how components coordinate)

Q1. How many distinct agents or coordinating components does the system appear to have?
1 single model or tool, no handoffs; 2 two components in a fixed sequence; 3 three to five components with conditional routing or a supervisor; 4 six or more components with dynamic or LLM-driven delegation; 5 self-organizing, competing or peer-to-peer agents with no fixed topology.

Q2. How dynamic is the coordination logic?
1 fixed single pipeline, no branching; 2 simple retry or fixed handoff; 3 conditional routing on intermediate output or state; 4 LLM-driven dynamic routing or role assignment at runtime; 5 emergent coordination: agents negotiate, compete or self-organize without a fixed controller.

## 3. Memory (storage, retrieval, persistence)

Q1. Over what time span and scope must information be retained and reused?
1 each request independent, no state kept; 2 context kept within one session or conversation; 3 persists across sessions for compliance, audit trail or personalization; 4 shared and synchronized across several agents or teams; 5 federated across organizational boundaries with strict provenance or compartmentalization controls.

Q2. How sophisticated is the retrieval?
1 none, fully stateless; 2 simple lookup from a static store (key-value or fixed corpus); 3 dynamic search of an updatable knowledge base (vector search or structured queries); 4 hybrid retrieval with consistency or concurrency requirements; 5 federated retrieval with cryptographic provenance or defenses against adversarial poisoning.

## 4. Perception (input modalities, signal quality, timing)

Q1. What input data does the system process?
1 clean structured data or simple fixed-schema text forms; 2 unstructured documents or one clean modality (text, audio or image); 3 several document formats or real-time text streams from heterogeneous sources; 4 two or more modalities that must be fused (image + text, or sensor telemetry); 5 adversarial or safety-critical multi-modal inputs in real time with no human fallback.

Q2. How strict is the latency requirement?
1 batch, hours of delay acceptable; 2 near-real-time, minutes acceptable; 3 soft real-time, seconds tolerable with graceful degradation; 4 hard real-time, sub-second with operational consequences for delay; 5 mission-critical real-time, late processing has safety or irreversible consequences.

## 5. Tool Calling (external capabilities, side-effect severity)

Q1. What is the most consequential action taken through external tools or APIs?
1 read-only retrieval or report generation, humans review all outputs before any action; 2 aggregation across a few systems with minor automated outputs; 3 writing results, sending notifications or updating records in operational systems; 4 controlling physical or digital systems, accessing privileged data or executing hard-to-reverse digital actions; 5 autonomous physical actions, infrastructure modification or irreversible actions with no human approval gate.

Q2. How are tools chosen?
1 one hardcoded tool call; 2 fixed sequence of 2 to 5 tools; 3 conditional selection based on intermediate results; 4 LLM-driven dynamic selection from a tool registry at runtime; 5 open-ended tool discovery at runtime or adversarial tool use with no predefined set.

## 6. Integration (external systems, governance)

Q1. How many distinct external systems, databases or services are connected?
1 one internal system; 2 two to four systems within one agency; 3 five to ten systems, including federal registries or compliance platforms; 4 ten to fifteen systems across several bureaus or agencies; 5 fifteen or more systems across organizational boundaries with conflicting governance or classification levels.

Q2. How complex are the governance or regulatory constraints on the data flows?
1 none, internal data only; 2 standard agency security requirements; 3 federal compliance such as FedRAMP, ATO or FISMA; 4 multi-agency data-sharing agreements with strict provenance requirements; 5 cross-jurisdictional integration with conflicting regulatory regimes or classified-data handling.

## 7. Error Handling (detection, propagation, recovery)

Q1. What is the worst-case consequence of an undetected output error?
1 a human reviewer catches all errors before any action; 2 minor inconvenience, easily corrected afterwards; 3 a compliance or audit finding requiring remediation; 4 an automated action that is hard to reverse or has significant operational impact; 5 a safety-critical, mission-critical or irreversible real-world consequence.

Q2. How sophisticated must error detection be?
1 explicit HTTP or API error codes suffice; 2 input validation and output confidence thresholds; 3 semantic error detection in AI-generated output (hallucination detection, plausibility checks); 4 silent-failure detection across distributed components or cascading-error prevention; 5 adversarial-injection defense, Byzantine fault detection or formal verification.

Error Handling and Resilience tend to move together: if one is high, check whether the other should be too.

## 8. Resilience (staying functional under failure or attack)

Q1. How much downtime is operationally acceptable?
1 days: batch or pilot system with no SLA; 2 same day: daily operational tool; 3 a few hours: agency-critical tool with a modest uptime requirement; 4 minutes: mission-critical, 99.9%+ uptime; 5 near zero: safety-critical or autonomous system where downtime directly risks human safety or mission failure.

Q2. Can a human restart or recover the system?
1 yes, human restart is the expected recovery; 2 yes, but automated retry reduces human involvement; 3 yes, automated checkpoint recovery handles most failures with human oversight available; 4 yes, but the system must largely self-recover, humans only for major outages; 5 no, the system must fully self-reconstitute autonomously.
