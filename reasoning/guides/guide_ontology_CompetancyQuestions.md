# Forming Competency Questions for Ontology Development

Competency Questions (CQs) are natural language questions that define the functional requirements of an ontology and serve as litmus tests for its completeness and scope. Originating from the pioneering work of Gruninger \& Fox in the TOVE project and popularized by Noy \& McGuinness in their seminal "Ontology Development 101", CQs bridge the gap between domain expert understanding and formal ontology representation. This guide provides an expansive, domain-agnostic framework for formulating effective competency questions applicable across diverse fields—from healthcare and cybersecurity to smart cities and scientific research.[^1][^2][^3][^4][^5][^6]

## Understanding Competency Questions: Foundations and Purpose

### What Are Competency Questions?

Competency Questions are questions that an ontology must be capable of answering using its axioms, concepts, properties, and relations. They serve multiple critical functions throughout the ontology development lifecycle:[^7][^2]

**Requirements Specification**: CQs help define the ontology scope, identify necessary concepts and relationships, and determine the appropriate level of granularity. They provide a mechanism to verify whether the ontology aligns with established requirements and properly represents the desired knowledge domain.[^2][^8]

**Evaluation Instrument**: CQs function as validation criteria to assess whether the ontology contains sufficient knowledge to answer domain-relevant questions. They help identify flaws in domain modeling and contribute to quality assessment, though they should not be the sole evaluation criterion.[^9][^10][^2]

**Communication Tool**: CQs create a shared language between domain experts (who understand the problem space), ontology engineers (who create formal representations), and stakeholders (who will use the ontology). They make abstract ontological commitments concrete and testable.[^4]

**Scope Management**: By explicitly stating what questions the ontology should answer, CQs help prevent scope creep and maintain focus during iterative development. They define boundaries between what belongs in the ontology and what does not.[^10]

### Historical Context and Methodological Evolution

The concept of competency questions emerged from the **TOVE (TOronto Virtual Enterprise) project** in the mid-1990s. Gruninger and Fox developed a rigorous methodology where CQs played a central role in ontology engineering for enterprise modeling. Their approach emphasized that CQs should not merely be simple lookup queries but should require reasoning across multiple axioms, reflecting the complexity of real-world problems.[^6][^11]

Noy and McGuinness later popularized CQs in their widely-cited "Ontology Development 101" guide, making the approach more accessible to practitioners. They recommended using CQs as one of the first steps in ontology development: after identifying the domain and purpose, developers should sketch competency questions to determine scope and requirements.[^3]

Recent research has expanded our understanding of CQ types and roles. Keet et al. (2024) identified five distinct categories of CQs serving different purposes beyond simple requirements specification, while survey research revealed that 63.5% of ontology developers use iterative approaches to CQ development, recognizing their dynamic nature throughout the development process.[^12][^13][^14][^2]

## Five Types of Competency Questions

Based on recent research analyzing CQ usage patterns, competency questions can be classified into five main types, each serving a distinct purpose in ontology development:[^13][^14][^12]

### 1. Scoping Competency Questions (SCQ)

**Purpose**: Define the boundaries and coverage of the ontology domain.

**Characteristics**:

- Establish what concepts, entities, and relationships fall within the ontology's purview
- Identify the "horizontal" scope (domain boundaries) and "vertical" scope (level of detail)[^15]
- Help prevent scope creep during development

**Example Questions**:

- "What is the domain that the ontology will cover?"[^3]
- "What are the key components and infrastructure elements relevant to this domain?"[^16]
- "Which regulatory frameworks and standards apply to this domain?"
- "What are the boundaries beyond which this ontology does not apply?"
- "Which stakeholders will use this ontology and for what purposes?"

**Cross-Domain Applications**:

- **Cybersecurity**: "What types of threats, vulnerabilities, and controls should be represented?"
- **Healthcare**: "Should this ontology cover only clinical workflows or also administrative and billing processes?"
- **Smart Cities**: "What domains and sectors (energy, transportation, governance) are addressed within the smart city context?"[^16]


### 2. Validating Competency Questions (VCQ)

**Purpose**: Evaluate whether the ontology conceptualization correctly represents domain knowledge and can answer expected queries.

**Characteristics**:

- Test whether the ontology contains the necessary concepts, properties, and relations
- Verify that relationships are correctly modeled
- Can be translated into SPARQL queries or description logic queries for automated testing[^17][^9]

**Example Questions**:

- "Which AI techniques are vulnerable to which types of adversarial attacks?"
- "What controls mitigate which specific risks for a given compliance requirement?"
- "What are the components of X and how are they related?"
- "Which entities have property Y with value Z?"
- "What is the relationship between entity X and entity Y under condition Z?"

**Implementation**:
Validating CQs are typically formalized into queries that can be executed against the ontology. Research has documented 234 CQs with their corresponding SPARQL-OWL query translations, demonstrating that one CQ pattern may map to multiple query patterns and vice versa.[^18][^19][^17]

### 3. Foundational Competency Questions (FCQ)

**Purpose**: Align domain entities to appropriate categories in a foundational (or top-level) ontology.

**Characteristics**:

- Ensure consistency with upper-level ontological commitments
- Help classify domain entities as processes, objects, qualities, roles, etc.
- Support interoperability across domain ontologies that share the same foundational ontology

**Example Questions**:

- "Is this entity a continuant (enduring through time) or an occurrent (happening in time)?"[^20]
- "Is this entity materially constituted or information-bearing?"
- "Does this entity depend on other entities for its existence?"
- "Can this entity be copied among different bearers?"[^20]
- "Is this entity a role, a function, or an intrinsic property?"

**Foundational Ontology Alignment**:
Major foundational ontologies like **BFO (Basic Formal Ontology)**, **DOLCE (Descriptive Ontology for Linguistic and Cognitive Engineering)**, and **GFO (General Formal Ontology)** provide different top-level structures. Decision trees and tools have been developed to help ontology engineers answer foundational CQs systematically, ensuring proper alignment and enabling cross-ontology consistency checking.[^21][^22][^20]

### 4. Metaproperty Competency Questions

**Purpose**: Examine ontological characteristics of entities such as rigidity, identity criteria, and unity.

**Characteristics**:

- Test whether classifications follow sound ontological principles
- Identify whether entities are rigid (essential across all instances) or anti-rigid (contingent)
- Clarify identity conditions and part-whole relationships

**Example Questions**:

- "Can something be part of itself?"[^23]
- "Are two entities the same if they have the same parts?"[^23]
- "Does every instance of X necessarily have property Y throughout its existence?"
- "What are the identity criteria for entities of type X?"
- "What is the difference between parts, components, and members?"[^23]

**Ontological Depth**:
These questions often reveal deep conceptual issues. For example, in an ontology containing "Braai" (South African barbecue), metaproperty CQs might ask: "Is 'heating method' an intrinsic property of a braai or a role that different objects can play?" Such questions push developers beyond surface modeling to consider fundamental ontological commitments.[^10]

### 5. Relation Characteristic Competency Questions

**Purpose**: Test properties of relations such as reflexivity, symmetry, transitivity, and functionality.

**Characteristics**:

- Ensure relations have appropriate logical characteristics
- Support automated reasoning and consistency checking
- Clarify domain and range constraints

**Example Questions**:

- "Is relation R reflexive (does every entity stand in relation R to itself)?"[^12]
- "If X is related to Y by R, is Y necessarily related to X by R (symmetry)?"
- "If X is related to Y and Y to Z by R, is X related to Z by R (transitivity)?"
- "Can an entity have more than one R relation to other entities (functionality)?"
- "What are the domain and range restrictions for relation R?"

**Example Application**:
For a "loves" relation: "Does a narcissist love himself?" requires reflexivity support. For a "part-of" relation: "If A is part of B and B is part of C, is A part of C?" tests transitivity. For an "eats" relation: "Can braai equipment eat?" tests domain restrictions.[^12][^10]

## The Competency Question Development Process

### Phase 1: Preparation and Scoping

#### 1.1 Identify Purpose and Context

Before formulating any CQs, establish the foundational parameters:[^3]

**Domain Identification**:

- What subject area does the ontology cover?
- What are the core phenomena, entities, and processes?
- What existing standards, regulations, or frameworks are relevant?

**Purpose Articulation**:

- Why are we building this ontology?
- What problems will it solve?
- What applications will it support?

**Usage Context**:

- Who will use the ontology?
- How will they use it (querying, reasoning, integration, visualization)?
- What technical infrastructure will it operate within?

**Example**: For an AI cybersecurity ontology:

- Domain: AI systems, adversarial attacks, defensive mechanisms, standards (MITRE ATLAS, FedRAMP)
- Purpose: Enable systematic mapping between AI risks, attacks, controls, and compliance requirements
- Usage: Risk assessment, control selection, audit support, threat intelligence integration
- Users: Security architects, compliance officers, AI developers, auditors


#### 1.2 Conduct Stakeholder Analysis

Effective CQ development requires input from diverse stakeholders:[^24]

**Stakeholder Categories**:

- **Domain Experts**: Provide deep knowledge of concepts, relationships, and constraints
- **End Users**: Describe practical scenarios and information needs
- **Subject Matter Experts**: Validate terminology and conceptual accuracy
- **Technical Specialists**: Identify implementation constraints and interoperability requirements
- **Decision Makers**: Define strategic priorities and success criteria

**Power-Interest Analysis**:[^25]
Create a matrix categorizing stakeholders by their influence (power) and stake (interest):

- High Power, High Interest: Close collaboration, detailed engagement
- High Power, Low Interest: Keep satisfied with regular summaries
- Low Power, High Interest: Keep informed through updates
- Low Power, Low Interest: Periodic monitoring

**Engagement Strategies**:[^24]

- Individual interviews for depth and complex requirements exploration
- Facilitated workshops for collaborative ideation and conflict resolution
- Observation sessions to capture implicit knowledge and tacit requirements
- Questionnaires for broad input from large stakeholder groups
- Prototyping sessions for experiential feedback on ontology design


#### 1.3 Gather Domain Knowledge

Systematic knowledge acquisition precedes effective CQ formulation:[^24]

**Domain Research**:

- Study existing documentation, standards, and regulations
- Review academic literature and technical specifications
- Analyze existing ontologies and knowledge bases in adjacent domains
- Understand domain terminology, abbreviations, and jargon
- Identify key domain challenges and recurring problems

**Contextual Understanding**:

- Organizational goals and strategic objectives
- Operational workflows and decision-making processes
- Competitive landscape and industry trends
- Regulatory environment and compliance requirements
- Technical architecture and system constraints

**Knowledge Sources**:

- Scientific papers and research publications
- Technical specifications and API documentation
- Industry standards and best practice guides
- Existing databases and information systems
- Expert interviews and ethnographic studies


### Phase 2: Scenario Development

#### 2.1 Create Motivating Scenarios

Following the Gruninger \& Fox methodology, develop concrete scenarios that illustrate how the ontology will be used:[^5][^6]

**Scenario Structure**:

- **Context**: Describe the situation and relevant actors
- **Problem**: State the information need or decision to be made
- **Current State**: Explain limitations with existing information systems
- **Desired State**: Articulate what the ontology should enable

**Example Scenario (AI Security)**:
*Context*: A cloud service provider is preparing for FedRAMP certification and must demonstrate comprehensive AI security controls.

*Problem*: The security team needs to identify which AI-specific attack vectors from MITRE ATLAS are relevant to their services and which controls address each vector while mapping to specific FedRAMP Key Security Indicators (KSIs).

*Current State*: Information is scattered across multiple documents with no systematic mapping between attack patterns, defensive controls, and compliance requirements.

*Desired State*: The ontology enables queries that automatically return relevant attack patterns for a given AI service, recommend appropriate controls, and show how each control satisfies specific FedRAMP KSIs, with evidence citations from research literature.

#### 2.2 Extract Information Needs from Scenarios

Transform scenarios into specific information needs that will become CQs:

**Question Derivation Process**:

1. Identify the key actors and their roles
2. List the decisions or actions they must take
3. Enumerate the information required for each decision
4. Formulate questions that would retrieve that information
5. Prioritize questions by criticality and frequency

**Example Derivation**:
From the scenario above:

- "What AI attack patterns apply to [specific AI service type]?"
- "Which defensive controls mitigate [specific attack pattern]?"
- "How does [control X] map to FedRAMP KSI [Y]?"
- "What research evidence supports the effectiveness of [control X] against [attack Y]?"
- "Which cloud environments support implementation of [control X]?"


### Phase 3: Competency Question Formulation

#### 3.1 Apply Question Design Principles

**Clarity and Specificity**:

- Use precise terminology consistent with domain language
- Avoid ambiguous terms unless explicitly defining polysemy
- Specify scope constraints (temporal, spatial, contextual)
- Make assumptions explicit

**Poor Example**: "What are the best AI controls?"

- "Best" is subjective and context-dependent
- No specification of threat model or environment
- Lacks measurable criteria

**Improved Example**: "Which AI defensive controls have peer-reviewed evidence of >90% effectiveness against adversarial evasion attacks in production cloud environments as of 2025?"

- Specifies evidence type (peer-reviewed)
- Defines threshold (>90%)
- Clarifies attack type (adversarial evasion)
- Constrains environment (production cloud)
- Sets temporal boundary (as of 2025)

**Answerability**:
Ensure the CQ can be answered using the ontology's content:

- Can the question be decomposed into concepts, properties, and relations?
- Does answering require information beyond the ontology scope?
- Is the expected answer type compatible with the ontology structure?

**Complexity Balance**:
Mix simple and complex questions:[^6]

- **Simple queries**: Test basic concept retrieval and property access
- **Complex queries**: Require reasoning across multiple relationships and axioms
- **Hierarchical queries**: Answers to complex questions depend on simpler sub-questions

Gruninger and Fox emphasized that an ontology is not well-designed if all CQs are simple lookup queries. Complex questions demonstrate that the ontology supports genuine reasoning, not just data retrieval.[^6]

#### 3.2 Structure Questions by Type

Organize CQs according to the five-type framework:

**Type 1 - Scoping (Boundaries)**:

- "What is X?" (definitional)
- "Is X within the scope?" (inclusion/exclusion)
- "What level of detail for X?" (granularity)
- "How does X relate to adjacent domains?" (boundary interfaces)

**Type 2 - Validating (Correctness)**:

- "Which X has property Y?" (attribute queries)
- "What are the components of X?" (part-whole queries)
- "How is X related to Y?" (relationship queries)
- "Under what conditions does Z occur?" (situational queries)

**Type 3 - Foundational (Upper-level alignment)**:

- "Is X a process or an object?" (basic category)
- "Does X depend on Y for existence?" (dependency)
- "Is X an instance or a class?" (classification level)

**Type 4 - Metaproperty (Ontological characteristics)**:

- "Is property P essential or contingent for X?" (rigidity)
- "What are the identity criteria for X?" (individuation)
- "Can X exist independently?" (dependence)

**Type 5 - Relation Characteristics (Logical properties)**:

- "Is relation R transitive?" (property testing)
- "What is the domain of relation R?" (constraint specification)
- "Can one entity have multiple R relations?" (cardinality)


#### 3.3 Formulate Questions at Multiple Granularities

Address different levels of abstraction:[^26]

**High-Level Questions** (strategic, scoping):

- "What are the major categories of AI threats?"
- "Which international standards govern AI security?"

**Mid-Level Questions** (tactical, operational):

- "What are the subtypes of model inversion attacks?"
- "Which controls are required for moderate-impact FedRAMP systems?"

**Low-Level Questions** (detailed, instance-level):

- "What is the Common Vulnerabilities and Exposures (CVE) identifier for vulnerability X?"
- "What is the implementation code for control Y in cloud platform Z?"

The appropriate granularity depends on intended applications. If the ontology will support automated reasoning for control selection, mid- and low-level CQs are critical. If it primarily guides human decision-making, high- and mid-level questions may suffice.[^26]

#### 3.4 Include Negative and Constraint Questions

While less common in traditional CQ methodologies, negative questions clarify boundaries and constraints:

**Exclusion Questions**:

- "Which entities should NOT be classified as X?"
- "What relationships are explicitly forbidden between X and Y?"
- "Under what conditions should process P NOT be initiated?"

**Constraint Questions**:

- "What are the maximum cardinality limits for relation R?"
- "Which combinations of properties are logically inconsistent?"
- "What temporal constraints apply to process P?"

**Example Application**:
In a healthcare ontology: "Can a medication be prescribed after its expiration date?" clarifies a constraint. "Can a diagnostic device also be classified as a therapeutic device?" tests for potentially problematic overlaps or necessary disjointness.

### Phase 4: Validation and Refinement

#### 4.1 Stakeholder Review

**Review Process**:[^24]

- Present CQs to domain experts for accuracy and completeness
- Validate terminology with end users for understandability
- Confirm technical feasibility with ontology engineers
- Check alignment with strategic goals with decision makers

**Review Workshops**:
Facilitate structured sessions where stakeholders:

- Rate each CQ on relevance (1-5 scale)
- Identify ambiguities or unclear terminology
- Suggest additional CQs based on missing scenarios
- Prioritize CQs by importance and frequency of use

**Delphi Method**:[^27]
For complex domains, use iterative expert consensus:

1. Round 1: Experts independently review CQs
2. Aggregation: Collect and anonymize feedback
3. Round 2: Share aggregate results, experts revise assessments
4. Iteration: Repeat until convergence on priority CQs

#### 4.2 Quality Assessment

Evaluate each CQ against quality criteria:

**Syntactic Quality**:

- Grammatically correct?
- Terminology consistent?
- Free from spelling errors?
- Proper noun capitalization?

**Semantic Quality**:

- Unambiguous meaning?
- Avoids synonyms without clarification?
- Concepts well-defined?
- Implicit assumptions made explicit?

Research analyzing 53 problematic CQs found common issues:[^12]

- **17 had grammar problems** (easily fixable)
- **9 were inappropriate** ("Can I...", "How to..." questions that no ontology can answer)
- **Remainder had ambiguity, vagueness, or required capabilities beyond ontology languages**

**Answerability Assessment**:

- Can concepts in the question be mapped to ontology entities?
- Does answering require reasoning capabilities available in the target ontology language?
- Are cardinality or temporal constraints expressible in the formalism?

Example problematic CQ: "How many legs does a human have?"[^12]

- Requires qualified cardinality constraints
- Only answerable if ontology language supports count restrictions
- May be better as an axiom than a CQ in some contexts


#### 4.3 Iterative Refinement

**Refinement Strategies**:[^2]

**Top-Down Refinement**:

- Start with high-level, abstract CQs
- Decompose into more specific sub-questions
- Specialize until reaching desired granularity
- Ensures comprehensive coverage from general to specific

**Bottom-Up Refinement**:

- Begin with detailed, concrete CQs from specific scenarios
- Generalize by identifying common patterns
- Abstract to broader questions
- Ensures grounding in real use cases

**Middle-Out Refinement** (Most Common):[^28][^2]

- Start with moderately abstract CQs
- Simultaneously generalize and specialize
- Balance theoretical coherence with practical applicability
- Iteratively adjust scope in both directions

Survey data shows 63.5% of ontology developers use iterative approaches, refining CQs across multiple development cycles. This recognizes that CQ understanding evolves as the ontology matures.[^2]

**Refinement Triggers**:

- Ontology implementation reveals ambiguities in CQs
- New stakeholder needs emerge
- Integration with other ontologies requires scope adjustment
- Evaluation shows CQs are unanswerable or trivial
- Domain knowledge evolves (new research, standards updates)


#### 4.4 Prioritization

Not all CQs are equally critical. Establish priority tiers:

**High Priority (Must Have)**:

- Core to the ontology's primary purpose
- Required for critical use cases
- Frequently asked by primary user groups
- Mandated by external requirements (regulations, standards)

**Medium Priority (Should Have)**:

- Support important but non-critical scenarios
- Enhance usability for secondary user groups
- Provide valuable but not essential information

**Low Priority (Nice to Have)**:

- Address edge cases
- Support potential future applications
- Offer convenience but have workarounds

**Prioritization Criteria**:

- Frequency of use (how often will this question be asked?)
- Impact (how critical is the answer to decision-making?)
- Complexity (how difficult to answer without the ontology?)
- Dependencies (is this CQ prerequisite for others?)


### Phase 5: Formalization and Implementation

#### 5.1 Translate CQs to Formal Queries

**SPARQL Translation**:[^19][^9][^17]

Natural Language CQ:
"Which AI models can generate trace-based explanations?"

SPARQL Query:

```sparql
PREFIX ai: <http://example.org/ai#>
PREFIX exp: <http://example.org/explanation#>

SELECT ?model
WHERE {
  ?model rdf:type ai:AIModel .
  ?model exp:canGenerate ?explanation .
  ?explanation rdf:type exp:TraceBasedExplanation .
}
```

Research has documented 234 CQs with 131 corresponding SPARQL-OWL queries, revealing that:[^17][^18]

- One CQ pattern can map to multiple query patterns
- One query pattern can satisfy multiple CQ patterns
- 106 distinct CQ patterns have been identified across diverse ontologies[^19]

**Description Logic Formalization**:[^9]

CQ: "What level of proficiency is required for skill S in career path C?"

DL Query:

```
CareerPath(?c) ∧ RequiresSkill(?c, ?s) ∧ hasProficiencyLevel(?s, ?level)
```


#### 5.2 TBox vs. ABox Questions

Distinguish between questions targeting different ontology components:[^29][^17]

**TBox (Terminological) Questions**:
Focus on schema, class definitions, and conceptual structure:

- "What are the subtypes of attack X?"
- "Is control Y a subclass of control Z?"
- "What properties can entities of type X have?"

**ABox (Assertional) Questions**:
Focus on individuals, instances, and specific data:

- "Which specific systems deployed in production have vulnerability V?"
- "What is the CVE-ID for this particular vulnerability instance?"
- "Which organizations have implemented control C?"

Dataset analyses show that CQs focusing on concepts help identify ontology structure, while instance-focused CQs are valuable for data-driven applications.[^2]

#### 5.3 Develop Test Infrastructure

**Unit Testing Framework**:[^9]

- Each CQ becomes a test case
- Expected answers are specified in advance
- Automated tests execute queries and compare results
- Pass/fail criteria determine ontology completeness

**CQChecker Tool**:[^9]
Automates CQ testing by:

1. Analyzing CQ structure
2. Classifying into question types
3. Generating appropriate SPARQL queries
4. Executing queries against the ontology
5. Validating results against expected answers

**Continuous Validation**:
Integrate CQ testing into ontology development workflow:

- Run tests after each modification
- Track which CQs pass/fail over time
- Identify regressions (previously answerable CQs become unanswerable)
- Monitor coverage (percentage of CQs satisfactorily answered)


#### 5.4 Document CQs Systematically

**Essential Documentation**:[^30]

- **CQ Identifier**: Unique reference (e.g., CQ-001)
- **Natural Language Formulation**: Precise question text
- **Category**: Type (Scoping, Validating, etc.)
- **Priority**: Tier (High/Medium/Low)
- **Scenario**: Motivating use case
- **Expected Answer Type**: Entity, boolean, count, etc.
- **Formal Query**: SPARQL or DL translation
- **Expected Result**: Sample correct answers
- **Status**: Draft, Validated, Implemented, Deprecated
- **Dependencies**: Related CQs or prerequisites
- **Rationale**: Why this CQ is important
- **Version History**: Changes over time

**Documentation Formats**:

- CSV files for lightweight tracking[^9]
- Ontology-based representation for semantic querying
- Markdown or LaTeX for human-readable specifications
- Integration with version control (Git) for change tracking


## Advanced Topics in Competency Question Development

### Automated CQ Generation Using AI

Recent advances in Large Language Models (LLMs) have enabled semi-automated CQ generation:[^31][^32][^33]

**RAG-Based Approach**:[^32]

1. Provide LLM with scientific papers as domain knowledge base
2. Use retrieval-augmented generation to ground CQs in authoritative sources
3. Generate questions targeting specific ontology requirements
4. Filter and validate generated CQs

**Knowledge Graph Integration**:[^31]

- Extract entities and relationships from domain documents
- Transform into structured graph representations
- Use entity-specific and community-focused retrieval
- Generate CQs using GPT-4o, Mistral, or similar models
- Apply Chain-of-Thought reasoning for complex questions
- Use Reflexion technique for iterative self-improvement

**Evaluation Metrics**:[^31]

- Cosine similarity scores (quantitative)
- LLM-as-a-Judge method (qualitative)
- Domain expert validation (human-in-the-loop)

**Limitations**:[^33][^31]

- 50% acceptance rate even with best-performing systems[^33]
- Variability across models and domains
- Requires expert oversight for quality assurance
- Context-specific performance dependencies

**Current State**: Automated generation is promising for bootstrapping CQ development but insufficient as sole approach. Hybrid workflows combining automated generation with expert curation are most effective.

### Cross-Domain CQ Patterns

While CQs must be domain-specific, recurring patterns emerge across fields:

**Structural Patterns**:[^19]

- "What are the components/parts of X?"
- "What is X a member/component of?"
- "How is X related to Y?"
- "What entities have property P with value V?"

**Temporal Patterns**:

- "For what timeframe is X valid?"
- "What is the temporal sequence of events E?"
- "When did state S transition to state S'?"

**Causal Patterns**:

- "What causes X to occur?"
- "What are the effects of action A?"
- "What is the mechanism by which X produces Y?"

**Classification Patterns**:

- "What type/category is X?"
- "What are the subtypes of Y?"
- "Is X a specialization of Y?"

**Eligibility/Constraint Patterns**:

- "Which types of X are eligible for Y?"
- "Under what conditions can Z occur?"
- "What constraints apply to process P?"

**Domain Adaptations**:

**Healthcare**:[^34][^35]

- "What clinical workflows are affected by intervention X?"
- "Which regulatory requirements (HIPAA, FDA) apply to device D?"
- "How does system S ensure patient data privacy?"
- "What interoperability standards (HL7, FHIR) are supported?"

**Smart Cities**:[^16]

- "How are infrastructure elements I interdependent?"
- "What are the cybersecurity risks for service S?"
- "How is data managed, secured, and shared across domains?"
- "What are the environmental impacts of technology T?"

**Finance**:

- "What regulatory frameworks govern transaction T?"
- "How is risk R calculated for portfolio P?"
- "What are the audit trails for compliance requirement C?"


### Workshop Facilitation for CQ Development

Collaborative CQ development workshops yield richer results than individual elicitation:[^36]

**Workshop Structure**:

**Pre-Workshop (1-2 weeks before)**:

- Distribute background materials (domain overview, example CQs)
- Share preliminary CQ draft for review
- Assign pre-work (scenario brainstorming, term glossaries)
- Confirm participant attendance and roles

**Opening (30 minutes)**:

- Welcome and agenda overview
- Explain CQ purpose and how they'll be used
- Review ontology scope and goals
- Icebreaker activity if participants unfamiliar with each other

**Divergent Phase (60-90 minutes)**:

- Individual brainstorming: Participants independently write CQs
- Small group sharing: Groups of 3-4 discuss and refine
- Post-up activity: All CQs displayed on walls/virtual whiteboard
- Silent review: Participants read all posted CQs

**Convergent Phase (60-90 minutes)**:

- Affinity diagramming: Group similar CQs into themes
- Prioritization: Dot voting or forced ranking on importance
- Refinement: Rewrite ambiguous or redundant CQs
- Gap analysis: Identify missing scenarios or question types

**Closing (30 minutes)**:

- Review prioritized CQ list
- Assign ownership for post-workshop refinement
- Clarify next steps and timeline
- Collect feedback on workshop process

**Facilitation Principles**:[^36]

- **Neutrality**: Facilitator doesn't contribute CQs, only guides process
- **Equal participation**: Use techniques to prevent domination by vocal participants
- **Psychological safety**: Encourage all ideas without premature critique
- **Diverge before converge**: Separate idea generation from evaluation
- **Document visually**: Make all contributions visible to the group

**Virtual Adaptations**:

- Use collaborative tools (Miro, Mural, Figma)
- Breakout rooms for small group work
- Anonymous submission options for quieter participants
- Asynchronous components (pre-workshop survey, post-workshop refinement)


### Ontology Reuse and CQ Mapping

**Reverse Engineering CQs**:[^37]
The **RevOnt** approach generates CQs from existing ontologies:

1. Analyze ontology axioms and annotations
2. Generate CQs that the ontology can answer
3. Compare CQ sets across ontologies to assess reuse potential
4. Identify coverage gaps between requirement CQs and ontology CQs

**Benefits**:

- Enable meaningful comparison of ontology scopes
- Support reuse decisions by matching CQs to capabilities
- Enhance testing by providing comprehensive question sets
- Facilitate ontology documentation

**Pattern Libraries**:[^38][^39]
Ontology Pattern Languages (OPLs) link patterns to CQs:

- Each pattern annotated with CQs it addresses
- CQ-driven pattern selection in development tools
- Dependency checking ensures completeness
- Reuse accelerates development while maintaining quality

**Example Workflow**:

1. Developer formulates CQs for new ontology
2. Tool searches OPL for patterns addressing those CQs
3. Patterns suggested based on CQ coverage
4. Developer selects and instantiates patterns
5. Tool checks dependencies and warns of gaps

### Completeness and Coverage Assessment

**Coverage Metrics**:

**CQ Coverage Rate**:
Percentage of high-priority CQs the ontology can answer:

- **>90%**: Excellent coverage
- **70-90%**: Good coverage, minor gaps
- **50-70%**: Adequate but needs improvement
- **<50%**: Insufficient, major revision required

**Concept Coverage**:
Percentage of domain concepts mentioned in CQs that appear in ontology:

- Calculate: (Concepts in Ontology ∩ Concepts in CQs) / (Concepts in CQs)

**Relationship Coverage**:
Percentage of relationships implied by CQs that are formalized:

- Calculate: (Relations in Ontology ∩ Relations implied by CQs) / (Relations implied by CQs)

**Completeness Theorems**:[^5][^6]
Following Gruninger \& Fox methodology:

1. Formalize CQs in first-order logic
2. Define solutions to CQs using ontology axioms
3. Specify completeness conditions: under what circumstances are solutions complete?
4. Prove theorems demonstrating completeness

**Example**:
CQ: "What are all the activities required to achieve goal G?"

Completeness Condition: A solution is complete if it includes all activities directly required by G, all activities transitively required by those activities (via enablement relations), and no activities not required by any in this chain.

Completeness Theorem: If the ontology includes exhaustive axiomatization of enablement relations and goal-activity associations, query Q will return complete answers.

### Evolution and Lifecycle Management

**Version Control**:

- Track CQs alongside ontology versions in Git or similar systems
- Use semantic versioning for major CQ set changes
- Maintain changelog documenting CQ additions, modifications, deletions

**Change Management**:

**Adding CQs**:

- Trigger: New use case, stakeholder request, domain evolution
- Process: Draft → Review → Formal translation → Testing → Documentation
- Impact: May require ontology extension

**Modifying CQs**:

- Trigger: Ambiguity discovered, terminology change, scope refinement
- Process: Version existing CQ → Create modified version → Validate with stakeholders → Update queries and tests
- Impact: May invalidate previous test results

**Deprecating CQs**:

- Trigger: Out of scope, superseded, no longer relevant
- Process: Mark as deprecated → Document reason → Retain for historical reference
- Impact: Remove from active test suites but preserve documentation

**Review Cycles**:

- **Quarterly**: Light review for minor updates
- **Semi-Annually**: Comprehensive review with stakeholder input
- **Major Releases**: Full CQ audit and realignment


## Common Pitfalls and How to Avoid Them

### Pitfall 1: Over-Reliance on CQs for Quality Assessment

**Problem**: Believing that if an ontology answers all CQs, it must be high quality.[^10]

**Reality**: CQs test functional requirements but not:

- Logical consistency and coherence
- Ontological rigor (disjointness, proper subsumption)
- Domain/range constraints on properties
- Adherence to design patterns and best practices
- Structural quality and maintainability

**Solution**: Combine CQ-based evaluation with:

- Automated pitfall detection (OOPS! scanner)[^10]
- Foundational ontology alignment checks
- Structural metrics (depth, breadth, tangledness)
- Expert ontological review
- Reasoner-based consistency checking


### Pitfall 2: Inappropriate Question Types

**Problem**: Formulating questions that no ontology can answer:[^12]

- "Can I render this if the supplier goes out of business?" (procedural, not ontological)
- "How to configure system X?" (instructional, not knowledge representation)
- "What should we prioritize?" (decision-making, requires preferences outside ontology scope)

**Solution**: Focus on knowledge representation questions:

- ✓ "What are the components of system X?"
- ✓ "What are the relationships between X and Y?"
- ✓ "Under what conditions does Z apply?"


### Pitfall 3: Ambiguity and Vagueness

**Problem**: CQs using ambiguous terms or lacking context:

- "What are the main types of data?" (main according to whom? types for what purpose?)
- "Where do I categorize bulk like this?" (what is "this"? what categorization scheme?)

**Solution**: Make context and criteria explicit:

- ✓ "According to ISO 27001, what are the data classification levels?"
- ✓ "In the pharmaceutical domain ontology, under which Material class should bulk chemical X be categorized?"


### Pitfall 4: Language-Expressivity Mismatch

**Problem**: CQs requiring reasoning capabilities the ontology language doesn't support:[^12]

- Reflexivity: "Does a narcissist love himself?" needs reflexive relation support
- Cardinality: "How many legs does a human have?" needs qualified cardinality
- Temporal: "What was true before event E?" needs temporal logic or reification

**Solution**:

- Assess target ontology language capabilities (OWL 2 DL, OWL Full, etc.)
- Reformulate CQs within expressivity constraints or
- Justify language choice based on CQ requirements
- Document CQs that require external reasoning


### Pitfall 5: All Simple Lookup Queries

**Problem**: Only formulating trivial questions that require no reasoning:[^6]

- "What is the definition of X?"
- "List all instances of class Y"

**Solution**: Include complex, hierarchical CQs requiring multi-step reasoning:

- ✓ "Given constraints C1-C3, which controls satisfy all requirements and have evidence effectiveness >80%?"
- ✓ "What is the minimal set of controls covering all attack vectors for system type S?"


### Pitfall 6: Neglecting Negative Cases and Boundaries

**Problem**: Only asking about what should be included, not what should be excluded.

**Solution**: Include boundary-testing CQs:

- "Under what conditions should X NOT be classified as Y?"
- "Which combinations of properties are invalid?"
- "What entities are explicitly outside the ontology scope?"


### Pitfall 7: Static CQ Sets

**Problem**: Treating CQs as fixed requirements rather than evolving artifacts.

**Solution**: Embrace iterative refinement:[^2]

- Review CQs at each development iteration
- Retire outdated CQs and add new ones as understanding deepens
- Document rationale for changes
- Maintain version history


### Pitfall 8: Insufficient Stakeholder Diversity

**Problem**: CQs reflect only one stakeholder perspective (e.g., only technical users, only domain experts).

**Solution**: Engage diverse stakeholders:[^24]

- Domain experts (conceptual accuracy)
- End users (practical utility)
- Technical implementers (feasibility)
- Decision makers (strategic alignment)
- Adjacent domain experts (interoperability)


## Practical Examples Across Domains

### Example 1: Healthcare Clinical Decision Support

**Scoping CQs**:

- "What clinical specialties are covered (cardiology, oncology, etc.)?"
- "Are diagnostic guidelines from which organizations included (AHA, ACS, WHO)?"
- "What level of detail: disease categories, specific conditions, or genetic variants?"

**Validating CQs**:

- "For patient with symptoms S1, S2, S3, what are the differential diagnoses?"
- "Which lab tests are indicated for suspected condition C?"
- "What are the contraindications for medication M given patient profile P?"
- "Which treatment guidelines apply to patient with comorbidities C1, C2?"

**Foundational CQs**:

- "Is a 'diagnosis' a process or a dependent entity?"
- "Is a 'symptom' a quality or a disposition?"
- "Are 'treatment protocols' plans or specifications?"

**Metaproperty CQs**:

- "Can a patient have multiple active diagnoses of the same condition?"
- "Is 'being diabetic' a rigid or anti-rigid property?"
- "What are the identity criteria for distinguishing two symptom occurrences?"

**Relation Characteristic CQs**:

- "Is the 'contraindicates' relation between medications symmetric?"
- "If medication M1 interacts with M2 and M2 interacts with M3, does M1 interact with M3?"
- "Can one symptom be caused by multiple conditions (functional vs. inverse-functional)?"


### Example 2: Supply Chain and Logistics

**Scoping CQs**:

- "Does the ontology cover raw materials, components, finished goods, or all?"
- "Are transportation modes (air, sea, ground, rail) all in scope?"
- "What geographic granularity: countries, regions, specific facilities?"

**Validating CQs**:

- "What is the lead time for component C from supplier S to facility F?"
- "Which suppliers provide material M with quality certification Q?"
- "What are the dependencies between production step P1 and P2?"
- "Which products are affected by disruption at supplier S?"

**Foundational CQs**:

- "Is a 'purchase order' a document or a social commitment?"
- "Is 'inventory' a material entity or a role played by materials?"
- "Is 'shipment' a process or an event?"

**Metaproperty CQs**:

- "Can a component be part of multiple assemblies simultaneously?"
- "What constitutes identity for tracking individual items vs. batches?"
- "Is 'being a supplier' an essential property or a contingent role?"

**Relation Characteristic CQs**:

- "Is the 'part-of' relation transitive across assemblies?"
- "If facility F1 supplies F2 and F2 supplies F3, does F1 transitively supply F3?"
- "What is the domain of 'shipment-contains' (only containerized goods?)?"


### Example 3: Legal and Regulatory Compliance

**Scoping CQs**:

- "Which jurisdictions' laws are covered (US federal, EU, specific states)?"
- "What legal domains: contract law, privacy law, intellectual property, or all?"
- "Temporal scope: current law only or historical versions?"

**Validating CQs**:

- "Which regulatory requirements from framework F apply to organization type T?"
- "What are the penalties for non-compliance with regulation R?"
- "Which controls satisfy requirement R1 in jurisdiction J?"
- "What evidence types E are acceptable for demonstrating compliance with C?"

**Foundational CQs**:

- "Is a 'regulation' a specification, a plan, or a generically dependent continuant?"
- "Is 'compliance' a state, a process, or a quality?"
- "Are 'legal obligations' social objects or dependent entities?"

**Metaproperty CQs**:

- "Can one control satisfy multiple regulatory requirements?"
- "What are the identity criteria for regulations across jurisdictional boundaries?"
- "Is 'being compliant' a rigid property once achieved?"

**Relation Characteristic CQs**:

- "If regulation R1 supersedes R2, is this relationship transitive?"
- "Is the 'derives-from' relation between requirements and sub-requirements transitive?"
- "What is the range of 'enforced-by' (only government agencies?)?"


## Competency Questions and AI Systems: Emerging Frontiers

As AI systems become more sophisticated, CQs play evolving roles:

**AI-Generated CQs**:
LLMs can assist in CQ generation but require:

- Human validation for accuracy and relevance
- Domain expert oversight for coverage
- Integration with knowledge graphs for grounding
- Iterative refinement through Reflexion techniques[^31]

**CQs for AI Explainability**:
Ontologies supporting AI explainability need CQs like:

- "What input features most influenced decision D?"
- "What counterfactual changes would alter outcome O?"
- "Which training examples are most similar to instance I?"
- "What is the provenance chain for prediction P?"

**CQs for AI Safety and Ethics**:
Emerging AI governance ontologies require:

- "What biases have been detected in model M?"
- "Which fairness metrics apply to use case U?"
- "What safeguards exist against failure mode F?"
- "How is data privacy ensured for training set T?"

**CQs Driving Agentic AI**:
As AI agents use ontologies for reasoning:

- CQs become agent queries executed autonomously
- CQ complexity determines agent reasoning depth
- CQ coverage defines agent competence boundaries
- CQ validation ensures agent behavior alignment


## Practical Tools and Resources

**Ontology Development Platforms**:

- **Protégé**: Industry-standard editor with plugin ecosystem
- **WebProtégé**: Collaborative web-based development
- **TopBraid Composer**: Enterprise-grade with governance features

**CQ Management Tools**:

- **CQChecker**: Automated CQ validation and testing[^9]
- **BFO Classifier**: Foundational ontology alignment assistance[^20]
- **OOPS!**: Ontology pitfall detection[^10]

**CQ Repositories**:

- **ROCQS** (Repository of Competency Questions): 438 CQs across domains[^12]
- **CQ-BEN**: Benchmark corpus for CQ evaluation[^4]
- **Mendeley CQ Dataset**: 234 CQs with SPARQL translations[^18][^17]

**Query Tools**:

- **Blazegraph Workbench**: SPARQL query execution and visualization
- **SPARQL endpoints**: Direct query interfaces to ontologies
- **Semantic reasoners**: HermiT, Pellet, FaCT++ for inference

**Documentation Frameworks**:

- **Markdown**: Lightweight, version-control friendly
- **OntoDoc**: Automated ontology documentation generation
- **Widoco**: Wizard for documenting ontologies


## Conclusion: The Strategic Role of Competency Questions

Competency Questions are far more than a requirements gathering technique—they are the conceptual bridge between human understanding and formal ontological commitment. By making explicit what knowledge the ontology must represent and what reasoning it must support, CQs transform abstract ontological development into a concrete, testable engineering discipline.

**Key Takeaways**:

1. **CQs are iterative, not static**: Expect 63.5% of development efforts to refine CQs across multiple cycles. This dynamism reflects deepening domain understanding.[^2]
2. **Five CQ types serve distinct purposes**: Scoping, Validating, Foundational, Metaproperty, and Relation Characteristic questions address different aspects of ontology quality.[^13][^12]
3. **Stakeholder diversity enriches CQs**: Engage domain experts, end users, technical specialists, and decision makers to capture comprehensive requirements.[^24]
4. **Formalization enables automation**: Translating CQs to SPARQL or Description Logic enables continuous testing and regression detection.[^17][^9]
5. **CQs alone are insufficient**: Combine CQ-based evaluation with structural analysis, pitfall detection, and foundational ontology alignment for comprehensive quality assurance.[^10]
6. **AI augments but doesn't replace human expertise**: LLM-generated CQs achieve ~50% acceptance rates, requiring expert curation.[^33]
7. **Cross-domain patterns exist but require adaptation**: Structural, temporal, causal, and classification patterns recur across domains but need context-specific instantiation.[^19]
8. **Documentation and version control are critical**: Systematic CQ documentation with rationale, dependencies, and version history ensures long-term maintainability.[^30]
9. **Negative and constraint questions clarify boundaries**: Explicitly stating what the ontology should NOT represent prevents scope creep and modeling errors.
10. **CQ complexity matters**: Well-designed ontologies answer hierarchical, multi-step CQs that require genuine reasoning, not just data retrieval.[^6]

By applying the principles, methodologies, and best practices outlined in this guide, ontology developers can harness Competency Questions to create knowledge representations that are scope-appropriate, stakeholder-aligned, technically sound, and genuinely useful for their intended applications—whether in cybersecurity, healthcare, supply chain, legal compliance, or any other domain requiring structured, machine-processable knowledge.
<span style="display:none">[^100][^101][^102][^40][^41][^42][^43][^44][^45][^46][^47][^48][^49][^50][^51][^52][^53][^54][^55][^56][^57][^58][^59][^60][^61][^62][^63][^64][^65][^66][^67][^68][^69][^70][^71][^72][^73][^74][^75][^76][^77][^78][^79][^80][^81][^82][^83][^84][^85][^86][^87][^88][^89][^90][^91][^92][^93][^94][^95][^96][^97][^98][^99]</span>

<div align="center">⁂</div>

[^1]: https://person.dibris.unige.it/mascardi-viviana/Download/questionnaire101.pdf

[^2]: https://nemo.inf.ufes.br/wp-content/papercite-data/pdf/use_of_competency_questions_in_ontology_engineering__a_survey_2023.pdf

[^3]: https://protege.stanford.edu/publications/ontology_development/ontology101.pdf

[^4]: https://ceur-ws.org/Vol-3953/369.pdf

[^5]: https://oa.upm.es/5480/1/Overview_Of_Methodologies.pdf

[^6]: http://www.eil.utoronto.ca/wp-content/uploads/enterprise-modelling/papers/gruninger-mmei96.pdf

[^7]: https://ceur-ws.org/Vol-1041/ontobras-2013_paper45.pdf

[^8]: http://ketrc.com/wp-content/uploads/2020/04/Evaluation-Competency-Questions-2020-4-30.pdf

[^9]: https://ceur-ws.org/Vol-1908/paper16.pdf

[^10]: https://keet.wordpress.com/2022/06/08/only-answering-competency-questions-is-not-enough-to-evaluate-your-ontology/

[^11]: https://www.academia.edu/70546830/The_Role_of_Competency_Questions_in_Enterprise_Engineering

[^12]: https://keet.wordpress.com/2024/11/07/different-roles-for-various-competency-questions-for-ontologies/

[^13]: https://arxiv.org/abs/2412.13688

[^14]: https://arxiv.org/html/2412.13688v1

[^15]: https://cacm.acm.org/research/a-lightweight-methodology-for-rapid-ontology-engineering/

[^16]: https://smartcitysecurity.net/2023/06/13/competence-questions-for-a-smart-city-domain-ontology/

[^17]: https://data.mendeley.com/datasets/pp6hmfxgfg/1

[^18]: https://pubmed.ncbi.nlm.nih.gov/31989008/

[^19]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3490821

[^20]: https://ceur-ws.org/Vol-3249/paper3-FOUST.pdf

[^21]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10712036/

[^22]: https://keet.wordpress.com/tag/ontology-alignment/

[^23]: http://ontolog.cim3.net/file/work/OntologySummit2012/2012-02-23_Ontology-Quality-in-Big-Systems/Ontology-Quality_Design-patterns_Competency--NicolaGuarino_20120223.pdf

[^24]: https://plprojects.co.uk/eliciting-requirements-from-stakeholders/

[^25]: https://www.izenbridge.com/kb/pmp-exam-content-outline/process-task4-engage-stakeholders/

[^26]: https://protege.stanford.edu/publications/ontology_development/ontology101-noy-mcguinness.html

[^27]: https://www.cambridgeassessment.org.uk/Images/research-matters-35-a-conceptual-approach-to-validating-competence-frameworks.pdf

[^28]: https://www.mecs-press.org/ijieeb/ijieeb-v12-n2/IJIEEB-V12-N2-5.pdf

[^29]: https://www.imrpress.com/journal/KO/52/8/10.31083/KO42705

[^30]: https://www.finalroundai.com/blog/documentation-interview-questions

[^31]: https://ceur-ws.org/Vol-3874/paper10.pdf

[^32]: https://arxiv.org/abs/2409.08820

[^33]: https://aclanthology.org/2025.ldk-1.15.pdf

[^34]: https://testrigor.com/blog/healthcare-domain-software-testing-interview-questions/

[^35]: https://www.invensislearning.com/blog/healthcare-project-manager-interview-questions-answers/

[^36]: https://www.nngroup.com/articles/workshop-facilitation-101/

[^37]: https://www.sciencedirect.com/science/article/pii/S1570826824000088

[^38]: https://ceur-ws.org/Vol-3905/master2.pdf

[^39]: https://www.inf.ufes.br/~monalessa/wp-content/papercite-data/pdf/using_competency_questions_to_enhance_patterns_selection_in_ontology_patterns_languages_2024.pdf

[^40]: Guide_Engineering_Basic_SchemaDesign.md

[^41]: prompt_context.txt

[^42]: 2008.07863v1_metadata.json

[^43]: 2504.00441_metadata.txt

[^44]: README.md

[^45]: https://tetherless-world.github.io/sciv-ontology/competencyquestions/

[^46]: https://cgi.csc.liv.ac.uk/~tbc/publications/itknows.pdf

[^47]: https://ceur-ws.org/Vol-3249/paper2-Ensusto.pdf

[^48]: https://inass.org/2019/2019043017.pdf

[^49]: https://iacis.org/iis/2025/4_iis_2025_476-496.pdf

[^50]: https://fairplus.github.io/the-fair-cookbook/content/recipes/interoperability/ontology-robot-recipe/competency-questions.html

[^51]: https://www.designsociety.org/download-publication/25547/a_methodology_of_engineering_ontology_development_for_information_retrieval

[^52]: https://www.sciencedirect.com/science/article/abs/pii/S1570826819300617

[^53]: https://eng.libretexts.org/Bookshelves/Computer_Science/Programming_and_Computation_Fundamentals/An_Introduction_to_Ontology_Engineering_(Keet)/06:_Methods_and_Methodologies/6.01:_Methodologies_for_Ontology_Development

[^54]: https://livrepository.liverpool.ac.uk/3190379/1/201315064_Feb2025.pdf

[^55]: https://www.semanticscholar.org/paper/The-Role-of-Competency-Questions-in-Enterprise-Gruninger-Fox/e84846b45565ffc2108246fe20713529e6f63ba7

[^56]: https://arxiv.org/html/2409.08820v1

[^57]: http://www.eil.utoronto.ca/wp-content/uploads/enterprise-modelling/papers/fox-eimt97.pdf

[^58]: https://tetherless-world.github.io/explanation-ontology/competencyquestions/

[^59]: https://jatit.org/volumes/Vol103No19/2Vol103No19.pdf

[^60]: https://arxiv.org/abs/2507.02989

[^61]: https://www.sciencedirect.com/science/article/pii/S2352340919314544

[^62]: https://vidcruiter.com/interview/questions/competency-based/

[^63]: https://www.prospects.ac.uk/careers-advice/interview-tips/competency-based-interviews

[^64]: https://livrepository.liverpool.ac.uk/3184940/1/EKAW2024-2.pdf

[^65]: https://info.lse.ac.uk/staff/divisions/Human-Resources/Assets/Documents/Recruitment-Toolkit/Interview-and-Assessment/4.2-A-Guide-to-Competency-Based-Interviews.pdf

[^66]: https://2014.eswc-conferences.org/sites/default/files/papers/paper_145.pdf

[^67]: https://www.thecorporatelawacademy.com/forum/threads/a-complete-guide-for-competency-interview-preparation.9380/

[^68]: https://www.sciencedirect.com/science/article/pii/S1071581914001013

[^69]: https://www.stlawu.edu/offices/human-resources/competency-values-based-interview-questions

[^70]: https://ceur-ws.org/Vol-3603/workshopOIIDDS1.pdf

[^71]: https://uxknowledgebase.com/domain-expert-interview-90c8db4cbaa

[^72]: https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2024.1397027/full

[^73]: https://www.roberthalf.com/au/en/insights/hiring-help/stakeholder-management-interview-questions-ask-and-how-ideal-candidate-would-answer

[^74]: https://www.finalroundai.com/blog/stakeholder-management-interview-questions

[^75]: https://www.unipamplona.edu.co/unipamplona/portalIG/home_23/recursos/general/06032011/onto_parte2.pdf

[^76]: https://timespro.com/blog/most-asked-stakeholder-management-interview-questions-and-tips-to-answer-them

[^77]: https://www.bridging-the-gap.com/what-questions-do-i-ask-during-requirements-elicitation/

[^78]: https://www.linkedin.com/pulse/six-effective-elicitation-questions-ask-your-angela

[^79]: https://yardstick.team/interview-questions/requirements-elicitation

[^80]: https://www.diva-portal.org/smash/get/diva2:747226/FULLTEXT01.pdf

[^81]: https://gitlab.esrf.fr/dau/ontology/esrf-ontology/-/wikis/Competency-questions/diff?version_id=9e1eef3091302c20ad1a19fd2150ff4dc42508ca\&w=0

[^82]: https://www.reddit.com/r/salesforce/comments/1dnctxu/what_are_your_go_to_questions_when_doing/

[^83]: http://ontologydesignpatterns.org/wiki/images/1/11/WOP2016_paper_01.pdf

[^84]: https://www.cmx1.com/blog/questions-product-lifecycle-management

[^85]: https://www.intelligentpeople.co.uk/employer-advice/product-management-interview-questions/

[^86]: https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=822618

[^87]: https://www.interviewbit.com/sdlc-interview-questions/

[^88]: https://binary.pensoft.net/file/259027

[^89]: https://yardstick.team/interview-questions/customer-lifecycle-management

[^90]: https://www.micro1.ai/interview-prep/customer-lifecycle-manager-interview-questions

[^91]: https://www.reddit.com/r/UXDesign/comments/1lc5ias/how_do_you_learn_to_facilitate_workshops_and/

[^92]: https://voltagecontrol.com/articles/top-interview-questions-to-assess-meeting-facilitation-skills-what-you-should-know/

[^93]: https://www.upgrad.com/blog/healthcare-interview-questions-for-freshers/

[^94]: https://www.youtube.com/watch?v=RCa8WDx9QEw

[^95]: https://arxiv.org/abs/2505.24554

[^96]: https://insightglobal.com/blog/20-interview-questions-for-healthcare-it-candidates/

[^97]: https://www.workshopper.com/post/the-ultimate-guide-to-facilitation

[^98]: https://research.ibm.com/publications/automated-generation-of-competency-questions-using-large-language-models-and-knowledge-graphs

[^99]: https://www.scribd.com/document/563569680/BA-Healthcare-Domain-Interview-questions

[^100]: https://knowledge.insead.edu/leadership-organisations/competencies-and-constraints-determine-leadership-success

[^101]: https://www.finalroundai.com/blog/competency-based-interview-questions

[^102]: https://huntr.co/interview-questions/documentation

