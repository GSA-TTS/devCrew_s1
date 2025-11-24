"""
Similarity-Based Cache Matching System.

This module provides semantic similarity matching for LLM cache lookups using
sentence transformers and vector embeddings for fuzzy cache retrieval.

Author: devCrew_s1
License: MIT
"""

import json
import logging
import pickle
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field, field_validator
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingModel(str, Enum):
    """Supported embedding models."""

    MINILM = "all-MiniLM-L6-v2"  # Fast, 384 dimensions
    MPNET = "all-mpnet-base-v2"  # Balanced, 768 dimensions
    INSTRUCTOR = "hkunlp/instructor-base"  # High quality, 768 dimensions
    MINILM_L12 = "all-MiniLM-L12-v2"  # Better quality, 384 dimensions
    DISTILBERT = "distilbert-base-nli-stsb-mean-tokens"  # 768 dimensions


class SimilarityMetric(str, Enum):
    """Similarity computation metrics."""

    COSINE = "cosine"
    DOT_PRODUCT = "dot_product"
    EUCLIDEAN = "euclidean"


class SimilarityConfig(BaseModel):
    """Configuration for similarity matching."""

    model_name: EmbeddingModel = Field(
        default=EmbeddingModel.MINILM, description="Embedding model to use"
    )
    threshold: float = Field(
        default=0.85, description="Minimum similarity threshold (0-1)"
    )
    top_k: int = Field(default=5, description="Number of top matches to return")
    batch_size: int = Field(default=32, description="Batch size for embeddings")
    max_cache_embeddings: int = Field(
        default=10000, description="Maximum embeddings to keep in memory"
    )
    metric: SimilarityMetric = Field(
        default=SimilarityMetric.COSINE, description="Similarity metric"
    )
    normalize_embeddings: bool = Field(
        default=True, description="Normalize embeddings for cosine similarity"
    )
    enable_persistence: bool = Field(
        default=True, description="Persist embeddings to disk"
    )
    persistence_path: str = Field(
        default="./cache_embeddings", description="Path for embedding persistence"
    )
    device: Optional[str] = Field(
        default=None, description="Device for model (cpu/cuda/mps)"
    )

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate similarity threshold."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Threshold must be between 0 and 1")
        return v

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        """Validate top_k is positive."""
        if v <= 0:
            raise ValueError("top_k must be positive")
        return v

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        """Validate batch_size is positive."""
        if v <= 0:
            raise ValueError("batch_size must be positive")
        return v


class SimilarMatch(BaseModel):
    """Similarity match result."""

    prompt: str = Field(description="Matched prompt text")
    response: str = Field(description="Cached response text")
    similarity_score: float = Field(description="Similarity score (0-1)")
    cache_key: str = Field(description="Cache key for this match")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    prompt_hash: str = Field(description="Hash of the matched prompt")
    token_count: Optional[int] = Field(default=None, description="Token count")
    model_name: Optional[str] = Field(default=None, description="Model name")
    rank: int = Field(default=0, description="Rank in similarity results (1-based)")

    @field_validator("similarity_score")
    @classmethod
    def validate_similarity_score(cls, v: float) -> float:
        """Validate similarity score."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Similarity score must be between 0 and 1")
        return v


class EmbeddingIndex(BaseModel):
    """Index entry for cached embedding."""

    cache_key: str = Field(description="Cache key")
    prompt: str = Field(description="Original prompt")
    embedding: List[float] = Field(description="Embedding vector")
    prompt_hash: str = Field(description="Hash of prompt")
    timestamp: float = Field(description="Index timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    def get_embedding_array(self) -> np.ndarray:
        """Get embedding as numpy array."""
        return np.array(self.embedding, dtype=np.float32)


class SimilarityMatcher:
    """
    Semantic similarity matcher for fuzzy cache lookups.

    Provides similarity-based cache retrieval using sentence transformers and
    vector embeddings to find semantically similar prompts in the cache.

    Examples:
        >>> from llm_cache import LLMCache, CacheConfig
        >>> config = SimilarityConfig(threshold=0.85, top_k=3)
        >>> cache = LLMCache(CacheConfig())
        >>> matcher = SimilarityMatcher(config, cache)
        >>> matches = matcher.find_similar("What is machine learning?", top_k=5)
        >>> for match in matches:
        ...     print(f"{match.similarity_score:.2f}: {match.prompt}")
    """

    def __init__(self, config: SimilarityConfig, cache: Any):
        """
        Initialize similarity matcher with embedding model.

        Args:
            config: Similarity matching configuration
            cache: LLM cache instance

        Raises:
            ValueError: If cache is invalid
            RuntimeError: If model loading fails
        """
        if cache is None:
            raise ValueError("Cache instance cannot be None")

        self.config = config
        self._cache = cache
        self._model: Optional[SentenceTransformer] = None
        self._embedding_index: Dict[str, EmbeddingIndex] = {}
        self._embeddings_array: Optional[np.ndarray] = None
        self._cache_keys_list: List[str] = []

        self._init_model()
        if config.enable_persistence:
            self._load_persistence()

        logger.info(
            f"Initialized similarity matcher with model: {config.model_name}, "
            f"threshold: {config.threshold}, metric: {config.metric}"
        )

    def _init_model(self) -> None:
        """Initialize the sentence transformer model."""
        try:
            device = self.config.device or self._detect_device()
            self._model = SentenceTransformer(
                self.config.model_name.value, device=device
            )
            logger.info(
                f"Loaded embedding model {self.config.model_name} on device: {device}"
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    def _detect_device(self) -> str:
        """Auto-detect the best available device."""
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    def _load_persistence(self) -> None:
        """Load persisted embeddings from disk."""
        try:
            persistence_dir = Path(self.config.persistence_path)
            if not persistence_dir.exists():
                persistence_dir.mkdir(parents=True, exist_ok=True)
                return

            index_file = persistence_dir / "embedding_index.pkl"
            if index_file.exists():
                with open(index_file, "rb") as f:
                    persisted_data = pickle.load(f)  # nosec B301 - controlled embeddings data
                    self._embedding_index = {
                        k: EmbeddingIndex(**v) if isinstance(v, dict) else v
                        for k, v in persisted_data.items()
                    }
                    self._rebuild_embeddings_array()
                    logger.info(
                        f"Loaded {len(self._embedding_index)} embeddings from disk"
                    )
        except Exception as e:
            logger.warning(f"Failed to load persisted embeddings: {e}")

    def _save_persistence(self) -> None:
        """Save embeddings to disk."""
        if not self.config.enable_persistence:
            return

        try:
            persistence_dir = Path(self.config.persistence_path)
            persistence_dir.mkdir(parents=True, exist_ok=True)

            index_file = persistence_dir / "embedding_index.pkl"
            with open(index_file, "wb") as f:
                pickle.dump(
                    {k: v.model_dump() for k, v in self._embedding_index.items()}, f
                )

            logger.debug(f"Saved {len(self._embedding_index)} embeddings to disk")
        except Exception as e:
            logger.warning(f"Failed to save embeddings: {e}")

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as numpy array

        Raises:
            RuntimeError: If embedding generation fails
        """
        if self._model is None:
            raise RuntimeError("Model not initialized")

        try:
            embedding = self._model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=self.config.normalize_embeddings,
            )

            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding, dtype=np.float32)

            logger.debug(f"Generated embedding with shape: {embedding.shape}")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of input texts

        Returns:
            Array of embeddings (shape: [num_texts, embedding_dim])

        Raises:
            RuntimeError: If embedding generation fails
        """
        if self._model is None:
            raise RuntimeError("Model not initialized")

        try:
            embeddings = self._model.encode(
                texts,
                batch_size=self.config.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=self.config.normalize_embeddings,
            )

            if not isinstance(embeddings, np.ndarray):
                embeddings = np.array(embeddings, dtype=np.float32)

            logger.debug(
                f"Generated {len(texts)} embeddings with shape: {embeddings.shape}"
            )
            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise RuntimeError(f"Batch embedding generation failed: {e}") from e

    def compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute similarity between two embeddings.

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Similarity score (0-1)
        """
        if self.config.metric == SimilarityMetric.COSINE:
            return self._cosine_similarity(emb1, emb2)
        elif self.config.metric == SimilarityMetric.DOT_PRODUCT:
            return self._dot_product_similarity(emb1, emb2)
        elif self.config.metric == SimilarityMetric.EUCLIDEAN:
            return self._euclidean_similarity(emb1, emb2)
        else:
            return self._cosine_similarity(emb1, emb2)

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity."""
        if self.config.normalize_embeddings:
            return float(np.dot(emb1, emb2))

        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(emb1, emb2) / (norm1 * norm2))

    def _dot_product_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute dot product similarity (normalized to 0-1)."""
        dot_prod = np.dot(emb1, emb2)
        max_possible = np.linalg.norm(emb1) * np.linalg.norm(emb2)

        if max_possible == 0:
            return 0.0

        return float((dot_prod / max_possible + 1) / 2)

    def _euclidean_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute Euclidean similarity (inverse distance, normalized to 0-1)."""
        distance = np.linalg.norm(emb1 - emb2)
        max_distance = np.sqrt(2 * (1 - (-1)))
        return float(1 - (distance / max_distance))

    def compute_similarity_batch(
        self, query_emb: np.ndarray, embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute similarity between query and multiple embeddings.

        Args:
            query_emb: Query embedding vector
            embeddings: Array of embeddings (shape: [num_embeddings, embedding_dim])

        Returns:
            Array of similarity scores
        """
        if self.config.metric == SimilarityMetric.COSINE:
            if self.config.normalize_embeddings:
                similarities = np.dot(embeddings, query_emb)
            else:
                norms = np.linalg.norm(embeddings, axis=1)
                query_norm = np.linalg.norm(query_emb)
                similarities = np.dot(embeddings, query_emb) / (
                    norms * query_norm + 1e-10
                )

        elif self.config.metric == SimilarityMetric.DOT_PRODUCT:
            dot_products = np.dot(embeddings, query_emb)
            norms = np.linalg.norm(embeddings, axis=1)
            query_norm = np.linalg.norm(query_emb)
            max_possibles = norms * query_norm
            similarities = (dot_products / (max_possibles + 1e-10) + 1) / 2

        elif self.config.metric == SimilarityMetric.EUCLIDEAN:
            distances = np.linalg.norm(embeddings - query_emb, axis=1)
            max_distance = np.sqrt(2 * (1 - (-1)))
            similarities = 1 - (distances / max_distance)

        else:
            similarities = np.dot(embeddings, query_emb)

        return similarities

    def index_prompt(
        self,
        prompt: str,
        cache_key: str,
        prompt_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add prompt to similarity index.

        Args:
            prompt: Prompt text to index
            cache_key: Associated cache key
            prompt_hash: Hash of the prompt
            metadata: Additional metadata

        Returns:
            True if indexed successfully, False otherwise
        """
        try:
            if cache_key in self._embedding_index:
                logger.debug(f"Prompt already indexed: {cache_key[:16]}...")
                return True

            if len(self._embedding_index) >= self.config.max_cache_embeddings:
                self._evict_oldest_embedding()

            embedding = self.generate_embedding(prompt)

            import time

            index_entry = EmbeddingIndex(
                cache_key=cache_key,
                prompt=prompt,
                embedding=embedding.tolist(),
                prompt_hash=prompt_hash,
                timestamp=time.time(),
                metadata=metadata or {},
            )

            self._embedding_index[cache_key] = index_entry
            self._rebuild_embeddings_array()

            if self.config.enable_persistence:
                self._save_persistence()

            logger.debug(f"Indexed prompt with cache key: {cache_key[:16]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to index prompt: {e}")
            return False

    def index_prompts_batch(
        self, prompts_data: List[Tuple[str, str, str, Dict[str, Any]]]
    ) -> int:
        """
        Index multiple prompts in batch.

        Args:
            prompts_data: List of (prompt, cache_key, prompt_hash, metadata) tuples

        Returns:
            Number of prompts successfully indexed
        """
        try:
            new_prompts = [
                (p, ck, ph, md)
                for p, ck, ph, md in prompts_data
                if ck not in self._embedding_index
            ]

            if not new_prompts:
                return 0

            prompts = [p for p, _, _, _ in new_prompts]
            embeddings = self.generate_embeddings_batch(prompts)

            import time

            current_time = time.time()
            indexed_count = 0

            for i, (prompt, cache_key, prompt_hash, metadata) in enumerate(new_prompts):
                if len(self._embedding_index) >= self.config.max_cache_embeddings:
                    self._evict_oldest_embedding()

                index_entry = EmbeddingIndex(
                    cache_key=cache_key,
                    prompt=prompt,
                    embedding=embeddings[i].tolist(),
                    prompt_hash=prompt_hash,
                    timestamp=current_time,
                    metadata=metadata or {},
                )

                self._embedding_index[cache_key] = index_entry
                indexed_count += 1

            self._rebuild_embeddings_array()

            if self.config.enable_persistence:
                self._save_persistence()

            logger.info(f"Batch indexed {indexed_count} prompts")
            return indexed_count

        except Exception as e:
            logger.error(f"Failed to batch index prompts: {e}")
            return 0

    def _evict_oldest_embedding(self) -> None:
        """Evict the oldest embedding from the index."""
        if not self._embedding_index:
            return

        oldest_key = min(
            self._embedding_index.keys(),
            key=lambda k: self._embedding_index[k].timestamp,
        )
        del self._embedding_index[oldest_key]
        logger.debug(f"Evicted oldest embedding: {oldest_key[:16]}...")

    def _rebuild_embeddings_array(self) -> None:
        """Rebuild the embeddings array and keys list for efficient search."""
        if not self._embedding_index:
            self._embeddings_array = None
            self._cache_keys_list = []
            return

        self._cache_keys_list = list(self._embedding_index.keys())
        embeddings_list = [
            self._embedding_index[key].get_embedding_array()
            for key in self._cache_keys_list
        ]
        self._embeddings_array = np.vstack(embeddings_list)

        logger.debug(
            f"Rebuilt embeddings array with shape: {self._embeddings_array.shape}"
        )

    def find_similar(
        self,
        prompt: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[SimilarMatch]:
        """
        Find similar prompts in the cache using semantic similarity.

        Args:
            prompt: Query prompt
            top_k: Number of top matches to return (uses config default if None)
            threshold: Minimum similarity threshold (uses config default if None)

        Returns:
            List of SimilarMatch objects, sorted by similarity (descending)
        """
        if self._embeddings_array is None or len(self._cache_keys_list) == 0:
            logger.debug("No embeddings in index")
            return []

        try:
            k = top_k if top_k is not None else self.config.top_k
            thresh = threshold if threshold is not None else self.config.threshold

            query_embedding = self.generate_embedding(prompt)

            similarities = self.compute_similarity_batch(
                query_embedding, self._embeddings_array
            )

            top_indices = np.argsort(similarities)[::-1][:k]

            matches: List[SimilarMatch] = []
            for rank, idx in enumerate(top_indices, start=1):
                similarity = float(similarities[idx])

                if similarity < thresh:
                    continue

                cache_key = self._cache_keys_list[idx]
                index_entry = self._embedding_index[cache_key]

                cached_response = self._cache.get_entry_by_key(cache_key)
                if cached_response is None:
                    logger.warning(
                        f"Cache entry not found for key: {cache_key[:16]}..."
                    )
                    continue

                match = SimilarMatch(
                    prompt=index_entry.prompt,
                    response=cached_response.value,
                    similarity_score=similarity,
                    cache_key=cache_key,
                    metadata=index_entry.metadata,
                    prompt_hash=index_entry.prompt_hash,
                    token_count=cached_response.token_count,
                    model_name=cached_response.model_name,
                    rank=rank,
                )

                matches.append(match)

            logger.info(
                f"Found {len(matches)} similar prompts above threshold {thresh:.2f}"
            )
            return matches

        except Exception as e:
            logger.error(f"Failed to find similar prompts: {e}")
            return []

    def find_similar_with_scores(
        self, prompt: str, top_k: Optional[int] = None
    ) -> List[Tuple[SimilarMatch, float]]:
        """
        Find similar prompts and return with detailed scores.

        Args:
            prompt: Query prompt
            top_k: Number of top matches to return

        Returns:
            List of (SimilarMatch, score) tuples
        """
        matches = self.find_similar(prompt, top_k=top_k, threshold=0.0)
        return [(match, match.similarity_score) for match in matches]

    def get_most_similar(
        self, prompt: str, threshold: Optional[float] = None
    ) -> Optional[SimilarMatch]:
        """
        Get the single most similar prompt.

        Args:
            prompt: Query prompt
            threshold: Minimum similarity threshold

        Returns:
            Most similar match if found, None otherwise
        """
        matches = self.find_similar(prompt, top_k=1, threshold=threshold)
        return matches[0] if matches else None

    def remove_from_index(self, cache_key: str) -> bool:
        """
        Remove a prompt from the similarity index.

        Args:
            cache_key: Cache key to remove

        Returns:
            True if removed, False if not found
        """
        if cache_key in self._embedding_index:
            del self._embedding_index[cache_key]
            self._rebuild_embeddings_array()

            if self.config.enable_persistence:
                self._save_persistence()

            logger.debug(f"Removed from index: {cache_key[:16]}...")
            return True
        return False

    def clear_index(self) -> None:
        """Clear all embeddings from the index."""
        self._embedding_index.clear()
        self._embeddings_array = None
        self._cache_keys_list = []

        if self.config.enable_persistence:
            self._save_persistence()

        logger.info("Cleared similarity index")

    def sync_with_cache(self) -> int:
        """
        Synchronize index with cache entries.

        Removes index entries for prompts no longer in cache and
        optionally indexes new cache entries.

        Returns:
            Number of entries removed from index
        """
        try:
            cache_keys = set(self._cache.get_all_keys())
            index_keys = set(self._embedding_index.keys())

            removed_keys = index_keys - cache_keys
            for key in removed_keys:
                self.remove_from_index(key)

            if removed_keys:
                self._rebuild_embeddings_array()
                if self.config.enable_persistence:
                    self._save_persistence()

            logger.info(
                f"Synchronized index, removed {len(removed_keys)} stale entries"
            )
            return len(removed_keys)

        except Exception as e:
            logger.error(f"Failed to sync index with cache: {e}")
            return 0

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the similarity index.

        Returns:
            Dictionary with index statistics
        """
        stats = {
            "total_indexed": len(self._embedding_index),
            "max_capacity": self.config.max_cache_embeddings,
            "utilization": len(self._embedding_index)
            / self.config.max_cache_embeddings,
            "model_name": self.config.model_name.value,
            "embedding_dimension": (
                self._embeddings_array.shape[1]
                if self._embeddings_array is not None
                else 0
            ),
            "similarity_metric": self.config.metric.value,
            "threshold": self.config.threshold,
            "top_k": self.config.top_k,
            "persistence_enabled": self.config.enable_persistence,
        }

        if self._embedding_index:
            timestamps = [entry.timestamp for entry in self._embedding_index.values()]
            stats["oldest_entry"] = min(timestamps)
            stats["newest_entry"] = max(timestamps)

        return stats

    def export_index(self, filepath: str) -> bool:
        """
        Export index to JSON file.

        Args:
            filepath: Path to export file

        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = {
                "config": self.config.model_dump(),
                "index": {k: v.model_dump() for k, v in self._embedding_index.items()},
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported index to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export index: {e}")
            return False

    def import_index(self, filepath: str) -> bool:
        """
        Import index from JSON file.

        Args:
            filepath: Path to import file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, encoding="utf-8") as f:
                import_data = json.load(f)

            index_data = import_data.get("index", {})
            self._embedding_index = {
                k: EmbeddingIndex(**v) for k, v in index_data.items()
            }

            self._rebuild_embeddings_array()

            if self.config.enable_persistence:
                self._save_persistence()

            logger.info(
                f"Imported {len(self._embedding_index)} entries from {filepath}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to import index: {e}")
            return False

    def reindex_all(self) -> int:
        """
        Rebuild index from all cache entries.

        Returns:
            Number of entries reindexed
        """
        try:
            self.clear_index()

            cache_keys = self._cache.get_all_keys()
            prompts_data: List[Tuple[str, str, str, Dict[str, Any]]] = []

            for cache_key in cache_keys:
                cached_response = self._cache.get_entry_by_key(cache_key)
                if cached_response is None:
                    continue

                prompt = cached_response.value
                prompt_hash = cached_response.prompt_hash
                metadata = cached_response.metadata

                prompts_data.append((prompt, cache_key, prompt_hash, metadata))

            indexed_count = self.index_prompts_batch(prompts_data)

            logger.info(f"Reindexed {indexed_count} cache entries")
            return indexed_count

        except Exception as e:
            logger.error(f"Failed to reindex: {e}")
            return 0

    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension of the current model."""
        if self._embeddings_array is not None:
            return self._embeddings_array.shape[1]
        test_emb = self.generate_embedding("test")
        return test_emb.shape[0]

    def __len__(self) -> int:
        """Get the number of indexed embeddings."""
        return len(self._embedding_index)

    def __contains__(self, cache_key: str) -> bool:
        """Check if a cache key is in the index."""
        return cache_key in self._embedding_index
