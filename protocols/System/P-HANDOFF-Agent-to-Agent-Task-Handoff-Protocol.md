# P-HANDOFF: Agent-to-Agent Task Handoff Protocol

## Objective
Define standardized agent-to-agent task handoff process ensuring context preservation, deliverable validation, and seamless workflow continuation across Framework phases and quality gates.

## Tool Requirements

- **TOOL-COLLAB-001** (GitHub Integration): Handoff documentation, artifact management, and agent coordination
  - Execute: Handoff documentation, artifact storage, agent coordination, task tracking, deliverable management
  - Integration: CLI commands (gh, git), API calls, repository operations, documentation systems, coordination workflows
  - Usage: Agent handoff coordination, artifact management, task tracking, documentation storage, team coordination

- **TOOL-CICD-001** (Pipeline Platform): Artifact validation, quality gate verification, and deliverable assessment
  - Execute: Artifact validation, quality gate verification, deliverable assessment, pipeline status validation, test result verification
  - Integration: CI/CD platforms, validation systems, quality gates, automated testing, pipeline management
  - Usage: Handoff validation, quality verification, deliverable assessment, pipeline coordination, validation workflows

- **TOOL-ORG-001** (Orchestration): Agent coordination, handoff orchestration, and workflow management
  - Execute: Agent coordination, handoff orchestration, workflow management, task assignment, agent communication
  - Integration: Orchestration platforms, agent management systems, workflow coordination, task management, communication systems
  - Usage: Agent handoff orchestration, workflow coordination, task management, agent communication, orchestration workflows

- **TOOL-DATA-003** (Privacy Management): Handoff data protection, context security, and information governance
  - Execute: Handoff data protection, context security validation, information governance, data access control, audit logging
  - Integration: Privacy management systems, data protection tools, access control, audit systems, governance frameworks
  - Usage: Handoff security, context protection, data governance, access control, audit trail management

## Trigger
- After quality gate passage (QG-PHASE1 through QG-PHASE7)
- During Framework phase transitions (Phase 1→2→3→4→5→6→7→8)
- When agent completes assigned task and next agent must continue
- When specialist expertise transition required (e.g., Backend-Engineer → Frontend-Engineer)

## Prerequisites
- Source agent completed assigned task
- Deliverables validated against acceptance criteria via **TOOL-CICD-001**
- Quality gate passed (if applicable) via **TOOL-CICD-001**
- Next agent identified and available via **TOOL-ORG-001**
- Handoff artifacts prepared via **TOOL-COLLAB-001**

## Steps

1. **Handoff Preparation (Source Agent)**:
   - **Deliverable Packaging**: Gather all outputs from completed task:
     - Source code (feature branch, commit SHAs)
     - Documentation (specs, diagrams, API docs, runbooks)
     - Test artifacts (test results, coverage reports, QA findings)
     - Configuration files (env vars, IaC, deployment configs)
     - Quality gate reports (QG-PHASE validation results, HITL approvals)
   - **Context Document Creation**: Write handoff\_context.md containing:
     - Task summary (what was accomplished)
     - Key decisions made and rationale
     - Known issues or limitations
     - Dependencies or blockers for next phase
     - Recommended next steps

2. **Artifact Validation (Source Agent)**:
   - Verify deliverables meet handoff criteria:
     - All acceptance criteria satisfied
     - Quality gate passed (if applicable)
     - Documentation complete
     - No blocking issues
   - Run pre-handoff checklist:
     - Code committed to feature branch
     - Tests passing in CI/CD
     - Configuration validated
     - Security scan passed (if applicable)

3. **Handoff Notification (Source Agent via Orchestrator)**:
   - Source agent notifies Orchestrator of task completion
   - Provides handoff package location (shared filesystem path, artifact repository)
   - Indicates next agent assignment (e.g., "Backend-Engineer → Frontend-Engineer")
   - Flags any special considerations or urgency

4. **Task Assignment (Orchestrator)**:
   - Orchestrator validates handoff package completeness
   - Uses CORE-COORD-002 to dispatch task to next agent
   - Provides task_packet.json with:
     - Previous agent's deliverables (artifact paths)
     - Handoff context document (handoff_context.md)
     - Current phase and quality gate status
     - Acceptance criteria for next phase
     - Priority and deadline

5. **Handoff Acceptance (Receiving Agent)**:
   - Receiving agent reviews handoff package:
     - Reads handoff_context.md for context
     - Validates all referenced artifacts accessible
     - Confirms understanding of task requirements
   - Performs acceptance validation:
     - Verifies deliverables match expectations
     - Checks for any missing dependencies
     - Identifies clarification needs
   - If handoff valid: Acknowledge acceptance, begin work
   - If issues found: Request clarification or reject handoff with specific feedback

6. **Clarification Loop (if needed)**:
   - Receiving agent requests clarification from source agent via Orchestrator
   - Source agent provides additional context or missing artifacts
   - Orchestrator facilitates asynchronous communication
   - Loop continues until receiving agent satisfied
   - If unresolvable: Orchestrator escalates to Human Command Group

7. **Work Continuation (Receiving Agent)**:
   - Receiving agent begins task using provided context
   - References previous agent's artifacts and documentation
   - Maintains traceability to previous work (commit references, documentation links)
   - Logs any deviations or changes from original plan

8. **Handoff Completion Logging**:
   - Orchestrator logs successful handoff:
     - Source agent ID
     - Receiving agent ID
     - Handoff timestamp
     - Deliverable manifest (list of artifacts)
     - Validation status (acceptance, clarification requests, rejections)
   - Metrics tracked:
     - Handoff time (preparation to acceptance)
     - Clarification cycles count
     - Rejection rate per agent pair

## Expected Outputs
- Handoff package containing:
  - Deliverable artifacts (code, docs, configs, test results)
  - handoff_context.md (summary, decisions, issues, next steps)
  - Quality gate reports (if applicable)
- Task assignment (task_packet.json for receiving agent)
- Handoff acceptance confirmation (receiving agent acknowledgment)
- Handoff completion log (Orchestrator record)

## Failure Handling
- **Incomplete Deliverables**: Source agent blocked from handoff until deliverables complete. Orchestrator notifies source agent of missing artifacts.
- **Quality Gate Failure**: Handoff blocked until quality gate passed. Source agent must remediate issues and resubmit.
- **Receiving Agent Rejection**: Orchestrator facilitates clarification loop. If unresolved after 3 cycles, escalate to Human Command Group.
- **Missing Artifacts**: Receiving agent requests specific artifacts. Source agent provides within 2 hours. If unavailable, Orchestrator escalates.
- **Context Insufficient**: Receiving agent requests additional context. Source agent updates handoff_context.md. Orchestrator re-dispatches updated package.
- **Blocking Issues**: If source agent identifies blockers, handoff proceeds but blocker flagged as high priority. Receiving agent addresses blocker first or escalates.

## Common Handoff Scenarios

### Scenario 1: Backend → Frontend (Phase 4 → Phase 5)
- **Source**: Backend-Engineer
- **Deliverables**: API implementation, OpenAPI spec, database schema, backend tests
- **Context**: Endpoint URLs, authentication flow, data models, rate limits
- **Receiving**: Frontend-Engineer
- **Acceptance**: Validates API contract matches design requirements

### Scenario 2: Frontend → QA (Phase 5 → Phase 6)
- **Source**: Frontend-Engineer
- **Deliverables**: UI components, frontend tests, Lighthouse reports, accessibility audits
- **Context**: Component storybook, test coverage gaps, known browser issues
- **Receiving**: QA-Tester
- **Acceptance**: Validates test environment access, component documentation complete

### Scenario 3: QA → DevOps (Phase 6 → Phase 7)
- **Source**: QA-Tester
- **Deliverables**: E2E test results, integration test reports, staging validation
- **Context**: Test data requirements, third-party dependencies, performance baselines
- **Receiving**: DevOps-Engineer
- **Acceptance**: Validates staging environment stable, deployment prerequisites met

### Scenario 4: DevOps → SRE (Phase 7 → Phase 8)
- **Source**: DevOps-Engineer
- **Deliverables**: Production deployment logs, infrastructure configs, monitoring dashboards
- **Context**: Deployment strategy (blue-green/canary), rollback procedures, alert thresholds
- **Receiving**: SRE
- **Acceptance**: Validates monitoring operational, incident runbooks available

## Related Protocols
- **CORE-COORD-002**: Hub-and-Spoke Coordination (Orchestrator dispatches handoffs)
- **P-QGATE**: Quality Gates (handoff often triggered by gate passage)
- **P-RESOURCE**: Resource Management (handoff respects execution slot allocation)
- **QG-PHASE1-7**: Quality Gates (validate deliverables before handoff)
- **P-FRONTEND-DEV, P-BACKEND-DEV**: Development workflows (include handoff steps)

## Validation Criteria
- Handoff package complete (all deliverables present)
- handoff_context.md provided with summary, decisions, issues, next steps
- Quality gate passed (if phase transition)
- Receiving agent acknowledges acceptance
- No unresolved clarification requests
- Handoff completion logged by Orchestrator
- Handoff time <2 hours (preparation to acceptance, 95th percentile)

## Performance SLOs
- Handoff preparation time: <30 minutes (source agent packages deliverables)
- Handoff acceptance time: <1 hour (receiving agent validates and accepts)
- Clarification response time: <2 hours (source agent responds to questions)
- Total handoff time: <2 hours (preparation to work continuation, 95th percentile)
- Handoff rejection rate: <10% (measure of handoff quality)
