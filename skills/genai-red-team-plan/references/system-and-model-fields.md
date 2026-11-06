---
created: "2026-11-04T23:13:59Z"
updated: "2026-11-04T23:13:59Z"
---

# System and model description fields

Fill every field from the user's material or a cited source; write "not stated" where neither gives it.

## Section 1: Target system description (five areas)

1. System architecture
   - System flows: the path of a request through the system (a diagram, or the flow in words).
   - Model type and architecture: the kind of generative model (for example LLM, GAN) and its architecture, including layers, parameters and design choices where known.
   - Training data and preprocessing: source, size and preprocessing steps.
   - Deployment environment and infrastructure: where the model runs (cloud platform, on-premises servers).
2. Functionality and use cases
   - Intended use cases: the applications and functions the system is for.
   - User personas: representative users with varying intentions, technical skills and backgrounds, including how each might try to misuse the system.
   - Input and output: the input types accepted and the outputs generated.
   - User roles and access controls: each role and its access permissions.
3. Data security and privacy
   - Data handling procedures: storage, processing and access controls for sensitive data.
   - Privacy measures: privacy-preserving techniques such as anonymization or differential privacy.
   - Compliance requirements: the data privacy regulations that apply (for example GDPR, CCPA).
4. Security measures
   - Authentication and authorization: how identities are verified and access controlled.
   - Vulnerability management: how vulnerabilities are found, assessed and mitigated.
   - Incident response plan: the procedure for security incidents and breaches.
5. Third-party dependencies
   - External APIs and libraries used.
   - Vendor risk management: how third-party vendor risk is assessed and managed.

## Section 2: Target model description (one block per model)

The fields assume a model the user does not own, assessed from public information, vendor documentation and critical analysis of claims. Label each claim stated, independent or inferred, as Inputs defines.

Core model information
1. Model name and version (official).
2. Provider or developer.
3. Model type, specific (for example transformer-based LLM).
4. Release date of the version.
5. Intended use cases as stated by the provider.
6. Out-of-scope use cases: those the provider discourages, and those inferred as technically possible but ethically or practically problematic.
7. Data summary: training data source description (type and claimed sources; note a vague description), data collection period, data preprocessing description (note any bias mitigation; a lack of detail is a red flag), known data limitations as stated and as inferred (biases the source description suggests).

Performance and evaluation
8. Performance metrics reported by the provider, and whether they fit the intended use cases.
9. Evaluation datasets: public or proprietary, and whether they represent real use; a lack of transparency is a major concern.
10. Benchmark comparisons, noting cherry-picked or unfair comparisons.
11. Independent evaluations by third parties and their findings.
12. Known performance limitations: conditions and input types where the model performs poorly.
13. Uncertainty quantification: whether the model reports confidence, and how.

Safety, bias and alignment
14. Bias mitigation strategies claimed, with concrete details or a note that they are vague.
15. Safety evaluations described (for example red teaming, adversarial robustness testing) and their results.
16. Alignment efforts claimed (for example reinforcement learning from human feedback, constitutional AI).
17. Known biases, reported and inferred: demographic, linguistic, cultural, confirmation bias; and their consequences.
18. Potential harms and misuse, even under intended use: disinformation and propaganda, discrimination and unfairness, privacy violations, security vulnerabilities.
19. Red teaming results the provider reports, and how they were addressed; a lack of detail is a warning sign.
20. Content policies and usage guidelines, and whether they are enforceable.

Access and usage
21. Access method (API, cloud service, downloadable software).
22. Terms of service: whether they address safety, bias and misuse, and whether they limit provider liability.
23. Pricing model: how usage relates to price.
24. Monitoring and auditing of misuse claimed by the provider.
25. User feedback mechanisms for reporting problems.

Caveats and limitations
26. Transparency limitations: the limits of the assessment from lacking direct access to the model, and that it rests on public data and provider claims.
27. Unverified claims: every provider claim not verified independently.
28. Open questions and concerns about safety, bias and alignment that need further investigation.
