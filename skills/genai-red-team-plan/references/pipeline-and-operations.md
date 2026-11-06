---
created: "2026-11-04T23:13:59Z"
updated: "2026-11-04T23:21:49Z"
---

# Test pipeline, operations and findings report

Material for Sections 5, 6 and 7. Component names are PyRIT's; with another toolset, describe the same role in that tool's terms.

## Section 5: Test pipeline (six stages, then reporting in Section 7)

1. Initialization
   - Environment: the tool and its dependencies installed, environment variables configured (API keys, connection strings), a dedicated environment (conda environment, virtual machine), dependencies for every part of the system, the access permissions needed.
   - PyRIT configuration: memory initialized and its type chosen (in-memory, DuckDB, Azure SQL) for persistence and collaboration needs; the PromptTarget configured with the correct endpoints, authentication and model parameters; the Scorer instances planned up front (more can be added later); an Orchestrator whose requirements fit the plan.
   - Baseline (optional, recommended): benign prompts sent and their responses recorded, stored in memory, as a point of comparison.
2. Dataset selection or creation
   - Existing datasets: the tool's built-in datasets (harmful prompts, bias-eliciting prompts, task datasets) and public datasets to adapt.
   - Custom datasets built systematically from the threat model across harm categories (toxicity, misinformation, PII disclosure), attack techniques (prompt injection, jailbreaking), the user personas, each input type, and edge cases; prompt templates with placeholders (SeedPrompt) and data augmentation (paraphrasing, back-translation).
   - Format: a structure the tool accepts (SeedPromptDataset) with metadata such as harm category and attack type for filtering and analysis.
   - Design: diverse, realistic, and started small and expanded iteratively.
3. Prompt conversion (optional)
   - Needed for jailbreaking, adversarial attacks, augmentation and cross-domain attacks (text to a document or an image); skipped when the dataset already targets the vulnerabilities.
   - Converters chosen for the threat scenarios (for example JailbreakConverter, ParaphraseConverter, TextToImageConverter, SearchReplaceConverter), stacked where useful (paraphrase, then jailbreak), or custom (subclass PromptConverter). Note the cost of converters that call an LLM.
4. Prompt sending
   - The PromptTarget handles the interaction, conversation history (PromptChatTarget) and storage in memory.
   - Orchestrator: PromptSendingOrchestrator for batches; MultiTurnOrchestrator for multi-turn conversations; CrescendoOrchestrator, PairOrchestrator or TreeOfAttacksWithPruningOrchestrator for specific attack strategies.
   - Error handling for timeouts, rate limits and unexpected responses; asynchronous sending; monitoring of the run for errors and delays.
   - Design: scalable, reproducible (consistent settings and parameters), within the target API's rate limits and usage restrictions.
5. Scoring
   - Scorers matched to the scenarios and harm types (for example ToxicityScorer, PIIScorer, StereotypeScorer, RefusalScorer, SelfAskTrueFalseScorer, HITLScorer for human scoring), combined where several aspects matter, or custom (subclass PromptScorer).
   - A threshold per scorer that marks a failure or red flag, and how scores are weighed against each other.
   - Automated scorers for volume and human scoring for nuance, often combined; scores read in the context of the prompt and the intended use; thresholds tuned for false positives and false negatives.
6. Iteration and refinement
   - Analyze: patterns, the prompts that most often elicited harmful behavior, the scorers that detected it, unexpected results.
   - Refine the dataset (add prompts for new vulnerabilities, strengthen existing ones, remove consistently ineffective ones), the converters (parameters, combinations, custom logic) and the scorers (thresholds, choice, custom logic).
   - Repeat until the success criteria are met or the constraints are reached; make small changes, track the effect of each, document each iteration, and share findings with the team and the system's developers.

## Section 6: Operations

- Logging, what to log: inputs (every prompt with prompt ID, source dataset, converter applied); outputs (raw and processed responses); scores (scorer name, value, rationale); timestamps of sending, receiving and scoring; errors with stack traces; configuration of all components (tool settings, model versions); orchestrator actions; memory operations where the tool has memory.
- Logging, how: levels (DEBUG for development and troubleshooting, INFO or WARNING for routine runs); structured format such as JSON with consistent fields (timestamp, event type, component, prompt ID, score); storage (local files for small exercises, a central logging system such as Elasticsearch, Splunk or Azure Monitor, or the tool's memory), secure and with enough capacity; a rotation policy and a retention period, which legal or compliance needs may set; tracing such as OpenTelemetry where the pipeline spans several services. Start verbose, centralize where possible, and automate log analysis.
- Logging, credentials: log no API key, token or connection string; record the configuration with secrets masked.
- Logging, personal data: anonymize or redact personal data in logged prompts and responses, as the legal and ethical constraint requires.
- Automation, schedule: continuous (every few hours, for regressions), periodic (daily, weekly, monthly, for less critical systems) or on-demand (after a code change, before a release); tools such as cron, Windows Task Scheduler, CI/CD pipelines or cloud schedulers; resource use kept off production peaks; data and date dependencies; failure handling (notification, retry). Run on demand reliably before automating, and monitor scheduled runs.
- Automation, triggers: code changes, model updates, training data updates, configuration changes, security events, manual trigger; mechanisms such as webhooks, event subscriptions or an API endpoint; filtering so the pipeline runs only when a change touches the AI components. Code and model changes come first.
- Reports and dashboards: static reports for stakeholders, interactive dashboards, or notebooks; generated automatically from the tool's memory; a regular cadence or after major updates.
- Integration: CI/CD (most important; trigger on code or model changes and report back, for example failing the build when vulnerabilities are found); vulnerability management system (tickets per vulnerability); SIEM (logs correlated with other security events); threat intelligence sharing; collaboration-platform notifications.

## Section 7: Findings report

- Audience: developers, security engineers, product managers or executives; detail and jargon matched to them (executives a high-level summary, developers technical detail).
- Structure: Executive summary (key findings and recommendations); Methodology (scope, constraints, methodologies, tools); Findings, one per vulnerability (Description, Severity with the named scoring system, Examples of successful attacks with prompts, responses and scores, Impact); Recommendations (specific mitigations ranked by severity and feasibility); Appendices (optional: logs, scripts, datasets).
- Also: summary statistics (prompts sent, vulnerabilities found, success rate per attack type, score distribution), trends over time, comparison to the baseline, charts and tables, a stakeholder review of the draft.
- Style: clear, concise, objective, constructive, with the relative priority of recommendations explicit.
