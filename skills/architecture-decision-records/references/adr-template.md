---
created: "2026-11-04T20:13:13Z"
updated: "2026-11-04T20:13:13Z"
---

# ADR template

Write the sections in this order. Each ADR records one decision, the answer to one well-defined problem; one decision may address several ASRs.

1. Number: a sequential identifier in the form ADR-0042, continuing after the highest number the user already has.
2. Title: present-tense imperative and solution-focused; it starts with the verb of the decision (Use, Adopt, Split) and names what is chosen.
3. Status: one of Proposed, Accepted, Rejected, Deprecated, or Superseded by ADR-nnnn.
4. Date: the creation date and the date of each status change.
5. Author(s): who contributed to the decision.
6. Stakeholders: the teams or people affected or consulted, and whose approval the decision needs.
7. Context: the problem and the forces at play; a Driving ASRs list giving each ASR by its ID with the business need it traces to.
8. Problem statement: the problem defined clearly and measurably.
9. NFRs considered: the quality attributes that drive the decision, each with its measurable criterion.
10. Assumptions and constraints: cost, schedule, existing technology standards or enterprise architecture principles that limit the options or influence the choice.
11. Options considered: two or three genuinely viable alternatives. For each: a description, Pros (advantages and benefits), Cons (disadvantages, risks and costs) and its cost (recurring and implementation).
12. Decision and rationale: the chosen option stated without ambiguity; why it was chosen over the others, referring to the pros and cons above and to the driving ASRs; an Evidence list (measurements, benchmarks, cost analysis, standards or research, each cited); a Trade-off acceptance list naming each con accepted and how it is mitigated.
13. Consequences: Positive and Negative lists; technical impact (effects on other systems, new dependencies, technical debt), operational impact (deployment, monitoring, maintenance), security impact, and the future decisions this one now requires; Risks, each with its mitigation; the timeline and the resources needed.
14. Fitness functions: at least two measurable validation criteria, each made from an ASR's measurable criterion: a name, a type (performance, compliance, reliability or another quality attribute), what is measured and how it would be checked automatically, the threshold, and how often it is checked.
15. Related decisions and artifacts: other ADRs this one depends on, conflicts with or supersedes, and the requirement documents or external standards it relates to.
