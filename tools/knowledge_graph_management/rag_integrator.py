"""
RAG Integrator for Knowledge Graph Management Platform.

This module provides Retrieval-Augmented Generation (RAG) capabilities
integrating LangChain, LlamaIndex, and Neo4j knowledge graphs for
enhanced question-answering with graph context.

Part of devCrew_s1 TOOL-KNOWLEDGE-001 implementation (Issue #54).
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores.neo4j_vector import Neo4jVector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from llama_index.core import KnowledgeGraphIndex
from llama_index.core.graph_stores import Neo4jGraphStore
from neo4j import GraphDatabase
from pydantic import BaseModel, Field, field_validator
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Custom Exceptions
class RAGError(Exception):
    """Base exception for RAG operations."""

    pass


class LLMError(RAGError):
    """Raised when LLM operations fail."""

    pass


class GraphRetrievalError(RAGError):
    """Raised when graph retrieval operations fail."""

    pass


# Pydantic Models
class RAGConfig(BaseModel):
    """Configuration for RAG integrator.

    Attributes:
        llm_provider: LLM provider name ('openai' or 'anthropic')
        model_name: Specific model to use
        temperature: LLM temperature for response generation
        max_tokens: Maximum tokens in LLM response
        neo4j_uri: Neo4j connection URI
        auth: Neo4j authentication tuple (username, password)
        max_context_entities: Maximum entities to include in context
        retrieval_strategy: Strategy for retrieval ('hybrid', 'semantic', 'graph')
    """

    llm_provider: str = Field(
        default="openai", description="LLM provider (openai or anthropic)"
    )
    model_name: str = Field(default="gpt-4", description="LLM model name")
    temperature: float = Field(
        default=0.7, description="LLM temperature", ge=0.0, le=2.0
    )
    max_tokens: int = Field(
        default=2000, description="Maximum tokens in response", gt=0
    )
    neo4j_uri: str = Field(description="Neo4j connection URI")
    auth: Tuple[str, str] = Field(
        description="Neo4j authentication (username, password)"
    )
    max_context_entities: int = Field(
        default=20, description="Maximum entities in context", gt=0
    )
    retrieval_strategy: str = Field(
        default="hybrid", description="Retrieval strategy (hybrid, semantic, or graph)"
    )

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        if v not in ["openai", "anthropic"]:
            raise ValueError("llm_provider must be 'openai' or 'anthropic'")
        return v

    @field_validator("retrieval_strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        """Validate retrieval strategy."""
        if v not in ["hybrid", "semantic", "graph"]:
            raise ValueError(
                "retrieval_strategy must be 'hybrid', 'semantic', or 'graph'"
            )
        return v


class RAGQuery(BaseModel):
    """Query for RAG system.

    Attributes:
        question: Question to answer
        filters: Optional filtering criteria
        max_depth: Maximum graph traversal depth
        include_relationships: Whether to include relationship information
    """

    question: str = Field(description="Question to answer")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional filters for retrieval"
    )
    max_depth: int = Field(
        default=2, description="Maximum graph traversal depth", ge=1, le=5
    )
    include_relationships: bool = Field(
        default=True, description="Include relationship information in context"
    )


class RAGResponse(BaseModel):
    """Response from RAG system.

    Attributes:
        answer: Generated answer text
        sources: List of source entity identifiers
        graph_entities: List of graph entities used in context
        graph_relationships: List of relationships used in context
        confidence: Confidence score for the answer (0-1)
        metadata: Additional response metadata
    """

    answer: str = Field(description="Generated answer")
    sources: List[str] = Field(
        default_factory=list, description="Source entity identifiers"
    )
    graph_entities: List[str] = Field(
        default_factory=list, description="Graph entities used in context"
    )
    graph_relationships: List[str] = Field(
        default_factory=list, description="Relationships used in context"
    )
    confidence: float = Field(
        default=0.0, description="Answer confidence score", ge=0.0, le=1.0
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class RAGIntegrator:
    """RAG integrator combining LLMs with knowledge graph retrieval.

    This class provides RAG capabilities by integrating LangChain and
    LlamaIndex with Neo4j knowledge graphs for context-aware question
    answering.

    Attributes:
        config: RAG configuration
        llm: Language model instance
        neo4j_driver: Neo4j database driver
        vector_store: LangChain vector store
        langchain_retriever: LangChain retriever
        llamaindex_connector: LlamaIndex knowledge graph connector
    """

    def __init__(self, config: RAGConfig) -> None:
        """Initialize RAG integrator.

        Args:
            config: RAG configuration

        Raises:
            RAGError: If initialization fails
        """
        try:
            self.config = config
            logger.info(
                f"Initializing RAGIntegrator with {config.llm_provider} "
                f"model {config.model_name}"
            )

            # Initialize LLM
            self._initialize_llm()

            # Initialize Neo4j connection
            self.neo4j_driver = GraphDatabase.driver(config.neo4j_uri, auth=config.auth)
            self.neo4j_driver.verify_connectivity()
            logger.info("Neo4j connection established")

            # Initialize LangChain components
            self.vector_store: Optional[Neo4jVector] = None
            self.langchain_retriever: Optional[Any] = None

            # Initialize LlamaIndex components
            self.llamaindex_connector: Optional[KnowledgeGraphIndex] = None

            logger.info("RAGIntegrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAGIntegrator: {e}")
            raise RAGError(f"Initialization failed: {e}") from e

    def _initialize_llm(self) -> None:
        """Initialize the LLM based on provider configuration.

        Raises:
            LLMError: If LLM initialization fails
        """
        try:
            if self.config.llm_provider == "openai":
                self.llm = ChatOpenAI(
                    model_name=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                logger.info(f"Initialized OpenAI LLM: {self.config.model_name}")

            elif self.config.llm_provider == "anthropic":
                self.llm = ChatAnthropic(
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                logger.info(f"Initialized Anthropic LLM: {self.config.model_name}")

            else:
                raise LLMError(f"Unsupported LLM provider: {self.config.llm_provider}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise LLMError(f"LLM initialization failed: {e}") from e

    @retry(
        retry=retry_if_exception_type(LLMError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def query(
        self, question: str, max_context_entities: Optional[int] = None
    ) -> RAGResponse:
        """Perform RAG query with graph context.

        Args:
            question: Question to answer
            max_context_entities: Maximum entities to include in context

        Returns:
            RAGResponse with answer and metadata

        Raises:
            RAGError: If query fails
        """
        try:
            logger.info(f"Processing RAG query: '{question}'")

            max_entities = max_context_entities or self.config.max_context_entities

            # Retrieve relevant entities based on strategy
            if self.config.retrieval_strategy == "semantic":
                entities = self._retrieve_entities_by_semantic_search(
                    question, top_k=max_entities
                )
            elif self.config.retrieval_strategy == "graph":
                entities = self._retrieve_entities_by_graph_traversal(
                    question, max_depth=2
                )
            else:  # hybrid
                entities = self._retrieve_entities_hybrid(question, top_k=max_entities)

            if not entities:
                logger.warning("No relevant entities found")
                return RAGResponse(
                    answer=(
                        "I couldn't find relevant information to "
                        "answer your question."
                    ),
                    sources=[],
                    graph_entities=[],
                    graph_relationships=[],
                    confidence=0.0,
                    metadata={"retrieval_strategy": self.config.retrieval_strategy},
                )

            # Extract subgraph context
            entity_ids = [e["id"] for e in entities]
            subgraph = self.extract_relevant_subgraph(question, max_depth=2)

            # Assemble context
            context = self.assemble_context(
                entities=[e["text"] for e in entities],
                relationships=subgraph.get("relationships", []),
            )

            # Generate answer
            answer = self.generate_answer(question, context)

            # Track citations
            sources = self.track_citations(entity_ids)

            # Evaluate answer quality
            confidence = self.evaluate_answer_quality(question, answer, context)

            response = RAGResponse(
                answer=answer,
                sources=sources,
                graph_entities=entity_ids,
                graph_relationships=[
                    f"{r['source']}-[{r['type']}]->{r['target']}"
                    for r in subgraph.get("relationships", [])
                ],
                confidence=confidence,
                metadata={
                    "retrieval_strategy": self.config.retrieval_strategy,
                    "entity_count": len(entities),
                    "relationship_count": len(subgraph.get("relationships", [])),
                },
            )

            logger.info(
                f"Generated answer with confidence {confidence:.2f} "
                f"using {len(entities)} entities"
            )
            return response

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise RAGError(f"Query processing failed: {e}") from e

    def query_with_graph_context(
        self, question: str, graph_depth: int = 2, max_entities: int = 30
    ) -> RAGResponse:
        """Enhanced RAG query with deeper graph traversal.

        Args:
            question: Question to answer
            graph_depth: Depth of graph traversal
            max_entities: Maximum entities to retrieve

        Returns:
            RAGResponse with answer and graph context

        Raises:
            RAGError: If query fails
        """
        try:
            logger.info(
                f"Processing enhanced RAG query with depth {graph_depth}: '{question}'"
            )

            # Retrieve initial entities
            seed_entities = self._retrieve_entities_by_semantic_search(
                question, top_k=10
            )

            if not seed_entities:
                logger.warning("No seed entities found")
                return RAGResponse(
                    answer=(
                        "I couldn't find relevant information to "
                        "answer your question."
                    ),
                    sources=[],
                    graph_entities=[],
                    graph_relationships=[],
                    confidence=0.0,
                )

            # Expand graph context
            seed_ids = [e["id"] for e in seed_entities]
            expanded_context = self._expand_graph_context(seed_ids, graph_depth)

            # Limit total entities
            all_entities = expanded_context["entities"][:max_entities]
            all_relationships = expanded_context["relationships"]

            # Format context for LLM
            formatted_context = self._format_graph_for_llm(
                all_entities, all_relationships
            )

            # Generate answer
            answer = self.generate_answer(question, formatted_context)

            # Track sources
            entity_ids = [e["id"] for e in all_entities]
            sources = self.track_citations(entity_ids)

            # Evaluate confidence
            confidence = self.evaluate_answer_quality(
                question, answer, formatted_context
            )

            response = RAGResponse(
                answer=answer,
                sources=sources,
                graph_entities=entity_ids,
                graph_relationships=[
                    f"{r['source']}-[{r['type']}]->{r['target']}"
                    for r in all_relationships
                ],
                confidence=confidence,
                metadata={
                    "graph_depth": graph_depth,
                    "entity_count": len(all_entities),
                    "relationship_count": len(all_relationships),
                },
            )

            logger.info(
                f"Generated enhanced answer with {len(all_entities)} entities "
                f"and {len(all_relationships)} relationships"
            )
            return response

        except Exception as e:
            logger.error(f"Enhanced query failed: {e}")
            raise RAGError(f"Enhanced query processing failed: {e}") from e

    def build_langchain_retriever(self) -> Any:
        """Create LangChain retriever with Neo4j vector store.

        Returns:
            LangChain retriever instance

        Raises:
            RAGError: If retriever creation fails
        """
        try:
            logger.info("Building LangChain retriever")

            # Initialize embeddings
            embeddings = OpenAIEmbeddings()

            # Create Neo4j vector store
            self.vector_store = Neo4jVector.from_existing_graph(
                embedding=embeddings,
                url=self.config.neo4j_uri,
                username=self.config.auth[0],
                password=self.config.auth[1],
                index_name="entity_embeddings",
                node_label="Entity",
                text_node_properties=["name", "description"],
                embedding_node_property="embedding",
            )

            # Create retriever
            self.langchain_retriever = self.vector_store.as_retriever(
                search_kwargs={"k": self.config.max_context_entities}
            )

            logger.info("LangChain retriever created successfully")
            return self.langchain_retriever

        except Exception as e:
            logger.error(f"Failed to build LangChain retriever: {e}")
            raise RAGError(f"Retriever creation failed: {e}") from e

    def build_llamaindex_connector(self) -> Any:
        """Create LlamaIndex knowledge graph connector.

        Returns:
            LlamaIndex KnowledgeGraphIndex instance

        Raises:
            RAGError: If connector creation fails
        """
        try:
            logger.info("Building LlamaIndex connector")

            # Create Neo4j graph store
            graph_store = Neo4jGraphStore(
                username=self.config.auth[0],
                password=self.config.auth[1],
                url=self.config.neo4j_uri,
                database="neo4j",
            )

            # Create knowledge graph index
            self.llamaindex_connector = KnowledgeGraphIndex.from_existing(graph_store)

            logger.info("LlamaIndex connector created successfully")
            return self.llamaindex_connector

        except Exception as e:
            logger.error(f"Failed to build LlamaIndex connector: {e}")
            raise RAGError(f"Connector creation failed: {e}") from e

    def assemble_context(self, entities: List[str], relationships: List[str]) -> str:
        """Assemble context from graph data for LLM prompt.

        Args:
            entities: List of entity text descriptions
            relationships: List of relationship descriptions

        Returns:
            Formatted context string
        """
        context_parts = []

        if entities:
            context_parts.append("Relevant Entities:")
            for i, entity in enumerate(entities, 1):
                context_parts.append(f"{i}. {entity}")

        if relationships:
            context_parts.append("\nRelationships:")
            for i, rel in enumerate(relationships, 1):
                context_parts.append(f"{i}. {rel}")

        return "\n".join(context_parts)

    def extract_relevant_subgraph(
        self, query: str, max_depth: int = 2
    ) -> Dict[str, Any]:
        """Extract subgraph relevant to the query.

        Args:
            query: Query string
            max_depth: Maximum traversal depth

        Returns:
            Dictionary with entities and relationships

        Raises:
            GraphRetrievalError: If extraction fails
        """
        try:
            logger.info(f"Extracting subgraph with depth {max_depth}")

            # Get seed entities through semantic search
            seed_entities = self._retrieve_entities_by_semantic_search(query, top_k=5)

            if not seed_entities:
                return {"entities": [], "relationships": []}

            seed_ids = [e["id"] for e in seed_entities]

            # Expand context
            subgraph = self._expand_graph_context(seed_ids, max_depth)

            logger.info(
                f"Extracted subgraph with {len(subgraph['entities'])} entities "
                f"and {len(subgraph['relationships'])} relationships"
            )
            return subgraph

        except Exception as e:
            logger.error(f"Failed to extract subgraph: {e}")
            raise GraphRetrievalError(f"Subgraph extraction failed: {e}") from e

    @retry(
        retry=retry_if_exception_type(LLMError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM with context.

        Args:
            question: Question to answer
            context: Context information from knowledge graph

        Returns:
            Generated answer text

        Raises:
            LLMError: If answer generation fails
        """
        try:
            logger.info("Generating answer with LLM")

            # Create prompt template
            prompt_template = (
                "You are a helpful assistant with access to a knowledge graph.\n"
                "Use the following context from the knowledge graph to answer "
                "the question.\n"
                "If you cannot find relevant information in the context, say so.\n"
                "\n"
                "Context:\n"
                "{context}\n"
                "\n"
                "Question: {question}\n"
                "\n"
                "Answer: Let me provide a comprehensive answer based on the "
                "knowledge graph context."
            )

            prompt = PromptTemplate(
                input_variables=["context", "question"], template=prompt_template
            )

            # Format prompt
            formatted_prompt = prompt.format(context=context, question=question)

            # Generate response
            response = self.llm.invoke(formatted_prompt)

            # Extract text from response
            if hasattr(response, "content"):
                answer = response.content
            else:
                answer = str(response)

            logger.info("Answer generated successfully")
            return answer

        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise LLMError(f"Answer generation failed: {e}") from e

    def track_citations(self, entity_ids: List[str]) -> List[str]:
        """Track sources used in answer generation.

        Args:
            entity_ids: List of entity IDs used in context

        Returns:
            List of formatted citation strings
        """
        try:
            citations = []

            with self.neo4j_driver.session() as session:
                for entity_id in entity_ids:
                    result = session.run(
                        """
                        MATCH (n)
                        WHERE elementId(n) = $entity_id
                        RETURN n.name as name, labels(n) as labels
                        """,
                        entity_id=entity_id,
                    )

                    record = result.single()
                    if record:
                        name = record["name"] or entity_id
                        labels = record["labels"]
                        label_str = f" ({labels[0]})" if labels else ""
                        citations.append(f"{name}{label_str}")

            logger.info(f"Tracked {len(citations)} citations")
            return citations

        except Exception as e:
            logger.error(f"Failed to track citations: {e}")
            return entity_ids  # Fallback to entity IDs

    def _retrieve_entities_by_semantic_search(
        self, query: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve entities using semantic search.

        Args:
            query: Search query
            top_k: Number of entities to retrieve

        Returns:
            List of entity dictionaries

        Raises:
            GraphRetrievalError: If retrieval fails
        """
        try:
            logger.info(f"Retrieving entities by semantic search (top_k={top_k})")

            # For now, use simple text matching as fallback
            # In production, this would use the semantic_search module
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    MATCH (n)
                    WHERE n.name CONTAINS $query
                       OR n.description CONTAINS $query
                    RETURN elementId(n) as id, n.name as name,
                           n.description as description,
                           labels(n) as labels
                    LIMIT $limit
                    """,
                    query=query,
                    limit=top_k,
                )

                entities = []
                for record in result:
                    entity_text = f"{record['name']}"
                    if record["description"]:
                        entity_text += f": {record['description']}"

                    entities.append(
                        {
                            "id": record["id"],
                            "text": entity_text,
                            "name": record["name"],
                            "labels": record["labels"],
                        }
                    )

            logger.info(f"Retrieved {len(entities)} entities")
            return entities

        except Exception as e:
            logger.error(f"Semantic search retrieval failed: {e}")
            raise GraphRetrievalError(f"Entity retrieval failed: {e}") from e

    def _retrieve_entities_by_graph_traversal(
        self, query: str, max_depth: int
    ) -> List[Dict[str, Any]]:
        """Retrieve entities using graph traversal.

        Args:
            query: Search query
            max_depth: Maximum traversal depth

        Returns:
            List of entity dictionaries
        """
        try:
            logger.info(f"Retrieving entities by graph traversal (depth={max_depth})")

            # Get seed nodes
            seed_entities = self._retrieve_entities_by_semantic_search(query, top_k=3)

            if not seed_entities:
                return []

            # Expand via graph traversal
            seed_ids = [e["id"] for e in seed_entities]
            expanded = self._expand_graph_context(seed_ids, max_depth)

            return expanded["entities"]

        except Exception as e:
            logger.error(f"Graph traversal retrieval failed: {e}")
            return []

    def _retrieve_entities_hybrid(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve entities using hybrid approach.

        Args:
            query: Search query
            top_k: Number of entities to retrieve

        Returns:
            List of entity dictionaries
        """
        try:
            logger.info(f"Retrieving entities with hybrid approach (top_k={top_k})")

            # Get semantic results
            semantic_entities = self._retrieve_entities_by_semantic_search(
                query, top_k=top_k // 2
            )

            # Get graph traversal results
            graph_entities = self._retrieve_entities_by_graph_traversal(
                query, max_depth=1
            )

            # Combine and deduplicate
            seen_ids = set()
            combined = []

            for entity in semantic_entities + graph_entities:
                if entity["id"] not in seen_ids:
                    seen_ids.add(entity["id"])
                    combined.append(entity)

                if len(combined) >= top_k:
                    break

            logger.info(f"Retrieved {len(combined)} entities using hybrid approach")
            return combined

        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            return []

    def _expand_graph_context(
        self, entity_ids: List[str], depth: int
    ) -> Dict[str, Any]:
        """Expand graph context from seed entities.

        Args:
            entity_ids: Seed entity IDs
            depth: Traversal depth

        Returns:
            Dictionary with entities and relationships

        Raises:
            GraphRetrievalError: If expansion fails
        """
        try:
            logger.info(f"Expanding graph context to depth {depth}")

            with self.neo4j_driver.session() as session:
                # Build variable-length path query
                result = session.run(
                    f"""
                    MATCH path = (start)-[*1..{depth}]-(connected)
                    WHERE elementId(start) IN $entity_ids
                    WITH nodes(path) as path_nodes, relationships(path) as path_rels
                    UNWIND path_nodes as node
                    WITH collect(DISTINCT node) as all_nodes, path_rels
                    UNWIND path_rels as rel
                    WITH all_nodes, collect(DISTINCT rel) as all_rels
                    RETURN all_nodes, all_rels
                    """,
                    entity_ids=entity_ids,
                )

                record = result.single()
                if not record:
                    return {"entities": [], "relationships": []}

                # Process entities
                entities = []
                for node in record["all_nodes"]:
                    entity_text = f"{node.get('name', 'Unknown')}"
                    if node.get("description"):
                        entity_text += f": {node['description']}"

                    entities.append(
                        {
                            "id": node.element_id,
                            "text": entity_text,
                            "name": node.get("name", "Unknown"),
                            "labels": list(node.labels),
                        }
                    )

                # Process relationships
                relationships = []
                for rel in record["all_rels"]:
                    relationships.append(
                        {
                            "source": rel.start_node.get("name", "Unknown"),
                            "type": rel.type,
                            "target": rel.end_node.get("name", "Unknown"),
                            "properties": dict(rel),
                        }
                    )

            logger.info(
                f"Expanded to {len(entities)} entities and "
                f"{len(relationships)} relationships"
            )
            return {"entities": entities, "relationships": relationships}

        except Exception as e:
            logger.error(f"Graph expansion failed: {e}")
            raise GraphRetrievalError(f"Graph expansion failed: {e}") from e

    def _format_graph_for_llm(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> str:
        """Format graph data for LLM prompt.

        Args:
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries

        Returns:
            Formatted string for LLM context
        """
        context_parts = []

        # Format entities
        if entities:
            context_parts.append("=== Knowledge Graph Entities ===")
            for i, entity in enumerate(entities, 1):
                labels = entity.get("labels", [])
                labels_str = f" [{', '.join(labels)}]" if labels else ""
                context_parts.append(f"{i}. {entity['text']}{labels_str}")

        # Format relationships
        if relationships:
            context_parts.append("\n=== Knowledge Graph Relationships ===")
            for i, rel in enumerate(relationships, 1):
                rel_str = f"{rel['source']} --[{rel['type']}]--> {rel['target']}"
                if rel.get("properties"):
                    props_str = ", ".join(
                        f"{k}={v}"
                        for k, v in rel["properties"].items()
                        if k not in ["source", "target", "type"]
                    )
                    if props_str:
                        rel_str += f" ({props_str})"
                context_parts.append(f"{i}. {rel_str}")

        return "\n".join(context_parts)

    def evaluate_answer_quality(
        self, question: str, answer: str, context: str
    ) -> float:
        """Evaluate the quality and confidence of the generated answer.

        Args:
            question: Original question
            answer: Generated answer
            context: Context used for generation

        Returns:
            Confidence score between 0 and 1
        """
        try:
            # Simple heuristic-based evaluation
            confidence = 0.5  # Base confidence

            # Check if answer uses context
            if context and any(
                phrase in answer.lower()
                for phrase in ["based on", "according to", "knowledge graph"]
            ):
                confidence += 0.2

            # Check answer length (reasonable answers are typically detailed)
            if len(answer.split()) > 20:
                confidence += 0.1

            # Check if answer acknowledges limitations
            if any(
                phrase in answer.lower()
                for phrase in ["cannot find", "not enough information", "unclear"]
            ):
                confidence -= 0.2

            # Check if question terms appear in answer
            question_terms = set(question.lower().split())
            answer_terms = set(answer.lower().split())
            overlap = len(question_terms & answer_terms) / len(question_terms)
            confidence += overlap * 0.2

            # Clamp to [0, 1]
            confidence = max(0.0, min(1.0, confidence))

            logger.info(f"Evaluated answer confidence: {confidence:.2f}")
            return confidence

        except Exception as e:
            logger.error(f"Failed to evaluate answer quality: {e}")
            return 0.5  # Default moderate confidence

    def close(self) -> None:
        """Close Neo4j connection and cleanup resources."""
        try:
            if self.neo4j_driver:
                self.neo4j_driver.close()
                logger.info("Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    def __enter__(self) -> "RAGIntegrator":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        self.close()


# Convenience functions for common use cases
def create_rag_system(
    neo4j_uri: str,
    neo4j_auth: Tuple[str, str],
    llm_provider: str = "openai",
    model_name: str = "gpt-4",
) -> RAGIntegrator:
    """Create a RAG system with default configuration.

    Args:
        neo4j_uri: Neo4j connection URI
        neo4j_auth: Neo4j authentication tuple
        llm_provider: LLM provider ('openai' or 'anthropic')
        model_name: LLM model name

    Returns:
        Initialized RAGIntegrator instance

    Example:
        >>> rag = create_rag_system(
        ...     "bolt://localhost:7687",
        ...     ("neo4j", "password"),
        ...     llm_provider="openai",
        ...     model_name="gpt-4"
        ... )
        >>> response = rag.query("What is machine learning?")
        >>> print(response.answer)
    """
    config = RAGConfig(
        llm_provider=llm_provider,
        model_name=model_name,
        neo4j_uri=neo4j_uri,
        auth=neo4j_auth,
    )
    return RAGIntegrator(config)


def query_knowledge_graph(
    question: str,
    neo4j_uri: str,
    neo4j_auth: Tuple[str, str],
    llm_provider: str = "openai",
    model_name: str = "gpt-4",
) -> str:
    """Simple one-shot query to knowledge graph.

    Args:
        question: Question to answer
        neo4j_uri: Neo4j connection URI
        neo4j_auth: Neo4j authentication tuple
        llm_provider: LLM provider
        model_name: LLM model name

    Returns:
        Generated answer string

    Example:
        >>> answer = query_knowledge_graph(
        ...     "What are the applications of AI?",
        ...     "bolt://localhost:7687",
        ...     ("neo4j", "password")
        ... )
        >>> print(answer)
    """
    with create_rag_system(neo4j_uri, neo4j_auth, llm_provider, model_name) as rag:
        response = rag.query(question)
        return response.answer
