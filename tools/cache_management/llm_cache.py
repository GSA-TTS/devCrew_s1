"""
LLM Cache Management System.

This module provides a comprehensive caching solution for LLM responses with support
for multiple backends (Redis, in-memory, disk), TTL management, and eviction policies.

Author: devCrew_s1
License: MIT
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import diskcache
import redis
from cachetools import LFUCache, LRUCache
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class CacheBackend(str, Enum):
    """Supported cache backend types."""

    REDIS = "redis"
    MEMORY = "memory"
    DISK = "disk"


class EvictionPolicy(str, Enum):
    """Cache eviction policies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live only


class CacheConfig(BaseModel):
    """Configuration for LLM cache."""

    backend: CacheBackend = Field(
        default=CacheBackend.MEMORY, description="Cache backend type"
    )
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(
        default=50, description="Maximum Redis connections"
    )
    ttl_seconds: int = Field(
        default=3600, description="Default TTL in seconds (1 hour)"
    )
    max_size_mb: int = Field(default=500, description="Maximum cache size in MB")
    max_entries: int = Field(default=10000, description="Maximum number of entries")
    eviction_policy: EvictionPolicy = Field(
        default=EvictionPolicy.LRU, description="Cache eviction policy"
    )
    disk_cache_dir: str = Field(
        default="./cache_data", description="Directory for disk cache"
    )
    enable_compression: bool = Field(
        default=True, description="Enable response compression"
    )
    include_model_params: bool = Field(
        default=True, description="Include model params in cache key"
    )

    @field_validator("ttl_seconds")
    @classmethod
    def validate_ttl(cls, v: int) -> int:
        """Validate TTL is positive."""
        if v <= 0:
            raise ValueError("TTL must be positive")
        return v

    @field_validator("max_size_mb")
    @classmethod
    def validate_max_size(cls, v: int) -> int:
        """Validate max size is positive."""
        if v <= 0:
            raise ValueError("Max size must be positive")
        return v


class CachedResponse(BaseModel):
    """Cached LLM response data."""

    key: str = Field(description="Cache key (SHA256 hash)")
    value: str = Field(description="LLM response text")
    timestamp: float = Field(description="Unix timestamp of cache creation")
    ttl: int = Field(description="Time-to-live in seconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    token_count: Optional[int] = Field(default=None, description="Token count")
    model_name: Optional[str] = Field(default=None, description="Model name")
    prompt_hash: str = Field(description="SHA256 hash of the prompt")
    hit_count: int = Field(default=0, description="Number of cache hits")
    created_at: str = Field(description="ISO 8601 timestamp")
    expires_at: Optional[str] = Field(default=None, description="Expiration timestamp")

    def is_expired(self) -> bool:
        """Check if the cached response has expired."""
        if self.expires_at is None:
            return False
        expires_timestamp = datetime.fromisoformat(self.expires_at).timestamp()
        return time.time() > expires_timestamp

    def time_until_expiry(self) -> Optional[float]:
        """Get seconds until expiry, None if no expiration."""
        if self.expires_at is None:
            return None
        expires_timestamp = datetime.fromisoformat(self.expires_at).timestamp()
        remaining = expires_timestamp - time.time()
        return max(0.0, remaining)


class CacheStats(BaseModel):
    """Cache statistics."""

    total_entries: int = Field(default=0, description="Total cached entries")
    total_hits: int = Field(default=0, description="Total cache hits")
    total_misses: int = Field(default=0, description="Total cache misses")
    hit_rate: float = Field(default=0.0, description="Cache hit rate (0-1)")
    total_size_bytes: int = Field(default=0, description="Total cache size in bytes")
    total_size_mb: float = Field(default=0.0, description="Total cache size in MB")
    oldest_entry: Optional[str] = Field(
        default=None, description="Oldest entry timestamp"
    )
    newest_entry: Optional[str] = Field(
        default=None, description="Newest entry timestamp"
    )
    backend: str = Field(description="Cache backend type")
    eviction_policy: str = Field(description="Eviction policy")


class LLMCache:
    """
    LLM Cache Manager with multiple backend support.

    Provides caching for LLM responses with configurable backends (Redis, memory, disk),
    TTL management, eviction policies, and comprehensive statistics tracking.

    Examples:
        >>> config = CacheConfig(backend=CacheBackend.REDIS, ttl_seconds=3600)
        >>> cache = LLMCache(config)
        >>> cache.set("What is Python?", "Python is a programming language", ttl=600)
        >>> response = cache.get("What is Python?")
        >>> print(response.value)
    """

    def __init__(self, config: CacheConfig):
        """
        Initialize LLM cache with specified configuration.

        Args:
            config: Cache configuration object

        Raises:
            ConnectionError: If Redis connection fails
            IOError: If disk cache directory cannot be created
        """
        self.config = config
        self._cache: Any = None
        self._stats_hits = 0
        self._stats_misses = 0
        self._init_backend()
        logger.info(
            f"Initialized LLM cache with backend: {config.backend}, "
            f"eviction policy: {config.eviction_policy}"
        )

    def _init_backend(self) -> None:
        """Initialize the appropriate cache backend."""
        if self.config.backend == CacheBackend.REDIS:
            self._init_redis_backend()
        elif self.config.backend == CacheBackend.MEMORY:
            self._init_memory_backend()
        elif self.config.backend == CacheBackend.DISK:
            self._init_disk_backend()
        else:
            raise ValueError(f"Unsupported cache backend: {self.config.backend}")

    def _init_redis_backend(self) -> None:
        """Initialize Redis cache backend."""
        try:
            connection_pool = redis.ConnectionPool(
                host=self._parse_redis_host(),
                port=self._parse_redis_port(),
                db=self.config.redis_db,
                password=self.config.redis_password,
                max_connections=self.config.redis_max_connections,
                decode_responses=False,
            )
            self._cache = redis.Redis(connection_pool=connection_pool)
            self._cache.ping()
            logger.info("Redis cache backend initialized successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Redis connection failed: {e}") from e

    def _parse_redis_host(self) -> str:
        """Parse Redis host from URL."""
        if not self.config.redis_url:
            return "localhost"
        url = self.config.redis_url.replace("redis://", "")
        if "@" in url:
            url = url.split("@")[1]
        if "/" in url:
            url = url.split("/")[0]
        if ":" in url:
            return url.split(":")[0]
        return url

    def _parse_redis_port(self) -> int:
        """Parse Redis port from URL."""
        if not self.config.redis_url:
            return 6379
        url = self.config.redis_url.replace("redis://", "")
        if "@" in url:
            url = url.split("@")[1]
        if "/" in url:
            url = url.split("/")[0]
        if ":" in url:
            return int(url.split(":")[1])
        return 6379

    def _init_memory_backend(self) -> None:
        """Initialize in-memory cache backend."""
        if self.config.eviction_policy == EvictionPolicy.LRU:
            self._cache = LRUCache(maxsize=self.config.max_entries)
            logger.info(
                f"Memory cache (LRU) initialized with max entries: "
                f"{self.config.max_entries}"
            )
        elif self.config.eviction_policy == EvictionPolicy.LFU:
            self._cache = LFUCache(maxsize=self.config.max_entries)
            logger.info(
                f"Memory cache (LFU) initialized with max entries: "
                f"{self.config.max_entries}"
            )
        else:
            self._cache = {}
            logger.info("Memory cache (dict) initialized")

    def _init_disk_backend(self) -> None:
        """Initialize disk cache backend."""
        try:
            cache_dir = Path(self.config.disk_cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            size_limit = self.config.max_size_mb * 1024 * 1024
            self._cache = diskcache.Cache(
                directory=str(cache_dir),
                size_limit=size_limit,
                eviction_policy=self.config.eviction_policy.value,
            )
            logger.info(
                f"Disk cache initialized at {cache_dir} with size limit: "
                f"{self.config.max_size_mb}MB"
            )
        except Exception as e:
            logger.error(f"Failed to initialize disk cache: {e}")
            raise IOError(f"Disk cache initialization failed: {e}") from e

    def _generate_cache_key(
        self, prompt: str, model_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate SHA256 cache key from prompt and model parameters.

        Args:
            prompt: Input prompt text
            model_params: Optional model parameters to include in key

        Returns:
            SHA256 hash string
        """
        key_data: Dict[str, Any] = {"prompt": prompt}
        if self.config.include_model_params and model_params:
            key_data["params"] = model_params

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode("utf-8")).hexdigest()

    def _generate_prompt_hash(self, prompt: str) -> str:
        """Generate SHA256 hash of just the prompt."""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def set(
        self,
        prompt: str,
        response: str,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        model_params: Optional[Dict[str, Any]] = None,
        token_count: Optional[int] = None,
        model_name: Optional[str] = None,
    ) -> bool:
        """
        Cache an LLM response with specified TTL.

        Args:
            prompt: Input prompt text
            response: LLM response text
            ttl: Time-to-live in seconds (uses config default if None)
            metadata: Additional metadata to store
            model_params: Model parameters to include in cache key
            token_count: Token count for the response
            model_name: Name of the model used

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(prompt, model_params)
            prompt_hash = self._generate_prompt_hash(prompt)
            ttl_value = ttl if ttl is not None else self.config.ttl_seconds

            created_at = datetime.now().isoformat()
            expires_at = (
                datetime.fromtimestamp(time.time() + ttl_value).isoformat()
                if ttl_value > 0
                else None
            )

            cached_response = CachedResponse(
                key=cache_key,
                value=response,
                timestamp=time.time(),
                ttl=ttl_value,
                metadata=metadata or {},
                token_count=token_count,
                model_name=model_name,
                prompt_hash=prompt_hash,
                hit_count=0,
                created_at=created_at,
                expires_at=expires_at,
            )

            serialized_data = json.dumps(cached_response.model_dump()).encode("utf-8")

            if self.config.backend == CacheBackend.REDIS:
                if ttl_value > 0:
                    self._cache.setex(cache_key, ttl_value, serialized_data)
                else:
                    self._cache.set(cache_key, serialized_data)
            elif self.config.backend == CacheBackend.MEMORY:
                if self.config.eviction_policy == EvictionPolicy.TTL:
                    self._cache[cache_key] = (
                        cached_response,
                        time.time() + ttl_value,
                    )
                else:
                    self._cache[cache_key] = cached_response
            elif self.config.backend == CacheBackend.DISK:
                if ttl_value > 0:
                    self._cache.set(cache_key, cached_response, expire=ttl_value)
                else:
                    self._cache.set(cache_key, cached_response)

            logger.debug(
                f"Cached response for prompt hash {prompt_hash[:16]}... "
                f"with TTL {ttl_value}s"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
            return False

    def get(
        self, prompt: str, model_params: Optional[Dict[str, Any]] = None
    ) -> Optional[CachedResponse]:
        """
        Retrieve cached LLM response for exact prompt match.

        Args:
            prompt: Input prompt text
            model_params: Model parameters used in cache key

        Returns:
            CachedResponse object if found and not expired, None otherwise
        """
        try:
            cache_key = self._generate_cache_key(prompt, model_params)

            if self.config.backend == CacheBackend.REDIS:
                data = self._cache.get(cache_key)
                if data is None:
                    self._stats_misses += 1
                    return None

                cached_response = CachedResponse(**json.loads(data.decode("utf-8")))

            elif self.config.backend == CacheBackend.MEMORY:
                if cache_key not in self._cache:
                    self._stats_misses += 1
                    return None

                if self.config.eviction_policy == EvictionPolicy.TTL:
                    cached_response, expires_at = self._cache[cache_key]
                    if time.time() > expires_at:
                        del self._cache[cache_key]
                        self._stats_misses += 1
                        return None
                else:
                    cached_response = self._cache[cache_key]

            elif self.config.backend == CacheBackend.DISK:
                cached_response = self._cache.get(cache_key)
                if cached_response is None:
                    self._stats_misses += 1
                    return None

            else:
                self._stats_misses += 1
                return None

            if cached_response.is_expired():
                self.invalidate(cache_key)
                self._stats_misses += 1
                return None

            cached_response.hit_count += 1
            self._update_hit_count(cache_key, cached_response)
            self._stats_hits += 1

            logger.debug(f"Cache hit for key {cache_key[:16]}...")
            return cached_response

        except Exception as e:
            logger.error(f"Failed to retrieve cached response: {e}")
            self._stats_misses += 1
            return None

    def _update_hit_count(
        self, cache_key: str, cached_response: CachedResponse
    ) -> None:
        """Update hit count for cached response."""
        try:
            if self.config.backend == CacheBackend.REDIS:
                ttl = self._cache.ttl(cache_key)
                if ttl > 0:
                    serialized = json.dumps(cached_response.model_dump()).encode(
                        "utf-8"
                    )
                    self._cache.setex(cache_key, ttl, serialized)

            elif self.config.backend == CacheBackend.MEMORY:
                if self.config.eviction_policy == EvictionPolicy.TTL:
                    _, expires_at = self._cache[cache_key]
                    self._cache[cache_key] = (cached_response, expires_at)
                else:
                    self._cache[cache_key] = cached_response

            elif self.config.backend == CacheBackend.DISK:
                self._cache.set(cache_key, cached_response)

        except Exception as e:
            logger.warning(f"Failed to update hit count: {e}")

    def exists(
        self, prompt: str, model_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a prompt is cached without retrieving it.

        Args:
            prompt: Input prompt text
            model_params: Model parameters used in cache key

        Returns:
            True if cached and not expired, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(prompt, model_params)

            if self.config.backend == CacheBackend.REDIS:
                return self._cache.exists(cache_key) > 0

            elif self.config.backend == CacheBackend.MEMORY:
                if cache_key not in self._cache:
                    return False

                if self.config.eviction_policy == EvictionPolicy.TTL:
                    _, expires_at = self._cache[cache_key]
                    if time.time() > expires_at:
                        del self._cache[cache_key]
                        return False
                return True

            elif self.config.backend == CacheBackend.DISK:
                return cache_key in self._cache

            return False

        except Exception as e:
            logger.error(f"Failed to check cache existence: {e}")
            return False

    def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match (for Redis: glob pattern, others: prefix)

        Returns:
            Number of entries invalidated
        """
        try:
            count = 0

            if self.config.backend == CacheBackend.REDIS:
                cursor = 0
                while True:
                    cursor, keys = self._cache.scan(cursor, match=pattern, count=100)
                    if keys:
                        count += self._cache.delete(*keys)
                    if cursor == 0:
                        break

            elif self.config.backend == CacheBackend.MEMORY:
                keys_to_delete = [
                    k for k in self._cache.keys() if k.startswith(pattern)
                ]
                for key in keys_to_delete:
                    del self._cache[key]
                    count += 1

            elif self.config.backend == CacheBackend.DISK:
                keys_to_delete = [k for k in self._cache.iterkeys() if pattern in k]
                for key in keys_to_delete:
                    del self._cache[key]
                    count += 1

            logger.info(
                f"Invalidated {count} cache entries matching pattern: {pattern}"
            )
            return count

        except Exception as e:
            logger.error(f"Failed to invalidate cache entries: {e}")
            return 0

    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.config.backend == CacheBackend.REDIS:
                self._cache.flushdb()
            elif self.config.backend == CacheBackend.MEMORY:
                self._cache.clear()
            elif self.config.backend == CacheBackend.DISK:
                self._cache.clear()

            self._stats_hits = 0
            self._stats_misses = 0
            logger.info("Cache cleared successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats object with current statistics
        """
        try:
            total_entries = 0
            total_size_bytes = 0
            oldest_entry: Optional[str] = None
            newest_entry: Optional[str] = None

            if self.config.backend == CacheBackend.REDIS:
                total_entries = self._cache.dbsize()
                info = self._cache.info("memory")
                total_size_bytes = info.get("used_memory", 0)

            elif self.config.backend == CacheBackend.MEMORY:
                total_entries = len(self._cache)
                timestamps: List[float] = []

                for value in self._cache.values():
                    if self.config.eviction_policy == EvictionPolicy.TTL:
                        cached_response, _ = value
                    else:
                        cached_response = value

                    if isinstance(cached_response, CachedResponse):
                        total_size_bytes += len(
                            json.dumps(cached_response.model_dump()).encode("utf-8")
                        )
                        timestamps.append(cached_response.timestamp)

                if timestamps:
                    oldest_entry = datetime.fromtimestamp(min(timestamps)).isoformat()
                    newest_entry = datetime.fromtimestamp(max(timestamps)).isoformat()

            elif self.config.backend == CacheBackend.DISK:
                total_entries = len(self._cache)
                total_size_bytes = self._cache.volume()

            total_requests = self._stats_hits + self._stats_misses
            hit_rate = self._stats_hits / total_requests if total_requests > 0 else 0.0

            return CacheStats(
                total_entries=total_entries,
                total_hits=self._stats_hits,
                total_misses=self._stats_misses,
                hit_rate=hit_rate,
                total_size_bytes=total_size_bytes,
                total_size_mb=total_size_bytes / (1024 * 1024),
                oldest_entry=oldest_entry,
                newest_entry=newest_entry,
                backend=self.config.backend.value,
                eviction_policy=self.config.eviction_policy.value,
            )

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return CacheStats(
                backend=self.config.backend.value,
                eviction_policy=self.config.eviction_policy.value,
            )

    def get_all_keys(self, pattern: str = "*") -> List[str]:
        """
        Get all cache keys matching pattern.

        Args:
            pattern: Pattern to match (Redis glob pattern)

        Returns:
            List of matching cache keys
        """
        try:
            keys: List[str] = []

            if self.config.backend == CacheBackend.REDIS:
                cursor = 0
                while True:
                    cursor, batch = self._cache.scan(cursor, match=pattern, count=100)
                    keys.extend([k.decode("utf-8") for k in batch])
                    if cursor == 0:
                        break

            elif self.config.backend == CacheBackend.MEMORY:
                keys = list(self._cache.keys())

            elif self.config.backend == CacheBackend.DISK:
                keys = list(self._cache.iterkeys())

            return keys

        except Exception as e:
            logger.error(f"Failed to get cache keys: {e}")
            return []

    def get_entry_by_key(self, cache_key: str) -> Optional[CachedResponse]:
        """
        Get cache entry by exact key.

        Args:
            cache_key: Exact cache key

        Returns:
            CachedResponse if found, None otherwise
        """
        try:
            if self.config.backend == CacheBackend.REDIS:
                data = self._cache.get(cache_key)
                if data is None:
                    return None
                return CachedResponse(**json.loads(data.decode("utf-8")))

            elif self.config.backend == CacheBackend.MEMORY:
                if cache_key not in self._cache:
                    return None

                if self.config.eviction_policy == EvictionPolicy.TTL:
                    cached_response, expires_at = self._cache[cache_key]
                    if time.time() > expires_at:
                        del self._cache[cache_key]
                        return None
                    return cached_response
                return self._cache[cache_key]

            elif self.config.backend == CacheBackend.DISK:
                return self._cache.get(cache_key)

            return None

        except Exception as e:
            logger.error(f"Failed to get entry by key: {e}")
            return None

    def update_ttl(self, cache_key: str, new_ttl: int) -> bool:
        """
        Update TTL for a cached entry.

        Args:
            cache_key: Cache key to update
            new_ttl: New TTL in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.config.backend == CacheBackend.REDIS:
                return self._cache.expire(cache_key, new_ttl)

            elif self.config.backend == CacheBackend.MEMORY:
                if cache_key not in self._cache:
                    return False

                if self.config.eviction_policy == EvictionPolicy.TTL:
                    cached_response, _ = self._cache[cache_key]
                    self._cache[cache_key] = (
                        cached_response,
                        time.time() + new_ttl,
                    )
                    return True
                return False

            elif self.config.backend == CacheBackend.DISK:
                cached_response = self._cache.get(cache_key)
                if cached_response is None:
                    return False
                self._cache.set(cache_key, cached_response, expire=new_ttl)
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update TTL: {e}")
            return False

    def __enter__(self) -> "LLMCache":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close cache connections and cleanup resources."""
        try:
            if self.config.backend == CacheBackend.REDIS:
                if self._cache:
                    self._cache.close()
                    logger.info("Redis connection closed")

            elif self.config.backend == CacheBackend.DISK:
                if self._cache:
                    self._cache.close()
                    logger.info("Disk cache closed")

        except Exception as e:
            logger.error(f"Error closing cache: {e}")

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        self.close()
