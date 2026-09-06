# Top-Down Ontology Development with Basic Formal Ontology (BFO)

The **top-down approach** begins with the most abstract, domain-neutral concepts and progressively specializes into domain-specific knowledge. When using **Basic Formal Ontology (BFO)**—an ISO-standardized top-level ontology—as the foundation, this methodology ensures maximum interoperability, formal rigor, and long-term semantic consistency. BFO provides a battle-tested upper-level framework adopted by over 550 ontology projects worldwide, offering three fundamental top-level categories: **Continuant** (entities enduring through time), **Occurrent** (processes happening in time), and refined distinctions like **dependent vs. independent continuants** and **realizable entities** (dispositions, roles, functions). For our AI cybersecurity evidence system integrating FedRAMP KSIs, MITRE ATLAS, and research literature, top-down development with BFO offers unparalleled interoperability with existing security ontologies and formal precision for compliance reasoning, though requiring 2-4 weeks initial learning investment and careful management of abstraction complexity.[^1][^2][^3][^4]

## Understanding Basic Formal Ontology (BFO)

### What is BFO?

**Basic Formal Ontology (BFO)** is a small, upper-level ontology designed as a common starting point for domain ontology development, ensuring consistency and interoperability across diverse knowledge domains.[^2][^5][^6]

**Key Characteristics**:

**Domain Neutrality**: BFO contains NO domain-specific terms—no biological, chemical, physical, social, or technical concepts. It provides only the most abstract categories applicable to ANY domain: entities, objects, processes, qualities, and their fundamental relationships.[^5][^1]

**Realist Philosophy**: Unlike conceptualist ontologies that represent mental models or linguistic structures, BFO adopts **realism**—representing entities that exist in space and time independent of human cognition. BFO classes must be instantiated by real-world particulars, not fictional or future entities.[^7]

**Small and Minimalistic**: BFO deliberately remains small (approximately 35 top-level classes) to maximize agreement across domains while providing sufficient structure for lower-level ontology development.[^6][^5]

**ISO International Standard**: ISO/IEC 21838-2:2021 specifies BFO as meeting rigorous requirements for top-level ontologies defined in ISO/IEC 21838-1. This standardization ensures stability, governance, and international recognition.[^1][^2][^7]

**Widespread Adoption**: As of 2025, BFO supports over 550 ontology projects:[^5][^1]

- **Biomedical**: Gene Ontology (GO), Ontology for Biomedical Investigations (OBI), Disease Ontology
- **Security \& Defense**: Intelligence ontologies, threat taxonomies
- **Industrial**: Industrial Ontologies Foundry (IOF) for manufacturing[^8][^1]
- **Scientific**: Chemistry, geospatial, environmental ontologies


### BFO's Role in Ontology Ecosystems

**Hub-and-Spokes Architecture**:[^8]

BFO serves as the **hub** at the center, with domain ontologies as **spokes** descending from it. This ensures:

1. **Shared foundation**: All ontologies speak the same upper-level language
2. **Automatic interoperability**: Aligning two ontologies to BFO automatically enables their integration
3. **Consistency**: Lower-level development constrained by inherited BFO axioms
4. **Reusability**: Mid-level ontologies (security, geospatial, temporal) extend BFO and serve multiple domains

**Example Ecosystem**:[^8]

```
              BFO (Hub)
                 |
    +------------+------------+
    |            |            |
Security     Industrial   Biomedical
Ontology     Ontology     Ontologies
    |            |            |
   our       Factory    Disease
  Project    Ontology    Ontology
```


## BFO's Top-Level Structure: The Fundamental Categories

### Entity: The Universal Root

**Everything is an Entity**. BFO's top-level class `Entity` encompasses all existence, divided into two fundamental, mutually exclusive categories based on their relationship to time.[^1]

### The Continuant-Occurrent Distinction

This is BFO's **most fundamental division**:[^3][^4][^1]


| Criterion | **Continuant** | **Occurrent** |
| :-- | :-- | :-- |
| **Temporal Nature** | Endures through time | Unfolds/happens in time |
| **Temporal Parts** | NO temporal parts | HAS temporal proper parts |
| **Presence** | Fully present at any instant | Extended across temporal interval |
| **Dimensions** | Three-dimensional (spatial) | Four-dimensional (spatiotemporal) |
| **Change** | CAN change (gain/lose qualities) | CANNOT change (different parts at different times) |
| **Examples** | Cat, color, temperature, function | Birth, war, metabolism, walking |

**Intuitive Understanding**:

- **Continuants** are things you can point to at a single moment: "That cat," "This redness," "our role as manager"
- **Occurrents** require a time span to exist: You cannot point to "a war" at a single instant; war unfolds over time with beginning, middle, and end


### Philosophical Grounding

**Continuant Persistence**:[^4][^3]
A cat today is the *same* cat tomorrow, maintaining identity despite changes (growing, aging). The entire cat exists at each moment—not just a "temporal slice."

**Occurrent Extension**:[^9][^3]
A process like "the Battle of Midway" has temporal parts: the reconnaissance phase, the attack phase, the aftermath. The entire battle doesn't exist at any single instant; only temporal parts exist at each moment.

**Critical Insight**: Processes don't "change" in BFO. If a car's motion "speeds up," it's not that the motion-process changed, but rather that temporal part₁ (at t₁) has speed v₁ and temporal part₂ (at t₂) has speed v₂. The process is the sum of these parts, each with fixed properties.[^9]

## Continuant Taxonomy: Entities That Endure

### Independent Continuant

**Definition**: Continuants that exist independently—neither generically nor specifically dependent on other entities.[^10][^3][^4]

#### Material Entity

**Entities with mass, occupying space**:[^11][^3]

**1. Object**[^12][^3][^10][^11]

**Definition**: Maximally self-connected material entity with complete **bona fide** boundary.[^12][^11]

**Bona Fide Boundary**: Natural boundary based on physical discontinuity or qualitative heterogeneity:[^12]

- Cell membrane (discontinuity in chemical composition)
- Object surface (boundary between object and surrounding air)
- Organism skin (physical barrier)

**Examples**:

- Biological: cell, organism, organ (heart, liver)
- Artificial: car, computer, building, server
- Atomic: molecule, atom, electron

**Key Property**: **Maximal self-connection**—every part connected to every other part through continuous material; boundary encloses entire object.[^12]

**2. Object Aggregate**[^3][^10][^11]

**Definition**: Collection or set of objects treated as a unit, but NOT materially connected.[^11]

**Examples**:

- Flock of birds
- Collection of three apples[^11]
- Server cluster (multiple machines)
- Defense force (collection of military units)

**Key Distinction from Object**: Parts NOT materially connected—gaps between members. An object aggregate is like a set; it has no parts other than its members.[^11]

**3. Fiat Object Part**[^10][^3][^12][^11]

**Definition**: Part of material entity demarcated by at least one **fiat boundary**—arbitrary boundary imposed by human decision, NOT natural discontinuity.[^12][^11]

**Fiat Boundary**: Artificial boundary where physical continuity exists:[^12]

- Boundary between our arm and torso (no natural discontinuity, tissue continuous)
- State borders through continuous terrain
- Left vs. right hemisphere of brain (arbitrary division plane)

**Examples**:

- our arm, my leg[^11]
- Northern France (part of France with fiat northern boundary)
- Engine block section (arbitrary subdivision of engine)

**Why Fiat Parts Matter**: Many scientifically and practically important entities are fiat parts (anatomical regions, geopolitical territories, functional zones). BFO accommodates them explicitly.[^12]

#### Immaterial Entity

**Entities without mass, zero to three-dimensional**:[^13][^10][^11]

**1. Site**[^11]

**Definition**: Three-dimensional immaterial entity that can be occupied by material entity.

**Examples**:

- Cavity in tooth (space within tooth)
- Parking space (designated three-dimensional region)
- Room (three-dimensional space bounded by walls)

**Key Property**: Can host material entities. A car occupies a parking space; a filling occupies a cavity.

**2. Continuant Fiat Boundary**[^13][^11][^12]

**Definition**: Immaterial entity of zero, one, or two dimensions, demarcated by fiat.[^13]

**Sub-types**:

- **Fiat Point** (0D): Occupies zero-dimensional spatial region (corner of room, GPS coordinate)
- **Fiat Line** (1D): Occupies one-dimensional spatial region (border between countries, edge of table)
- **Fiat Surface** (2D): Occupies two-dimensional spatial region (skin surface, boundary plane between air and water)

**Examples**:[^13][^11]

- Equator (fiat line around Earth)
- State border through field (fiat line/surface)
- Surface of object (fiat surface, as physical surface not perfectly continuous at atomic level)[^11]

**Critical Note**: All boundaries in BFO are fiat boundaries because at sufficient granularity (atomic/molecular), no perfectly sharp natural boundaries exist.[^13]

**3. Spatial Region**[^10][^11]

**Definition**: Portion of space itself (not an entity occupying space, but the space).

**Sub-types**:

- Zero-dimensional: Point
- One-dimensional: Line segment
- Two-dimensional: Surface region
- Three-dimensional: Volume

**Usage**: Material entities occupy three-dimensional spatial regions; boundaries occupy lower-dimensional regions.[^11]

### Dependent Continuant

**Definition**: Continuants that depend on other entities for their existence.[^14][^4][^3]

BFO distinguishes two fundamentally different types of dependence:

#### Specifically Dependent Continuant (SDC)

**Definition**: Depends for existence on ONE specific independent continuant—cannot transfer to another bearer.[^15][^14][^10]

**Canonical Example**:[^4][^3][^10]
The **redness of THIS ball**. That specific redness instance exists only as long as this particular ball exists. If the ball is destroyed, the redness ceases. The redness cannot "move" to another ball—another ball's redness is a different redness instance.

**Two Major Sub-types**:

**1. Quality**[^14][^15][^4][^10]

**Definition**: Specifically dependent continuant that needs NO process to be manifest—it simply exists as long as its bearer exists.

**Examples**:

- Color of this ball (redness, blueness)
- Temperature of this patient (98.6°F)
- Mass of this object (50 kg)
- Shape of this molecule
- Electric charge of this particle

**Key Properties**:

- Inheres in exactly one bearer at a time
- Cannot migrate to different bearer
- No process required for manifestation (contrast with realizable entities)

**Sub-type: Relational Quality**[^15]

**Definition**: Quality that inheres in multiple bearers simultaneously.

**Example**: Spatial distance between object A and object B—a quality inhering in both simultaneously.

**2. Realizable Entity**[^16][^17][^18][^4]

**Definition**: Specifically dependent continuant that:

1. Has an independent continuant as bearer
2. Can be **realized** (manifested, actualized, executed) in associated processes
3. Requires a process for its manifestation

**Core Insight**: Unlike qualities (which are always "on"), realizable entities are **potential**—they exist as capabilities or tendencies that may or may not be actualized.[^16][^4]

**Three Sub-types of Realizable Entity**:

**A. Disposition**[^17][^19][^4][^16]

**Definition**: **Internally grounded** realizable entity—if disposition ceases to exist, the bearer's physical makeup must have changed.[^17][^16]

**Examples**:

- **Fragility** of glass (disposition to break when struck)
- **Solubility** of salt (disposition to dissolve in water)
- **Flammability** of wood (disposition to burn when ignited)
- **Vulnerability** of system (disposition to be compromised by attack)

**Internal Grounding**: To remove fragility from glass, you must change its physical structure (e.g., temper it, reinforce it). You cannot remove fragility by changing external circumstances alone.[^16][^17]

**Realization**: Disposition realized in process—fragility realized in breaking process, solubility in dissolving process.

**B. Role**[^18][^4][^17][^16]

**Definition**: **Externally grounded** realizable entity characterized by:

1. **Optionality**: Exists because bearer is in special circumstances the bearer doesn't have to be in[^17][^16]
2. **External dependence**: Role can cease without bearer's physical change—only circumstances change

**Examples**:

- Being a **doctor** (person in medical licensing/employment circumstances)
- Being a **student** (person enrolled in educational institution)
- Being **president** (person elected to office)
- Being a **spouse** (person in marriage relationship)
- Being a **guardian** (person in custodial role)

**External Grounding**: You can lose role of "doctor" (retire, lose license) without any physical change to our body. Role depends on social, institutional, or relational circumstances external to our physical makeup.[^17]

**Realization**: Role realized in processes like practicing medicine (doctor role), attending classes (student role).

**C. Function**[^19][^18][^4][^16][^17]

**Definition**: Realizable entity with intended purpose or designed use; what the bearer is "for."

**Two Types**:

**Biological Function**:[^18][^4]

- Function of **heart to pump blood**
- Function of **enzyme to catalyze reaction**
- Function of **immune system to defend against pathogens**

**Artifact Function** (Use Function):[^17]

- Function of **key to unlock door**
- Function of **firewall to filter network traffic**
- Function of **brake to stop vehicle**

**Realization**: Function realized in processes where bearer performs its function—heart pumping blood, key unlocking door.

**Disposition vs. Function Distinction**: Both are causally grounded in bearer's internal structure, but functions involve **teleology** (purpose, design, selection). Fragility is disposition without purpose; heart's pumping is function selected by evolution.[^19]

#### Generically Dependent Continuant (GDC)

**Definition**: Depends on SOME independent continuant but not any ONE in particular—can migrate between bearers while remaining the same individual.[^20][^14][^15][^10]

**Canonical Example: Information**[^14][^15][^10]

**File content that can be copied**:

- Save file to hard drive₁
- Copy file to hard drive₂
- Delete from hard drive₁
- **Same content**, different bearer

The information (GDC) persists even though its physical bearer changed. This is impossible for specifically dependent continuants.

**Other Examples**:

- **Software code**: Same code on multiple machines
- **Book content**: Same text in multiple physical copies
- **Musical composition**: Same piece played by different orchestras
- **Blueprint**: Same design in multiple documents

**Key Property**: **Bearer-transferability**—can exist in multiple bearers simultaneously or transfer without ceasing to exist.[^20][^15]

**Primary Sub-type: Information Content Entity (ICE)**[^15][^14]

**Definition**: GDC that is "about" something—has aboutness, semantic content.

**Examples**:

- Document content
- Database record
- Ontology itself (information about domain)
- Security policy text
- Standard specification

**Relevance to our Project**: FedRAMP standards, MITRE ATLAS techniques, research paper content are all GDCs (ICEs).

## Occurrent Taxonomy: Entities That Occur

### Process

**Definition**: Occurrent that has temporal proper parts and specifically depends on some material entity at some time.[^21][^22][^23][^3]

**Examples**:

- **Biological**: cell division, metabolism, apoptosis, immune response
- **Physical**: heating, cooling, motion, chemical reaction
- **Social**: meeting, war, election, negotiation
- **Manufacturing**: assembly, quality control, packaging
- **Cybersecurity**: attack process, monitoring process, incident response

**Key Properties**:

**Temporal Parts**:[^24][^3][^9]
Process has parts existing at different times:

- our **youth** is temporal part of our **life**
- **Diastole** and **systole** are temporal parts of **heartbeat**[^24]
- **Reconnaissance** and **exploitation** are temporal parts of **cyberattack**

**Timelessly True Parthood**:[^24]
"Battle of Midway was part of World War II" is **timelessly true**—always was, always will be true. Occurrent parthood is a **two-place relation** (A part_of B), not time-indexed like continuant parthood.

**Cannot Change**:[^9]
Processes don't change properties. If "the motion gets faster," it's different temporal parts with different speeds, not the process changing. Process is the sum of all its temporal parts, each with fixed properties.

**Depends on Continuants**:[^23]
Every process specifically depends on some material entity (participant). Attack process depends on attacker and target; metabolism depends on organism.

### Process Boundary

**Definition**: Occurrent occupying zero-dimensional temporal region (instant).[^22][^21]

**Examples**:

- **Birth**: Beginning of life process
- **Death**: Ending of life process
- **Start of meeting**: Beginning of meeting process
- **Breach detection**: Instant attack detected

**Key Property**: Instantaneous—no temporal extent, marks transition between process phases or between existence and non-existence.

### Temporal Region

**Definition**: Portions of time itself.[^1][^24]

**Sub-types**:

- **Temporal Instant** (0D): Point in time
- **Temporal Interval** (1D): Duration, time span

**Relations**:[^24][^11]

- **Process occupies temporal interval**: Attack spans hours/days
- **Process boundary occupies temporal instant**: Attack begins at t₀


## BFO Relations: Connecting Entities

### Parthood Relations

#### Continuant Part Of

**Three-Place Relation**: `A continuant_part_of B at time t`[^24]

**Why Time-Indexed?** Continuants can gain/lose parts over time:[^24]

- Dog has tail at t₁
- Dog loses tail in accident
- Dog does NOT have tail at t₂

**Transitivity Challenge**:[^24]
Without proper time indexing, transitivity can fail:

- 11th Hussars continuant_part_of King's Royal Hussars at t₁
- King's Royal Hussars continuant_part_of 12th Armored Infantry Brigade at t₂ (different time)
- But 11th Hussars NOT continuant_part_of 12th Brigade

**ISO BFO Solution**: Binarize into two relations:[^24]

1. **A continuant_part_of B at all times**: A is part of B whenever both exist
2. **A continuant_part_of B at some time**: A is part of B at least once

This preserves transitivity while accommodating change.

#### Occurrent Part Of

**Two-Place Relation**: `A occurrent_part_of B` (timelessly)[^24]

**Why Not Time-Indexed?** Occurrent parthood holds timelessly or not at all:

- "Battle of Midway part of WWII" always true[^24]
- "Diastole part of heartbeat" always true (for that heartbeat instance)

**Always Transitive**: If A part_of B and B part_of C, then A part_of C. No time-dependency complications.

### Dependence Relations

#### Specifically Depends On

`Quality specifically_depends_on Object`

**Example**: This redness specifically_depends_on this ball. If ball ceases to exist, redness ceases.

#### Generically Depends On

`Information generically_depends_on some bearer`

**Example**: File content generically_depends_on some storage medium (could be any hard drive, USB, server).

### Inherence Relations

#### inheres_in / bearer_of[^14][^11]

**Inverse pair connecting dependent continuants to bearers**:

- `Quality inheres_in Object`
- `Object bearer_of Quality`

**Example**:

- `Temperature_98.6F inheres_in Patient_Smith`
- `Patient_Smith bearer_of Temperature_98.6F`

**Also for Realizable Entities**:

- `Vulnerability inheres_in System`
- `System bearer_of Vulnerability`


### Realization Relations

#### realizes[^4][^16]

`Process realizes Realizable_Entity`

**Examples**:

- `HeartPumping_process realizes PumpingFunction_of_heart`
- `AttackExecution_process realizes AttackCapability_of_adversary`
- `DissolvingProcess realizes Solubility_of_salt`

**Meaning**: Process is the manifestation/actualization of the realizable entity.

### Spatial/Temporal Relations

#### occupies[^11]

- `Material_Entity occupies Three_Dimensional_Spatial_Region`
- `Process occupies Temporal_Interval`
- `Fiat_Boundary occupies Lower_Dimensional_Spatial_Region`


#### participates_in[^4]

`Continuant participates_in Process`

**Examples**:

- `Enzyme participates_in Catalysis_process`
- `Adversary participates_in Attack_process`
- `Analyst participates_in ThreatAssessment_process`


## Top-Down Development Methodology with BFO

### Phase 1: Foundational Knowledge Acquisition (Weeks 1-4)

#### Study BFO Thoroughly

**Required Reading**:[^7][^5][^1]

1. **BFO Specification**: ISO/IEC 21838-2 (freely available)
2. **Guidebook**: *Building Ontologies with Basic Formal Ontology* (Arp, Smith \& Spear, 2015)
3. **BFO Tutorials**: Video series on YouTube[^25][^7][^1]
4. **BFO Case Studies**: Domain-specific examples[^3]

**Time Investment**: 2-4 weeks intensive study for team leads, 1-2 weeks overview for domain experts.

**Learning Objectives**:

- Master continuant vs. occurrent distinction
- Understand dependent vs. independent continuant
- Grasp realizable entities (disposition, role, function)
- Recognize bona fide vs. fiat boundaries
- Learn BFO axioms and constraints


#### Key Conceptual Exercises

**Exercise 1: Classify Domain Entities**

For each entity in our domain, determine:

- Continuant or Occurrent?
- If Continuant: Independent or Dependent?
- If Dependent: Specifically or Generically?
- If Specifically: Quality or Realizable?
- If Realizable: Disposition, Role, or Function?

**Example Answers**:

- **Firewall device**: Continuant > Independent > Material Entity > Object
- **Firewall filtering capability**: Continuant > Dependent > Realizable > Function
- **Filtering process**: Occurrent > Process
- **Vulnerability**: Continuant > Dependent > Realizable > Disposition
- **Security policy document**: Continuant > Dependent (Generic) > ICE

**Exercise 2: Identify Temporal Parts**

For processes in our domain, identify temporal parts:

- **Cyberattack**: Reconnaissance (part) > Initial Access (part) > Lateral Movement (part) > Exfiltration (part)
- **Compliance Audit**: Planning (part) > Assessment (part) > Reporting (part)

**Exercise 3: Trace Realization Chains**

Map realizable entities to their realizations:

- **Vulnerability** (disposition) → **Exploit_Process** (realization)
- **Detection_Function** (function) → **Monitoring_Process** (realization)
- **Auditor_Role** (role) → **Conducting_Audit_Process** (realization)


### Phase 2: Domain Term Collection and Analysis (Weeks 5-6)

#### Gather Comprehensive Lexicon[^26]

**Sources for our Project**:

1. **FedRAMP**: All 72 KSI definitions, control families, assessment procedures
2. **MITRE ATLAS**: All technique descriptions, tactics, mitigations
3. **Standards**: NIST SP 800-53, ISO 27001/27002, CIS Controls
4. **Research Literature**: Core papers on AI security, adversarial ML
5. **Threat Intelligence**: CVE descriptions, attack pattern databases

**Collection Method**:

- Extract nouns (potential classes)
- Extract verbs (potential properties/processes)
- Extract adjectives (potential qualities/attributes)
- Note hierarchical language ("type of," "kind of," "subclass")

**Example Term List** (partial):

- Nouns: Attack, Control, KSI, Vulnerability, Risk, Evidence, Claim, Mechanism, Standard, Requirement
- Verbs: mitigates, exploits, addresses, supports, implements, validates
- Adjectives: adversarial, certified, compliant, vulnerable, effective


#### Distinguish Entity Types[^26]

**Classes vs. Individuals**:

- **Class**: Type with multiple instances
    - Example: `Control` (class with instances: MFA, Firewall, Encryption)
- **Individual**: Specific, named entity
    - Example: `FedRAMP` (specific standard), `MITRE_ATLAS` (specific framework)

**Types vs. Instances in our Data**:

- **Type**: `AttackPattern` (class)
- **Instance**: `T0043_Craft_Adversarial_Data` (individual attack pattern)

**Relations vs. Qualities**:

- **Relation**: Connects two entities
    - Example: `mitigates` (Control mitigates Attack)
- **Quality**: Property of single entity
    - Example: `severity` (quality of Vulnerability)


### Phase 3: BFO Alignment with Decision Diagram (Weeks 7-10)

#### Use BFO Classifier Tool[^27][^28]

**Tool Function**: Guides alignment through series of yes/no questions.[^27]

**Example Decision Path for "Risk"**:

**Q1**: "Does this entity occur in time (has temporal parts) or endure through time?"

- **A**: Endure → **Continuant**

**Q2**: "Can this entity exist independently, or does it depend on others?"

- **A**: Depends → **Dependent Continuant**

**Q3**: "Does it depend on one specific bearer or can it transfer between bearers?"

- **A**: Specific bearer (this system's risk) → **Specifically Dependent Continuant**

**Q4**: "Does it need a process to be manifest, or is it always manifest?"

- **A**: Needs process (risk realized in harm event) → **Realizable Entity**

**Q5**: "Would removing it require changing bearer's physical makeup?"

- **A**: Yes (reduce risk by hardening system) → **Disposition**

**Result**: `Risk SubClassOf BFO:Disposition`

#### Apply to Core Concepts

**our Project Alignments**:

**1. Control**

**Multiple Aspects** (create separate classes):

- **ControlSpecification**: `BFO:Generically_Dependent_Continuant > ICE`
    - Rationale: Description of control (information, can exist in standards, policies, databases)
- **ControlImplementation**: `BFO:Independent_Continuant > Material_Entity > Object` OR `BFO:Realizable > Function`
    - Rationale: Physical device (Object) OR capability to protect (Function)
- **ControlExecution**: `BFO:Occurrent > Process`
    - Rationale: Actual operation of control over time

**2. AttackPattern**

**Multiple Aspects**:

- **AttackPatternSpecification**: `BFO:Generically_Dependent_Continuant > ICE`
    - Rationale: MITRE ATLAS description (information artifact)
- **AttackProcess**: `BFO:Occurrent > Process`
    - Rationale: Actual execution of attack
- **AttackCapability**: `BFO:Realizable > Disposition`
    - Rationale: Adversary's capability to execute attack

**3. KSI (Key Security Indicator)**

**Alignment**: `BFO:Generically_Dependent_Continuant > ICE`

**Rationale**: KSI definitions are informational specifications that can exist in FedRAMP documents, assessment tools, compliance databases—same KSI content, multiple bearers.

**4. Evidence Fragment**

**Alignment**: `BFO:Generically_Dependent_Continuant > ICE`

**Rationale**: Information extracted from papers, can be cited in multiple places (our knowledge base, reports, other papers).

**5. Standard (FedRAMP, MITRE ATLAS)**

**Alignment**: `BFO:Generically_Dependent_Continuant > ICE`

**Rationale**: Informational specifications existing in documents, websites, databases.

**6. Vulnerability**

**Alignment**: `BFO:Specifically_Dependent_Continuant > Realizable > Disposition`

**Rationale**: Disposition of system to be exploited; inheres in specific system; realized in exploit process.

**7. Risk**

**Alignment**: `BFO:Specifically_Dependent_Continuant > Realizable > Disposition`

**Rationale**: Disposition of asset to suffer harm under certain conditions; inheres in specific asset/system.

**8. Claim**

**Alignment**: `BFO:Generically_Dependent_Continuant > ICE`

**Rationale**: Propositional content (information) about relationships between entities; can exist in papers, our ontology, reports.

**9. Mechanism**

**Alignment**: `BFO:Generically_Dependent_Continuant > ICE` OR `BFO:Occurrent > Process`

- If explanation/description: ICE (information about how something works)
- If actual causal process: Process (the mechanism operating)

**Recommended**: ICE (explanatory model)

#### Document Alignment Rationale[^29][^27]

**For Each Alignment, Record**:

1. **Decision Path**: Answers to BFO Classifier questions
2. **Rationale**: Why this BFO class chosen
3. **Alternatives Considered**: Other BFO classes evaluated
4. **Edge Cases**: Situations where alignment uncertain
5. **Domain Expert Validation**: Confirmation from stakeholders

**Example Documentation**:

```
Class: Risk
BFO Alignment: BFO:Disposition
Decision Path: Continuant > Dependent > Specifically Dependent > Realizable > Disposition
Rationale: Risk is a disposition of an asset to suffer harm. It inheres in specific systems (not transferable like information). Realized in harm events when threat exploits vulnerability.
Alternatives: Quality (rejected—risk requires realization process, not always manifest)
Edge Cases: Risk scores/metrics might be Qualities (measurements), distinct from risk itself
Validation: Security architect confirmed risk is potential harm, not actual measurement
```


### Phase 4: Build Mid-Level Security Ontology (Weeks 11-16)

#### Create Reusable Security Framework

**Goal**: Develop domain ontology extending BFO, reusable across security projects.[^6][^8]

**Mid-Level Classes** (partial hierarchy):

```owl
# Material Security Entities
BFO:Material_Entity
  └─ SecurityDevice [new]
      ├─ NetworkSecurityDevice
      │   ├─ Firewall
      │   ├─ IntrusionDetectionSystem
      │   └─ IntrusionPreventionSystem
      ├─ EndpointSecurityDevice
      │   ├─ AntivirusSoftware (if considering software as artifact)
      │   └─ HostFirewall
      └─ PhysicalSecurityDevice
          ├─ AccessControlSystem
          └─ SurveillanceCamera

# Information Security Entities
BFO:Generically_Dependent_Continuant
  └─ SecurityInformationArtifact [new]
      ├─ SecurityPolicy
      │   ├─ AccessControlPolicy
      │   └─ DataProtectionPolicy
      ├─ SecurityStandard
      │   ├─ RegulatoryStandard (FedRAMP, NIST)
      │   └─ IndustryBestPractice (CIS, OWASP)
      ├─ ThreatIntelligence
      │   ├─ ThreatIndicator
      │   └─ AttackPatternSpecification
      └─ VulnerabilityReport
          ├─ CVEReport
          └─ VulnerabilityDisclosure

# Security Processes
BFO:Process
  └─ SecurityProcess [new]
      ├─ AttackProcess
      │   ├─ ReconnaissanceProcess
      │   ├─ InitialAccessProcess
      │   ├─ ExecutionProcess
      │   ├─ PersistenceProcess
      │   ├─ PrivilegeEscalationProcess
      │   ├─ DefenseEvasionProcess
      │   ├─ CredentialAccessProcess
      │   ├─ DiscoveryProcess
      │   ├─ LateralMovementProcess
      │   ├─ CollectionProcess
      │   └─ ExfiltrationProcess
      ├─ DefenseProcess
      │   ├─ MonitoringProcess
      │   ├─ DetectionProcess
      │   ├─ IncidentResponseProcess
      │   │   ├─ ContainmentProcess
      │   │   ├─ EradicationProcess
      │   │   └─ RecoveryProcess
      │   └─ PreventionProcess
      └─ AssessmentProcess
          ├─ VulnerabilityAssessmentProcess
          ├─ PenetrationTestingProcess
          ├─ RiskAssessmentProcess
          └─ ComplianceAuditProcess

# Security Realizable Entities
BFO:Realizable_Entity
  └─ SecurityRealizable [new]
      ├─ SecurityDisposition
      │   ├─ Vulnerability
      │   │   ├─ SoftwareVulnerability
      │   │   ├─ ConfigurationVulnerability
      │   │   └─ DesignVulnerability
      │   ├─ Threat
      │   │   ├─ InsiderThreat
      │   │   └─ ExternalThreat
      │   └─ Risk
      │       ├─ OperationalRisk
      │       ├─ ComplianceRisk
      │       └─ ReputationalRisk
      ├─ SecurityFunction
      │   ├─ ProtectionFunction
      │   │   ├─ AccessControlFunction
      │   │   ├─ EncryptionFunction
      │   │   └─ AuthenticationFunction
      │   ├─ DetectionFunction
      │   │   ├─ AnomalyDetectionFunction
      │   │   └─ SignatureDetectionFunction
      │   └─ ResponseFunction
      │       ├─ AlertingFunction
      │       └─ IsolationFunction
      └─ SecurityRole
          ├─ SecurityAdministratorRole
          ├─ SecurityAnalystRole
          ├─ IncidentResponderRole
          ├─ SecurityAuditorRole
          └─ ChiefInformationSecurityOfficerRole

# Security Qualities
BFO:Quality
  └─ SecurityQuality [new]
      ├─ ConfidentialityLevel
      ├─ IntegrityLevel
      ├─ AvailabilityLevel
      ├─ SeverityLevel
      └─ EffectivenessRating
```


#### Define Mid-Level Relations

**Extending BFO Relations with Domain Specifics**:

```owl
# Inherited from BFO
- inheres_in: Vulnerability inheres_in System
- bearer_of: System bearer_of Vulnerability
- realizes: ExploitProcess realizes Vulnerability
- participates_in: Adversary participates_in AttackProcess

# New Domain Relations (not in BFO)
ObjectProperty: exploitsVulnerability
  Domain: AttackProcess
  Range: Vulnerability
  SubPropertyOf: realizes (exploiting is form of realizing vulnerability)

ObjectProperty: mitigatesAttack
  Domain: DefenseProcess
  Range: AttackProcess
  Annotations: "Defense process counteracts attack process"

ObjectProperty: protectsAgainst
  Domain: SecurityFunction
  Range: Threat
  Annotations: "Function designed to protect against threat"

ObjectProperty: detectsThreat
  Domain: DetectionFunction
  Range: Threat
  
ObjectProperty: remediatesVulnerability
  Domain: ResponseFunction
  Range: Vulnerability

ObjectProperty: hasImpactLevel
  Domain: Vulnerability OR Risk
  Range: SeverityLevel (Quality)

ObjectProperty: compliesWithStandard
  Domain: SecurityProcess OR SecurityDevice
  Range: SecurityStandard (ICE)
```


#### Axiomatize Mid-Level Classes

**Add Logical Constraints**:

```owl
Class: Vulnerability
  SubClassOf: BFO:Disposition
  SubClassOf: inheres_in some System
  SubClassOf: realized_by some ExploitProcess
  DisjointWith: SecurityFunction, Threat

Class: SecurityFunction
  SubClassOf: BFO:Function
  SubClassOf: inheres_in some SecurityDevice
  SubClassOf: realized_by some DefenseProcess
  
Class: AttackProcess
  SubClassOf: BFO:Process
  SubClassOf: exploitsVulnerability some Vulnerability
  SubClassOf: participates_in some Adversary
  SubClassOf: has_part min 1 AttackPhase

Class: SecurityDevice
  SubClassOf: BFO:Object
  SubClassOf: bearer_of some SecurityFunction
  SubClassOf: participates_in some DefenseProcess
```


### Phase 5: Specialize to AI Cybersecurity Domain (Weeks 17-24)

#### Extend Mid-Level to our Project

**FedRAMP Module**:

```owl
# Extend Information Artifacts
SecurityStandard
  └─ FedRAMPStandard [new domain class]
      SubClassOf: SecurityStandard
      SubClassOf: BFO:Generically_Dependent_Continuant
      Annotations: "Federal Risk and Authorization Management Program standard"

FedRAMPStandard
  └─ FedRAMPKSI [new]
      SubClassOf: FedRAMPStandard
      SubClassOf: specifiesRequirement some SecurityRequirement
      Annotations: "One of 72 Key Security Indicators in FedRAMP 20x"

# Individuals (KSI instances)
Individual: KSI_001_AccessControl
  Type: FedRAMPKSI
  hasKSINumber "001"
  hasDescription "Limit information system access..."
  hasControlFamily "Access Control (AC)"

Individual: KSI_002_AwarenessTraining
  Type: FedRAMPKSI
  hasKSINumber "002"
  ...

[Continue for all 72 KSIs]

# Controls
SecurityFunction
  └─ FedRAMPControl [new]
      SubClassOf: SecurityFunction
      SubClassOf: addressesKSI some FedRAMPKSI
      SubClassOf: addressesKSI min 1 FedRAMPKSI
      Annotations: "Control specified in FedRAMP baseline"

FedRAMPControl
  ├─ AccessControl
  │   ├─ MFAControl
  │   └─ RBACControl
  ├─ AuditControl
  │   └─ LoggingControl
  └─ ... (all control families)
```

**MITRE ATLAS Module**:

```owl
# Extend Information Artifacts
AttackPatternSpecification
  └─ ATLASPatternSpecification [new]
      SubClassOf: AttackPatternSpecification
      SubClassOf: BFO:Generically_Dependent_Continuant
      Annotations: "Attack pattern from MITRE ATLAS framework"

ATLASPatternSpecification
  └─ ATLASTechnique [new]
      SubClassOf: ATLASPatternSpecification
      SubClassOf: usesTactic some ATLASTactic
      SubClassOf: mitigatedBy some ATLASMitigation

# Individuals (Technique instances)
Individual: T0043_Craft_Adversarial_Data
  Type: ATLASTechnique
  hasTechniqueID "T0043"
  hasDescription "Craft adversarial data to evade ML model"
  usesTactic Tactic_ML_Attack_Staging

Individual: T0044_Full_ML_Model_Access
  Type: ATLASTechnique
  hasTechniqueID "T0044"
  ...

# Extend Processes
AttackProcess
  └─ AdversarialMLAttack [new]
      SubClassOf: AttackProcess
      SubClassOf: targetsAISystem some AISystem
      SubClassOf: followsPattern some ATLASPatternSpecification

AdversarialMLAttack
  ├─ ModelInversionAttack
  ├─ ModelExtractionAttack
  ├─ DataPoisoningAttack
  │   ├─ LabelFlippingAttack
  │   └─ BackdoorAttack
  ├─ EvasionAttack
  │   └─ AdversarialExampleAttack
  └─ MembershipInferenceAttack

# Tactics (Organizing Concepts - ICE)
Individual: Tactic_Reconnaissance
  Type: ATLASTactic
Individual: Tactic_Resource_Development
  Type: ATLASTactic
Individual: Tactic_ML_Attack_Staging
  Type: ATLASTactic
...
```

**Evidence Module**:

```owl
# Extend Information Artifacts
BFO:Generically_Dependent_Continuant
  └─ ResearchArtifact [new]
      SubClassOf: BFO:ICE
      
ResearchArtifact
  ├─ ResearchPaper
  │   SubClassOf: hasAuthor some Researcher
  │   SubClassOf: publishedIn some Venue
  │   SubClassOf: hasPublicationDate some xsd:date
  ├─ EvidenceFragment
  │   SubClassOf: extractedFrom some ResearchPaper
  │   SubClassOf: hasConfidenceLevel some xsd:float
  │   SubClassOf: supportsEvidence some Claim
  ├─ Claim
  │   SubClassOf: aboutEntity some BFO:Entity
  │   SubClassOf: supportedBy min 1 EvidenceFragment
  │   └─ EffectivenessClaim
  │       SubClassOf: Claim
  │       SubClassOf: aboutControl some SecurityFunction
  │       SubClassOf: aboutAttack some AttackProcess
  │   └─ MechanismClaim
  │       SubClassOf: Claim
  │       SubClassOf: explainsMechanism some Mechanism
  └─ Mechanism
      SubClassOf: ResearchArtifact
      SubClassOf: explainsRelationship between (?x, ?y)
      Annotations: "Causal or explanatory model"
```


#### Bridge Modules with Integration Ontology

```owl
# Cross-Module Relations
ObjectProperty: addressesKSI
  Domain: FedRAMPControl
  Range: FedRAMPKSI
  Annotations: "Control addresses security indicator"

ObjectProperty: mitigatesATLASTechnique
  Domain: FedRAMPControl
  Range: ATLASTechnique
  Annotations: "Control mitigates ATLAS technique"

ObjectProperty: techniqueTargetsKSI
  Domain: ATLASTechnique
  Range: FedRAMPKSI
  Annotations: "Attack technique targets systems measured by KSI"

ObjectProperty: providesEvidenceFor
  Domain: EvidenceFragment
  Range: Claim
  
ObjectProperty: claimAboutControl
  Domain: EffectivenessClaim
  Range: FedRAMPControl
  
ObjectProperty: claimAboutTechnique
  Domain: EffectivenessClaim
  Range: ATLASTechnique

# Integration Axioms
EffectivenessClaim
  SubClassOf: claimAboutControl some FedRAMPControl
  SubClassOf: claimAboutTechnique some ATLASTechnique
  SubClassOf: supportedBy min 1 EvidenceFragment
  Annotations: "Claim that control is effective against technique, backed by evidence"
```


### Phase 6: Populate and Validate (Weeks 25-36)

#### Populate with Instances

**FedRAMP KSIs**: Create 72 individuals (KSI_001 through KSI_072)

**MITRE ATLAS Techniques**: Create individuals for all techniques (T0043, T0044, etc.)

**Research Papers**: Create individuals for evidence corpus:

```owl
Individual: Paper_Smith2024
  Type: ResearchPaper
  hasAuthor "Smith, J."
  publishedIn "IEEE S&P 2024"
  hasPublicationDate "2024-05-20"
  hasDOI "10.1109/SP.2024.12345"

Individual: Evidence_Fragment_001
  Type: EvidenceFragment
  extractedFrom Paper_Smith2024
  hasContent "MFA reduced unauthorized access by 94% in controlled experiment"
  hasConfidenceLevel "0.92"
  supportsEvidence Claim_MFA_Effectiveness

Individual: Claim_MFA_Effectiveness
  Type: EffectivenessClaim
  claimAboutControl MFAControl
  claimAboutTechnique T0043_Craft_Adversarial_Data
  supportedBy Evidence_Fragment_001
  supportedBy Evidence_Fragment_047
  hasStrength "Strong"
```


#### Validate with Competency Questions

**Translate CQs to DL Queries or SPARQL**:

**CQ1**: "Which FedRAMP controls address KSI-015 (Access Control)?"

```sparql
SELECT ?control
WHERE {
  ?control rdf:type :FedRAMPControl .
  ?control :addressesKSI :KSI_015_AccessControl .
}
```

**CQ2**: "Which MITRE ATLAS techniques are mitigated by MFA?"

```sparql
SELECT ?technique
WHERE {
  :MFAControl :mitigatesATLASTechnique ?technique .
  ?technique rdf:type :ATLASTechnique .
}
```

**CQ3**: "What research evidence (confidence > 0.8) supports that control C mitigates attack A?"

```sparql
SELECT ?evidence ?paper ?confidence
WHERE {
  ?claim rdf:type :EffectivenessClaim .
  ?claim :claimAboutControl :MFAControl .
  ?claim :claimAboutTechnique :T0043_Craft_Adversarial_Data .
  ?claim :supportedBy ?evidence .
  ?evidence :hasConfidenceLevel ?confidence .
  FILTER (?confidence > 0.8)
  ?evidence :extractedFrom ?paper .
}
```

**Execute Queries, Verify Results**:

- If query fails: Missing classes, properties, or instances
- If query returns wrong results: Incorrect axioms or alignments
- If query slow: Optimize restrictions, add indices


#### Reasoner Validation

**Run DL Reasoner** (HermiT, Pellet, FaCT++):

1. **Consistency Check**: No logical contradictions
2. **Class Satisfiability**: All classes can have instances
3. **Inferred Taxonomy**: Check automatically inferred subsumptions
4. **Realization**: Infer types for individuals

**Example Inferred Knowledge**:

```
MFAControl implements AccessControlFunction
AccessControlFunction SubClassOf SecurityFunction
SecurityFunction SubClassOf BFO:Function
→ Reasoner infers: MFAControl SubClassOf BFO:Function
```


#### Iterate and Refine

**Gap Analysis**:

- CQs unanswerable → Add missing classes/properties
- Incorrect answers → Fix axioms, alignments
- Performance issues → Simplify restrictions, modularize

**Stakeholder Review**:

- Domain experts validate terminology, definitions
- Security architects validate attack-control mappings
- Compliance officers validate KSI mappings
- Researchers validate evidence representation

**Refinement Cycles** (repeat until target quality):

1. Identify issues from validation
2. Update ontology (add/modify/remove elements)
3. Re-run reasoner, re-execute CQs
4. Review with stakeholders
5. Document changes and rationale

## Advantages of Top-Down with BFO for our Project

### 1. Maximum Interoperability[^2][^6][^8]

**Existing BFO-Aligned Security Ontologies**:

- **UCO (Unified Cyber Ontology)**: Cyber investigation
- **Security Ontologies**: Threat, vulnerability, attack taxonomies
- **Infrastructure Ontologies**: Cloud computing, network architecture

**our Benefit**: Import and reuse classes from these ontologies without reimplementation. Automatic semantic alignment because all use BFO foundation.

### 2. Formal Rigor and Reasoning[^6]

**Inherited BFO Axioms**:

- Disjointness: Continuant disjoint from Occurrent
- Parthood transitivity: If A part_of B and B part_of C, then A part_of C
- Dependence constraints: Quality must inhere_in Independent Continuant

**our Benefit**: Reasoner automatically detects:

- Modeling errors (e.g., attack both Process and Object)
- Missing axioms (e.g., control without bearer)
- Inconsistencies (e.g., contradictory restrictions)


### 3. Long-Term Stability[^2][^7]

**ISO Standard**: BFO won't change capriciously; updates follow rigorous standardization process.[^2]

**our Benefit**: Ontology investment protected. No risk of foundational ontology abandonment or incompatible major version.

### 4. Community and Resources[^25][^7][^5][^1]

**Extensive Support**:

- **Guidebook**: 300+ page manual with examples[^5]
- **Tutorials**: Hours of video instruction[^7][^25][^1]
- **Workshops**: Regular training events[^5]
- **Community**: Active mailing lists, forums
- **Tools**: BFO Classifier, alignment validators[^28][^27]

**our Benefit**: Team not alone. Can leverage community expertise, ask questions, share experiences.

### 5. Multi-Domain Integration Potential

**Future Extensions**:
If later need to integrate with:

- **Biomedical** (e.g., AI for healthcare security)
- **Industrial** (e.g., AI for manufacturing security)
- **Geospatial** (e.g., physical security)

BFO alignment makes this seamless—all domains share upper-level vocabulary.

## Challenges and Mitigation Strategies

### Challenge 1: Steep Learning Curve

**Problem**: 2-4 weeks study required; philosophical concepts challenging for engineers.[^29][^6]

**Mitigation**:

- **Phased Training**: Core team (2-3 people) study intensively; train others incrementally
- **External Expertise**: Hire BFO consultant for kickoff workshop
- **Learning by Doing**: Start with mid-level security ontology (familiar domain), practice BFO alignment on known concepts
- **Tool Support**: Use BFO Classifier to guide decisions, reduces need for deep theoretical understanding[^27]


### Challenge 2: Alignment Ambiguity

**Problem**: Some domain concepts don't map cleanly; multiple valid BFO interpretations.[^29][^27]

**Mitigation**:

- **Document Decisions**: Record alignment rationale, alternatives considered
- **Consistency over Perfection**: Choose one interpretation, apply consistently
- **Community Consultation**: Post ambiguous cases to BFO mailing list for expert input
- **Iterative Refinement**: Alignment not final; adjust based on downstream issues


### Challenge 3: Abstraction Overhead

**Problem**: BFO introduces abstract classes (GDC, SDC) that stakeholders find alienating.

**Mitigation**:

- **Layered Presentation**: Show stakeholders domain-level ontology only; hide BFO complexity
- **Domain Terminology**: Use familiar terms in annotations ("Security Control" not "Realizable Entity Function")
- **Visual Tools**: Develop user interfaces that present ontology in domain-specific views
- **Selective Exposure**: Only ontology engineers need deep BFO knowledge; domain experts interact at mid/domain level


### Challenge 4: Risk of Empty Content

**Problem**: Top-down can create abstract classes never instantiated.[^30]

**Mitigation**:

- **Evidence-Driven**: Only create mid-level classes when needed by domain use cases
- **Regular Reviews**: Quarterly audit for unused classes; deprecate if no instances after 6 months
- **CQ Validation**: Every class must support answering at least one competency question
- **Hybrid Approach**: Use top-down for structure, bottom-up for population (Phase 6 focus on instances)


### Challenge 5: Time Investment

**Problem**: 36 weeks (9 months) from learning to validated ontology is long.

**Mitigation**:

- **Parallel Workstreams**: While core team learns BFO (Weeks 1-4), others collect domain terms (Phase 2)
- **Incremental Delivery**: Release FedRAMP module first (Week 16), ATLAS module next (Week 20), Evidence module last (Week 24)
- **MVP Approach**: Minimum Viable Ontology answering top 10 CQs by Week 12; expand iteratively
- **Reuse Mid-Level**: Don't build security ontology from scratch; adopt existing BFO-aligned security ontology as starting point


## Recommended Hybrid: Top-Down Structure, Bottom-Up Content

### Optimal Strategy for our Project

**Combine Strengths**:

1. **Top-Down (Weeks 1-16)**: Learn BFO, align core concepts, build mid-level security ontology
2. **Bottom-Up (Weeks 17-24)**: Extract evidence from papers, populate KSI/ATLAS instances
3. **Middle-Out Iteration (Weeks 25-36)**: Refine based on CQs, operating at domain-central concepts (KSI, Control, Attack)

**Result**: Formal rigor and interoperability (top-down) + empirical grounding and relevance (bottom-up) + agile iteration (middle-out).

### Concrete Timeline

| Phase | Weeks | Activity | Approach |
| :-- | :-- | :-- | :-- |
| 1 | 1-4 | Learn BFO | Top-Down |
| 2 | 5-6 | Collect domain terms | Bottom-Up |
| 3 | 7-10 | Align to BFO | Top-Down |
| 4 | 11-16 | Build mid-level | Top-Down |
| 5 | 17-20 | FedRAMP module | Top-Down (structure) + Bottom-Up (instances) |
| 6 | 21-24 | ATLAS module | Top-Down + Bottom-Up |
| 7 | 25-28 | Evidence module | Bottom-Up (extraction) |
| 8 | 29-36 | Validate \& refine | Middle-Out (CQ-driven iteration) |

## Conclusion: When to Choose Top-Down with BFO

**Choose Top-Down with BFO if**:

- Long-term interoperability with other BFO ontologies is critical
- Formal semantic rigor required for compliance reasoning or certification
- Team has or can acquire BFO expertise (hire consultant or train core members)
- 9-month timeline acceptable for comprehensive, production-grade ontology
- Integration with biomedical, industrial, or other BFO domains anticipated

**Consider Alternatives if**:

- Rapid prototyping prioritized (3-month deadline) → Middle-Out
- Team lacks ontology engineering expertise, no budget for training → Bottom-Up
- Stakeholders resistant to abstract formalism → Middle-Out
- Domain highly novel with few precedents → Middle-Out (discover structure iteratively)

For our **AI cybersecurity evidence system**, top-down with BFO offers compelling advantages—especially interoperability with existing security ontologies and formal precision for FedRAMP compliance reasoning—provided you invest in the learning curve and manage abstraction complexity through layered presentation and tooling support.
<span style="display:none">[^31][^32][^33][^34][^35][^36][^37][^38][^39][^40][^41][^42][^43][^44]</span>

<div align="center">⁂</div>

[^1]: https://www.youtube.com/watch?v=GWkk5AfRCpM

[^2]: https://en.wikipedia.org/wiki/Basic_Formal_Ontology

[^3]: https://philarchive.org/archive/OTTBBF

[^4]: http://ontology.buffalo.edu/smith/articles/realizables.pdf

[^5]: https://basic-formal-ontology.org

[^6]: https://www.nist.gov/document/nist-ai-rfi-cubrcinc002pdf

[^7]: https://www.youtube.com/watch?v=uflMfvI-ZxI

[^8]: https://www.youtube.com/watch?v=glmdyYbEjyc

[^9]: https://isao2016.inf.unibz.it/wp-content/uploads/2016/06/bolzano-notes.pdf

[^10]: https://www.stephendiehl.com/posts/bfo/

[^11]: https://www.youtube.com/watch?v=GJJcu0UKQyo

[^12]: https://pmc.ncbi.nlm.nih.gov/articles/PMC3520998/

[^13]: https://www.utwente.nl/en/eemcs/fois2024/resources/papers/ceusters-fiat-surfaces-in-basic-formal-ontology.pdf

[^14]: https://www.nist.gov/document/nist-ai-rfi-cubrcinc004pdf

[^15]: https://ceur-ws.org/Vol-2137/ws_SoLe_paper_1.pdf

[^16]: https://fois2021.inf.unibz.it/wp-content/uploads/2021/08/paper_23.pdf

[^17]: https://ceur-ws.org/Vol-3249/paper5-FOUST.pdf

[^18]: https://www.nature.com/articles/npre.2008.1941.1.pdf

[^19]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4089563/

[^20]: https://keet.wordpress.com/2008/07/09/bfo’s-specific-and-generic-dependence-and-generalising-progress-in-essential-and-mandatory-parts/

[^21]: http://www.jarrar.info/publications/JC17.pdf

[^22]: https://www.virtualflybrain.org/blog/releases/ontologies/bfo/

[^23]: http://isao2020.inf.unibz.it/wp-content/uploads/2016/06/bolzano-slides-3.pdf

[^24]: https://www.youtube.com/watch?v=8-dGGDQ7qCw

[^25]: https://www.youtube.com/playlist?list=PLyngZgIl3WTiv14_38gdzEubaurk4v6E3

[^26]: https://www.sciencedirect.com/science/article/abs/pii/S1566253508000377

[^27]: https://ceur-ws.org/Vol-3249/paper3-FOUST.pdf

[^28]: https://keet.wordpress.com/2021/12/10/bfo-decision-diagram-and-alignment-tool/

[^29]: https://pubs.cs.uct.ac.za/1678/1/FAIA-377-FAIA231123.pdf

[^30]: https://ceur-ws.org/Vol-3603/workshopOIIDDS1.pdf

[^31]: Guide_Engineering_Basic_SchemaDesign.md

[^32]: prompt_context.txt

[^33]: 2008.07863v1_metadata.json

[^34]: 2504.00441_metadata.txt

[^35]: README.md

[^36]: http://basic-formal-ontology.org/documents/seyed-shapiro-fois-2012.pdf

[^37]: https://ncorwiki.buffalo.edu/index.php/Basic_Formal_Ontology_2.0

[^38]: https://www.sciencedirect.com/topics/computer-science/ontology-alignment

[^39]: https://cse.buffalo.edu/sneps/Bibliography/seyedDissertation.pdf

[^40]: https://developers.sefaria.org/docs/topic-ontology

[^41]: https://protege.stanford.edu/publications/ontology_development/ontology101.pdf

[^42]: https://www.cto.mil/wp-content/uploads/2025/06/SERC_Handbook-on-Digital-Engineering-with-Ontologies_2.0.pdf

[^43]: https://ontology.naas.ai/bfo/Occurrent/Process/

[^44]: https://oborel.github.io/obo-relations/process-relations/

