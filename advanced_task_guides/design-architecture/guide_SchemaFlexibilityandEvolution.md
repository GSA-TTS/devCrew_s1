# Guide to Schema Flexibility and Evolution

Schema evolution represents one of the most challenging aspects of enterprise knowledge graph operations, particularly in rapidly evolving domains like AI-cybersecurity where new threats, standards, and research findings emerge continuously. Static schemas quickly become obsolete, yet uncontrolled schema changes risk breaking existing applications, invalidating historical data, and undermining trust in the knowledge system.[^1][^2][^3]

This guide presents a comprehensive framework for schema flexibility and evolution grounded in Basic Formal Ontology (BFO) principles, semantic versioning standards, and modern schema-adaptable construction techniques. The framework balances three competing imperatives: **agility** (rapid schema adaptation to new requirements), **stability** (predictable, backward-compatible changes), and **rigor** (consistency checking via OWL reasoning and SHACL validation).[^4][^3][^5][^6][^7][^1]

Our approach integrates versioned ontology snapshots with automated schema induction from LLMs, SHACL shape extraction from evolving data, and formal migration pathways that preserve data integrity across versions. By anchoring schema evolution in BFO's principled upper-level architecture, organizations ensure that domain-specific changes remain compatible with the broader ontology ecosystem and maintain interoperability across systems.[^8][^5][^7][^9][^4]

## Part I: Schema Versioning Principles and Best Practices

### Semantic Versioning for Ontologies

Semantic Versioning (SEMVER) provides a standardized framework for communicating the impact of ontology changes through version numbers. SEMVER follows an **X.Y.Z pattern** where:[^4]

**Major Version (X)**: Incremented for backward-incompatible changes that require dependent applications to update. Examples include:[^10][^4]

- Removing classes or properties actively used by applications
- Changing domain or range restrictions in ways that invalidate existing data
- Restructuring class hierarchies such that `rdfs:subClassOf` relationships break
- Renaming fundamental concepts without providing equivalence mappings

**Minor Version (Y)**: Incremented for backward-compatible additions—new classes, properties, or axioms that extend functionality without breaking existing queries or applications. Examples:[^10][^4]

- Adding new sibling classes (horizontal expansion)[^1]
- Introducing new optional properties with no cardinality constraints
- Defining new `skos:Concept` instances in controlled vocabularies
- Adding SHACL shapes for validation without altering core ontology

**Patch Version (Z)**: Reserved for bug fixes that correct errors without semantic impact. Less commonly used for ontologies since RDF editors typically catch syntactic issues during authoring.[^4]

**Version Numbering in IRIs**:[^3][^10][^4]

```turtle
# Ontology declaration with version IRI
<https://cybersec.example.org/ontology/v2.1.0> a owl:Ontology ;
    owl:versionIRI <https://cybersec.example.org/ontology/v2.1.0> ;
    owl:versionInfo "2.1.0" ;
    owl:priorVersion <https://cybersec.example.org/ontology/v2.0.0> ;
    dct:created "2025-06-01"^^xsd:date ;
    dct:modified "2026-01-16"^^xsd:date ;
    rdfs:comment "Minor update: Added 15 new MITRE ATLAS techniques, refined PROV-O integration" ;
    owl:imports <http://www.w3.org/ns/prov-o#> ,
                <http://www.w3.org/2004/02/skos/core#> .
```

The `owl:versionIRI` uniquely identifies this specific version, while `owl:priorVersion` creates a linked chain of ontology evolution. Applications specify which version they depend on, enabling controlled migration rather than forced upgrades.[^3][^4]

### Compatibility Types and Change Management

Ontology versioning must manage compatibility in two temporal directions:[^10][^3]

**Backward Compatibility** (Prospective Use): A newer ontology version can correctly interpret data created under an older version. This is the most critical compatibility mode for production systems where historical data remains valuable.[^3][^10]

*Example*: Adding a new property `cybersec:exploitComplexity` to `cybersec:Vulnerability` maintains backward compatibility—old data lacking this property remains valid, and queries not referencing the new property continue to work.[^4]

**Upward Compatibility** (Retrospective Use): Newer data can be correctly interpreted with an older ontology version. This compatibility mode supports scenarios where some systems lag in ontology upgrades.[^10][^3]

*Example*: Adding a new optional annotation property to EKIs maintains upward compatibility—systems using older ontology versions ignore unrecognized properties and process known properties correctly.[^3]

**Full Compatibility**: Changes work correctly in both directions. Purely additive changes (new classes, new optional properties, new concept scheme members) typically achieve full compatibility.[^4][^10][^3]

**Incompatible Changes**: Semantics change such that interpretation is affected in at least one direction. These require major version increments and explicit migration support.[^10][^3][^4]

### Backward Compatibility Strategies

Maintaining backward compatibility reduces disruption to dependent systems and enables gradual migration. Best practices include:[^1][^4][^10]

**1. Check Usage Before Deletion**[^4]

Before removing any ontology element, verify whether it's actively used by applications, data sources, or downstream systems. Unused elements can be removed safely with minor version increment; used elements require deprecation periods and major version changes.[^4]

```sparql
# SPARQL query to check if class is instantiated
SELECT (COUNT(?instance) AS ?instanceCount)
WHERE {
    ?instance a cybersec:LegacyThreatCategory .
}
```

If `?instanceCount = 0` and no applications reference the class in code, removal is safe.[^4]

**2. Deprecation Periods (9-12 months)**[^11][^12]

Mark entities as deprecated rather than immediately deleting them:[^11][^1]

```turtle
cybersec:legacySourceField a owl:DatatypeProperty ;
    rdfs:domain cybersec:EvidenceKnowledgeItem ;
    rdfs:range xsd:string ;
    owl:deprecated true ;
    rdfs:comment "DEPRECATED as of v2.0.0. Use prov:wasDerivedFrom instead. Will be removed in v3.0.0." ;
    dct:modified "2025-06-01"^^xsd:date .
```

Deprecation warnings give applications time to migrate while maintaining functionality. Typical deprecation windows range from 9-12 months before removal.[^12][^11]

**3. Equivalence and Alias Properties**[^1][^10]

When renaming properties or classes, define equivalences to preserve backward compatibility:[^1]

```turtle
# Property rename with backward compatibility
cybersec:hasEvidenceFragment a owl:DatatypeProperty ;
    rdfs:domain cybersec:EvidenceKnowledgeItem ;
    rdfs:range xsd:string ;
    rdfs:comment "Text snippet from source document supporting this EKI" .

cybersec:EvidenceFragment owl:equivalentProperty cybersec:hasEvidenceFragment ;
    owl:deprecated true ;
    rdfs:comment "DEPRECATED: Use cybersec:hasEvidenceFragment" .
```

OWL reasoners automatically infer equivalence, allowing legacy queries using `cybersec:EvidenceFragment` to continue working.[^13][^14]

**4. Additive Backward Compatible Additions**[^10][^4]

Structure schema evolution to favor additions over modifications:[^1][^4]

- **Add new classes** as siblings or subclasses without removing existing classes
- **Add new properties** with optional cardinality (`sh:minCount 0` in SHACL)
- **Extend controlled vocabularies** (SKOS concept schemes) with new members
- **Add SHACL shapes** for new validation rules without altering core ontology axioms

Mark additions explicitly using a dedicated class to track incremental features:[^10]

```turtle
# Track additions for minor version transparency
cybersec:Additions2.1 a owl:Class ;
    rdfs:label "Features added in version 2.1.0" ;
    rdfs:comment "New MITRE ATLAS techniques and exploit complexity property" .

cybersec:exploitComplexity rdfs:subPropertyOf cybersec:Additions2.1 .
cybersec:ATLASTechnique_LLM_DataPoisoning a skos:Concept , cybersec:Additions2.1 .
```

Applications specify the minimal minor version they require, ensuring access to necessary features while maintaining compatibility.[^10]

**5. Migration Rules and Scripts**[^15][^16][^1]

For breaking changes, provide explicit migration pathways:[^15][^1]

```cypher
// Neo4j migration script: Rename property with data transformation
MATCH (eki:EvidenceKnowledgeItem)
WHERE eki.EvidenceFragment IS NOT NULL
SET eki.hasEvidenceFragment = eki.EvidenceFragment
REMOVE eki.EvidenceFragment
```

```sparql
# RDF migration: Transform data for ontology v2.0
DELETE { ?eki cybersec:legacySourceField ?source }
INSERT { 
    ?eki prov:wasDerivedFrom ?dataItem .
    ?dataItem a cybersec:DataItem ;
              schema:url ?source .
}
WHERE {
    ?eki a cybersec:EvidenceKnowledgeItem ;
         cybersec:legacySourceField ?source .
    BIND(IRI(CONCAT("https://cybersec.example.org/data/", MD5(?source))) AS ?dataItem)
}
```

Document migration scripts in version change logs, providing automated upgrade paths for users.[^1][^4]

### Hybrid Schema and Data Versioning

The most robust versioning strategy combines **schema versioning** with **data snapshots**, enabling both schema evolution tracking and point-in-time data recovery.[^17][^1]

**Schema Versioning Component**:[^3][^4][^10]

- Maintain explicit version identifiers in ontology IRIs
- Record change logs describing added/removed/modified elements
- Link successive versions via `owl:priorVersion`
- Provide separate versioned endpoints for major versions

**Data Snapshot Component**:[^18][^19][^17]

- Create full RDF/property graph dumps at key milestones (quarterly releases, major schema changes)
- Tag snapshots with schema version, timestamp, checksum
- Store snapshots in versioned object storage (S3 with versioning, Git LFS, DVC)
- Enable reproducibility for analyses and audits

**Hybrid Architecture Pattern**:[^17][^1]

```yaml
# Version Manifest v2.1.0
version: "2.1.0"
release_date: "2026-01-16"
ontology:
  iri: "https://cybersec.example.org/ontology/v2.1.0"
  file: "ontology/cybersec-v2.1.0.ttl"
  prior_version: "https://cybersec.example.org/ontology/v2.0.0"
shacl_shapes:
  iri: "https://cybersec.example.org/shapes/v2.1.0"
  file: "ontology/shacl-shapes-v2.1.0.ttl"
property_graph_schema:
  neo4j_constraints: "pg-schema/neo4j-constraints-v2.1.0.cypher"
  falkordb_indexes: "pg-schema/falkordb-indexes-v2.1.0.redis"
data_snapshots:
  rdf_dump: "snapshots/2026-01-16-rdf-v2.1.0.nq.gz"
  rdf_checksum_sha256: "a3f5b8c9d2e1..."
  property_graph_export: "snapshots/2026-01-16-neo4j-v2.1.0.cypher.gz"
  pg_checksum_sha256: "7d8f3a2c1b9e..."
mappings:
  rml: "mappings/pg-to-rdf-v2.1.0.rml.ttl"
  r2rml: "mappings/rdb-to-rdf-v2.1.0.r2rml.ttl"
migration_scripts:
  - path: "migrations/2.0-to-2.1-add-exploit-complexity.cypher"
    description: "Add exploitComplexity property to Vulnerability nodes"
  - path: "migrations/2.0-to-2.1-atlas-techniques.sparql"
    description: "Insert 15 new ATLAS technique concepts"
changelog: |
  ### Added (Minor)
  - 15 new MITRE ATLAS techniques for LLM/GenAI threats
  - cybersec:exploitComplexity property (float [0.0, 1.0])
  - SHACL shapes for exploit complexity validation
  ### Changed
  - Refined PROV-O integration: added extractedBy for agent attribution
  - Updated competency questions document
  ### Deprecated
  - cybersec:EvidenceFragment (use cybersec:hasEvidenceFragment)
  ### Fixed
  - Corrected domain/range on cybersec:classifiedUnderKDI
```

This manifest links all components of a versioned release, enabling reproducible deployments and rollback capabilities.[^17][^1]

**Data Snapshot Strategies**:[^19][^18][^17]

*Full Duplication*: Store complete graph at each version.[^19][^17]

- **Pros**: Simple, fast restoration, no reconstruction needed[^17]
- **Cons**: Storage-intensive, viable only for smaller graphs or infrequent snapshots[^19]
- **Use case**: Quarterly releases, regulatory compliance snapshots[^17]

*Incremental Changesets*: Store deltas between versions.[^8][^15]

- **Pros**: Storage-efficient, granular change tracking[^15]
- **Cons**: Requires reconstructing state by replaying changes, slower restoration[^15]
- **Use case**: Continuous schema evolution, large graphs with frequent updates[^8]

*Hybrid Snapshot Strategy*: Full snapshots at major milestones + incremental changes between.[^19][^17]

- **Pros**: Balances storage efficiency and recovery speed[^17]
- **Cons**: More complex to implement and manage[^17]
- **Use case**: Enterprise production systems requiring both agility and reliability[^17]


### Version Manifest Implementation

For our evidence-based cybersecurity knowledge graph, maintain an internal version manifest linking ontology, SHACL shapes, property graph schema, mappings, and migration scripts:[^1]

```turtle
# Version Manifest as RDF (alternative to YAML)
:VersionManifest_v2.1.0 a cybersec:VersionManifest ;
    cybersec:versionNumber "2.1.0" ;
    dct:created "2026-01-16T08:00:00Z"^^xsd:dateTime ;
    cybersec:ontologyIRI <https://cybersec.example.org/ontology/v2.1.0> ;
    cybersec:shaclShapesIRI <https://cybersec.example.org/shapes/v2.1.0> ;
    cybersec:priorManifest :VersionManifest_v2.0.0 ;
    cybersec:dataSnapshot [
        a cybersec:RDFSnapshot ;
        schema:contentUrl <s3://cyberkg-snapshots/2026-01-16-rdf-v2.1.0.nq.gz> ;
        cybersec:checksumSHA256 "a3f5b8c9d2e1..." ;
        schema:dateCreated "2026-01-16T10:00:00Z"^^xsd:dateTime ;
    ] ;
    cybersec:dataSnapshot [
        a cybersec:PropertyGraphSnapshot ;
        schema:contentUrl <s3://cyberkg-snapshots/2026-01-16-neo4j-v2.1.0.cypher.gz> ;
        cybersec:checksumSHA256 "7d8f3a2c1b9e..." ;
        schema:dateCreated "2026-01-16T10:30:00Z"^^xsd:dateTime ;
    ] ;
    cybersec:migrationScript [
        schema:name "Add exploit complexity" ;
        schema:contentUrl <file:///migrations/2.0-to-2.1-add-exploit-complexity.cypher> ;
    ] .
```

Storing manifests as RDF enables queries across version history:

```sparql
# Find all versions introducing new ATLAS techniques
SELECT ?version ?date ?changelog
WHERE {
    ?manifest a cybersec:VersionManifest ;
              cybersec:versionNumber ?version ;
              dct:created ?date ;
              cybersec:changelogText ?changelog .
    FILTER(CONTAINS(?changelog, "ATLAS"))
}
ORDER BY DESC(?date)
```


***

## Part II: Schema-Adaptable Construction with BFO

### Incremental Schema Growth: Horizontal and Vertical Expansion

Knowledge graphs in evolving domains like AI-cybersecurity require continuous schema refinement as new threats, standards, and research emerge. BFO's hierarchical structure naturally supports two modes of incremental growth:[^20][^7][^1]

**Horizontal Expansion**: Adding sibling classes at the same level of abstraction.[^21][^22][^1]

*Mechanism*: Introduce new subclasses of an existing parent without altering the hierarchy depth or removing existing siblings.[^20]

*Example in BFO-Grounded Cybersecurity Ontology*:

```turtle
# Existing ATLAS threat taxonomy
cybersec:ATLASTechnique rdfs:subClassOf bfo:Process .
cybersec:ATLASModelAttack rdfs:subClassOf cybersec:ATLASTechnique .
cybersec:ATLASDataAttack rdfs:subClassOf cybersec:ATLASTechnique .

# Horizontal expansion: Add new sibling threat category
cybersec:ATLASSupplyChainAttack rdfs:subClassOf cybersec:ATLASTechnique ;
    rdfs:label "ATLAS Supply Chain Attack"@en ;
    rdfs:comment "Attacks targeting AI model or data pipelines during development, training, or deployment phases" ;
    dct:created "2026-01-16"^^xsd:date ;
    cybersec:addedInVersion "2.1.0" .
```

Horizontal expansion is fully backward compatible: existing subclasses, instances, and queries remain valid. Applications not yet aware of the new sibling class simply ignore it, while updated applications benefit from finer-grained classification.[^22][^1][^4]

**Vertical Expansion**: Adding subtypes to create deeper hierarchies or specializations.[^21][^20][^1]

*Mechanism*: Subdivide existing classes into more specific subclasses, increasing hierarchy depth.[^20]

*Example*:

```turtle
# Existing coarse-grained class
cybersec:ATLASModelAttack rdfs:subClassOf cybersec:ATLASTechnique .

# Vertical expansion: Refine with specific attack subtypes
cybersec:ModelPoisoning rdfs:subClassOf cybersec:ATLASModelAttack ;
    rdfs:label "Model Poisoning Attack"@en ;
    rdfs:comment "Inject malicious training data to manipulate model behavior" ;
    cybersec:addedInVersion "2.1.0" .

cybersec:AdversarialPerturbation rdfs:subClassOf cybersec:ATLASModelAttack ;
    rdfs:label "Adversarial Perturbation"@en ;
    rdfs:comment "Craft inputs designed to evade or fool model predictions" ;
    cybersec:addedInVersion "2.1.0" .

cybersec:ModelInversion rdfs:subClassOf cybersec:ATLASModelAttack ;
    rdfs:label "Model Inversion Attack"@en ;
    rdfs:comment "Extract sensitive training data by querying model outputs" ;
    cybersec:addedInVersion "2.1.0" .
```

Vertical expansion enriches the ontology's expressiveness while maintaining backward compatibility: instances previously typed as `cybersec:ATLASModelAttack` remain valid, and reasoners infer the parent class membership automatically via `rdfs:subClassOf` transitivity.[^13][^20]

**Hybrid Growth Strategy**:[^1]

Combine horizontal and vertical expansion to adapt to evolving knowledge:

1. **Initial Ontology (v1.0)**: Broad, shallow hierarchy covering known threats
2. **Horizontal Growth (v1.1 - v1.5)**: Add sibling classes as new threat categories emerge
3. **Vertical Refinement (v2.0)**: Deepen hierarchy by subdividing frequently-used classes based on real-world usage patterns
4. **Iterative Refinement (v2.1+)**: Continuously add siblings and refine depth based on competency questions and application feedback

This strategy balances pragmatism (avoid premature ontology engineering) with rigor (maintain logical consistency).[^20][^1]

### BFO-Grounded Schema Evolution: Versioning Case Study

The Basic Formal Ontology (BFO) itself exemplifies principled schema evolution through three major versions (BFO 1.0, 1.1, 2.0), providing valuable lessons for domain ontologies.[^7][^9]

**BFO Evolution Methodology: Realism-Based Ontology Versioning (RBOV)**[^9][^7]

RBOV combines Evolutionary Terminology Auditing (ETA) with realist ontology principles to systematically track and evaluate changes. The method scores each representational element (class, property, axiom) across versions based on:[^7]

- **Objective Existence (OE)**: Does the represented entity actually exist in reality?
- **Objective Relevance (OR)**: Is the entity relevant to the ontology's domain?
- **Belief in Existence (BE)**: Do ontology authors believe the entity exists?
- **Belief in Relevance (BR)**: Do authors believe it's relevant?
- **Intended Encoding (IE)**: Does the representational element correctly encode the intended meaning?

**Governing Principles**:[^7]

*Principle of Consistency with Established Science (PCES)*: The latest ontology version reflects current scientific understanding and serves as the reference standard.[^7]

*Principle of Intended Encoding (PIE)*: Representational elements should accurately encode their intended meaning without ambiguity.[^7]

*Principle of Objective Relevance (PIR)*: The latest version defines what is objectively relevant for the domain; earlier versions are evaluated against this standard.[^7]

**Change Configuration Patterns**:[^7]

RBOV identifies eight types of changes through configuration analysis:

- **Justified Absences (A+)**: Elements correctly absent in a version (e.g., concept not yet discovered or not relevant)
- **Unjustified Absences (A-)**: Elements that should have been present but were missing (errors in earlier versions)
- **Justified Presences (P+)**: Elements correctly included
- **Problematic Presences (P-)**: Elements that should not have been included (errors to be removed)

*Example Pattern*: "A+ P- A+" configuration observed in BFO indicates an element absent in v1.0 (justified), present in v1.1 (problematic), and absent again in v2.0 (justified removal).[^7]

**BFO Quality Trajectory**:[^7]

Empirical analysis shows monotonic quality improvement:

- **BFO 1.0 score**: 0.62 (normalized quality)
- **BFO 1.1 score**: 0.66 (against v1.1 as reference at time t2)
- **BFO 2.0 score**: 1.0 (by definition, as current reference at time t3)

The qualitative improvement from BFO 1.1 to BFO 2.0 was substantially larger than from 1.0 to 1.1, reflecting major conceptual refinements and alignment with scientific ontology standards.[^7]

**Migration Challenges**:[^7]

Domain ontologies built on BFO 1.0 or 1.1 must migrate to BFO 2.0 for continued interoperability. Key challenges identified:[^7]

- **Terminology Ambiguity**: Same terms denoting different concepts across versions (e.g., 'process' in BFO 1.0 vs. 2.0, 'processual entity')[^7]
- **Structural Changes**: Classes moved within the hierarchy, requiring updates to `rdfs:subClassOf` relationships[^7]
- **Deleted Entities**: Terms removed from BFO 2.0 (e.g., 'dependent continuant') require remapping in domain ontologies[^7]

**Lessons for Domain Ontologies**:[^9][^7]

1. **Document Changes Systematically**: Maintain change logs with rationale, not just diffs[^7]
2. **Provide Migration Guidance**: Explicitly state how domain ontologies should update when upper-level ontologies change[^7]
3. **Disambiguate Terminology**: Never assume same term = same concept across versions[^7]
4. **Evaluate Against Latest Standard**: Periodically reassess older versions using current scientific understanding[^7]

### Automated Schema Induction with LLMs

Modern knowledge graph construction increasingly leverages Large Language Models (LLMs) to induce schemas from unstructured text, reducing manual ontology engineering overhead while maintaining alignment with BFO principles.[^5][^6][^23]

**LLM-Based Schema Generation Workflow**:[^6][^23][^5]

1. **Corpus Processing**: Ingest large document collections (research papers, threat reports, standards documents)[^5]
2. **Concept Extraction**: LLM identifies candidate concepts, relations, and attributes via controlled prompting[^23][^5]
3. **Clustering and Refinement**: Statistical clustering groups similar concepts; LLM resolves ambiguities and proposes hierarchies[^23][^5]
4. **BFO Alignment**: Map induced concepts to BFO/CCO upper-level categories (continuants vs. occurrents, qualities vs. roles)[^7]
5. **Validation**: Check induced schema against competency questions, existing ontology constraints, and SHACL shapes[^5][^1]

**AutoSchemaKG: Case Study in Autonomous Schema Induction**[^5]

AutoSchemaKG demonstrates state-of-the-art LLM-driven schema construction:

- **Scale**: Processes tens of millions of documents, constructs billion-node knowledge graphs[^5]
- **Triplet Diversity**: Simultaneously extracts entity-entity, entity-event, and event-event relationships[^5]
- **Semantic Alignment**: Achieves 95% alignment with manually curated ontologies (measured via embedding similarity)[^5]
- **Computational Cost**: Requires extensive resources (e.g., 78,400 GPU hours for ATLAS KG construction)[^5]

**Technique: Controlled Prompt Engineering**:[^5]

```python
# Simplified prompt template for LLM schema induction
schema_induction_prompt = f"""
You are a domain expert in cybersecurity and AI safety. Analyze the following research paper abstract and extract structured knowledge.

Abstract:
{abstract_text}

Tasks:
1. Identify key entities (threats, vulnerabilities, controls, agents, systems)
2. Classify each entity into one of: Process, Material Entity, Quality, Role, Disposition
3. Extract relationships between entities with relation types
4. Propose subclass relationships to organize entities hierarchically

Output format: JSON with entities (name, type, BFO_category) and relations (subject, predicate, object).

Constraints:
- Align classifications with BFO categories where possible
- Use MITRE ATLAS taxonomy terms when applicable
- Distinguish processes (occur over time) from continuants (endure through time)
"""
```

The LLM outputs structured JSON mapping entities to BFO categories, which is then validated against the existing ontology for consistency.[^5]

**Benefits for Evidence-Based Cybersecurity KGs**:[^1][^5]

- **Rapid Schema Expansion**: Ingest new research papers, automatically propose EKI schema refinements and new KDI categories[^1]
- **Competency Question Validation**: LLM checks whether induced schema elements enable answering target questions[^5]
- **Alignment with Standards**: Map extracted concepts to FedRAMP KSIs, MITRE ATLAS, NIST frameworks automatically[^1][^5]

**Limitations and Risks**:[^5]

- **Hallucination**: LLMs may generate plausible but incorrect concepts or relationships
- **Bias**: Training data biases propagate into induced schemas
- **Computational Cost**: Billion-node KGs require massive GPU resources[^5]
- **Human Oversight**: Automated induction must be validated by domain experts before production deployment[^5]


### SHACL Shape Extraction from Evolving Data

As knowledge graphs grow and schemas adapt, manually maintaining SHACL validation shapes becomes infeasible. Automated shape extraction algorithms learn constraints from data, then validate new data against inferred shapes.[^24][^25][^8]

**QSE (Quality Shapes Extraction): Production-Grade Shape Learning**[^25][^8]

QSE extracts SHACL shapes from very large RDF graphs (billions of triples) via statistical analysis and pattern mining:[^25][^8]

**Algorithm Overview**:[^25]

1. **Predicate Frequency Analysis**: Compute frequency of each predicate for each class
2. **Cardinality Inference**: Determine `sh:minCount`, `sh:maxCount` from observed instance patterns
3. **Datatype Inference**: Analyze literal values to infer `sh:datatype`, `sh:nodeKind`
4. **Range Inference**: Identify target classes for object properties via `sh:class`
5. **Shape Generation**: Construct SHACL `sh:NodeShape` and `sh:PropertyShape` definitions
6. **Parameterization**: Use thresholds to balance precision (strict shapes) vs. recall (permissive shapes)

**Acceleration for Evolving KGs**:[^8]

*Changeset-Based Optimization*: When a KG undergoes minor updates, QSE can process only the changeset (added/removed triples) rather than re-extracting shapes from the entire graph.[^8]

- **Viable when**: Changeset is small relative to full graph size (e.g., <1% of triples changed)
- **Performance Gain**: 10-100× faster than full re-extraction[^8]
- **Limitation**: Large-scale schema changes require full re-extraction[^8]

*SPARQL-Based Shape Verification*: For subsequent versions, verify existing shapes via SPARQL queries rather than re-extracting:[^8]

```sparql
# Check if shape constraint still holds in new graph version
SELECT ?targetClass (COUNT(?instance) AS ?violationCount)
WHERE {
    ?instance a ?targetClass .
    FILTER NOT EXISTS {
        ?instance ?predicate ?value .
        # Check if required property is present
    }
}
GROUP BY ?targetClass
HAVING (?violationCount > 0)
```

If violations detected, re-extract shapes for affected classes.[^8]

**LLM-Augmented ShEx Generation**[^6]

Recent work combines LLM reasoning with graph structure analysis to generate Shape Expressions (ShEx, an alternative to SHACL):[^6]

**Pipeline**:[^6]

1. **Local Context Extraction**: For each class, sample representative instances and their immediate neighborhoods
2. **Global Structure Analysis**: Compute graph-wide statistics (predicate frequency, value distributions)
3. **LLM Synthesis**: Feed local + global context to LLM with prompt requesting ShEx constraint definitions
4. **Validation Metrics**: Evaluate generated shapes against ground truth using:
    - **Normalized Graph Edit Distance (NGED)**: Structural similarity between generated and gold-standard shapes
    - **Macro-F1 on Constraint Matches**: Precision/recall on individual constraint elements

**Example Generated ShEx Shape**:[^6]

```shex
# ShEx shape for EvidenceKnowledgeItem (LLM-generated)
:EvidenceKnowledgeItemShape {
    a [ cybersec:EvidenceKnowledgeItem ] ;
    cybersec:claimText xsd:string ;
    cybersec:confidenceScore xsd:float ;
    cybersec:derivedFrom @:DataItemShape+ ;
    prov:wasAttributedTo @:AgentShape ;
    dct:created xsd:dateTime ;
    cybersec:classifiedUnderKDI @:KDIConceptShape* ;
}
```

**Accuracy**: Under relaxed matching criteria (allowing datatype substitutions), LLM-generated shapes achieve >90% validity against ground truth. Exact matching (strict datatype, cardinality) yields lower accuracy, indicating room for improvement.[^6]

**Integration with Evidence-Based KG Workflow**:[^6][^8][^1]

1. **Initial Deployment**: Manually define core SHACL shapes for EKI, DataItem, KDI based on competency questions[^1]
2. **Incremental Extraction**: As new data ingested, run QSE quarterly to learn constraints from actual instance data[^8]
3. **Validation and Refinement**: Human experts review extracted shapes, adjust thresholds, merge with manually-defined constraints[^8]
4. **Continuous Validation**: Validate new data at ingestion time against evolving shape set; reject or flag violations[^8][^1]
5. **Schema Evolution Trigger**: When validation violations exceed threshold, propose schema changes (new properties, relaxed cardinalities)[^1]

This feedback loop ensures schemas remain synchronized with data reality while maintaining validation rigor.[^8][^1]

***

## Part III: Migration Strategies and Deprecation Management

### Deprecation Windows and Lifecycle Management

Removing ontology elements without disrupting dependent systems requires structured deprecation processes.[^12][^11]

**Standard Deprecation Timeline**:[^11][^12]


| Phase | Duration | Actions |
| :-- | :-- | :-- |
| **Announcement** | 0-1 month | Publish deprecation notice in change log, documentation, and API release notes[^4][^11] |
| **Deprecation Period** | 9-12 months | Mark elements `owl:deprecated true`; issue warnings in validation reports; provide migration guidance[^11][^12] |
| **Sunset Warning** | 1-2 months before removal | Final notice to users; automated tools flag usage of deprecated elements in codebases[^11] |
| **Removal** | Major version increment | Delete deprecated elements; release migration scripts; maintain old version endpoints[^4][^11] |

**Deprecation Metadata**:[^11]

```turtle
cybersec:legacyThreatSeverity a owl:DatatypeProperty ;
    rdfs:domain cybersec:Threat ;
    rdfs:range xsd:string ;
    owl:deprecated true ;
    cybersec:deprecatedInVersion "2.1.0" ;
    cybersec:removalPlannedInVersion "3.0.0" ;
    cybersec:replacedBy cybersec:cvssScore ;
    rdfs:comment "DEPRECATED: Use cybersec:cvssScore (float CVSS 3.1 score) instead of textual severity. Removal planned for v3.0.0 (estimated Q3 2026)." ;
    dct:modified "2026-01-16"^^xsd:date .
```

Explicit metadata enables automated tools to detect deprecated usage and suggest replacements.[^11]

**Rollback and Revert Capabilities**[^11]

Maintain ability to revert ontology changes if unintended consequences discovered:[^11]

- **Version Control**: Use Git/GitLab for ontology files; tag releases with version numbers[^11]
- **Revert Commits**: `git revert` to undo specific changes while preserving history[^11]
- **Branching Strategy**: Maintain stable release branches alongside development branches[^11]

```bash
# Git workflow for ontology versioning
git tag v2.1.0  # Tag release
git checkout -b hotfix/v2.1.1  # Create hotfix branch
# Make corrections
git commit -m "Fix: Correct domain/range on classifiedUnderKDI"
git tag v2.1.1  # Tag hotfix release
```


### Migration Assistants and Tooling

**Automated Migration Recommendations**[^26]

Enterprise ontology management platforms (e.g., Palantir Ontology Manager, TopBraid EDG) provide migration assistants that analyze ontology changes and recommend resource placement:[^26]

**Features**:[^26]

- **Strong Recommendations**: Preselected based on usage patterns, permissions, and dependency analysis[^26]
- **Weak Suggestions**: Flagged for manual review when confidence is low[^26]
- **Preview**: Show current vs. target state before committing migration[^26]
- **Bulk Operations**: Migrate multiple related resources together to preserve dependencies[^26]

**Manual Migration Options**:[^16]

For organizations without automated assistants, provide manual migration utilities:

**RDF Transformation Scripts**:

```sparql
# SPARQL UPDATE to migrate deprecated property to replacement
PREFIX cybersec: <https://cybersec.example.org/ontology/>

DELETE { ?threat cybersec:legacyThreatSeverity ?severity }
INSERT { 
    ?threat cybersec:cvssScore ?cvssScore .
}
WHERE {
    ?threat a cybersec:Threat ;
            cybersec:legacyThreatSeverity ?severity .
    
    # Map textual severity to CVSS score (approximate)
    BIND(
        IF(?severity = "Critical", 9.5,
        IF(?severity = "High", 7.5,
        IF(?severity = "Medium", 5.0,
        IF(?severity = "Low", 2.5, 0.0))))
        AS ?cvssScore
    )
}
```

**Property Graph Migration Scripts**:

```cypher
// Cypher migration for Neo4j/FalkorDB
MATCH (threat:Threat)
WHERE threat.legacyThreatSeverity IS NOT NULL
SET threat.cvssScore = 
    CASE threat.legacyThreatSeverity
        WHEN "Critical" THEN 9.5
        WHEN "High" THEN 7.5
        WHEN "Medium" THEN 5.0
        WHEN "Low" THEN 2.5
        ELSE 0.0
    END
REMOVE threat.legacyThreatSeverity
```

**Validation After Migration**:[^8][^1]

```sparql
# SPARQL query to verify migration completeness
SELECT ?threat
WHERE {
    ?threat a cybersec:Threat .
    FILTER NOT EXISTS { ?threat cybersec:cvssScore ?score }
}
# Should return 0 results if migration successful
```

Run SHACL validation against migrated data to ensure conformance with new shapes.[^1][^8]

### Versioned Endpoints and Multi-Version Support

**Challenge**: Applications may require different ontology versions during migration periods.[^4]

**Solution**: Expose multiple versioned endpoints, allowing gradual migration without forced upgrades.[^4]

**Ontology IRI Pattern**:[^10][^4]

```
# Version-independent IRI (always resolves to latest)
https://cybersec.example.org/ontology/

# Version-specific IRIs (stable, never change)
https://cybersec.example.org/ontology/v2.0.0
https://cybersec.example.org/ontology/v2.1.0
https://cybersec.example.org/ontology/v3.0.0
```

**SPARQL Endpoint Versioning**:[^1]

```
# Default endpoint (latest version)
https://api.cybersec.example.org/sparql

# Versioned endpoints
https://api.cybersec.example.org/v2/sparql  # Major version 2.x
https://api.cybersec.example.org/v3/sparql  # Major version 3.x
```

Applications specify desired version in API calls:

```bash
# Query v2 endpoint during migration
curl -X POST https://api.cybersec.example.org/v2/sparql \
  -H "Content-Type: application/sparql-query" \
  -d "SELECT ?eki ?claim WHERE { ?eki a cybersec:EvidenceKnowledgeItem ; cybersec:claimText ?claim }"
```

**Deprecation of Old Endpoints**:[^4][^11]

- Announce deprecation 12 months before removal[^12][^11]
- Return `X-API-Deprecated: true` header with sunset date[^11]
- Provide migration documentation in response headers[^11]
- After sunset, return HTTP 410 Gone with pointer to current endpoint[^4]

**Version Negotiation** (Advanced):[^4]

```http
GET /ontology/cybersec
Accept: application/rdf+xml
X-Ontology-Version: 2.1.0

HTTP/1.1 200 OK
Content-Type: application/rdf+xml
X-Ontology-Version: 2.1.0
X-Latest-Version: 2.1.0
```

Clients request specific versions via headers; server returns requested version if available, otherwise returns closest compatible version with version mismatch warning.[^4]

***

## Part IV: Reproducibility and Provenance of Schema Changes

### Data Versioning for Reproducible Analyses

Scientific reproducibility requires ability to reconstruct exact graph state at time of analysis.[^18][^19]

**Requirements**:[^18]

1. **Version Data**: Snapshot or reference to exact dataset used[^18][^19]
2. **Version Schema**: Link data snapshot to ontology version[^18][^1]
3. **Version Code**: Record query/analysis scripts with version tags[^18]
4. **Version Dependencies**: Capture reasoner versions, SHACL validators, RDF libraries[^18]

**Implementation Pattern**:[^19][^18]

```yaml
# Analysis reproducibility manifest
analysis_id: "atlas-threat-coverage-2026-q1"
date: "2026-01-16"
data_snapshot:
  rdf_dump: "s3://cyberkg-snapshots/2026-01-16-rdf-v2.1.0.nq.gz"
  checksum_sha256: "a3f5b8c9d2e1..."
schema_version:
  ontology: "https://cybersec.example.org/ontology/v2.1.0"
  shacl_shapes: "https://cybersec.example.org/shapes/v2.1.0"
code_version:
  git_repo: "https://github.com/org/cyberkg-analysis"
  git_commit: "7d8f3a2c"
  analysis_script: "scripts/threat_coverage_analysis.sparql"
dependencies:
  rdflib_version: "7.0.0"
  owlrl_version: "6.0.2"
  hermit_version: "1.4.5"
  python_version: "3.11"
results:
  output_file: "results/atlas-threat-coverage-2026-q1.csv"
  checksum_sha256: "c9d2e1f8b3a7..."
```

Storing this manifest alongside results enables exact reproduction months or years later.[^19][^18]

**Restoration Workflow**:[^19][^18]

```bash
# Reproduce analysis from manifest
aws s3 cp s3://cyberkg-snapshots/2026-01-16-rdf-v2.1.0.nq.gz data/
sha256sum -c manifest.checksums  # Verify data integrity
git checkout 7d8f3a2c  # Restore analysis code
docker build -t analysis:2026-q1 --build-arg PYTHON_VERSION=3.11 .  # Restore environment
docker run analysis:2026-q1 scripts/threat_coverage_analysis.sparql
```


### Provenance of Schema Evolution Decisions

Document *why* schema changes were made, not just *what* changed.[^4][^7]

**Change Log Best Practices**:[^4][^7]

```markdown
# Changelog v2.1.0 (2026-01-16)

## Added
- **15 new MITRE ATLAS techniques** for LLM/GenAI threats
  - *Rationale*: MITRE updated ATLAS framework in Dec 2025 with generative AI attack patterns
  - *Impacted competency questions*: CQ-3 (Which ATLAS techniques are addressed by which controls?)
  - *Evidence*: [ATLAS v2.0 Release Notes](https://atlas.mitre.org/changelog/v2.0)

- **cybersec:exploitComplexity property** (float [0.0, 1.0])
  - *Rationale*: Multiple EKIs from recent research [paper:arxiv-2504-00441, paper:usenix-sec-2024] reference exploit difficulty; needed structured representation
  - *BFO grounding*: Models a Quality of Vulnerability (disposition to be exploited)
  - *SHACL shape*: Added cardinality constraints (sh:minCount 0, sh:maxCount 1) to shapes v2.1.0

## Changed
- **Refined PROV-O integration**: added cybersec:extractedBy for agent attribution
  - *Rationale*: Support distinction between human evaluators and AI extraction agents
  - *Backward compatibility*: Additive change, existing data valid

## Deprecated
- **cybersec:EvidenceFragment** → **cybersec:hasEvidenceFragment**
  - *Rationale*: Naming convention alignment (properties should be verb-like)
  - *Migration path*: Equivalence axiom maintains compatibility until v3.0.0
  - *Deprecation timeline*: Will be removed in v3.0.0 (estimated Q3 2026)

## Fixed
- **Corrected domain/range on cybersec:classifiedUnderKDI**
  - *Issue*: Range incorrectly specified as cybersec:KDI (internal class); should be skos:Concept
  - *Impact*: Minor; reasoners handled via subclass inference, but explicit correction improves clarity
```

This structured format documents rationale, evidence, BFO alignment, and migration guidance.[^4][^7]

**Linking Schema Changes to Provenance**:[^7]

```turtle
# Provenance of schema change decision
:SchemaChange_v2.1.0_AddExploitComplexity a prov:Activity ;
    rdfs:label "Schema change: Add exploitComplexity property" ;
    prov:startedAtTime "2025-12-20T10:00:00Z"^^xsd:dateTime ;
    prov:endedAtTime "2026-01-10T15:00:00Z"^^xsd:dateTime ;
    prov:wasAssociatedWith :KnowledgeEngineer_Bob ;
    prov:used :Paper_arXiv_2504_00441 ,
              :Paper_USENIX_Sec_2024 ,
              :CompetencyQuestion_CQ7 ;
    cybersec:changeJustification "Multiple recent research papers quantify exploit difficulty; structured property needed for analysis queries" ;
    cybersec:resultedInOntologyVersion <https://cybersec.example.org/ontology/v2.1.0> .

:Paper_arXiv_2504_00441 a prov:Entity , cybersec:ResearchPaper ;
    dct:title "No Free Lunch with Guardrails" ;
    schema:url <https://arxiv.org/pdf/2504.00441.pdf> .
```

Schema changes become queryable provenance chains, supporting audits and rationale reconstruction.[^7]

***

## Part V: Practical Implementation for Evidence-Based Cybersecurity KG

### Version Control Workflow

**Git Repository Structure**:

```
cyberkg-ontology/
├── ontology/
│   ├── cybersec-core-v2.1.0.ttl
│   ├── bfo-import.ttl
│   ├── cco-import.ttl
│   └── prov-o-extensions.ttl
├── shapes/
│   ├── eki-shapes-v2.1.0.ttl
│   ├── kdi-shapes-v2.1.0.ttl
│   └── provenance-shapes-v2.1.0.ttl
├── property-graph-schema/
│   ├── neo4j-constraints-v2.1.0.cypher
│   └── falkordb-indexes-v2.1.0.redis
├── mappings/
│   ├── pg-to-rdf-v2.1.0.rml.ttl
│   └── rdb-to-rdf-v2.1.0.r2rml.ttl
├── migrations/
│   ├── 2.0-to-2.1/
│   │   ├── add-exploit-complexity.cypher
│   │   ├── add-atlas-techniques.sparql
│   │   └── migration-manifest.yaml
├── snapshots/
│   ├── 2026-01-16-rdf-v2.1.0.nq.gz
│   └── 2026-01-16-neo4j-v2.1.0.cypher.gz
├── docs/
│   ├── CHANGELOG.md
│   ├── MIGRATION_GUIDE_2.0_to_2.1.md
│   └── competency-questions-v2.1.0.md
└── version-manifest-v2.1.0.yaml
```

**Git Tagging for Releases**:

```bash
# Tag release with semantic version
git tag -a v2.1.0 -m "Release v2.1.0: Add ATLAS techniques, exploit complexity"

# Push tag to remote
git push origin v2.1.0

# Generate release notes from changelog
gh release create v2.1.0 --title "v2.1.0" --notes-file CHANGELOG.md \
  --attach snapshots/2026-01-16-rdf-v2.1.0.nq.gz \
  --attach version-manifest-v2.1.0.yaml
```


### Continuous Integration for Schema Validation

**Automated Testing on Every Commit**:

```yaml
# .github/workflows/ontology-validation.yml
name: Ontology Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate RDF Syntax
        run: |
          rapper -i turtle -o ntriples ontology/cybersec-core-v2.1.0.ttl > /dev/null
      
      - name: Check OWL Consistency with HermiT
        run: |
          java -jar hermit-reasoner.jar --check-consistency ontology/cybersec-core-v2.1.0.ttl
      
      - name: Validate SHACL Shapes
        run: |
          pyshacl -s shapes/eki-shapes-v2.1.0.ttl -df turtle ontology/cybersec-core-v2.1.0.ttl
      
      - name: Run Competency Question Tests
        run: |
          python tests/test_competency_questions.py
      
      - name: Check Semantic Versioning Compliance
        run: |
          python scripts/check_version_increment.py --prior v2.0.0 --current v2.1.0
```

This pipeline catches syntax errors, consistency violations, SHACL shape mismatches, and versioning mistakes before merge.[^1][^4]

### LLM-Assisted Schema Proposal Workflow

**Incremental Schema Growth Pipeline**:

1. **Trigger**: New research papers added to Data layer (e.g., 50 papers on novel LLM attacks)
2. **Extraction**: LLM-based EKI extraction identifies concepts not mapped to existing ontology
3. **Schema Proposal**: LLM generates candidate new classes/properties with BFO grounding
```python
# Pseudocode: LLM schema proposal
unmapped_concepts = extract_unmapped_concepts(new_ekis)
for concept in unmapped_concepts:
    proposal = llm.generate_schema_element(
        concept_name=concept,
        existing_ontology=load_ontology("v2.1.0"),
        bfo_alignment=True,
        examples=get_eki_examples(concept)
    )
    proposals.append(proposal)
```

4. **Validation**: Check proposals against competency questions
```python
for proposal in proposals:
    can_answer_cqs = validate_against_competency_questions(
        proposal, competency_questions
    )
    if can_answer_cqs:
        human_review_queue.add(proposal)
```

5. **Human Review**: Knowledge engineer reviews, refines, approves
6. **Integration**: Merge approved proposals into development branch
7. **Testing**: Run CI validation pipeline
8. **Release**: Tag minor version increment (v2.2.0)

### Monitoring Schema Drift

**Drift Detection Queries**:

```sparql
# Detect EKIs with properties not defined in current schema
SELECT DISTINCT ?predicate (COUNT(?eki) AS ?instanceCount)
WHERE {
    ?eki a cybersec:EvidenceKnowledgeItem ;
         ?predicate ?value .
    
    FILTER NOT EXISTS {
        ?predicate a ?propertyType .
        FILTER(?propertyType IN (owl:DatatypeProperty, owl:ObjectProperty, owl:AnnotationProperty))
    }
}
GROUP BY ?predicate
ORDER BY DESC(?instanceCount)
```

If this query returns results, data is using predicates not declared in the ontology—signal for horizontal expansion.[^1]

**SHACL Validation Reports as Drift Signals**:

Run weekly SHACL validation against production data:

```bash
# Weekly validation job
pyshacl -s shapes/eki-shapes-v2.1.0.ttl \
        -df turtle \
        -f human \
        production-data-2026-01-23.nq > validation-report-2026-01-23.txt
```

Increasing violation rates signal schema drift:[^8]

```
Week 1: 12 violations
Week 2: 18 violations
Week 3: 45 violations  # ALERT: Schema drift detected
```

Trigger SHACL shape re-extraction or manual schema review.[^8]

***

## Conclusion: Adaptive Ontology Governance

Schema evolution is not an engineering afterthought but a core strategic capability for knowledge graph longevity. As AI-cybersecurity domains evolve at unprecedented pace—new threats emerge weekly, standards update quarterly, research findings accumulate daily—our ontology must adapt without sacrificing stability or breaking dependent systems.[^2][^3][^17][^1][^7]

The framework presented integrates complementary best practices:

**Semantic Versioning** communicates impact clearly (major.minor.patch), enabling informed migration decisions. **BFO-grounded incremental growth** (horizontal and vertical expansion) ensures domain-specific changes remain interoperable with the broader ontology ecosystem. **Automated schema induction** via LLMs accelerates adaptation while reducing manual engineering overhead. **SHACL shape extraction** keeps validation constraints synchronized with evolving data reality. **Hybrid schema+data versioning** with manifests enables reproducible analyses and rollback capabilities.[^25][^6][^18][^17][^5][^8][^4][^1][^7]

By anchoring evolution in BFO principles, documenting change rationale with provenance chains, and validating every modification against competency questions, organizations achieve the trifecta: **agility** (rapid schema updates), **stability** (predictable backward compatibility), and **rigor** (consistency checking via OWL reasoning and SHACL validation).[^9][^1][^7]

Our evidence-based cybersecurity knowledge graph exemplifies this approach: FedRAMP KSIs and MITRE ATLAS techniques require frequent updates as threats evolve; EKI schemas must adapt as research methodologies change; operational views must incorporate new controls and mitigations in real-time. The versioning framework presented ensures these changes strengthen rather than destabilize the knowledge system, positioning our organizations to maintain trustworthy, mission-critical AI-ready knowledge graphs at enterprise scale.

***

## References

Guide_Engineering_Basic_SchemaDesign.md — Ontology and schema design for evidence-centric KG[^1]
prompt_context.txt — Four-layer evidence-based cybersecurity KG context[^27]
https://data.world/blog/owl-semantic-layers/ — OWL reasoning capabilities[^13]
http://www.cs.ox.ac.uk/people/boris.motik/pubs/hmw12HermiT.pdf — HermiT OWL Reasoner[^14]
https://enterprise-knowledge.com/top-5-tips-for-managing-and-versioning-an-ontology/ — Top 5 ontology versioning tips[^4]
https://openproceedings.org/2020/conf/edbt/paper_T4.pdf — NoSQL schema evolution and data migration[^15]
https://ceur-ws.org/Vol-201/03.pdf — Classification of ontology change[^2]
https://www.cs.vu.nl/~mcaklein/presentations/2001-07-31-SWWS-Stanford.pdf — Ontology versioning on Semantic Web[^10]
https://files.ifi.uzh.ch/ddis/iswc_archive/iswc/ih/SWWS-2001/program/full/paper56a.pdf — Ontology versioning framework[^3]
https://web.stanford.edu/class/cs520/2020/notes/How_To_Evolve_A_Knowledge_Graph.html — How to evolve a knowledge graph[^20]
https://repositum.tuwien.at/bitstream/20.500.12708/208798/1/Puermayr Eva - 2025 - SHACL Shapes Extraction for ... — SHACL shapes extraction for evolving KGs[^8]
https://edgedelta.com/company/knowledge-center/horizontal-vs-vertical-scaling-2 — Horizontal vs vertical scaling[^21]
https://www.emergentmind.com/topics/schema-adaptable-knowledge-graph-construction — Schema-adaptable knowledge graphs[^5]
https://relweb.cs.aau.dk/qse/shactor/ — SHACTOR shapes extraction system[^24]
https://multishoring.com/blog/horizontal-vs-vertical-scaling/ — Horizontal vs vertical scaling strategies[^22]
https://arxiv.org/abs/2506.04512 — Schema generation for large KGs using LLMs[^6]
https://www.vldb.org/pvldb/vol16/p1023-rabbani.pdf — Extraction of validating shapes from very large KGs[^25]
https://www.datacamp.com/blog/horizontal-vs-vertical-scaling — Horizontal vs vertical scaling developer's guide[^28]
https://dl.acm.org/doi/10.1145/3631700.3665234 — Zero-shot knowledge graph building[^23]
https://www.drivewingrow.com/how-to-manage-knowledge-graph-evolution-and-versioning/ — Managing KG evolution and versioning[^17]
https://www.palantir.com/docs/foundry/ontology-manager/migrate-to-project-based-permissions — Migrate to project-based permissions[^26]
https://ontology.buffalo.edu/smith/articles/fois2014.pdf — Versioning method for tracking BFO changes[^7]
https://www.dailydoseofds.com/mlops-crash-course-part-3/ — Reproducibility and versioning in ML[^18]
https://palantir.com/docs/foundry/ontologies/ontology-migration/ — Migrating between ontologies[^16]
https://scibite.com/solutions/ontology-management/centree/ — CENtree ontology management[^11]
https://lakefs.io/data-version-control/dvc-best-practices/ — Data version control best practices[^19]
https://seljaseppala.wordpress.com/2014/10/02/applying-the-realism-based-ontology-versioning-method-for-tracking-changes-in-the-... — Applying RBOV to BFO[^9]
https://www.linkedin.com/posts/stuart-winter-tear_ontologies-are-like-a-secret-sauce-that-supercharge-activity-73024947758767267... — Deprecation windows in enterprise AI[^12]

***

**Document Version**: 1.0
**Created**: January 16, 2026
**License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
<span style="display:none">[^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39][^40][^41][^42][^43][^44][^45][^46][^47][^48][^49][^50][^51][^52]</span>

<div align="center">⁂</div>

[^1]: Guide_Engineering_Basic_SchemaDesign.md

[^2]: https://ceur-ws.org/Vol-201/03.pdf

[^3]: https://files.ifi.uzh.ch/ddis/iswc_archive/iswc/ih/SWWS-2001/program/full/paper56a.pdf

[^4]: https://enterprise-knowledge.com/top-5-tips-for-managing-and-versioning-an-ontology/

[^5]: https://www.emergentmind.com/topics/schema-adaptable-knowledge-graph-construction

[^6]: https://arxiv.org/abs/2506.04512

[^7]: https://ontology.buffalo.edu/smith/articles/fois2014.pdf

[^8]: https://repositum.tuwien.at/bitstream/20.500.12708/208798/1/Puermayr Eva - 2025 - SHACL Shapes Extraction for Evolving Knowledge Graphs.pdf

[^9]: https://seljaseppala.wordpress.com/2014/10/02/applying-the-realism-based-ontology-versioning-method-for-tracking-changes-in-the-basic-formal-ontology/

[^10]: https://www.cs.vu.nl/~mcaklein/presentations/2001-07-31-SWWS-Stanford.pdf

[^11]: https://scibite.com/solutions/ontology-management/centree/

[^12]: https://www.linkedin.com/posts/stuart-winter-tear_ontologies-are-like-a-secret-sauce-that-supercharge-activity-7302494775876726785-VjDU

[^13]: https://data.world/blog/owl-semantic-layers/

[^14]: http://www.cs.ox.ac.uk/people/boris.motik/pubs/hmw12HermiT.pdf

[^15]: https://openproceedings.org/2020/conf/edbt/paper_T4.pdf

[^16]: https://palantir.com/docs/foundry/ontologies/ontology-migration/

[^17]: https://www.drivewingrow.com/how-to-manage-knowledge-graph-evolution-and-versioning/

[^18]: https://www.dailydoseofds.com/mlops-crash-course-part-3/

[^19]: https://lakefs.io/data-version-control/dvc-best-practices/

[^20]: https://web.stanford.edu/class/cs520/2020/notes/How_To_Evolve_A_Knowledge_Graph.html

[^21]: https://edgedelta.com/company/knowledge-center/horizontal-vs-vertical-scaling-2

[^22]: https://multishoring.com/blog/horizontal-vs-vertical-scaling/

[^23]: https://dl.acm.org/doi/10.1145/3631700.3665234

[^24]: https://relweb.cs.aau.dk/qse/shactor/

[^25]: https://www.vldb.org/pvldb/vol16/p1023-rabbani.pdf

[^26]: https://www.palantir.com/docs/foundry/ontology-manager/migrate-to-project-based-permissions

[^27]: prompt_context.txt

[^28]: https://www.datacamp.com/blog/horizontal-vs-vertical-scaling

[^29]: 2008.07863v1_metadata.json

[^30]: 2504.00441_metadata.txt

[^31]: README.md

[^32]: https://dl.acm.org/doi/10.5555/2956602.2956610

[^33]: https://www.falkordb.com/blog/relational-database-to-graph-database-2/

[^34]: https://kinde.com/learn/ai-for-software-engineering/using-ai-for-your-database/ai-powered-database-schema-evolution-from-legacy-to-modern-with-zero-downtime/

[^35]: http://art.uniroma2.it/publications/docs/2017_IJMSO_ChangeManagementValidationRDF.pdf

[^36]: https://eprints.soton.ac.uk/263067/1/9month.pdf

[^37]: https://gitlab.com/gitlab-com/content-sites/handbook/-/blob/ce8a841fde2c12a9534fa42e45c2f9759b6ebe42/content/handbook/engineering/architecture/design-documents/gitlab_knowledge_graph/schema_management.md

[^38]: https://www.w3.org/TR/owl2-rdf-based-semantics/

[^39]: https://lists.w3.org/Archives/Public/semantic-web/2017Jan/0103.html

[^40]: https://www.w3.org/2007/OWL/draft/ED-owl2-rdf-based-semantics-20090521/diff-from-20090421

[^41]: https://www.schemaapp.com/schema-markup/how-to-leverage-your-content-knowledge-graph-for-llms-like-chatgpt/

[^42]: https://zenodo.org/records/7598613

[^43]: https://www.pingcap.com/horizontal-scaling-vs-vertical-scaling/

[^44]: https://www.reddit.com/r/LLMDevs/comments/1plawrv/build_a_selfupdating_knowledge_graph_from/

[^45]: https://lirias.kuleuven.be/retrieve/f4363b8e-bb85-4ff2-a3d1-180cd0089198

[^46]: https://fullscale.io/blog/vertical-vs-horizontal-scaling/

[^47]: https://www.sciencedirect.com/science/article/pii/S1532046415001069

[^48]: https://www.nature.com/articles/s41597-022-01352-z

[^49]: https://www.semanticarts.com/wp-content/uploads/2025/01/20241024-BFO-and-gist-Article.pdf

[^50]: https://biocypher.org/BioCypher/learn/explanation/architecture-migration/

[^51]: https://www.meegle.com/en_us/topics/knowledge-graphs/knowledge-graph-versioning

[^52]: https://ceur-ws.org/Vol-3603/Paper14.pdf

