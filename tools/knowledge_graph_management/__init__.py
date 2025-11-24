"""
Knowledge Graph Management Platform.

A comprehensive platform for knowledge graph construction, semantic querying,
and RAG integration. Supports Neo4j graph database, spaCy entity extraction,
LangChain/LlamaIndex RAG, and NetworkX graph algorithms.

Protocols supported:
- P-KNOW-KG-INTERACTION: Knowledge graph construction and querying
- P-KNOW-RAG: RAG integration for graph-enhanced retrieval
- P-CONTEXT-VALIDATION: Validate knowledge context quality

Project: devCrew_s1
"""

__version__ = "1.0.0"
__author__ = "devCrew_s1"

# Graph Analyzer
from .graph_analyzer import (AnalyzerConfig, CommunityResult, GraphAnalyzer,
                             GraphMetrics, PathResult)
# Graph Builder
from .graph_builder import (GraphBuilder, GraphBuilderConfig, GraphNode,
                            GraphRelationship, GraphSchema)
# Graph Query Engine
from .graph_query import (CypherQuery, GraphQueryEngine, NLToCypherTranslator,
                          QueryConfig, QueryResult)
# Knowledge Extractor
from .knowledge_extractor import (Entity, EntityType, ExtractionConfig,
                                  KnowledgeExtractor, Relationship,
                                  RelationshipType, Triple)
# RAG Integrator
from .rag_integrator import RAGConfig, RAGIntegrator, RAGQuery, RAGResponse
# Semantic Search
from .semantic_search import SearchConfig, SearchResult, SemanticSearchEngine

__all__ = [
    # Knowledge Extractor
    "KnowledgeExtractor",
    "ExtractionConfig",
    "Entity",
    "EntityType",
    "Relationship",
    "RelationshipType",
    "Triple",
    # Graph Builder
    "GraphBuilder",
    "GraphBuilderConfig",
    "GraphNode",
    "GraphRelationship",
    "GraphSchema",
    # Semantic Search
    "SemanticSearchEngine",
    "SearchConfig",
    "SearchResult",
    # RAG Integrator
    "RAGIntegrator",
    "RAGConfig",
    "RAGQuery",
    "RAGResponse",
    # Graph Query Engine
    "GraphQueryEngine",
    "NLToCypherTranslator",
    "QueryConfig",
    "CypherQuery",
    "QueryResult",
    # Graph Analyzer
    "GraphAnalyzer",
    "AnalyzerConfig",
    "GraphMetrics",
    "CommunityResult",
    "PathResult",
]
