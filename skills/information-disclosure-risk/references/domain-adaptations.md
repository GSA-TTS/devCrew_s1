---
created: "2026-11-04T19:58:28Z"
updated: "2026-11-04T19:58:28Z"
---

# Domain adaptations and regulatory add-ons

## Government and defense

- Frameworks: FISMA, the NIST Risk Management Framework, FedRAMP, ITAR and EAR export controls, classification guides.
- Data types: classified information (CUI, Confidential, Secret, Top Secret), sensitive but unclassified, personally identifiable information.
- Stakeholders: agencies, contractors, foreign partners under agreements, oversight bodies.
- Scope: name the system's level (FISMA Low, Moderate or High, or a national security classification).
- Inventory: apply formal classification markings to every asset, including portion markings.
- Controls: select the NIST SP 800-53 baseline for the level; enforce need-to-know strictly; separate networks per classification level (air-gapped when required); clearances before access; foreign disclosure controls with releasability markings; formal classification and declassification procedures.
- Documentation: justify every access grant on need-to-know.

## Healthcare

- Frameworks: HIPAA Privacy, Security and Breach Notification Rules; HITECH.
- Treat all patient information as PHI. Share only the minimum necessary PHI and document that justification for each sharing scenario.
- Assess re-identification of de-identified sets with the HIPAA Safe Harbor or Expert Determination methods.
- Role-based access by job function, with emergency (break-glass) access; log every PHI access (who, what, when, why); Business Associate Agreements for third parties.

## Financial services

- Frameworks: PCI-DSS, GLBA, SOX, FFIEC guidance.
- Separate PCI-DSS in-scope cardholder data from other data and map where cardholder data is transmitted; isolate the cardholder data environment.
- Weigh fraud analytics against privacy; maker-checker separation of duties; strong authentication for high-risk transactions; compensating controls where a PCI-DSS requirement cannot be met directly.

## Manufacturing and supply chain

- Frameworks: CMMC for defense contractors; sector standards such as TISAX.
- Protect intellectual property (designs, formulas, processes) against espionage and competitive intelligence; map supplier dependencies and single-source suppliers; segment OT from IT networks; give each supplier only what its role needs.

## Technology and SaaS

- Frameworks: GDPR, CCPA, SOC 2, ISO 27001.
- Classify data by tenant and isolate tenants; map API flows and which APIs expose sensitive data; enforce tenant boundaries with attribute-based rules at the API gateway; data residency; breach notification across customers; customer-facing data handling documents (privacy policies, data processing agreements).

## Data protection impact assessment (GDPR and similar)

- Triggers: systematic and extensive profiling with significant effects; large-scale processing of special category data (health, biometric, genetic); large-scale systematic monitoring of public areas; new technology with high privacy risk; processing that prevents people from exercising their rights.
- The analysis supplies its parts: describe the processing (scope and flows), necessity and proportionality and the risks to rights and freedoms (risk register), mitigations (controls), consultation with the data protection officer and stakeholders, and monitoring.

## Third parties and vendors

- Identify third-party stakeholders and their flows; assess disclosure from their access together with a vendor security assessment; mitigate by contract (data processing agreements, business associate agreements) with breach notification clauses; monitor the vendor's security posture.

## Consent

- Valid consent is freely given, specific to each purpose, informed, unambiguous (an affirmative act) and withdrawable.
- Tag assets with purpose and legal basis; allow access only where valid consent exists; show consent status in documents shared with data subjects; track expiry, renewal and withdrawal.
