---
created: "2026-11-04T19:58:28Z"
updated: "2026-11-04T19:58:28Z"
---

# Controls and documentation requirements

## Principles

Least disclosure (share only the minimum needed for the purpose), data minimization (collect and keep only what is essential), purpose limitation, need-to-know, separation of duties, defense in depth, privacy by design. Turn them into requirements for access control (who, what, when, how), encryption in transit and at rest, audit and monitoring, retention and disposal, and anonymization or de-identification.

## Control baseline

- Low (149 controls): limited or minor impact; basic access control and authentication, security awareness training, incident response planning.
- Moderate (287 controls): serious impact; least privilege and separation of duties, configuration management, encryption at rest and in transit.
- High (370 controls): severe or catastrophic impact; continuous monitoring, full encryption and key management, audit and forensics.
- Tailor the baseline: scope it to the environment, pick compensating controls where a baseline control is infeasible, add controls for unique risks, and record each tailoring decision with its reason.

## Access control

- Attribute-based rules combine subject attributes (role, department, clearance, authentication strength), resource attributes (classification, owner, sensitivity, regulatory tags), action attributes (read, write or delete; purpose; time) and environment attributes (location, device posture, network zone, time of day).
- An access control matrix lists subjects (users, roles, systems) as rows, objects (assets, files, services) as columns and permissions (read, write, execute, delete, own) in the cells.
- Least privilege: start from no access and add only what is needed; prefer read-only; make temporary access time-limited; separate duties for critical functions.

## De-identification (statistical disclosure control)

- k-anonymity: each record indistinguishable from at least k-1 others, by generalization (age to age band) and suppression (remove outliers).
- l-diversity: each k-anonymous group holds at least l different sensitive values, against attribute disclosure.
- t-closeness: the distribution of a sensitive attribute in each group resembles the overall distribution, against inference from skew.
- Differential privacy: calibrated noise under a privacy budget (epsilon, delta), tracking cumulative loss across releases.
- Workflow: remove direct identifiers (names, ID numbers, contact details), treat quasi-identifiers with the techniques above, reassess residual risk, and repeat until the risk is below the threshold. Measure the utility lost and confirm the result still supports the intended downstream tasks; record the privacy-utility trade-off.

## Sharing

- Mechanisms: encryption (AES-256 at rest, TLS 1.3 in transit), secure transfer (SFTP, HTTPS, authenticated APIs), data sharing agreements (permitted uses, security requirements, breach notification), virtual data rooms with granular permissions and audit logs.
- Tiers by sensitivity: public sharing, partner sharing under a data use agreement, restricted sharing with strong authentication and encryption, no sharing (secure enclave only).
- Traffic Light Protocol markings: RED (no disclosure beyond the named recipient), AMBER (limited to the organization), GREEN (community-wide), WHITE (public).

## Monitoring and audit

- Logs: access (successful and failed), changes to data and configuration, transfers across trust boundaries, access-control policy decisions.
- Alerts: unusual access patterns (time, location, volume), unauthorized attempts, policy violations, privilege escalation attempts.
- Review: how often logs are reviewed, who reviews and escalates, how long logs are kept.

## Verification methods

Test (controlled tests of control behaviour, such as access rules run with different roles), demonstration (show the control working, such as the request and approval flow), inspection (review policies, configurations and matrices), analysis (reasoning or calculation, such as residual disclosure risk compared with tolerance).

## Documentation each stakeholder type needs

- Upstream providers: data specifications (schema, format, quality), service level agreements, security and compliance requirements, incident response and breach notification procedures.
- Downstream consumers: data dictionaries and metadata, usage guidelines and permitted purposes, quality metrics and known limits, access request and approval procedures.
- Data owners: inventory and classification records, risk assessment results, access logs and audit reports, lineage and provenance records.
- Compliance officers and auditors: policies and procedures, risk assessment reports, control implementation evidence, audit logs and incident reports.
- System operators: architecture diagrams, configuration records, runbooks, monitoring and alerting settings.

## Documentation minimums

- Essential content: needed for the task or for compliance. Recommended content: improves utility but not required. Prohibited content: brings unacceptable disclosure risk.
- Apply minimization: only what the purpose needs, no personal identifiers where avoidable, aggregated or de-identified data when individual records are not needed, sensitive fields the recipient does not need removed or redacted.
- For each include or exclude decision record the necessity, the residual risk if included, the utility lost if excluded, and the alternatives considered.
- Granularity: detailed when precise analysis or troubleshooting is needed, regulation requires detail, or the recipient has clearance and a legitimate need; aggregated when trends are enough, detail poses excessive risk, or the recipient has limited privileges. Aggregation can be temporal (daily to monthly), spatial (individual to team to organization) or statistical (counts, averages, medians, ranges).
- Lifecycle and access for each document type: retention period, archival, secure disposal, its own classification, who may access it, under which conditions, how access is granted, and how it is monitored.
- A traceability line per downstream task: task, required data assets, supporting documentation, access requirements.

## Review cycle

Quarterly operational review; annual full risk reassessment; an extra review on any significant change (a new regulation, a security incident, a major system change).

## Example control row (format only)

| ID | Control | Mitigates | Verify by |
|---|---|---|---|
| C-07 | Release trip records only as stop-level hourly counts; suppress cells under the agreed minimum | R-04 | Analysis: recompute uniqueness on the release file |
