---
created: "2026-11-04T19:58:28Z"
updated: "2026-11-04T19:58:28Z"
---

# Disclosure assessment: scenarios, vectors, methods and scales

## Scenario types

- Intentional: authorized sharing with downstream consumers.
- Accidental: unintended exposure through misconfiguration or error.
- Unauthorized: malicious access or a breach.
- Inference: re-identification by linking the data with external datasets.
- Aggregation: combining several low-sensitivity datasets to reveal sensitive information.

For each scenario record the trigger event, the assets affected, the possible attackers or recipients, and the external data available for linkage.

## Quasi-identifiers and linkage data

- Quasi-identifier families: demographic (age, gender, location), temporal (dates, timestamps), behavioural (transaction patterns, access logs), relational (organizational affiliations, social connections).
- External data that enables linkage: public registries (census, electoral rolls, property records), commercial datasets (credit bureaus, marketing databases), social media and other public information, partner organizations holding overlapping data.

## Methods

- Absolute disclosure risk: the probability of identifying a subject given the release. Needs assumptions about the attacker's capabilities and prior knowledge; suits high-stakes, well-defined scenarios.
- Differential privacy (counterfactual): measures how much a release changes the attacker's beliefs, with a privacy budget (epsilon, delta); preferred for repeated releases and cumulative risk.
- Prior-to-posterior comparison: what the attacker knows before and after the release; useful when the attacker's priors can be estimated.

State which method was used and why.

## Metrics (computed from records, not guessed)

- Uniqueness: the share of records with a unique combination of quasi-identifiers.
- k-anonymity: the smallest group of records sharing the same quasi-identifier values.
- Re-identification rate: the estimated success rate of a linkage attack.
- Disclosure risk score: an aggregate of several factors.

## Harm categories

- Individual: privacy violation, discrimination, identity theft, reputational damage.
- Organizational: regulatory penalties, loss of competitive advantage, reputational damage.
- Operational: service disruption, loss of trust, stakeholders withdrawing.
- National security (government and defense): espionage, strategic disadvantage.

## Scales

- Likelihood of disclosure: 1 (Remote) to 5 (Certain).
- Severity of harm: 1 (Minimal) to 5 (Catastrophic).
- Risk score: likelihood times severity.
- Acceptable and unacceptable levels come from the organization's risk tolerance.

## Register row fields

Risk ID, asset ID and classification, scenario, quasi-identifiers and vectors, method, metrics, harm categories and severity, likelihood, score and band, risk owner.

## Example row (format only)

Transit ridership shared with a university, continuing the inventory example.

| ID | Asset | Scenario | Who could get it | Vectors | L | S | Score | Band |
|---|---|---|---|---|---|---|---|---|
| R-04 | A-03 | Inference | A researcher or anyone who obtains the extract | Tap times and stops, linked with property records | 3 | 4 | 12 | High (cut-off assumed) |
