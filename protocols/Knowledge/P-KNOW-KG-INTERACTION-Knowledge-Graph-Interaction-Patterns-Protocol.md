# P-KNOW-KG-INTERACTION: Knowledge Graph Interaction Patterns Protocol

**Version**: 1.0
**Last Updated**: 2025-11-13
**Status**: Active
**Owner**: Backend-Engineer

## Objective

Establish knowledge graph interaction patterns protocol enabling graph query optimization, entity relationship traversal, semantic search, graph embeddings integration, multi-hop reasoning, knowledge graph maintenance, and intelligent information retrieval ensuring efficient knowledge access, contextual understanding, and AI-enhanced decision support with performance-optimized graph operations.

## Tool Requirements

- **TOOL-KNOWLEDGE-001** (Knowledge Management): Knowledge graph management, graph operations, and knowledge coordination
  - Execute: Knowledge graph management, graph operations, knowledge coordination, graph maintenance, knowledge organization
  - Integration: Knowledge graph databases, graph management systems, graph analytics, knowledge platforms, graph frameworks
  - Usage: Knowledge graph management, graph operations, knowledge coordination, graph maintenance, knowledge orchestration

- **TOOL-DATA-002** (Statistical Analysis): Graph analytics, performance optimization, and knowledge graph insights
  - Execute: Graph analytics, performance optimization, knowledge graph insights, graph analysis, performance measurement
  - Integration: Analytics platforms, graph analytics tools, performance analysis systems, graph optimization, analytics frameworks
  - Usage: Graph analytics, performance optimization, knowledge insights, graph analysis, performance coordination

- **TOOL-AI-001** (AI Reasoning): Semantic reasoning, graph embeddings, and AI-powered knowledge processing
  - Execute: Semantic reasoning, graph embeddings generation, AI-powered knowledge processing, intelligent graph analysis, semantic coordination
  - Integration: AI platforms, semantic reasoning systems, embedding frameworks, knowledge AI, reasoning tools
  - Usage: Semantic reasoning, graph embeddings, AI knowledge processing, intelligent analysis, semantic coordination

- **TOOL-API-001** (Customer Data): Graph API management, knowledge API coordination, and data integration
  - Execute: Graph API management, knowledge API coordination, data integration, API optimization, knowledge integration
  - Integration: API management platforms, knowledge APIs, data integration systems, API coordination, integration frameworks
  - Usage: Graph API management, knowledge integration, API coordination, data integration, knowledge API optimization

## Trigger

- Semantic search requirement for contextual information
- Multi-hop reasoning query across entity relationships
- Knowledge graph query optimization needed
- Entity relationship traversal for decision support
- Graph embedding generation for ML integration
- Knowledge base update requiring graph maintenance
- RAG (Retrieval-Augmented Generation) integration

## Agents

**Primary**: Backend-Engineer
**Supporting**: System-Architect, AI-Engineer
**Review**: Technical-Lead
**Orchestration**: Orchestrator (CORE-COORD-002)

## Prerequisites

- Knowledge graph database (Neo4j, AWS Neptune, Azure Cosmos DB Gremlin)
- Graph schema and ontology defined
- Entity extraction and linking pipeline
- Graph embedding model (Node2Vec, GraphSAGE)
- Query optimization tools
- Graph visualization tools

## Steps

### Step 1: Graph Query Pattern Selection (Estimated Time: 10 minutes)
**Action**: Select appropriate graph query pattern based on use case

**Query Patterns**:
```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class GraphQueryPattern(Enum):
    SHORTEST_PATH = "shortest_path"
    NEIGHBORHOOD = "neighborhood"
    SUBGRAPH = "subgraph"
    PATTERN_MATCH = "pattern_match"
    CENTRALITY = "centrality"
    COMMUNITY = "community_detection"
    SIMILARITY = "similarity_search"

@dataclass
class GraphQuery:
    pattern: GraphQueryPattern
    start_nodes: List[str]
    relationship_types: List[str]
    max_depth: int
    filters: Dict
    limit: int

class GraphQueryBuilder:
    def build_cypher_query(self, query: GraphQuery) -> str:
        """Build Cypher query for Neo4j"""

        if query.pattern == GraphQueryPattern.SHORTEST_PATH:
            return f"""
            MATCH (start {{id: '{query.start_nodes[0]}'}})
            MATCH (end {{id: '{query.start_nodes[1]}'}})
            MATCH path = shortestPath((start)-[*..{query.max_depth}]-(end))
            RETURN path, length(path) as pathLength
            ORDER BY pathLength
            LIMIT {query.limit}
            """

        elif query.pattern == GraphQueryPattern.NEIGHBORHOOD:
            rel_filter = '|'.join(query.relationship_types) if query.relationship_types else ''
            return f"""
            MATCH (n {{id: '{query.start_nodes[0]}'}})-[r:{rel_filter}*1..{query.max_depth}]-(m)
            RETURN DISTINCT n, r, m
            LIMIT {query.limit}
            """

        elif query.pattern == GraphQueryPattern.PATTERN_MATCH:
            return f"""
            MATCH (a)-[r:{query.relationship_types[0]}]->(b)
            WHERE a.type = '{query.filters.get('type', 'Entity')}'
            RETURN a, r, b
            LIMIT {query.limit}
            """

        elif query.pattern == GraphQueryPattern.CENTRALITY:
            return f"""
            CALL gds.pageRank.stream({{
                nodeQuery: 'MATCH (n) RETURN id(n) AS id',
                relationshipQuery: 'MATCH (n)-[r]-(m) RETURN id(n) AS source, id(m) AS target'
            }})
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS node, score
            ORDER BY score DESC
            LIMIT {query.limit}
            """

        return ""
```

**Expected Outcome**: Optimized graph query pattern selected
**Validation**: Query pattern matches use case, performance acceptable

### Step 2: Entity Relationship Traversal (Estimated Time: 15 minutes)
**Action**: Execute graph traversal to discover entity relationships

**Traversal Implementation**:
```python
from neo4j import GraphDatabase

class KnowledgeGraphTraverser:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def traverse_relationships(self, start_entity_id: str, max_depth: int = 3) -> Dict:
        """Traverse relationships from starting entity"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (start {id: $entity_id})-[*1..$max_depth]-(connected)
                RETURN
                    start.id as start_id,
                    start.name as start_name,
                    [rel in relationships(path) | type(rel)] as relationship_types,
                    connected.id as connected_id,
                    connected.name as connected_name,
                    length(path) as distance
                ORDER BY distance
                LIMIT 100
            """, entity_id=start_entity_id, max_depth=max_depth)

            relationships = []
            for record in result:
                relationships.append({
                    'start': {'id': record['start_id'], 'name': record['start_name']},
                    'connected': {'id': record['connected_id'], 'name': record['connected_name']},
                    'relationship_path': record['relationship_types'],
                    'distance': record['distance']
                })

            return {
                'start_entity': start_entity_id,
                'relationships_found': len(relationships),
                'relationships': relationships
            }

    def multi_hop_reasoning(self, start_entity: str, target_entity: str, max_hops: int = 5) -> List[Dict]:
        """Multi-hop reasoning to find connection between entities"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = shortestPath(
                    (start {id: $start})-[*1..$max_hops]-(target {id: $target})
                )
                RETURN
                    [node in nodes(path) | {id: node.id, name: node.name, type: labels(node)[0]}] as nodes,
                    [rel in relationships(path) | {type: type(rel), properties: properties(rel)}] as relationships,
                    length(path) as hops
            """, start=start_entity, target=target_entity, max_hops=max_hops)

            paths = []
            for record in result:
                paths.append({
                    'nodes': record['nodes'],
                    'relationships': record['relationships'],
                    'hops': record['hops']
                })

            return paths

    def find_similar_entities(self, entity_id: str, similarity_threshold: float = 0.7) -> List[Dict]:
        """Find similar entities based on graph structure"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e1 {id: $entity_id})-[r1]-(common)-[r2]-(e2)
                WHERE e1 <> e2
                WITH e2, count(DISTINCT common) as common_neighbors
                MATCH (e1)-[r]-(neighbor)
                WITH e2, common_neighbors, count(DISTINCT neighbor) as total_neighbors
                WITH e2, common_neighbors, total_neighbors,
                     toFloat(common_neighbors) / total_neighbors as similarity
                WHERE similarity >= $threshold
                RETURN e2.id as entity_id, e2.name as entity_name, similarity
                ORDER BY similarity DESC
                LIMIT 10
            """, entity_id=entity_id, threshold=similarity_threshold)

            return [dict(record) for record in result]
```

**Expected Outcome**: Entity relationships discovered, multi-hop paths identified
**Validation**: Relevant connections found, traversal depth appropriate

### Step 3: Semantic Search and Context Retrieval (Estimated Time: 15 minutes)
**Action**: Perform semantic search using graph embeddings

**Semantic Search**:
```python
import numpy as np
from typing import List, Tuple

class SemanticGraphSearch:
    def __init__(self, kg_traverser: KnowledgeGraphTraverser):
        self.kg = kg_traverser
        self.embeddings_cache = {}

    def semantic_search(self, query_text: str, top_k: int = 10) -> List[Dict]:
        """Search knowledge graph using semantic similarity"""
        # 1. Extract entities from query
        query_entities = self._extract_entities(query_text)

        # 2. Get graph embeddings for query entities
        query_embeddings = [self._get_entity_embedding(e) for e in query_entities]

        # 3. Find similar entities in graph
        similar_entities = []
        for entity_id in query_entities:
            similar = self.kg.find_similar_entities(entity_id, similarity_threshold=0.6)
            similar_entities.extend(similar)

        # 4. Rank by relevance
        ranked_results = self._rank_by_relevance(query_embeddings, similar_entities)

        return ranked_results[:top_k]

    def contextual_retrieval(self, entity_id: str, context_depth: int = 2) -> Dict:
        """Retrieve contextual information around entity"""
        # Get immediate neighbors
        neighbors = self.kg.traverse_relationships(entity_id, max_depth=1)

        # Get extended context
        extended_context = self.kg.traverse_relationships(entity_id, max_depth=context_depth)

        # Build context summary
        context = {
            'entity_id': entity_id,
            'immediate_connections': neighbors['relationships_found'],
            'extended_context': extended_context['relationships_found'],
            'key_relationships': self._identify_key_relationships(extended_context),
            'context_summary': self._generate_context_summary(extended_context)
        }

        return context

    def _extract_entities(self, text: str) -> List[str]:
        """Extract entity IDs from text (NER + entity linking)"""
        # Placeholder: Use NER model + entity linking
        return []

    def _get_entity_embedding(self, entity_id: str) -> np.ndarray:
        """Get graph embedding for entity"""
        if entity_id in self.embeddings_cache:
            return self.embeddings_cache[entity_id]

        # Generate embedding using Node2Vec or GraphSAGE
        embedding = np.random.rand(128)  # Placeholder
        self.embeddings_cache[entity_id] = embedding
        return embedding

    def _rank_by_relevance(self, query_embeddings: List[np.ndarray],
                          candidates: List[Dict]) -> List[Dict]:
        """Rank candidates by semantic relevance"""
        # Compute cosine similarity
        for candidate in candidates:
            candidate['relevance_score'] = 0.85  # Placeholder

        return sorted(candidates, key=lambda x: x['relevance_score'], reverse=True)

    def _identify_key_relationships(self, context: Dict) -> List[Dict]:
        """Identify most important relationships in context"""
        relationships = context['relationships']
        # Filter by importance (frequency, centrality, etc.)
        key_rels = sorted(relationships, key=lambda r: r['distance'])[:5]
        return key_rels

    def _generate_context_summary(self, context: Dict) -> str:
        """Generate natural language summary of context"""
        rel_count = context['relationships_found']
        return f"Found {rel_count} related entities across {context.get('max_depth', 2)} relationship hops"
```

**Expected Outcome**: Semantically relevant information retrieved
**Validation**: Search results relevant, context appropriate

### Step 4: Graph Maintenance and Updates (Estimated Time: 20 minutes)
**Action**: Maintain graph consistency with entity/relationship updates

**Maintenance Operations**:
```python
class KnowledgeGraphMaintainer:
    def __init__(self, kg_traverser: KnowledgeGraphTraverser):
        self.kg = kg_traverser

    def add_entity(self, entity_id: str, entity_type: str, properties: Dict) -> bool:
        """Add new entity to knowledge graph"""
        with self.kg.driver.session() as session:
            result = session.run("""
                MERGE (e:Entity {id: $entity_id})
                SET e.type = $entity_type
                SET e += $properties
                RETURN e
            """, entity_id=entity_id, entity_type=entity_type, properties=properties)
            return result.single() is not None

    def add_relationship(self, source_id: str, target_id: str,
                        rel_type: str, properties: Dict = None) -> bool:
        """Add relationship between entities"""
        with self.kg.driver.session() as session:
            props = properties or {}
            result = session.run(f"""
                MATCH (source {{id: $source_id}})
                MATCH (target {{id: $target_id}})
                MERGE (source)-[r:{rel_type}]->(target)
                SET r += $properties
                RETURN r
            """, source_id=source_id, target_id=target_id, properties=props)
            return result.single() is not None

    def update_entity(self, entity_id: str, updates: Dict) -> bool:
        """Update entity properties"""
        with self.kg.driver.session() as session:
            result = session.run("""
                MATCH (e {id: $entity_id})
                SET e += $updates
                RETURN e
            """, entity_id=entity_id, updates=updates)
            return result.single() is not None

    def delete_entity(self, entity_id: str, cascade: bool = False) -> int:
        """Delete entity (optionally with relationships)"""
        with self.kg.driver.session() as session:
            if cascade:
                result = session.run("""
                    MATCH (e {id: $entity_id})
                    DETACH DELETE e
                    RETURN count(*) as deleted
                """, entity_id=entity_id)
            else:
                result = session.run("""
                    MATCH (e {id: $entity_id})
                    WHERE NOT (e)--()
                    DELETE e
                    RETURN count(*) as deleted
                """, entity_id=entity_id)

            return result.single()['deleted']

    def validate_graph_consistency(self) -> Dict:
        """Validate graph consistency (orphaned nodes, broken relationships)"""
        with self.kg.driver.session() as session:
            # Check for orphaned nodes
            orphaned = session.run("""
                MATCH (n)
                WHERE NOT (n)--()
                RETURN count(n) as orphaned_count
            """).single()['orphaned_count']

            # Check for missing properties
            missing_props = session.run("""
                MATCH (n)
                WHERE n.name IS NULL OR n.type IS NULL
                RETURN count(n) as missing_properties
            """).single()['missing_properties']

            return {
                'orphaned_nodes': orphaned,
                'missing_properties': missing_props,
                'status': 'healthy' if orphaned == 0 and missing_props == 0 else 'needs_attention'
            }
```

**Expected Outcome**: Graph maintained with consistent data
**Validation**: No orphaned nodes, relationships valid, properties complete

### Step 5: Query Optimization and Performance Tuning (Estimated Time: 15 minutes)
**Action**: Optimize graph queries for performance

**Optimization Strategies**:
```python
class GraphQueryOptimizer:
    def __init__(self, kg_traverser: KnowledgeGraphTraverser):
        self.kg = kg_traverser

    def create_indexes(self, properties: List[Tuple[str, str]]):
        """Create indexes on frequently queried properties"""
        with self.kg.driver.session() as session:
            for label, prop in properties:
                session.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{prop})")

    def analyze_query_plan(self, cypher_query: str) -> Dict:
        """Analyze query execution plan"""
        with self.kg.driver.session() as session:
            result = session.run(f"EXPLAIN {cypher_query}")
            plan = result.consume().plan

            return {
                'estimated_rows': plan.get('estimatedRows', 0),
                'operator_type': plan.get('operatorType', 'unknown'),
                'identifiers': plan.get('identifiers', [])
            }

    def optimize_traversal_depth(self, query: GraphQuery) -> int:
        """Recommend optimal traversal depth based on graph density"""
        with self.kg.driver.session() as session:
            # Calculate average degree
            result = session.run("""
                MATCH (n)-[r]-()
                RETURN avg(count(r)) as avg_degree
            """)
            avg_degree = result.single()['avg_degree']

            # Recommend depth based on graph density
            if avg_degree > 10:
                return min(query.max_depth, 3)  # Sparse graph, limit depth
            else:
                return query.max_depth
```

**Expected Outcome**: Graph queries optimized for performance
**Validation**: Query execution time within target, indexes effective

### Step 6: Integration with RAG (Retrieval-Augmented Generation) (Estimated Time: 10 minutes)
**Action**: Integrate knowledge graph with RAG pipelines

**RAG Integration**:
```python
class KnowledgeGraphRAG:
    def __init__(self, kg_traverser: KnowledgeGraphTraverser,
                 semantic_search: SemanticGraphSearch):
        self.kg = kg_traverser
        self.search = semantic_search

    def retrieve_context_for_llm(self, user_query: str, max_context_tokens: int = 2000) -> str:
        """Retrieve graph context for LLM augmentation"""
        # 1. Semantic search to find relevant entities
        relevant_entities = self.search.semantic_search(user_query, top_k=5)

        # 2. Gather contextual information
        context_parts = []
        for entity in relevant_entities:
            entity_context = self.search.contextual_retrieval(entity['entity_id'], context_depth=2)
            context_parts.append(self._format_context(entity_context))

        # 3. Combine and truncate to token limit
        full_context = "\n\n".join(context_parts)
        truncated_context = self._truncate_to_tokens(full_context, max_context_tokens)

        return truncated_context

    def _format_context(self, entity_context: Dict) -> str:
        """Format entity context for LLM consumption"""
        return f"""
Entity: {entity_context['entity_id']}
Connections: {entity_context['immediate_connections']}
Context: {entity_context['context_summary']}
Key Relationships: {', '.join([str(r) for r in entity_context['key_relationships']])}
        """

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximate token limit"""
        # Rough approximation: 4 characters per token
        max_chars = max_tokens * 4
        return text[:max_chars] if len(text) > max_chars else text
```

**Expected Outcome**: Knowledge graph integrated with RAG
**Validation**: Relevant context retrieved, LLM responses enhanced

### Step 7: Performance Monitoring and Reporting (Estimated Time: 10 minutes)
**Action**: Monitor knowledge graph performance and generate reports

**Expected Outcome**: Performance metrics collected, optimization recommendations
**Validation**: Query latency within target, graph health validated

## Expected Outputs

- **Query Pattern Documentation**: Optimized patterns per use case
- **Relationship Map**: Entity connections discovered
- **Semantic Search Results**: Top-k relevant entities
- **Graph Maintenance Report**: Consistency validation, orphaned node cleanup
- **Performance Metrics**: Query latency, traversal efficiency
- **RAG Context**: Formatted context for LLM augmentation
- **Success Indicators**: <100ms query latency, >90% search relevance, 100% graph consistency

## Rollback/Recovery

**Trigger**: Graph corruption, query performance degradation, inconsistent data

**P-RECOVERY Integration**:
1. Restore graph from backup snapshot
2. Rebuild graph from source data
3. Re-index graph for performance
4. Validate graph consistency

**Verification**: Graph operational, queries performant, data consistent
**Data Integrity**: High - Graph backup essential

## Failure Handling

### Failure Scenario 1: Graph Query Timeout
- **Symptoms**: Queries exceeding timeout (>5 seconds)
- **Root Cause**: Inefficient traversal, missing indexes, graph too dense
- **Impact**: High - User experience degraded, RAG integration slow
- **Resolution**: Add indexes, limit traversal depth, optimize query patterns
- **Prevention**: Query optimization, index management, depth limits

### Failure Scenario 2: Orphaned Nodes Degrading Graph Quality
- **Symptoms**: Many disconnected entities, poor search results
- **Root Cause**: Incomplete entity deletion, relationship maintenance gaps
- **Impact**: Medium - Graph quality reduced, search relevance poor
- **Resolution**: Cleanup orphaned nodes, fix deletion procedures
- **Prevention**: Cascade deletes, consistency validation, maintenance schedules

### Failure Scenario 3: Embedding Generation Failures
- **Symptoms**: Semantic search returning irrelevant results
- **Root Cause**: Embedding model drift, outdated embeddings
- **Impact**: High - Search quality degraded, RAG context poor
- **Resolution**: Regenerate embeddings, update model
- **Prevention**: Regular embedding updates, model monitoring

### Failure Scenario 4: Graph Scaling Issues
- **Symptoms**: Performance degradation as graph grows
- **Root Cause**: Insufficient indexing, query complexity
- **Impact**: Critical - System unusable at scale
- **Resolution**: Horizontal scaling, query optimization, caching
- **Prevention**: Capacity planning, performance testing, sharding

### Failure Scenario 5: Inconsistent Graph Updates
- **Symptoms**: Concurrent updates causing inconsistencies
- **Root Cause**: Lack of transactions, race conditions
- **Impact**: High - Data integrity compromised
- **Resolution**: Use transactions, implement locks, validate consistency
- **Prevention**: Transactional updates, consistency checks, conflict resolution

### Failure Scenario 6: RAG Context Retrieval Failures
- **Symptoms**: LLM receiving irrelevant or incomplete context
- **Root Cause**: Poor entity extraction, shallow traversal
- **Impact**: High - AI responses inaccurate
- **Resolution**: Improve NER, increase traversal depth, enhance ranking
- **Prevention**: Entity linking validation, context relevance scoring

## Validation Criteria

### Quantitative Thresholds
- Query latency: <100ms (p95)
- Search relevance: >90% (user feedback)
- Graph consistency: 100% (no orphaned nodes)
- Traversal efficiency: <3 hops for 90% queries
- Index coverage: 100% of frequently queried properties
- RAG context quality: >85% LLM response accuracy

### Boolean Checks
- Query pattern implemented: Pass/Fail
- Traversal functional: Pass/Fail
- Semantic search working: Pass/Fail
- Graph maintenance executed: Pass/Fail
- Optimization applied: Pass/Fail
- RAG integration operational: Pass/Fail

### Qualitative Assessments
- Search result relevance: User feedback (≥4/5)
- Context quality: AI team assessment (≥4/5)
- Graph maintainability: Backend team (≥4/5)

**Overall Success**: Thresholds met AND boolean checks pass AND assessments ≥4/5

## HITL Escalation

### Automatic Triggers
- Query timeout >5 seconds
- Graph consistency <95%
- Search relevance <70%

### Manual Triggers
- Graph schema changes
- Query pattern optimization
- RAG integration tuning

### Escalation Procedure
1. **Level 1**: Backend-Engineer query optimization
2. **Level 2**: System-Architect schema redesign
3. **Level 3**: AI-Engineer embedding model updates

## Related Protocols

### Upstream
- **Entity Extraction**: Provides entities for graph
- **Data Ingestion**: Populates knowledge graph

### Downstream
- **P-KNOW-RAG**: Uses graph for context retrieval
- **P-CONTEXT-VALIDATION**: Validates graph-derived context

### Alternatives
- **Relational Database**: SQL vs. graph queries
- **Vector Database**: Semantic search only vs. graph + semantic

## Test Scenarios

### Happy Path
#### Scenario 1: Multi-Hop Entity Discovery
- **Setup**: User queries "How is Product A related to Company B?"
- **Execution**: Multi-hop traversal finds 3-hop connection
- **Expected Result**: Path discovered: Product A → Category → Manufacturer → Company B
- **Validation**: Relevant path found, query <50ms

### Failure Scenarios
#### Scenario 2: Query Timeout Recovery
- **Setup**: Complex 10-hop traversal query times out
- **Execution**: Automatic depth limit applied, query retried
- **Expected Result**: Query succeeds with 5-hop limit, results returned
- **Validation**: Timeout prevented, relevant results found

### Edge Cases
#### Scenario 3: Semantic Search with No Exact Matches
- **Setup**: User query has no direct entity matches
- **Execution**: Embedding similarity finds related entities
- **Expected Result**: Semantically similar entities returned (70%+ similarity)
- **Validation**: Results relevant despite no exact match

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol for Epic 111. Knowledge graph interaction with traversal, semantic search, RAG integration, 6 failure scenarios. | Backend-Engineer |

### Review Cycle
- **Frequency**: Quarterly
- **Next Review**: 2026-01-10
- **Reviewers**: Backend-Engineer lead, System-Architect, AI-Engineer

### Compliance Status
- **Framework Standards**: ✅ Compliant
- **Knowledge Management**: Required
- **Last Validation**: 2025-10-10

## Performance SLOs

- **Query latency**: <100ms (p95)
- **Search relevance**: >90%
- **Graph consistency**: 100%
- **Traversal efficiency**: <3 hops (90%)
- **RAG context quality**: >85%
