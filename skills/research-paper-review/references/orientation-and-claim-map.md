---
created: "2026-11-05T00:04:27Z"
updated: "2026-11-05T00:13:10Z"
---

# Orientation pass and claim–evidence map

## Evaluation context to record

- Journal criteria: aims and scope, target audience and expected breadth, article-type requirements, reviewer form with its scoring rubric and decision categories, the editor's specific questions, data, code and supplementary-file expectations, and research-integrity, ethics, image and AI policies.
- Review scope: comprehensive, or limited to statistics, methods, artifacts or ethics.
- Package inventory: main manuscript; cover letter where visible; figures, tables and appendices; extended data and supplement; reporting checklists and flow diagrams; protocol, preregistration or registered-report materials; data, code, model, software and repository links; ethics, registration, consent, funding, authorship and competing-interest statements; revision files and response to reviewers, if any.

## Article type and provisional reporting standard

Check the declared type against the methods and evidence; a hybrid genre can need more than one standard, and an undeclared secondary or post hoc analysis is noted.

| Study type | Standard |
|---|---|
| Randomized trial or trial protocol | CONSORT, SPIRIT |
| Observational study | STROBE, RECORD |
| Systematic review or meta-analysis | PRISMA, with a risk-of-bias tool |
| Diagnostic accuracy | STARD |
| Prediction model | TRIPOD or TRIPOD+AI, PROBAST |
| Qualitative study | COREQ, SRQR |
| Animal research | ARRIVE (the Essential 10 at minimum) |
| Case report | CARE |
| Economic evaluation | CHEERS |
| Quality improvement | SQUIRE |
| Web survey | CHERRIES |
| Software, benchmark, dataset, security, hardware or engineering work | the domain or community standard |

Reporting completeness by design: trial (allocation, flow, outcomes, harms, registration); observational (population, variables, bias, confounding, missingness); systematic review (eligibility, search, screening, risk of bias, synthesis); diagnostic (index test, reference standard, participant flow, accuracy); prediction (data sources, predictors, outcomes, validation, performance); qualitative (research team, context, sampling, analysis, reflexivity); computational (data provenance, splits, baselines, parameters, code or artifact).

## First full read

- Order: front matter (title, article type, abstract, keywords, highlights or lay summary), then the narrative from introduction to conclusion, then the evidence (each main figure and table, legends and notes, the supplement index), then the data, code, ethics and competing-interest statements.
- Check that each central result has an associated method and display; note unavailable, broken or unreadable artifacts.
- Restraint during this read: no copyediting, no recommendation, no exhaustive reference search, no demand for new experiments, no inference of misconduct from a single irregularity, no running of code unless the review requires it and it is authorized.

## Synopsis elements

Problem addressed; claimed gap; research question or thesis; design and evidence base; main findings; claimed contribution; claimed implications.

## Claims to map

All primary claims; secondary claims that support the primary conclusion; claims of novelty, generalizability, mechanism, causality, safety or superiority; claims stated in the title, abstract, highlights or conclusion. Keep apart the claim (the authors' proposition), the evidence (result, table, figure, proof, analysis or source), the method that produced it, the inference that links them, and the assumptions the inference needs.

## Claim–evidence map columns

| Column | Content |
|---|---|
| Claim ID | C1, C2, ... |
| Claim | exact wording or faithful paraphrase, with its scope qualifiers |
| Status | primary, secondary or exploratory, as the manuscript presents it |
| Location | where the claim is stated |
| Evidence | results location, figure, table or panel, supplement or repository location, and the estimate with its uncertainty; none found when absent |
| Inference | descriptive, associational, predictive, causal, mechanistic, explanatory, interpretive or deployment-oriented |
| Defects | defect types from the list below, or none |
| Severity | from the severity scale below |
| Remedy | from the remedy types below |

## Chain tests

- Question: does the claim answer the stated question, sit outside the objective, or carry a status it does not have?
- Method: does the design generate relevant evidence; are the unit of analysis, comparator and measurement adequate for the claim's strength; is the analysis fit for the design and data?
- Evidence: does the result support the claim directly or indirectly, in enough quantity and quality, with uncertainty reported; is it duplicated, missing or inconsistent?
- Inference: is it weaker than, equal to or stronger than the evidence permits; are assumptions met, defended or untested; are alternatives addressed; does the conclusion keep the qualifiers?

## Defect types

- Unsupported: no evidence, evidence that does not address the claim or is insufficient for its importance, evidence unavailable to reviewers, or reliance on a citation instead of reported results.
- Overbroad: population, setting, time horizon, causal, mechanistic, practical or general language beyond what the evidence covers.
- Circular: conclusion restates an assumption; outcome definition embeds the conclusion; benchmark built to favour the proposed method; validation data overlapping training data; theory used as both premise and proof.
- Non-evaluable: key terms without operational definition; no success criterion; undefined comparator; untestable prediction; theory without failure conditions; mechanism without discriminating evidence.
- Orphan evidence: result tied to no question or claim; display with no interpretive role; supplementary analysis not integrated; unused data collection; unlabelled exploratory result.
- Missing dependency: claim resting on an unavailable supplement, inaccessible data or code, missing protocol or instrument detail, an insufficiently described cited method, or unverifiable external data.

## Severity and remedy

- Severity: Invalidating (if confirmed, the defect invalidates the claim); Major uncertainty (the claim's support is in doubt but not shown invalid); Repairable reporting gap (information a revision can supply); Minor ambiguity (wording, label or definition unclear); Optional strengthening opportunity (not required for the claim to stand).
- Priority by claim: central conclusion, main contribution, key enabling claim, secondary claim, peripheral narrative claim.
- Remedy types: clarify language; add missing reporting; supply artifact or source data; reanalyze; add robustness test; add validation or control; narrow claim; correct factual error; escalate confidentially.

## Candidate fatal flaws

A candidate fatal flaw is a credible, decision-relevant defect that, if confirmed, invalidates a central claim, makes the contribution nonpublishable for the venue, or cannot be repaired by a proportionate revision.

- Claim-invalidating: conclusion contradicts the reported data; design cannot answer the central question; central outcome or construct invalidly measured; essential control, comparator or baseline absent; core analysis unsuitable for the data or design; leakage, contamination or dependence invalidates results; causal claim without a defensible identification strategy; key proof, derivation or algorithmic claim invalid.
- Evidence-invalidating: central evidence unavailable or irretrievably incomplete; central dataset or repository inaccessible for required review; key results not linkable to methods; indeterminate sample provenance or inclusion; irreconcilable internal contradictions; apparent fabrication, falsification or noncompliant image manipulation.
- Contribution-invalidating: outside journal scope; not novel after the closest prior art; advance too slight for the venue; redundant or duplicative; implication resting on an unsupported premise.
- Ethics- and policy-invalidating: missing required ethics approval or consent; serious animal-welfare concern; unresolved privacy or legal restriction; unmanaged dual-use or safety risk; unresolvable competing interest.
- Confirmation discipline: keep the label candidate during the first pass; locate the specific supporting evidence; look for an explanation in the methods, supplement or policy materials; distinguish incomplete reporting from underlying invalidity; decide whether a bounded remedy exists; escalate integrity concerns confidentially instead of adjudicating them alone.

## Integrity and ethics screen

- Research ethics: human-subject approval or exemption; consent and privacy; animal-use approval and welfare; permits or community governance; trial registration where expected; data-use and licensing compliance.
- Publication ethics signals: unattributed overlap, duplicate or redundant publication, inappropriate authorship, undisclosed conflicts, citation or peer-review manipulation.
- Data and image integrity signals: implausible or inconsistent values; duplicated, mirrored, spliced or selectively cropped images; figure and legend mismatch; inconsistent sample sizes; unexplained exclusions; unavailable or contradictory source data.
- Safety and societal risk: dual use, biosafety, cybersecurity disclosure, privacy or re-identification, discriminatory or equity harm, environmental or community harm.
- Escalation: record the observable facts, their location and why they matter; do not accuse authors of intent; do not investigate beyond the review; raise the concern confidentially with the editor; ask for specialist review where needed.

## Feasibility

- Expertise gap classes: nonmaterial (proceed); bounded (main contribution assessable, one component not); material (specialist review needed); fundamental (return the assignment). Do not mask a gap with confident but unsupported criticism.
- Access problem classes: nonessential (note it); important but resolvable (request it through the editor); central to validity or reproducibility (pause); prohibited or impossible (alert the editor). Record the artifact name, link, version and failure mode; do not substitute speculation for unavailable evidence.
- Dispositions: proceed to deep review (conflicts manageable, expertise sufficient, package complete enough, no unresolvable threshold problem); proceed with declared limitation (a bounded component needs another reviewer); pause pending editorial clarification (essential materials, access, scope or specialist review unresolved); return without full review (conflict, inadequate expertise, inaccessible central evidence or time prevents a fair review); escalate confidentially (credible ethics, integrity, safety, legal or confidentiality concern).
