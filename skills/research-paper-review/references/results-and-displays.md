---
created: "2026-11-05T00:07:24Z"
updated: "2026-11-05T00:07:24Z"
---

# Results-and-displays pass

## Results completeness

- Map every stated question, outcome, hypothesis and protocol commitment to a reported result; classify each result as primary, secondary, safety, validation, robustness or exploratory and check its label.
- Negative and null findings: null primary findings, negative effects, failed replications or robustness checks, unsuccessful comparisons, negative controls and adverse findings are reported; a null result carries an effect estimate and interval; absence of evidence is not presented as evidence of absence without adequate precision; central null findings are not omitted from the abstract or discussion.
- Deviations and exclusions affecting results are reported; sample or unit flow is complete (screened, eligible, enrolled, allocated, analysed; for data studies, records and partitions); denominators and missingness are explicit.
- Results report observations; interpretation belongs in the discussion. Flag boundary violations.

## Numerical integrity

- Compare locations: title, abstract, main text, figures, tables, supplement, source data, methods and analysis plan, protocol or preregistration, code output where available.
- Reconcile core values: sample and group sizes, events, means or medians, SDs or SEs, intervals, effect estimates, test statistics, degrees of freedom, P values, performance metrics, follow-up time, percentages and rates, units.
- Arithmetic and flow: totals add up; percentages use the right denominator and match counts; screened minus excluded equals eligible and enrolled minus withdrawals equals analysed where applicable; partitions reconcile with the dataset total; repeated measures are not counted as independent units.
- Units and scales: stated and consistent; log versus raw scale explicit; percent versus proportion not conflated.
- Statistical consistency: effect direction matches group summaries; the interval contains the point estimate; the P value agrees with the interval or test statistic; degrees of freedom are plausible for the design; ratios match exponentiated coefficients; predicted probabilities lie in range; confusion-matrix totals match reported accuracy, precision and recall; corrected and uncorrected P values are labelled.
- Rounding and precision: consistent decimals; no spurious precision; small counts not hidden behind percentages; P values not reported as zero; values within logical bounds and metric constraints.
- Anomaly signals: identical values where variation is expected; copied rows or columns; impossible totals; mismatched labels or reference groups; a figure point missing from the table; an abstract value differing from the main result; a supplement contradicting the main claim.
- Escalation discipline: document the exact locations and the discrepancy; check source data or code where available; request correction or clarification first when plausible; distinguish a typographic or reporting error from an analytical error; raise a possible integrity concern confidentially when discrepancies are material, repeated, unexplained or suggest manipulation.

## Figures and images

- Each display is necessary and has an evidentiary role; identifiers, axes, scales, units and legends (n, error-bar definition, interval level, statistical test) are complete.
- Misleading encodings: truncated or selective axis ranges, inconsistent scales across panels, area or 3D distortion, dual axes implying unsupported comparison, hidden bins, overplotting, colour implying order, inaccessible colours. Visual differences are proportional to numeric ones.
- Raw data and distributions are shown where appropriate; uncertainty is defined, matches the estimate and is not suppressed for central results; error bars are not mistaken for replicate distributions.
- Accessibility and technical quality: colour is not the sole carrier of meaning and contrast is sufficient; labels are legible at publication size; resolution suits review; no raster artifacts or inappropriate interpolation.
- Images: acquisition details; brightness, contrast, filtering or AI restoration disclosed and applied consistently; splicing, compositing and cropping marked and not concealing context; no duplication across conditions or panels; representative images backed by the number of independent experiments and by quantification where the claim requires it; source images available where policy requires.
- Source data for central figures available, and plots reproducible from it.

## Tables

Necessary and not duplicating a figure; complete title, headings and notes (abbreviations, units, denominators, tests); values correct and missingness treated explicitly; comparisons report estimate, uncertainty and test; readable structure.

## Equations, algorithms and proofs

- Notation: every symbol defined before use and used consistently.
- Equations and derivations: each equation matches its verbal claim with inputs, outputs and constraints stated; each step follows from the prior line, with equality, approximation and inequality distinguished; the derived result has the right sign, sensible limiting behaviour, compatible units, and matches the implementation and reported outputs.
- Assumptions explicit and necessary; boundary and degenerate cases handled.
- Theorems: definitions precede the theorem; assumptions, quantifiers, constants and scope stated; the claim is no stronger than the proof. Proofs address every component, cite lemmas that apply under the given assumptions, and a proof sketch is identified as one. An empirical result is not a proof; an asymptotic theorem is not a finite-sample guarantee; an upper bound is not exact complexity; a special case is not generalized beyond its assumptions.
- Complexity claims define the input-size variables and computational model and distinguish worst-case, expected and empirical runtime; empirical runtime claims state hardware, problem sizes and repetitions, and a complexity conclusion does not rest on a small benchmark alone.
- Pseudocode is complete (inputs, outputs, stopping criterion) and matches the implementation.

## Cross-cutting audits

- Each central display agrees with the text and the claim it supports.
- Central evidence sits in the main manuscript; critical negative or robustness results are not buried in the supplement; extended-data panels are cited in the text; the supplement is consistent with the main manuscript and accessible.

## Ratings

| Dimension | Scale |
|---|---|
| Results completeness | Strong: all planned and material results, flow, deviations, exclusions, uncertainty and exploratory status transparent. Adequate: central results complete with limited gaps. Weak: incomplete outcome reporting or unclear analysis populations. Defective: missing primary outcomes, selective reporting or undocumented changes prevent reliable evaluation. |
| Numerical integrity | Strong: all artifacts reconcile. Adequate: minor correctable discrepancies only. Weak: multiple inconsistencies or unclear denominators undermine confidence. Defective: material contradictions, impossible values or unexplained anomalies affect central findings. |
| Figures and images | Strong: relevant, self-contained, honest, accessible, source-supported, reproducible. Adequate: sound central displays with limited presentation issues. Weak: incomplete legends, misleading encodings, suppressed distributions or uncertainty, or unclear image handling. Defective: manipulated or selective images, material visual misrepresentation or an unreproducible central display. |
| Tables | Strong: necessary, self-contained, accurate, nonduplicative, statistically complete. Adequate: limited formatting or note deficiencies. Weak: unclear denominators, missing notes, redundancy or ambiguous comparison. Defective: material numerical or statistical inconsistency obscures or reverses a central result. |
| Equations, algorithms and proofs | Strong: notation, assumptions, derivations, boundaries, proofs, complexity and implementation coherent and auditable. Adequate: sound core result with minor gaps. Weak: important derivation, assumption, complexity or implementation ambiguity. Defective: theorem and proof mismatch, invalid derivation, undefined algorithm behaviour or unsupported complexity claim. |

## Pass-specific cautions

Do not demand raw-data display where privacy, ethics, security or scale make it inappropriate; a polished display is not evidence of a valid analysis; do not infer misconduct from a discrepancy alone; do not require every display type; visual non-overlap of error bars is not a statistical test; representative images are not quantitative evidence; supplementary placement must not hide essential limitations, null findings or central evidence.
