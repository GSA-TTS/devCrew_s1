# Using Competency Questions to Drive Ontology Classes, Properties, and Constraints

Once competency questions (CQs) are formulated, they serve as the primary blueprint for ontology design—directly driving what classes, properties, axioms, and constraints must be implemented. This guide presents a systematic methodology for extracting ontological requirements from CQs through linguistic analysis, presupposition identification, pattern matching, and formal translation into OWL constructs. The process transforms natural language questions into testable, executable ontology specifications through a disciplined, iterative approach that ensures the resulting ontology precisely addresses stakeholder needs.[^1][^2][^3]

## Foundational Principles: From Questions to Ontological Commitments

### The Presupposition Paradigm

Every competency question carries **linguistic presuppositions**—implicit assumptions about domain structure that must be satisfied for the question to be meaningful. These presuppositions directly translate to ontology requirements:[^2]

**Example Analysis**:[^1]

**Competency Question**: "What is the average performance of students over the semester?"

**Presuppositions Extracted**:

1. **"Student Performance" must exist** → Requires Class `StudentPerformance` or Data Property `hasPerformance`
2. **Performance must be measurable** → Requires Data Property with numeric range (xsd:float, xsd:integer)
3. **Temporal dimension "over semester"** → Requires temporal property or qualified relation
4. **Aggregation capability "average"** → Implies multiple performance instances, cardinality considerations
5. **Students exist as distinct entities** → Requires Class `Student`

Each presupposition becomes a **non-negotiable ontology requirement**. If any is missing, the CQ cannot be answered meaningfully, indicating ontology incompleteness.

### The Three-Layer Translation Framework

**Layer 1: Syntactic Analysis**
Parse natural language structure to identify grammatical components (nouns, verbs, adjectives, modifiers)

**Layer 2: Semantic Mapping**
Map linguistic components to ontological primitives (classes, properties, individuals, restrictions)

**Layer 3: Logical Formalization**
Express requirements as OWL axioms, Description Logic constraints, or SPARQL queries

This layered approach ensures systematic coverage from surface language to formal logic, minimizing gaps between stakeholder intent and implemented ontology.

## Phase 1: Linguistic Analysis and Component Extraction

### Noun Phrase Extraction → Classes and Instances

#### Parse Tree Analysis

Modern ontology engineering leverages **constituency parsing** to extract noun phrases systematically:[^4]

**Process**:

1. Parse CQ sentence into constituent tree structure
2. Identify Noun Phrase (NP) nodes in tree
3. Extract head noun (core concept) and modifiers (attributes, qualifiers)
4. Handle nested noun phrases recursively

**Example**:[^4]
Phrase: "finishes which may radiate noise"

- Parse identifies nested NP: "finishes" (head) modified by relative clause
- Head noun → Candidate Class: `Finish`
- Modifier "radiate noise" → Candidate property or constraint

**POS Tagging Patterns**:[^4]

Pattern: `DT? JJ* NN+` (optional determiner, zero+ adjectives, one+ nouns)

Examples:

- "a stringent requirement" (DT JJ NN) → Class: `Requirement` with attribute `stringent`
- "braai equipment" (NN NN) → Class: `BraaiEquipment` (compound noun)
- "AI security control" (NN NN NN) → Class: `AISecurityControl`

**Multi-Word Concepts**:[^4]
Domain terminology often appears as multi-word expressions requiring special handling:

- "natural language processing" → Single class `NaturalLanguageProcessing`, not three classes
- "cloud service provider" → Single class `CloudServiceProvider`
- Use domain glossaries and expert validation to identify atomic vs. composite terms


#### Classification Rules

**Common Nouns → OWL Classes**:[^5]

- "students", "courses", "assessments" → Classes `Student`, `Course`, `Assessment`
- Represent categories/types that have multiple instances

**Proper Nouns → Individuals**:[^5]

- "FedRAMP", "MITRE ATLAS", "GPT-4" → Individuals (specific entities)
- Named entities that are unique instances of classes

**Abstract Concepts → Classes**:

- "performance", "risk", "compliance" → Classes at appropriate abstraction level
- Often require careful positioning in hierarchy

**Determining Class vs. Individual**:

- Can there be multiple instances with different properties? → Class
- Is this a unique, specific entity that won't have instances? → Individual
- Does the domain expect to reason about this category? → Class


### Verb Phrase Extraction → Properties and Relations

#### Dependency Parsing for Relationships

**Main Clause Patterns** (nominal subject):[^6]
Pattern: Subject (noun) + Verb + Object (noun)

Examples:

- "processes implement algorithms" → `implements` property (domain: `Process`, range: `Algorithm`)
- "students enroll in courses" → `enrolledIn` property (domain: `Student`, range: `Course`)
- "controls mitigate risks" → `mitigates` property (domain: `Control`, range: `Risk`)

**Passive Clause Patterns**:[^6]
Pattern: Subject + "is/are" + past participle + "by" + Agent

Examples:

- "risks are mitigated by controls" → Same `mitigates` property, inverse perspective
- "algorithms are implemented by processes" → Indicates need for inverse property

**Relative Clause Patterns**:[^6]
Pattern: Noun + relative pronoun + verb phrase

Examples:

- "systems which support AI workloads" → `supports` property
- "attacks that exploit vulnerabilities" → `exploits` property


#### Property Type Determination

**Object Properties** (Class → Class):[^7][^8]

- **Trigger**: Verb connecting two entity types
- **Range**: Another class (not a literal value)
- **Example**: "book has author" → `hasAuthor` (domain: `Book`, range: `Author`)

**Datatype Properties** (Class → Literal):[^8][^7]

- **Trigger**: Attribute assignment, measurement, or simple value
- **Range**: XML Schema datatype (xsd:string, xsd:integer, xsd:date, etc.)
- **Example**: "publication year" → `publicationYear` (domain: `Book`, range: `xsd:integer`)

**Decision Criteria**:

- Does the object have its own properties and can exist independently? → Object Property
- Is it a simple value (number, text, date)? → Datatype Property
- Can it be measured or counted directly? → Typically Datatype Property


#### Verb Pattern Categories

**Transitive Verbs**:[^6]
Map directly to properties with clear domain/range:

- "authors write books" → `writes` property
- "lecturers teach courses" → `teaches` property

**Copula ("is/are") Patterns**:[^6]
Indicate classification or equivalence:

- "X is a type of Y" → `rdfs:subClassOf` (subsumption)
- "X is Y" → Either equivalence (`owl:equivalentClass`) or typing (`rdf:type`)

**Possessive Structures**:[^6]
Noun + possessive + Noun:

- "system's components" → `hasComponent` property
- "attack's target" → `hasTarget` property
- Often become "has-X" or "of-X" properties

**Comparative Structures**:[^6]
Adjective comparisons:

- "X is larger than Y" → `largerThan` property
- "X is more severe than Y" → `moreSevereThan` property
- May require ordering or ranking mechanisms


### Adjective and Modifier Extraction → Attributes and Restrictions

#### Attribute Identification

**Simple Adjectives → Datatype Properties or Class Specialization**:

- "stringent requirement" → Either Data Property `isStringent` (boolean) or subclass `StringentRequirement`
- "high risk" → Subclass `HighRisk` or Data Property `riskLevel` with range constraint

**Quantifying Adjectives → Cardinality Constraints**:

- "multiple controls" → No maximum cardinality restriction
- "single point of failure" → `cardinality 1` restriction
- "at least three validators" → `minCardinality 3`

**Qualifying Modifiers → Property Restrictions**:

- "AI-specific controls" → Restriction: `Control AND (appliesTo some AISystem)`
- "certified assessor" → Restriction: `Assessor AND (hasCertification some Certification)`


#### Boolean and Enumerated Values

**Boolean Attributes**:
CQ: "Which systems are certified?"

- Property: `isCertified` with range `xsd:boolean`
- Alternative: Create disjoint classes `CertifiedSystem` and `UncertifiedSystem`

**Enumerated Values**:
CQ: "What is the impact level (Low, Moderate, High)?"

- Define Class `ImpactLevel` with individuals: `Low`, `Moderate`, `High`
- Property: `hasImpactLevel` with range `ImpactLevel`
- Add axiom: `ImpactLevel owl:oneOf (Low Moderate High)`


## Phase 2: Building the Class Hierarchy

### Identifying Subsumption Relationships

#### Pattern Recognition for Hierarchies

**"Type of" / "Kind of" Patterns**:[^6]

CQ: "What types of AI attacks exist?"

- Indicates hierarchy: `Attack` as superclass
- Subtypes: `AdversarialAttack`, `DataPoisoningAttack`, `ModelInversionAttack`
- Axioms: `AdversarialAttack rdfs:subClassOf Attack`

**"Such as" / "Including" Patterns**:[^4]

CQ: "Which security frameworks, such as FedRAMP and NIST, apply?"

- `FedRAMP` and `NIST` are examples (instances or subclasses) of `SecurityFramework`
- Lexico-syntactic pattern: "NPList1 such as NPList2" → NPList2 instances/subclasses of NPList1

**Taxonomic Questions**:

CQ: "Is X a specialized form of Y?"

- Direct subsumption: `X rdfs:subClassOf Y`

CQ: "What are the components of X?"

- Part-whole hierarchy, not subsumption
- Use properties like `hasPart` / `isPartOf` instead


#### Hierarchy Design Principles

**Single vs. Multiple Inheritance**:

- **Single inheritance**: Each class has one direct superclass (simpler, clearer)
- **Multiple inheritance**: Class can have multiple superclasses (more expressive, risk of complexity)
- OWL supports multiple inheritance; use judiciously when entity genuinely belongs to multiple categories

**Depth vs. Breadth**:

- **Deep hierarchies**: Many levels (e.g., 5-7 levels) provide fine-grained classification
- **Shallow hierarchies**: Few levels (2-3) are easier to understand but may be too coarse
- Balance based on domain complexity and CQ granularity requirements

**Top-Down vs. Bottom-Up Construction**:

- **Top-down**: Define high-level classes first (e.g., `Entity`, `Process`, `Resource`), then specialize
- **Bottom-up**: Identify specific classes from CQs, then generalize to find common parents
- **Middle-out** (recommended): Start at mid-level abstractions, extend in both directions


### Disjointness and Coverage

#### Disjointness Axioms

**Not Automatically Derived from CQs**:[^9]
CQs typically specify what *should* be related, not what *should not* overlap. Disjointness must be inferred from domain knowledge and validated with experts.

**Critical for Quality**:[^9]

Example: In a braai (barbecue) ontology:

- `Site` (location) and `BraaiEquipment` (physical object) should be disjoint
- Without disjointness axiom, reasoner could infer that a location is equipment
- Pitfall: Unintended models that violate domain semantics

**Adding Disjointness**:

```owl
DisjointClasses: Site, BraaiEquipment, FoodItem, Person
```

**Tool Support**:

- **Advocatus Diaboli / PEW (Possible World Explorer)**: Identifies where disjointness axioms should be added[^9]
- **OOPS! Pitfall Scanner**: Detects missing disjointness as ontology pitfall[^9]


#### Coverage Axioms

**Covering Axioms** (Closed World Assumption):

CQ: "What are *all* the impact levels?"

- Axiom: `ImpactLevel equivalentClass {Low, Moderate, High}`
- Ensures no other impact levels exist

**Partitions**:

CQ: "Are systems either development, staging, or production?"

- Disjoint union: `System = DevelopmentSystem ⊔ StagingSystem ⊔ ProductionSystem`
- Each system instance belongs to exactly one category


## Phase 3: Defining Properties and Their Characteristics

### Domain and Range Specification

#### Extracting Domain and Range from CQs

**General Pattern**: "Which [Domain] [Property] [Range]?"

Examples:

CQ: "Which **students** are **enrolled in** **courses**?"

- Domain: `Student`
- Property: `enrolledIn`
- Range: `Course`

CQ: "Which **controls** **mitigate** **risks**?"

- Domain: `Control`
- Property: `mitigates`
- Range: `Risk`

**Formal OWL Specification**:[^10][^7]

```owl
ObjectProperty: enrolledIn
  Domain: Student
  Range: Course

ObjectProperty: mitigates
  Domain: Control
  Range: Risk
```

**OWL 2 DL Constraint**: Exactly one `rdfs:domain` and one `rdfs:range` per property (although multiple can be specified via intersection).[^10]

#### Multiple Domain/Range Values

**Intersection Semantics**:

```owl
Domain: Student ⊓ Employee
```

Means: Property applies to entities that are *both* Student *and* Employee

**Union Semantics** (via separate properties or reasoning):

Use multiple properties:

- `teacherEnrolledIn` (domain: `Teacher`, range: `Course`)
- `studentEnrolledIn` (domain: `Student`, range: `Course`)

Or create superclass:

- `Person ⊔ {Student, Teacher}`
- `enrolledIn` domain: `Person`


### Property Characteristics from CQs

#### Transitivity

**CQ Pattern**: "If X [relation] Y and Y [relation] Z, is X [relation] Z?"

Examples:[^11]

CQ: "If component A is part of assembly B, and assembly B is part of system C, is A part of C?"

- Answer: Yes → `partOf` is **transitive**
- OWL: `owl:TransitiveProperty`

CQ: "If activity A precedes activity B, and B precedes C, does A precede C?"

- Answer: Yes → `precedes` is **transitive**

**Implementation**:[^11]

```owl
ObjectProperty: hasSubStage
  Characteristics: Transitive
  
ObjectProperty: hasNextStage
  Characteristics: Transitive
```

**Reasoning Benefit**: Reasoner infers transitive closure automatically—if A part of B and B part of C, infers A part of C without explicit assertion.

#### Symmetry

**CQ Pattern**: "If X [relation] Y, does Y [relation] X?"

Examples:

CQ: "If person A is sibling of person B, is B sibling of A?"

- Answer: Yes → `siblingOf` is **symmetric**

CQ: "If system X integrates with system Y, does Y integrate with X?"

- Answer: Yes → `integratesWith` is **symmetric**

**Implementation**:

```owl
ObjectProperty: siblingOf
  Characteristics: Symmetric
```


#### Reflexivity

**CQ Pattern**: "Can X [relation] itself?"

Examples:[^12]

CQ: "Does a narcissist love himself?"

- Answer: Yes → `loves` can be **reflexive**
- Requires reflexivity support in ontology language

CQ: "Can a system depend on itself?"

- Answer: Depends on domain; often No → `dependsOn` is **irreflexive**

**Implementation**:

```owl
ObjectProperty: loves
  Characteristics: Reflexive

ObjectProperty: dependsOn
  Characteristics: Irreflexive
```


#### Functionality and Inverse Functionality

**Functional Property**: Each domain individual has at most one range value

**CQ Pattern**: "Can X have multiple Y values?"

Examples:

CQ: "Can a person have multiple birth dates?"

- Answer: No → `hasBirthDate` is **functional**

CQ: "Can a system have multiple owners?"

- Answer: Yes → `hasOwner` is **not functional**

**Implementation**:[^8]

```owl
DataProperty: hasBirthDate
  Characteristics: Functional
  Domain: Person
  Range: xsd:date
```

**Inverse Functional**: Each range individual is related to at most one domain individual

CQ: "Can multiple people share the same social security number?"

- Answer: No → `hasSSN` is **inverse functional**


#### Inverse Properties

**CQ Pattern**: Bidirectional relationships with different perspectives[^11]

Examples:

CQ: "If activity A is a substage of B, is B a superstage of A?"

- Properties: `hasSubStage` ↔ `hasSuperStage`

CQ: "If component C is part of system S, does S contain C?"

- Properties: `partOf` ↔ `hasPart`

**Implementation**:[^11]

```owl
ObjectProperty: hasSubStage
  InverseOf: hasSuperStage

ObjectProperty: hasNextStage
  InverseOf: hasPreviousStage
```

**Reasoning Benefit**: Asserting one direction automatically infers the inverse.

## Phase 4: Extracting Constraints and Restrictions

### Cardinality Constraints from CQs

#### Quantifier Analysis

**Minimum Cardinality**:

CQ: "Must every class have **at least one** assessment?"

- Restriction: `Class ⊑ ≥1 hasAssessment.Assessment`
- OWL: `minCardinality 1 on hasAssessment`

**Maximum Cardinality**:

CQ: "Can a student have **no more than two** active enrollments?"

- Restriction: `Student ⊑ ≤2 enrolledIn.Course`
- OWL: `maxCardinality 2 on enrolledIn`

**Exact Cardinality**:

CQ: "Does every vehicle have **exactly four** wheels?"

- Restriction: `Vehicle ⊑ =4 hasWheel.Wheel`
- OWL: `cardinality 4 on hasWheel`

**Qualified Cardinality** (specific class):

CQ: "Must every security assessment include **at least one** certified assessor?"

- Restriction: `SecurityAssessment ⊑ ≥1 includes.CertifiedAssessor`
- OWL: `minQualifiedCardinality 1 hasAssessor someValuesFrom CertifiedAssessor`


#### Implicit Cardinality from Semantics

**Implicit "at least one"**:

CQ: "What controls does system X implement?"

- Presupposes systems *have* controls → `minCardinality 1 implementsControl`

**Implicit "exactly one"** (from uniqueness):

CQ: "What is the risk level of vulnerability V?"

- Presupposes single risk level → `cardinality 1 hasRiskLevel`

**Open Cardinality** (default):

CQ: "Which vulnerabilities affect system S?"

- No constraint → Zero or more vulnerabilities allowed


### Value Restrictions

#### Existential Quantification (∃ / someValuesFrom)

**CQ Pattern**: "Which X have *at least one* Y?"

Examples:[^13]

CQ: "Which AI systems can generate trace-based explanations?"

- Restriction: `AISystem AND (canGenerate some TraceBasedExplanation)`

CQ: "Which courses have prerequisites?"

- Restriction: `Course AND (hasPrerequisite some Course)`

**OWL Implementation**:[^7]

```owl
Class: AISystemWithExplanations
  EquivalentTo: AISystem AND (canGenerate some TraceBasedExplanation)
```


#### Universal Quantification (∀ / allValuesFrom)

**CQ Pattern**: "Which X have *only* Y values?"

Examples:[^13]

CQ: "Which students are enrolled only in graduate courses?"

- Restriction: `Student AND (enrolledIn only GraduateCourse)`

CQ: "Which controls mitigate only high-severity risks?"

- Restriction: `Control AND (mitigates only HighSeverityRisk)`

**OWL Implementation**:[^7]

```owl
Class: GraduateStudent
  EquivalentTo: Student AND (enrolledIn only GraduateCourse)
```

**Critical Distinction**:

- `someValuesFrom`: At least one relation to specified class (existential)
- `allValuesFrom`: All relations (if any) must be to specified class (universal)
- `someValuesFrom` more common in practice; `allValuesFrom` often misunderstood


#### Specific Value Restrictions (hasValue)

**CQ Pattern**: "Which X have property P with specific value V?"

Examples:[^13]

CQ: "Which courses are taught by Professor Smith?"

- Restriction: `Course AND (taughtBy hasValue ProfessorSmith)`

CQ: "Which vulnerabilities have CVSS score 9.0?"

- Restriction: `Vulnerability AND (hasCVSSScore hasValue "9.0"^^xsd:float)`

**OWL Implementation**:[^7]

```owl
Class: SmithCourses
  EquivalentTo: Course AND (taughtBy hasValue ProfessorSmith)
```


### Complex Restrictions from Boolean CQs

#### Intersection (AND / ⊓)

**CQ Pattern**: "Which X have *both* property P and property Q?"

Examples:[^13]

CQ: "Which controls address both confidentiality and integrity?"

- Restriction: `Control AND (addresses some Confidentiality) AND (addresses some Integrity)`

**OWL**:

```owl
Class: ComprehensiveControl
  EquivalentTo: Control AND (addresses some Confidentiality) AND (addresses some Integrity)
```


#### Union (OR / ⊔)

**CQ Pattern**: "Which X have *either* property P or property Q?"

Examples:[^13]

CQ: "Which systems are either cloud-based or hybrid?"

- Union: `CloudBasedSystem ⊔ HybridSystem`

**OWL**:[^7]

```owl
Class: FlexibleDeployment
  EquivalentTo: CloudBasedSystem OR HybridSystem
```


#### Complement (NOT)

**CQ Pattern**: "Which X do *not* have property P?"

Examples:

CQ: "Which vulnerabilities are not yet patched?"

- Restriction: `Vulnerability AND (NOT (hasStatus hasValue "Patched"))`

**OWL**:[^7]

```owl
Class: UnpatchedVulnerability
  EquivalentTo: Vulnerability AND (NOT PatchedVulnerability)
```


### Temporal and Contextual Constraints

#### Temporal Properties from CQs

**CQ Temporal Indicators**:[^1]

CQ: "What is the average performance of students **over the semester**?"

- Requires: `hasSemester` property or temporal indexing

CQ: "Which controls were effective **during** the assessment period?"

- Requires: `validFrom`, `validTo` properties or temporal qualification

**Implementation Approaches**:

**Direct Temporal Properties**:

```owl
DataProperty: validFrom
  Domain: Control
  Range: xsd:dateTime

DataProperty: validTo
  Domain: Control
  Range: xsd:dateTime
```

**Qualified Relations** (4D Ontology Approach):

```owl
Class: ControlEffectivenessEvent
  SubClassOf: Event
  
ObjectProperty: controlInvolved
  Domain: ControlEffectivenessEvent
  Range: Control

ObjectProperty: occursDuring
  Domain: ControlEffectivenessEvent
  Range: TemporalInterval
```


#### Contextual Constraints

**CQ Pattern**: "Under what *conditions* does X apply?"

Examples:

CQ: "Which controls apply to moderate-impact systems?"

- Restriction: `Control AND (appliesTo some ModerateImpactSystem)`

CQ: "What are mitigation requirements *given* FedRAMP authorization?"

- Context class: `FedRAMPAuthorizedSystem`
- Restriction: `FedRAMPAuthorizedSystem ⊑ ≥3 implements.Control`


## Phase 5: Formal Translation to OWL and SPARQL

### From CQ to Description Logic Query

#### DL Query Construction[^14][^13]

**CQ**: "What level of proficiency is required for skill S in career path C?"

**DL Query**:

```
CareerPath(?c) ∧ RequiresSkill(?c, ?s) ∧ hasProficiencyLevel(?s, ?level)
```

**Process**:

1. Identify variables: `?c` (career path), `?s` (skill), `?level` (proficiency level)
2. Map nouns to classes: `CareerPath`, `Skill` (implicit from property domain/range)
3. Map verbs to properties: `RequiresSkill`, `hasProficiencyLevel`
4. Construct logical conjunction

### From CQ to SPARQL Query

#### Systematic SPARQL Generation[^15][^16][^17]

**Step-by-Step Translation**:

**CQ**: "Which AI models can generate trace-based explanations?"

**Analysis**:

1. Target (SELECT): "AI models" → Variable `?model`
2. Class constraint: "AI models" → `?model rdf:type ai:AIModel`
3. Property: "can generate" → `?model exp:canGenerate ?explanation`
4. Value constraint: "trace-based explanations" → `?explanation rdf:type exp:TraceBasedExplanation`

**SPARQL Query**:[^15]

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


#### Complex SPARQL Patterns

**Property Paths for Transitivity**:[^15]

CQ: "What are all substages of activity A, at any depth?"

```sparql
SELECT ?substage
WHERE {
  :ActivityA :hasSubStage+ ?substage .
}
```

- `+` operator: One or more steps along property
- `*` operator: Zero or more steps (reflexive-transitive closure)

**UNION for Alternatives**:

CQ: "Which systems are based on System Recommendation OR include Statistical Evidence?"

```sparql
SELECT ?explanation
WHERE {
  {
    ?explanation exp:isBasedOn exp:SystemRecommendation .
  }
  UNION
  {
    ?explanation exp:includes exp:StatisticalEvidence .
  }
}
```

**OPTIONAL for Non-Required Conditions**:

CQ: "What are the controls and, if known, their effectiveness ratings?"

```sparql
SELECT ?control ?rating
WHERE {
  ?control rdf:type sec:Control .
  OPTIONAL { ?control sec:hasEffectivenessRating ?rating . }
}
```

**Aggregation for Quantitative CQs**:

CQ: "What is the average performance of students in course C?"

```sparql
SELECT (AVG(?performance) AS ?avgPerformance)
WHERE {
  ?student rdf:type :Student .
  ?student :enrolledIn :CourseC .
  ?student :hasPerformance ?performance .
}
```


#### Automated SPARQL Generation Tools

**Chain-of-Thought Prompting**:[^17]

Recent LLM-based approaches use CoT reasoning:

1. Parse input question
2. Extract entities and relations
3. Map to ontology schema
4. Generate SPARQL step-by-step
5. Validate syntax and semantics

**Example Prompt Structure**:[^17]

```
Task: Generate SPARQL query for the question.
Ontology schema: [classes and properties]
Question: "Which AI models can generate explanations?"
Let's think step by step:
1. Identify target: AI models (variable ?model)
2. Identify class: AIModel
3. Identify property: canGenerate
4. Generate query: ...
```

**FrODO: Frame-Based Ontology Design**:[^18]

Automated tool that generates OWL ontologies directly from CQs:

- Uses frame semantics to parse CQs
- Extracts domain terminology
- Generates classes, properties, restrictions
- Produces Manchester syntax OWL output

**Example Output** from CQ "Who commissioned a component of a system?":[^18]

```owl
ObjectProperty: involvesComponent
  Annotations: rdfs:label "involves component"
  Range: Component
  InverseOf: isComponentInvolvedIn

ObjectProperty: involvesPerson
  Annotations: rdfs:label "involves person"
  Range: Person
  InverseOf: isPersonInvolvedIn

Class: Component
Class: Person
Class: System
```


## Phase 6: Ontology Pattern Selection from CQs

### CQ-Driven Pattern Reuse

#### Pattern Libraries and CQ Mapping[^19][^20]

**Process Flow**:

1. Ontology engineer formulates CQs for new domain ontology
2. Tool searches **Ontology Pattern Language (OPL)** for patterns addressing those CQs
3. Each pattern annotated with CQs it can answer
4. Patterns selected based on CQ coverage
5. Tool checks dependencies (Pattern A requires Pattern B)
6. Warn if dependencies unresolved
7. Instantiate and integrate selected patterns

**Benefits**:[^20]

- Accelerates development through proven solutions
- Ensures design best practices
- Maintains consistency
- Reduces conceptual errors


#### Pattern Dependency Resolution

**Example Scenario**:[^19]

CQs require patterns:

- CQ1: "What components does system X have?" → **Part-Whole Pattern**
- CQ2: "What roles do persons play?" → **Agent-Role Pattern**
- CQ3: "When was component C installed?" → **Time-Indexed Situation Pattern**

Dependencies:

- Time-Indexed Situation Pattern **depends on** Agent-Role Pattern (situations involve agents)
- Must include both patterns, even if only one CQ explicitly mentions roles

Tool warns: "CQ3 requires Agent-Role Pattern; please include or revise requirements."

#### Pattern Specialization

**Generic Pattern → Domain-Specific Instantiation**:

**Pattern**: Part-Whole (generic)

- Classes: `Whole`, `Part`
- Property: `hasPart`

**Domain Specialization** (for AI security ontology):

- `Whole` → `AISystem`
- `Part` → `AIComponent`
- `hasPart` → `hasAIComponent`

**Additional Domain Constraints**:

- Add subclasses: `ModelComponent`, `DataComponent`, `InterfaceComponent`
- Add cardinality: AI system must have at least one model component


## Phase 7: Test-Driven Development and Validation

### TDD Workflow for Ontology Engineering

#### The Red-Green-Refactor Cycle[^21][^22]

**Red Phase** (Test Fails):

1. Write CQ as test case with expected answer
2. Formalize as SPARQL query or DL query
3. Execute against current ontology
4. Test fails (CQ unanswerable or incorrect answer)

**Green Phase** (Make Test Pass):

1. Add/modify classes to address CQ requirements
2. Add/modify properties and axioms
3. Re-run test
4. Iterate until test passes

**Refactor Phase**:

1. Improve ontology structure without changing behavior
2. Optimize class hierarchies
3. Add disjointness and domain/range axioms
4. Ensure all tests still pass

#### Themis Tool Framework[^21]

**Three Automated Activities**:

**1. Test Design** (Manual):

- From each CQ, define expected behavior
- Specify test inputs (if instance data involved)
- Specify expected outputs

**2. Test Implementation** (Automated by Themis):

- Translate CQ to executable query (SPARQL or DL)
- Set up test harness
- Link to ontology under test

**3. Test Execution** (Automated by Themis):

- Execute queries via reasoner (Pellet, HermiT)
- Compare actual results to expected results
- Generate pass/fail report
- Maintain traceability: CQ → Test → Ontology Element

**Benefits**:[^21]

- Continuous validation during development
- Regression detection (previously passing CQ now fails)
- Requirements traceability
- Automated consistency checking


### Validation Dimensions

#### Consistency Checking[^1]

**Logical Consistency**:

- No contradictions in axioms
- All classes satisfiable (not equivalent to `owl:Nothing`)
- Property constraints compatible

**Reasoner Output**:

```
✓ Ontology is logically consistent
✓ All classes are satisfiable
✗ Class 'X' is unsatisfiable (check axioms)
```


#### CQ Answerability[^1]

**Metrics**:

- **Coverage Rate**: Percentage of CQs the ontology can answer
    - High Priority CQs: Target >90% coverage
    - All CQs: Target >70% coverage
- **Correctness**: Percentage of answered CQs with correct results (validated by domain experts)

**Evaluation Process**:[^1]

1. Execute all CQ queries
2. Classify results: Answered Correctly / Answered Incorrectly / Unanswerable
3. For unanswerable: Identify missing ontology element
4. For incorrect: Identify modeling error

#### Competency Question Mapping to Axioms[^1]

**Traceability Matrix**:


| CQ ID | CQ Text | Classes Required | Properties Required | Axioms Supporting | Status |
| :-- | :-- | :-- | :-- | :-- | :-- |
| CQ-001 | Which students enroll in courses? | Student, Course | enrolledIn | Domain/Range axioms | Pass |
| CQ-002 | What is average student performance? | Student, Performance | hasPerformance | Datatype property | Pass |
| CQ-003 | Which courses have prerequisites? | Course | hasPrerequisite | Transitive property | Fail |

**For each failing CQ**: Document what's missing and prioritize addition.

### Iterative Refinement

#### Refinement Triggers

**CQ Not Answerable → Add Elements**:

**Scenario**: CQ "Which MITRE ATLAS techniques are addressed by control C?" fails

**Diagnosis**: No `addresses` property connecting `Control` and `ATLASTechnique`

**Action**:

1. Add property: `addresses` (domain: `Control`, range: `ATLASTechnique`)
2. Add axiom: All controls must address at least one technique
3. Re-run test → Pass

**CQ Answer Incorrect → Fix Modeling**:

**Scenario**: CQ "Which vulnerabilities have high severity?" returns incorrect results

**Diagnosis**: `hasHighSeverity` is a boolean property, but severity should be enumerated

**Action**:

1. Replace `hasHighSeverity` with `hasSeverity` (range: `SeverityLevel`)
2. Define `SeverityLevel` with individuals: `Low`, `Moderate`, `High`, `Critical`
3. Update test query to filter on `hasSeverity value High`
4. Re-run test → Pass

**CQ Answer Too Broad → Add Constraints**:

**Scenario**: CQ "Which controls mitigate risk R?" returns controls that *can* mitigate but aren't actually implemented

**Diagnosis**: Missing distinction between potential and actual mitigation

**Action**:

1. Add property: `actuallyMitigates` (subproperty of `canMitigate`)
2. Update CQ query to use `actuallyMitigates`
3. Re-run test → Pass

## Phase 8: Integration with Data Sources

### Ontology-Data Alignment

#### Schema Mapping Process[^1]

**Step 1: Identify Data Sources**

Examples:

- Learning Management System (LMS) database
- Threat intelligence feeds
- Compliance audit reports
- Cloud service APIs

**Step 2: Map Concepts**


| Data Source | Field/Column | Ontology Class | Ontology Property |
| :-- | :-- | :-- | :-- |
| LMS DB | students table | Student | (instances) |
| LMS DB | courses table | Course | (instances) |
| LMS DB | enrollments.student_id | Student | subject of enrolledIn |
| LMS DB | enrollments.course_id | Course | object of enrolledIn |
| LMS DB | grades.score | Student | hasGrade (datatype) |

**Step 3: Data Transformation**

Convert source data format to ontology structure:

```sparql
# LMS grade "85.5" in field "score"
# Becomes:
:Student_001 :hasGrade "85.5"^^xsd:float .
```

**Step 4: Validation**

Check that integrated data satisfies ontology constraints:

- Cardinality constraints (e.g., student must have grade for enrolled courses)
- Domain/range constraints (e.g., grade values are numeric)
- Disjointness (e.g., instructor ≠ student for same course)


#### Provenance Tracking

**Annotate Ontology Elements**:[^1]

```owl
Class: Student
  Annotations:
    rdfs:comment "Derived from LMS students table"
    dc:source "LMS Database v2.3"
    prov:wasDerivedFrom <http://lms.example.org/schema/students>
```

**Benefits**:

- Trace ontology decisions to data sources
- Document rationale for modeling choices
- Support auditing and governance


## Phase 9: Advanced Techniques

### Handling Ambiguity and Polysemy

#### Resolving Multiple Meanings

**Problem**: Same term has different meanings in different contexts

Example: "Control" can mean:

- Security control (mitigation measure)
- Experiment control (baseline condition)
- Operational control (management authority)

**Solutions**:

**1. Distinct Classes**:

```owl
Class: SecurityControl
Class: ExperimentControl
Class: OperationalControl
```

**2. Qualified Names**:

```owl
Class: sec:Control
Class: exp:Control
Class: ops:Control
```

**3. Context Properties**:

```owl
Class: Control
  SubClassOf: hasContext some SecurityContext
```


### Temporal Modeling Strategies

#### Allen's Interval Algebra Patterns

For CQs involving temporal relationships:

**Before/After**:

```owl
ObjectProperty: occursBefore
  Domain: Event
  Range: Event
  Characteristics: Transitive, Irreflexive, Asymmetric
```

**During/Contains**:

```owl
ObjectProperty: occursDuringInterval
  Domain: Event
  Range: TemporalInterval
```

**Overlaps**:

```owl
ObjectProperty: overlapsWithEvent
  Domain: Event
  Range: Event
  Characteristics: Symmetric
```


### Modular Architecture

**Divide Ontology by CQ Clusters**:

**Module 1: Core Concepts** (foundational CQs)

- `Entity`, `Process`, `Resource`
- Universal properties

**Module 2: AI Security** (AI-specific CQs)

- `AISystem`, `AIThreat`, `AIControl`
- Domain properties

**Module 3: Compliance** (compliance-related CQs)

- `Requirement`, `Assessment`, `Evidence`
- Regulatory properties

**Module 4: Integration** (cross-domain CQs)

- Mappings between modules
- Bridge properties

**Benefits**:

- Manage complexity
- Enable independent development
- Support selective reuse
- Facilitate maintenance


## Practical Workflow Summary

### End-to-End Process

**Phase 1: CQ Collection**

- Gather CQs from stakeholders
- Categorize by domain area and priority
- Store in structured format (Excel, CSV, database)

**Phase 2: Linguistic Analysis**

- Parse CQs with NLP tools
- Extract noun phrases (→ classes)
- Extract verb phrases (→ properties)
- Identify modifiers (→ restrictions)

**Phase 3: Presupposition Extraction**

- For each CQ, list what must exist for question to be meaningful
- Convert presuppositions to requirements list

**Phase 4: Ontology Element Specification**

- Create class hierarchy from noun clusters
- Define properties with domain/range from verb patterns
- Add cardinality constraints from quantifiers
- Specify value restrictions from qualifiers

**Phase 5: Axiom Formalization**

- Write OWL axioms (Manchester or Functional syntax)
- Add disjointness, equivalence, subsumption axioms
- Document rationale with annotations

**Phase 6: Query Translation**

- Translate each CQ to SPARQL or DL query
- Validate query syntax
- Store alongside CQ for testing

**Phase 7: Implementation**

- Build ontology in Protégé or programmatically
- Run reasoner to check consistency
- Execute CQ queries

**Phase 8: Validation**

- Compare query results to expected answers
- Calculate coverage metrics
- Identify gaps (unanswerable CQs)

**Phase 9: Iteration**

- Add missing elements
- Fix incorrect modeling
- Re-run tests until target coverage achieved

**Phase 10: Deployment**

- Integrate with data sources
- Document ontology with CQ mappings
- Establish maintenance procedures


## Common Pitfalls and Solutions

### Pitfall 1: CQs Don't Capture Disjointness

**Problem**: CQs specify what should be related, not what should be disjoint[^9]

**Solution**:

- Use domain expert interviews to identify disjoint concepts
- Apply Advocatus Diaboli/PEW tool to find missing disjointness
- Add disjointness axioms proactively


### Pitfall 2: Over-Reliance on Automated Tools

**Problem**: Automated CQ-to-ontology tools (FrODO, LLM-based) produce drafts requiring significant refinement

**Solution**:

- Use automation for bootstrapping
- Always validate with domain experts
- Refine iteratively based on test results


### Pitfall 3: Ignoring Property Characteristics

**Problem**: Missing transitivity, symmetry declarations lead to incomplete reasoning

**Solution**:

- For each property, explicitly ask: "Is this transitive? Symmetric? Functional?"
- Document reasoning in annotations
- Test with example data to confirm behavior


### Pitfall 4: Insufficient Granularity

**Problem**: CQs too high-level, resulting in overly abstract ontology

**Solution**:

- Decompose high-level CQs into specific sub-questions
- Ensure CQs span abstraction levels (high, mid, low)
- Add instance-level CQs for concrete testing


### Pitfall 5: No Test Infrastructure

**Problem**: CQs gathered but never formalized into executable tests

**Solution**:

- Use TDDOnto or Themis tools for test automation
- Maintain CQ-to-query mappings in version control
- Run tests on every ontology change (CI/CD for ontologies)


## Conclusion: From Questions to Formal Knowledge

Competency questions are not merely requirements documentation—they are the **executable specifications** of an ontology. Through systematic linguistic analysis, semantic mapping, and formal translation, CQs drive every aspect of ontology design:

- **Classes** emerge from noun phrases denoting domain concepts
- **Properties** arise from verb patterns connecting entities
- **Hierarchies** form from taxonomic and partitive language structures
- **Constraints** materialize from quantifiers, qualifiers, and presuppositions
- **Axioms** encode domain rules implicit in question semantics

By treating CQs as both requirements and tests, ontology engineers ensure their models are **purpose-driven, stakeholder-aligned, and empirically validated**. The resulting ontologies are not abstract exercises in knowledge representation but practical artifacts that demonstrably serve their intended functions—answering the questions that matter to their users.

The methodology presented here—spanning linguistic analysis, pattern recognition, formal translation, test-driven development, and iterative refinement—provides a disciplined path from natural language queries to production-grade OWL ontologies capable of powering intelligent systems across domains from cybersecurity to healthcare, from supply chain to regulatory compliance.
<span style="display:none">[^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39][^40][^41][^42][^43][^44][^45][^46][^47][^48][^49][^50][^51][^52][^53][^54][^55][^56][^57][^58][^59][^60]</span>

<div align="center">⁂</div>

[^1]: https://jatit.org/volumes/Vol103No19/2Vol103No19.pdf

[^2]: https://2014.eswc-conferences.org/sites/default/files/papers/paper_145.pdf

[^3]: https://research.manchester.ac.uk/en/publications/towards-competency-question-driven-ontology-authoring/

[^4]: https://www.cs.ubc.ca/sites/default/files/tr/2012/TR-2012-04_0.pdf

[^5]: https://arxiv.org/pdf/1709.08448.pdf

[^6]: https://site.uottawa.ca/~azouaq/publications/Conferences, Workshops, Books/[C22]_WOP_2012.pdf

[^7]: https://www.w3.org/TR/owl-ref/

[^8]: https://www.youtube.com/watch?v=CXw-P7H2rOQ

[^9]: https://keet.wordpress.com/2022/06/08/only-answering-competency-questions-is-not-enough-to-evaluate-your-ontology/

[^10]: https://arxiv.org/html/2506.01232v1

[^11]: https://digitalconstruction.github.io/Lifecycle/v/0.5/

[^12]: https://keet.wordpress.com/2024/11/07/different-roles-for-various-competency-questions-for-ontologies/

[^13]: https://ceur-ws.org/Vol-1908/paper16.pdf

[^14]: https://ceur-ws.org/Vol-3249/paper2-Ensusto.pdf

[^15]: https://tetherless-world.github.io/explanation-ontology/competencyquestions/

[^16]: https://www.scitepress.org/Papers/2023/121800/121800.pdf

[^17]: https://papers.dice-research.org/2024/SEMANTICS_Cot-SPARQL/public.pdf

[^18]: https://ceur-ws.org/Vol-3235/paper13.pdf

[^19]: https://ceur-ws.org/Vol-3905/master2.pdf

[^20]: https://www.inf.ufes.br/~monalessa/wp-content/papercite-data/pdf/using_competency_questions_to_enhance_patterns_selection_in_ontology_patterns_languages_2024.pdf

[^21]: https://ksiresearch.org/seke/seke19paper/seke19paper_117.pdf

[^22]: http://www.jatit.org/volumes/Vol103No11/14Vol103No11.pdf

[^23]: Guide_Engineering_Basic_SchemaDesign.md

[^24]: prompt_context.txt

[^25]: 2008.07863v1_metadata.json

[^26]: 2504.00441_metadata.txt

[^27]: README.md

[^28]: https://stackoverflow.com/questions/52284921/mapping-class-and-properties-between-ontologies

[^29]: https://arxiv.org/html/2409.08820v1

[^30]: https://www.sciencedirect.com/science/article/abs/pii/S1570826819300617

[^31]: https://dl.acm.org/doi/fullHtml/10.1145/3184558.3186575

[^32]: https://arxiv.org/html/2412.13688v1

[^33]: https://protege.stanford.edu/publications/ontology_development/ontology101.pdf

[^34]: https://nemo.inf.ufes.br/wp-content/papercite-data/pdf/use_of_competency_questions_in_ontology_engineering__a_survey_2023.pdf

[^35]: https://kmi.open.ac.uk/events/sssw08/presentations/Gomez Perez-NeOn-Methodology-OntologySpecification-v3.pdf

[^36]: https://arxiv.org/abs/1811.09529

[^37]: https://dl.acm.org/doi/pdf/10.1145/3459637.3482387

[^38]: https://www.sciencedirect.com/science/article/pii/S1570826824000088

[^39]: https://docs.enslaved.org/competencyQuestions/

[^40]: https://ask.qcloudimg.com/draft/8495412/dij423n5ar.pdf

[^41]: https://etheses.bham.ac.uk/4620/1/Abdi13PhD.pdf

[^42]: https://homepages.inf.ed.ac.uk/wenfei/papers/pods15.pdf

[^43]: https://www.cs.uleth.ca/~benkoczi/files/main-full-oneside.pdf

[^44]: https://www.sciencedirect.com/science/article/pii/S2352340919314544

[^45]: https://dl.acm.org/doi/full/10.1145/3731443.3771350

[^46]: https://ieeexplore.ieee.org/iel8/6287639/10380310/10772211.pdf

[^47]: https://files.core.ac.uk/download/pdf/232196593.pdf

[^48]: https://faculty.cc.gatech.edu/~harrold/6340/cs6340_fall2009/Slides/class16.pdf

[^49]: http://www.ontologydesignpatterns.org/ont/training/foi/ODP.pdf

[^50]: https://www.diva-portal.org/smash/get/diva2:747226/FULLTEXT01.pdf

[^51]: https://www.artificialhumancompanions.com/robot-mind-robot-body-whatever-happened-subsumption-architecture/

[^52]: https://www.w3.org/2005/Incubator/decision/wiki/Decision_Incubator_Tools/ODP_Tour.html

[^53]: https://www.reddit.com/r/cpp_questions/comments/10tqx63/class_hierarchy_design_question/

[^54]: https://dl.acm.org/doi/10.1007/978-3-031-47262-6_3

[^55]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7581285/

[^56]: https://www.wisdomlib.org/concept/description-logic-query

[^57]: https://www.ontotext.com/blog/natural-language-querying-of-graphdb-in-langchain/

[^58]: https://arxiv.org/pdf/2410.06062.pdf

[^59]: https://github.com/frankj-rpi/fairness-metrics-ontology/blob/main/competency-questions.md

[^60]: https://wellcomeopenresearch.org/articles/10-122

