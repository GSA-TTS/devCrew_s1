---
created: "2026-11-05T00:33:55Z"
updated: "2026-11-05T00:33:55Z"
---

# Source types, screening, extraction fields and classification schemas

## Source types (Document inventory, Type column)

- Primary policy document: legislation (statutes, acts, bills); regulations (administrative rules, codes); executive orders and administrative directives; judicial decisions interpreting the policy; official policy guidance and implementation manuals.
- Secondary analytical source: government reports and evaluations; academic research and systematic reviews; think tank analyses and white papers; international organization assessments; media coverage and stakeholder commentary.
- Contextual and implementation data: budget documents and resource allocations; implementation plans and timelines; monitoring and evaluation reports; performance indicators and outcome data; stakeholder consultation records.

Search terms are defined per source type. Coverage aims at all major policy levers (legislative, regulatory, programmatic) and the full policy cycle (formulation, adoption, implementation, evaluation). Forward and backward citation chaining finds further sources.

## Screening (Document inventory, Screening decision column)

Stage 1 reads title and abstract and excludes the obviously irrelevant. Stage 2 reads the full text of what remains and records a reason for each exclusion.

Inclusion criteria (adapt to the question):
- Directly addresses the policy issue as defined in the research question.
- Issued by an authoritative body with jurisdiction over the policy.
- Covers the timeframe set in the scope.
- Available in an accessible language or with a reliable translation.
- Contains substantive policy content, not only procedure.

Exclusion criteria (adapt to the question):
- Superseded by a later policy, unless the question is historical.
- Draft or proposed but never enacted, unless the question is about policy formulation.
- Tangential: mentions the issue but is not about the policy.
- Duplicate of another publication: keep the most authoritative version.
- Too little detail for analysis, such as a press release where the full regulation text exists.

## Extraction fields per jurisdiction

Extract every included document of one jurisdiction before moving to the next. Record what the text states and what it implies, keep short quotations for interpretive claims, and note the document's purpose and audience.

| Field group | What to record | Feeds |
| :-- | :-- | :-- |
| Policy description | stated objectives and rationale; target population and scope; instruments and mechanisms; implementation responsibilities and timeline; resource allocations and financing | matrix rows Objectives, Target population, Policy instruments, Implementation timeline, Resources |
| Classification | regulatory style; policy modality; scope | matrix row Regulatory style; Patterns and classification |
| Evidence base | research and data cited to justify the policy; evaluation or monitoring provisions; theory of change, stated or implicit | matrix row Evaluation provisions; Lessons, Why column |
| Contextual factors | political and institutional context; stakeholder consultation; adoption pathway and controversies; relation to prior policies | Benefits and drawbacks, Intrinsic or contingent column; Lessons, Where column |
| Implementation and enforcement | administrative structures and capacity; enforcement mechanisms and sanctions; compliance monitoring; flexibility and adaptation provisions | matrix rows Enforcement and Resources |
| Outcomes and evaluation (if available) | outcome indicators; evaluation findings; unintended consequences and spillovers; implementation challenges | Benefits and drawbacks |

For the theory of change, note the assumed causal mechanism, the expected pathway from policy to outcome, critical dependencies and enablers, and likely failure points.

Codes come from the schemas below (deductive) and from content the schemas did not anticipate (inductive). An inductive code that contradicts the schemas is an emerging pattern.

## Classification schemas (Patterns and classification table)

Regulatory style, from two positions:
- Restrictiveness of rules: narrow boundaries (prohibitive) to wide boundaries (permissive).
- Severity of sanctions: high consequences for non-compliance to low or no enforcement.
- Resulting styles: Authority (restrictive rules, severe sanctions), Lenient Authority (restrictive rules, light sanctions), Permissiveness (permissive rules, light sanctions), Punitive Permissiveness (permissive rules, severe sanctions).

Policy modality (one or more):
- Command: direct regulation, mandates.
- Competition: market mechanisms, incentives.
- Communication: information, disclosure.
- Consensus: voluntary agreements, standards.
- Code or architecture: design, defaults, infrastructure.

Scope (one value from each pair): targeted or universal; sectoral or cross-sectoral; macro (overarching framework) or micro (specific interventions).

Type: an ideal type the jurisdiction fits, or a hybrid variant. Example axes: regulatory style (authority-oriented or permissive-oriented); intervention logic (prevention, treatment or harm reduction); governance model (centralized, decentralized or co-governance).

When a policy does not fit one category: create a hybrid category, code each dimension separately instead of forcing one type, or give membership in more than one category, and present the evidence for each reading.
