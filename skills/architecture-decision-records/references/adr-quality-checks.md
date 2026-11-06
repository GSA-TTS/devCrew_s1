---
created: "2026-11-04T20:13:13Z"
updated: "2026-11-04T20:13:13Z"
---

# ADR quality checks

Run every check on each ADR, drafted or supplied. Write the result as a table: Check, Result (met, not met or pending), Evidence (the section or a short phrase from the ADR), Fix (for each result not met).

## Anti-patterns

1. Fairy Tale (wishful thinking): the decision is justified by a one-sided argument, benefits only, with no realistic trade-off or risk. Signs: an option with no cons; a rationale that restates the purpose of the thing chosen as its justification. Fix: add the drawbacks, risks, added complexity, cost and single points of failure.
2. Sales Pitch: a biased presentation that favours a predetermined solution. Signs: superlatives (industry-leading, cutting-edge, revolutionary, outstanding, unrivalled) and claims with no evidence. Fix: replace each with a factual statement backed by a measurement, benchmark, cost analysis or cited source, naming the pro and the con.
3. Dummy Alternative: clearly non-viable options set beside the preferred one to make the evaluation look thorough. Signs: an option dismissed in one phrase, such as building the component from scratch or keeping an approach already known to fail, while realistic alternatives (other existing products, an incremental or hybrid approach) are missing. Fix: replace it with a genuinely viable alternative that has its own pros and cons.
4. Free Lunch Coupon: benefits claimed without their costs, risks or trade-offs. Signs: Consequences with no negative item, no cost, effort or timeline, or no mention of new coupling the choice introduces. Fix: add the costs, effort, timeline, risks and new coupling.

## Evidence and completeness

5. Alternative viability: two or three genuinely viable alternatives, compared on the same criteria, each with pros and cons.
6. Evidence standards: every claim in the rationale is supported by data, a benchmark, a measurement, a standard or research, and each outside source is cited.
7. Consequence realism: timelines, resource estimates and risk assessments are grounded in the user's data or in cited empirical data or benchmarks.
8. Fitness functions: at least two are defined, with thresholds.
9. Stakeholder approval: the sign-offs of the stakeholders named in the ADR. For a draft this is pending; the Evidence column names who must sign off.

## Example of a fix (Free Lunch Coupon)

```text
Before: Moving session state into a shared cache lets any app server
handle any request.

After: Moving session state into a shared cache lets any app server
handle any request, but adds a cache cluster the operations team must
run and monitor, makes the cache a dependency of every login, and needs
a plan for sessions lost when a cache node fails.
```
