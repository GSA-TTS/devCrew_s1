# Ontology and Schema Design for a Large-Scale, Evidence-Centric Knowledge Graph

## Executive Summary

Designing the ontology and schema for our 4-layer knowledge graph (Data → Extracted Knowledge → Knowledge Domain → Operational) is the single most important architectural decision for long‑term scalability, interoperability, and trustworthiness of the system. Robust ontology design will:[1]

- Encode **clear semantics** for EKIs, KD items, and operational views.
- Support **evidence tracking** and provenance for every knowledge claim.
- Allow **schema evolution** as AI/cybersecurity standards and practices change.
- Enable **hybrid use** of property graphs and semantic web standards (RDF/OWL, SHACL) for both flexibility and rigor.

The key best practices below draw from canonical ontology guidance (Noy & McGuinness “Ontology Development 101”), FAIR ontology best practices, ontology design patterns, enterprise ontology design guidance, and modern property-graph practice (Neo4j, FalkorDB, Semantic Arts, etc.).[2][3][4][5][6][7][8][9][10][11][12][13][14]

***

## 1. Ontology Design Methodology: How to Start and Iterate

### 1.1 Define Domain, Scope, and Competency Questions

Noy & McGuinness emphasize that ontology development must start with explicit **domain, scope, and usage** questions and proceed iteratively.[5][7]

For our system, examples:

- Domain: interdependent cybersecurity in the age of AI agents, across FedRAMP 20x KSIs, MITRE ATLAS, and related standards.[1]
- Scope: what must be representable for:
  - Evidence-backed EKIs (findings, claims, mechanisms).
  - Mappings to KSIs, MITRE ATLAS techniques, other KDs.
  - Operational views (e.g., what AI controls mitigate which attack patterns under which FedRAMP KSIs?).
- Competency questions:
  - “Given a FedRAMP KSI, which EKIs (with sources) describe AI-related risks and mitigations relevant to this KSI?”
  - “Which MITRE ATLAS techniques are addressed by which controls in which cloud environments?”
  - “What research evidence supports the claim that a given AI-agent pattern reduces a specific KSI risk?”

Best practices:

- **Write competency questions first**; use them to drive what classes, properties, and constraints are actually needed.[8][5]
- Accept that **ontology design is intrinsically iterative**; expect to refine class hierarchies and relationships as new standards or research appear.[15][4][5]

### 1.2 Top‑down, Bottom‑up, and Middle‑out

Ontology 101 outlines three strategies; in practice a **middle‑out** approach is usually best.[5]

- **Top‑down**: start from general concepts (Artifact, Risk, Control, Standard, AttackPattern) and specialize.
- **Bottom‑up**: start from concrete instances (a specific paper, a specific KSI, a specific ATLAS technique) and generalize.
- **Middle‑out**: start from salient, domain‑central concepts (KSI, AttackPattern, Control, EvidenceFragment, EKI) and then generalize/specialize as needed.[5]

For our KG:

- Middle‑out is ideal: start from **EKI**, **DataItem**, **KDI (KD Item)**, and **OperationalViewElement** as the backbone, then refine.

***

## 2. Reusing and Extending Existing Ontologies

### 2.1 Why Reuse

Across ontology communities, “**reuse existing ontologies and vocabularies as much as possible**” is a primary best practice.[16][9][11][17][8]

Benefits:

- **Interoperability**: alignment with standards (e.g., FOAF, schema.org, ORG, SKOS, PROV‑O) means external tools and datasets can understand our KG more easily.[9][16][8]
- **Faster design**: avoids reinventing generic patterns (people, organizations, locations, documents).[9][5]
- **Higher quality**: mature ontologies encode many hard‑won modeling decisions and avoid common pitfalls.[6][10][12]

### 2.2 What to Reuse in Our Context

Relevant candidate ontologies/vocabularies:

- **PROV‑O (W3C Provenance Ontology)** for representing that EKIs are derived from one or more DataItems and for modeling evidence chains and data lineage.[18][19][20]
- **Dublin Core / DC Terms** for document metadata: title, creator, date, subject, identifier, etc.
- **FOAF / ORG / schema.org** for people, organizations, roles, and basic descriptive metadata.[8][9]
- **SKOS** for controlled vocabularies and taxonomies (e.g., KSI list, ATLAS techniques, other enumerated control catalogs) where a full ontological commitment is not required.[9]
- **Time Ontology in OWL** for temporal relationships (observation dates, control change dates, version validity).

Best practice is to reuse common building blocks (Person, Organization, Document, ConceptScheme, Concept, Provenance) rather than build them anew.[17][16][8][5][9]

### 2.3 How to Reuse

Best practices for reuse include:[12][16][17][8][5][9]

- **Import, don’t copy**: use mechanisms like `owl:imports` or equivalent to pull in external ontologies instead of re-defining identical classes locally.[21][16][17]
- **Align with, or subclass from, external classes**:
  - e.g., `KSI` as `skos:Concept` in a `skos:ConceptScheme` for the FedRAMP KSI list, with additional local properties.[9]
  - `ResearchPaper` as subclass of `schema:ScholarlyArticle`; `DataItem` as a union of documents and other structured artifacts.
- **Map but avoid “ontology spaghetti”**: prefer a small, curated set of core external ontologies and map to them systematically rather than linking to every ontology encountered.[17][9]
- For shapes/validation, use **SHACL or ShEx** to define the shape that our data must follow when you reuse ontologies.[4][16]

***

## 3. Ontology Design Patterns (ODPs) and Pattern Languages

### 3.1 Role of ODPs

Ontology Design Patterns (ODPs) are **reusable modeling solutions to recurring ontology problems**—analogous to design patterns in software engineering.[10][11][6][12]

Best practices:

- Use ODPs to **systematically avoid common modeling mistakes**, like confusing part‑of vs. subclass, or misrepresenting roles vs. types.[11][6][12]
- Organize ODPs into a **pattern language** for our domain so patterns can be combined coherently.[10][12]
- Focus on **domain‑related ODPs** (DROPs) for cybersecurity, risk, evidence, etc., not just very general patterns, to improve modeling speed and consistency.[12][10]

Examples relevant to our system:

- **Evidence & Provenance Pattern**: modeling claims (EKIs), evidence fragments, sources (DataItems), and derivation steps using PROV‑O terms like `prov:Entity`, `prov:wasDerivedFrom`, `prov:wasAttributedTo`.[19][18]
- **N‑ary relationship patterns**: for relationships involving multiple arguments (e.g., “Control mitigates Risk in Context”), use intermediate nodes/patterns rather than overloaded binary properties.[6][10][5]
- **Classification pattern**: EKIs belonging to one or more KD items (e.g., KSI, ATLAS technique) can use SKOS or similar classification patterns for many‑to‑many assignment.

### 3.2 Documenting Patterns and Ontologies

Good documentation is itself a best practice:

- ODP research stresses **clear pattern documentation templates** (intent, context, solution, consequences, examples) so patterns are applied correctly.[11][12]
- FAIR ontology guidelines recommend:
  - **Human‑readable documentation**.
  - **Machine‑readable representations** with resolvable IRIs.
  - Clear versioning and change logs.[13]

For our project, establish:

- A small internal “**pattern library**” for:
  - Evidence & provenance.
  - Risk–Control–Standard linkage.
  - Attack pattern modeling.
  - EKI grouping & KD membership.
- A documentation standard for each pattern, including **do/don’t examples** specifically in the AI‑cybersecurity context.

***

## 4. Classes, Instances, and Relationship Design

### 4.1 Distinguishing Classes vs Instances

Enterprise ontology guidance emphasizes clear distinction between **classes (types)** and **instances (individuals)**.[8][5]

- **Classes**: `ResearchPaper`, `KSI`, `AttackPattern`, `Control`, `EKI`, `KnowledgeDomain`, `OperationalView`.
- **Instances**: a particular paper, “FRMR‑KSI‑01”, “ATLAS: LLM Jailbreak”, a specific EKI capturing a claim, etc.

Best practices:[5][8]

- Ensure that what has “independent existence” in our domain is modeled as a **class**; descriptive properties belong as **datatype properties**.
- Avoid proliferation of classes that should be instances (e.g., each KSI is an instance of class `KSIConcept` in SKOS; or model each KSI as `skos:Concept` instead of a separate OWL class unless reasoning needs demand otherwise).

### 4.2 Defining Relationships and Cardinalities

High‑quality ontologies explicitly define:

- **Object properties** (links between entities).
- **Datatype properties** (literals, numbers, strings).
- **Cardinalities and constraints** where appropriate.[13][8][5]

For our layers:

- Data/EKI layer:
  - `eki:derivedFrom` (EKI → DataItem) with cardinality ≥ 1 for our evidence requirement.[18][1]
  - `eki:hasEvidenceFragment` (EKI → textual / structural snippet) to anchor claims in source text.
- Knowledge Domain layer:
  - `eki:classifiedUnderKDI` (EKI → KD Item), many‑to‑many.
  - `kd:itemRelatesToItem` (KD Item ↔ KD Item) with typed relationships (e.g., “strengthens”, “contradicts”, “dependsOn”).
- Operational layer:
  - `view:includesKDI` (OperationalView → KD Item).
  - `view:includesEKI` (OperationalView → EKI) for evidence‑rich operational dashboards.

Ontology development guidelines stress being explicit about **intended use, intuitive naming, and role clarity** for each property.[13][8][5][9]

***

## 5. Node vs Attribute: Property-Graph Modeling Heuristics

Our system likely uses a property graph implementation (or a hybrid). The FalkorDB case study highlights an important modeling decision: **what becomes a node vs what stays as an attribute.**[2]

### 5.1 Node vs Attribute Heuristics

From the FalkorDB workshop and broader graph modeling practice:[22][23][24][2]

- Treat something as a **node** when:
  - It needs to be **traversed** from multiple directions or is a hub in queries.
  - It has its **own attributes and lifecycle** (e.g., KSI item, ATLAS technique, Control, Organization).
  - You foresee **relationships to many other entities** (e.g., Country used for geopolitical analysis; Standard used across EKIs).
- Treat something as an **attribute** when:
  - It is **trivial** and not central to traversals (e.g., a static label, a comment).
  - It has limited distinct values and is only used for **filtering within a node**.
  - The domain does not require modeling it as an entity with relationships.

FalkorDB guidance summarizes this as:

- Start from **the questions you need to answer**: if you will often “start from X and traverse outwards”, X should likely be a node.[2]
- Consider **memory and duplication**: repeated strings (e.g., country names) are candidates for nodes or for engine‑level string interning; property graphs like FalkorDB can deduplicate such values.[2]

For our KG:

- Make **EKI**, **DataItem**, **KD Item**, **OperationalView**, **Person**, **Organization**, **Standard**, **AttackPattern** nodes.
- Keep literal **risk score**, **confidence score**, **status flags**, and editorial tags as attributes.
- For **vocabularies** (categories, tags), model them as SKOS concepts or nodes if they participate in reasoning or need multi‑lingual labels.

***

## 6. Property Graphs vs RDF/OWL: Hybrid Strategy

### 6.1 Capabilities and Trade-offs

Semantic Arts and others highlight where pure property graphs “hit the wall” and where RDF/OWL ontologies shine.[3][25]

| Aspect | Property Graphs | RDF/OWL Knowledge Graphs |
|--------|-----------------|--------------------------|
| **Schema** | Often “schema-less”; labels & types implicit; constraints via vendor features (unique/existence constraints).[2][22][3] | Rich, explicit schema (RDFS/OWL classes, properties, axioms). |
| **Identifiers** | Usually local IDs; global URIs optional. | Global IRIs for all resources and schema; easier linked data and “follow our nose” semantics.[3][25] |
| **Constraints & Validation** | Engine-specific constraints; fewer semantics out-of-the-box. | SHACL/ShEx for shape constraints; OWL axioms for logical constraints.[4][16][13] |
| **Inference** | Limited; often manual or application‑coded. | Standard reasoners can infer subclass, property characteristics, sameAs, etc.[3][25] |
| **Interoperability** | Strong for internal apps; weaker for open data. | Designed for semantic web and cross‑system integration.[25][8][13] |
| **Developer ergonomics** | Very intuitive for traversal and application developers.[2][22][24] | Steeper learning curve; more formal but more powerful. |

Best practice emerging in large enterprise KGs is **hybrid**:

- Use a **property graph** (Neo4j, FalkorDB, Neptune PG, etc.) as the main operational store for traversal‑heavy queries and LLM agent integration.[26][24][14][2]
- Maintain an **explicit RDF/OWL ontology layer** (possibly in the same or a companion store) to define:
  - Classes, properties, constraints, mappings to external vocabularies (schema.org, SKOS, PROV‑O).[25][3][8][13]
  - SHACL shapes for validation.[4][16]
- Optionally materialize or sync RDF representations from the property graph, or vice versa, using mapping tools.

This matches our need for **schema flexibility (property graph)** and **semantic rigor and evidence‑based reasoning (RDF/OWL + PROV‑O + SHACL)**.[3][25][1][4][2]

***

## 7. Schema Flexibility and Evolution

Our system needs to improve the “bare‑bone” EKI schema over time without breaking existing data or tools. Modern practice around **schema-adaptable KGs** and **schema evolution/versioning** is directly relevant.[27][28][15][1][4][13]

### 7.1 Schema Versioning

Best practices for KG evolution include:[28][15][27][4][13]

- **Schema versioning**:
  - Maintain explicit **version identifiers** for ontology releases (e.g., `v1.2.0`) and reference them in IRIs or metadata.[15][13]
  - Record change logs describing added/removed classes, properties, and constraints.
- **Backward compatibility**:
  - Prefer **additive changes** (adding new classes/properties) over breaking changes.
  - For breaking changes (e.g., property renames or type changes), support **migration rules** or deprecation periods.
- **Hybrid schema+data versioning**:
  - Combine schema versioning with **data snapshots** of the KG at key milestones, allowing rollback and reproducibility for analyses.[15]

For our system:

- Version the **ontology and shapes**, not just the code:
  - e.g., `cyberkg-ontology-2026-01`, `cyberkg-ontology-2026-06`.
- Maintain an internal **version manifest** linking:
  - Ontology version.
  - SHACL version.
  - Data snapshot or migration scripts used.

### 7.2 Schema-Adaptable Construction

Research on schema‑adaptable KG construction emphasizes:[4]

- **Incremental schema growth**:
  - Support **horizontal expansion** (adding sibling types) and **vertical expansion** (adding subtypes and deeper hierarchies), both common in evolving domains like cybersecurity.[4]
- **Automated schema induction and enrichment**:
  - Use LLMs and statistical analysis to propose new schema elements, then validate them against constraints and competency questions.[4]
- **Validation with shapes**:
  - Automatically learn and refine **ShEx or SHACL shapes** from large KGs and validate new data against these shapes, correcting or rejecting inconsistent structures.[16][4]

These directly map to our plan to refine EKI schemas and add new Knowledge Domains (e.g., new standards) as AI/cybersecurity evolves.

***

## 8. Constraints, Validation, and Quality Control

### 8.1 Constraints in Property Graphs

Property-graph systems like FalkorDB and Neo4j, though “schemaless”, offer **constraints to partially enforce ontology rules**:[22][26][2]

- **Uniqueness constraints**: e.g., `EKI.id` must be unique; `KSI.code` must be unique; `DataItem.doi` or `DataItem.hash` must be unique.[2]
- **Existence constraints**: ensure that certain properties are present on all nodes of a type (e.g., every `DataItem` must have `sourceType` and `ingestionDate`).[2]
- Indexing critical properties to support performance and deduplication.

Best practice is to reflect the high‑level ontology in **concrete constraints** wherever feasible, even if full OWL semantics are not enforced by the	engine.

### 8.2 SHACL/ShEx Validation

RDF/Semantic Web practice strongly recommends using **SHACL or ShEx** to define and validate graph “shapes”:[16][13][4]

- Define shapes for:
  - `EkiShape` (must have at least one `derivedFrom` edge to `DataItem`, a `confidenceScore`, `createdBy`, etc.).
  - `DataItemShape` (must have metadata fields and checksum).
  - `KDIShape` (must belong to exactly one `KnowledgeDomain` and have a unique code).
- Use validation both:
  - At **ingestion time**, to reject or correct malformed data.
  - In **quality audits**, to detect drift as schemas evolve.

Maastricht’s ontology best practices recommend defining such shapes explicitly when reusing ontologies. Recent work on automatic ShEx generation shows this can be partially automated and updated from data patterns.[16][4]

***

## 9. Naming, Identifiers, and FAIR Principles

### 9.1 Stable, Resolvable Identifiers

Semantic Arts and FAIR guidelines highlight that **every node (and schema element) should have a stable, globally unique IRI** where possible.[25][3][13]

Best practices:

- Use structured, stable IRIs for:
  - `DataItem` (e.g., hashed from content, or DOI‑based).
  - `EKI` (e.g., internal namespace plus UUID).
  - `KSI`, `ATLAS technique`, and other KD Items; align with any existing canonical IRIs where possible.
- Ensure ontology IRIs and documentation links are **resolvable**, so a consumer can “follow their nose” from a class or property to its definition.[3][13]

### 9.2 Naming Conventions and Readability

Enterprise ontology design guidance recommends:[8][13][9]

- **Consistent naming**:
  - CamelCase or PascalCase for classes (e.g., `EvidenceKnowledgeItem`).
  - lowerCamelCase for properties (e.g., `derivedFrom`, `classifiedUnderKdi`).
- Avoid overloaded or ambiguous names; prefer **domain‑clear names** like `mitigatesRisk`, `implementsControl`, `addressesKsi`.
- Provide:
  - `rdfs:label` (human‑friendly label).
  - `rdfs:comment` or documentation strings for each class and property.[13]

Applying FAIR ontology best practices means our ontology is **Findable, Accessible, Interoperable, and Reusable**:[13]

- Published in standard formats (Turtle, RDF/XML, JSON‑LD).
- Accompanied by **clear license and governance information**.
- Linked to external standards (e.g., PROV‑O, SKOS, schema.org).[8][9][13]

***

## 10. Mapping the Ontology to Our 4-Layer Architecture

Finally, it helps to explicitly map ontology and schema decisions to the four layers defined in our prompt context.[1]

### 10.1 Data Layer

- Represent **DataItems** as instances of `prov:Entity` (and subclasses like `ScholarlyArticle`, `StandardDocument`, `ThreatReport`).[25][18]
- Use Dublin Core and schema.org for **core metadata**.
- Capture **checksum/hash**, **ingestion timestamp**, **source system**, and associated file references as properties.

### 10.2 Extracted Knowledge Layer (EKIs)

- Model each EKI as an instance of an `EvidenceKnowledgeItem` class:
  - Link to one or more DataItems via PROV (`wasDerivedFrom`) and domain-specific `derivedFromFragment` patterns.[19][18]
  - Include properties for **claim text**, **normalized representation**, **confidence**, **evaluator** (human/agent), **timestamp**.
- Ensure **global uniqueness** of EKI identifiers via constraints and IRI design.[13][2]
- Use **classification patterns** to associate EKIs with KD items.

### 10.3 Knowledge Domain Layer (KDs and KD Items)

- Model FedRAMP KSIs, MITRE ATLAS items, and future catalogs as **SKOS concept schemes** or domain ontologies:[9][8]
  - `KnowledgeDomain` as a `skos:ConceptScheme`.
  - `KDI` as `skos:Concept` with additional domain-specific properties.
- Encode **relationships among KDIs** (e.g., “broader-than”, “related‑to”, “requires”) via SKOS relations (`broader`, `related`) or domain-specific object properties.

### 10.4 Operational Layer (Views and Stakeholder-Specific Semantics)

- Represent an **OperationalView** as a node or resource that:
  - Collects specific KDIs, EKIs, and perhaps aggregated metrics.
  - Adds **stakeholder‑specific relationships** that do not affect the core ontology (e.g., “priorityForCSP”, “excludedByInsurer”).
- Use a clear separation in namespace and ontology modules so operational semantics can evolve without destabilizing the core model.

***

## 11. Practical Recommendations for Our Next Steps

Putting this together for our project:

1. **Define a minimal core ontology module**:
   - Classes: `DataItem`, `EvidenceKnowledgeItem`, `KnowledgeDomain`, `KDI`, `OperationalView`, `Person`, `Organization`.
   - Properties: `derivedFrom`, `classifiedUnderKdi`, `belongsToDomain`, `includesKdi`, `includesEki`, plus provenance links (PROV‑O).

2. **Adopt a hybrid stack**:
   - Property graph as primary store for traversal and LLM‑agent integration, using clear labels and constraints.[22][3][2]
   - RDF/OWL ontology (with SHACL shapes) as the authoritative specification and for advanced reasoning, mapping onto the property graph schema.[3][25][16][13]

3. **Reuse and align with standards**:
   - PROV‑O, SKOS, schema.org, FOAF/ORG, Dublin Core.
   - Use SHACL to define required shapes for EKIs, KDI, and views.[16][13]

4. **Establish governance and evolution processes**:
   - Ontology versioning, change logs, and data snapshot strategy.[15][4][13]
   - Pattern library and documentation for recurrent modeling problems (evidence, risk, control, attack pattern).[6][10][11][12]

5. **Drive modeling from core use cases**:
   - Use our highest‑value operational queries and AI‑agent workflows to test whether the ontology supports efficient traversal and reasoning; adjust middle‑out as needed.[24][22][5][8][2]

This set of practices provides a robust, future‑proof foundation for the ontology and schema design of our large‑scale, evidence-based cybersecurity knowledge graph.

[1](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_3fea1735-a8ad-4396-891a-1a8fed03d040/1592f948-26a4-4e54-ab38-d9248f8ecb8a/prompt_context.txt)
[2](https://www.falkordb.com/blog/how-to-build-a-knowledge-graph/)
[3](https://www.semanticarts.com/property-graphs-training-wheels-on-the-way-to-knowledge-graphs/)
[4](https://www.emergentmind.com/topics/schema-adaptable-knowledge-graph-construction)
[5](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf)
[6](https://pmc.ncbi.nlm.nih.gov/articles/PMC3540458/)
[7](https://ld4pe.dublincore.org/learning_resource/ontology-development-101-a-guide-to-creating-our-first-ontology/index.html)
[8](https://enterprise-knowledge.com/keys-to-successful-ontology-design/)
[9](https://www.mkbergman.com/911/a-reference-guide-to-ontology-best-practices/)
[10](https://nemo.inf.ufes.br/wp-content/papercite-data/pdf/organizing_ontology_design_patterns_as_ontology_pattern_languages_2013.pdf)
[11](https://hammar.dev/downloads/karima2017document.pdf)
[12](https://www.dfki.de/fileadmin/user_upload/import/10542_ODLSJowo.pdf)
[13](https://dgarijo.com/papers/best_practices2020.pdf)
[14](https://www.falkordb.com/blog/building-knowledge-graphs-lessons-from-vcpedia-and-fractal-kg/)
[15](https://www.drivewingrow.com/how-to-manage-knowledge-graph-evolution-and-versioning/)
[16](https://maastrichtu-ids.github.io/best-practices/docs/using-ontologies/)
[17](https://github.com/w3c/scholarly-html/issues/6)
[18](https://milvus.io/ai-quick-reference/how-do-knowledge-graphs-contribute-to-improving-data-lineage)
[19](https://blog.diffbot.com/knowledge-graph-glossary/data-provenance/)
[20](https://data.world/blog/what-is-data-lineage/)
[21](https://stackoverflow.com/questions/74797700/reuse-existing-classes-in-an-ontology)
[22](https://help.neo4j.solutions/neo4j-solutions/cypher-workbench/model/)
[23](https://neo4j.guide/article/Best_practices_for_modeling_our_data_in_Neo4j.html)
[24](https://web.stanford.edu/class/cs520/2020/notes/How_To_Create_A_Knowledge_Graph.html)
[25](https://www.puppygraph.com/blog/rdf-knowledge-graph)
[26](https://aws.amazon.com/blogs/database/build-and-explore-knowledge-graphs-faster-with-amazon-neptune-using-graph-build-and-g-v-part-1/)
[27](https://www.usdsi.org/data-science-insights/schema-in-data-pipelines-strategies-for-modern-data-teams)
[28](https://dataengineeracademy.com/module/best-practices-for-managing-schema-evolution-in-data-pipelines/)
[29](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_3fea1735-a8ad-4396-891a-1a8fed03d040/3a973b45-ab29-4350-bec4-1078d015344b/2008.07863v1_metadata.json)
[30](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_3fea1735-a8ad-4396-891a-1a8fed03d040/212b25f9-e567-4815-b258-a356736d83e0/2504.00441_metadata.txt)
[31](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_3fea1735-a8ad-4396-891a-1a8fed03d040/9c991d75-fa25-4889-8bfa-e7fc9cbbd050/README.md)
[32](https://www.slideshare.net/slideshow/graph-data-modeling-best-practicesericmonkpptx/252240301)
[33](https://wundergraph.com/blog/announcing_graph_feature_flags_for_graphql_federation)
[34](https://support.neo4j.com/s/article/360024789554-Data-Modeling-Best-Practices)
[35](https://www.schemaapp.com/schema-markup/the-4-steps-to-building-a-content-knowledge-graph/)
[36](https://www.semanticscholar.org/paper/Ontology-Development-101:-A-Guide-to-Creating-Our-Noy/c15cf32df98969af5eaf85ae3098df6d2180b637)
[37](https://www.reddit.com/r/semanticweb/comments/n3gvv2/is_there_an_updated_version_of_ontology/)
[38](https://www.scirp.org/reference/referencespapers)