"""
Cache Manager for Web Research Platform.

Production-ready caching system with Redis and in-memory backends,
content deduplication, compression, analytics, and cache warming strategies.
Supports configurable TTL, automatic expiration, and comprehensive statistics.
"""

import gzip
import hashlib
import json
import logging
import pickle
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import redis
from pydantic import BaseModel, Field, field_validator

# Configure logging
logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Base exception for cache operations."""

    pass


class RedisConnectionError(CacheError):
    """Exception raised when Redis connection fails."""

    pass


class CompressionError(CacheError):
    """Exception raised during compression/decompression operations."""

    pass


class CacheBackend(str, Enum):
    """Cache backend types."""

    REDIS = "redis"
    MEMORY = "memory"


class CacheConfig(BaseModel):
    """
    Configuration for cache manager.

    Attributes:
        backend: Cache backend type (redis or memory)
        redis_url: Redis connection URL (required for redis backend)
        ttl_seconds: Default time-to-live in seconds
        max_memory: Maximum memory usage in bytes (for memory backend)
        compression_enabled: Enable compression for large content
        compression_threshold: Minimum size in bytes to trigger compression
        key_prefix: Prefix for all cache keys
        enable_stats: Track cache statistics
        eviction_policy: Eviction policy for memory backend (lru, lfu)
    """

    backend: CacheBackend = Field(default=CacheBackend.MEMORY)
    redis_url: Optional[str] = Field(
        default=None, description="Redis URL (redis://host:port/db)"
    )
    ttl_seconds: int = Field(default=3600, gt=0)
    max_memory: int = Field(default=100 * 1024 * 1024, gt=0)
    compression_enabled: bool = Field(default=True)
    compression_threshold: int = Field(default=1024, gt=0)
    key_prefix: str = Field(default="webcache:")
    enable_stats: bool = Field(default=True)
    eviction_policy: str = Field(default="lru")

    @field_validator("backend", mode="before")
    @classmethod
    def validate_backend(cls, v: Any) -> CacheBackend:
        """Validate and convert backend to CacheBackend enum."""
        if isinstance(v, CacheBackend):
            return v
        if isinstance(v, str):
            return CacheBackend(v.lower())
        raise ValueError(f"Invalid backend: {v}")

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Validate Redis URL is provided when backend is redis."""
        backend = info.data.get("backend")
        if backend == CacheBackend.REDIS and not v:
            raise ValueError("redis_url is required when backend is redis")
        return v


class CacheStats(BaseModel):
    """
    Cache statistics and analytics.

    Attributes:
        total_hits: Total number of cache hits
        total_misses: Total number of cache misses
        hit_rate: Cache hit rate (0.0 to 1.0)
        total_entries: Current number of cached entries
        memory_usage: Current memory usage in bytes
        evictions: Total number of evictions
        compressions: Total number of compressions performed
        decompressions: Total number of decompressions performed
        last_reset: Timestamp of last statistics reset
    """

    total_hits: int = Field(default=0, ge=0)
    total_misses: int = Field(default=0, ge=0)
    hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    total_entries: int = Field(default=0, ge=0)
    memory_usage: int = Field(default=0, ge=0)
    evictions: int = Field(default=0, ge=0)
    compressions: int = Field(default=0, ge=0)
    decompressions: int = Field(default=0, ge=0)
    last_reset: datetime = Field(default_factory=datetime.utcnow)


class CachedContent(BaseModel):
    """
    Cached data structure.

    Attributes:
        key: Cache key
        value: Cached value
        cached_at: Timestamp when content was cached
        expires_at: Timestamp when content expires
        access_count: Number of times accessed
        size_bytes: Size of cached content in bytes
        compressed: Whether content is compressed
        content_hash: Hash of content for deduplication
    """

    key: str
    value: Any
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    access_count: int = Field(default=0, ge=0)
    size_bytes: int = Field(default=0, ge=0)
    compressed: bool = Field(default=False)
    content_hash: Optional[str] = Field(default=None)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class CacheManager:
    """
    Production-ready cache manager with Redis and in-memory backends.

    Supports content caching, deduplication, compression, analytics,
    and cache warming strategies with thread-safe operations.
    """

    def __init__(self, config: CacheConfig):
        """
        Initialize cache manager.

        Args:
            config: Cache configuration

        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self.config = config
        self._lock = threading.RLock()

        # Initialize statistics
        self._stats = CacheStats()

        # Initialize backend
        if config.backend == CacheBackend.REDIS:
            self._init_redis_backend()
        else:
            self._init_memory_backend()

        # Content hash to key mapping for deduplication
        self._hash_to_keys: Dict[str, Set[str]] = defaultdict(set)

        logger.info(
            f"Cache manager initialized with {config.backend} backend, "
            f"TTL={config.ttl_seconds}s, "
            f"compression={config.compression_enabled}"
        )

    def _init_redis_backend(self) -> None:
        """Initialize Redis backend connection."""
        try:
            self._redis_client = redis.from_url(
                self.config.redis_url,  # type: ignore
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self._redis_client.ping()
            logger.info(f"Connected to Redis at {self.config.redis_url}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            error_msg = f"Failed to connect to Redis: {str(e)}"
            logger.error(error_msg)
            raise RedisConnectionError(error_msg) from e

    def _init_memory_backend(self) -> None:
        """Initialize in-memory backend."""
        self._memory_cache: Dict[str, CachedContent] = {}
        self._access_times: Dict[str, float] = {}
        self._access_counts: Dict[str, int] = defaultdict(int)
        self._current_memory: int = 0
        logger.info("Initialized in-memory cache backend")

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired

        Raises:
            CacheError: If cache operation fails
        """
        with self._lock:
            full_key = self._make_full_key(key)

            try:
                if self.config.backend == CacheBackend.REDIS:
                    result = self._get_from_redis(full_key)
                else:
                    result = self._get_from_memory(full_key)

                if result is not None:
                    self._stats.total_hits += 1
                    logger.debug(f"Cache hit: {key}")
                else:
                    self._stats.total_misses += 1
                    logger.debug(f"Cache miss: {key}")

                self._update_hit_rate()
                return result

            except Exception as e:
                logger.error(f"Error getting from cache: {str(e)}")
                self._stats.total_misses += 1
                self._update_hit_rate()
                raise CacheError(f"Failed to get from cache: {str(e)}") from e

    def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis backend."""
        data = self._redis_client.get(key)
        if data is None:
            return None

        try:
            cached = pickle.loads(data)
            if isinstance(cached, CachedContent):
                # Check expiration
                if datetime.utcnow() >= cached.expires_at:
                    self._redis_client.delete(key)
                    return None

                # Update access count
                cached.access_count += 1
                self._redis_client.set(key, pickle.dumps(cached))

                # Unpickle and decompress if needed
                value = cached.value
                if cached.compressed:
                    value = self._decompress(value)
                    self._stats.decompressions += 1

                # Unpickle the value
                value = pickle.loads(value)

                return value
            return cached
        except Exception as e:
            logger.error(f"Error deserializing cached data: {str(e)}")
            self._redis_client.delete(key)
            return None

    def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from memory backend."""
        if key not in self._memory_cache:
            return None

        cached = self._memory_cache[key]

        # Check expiration
        if datetime.utcnow() >= cached.expires_at:
            self._remove_from_memory(key)
            return None

        # Update access tracking
        cached.access_count += 1
        self._access_times[key] = time.time()
        self._access_counts[key] += 1

        # Unpickle and decompress if needed
        value = cached.value
        if cached.compressed:
            value = self._decompress(value)
            self._stats.decompressions += 1

        # Unpickle the value
        value = pickle.loads(value)

        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise

        Raises:
            CacheError: If cache operation fails
        """
        with self._lock:
            full_key = self._make_full_key(key)
            ttl = ttl or self.config.ttl_seconds

            try:
                # Calculate content hash for deduplication
                content_hash = self.calculate_content_hash(str(value))

                # Serialize and measure size
                serialized = pickle.dumps(value)
                size_bytes = len(serialized)

                # Compress if enabled and above threshold
                compressed = False
                if (
                    self.config.compression_enabled
                    and size_bytes >= self.config.compression_threshold
                ):
                    serialized = self._compress(serialized)
                    compressed = True
                    self._stats.compressions += 1
                    logger.debug(
                        f"Compressed {key}: {size_bytes} -> {len(serialized)} bytes"
                    )

                # Create cached content
                cached = CachedContent(
                    key=full_key,
                    value=serialized,
                    expires_at=datetime.utcnow() + timedelta(seconds=ttl),
                    size_bytes=len(serialized),
                    compressed=compressed,
                    content_hash=content_hash,
                )

                # Store in appropriate backend
                if self.config.backend == CacheBackend.REDIS:
                    success = self._set_to_redis(full_key, cached, ttl)
                else:
                    success = self._set_to_memory(full_key, cached)

                if success:
                    # Update deduplication mapping
                    self._hash_to_keys[content_hash].add(full_key)
                    logger.debug(f"Cached: {key} (TTL={ttl}s)")

                return success

            except Exception as e:
                logger.error(f"Error setting cache: {str(e)}")
                raise CacheError(f"Failed to set cache: {str(e)}") from e

    def _set_to_redis(self, key: str, cached: CachedContent, ttl: int) -> bool:
        """Set value in Redis backend."""
        try:
            data = pickle.dumps(cached)
            self._redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Error setting to Redis: {str(e)}")
            return False

    def _set_to_memory(self, key: str, cached: CachedContent) -> bool:
        """Set value in memory backend."""
        # Check memory limit and evict if needed
        required_memory = cached.size_bytes
        while (
            self._current_memory + required_memory > self.config.max_memory
            and self._memory_cache
        ):
            self._evict_one()

        # Check if still not enough memory
        if self._current_memory + required_memory > self.config.max_memory:
            logger.warning("Insufficient memory for cache entry")
            return False

        # Store in memory
        self._memory_cache[key] = cached
        self._current_memory += cached.size_bytes
        self._access_times[key] = time.time()
        self._access_counts[key] = 0

        return True

    def delete(self, key: str) -> bool:
        """
        Remove entry from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found

        Raises:
            CacheError: If cache operation fails
        """
        with self._lock:
            full_key = self._make_full_key(key)

            try:
                if self.config.backend == CacheBackend.REDIS:
                    result = self._redis_client.delete(full_key)
                    return result > 0
                else:
                    return self._remove_from_memory(full_key)

            except Exception as e:
                logger.error(f"Error deleting from cache: {str(e)}")
                raise CacheError(f"Failed to delete from cache: {str(e)}") from e

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists and not expired, False otherwise
        """
        with self._lock:
            full_key = self._make_full_key(key)

            try:
                if self.config.backend == CacheBackend.REDIS:
                    return self._redis_client.exists(full_key) > 0
                else:
                    if full_key not in self._memory_cache:
                        return False
                    cached = self._memory_cache[full_key]
                    if datetime.utcnow() >= cached.expires_at:
                        self._remove_from_memory(full_key)
                        return False
                    return True

            except Exception as e:
                logger.error(f"Error checking cache existence: {str(e)}")
                return False

    def get_or_fetch(
        self, key: str, fetch_func: Callable[[], Any], ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or fetch and cache if not found.

        Args:
            key: Cache key
            fetch_func: Function to fetch value if not cached
            ttl: Time-to-live in seconds

        Returns:
            Cached or fetched value

        Raises:
            CacheError: If cache operation fails
        """
        # Try to get from cache
        value = self.get(key)
        if value is not None:
            return value

        # Fetch value
        try:
            value = fetch_func()
            self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Error fetching value: {str(e)}")
            raise CacheError(f"Failed to fetch value: {str(e)}") from e

    def generate_cache_key(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate normalized cache key from URL and parameters.

        Args:
            url: URL to generate key for
            params: Additional parameters

        Returns:
            Normalized cache key
        """
        # Parse and normalize URL
        parsed = urlparse(url)

        # Normalize scheme and netloc (lowercase)
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()

        # Normalize path (remove trailing slash, decode special chars)
        path = parsed.path.rstrip("/")

        # Parse and sort query parameters
        query_params = parse_qs(parsed.query)
        sorted_params = sorted(query_params.items())
        normalized_query = urlencode(sorted_params, doseq=True)

        # Reconstruct normalized URL
        normalized_url = urlunparse((scheme, netloc, path, "", normalized_query, ""))

        # Add additional parameters if provided
        if params:
            sorted_params_list = sorted(params.items())
            params_str = json.dumps(sorted_params_list, sort_keys=True)
            key = f"{normalized_url}::{params_str}"
        else:
            key = normalized_url

        # Generate hash for compact key
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]

        return f"url:{key_hash}"

    def calculate_content_hash(self, content: str) -> str:
        """
        Calculate content hash for deduplication.

        Args:
            content: Content to hash

        Returns:
            SHA256 hash of content
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def get_stats(self) -> CacheStats:
        """
        Retrieve cache statistics.

        Returns:
            Current cache statistics
        """
        with self._lock:
            # Update current stats
            if self.config.backend == CacheBackend.MEMORY:
                self._stats.total_entries = len(self._memory_cache)
                self._stats.memory_usage = self._current_memory
            else:
                try:
                    # Get Redis info (approximate)
                    info = self._redis_client.info("keyspace")
                    db_info = info.get("db0", {})
                    if isinstance(db_info, dict):
                        self._stats.total_entries = db_info.get("keys", 0)
                except Exception as e:
                    logger.warning(f"Failed to get Redis stats: {str(e)}")

            return self._stats.model_copy()

    def clear_expired(self) -> int:
        """
        Clear expired entries from cache.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            cleared = 0

            if self.config.backend == CacheBackend.MEMORY:
                now = datetime.utcnow()
                expired_keys = [
                    key
                    for key, cached in self._memory_cache.items()
                    if now >= cached.expires_at
                ]

                for key in expired_keys:
                    if self._remove_from_memory(key):
                        cleared += 1
            else:
                # Redis handles expiration automatically via TTL
                pass

            if cleared > 0:
                logger.info(f"Cleared {cleared} expired cache entries")

            return cleared

    def warm_cache(self, urls: List[str], fetch_func: Callable[[str], Any]) -> int:
        """
        Pre-populate cache with content from URLs.

        Args:
            urls: List of URLs to warm cache with
            fetch_func: Function to fetch content for each URL

        Returns:
            Number of entries successfully cached

        Raises:
            CacheError: If warming operation fails
        """
        cached_count = 0

        for url in urls:
            try:
                key = self.generate_cache_key(url)

                # Skip if already cached
                if self.exists(key):
                    logger.debug(f"Cache already warmed for {url}")
                    continue

                # Fetch and cache content
                content = fetch_func(url)
                if self.set(key, content):
                    cached_count += 1
                    logger.debug(f"Cache warmed: {url}")

            except Exception as e:
                logger.warning(f"Failed to warm cache for {url}: {str(e)}")
                continue

        logger.info(f"Cache warming completed: {cached_count}/{len(urls)} cached")
        return cached_count

    def find_duplicates(self) -> Dict[str, List[str]]:
        """
        Find duplicate content by hash.

        Returns:
            Dictionary mapping content hash to list of keys
        """
        with self._lock:
            duplicates = {
                hash_val: list(keys)
                for hash_val, keys in self._hash_to_keys.items()
                if len(keys) > 1
            }

            if duplicates:
                logger.info(f"Found {len(duplicates)} duplicate content groups")

            return duplicates

    def _compress(self, data: bytes) -> bytes:
        """
        Compress data using gzip.

        Args:
            data: Data to compress

        Returns:
            Compressed data

        Raises:
            CompressionError: If compression fails
        """
        try:
            return gzip.compress(data, compresslevel=6)
        except Exception as e:
            raise CompressionError(f"Compression failed: {str(e)}") from e

    def _decompress(self, data: bytes) -> bytes:
        """
        Decompress gzip data.

        Args:
            data: Compressed data

        Returns:
            Decompressed data

        Raises:
            CompressionError: If decompression fails
        """
        try:
            return gzip.decompress(data)
        except Exception as e:
            raise CompressionError(f"Decompression failed: {str(e)}") from e

    def _make_full_key(self, key: str) -> str:
        """Create full cache key with prefix."""
        return f"{self.config.key_prefix}{key}"

    def _update_hit_rate(self) -> None:
        """Update cache hit rate statistic."""
        total = self._stats.total_hits + self._stats.total_misses
        if total > 0:
            self._stats.hit_rate = self._stats.total_hits / total

    def _remove_from_memory(self, key: str) -> bool:
        """Remove entry from memory backend."""
        if key not in self._memory_cache:
            return False

        cached = self._memory_cache[key]
        self._current_memory -= cached.size_bytes
        del self._memory_cache[key]

        # Clean up tracking
        self._access_times.pop(key, None)
        self._access_counts.pop(key, None)

        # Clean up deduplication mapping
        if cached.content_hash:
            self._hash_to_keys[cached.content_hash].discard(key)
            if not self._hash_to_keys[cached.content_hash]:
                del self._hash_to_keys[cached.content_hash]

        return True

    def _evict_one(self) -> bool:
        """
        Evict one entry from memory cache based on policy.

        Returns:
            True if evicted, False if cache is empty
        """
        if not self._memory_cache:
            return False

        # Select victim based on eviction policy
        if self.config.eviction_policy == "lru":
            # Least Recently Used
            victim_key = min(
                self._access_times.keys(),
                key=lambda k: self._access_times[k],
            )
        else:  # lfu
            # Least Frequently Used
            victim_key = min(
                self._access_counts.keys(),
                key=lambda k: self._access_counts[k],
            )

        # Remove victim
        if self._remove_from_memory(victim_key):
            self._stats.evictions += 1
            logger.debug(f"Evicted cache entry: {victim_key}")
            return True

        return False

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._lock:
            self._stats = CacheStats()
            logger.info("Cache statistics reset")

    def clear_all(self) -> int:
        """
        Clear all entries from cache.

        Returns:
            Number of entries cleared

        Raises:
            CacheError: If clear operation fails
        """
        with self._lock:
            try:
                if self.config.backend == CacheBackend.REDIS:
                    # Clear only keys with our prefix
                    pattern = f"{self.config.key_prefix}*"
                    cursor = 0
                    cleared = 0

                    while True:
                        cursor, keys = self._redis_client.scan(
                            cursor, match=pattern, count=100
                        )
                        if keys:
                            cleared += self._redis_client.delete(*keys)
                        if cursor == 0:
                            break

                    logger.info(f"Cleared {cleared} Redis cache entries")
                    return cleared
                else:
                    count = len(self._memory_cache)
                    self._memory_cache.clear()
                    self._access_times.clear()
                    self._access_counts.clear()
                    self._current_memory = 0
                    self._hash_to_keys.clear()
                    logger.info(f"Cleared {count} memory cache entries")
                    return count

            except Exception as e:
                logger.error(f"Error clearing cache: {str(e)}")
                raise CacheError(f"Failed to clear cache: {str(e)}") from e

    def get_memory_usage(self) -> Tuple[int, int]:
        """
        Get current and maximum memory usage.

        Returns:
            Tuple of (current_bytes, max_bytes)
        """
        if self.config.backend == CacheBackend.MEMORY:
            return (self._current_memory, self.config.max_memory)
        else:
            try:
                info = self._redis_client.info("memory")
                used = info.get("used_memory", 0)
                max_mem = info.get("maxmemory", 0)
                return (used, max_mem)
            except Exception as e:
                logger.warning(f"Failed to get Redis memory info: {str(e)}")
                return (0, 0)

    def close(self) -> None:
        """Close cache connections and cleanup resources."""
        with self._lock:
            if self.config.backend == CacheBackend.REDIS:
                try:
                    self._redis_client.close()
                    logger.info("Redis connection closed")
                except Exception as e:
                    logger.warning(f"Error closing Redis connection: {str(e)}")
            else:
                self._memory_cache.clear()
                self._access_times.clear()
                self._access_counts.clear()
                self._hash_to_keys.clear()
                self._current_memory = 0
                logger.info("Memory cache cleared")

    def __enter__(self) -> "CacheManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CacheManager(backend={self.config.backend}, "
            f"entries={self._stats.total_entries}, "
            f"hit_rate={self._stats.hit_rate:.2%})"
        )
