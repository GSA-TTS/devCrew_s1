"""
Knowledge Indexer for Web Research Platform.

Provides semantic indexing and search capabilities using Sentence Transformers
and ChromaDB. Supports text chunking, embedding generation, vector database
operations, and semantic search with metadata filtering.
"""

import hashlib
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
import torch
from chromadb.config import Settings
from pydantic import BaseModel, Field, field_validator
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class VectorDB(str, Enum):
    """Supported vector database backends."""

    CHROMADB = "chromadb"
    WEAVIATE = "weaviate"
    INMEMORY = "inmemory"


class IndexingError(Exception):
    """Base exception for indexing operations."""

    pass


class EmbeddingError(IndexingError):
    """Exception raised when embedding generation fails."""

    pass


class VectorDBError(IndexingError):
    """Exception raised when vector database operations fail."""

    pass


class IndexConfig(BaseModel):
    """Configuration for knowledge indexing operations."""

    vector_db: VectorDB = Field(
        default=VectorDB.CHROMADB,
        description="Vector database backend to use",
    )
    collection_name: str = Field(
        default="web_research",
        description="Name of the collection to store embeddings",
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model name",
    )
    chunk_size: int = Field(
        default=512,
        ge=100,
        le=2048,
        description="Maximum characters per text chunk",
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=512,
        description="Overlap between consecutive chunks",
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for search results",
    )
    persist_directory: Optional[str] = Field(
        default=None,
        description="Directory for persisting vector database",
    )
    batch_size: int = Field(
        default=32,
        ge=1,
        le=256,
        description="Batch size for embedding generation",
    )
    device: Optional[str] = Field(
        default=None,
        description="Device for model inference (cuda/cpu)",
    )

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:  # noqa: E501
        """Ensure overlap is less than chunk size."""
        if "chunk_size" in info.data and v >= info.data["chunk_size"]:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v

    class Config:
        """Pydantic config."""

        use_enum_values = True


class TextChunk(BaseModel):
    """Model for text chunks with embeddings."""

    text: str = Field(description="The chunk text content")
    chunk_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the chunk",
    )
    document_id: str = Field(description="Identifier of source document")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the chunk",
    )
    embedding: Optional[List[float]] = Field(
        default=None,
        description="Vector embedding of the chunk",
    )
    chunk_index: int = Field(
        default=0,
        description="Position of chunk in document",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of chunk creation",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary format."""
        return {
            "text": self.text,
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "metadata": self.metadata,
            "chunk_index": self.chunk_index,
            "created_at": self.created_at.isoformat(),
        }


class SemanticSearchResult(BaseModel):
    """Model for semantic search results."""

    text: str = Field(description="Matched text content")
    score: float = Field(description="Similarity score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Associated metadata",
    )
    document_id: str = Field(description="Source document identifier")
    chunk_id: str = Field(description="Chunk identifier")
    distance: Optional[float] = Field(
        default=None,
        description="Distance metric (if available)",
    )

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class EmbeddingStats(BaseModel):
    """Statistics for embeddings in a collection."""

    total_chunks: int = Field(description="Total number of chunks")
    total_embeddings: int = Field(description="Total number of embeddings")
    avg_chunk_size: float = Field(description="Average chunk size in chars")
    model_name: str = Field(description="Embedding model used")
    collection_name: str = Field(description="Collection name")
    total_documents: int = Field(
        default=0,
        description="Total unique documents",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Stats generation timestamp",
    )
    dimension: int = Field(
        default=384,
        description="Embedding vector dimension",
    )


class IndexStats(BaseModel):
    """Statistics for batch indexing operations."""

    total_articles: int = Field(description="Total articles processed")
    total_chunks: int = Field(description="Total chunks created")
    total_embeddings: int = Field(description="Total embeddings generated")
    successful_indices: int = Field(description="Successfully indexed chunks")
    failed_indices: int = Field(description="Failed indexing operations")
    processing_time: float = Field(description="Total processing time in sec")
    avg_chunks_per_article: float = Field(description="Average chunks per article")
    errors: List[str] = Field(
        default_factory=list,
        description="List of errors encountered",
    )


@dataclass
class ExtractedArticle:
    """
    Placeholder for ExtractedArticle model.

    Imported from content_extractor in production use.
    """

    url: str
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.utcnow)


class KnowledgeIndexer:
    """
    Knowledge indexer for semantic search and RAG applications.

    Provides text chunking, embedding generation, vector database indexing,
    and semantic search capabilities using Sentence Transformers and ChromaDB.
    """

    def __init__(self, config: IndexConfig):
        """
        Initialize the knowledge indexer.

        Args:
            config: Configuration for indexing operations

        Raises:
            EmbeddingError: If model loading fails
            VectorDBError: If database initialization fails
        """
        self.config = config
        self._embedding_model: Optional[SentenceTransformer] = None
        self._chroma_client: Optional[chromadb.Client] = None
        self._collections: Dict[str, Any] = {}

        logger.info(f"Initializing KnowledgeIndexer with {config.vector_db} backend")

        try:
            self._initialize_embedding_model()
            self._initialize_vector_db()
        except Exception as e:
            logger.error(f"Failed to initialize KnowledgeIndexer: {e}")
            raise

    def _initialize_embedding_model(self) -> None:
        """
        Initialize the sentence transformer model.

        Raises:
            EmbeddingError: If model loading fails
        """
        try:
            device = self.config.device
            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"

            logger.info(
                f"Loading embedding model: {self.config.embedding_model} "
                f"on {device}"
            )

            self._embedding_model = SentenceTransformer(
                self.config.embedding_model,
                device=device,
            )

            logger.info(
                f"Model loaded successfully. "
                f"Embedding dimension: "
                f"{self._embedding_model.get_sentence_embedding_dimension()}"
            )

        except Exception as e:
            error_msg = f"Failed to load embedding model: {e}"
            logger.error(error_msg)
            raise EmbeddingError(error_msg) from e

    def _initialize_vector_db(self) -> None:
        """
        Initialize the vector database client.

        Raises:
            VectorDBError: If database initialization fails
        """
        try:
            if self.config.vector_db == VectorDB.CHROMADB:
                self._initialize_chromadb()
            elif self.config.vector_db == VectorDB.INMEMORY:
                self._initialize_inmemory_db()
            elif self.config.vector_db == VectorDB.WEAVIATE:
                raise NotImplementedError("Weaviate backend not yet implemented")
            else:
                raise VectorDBError(f"Unsupported vector DB: {self.config.vector_db}")

            logger.info(f"Vector database initialized: {self.config.vector_db}")

        except Exception as e:
            error_msg = f"Failed to initialize vector database: {e}"
            logger.error(error_msg)
            raise VectorDBError(error_msg) from e

    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB client."""
        if self.config.persist_directory:
            persist_path = Path(self.config.persist_directory)
            persist_path.mkdir(parents=True, exist_ok=True)

            settings = Settings(
                persist_directory=str(persist_path),
                anonymized_telemetry=False,
            )
            self._chroma_client = chromadb.Client(settings)
            logger.info(f"ChromaDB persisting to: {persist_path}")
        else:
            self._chroma_client = chromadb.Client()
            logger.info("ChromaDB running in-memory mode")

    def _initialize_inmemory_db(self) -> None:
        """Initialize in-memory database (for testing)."""
        self._chroma_client = chromadb.Client()
        logger.info("Using in-memory vector database")

    def chunk_content(
        self,
        content: str,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
    ) -> List[TextChunk]:
        """
        Split content into overlapping chunks.

        Args:
            content: Text content to chunk
            chunk_size: Maximum characters per chunk (uses config default)
            overlap: Overlap between chunks (uses config default)

        Returns:
            List of TextChunk objects

        Raises:
            IndexingError: If chunking fails
        """
        try:
            chunk_size = chunk_size or self.config.chunk_size
            overlap = overlap or self.config.chunk_overlap

            if not content or not content.strip():
                logger.warning("Empty content provided for chunking")
                return []

            # Clean content
            content = self._clean_text(content)

            # Split into sentences for smarter chunking
            sentences = self._split_into_sentences(content)

            chunks: List[TextChunk] = []
            current_chunk = ""
            chunk_index = 0

            for sentence in sentences:
                # If single sentence exceeds chunk size, split it
                if len(sentence) > chunk_size:
                    if current_chunk:
                        chunks.append(
                            self._create_text_chunk(
                                current_chunk.strip(),
                                chunk_index,
                            )
                        )
                        chunk_index += 1
                        current_chunk = ""

                    # Split long sentence by words
                    words = sentence.split()
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk) + len(word) + 1 <= chunk_size:
                            temp_chunk += " " + word if temp_chunk else word
                        else:
                            if temp_chunk:
                                chunks.append(
                                    self._create_text_chunk(
                                        temp_chunk.strip(),
                                        chunk_index,
                                    )
                                )
                                chunk_index += 1
                            temp_chunk = word

                    if temp_chunk:
                        current_chunk = temp_chunk
                    continue

                # Check if adding sentence exceeds chunk size
                test_chunk = (
                    current_chunk + " " + sentence if current_chunk else sentence
                )

                if len(test_chunk) <= chunk_size:
                    current_chunk = test_chunk
                else:
                    # Save current chunk
                    if current_chunk:
                        chunks.append(
                            self._create_text_chunk(
                                current_chunk.strip(),
                                chunk_index,
                            )
                        )
                        chunk_index += 1

                    # Start new chunk with overlap
                    if overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-overlap:]
                        current_chunk = overlap_text + " " + sentence
                    else:
                        current_chunk = sentence

            # Add final chunk
            if current_chunk:
                chunks.append(
                    self._create_text_chunk(current_chunk.strip(), chunk_index)
                )

            logger.info(f"Created {len(chunks)} chunks from {len(content)} chars")
            return chunks

        except Exception as e:
            error_msg = f"Failed to chunk content: {e}"
            logger.error(error_msg)
            raise IndexingError(error_msg) from e

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace and normalizing.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove multiple spaces
        text = re.sub(r"\s+", " ", text)
        # Remove leading/trailing whitespace
        text = text.strip()
        # Normalize line breaks
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with spaCy)
        sentence_endings = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def _create_text_chunk(
        self,
        text: str,
        chunk_index: int,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TextChunk:
        """
        Create a TextChunk object.

        Args:
            text: Chunk text
            chunk_index: Position in document
            document_id: Source document ID
            metadata: Additional metadata

        Returns:
            TextChunk object
        """
        if document_id is None:
            # Generate document ID from text hash (not for security)
            document_id = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()[
                :16
            ]

        return TextChunk(
            text=text,
            document_id=document_id,
            chunk_index=chunk_index,
            metadata=metadata or {},
        )

    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing (uses config default)

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            if not texts:
                return []

            if self._embedding_model is None:
                raise EmbeddingError("Embedding model not initialized")

            batch_size = batch_size or self.config.batch_size

            logger.info(f"Generating embeddings for {len(texts)} texts")

            # Generate embeddings
            embeddings = self._embedding_model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100,
                convert_to_numpy=True,
            )

            # Convert to list format
            embeddings_list = embeddings.tolist()

            logger.info(
                f"Generated {len(embeddings_list)} embeddings, "
                f"dim={len(embeddings_list[0])}"
            )

            return embeddings_list

        except Exception as e:
            error_msg = f"Failed to generate embeddings: {e}"
            logger.error(error_msg)
            raise EmbeddingError(error_msg) from e

    def index_to_vectordb(
        self,
        chunks: List[TextChunk],
        embeddings: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Index chunks and embeddings to vector database.

        Args:
            chunks: List of text chunks
            embeddings: Corresponding embeddings
            metadata: Additional metadata to store

        Returns:
            True if successful

        Raises:
            VectorDBError: If indexing fails
        """
        try:
            if len(chunks) != len(embeddings):
                raise VectorDBError(
                    f"Chunks ({len(chunks)}) and embeddings "
                    f"({len(embeddings)}) count mismatch"
                )

            if not chunks:
                logger.warning("No chunks to index")
                return True

            # Get or create collection
            collection = self._get_or_create_collection(self.config.collection_name)

            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.text for chunk in chunks]

            # Merge chunk metadata with additional metadata
            metadatas = []
            for chunk in chunks:
                chunk_meta = chunk.metadata.copy()
                chunk_meta["document_id"] = chunk.document_id
                chunk_meta["chunk_index"] = chunk.chunk_index
                chunk_meta["created_at"] = chunk.created_at.isoformat()

                if metadata:
                    chunk_meta.update(metadata)

                metadatas.append(chunk_meta)

            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

            logger.info(
                f"Indexed {len(chunks)} chunks to collection "
                f"'{self.config.collection_name}'"
            )

            return True

        except Exception as e:
            error_msg = f"Failed to index to vector database: {e}"
            logger.error(error_msg)
            raise VectorDBError(error_msg) from e

    def _get_or_create_collection(self, collection_name: str) -> Any:
        """
        Get or create a ChromaDB collection.

        Args:
            collection_name: Name of the collection

        Returns:
            ChromaDB collection object
        """
        if collection_name in self._collections:
            return self._collections[collection_name]

        try:
            if self._chroma_client is None:
                raise VectorDBError("ChromaDB client not initialized")

            collection = self._chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._collections[collection_name] = collection
            logger.info(f"Using collection: {collection_name}")
            return collection

        except Exception as e:
            raise VectorDBError(
                f"Failed to get/create collection '{collection_name}': {e}"
            ) from e

    def batch_index(
        self,
        articles: List[ExtractedArticle],
        show_progress: bool = True,
    ) -> IndexStats:
        """
        Batch index multiple articles.

        Args:
            articles: List of ExtractedArticle objects
            show_progress: Whether to show progress bar

        Returns:
            IndexStats with processing statistics

        Raises:
            IndexingError: If batch indexing fails
        """
        import time

        start_time = time.time()

        stats = IndexStats(
            total_articles=len(articles),
            total_chunks=0,
            total_embeddings=0,
            successful_indices=0,
            failed_indices=0,
            processing_time=0.0,
            avg_chunks_per_article=0.0,
            errors=[],
        )

        if not articles:
            logger.warning("No articles provided for batch indexing")
            return stats

        logger.info(f"Starting batch indexing of {len(articles)} articles")

        all_chunks: List[TextChunk] = []
        chunk_count_per_article: List[int] = []

        # Phase 1: Chunk all articles
        for idx, article in enumerate(articles):
            try:
                # Create chunks with article-specific document_id
                doc_id = self._generate_document_id(article)

                chunks = self.chunk_content(article.content)

                # Update chunks with document_id and metadata
                for chunk in chunks:
                    chunk.document_id = doc_id
                    chunk.metadata.update(
                        {
                            "title": article.title,
                            "url": article.url,
                            "extracted_at": article.extracted_at.isoformat(),
                            **article.metadata,
                        }
                    )

                all_chunks.extend(chunks)
                chunk_count_per_article.append(len(chunks))

                logger.debug(
                    f"Article {idx + 1}/{len(articles)}: "
                    f"{len(chunks)} chunks created"
                )

            except Exception as e:
                error_msg = f"Failed to chunk article '{article.title}': {e}"
                logger.error(error_msg)
                stats.errors.append(error_msg)
                stats.failed_indices += 1
                chunk_count_per_article.append(0)

        stats.total_chunks = len(all_chunks)

        if not all_chunks:
            logger.warning("No chunks created from articles")
            stats.processing_time = time.time() - start_time
            return stats

        # Phase 2: Generate embeddings in batches
        try:
            texts = [chunk.text for chunk in all_chunks]
            embeddings = self.generate_embeddings(
                texts,
                batch_size=self.config.batch_size,
            )
            stats.total_embeddings = len(embeddings)

            # Assign embeddings to chunks
            for chunk, embedding in zip(all_chunks, embeddings):
                chunk.embedding = embedding

        except Exception as e:
            error_msg = f"Failed to generate embeddings: {e}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
            stats.processing_time = time.time() - start_time
            return stats

        # Phase 3: Index to vector database
        try:
            success = self.index_to_vectordb(all_chunks, embeddings)

            if success:
                stats.successful_indices = len(all_chunks)
            else:
                stats.failed_indices = len(all_chunks)
                stats.errors.append("Vector DB indexing returned False")

        except Exception as e:
            error_msg = f"Failed to index to vector database: {e}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
            stats.failed_indices = len(all_chunks)

        # Calculate statistics
        stats.processing_time = time.time() - start_time

        if stats.total_articles > 0:
            stats.avg_chunks_per_article = stats.total_chunks / stats.total_articles

        logger.info(
            f"Batch indexing completed: {stats.total_articles} articles, "
            f"{stats.total_chunks} chunks, "
            f"{stats.successful_indices} successful, "
            f"{stats.failed_indices} failed, "
            f"time={stats.processing_time:.2f}s"
        )

        return stats

    def _generate_document_id(self, article: ExtractedArticle) -> str:
        """
        Generate a unique document ID for an article.

        Args:
            article: ExtractedArticle object

        Returns:
            Document ID string
        """
        # Use URL as primary identifier
        content = f"{article.url}_{article.title}"
        content_bytes = content.encode() if content else b""
        return hashlib.sha256(content_bytes).hexdigest()[:32]

    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,
    ) -> List[SemanticSearchResult]:
        """
        Perform semantic search with natural language query.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            filters: Metadata filters (ChromaDB where clause)
            collection_name: Collection to search (uses default if None)

        Returns:
            List of SemanticSearchResult objects

        Raises:
            VectorDBError: If search fails
        """
        try:
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")

            collection_name = collection_name or self.config.collection_name

            # Get collection
            if self._chroma_client is None:
                raise VectorDBError("ChromaDB client not initialized")

            collection = self._get_or_create_collection(collection_name)

            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]

            # Prepare where clause
            where_clause = filters if filters else None

            # Search in ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
            )

            # Parse results
            search_results = self._parse_search_results(results)

            # Filter by similarity threshold
            filtered_results = [
                r for r in search_results if r.score >= self.config.similarity_threshold
            ]

            logger.info(
                f"Semantic search returned {len(filtered_results)} results "
                f"(threshold={self.config.similarity_threshold})"
            )

            return filtered_results

        except Exception as e:
            error_msg = f"Semantic search failed: {e}"
            logger.error(error_msg)
            raise VectorDBError(error_msg) from e

    def _parse_search_results(
        self,
        results: Dict[str, Any],
    ) -> List[SemanticSearchResult]:
        """
        Parse ChromaDB search results into SemanticSearchResult objects.

        Args:
            results: Raw ChromaDB results

        Returns:
            List of SemanticSearchResult objects
        """
        search_results = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        for doc, meta, dist, doc_id in zip(documents, metadatas, distances, ids):
            # Convert distance to similarity score (cosine)
            score = 1.0 - dist

            search_result = SemanticSearchResult(
                text=doc,
                score=score,
                metadata=meta,
                document_id=meta.get("document_id", "unknown"),
                chunk_id=doc_id,
                distance=dist,
            )

            search_results.append(search_result)

        return search_results

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from the vector database.

        Args:
            collection_name: Name of collection to delete

        Returns:
            True if successful

        Raises:
            VectorDBError: If deletion fails
        """
        try:
            if self._chroma_client is None:
                raise VectorDBError("ChromaDB client not initialized")

            self._chroma_client.delete_collection(name=collection_name)

            # Remove from cache
            if collection_name in self._collections:
                del self._collections[collection_name]

            logger.info(f"Deleted collection: {collection_name}")
            return True

        except Exception as e:
            error_msg = f"Failed to delete collection '{collection_name}': {e}"
            logger.error(error_msg)
            raise VectorDBError(error_msg) from e

    def list_collections(self) -> List[str]:
        """
        List all collections in the vector database.

        Returns:
            List of collection names

        Raises:
            VectorDBError: If listing fails
        """
        try:
            if self._chroma_client is None:
                raise VectorDBError("ChromaDB client not initialized")

            collections = self._chroma_client.list_collections()
            collection_names = [col.name for col in collections]

            logger.info(f"Found {len(collection_names)} collections")
            return collection_names

        except Exception as e:
            error_msg = f"Failed to list collections: {e}"
            logger.error(error_msg)
            raise VectorDBError(error_msg) from e

    def get_collection_stats(
        self,
        collection_name: Optional[str] = None,
    ) -> EmbeddingStats:
        """
        Get statistics for a collection.

        Args:
            collection_name: Collection name (uses default if None)

        Returns:
            EmbeddingStats object

        Raises:
            VectorDBError: If stats retrieval fails
        """
        try:
            collection_name = collection_name or self.config.collection_name
            collection = self._get_or_create_collection(collection_name)

            # Get collection count
            count = collection.count()

            if count == 0:
                if self._embedding_model is None:
                    raise EmbeddingError("Embedding model not initialized")

                return EmbeddingStats(
                    total_chunks=0,
                    total_embeddings=0,
                    avg_chunk_size=0.0,
                    model_name=self.config.embedding_model,
                    collection_name=collection_name,
                    total_documents=0,
                    dimension=self._embedding_model.get_sentence_embedding_dimension(),  # noqa: E501
                )

            # Get all data for statistics
            results = collection.get(
                limit=count,
                include=["documents", "metadatas"],
            )

            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])

            # Calculate statistics
            total_chars = sum(len(doc) for doc in documents)
            avg_chunk_size = total_chars / len(documents) if documents else 0.0

            # Count unique documents
            unique_docs = set()
            for meta in metadatas:
                if "document_id" in meta:
                    unique_docs.add(meta["document_id"])

            if self._embedding_model is None:
                raise EmbeddingError("Embedding model not initialized")

            stats = EmbeddingStats(
                total_chunks=len(documents),
                total_embeddings=count,
                avg_chunk_size=avg_chunk_size,
                model_name=self.config.embedding_model,
                collection_name=collection_name,
                total_documents=len(unique_docs),
                dimension=self._embedding_model.get_sentence_embedding_dimension(),  # noqa: E501
            )

            logger.info(
                f"Collection '{collection_name}' stats: "
                f"{stats.total_chunks} chunks, "
                f"{stats.total_documents} documents"
            )

            return stats

        except Exception as e:
            error_msg = f"Failed to get stats for collection '{collection_name}': {e}"
            logger.error(error_msg)
            raise VectorDBError(error_msg) from e

    def update_chunk_metadata(
        self,
        chunk_id: str,
        metadata: Dict[str, Any],
        collection_name: Optional[str] = None,
    ) -> bool:
        """
        Update metadata for a specific chunk.

        Args:
            chunk_id: ID of chunk to update
            metadata: New metadata to merge
            collection_name: Collection name (uses default if None)

        Returns:
            True if successful

        Raises:
            VectorDBError: If update fails
        """
        try:
            collection_name = collection_name or self.config.collection_name
            collection = self._get_or_create_collection(collection_name)

            # Get existing metadata
            result = collection.get(ids=[chunk_id], include=["metadatas"])

            if not result["ids"]:
                raise VectorDBError(f"Chunk ID '{chunk_id}' not found")

            existing_meta = result["metadatas"][0]
            updated_meta = {**existing_meta, **metadata}

            # Update in ChromaDB
            collection.update(
                ids=[chunk_id],
                metadatas=[updated_meta],
            )

            logger.info(f"Updated metadata for chunk: {chunk_id}")
            return True

        except Exception as e:
            error_msg = f"Failed to update chunk metadata: {e}"
            logger.error(error_msg)
            raise VectorDBError(error_msg) from e

    def delete_by_document_id(
        self,
        document_id: str,
        collection_name: Optional[str] = None,
    ) -> int:
        """
        Delete all chunks belonging to a document.

        Args:
            document_id: Document ID to delete
            collection_name: Collection name (uses default if None)

        Returns:
            Number of chunks deleted

        Raises:
            VectorDBError: If deletion fails
        """
        try:
            collection_name = collection_name or self.config.collection_name
            collection = self._get_or_create_collection(collection_name)

            # Query for chunks with this document_id
            results = collection.get(
                where={"document_id": document_id},
                include=["metadatas"],
            )

            chunk_ids = results["ids"]

            if not chunk_ids:
                logger.info(f"No chunks found for document_id: {document_id}")
                return 0

            # Delete chunks
            collection.delete(ids=chunk_ids)

            logger.info(f"Deleted {len(chunk_ids)} chunks for document: {document_id}")
            return len(chunk_ids)

        except Exception as e:
            error_msg = f"Failed to delete by document_id: {e}"
            logger.error(error_msg)
            raise VectorDBError(error_msg) from e

    def hybrid_search(
        self,
        query: str,
        filters: Dict[str, Any],
        top_k: int = 10,
        collection_name: Optional[str] = None,
    ) -> List[SemanticSearchResult]:
        """
        Perform hybrid search combining semantic search and metadata filtering.

        Args:
            query: Natural language query
            filters: Metadata filters to apply
            top_k: Number of results
            collection_name: Collection to search

        Returns:
            List of SemanticSearchResult objects
        """
        logger.info(f"Hybrid search: query='{query}', filters={filters}")

        return self.semantic_search(
            query=query,
            top_k=top_k,
            filters=filters,
            collection_name=collection_name,
        )

    def get_chunk_by_id(
        self,
        chunk_id: str,
        collection_name: Optional[str] = None,
    ) -> Optional[TextChunk]:
        """
        Retrieve a specific chunk by ID.

        Args:
            chunk_id: Chunk ID to retrieve
            collection_name: Collection name (uses default if None)

        Returns:
            TextChunk object if found, None otherwise

        Raises:
            VectorDBError: If retrieval fails
        """
        try:
            collection_name = collection_name or self.config.collection_name
            collection = self._get_or_create_collection(collection_name)

            result = collection.get(
                ids=[chunk_id],
                include=["documents", "metadatas", "embeddings"],
            )

            if not result["ids"]:
                logger.warning(f"Chunk not found: {chunk_id}")
                return None

            chunk = TextChunk(
                text=result["documents"][0],
                chunk_id=result["ids"][0],
                document_id=result["metadatas"][0].get("document_id", "unknown"),
                metadata=result["metadatas"][0],
                embedding=result["embeddings"][0] if result["embeddings"] else None,
                chunk_index=result["metadatas"][0].get("chunk_index", 0),
            )

            return chunk

        except Exception as e:
            error_msg = f"Failed to get chunk by ID: {e}"
            logger.error(error_msg)
            raise VectorDBError(error_msg) from e

    def clear_cache(self) -> None:
        """Clear the collection cache."""
        self._collections.clear()
        logger.info("Collection cache cleared")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.

        Returns:
            Dictionary with model information
        """
        if self._embedding_model is None:
            raise EmbeddingError("Embedding model not initialized")

        return {
            "model_name": self.config.embedding_model,
            "dimension": self._embedding_model.get_sentence_embedding_dimension(),  # noqa: E501
            "max_seq_length": self._embedding_model.max_seq_length,
            "device": str(self._embedding_model.device),
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"KnowledgeIndexer(backend={self.config.vector_db}, "
            f"model={self.config.embedding_model}, "
            f"collection={self.config.collection_name})"
        )
