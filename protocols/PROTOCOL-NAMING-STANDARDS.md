# Protocol Naming Standards

## Purpose
This document establishes official naming conventions for all protocols in the DevGru Framework to ensure consistency, discoverability, and maintainability.

## Naming Convention Rules

### Protocol Prefix Categories

| Prefix | Category | Purpose | Examples |
|--------|----------|---------|----------|
| **P-** | Process Protocols | Core development, quality, and operational processes | P-TDD, P-CODE-REVIEW, P-API-CONTRACT-VALIDATION |
| **QG-** | Quality Gate Protocols | HITL approval gates between framework phases | QG-PHASE1, QG-PHASE2, QG-PHASE7 |
| **GH-** | GitHub Integration Protocols | GitHub-specific workflow automations | GH-1 (GitHub Issue Triage) |
| **CA-** | Command Authority Protocols | Orchestrator command authority actions | CA-CS-NotifyHuman |

### Naming Structure

**Standard Format**: `{PREFIX}-{SHORT-NAME}-{Description}.md`

- **PREFIX**: One of P-, QG-, GH-, CA-
- **SHORT-NAME**: Uppercase, hyphen-separated, 2-4 words max
- **Description**: Full descriptive name with hyphens
- **Extension**: Always `.md`

**Examples**:
- ✅ `P-TDD-Test-Driven-Development-Protocol.md`
- ✅ `QG-PHASE4-Backend-Development-Review-Quality-Gate.md`
- ✅ `GH-1-Github-Issue-Triage-Protocol.md`
- ❌ `Technology-Radar-Protocol.md` (no prefix)
- ❌ `STRAT-PRIO-001-RICE-Scoring-Protocol.md` (non-standard prefix)

### Protocol ID Format (Internal Reference)

When referencing protocols in documentation or agent specifications:

- **Format**: `{PREFIX}-{SHORT-NAME}`
- **Examples**: `P-TDD`, `QG-PHASE6`, `GH-1`
- **Usage**: "Agent follows **P-TDD** protocol for all feature development"

## Current Protocol Inventory

### Compliant Protocols (40)

#### Quality Gate Protocols (10)
- `QG-PHASE1-Requirements-Approval-Quality-Gate.md`
- `QG-PHASE2-Architecture-Review-Quality-Gate.md`
- `QG-PHASE3-Infrastructure-Setup-Validation-Quality-Gate.md`
- `QG-PHASE4-Backend-Development-Review-Quality-Gate.md`
- `QG-PHASE5-Frontend-Development-Review-Quality-Gate.md`
- `QG-PHASE6-Integration-Testing-Review-Quality-Gate.md`
- `QG-PHASE7-Final-Deployment-Approval-Quality-Gate.md`
- `QG-ADR-VALIDATION-Quality-Gate.md`
- `QG-ALIGN-VALIDATION-Quality-Gate.md`
- `QG-ASR-VALIDATION-Quality-Gate.md`

#### Process Protocols (29)

**Architecture**:
- `P-ARCH-INTEGRATION-Architecture-Integration-Protocol.md`

**Development**:
- `P-API-CONTRACT-VALIDATION-API-Contract-Validation-Protocol.md`
- `P-API-DEV-API-Development-Lifecycle-Protocol.md`
- `P-BUG-FIX-Bug-Triage-and-Resolution-Protocol.md`
- `P-DB-MIGRATE-Zero-Downtime-Database-Migration-Protocol.md`
- `P-FEATURE-DEV-New-Feature-Development-Lifecycle-Protocol.md`
- `P-FRONTEND-DEV-Frontend-Development-Workflow-Protocol.md`
- `P-TDD-Test-Driven-Development-Protocol.md`

**Operations**:
- `P-BACKUP-TEST-Backup-and-Restore-Testing-Protocol.md`
- `P-DEPLOYMENT-VALIDATION-Deployment-Validation-Checks-Protocol.md`

**Privacy**:
- `P-CONSENT-DESIGN-User-Consent-Management-Protocol.md`
- `P-DATA-MINIMIZATION-Data-Minimization-Enforcement-Protocol.md`
- `P-ETHICAL-DESIGN-Ethical-Design-and-Dark-Pattern-Prevention-Protocol.md`
- `P-PIA-Privacy-Impact-Assessment-Protocol.md`
- `P-PRIVACY-BY-DESIGN-Privacy-by-Design-Lifecycle-Protocol.md`

**Product**:
- `P-POST-LAUNCH-Monitoring-and-Optimization-Protocol.md`
- `P-USER-RESEARCH-User-Interview-and-Research-Protocol.md`

**Quality**:
- `P-ACCESSIBILITY-GATE-Accessibility-Compliance-Gate-Protocol.md`
- `P-DESIGN-REVIEW-Design-Review-Process-Protocol.md`
- `P-E2E-TESTING-End-to-End-Testing-Workflow-Protocol.md`
- `P-QGATE-Automated-Quality-Gate-Protocol.md`

**Security**:
- `P-DEVSECOPS-Integrated-DevSecOps-Pipeline-Protocol.md`
- `P-SEC-CHAOS-Security-Chaos-Engineering-Protocol.md`
- `P-SEC-INCIDENT-Cybersecurity-Incident-Response-Protocol.md`
- `P-SEC-VULN-Automated-Vulnerability-Management-Protocol.md`

**System**:
- `P-ENV-SETUP-Environment-Setup-Configuration-Protocol.md`
- `P-HANDOFF-Agent-to-Agent-Task-Handoff-Protocol.md`
- `P-INFRASTRUCTURE-SETUP-Environment-Provisioning-Protocol.md`
- `P-LEARN-Continuous-Learning-and-Self-Optimization-Protocol.md`
- `P-ORCHESTRATION-Improved-Orchestration-Workflow-Protocol.md`
- `P-RECOVERY-Failure-Recovery-and-Transactional-Rollback-Protocol.md`
- `P-RESOURCE-Task-Queue-and-Resource-Management-Protocol.md`

#### GitHub Integration Protocols (1)
- `GH-1-Github-Issue-Triage-Protocol.md`

### Migrated Protocols (28) - COMPLETED ✅

**Status**: All legacy protocols have been successfully migrated to standard naming convention as of Issue #99.

**Migration Summary**:
- ✅ Architecture (9 files): All renamed to P-{SHORT-NAME} format
- ✅ Operations (3 files): All renamed to P-/GH- format
- ✅ Product (9 files): All renamed to P-{SHORT-NAME} format
- ✅ Quality (2 files): All renamed to P-{SHORT-NAME} format
- ✅ Security (1 file): Renamed to P-{SHORT-NAME} format
- ✅ System (4 files): Renamed to P-{SHORT-NAME} format, duplicates consolidated

**Note**: References in agent specifications and documentation require systematic updates. See Issue #99 for reference update tracking.

#### Architecture (9 files)
| Current Name | Standard Name | Protocol ID | Status |
|--------------|---------------|-------------|--------|
| `ADR-Creation-Protocol.md` | `P-ADR-CREATION-Architecture-Decision-Record-Creation-Protocol.md` | P-ADR-CREATION | Legacy |
| `ASR-ADR-Alignment-Protocol.md` | `P-ASR-ADR-ALIGNMENT-Architecture-Requirement-Alignment-Protocol.md` | P-ASR-ADR-ALIGNMENT | Legacy |
| `ASR-Extraction-Protocol.md` | `P-ASR-EXTRACTION-Architecture-Significant-Requirement-Extraction-Protocol.md` | P-ASR-EXTRACTION | Legacy |
| `C4-Architectural-Visualization-Protocol.md` | `P-C4-VISUALIZATION-C4-Architecture-Diagram-Protocol.md` | P-C4-VISUALIZATION | Legacy |
| `CFR-001-Cross-Functional-Requirements-Integration-Protocol.md` | `P-CFR-INTEGRATION-Cross-Functional-Requirements-Integration-Protocol.md` | P-CFR-INTEGRATION | Legacy |
| `DEBT-001-Technical-Debt-Management-Protocol.md` | `P-DEBT-MANAGEMENT-Technical-Debt-Management-Protocol.md` | P-DEBT-MANAGEMENT | Legacy |
| `FIT-001-Architecture-Fitness-Protocol.md` | `P-ARCH-FITNESS-Architecture-Fitness-Function-Protocol.md` | P-ARCH-FITNESS | Legacy |
| `PAT-001-Architectural-Pattern-Management-Protocol.md` | `P-PATTERN-MANAGEMENT-Architectural-Pattern-Management-Protocol.md` | P-PATTERN-MANAGEMENT | Legacy |
| `Technology-Radar-Protocol.md` | `P-TECH-RADAR-Technology-Radar-Evaluation-Protocol.md` | P-TECH-RADAR | Legacy |

#### Operations (3 files)
| Current Name | Standard Name | Protocol ID | Status |
|--------------|---------------|-------------|--------|
| `Github-Maintenance-Protocol.md` | `GH-MAINTENANCE-GitHub-Repository-Maintenance-Protocol.md` | GH-MAINTENANCE | Legacy |
| `Local-Dependency-Maintenance-Protocol.md` | `P-DEPENDENCY-MAINTENANCE-Local-Dependency-Maintenance-Protocol.md` | P-DEPENDENCY-MAINTENANCE | Legacy |
| `OPS-001-Operational-Resilience-Protocol.md` | `P-OPS-RESILIENCE-Operational-Resilience-Protocol.md` | P-OPS-RESILIENCE | Legacy |

#### Product (9 files)
| Current Name | Standard Name | Protocol ID | Status |
|--------------|---------------|-------------|--------|
| `COMM-LIAISON-001-Stakeholder-Communication-Protocol.md` | `P-STAKEHOLDER-COMM-Stakeholder-Communication-Liaison-Protocol.md` | P-STAKEHOLDER-COMM | Legacy |
| `EXPERIMENT-001-AB-Experimentation-Protocol.md` | `P-AB-EXPERIMENT-AB-Testing-Experimentation-Protocol.md` | P-AB-EXPERIMENT | Legacy |
| `FEEDBACK-INGEST-001-Customer-and-Stakeholder-Feedback-Ingestion-Protocol.md` | `P-FEEDBACK-INGEST-Customer-Feedback-Ingestion-Protocol.md` | P-FEEDBACK-INGEST | Legacy |
| `File-Read-Write-Protocol.md` | `P-FILE-IO-File-Input-Output-Protocol.md` | P-FILE-IO | Legacy |
| `METRIC-TRACK-001-Continuous-Value-Measurement-Protocol.md` | `P-METRIC-TRACKING-Continuous-Value-Measurement-Protocol.md` | P-METRIC-TRACKING | Legacy |
| `ROADMAP-UPDATE-001-Roadmap-Synchronization-Protocol.md` | `P-ROADMAP-SYNC-Roadmap-Synchronization-Protocol.md` | P-ROADMAP-SYNC | Legacy |
| `STRAT-PRIO-001-RICE-Scoring-Protocol.md` | `P-RICE-SCORING-RICE-Prioritization-Protocol.md` | P-RICE-SCORING | Legacy |
| `STRAT-PRIO-002-Bug-Triage-and-Prioritization-Protocol.md` | `P-BUG-PRIORITIZATION-Bug-Triage-Prioritization-Protocol.md` | P-BUG-PRIORITIZATION | Legacy |
| `USER-STORY-MAP-001-User-Story-Mapping-Protocol.md` | `P-USER-STORY-MAPPING-User-Story-Mapping-Protocol.md` | P-USER-STORY-MAPPING | Legacy |

#### Quality (2 files)
| Current Name | Standard Name | Protocol ID | Status |
|--------------|---------------|-------------|--------|
| `Code-Reviewing-Protocol.md` | `P-CODE-REVIEW-Code-Review-Process-Protocol.md` | P-CODE-REVIEW | Legacy |
| `Feedback-Generation-Protocol.md` | `P-FEEDBACK-GENERATION-Feedback-Generation-Protocol.md` | P-FEEDBACK-GENERATION | Legacy |

#### Security (1 file)
| Current Name | Standard Name | Protocol ID | Status |
|--------------|---------------|-------------|--------|
| `Security-Scan-Protocol.md` | `P-SECURITY-SCAN-Security-Scanning-Protocol.md` | P-SECURITY-SCAN | Legacy |

#### System (4 files)
| Current Name | Standard Name | Protocol ID | Status |
|--------------|---------------|-------------|--------|
| `CORE-COORD-002-Hub-and-Spoke-Coordination-Pattern-Protocol.md` | `P-HUB-SPOKE-COORDINATION-Hub-and-Spoke-Coordination-Protocol.md` | P-HUB-SPOKE-COORDINATION | Legacy, Possible Duplicate |
| `Hub-and-Spoke-Coordination-Protocol.md` | Same as above | P-HUB-SPOKE-COORDINATION | Legacy, Possible Duplicate |
| `Research-Cache-Management-Protocol.md` | `P-CACHE-MANAGEMENT-Research-Cache-Management-Protocol.md` | P-CACHE-MANAGEMENT | Legacy |

**Note**: `Hub-and-Spoke-Coordination-Protocol.md` and `CORE-COORD-002-Hub-and-Spoke-Coordination-Pattern-Protocol.md` appear to be duplicates and should be consolidated.

## Migration Guidance

### For New Protocols

1. **Always use standard prefix**: P-, QG-, GH-, or CA-
2. **Use SHORT-NAME format**: 2-4 uppercase hyphen-separated words
3. **Include full description**: Readable filename with protocol purpose
4. **Follow filename pattern**: `{PREFIX}-{SHORT-NAME}-{Description}-Protocol.md`

### For Existing Protocols

**Priority 1 (Do Not Rename)**:
- Protocols referenced in agent specifications
- Protocols referenced in framework documentation
- Protocols actively used in workflows

**Priority 2 (Gradual Migration)**:
- When updating a legacy protocol, rename to standard format
- Update all references in same commit
- Document rename in commit message
- Add redirect note in old location if needed

**Priority 3 (Consolidation)**:
- Identify and merge duplicate protocols
- Archive obsolete protocols to `protocols/archive/`
- Update references to point to canonical version

## Protocol Reference Best Practices

### In Agent Specifications

Use Protocol ID format for clarity:

```markdown
### Core Responsibilities
- Implements **P-TDD** (Test-Driven Development) for all feature work
- Validates code through **P-CODE-REVIEW** before merge
- Follows **P-API-CONTRACT-VALIDATION** for API development
```

### In Framework Documentation

Reference protocols with full context:

```markdown
## Quality Gate 4: Backend Readiness
- **Protocol Reference**: QG-PHASE4-Backend-Development-Review-Quality-Gate
- **HITL Trigger**: Orchestrator submits comprehensive backend review
```

### In Orchestrator Commands

Use Protocol ID for command parameters:

```json
{
  "command": "execute_quality_gate",
  "protocol": "QG-PHASE4",
  "artifacts": ["backend-impl/", "test-results/"]
}
```

## Compliance Enforcement

### Automated Checks (Future)

- GitHub Actions workflow to validate new protocol filenames
- Pre-commit hook to check protocol references
- Automated protocol inventory generation

### Manual Review

- All new protocols must follow naming standards
- Protocol renames require approval from Framework maintainers
- Legacy protocol migration tracked in separate issues

## Summary Statistics

- **Total Protocols**: 68
- **Compliant**: 40 (58.8%)
- **Non-Compliant (Legacy)**: 28 (41.2%)
- **Quality Gates**: 10 (100% compliant)
- **Process Protocols**: 29 compliant + 25 legacy = 54 total
- **GitHub Integration**: 1 compliant + 1 legacy = 2 total
- **Duplicates Identified**: 2 (Hub-and-Spoke protocols)

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-08 | Initial protocol naming standards document | Claude Code |

## Related Documentation

- [Protocol README](./README.md) - Overview of all protocols
- [Agent Specifications](../proposed_agents/) - Agent protocol references
- [DevGru Framework](../docs/architecture/DevGru_Framework.md) - Framework integration
