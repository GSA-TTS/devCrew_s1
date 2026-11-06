# Resources for Agent Reasoning

Resources that support both **agent design** and **real-time agent reasoning**. Agents can load files from this folder as inputs during their reasoning steps. For example, a plan-and-execute agent may load guides to structure its planning phase before acting.

## Guides

Each guide is a self-contained, structured methodology an agent can follow to complete a specific class of analytical or design task. Guides are written to be domain-agnostic and loadable at runtime.

Guides are grouped into category subfolders directly under `advanced_task_guides/`. Every file is named `guide_<Name>.md`, so a guide is loaded as `advanced_task_guides/<subfolder>/guide_<Name>.md`.

| Subfolder | Guides |
|---|---|
| `planning/` | MetaReasoning, IntelligentGoalDecomposition, HierarchicalTaskNetworkPlanning, PlanExecuteDecoupling, PlanTodoRecitation, TaskManagementOrchestration, ConstraintSatisfactionPlanning, ScenarioBasedPlanning, WorldModelSimulationPlanning |
| `research-analysis/` | ArxivResearch, BarrierAnalysis, Cross-domainAnalogyandTransfer, SetComparison, StratifiedComparative_n_FactorVariationAnalysis, TemporalEvolutionAnalysisandForecasting |
| `policy-risk/` | Cross-jurisdictionalComparativePolicyAnalysis, InformationDependencyDisclosureRiskAnalysis, SystemSpecificRiskAssessment, ControlEffectiveness-by-ConditionAnalysis, LifecycleComparison_n_RiskAnalysis |
| `design-architecture/` | DesignAdaptation, DesignTechnicalBookStudyPlan, FrameworkMappingAdoptionFitAnalysis, MonitoringDesignConstraintAnalysis, SchemaFlexibilityandEvolution, TelemetryDesign |
| `knowledge-graphs/` | KG_SchemaDesign, KG_EntityResolutionDedup, KG_HumanAIcolab, KG_QualityControl, KG_ScalabilityArch, KG_identifierFairPrinciples, KG_DataProvenanceEvidenceTracking |
| `ontology/` | ontology_TopDownBuild, ontology_CompetancyQuestions, ontology_CQ2Onto |
| `scoring/` | complexityScoring, techAcceptanceScoring |
| `authoring/` | guidewriting |
| `specialized/` | `MethodInventoryClassificationMaturity Assessment`, AI tutor |
| `memory-management/` | AgentMemoryManagement, AttentionBasedMemoryRetrieval, DistributedMemoryArchitecture, EpisodicMemory, GenerativeAgentMemory, HierarchicalMemory, LatentMemoryNetworks, MemoryConsolidation, MemoryForgetting, MemoryReadWriteOperations, SemanticMemory, StructuredMemory, TemporalKnowledgeGraphMemory, TransactiveMemory, UnstructuredMemory, WorkingMemory |
| `knowledge-retrieval/` | AdvancedKnowledgeRetrieval, AgenticRAG, CodebaseStructureRetrieval, CorrectiveRAG, DeepResearchAgent, GraphRAG, HierarchicalIndexRetrieval, LatentKnowledgeRetrieval, ModularRAG, MultimodalRAG, QueryTransformationRetrieval, SelfRAG |
| `context-management/` | ContextCompression, ContextEditingAndToolResultClearing, ContextEngineeringFrameworks, ContextFailurePrevention, ContextIsolation, ContextLifecycle, ContextManagement, ContextMemoryBlocks, ContextSelection, ContextStateMachines, ContextStreamingProtocols, ContextWritePatterns, FilesystemAsContext, HierarchicalContextArchitecture, KVCacheAwarePromptConstruction, SemanticContextCompression, SlidingWindowContext |
| `reasoning/` | AbductiveReasoning, AnalogicalReasoning, BufferOfThoughts, CausalReasoning, ChainOfThoughtReasoning, ChainOfVerification, ForestOfThought, GraphOfThought, LeastToMostReasoning, MetacognitiveMonitoring, ProactiveClarification, ReflectiveMonteCarloTreeSearch, SelfConsistency, SkeletonOfThought, StepBackPrompting, TreeOfThought |
| `tool-use/` | AgentControlPlane, AgentSkills, CodeAsAction, CodeExecution, ComputerUse, MCPToolGateway, ModelContextProtocol, StructuredReflectionTool, ToolRetrieval, ToolUseAndFunctionCalling |
| `routing/` | CapabilityRouting, ContentBasedRouting, EmbeddingBasedRouting, LLMBasedRouting, RuleBasedRouting |

The `planning/` guides are operational restructurings of a set of prose guides on agent planning patterns. They share a common structure and cross-reference one another by repository path, so several can be loaded together for a single planning task.

The six categories `memory-management/`, `knowledge-retrieval/`, `context-management/`, `reasoning/`, `tool-use/` and `routing/` are operational restructurings of a further 78 prose guides, produced under `authoring/guide_guidewriting.md`. They follow the same conventions as `planning/` and cross-reference one another and the older categories by repository path. Each carries a status block, a phase-and-step Operational Framework, an `Implementation Guidance for AI Agents` section, and an execution tier partition naming which work is deterministic, which requires a model call, and which component holds authority when the two disagree.

Two of the 78 sources were assessed as not operationalizable at the agent layer and were not converted, because their methods require a modified model architecture, training, or access to model internals. The assessment for each is recorded outside this repository with the originating material.

`advanced_task_guides/authoring/guide_guidewriting.md` is the house-style specification for this directory. Load it when writing a new guide rather than when performing an analytical task.

---

## sysprompts/

System prompts are examples about configuring an agent's persona, mandate, and operating constraints. These example sys-prompts mostly target single-agent use cases.

| File | Purpose |
|---|---|
| `aiTutor_sysprompt.md` | Configures a pedagogy-aware AI tutor with knowledge grounding rules, learner modeling, and session lifecycle behavior |

---

## Usage Patterns

**Plan-and-execute**: At the planning step, the agent loads the relevant guide as context, uses it to generate a structured plan, then executes against that plan.

**Agent design**: Use guides and sysprompts as templates or references when defining new agent roles, reasoning protocols, or system prompts.

**Composable reasoning**: Multiple guides can be combined for complex tasks (e.g., load `KG_SchemaDesign` + `ontology_TopDownBuild` together for a knowledge graph build task, or `IntelligentGoalDecomposition` + `HierarchicalTaskNetworkPlanning` + `PlanTodoRecitation` to decompose an objective, expand it into a task network, and hold the resulting plan in context across a long run).
