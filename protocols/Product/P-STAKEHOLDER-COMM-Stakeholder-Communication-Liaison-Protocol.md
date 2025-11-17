# COMM-LIAISON-001: Stakeholder Communication Protocol

**Version**: 1.0
**Last Updated**: 2025-11-17
**Status**: Active
**Owner**: Product-Owner

## Objective

Ensure transparent, timely, and actionable communication with all stakeholders (executives, customers, partners, internal teams) for major product deliverables, maintaining communication quality, stakeholder engagement, and feedback loops.

## Tool Requirements

- **TOOL-COLLAB-001** (GitHub Integration): Stakeholder documentation, communication tracking, and version control for communications
  - Execute: Communication documentation, stakeholder coordination, version control, artifact sharing, collaboration workflows
  - Integration: CLI commands (gh, git), API calls, repository operations, documentation systems, communication workflows
  - Usage: Communication management, stakeholder coordination, documentation sharing, version control, collaboration tracking

- **TOOL-API-001** (Customer Data): Stakeholder data management, contact information, and communication preferences
  - Execute: Stakeholder information management, contact data access, communication preferences, segmentation management
  - Integration: CRM systems, stakeholder management platforms, contact databases, communication preference systems
  - Usage: Stakeholder targeting, contact management, communication personalization, segmentation coordination

- **TOOL-COMM-001** (Communication): Multi-channel communication delivery, message distribution, and engagement tracking
  - Execute: Email delivery, Slack messaging, notification systems, communication analytics, engagement tracking
  - Integration: Email platforms, messaging systems, notification services, communication analytics, engagement tracking
  - Usage: Message delivery, communication automation, engagement monitoring, multi-channel coordination

- **TOOL-DATA-002** (Statistical Analysis): Communication analytics, engagement metrics, and effectiveness measurement
  - Execute: Communication analytics, engagement measurement, response tracking, effectiveness analysis, metrics calculation
  - Integration: Analytics platforms, engagement tracking systems, metrics calculation, reporting frameworks
  - Usage: Communication effectiveness analysis, engagement measurement, response analytics, communication optimization

## Trigger

- Major deliverable completed (PRD, roadmap, release notes, experiment results)
- Product-Owner creates artifact requiring stakeholder distribution
- Quarterly business review (QBR) preparation
- Critical product update or incident requiring stakeholder notification
- Stakeholder explicitly requests communication on specific topic
- Post-ROADMAP-UPDATE-001 execution (roadmap published)

## Agents

- **Primary**: Product-Owner
- **Supporting**: COMM specialist (messaging quality review), Marketing (external communications)
- **Review**: Human Command Group (for sensitive/strategic communications)

## Prerequisites

- Source artifact exists (e.g., `prd_{{issue_number}}.md`, `roadmap_Q{{quarter}}_{{year}}.md`, `experiment_{{id}}_results.yaml`)
- Stakeholder contact lists current and accessible via **TOOL-API-001**
- Communication channels configured via **TOOL-COMM-001** (email, Slack, GitHub, wiki)
- Stakeholder segmentation defined (executives, customers, engineering, sales, support)
- Previous communication history available for context via **TOOL-DATA-002**

## Steps

### Step 1: Identify Source Artifact (Estimated Time: 5m)
**Action**:
- Determine which artifact requires stakeholder communication
- Validate artifact completeness and readiness for external distribution
- Classify artifact type: PRD, Roadmap, Release Notes, Experiment Results, Incident Report

**Expected Outcome**: Source artifact identified and validated
**Validation**: Artifact file exists, content complete, metadata present

### Step 2: Determine Target Stakeholders (Estimated Time: 10m)
**Action**:
- Based on artifact type and content, identify relevant stakeholder groups:
  - **PRD**: Engineering teams, System Architect, QA, dependent teams
  - **Roadmap**: Executives (C-suite), Sales, Marketing, Customer Success, partners
  - **Release Notes**: All customers, support teams, sales engineering
  - **Experiment Results**: Product team, data science, marketing
  - **Incident Report**: Affected customers, support, engineering, executives
- Retrieve stakeholder contact information from `/docs/product/stakeholders/stakeholder_registry.yaml`
- Segment by communication preference (email, Slack, in-person briefing)

**Expected Outcome**: Target stakeholder list with contact preferences
**Validation**: All critical stakeholders identified, contact info valid

### Step 3: Generate Communication Summary (Estimated Time: 20m)
**Action**:
Create `comm_{{artifact_type}}_{{identifier}}.md` with structure:
```markdown
# {{Artifact Type}} Communication - {{Title}}

**Date**: {{YYYY-MM-DD}}
**Audience**: {{Stakeholder groups}}
**Priority**: High | Medium | Low
**Action Required**: Yes | No | By {{date}}

## Executive Summary (2-3 sentences)
[Key message, impact, call-to-action]

## Key Highlights
- **Highlight 1**: [Specific outcome or decision]
- **Highlight 2**: [Specific outcome or decision]
- **Highlight 3**: [Specific outcome or decision]

## What Changed / What's New
[Detailed explanation of updates, changes, or new information]

## Impact Assessment
- **For Customers**: [Direct impact, benefits, required actions]
- **For Engineering**: [Technical implications, implementation requirements]
- **For Sales/Marketing**: [Positioning, messaging, competitive advantages]
- **For Support**: [FAQ updates, common questions, escalation paths]

## Next Steps
1. [Action item 1] - Owner: [Name] - Due: [Date]
2. [Action item 2] - Owner: [Name] - Due: [Date]

## Questions & Feedback
Please direct questions to: {{contact_email}} or Slack: {{channel}}

## Related Links
- Original artifact: {{link_to_artifact}}
- Previous communication: {{link_if_applicable}}
- Supporting materials: {{links}}
```

**Expected Outcome**: Well-structured communication summary
**Validation**: Summary <500 words, key highlights clear, call-to-action explicit

### Step 4: Tailor Messages by Channel (Estimated Time: 15m)
**Action**:
Create channel-specific versions from base summary:

- **Email**: Full summary with formatted HTML, clear subject line
  - Subject format: `[{{Priority}}] {{Artifact Type}}: {{Title}}`
  - Include inline links, attachments if needed

- **Slack**: Condensed summary with thread for details
  - Use Slack blocks for formatting
  - Pin important updates to channel
  - Tag relevant individuals with @mentions

- **GitHub**: Issue comment or wiki page
  - Link to source artifact
  - Enable discussions for Q&A

- **Executive Brief**: 1-page summary for C-suite
  - Focus on business impact, risks, strategic alignment
  - Include financial implications if applicable

**Expected Outcome**: Channel-optimized messages prepared
**Validation**: Each channel has appropriate format and content length

### Step 5: Review for Clarity and Accuracy (Estimated Time: 10m)
**Action**:
- Self-review checklist:
  - ✅ Message is clear and unambiguous
  - ✅ Technical jargon explained or avoided
  - ✅ Action items have owners and deadlines
  - ✅ Tone is appropriate for audience (formal for executives, casual for internal Slack)
  - ✅ No sensitive information leaked (PII, trade secrets, unannounced features)
  - ✅ Links and attachments work correctly
  - ✅ Grammar and spelling checked
- If COMM specialist available: request review
- If sensitive/strategic: escalate to Human Command Group for approval

**Expected Outcome**: Communication quality validated
**Validation**: Checklist complete, no errors found, approval obtained if required

### Step 6: Distribute to Stakeholders (Estimated Time: 15m)
**Action**:
Execute distribution based on channel:

**Email**:
```bash
# Using configured email service or gh CLI
mail -s "[High] Roadmap Q4 2025: New AI Features" \
  -c stakeholders@company.com \
  < comm_roadmap_Q4_2025.md
```

**Slack**:
```bash
# Post to relevant channels
slack-cli post -c #product-updates -f comm_roadmap_Q4_2025.md
slack-cli post -c #engineering -f comm_roadmap_Q4_2025_eng.md
```

**GitHub**:
```bash
gh issue comment {{issue_number}} --body-file comm_prd_{{issue_number}}.md
```

**Executive Brief**: Email PDF directly to C-suite with meeting invitation if needed

**Expected Outcome**: Messages delivered to all channels successfully
**Validation**: Delivery confirmations received, no bounce-backs, Slack posts visible

### Step 7: Monitor Engagement and Feedback (Estimated Time: Ongoing)
**Action**:
- Track engagement metrics:
  - Email: Open rate, click-through rate
  - Slack: Reactions, replies, thread engagement
  - GitHub: Comments, issue activity
- Collect feedback and questions
- Categorize feedback: Clarification needed, Concerns, Endorsements, Action items
- Respond to questions within SLA (24 hours for normal, 2 hours for urgent)

**Expected Outcome**: Stakeholder engagement tracked, feedback collected
**Validation**: ≥60% open rate for emails, ≥3 reactions on Slack, questions answered promptly

### Step 8: Document Communication Outcome (Estimated Time: 10m)
**Action**:
- Update communication log at `/docs/product/communications/comm_log_{{quarter}}.yaml`:
```yaml
- communication_id: comm_roadmap_Q4_2025
  date: 2025-10-08
  artifact: roadmap_Q4_2025.md
  stakeholders: [executives, sales, marketing, engineering]
  channels: [email, slack, github]
  engagement:
    email_open_rate: 72%
    slack_reactions: 15
    questions_received: 8
    questions_answered: 8
  outcome: Successful - High engagement, all questions resolved
```
- Archive communication summary in `/docs/product/communications/archive/`
- Update stakeholder registry if contact changes identified

**Expected Outcome**: Communication documented and archived
**Validation**: Log entry created, metrics recorded, files archived

## Expected Outputs

- **Primary Artifact**: Communication summary `comm_{{artifact_type}}_{{identifier}}.md`
- **Secondary Artifacts**:
  - Channel-specific messages (email, Slack, GitHub, executive brief)
  - Communication log entry
  - Engagement metrics report
  - Stakeholder feedback summary
- **Success Indicators**:
  - Message distributed to all target stakeholders
  - Email open rate ≥60%
  - Stakeholder questions answered within SLA
  - No critical information errors or leaks
  - Positive stakeholder feedback (≥4/5 rating if surveyed)

## Failure Handling

### Failure Scenario 1: Stakeholder Contact Information Outdated
- **Symptoms**: Email bounces, Slack user not found, invalid contact info
- **Root Cause**: Stakeholder registry not maintained, personnel changes not reflected
- **Impact**: Medium - Some stakeholders miss communication
- **Resolution**:
  1. Identify bounced/invalid contacts from delivery logs
  2. Cross-reference with HR system or org chart for current contacts
  3. Update stakeholder registry immediately
  4. Re-send communication to corrected contact list
  5. Verify delivery confirmation
- **Prevention**: Quarterly stakeholder registry validation, automated contact verification

### Failure Scenario 2: Sensitive Information Leaked
- **Symptoms**: Stakeholder reports receiving inappropriate information (e.g., unannounced feature, competitive intel)
- **Root Cause**: Insufficient review, wrong audience segment selected
- **Impact**: Critical - Reputational damage, competitive disadvantage, legal risk
- **Resolution**:
  1. Immediately recall message if possible (email recall, delete Slack post)
  2. Send follow-up clarification/retraction to affected stakeholders
  3. Escalate to Human Command Group and Legal
  4. Conduct post-incident review to identify approval gap
  5. Implement mandatory review for sensitive communications
- **Prevention**: HITL approval for all strategic/sensitive communications, automated sensitive content detection

### Failure Scenario 3: Low Engagement (Open Rate <30%)
- **Symptoms**: Few stakeholders open email, no Slack reactions, no questions
- **Root Cause**: Poor subject line, message not relevant, communication fatigue
- **Impact**: Low - Message not reaching intended audience
- **Resolution**:
  1. Analyze subject line effectiveness (A/B test if possible)
  2. Review message relevance - is audience correctly targeted?
  3. Check communication frequency - are stakeholders overwhelmed?
  4. Re-send with improved subject line and condensed summary
  5. Follow up with direct outreach to critical stakeholders
- **Prevention**: Subject line best practices, stakeholder segmentation refinement, communication cadence limits

### Failure Scenario 4: Stakeholder Confusion or Misinterpretation
- **Symptoms**: Stakeholders ask clarifying questions indicating message wasn't clear
- **Root Cause**: Ambiguous wording, jargon, missing context, too much detail
- **Impact**: Medium - Requires additional communication cycles to clarify
- **Resolution**:
  1. Acknowledge confusion and provide immediate clarification
  2. Create FAQ document addressing common questions
  3. Post FAQ to Slack, email thread, GitHub issue
  4. Revise original communication summary for future reference
  5. Update communication template to avoid similar issues
- **Prevention**: Plain language guidelines, readability scoring (Flesch-Kincaid Grade <10), peer review

### Failure Scenario 5: Channel Distribution Failure
- **Symptoms**: Email service down, Slack API error, GitHub unavailable
- **Root Cause**: Infrastructure outage, API rate limit, authentication failure
- **Impact**: Medium - Communication delayed but not lost
- **Resolution**:
  1. Detect failure via delivery status monitoring
  2. Attempt alternative channel (if email fails, use Slack)
  3. If all channels fail: Log for retry with P-RECOVERY
  4. Retry with exponential backoff (3 attempts)
  5. If persistent: Notify stakeholders via emergency channel (phone tree, SMS)
- **Prevention**: Multi-channel redundancy, pre-flight connectivity checks, fallback communication plan

## Rollback/Recovery

**Trigger**: Failure during Steps 6-8 (distribution, monitoring, documentation)

**Standard Approach**: Invoke **P-RECOVERY** protocol for transactional rollback

**P-RECOVERY Integration**:
1. Before Step 6: CreateBranch to create isolated workspace (`comm_distribution_{{artifact}}_{{timestamp}}`)
2. Execute Steps 6-8 with checkpoints after each channel distribution
3. On success: MergeBranch commits communication log atomically
4. On failure: DiscardBranch rolls back partial distributions, no communication sent
5. P-RECOVERY handles retry logic with exponential backoff (3 attempts)
6. P-RECOVERY escalates to NotifyHuman if persistent failures

**Custom Rollback** (communication-specific):
1. If sensitive information leaked: Execute message recall/retraction immediately
2. If partial distribution: Complete remaining channels or abort and reschedule
3. Notify stakeholders of communication issue via emergency channel
4. Document incident for post-mortem review

**Verification**: Communication log shows no partial states, stakeholders receive complete message or nothing
**Data Integrity**: Low risk - draft communications stored separately, published only on full success

## Validation Criteria

### Quantitative Thresholds
- Email open rate: ≥60%
- Slack engagement: ≥3 reactions or ≥5 thread replies per post
- Question response time: ≤24 hours (normal), ≤2 hours (urgent)
- Stakeholder satisfaction: ≥4/5 rating (if surveyed)
- Distribution success rate: ≥95% (no bounces/failures)
- Time to distribute: ≤2 hours from artifact completion

### Boolean Checks
- All target stakeholders received message: Pass/Fail
- No sensitive information leaked: Pass/Fail
- Call-to-action clear and actionable: Pass/Fail
- Links and attachments functional: Pass/Fail
- Communication documented in log: Pass/Fail

### Qualitative Assessments
- Message clarity: Readability score (Flesch-Kincaid Grade <10)
- Tone appropriateness: Peer review approval
- Stakeholder feedback quality: Positive/neutral/negative sentiment analysis

**Overall Success**: All quantitative thresholds met AND all boolean checks pass AND no negative stakeholder feedback

## HITL Escalation

### Automatic Triggers
- Sensitive information detected in draft (keywords: "confidential", "unreleased", "internal only")
- Distribution failure after 3 retries across all channels
- Email bounce rate >20% (indicates stakeholder registry severely outdated)
- Negative stakeholder feedback (complaints, confusion, anger)
- Security/legal concern flagged in content

### Manual Triggers
- Strategic communication requiring executive approval (M&A, layoffs, major pivots)
- Crisis communication (security breach, service outage, data loss)
- Multi-stakeholder conflict requiring mediation
- Regulatory disclosure or compliance-related communication

### Escalation Procedure
1. **Level 1 - Self-Recovery**: Retry distribution, fix minor errors, clarify ambiguities
2. **Level 2 - COMM Specialist Review**: Request professional review of messaging, channel strategy
3. **Level 3 - Human-in-the-Loop**: Escalate to Product-Owner supervisor, obtain approval before distribution
4. **Level 4 - Executive Approval**: Critical communications require C-suite sign-off, Legal review

## Related Protocols

### Upstream (Prerequisites)
- ROADMAP-UPDATE-001: Roadmap Synchronization (produces roadmap requiring communication)
- EXPERIMENT-001: A/B Testing (produces experiment results for stakeholder sharing)
- METRIC-TRACK-001: Value Measurement (produces metrics reports)
- FEEDBACK-INGEST-001: Customer Feedback (stakeholders may respond with feedback)

### Downstream (Consumers)
- FEEDBACK-INGEST-001: Collects responses to communications
- METRIC-TRACK-001: Tracks communication effectiveness metrics
- Stakeholder satisfaction surveys (external process)

### Alternatives
- Manual stakeholder outreach: For small teams or highly sensitive topics
- Marketing automation tools: For large-scale customer communications (newsletters, product announcements)
- Jira/Confluence notifications: For engineering-focused updates

## Test Scenarios

### Happy Path Scenarios

#### Scenario 1: Quarterly Roadmap Communication
- **Setup**: Q4 2025 roadmap published, 50 stakeholders across 4 groups (execs, sales, eng, marketing)
- **Execution**: Run COMM-LIAISON-001 for roadmap artifact
- **Expected Result**: Communication distributed via email/Slack/GitHub, 70% open rate, 10+ questions answered
- **Validation**: All stakeholders received message, engagement metrics meet thresholds, positive feedback

#### Scenario 2: PRD Notification to Engineering
- **Setup**: PRD for issue #142 completed, 15 engineering stakeholders
- **Execution**: Run COMM-LIAISON-001 for PRD artifact
- **Expected Result**: GitHub issue comment posted, Slack #engineering notified, 100% stakeholders aware
- **Validation**: GitHub comment visible, Slack post has reactions, engineers confirm receipt

### Failure Scenarios

#### Scenario 3: Email Bounces (Outdated Contacts)
- **Setup**: Stakeholder registry 6 months old, 30% contacts changed roles
- **Execution**: Run COMM-LIAISON-001, email distribution fails for 15/50 stakeholders
- **Expected Result**: Bounces detected, stakeholder registry updated, re-send successful
- **Validation**: Updated registry reflects current contacts, second distribution 100% successful

#### Scenario 4: Sensitive Information Leak
- **Setup**: Draft communication includes unreleased feature details not approved for external sharing
- **Execution**: Run COMM-LIAISON-001, sensitive content detector flags issue before distribution
- **Expected Result**: Distribution blocked, Human Command Group alerted, content revised
- **Validation**: No message sent, sensitive content removed, revised version approved and distributed

### Edge Cases

#### Scenario 5: Multi-Channel Infrastructure Outage
- **Setup**: Email service down, Slack API rate-limited, GitHub slow
- **Execution**: Run COMM-LIAISON-001 during infrastructure issues
- **Expected Result**: P-RECOVERY retries detect persistent failure, escalate to emergency SMS/phone notification
- **Validation**: Stakeholders notified via fallback channel, communication rescheduled for when services recover

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-08 | Initial protocol creation, expanded from 10-line stub to full 14-section protocol | Claude Code (Sonnet 4.5) |

### Review Cycle
- **Frequency**: Quarterly (aligned with stakeholder registry updates)
- **Next Review**: 2026-01-08
- **Reviewers**: Product-Owner supervisor, COMM specialist, Marketing lead

### Compliance Status
- **Framework Standards**: ✅ Compliant with 14-section template
- **Security Audit**: Required (handles stakeholder PII and potentially sensitive product information)
- **Last Validation**: 2025-10-08
