# EXPERIMENT-001: A/B Experimentation Protocol

**Version**: 1.0
**Last Updated**: 2025-11-17
**Status**: Active
**Owner**: Product-Owner

## Objective

Design, deploy, monitor, and analyze statistically rigorous A/B experiments to validate product hypotheses, optimize user experiences, and inform data-driven product decisions with quantifiable impact.

## Tool Requirements

- **TOOL-DATA-002** (Statistical Analysis): A/B testing calculations, statistical significance testing, sample size determination, and experimental data analysis
  - Execute: Sample size calculations, chi-square tests, Bayesian analysis, confidence intervals, effect size measurement, power analysis
  - Integration: Statistical analysis platforms, data science tools, experimental analytics, A/B testing frameworks, Jupyter notebooks
  - Usage: Hypothesis testing, conversion rate analysis, statistical validation, experimental design optimization, results interpretation

- **TOOL-CICD-001** (Pipeline Platform): Automated experiment deployment, feature flag management, and controlled rollout orchestration
  - Execute: Experiment deployment automation, variant traffic control, feature flag management, automated rollback, deployment validation
  - Integration: CI/CD platforms, feature flag systems, deployment pipelines, automated testing, rollout automation tools
  - Usage: Experiment deployment, traffic splitting, automated monitoring, deployment validation, rollout management

- **TOOL-COLLAB-001** (GitHub Integration): Experiment documentation, result archiving, stakeholder coordination, and version control management
  - Execute: Experiment design documentation, results reporting, stakeholder notifications, artifact archiving, version control
  - Integration: CLI commands (gh, git), API calls, repository operations, documentation systems, collaboration workflows
  - Usage: Experiment documentation, results archiving, team coordination, stakeholder communication, version control

- **TOOL-DATA-003** (Privacy Management): User consent validation, experiment data privacy, and compliance enforcement for A/B testing data collection
  - Execute: Consent validation, privacy compliance checking, data collection monitoring, user segmentation privacy, anonymization validation
  - Integration: Privacy management platforms, consent systems, data protection tools, compliance validation, user data systems
  - Usage: Experiment privacy compliance, user consent verification, data collection validation, privacy impact assessment

## Trigger

- Hypothesis formulated requiring empirical validation (conversion optimization, feature adoption, pricing)
- STRAT-PRIO-001 identifies high-impact, high-uncertainty feature requiring testing before full rollout
- User feedback (FEEDBACK-INGEST-001) suggests potential improvement but impact unknown
- Quarterly experimentation roadmap requires new experiment launch
- Previous experiment completed, need follow-up test (multi-variate, sequential)
- Product-market fit validation for new segment or geography

## Agents

- **Primary**: Product-Owner
- **Supporting**: Data Scientist (statistical analysis, sample size calculation), Engineering (variant deployment)
- **Review**: Core Leadership Group (rollout decisions with revenue/risk implications)

## Prerequisites

- Hypothesis clearly defined with success metric
- Experiment infrastructure operational via **TOOL-CICD-001** (feature flags, analytics tracking, A/B testing platform)
- Sufficient user traffic for statistical power (≥1000 users per variant for 80% power) validated by **TOOL-DATA-002**
- Baseline metric established (pre-experiment conversion rate, engagement level) through **TOOL-DATA-002**
- Engineering capacity available for variant implementation (if code changes required)
- Legal/compliance approval for experiments affecting pricing, data collection, or user experience validated by **TOOL-DATA-003**

## Steps

### Step 1: Define Experiment Design (Estimated Time: 30m)
**Action**:
Create experiment design document at `/docs/product/experiments/design_{{experiment_id}}.yaml`:

```yaml
experiment_id: exp_{{increment_id}}
name: "{{Descriptive experiment name}}"
owner: Product-Owner
status: design # design → deployed → running → completed → analyzed

hypothesis:
  statement: "{{If we do X, then Y will happen, because Z}}"
  expected_direction: increase # increase | decrease | no_change
  expected_magnitude: "{{+10% conversion rate}}"

variants:
  - name: control
    description: "Current experience (baseline)"
    traffic_allocation: 50%

  - name: variant_a
    description: "{{New feature/design/copy}}"
    traffic_allocation: 50%
    implementation_details: "{{Button color changed from blue to green}}"

success_metric:
  primary: conversion_rate # activation_rate | retention_d7 | revenue_per_user
  definition: "{{Users who complete checkout / Users who view product page}}"
  baseline_value: 12.5%
  minimum_detectable_effect: 2% # MDE - smallest change worth detecting

secondary_metrics:
  - metric: bounce_rate
    expected_change: decrease
  - metric: time_on_page
    expected_change: increase

guardrail_metrics:
  - metric: page_load_time
    threshold: "<3 seconds"
    action_if_violated: "Stop experiment immediately"
  - metric: error_rate
    threshold: "<0.5%"
    action_if_violated: "Stop experiment immediately"

sample_size:
  calculation_method: "Two-proportion z-test"
  alpha: 0.05 # significance level (5% false positive rate)
  power: 0.80 # 80% power (20% false negative rate)
  minimum_per_variant: 3850 # calculated based on baseline=12.5%, MDE=2%, alpha=0.05, power=0.80
  total_required: 7700
  expected_duration_days: 14 # based on daily traffic of 550 users

exclusion_criteria:
  - "Users who signed up <7 days ago (activation not stabilized)"
  - "Bot traffic (identified via user-agent)"
  - "Internal company users (email domain @company.com)"

risks:
  - risk: "Variant A reduces conversion, loses revenue"
    mitigation: "Monitor daily, stop if conversion drops >5%"
    probability: low
  - risk: "Sample size insufficient due to seasonality"
    mitigation: "Extend duration if needed, pause during holidays"
    probability: medium
```

**Expected Outcome**: Complete experiment design document with all parameters defined
**Validation**: Hypothesis is testable, sample size calculated, success metrics measurable, risks identified

### Step 2: Calculate Sample Size and Duration (Estimated Time: 15m)
**Action**:
- Use statistical power calculator or Python scipy.stats:
```python
from scipy.stats import norm
import math

def calculate_sample_size(baseline_rate, mde, alpha=0.05, power=0.80):
    z_alpha = norm.ppf(1 - alpha/2)  # 1.96 for alpha=0.05
    z_beta = norm.ppf(power)          # 0.84 for power=0.80
    p1 = baseline_rate
    p2 = baseline_rate + mde
    p_avg = (p1 + p2) / 2

    n = (z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) +
         z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (p2 - p1) ** 2

    return math.ceil(n)

# Example: baseline=12.5%, MDE=2%, alpha=0.05, power=0.80
n_per_variant = calculate_sample_size(0.125, 0.02)  # Returns ~3850
```

- Estimate experiment duration:
```
Duration (days) = Total sample size / (Daily traffic * Eligible user %)
Duration = 7700 / (1000 * 0.55) = 14 days
```

- Adjust for:
  - Weekday vs. weekend traffic patterns (run full weeks)
  - Seasonality (avoid major holidays, sale periods)
  - Minimum runtime (at least 7 days to capture weekly patterns)

**Expected Outcome**: Statistically valid sample size, realistic timeline
**Validation**: Sample size provides 80% power to detect MDE, duration accounts for traffic patterns

### Step 3: Implement Variants and Instrumentation (Estimated Time: varies, 2-5 days engineering)
**Action**:
- Coordinate with Engineering team to implement variant code
- Use feature flag system (LaunchDarkly, Optimizely, custom) to control variant exposure
- Add analytics tracking for all success metrics and guardrail metrics:
```javascript
// Example tracking code
trackEvent('experiment_exposure', {
  experiment_id: 'exp_042',
  variant: assignedVariant,
  user_id: userId,
  timestamp: Date.now()
});

trackEvent('conversion', {
  experiment_id: 'exp_042',
  variant: assignedVariant,
  user_id: userId,
  conversion_type: 'checkout_completed',
  value: orderTotal
});
```

- Implement guardrail monitoring (page load time, error rates)
- Test variant assignment logic (50/50 split, consistent assignment per user)
- QA test both control and variant experiences

**Expected Outcome**: Variants implemented, tracking instrumented, QA passed
**Validation**: Both variants render correctly, assignment is random and consistent, all events tracked

### Step 4: Deploy Experiment (Estimated Time: 30m)
**Action**:
```bash
# Deploy via GitHub Actions workflow
gh workflow run experiment-deploy.yml \
  --field experiment_id=exp_042 \
  --field traffic_percent=100 \
  --field variants="control:50,variant_a:50"

# Verify deployment
curl https://api.company.com/experiments/exp_042/status
# Expected: {"status": "running", "traffic": 100, "variants": {"control": 50, "variant_a": 50}}

# Create monitoring dashboard link
# Mixpanel/Amplitude: https://analytics.company.com/experiments/exp_042
```

- Update experiment status in design YAML: `status: running`
- Set auto-stop conditions in monitoring platform:
  - Guardrail metric violations
  - Statistical significance reached (p<0.05) AND minimum sample size met
  - Maximum duration exceeded (4 weeks)
- Notify stakeholders of experiment launch via COMM-LIAISON-001

**Expected Outcome**: Experiment live, traffic split 50/50, monitoring active
**Validation**: Variant assignment logs show 50/50 split, tracking events flowing to analytics

### Step 5: Monitor Experiment Progress (Estimated Time: 10m daily)
**Action**:
Daily monitoring checklist:
- ✅ Check sample size progress: `current_users / target_users * 100%`
- ✅ Verify traffic split: Control vs. Variant A (should be ~50/50, allow ±2% variance)
- ✅ Monitor guardrail metrics: Page load time <3s, error rate <0.5%
- ✅ Early trend detection: Is variant performing as hypothesized?
- ✅ Sequential testing: Update Bayesian credible intervals daily (if using Bayesian approach)
- ✅ Anomaly detection: Traffic drops, bot spikes, deployment issues

Automated alerts:
- Guardrail violation: Immediate email + Slack notification
- Sample size milestone: 25%, 50%, 75%, 100% progress notifications
- Statistical significance reached: Auto-notification to review results

**Expected Outcome**: Experiment running smoothly, progress on track
**Validation**: Daily monitoring logs, no guardrail violations, traffic split stable

### Step 6: Collect and Validate Data (Estimated Time: 20m at experiment end)
**Action**:
- Export raw experiment data from analytics platform:
```sql
SELECT
  user_id,
  experiment_id,
  variant,
  exposed_at,
  converted,
  conversion_value,
  session_duration,
  bounce
FROM experiment_events
WHERE experiment_id = 'exp_042'
  AND exposed_at BETWEEN '2025-10-08' AND '2025-10-22'
```

- Save to `/integrations/analytics/experiment_exp_042_results.json`
- Data quality checks:
  - ✅ No duplicate user_id entries (each user in one variant only)
  - ✅ Exposure counts match expected sample size (±5%)
  - ✅ Variant split is 50/50 (±2%)
  - ✅ Success metric data complete (no nulls for converted users)
  - ✅ Timestamps valid (all within experiment window)

**Expected Outcome**: Clean dataset ready for statistical analysis
**Validation**: Data quality checks pass, no anomalies detected

### Step 7: Perform Statistical Analysis (Estimated Time: 30m)
**Action**:
Apply A/B Reasoning pattern for rigorous analysis:

**Frequentist Approach** (default):
```python
from scipy.stats import chi2_contingency

# Data
control_conversions = 487
control_total = 3850
variant_conversions = 562
variant_total = 3850

# Conversion rates
control_rate = control_conversions / control_total  # 12.6%
variant_rate = variant_conversions / variant_total  # 14.6%
lift = (variant_rate - control_rate) / control_rate * 100  # +15.9%

# Chi-square test for statistical significance
contingency_table = [[control_conversions, control_total - control_conversions],
                     [variant_conversions, variant_total - variant_conversions]]
chi2, p_value, dof, expected = chi2_contingency(contingency_table)

# Results
print(f"Control rate: {control_rate:.2%}")
print(f"Variant rate: {variant_rate:.2%}")
print(f"Lift: {lift:.1f}%")
print(f"p-value: {p_value:.4f}")
print(f"Significant: {p_value < 0.05}")  # True if p<0.05
```

**Bayesian Approach** (for early stopping or continuous monitoring):
```python
import pymc3 as pm

with pm.Model() as model:
    # Priors
    p_control = pm.Beta('p_control', alpha=1, beta=1)
    p_variant = pm.Beta('p_variant', alpha=1, beta=1)

    # Likelihood
    control_obs = pm.Binomial('control_obs', n=control_total, p=p_control, observed=control_conversions)
    variant_obs = pm.Binomial('variant_obs', n=variant_total, p=p_variant, observed=variant_conversions)

    # Difference
    delta = pm.Deterministic('delta', p_variant - p_control)

    trace = pm.sample(2000)

# Probability that variant is better
prob_variant_better = (trace['delta'] > 0).mean()  # e.g., 97.5%
print(f"Probability variant better: {prob_variant_better:.1%}")
```

**Effect Size and Confidence Interval**:
```python
from statsmodels.stats.proportion import confint_proportions_2indep

ci_low, ci_high = confint_proportions_2indep(
    variant_conversions, variant_total,
    control_conversions, control_total,
    method='wald'
)

print(f"95% CI for lift: [{ci_low:.2%}, {ci_high:.2%}]")
```

**Expected Outcome**: Statistical significance determined, effect size quantified
**Validation**: p-value calculated correctly, confidence intervals sensible, multiple testing correction applied if needed

### Step 8: Generate Results Report (Estimated Time: 25m)
**Action**:
Create `results_exp_042.md`:

```markdown
# Experiment Results: exp_042 - Green CTA Button Test

**Experiment ID**: exp_042
**Owner**: Product-Owner
**Run Dates**: 2025-10-08 to 2025-10-22 (14 days)
**Status**: ✅ Completed

## Hypothesis
**Statement**: If we change the CTA button color from blue to green, then conversion rate will increase by ≥2%, because green signals "go" and creates urgency.

**Result**: ✅ **VALIDATED** - Conversion rate increased by 2.0 percentage points (15.9% relative lift)

## Experiment Setup
- **Variants**: Control (blue button) vs. Variant A (green button)
- **Traffic Split**: 50% / 50%
- **Sample Size**: 7,700 total (3,850 per variant)
- **Primary Metric**: Checkout conversion rate
- **Duration**: 14 days

## Results Summary

### Primary Metric: Conversion Rate
| Variant | Conversions | Total Users | Rate | Lift vs. Control |
|---------|-------------|-------------|------|------------------|
| Control | 487 | 3,850 | 12.6% | - |
| Variant A (Green) | 562 | 3,850 | 14.6% | **+2.0pp (+15.9%)** |

**Statistical Significance**: p = 0.0032 (p < 0.05) ✅ **SIGNIFICANT**
**95% Confidence Interval**: [+0.7pp, +3.3pp]
**Conclusion**: Variant A significantly outperforms Control with 99.7% confidence.

### Secondary Metrics
| Metric | Control | Variant A | Change | Significant |
|--------|---------|-----------|--------|-------------|
| Bounce Rate | 42.1% | 38.7% | -3.4pp | ✅ Yes (p=0.011) |
| Time on Page | 2m 15s | 2m 28s | +13s | ✅ Yes (p=0.021) |
| Add to Cart | 28.3% | 30.1% | +1.8pp | ✅ Yes (p=0.041) |

### Guardrail Metrics
| Metric | Control | Variant A | Threshold | Status |
|--------|---------|-----------|-----------|--------|
| Page Load Time | 1.8s | 1.9s | <3s | ✅ Pass |
| Error Rate | 0.2% | 0.3% | <0.5% | ✅ Pass |

## Segment Analysis
Performance varied by segment:
- **New Users**: Variant A lift +18.2% (stronger effect)
- **Returning Users**: Variant A lift +12.1%
- **Mobile**: Variant A lift +14.5%
- **Desktop**: Variant A lift +17.3%

**Insight**: Green button particularly effective for new users and desktop traffic.

## Business Impact Estimate
Based on current traffic (1,000 daily product page views):
- **Baseline conversions/day**: 126 (12.6% * 1,000)
- **With Variant A**: 146 (14.6% * 1,000)
- **Additional conversions/day**: +20
- **Additional conversions/quarter**: +1,800
- **Estimated revenue impact/quarter**: +$90,000 (assuming $50 AOV)

## Recommendation
✅ **ROLLOUT VARIANT A TO 100%**

**Rationale**:
1. Strong statistical significance (p=0.0032, well below 0.05 threshold)
2. Meaningful business impact (+$360K annual revenue at current traffic)
3. No negative effects on guardrail metrics
4. Positive secondary metrics (lower bounce, higher engagement)
5. Effect consistent across all segments

**Rollout Plan**:
1. Deploy green button to 100% traffic immediately
2. Monitor for 7 days post-rollout to confirm sustained lift
3. Update design system to make green the default CTA color
4. Add to ROADMAP-UPDATE-001 as shipped feature
5. Update METRIC-TRACK-001 baseline conversion rate to 14.6%

## Learnings
1. Color psychology impacts conversion (green > blue for CTAs)
2. Effect size larger than expected (15.9% vs. 10% hypothesized)
3. New users most responsive to visual changes (18% lift)
4. Future experiments: Test other CTA colors (orange, red), test on other pages

## Appendix
- **Raw Data**: `/integrations/analytics/experiment_exp_042_results.json`
- **Analysis Notebook**: `/notebooks/exp_042_analysis.ipynb`
- **Design Doc**: `/docs/product/experiments/design_exp_042.yaml`
```

**Expected Outcome**: Comprehensive results report with recommendation
**Validation**: All metrics reported, statistical analysis correct, recommendation actionable

### Step 9: Make Rollout Decision (Estimated Time: 15m)
**Action**:
Decision framework based on results:

**IF** p_value < 0.05 **AND** lift ≥ MDE **AND** guardrails pass:
  → **ROLLOUT TO 100%**

**IF** p_value < 0.05 **AND** lift < MDE **AND** guardrails pass:
  → **ROLLOUT** (statistically significant, even if smaller effect than hoped)

**IF** p_value ≥ 0.05:
  → **NO ROLLOUT** (not statistically significant, could be chance)
  → **OPTIONS**: Extend duration for more sample, redesign experiment, abandon hypothesis

**IF** guardrails violated:
  → **NO ROLLOUT** (even if conversion improves, UX degraded)

**IF** results inconclusive:
  → **ESCALATE TO HITL** for business judgment call

Document decision in design YAML:
```yaml
decision:
  outcome: rollout_100 # rollout_100 | rollout_partial | no_rollout | extend_duration
  decided_by: Product-Owner
  decided_at: 2025-10-22
  rationale: "p=0.0032 < 0.05, lift=+15.9% > MDE=10%, guardrails pass, strong business case"
  rollout_date: 2025-10-23
```

**Expected Outcome**: Clear rollout decision with rationale
**Validation**: Decision follows framework, rationale documented, rollout plan defined

### Step 10: Execute Rollout and Archive (Estimated Time: 20m)
**Action**:
```bash
# Rollout winning variant to 100%
gh workflow run experiment-rollout.yml \
  --field experiment_id=exp_042 \
  --field winning_variant=variant_a \
  --field traffic_percent=100

# Update backlog with learnings
# Add task to design system: "Update CTA button color to green"

# Archive experiment artifacts
git add docs/product/experiments/design_exp_042.yaml
git add docs/product/experiments/results_exp_042.md
git add integrations/analytics/experiment_exp_042_results.json
git commit -m "Archive exp_042: Green CTA button (+15.9% conversion) - ROLLOUT"

# Notify stakeholders
gh issue comment {{related_issue}} --body "Experiment exp_042 completed: Green CTA button increased conversion by 15.9% (p=0.0032). Rolled out to 100% traffic. Estimated +$360K annual revenue."

# Update METRIC-TRACK-001 baseline
# Edit /docs/product/kpis/kpi_definitions.yaml
# baseline_conversion_rate: 14.6%  # Updated from 12.6% based on exp_042
```

**Expected Outcome**: Variant rolled out, artifacts archived, stakeholders notified
**Validation**: 100% traffic on winning variant, git commit successful, baseline metrics updated

## Expected Outputs

- **Primary Artifact**: Experiment results report `results_exp_{{id}}.md`
- **Secondary Artifacts**:
  - Experiment design YAML
  - Raw data JSON/CSV
  - Analysis notebook (Python/R)
  - Rollout decision documentation
  - Git commits archiving experiment
- **Success Indicators**:
  - Statistical significance achieved (p < 0.05) OR conclusive null result
  - Decision made (rollout/no rollout) with clear rationale
  - Business impact quantified ($revenue, conversions)
  - Learnings documented for future experiments

## Failure Handling

### Failure Scenario 1: Insufficient Sample Size (Low Traffic)
- **Symptoms**: After 4 weeks, only 40% of target sample size collected
- **Root Cause**: Traffic lower than estimated, experiment too narrow (targeting small segment)
- **Impact**: High - Cannot reach statistical power, results inconclusive
- **Resolution**:
  1. Calculate actual daily traffic and revise duration estimate
  2. If extended duration >8 weeks: Consider widening eligibility criteria
  3. If still insufficient: Lower MDE (accept detecting smaller effect), reduce power to 70%
  4. Document limitation in results: "Underpowered, interpret with caution"
  5. If critical experiment: Run on multiple pages/touchpoints simultaneously
- **Prevention**: Pre-experiment traffic analysis, conservative sample size estimates

### Failure Scenario 2: Guardrail Metric Violation
- **Symptoms**: Variant A shows +20% conversion but page load time increases to 4.5s (threshold: <3s)
- **Root Cause**: Variant implementation introduced performance regression
- **Impact**: Critical - UX degraded despite conversion improvement
- **Resolution**:
  1. Immediately stop experiment (0% traffic to variant)
  2. Notify Engineering to fix performance issue
  3. Document violation in results report
  4. Decision: **NO ROLLOUT** until performance fixed
  5. Restart experiment after fix deployed
- **Prevention**: Thorough QA of variant implementation, automated performance testing

### Failure Scenario 3: Novelty Effect (Metric Degrades Over Time)
- **Symptoms**: First week shows +18% lift, second week +12%, third week +5%
- **Root Cause**: Users initially attracted to change, but effect fades as novelty wears off
- **Impact**: Medium - True long-term effect smaller than initial results suggest
- **Resolution**:
  1. Extend experiment to 4-6 weeks to measure stabilized effect
  2. Analyze cohorts by exposure duration (week 1 vs. week 4)
  3. Report stabilized effect size (e.g., +5% sustained lift)
  4. Rollout decision based on long-term effect, not initial spike
- **Prevention**: Run experiments for minimum 2 weeks, analyze temporal trends

### Failure Scenario 4: Multiple Testing Problem (Running 20 Experiments Simultaneously)
- **Symptoms**: 3 of 20 experiments show p<0.05, but could be false positives
- **Root Cause**: With α=0.05, expect 1 false positive per 20 tests by chance
- **Impact**: Medium - Risk of rolling out ineffective changes
- **Resolution**:
  1. Apply Bonferroni correction: Adjusted α = 0.05 / 20 = 0.0025
  2. Only results with p<0.0025 considered significant
  3. Alternatively: False Discovery Rate (FDR) control via Benjamini-Hochberg
  4. Prioritize experiments with largest effect sizes and strongest priors
- **Prevention**: Limit simultaneous experiments, use Bayesian approach with informative priors

### Failure Scenario 5: Simpson's Paradox (Variant Wins Overall but Loses in Every Segment)
- **Symptoms**: Overall: Variant A +5% lift. Mobile: -2%, Desktop: -3%, Tablet: -1%
- **Root Cause**: Confounding variable (e.g., variant shown more to high-converting segment)
- **Impact**: High - Overall result is misleading, wrong decision
- **Resolution**:
  1. Verify randomization was truly random across segments
  2. Check for sampling bias (e.g., time-of-day effects)
  3. Perform stratified analysis (segment-specific tests)
  4. Decision based on segment-specific results, not overall
  5. If randomization flawed: Discard experiment, re-run with proper randomization
- **Prevention**: Pre-check randomization balance across segments, use stratified randomization

## Rollback/Recovery

**Trigger**: Guardrail violation, performance regression, negative user feedback spike post-rollout

**Standard Approach**: Invoke **P-RECOVERY** protocol for transactional rollback

**P-RECOVERY Integration**:
1. Before Step 4 (Deploy): CreateBranch for experiment code (`experiment_exp_042_deploy`)
2. Execute deployment with feature flag (enables instant rollback)
3. On success (experiment completes, positive results): MergeBranch to make permanent
4. On failure (guardrail violation, negative results): DiscardBranch, revert to control
5. P-RECOVERY handles retry logic for deployment issues
6. P-RECOVERY escalates to NotifyHuman if persistent deployment failures

**Custom Rollback** (experiment-specific):
1. **Instant Feature Flag Rollback**: Set traffic to 0% for failing variant
2. **Data Preservation**: Archive all experiment data before rollback
3. **User Communication**: If users noticed the variant, explain change via support channels
4. **Post-Mortem**: Document why experiment failed, prevent similar issues

**Verification**: Traffic reverted to 100% control, metrics return to baseline
**Data Integrity**: Low risk - experiment data archived, user experience restored

## Validation Criteria

### Quantitative Thresholds
- Sample size achieved: ≥100% of calculated minimum (or documented reason if <100%)
- Statistical power: ≥80% (or explicitly lowered with justification)
- Significance level: p < 0.05 for frequentist (or Bayesian probability >95%)
- Guardrail metrics: All within thresholds (no violations)
- Traffic split variance: ±2% from target (e.g., 48-52% for 50/50 split)

### Boolean Checks
- Hypothesis clearly stated before experiment: Pass/Fail
- Sample size calculation documented: Pass/Fail
- Randomization verified (no sampling bias): Pass/Fail
- Statistical analysis performed correctly: Pass/Fail
- Rollout decision follows framework: Pass/Fail

### Qualitative Assessments
- Business impact quantified (revenue, conversions): Manual review
- Segment analysis performed: Manual review
- Learnings documented for future experiments: Manual review

**Overall Success**: Statistical significance determined AND rollout decision made AND learnings documented

## HITL Escalation

### Automatic Triggers
- Guardrail metric violation during experiment
- Experiment duration >8 weeks (extended repeatedly, likely underpowered)
- Results borderline significant (0.04 < p < 0.06)
- Conflicting metrics (primary improves, key secondary degrades)
- Sample size <50% of target after 4 weeks

### Manual Triggers
- High-stakes decision (pricing changes, major UX overhaul)
- Inconclusive results requiring business judgment (small lift, high implementation cost)
- Ethical concerns (experiment affects vulnerable users)
- Multi-stakeholder conflict (Product wants rollout, Engineering concerned about tech debt)

### Escalation Procedure
1. **Level 1 - Self-Recovery**: Extend duration, adjust sample size, re-analyze
2. **Level 2 - Data Scientist Review**: Validate statistical analysis, advise on methodology
3. **Level 3 - Human-in-the-Loop**: Escalate to Product-Owner supervisor, convene decision committee
4. **Level 4 - Executive Approval**: High-risk experiments require C-suite sign-off before rollout

## Related Protocols

### Upstream (Prerequisites)
- STRAT-PRIO-001: RICE Scoring (identifies high-impact hypotheses to test)
- FEEDBACK-INGEST-001: Customer Feedback (informs hypotheses)
- ROADMAP-UPDATE-001: Roadmap (schedules experiments)

### Downstream (Consumers)
- METRIC-TRACK-001: Value Measurement (uses experiment results for KPI updates)
- COMM-LIAISON-001: Stakeholder Communication (distributes experiment results)
- Backlog prioritization (winning variants added as features)

### Alternatives
- Multivariate testing (MVT): Test multiple changes simultaneously
- Sequential testing: Continuously monitor, stop early if significant
- Bandit algorithms: Dynamically allocate traffic to better-performing variant

## Test Scenarios

### Happy Path Scenarios

#### Scenario 1: CTA Button Color Experiment (Positive Result)
- **Setup**: Test green vs. blue button, 14-day experiment, 7,700 users
- **Execution**: Deploy variants, monitor daily, collect data, analyze
- **Expected Result**: Variant A wins (p=0.0032, +15.9% lift), rollout to 100%
- **Validation**: Results match example above, rollout successful, baseline updated

#### Scenario 2: Pricing Experiment (No Significant Difference)
- **Setup**: Test $9.99 vs. $10.99 pricing, 21-day experiment
- **Execution**: Run experiment, analyze results
- **Expected Result**: p=0.32 (not significant), no rollout, learning documented
- **Validation**: Decision: Keep current pricing, document null result for future reference

### Failure Scenarios

#### Scenario 3: Guardrail Violation (Page Load Time)
- **Setup**: Variant introduces heavy JavaScript, page load increases to 5s
- **Execution**: Deploy variant, automated monitoring detects violation
- **Expected Result**: Experiment auto-stopped, 0% traffic to variant, Engineering notified
- **Validation**: Users never experience slow page, experiment aborted, issue fixed before retry

#### Scenario 4: Insufficient Traffic (Underpowered)
- **Setup**: Target 10,000 users, but only 2,500 after 8 weeks
- **Execution**: Attempt to analyze with low sample size
- **Expected Result**: HITL escalation, decision to abandon (inconclusive) or extend with lower power
- **Validation**: Results documented as underpowered, no rollout made without confidence

### Edge Cases

#### Scenario 5: Novelty Effect Detected
- **Setup**: Initial lift +20%, fades to +3% by week 4
- **Execution**: Extend experiment to 6 weeks, analyze temporal trend
- **Expected Result**: Report stabilized +3% effect, rollout decision based on long-term data
- **Validation**: Temporal analysis included in results, decision accounts for novelty decay

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-08 | Initial protocol creation, expanded from 25-line stub to full 14-section protocol | Claude Code (Sonnet 4.5) |

### Review Cycle
- **Frequency**: Quarterly (review experimentation methodology, statistical rigor)
- **Next Review**: 2026-01-08
- **Reviewers**: Product-Owner supervisor, Data Scientist, Engineering lead

### Compliance Status
- **Framework Standards**: ✅ Compliant with 14-section template
- **Security Audit**: Required if experiments affect data collection or PII
- **Last Validation**: 2025-10-08
