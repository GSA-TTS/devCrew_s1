---
created: "2026-11-04T23:09:57Z"
updated: "2026-11-04T23:09:57Z"
---

# Unique element profile: fields and allowed values

Write one profile per element of A \ B, headed by its ID and name, with the fields below in this order, grouped under Mechanism, Impact and Preconditions, then Sources.

## Mechanism

- Mechanism: how the element functions; the processes, interactions or sequences that make it work.
- Enabling factors: the technologies, architectures, capabilities or conditions that make it possible.
- Causal chain: precondition, then trigger, then mechanism, then impact, written as one chain with arrows.
- Feedback loops: self-reinforcing or dampening factors and cascading effects, or none identified.

## Impact

- Impact domain: one or more of Confidentiality, Integrity, Availability, Safety, Compliance, plus any domain dimension added for the user's field.
- Severity: Critical, High, Medium or Low.
- Scope: system-level, organization-level or ecosystem-level.
- Temporal: immediate, delayed, persistent or cascading; say when the impact shows (real time or latent).
- Affected assets and stakeholders: the data, systems, processes and people or user groups at risk.
- Quantitative estimates: financial (cost of exploitation or mitigation), operational (downtime, degradation, resource use), reputational (brand damage, trust erosion) or regulatory (fines, sanctions, liability), each with its method and source; otherwise not quantified.
- Comparison to baseline: how the impact differs from that of the closest Set B element: more or less severe, different assets affected, or impacts that accumulate or interact in new ways.

## Preconditions

List each precondition once, tagged with its type: technical (technologies, architectures, configurations), organizational (processes, policies, culture) or environmental (external context, threat landscape).

- Necessary: must be present; without it the element cannot occur.
- Sufficient: alone can enable the element.
- Contributing: raises the likelihood but is not required.
- Inhibiting: its presence prevents the element.
- Precondition dependencies: whether the preconditions are independent, form chains (one enables the next) or are alternative sets (either one enables the element).
- Prevalence: how common the preconditions are in the target environments, as a share of target systems or settings where evidence gives one, with its source; otherwise not estimated.
- Trend: increasing, stable or decreasing over time, with the evidence.

## Sources

- The citations behind the profile's claims, each with its access date.
