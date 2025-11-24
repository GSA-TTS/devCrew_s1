# Knowledge Graph Management Platform

A comprehensive knowledge graph management platform for the devCrew_s1 project, featuring entity extraction, graph building, semantic search, RAG integration, and advanced analytics.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Configuration](#configuration)
6. [Knowledge Extraction](#knowledge-extraction)
7. [Graph Building](#graph-building)
8. [Semantic Search](#semantic-search)
9. [RAG Integration](#rag-integration)
10. [Graph Querying](#graph-querying)
11. [Graph Analysis](#graph-analysis)
12. [CLI Reference](#cli-reference)
13. [Protocol Integration](#protocol-integration)
14. [Troubleshooting](#troubleshooting)
15. [API Reference](#api-reference)

## Overview

The Knowledge Graph Management Platform is a production-ready system for building, querying, and analyzing knowledge graphs in Neo4j. It integrates with the devCrew_s1 ecosystem to provide:

- **Entity Extraction**: Extract entities and relationships from text using spaCy and LLMs
- **Graph Building**: Create and manage Neo4j knowledge graphs with batch processing
- **Semantic Search**: FAISS-based vector search and hybrid search capabilities
- **RAG Integration**: Retrieval-Augmented Generation with LangChain and LlamaIndex
- **Advanced Querying**: Natural language to Cypher translation, graph traversal, path finding
- **Graph Analytics**: PageRank, centrality measures, community detection, graph metrics
- **CLI Interface**: Comprehensive command-line tools for all operations

## Features

### Core Capabilities

- **Multiple Extraction Methods**: spaCy NER, LLM-based extraction, hybrid approaches
- **Flexible Graph Building**: Batch imports, schema management, constraints and indexes
- **Intelligent Search**: Vector similarity, keyword search, hybrid ranking
- **RAG-Enhanced QA**: Context-aware question answering with graph knowledge
- **Natural Language Queries**: Automatic translation from NL to Cypher queries
- **Graph Analytics**: Comprehensive analysis tools including centrality and communities
- **Production Ready**: Error handling, logging, validation, and testing

### Integration Points

- **Neo4j**: Native graph database integration
- **OpenAI/Anthropic**: LLM integration for extraction and query translation
- **LangChain/LlamaIndex**: RAG framework support
- **FAISS**: High-performance vector search
- **NetworkX**: Graph algorithms and analysis

## Installation

### Prerequisites

- Python 3.8+
- Neo4j 4.0+ (local or AuraDB)
- OpenAI API key (for LLM features)

### Neo4j Setup

#### Option 1: Docker (Recommended)

```bash
# Run Neo4j in Docker
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS='["apoc"]' \
    neo4j:latest
```

#### Option 2: Neo4j Desktop

1. Download from https://neo4j.com/download/
2. Create a new database
3. Start the database
4. Note the bolt URI and credentials

#### Option 3: Neo4j AuraDB (Cloud)

1. Sign up at https://neo4j.com/cloud/aura/
2. Create a free instance
3. Save connection credentials

### Python Dependencies

```bash
# Navigate to devCrew_s1 repository
cd /path/to/devCrew_s1/tools/knowledge_graph_management

# Install dependencies
pip install -r requirements.txt

# Install spaCy models
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg
```

### Requirements File

Create `requirements.txt`:

```
neo4j==5.14.0
pydantic==2.5.0
openai==1.3.0
networkx==3.2.1
python-louvain==0.16
sentence-transformers==2.2.2
faiss-cpu==1.7.4
spacy==3.7.2
langchain==0.1.0
llama-index==0.9.0
click==8.1.7
rich==13.7.0
pyyaml==6.0.1
pytest==7.4.3
pytest-mock==3.12.0
responses==0.24.1
```

### Environment Variables

Create `.env` file:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Anthropic
ANTHROPIC_API_KEY=your-anthropic-key
```

## Quick Start

### 1. Extract Entities from Documents

```python
from knowledge_extractor import KnowledgeExtractor, ExtractorConfig

# Configure extractor
config = ExtractorConfig(
    spacy_model="en_core_web_sm",
    llm_model="gpt-4",
    enable_llm=True
)

extractor = KnowledgeExtractor(config)

# Extract from text
text = """
John Smith works at Google as a software engineer in Mountain View, California.
He specializes in machine learning and natural language processing.
Google was founded by Larry Page and Sergey Brin in 1998.
"""

entities = extractor.extract_entities_spacy(text)
relationships = extractor.extract_relationships(text)

print(f"Found {len(entities)} entities and {len(relationships)} relationships")
```

### 2. Build Knowledge Graph

```python
from graph_builder import GraphBuilder, BuilderConfig

# Configure builder
config = BuilderConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    batch_size=500
)

builder = GraphBuilder(config)

# Create schema
builder.create_schema(entities, relationships)

# Import entities and relationships
builder.create_entities_batch(entities)
builder.create_relationships_batch(relationships)

# Get statistics
stats = builder.get_statistics()
print(f"Graph contains {stats['node_count']} nodes and {stats['relationship_count']} relationships")
```

### 3. Query the Graph

```python
from graph_query import GraphQueryEngine, QueryConfig, CypherQuery

# Configure query engine
config = QueryConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    enable_nl_translation=True,
    llm_model="gpt-4"
)

engine = GraphQueryEngine(config)

# Natural language query
result = engine.execute_natural_language("Find all people who work at Google")
print(f"Found {len(result.records)} results")

# Direct Cypher query
query = CypherQuery(query="MATCH (p:Person)-[:WORKS_AT]->(o:Organization) RETURN p, o LIMIT 10")
result = engine.execute_cypher(query)
```

### 4. Semantic Search

```python
from semantic_search import SemanticSearch, SearchConfig

# Configure search
config = SearchConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)

search = SemanticSearch(config)

# Build FAISS index
search.build_faiss_index()

# Hybrid search (vector + keyword)
results = search.hybrid_search("artificial intelligence researchers", top_k=10)

for i, result in enumerate(results, 1):
    print(f"{i}. {result['text']} (score: {result['score']:.3f})")
```

### 5. RAG Question Answering

```python
from rag_integrator import RAGIntegrator, RAGConfig

# Configure RAG
config = RAGConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    llm_model="gpt-4",
    framework="langchain"
)

rag = RAGIntegrator(config)

# Ask question
result = rag.answer_question("What is the relationship between AI and robotics?")

print(f"Answer: {result['answer']}")
print(f"\nContext used:")
for ctx in result['context']:
    print(f"- {ctx}")
```

### 6. Graph Analysis

```python
from graph_analyzer import GraphAnalyzer, AnalyzerConfig

# Configure analyzer
config = AnalyzerConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password")
)

analyzer = GraphAnalyzer(config)

# PageRank
pagerank = analyzer.calculate_pagerank(top_k=10)
print("Top 10 influential nodes:")
for node_id, score in pagerank.items():
    print(f"  {node_id}: {score:.6f}")

# Community detection
communities = analyzer.detect_communities()
print(f"\nDetected {communities.num_communities} communities")
print(f"Modularity: {communities.modularity:.3f}")

# Graph metrics
metrics = analyzer.calculate_graph_metrics()
print(f"\nGraph Metrics:")
print(f"  Nodes: {metrics.node_count}")
print(f"  Edges: {metrics.edge_count}")
print(f"  Density: {metrics.density:.4f}")
print(f"  Avg Degree: {metrics.avg_degree:.2f}")
```

## Configuration

### ExtractorConfig

Configuration for knowledge extraction:

```python
from knowledge_extractor import ExtractorConfig

config = ExtractorConfig(
    spacy_model="en_core_web_sm",      # spaCy model for NER
    llm_model="gpt-4",                  # LLM for extraction
    llm_api_key="sk-...",               # OpenAI API key
    enable_llm=True,                    # Enable LLM extraction
    entity_types=["PERSON", "ORG"],     # Entity types to extract
    confidence_threshold=0.7,           # Minimum confidence score
    batch_size=10                       # Batch size for processing
)
```

### BuilderConfig

Configuration for graph building:

```python
from graph_builder import BuilderConfig

config = BuilderConfig(
    neo4j_uri="bolt://localhost:7687",  # Neo4j connection URI
    auth=("neo4j", "password"),         # Authentication credentials
    batch_size=500,                     # Batch size for imports
    create_indexes=True,                # Automatically create indexes
    create_constraints=True,            # Create uniqueness constraints
    merge_duplicates=True               # Merge duplicate nodes
)
```

### QueryConfig

Configuration for graph querying:

```python
from graph_query import QueryConfig

config = QueryConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    enable_nl_translation=True,         # Enable NL to Cypher
    llm_model="gpt-4",                  # Model for translation
    llm_api_key="sk-...",
    max_retries=3,                      # Query retry attempts
    timeout=30.0                        # Query timeout (seconds)
)
```

### SearchConfig

Configuration for semantic search:

```python
from semantic_search import SearchConfig

config = SearchConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    index_path="./faiss_index",         # FAISS index location
    cache_embeddings=True,              # Cache entity embeddings
    vector_dimensions=384               # Embedding dimensions
)
```

### AnalyzerConfig

Configuration for graph analysis:

```python
from graph_analyzer import AnalyzerConfig

config = AnalyzerConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    cache_results=True,                 # Cache NetworkX graphs
    max_cache_size=5                    # Maximum cached graphs
)
```

### RAGConfig

Configuration for RAG integration:

```python
from rag_integrator import RAGConfig

config = RAGConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    llm_model="gpt-4",
    llm_api_key="sk-...",
    framework="langchain",              # or "llamaindex"
    context_window=3,                   # Nodes to include in context
    temperature=0.7,                    # LLM temperature
    max_tokens=500                      # Maximum response tokens
)
```

## Knowledge Extraction

### spaCy NER Extraction

Extract entities using spaCy's Named Entity Recognition:

```python
from knowledge_extractor import KnowledgeExtractor, ExtractorConfig

config = ExtractorConfig(spacy_model="en_core_web_lg")
extractor = KnowledgeExtractor(config)

text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."

# Extract all entity types
entities = extractor.extract_entities_spacy(text)

# Extract specific types
entities = extractor.extract_entities_spacy(
    text,
    entity_types=["PERSON", "ORG", "GPE"]
)

# Output format
for entity in entities:
    print(f"{entity['text']} ({entity['label']}) - confidence: {entity['confidence']}")
```

### LLM-Based Extraction

Use LLMs for more accurate entity and relationship extraction:

```python
config = ExtractorConfig(
    llm_model="gpt-4",
    llm_api_key="sk-...",
    enable_llm=True
)

extractor = KnowledgeExtractor(config)

# Extract entities with LLM
entities = extractor.extract_entities_llm(text)

# Extract relationships
relationships = extractor.extract_relationships(text)

# Extract complete triples (subject-predicate-object)
triples = extractor.extract_triples(text)

for triple in triples:
    print(f"{triple['subject']} --[{triple['predicate']}]--> {triple['object']}")
```

### Hybrid Extraction

Combine spaCy and LLM for best results:

```python
# spaCy for fast entity detection
spacy_entities = extractor.extract_entities_spacy(text)

# LLM for relationships and complex patterns
llm_relationships = extractor.extract_relationships(text)

# Merge and deduplicate
all_entities = extractor.deduplicate_entities(spacy_entities + llm_entities)
```

### Batch Processing

Process multiple documents efficiently:

```python
documents = [
    {"id": "doc1", "text": "..."},
    {"id": "doc2", "text": "..."},
    {"id": "doc3", "text": "..."}
]

results = extractor.process_batch(documents, batch_size=10)

for result in results:
    print(f"Document {result['id']}: {len(result['entities'])} entities")
```

### File Processing

Extract from various file formats:

```python
# Process single file
result = extractor.process_file("document.txt")

# Process directory
from pathlib import Path

docs_dir = Path("./documents")
for file_path in docs_dir.glob("**/*.txt"):
    result = extractor.process_file(file_path)
    print(f"Processed {file_path.name}")
```

## Graph Building

### Schema Creation

Define graph schema before importing data:

```python
from graph_builder import GraphBuilder, BuilderConfig

config = BuilderConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password")
)

builder = GraphBuilder(config)

# Create schema from entities and relationships
builder.create_schema(entities, relationships)

# Manually create indexes
builder.create_index("Person", "id")
builder.create_index("Organization", "name")

# Create constraints
builder.create_unique_constraint("Person", "id")
builder.create_unique_constraint("Organization", "id")
```

### Node Creation

Create nodes individually or in batches:

```python
# Single node
node = {
    "id": "person_1",
    "text": "John Smith",
    "label": "Person",
    "age": 30,
    "department": "Engineering"
}

builder.create_node(node)

# Batch creation (recommended for large datasets)
nodes = [
    {"id": "person_1", "text": "John Smith", "label": "Person"},
    {"id": "person_2", "text": "Jane Doe", "label": "Person"},
    {"id": "org_1", "text": "Google", "label": "Organization"}
]

builder.create_entities_batch(nodes)
```

### Relationship Creation

Create relationships between nodes:

```python
# Single relationship
rel = {
    "source": "person_1",
    "target": "org_1",
    "type": "WORKS_AT",
    "since": 2020,
    "position": "Software Engineer"
}

builder.create_relationship(rel)

# Batch creation
relationships = [
    {"source": "person_1", "target": "org_1", "type": "WORKS_AT"},
    {"source": "person_2", "target": "org_1", "type": "WORKS_AT"},
    {"source": "org_1", "target": "gpe_1", "type": "LOCATED_IN"}
]

builder.create_relationships_batch(relationships)
```

### Merging Nodes

Create or update nodes (upsert):

```python
# Merge creates node if it doesn't exist, updates if it does
node = {
    "id": "person_1",
    "text": "John Smith",
    "label": "Person",
    "age": 31  # Updated age
}

builder.merge_node(node)
```

### Updating Properties

Update node properties:

```python
builder.update_node_properties(
    node_id="person_1",
    properties={"age": 32, "title": "Senior Engineer"}
)
```

### Batch Import Best Practices

For large-scale imports:

```python
# Use larger batch sizes
config = BuilderConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    batch_size=1000  # Process 1000 nodes at a time
)

builder = GraphBuilder(config)

# Import in stages
# 1. Create all nodes first
builder.create_entities_batch(all_entities)

# 2. Create relationships after nodes exist
builder.create_relationships_batch(all_relationships)

# 3. Create indexes after import for better performance
builder.create_index("Person", "name")
builder.create_index("Organization", "name")
```

### Graph Statistics

Get statistics about your graph:

```python
stats = builder.get_statistics()

print(f"Nodes: {stats['node_count']}")
print(f"Relationships: {stats['relationship_count']}")
print(f"Labels: {stats['label_counts']}")
print(f"Relationship Types: {stats['relationship_type_counts']}")
```

### Clearing Graph Data

Clear graph when needed:

```python
# Clear all data (use with caution!)
builder.clear_graph()

# Delete specific node
builder.delete_node("person_1")

# Delete nodes by label
builder.delete_nodes_by_label("Person")
```

## Semantic Search

### Building FAISS Index

Create vector index for fast similarity search:

```python
from semantic_search import SemanticSearch, SearchConfig

config = SearchConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)

search = SemanticSearch(config)

# Build index from all entities
search.build_faiss_index()

# Build index for specific entity type
search.build_faiss_index(entity_type="Person")

# Save index to disk
search.save_index("./faiss_index/persons.index")
```

### Vector Similarity Search

Search using vector embeddings:

```python
# Semantic search
results = search.vector_search(
    query="machine learning researchers",
    top_k=10,
    entity_type="Person"
)

for result in results:
    print(f"{result['text']}: {result['score']:.3f}")
```

### Keyword Search

Traditional keyword-based search:

```python
results = search.keyword_search(
    query="artificial intelligence",
    top_k=10
)
```

### Hybrid Search

Combine vector and keyword search:

```python
# Hybrid search with automatic score fusion
results = search.hybrid_search(
    query="AI research in robotics",
    top_k=10,
    vector_weight=0.7,  # 70% vector, 30% keyword
    keyword_weight=0.3
)
```

### Search with Context

Include graph context in results:

```python
# Get entities with their neighbors
results = search.search_with_context(
    query="neural networks",
    top_k=5,
    context_depth=1  # Include 1-hop neighbors
)

for result in results:
    print(f"Entity: {result['entity']}")
    print(f"Context: {result['context']}")
```

### Custom Embedding Models

Use different embedding models:

```python
# Multilingual model
config = SearchConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Domain-specific model
config = SearchConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    embedding_model="pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb"
)
```

## RAG Integration

### LangChain Integration

Use LangChain for RAG:

```python
from rag_integrator import RAGIntegrator, RAGConfig

config = RAGConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    llm_model="gpt-4",
    framework="langchain"
)

rag = RAGIntegrator(config)

# Ask question
result = rag.answer_question(
    question="What are the main applications of deep learning?",
    context_window=3
)

print(f"Answer: {result['answer']}")
print(f"Context: {result['context']}")
print(f"Confidence: {result['metadata']['confidence']}")
```

### LlamaIndex Integration

Use LlamaIndex for RAG:

```python
config = RAGConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    llm_model="gpt-4",
    framework="llamaindex"
)

rag = RAGIntegrator(config)

# Query with custom parameters
result = rag.answer_question(
    question="Explain neural network architectures",
    context_window=5,
    temperature=0.7,
    max_tokens=500
)
```

### Custom Prompts

Customize RAG prompts:

```python
custom_prompt = """
Based on the following knowledge graph context:

{context}

Please answer this question: {question}

Provide a detailed, technical answer with specific examples from the context.
"""

result = rag.answer_question(
    question="How does backpropagation work?",
    prompt_template=custom_prompt
)
```

### Multi-Hop Reasoning

Perform multi-hop reasoning over graph:

```python
# Retrieve entities up to 3 hops away
result = rag.answer_question_with_hops(
    question="What technologies does Google use for AI research?",
    max_hops=3
)
```

### Answer with Citations

Get answers with source citations:

```python
result = rag.answer_with_citations(
    question="Who are the pioneers of AI?"
)

print(f"Answer: {result['answer']}")
print("Sources:")
for i, source in enumerate(result['sources'], 1):
    print(f"  [{i}] {source}")
```

## Graph Querying

### Direct Cypher Queries

Execute Cypher queries:

```python
from graph_query import GraphQueryEngine, QueryConfig, CypherQuery

config = QueryConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password")
)

engine = GraphQueryEngine(config)

# Simple query
query = CypherQuery(query="""
    MATCH (p:Person)-[:WORKS_AT]->(o:Organization)
    RETURN p.name as person, o.name as organization
    LIMIT 10
""")

result = engine.execute_cypher(query)

for record in result.records:
    print(f"{record['person']} works at {record['organization']}")
```

### Parameterized Queries

Use parameters for safety:

```python
query = CypherQuery(
    query="""
        MATCH (p:Person {id: $person_id})-[:KNOWS]->(friend:Person)
        RETURN friend.name as friend_name
    """,
    parameters={"person_id": "person_123"}
)

result = engine.execute_cypher(query)
```

### Natural Language Queries

Translate NL to Cypher automatically:

```python
config = QueryConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    enable_nl_translation=True,
    llm_model="gpt-4"
)

engine = GraphQueryEngine(config)

# Natural language query
result = engine.execute_natural_language(
    "Find all software engineers who work at tech companies in California"
)

print(f"Generated Cypher: {result.query}")
print(f"Results: {len(result.records)} records")
```

### Graph Traversal

Traverse from a starting entity:

```python
# Traverse 2 hops in both directions
result = engine.traverse_from_entity(
    entity_id="person_123",
    depth=2,
    direction="both"  # "outgoing", "incoming", or "both"
)

print(f"Found {result['node_count']} nodes and {result['relationship_count']} relationships")
```

### Shortest Path Finding

Find shortest paths between entities:

```python
paths = engine.find_shortest_path(
    source_id="person_123",
    target_id="person_456",
    max_hops=5
)

for path in paths:
    print(f"Path length: {path['length']}")
    print(f"Nodes: {[n['id'] for n in path['nodes']]}")
```

### Subgraph Extraction

Extract subgraphs around entities:

```python
subgraph = engine.extract_subgraph(
    entity_ids=["person_123", "org_456", "tech_789"],
    depth=2
)

print(f"Subgraph contains:")
print(f"  {subgraph['node_count']} nodes")
print(f"  {subgraph['relationship_count']} relationships")
```

### Schema Inspection

Get graph schema information:

```python
schema = engine.get_schema()

print("Node Labels:", schema['node_labels'])
print("Relationship Types:", schema['relationship_types'])
print("Properties:", schema['property_keys'])
```

### Query Examples

Get common query patterns:

```python
examples = engine.get_query_examples()

for example in examples:
    print(f"Description: {example['description']}")
    print(f"Query: {example['query']}\n")
```

## Graph Analysis

### PageRank Centrality

Calculate PageRank scores:

```python
from graph_analyzer import GraphAnalyzer, AnalyzerConfig

config = AnalyzerConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password")
)

analyzer = GraphAnalyzer(config)

# Top 20 most influential nodes
pagerank = analyzer.calculate_pagerank(top_k=20)

print("Most Influential Nodes:")
for node_id, score in pagerank.items():
    print(f"  {node_id}: {score:.6f}")
```

### Betweenness Centrality

Find nodes that bridge communities:

```python
betweenness = analyzer.calculate_betweenness_centrality(top_k=20)

print("Bridge Nodes:")
for node_id, score in betweenness.items():
    print(f"  {node_id}: {score:.6f}")
```

### Closeness Centrality

Find most central nodes:

```python
closeness = analyzer.calculate_closeness_centrality(top_k=20)

print("Most Central Nodes:")
for node_id, score in closeness.items():
    print(f"  {node_id}: {score:.6f}")
```

### Community Detection

Detect communities using Louvain algorithm:

```python
communities = analyzer.detect_communities(algorithm="louvain")

print(f"Detected {communities.num_communities} communities")
print(f"Modularity: {communities.modularity:.3f}")

for comm_id, members in communities.communities.items():
    print(f"\nCommunity {comm_id} ({len(members)} members):")
    print(f"  {', '.join(members[:5])}")
    if len(members) > 5:
        print(f"  ... and {len(members)-5} more")
```

### Label Propagation

Alternative community detection:

```python
communities = analyzer.detect_communities(algorithm="label_propagation")
```

### Graph Metrics

Calculate comprehensive graph metrics:

```python
metrics = analyzer.calculate_graph_metrics()

print(f"Graph Metrics:")
print(f"  Nodes: {metrics.node_count}")
print(f"  Edges: {metrics.edge_count}")
print(f"  Density: {metrics.density:.4f}")
print(f"  Average Degree: {metrics.avg_degree:.2f}")
print(f"  Clustering Coefficient: {metrics.clustering_coefficient:.4f}")
print(f"  Average Clustering: {metrics.avg_clustering:.4f}")
print(f"  Connected Components: {metrics.connected_components}")
print(f"  Is Connected: {metrics.is_connected}")
if metrics.diameter:
    print(f"  Diameter: {metrics.diameter}")
```

### Bridge Node Identification

Find nodes connecting communities:

```python
bridges = analyzer.identify_bridge_nodes()

print("Bridge Nodes:")
for bridge in bridges[:10]:
    print(f"  {bridge['node_id']}")
    print(f"    Community: {bridge['community']}")
    print(f"    Connects to: {bridge['num_connections']} other communities")
    print(f"    Degree: {bridge['degree']}")
```

### Node Importance

Calculate multiple centrality measures:

```python
importance = analyzer.get_node_importance("person_123")

print(f"Node Importance Metrics:")
print(f"  PageRank: {importance['pagerank']:.6f}")
print(f"  Betweenness: {importance['betweenness']:.6f}")
print(f"  Closeness: {importance['closeness']:.6f}")
print(f"  Degree: {importance['degree']}")
print(f"  Clustering Coefficient: {importance['clustering_coefficient']:.4f}")
```

### Entity Clustering

Cluster similar entities:

```python
clusters = analyzer.cluster_entities_by_similarity(
    entity_type="Person",
    threshold=0.8
)

print(f"Found {len(clusters)} clusters:")
for cluster_id, members in clusters.items():
    print(f"  {cluster_id}: {len(members)} members")
```

## CLI Reference

### Installation

```bash
# Make CLI executable
chmod +x kg_cli.py

# Create symlink (optional)
ln -s $(pwd)/kg_cli.py /usr/local/bin/kg

# Or add to PATH
export PATH=$PATH:$(pwd)
```

### Extract Command

Extract entities from documents:

```bash
# Extract with spaCy
kg extract -i documents/ -o entities.json --method spacy

# Extract with LLM
kg extract -i documents/ -o entities.json --method llm --llm-model gpt-4

# Extract specific types
kg extract -i documents/ -o entities.json --entity-types PERSON,ORG,GPE

# Batch processing
kg extract -i documents/ -o entities.json --batch-size 50
```

### Build Command

Build knowledge graph:

```bash
# Build from extracted entities
kg build -e entities.json \
    --neo4j-uri bolt://localhost:7687 \
    --username neo4j \
    --password password

# Clear and rebuild
kg build -e entities.json \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --clear

# Custom batch size
kg build -e entities.json \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --batch-size 1000
```

### Query Command

Execute queries:

```bash
# Cypher query
kg query -c "MATCH (n:Person) RETURN n LIMIT 10" \
    --neo4j-uri bolt://localhost:7687 \
    --password password

# Natural language query
kg query -n "Find all people who work at Google" \
    --neo4j-uri bolt://localhost:7687 \
    --password password

# JSON output
kg query -c "MATCH (n) RETURN n LIMIT 5" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --format json

# Limit results
kg query -c "MATCH (n:Person) RETURN n" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --limit 100
```

### Search Command

Semantic search:

```bash
# Vector search
kg search -q "artificial intelligence researchers" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --method vector

# Keyword search
kg search -q "machine learning" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --method keyword

# Hybrid search
kg search -q "neural networks" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --method hybrid \
    --top-k 20

# Filter by entity type
kg search -q "technology companies" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --entity-type Organization
```

### RAG Command

Question answering:

```bash
# Answer question with LangChain
kg rag -q "What is the relationship between AI and robotics?" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --framework langchain

# Use LlamaIndex
kg rag -q "Explain neural network architectures" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --framework llamaindex

# Custom model
kg rag -q "What are transformers in NLP?" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --llm-model gpt-3.5-turbo

# Larger context window
kg rag -q "History of deep learning" \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --context-window 5
```

### Analyze Command

Graph analysis:

```bash
# PageRank
kg analyze --type pagerank \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --top-k 20

# Betweenness centrality
kg analyze --type betweenness \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --top-k 20

# Community detection
kg analyze --type communities \
    --neo4j-uri bolt://localhost:7687 \
    --password password

# Graph metrics
kg analyze --type metrics \
    --neo4j-uri bolt://localhost:7687 \
    --password password

# Bridge nodes
kg analyze --type bridges \
    --neo4j-uri bolt://localhost:7687 \
    --password password

# Filter by node type
kg analyze --type pagerank \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --node-type Person

# Save results
kg analyze --type pagerank \
    --neo4j-uri bolt://localhost:7687 \
    --password password \
    --output pagerank_results.json
```

### Export Command

Export graph data:

```bash
# Export to JSON
kg export --neo4j-uri bolt://localhost:7687 \
    --password password \
    -o graph.json

# Export to CSV
kg export --neo4j-uri bolt://localhost:7687 \
    --password password \
    -o graph.csv \
    --format csv

# Export to GraphML
kg export --neo4j-uri bolt://localhost:7687 \
    --password password \
    -o graph.graphml \
    --format graphml

# Filter by node type
kg export --neo4j-uri bolt://localhost:7687 \
    --password password \
    -o persons.json \
    --node-type Person
```

### Info Command

Display graph information:

```bash
kg info --neo4j-uri bolt://localhost:7687 --password password
```

### Configuration File

Create `~/.kg-config.yaml`:

```yaml
neo4j:
  uri: bolt://localhost:7687
  username: neo4j
  password: password

openai:
  api_key: sk-your-key-here
  model: gpt-4

settings:
  batch_size: 500
  cache_enabled: true
```

Then use CLI without repeating parameters:

```bash
kg query -c "MATCH (n) RETURN n LIMIT 10"
```

## Protocol Integration

### P-KNOW-KG-INTERACTION

Knowledge Graph Interaction Protocol integration:

```python
from graph_query import GraphQueryEngine, QueryConfig

# Configure for protocol compliance
config = QueryConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    enable_nl_translation=True
)

engine = GraphQueryEngine(config)

# Protocol-compliant query
result = engine.execute_natural_language(
    "Retrieve entities related to machine learning"
)

# Format response for protocol
response = {
    "query": result.query,
    "results": result.records,
    "metadata": {
        "execution_time": result.execution_time,
        "node_count": result.node_count,
        "relationship_count": result.relationship_count
    }
}
```

### P-KNOW-RAG

RAG Protocol integration:

```python
from rag_integrator import RAGIntegrator, RAGConfig

config = RAGConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    llm_model="gpt-4"
)

rag = RAGIntegrator(config)

# Protocol-compliant RAG query
result = rag.answer_question("What is deep learning?")

# Format for protocol
response = {
    "question": "What is deep learning?",
    "answer": result["answer"],
    "context": result["context"],
    "confidence": result["metadata"]["confidence"],
    "sources": result.get("sources", [])
}
```

### P-CONTEXT-VALIDATION

Context Validation Protocol:

```python
from semantic_search import SemanticSearch, SearchConfig

config = SearchConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password")
)

search = SemanticSearch(config)

# Validate context relevance
def validate_context(query: str, context: list) -> float:
    """Validate context relevance score."""
    results = search.vector_search(query, top_k=len(context))

    # Calculate relevance score
    relevance_scores = []
    for ctx in context:
        score = search.calculate_similarity(query, ctx)
        relevance_scores.append(score)

    return sum(relevance_scores) / len(relevance_scores)

# Use in RAG
context = rag._retrieve_context("neural networks")
relevance = validate_context("neural networks", context)

if relevance < 0.7:
    # Context not relevant enough, retrieve more
    context = rag._retrieve_context("neural networks", window=5)
```

## Troubleshooting

### Neo4j Connection Issues

```python
# Test connection
from neo4j import GraphDatabase

try:
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    )
    with driver.session() as session:
        result = session.run("RETURN 1")
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
```

Common issues:
- **Port already in use**: Change Neo4j port in config
- **Authentication failed**: Reset Neo4j password
- **Connection timeout**: Check Neo4j is running

### Memory Issues

For large graphs:

```python
# Use smaller batch sizes
config = BuilderConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    batch_size=100  # Reduce from default 500
)

# Disable caching
config = AnalyzerConfig(
    neo4j_uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    cache_results=False
)
```

### FAISS Index Errors

```python
# Rebuild index if corrupted
search = SemanticSearch(config)
search.clear_index()
search.build_faiss_index()
```

### LLM API Errors

```python
# Handle rate limits
import time
from openai.error import RateLimitError

try:
    result = engine.execute_natural_language(query)
except RateLimitError:
    time.sleep(60)  # Wait 1 minute
    result = engine.execute_natural_language(query)
```

### Graph Query Timeouts

```python
# Increase timeout
query = CypherQuery(
    query="MATCH (n) RETURN n",
    timeout=60.0  # 60 seconds
)
```

## API Reference

### Core Classes

- `KnowledgeExtractor`: Entity and relationship extraction
- `GraphBuilder`: Graph construction and management
- `SemanticSearch`: Vector and keyword search
- `RAGIntegrator`: RAG-based question answering
- `GraphQueryEngine`: Cypher and NL querying
- `GraphAnalyzer`: Graph analytics and metrics

### Configuration Models

- `ExtractorConfig`: Extractor configuration
- `BuilderConfig`: Builder configuration
- `SearchConfig`: Search configuration
- `RAGConfig`: RAG configuration
- `QueryConfig`: Query configuration
- `AnalyzerConfig`: Analyzer configuration

### Data Models

- `CypherQuery`: Cypher query specification
- `QueryResult`: Query execution results
- `GraphMetrics`: Graph-level metrics
- `CommunityResult`: Community detection results
- `PathResult`: Path finding results

For complete API documentation, see source code docstrings.

## Contributing

Contributions to the devCrew_s1 Knowledge Graph Management Platform are welcome! Please follow these guidelines:

1. Write comprehensive tests for new features
2. Follow PEP 8 style guidelines
3. Add docstrings to all functions and classes
4. Update README with new features
5. Run full test suite before submitting PR

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/devCrew_s1/issues
- Documentation: See this README
- Examples: Check `examples/` directory

---

**devCrew_s1 Knowledge Graph Management Platform v1.0.0**
