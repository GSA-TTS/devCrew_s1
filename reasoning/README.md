# reasoning/

Resources that support both **agent design** and **real-time agent reasoning**. Agents can load files from this folder as inputs during their reasoning steps—for example, a plan-and-execute agent loads a guide to structure its planning phase before acting.

---

## Folder Structure

```
reasoning/
├── guides/        # Step-by-step methodology guides for agent reasoning tasks
└── sysprompts/    # System prompts that define agent personas and operating rules
```

---

## guides/

Each guide is a self-contained, structured methodology an agent can follow to complete a specific class of analytical or design task. Guides are written to be domain-agnostic and loadable at runtime.

| Category | Guides |
|---|---|
| **Research & Analysis** | ArxivResearch, BarrierAnalysis, Cross-domainAnalogyandTransfer, SetComparison, StratifiedComparative_n_FactorVariationAnalysis, TemporalEvolutionAnalysisandForecasting |
| **Policy & Risk** | Cross-jurisdictionalComparativePolicyAnalysis, InformationDependencyDisclosureRiskAnalysis, SystemSpecificRiskAssessment, ControlEffectiveness-by-ConditionAnalysis, LifecycleComparison_n_RiskAnalysis |
| **Design & Architecture** | DesignAdaptation, DesignTechnicalBookStudyPlan, FrameworkMappingAdoptionFitAnalysis, MonitoringDesignConstraintAnalysis, SchemaFlexibilityandEvolution, TelemetryDesign |
| **Knowledge Graphs** | KG_SchemaDesign, KG_EntityResolutionDedup, KG_HumanAIcolab, KG_QualityControl, KG_ScalabilityArch, KG_identifierFairPrinciples, KG_DataProvenanceEvidenceTracking |
| **Ontology** | ontology_TopDownBuild, ontology_CompetancyQuestions, ontology_CQ2Onto |
| **Specialized** | MethodInventoryClassificationMaturityAssessment, AI Tutor |

---

## sysprompts/

System prompts that configure an agent's persona, mandate, and operating constraints. Load these at agent initialization to define how the agent behaves across an entire session.

| File | Purpose |
|---|---|
| `aiTutor_sysprompt.md` | Configures a pedagogy-aware AI tutor with knowledge grounding rules, learner modeling, and session lifecycle behavior |

---

## Usage Patterns

**Plan-and-execute**: At the planning step, the agent loads the relevant guide as context, uses it to generate a structured plan, then executes against that plan.

**Agent design**: Use guides and sysprompts as templates or references when defining new agent roles, reasoning protocols, or system prompts.

**Composable reasoning**: Multiple guides can be combined for complex tasks (e.g., load `KG_SchemaDesign` + `ontology_TopDownBuild` together for a knowledge graph build task).
