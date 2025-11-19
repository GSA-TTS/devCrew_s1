# ASR-ADR Alignment Protocol

## Objective
Ensure traceability between ASRs and ADRs, prevent drift, and maintain governance oversight.

## Trigger

- When new ASRs are identified from GitHub issues
- After ADR creation or updates
- During architectural review processes (ARB)
- As part of QG-ALIGN-VALIDATION quality gate execution
- When architectural drift is detected

## Prerequisites

- Existing ADR registry in `/docs/architecture/ADRs` directory
- Identified ASRs documented in `issue_{{issue_number}}_asr.md`
- Access to TOOL-ARCH-001, TOOL-DATA-002, TOOL-AI-001, TOOL-COLLAB-001
- Graph-of-Thoughts cache available and operational
- Architecture Review Board (ARB) process defined and accessible
- Semantic search and analysis tools configured

## Tool Requirements

- **TOOL-ARCH-001** (Architecture Management): ASR-ADR alignment analysis, traceability management, and governance coordination
  - Execute: ASR-ADR alignment analysis, traceability management, governance coordination, alignment validation, architecture coordination
  - Integration: Architecture tools, traceability systems, governance platforms, alignment frameworks, architectural analysis systems
  - Usage: Alignment analysis, traceability management, governance coordination, alignment validation, architectural oversight

- **TOOL-DATA-002** (Statistical Analysis): Impact analysis, coverage assessment, and alignment metrics
  - Execute: Impact analysis, coverage assessment, alignment metrics, dependency analysis, gap analysis
  - Integration: Analytics platforms, impact assessment tools, coverage analysis, metrics systems, dependency tracking
  - Usage: Impact analysis, coverage assessment, alignment analytics, dependency analysis, gap identification

- **TOOL-AI-001** (AI Reasoning): Semantic analysis, requirement matching, and intelligent traceability
  - Execute: Semantic analysis, requirement matching, intelligent traceability, semantic search, requirement alignment
  - Integration: AI platforms, semantic analysis tools, requirement matching systems, intelligent search, alignment algorithms
  - Usage: Semantic alignment, intelligent traceability, requirement matching, semantic analysis, AI-driven alignment

- **TOOL-COLLAB-001** (GitHub Integration): Documentation management, stakeholder coordination, and alignment tracking
  - Execute: Documentation management, stakeholder coordination, alignment tracking, version control, collaboration workflows
  - Integration: CLI commands (gh, git), API calls, repository operations, documentation systems, collaboration workflows
  - Usage: Alignment documentation, stakeholder coordination, tracking management, version control, collaboration coordination

## Steps

1. **ADR Registry Analysis:** Review existing ADRs in `/docs/architecture/ADRs` directory using semantic search and structural analysis for comprehensive coverage assessment. Cache results in GoT Cache.

2. **Cross-Reference Mapping:** Cross-reference identified ASRs in `issue_{{issue_number}}_asr.md` with existing ADRs using semantic similarity and explicit requirement traceability. Link ASRs to ADRs using **Graph-of-Thoughts** if possible.

3. **Coverage Documentation:** Update `issue_{{issue_number}}_asr.md` to note ASRs covered by existing ADRs with explicit links, version references, and coverage gap analysis.

4. **Gap Prioritization:** Identify ASRs requiring new ADRs and prioritize them based on architectural risk, business impact, stakeholder priority, and implementation timeline constraints. Run Monte Carlo Tree Search simulations to estimate risk/impact of missing ADRs.

5. **Dependency Impact Graph Generation:** Visualize how ADR gaps cascade through existing ADR networks. Generate a directed graph in `docs/reports/{{issue}}_DependencyGraph.svg` showing ADR nodes and missing-ASR links to illustrate ripple effects.

6. **Impact Analysis:** Create comprehensive architectural impact analysis for changes to existing ADRs including downstream effects and stakeholder notification requirements. Use Contrastive Analysis to generate downstream impact matrices; save in `docs/reports/..._ImpactAnalysis.md`.

7. **Governance Trigger:** Initiate Architecture Review Board (ARB) process for high-impact decisions requiring formal governance approval.

8. **Quality Gate:** Execute **QG-ALIGN-VALIDATION** before completing.

## Expected Outputs

- Updated `issue_{{issue_number}}_asr.md` with ADR cross-references and traceability links
- Coverage gap analysis report identifying ASRs without corresponding ADRs
- Dependency impact graph (`docs/reports/{{issue}}_DependencyGraph.svg`) showing ADR relationships
- Impact analysis document (`docs/reports/..._ImpactAnalysis.md`) with downstream effects
- ARB review requests for high-impact architectural decisions (if triggered)
- QG-ALIGN-VALIDATION quality gate execution results
- Alignment metrics and coverage statistics

## Failure Handling

- **Semantic search fails**: Fallback to manual ADR review, escalate to System-Architect
- **Graph-of-Thoughts cache corruption**: Rebuild cache from ADR registry, delay execution
- **ADR registry missing/inaccessible**: Escalate to DevOps, block until registry restored
- **QG-ALIGN-VALIDATION failure**: Document gaps, create remediation plan, block phase transition
- **ARB process unavailable**: Queue for next ARB meeting, escalate if time-critical