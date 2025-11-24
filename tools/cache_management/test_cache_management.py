"""
Comprehensive Test Suite for Cache Management Platform.

Tests for LLM caching, reasoning step caching, similarity matching,
distributed caching, and CLI operations.

Protocol Coverage:
- P-COG-COT: Chain-of-Thought reasoning caching
- P-COG-TOT: Tree-of-Thoughts reasoning caching
- CORE-CACHE-003: LLM response caching with semantic similarity
- P-CACHE-MANAGEMENT: Distributed cache orchestration
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest
from click.testing import CliRunner

# Test imports
pytest_plugins = ("pytest_asyncio",)


# Mock imports for testing without actual dependencies
class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self) -> None:
        """Initialize mock Redis."""
        self.data: Dict[str, Any] = {}
        self.ttl_map: Dict[str, float] = {}

    async def get(self, key: str) -> Any:
        """Mock get operation."""
        if key in self.ttl_map:
            if time.time() > self.ttl_map[key]:
                del self.data[key]
                del self.ttl_map[key]
                return None
        return self.data.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Mock set operation."""
        self.data[key] = value
        if ex:
            self.ttl_map[key] = time.time() + ex
        return True

    async def delete(self, key: str) -> int:
        """Mock delete operation."""
        if key in self.data:
            del self.data[key]
            if key in self.ttl_map:
                del self.ttl_map[key]
            return 1
        return 0

    async def keys(self, pattern: str = "*") -> List[str]:
        """Mock keys operation."""
        return list(self.data.keys())

    async def exists(self, key: str) -> int:
        """Mock exists operation."""
        return 1 if key in self.data else 0

    async def ttl(self, key: str) -> int:
        """Mock TTL operation."""
        if key in self.ttl_map:
            remaining = int(self.ttl_map[key] - time.time())
            return remaining if remaining > 0 else -2
        return -1


class MockSentenceTransformer:
    """Mock sentence transformer for testing."""

    def __init__(self, model_name: str) -> None:
        """Initialize mock transformer."""
        self.model_name = model_name

    def encode(self, texts: List[str]) -> List[List[float]]:
        """Mock encode operation."""
        import hashlib

        embeddings = []
        for text in texts:
            # Generate deterministic embeddings based on text hash
            hash_val = int(hashlib.md5(text.encode(), usedforsecurity=False).hexdigest(), 16)  # nosec B324
            # Create 384-dim embedding (MiniLM size)
            embedding = [(hash_val >> i) % 100 / 100.0 for i in range(384)]
            embeddings.append(embedding)
        return embeddings


# Import modules after mocks are defined
from cache_cli import cli
from cache_manager import CacheManager, CacheStats, CacheWarmer, EvictionPolicy
from distributed_cache import DistributedCache, ReplicationConfig, ShardingStrategy
from llm_cache import CacheBackend, CacheConfig, CachedResponse, LLMCache
from metrics import MetricsCollector
from reasoning_cache import CoTStep, ReasoningCache, ReasoningResult, ToTNode
from similarity_matcher import (
    EmbeddingModel,
    SimilarityConfig,
    SimilarityMatcher,
    SimilarMatch,
)


# Fixtures
@pytest.fixture
def mock_redis():
    """Provide mock Redis client."""
    return MockRedis()


@pytest.fixture
def cache_config():
    """Provide test cache configuration."""
    return CacheConfig(
        backend=CacheBackend.MEMORY,
        redis_host="localhost",
        redis_port=6379,
        redis_db=0,
        ttl_seconds=3600,
        max_size=1000,
    )


@pytest.fixture
def llm_cache(cache_config):
    """Provide LLM cache instance."""
    return LLMCache(cache_config)


@pytest.fixture
def reasoning_cache(cache_config):
    """Provide reasoning cache instance."""
    return ReasoningCache(cache_config)


@pytest.fixture
def similarity_config():
    """Provide similarity matcher configuration."""
    return SimilarityConfig(
        model=EmbeddingModel.MINILM,
        threshold=0.85,
        cache_embeddings=True,
    )


@pytest.fixture
def similarity_matcher(similarity_config):
    """Provide similarity matcher instance."""
    with patch(
        "sentence_transformers.SentenceTransformer",
        MockSentenceTransformer,
    ):
        return SimilarityMatcher(similarity_config)


@pytest.fixture
def cache_manager(llm_cache, reasoning_cache, similarity_matcher):
    """Provide cache manager instance."""
    return CacheManager(
        llm_cache=llm_cache,
        reasoning_cache=reasoning_cache,
        similarity_matcher=similarity_matcher,
        eviction_policy=EvictionPolicy.LRU,
    )


@pytest.fixture
def metrics_collector():
    """Provide metrics collector instance."""
    return MetricsCollector()


@pytest.fixture
def cli_runner():
    """Provide Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_file(tmp_path):
    """Create temporary config file."""
    config = {
        "backend": "memory",
        "redis_host": "localhost",
        "redis_port": 6379,
        "redis_db": 0,
        "ttl_seconds": 3600,
        "max_size": 1000,
        "embedding_model": "all-MiniLM-L6-v2",
        "similarity_threshold": 0.85,
        "eviction_policy": "lru",
    }
    config_file = tmp_path / "cache_config.yaml"
    import yaml

    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file


# LLMCache Tests
class TestLLMCache:
    """Test suite for LLMCache."""

    @pytest.mark.asyncio
    async def test_set_and_get_basic(self, llm_cache):
        """Test basic set and get operations."""
        response = CachedResponse(
            prompt="What is Python?",
            response="Python is a programming language.",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=6,
            metadata={},
        )

        await llm_cache.set("test_key", response)
        retrieved = await llm_cache.get("test_key")

        assert retrieved is not None
        assert retrieved.prompt == response.prompt
        assert retrieved.response == response.response
        assert retrieved.model == response.model

    @pytest.mark.asyncio
    async def test_cache_miss(self, llm_cache):
        """Test cache miss returns None."""
        result = await llm_cache.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache_config):
        """Test TTL expiration."""
        cache_config.ttl_seconds = 1
        llm_cache = LLMCache(cache_config)

        response = CachedResponse(
            prompt="Test",
            response="Response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=1,
            metadata={},
        )

        await llm_cache.set("test_key", response)
        assert await llm_cache.get("test_key") is not None

        # Wait for expiration
        await asyncio.sleep(1.5)
        assert await llm_cache.get("test_key") is None

    @pytest.mark.asyncio
    async def test_memory_backend(self, cache_config):
        """Test memory backend operations."""
        cache_config.backend = CacheBackend.MEMORY
        llm_cache = LLMCache(cache_config)

        response = CachedResponse(
            prompt="Memory test",
            response="Memory response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=2,
            metadata={},
        )

        await llm_cache.set("mem_key", response)
        retrieved = await llm_cache.get("mem_key")

        assert retrieved is not None
        assert retrieved.response == "Memory response"

    @pytest.mark.asyncio
    async def test_disk_backend(self, cache_config, tmp_path):
        """Test disk backend operations."""
        cache_config.backend = CacheBackend.DISK
        cache_config.disk_path = str(tmp_path / "cache")
        llm_cache = LLMCache(cache_config)

        response = CachedResponse(
            prompt="Disk test",
            response="Disk response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=2,
            metadata={},
        )

        await llm_cache.set("disk_key", response)
        retrieved = await llm_cache.get("disk_key")

        assert retrieved is not None
        assert retrieved.response == "Disk response"

    @pytest.mark.asyncio
    async def test_delete_entry(self, llm_cache):
        """Test deleting cache entries."""
        response = CachedResponse(
            prompt="Delete test",
            response="To be deleted",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=3,
            metadata={},
        )

        await llm_cache.set("delete_key", response)
        assert await llm_cache.get("delete_key") is not None

        await llm_cache.delete("delete_key")
        assert await llm_cache.get("delete_key") is None

    @pytest.mark.asyncio
    async def test_exists_check(self, llm_cache):
        """Test checking if key exists."""
        response = CachedResponse(
            prompt="Exists test",
            response="Exists response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=2,
            metadata={},
        )

        await llm_cache.set("exists_key", response)
        assert await llm_cache.exists("exists_key") is True
        assert await llm_cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_list_keys(self, llm_cache):
        """Test listing cache keys."""
        for i in range(5):
            response = CachedResponse(
                prompt=f"Test {i}",
                response=f"Response {i}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            await llm_cache.set(f"key_{i}", response)

        keys = await llm_cache.list_keys()
        assert len(keys) >= 5
        assert all(f"key_{i}" in keys for i in range(5))

    @pytest.mark.asyncio
    async def test_max_size_eviction(self, cache_config):
        """Test max size enforcement with eviction."""
        cache_config.max_size = 3
        llm_cache = LLMCache(cache_config)

        for i in range(5):
            response = CachedResponse(
                prompt=f"Test {i}",
                response=f"Response {i}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            await llm_cache.set(f"key_{i}", response)

        keys = await llm_cache.list_keys()
        assert len(keys) <= 3

    @pytest.mark.asyncio
    async def test_metadata_storage(self, llm_cache):
        """Test storing and retrieving metadata."""
        metadata = {
            "user_id": "12345",
            "session": "abc-def",
            "tags": ["test", "metadata"],
        }

        response = CachedResponse(
            prompt="Metadata test",
            response="With metadata",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=2,
            metadata=metadata,
        )

        await llm_cache.set("meta_key", response)
        retrieved = await llm_cache.get("meta_key")

        assert retrieved is not None
        assert retrieved.metadata == metadata

    @pytest.mark.asyncio
    async def test_concurrent_access(self, llm_cache):
        """Test concurrent cache access."""

        async def set_and_get(key: str) -> bool:
            response = CachedResponse(
                prompt=f"Concurrent {key}",
                response=f"Response {key}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            await llm_cache.set(key, response)
            retrieved = await llm_cache.get(key)
            return retrieved is not None

        tasks = [set_and_get(f"key_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert all(results)

    @pytest.mark.asyncio
    async def test_large_response_storage(self, llm_cache):
        """Test storing large responses."""
        large_response = "X" * 100000  # 100KB response

        response = CachedResponse(
            prompt="Large test",
            response=large_response,
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=50000,
            metadata={},
        )

        await llm_cache.set("large_key", response)
        retrieved = await llm_cache.get("large_key")

        assert retrieved is not None
        assert len(retrieved.response) == 100000

    @pytest.mark.asyncio
    async def test_unicode_handling(self, llm_cache):
        """Test Unicode text handling."""
        unicode_text = "Hello 世界 🌍 مرحبا"

        response = CachedResponse(
            prompt="Unicode test",
            response=unicode_text,
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=4,
            metadata={},
        )

        await llm_cache.set("unicode_key", response)
        retrieved = await llm_cache.get("unicode_key")

        assert retrieved is not None
        assert retrieved.response == unicode_text

    @pytest.mark.asyncio
    async def test_serialization(self, llm_cache):
        """Test response serialization and deserialization."""
        response = CachedResponse(
            prompt="Serialization test",
            response="Test response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=2,
            metadata={"nested": {"key": "value"}},
        )

        serialized = response.to_dict()
        assert isinstance(serialized, dict)
        assert "prompt" in serialized
        assert "response" in serialized

        # Round-trip test
        await llm_cache.set("serial_key", response)
        retrieved = await llm_cache.get("serial_key")
        assert retrieved.to_dict() == response.to_dict()

    @pytest.mark.asyncio
    async def test_pattern_deletion(self, llm_cache):
        """Test pattern-based deletion."""
        # Set up test data
        for i in range(5):
            response = CachedResponse(
                prompt=f"Pattern {i}",
                response=f"Response {i}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            await llm_cache.set(f"pattern_key_{i}", response)

        # Delete pattern
        deleted = await llm_cache.delete_pattern("pattern_key_*")
        assert deleted >= 5


# ReasoningCache Tests
class TestReasoningCache:
    """Test suite for ReasoningCache."""

    @pytest.mark.asyncio
    async def test_cot_caching(self, reasoning_cache):
        """Test Chain-of-Thought caching."""
        steps = [
            CoTStep(
                step_number=1,
                thought="First, identify the problem",
                rationale="Need to understand requirements",
                confidence=0.9,
            ),
            CoTStep(
                step_number=2,
                thought="Then, break it down",
                rationale="Divide and conquer approach",
                confidence=0.85,
            ),
        ]

        result = ReasoningResult(
            reasoning_type="cot",
            problem="How to solve complex problem?",
            steps=steps,
            final_answer="By breaking it into smaller parts",
            metadata={},
        )

        await reasoning_cache.set("cot_key", result)
        retrieved = await reasoning_cache.get("cot_key")

        assert retrieved is not None
        assert retrieved.reasoning_type == "cot"
        assert len(retrieved.steps) == 2
        assert retrieved.final_answer == result.final_answer

    @pytest.mark.asyncio
    async def test_tot_caching(self, reasoning_cache):
        """Test Tree-of-Thoughts caching."""
        nodes = [
            ToTNode(
                node_id="root",
                thought="Starting point",
                parent_id=None,
                children_ids=["child1", "child2"],
                score=0.9,
                depth=0,
            ),
            ToTNode(
                node_id="child1",
                thought="Branch 1",
                parent_id="root",
                children_ids=[],
                score=0.85,
                depth=1,
            ),
            ToTNode(
                node_id="child2",
                thought="Branch 2",
                parent_id="root",
                children_ids=[],
                score=0.88,
                depth=1,
            ),
        ]

        result = ReasoningResult(
            reasoning_type="tot",
            problem="Find optimal path",
            steps=nodes,
            final_answer="Branch 2 is optimal",
            metadata={"explored_nodes": 3},
        )

        await reasoning_cache.set("tot_key", result)
        retrieved = await reasoning_cache.get("tot_key")

        assert retrieved is not None
        assert retrieved.reasoning_type == "tot"
        assert len(retrieved.steps) == 3

    @pytest.mark.asyncio
    async def test_reasoning_serialization(self, reasoning_cache):
        """Test reasoning result serialization."""
        steps = [
            CoTStep(
                step_number=1,
                thought="Test",
                rationale="Testing",
                confidence=0.9,
            )
        ]

        result = ReasoningResult(
            reasoning_type="cot",
            problem="Test problem",
            steps=steps,
            final_answer="Test answer",
            metadata={"test": True},
        )

        serialized = result.to_dict()
        assert isinstance(serialized, dict)
        assert serialized["reasoning_type"] == "cot"

    @pytest.mark.asyncio
    async def test_complex_tot_tree(self, reasoning_cache):
        """Test complex ToT tree structure."""
        nodes = []
        for depth in range(3):
            for i in range(2**depth):
                node_id = f"node_{depth}_{i}"
                parent_id = f"node_{depth-1}_{i//2}" if depth > 0 else None
                children_ids = (
                    [f"node_{depth+1}_{i*2}", f"node_{depth+1}_{i*2+1}"]
                    if depth < 2
                    else []
                )

                nodes.append(
                    ToTNode(
                        node_id=node_id,
                        thought=f"Thought at depth {depth}",
                        parent_id=parent_id,
                        children_ids=children_ids,
                        score=0.9 - (depth * 0.1),
                        depth=depth,
                    )
                )

        result = ReasoningResult(
            reasoning_type="tot",
            problem="Complex tree problem",
            steps=nodes,
            final_answer="Best path found",
            metadata={"tree_depth": 3, "total_nodes": len(nodes)},
        )

        await reasoning_cache.set("complex_tot", result)
        retrieved = await reasoning_cache.get("complex_tot")

        assert retrieved is not None
        assert len(retrieved.steps) == len(nodes)

    @pytest.mark.asyncio
    async def test_reasoning_metadata(self, reasoning_cache):
        """Test reasoning metadata storage."""
        steps = [CoTStep(step_number=1, thought="Test", rationale="", confidence=1.0)]

        metadata = {
            "model": "gpt-4",
            "temperature": 0.7,
            "elapsed_time": 2.5,
            "tokens_used": 150,
        }

        result = ReasoningResult(
            reasoning_type="cot",
            problem="Test",
            steps=steps,
            final_answer="Answer",
            metadata=metadata,
        )

        await reasoning_cache.set("meta_reasoning", result)
        retrieved = await reasoning_cache.get("meta_reasoning")

        assert retrieved is not None
        assert retrieved.metadata == metadata

    @pytest.mark.asyncio
    async def test_reasoning_update(self, reasoning_cache):
        """Test updating reasoning results."""
        steps = [
            CoTStep(step_number=1, thought="Initial", rationale="", confidence=0.5)
        ]

        result = ReasoningResult(
            reasoning_type="cot",
            problem="Evolving problem",
            steps=steps,
            final_answer="Initial answer",
            metadata={},
        )

        await reasoning_cache.set("update_key", result)

        # Update with more steps
        steps.append(
            CoTStep(
                step_number=2,
                thought="Refined",
                rationale="",
                confidence=0.9,
            )
        )
        result.steps = steps
        result.final_answer = "Refined answer"

        await reasoning_cache.set("update_key", result)
        retrieved = await reasoning_cache.get("update_key")

        assert retrieved is not None
        assert len(retrieved.steps) == 2
        assert retrieved.final_answer == "Refined answer"

    @pytest.mark.asyncio
    async def test_reasoning_deletion(self, reasoning_cache):
        """Test deleting reasoning entries."""
        steps = [CoTStep(step_number=1, thought="Test", rationale="", confidence=1.0)]

        result = ReasoningResult(
            reasoning_type="cot",
            problem="Delete test",
            steps=steps,
            final_answer="Answer",
            metadata={},
        )

        await reasoning_cache.set("delete_reasoning", result)
        assert await reasoning_cache.get("delete_reasoning") is not None

        await reasoning_cache.delete("delete_reasoning")
        assert await reasoning_cache.get("delete_reasoning") is None

    @pytest.mark.asyncio
    async def test_empty_steps(self, reasoning_cache):
        """Test handling empty reasoning steps."""
        result = ReasoningResult(
            reasoning_type="cot",
            problem="Empty steps",
            steps=[],
            final_answer="Direct answer",
            metadata={},
        )

        await reasoning_cache.set("empty_steps", result)
        retrieved = await reasoning_cache.get("empty_steps")

        assert retrieved is not None
        assert len(retrieved.steps) == 0

    @pytest.mark.asyncio
    async def test_cot_confidence_tracking(self, reasoning_cache):
        """Test CoT confidence score tracking."""
        steps = [
            CoTStep(
                step_number=i,
                thought=f"Step {i}",
                rationale="",
                confidence=0.9 - (i * 0.1),
            )
            for i in range(1, 6)
        ]

        result = ReasoningResult(
            reasoning_type="cot",
            problem="Confidence test",
            steps=steps,
            final_answer="Answer",
            metadata={},
        )

        await reasoning_cache.set("confidence_key", result)
        retrieved = await reasoning_cache.get("confidence_key")

        assert retrieved is not None
        confidences = [s.confidence for s in retrieved.steps]
        assert all(0 <= c <= 1 for c in confidences)

    @pytest.mark.asyncio
    async def test_tot_scoring(self, reasoning_cache):
        """Test ToT node scoring."""
        nodes = [
            ToTNode(
                node_id=f"node_{i}",
                thought=f"Thought {i}",
                parent_id=None,
                children_ids=[],
                score=i * 0.1,
                depth=0,
            )
            for i in range(10)
        ]

        result = ReasoningResult(
            reasoning_type="tot",
            problem="Scoring test",
            steps=nodes,
            final_answer="Best score node",
            metadata={},
        )

        await reasoning_cache.set("scoring_key", result)
        retrieved = await reasoning_cache.get("scoring_key")

        assert retrieved is not None
        scores = [n.score for n in retrieved.steps]
        assert max(scores) == 0.9

    @pytest.mark.asyncio
    async def test_reasoning_ttl(self, reasoning_cache):
        """Test reasoning cache TTL."""
        steps = [
            CoTStep(step_number=1, thought="TTL test", rationale="", confidence=1.0)
        ]

        result = ReasoningResult(
            reasoning_type="cot",
            problem="TTL test",
            steps=steps,
            final_answer="Answer",
            metadata={},
        )

        await reasoning_cache.set("ttl_reasoning", result, ttl_seconds=1)
        assert await reasoning_cache.get("ttl_reasoning") is not None

        await asyncio.sleep(1.5)
        assert await reasoning_cache.get("ttl_reasoning") is None

    @pytest.mark.asyncio
    async def test_reasoning_list_keys(self, reasoning_cache):
        """Test listing reasoning cache keys."""
        for i in range(3):
            steps = [
                CoTStep(
                    step_number=1,
                    thought=f"Test {i}",
                    rationale="",
                    confidence=1.0,
                )
            ]
            result = ReasoningResult(
                reasoning_type="cot",
                problem=f"Problem {i}",
                steps=steps,
                final_answer=f"Answer {i}",
                metadata={},
            )
            await reasoning_cache.set(f"list_key_{i}", result)

        keys = await reasoning_cache.list_keys()
        assert len(keys) >= 3

    @pytest.mark.asyncio
    async def test_mixed_reasoning_types(self, reasoning_cache):
        """Test storing both CoT and ToT in same cache."""
        cot_result = ReasoningResult(
            reasoning_type="cot",
            problem="CoT problem",
            steps=[CoTStep(step_number=1, thought="CoT", rationale="", confidence=1.0)],
            final_answer="CoT answer",
            metadata={},
        )

        tot_result = ReasoningResult(
            reasoning_type="tot",
            problem="ToT problem",
            steps=[
                ToTNode(
                    node_id="root",
                    thought="ToT",
                    parent_id=None,
                    children_ids=[],
                    score=0.9,
                    depth=0,
                )
            ],
            final_answer="ToT answer",
            metadata={},
        )

        await reasoning_cache.set("cot_key", cot_result)
        await reasoning_cache.set("tot_key", tot_result)

        retrieved_cot = await reasoning_cache.get("cot_key")
        retrieved_tot = await reasoning_cache.get("tot_key")

        assert retrieved_cot.reasoning_type == "cot"
        assert retrieved_tot.reasoning_type == "tot"

    @pytest.mark.asyncio
    async def test_reasoning_stats(self, reasoning_cache):
        """Test reasoning cache statistics."""
        for i in range(5):
            steps = [
                CoTStep(
                    step_number=1,
                    thought=f"Test {i}",
                    rationale="",
                    confidence=1.0,
                )
            ]
            result = ReasoningResult(
                reasoning_type="cot",
                problem=f"Problem {i}",
                steps=steps,
                final_answer=f"Answer {i}",
                metadata={},
            )
            await reasoning_cache.set(f"stats_key_{i}", result)

        stats = await reasoning_cache.get_stats()
        assert stats["total_entries"] >= 5


# SimilarityMatcher Tests
class TestSimilarityMatcher:
    """Test suite for SimilarityMatcher."""

    def test_embedding_generation(self, similarity_matcher):
        """Test generating embeddings."""
        text = "Test embedding generation"
        embedding = similarity_matcher.generate_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_cosine_similarity(self, similarity_matcher):
        """Test cosine similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]

        sim_identical = similarity_matcher.cosine_similarity(vec1, vec2)
        sim_orthogonal = similarity_matcher.cosine_similarity(vec1, vec3)

        assert sim_identical == pytest.approx(1.0, abs=0.01)
        assert sim_orthogonal == pytest.approx(0.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_find_similar_basic(self, similarity_matcher):
        """Test finding similar entries."""
        # Index some entries
        entries = [
            ("What is Python?", "Python is a programming language"),
            ("Explain Python", "Python is a high-level language"),
            ("What is Java?", "Java is a programming language"),
        ]

        for prompt, response in entries:
            await similarity_matcher.index_entry(prompt, response)

        # Find similar
        query = "Tell me about Python"
        matches = await similarity_matcher.find_similar(query, threshold=0.5, limit=2)

        assert len(matches) <= 2
        assert all(isinstance(m, SimilarMatch) for m in matches)

    @pytest.mark.asyncio
    async def test_similarity_threshold(self, similarity_matcher):
        """Test similarity threshold filtering."""
        await similarity_matcher.index_entry("Python programming", "About Python")

        # High threshold should return fewer results
        high_threshold_matches = await similarity_matcher.find_similar(
            "Python", threshold=0.95, limit=10
        )

        # Low threshold should return more results
        low_threshold_matches = await similarity_matcher.find_similar(
            "Python", threshold=0.3, limit=10
        )

        assert len(high_threshold_matches) <= len(low_threshold_matches)

    @pytest.mark.asyncio
    async def test_embedding_caching(self, similarity_config):
        """Test embedding caching."""
        similarity_config.cache_embeddings = True
        with patch(
            "sentence_transformers.SentenceTransformer",
            MockSentenceTransformer,
        ):
            matcher = SimilarityMatcher(similarity_config)

            text = "Test caching"
            emb1 = matcher.generate_embedding(text)
            emb2 = matcher.generate_embedding(text)

            # Should return same embedding from cache
            assert emb1 == emb2

    def test_different_embedding_models(self):
        """Test different embedding models."""
        models = [
            EmbeddingModel.MINILM,
            EmbeddingModel.MPNET,
            EmbeddingModel.DISTILBERT,
        ]

        for model in models:
            config = SimilarityConfig(model=model, threshold=0.85)
            with patch(
                "sentence_transformers.SentenceTransformer",
                MockSentenceTransformer,
            ):
                matcher = SimilarityMatcher(config)
                embedding = matcher.generate_embedding("Test")
                assert len(embedding) > 0

    @pytest.mark.asyncio
    async def test_batch_indexing(self, similarity_matcher):
        """Test batch indexing of entries."""
        entries = [(f"Prompt {i}", f"Response {i}") for i in range(10)]

        for prompt, response in entries:
            await similarity_matcher.index_entry(prompt, response)

        # Should be able to find any entry
        matches = await similarity_matcher.find_similar(
            "Prompt 5", threshold=0.5, limit=10
        )
        assert len(matches) > 0

    @pytest.mark.asyncio
    async def test_similarity_ranking(self, similarity_matcher):
        """Test similarity score ranking."""
        await similarity_matcher.index_entry("Python programming", "Python guide")
        await similarity_matcher.index_entry("Python language", "Python tutorial")
        await similarity_matcher.index_entry("Java programming", "Java guide")

        matches = await similarity_matcher.find_similar(
            "Python code", threshold=0.3, limit=3
        )

        # Matches should be sorted by score (descending)
        if len(matches) > 1:
            for i in range(len(matches) - 1):
                assert matches[i].score >= matches[i + 1].score

    @pytest.mark.asyncio
    async def test_no_matches_found(self, similarity_matcher):
        """Test when no similar matches found."""
        await similarity_matcher.index_entry(
            "Completely different", "Unrelated content"
        )

        matches = await similarity_matcher.find_similar(
            "Python programming", threshold=0.99, limit=10
        )

        # High threshold should find nothing
        assert len(matches) == 0

    @pytest.mark.asyncio
    async def test_limit_parameter(self, similarity_matcher):
        """Test limit parameter in find_similar."""
        for i in range(20):
            await similarity_matcher.index_entry(f"Test {i}", f"Response {i}")

        matches = await similarity_matcher.find_similar(
            "Test query", threshold=0.3, limit=5
        )

        assert len(matches) <= 5

    @pytest.mark.asyncio
    async def test_unicode_similarity(self, similarity_matcher):
        """Test similarity with Unicode text."""
        await similarity_matcher.index_entry("Hello world", "English greeting")
        await similarity_matcher.index_entry("مرحبا بالعالم", "Arabic greeting")
        await similarity_matcher.index_entry("你好世界", "Chinese greeting")

        matches = await similarity_matcher.find_similar(
            "Hello", threshold=0.3, limit=10
        )

        assert len(matches) > 0

    @pytest.mark.asyncio
    async def test_empty_query(self, similarity_matcher):
        """Test handling empty query."""
        matches = await similarity_matcher.find_similar("", threshold=0.8, limit=10)
        assert isinstance(matches, list)

    @pytest.mark.asyncio
    async def test_similarity_with_long_text(self, similarity_matcher):
        """Test similarity with long text."""
        long_text = "Python " * 1000
        await similarity_matcher.index_entry(long_text, "Long response")

        matches = await similarity_matcher.find_similar(
            "Python programming", threshold=0.5, limit=5
        )

        # Should handle long text without errors
        assert isinstance(matches, list)

    @pytest.mark.asyncio
    async def test_deduplication(self, similarity_matcher):
        """Test deduplication of similar entries."""
        # Add duplicate-like entries
        await similarity_matcher.index_entry("What is Python?", "Python explanation")
        await similarity_matcher.index_entry("What is Python?", "Python explanation")

        matches = await similarity_matcher.find_similar(
            "What is Python?", threshold=0.9, limit=10
        )

        # Should handle duplicates
        assert len(matches) >= 1

    @pytest.mark.asyncio
    async def test_clear_index(self, similarity_matcher):
        """Test clearing similarity index."""
        await similarity_matcher.index_entry("Test entry", "Test response")

        await similarity_matcher.clear_index()

        matches = await similarity_matcher.find_similar(
            "Test entry", threshold=0.5, limit=10
        )
        assert len(matches) == 0


# CacheManager Tests
class TestCacheManager:
    """Test suite for CacheManager."""

    @pytest.mark.asyncio
    async def test_orchestration(self, cache_manager):
        """Test cache manager orchestration."""
        response = CachedResponse(
            prompt="Orchestration test",
            response="Test response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=2,
            metadata={},
        )

        await cache_manager.set_llm_cache("test_key", response)
        retrieved = await cache_manager.get_llm_cache("test_key")

        assert retrieved is not None
        assert retrieved.response == response.response

    @pytest.mark.asyncio
    async def test_lru_eviction(self, cache_manager):
        """Test LRU eviction policy."""
        cache_manager.eviction_policy = EvictionPolicy.LRU

        # Fill cache
        for i in range(10):
            response = CachedResponse(
                prompt=f"LRU test {i}",
                response=f"Response {i}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            await cache_manager.set_llm_cache(f"lru_key_{i}", response)

        # Access some keys to update LRU order
        await cache_manager.get_llm_cache("lru_key_0")
        await cache_manager.get_llm_cache("lru_key_1")

        # Trigger eviction (implementation-specific)
        stats = await cache_manager.get_stats()
        assert stats.total_entries <= cache_manager.max_size

    @pytest.mark.asyncio
    async def test_lfu_eviction(self, cache_manager):
        """Test LFU eviction policy."""
        cache_manager.eviction_policy = EvictionPolicy.LFU

        response = CachedResponse(
            prompt="LFU test",
            response="Response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=1,
            metadata={},
        )

        await cache_manager.set_llm_cache("lfu_key", response)

        # Access multiple times to increase frequency
        for _ in range(5):
            await cache_manager.get_llm_cache("lfu_key")

        stats = await cache_manager.get_stats()
        assert stats.hits >= 5

    @pytest.mark.asyncio
    async def test_ttl_eviction(self, cache_manager):
        """Test TTL-based eviction."""
        cache_manager.eviction_policy = EvictionPolicy.TTL

        response = CachedResponse(
            prompt="TTL eviction test",
            response="Response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=1,
            metadata={},
        )

        await cache_manager.set_llm_cache("ttl_evict_key", response, ttl_seconds=1)
        await asyncio.sleep(1.5)

        retrieved = await cache_manager.get_llm_cache("ttl_evict_key")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_cache_warming(self, cache_manager):
        """Test cache warming functionality."""
        entries = [
            CachedResponse(
                prompt=f"Warm {i}",
                response=f"Response {i}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            for i in range(5)
        ]

        warmer = CacheWarmer(cache_manager)
        await warmer.warm(entries)

        # Verify entries are cached
        for i, entry in enumerate(entries):
            retrieved = await cache_manager.get_llm_cache(f"warm_{i}")
            assert retrieved is not None, "Entry should exist after warming"

    @pytest.mark.asyncio
    async def test_invalidate_all(self, cache_manager):
        """Test invalidating all cache entries."""
        # Add entries
        for i in range(3):
            response = CachedResponse(
                prompt=f"Test {i}",
                response=f"Response {i}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            await cache_manager.set_llm_cache(f"inv_key_{i}", response)

        # Invalidate all
        count = await cache_manager.invalidate_all()

        assert count >= 3

        # Verify cache is empty
        for i in range(3):
            retrieved = await cache_manager.get_llm_cache(f"inv_key_{i}")
            assert retrieved is None

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache_manager):
        """Test pattern-based invalidation."""
        # Add entries
        await cache_manager.set_llm_cache(
            "user_123_session_1",
            CachedResponse(
                prompt="Test",
                response="Response",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=1,
                metadata={},
            ),
        )
        await cache_manager.set_llm_cache(
            "user_123_session_2",
            CachedResponse(
                prompt="Test",
                response="Response",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=1,
                metadata={},
            ),
        )
        await cache_manager.set_llm_cache(
            "user_456_session_1",
            CachedResponse(
                prompt="Test",
                response="Response",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=1,
                metadata={},
            ),
        )

        # Invalidate user_123 sessions
        count = await cache_manager.invalidate_pattern("user_123*")

        assert count >= 2

    @pytest.mark.asyncio
    async def test_invalidate_older_than(self, cache_manager):
        """Test age-based invalidation."""
        old_response = CachedResponse(
            prompt="Old",
            response="Response",
            model="gpt-4",
            timestamp=datetime.now() - timedelta(hours=2),
            token_count=1,
            metadata={},
        )
        new_response = CachedResponse(
            prompt="New",
            response="Response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=1,
            metadata={},
        )

        await cache_manager.set_llm_cache("old_key", old_response)
        await cache_manager.set_llm_cache("new_key", new_response)

        # Invalidate entries older than 1 hour
        count = await cache_manager.invalidate_older_than(seconds=3600)

        assert count >= 1

        # New entry should still exist
        retrieved = await cache_manager.get_llm_cache("new_key")
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_get_stats(self, cache_manager):
        """Test getting cache statistics."""
        # Add some entries
        for i in range(3):
            response = CachedResponse(
                prompt=f"Stats test {i}",
                response=f"Response {i}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            await cache_manager.set_llm_cache(f"stats_key_{i}", response)

        # Get one entry (cache hit)
        await cache_manager.get_llm_cache("stats_key_0")

        # Try to get non-existent entry (cache miss)
        await cache_manager.get_llm_cache("nonexistent")

        stats = await cache_manager.get_stats()

        assert isinstance(stats, CacheStats)
        assert stats.total_entries >= 3
        assert stats.hits >= 1
        assert stats.misses >= 1

    @pytest.mark.asyncio
    async def test_export_entries(self, cache_manager):
        """Test exporting cache entries."""
        # Add entries
        for i in range(3):
            response = CachedResponse(
                prompt=f"Export test {i}",
                response=f"Response {i}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            await cache_manager.set_llm_cache(f"export_key_{i}", response)

        # Export
        entries = await cache_manager.export_entries()

        assert len(entries) >= 3
        assert all(isinstance(e, dict) for e in entries)

    @pytest.mark.asyncio
    async def test_import_entries(self, cache_manager):
        """Test importing cache entries."""
        entries = [
            {
                "prompt": f"Import test {i}",
                "response": f"Response {i}",
                "model": "gpt-4",
                "timestamp": datetime.now().isoformat(),
                "token_count": 2,
                "metadata": {},
            }
            for i in range(3)
        ]

        await cache_manager.import_entries(entries)

        # Verify imported entries
        for i in range(3):
            retrieved = await cache_manager.get_llm_cache(f"Import test {i}")
            assert retrieved is not None, "Should be able to retrieve imported entry"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, cache_manager):
        """Test concurrent cache operations."""

        async def set_and_get(key: str) -> bool:
            response = CachedResponse(
                prompt=f"Concurrent {key}",
                response=f"Response {key}",
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=2,
                metadata={},
            )
            await cache_manager.set_llm_cache(key, response)
            retrieved = await cache_manager.get_llm_cache(key)
            return retrieved is not None

        tasks = [set_and_get(f"key_{i}") for i in range(20)]
        results = await asyncio.gather(*tasks)

        assert all(results)

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, cache_manager):
        """Test handling memory pressure."""
        # Fill cache with large entries
        large_response = "X" * 10000

        for i in range(50):
            response = CachedResponse(
                prompt=f"Large {i}",
                response=large_response,
                model="gpt-4",
                timestamp=datetime.now(),
                token_count=5000,
                metadata={},
            )
            await cache_manager.set_llm_cache(f"large_key_{i}", response)

        stats = await cache_manager.get_stats()
        # Cache manager should handle pressure with eviction
        assert stats.total_entries <= cache_manager.max_size

    @pytest.mark.asyncio
    async def test_reasoning_and_llm_coordination(self, cache_manager):
        """Test coordinating reasoning and LLM caches."""
        # Set LLM cache
        llm_response = CachedResponse(
            prompt="Coordination test",
            response="LLM response",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=2,
            metadata={},
        )
        await cache_manager.set_llm_cache("coord_key", llm_response)

        # Set reasoning cache
        reasoning_result = ReasoningResult(
            reasoning_type="cot",
            problem="Coordination test",
            steps=[
                CoTStep(
                    step_number=1,
                    thought="Test",
                    rationale="",
                    confidence=1.0,
                )
            ],
            final_answer="Answer",
            metadata={},
        )
        await cache_manager.set_reasoning_cache("coord_reasoning", reasoning_result)

        # Retrieve both
        retrieved_llm = await cache_manager.get_llm_cache("coord_key")
        retrieved_reasoning = await cache_manager.get_reasoning_cache("coord_reasoning")

        assert retrieved_llm is not None
        assert retrieved_reasoning is not None


# DistributedCache Tests
class TestDistributedCache:
    """Test suite for DistributedCache."""

    @pytest.mark.asyncio
    async def test_consistent_hashing(self):
        """Test consistent hashing strategy."""
        nodes = ["node1:6379", "node2:6379", "node3:6379"]
        replication_config = ReplicationConfig(replicas=2)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
            replication_config=replication_config,
        )

        # Same key should map to same node
        node1 = dist_cache.get_node_for_key("test_key")
        node2 = dist_cache.get_node_for_key("test_key")

        assert node1 == node2

    @pytest.mark.asyncio
    async def test_mod_hash_sharding(self):
        """Test modulo hash sharding."""
        nodes = ["node1:6379", "node2:6379", "node3:6379"]
        replication_config = ReplicationConfig(replicas=1)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.MOD_HASH,
            replication_config=replication_config,
        )

        # Keys should distribute across nodes
        key_nodes = [dist_cache.get_node_for_key(f"key_{i}") for i in range(30)]

        # Should use all nodes
        unique_nodes = set(key_nodes)
        assert len(unique_nodes) > 1

    @pytest.mark.asyncio
    async def test_range_sharding(self):
        """Test range-based sharding."""
        nodes = ["node1:6379", "node2:6379", "node3:6379"]
        replication_config = ReplicationConfig(replicas=1)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.RANGE,
            replication_config=replication_config,
        )

        # Alphabetically sorted keys should map predictably
        node_a = dist_cache.get_node_for_key("aaa")
        node_z = dist_cache.get_node_for_key("zzz")

        # Different keys should potentially map to different nodes
        assert isinstance(node_a, str)
        assert isinstance(node_z, str)

    @pytest.mark.asyncio
    async def test_replication(self):
        """Test data replication across nodes."""
        nodes = ["node1:6379", "node2:6379", "node3:6379"]
        replication_config = ReplicationConfig(replicas=2, consistency_level="quorum")

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
            replication_config=replication_config,
        )

        replica_nodes = dist_cache.get_replica_nodes("test_key")

        # Should return replica count + 1 (primary + replicas)
        assert len(replica_nodes) == 3  # 1 primary + 2 replicas

    @pytest.mark.asyncio
    async def test_consistency_levels(self):
        """Test different consistency levels."""
        nodes = ["node1:6379", "node2:6379", "node3:6379"]

        consistency_levels = ["one", "quorum", "all"]

        for level in consistency_levels:
            replication_config = ReplicationConfig(replicas=2, consistency_level=level)

            dist_cache = DistributedCache(
                nodes=nodes,
                sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
                replication_config=replication_config,
            )

            required = dist_cache.get_required_acks()

            if level == "one":
                assert required == 1
            elif level == "quorum":
                assert required == 2  # Majority of 3
            elif level == "all":
                assert required == 3

    @pytest.mark.asyncio
    async def test_node_failure_handling(self):
        """Test handling node failures."""
        nodes = ["node1:6379", "node2:6379", "node3:6379"]
        replication_config = ReplicationConfig(replicas=2)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
            replication_config=replication_config,
        )

        # Mark node as failed
        dist_cache.mark_node_failed("node1:6379")

        # Should route to other nodes
        available_nodes = dist_cache.get_available_nodes()
        assert "node1:6379" not in available_nodes
        assert len(available_nodes) == 2

    @pytest.mark.asyncio
    async def test_node_recovery(self):
        """Test node recovery after failure."""
        nodes = ["node1:6379", "node2:6379", "node3:6379"]
        replication_config = ReplicationConfig(replicas=1)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
            replication_config=replication_config,
        )

        # Fail and recover node
        dist_cache.mark_node_failed("node1:6379")
        assert "node1:6379" not in dist_cache.get_available_nodes()

        dist_cache.mark_node_recovered("node1:6379")
        assert "node1:6379" in dist_cache.get_available_nodes()

    @pytest.mark.asyncio
    async def test_distributed_lock(self):
        """Test distributed locking mechanism."""
        nodes = ["node1:6379"]
        replication_config = ReplicationConfig(replicas=0)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
            replication_config=replication_config,
        )

        # Acquire lock
        locked = await dist_cache.acquire_lock("test_resource", timeout=5)
        assert locked is True

        # Try to acquire same lock (should fail)
        locked_again = await dist_cache.acquire_lock("test_resource", timeout=1)
        assert locked_again is False

        # Release lock
        await dist_cache.release_lock("test_resource")

        # Should be able to acquire again
        locked_third = await dist_cache.acquire_lock("test_resource", timeout=5)
        assert locked_third is True

    @pytest.mark.asyncio
    async def test_hot_spot_detection(self):
        """Test detecting hot spot keys."""
        nodes = ["node1:6379", "node2:6379"]
        replication_config = ReplicationConfig(replicas=1)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
            replication_config=replication_config,
        )

        # Simulate hot key access
        hot_key = "popular_key"
        for _ in range(1000):
            dist_cache.record_key_access(hot_key)

        hot_spots = dist_cache.get_hot_spots(threshold=100)

        assert hot_key in hot_spots

    @pytest.mark.asyncio
    async def test_resharding(self):
        """Test resharding when nodes are added/removed."""
        nodes = ["node1:6379", "node2:6379"]
        replication_config = ReplicationConfig(replicas=1)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
            replication_config=replication_config,
        )

        # Add node
        dist_cache.add_node("node3:6379")

        assert len(dist_cache.get_available_nodes()) == 3

        # Remove node
        dist_cache.remove_node("node1:6379")

        assert len(dist_cache.get_available_nodes()) == 2

    @pytest.mark.asyncio
    async def test_load_balancing(self):
        """Test load balancing across nodes."""
        nodes = ["node1:6379", "node2:6379", "node3:6379"]
        replication_config = ReplicationConfig(replicas=0)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
            replication_config=replication_config,
        )

        # Distribute keys
        node_loads = {node: 0 for node in nodes}

        for i in range(300):
            node = dist_cache.get_node_for_key(f"key_{i}")
            node_loads[node] += 1

        # Check load distribution
        loads = list(node_loads.values())
        max_load = max(loads)
        min_load = min(loads)

        # Should be reasonably balanced
        assert max_load - min_load < 100  # Allow 33% variation

    @pytest.mark.asyncio
    async def test_geographic_distribution(self):
        """Test geographic node distribution."""
        nodes = ["us-east:6379", "us-west:6379", "eu-west:6379"]
        replication_config = ReplicationConfig(replicas=1)

        dist_cache = DistributedCache(
            nodes=nodes,
            sharding_strategy=ShardingStrategy.CONSISTENT_HASH,
            replication_config=replication_config,
        )

        # Should handle geographically distributed nodes
        assert len(dist_cache.get_available_nodes()) == 3


# Metrics Tests
class TestMetrics:
    """Test suite for MetricsCollector."""

    def test_record_cache_hit(self, metrics_collector):
        """Test recording cache hits."""
        metrics_collector.record_cache_hit("test_key")
        metrics_collector.record_cache_hit("test_key")

        metrics = metrics_collector.get_cache_metrics()
        assert metrics.hits >= 2

    def test_record_cache_miss(self, metrics_collector):
        """Test recording cache misses."""
        metrics_collector.record_cache_miss("missing_key")
        metrics_collector.record_cache_miss("another_missing")

        metrics = metrics_collector.get_cache_metrics()
        assert metrics.misses >= 2

    def test_record_cache_set(self, metrics_collector):
        """Test recording cache sets."""
        metrics_collector.record_cache_set("key1", size=100)
        metrics_collector.record_cache_set("key2", size=200)

        metrics = metrics_collector.get_cache_metrics()
        assert metrics.sets >= 2

    def test_hit_rate_calculation(self, metrics_collector):
        """Test hit rate calculation."""
        # Record hits and misses
        for _ in range(7):
            metrics_collector.record_cache_hit("key")
        for _ in range(3):
            metrics_collector.record_cache_miss("key")

        metrics = metrics_collector.get_cache_metrics()
        hit_rate = metrics.hits / (metrics.hits + metrics.misses)

        assert hit_rate == pytest.approx(0.7, abs=0.01)

    def test_latency_tracking(self, metrics_collector):
        """Test latency tracking."""
        # Record latencies
        latencies = [10, 15, 12, 18, 20, 25, 30, 14, 16, 22]

        for latency in latencies:
            metrics_collector.record_get_latency(latency)

        perf_metrics = metrics_collector.get_performance_metrics()

        assert perf_metrics.avg_get_latency_ms > 0
        assert perf_metrics.p95_get_latency_ms >= perf_metrics.avg_get_latency_ms

    def test_percentile_calculation(self, metrics_collector):
        """Test percentile latency calculation."""
        # Record sorted latencies for predictable percentiles
        for i in range(100):
            metrics_collector.record_get_latency(i)

        perf_metrics = metrics_collector.get_performance_metrics()

        # P95 should be around 95
        assert 90 <= perf_metrics.p95_get_latency_ms <= 100
        # P99 should be around 99
        assert 95 <= perf_metrics.p99_get_latency_ms <= 100

    def test_prometheus_export(self, metrics_collector):
        """Test Prometheus metrics export."""
        metrics_collector.record_cache_hit("key")
        metrics_collector.record_cache_miss("key")

        prometheus_metrics = metrics_collector.export_prometheus()

        assert isinstance(prometheus_metrics, str)
        assert "cache_hits_total" in prometheus_metrics
        assert "cache_misses_total" in prometheus_metrics

    def test_metrics_reset(self, metrics_collector):
        """Test resetting metrics."""
        metrics_collector.record_cache_hit("key")
        metrics_collector.record_cache_miss("key")

        metrics_collector.reset()

        metrics = metrics_collector.get_cache_metrics()
        assert metrics.hits == 0
        assert metrics.misses == 0

    def test_cache_size_tracking(self, metrics_collector):
        """Test tracking cache size."""
        metrics_collector.record_cache_set("key1", size=1000)
        metrics_collector.record_cache_set("key2", size=2000)

        metrics = metrics_collector.get_cache_metrics()

        assert metrics.size_bytes >= 3000

    def test_eviction_tracking(self, metrics_collector):
        """Test tracking cache evictions."""
        metrics_collector.record_eviction("key1", reason="ttl_expired")
        metrics_collector.record_eviction("key2", reason="max_size")

        metrics = metrics_collector.get_cache_metrics()
        assert metrics.evictions >= 2

    def test_invalidation_tracking(self, metrics_collector):
        """Test tracking cache invalidations."""
        metrics_collector.record_invalidation("key1")
        metrics_collector.record_invalidation("key2")
        metrics_collector.record_invalidation("key3")

        metrics = metrics_collector.get_cache_metrics()
        assert metrics.invalidations >= 3


# CLI Tests
class TestCLI:
    """Test suite for CLI commands."""

    def test_cli_help(self, cli_runner):
        """Test CLI help command."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Cache Management CLI" in result.output

    def test_set_command(self, cli_runner, temp_config_file):
        """Test cache set command."""
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "set-cache",
                "What is Python?",
                "Python is a programming language",
            ],
        )
        assert result.exit_code == 0

    def test_get_command(self, cli_runner, temp_config_file):
        """Test cache get command."""
        # First set a value
        cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "set-cache",
                "Test prompt",
                "Test response",
            ],
        )

        # Then get it
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "get-cache",
                "Test prompt",
            ],
        )
        assert result.exit_code == 0

    def test_stats_command(self, cli_runner, temp_config_file):
        """Test stats command."""
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "stats",
            ],
        )
        assert result.exit_code == 0

    def test_invalidate_command(self, cli_runner, temp_config_file):
        """Test invalidate command."""
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "invalidate",
                "--pattern",
                "test*",
                "--no-confirm",
            ],
        )
        assert result.exit_code == 0

    def test_config_show_command(self, cli_runner, temp_config_file):
        """Test config show command."""
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "config",
                "show",
            ],
        )
        assert result.exit_code == 0

    def test_config_validate_command(self, cli_runner, temp_config_file):
        """Test config validate command."""
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "config",
                "validate",
            ],
        )
        assert result.exit_code == 0

    def test_metrics_command(self, cli_runner, temp_config_file):
        """Test metrics command."""
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "metrics",
            ],
        )
        assert result.exit_code == 0

    def test_export_command(self, cli_runner, temp_config_file, tmp_path):
        """Test export command."""
        export_file = tmp_path / "export.json"

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "export",
                str(export_file),
            ],
        )
        assert result.exit_code == 0
        assert export_file.exists()

    def test_import_command(self, cli_runner, temp_config_file, tmp_path):
        """Test import command."""
        import_file = tmp_path / "import.json"

        # Create import file
        data = [
            {
                "prompt": "Import test",
                "response": "Import response",
                "model": "gpt-4",
                "timestamp": datetime.now().isoformat(),
                "token_count": 2,
                "metadata": {},
            }
        ]
        with open(import_file, "w") as f:
            json.dump(data, f)

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "import-cache",
                str(import_file),
                "--no-confirm",
            ],
        )
        assert result.exit_code == 0

    def test_verbose_flag(self, cli_runner, temp_config_file):
        """Test verbose flag."""
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(temp_config_file),
                "--verbose",
                "stats",
            ],
        )
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
