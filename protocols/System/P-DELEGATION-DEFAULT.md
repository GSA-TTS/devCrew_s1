# P-DELEGATION-DEFAULT: Default Agent Delegation Protocol

## Objective
Standardize agent-to-agent delegation using GitHub issues for audit trail, progress tracking, and deliverable management. Provides default coordination mechanism for all agent delegations with comprehensive lifecycle management, failure handling, and integration with specialized protocols.

## Tool Requirements

- **TOOL-COLLAB-001** (GitHub Integration): Issue creation, label management, progress tracking, and delegated work coordination
  - Execute: Delegation issue creation, label application, status tracking, deliverable linking, audit trail management, HITL comment polling
  - Integration: GitHub CLI (gh), issue templates, labels, comments, milestones, project boards
  - Usage: Delegation lifecycle management, progress monitoring, deliverable tracking, agent coordination, human approval workflows

- **TOOL-ORG-001** (Orchestration): Agent assignment, workload distribution, and delegation monitoring
  - Execute: Agent assignment, delegation monitoring, workload balancing, escalation management, resource coordination, platform detection
  - Integration: Agent management systems, workload monitoring, delegation queues, escalation workflows, platform-specific configurations
  - Usage: Agent delegation orchestration, workload management, resource allocation, escalation handling, monitoring optimization

- **TOOL-CICD-001** (Pipeline Platform): Deliverable validation, quality verification, and automated testing integration
  - Execute: Deliverable validation, automated testing, quality gate verification, integration validation
  - Integration: CI/CD pipelines, automated testing, quality gates, validation workflows
  - Usage: Delegation deliverable validation, quality assurance, automated verification

- **TOOL-CONFIG-001** (Platform Configuration): Platform detection, monitoring configuration, and adaptive behavior
  - Execute: Platform identification (Claude Code, CrewAI, AWS Strands), monitoring parameter configuration, polling optimization
  - Integration: Platform-specific APIs, configuration management, adaptive workflows
  - Usage: Platform-optimized delegation monitoring, configurable polling intervals, handoff signal detection

## Trigger
- Any agent requires another agent to perform specialized work
- Agent workload requires distribution across multiple specialists
- Cross-functional expertise needed (e.g., Backend-Engineer → Security-Auditor)
- Specialized protocol delegation (P-TDD test creation, P-QGATE validation)
- Quality assurance work requiring independent verification
- Infrastructure or operations work requiring SRE/DevOps expertise

## Prerequisites
- Delegating agent has clear task definition and requirements
- Target agent availability confirmed via **TOOL-ORG-001**
- Delegation category identified (analysis, planning, implementation, qa, operations)
- Required deliverables and acceptance criteria defined
- Appropriate delegation template selected from `.github/ISSUE_TEMPLATE/`

## Steps

### 1. Pre-Delegation (Issue Creation)
**Delegating Agent Actions:**
- **Template Selection**: Choose appropriate delegation template:
  | Delegation Type | Template | Use Case |
  |----------------|----------|----------|
  | ASR/ADR/Feasibility Analysis | `agent-delegation-analysis.yml` | System-Architect → asr-writer |
  | Implementation Planning | `agent-delegation-planning.yml` | Backend-Engineer → Blueprint-Writer |
  | Feature Development | `agent-delegation-implementation.yml` | Orchestrator → Backend-Engineer |
  | Test Creation/Code Review | `agent-delegation-qa.yml` | Backend-Engineer → QATester (P-TDD) |
  | Incident Response | `agent-delegation-operations.yml` | Orchestrator → SRE |

- **Issue Creation**: Execute via **TOOL-COLLAB-001**:
  ```bash
  gh issue create --template {delegation-template}.yml \
    --title "[DELEGATION] {task-summary}" \
    --assignee {target-agent}
  ```

- **Label Application**: Auto-applied via template + manual assignment:
  - Core: `delegation`, `delegation-{category}`
  - Agent: `assigned-to-{target-agent}`
  - Status: `delegation-pending`

- **Requirements Documentation**: Complete all template fields:
  - Task scope and deliverables
  - Quality standards and acceptance criteria
  - Dependencies and constraints
  - Due date/SLO expectations
  - Handoff instructions

### 2. Monitoring (Progress Tracking)
**Delegating Agent Actions:**

- **Platform Detection & Configuration**: Identify platform via **TOOL-CONFIG-001** and configure monitoring:
  ```bash
  # Platform-specific monitoring configuration
  PLATFORM=$(detect_platform)  # Claude Code, CrewAI, AWS Strands, Generic
  case $PLATFORM in
    "Claude-Code")
      POLLING_ENABLED=false
      HANDOFF_SIGNAL=true
      MONITORING_INTERVAL="N/A"
      ;;
    *)
      POLLING_ENABLED=true
      HANDOFF_SIGNAL=false
      MONITORING_INTERVAL=${MONITORING_INTERVAL:-180}  # Default 3 minutes (180 seconds)
      ;;
  esac
  ```

- **Status Monitoring**: Platform-aware monitoring via **TOOL-COLLAB-001**:
  ```bash
  if [ "$POLLING_ENABLED" = true ]; then
    # Traditional polling for non-Claude Code platforms
    while true; do
      gh issue list --assignee {target-agent} --label "delegation-pending"
      gh issue view {issue-number} --json labels,comments,state
      sleep $MONITORING_INTERVAL
    done
  else
    # Claude Code: Wait for handoff signal instead of polling
    echo "Monitoring via handoff signals - no polling required"
  fi
  ```

- **Timeout Detection**: Monitor for delegation pickup within SLO:
  - Analysis/Planning: 24 hours pickup SLO
  - Implementation: 48 hours pickup SLO
  - QA/Operations: 12 hours pickup SLO

- **Escalation Trigger**: If no pickup detected:
  ```bash
  gh issue comment {issue-number} --body "⚠️ Delegation timeout. Escalating to @Orchestrator"
  gh issue edit {issue-number} --add-label "escalation-required"
  ```

**Target Agent Actions:**
- **Pickup Acknowledgment**: Update status when starting work:
  ```bash
  gh issue edit {issue-number} \
    --add-label "delegation-in-progress" \
    --remove-label "delegation-pending"
  gh issue comment {issue-number} --body "🚀 Starting delegation work. ETA: {timeline}"
  ```

### 3. In-Progress Updates (Work Execution)
**Target Agent Actions:**
- **Progress Comments**: Post milestone updates via **TOOL-COLLAB-001**:
  ```bash
  gh issue comment {issue-number} --body "📊 Progress: {milestone} completed. Next: {next-step}"
  ```

- **Blocked Handling**: If delegation becomes blocked:
  ```bash
  gh issue edit {issue-number} --add-label "delegation-blocked"
  gh issue comment {issue-number} --body "🚫 BLOCKED: {blocking-issue}. Resolution needed from {responsible-party}"
  ```

- **Deliverable Linking**: Link work products as they're created:
  ```bash
  gh issue comment {issue-number} --body "📎 Deliverable: {file-path} completed"
  ```

**Monitoring Agents Actions:**
- **Progress Verification**: Check for regular updates (every 48 hours)
- **Blocked Resolution**: Assist with unblocking if labeled `delegation-blocked`
- **Quality Assistance**: Provide clarification if deliverables unclear

### 4. Completion & Handoff (Deliverable Submission)
**Target Agent Actions:**
- **Finishing Comment**: Post comprehensive completion summary via **TOOL-COLLAB-001**:
  ```bash
  gh issue comment {issue-number} --body "✅ DELEGATION COMPLETED

  ## Deliverables
  - {deliverable-1}: {location/link}
  - {deliverable-2}: {location/link}

  ## Quality Verification
  - {quality-metric-1}: ✅ Passed
  - {quality-metric-2}: ✅ Passed

  ## Summary
  {work-summary-and-key-decisions}

  ## Handoff Notes
  {any-important-context-for-next-steps}
  "
  ```

- **Status Update & Closure**:
  ```bash
  gh issue edit {issue-number} \
    --add-label "delegation-completed" \
    --remove-label "delegation-in-progress"
  gh issue close {issue-number}
  ```

- **Deliverable Validation**: Verify outputs meet acceptance criteria via **TOOL-CICD-001**

### 5. Post-Handoff (Verification & Continuation)
**Delegating Agent Actions:**
- **Completion Detection**: Platform-aware completion detection via **TOOL-COLLAB-001**:
  ```bash
  if [ "$HANDOFF_SIGNAL" = true ]; then
    # Claude Code: Direct handoff signal received
    echo "Handoff signal received - proceeding to verification"
  else
    # Other platforms: Traditional polling
    gh issue list --author {target-agent} --label "delegation-completed" --state closed
  fi
  ```

- **Deliverable Verification**: Validate all expected deliverables received:
  - Check linked files/locations exist
  - Verify quality standards met
  - Confirm acceptance criteria satisfied

- **HITL Decision Point**: For critical operations requiring human oversight:
  ```bash
  # Check if HITL approval required for this delegation
  if grep -q "hitl-required" <<< "$(gh issue view {issue-number} --json labels)"; then
    # Request human approval
    gh issue comment {issue-number} --body "🔒 **HITL APPROVAL REQUIRED**

    Delegation completed successfully. Human review needed before proceeding.

    **Action Required**: Please comment with one of:
    - \`/approve\` - Approve delegation results and continue workflow
    - \`/reject\` - Reject delegation results and require rework

    **Auto-timeout**: If no response within 4 hours, will escalate to @Orchestrator"

    # Poll for human response
    HITL_TIMEOUT=240  # 4 hours in minutes
    HITL_POLL_INTERVAL=180  # 3 minutes
    ELAPSED=0

    while [ $ELAPSED -lt $HITL_TIMEOUT ]; do
      LATEST_COMMENT=$(gh issue view {issue-number} --json comments --jq '.comments[-1].body')

      case "$LATEST_COMMENT" in
        */approve*)
          echo "✅ Human approval received - proceeding"
          break
          ;;
        */reject*)
          echo "❌ Human rejection received - triggering rework"
          gh issue reopen {issue-number}
          gh issue edit {issue-number} --add-label "delegation-failed" --add-label "hitl-rejected"
          gh issue comment {issue-number} --body "❌ **HITL REJECTION**: Human reviewer rejected delegation results. Reassigning for rework."
          gh issue edit {issue-number} --assignee {original-target-agent}
          return 1
          ;;
      esac

      sleep $((HITL_POLL_INTERVAL * 60))
      ELAPSED=$((ELAPSED + HITL_POLL_INTERVAL))
    done

    # Handle HITL timeout
    if [ $ELAPSED -ge $HITL_TIMEOUT ]; then
      gh issue comment {issue-number} --body "⏰ **HITL TIMEOUT**: No human response within 4 hours. Escalating to @Orchestrator"
      gh issue edit {issue-number} --add-label "escalation-required" --add-label "hitl-timeout"
      return 1
    fi
  fi
  ```

- **Workflow Continuation**: Resume main workflow with delegation outputs
- **Audit Trail**: Document delegation success in main workflow tracking

**Enhanced Failure Recovery Actions:**
- **Verification Failure with Re-delegation**: If deliverables inadequate:
  ```bash
  # Enhanced failure handling with detailed feedback
  gh issue reopen {issue-number}
  gh issue edit {issue-number} \
    --add-label "delegation-failed" \
    --remove-label "delegation-completed"

  # Post detailed failure explanation
  gh issue comment {issue-number} --body "❌ **VERIFICATION FAILED**

  **Issues Identified:**
  {specific-verification-failures}

  **Required Actions:**
  {specific-remediation-steps}

  **Reassignment**: This issue has been reassigned to the original agent for resolution.

  **Next Steps**: Please address the identified issues and resubmit for verification."

  # Reassign to original target agent instead of continuing workflow
  gh issue edit {issue-number} --assignee {original-target-agent}

  # Track failure for escalation patterns
  FAILURE_COUNT=$(gh issue view {issue-number} --json labels --jq '.labels | map(select(.name | contains("failure-count"))) | length')
  if [ $FAILURE_COUNT -ge 2 ]; then
    gh issue edit {issue-number} --add-label "escalation-required"
    gh issue comment {issue-number} --body "⚠️ **ESCALATION**: Multiple verification failures detected. Escalating to @Orchestrator for review."
  fi
  ```

### 5.5. Human-in-the-Loop (HITL) Integration
**Enhanced HITL with Standardized Templates:**

#### **Standardized HITL Trigger Categories**

**P-HITL-CRITICAL: Critical System Events**
- **Use Cases**: Security vulnerabilities (CVSS ≥9.0), production failures, unresolved P1 incidents, error budget exhaustion
- **Timeout**: 15 minutes for P1, immediate for P0
- **Template Usage**: `P-HITL-CRITICAL` with automatic escalation to @Orchestrator

**P-HITL-THRESHOLD: Threshold-Based Alerts**
- **Use Cases**: Performance regression (>20%), project delays (>20%), cost increases (>$1,000/month)
- **Timeout**: 4 hours
- **Template Usage**: `P-HITL-THRESHOLD` with configurable threshold values

**P-HITL-APPROVAL: Approval Gates**
- **Use Cases**: Architectural conflicts, new ADR requirements, scope expansion (>150%), design system components, agent modifications
- **Timeout**: 4 hours business hours, 24 hours for agent modifications
- **Template Usage**: `P-HITL-APPROVAL` with structured approval workflows

**P-HITL-EXCEPTION: Data/Exception Handling**
- **Use Cases**: Ambiguous data conflicts, unresolvable system conflicts
- **Timeout**: 2 hours
- **Template Usage**: `P-HITL-EXCEPTION` with subject matter expert escalation

#### **Agent HITL Implementation Pattern**
Instead of custom HITL implementations, agents use standardized templates:

```markdown
**Human-in-the-Loop (HITL) Triggers:**
- **{Category}**: Uses `P-HITL-{TYPE}` template for {specific-scenarios} (threshold: {value})
- **Integration**: Leverages P-DELEGATION-DEFAULT `/approve` and `/reject` workflow with {timeout} and @{escalation-target} escalation
```

**Examples of Simplified Agent HITL Sections:**
```markdown
# PerformanceEngineer Example
**Human-in-the-Loop (HITL) Triggers:**
- **Performance Monitoring**: Uses `P-HITL-THRESHOLD` template for performance regression (threshold: >20% degradation)
- **Integration**: Leverages P-DELEGATION-DEFAULT `/approve` and `/reject` workflow with 4-hour timeout and @Orchestrator escalation

# SecurityAuditor Example
**Human-in-the-Loop (HITL) Triggers:**
- **Security Critical**: Uses `P-HITL-CRITICAL` template for vulnerabilities (threshold: CVSS ≥9.0)
- **Integration**: Leverages P-DELEGATION-DEFAULT `/approve` and `/reject` workflow with 15-minute timeout and @Orchestrator escalation

# BlueprintWriter Example
**Human-in-the-Loop (HITL) Triggers:**
- **Architectural Governance**: Uses `P-HITL-APPROVAL` template for ADR conflicts and scope expansion (threshold: requirements >150% of original scope)
- **Integration**: Leverages P-DELEGATION-DEFAULT `/approve` and `/reject` workflow with 4-hour timeout and @Orchestrator escalation
```

#### **Template-Based HITL Configuration**
```bash
# Apply HITL template during delegation creation based on category
apply_hitl_template() {
  local issue_number=$1
  local template_type=$2
  local threshold_value=${3:-"default"}

  case $template_type in
    "P-HITL-CRITICAL")
      timeout_minutes=15
      escalation_target="@Orchestrator"
      priority="P1"
      ;;
    "P-HITL-THRESHOLD")
      timeout_minutes=240  # 4 hours
      escalation_target="@Orchestrator"
      priority="P2"
      ;;
    "P-HITL-APPROVAL")
      timeout_minutes=240  # 4 hours, 1440 for agent modifications
      escalation_target="@Orchestrator"
      priority="P2"
      ;;
    "P-HITL-EXCEPTION")
      timeout_minutes=120  # 2 hours
      escalation_target="@Orchestrator"
      priority="P2"
      ;;
  esac

  gh issue edit $issue_number --add-label "hitl-required" --add-label "$template_type"
}

# Enhanced HITL approval workflow with template support
hitl_approval_workflow() {
  local issue_number=$1
  local template_type=$2
  local operation_type=$3
  local threshold_value=${4:-"N/A"}

  # Get template configuration
  apply_hitl_template $issue_number $template_type $threshold_value

  # Post template-based approval request
  gh issue comment $issue_number --body "🔒 **HUMAN APPROVAL REQUIRED** ($template_type)

  **Operation**: $operation_type
  **Template**: $template_type
  **Threshold**: $threshold_value
  **Delegation Results**: [Link to deliverables]

  **Required Action**: Please review and respond with:
  - \`/approve\` - Approve delegation results and continue workflow
  - \`/reject\` - Reject delegation results and require rework
  - \`/escalate\` - Escalate to higher authority

  **Timeout**: ${timeout_minutes} minutes - will auto-escalate if no response"

  # Monitor for human responses with template-specific timeouts
  poll_hitl_responses $issue_number $timeout_minutes
}
```

## Inputs
- **Delegation Request**: Task definition, scope, requirements
- **Target Agent**: Identified specialist for the work
- **Parent Context**: Main workflow/issue being supported
- **Quality Standards**: Acceptance criteria and validation requirements
- **Timeline**: Due date and SLO expectations

## Outputs
- **GitHub Issue**: Complete audit trail of delegation lifecycle
- **Deliverables**: Work products from target agent (code, docs, analysis, etc.)
- **Status Updates**: Progress tracking and milestone notifications
- **Quality Reports**: Validation results and acceptance confirmation
- **Handoff Documentation**: Context for workflow continuation

## Failure Handling

### Timeout Scenarios
- **No Pickup**: Agent doesn't acknowledge delegation within SLO
  - **Recovery**: Escalate to @Orchestrator for reassignment
  - **Action**: Add `escalation-required` label, notify management

- **Progress Stalled**: No updates for >48 hours during active work
  - **Recovery**: Direct agent contact, workload rebalancing
  - **Action**: Add `needs-attention` label, manager notification

### Quality Failures
- **Inadequate Deliverables**: Outputs don't meet acceptance criteria
  - **Recovery**: Reopen issue with specific feedback
  - **Action**: Add `delegation-failed` label, provide detailed requirements

- **Scope Misunderstanding**: Agent delivers wrong/incomplete work
  - **Recovery**: Clarify requirements, partial re-delegation if needed
  - **Action**: Update issue description, provide examples

### Agent Unavailability
- **Agent Overload**: Target agent has too many active delegations
  - **Recovery**: Load balancing, alternative agent assignment
  - **Action**: Reassign via `assigned-to-{new-agent}` label update

- **Agent Expertise Gap**: Target agent lacks required skills
  - **Recovery**: Pair programming, knowledge transfer, reassignment
  - **Action**: Update delegation type or reassign to appropriate specialist

## Integration with Existing Protocols

### Specialized Protocol Coordination
P-DELEGATION-DEFAULT runs **alongside** specialized protocols:

- **P-TDD Integration**: Backend-Engineer delegates test creation to QATester
  ```
  1. Backend-Engineer creates delegation-qa issue for test creation
  2. QATester follows P-TDD protocol (Red phase)
  3. QATester reports failing tests back via delegation completion
  4. Backend-Engineer continues P-TDD (Green phase)
  ```

- **P-HANDOFF-PO-ARCH Integration**: Product-Owner to System-Architect handoff
  ```
  1. Product-Owner completes requirements (existing P-HANDOFF flow)
  2. System-Architect creates delegation-analysis for ASR extraction
  3. asr-writer completes ASR analysis via delegation
  4. System-Architect continues with architecture design
  ```

- **P-QGATE Integration**: Quality gate validation delegation
  ```
  1. Development completes feature
  2. P-QGATE triggers quality validation delegation
  3. Code-Reviewer/QATester validates via delegation issue
  4. P-QGATE continues based on delegation results
  ```

### Label Coordination
P-DELEGATION-DEFAULT labels coordinate with other protocol labels:
- Protocol-specific labels (e.g., `p-tdd`, `p-qgate`) applied alongside delegation labels
- Delegation status doesn't override protocol status - both maintained

## Protocol Examples

### Example 1: Analysis Delegation (ASR Extraction)
**Scenario**: System-Architect needs ASR extraction for Issue #123

```bash
# Step 1: Pre-Delegation
gh issue create --template agent-delegation-analysis.yml \
  --title "[DELEGATION] Extract ASRs for User Authentication Feature #123" \
  --assignee asr-writer

# Auto-applied labels: delegation, delegation-analysis, delegation-pending
# Manual label: assigned-to-asr-writer

# Step 2-3: Monitoring & Work
# asr-writer updates status and completes ASR extraction

# Step 4-5: Completion & Handoff
# asr-writer posts deliverables and closes issue
# System-Architect continues with architecture design using extracted ASRs
```

### Example 2: Implementation Delegation (Feature Development)
**Scenario**: Orchestrator delegates API implementation to Backend-Engineer

```bash
# Step 1: Pre-Delegation
gh issue create --template agent-delegation-implementation.yml \
  --title "[DELEGATION] Implement User Dashboard API #456" \
  --assignee backend-engineer

# Step 2: Backend-Engineer picks up, follows P-TDD
# Step 3: Backend-Engineer delegates test creation to QATester
gh issue create --template agent-delegation-qa.yml \
  --title "[DELEGATION] Create tests for Dashboard API #456" \
  --assignee qa-tester

# Nested delegation: QATester completes tests, Backend-Engineer continues implementation
# Step 4-5: Backend-Engineer completes API, Orchestrator continues with integration
```

### Example 3: QA Delegation (Code Review)
**Scenario**: Development team needs security review before deployment

```bash
# Step 1: Pre-Delegation
gh issue create --template agent-delegation-qa.yml \
  --title "[DELEGATION] Security review for Payment Processing PR #789" \
  --assignee security-auditor

# Step 2-4: Security-Auditor performs review, posts findings
# Step 5: Development team addresses findings and continues deployment
```

### Example 4: Operations Delegation (Incident Response)
**Scenario**: Production incident requires SRE expertise

```bash
# Step 1: Pre-Delegation
gh issue create --template agent-delegation-operations.yml \
  --title "[DELEGATION] P0 Incident: API Gateway Outage" \
  --assignee sre

# Step 2: SRE acknowledges immediately (12-hour SLO for operations)
# Step 3: SRE provides incident updates every 30 minutes
# Step 4: SRE resolves incident and posts post-mortem
# Step 5: Incident commander continues with stakeholder communication
```

### Example 5: Planning Delegation (Implementation Blueprint)
**Scenario**: Backend-Engineer needs detailed implementation plan

```bash
# Step 1: Pre-Delegation
gh issue create --template agent-delegation-planning.yml \
  --title "[DELEGATION] Create implementation blueprint for Microservices Migration #999" \
  --assignee blueprint-writer

# Step 2-4: Blueprint-Writer creates comprehensive implementation plan
# Step 5: Backend-Engineer uses blueprint to execute implementation following P-TDD
```

## Success Metrics

### Performance Metrics
- **Delegation Pickup Time**: Time from creation to agent acknowledgment
  - Target: <24 hours for planning/analysis, <48 hours for implementation, <12 hours for operations/qa
- **Completion Rate**: Percentage of delegations completed successfully
  - Target: >95% completion rate
- **Cycle Time**: Total time from delegation to deliverable handoff
  - Target: Within agreed SLO per delegation type
- **Platform Optimization**: Monitoring efficiency gains from platform-aware configurations
  - Target: 50% reduction in unnecessary polling for Claude Code implementations

### Quality Metrics
- **Deliverable Acceptance Rate**: Percentage of deliverables accepted on first submission
  - Target: >90% acceptance rate (improved from enhanced verification feedback)
- **Rework Rate**: Percentage of delegations requiring significant revision
  - Target: <10% rework rate (reduced through better failure explanations)
- **Audit Trail Completeness**: Percentage of delegations with complete documentation
  - Target: 100% audit trail completeness
- **Verification Failure Recovery**: Time to resolution after verification failure
  - Target: <24 hours from failure detection to re-delegation completion

### Coordination Metrics
- **Escalation Rate**: Percentage of delegations requiring escalation
  - Target: <5% escalation rate
- **Agent Utilization**: Workload distribution across available agents
  - Target: Balanced workload, no agent >80% capacity
- **Protocol Integration**: Successful coordination with specialized protocols (P-TDD, P-QGATE, etc.)
  - Target: 100% successful integration

### Human-in-the-Loop Metrics
- **HITL Response Time**: Time from approval request to human response
  - Target: <2 hours during business hours, <4 hours overall
- **HITL Approval Rate**: Percentage of HITL requests approved on first review
  - Target: >85% approval rate
- **HITL Timeout Rate**: Percentage of HITL requests that timeout without response
  - Target: <5% timeout rate

## Monitoring and Alerting

### Automated Monitoring
```bash
# Daily delegation health check
gh issue list --label "delegation" --state open --json number,title,labels,assignees,created_at

# Overdue delegation detection
gh issue list --label "delegation-pending" --json created_at | \
  jq '.[] | select((now - (.created_at | strptime("%Y-%m-%dT%H:%M:%SZ") | mktime)) > 86400)'

# Agent workload analysis
for agent in $(gh label list | grep "assigned-to-" | cut -f1); do
  count=$(gh issue list --label "$agent,delegation-in-progress" --json number | jq length)
  echo "$agent: $count active delegations"
done

# Blocked delegation alerts
gh issue list --label "delegation-blocked" --json number,title,assignees
```

### Escalation Triggers
- Delegation pending >24 hours (analysis/planning) or >12 hours (operations/qa)
- No progress updates for >48 hours during active work
- Delegation blocked for >24 hours without resolution plan
- Agent with >5 active delegations (overload detection)
- Failed delegations requiring management attention

---

**Protocol Code**: P-DELEGATION-DEFAULT
**Version**: 1.0
**Status**: Active
**Category**: System/Coordination
**Applies To**: All agents in DevGru ecosystem
**Integration**: Runs alongside specialized protocols (P-TDD, P-HANDOFF, P-QGATE, etc.)
**Documentation**: See `.github/labels.md` for label details, `.github/ISSUE_TEMPLATE/` for templates