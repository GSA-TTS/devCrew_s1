---
created: "2026-11-04T23:13:59Z"
updated: "2026-11-04T23:13:59Z"
---

# Threat model catalog

Material for the Key assumptions table (columns Area, Type, Assumption) and the Threats table (columns ID, Phase, Attack vector, TTP, Risk).

## Key assumptions: the ten areas

Common (shared by most generative AI systems):
- System access: who has legitimate access (users, administrators, developers), their roles and privileges, and access levels (read-only, query, modify). Take these from the system description's user roles and access controls and assume they are correctly implemented for this threat model; their implementation can be red-teamed separately.
- Attacker knowledge: black-box (no internal knowledge), grey-box (partial knowledge, such as API documentation or published papers) or white-box (full access to architecture and weights). Consider several attacker profiles, from an unskilled individual to a nation-state actor; MITRE ATLAS ML Model Access (AML.TA0000) applies.
- Attacker capabilities: query volume, specialized hardware or software, collusion, computational power, budget, expertise, access to datasets, and the limits that rate limiting or other defenses impose.
- Data integrity (initial): whether the initial training data is assumed free of intentional poisoning and significant unintentional bias. Not assuming it widens the threat model considerably.
- System security (non-AI specific): whether the infrastructure (servers, networks, databases) is assumed secure. Prefer to keep traditional cybersecurity threats separate and focus on threats specific to the AI components, referencing MITRE ATT&CK techniques where needed instead of duplicating a full cybersecurity threat model.

Unique (specific to this system):
- Model-specific behavior: known behaviors of this model that could be exploited (a known bias, hallucination in certain domains, sensitivity to some input types), from the model description.
- Deployment environment: aspects of the deployment that create vulnerabilities (edge devices with limited security, a specific third-party API), across the whole system flow.
- Intended use and misuse: the intended uses and the most likely or impactful misuses, drawing on the model description's potential harms and misuse.
- Data sensitivity: the input data, whether it is sensitive, and whether it contains PII, from the data security and privacy area.
- Mitigation measures in place: the security and prevention controls assumed present, from the security measures area.

## Threats by phase

Each phase has attack vectors, TTPs and risks (consequences for confidentiality, integrity and availability, for the model, data, system and users, short and long term).

### Pre-inference (before the input reaches the model)
- Attack vectors: entry points such as API, web form, file upload, pre-processing steps and connected systems. Examples: malicious file upload; tampering with data in transit from an external source; compromise of a third-party pre-processing component; exploiting API gateway vulnerabilities; data poisoning where the system learns from user data (ATLAS Poison Data, AML.T0015).
- TTPs: reconnaissance (ATLAS Victim Research, AML.T0007); resource development (ATLAS Acquire ML Artifacts, AML.T0009; Develop Adversarial ML Capabilities, AML.T0001); initial access (ATLAS Supply Chain Compromise, AML.T0010, or ATT&CK initial access techniques); data collection and staging.
- Risks: data poisoning degrading accuracy and reliability over time; leakage of sensitive data used in pre-processing; system compromise; denial of service of the pre-processing pipeline. The NIST AI RMF discussion of risks applies.

### Inference (while the model processes the input)
- Attack vectors, mainly prompt manipulation: prompt injection (prompts that make the model ignore its instructions or produce unintended output); prompt leaking (extracting the system instructions); jailbreaking (bypassing safety filters); token smuggling (encoding instructions to pass input filters); indirect prompt injection (instructions arriving in external data such as a web page); excessive resource consumption (tokens, memory, compute).
- TTPs: ATLAS ML Model Access (AML.TA0000) and ML Attack Staging (AML.TA0001) as they apply to inference; Craft Adversarial Examples, black box (AML.T0005); Discover Model Ontology (AML.T0017). Examples: crafted prefixes or suffixes, special characters or escape sequences to pass input sanitization, few-shot prompting with malicious examples.
- Risks: generation of harmful content (toxic language, hate speech, misinformation); exposure of sensitive information from training data or system prompts; violation of content policies or terms of service; reputational damage; resource exhaustion.

### Post-inference (after generation, before the user or a downstream system receives it)
- Attack vectors: output handling, filtering, logging and post-processing. Examples: tampering with output in transit; exploiting the display mechanism (cross-site scripting); compromising logging to inject false entries or delete evidence; manipulating post-processing steps (sentiment analysis, summarization).
- TTPs: defense evasion (bypassing output filters); exfiltration (stealing output); impact (harm through modified output), such as code injection where output becomes code, or cross-site scripting where output is shown in a web page; relevant ATT&CK techniques apply.
- Risks: dissemination of harmful content the model did not generate; incorrect decisions where output drives decisions; instability or compromise of downstream systems from malicious code; loss of auditability from tampered logs.
