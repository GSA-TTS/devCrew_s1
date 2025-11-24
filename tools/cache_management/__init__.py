"""
Cache Management & Optimization Platform.

Intelligent LLM response caching, reasoning step caching, and cache optimization
platform. Reduces LLM API costs by 70-90% through strategic caching of Chain-of-
Thought (CoT) and Tree-of-Thoughts (ToT) reasoning steps, with semantic similarity
matching for fuzzy cache hits.
"""

__version__ = "1.0.0"
__author__ = "devCrew_s1"

from .cache_manager import (CacheManager, CacheStats, CacheWarmer,
                            EvictionPolicy)
from .distributed_cache import (DistributedCache, ReplicationConfig,
                                ShardingStrategy)
from .llm_cache import CacheBackend, CacheConfig, CachedResponse, LLMCache
from .metrics import CacheMetrics, MetricsCollector, PerformanceMetrics
from .reasoning_cache import CoTStep, ReasoningCache, ReasoningResult, ToTNode
from .similarity_matcher import (EmbeddingModel, SimilarityConfig,
                                 SimilarityMatcher, SimilarMatch)

__all__ = [
    "LLMCache",
    "CacheConfig",
    "CachedResponse",
    "CacheBackend",
    "ReasoningCache",
    "CoTStep",
    "ToTNode",
    "ReasoningResult",
    "SimilarityMatcher",
    "SimilarityConfig",
    "SimilarMatch",
    "EmbeddingModel",
    "CacheManager",
    "EvictionPolicy",
    "CacheStats",
    "CacheWarmer",
    "DistributedCache",
    "ShardingStrategy",
    "ReplicationConfig",
    "MetricsCollector",
    "CacheMetrics",
    "PerformanceMetrics",
]
