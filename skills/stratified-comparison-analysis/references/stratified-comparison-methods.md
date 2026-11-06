---
created: "2026-11-04T23:12:25Z"
updated: "2026-11-04T23:12:25Z"
---

# Stratified comparison methods

Method detail for the Factors, Strata, Manifestation matrix, Cross-strata comparison, Synthesis and Limitations sections.

## Factors section

Where candidate factors come from:
- Literature: established dimensional frameworks and factor taxonomies in review papers and meta-analyses of the domain; note for each candidate why it should matter for the research questions.
- The user or domain experts: factors they name or confirm.
- Case-level data with many candidate variables: exploratory factor analysis can group the variables into dimensions; keep only dimensions that make conceptual sense.

Column content:
- Definition: the explicit criterion for observing or measuring the factor (for example, company size by employee count).
- Scale: nominal, ordinal, interval or ratio.
- Levels: the discrete categories, or the boundaries cut on a continuous factor.

## Strata section

Strategy, written as one line:
- A priori: predefined categories from theory or an established taxonomy (demographic groups, organization types); suits factors whose categories are well established; may miss patterns the categories do not capture.
- Post-hoc: groups found by clustering the cases (k-means, hierarchical clustering, latent class analysis); needs case-level data and larger samples; interpretation can be hard.
- Hybrid: stratify on established dimensions, then subdivide with data-driven methods, or cluster on factor scores.

Method, written as one line:
- Single factor: order the cases by the factor value (ordinal or continuous factors), set the number of strata, apply cutpoints or category definitions, assign each case, then check the strata rules.
- Complete factorial: one stratum per combination of factor levels; the number of strata is the product of the levels per factor (3 levels by 2 levels by 4 levels gives 24 strata).
- Decision tree (case-level data): split on the factor with the greatest variance reduction, split each branch on the next factor, and stop when a stratum reaches the minimum size, the variance reduction falls below a threshold, or a maximum depth is reached; the end nodes are the strata.
- Cluster-based (case-level data): cluster on several factors at once; choose the number of clusters by silhouette coefficient (above 0.50), Calinski-Harabasz index (higher is better), gap statistic and interpretability; label each cluster by its factor profile.

Validation with case-level data: stratum size against the minimum (adjust for the effect size sought), low spread on the stratifying factors within each stratum, significant differences on those factors between strata (ANOVA or Kruskal-Wallis), and stability when the boundaries move slightly.

Recovery options when strata fall below the minimum size:
1. Collapse adjacent categories or reduce the factor levels.
2. Use fewer factors, dropping the least important.
3. Relax the minimum, if the goal and a power analysis justify it; say so in Limitations.
4. Gather more cases, if the user can.
5. Ask the user when none of these resolves it.

## Manifestation matrix cells

Presence criterion by element type:
- Attribute: an observable characteristic that meets a stated threshold.
- Behaviour: an action that occurs at a stated minimum frequency.
- Outcome: a result that exceeds a stated baseline.

Detection methods: structured observation against a codebook, document analysis (keyword search with the context checked), surveys or interviews reported in sources, and pattern matching over supplied data. Apply the same criterion and method in every stratum.

What a Present cell carries:
- Form: the specific variant in that stratum (email campaigns rather than social media campaigns).
- Intensity: degree of manifestation on the ordinal or continuous scale named in the matrix legend.
- Prevalence: the proportion of cases in the stratum showing the element, when data or a source gives it.
- Context, mechanism, outcomes or constraints: add the one that explains a difference, when the evidence gives it.

Within-stratum line: which elements are most prevalent or central in the stratum, and which appear together (co-occurrence).

Format example (an excerpt with an intensity legend of low, medium, high):

```text
| Stratum | E1 Annual-plan discount | E2 Usage alerts | E3 Win-back offer |
|---|---|---|---|
| S1 Consumer, monthly plan | Absent [2] | Present, low: monthly email nudge [1] | Not found |
| S2 Business, annual plan | Present, high: discount at renewal [3] | Present, medium: in-app dashboard [3] | Present, low: sales call after lapse [4] |
S1 within: E2 is the only retention element found.
S2 within: E1 and E2 appear together at renewal.
```

## Cross-strata comparison

Structures:
- Pairwise: compare every pair of strata, n(n-1)/2 comparisons for n strata, tracked in a comparison grid; suits a small number of strata (5 or fewer) and targeted hypotheses.
- Aggregate: compare each stratum with all the others pooled; suits many strata and finding each stratum's distinctive profile.
- Hierarchical: for decision-tree strata, compare sibling strata first, then parent with child, tracing differences down the tree.
- Full factorial: a table of strata by elements; read the marginal effect of each factor, then the interactions between factors; suits small factorial structures.

Statistical tests (case-level data only):
- Presence counts: a cross-tabulation of strata by element presence, a chi-square test of independence, Cramér's V for effect size, and pairwise post-hoc tests with Bonferroni correction.
- Proportions: prevalence per stratum with confidence intervals; z-test or Fisher's exact test for differences.
- Intensity on a continuous scale: ANOVA or Kruskal-Wallis for the overall difference; Tukey HSD or Dunn's test pairwise; eta squared or epsilon squared for effect size.
- Many comparisons: apply Bonferroni, Holm-Bonferroni or Benjamini-Hochberg; report unadjusted and adjusted p-values and the effect size beside each test.
- Too many significant results to synthesize: rank them by effect size, report the high-level patterns and put the detail in an appendix.
- Sensitivity: re-run the comparison with alternative stratum boundaries.

## Synthesis

Configurational analysis, when the user asks a causal question and supplies case-level data:
1. Conditions are the stratifying factors; the outcome is an element's presence.
2. Code each case 1 or 0 on every condition and on the outcome; one truth-table row per distinct configuration.
3. A necessary condition is present whenever the outcome occurs: consistency of 0.90 or more (the share of outcome cases that have the condition).
4. A sufficient configuration produces the outcome: coverage of 0.75 or more (the share of the outcome it explains); low coverage marks it as trivial.
5. Look for equifinality: several distinct configurations leading to the same manifestation.

Implications, for an applied request: diagnostic insights (which factor configurations reliably signal a manifestation), intervention targets (which factors can be changed), and configurations that favour the outcome the user wants.

## Limitations section

- Measurement: imperfect definitions of elements or factors, measurement error, proxies used.
- Sampling: non-representative sources or cases, selection bias, coverage gaps.
- Analytical: unmeasured confounders, the limits of causal inference from the design, statistical power.
- Generalizability: the context, period and domain the findings hold for.
