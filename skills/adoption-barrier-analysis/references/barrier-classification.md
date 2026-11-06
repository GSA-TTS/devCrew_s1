---
created: "2026-11-04T19:29:29Z"
updated: "2026-11-04T19:35:11Z"
---

# Barrier classification, comparison and root causes

## Four classification dimensions

Assign every barrier one value on each dimension.

1. Type (by determinant)
   - Individual-cognitive: knowledge gaps, beliefs, attitudes, perceptions.
   - Individual-affective: emotions, fear, anxiety, low motivation.
   - Individual-behavioural: skill deficits, clash with habits, low self-efficacy.
   - Social-normative: perceived norms, social pressure, peer influence.
   - Social-structural: access limits, resource availability, lack of social support.
   - Organizational: leadership commitment, resource allocation, culture, climate.
   - Systemic: policies, regulations, infrastructure, economic incentives.
2. Effect mechanism
   - Blocking: prevents adoption outright.
   - Slowing: delays adoption without preventing it.
   - Reducing: lowers the quality or depth of use among adopters.
   - Cascading: triggers other barriers.
3. Scope: general (any context), sector-specific, or context-dependent (only under certain conditions).
4. Modifiability: fixed (cannot be changed, such as a regulatory mandate), resistant (changes only with substantial effort, such as organizational culture), malleable (yields to a targeted intervention, such as training).

Each barrier must fit exactly one category per dimension; if a barrier seems to fit two types, split it into two barriers.

## Adopter and non-adopter comparison

Determinants to compare between adopters (people already doing the practice) and non-adopters:

| Determinant | What to ask about |
| :-- | :-- |
| Knowledge | factual understanding of the practice |
| Attitudes | general favourability toward it |
| Beliefs | specific perceptions of benefits, risks, compatibility |
| Emotions | fear, excitement, anxiety |
| Skills | perceived and actual ability to do it |
| Norms | perceived expectations and approval of others |
| Access | resources, support, infrastructure |
| Habits | fit with existing routines |

With data:
1. Use the same questions for both groups.
2. For each determinant, compute delta = P(adopters) minus P(non-adopters), the difference in the share giving the positive response, in percentage points.
3. Flag a determinant as a salient barrier when the absolute delta exceeds 20 percentage points; when counts allow, also require a chi-square p value below 0.05.
4. Rank flagged determinants by absolute delta, largest first.
5. State the group sizes. The design calls for about 45 per group, with a minimum of 40 per group; below 40 per group, label the comparison indicative (the label is a convention of this skill).

Without data, give the comparison design instead: who counts as an adopter, who counts as a non-adopter, about 45 of each, one identical questionnaire covering the eight determinants above.

## Eliciting barriers without survey data

Probe five domains, using the user's description, interview notes, complaints or support tickets:

1. The practice itself: complexity, relative advantage, adaptability, whether it can be tried on a small scale.
2. Outer setting: external policies, incentives, partnerships, competition.
3. Inner setting: culture, readiness, resources, internal communication.
4. Individuals: knowledge, beliefs, self-efficacy, motivation, stage of change.
5. Implementation process: planning, engagement, execution, evaluation.

Count how often each barrier is mentioned per stakeholder group (decision-makers, implementers, recipients) when the material allows.

## Root causes

Use one method per priority barrier.

- Five whys: start from the barrier as stated, ask why it exists up to five times, record each layer, stop at the deepest cause that someone can act on.
- Fishbone: put the barrier as the effect and list contributing causes under six headings: people (skills, motivation, capacity), methods (process and procedure), machines (technology and infrastructure), materials (resource availability and quality), measurement (data, monitoring, feedback), environment (external context).
- Target, hazard, barrier: the target is who should adopt, the hazard is the consequence of not adopting, the barriers are the controls in place or missing between them; ask which controls failed, why, and what alternatives exist.

A root cause is accepted when it is distinct from the symptom, specific (names a process, resource, rule or person group), and actionable (an intervention can be matched to it). "Culture" or "resistance to change" alone is a symptom; go one layer deeper.

Write each chain as: symptom, then intermediate causes, then root cause.

## How a barrier affects adoption

For each barrier, estimate where data allows:
- Blocking rate: share of the target population for whom it prevents adoption.
- Delay: average time it adds before adoption, for those who do adopt.
- Reduction: drop in depth or quality of use it causes.

Blocking strength can be expressed as an adoption rate ratio: adoption rate where the barrier is absent divided by the rate where it is present; a ratio well above 1 means strong blocking.

## Interactions and cascades

- For each pair of barriers, record whether one raises, lowers or leaves unchanged the likelihood or severity of the other.
- Mark reinforcing loops (barriers that feed each other) and balancing loops (barriers that offset each other).
- Write cascade paths as arrows, for example: no hands-on practice, then low confidence, then avoidance of the tool, then colleagues see it as unused, then resistance to the next change.
- The first link of a cascade is a leverage point: an intervention there removes the barriers downstream.

## Sector patterns

Check these common barriers first when the sector matches:
- Healthcare: clinical workflow disruption, doubts about the evidence, reimbursement rules. Weight patient safety and regulatory compliance in prioritization.
- Technology and software: usability, integration complexity, resistance to change management. Weight user experience and technical feasibility.
- Policy implementation: political resistance, resource constraints, coordination between levels of government. Expect longer timelines for barrier reduction.
- Education: teacher beliefs and self-efficacy, resource availability, administrative support. Professional development is the usual intervention; involve teachers in its design.
