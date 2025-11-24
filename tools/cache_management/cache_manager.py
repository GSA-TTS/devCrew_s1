"""
Cache Manager for LLM Response Caching Platform.

This module provides comprehensive cache orchestration, management, and
optimization capabilities including eviction policies, cache warming,
batch invalidation, and usage analytics.

Features:
- Orchestrated get with exact and fuzzy matching
- Multiple eviction policies (LRU, LFU, TTL, RANDOM)
- Automated cache warming with scheduling
- Batch invalidation with pattern matching
- Usage analytics and efficiency metrics
- Cost savings calculation
"""

import hashlib
import heapq
import logging
import random
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class EvictionPolicy(str, Enum):
    """Cache eviction policy strategies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    RANDOM = "random"  # Random eviction


class CacheStats(BaseModel):
    """Cache statistics and performance metrics."""

    hit_count: int = Field(default=0, description="Total cache hits")
    miss_count: int = Field(default=0, description="Total cache misses")
    exact_hit_count: int = Field(default=0, description="Exact match hits")
    fuzzy_hit_count: int = Field(default=0, description="Fuzzy match hits")
    hit_rate: float = Field(default=0.0, description="Cache hit rate (0-1)")
    memory_usage_mb: float = Field(default=0.0, description="Cache memory usage in MB")
    eviction_count: int = Field(default=0, description="Total evictions")
    entry_count: int = Field(default=0, description="Current cache entries")
    avg_latency_ms: float = Field(
        default=0.0, description="Average cache operation latency"
    )
    total_cost_saved_usd: float = Field(
        default=0.0, description="Estimated cost savings"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    @field_validator("hit_rate")
    @classmethod
    def validate_hit_rate(cls, v: float) -> float:
        """Validate hit rate is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Hit rate must be between 0.0 and 1.0")
        return v


class CacheWarmer(BaseModel):
    """Configuration for cache warming operations."""

    prompts: List[str] = Field(default_factory=list, description="Prompts to pre-cache")
    schedule: Optional[str] = Field(
        default=None, description="Cron schedule for warming"
    )
    model_name: str = Field(
        default="gpt-3.5-turbo", description="LLM model for warming"
    )
    priority: int = Field(default=1, description="Warming priority (1-10)")
    enabled: bool = Field(default=True, description="Whether warming is enabled")
    batch_size: int = Field(default=10, description="Batch size for warming")
    max_retries: int = Field(default=3, description="Max retries per prompt")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Validate priority is between 1 and 10."""
        if not 1 <= v <= 10:
            raise ValueError("Priority must be between 1 and 10")
        return v

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        """Validate batch size is positive."""
        if v <= 0:
            raise ValueError("Batch size must be positive")
        return v


@dataclass
class CacheEntry:
    """Internal cache entry with metadata."""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl: Optional[int]
    size_bytes: int
    model_name: str
    cost_usd: float


@dataclass
class EvictionCandidate:
    """Candidate for cache eviction with scoring."""

    key: str
    score: float
    entry: CacheEntry


class CacheManager:
    """
    Comprehensive cache manager with orchestration and optimization.

    Manages LLM response caching with multiple eviction policies,
    cache warming, batch operations, and advanced analytics.
    """

    def __init__(
        self,
        llm_cache: Optional[Any] = None,
        reasoning_cache: Optional[Any] = None,
        similarity_matcher: Optional[Any] = None,
        max_memory_mb: float = 1024.0,
        default_ttl: int = 3600,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
    ):
        """
        Initialize cache manager.

        Args:
            llm_cache: LLM response cache instance
            reasoning_cache: Reasoning step cache instance
            similarity_matcher: Semantic similarity matcher
            max_memory_mb: Maximum cache memory in MB
            default_ttl: Default TTL in seconds
            eviction_policy: Eviction policy to use
        """
        self.llm_cache = llm_cache
        self.reasoning_cache = reasoning_cache
        self.similarity_matcher = similarity_matcher
        self.max_memory_mb = max_memory_mb
        self.default_ttl = default_ttl
        self.eviction_policy = eviction_policy

        # Internal state
        self._entries: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU
        self._access_frequency: Dict[str, int] = defaultdict(int)  # For LFU
        self._stats = CacheStats()
        self._warmers: List[CacheWarmer] = []
        self._warming_active = False

        # Cost tracking
        self._cost_per_token = 0.000002  # $0.002 per 1K tokens
        self._avg_tokens_per_request = 500

        logger.info(
            f"Initialized CacheManager with policy={eviction_policy.value}, "
            f"max_memory={max_memory_mb}MB"
        )

    def orchestrate_get(
        self,
        prompt: str,
        model_name: str = "gpt-3.5-turbo",
        similarity_threshold: float = 0.85,
        use_fuzzy: bool = True,
    ) -> Optional[Any]:
        """
        Orchestrated cache retrieval with exact and fuzzy matching.

        First attempts exact match, then falls back to semantic similarity
        if fuzzy matching is enabled.

        Args:
            prompt: Input prompt to lookup
            model_name: LLM model name
            similarity_threshold: Minimum similarity for fuzzy match
            use_fuzzy: Whether to use fuzzy matching

        Returns:
            Cached response if found, None otherwise
        """
        start_time = time.time()

        try:
            # Generate cache key
            cache_key = self._generate_key(prompt, model_name)

            # Try exact match first
            if cache_key in self._entries:
                entry = self._entries[cache_key]

                # Check TTL
                if self._is_expired(entry):
                    self._remove_entry(cache_key)
                    self._stats.miss_count += 1
                    return None

                # Update access metadata
                self._update_access(cache_key)

                self._stats.hit_count += 1
                self._stats.exact_hit_count += 1
                self._update_hit_rate()

                latency = (time.time() - start_time) * 1000
                self._update_avg_latency(latency)

                logger.debug(
                    f"Exact cache hit for key={cache_key[:16]}... "
                    f"latency={latency:.2f}ms"
                )

                return entry.value

            # Try fuzzy matching with similarity matcher
            if use_fuzzy and self.similarity_matcher:
                similar_result = self._find_similar(
                    prompt, model_name, similarity_threshold
                )

                if similar_result:
                    similar_key, similarity_score, value = similar_result

                    # Update access for similar entry
                    self._update_access(similar_key)

                    self._stats.hit_count += 1
                    self._stats.fuzzy_hit_count += 1
                    self._update_hit_rate()

                    latency = (time.time() - start_time) * 1000
                    self._update_avg_latency(latency)

                    logger.debug(
                        f"Fuzzy cache hit with similarity={similarity_score:.3f} "
                        f"latency={latency:.2f}ms"
                    )

                    return value

            # Cache miss
            self._stats.miss_count += 1
            self._update_hit_rate()

            latency = (time.time() - start_time) * 1000
            self._update_avg_latency(latency)

            logger.debug(f"Cache miss for prompt='{prompt[:50]}...'")

            return None

        except Exception as e:
            logger.error(f"Error in orchestrate_get: {e}", exc_info=True)
            return None

    def put(
        self,
        prompt: str,
        response: Any,
        model_name: str = "gpt-3.5-turbo",
        ttl: Optional[int] = None,
        cost_usd: float = 0.0,
    ) -> bool:
        """
        Store response in cache.

        Args:
            prompt: Input prompt
            response: LLM response to cache
            model_name: Model name
            ttl: Time to live in seconds
            cost_usd: Cost of LLM call

        Returns:
            True if stored successfully
        """
        try:
            cache_key = self._generate_key(prompt, model_name)
            ttl = ttl or self.default_ttl

            # Calculate size
            size_bytes = self._estimate_size(response)

            # Check memory limit
            if not self._has_space(size_bytes):
                self.enforce_eviction_policy(self.eviction_policy)

            # Create entry
            entry = CacheEntry(
                key=cache_key,
                value=response,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=0,
                ttl=ttl,
                size_bytes=size_bytes,
                model_name=model_name,
                cost_usd=cost_usd,
            )

            self._entries[cache_key] = entry
            self._access_order.append(cache_key)
            self._access_frequency[cache_key] = 0

            # Update stats
            self._stats.entry_count = len(self._entries)
            self._update_memory_usage()

            logger.debug(
                f"Cached response for key={cache_key[:16]}... "
                f"size={size_bytes} bytes"
            )

            return True

        except Exception as e:
            logger.error(f"Error in put: {e}", exc_info=True)
            return False

    def enforce_eviction_policy(self, policy: Optional[EvictionPolicy] = None) -> int:
        """
        Enforce cache eviction policy to free memory.

        Args:
            policy: Eviction policy to use (uses default if None)

        Returns:
            Number of entries evicted
        """
        policy = policy or self.eviction_policy
        evicted_count = 0

        try:
            # Calculate how much to evict (25% of entries)
            target_evictions = max(1, len(self._entries) // 4)

            if policy == EvictionPolicy.LRU:
                evicted_count = self._evict_lru(target_evictions)
            elif policy == EvictionPolicy.LFU:
                evicted_count = self._evict_lfu(target_evictions)
            elif policy == EvictionPolicy.TTL:
                evicted_count = self._evict_expired()
            elif policy == EvictionPolicy.RANDOM:
                evicted_count = self._evict_random(target_evictions)

            self._stats.eviction_count += evicted_count
            self._stats.entry_count = len(self._entries)
            self._update_memory_usage()

            logger.info(f"Evicted {evicted_count} entries using policy={policy.value}")

            return evicted_count

        except Exception as e:
            logger.error(f"Error in enforce_eviction_policy: {e}", exc_info=True)
            return 0

    def warm_cache(self, prompts: List[str], model_name: str = "gpt-3.5-turbo") -> int:
        """
        Pre-populate cache with common prompts.

        Args:
            prompts: List of prompts to warm
            model_name: Model name to use

        Returns:
            Number of entries warmed
        """
        warmed_count = 0

        try:
            logger.info(f"Starting cache warming with {len(prompts)} prompts")

            for prompt in prompts:
                cache_key = self._generate_key(prompt, model_name)

                # Skip if already cached
                if cache_key in self._entries:
                    continue

                # Simulate LLM response (in production, would call actual LLM)
                response = self._generate_mock_response(prompt, model_name)

                if self.put(prompt, response, model_name, ttl=self.default_ttl * 2):
                    warmed_count += 1

            logger.info(f"Cache warming completed: {warmed_count} entries added")

            return warmed_count

        except Exception as e:
            logger.error(f"Error in warm_cache: {e}", exc_info=True)
            return warmed_count

    def schedule_warming(
        self, prompts: List[str], cron: str, model_name: str = "gpt-3.5-turbo"
    ) -> bool:
        """
        Schedule cache warming with cron expression.

        Args:
            prompts: Prompts to warm
            cron: Cron schedule expression
            model_name: Model name

        Returns:
            True if scheduled successfully
        """
        try:
            warmer = CacheWarmer(prompts=prompts, schedule=cron, model_name=model_name)

            self._warmers.append(warmer)

            logger.info(
                f"Scheduled cache warming with {len(prompts)} prompts "
                f"on schedule '{cron}'"
            )

            return True

        except Exception as e:
            logger.error(f"Error in schedule_warming: {e}", exc_info=True)
            return False

    def batch_invalidate(self, patterns: List[str]) -> int:
        """
        Invalidate cache entries matching patterns.

        Args:
            patterns: List of regex patterns to match keys

        Returns:
            Number of entries invalidated
        """
        invalidated_count = 0

        try:
            compiled_patterns = [re.compile(p) for p in patterns]
            keys_to_remove = []

            for key in self._entries.keys():
                for pattern in compiled_patterns:
                    if pattern.search(key):
                        keys_to_remove.append(key)
                        break

            for key in keys_to_remove:
                self._remove_entry(key)
                invalidated_count += 1

            self._stats.entry_count = len(self._entries)
            self._update_memory_usage()

            logger.info(
                f"Batch invalidated {invalidated_count} entries "
                f"matching {len(patterns)} patterns"
            )

            return invalidated_count

        except Exception as e:
            logger.error(f"Error in batch_invalidate: {e}", exc_info=True)
            return 0

    def analyze_usage(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze cache usage patterns over time period.

        Args:
            days: Number of days to analyze

        Returns:
            Usage analysis report
        """
        try:
            cutoff_time = time.time() - (days * 86400)

            # Analyze entries
            recent_entries = [
                e for e in self._entries.values() if e.created_at >= cutoff_time
            ]

            if not recent_entries:
                return {
                    "period_days": days,
                    "total_entries": 0,
                    "message": "No entries in time period",
                }

            # Calculate statistics
            total_accesses = sum(e.access_count for e in recent_entries)
            avg_accesses = total_accesses / len(recent_entries) if recent_entries else 0
            avg_lifetime = sum(
                time.time() - e.created_at for e in recent_entries
            ) / len(recent_entries)

            # Model distribution
            model_dist: Dict[str, int] = defaultdict(int)
            for entry in recent_entries:
                model_dist[entry.model_name] += 1

            # Top accessed entries
            top_entries = sorted(
                recent_entries, key=lambda e: e.access_count, reverse=True
            )[:10]

            analysis = {
                "period_days": days,
                "total_entries": len(recent_entries),
                "total_accesses": total_accesses,
                "avg_accesses_per_entry": round(avg_accesses, 2),
                "avg_lifetime_hours": round(avg_lifetime / 3600, 2),
                "model_distribution": dict(model_dist),
                "top_accessed_keys": [e.key[:32] for e in top_entries],
                "top_access_counts": [e.access_count for e in top_entries],
                "memory_efficiency": self._calculate_memory_efficiency(),
                "hit_rate": self._stats.hit_rate,
                "cost_savings_usd": self._stats.total_cost_saved_usd,
            }

            logger.info(f"Usage analysis completed for {days} days")

            return analysis

        except Exception as e:
            logger.error(f"Error in analyze_usage: {e}", exc_info=True)
            return {"error": str(e)}

    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """
        Calculate cache efficiency and cost savings.

        Returns:
            Efficiency metrics including cost savings
        """
        try:
            total_requests = self._stats.hit_count + self._stats.miss_count

            if total_requests == 0:
                return {
                    "total_requests": 0,
                    "hit_rate": 0.0,
                    "cost_savings_usd": 0.0,
                    "message": "No cache activity yet",
                }

            # Calculate cost savings
            avg_cost_per_call = self._cost_per_token * self._avg_tokens_per_request
            saved_calls = self._stats.hit_count
            total_savings = saved_calls * avg_cost_per_call

            # Update stats
            self._stats.total_cost_saved_usd = total_savings

            # Calculate efficiency score
            efficiency_score = self._calculate_efficiency_score()

            metrics = {
                "total_requests": total_requests,
                "cache_hits": self._stats.hit_count,
                "cache_misses": self._stats.miss_count,
                "hit_rate": self._stats.hit_rate,
                "exact_hit_rate": (
                    self._stats.exact_hit_count / total_requests
                    if total_requests > 0
                    else 0.0
                ),
                "fuzzy_hit_rate": (
                    self._stats.fuzzy_hit_count / total_requests
                    if total_requests > 0
                    else 0.0
                ),
                "cost_savings_usd": round(total_savings, 4),
                "cost_per_saved_call": round(avg_cost_per_call, 6),
                "efficiency_score": efficiency_score,
                "memory_usage_mb": self._stats.memory_usage_mb,
                "avg_latency_ms": self._stats.avg_latency_ms,
                "eviction_count": self._stats.eviction_count,
            }

            logger.debug(
                f"Efficiency metrics: hit_rate={metrics['hit_rate']:.3f}, "
                f"savings=${metrics['cost_savings_usd']:.2f}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error in get_efficiency_metrics: {e}", exc_info=True)
            return {"error": str(e)}

    def get_stats(self) -> CacheStats:
        """
        Get comprehensive cache statistics.

        Returns:
            Current cache statistics
        """
        self._stats.entry_count = len(self._entries)
        self._update_memory_usage()
        self._stats.last_updated = datetime.utcnow()

        return self._stats

    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if cleared successfully
        """
        try:
            self._entries.clear()
            self._access_order.clear()
            self._access_frequency.clear()

            self._stats.entry_count = 0
            self._stats.memory_usage_mb = 0.0

            logger.info("Cache cleared successfully")

            return True

        except Exception as e:
            logger.error(f"Error in clear: {e}", exc_info=True)
            return False

    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics for monitoring.

        Returns:
            Complete metrics export
        """
        return {
            "stats": self._stats.model_dump(),
            "efficiency": self.get_efficiency_metrics(),
            "policy": self.eviction_policy.value,
            "max_memory_mb": self.max_memory_mb,
            "default_ttl": self.default_ttl,
            "active_warmers": len(self._warmers),
        }

    # Private helper methods

    def _generate_key(self, prompt: str, model_name: str) -> str:
        """Generate cache key from prompt and model."""
        combined = f"{model_name}:{prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        if entry.ttl is None:
            return False
        return time.time() - entry.created_at > entry.ttl

    def _update_access(self, key: str) -> None:
        """Update access metadata for cache entry."""
        if key in self._entries:
            self._entries[key].last_accessed = time.time()
            self._entries[key].access_count += 1
            self._access_frequency[key] += 1

            # Update LRU order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self._entries:
            del self._entries[key]

        if key in self._access_order:
            self._access_order.remove(key)

        if key in self._access_frequency:
            del self._access_frequency[key]

    def _find_similar(
        self, prompt: str, model_name: str, threshold: float
    ) -> Optional[Tuple[str, float, Any]]:
        """Find similar cached entry using semantic similarity."""
        if not self.similarity_matcher or not self._entries:
            return None

        try:
            # Get embeddings for prompt
            # In production, would use actual similarity matcher
            # For now, return None (similarity matching requires embeddings)
            return None

        except Exception as e:
            logger.error(f"Error finding similar entry: {e}")
            return None

    def _evict_lru(self, count: int) -> int:
        """Evict least recently used entries."""
        evicted = 0

        for _ in range(min(count, len(self._access_order))):
            if self._access_order:
                key = self._access_order.pop(0)
                self._remove_entry(key)
                evicted += 1

        return evicted

    def _evict_lfu(self, count: int) -> int:
        """Evict least frequently used entries."""
        evicted = 0

        # Build min heap of (frequency, key)
        heap = [(freq, key) for key, freq in self._access_frequency.items()]
        heapq.heapify(heap)

        for _ in range(min(count, len(heap))):
            if heap:
                _, key = heapq.heappop(heap)
                self._remove_entry(key)
                evicted += 1

        return evicted

    def _evict_expired(self) -> int:
        """Evict all expired entries."""
        evicted = 0
        keys_to_remove = []

        for key, entry in self._entries.items():
            if self._is_expired(entry):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self._remove_entry(key)
            evicted += 1

        return evicted

    def _evict_random(self, count: int) -> int:
        """Evict random entries."""
        evicted = 0
        keys = list(self._entries.keys())

        for _ in range(min(count, len(keys))):
            if keys:
                key = random.choice(keys)
                keys.remove(key)
                self._remove_entry(key)
                evicted += 1

        return evicted

    def _estimate_size(self, obj: Any) -> int:
        """Estimate size of object in bytes."""
        try:
            import sys

            return sys.getsizeof(obj)
        except Exception:
            # Rough estimate
            return 1024

    def _has_space(self, required_bytes: int) -> bool:
        """Check if cache has space for new entry."""
        current_mb = self._stats.memory_usage_mb
        required_mb = required_bytes / (1024 * 1024)
        return (current_mb + required_mb) <= self.max_memory_mb

    def _update_memory_usage(self) -> None:
        """Update memory usage statistics."""
        total_bytes = sum(e.size_bytes for e in self._entries.values())
        self._stats.memory_usage_mb = total_bytes / (1024 * 1024)

    def _update_hit_rate(self) -> None:
        """Update cache hit rate."""
        total = self._stats.hit_count + self._stats.miss_count
        if total > 0:
            self._stats.hit_rate = self._stats.hit_count / total
        else:
            self._stats.hit_rate = 0.0

    def _update_avg_latency(self, latency_ms: float) -> None:
        """Update average latency with new sample."""
        total = self._stats.hit_count + self._stats.miss_count
        if total > 0:
            current_avg = self._stats.avg_latency_ms
            self._stats.avg_latency_ms = (
                current_avg * (total - 1) + latency_ms
            ) / total

    def _calculate_memory_efficiency(self) -> float:
        """Calculate memory efficiency score."""
        if self._stats.memory_usage_mb == 0:
            return 1.0

        # Efficiency = (hit_rate * entries) / memory_mb
        entries = len(self._entries)
        if entries == 0:
            return 0.0

        efficiency = self._stats.hit_rate * entries / self._stats.memory_usage_mb
        return round(min(efficiency, 1.0), 4)

    def _calculate_efficiency_score(self) -> float:
        """Calculate overall efficiency score (0-1)."""
        # Weighted score: 60% hit rate, 30% memory efficiency, 10% latency
        hit_rate_score = self._stats.hit_rate
        memory_score = self._calculate_memory_efficiency()

        # Latency score (lower is better, normalize to 0-1)
        latency_score = 1.0
        if self._stats.avg_latency_ms > 0:
            # Assume 100ms is poor, 1ms is excellent
            latency_score = max(0.0, 1.0 - (self._stats.avg_latency_ms / 100.0))

        efficiency = 0.6 * hit_rate_score + 0.3 * memory_score + 0.1 * latency_score
        return round(efficiency, 4)

    def _generate_mock_response(self, prompt: str, model_name: str) -> str:
        """Generate mock response for cache warming."""
        return f"Mock response for '{prompt[:50]}...' using {model_name}"
