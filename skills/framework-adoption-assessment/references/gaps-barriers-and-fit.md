---
created: "2026-11-04T23:07:21Z"
updated: "2026-11-04T23:07:21Z"
---

# Gap types, gap priority, barrier categories, fit findings and cross-mapping

## Gap types (Gap type column)

- Performance: the capability exists but does not meet the framework's performance standard (monitoring exists, detection is slower than required).
- Process: a required process is not documented, standardized or consistently followed (assessment required quarterly, done yearly).
- Capability: a required capability is absent (penetration testing required, none exists).
- Skill: staff lack the expertise a requirement needs.
- Technology: required tools or infrastructure are not available (automated configuration management required, only manual processes).
- Documentation: a required policy, procedure or plan does not exist.

## Gap priority (Priority column, from Impact and Effort)

| Impact / Effort | Low effort | Medium effort | High effort |
|---|---|---|---|
| High impact | Quick win (1) | Strategic project (2) | Major initiative (3) |
| Medium impact | Easy improvement (2) | Consider (3) | Reconsider (4) |
| Low impact | Low priority (4) | Avoid (5) | Avoid (5) |

## Barrier categories (Category column of the barrier table)

1. Organizational: weak sponsorship or unclear accountability; misalignment with strategy or unclear value; budget, staff or time constraints; cultural resistance.
2. Technical: framework complexity or overly prescriptive requirements; poor fit with existing or legacy systems; infrastructure or tool gaps; technical debt.
3. Process: disruption of established workflows; undocumented or ad hoc processes; unclear implementation guidance; weak change management or no pilot.
4. Knowledge and skills: missing expertise; learning curve and terminology; inadequate training; reliance on key individuals.
5. Stakeholder and communication: low involvement or buy-in; low awareness or misconceptions about requirements; poor channels or inconsistent messages; end-user resistance or fear of added workload.
6. External and environmental: unclear or changing regulation; market and time pressure; cost pressure or uncertain return; limited vendor support or tools.

## Fit findings (Dimension and Resolution columns)

| Dimension | What it means | Resolution |
|---|---|---|
| Coverage insufficiency | The framework does not address a critical need (for example data security covered, AI ethics not) | Supplement with controls from another source |
| Specificity insufficiency | Requirements too vague to implement | Write detailed implementation standards |
| Contextual misfit | Framework assumes a different context (centralized IT where the organization is federated) | Tailor through a context-specific profile |
| Technical inappropriateness | A requirement is obsolete or infeasible | Document an exception with compensating controls or an updated requirement |
| Scale misalignment | Built for a different size of organization | Apply selectively with risk-based scoping |
| Performance inadequacy | The framework's standard is too weak for the organization's risk profile | Set a more stringent organizational standard |

Needs with match class NM in the mapping are coverage findings. Each finding names its evidence and at least one resolution or alternative framework.

## Tailoring (Tailoring field of the recommendation)

- Control selection: which controls apply given scope, technology and risk profile; the reason for each exclusion; optional controls to add; a current profile and a target profile.
- Control statements: organizational wording; added specificity; frequency adjusted to risk; the tools and processes that implement them.
- Evidence: acceptable evidence per control and existing artifacts that already satisfy it.
- Process: where framework activities fit existing workflows, with roles and timing.

Tailoring keeps the framework's compliance intent and auditability.

## Cross-mapping (when several frameworks must be satisfied)

Mapping strength between a pair of controls:

- Direct: requirements identical; the same evidence satisfies both.
- Strong: objectives aligned; implementation needs minor adaptation.
- Weak: related in concept, with significant differences in requirements.
- None: no meaningful relationship.

Compare control objectives, technical requirements and evidence requirements to classify a pair. Prefer an official crosswalk or the framework's informative references when one exists. Report the overlap percentage for each framework pair, the common controls, the controls unique to each framework, and a unified control set.

When requirements conflict: state the exact conflicting requirements; decide whether it is a true conflict or a difference in specificity or evidence format; look for one implementation that satisfies both; where they differ in rigor, apply the more stringent one; where they truly conflict, use compensating controls that meet the intent of both, or present it to the governance body for a risk-based decision; record the approach and its reason.
