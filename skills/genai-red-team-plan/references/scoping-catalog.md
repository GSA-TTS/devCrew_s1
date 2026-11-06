---
created: "2026-11-04T23:13:59Z"
updated: "2026-11-04T23:17:43Z"
---

# Scoping catalog

Material for Section 4: the Risk matrix (columns ID, Threat scenario, Probability, Impact, Impact dimensions, Priority), the Constraints list, the Test methods table (columns Scenario ID, Testing type, Methodology, Tools, Quantitative metric and target) and the success criteria.

## Risk matrix

- Probability: how likely the attack is to be attempted and to succeed, given the assumed attacker capabilities and existing security measures.
- Impact: the severity of the consequences if it succeeds. Impact dimensions: confidentiality (user data, training data, model internals), integrity (model, data, outputs), availability (service disruption, denial of access), reputation (brand and user trust), financial (monetary loss, fines, legal costs), legal and compliance (regulations such as GDPR, CCPA), safety (physical harm, where the system controls devices or real-world actions).
- Inputs to prioritization: the Risks of the three phases; any key assumption whose violation would lead to severe consequences; the NIST AI RMF trustworthiness characteristics most critical for this system (valid and reliable, safe, secure and resilient, accountable and transparent, explainable and interpretable, privacy-enhanced, fair with harmful bias managed); the OECD AI Principles whose violation would be most problematic for this system.
- A threat scenario is concrete: it names the attacker's action, the technique and the consequence, not an abstract risk name such as data poisoning.

## Constraints (six categories)

1. Time: the time allocated; a shorter engagement means a narrower scope.
2. Budget: personnel, tools, cloud costs, tools or services to buy, limits on paid API calls.
3. Personnel: team size and skills (prompt engineering, reverse engineering, machine learning, cybersecurity), and access to people who know the target system.
4. Legal and ethical: restrictions on attack types (for example no social engineering, no attacks on production systems), consent needed from users or stakeholders, data privacy regulations limiting data access or analysis, anonymization or redaction of collected data. Ethical considerations take priority: the goal is to improve security, not to cause harm.
5. Technical: limits of the test environment, whether it matches production infrastructure and how a difference affects testing, tool or technique restrictions (network traffic, software installation), API rate limits.
6. Scope of access: components or functions off-limits for testing (for example a critical database, a third-party service), with explicit in-scope and out-of-scope lists.

## Testing types

- Black-box: the attacker has no internal knowledge; input manipulation and output analysis.
- Grey-box: the attacker has some knowledge (API documentation, published research); allows more targeted tests.
- White-box: full internal access; generally not applicable to a proprietary model the user does not own.

## Methodologies

- Prompt injection: direct, indirect, jailbreaking and token smuggling attacks to bypass filters, elicit unintended outputs or extract information, with prompt injection testing tools (for example PromptInject, promptfoo).
- Adversarial example generation: where applicable (image or text classification), including black-box iterative input changes.
- Data poisoning simulation: only if the threat model includes poisoning; a small poisoned dataset and an assessment of its impact (difficult without training access).
- Model extraction or inversion (limited): inferring model characteristics by repeated querying; limited success expected without white-box access.
- Membership inference (limited): testing whether specific data points were in the training set; limited success expected without internal access.
- Manual analysis and exploration: interacting with the system to find unexpected behavior, biases or vulnerabilities; central to black-box and grey-box work.
- Fuzzing: large numbers of randomly generated inputs.
- Regression testing: where examples can be added to a regression suite, a set of scenarios the model should not be vulnerable to.
- Scanning open-source components: where the threat model assumes code access, scanning dependencies for known vulnerabilities.

## Success criteria

Quantitative metric types, each with a target:
- Prompt injection success rate: percentage of attempts that bypass content filters and elicit harmful output.
- Adversarial example success rate: percentage causing misclassification.
- Data extraction rate: number of data points extracted by model inversion (expected low in black-box testing).
- Resource consumption: whether resources can be consumed to prevent availability.
- Number of vulnerabilities found: at least N distinct vulnerabilities in a named risk area.

Qualitative criteria:
- Severity of vulnerabilities, categorized with a standard scoring system such as CVSS.
- Clarity of exploitation: how each vulnerability can be exploited in a realistic attack scenario.
- Impact on trustworthiness: which trustworthiness characteristics each vulnerability affects.
- Actionable recommendations: specific mitigations for each vulnerability.
- Coverage assessment: how comprehensive the exercise was and the areas for further work.

Overall success definition: one statement combining the quantitative and qualitative criteria, bounded by the time and budget constraints.
