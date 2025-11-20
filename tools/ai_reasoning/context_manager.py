"""
Context Management Module.

This module handles conversation history, context compression,
semantic similarity search, and memory persistence.

Protocol Coverage:
- P-CONTEXT-VALIDATION: Context integrity checking
- P-KNOW-RAG: Retrieval-Augmented Generation
- P-KNOW-KG-INTERACTION: Knowledge graph reasoning
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import asyncio


logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Represents a single context entry."""
    id: str
    content: str
    timestamp: datetime
    role: str  # 'user', 'assistant', 'system'
    tokens: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "role": self.role,
            "tokens": self.tokens,
            "metadata": self.metadata
        }


@dataclass
class ContextWindow:
    """Represents a context window with entries."""
    entries: List[ContextEntry]
    total_tokens: int
    max_tokens: int
    compression_ratio: float = 1.0

    def is_full(self) -> bool:
        """Check if window is at capacity."""
        return self.total_tokens >= self.max_tokens

    def get_recent(self, n: int) -> List[ContextEntry]:
        """Get n most recent entries."""
        return self.entries[-n:] if n < len(self.entries) else self.entries


class ContextManager:
    """
    Manages conversation history, context compression,
    and retrieval with Redis persistence.
    """

    def __init__(
        self,
        max_tokens: int = 8000,
        sliding_window_size: int = 10,
        compression_threshold: float = 0.8,
        redis_client: Optional[Any] = None,
        embedding_model: Optional[Any] = None
    ):
        """
        Initialize context manager.

        Args:
            max_tokens: Maximum tokens in context window
            sliding_window_size: Number of recent entries to keep
            compression_threshold: Threshold to trigger compression
            redis_client: Redis client for persistence
            embedding_model: Model for generating embeddings
        """
        self.max_tokens = max_tokens
        self.sliding_window_size = sliding_window_size
        self.compression_threshold = compression_threshold
        self.redis_client = redis_client
        self.embedding_model = embedding_model

        self.context_window = ContextWindow(
            entries=[],
            total_tokens=0,
            max_tokens=max_tokens
        )

        self.compression_history: List[Dict[str, Any]] = []

    async def add_entry(
        self,
        content: str,
        role: str,
        tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextEntry:
        """
        Add entry to context window.

        Args:
            content: Entry content
            role: Entry role (user/assistant/system)
            tokens: Token count
            metadata: Additional metadata

        Returns:
            Created ContextEntry
        """
        entry_id = self._generate_entry_id(content, role)

        entry = ContextEntry(
            id=entry_id,
            content=content,
            timestamp=datetime.now(),
            role=role,
            tokens=tokens,
            metadata=metadata or {}
        )

        # Generate embedding if model available
        if self.embedding_model:
            entry.embedding = await self._generate_embedding(content)

        self.context_window.entries.append(entry)
        self.context_window.total_tokens += tokens

        logger.debug(f"Added entry: {role}, {tokens} tokens")

        # Check if compression needed
        if self._should_compress():
            await self.compress_context()

        # Persist to Redis if available
        if self.redis_client:
            await self._persist_entry(entry)

        return entry

    async def get_context(
        self,
        max_entries: Optional[int] = None,
        include_system: bool = True
    ) -> List[ContextEntry]:
        """
        Get context entries.

        Args:
            max_entries: Maximum entries to return
            include_system: Include system messages

        Returns:
            List of context entries
        """
        entries = self.context_window.entries

        if not include_system:
            entries = [e for e in entries if e.role != "system"]

        if max_entries:
            entries = entries[-max_entries:]

        return entries

    async def compress_context(self, llm_provider: Optional[Any] = None) -> Dict[str, Any]:
        """
        Compress context to reduce token count.

        Args:
            llm_provider: LLM provider for summarization

        Returns:
            Compression statistics
        """
        logger.info("Starting context compression")

        original_token_count = self.context_window.total_tokens
        original_entry_count = len(self.context_window.entries)

        # Keep recent entries, compress older ones
        recent_entries = self.context_window.get_recent(self.sliding_window_size)
        older_entries = self.context_window.entries[:-self.sliding_window_size]

        if not older_entries:
            logger.info("No entries to compress")
            return {"compressed": False}

        # Summarize older entries
        if llm_provider:
            summary = await self._summarize_entries(older_entries, llm_provider)
        else:
            summary = self._simple_compression(older_entries)

        # Create compressed entry
        compressed_entry = ContextEntry(
            id=self._generate_entry_id(summary["content"], "system"),
            content=summary["content"],
            timestamp=datetime.now(),
            role="system",
            tokens=summary["tokens"],
            metadata={
                "compressed": True,
                "original_entries": len(older_entries),
                "original_tokens": sum(e.tokens for e in older_entries)
            }
        )

        # Update context window
        self.context_window.entries = [compressed_entry] + recent_entries
        self.context_window.total_tokens = sum(
            e.tokens for e in self.context_window.entries
        )

        # Calculate compression ratio
        new_token_count = self.context_window.total_tokens
        compression_ratio = new_token_count / original_token_count
        self.context_window.compression_ratio = compression_ratio

        compression_stats = {
            "compressed": True,
            "original_tokens": original_token_count,
            "new_tokens": new_token_count,
            "compression_ratio": compression_ratio,
            "original_entries": original_entry_count,
            "new_entries": len(self.context_window.entries),
            "timestamp": datetime.now().isoformat()
        }

        self.compression_history.append(compression_stats)

        logger.info(
            f"Context compressed: {original_token_count} -> {new_token_count} tokens "
            f"({compression_ratio:.2%})"
        )

        return compression_stats

    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[ContextEntry, float]]:
        """
        Search for similar context entries.

        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of (entry, similarity_score) tuples
        """
        if not self.embedding_model:
            logger.warning("Embedding model not available for similarity search")
            return []

        # Generate query embedding
        query_embedding = await self._generate_embedding(query)

        # Calculate similarities
        similarities = []
        for entry in self.context_window.entries:
            if entry.embedding:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                if similarity >= similarity_threshold:
                    similarities.append((entry, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    async def clear_context(self, keep_system: bool = True) -> None:
        """
        Clear context window.

        Args:
            keep_system: Keep system messages
        """
        if keep_system:
            system_entries = [
                e for e in self.context_window.entries if e.role == "system"
            ]
            self.context_window.entries = system_entries
            self.context_window.total_tokens = sum(e.tokens for e in system_entries)
        else:
            self.context_window.entries = []
            self.context_window.total_tokens = 0

        logger.info("Context cleared")

    async def get_summary(self, llm_provider: Optional[Any] = None) -> str:
        """
        Get summary of current context.

        Args:
            llm_provider: LLM provider for summarization

        Returns:
            Context summary
        """
        if not self.context_window.entries:
            return "No context available"

        if llm_provider:
            summary_result = await self._summarize_entries(
                self.context_window.entries,
                llm_provider
            )
            return summary_result["content"]
        else:
            return self._simple_summary()

    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics."""
        return {
            "total_entries": len(self.context_window.entries),
            "total_tokens": self.context_window.total_tokens,
            "max_tokens": self.max_tokens,
            "utilization": self.context_window.total_tokens / self.max_tokens,
            "compression_ratio": self.context_window.compression_ratio,
            "compression_count": len(self.compression_history),
            "role_distribution": self._get_role_distribution()
        }

    async def validate_context(self) -> Dict[str, Any]:
        """
        Validate context integrity.

        Returns:
            Validation results
        """
        validation = {
            "is_valid": True,
            "issues": [],
            "warnings": []
        }

        # Check token count consistency
        calculated_tokens = sum(e.tokens for e in self.context_window.entries)
        if calculated_tokens != self.context_window.total_tokens:
            validation["is_valid"] = False
            validation["issues"].append(
                f"Token count mismatch: {calculated_tokens} vs {self.context_window.total_tokens}"
            )

        # Check for duplicate entries
        entry_ids = [e.id for e in self.context_window.entries]
        if len(entry_ids) != len(set(entry_ids)):
            validation["warnings"].append("Duplicate entries detected")

        # Check chronological order
        timestamps = [e.timestamp for e in self.context_window.entries]
        if timestamps != sorted(timestamps):
            validation["warnings"].append("Entries not in chronological order")

        # Check token limit
        if self.context_window.total_tokens > self.max_tokens:
            validation["is_valid"] = False
            validation["issues"].append(
                f"Context exceeds max tokens: {self.context_window.total_tokens} > {self.max_tokens}"
            )

        return validation

    async def _summarize_entries(
        self,
        entries: List[ContextEntry],
        llm_provider: Any
    ) -> Dict[str, Any]:
        """Summarize entries using LLM."""
        # Build conversation text
        conversation = []
        for entry in entries:
            conversation.append(f"{entry.role.upper()}: {entry.content}")

        conversation_text = "\n".join(conversation)

        prompt = f"""
Summarize the following conversation in a concise way while preserving key information:

{conversation_text}

Provide a summary that captures the main points and decisions:
"""

        response = await llm_provider.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=500
        )

        summary_text = response.get("text", "").strip()
        summary_tokens = response.get("token_count", 100)

        return {
            "content": f"[Summary of previous conversation]: {summary_text}",
            "tokens": summary_tokens
        }

    def _simple_compression(self, entries: List[ContextEntry]) -> Dict[str, Any]:
        """Simple compression without LLM."""
        # Extract key information
        user_messages = [e.content for e in entries if e.role == "user"]
        assistant_messages = [e.content for e in entries if e.role == "assistant"]

        summary = f"Previous conversation included {len(user_messages)} user messages "
        summary += f"and {len(assistant_messages)} assistant responses. "
        summary += f"Topics discussed: {', '.join(user_messages[:3])}..."

        return {
            "content": summary,
            "tokens": len(summary.split()) * 1.3  # Rough estimate
        }

    def _simple_summary(self) -> str:
        """Simple summary without LLM."""
        stats = self.get_stats()
        return f"Context contains {stats['total_entries']} entries, " \
               f"{stats['total_tokens']} tokens ({stats['utilization']:.1%} utilization)"

    def _should_compress(self) -> bool:
        """Check if compression should be triggered."""
        utilization = self.context_window.total_tokens / self.max_tokens
        return utilization >= self.compression_threshold

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not self.embedding_model:
            return []

        try:
            embedding = await self.embedding_model.embed(text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _generate_entry_id(self, content: str, role: str) -> str:
        """Generate unique entry ID."""
        hash_input = f"{content}{role}{datetime.now().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _get_role_distribution(self) -> Dict[str, int]:
        """Get distribution of roles in context."""
        distribution = {}
        for entry in self.context_window.entries:
            distribution[entry.role] = distribution.get(entry.role, 0) + 1
        return distribution

    async def _persist_entry(self, entry: ContextEntry) -> None:
        """Persist entry to Redis."""
        if not self.redis_client:
            return

        try:
            key = f"context:entry:{entry.id}"
            value = json.dumps(entry.to_dict())
            await self.redis_client.set(key, value, ex=86400)  # 24h expiry
            logger.debug(f"Persisted entry to Redis: {entry.id}")
        except Exception as e:
            logger.error(f"Failed to persist entry to Redis: {e}")

    async def load_from_redis(self, session_id: str) -> int:
        """
        Load context from Redis.

        Args:
            session_id: Session identifier

        Returns:
            Number of entries loaded
        """
        if not self.redis_client:
            logger.warning("Redis client not available")
            return 0

        try:
            pattern = f"context:entry:*"
            keys = await self.redis_client.keys(pattern)

            for key in keys:
                value = await self.redis_client.get(key)
                if value:
                    entry_dict = json.loads(value)
                    entry = ContextEntry(
                        id=entry_dict["id"],
                        content=entry_dict["content"],
                        timestamp=datetime.fromisoformat(entry_dict["timestamp"]),
                        role=entry_dict["role"],
                        tokens=entry_dict["tokens"],
                        metadata=entry_dict.get("metadata", {})
                    )
                    self.context_window.entries.append(entry)

            self.context_window.total_tokens = sum(
                e.tokens for e in self.context_window.entries
            )

            logger.info(f"Loaded {len(keys)} entries from Redis")
            return len(keys)

        except Exception as e:
            logger.error(f"Failed to load context from Redis: {e}")
            return 0


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        manager = ContextManager(max_tokens=1000, sliding_window_size=3)

        # Add entries
        await manager.add_entry(
            "What is microservices architecture?",
            role="user",
            tokens=100
        )

        await manager.add_entry(
            "Microservices architecture is a design pattern...",
            role="assistant",
            tokens=200
        )

        # Get context
        context = await manager.get_context()
        print(f"Context entries: {len(context)}")

        # Get stats
        stats = manager.get_stats()
        print(f"Stats: {stats}")

        # Validate
        validation = await manager.validate_context()
        print(f"Validation: {validation}")

    asyncio.run(main())
