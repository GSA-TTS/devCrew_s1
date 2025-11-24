"""
Semantic Search Engine for Knowledge Graph Management Platform.

This module provides semantic search capabilities using sentence transformers
and FAISS indexing for efficient similarity search over graph entities.

Part of devCrew_s1 TOOL-KNOWLEDGE-001 implementation (Issue #54).
"""

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from neo4j import GraphDatabase
from pydantic import BaseModel, Field, field_validator
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Custom Exceptions
class SearchError(Exception):
    """Base exception for search operations."""

    pass


class IndexNotFoundError(SearchError):
    """Raised when FAISS index is not found or not initialized."""

    pass


# Pydantic Models
class SearchConfig(BaseModel):
    """Configuration for semantic search engine.

    Attributes:
        embedding_model: Name of the sentence-transformers model to use
        index_type: Type of FAISS index (currently supports 'faiss')
        dimension: Dimension of embedding vectors
        similarity_metric: Distance metric ('cosine' or 'l2')
        top_k: Default number of results to return
        similarity_threshold: Minimum similarity score threshold
    """

    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence-transformers model name"
    )
    index_type: str = Field(
        default="faiss", description="Index type for similarity search"
    )
    dimension: int = Field(default=384, description="Embedding vector dimension")
    similarity_metric: str = Field(
        default="cosine", description="Similarity metric (cosine or l2)"
    )
    top_k: int = Field(
        default=10, description="Default number of results to return", gt=0
    )
    similarity_threshold: float = Field(
        default=0.7, description="Minimum similarity score threshold", ge=0.0, le=1.0
    )

    @field_validator("similarity_metric")
    @classmethod
    def validate_metric(cls, v: str) -> str:
        """Validate similarity metric."""
        if v not in ["cosine", "l2"]:
            raise ValueError("similarity_metric must be 'cosine' or 'l2'")
        return v

    @field_validator("index_type")
    @classmethod
    def validate_index_type(cls, v: str) -> str:
        """Validate index type."""
        if v != "faiss":
            raise ValueError("Currently only 'faiss' index_type is supported")
        return v


class SearchResult(BaseModel):
    """Result from semantic search operation.

    Attributes:
        entity_id: Unique identifier of the entity
        text: Text content of the entity
        score: Similarity score (0-1 for cosine, distance for L2)
        metadata: Additional metadata about the entity
        embedding: Optional embedding vector
    """

    entity_id: str = Field(description="Unique entity identifier")
    text: str = Field(description="Entity text content")
    score: float = Field(description="Similarity score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional entity metadata"
    )
    embedding: Optional[List[float]] = Field(
        default=None, description="Entity embedding vector"
    )

    model_config = {"arbitrary_types_allowed": True}


class SemanticSearchEngine:
    """Semantic search engine using sentence transformers and FAISS.

    This class provides semantic search capabilities over Neo4j graph entities
    using sentence-transformers for embeddings and FAISS for efficient
    similarity search.

    Attributes:
        config: Search configuration
        model: Sentence-transformers model
        index: FAISS index for similarity search
        entity_map: Mapping from index position to entity data
        neo4j_driver: Neo4j database driver
    """

    def __init__(
        self, config: SearchConfig, neo4j_uri: str, auth: Tuple[str, str]
    ) -> None:
        """Initialize the semantic search engine.

        Args:
            config: Search configuration
            neo4j_uri: Neo4j connection URI
            auth: Tuple of (username, password) for Neo4j

        Raises:
            SearchError: If initialization fails
        """
        try:
            self.config = config
            logger.info(
                f"Initializing SemanticSearchEngine with model "
                f"{config.embedding_model}"
            )

            # Initialize sentence-transformers model
            self.model = SentenceTransformer(config.embedding_model)
            logger.info("Sentence-transformers model loaded successfully")

            # Validate embedding dimension
            test_embedding = self.model.encode(["test"])
            actual_dim = test_embedding.shape[1]
            if actual_dim != config.dimension:
                logger.warning(
                    f"Configured dimension {config.dimension} does not match "
                    f"model dimension {actual_dim}. Updating configuration."
                )
                self.config.dimension = actual_dim

            # Initialize FAISS index
            self.index: Optional[faiss.Index] = None
            self.entity_map: Dict[int, Dict[str, Any]] = {}

            # Initialize Neo4j connection
            self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=auth)
            logger.info("Neo4j connection established")

            # Verify connection
            self.neo4j_driver.verify_connectivity()

        except Exception as e:
            logger.error(f"Failed to initialize SemanticSearchEngine: {e}")
            raise SearchError(f"Initialization failed: {e}") from e

    def _create_faiss_index(self, dimension: int) -> faiss.Index:
        """Create a FAISS index based on similarity metric.

        Args:
            dimension: Embedding vector dimension

        Returns:
            FAISS index instance
        """
        if self.config.similarity_metric == "cosine":
            # Use Inner Product for cosine similarity (with normalized vectors)
            index = faiss.IndexFlatIP(dimension)
            logger.info(f"Created FAISS IndexFlatIP with dimension {dimension}")
        else:  # l2
            # Use L2 distance
            index = faiss.IndexFlatL2(dimension)
            logger.info(f"Created FAISS IndexFlatL2 with dimension {dimension}")

        return index

    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            Numpy array of embeddings (num_texts x dimension)

        Raises:
            SearchError: If embedding generation fails
        """
        try:
            if not texts:
                return np.array([]).reshape(0, self.config.dimension)

            embeddings = self.model.encode(
                texts, show_progress_bar=len(texts) > 100, convert_to_numpy=True
            )

            # Normalize for cosine similarity
            if self.config.similarity_metric == "cosine":
                faiss.normalize_L2(embeddings)

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise SearchError(f"Embedding generation failed: {e}") from e

    def build_index(self, entity_type: Optional[str] = None) -> int:
        """Build FAISS index from Neo4j entities.

        Args:
            entity_type: Optional entity type filter (e.g., 'Person', 'Document')

        Returns:
            Number of entities indexed

        Raises:
            SearchError: If index building fails
        """
        try:
            logger.info(f"Building index for entity_type: {entity_type or 'all'}")

            # Fetch entities from Neo4j
            with self.neo4j_driver.session() as session:
                if entity_type:
                    query = """
                    MATCH (n)
                    WHERE $entity_type IN labels(n)
                    RETURN elementId(n) as id, n.name as name,
                           n.description as description,
                           labels(n) as labels, properties(n) as properties
                    """
                    result = session.run(query, entity_type=entity_type)
                else:
                    query = """
                    MATCH (n)
                    RETURN elementId(n) as id, n.name as name,
                           n.description as description,
                           labels(n) as labels, properties(n) as properties
                    """
                    result = session.run(query)

                entities = []
                for record in result:
                    entity_data = {
                        "id": record["id"],
                        "name": record["name"] or "",
                        "description": record["description"] or "",
                        "labels": record["labels"],
                        "properties": record["properties"],
                    }
                    entities.append(entity_data)

            if not entities:
                logger.warning("No entities found to index")
                return 0

            logger.info(f"Found {len(entities)} entities to index")

            # Create text representations for embedding
            texts = []
            for entity in entities:
                text_parts = []
                if entity["name"]:
                    text_parts.append(f"Name: {entity['name']}")
                if entity["description"]:
                    text_parts.append(f"Description: {entity['description']}")
                if entity["labels"]:
                    text_parts.append(f"Type: {', '.join(entity['labels'])}")

                # Add other relevant properties
                for key, value in entity["properties"].items():
                    if key not in ["name", "description"] and value:
                        text_parts.append(f"{key}: {value}")

                texts.append(" | ".join(text_parts))

            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self._generate_embeddings(texts)

            # Create FAISS index
            self.index = self._create_faiss_index(self.config.dimension)

            # Add embeddings to index
            self.index.add(embeddings)

            # Store entity mapping
            self.entity_map = {
                i: {
                    "entity_id": entities[i]["id"],
                    "text": texts[i],
                    "metadata": {
                        "name": entities[i]["name"],
                        "labels": entities[i]["labels"],
                        "properties": entities[i]["properties"],
                    },
                    "embedding": embeddings[i].tolist(),
                }
                for i in range(len(entities))
            }

            logger.info(f"Successfully built index with {len(entities)} entities")
            return len(entities)

        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            raise SearchError(f"Index building failed: {e}") from e

    def add_entities_to_index(self, entities: List[Dict[str, Any]]) -> bool:
        """Add entities to the existing FAISS index.

        Args:
            entities: List of entity dictionaries with keys:
                     - id: Entity ID
                     - text: Text content
                     - metadata: Optional metadata dict

        Returns:
            True if successful

        Raises:
            IndexNotFoundError: If index is not initialized
            SearchError: If adding entities fails
        """
        try:
            if self.index is None:
                raise IndexNotFoundError(
                    "Index not initialized. Call build_index first."
                )

            if not entities:
                logger.warning("No entities provided to add")
                return True

            logger.info(f"Adding {len(entities)} entities to index")

            # Extract texts
            texts = [e.get("text", "") for e in entities]

            # Generate embeddings
            embeddings = self._generate_embeddings(texts)

            # Add to index
            current_size = self.index.ntotal
            self.index.add(embeddings)

            # Update entity mapping
            for i, entity in enumerate(entities):
                idx = current_size + i
                self.entity_map[idx] = {
                    "entity_id": entity.get("id", f"entity_{idx}"),
                    "text": texts[i],
                    "metadata": entity.get("metadata", {}),
                    "embedding": embeddings[i].tolist(),
                }

            logger.info(
                f"Successfully added {len(entities)} entities. "
                f"Total index size: {self.index.ntotal}"
            )
            return True

        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to add entities: {e}")
            raise SearchError(f"Adding entities failed: {e}") from e

    def search(self, query: str, top_k: Optional[int] = None) -> List[SearchResult]:
        """Perform semantic search with the given query.

        Args:
            query: Search query string
            top_k: Number of results to return (uses config default if None)

        Returns:
            List of SearchResult objects ordered by similarity

        Raises:
            IndexNotFoundError: If index is not initialized
            SearchError: If search fails
        """
        try:
            if self.index is None:
                raise IndexNotFoundError(
                    "Index not initialized. Call build_index first."
                )

            if not query.strip():
                logger.warning("Empty query provided")
                return []

            k = top_k or self.config.top_k
            k = min(k, self.index.ntotal)  # Don't exceed index size

            logger.info(f"Searching for: '{query}' (top_k={k})")

            # Generate query embedding
            query_embedding = self._generate_embeddings([query])

            # Search index
            scores, indices = self.index.search(query_embedding, k)

            # Convert to SearchResult objects
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue

                entity_data = self.entity_map.get(idx)
                if entity_data is None:
                    logger.warning(f"Entity data not found for index {idx}")
                    continue

                # Convert score based on metric
                if self.config.similarity_metric == "cosine":
                    # Inner product score (already normalized)
                    similarity_score = float(score)
                else:  # l2
                    # Convert L2 distance to similarity score (smaller is better)
                    similarity_score = 1.0 / (1.0 + float(score))

                # Apply threshold
                if similarity_score < self.config.similarity_threshold:
                    continue

                result = SearchResult(
                    entity_id=entity_data["entity_id"],
                    text=entity_data["text"],
                    score=similarity_score,
                    metadata=entity_data["metadata"],
                    embedding=entity_data["embedding"],
                )
                results.append(result)

            logger.info(f"Found {len(results)} results above threshold")
            return results

        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Search operation failed: {e}") from e

    def hybrid_search(
        self, query: str, cypher_filter: str, top_k: int = 10
    ) -> List[SearchResult]:
        """Combine semantic search with Cypher graph filtering.

        Args:
            query: Semantic search query
            cypher_filter: Cypher query to filter entities (must return 'id')
            top_k: Number of results to return

        Returns:
            List of SearchResult objects

        Raises:
            SearchError: If hybrid search fails
        """
        try:
            logger.info(f"Performing hybrid search: '{query}'")

            # Get filtered entity IDs from Neo4j
            with self.neo4j_driver.session() as session:
                result = session.run(cypher_filter)
                filtered_ids = {record["id"] for record in result}

            if not filtered_ids:
                logger.warning("Cypher filter returned no entities")
                return []

            logger.info(f"Cypher filter returned {len(filtered_ids)} entities")

            # Perform semantic search
            all_results = self.search(query, top_k=top_k * 3)

            # Filter by Cypher results
            filtered_results = [r for r in all_results if r.entity_id in filtered_ids][
                :top_k
            ]

            logger.info(f"Hybrid search returned {len(filtered_results)} results")
            return filtered_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise SearchError(f"Hybrid search failed: {e}") from e

    def get_entity_embedding(self, entity_id: str) -> Optional[List[float]]:
        """Get the embedding vector for a specific entity.

        Args:
            entity_id: Entity identifier

        Returns:
            Embedding vector or None if not found
        """
        try:
            for entity_data in self.entity_map.values():
                if entity_data["entity_id"] == entity_id:
                    return entity_data["embedding"]

            logger.warning(f"Entity {entity_id} not found in index")
            return None

        except Exception as e:
            logger.error(f"Failed to get entity embedding: {e}")
            return None

    def get_similar_entities(
        self, entity_id: str, top_k: int = 10
    ) -> List[SearchResult]:
        """Find entities similar to a given entity.

        Args:
            entity_id: Entity identifier to find similar entities for
            top_k: Number of similar entities to return

        Returns:
            List of SearchResult objects

        Raises:
            SearchError: If operation fails
        """
        try:
            # Get entity embedding
            embedding = self.get_entity_embedding(entity_id)
            if embedding is None:
                raise SearchError(f"Entity {entity_id} not found in index")

            logger.info(f"Finding similar entities for {entity_id} (top_k={top_k})")

            # Convert to numpy array and reshape
            query_embedding = np.array([embedding], dtype=np.float32)

            # Normalize if using cosine similarity
            if self.config.similarity_metric == "cosine":
                faiss.normalize_L2(query_embedding)

            # Search (k+1 to account for the entity itself)
            k = min(top_k + 1, self.index.ntotal)
            scores, indices = self.index.search(query_embedding, k)

            # Convert to SearchResult objects
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue

                entity_data = self.entity_map.get(idx)
                if entity_data is None:
                    continue

                # Skip the entity itself
                if entity_data["entity_id"] == entity_id:
                    continue

                # Convert score
                if self.config.similarity_metric == "cosine":
                    similarity_score = float(score)
                else:
                    similarity_score = 1.0 / (1.0 + float(score))

                result = SearchResult(
                    entity_id=entity_data["entity_id"],
                    text=entity_data["text"],
                    score=similarity_score,
                    metadata=entity_data["metadata"],
                    embedding=entity_data["embedding"],
                )
                results.append(result)

            # Return top_k results (excluding the original entity)
            results = results[:top_k]
            logger.info(f"Found {len(results)} similar entities")
            return results

        except SearchError:
            raise
        except Exception as e:
            logger.error(f"Failed to find similar entities: {e}")
            raise SearchError(f"Similar entity search failed: {e}") from e

    def save_index(self, path: str) -> bool:
        """Serialize FAISS index and entity mapping to disk.

        Args:
            path: Directory path to save index files

        Returns:
            True if successful

        Raises:
            IndexNotFoundError: If index is not initialized
            SearchError: If save operation fails
        """
        try:
            if self.index is None:
                raise IndexNotFoundError("No index to save")

            save_path = Path(path)
            save_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"Saving index to {save_path}")

            # Save FAISS index
            index_file = save_path / "faiss_index.bin"
            faiss.write_index(self.index, str(index_file))
            logger.info(f"FAISS index saved to {index_file}")

            # Save entity mapping
            mapping_file = save_path / "entity_mapping.pkl"
            with open(mapping_file, "wb") as f:
                pickle.dump(self.entity_map, f)
            logger.info(f"Entity mapping saved to {mapping_file}")

            # Save configuration
            config_file = save_path / "config.pkl"
            with open(config_file, "wb") as f:
                pickle.dump(self.config.model_dump(), f)
            logger.info(f"Configuration saved to {config_file}")

            return True

        except IndexNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise SearchError(f"Index save failed: {e}") from e

    def load_index(self, path: str) -> bool:
        """Load FAISS index and entity mapping from disk.

        Args:
            path: Directory path containing index files

        Returns:
            True if successful

        Raises:
            SearchError: If load operation fails
        """
        try:
            load_path = Path(path)
            if not load_path.exists():
                raise SearchError(f"Index path does not exist: {path}")

            logger.info(f"Loading index from {load_path}")

            # Load FAISS index
            index_file = load_path / "faiss_index.bin"
            if not index_file.exists():
                raise SearchError(f"Index file not found: {index_file}")
            self.index = faiss.read_index(str(index_file))
            logger.info(f"FAISS index loaded from {index_file}")

            # Load entity mapping
            mapping_file = load_path / "entity_mapping.pkl"
            if not mapping_file.exists():
                raise SearchError(f"Mapping file not found: {mapping_file}")
            with open(mapping_file, "rb") as f:
                self.entity_map = pickle.load(f)
            logger.info(f"Entity mapping loaded from {mapping_file}")

            # Load configuration (optional, for validation)
            config_file = load_path / "config.pkl"
            if config_file.exists():
                with open(config_file, "rb") as f:
                    saved_config = pickle.load(f)
                logger.info(f"Loaded configuration: {saved_config}")

            logger.info(f"Successfully loaded index with {self.index.ntotal} entities")
            return True

        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            raise SearchError(f"Index load failed: {e}") from e

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index.

        Returns:
            Dictionary with index statistics
        """
        if self.index is None:
            return {"initialized": False, "size": 0, "dimension": self.config.dimension}

        return {
            "initialized": True,
            "size": self.index.ntotal,
            "dimension": self.config.dimension,
            "similarity_metric": self.config.similarity_metric,
            "model": self.config.embedding_model,
            "entity_count": len(self.entity_map),
        }

    def close(self) -> None:
        """Close Neo4j connection and cleanup resources."""
        try:
            if self.neo4j_driver:
                self.neo4j_driver.close()
                logger.info("Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    def __enter__(self) -> "SemanticSearchEngine":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        self.close()
