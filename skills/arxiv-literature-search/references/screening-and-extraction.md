---
created: "2026-11-05T00:32:47Z"
updated: "2026-11-05T00:32:47Z"
---

# Screening, paper entries, synthesis and evidence categories

## Screening one paper

1. Title: does it directly address the cluster's research question? An explicit match points to Green, a related but indirect topic to Yellow, a tangential one to Red.
2. Abstract: note the research problem, the proposed solution and the key findings; flag the methodology (empirical or theoretical), the dataset or context, and how far it applies to the user's topic.
3. Structure: scan the section headings for the experimental setup, datasets and empirical claims, and whether the contribution is theoretical or applied.

Tags:

- Green (read in full): directly addresses the research question and is likely to give novel findings.
- Yellow (review later): related but not directly relevant; may give context.
- Red (skip): out-of-scope topic, fails an inclusion or exclusion criterion, is older than 5 years unless seminal, or is not peer reviewed when the user's criteria require peer review.

The aim is to bring 50 to 100 screened papers down to about 15 to 25 Green papers per cluster.

## Paper entry fields

Metadata:
- Title; Authors; Date and venue (the venue the paper states, or preprint); arXiv ID; Citation count, with the index it came from; Relevance tag; Read basis (full text or abstract only).

Problem and context:
- Problem statement in 1 to 2 sentences; Research question (stated, or inferred from the gaps the paper names and labelled inferred); Motivation (quantitative evidence of the problem's scale, or the qualitative reason); Relation to the user's topic.

Methodology:
- Type: Empirical (measurement, user study, experiment), Theoretical (formal analysis, proof), Implementation (architecture, tool, framework) or Literature survey; Setting and sample (where, who, what scale, and how far the findings generalize); Key technical approach; Limitations and scope constraints.

Key findings:
- Findings 1 to 3, each a specific quantitative or qualitative result with exact numbers as the paper states them and statistical significance where given; Critical caveats.

Assessment:
- Strengths (rigor, novelty, applicability); Weaknesses (limitations the authors state and gaps you identify, such as confounds, small samples, artificial settings); Relevance: Direct application (validates or refutes a claim of the user's), Tangential (background or context) or Gap-closing (addresses an uncertainty in the user's material).

Extractable insights:
- Practitioner action; Quantitative evidence (metrics, thresholds, benchmarks); Validation or contradiction of the user's claims; Research gaps identified.

## Synthesis per cluster

- Compare findings: whether measurements align, where papers agree and where they conflict, and whether a difference comes from methodology, context or a genuinely different result.
- Trends over time: emerging against established practices across the papers' dates.
- Evidence matrix: one row per Green paper, one column per key dimension of the cluster (model type, dataset size or error rate, for example), cells holding what each paper reports.
- Research gaps: questions the papers together do not answer, methodological limits they share, contexts that are under-represented.
- Cluster summary: state of the art, consensus findings, open questions and recommended next steps.

## Evidence categories for a claim

- Strong empirical support: several peer-reviewed papers with consistent findings.
- Theoretical support: well argued but not empirically validated.
- Emerging evidence: few papers, preliminary findings.
- No direct evidence: a gap in the literature; the claim is not supported by published research.

A claim with no direct evidence is flagged for further research or expert validation.
