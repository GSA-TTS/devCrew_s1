---
created: "2026-11-04T19:14:33Z"
updated: "2026-11-04T19:14:33Z"
---

# Proxy rules: fields, text signals and a rule-based baseline

## Field groups and column mapping

Normalize the user's columns to these names before scoring. Availability is typical for a recent federal AI use case inventory.

| Group | Field | Columns that usually carry it |
|---|---|---|
| Primary | use_case_name | use case name, title |
| Primary | problem_solved | summary, what problem the AI is intended to solve |
| Primary | benefits | expected benefits, intended purpose and expected benefits |
| Primary | development_stage | stage of development: pre-deployment, pilot, deployed, retired |
| Primary | is_high_impact | high-impact flag; rights-impacting or safety-impacting flags |
| Primary | biz_goals | business or mission goals |
| Secondary | system_outputs | outputs |
| Secondary | classification | AI technique or type |
| Secondary | topic_area | topic area |
| Sparse | have_ato | ATO status |
| Sparse | has_pii | PII flag |
| Sparse | contracting_usage | contracted or vendor use |
| Sparse | has_custom_code | custom code, open-source code link |
| Sparse | data_description | training data description |
| Sparse | demographic_features | demographic variables used |

Confidence counts only the 9 primary and secondary fields. Identifiers (use case ID, agency, component) are carried into the record but not counted.

## Text signals per construct

Use these as evidence when answering the dimension questions and when writing the rationale.

- PU: mission-impact wording (detecting fraud, improving safety, supporting enforcement, benefits to the public or to vulnerable groups); time, cost or error reduction (reduce, improve accuracy, save time, increase throughput); a high-impact, rights-impacting or safety-impacting flag; deployed rather than pre-deployment, which is partial evidence of realized usefulness.
- PEOU: assistive, embedded wording (assist, suggest, autocomplete, summarize, chat, copilot, recommend) raises it; multi-system orchestration, complex multi-step decision automation or specialized technical use lowers it.
- Trust: a non-trivial training data description, a privacy impact assessment or other public documentation, a risk management entry with specific controls (not boilerplate), ATO status; a rights- or safety-impacting use with little documentation lowers it.
- Explainability: wording about validation criteria, rule-based overlays, explainability tools or interpretable outputs (a score plus rationale); public documentation of the model or data.
- Human oversight (feeds Trust Q2): high when the text says humans review AI outputs, analysts adjudicate, a case officer approves, or feedback retrains the model; medium when the AI only gives recommendations to staff with no review wording; low when the decision is fully automated with little oversight, especially in rights- or safety-impacting uses.
- Augmentation versus automation (support, assist, copilot against full automation of human judgment) is a weak, low-confidence signal; mention it in a rationale only as such.

## Rule-based baseline (cross-check or when the user asks for transparent rules)

Each index starts at 0.5, is capped between 0 and 1 and is reported as low, medium or high. The increments are illustrative weights, not calibrated values; say so when you report them.

- PU: +0.2 if benefits mention mission-critical outcomes; +0.1 for time savings, cost savings or productivity wording; +0.1 if high-impact or rights- or safety-impacting; +0.1 if deployed for more than a year.
- PEOU: +0.2 if the AI is an assistive tool inside an existing interface; -0.2 for complex multi-system orchestration or specialized technical use; -0.1 if rights- or safety-impacting with no user-facing explanation or training mentioned.
- Trust: +0.2 for a present, non-trivial training data description; +0.1 for a privacy impact assessment or other public documentation; +0.1 for a specific risk management entry; -0.2 if rights- or safety-impacting, PII-heavy and the documentation fields are mostly blank.

These rules are a fallback and an explanatory layer: report them beside the 1 to 5 scores, never in place of them.

## Portfolio checks and uses

- Lifecycle check: high-PU and high-PEOU cases should more often be deployed than pre-deployment or retired.
- Risk alignment: for high-impact or rights- or safety-impacting cases, Trust should follow the richness of risk management documentation; a mismatch points to a governance gap or a scoring error.
- Sector check: PU and PEOU distributions should differ plausibly across agencies and topic areas (analytics-heavy work lower on PEOU than office productivity tools).
- Uses: low PEOU points to UX, training or guardrail work; high PU with low PEOU marks valuable but hard to use systems; high PU with low Trust in rights- or safety-impacting cases calls for documentation, transparency and oversight work; re-scoring after each inventory update tracks direction over time.

## Expert labels

If the user wants the scores grounded in human judgement, describe this weak-supervision path for them to run:
1. Domain experts or representative users rate about 50 to 150 diverse cases on PU, PEOU and Trust (1 to 5 or low/medium/high), from the inventory row alone, with a rubric anchored in the construct definitions.
2. Train one simple model per construct (gradient-boosted trees or ordinal regression) on the text signals and fields above, and check with cross-validation that it separates low from high; a useful rank order is enough for triage even when fit is modest.
3. Score the full inventory and report quantiles or terciles (for example the top 20 percent on PU) to offset calibration problems.
Do not claim to have trained or run such a model yourself.
