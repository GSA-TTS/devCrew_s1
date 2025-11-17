# STRAT-PRIO-002: Bug Triage & Prioritization Protocol

**Version**: 1.0
**Last Updated**: 2025-11-17
**Status**: Active
**Owner**: Product-Owner

## Objective

Systematically triage, assess, and prioritize incoming bug reports using data-driven severity classification, impact analysis, and resource allocation to ensure critical issues receive immediate attention while maintaining development velocity and customer satisfaction.

## Tool Requirements

- **TOOL-COLLAB-001** (GitHub Integration): Bug tracking, issue management, triage coordination, and development team collaboration
  - Execute: Bug issue tracking, triage coordination, team collaboration, priority management, issue labeling, assignment workflows
  - Integration: CLI commands (gh, git), API calls, repository operations, issue management, team collaboration workflows
  - Usage: Bug issue management, triage coordination, team collaboration, priority tracking, development coordination

- **TOOL-DATA-002** (Statistical Analysis): Bug impact analysis, severity assessment, customer impact measurement, and prioritization analytics
  - Execute: Bug impact analysis, severity calculation, customer impact assessment, prioritization scoring, trend analysis
  - Integration: Analytics platforms, impact assessment tools, metrics calculation, customer data analysis, prioritization frameworks
  - Usage: Bug impact analysis, severity assessment, prioritization scoring, customer impact evaluation, analytics reporting

- **TOOL-API-001** (Customer Data): Customer impact assessment, segment analysis, and escalation management
  - Execute: Customer impact assessment, segment analysis, escalation tracking, customer communication, impact measurement
  - Integration: Customer support systems, CRM platforms, customer data access, impact tracking, escalation management
  - Usage: Customer impact analysis, segment prioritization, escalation management, customer communication coordination

- **TOOL-SEC-001** (SAST Scanner): Security vulnerability assessment, risk analysis, and security bug prioritization
  - Execute: Security vulnerability assessment, risk analysis, security bug prioritization, vulnerability scanning, security validation
  - Integration: Security scanning tools, vulnerability databases, risk assessment platforms, security analysis systems
  - Usage: Security bug assessment, vulnerability prioritization, risk analysis, security impact evaluation

## Trigger

- New bug reports submitted via GitHub issues (label: `bug`)
- Daily bug triage cycle (morning standup preparation)
- Critical/P0 bugs reported by customers or support team
- Post-release monitoring detecting new issues
- Weekly backlog review requiring bug priority reassessment
- Security vulnerabilities detected requiring immediate classification
- Customer escalations requiring priority adjustment

## Agents

- **Primary**: Product-Owner
- **Supporting**: Engineering Lead (technical assessment), QA team (reproducibility validation), Customer Success (customer impact assessment)
- **Review**: Engineering Manager (resource allocation), Security team (vulnerability assessment), Executive team (business impact validation)

## Prerequisites

- Access to GitHub repository with bug tracking enabled via **TOOL-COLLAB-001**
- Bug classification taxonomy defined: `/docs/product/bugs/bug_taxonomy.yaml`
- Customer impact assessment tools configured via **TOOL-API-001**
- Current sprint backlog accessible via **TOOL-COLLAB-001**: `/docs/product/backlog/backlog_{{sprint_id}}.yaml`
- Bug severity matrix with quantitative thresholds via **TOOL-DATA-002**
- Engineering team capacity and expertise mapping
- Customer segment priority matrix (enterprise, SMB, free users) via **TOOL-API-001**

## Steps

### Step 1: Collect and Validate Bug Reports (Estimated Time: 15m)
**Action**:
- Fetch all open bug reports: `gh issue list --label bug --state open --json number,title,body,labels,assignees,createdAt,updatedAt`
- Filter new bugs since last triage (within 24 hours)
- Validate bug report completeness using template checklist:
  - Steps to reproduce provided
  - Expected vs. actual behavior described
  - Environment details included (browser, OS, version)
  - Screenshots/logs attached when applicable
- Flag incomplete reports for reporter follow-up
- Identify duplicates using title/description similarity matching

**Expected Outcome**: Validated list of triageable bug reports
**Validation**: All bugs have required information, duplicates identified and merged, incomplete reports flagged

### Step 2: Reproduce and Classify Technical Severity (Estimated Time: 30m)
**Action**:
For each validated bug, assess technical severity using standardized matrix:

**Critical (P0)**:
- Complete system failure or security vulnerability
- Data loss or corruption
- Payment/billing system failure
- Authentication/authorization bypass

**High (P1)**:
- Core feature completely broken
- Major workflow disruption
- Performance degradation >50%
- High-value customer impacted

**Medium (P2)**:
- Feature partially broken or workaround available
- UI/UX issues affecting usability
- Performance degradation 20-50%
- Integration issues with minor impact

**Low (P3)**:
- Cosmetic issues or minor inconsistencies
- Edge case scenarios
- Performance degradation <20%
- Enhancement disguised as bug

Document reproducibility status and assign technical severity score (0-10).

**Expected Outcome**: All bugs classified with technical severity and reproducibility status
**Validation**: 100% bugs have severity classification, reproduction steps validated

### Step 3: Assess Customer Impact and Frequency (Estimated Time: 20m)
**Action**:
Calculate customer impact using multi-dimensional analysis:

**Frequency Analysis**:
- User reports count (GitHub comments, support tickets)
- Customer segment affected (Enterprise: 10x weight, SMB: 3x weight, Free: 1x weight)
- Geographic distribution (regulatory compliance implications)
- Estimated affected user percentage

**Business Impact Scoring**:
```yaml
impact_factors:
  revenue_risk: 0-10  # Potential revenue loss
  churn_risk: 0-10    # Customer retention threat
  compliance_risk: 0-10  # Regulatory/legal exposure
  reputation_risk: 0-10  # Brand damage potential
  competitive_risk: 0-10  # Competitive disadvantage
```

Calculate composite impact score: `Impact = (revenue_risk × 0.3) + (churn_risk × 0.25) + (compliance_risk × 0.2) + (reputation_risk × 0.15) + (competitive_risk × 0.1)`

**Expected Outcome**: Customer impact scores and frequency estimates for all bugs
**Validation**: Impact scoring complete, customer segment analysis documented

### Step 4: Calculate Priority Score and Ranking (Estimated Time: 15m)
**Action**:
Compute comprehensive priority score using weighted formula:
```
Priority = (Severity × 0.4) + (Impact × 0.35) + (Frequency × 0.15) + (Effort^-1 × 0.1)
```

Where:
- Severity: Technical severity score (0-10)
- Impact: Business impact score (0-10)
- Frequency: Affected user percentage (0-10)
- Effort^-1: Inverse effort estimate (10/effort_estimate for 1-10 scale)

Rank all bugs by priority score descending and assign priority tiers:
- **P0**: Score ≥8.0 (Immediate fix required)
- **P1**: Score 6.0-7.9 (Fix in current sprint)
- **P2**: Score 4.0-5.9 (Fix in next sprint)
- **P3**: Score <4.0 (Backlog for future consideration)

**Expected Outcome**: All bugs ranked with quantitative priority scores and tier assignments
**Validation**: Priority calculations verified, tier assignments consistent with thresholds

### Step 5: Update Sprint Backlog and Assignment (Estimated Time: 20m)
**Action**:
- Load current sprint backlog: `/docs/product/backlog/backlog_{{sprint_id}}.yaml`
- For each triaged bug, add entry under `bugs:` section:
```yaml
bugs:
  - bug_id: "{{github_issue_number}}"
    title: "{{bug_title}}"
    priority_tier: "P0|P1|P2|P3"
    priority_score: {{calculated_score}}
    severity: "Critical|High|Medium|Low"
    impact_score: {{business_impact}}
    frequency_score: {{user_affected_percentage}}
    effort_estimate: {{story_points}}
    customer_segments: [{{affected_segments}}]
    assignee: "{{engineer_name}}"
    target_sprint: "{{sprint_id}}"
    created_date: "{{YYYY-MM-DD}}"
    triage_date: "{{YYYY-MM-DD}}"
    status: "triaged"
```

- Assign P0/P1 bugs to engineers based on expertise and current workload
- Escalate P0 bugs to engineering manager for immediate attention
- Validate sprint capacity doesn't exceed team velocity

**Expected Outcome**: Backlog updated with prioritized bugs and initial assignments
**Validation**: All bugs added to backlog, P0/P1 assignments confirmed, capacity validated

### Step 6: Communicate Bug Priorities and Actions (Estimated Time: 15m)
**Action**:
- Post priority assessment comment on each GitHub issue:
```markdown
## Bug Triage Complete

**Priority**: {{P0|P1|P2|P3}} (Score: {{priority_score}})
**Severity**: {{severity_level}}
**Target Sprint**: {{sprint_id}}
**Assigned**: {{engineer_name}}

### Assessment Details
- Technical Severity: {{score}}/10
- Customer Impact: {{score}}/10
- Affected Users: ~{{percentage}}%
- Effort Estimate: {{story_points}} points

### Next Steps
{{action_items_based_on_priority}}
```

- For P0 bugs: Immediately notify assigned engineer and engineering manager via Slack
- For P1 bugs: Add to current sprint with assignment notification
- For P2/P3 bugs: Add to backlog with estimated timeline
- Update #engineering Slack channel with daily triage summary

**Expected Outcome**: All stakeholders informed of bug priorities and assignments
**Validation**: GitHub comments posted, Slack notifications sent, team awareness confirmed

### Step 7: Initiate Immediate Response for Critical Issues (Estimated Time: Variable)
**Action**:
For P0 bugs only:
- Create incident response thread in #incidents Slack channel
- Notify Customer Success team of affected customers
- Prepare hotfix branch if immediate fix required
- Schedule emergency deployment if critical
- Draft customer communication if external impact
- Document incident timeline for post-mortem

For P1 bugs:
- Ensure engineer availability for fix in current sprint
- Identify dependencies and blockers
- Estimate fix timeline and communicate to stakeholders
- Prepare rollback plan if fix introduces risk

**Expected Outcome**: Critical issues have immediate response plan initiated
**Validation**: P0 incident response active, P1 fixes planned and resourced

### Step 8: Document Triage Metrics and Archive (Estimated Time: 10m)
**Action**:
- Update bug triage metrics: `/docs/product/bugs/triage_metrics_{{quarter}}.yaml`
```yaml
- date: "{{YYYY-MM-DD}}"
  bugs_triaged: {{count}}
  p0_critical: {{count}}
  p1_high: {{count}}
  p2_medium: {{count}}
  p3_low: {{count}}
  average_triage_time: "{{minutes}}"
  duplicate_rate: "{{percentage}}"
  incomplete_report_rate: "{{percentage}}"
  engineering_capacity_used: "{{percentage}}"
```

- Archive triage decisions for audit trail
- Update bug taxonomy if new categories identified
- Commit backlog changes with descriptive message
- Schedule follow-up for bug resolution tracking

**Expected Outcome**: Triage process documented, metrics tracked, audit trail maintained
**Validation**: Metrics logged, backlog committed, follow-up scheduled

## Expected Outputs

- **Primary Artifact**: Updated sprint backlog `backlog_{{sprint_id}}.yaml` with prioritized bugs and assignments
- **Secondary Artifacts**:
  - GitHub issue comments with priority assessments
  - Triage metrics update
  - Incident response initiation (for P0 bugs)
  - Team communication summaries
- **Success Indicators**:
  - 100% new bugs triaged within 24 hours
  - P0 bugs have immediate response initiated
  - Engineering team capacity optimally allocated
  - Customer impact accurately assessed and communicated
  - Stakeholder awareness and alignment achieved

## Failure Handling

### Failure Scenario 1: GitHub API Rate Limiting or Outage
- **Symptoms**: API calls fail, issue data unavailable, cannot post comments
- **Root Cause**: GitHub service disruption, API rate limits exceeded, authentication failure
- **Impact**: Medium - Triage delayed but not data lost
- **Resolution**:
  1. Check GitHub status page and wait for service restoration
  2. Use cached issue data from previous 24 hours if available
  3. Manually review critical bugs via GitHub web interface
  4. Batch API calls with rate limiting to reduce load
  5. Complete triage offline and sync when service restored
- **Prevention**: API rate monitoring, cached data backup, alternative triage methods

### Failure Scenario 2: Incomplete Bug Reports Blocking Assessment
- **Symptoms**: Missing reproduction steps, unclear impact description, no environment details
- **Root Cause**: Poor bug reporting templates, insufficient user guidance, rushed submissions
- **Impact**: Low - Individual bugs delayed but triage continues
- **Resolution**:
  1. Use bug report template validation bot to request missing information
  2. Engage reporter via GitHub comments with specific requests
  3. Estimate severity based on available information with confidence flag
  4. Schedule follow-up triage when complete information available
  5. Escalate to Customer Success for high-value customer reports
- **Prevention**: Improved bug report templates, user guidance, validation automation

### Failure Scenario 3: Engineering Team Over-Capacity (Cannot Accept New Bugs)
- **Symptoms**: All engineers at 100% capacity, P1 bugs cannot be assigned, sprint velocity exceeded
- **Root Cause**: Underestimated existing work, unexpected complexity, team availability issues
- **Impact**: High - Bug fixes delayed, customer satisfaction risk
- **Resolution**:
  1. Review current sprint commitments for scope reduction opportunities
  2. Escalate to Engineering Manager for resource reallocation
  3. Consider external contractor or temporary team expansion
  4. Communicate delays to affected customers with workarounds
  5. Adjust priority thresholds to reduce P1 classification temporarily
- **Prevention**: Capacity planning, sprint buffer allocation, cross-training

### Failure Scenario 4: Conflicting Priority Assessments (Stakeholder Disagreement)
- **Symptoms**: Customer Success rates bug as critical, Engineering rates as low, executives disagree
- **Root Cause**: Different perspectives on impact, missing context, unclear prioritization criteria
- **Impact**: Medium - Delays decision-making, team confusion
- **Resolution**:
  1. Schedule immediate stakeholder alignment meeting with data presentation
  2. Re-evaluate using expanded impact criteria including political/strategic factors
  3. Executive decision if consensus cannot be reached
  4. Document decision rationale for future reference
  5. Update prioritization criteria to prevent similar conflicts
- **Prevention**: Clear prioritization framework, stakeholder education, regular calibration

### Failure Scenario 5: Critical Security Vulnerability Discovered
- **Symptoms**: Bug reveals security vulnerability, potential data breach, compliance violation
- **Root Cause**: Security testing gap, new attack vector, dependency vulnerability
- **Impact**: Critical - Security risk, regulatory exposure, customer trust
- **Resolution**:
  1. Immediately escalate to Security team and Engineering Manager
  2. Activate incident response protocol
  3. Assess blast radius and affected systems
  4. Implement temporary mitigations if possible
  5. Coordinate with Legal/Compliance teams for disclosure requirements
- **Prevention**: Security testing integration, dependency scanning, regular security audits

## Rollback/Recovery

**Trigger**: Failure during Steps 5-8 (backlog update, assignment, communication, documentation)

**Standard Approach**: Invoke **P-RECOVERY** protocol for transactional rollback

**P-RECOVERY Integration**:
1. Before Step 5: CreateBranch to create isolated workspace (`bug_triage_{{date}}_{{timestamp}}`)
2. Execute Steps 5-8 with checkpoints after each major operation
3. On success: MergeBranch commits backlog changes and assignments atomically
4. On failure: DiscardBranch rolls back partial changes, preserves original state
5. P-RECOVERY handles retry logic with exponential backoff (3 attempts)
6. P-RECOVERY escalates to NotifyHuman if persistent failures

**Custom Rollback** (bug-specific):
1. If backlog corruption detected: Restore from git backup, re-apply valid changes
2. If incorrect assignments made: Unassign bugs and restart assignment process
3. If communication errors: Correct GitHub comments and resend notifications
4. If P0 escalation inappropriate: De-escalate and adjust priority classification

**Verification**: Backlog integrity verified, assignments valid, communications accurate
**Data Integrity**: Medium risk - bug assessments backed up before backlog changes

## Validation Criteria

### Quantitative Thresholds
- Triage completion time: ≤4 hours for P0 bugs, ≤24 hours for all bugs
- Priority accuracy: ≥90% stakeholder agreement on P0/P1 classifications
- Assignment efficiency: ≥80% bugs assigned to appropriate engineers
- Communication completeness: 100% bugs have GitHub comments with assessment
- Capacity utilization: 80-100% sprint capacity used, no over-allocation
- Duplicate detection rate: ≥95% accuracy in identifying duplicate reports

### Boolean Checks
- All new bugs triaged and classified: Pass/Fail
- P0 bugs have immediate response initiated: Pass/Fail
- Sprint backlog updated with all triaged bugs: Pass/Fail
- Engineering assignments confirmed and accepted: Pass/Fail
- Stakeholder notifications sent successfully: Pass/Fail
- Triage metrics documented: Pass/Fail

### Qualitative Assessments
- Priority assessment accuracy: Stakeholder validation survey (≥4/5 rating)
- Engineer satisfaction with assignments: Team feedback collection
- Customer impact assessment quality: Customer Success team review
- Communication clarity: GitHub comment readability and completeness

**Overall Success**: All quantitative thresholds met AND all boolean checks pass AND stakeholder satisfaction ≥4/5 rating

## HITL Escalation

### Automatic Triggers
- P0 bug volume spike (>5 critical bugs in 24 hours)
- Engineering capacity exceeded by >120%
- Conflicting priority assessments requiring arbitration
- Security vulnerabilities requiring immediate escalation
- Customer escalations involving high-value accounts
- Regulatory compliance violations detected

### Manual Triggers
- Cross-functional impact requiring coordination (sales, marketing, legal)
- Technical complexity requiring architectural review
- Resource allocation conflicts between teams
- Customer communication requiring executive involvement
- Legal/compliance implications requiring review

### Escalation Procedure
1. **Level 1 - Self-Recovery**: Adjust priority thresholds, redistribute assignments, extend timelines
2. **Level 2 - Team Coordination**: Engage Engineering Manager, Customer Success lead for resource and context
3. **Level 3 - Human-in-the-Loop**: Escalate to Product-Owner supervisor, require executive decision for resource allocation
4. **Level 4 - Executive Review**: Critical security issues, major customer impact, regulatory requirements

## Related Protocols

### Upstream (Prerequisites)
- **FEEDBACK-INGEST-001**: Customer Feedback (provides bug reports from customer feedback)
- **EXPERIMENT-001**: A/B Testing (may reveal bugs in new features)
- **METRIC-TRACK-001**: Value Measurement (provides usage data for impact assessment)
- GitHub issue creation (external process from users, QA, engineering)

### Downstream (Consumers)
- **Engineering Sprint Planning**: Uses prioritized bug list for sprint allocation
- **COMM-LIAISON-001**: Stakeholder Communication (communicates bug status to customers)
- **Release Planning**: Incorporates bug fixes into release timeline
- **Security Incident Response**: Escalates security-related bugs

### Alternatives
- Automated bug triaging with ML classification: For high-volume bug environments
- Customer-driven priority voting: For community-driven products
- SLA-based prioritization: For enterprise customers with support contracts

## Test Scenarios

### Happy Path Scenarios

#### Scenario 1: Daily Bug Triage (Standard Volume)
- **Setup**: 15 new bug reports submitted overnight, mix of severities and customer segments
- **Execution**: Run STRAT-PRIO-002 for daily triage cycle
- **Expected Result**: All bugs triaged within 2 hours, 2 P0, 4 P1, 6 P2, 3 P3 classifications, engineers notified
- **Validation**: Backlog updated, GitHub comments posted, sprint capacity maintained

#### Scenario 2: Critical Security Bug Discovery
- **Setup**: Security vulnerability reported affecting authentication system
- **Execution**: Run STRAT-PRIO-002 with immediate P0 classification and escalation
- **Expected Result**: Incident response initiated within 15 minutes, security team engaged, hotfix planned
- **Validation**: Security protocols activated, customer communication prepared, fix timeline established

### Failure Scenarios

#### Scenario 3: GitHub Outage During Triage
- **Setup**: GitHub API unavailable during morning triage, 10 bugs pending assessment
- **Execution**: Run STRAT-PRIO-002 with limited GitHub access
- **Expected Result**: Cached data used, manual assessment via web interface, sync when service restored
- **Validation**: No bugs missed, priorities assessed, stakeholder communication maintained

#### Scenario 4: Engineering Team at Full Capacity
- **Setup**: Current sprint at 100% capacity, 3 new P1 bugs require immediate attention
- **Execution**: Run STRAT-PRIO-002 with capacity constraints
- **Expected Result**: Engineering Manager escalation, scope negotiation, resource reallocation
- **Validation**: P1 bugs accommodated, sprint scope adjusted, stakeholder expectations managed

### Edge Cases

#### Scenario 5: Duplicate Bug Reports from Multiple Channels
- **Setup**: Same bug reported via GitHub, support tickets, and social media
- **Execution**: Run STRAT-PRIO-002 with duplicate detection and consolidation
- **Expected Result**: Duplicates identified and merged, single priority assessment, all reporters notified
- **Validation**: No duplicate work, consolidated tracking, comprehensive stakeholder communication

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-08 | Initial protocol creation, expanded from 19-line stub to comprehensive 14-section protocol with P-RECOVERY integration | Claude Code (Sonnet 4) |

### Review Cycle
- **Frequency**: Bi-weekly (aligned with sprint planning and engineering capacity review)
- **Next Review**: 2025-10-22
- **Reviewers**: Product-Owner supervisor, Engineering Manager, Customer Success lead

### Compliance Status
- **Framework Standards**: ✅ Compliant with 14-section template
- **Security Audit**: Required (handles security vulnerability classification and incident response)
- **Last Validation**: 2025-10-08