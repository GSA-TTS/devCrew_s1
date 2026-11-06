---
created: "2026-11-04T19:36:30Z"
updated: "2026-11-04T19:36:30Z"
---

# Phase criteria: what each phase of the assessment covers

One section per phase, in the order the assessment runs. Each gives the items to cover, the scales or options to choose from, and the output the phase hands to the next.

## 1. System definition and boundary

- Name the system and its type: physical process, information system, organizational function, or hybrid.
- Boundary dimensions; state what is in and what is out on each that applies, with the inclusion or exclusion reason:
  - Physical: locations, facilities, equipment.
  - Logical: software, data flows, network segments.
  - Organizational: departments, teams, stakeholders.
  - Temporal: project phases, operating timeframes, lifecycle stages.
- Component inventory: hardware and physical assets; software and platforms; data stores and information flows; personnel roles; processes and procedures; supporting infrastructure and utilities; third-party dependencies and external interfaces.
- Characteristics: criticality and sensitivity; performance and service-level expectations; compliance and regulatory requirements; security classification and data sensitivity; operating environment.
- Intended behaviour: intended functions, normal operating parameters, what counts as acceptable operation, and how users use the system.
- Context: internal (governance, risk management maturity, existing policies and controls, budget and staff, risk appetite and tolerance) and external (regulation, industry standards, market, technology trends and emerging threats, stakeholder expectations).

## 2. Stakeholders

- Internal (executives, system owners, operators, end users, IT, compliance) and external (customers, suppliers, regulators, partners, community groups); direct and indirect.
- Attributes: power, legitimacy, urgency, interest, impact. Classify with a power/interest matrix (high power and high interest need close management), an influence/impact grid or the salience model (power, legitimacy, urgency).
- Record each group's concerns about the system's risks; these feed identification and the audience of the deliverable.

## 3. Risk identification

- Taxonomy, adjusted to the system type: technical (hardware failure, software defects, integration); operational (process failure, human error, capacity); security (cyber threats, physical breaches, access control failure); compliance (regulatory violation, standard non-conformance); strategic (misalignment with objectives, inadequate capability); external (natural events, third-party failure, market change); financial (budget overrun, funding disruption).
- Techniques; use more than one:
  - Asset-based: for each critical asset, its threats; for each threat, the vulnerabilities it could exploit.
  - Process-based: each process step and each handoff or transition as a failure point.
  - Threat-based: threat sources (human, environmental, natural) mapped to components, including emerging threats.
  - Scenario analysis: base, worst and best cases; what-if questions; cascading and compounding effects.
  - FMEA: per component, failure modes with causes, effects, severity, occurrence and detectability.
  - Fault tree: an undesired top event worked backwards through AND/OR gates to minimal cut sets.
  - Bowtie: a central event with threats on one side, consequences on the other, preventive and recovery barriers, and escalation factors that weaken barriers.
  - Workshops, expert interviews, checklists, past risk registers, incident and audit reports.
- Dependencies: upstream (inputs the system needs), downstream (systems relying on its outputs), lateral (parallel systems sharing resources); typed physical, cyber, geographic or logical; trace how a failure cascades and mark single points of failure. Examine interfaces at the boundary, third parties, supply chain and shared infrastructure.
- Prune: remove generic risks that do not fit this system, remove risks outside the boundary, merge duplicates, keep only risks that could realistically affect the system.
- Output: a risk register with a unique ID and a description per risk, by category.

## 4. Risk analysis

- Method:
  - Qualitative: descriptive scales, expert judgement; fits limited data.
  - Quantitative: numerical probabilities and impacts from data; fits when quality data exist.
  - Semi-quantitative: numeric scores on qualitative categories, risk priority numbers or weighted scores.
- Likelihood scale (5-point): Rare, Unlikely, Possible, Likely, Almost Certain; as probability ranges below 10%, 10-30%, 30-50%, 50-70%, above 70%. Drivers: threat capability and motivation, vulnerability severity and exploitability, existing control effectiveness, environment.
- Impact scale: Negligible, Minor, Moderate, Major, Catastrophic (or 1-5, 1-10, money ranges for financial impact, duration for operational impact). Dimensions: financial, operational, reputational, safety and health, compliance, strategic. Use units (money, downtime hours, affected users) where the user's data allow.
- Existing controls: preventive (lower likelihood), detective (timely discovery), corrective (lower impact or enable recovery), directive (policy, procedure), compensating (alternative measures). Judge each on design, implementation status, operating effectiveness and reliability, from how it actually operates, not its design intent; name control gaps and single points of failure.
- Exposure: Likelihood x Impact on a matrix; expected loss = probability x financial impact; for FMEA, risk priority number = severity x occurrence x detection.
- Root cause for priority risks: 5 whys, fishbone (people, process, technology, environment), fault tree, Pareto. Separate symptoms, contributing factors and root causes.

## 5. Risk evaluation and prioritization

- Criteria: risk appetite (overall willingness, risk-averse, risk-neutral or risk-seeking, possibly per category), risk tolerance (measurable acceptable deviation, limits per category), risk thresholds (values that trigger escalation; red, amber and green boundaries).
- Compare each risk with the criteria: exceeds tolerance, approaching a threshold, or within range. Apply mandatory treatment rules (for example critical safety risks) and compliance-driven criteria.
- Priority: primary factor is the risk score; secondary factors are velocity, control effectiveness, residual risk after existing controls, detectability, trend, stakeholder concern.
- Tiers: Critical or High, immediate action; Medium, treatment within a defined timeframe; Low, monitor or accept.
- Acceptability: acceptable (within tolerance, no action), ALARP (as low as reasonably practicable; acceptable when further reduction is impractical), unacceptable (exceeds tolerance, needs treatment), conditional (accepted with monitoring or time-bound conditions).

## 6. Risk treatment

- The four options:
  - Tolerate or accept: risk below the threshold, treatment costs more than the benefit, no practical treatment, or the risk is needed to reach objectives; needs explicit approval.
  - Treat or mitigate: preventive (procedures, training, access control, redundancy), detective (monitoring, audits, alerts), corrective (backups, incident response, recovery procedures).
  - Transfer or share: insurance, contracts (indemnification, warranties), outsourcing; shifts the financial impact, not the likelihood.
  - Terminate or avoid: stop the activity when the risk is unacceptably high and cannot be mitigated, the activity is not critical, or an alternative exists.
- Selection criteria: cost against risk reduction, feasibility, resources, urgency and duration, organizational priorities and appetite, stakeholder acceptance, mandated controls. Options can be combined (mitigate the likelihood and transfer the financial impact).
- Plan fields per priority risk: the risk; the option or combination; actions (what, how, where, when); risk owner and implementers; resources (budget, staff time, technology, outside help); start and end dates and milestones; target residual risk and measurable success criteria; key risk indicators, review frequency, escalation trigger.
- Residual risk: re-rate likelihood and impact assuming the treatment works, compare with tolerance, add treatment if still above it, and record who must approve accepting it.
- Overall strategy: controls that address several risks, sequence with the highest-impact treatments first, governance for oversight, approval and escalation.

## 7. Implementation and verification

- Verify each control is installed as designed, configured, tested (functional tests, scenario simulation, penetration tests for security controls, tabletop exercises for procedural controls), and that staff are trained.
- Record implementation dates and update control effectiveness and residual risk in the register.

## 8. Monitoring and review

- Key risk indicators per priority risk with green, amber and red thresholds; monitoring frequency set by how fast the risk can materialize. Control performance indicators: failures, exceptions, fitness for purpose.
- Full reassessment cycle: high-risk systems quarterly, medium-risk semi-annually, low-risk annually.
- Reassessment triggers: system change or upgrade, new threats or vulnerabilities, regulatory change, organizational change, an incident.
- Watch for emerging risks (threat information, technology and regulatory change, incidents at similar systems) and assess them with the same method.
