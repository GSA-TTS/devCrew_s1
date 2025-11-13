# CORE-CACHE-003: Cache Management and Optimization Protocol

**Version**: 1.0
**Last Updated**: 2025-11-13
**Status**: Active
**Owner**: Backend-Engineer

## Objective

Establish intelligent cache management and optimization protocol enabling cache strategy selection, invalidation policies, cache warming, hit rate optimization, distributed cache coordination, cache coherence validation, and performance monitoring ensuring application responsiveness, reduced database load, and cost-effective resource utilization with automated cache lifecycle management.

## Tool Requirements

- **TOOL-CACHE-001** (Cache Management): Cache orchestration, cache strategy management, and cache optimization
  - Execute: Cache orchestration, cache strategy management, cache optimization, cache coordination, cache lifecycle management
  - Integration: Cache management systems, cache optimization tools, cache coordination platforms, cache monitoring, cache frameworks
  - Usage: Cache management, cache optimization, cache coordination, cache strategy implementation, cache lifecycle oversight

- **TOOL-MON-001** (APM): Cache performance monitoring, hit rate tracking, and cache analytics
  - Execute: Cache performance monitoring, hit rate tracking, cache analytics, cache metrics, performance analysis
  - Integration: Monitoring platforms, performance tracking systems, cache analytics, metrics collection, performance monitoring
  - Usage: Cache monitoring, performance tracking, hit rate analysis, cache metrics, performance optimization

- **TOOL-DATA-002** (Statistical Analysis): Cache analytics, optimization algorithms, and performance analysis
  - Execute: Cache analytics, optimization algorithms, performance analysis, cache intelligence, optimization analytics
  - Integration: Analytics platforms, optimization tools, cache analytics systems, performance analysis, statistical frameworks
  - Usage: Cache analytics, optimization analysis, performance intelligence, cache optimization, analytical insights

- **TOOL-INFRA-001** (Infrastructure): Distributed cache coordination, infrastructure integration, and cache resource management
  - Execute: Distributed cache coordination, infrastructure integration, cache resource management, cache infrastructure, resource optimization
  - Integration: Infrastructure platforms, cache infrastructure, distributed systems, resource management, infrastructure coordination
  - Usage: Cache infrastructure, distributed coordination, resource management, infrastructure optimization, cache deployment

## Trigger

- Application performance degradation due to cache misses
- New feature deployment requiring cache strategy
- Cache hit rate below threshold (<80%)
- Cache invalidation requirement after data updates
- Scheduled cache warming before traffic spikes
- Distributed cache synchronization issues
- Memory pressure requiring cache eviction

## Agents

**Primary**: Backend-Engineer
**Supporting**: Performance-Engineer, SRE, System-Architect
**Review**: Technical-Lead
**Orchestration**: Orchestrator (CORE-COORD-002)

## Prerequisites

- Cache infrastructure (Redis, Memcached, CDN, application-level)
- Cache monitoring and metrics
- Data consistency requirements defined
- TTL and eviction policies
- Cache key naming conventions
- Invalidation patterns documented

## Steps

### Step 1: Cache Strategy Selection (Estimated Time: 10 minutes)
**Action**: Select appropriate cache strategy based on data characteristics

**Cache Strategies**:
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class CacheStrategy(Enum):
    CACHE_ASIDE = "cache_aside"           # Lazy loading, app manages cache
    READ_THROUGH = "read_through"         # Cache loads data automatically
    WRITE_THROUGH = "write_through"       # Writes go through cache to DB
    WRITE_BEHIND = "write_behind"         # Async writes, eventual consistency
    REFRESH_AHEAD = "refresh_ahead"       # Proactive refresh before expiry

@dataclass
class CacheConfiguration:
    key_pattern: str
    strategy: CacheStrategy
    ttl_seconds: int
    max_size_mb: int
    eviction_policy: str  # LRU, LFU, FIFO
    consistency_requirement: str  # strong, eventual
    invalidation_pattern: str

class CacheStrategySelector:
    def recommend_strategy(self, data_type: str, read_write_ratio: float,
                          consistency: str) -> CacheStrategy:
        """Recommend cache strategy based on characteristics"""

        # High read, low write, eventual consistency: Cache-aside
        if read_write_ratio > 10 and consistency == 'eventual':
            return CacheStrategy.CACHE_ASIDE

        # High read, low write, strong consistency: Read-through
        if read_write_ratio > 5 and consistency == 'strong':
            return CacheStrategy.READ_THROUGH

        # High write, strong consistency: Write-through
        if read_write_ratio < 2 and consistency == 'strong':
            return CacheStrategy.WRITE_THROUGH

        # High write, eventual consistency: Write-behind (performance)
        if read_write_ratio < 2 and consistency == 'eventual':
            return CacheStrategy.WRITE_BEHIND

        # Predictable access patterns: Refresh-ahead
        if data_type in ['trending_content', 'hot_products']:
            return CacheStrategy.REFRESH_AHEAD

        return CacheStrategy.CACHE_ASIDE  # Default safe choice
```

**Expected Outcome**: Cache strategy selected per data characteristics
**Validation**: Strategy aligns with consistency requirements, performance goals

### Step 2: Cache Implementation with TTL and Eviction (Estimated Time: 20 minutes)
**Action**: Implement caching logic with appropriate TTL and eviction policies

**Cache Implementation**:
```python
import redis
from typing import Any, Optional
import json
import hashlib

class CacheManager:
    def __init__(self, redis_client: redis.Redis, default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        serialized = json.dumps(value)
        return self.redis.setex(key, ttl, serialized)

    def delete(self, key: str) -> bool:
        """Delete key from cache (invalidation)"""
        return self.redis.delete(key) > 0

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        keys = self.redis.keys(pattern)
        if keys:
            return self.redis.delete(*keys)
        return 0

    def cache_aside_get(self, key: str, loader_func, ttl: Optional[int] = None) -> Any:
        """Cache-aside pattern: Check cache, fallback to loader"""
        # Try cache first
        cached = self.get(key)
        if cached is not None:
            return cached

        # Cache miss: load from source
        value = loader_func()
        if value is not None:
            self.set(key, value, ttl)

        return value

    def get_or_set(self, key: str, value_func, ttl: Optional[int] = None) -> Any:
        """Atomic get-or-set operation"""
        lua_script = """
        local value = redis.call('GET', KEYS[1])
        if not value then
            value = ARGV[1]
            redis.call('SETEX', KEYS[1], ARGV[2], value)
        end
        return value
        """
        ttl = ttl or self.default_ttl
        return self.redis.eval(lua_script, 1, key, json.dumps(value_func()), ttl)
```

**Expected Outcome**: Cache implemented with appropriate TTL and eviction
**Validation**: Cache hits returning correct data, TTL expiring correctly

### Step 3: Cache Invalidation Strategy Implementation (Estimated Time: 15 minutes)
**Action**: Implement cache invalidation on data updates

**Invalidation Patterns**:
```python
from typing import List, Callable

class CacheInvalidator:
    def __init__(self, cache: CacheManager):
        self.cache = cache
        self.invalidation_hooks: dict[str, List[Callable]] = {}

    def invalidate_on_write(self, entity_type: str, entity_id: str):
        """Invalidate cache entries when entity updated"""
        invalidation_patterns = [
            f"{entity_type}:{entity_id}",           # Specific entity
            f"{entity_type}:list:*",                # Entity lists
            f"{entity_type}:count",                 # Aggregate counts
            f"user:*:{entity_type}:{entity_id}"     # User-specific views
        ]

        total_deleted = 0
        for pattern in invalidation_patterns:
            total_deleted += self.cache.delete_pattern(pattern)

        return total_deleted

    def invalidate_dependent_caches(self, entity_type: str, entity_id: str):
        """Invalidate caches that depend on this entity"""
        # Example: Invalidating order cache should also invalidate user's order list
        dependencies = {
            'order': ['user:*:orders', 'order:stats'],
            'product': ['product:list', 'category:*:products'],
            'user': ['user:*:profile', 'user:list']
        }

        if entity_type in dependencies:
            for dep_pattern in dependencies[entity_type]:
                self.cache.delete_pattern(dep_pattern)

    def register_invalidation_hook(self, entity_type: str, hook: Callable):
        """Register custom invalidation logic"""
        if entity_type not in self.invalidation_hooks:
            self.invalidation_hooks[entity_type] = []
        self.invalidation_hooks[entity_type].append(hook)

    def execute_hooks(self, entity_type: str, entity_id: str):
        """Execute registered invalidation hooks"""
        if entity_type in self.invalidation_hooks:
            for hook in self.invalidation_hooks[entity_type]:
                hook(entity_id)
```

**Expected Outcome**: Stale cache entries invalidated on data updates
**Validation**: Cache coherence maintained, no stale data served

### Step 4: Cache Warming and Pre-loading (Estimated Time: 15 minutes)
**Action**: Warm cache with frequently accessed data before traffic spikes

**Cache Warming**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

class CacheWarmer:
    def __init__(self, cache: CacheManager):
        self.cache = cache

    def warm_critical_data(self, data_loaders: dict[str, Callable]):
        """Pre-load critical data into cache"""
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}

            for key_pattern, loader_func in data_loaders.items():
                future = executor.submit(self._load_and_cache, key_pattern, loader_func)
                futures[future] = key_pattern

            results = {}
            for future in as_completed(futures):
                key_pattern = futures[future]
                try:
                    results[key_pattern] = future.result()
                except Exception as e:
                    results[key_pattern] = f"Error: {str(e)}"

            return results

    def _load_and_cache(self, key_pattern: str, loader_func: Callable) -> int:
        """Load data and cache it"""
        data = loader_func()
        if isinstance(data, dict):
            # Multiple keys to cache
            cached_count = 0
            for key, value in data.items():
                self.cache.set(key, value)
                cached_count += 1
            return cached_count
        else:
            # Single key
            self.cache.set(key_pattern, data)
            return 1

    def schedule_periodic_warming(self, schedule_cron: str):
        """Schedule cache warming at specific times"""
        # Example: Warm cache at 2 AM daily before traffic surge
        # Implementation would use APScheduler or similar
        pass
```

**Expected Outcome**: Cache warmed with frequently accessed data
**Validation**: Cache hit rate increases after warming

### Step 5: Distributed Cache Coordination and Coherence (Estimated Time: 15 minutes)
**Action**: Ensure cache coherence across distributed cache nodes

**Distributed Coordination**:
```python
import redis

class DistributedCacheCoordinator:
    def __init__(self, redis_cluster: redis.RedisCluster):
        self.redis_cluster = redis_cluster
        self.pubsub = self.redis_cluster.pubsub()

    def publish_invalidation(self, key_pattern: str):
        """Publish invalidation event to all cache nodes"""
        self.redis_cluster.publish('cache:invalidate', key_pattern)

    def subscribe_invalidations(self, callback: Callable):
        """Subscribe to invalidation events"""
        self.pubsub.subscribe('cache:invalidate')

        for message in self.pubsub.listen():
            if message['type'] == 'message':
                key_pattern = message['data'].decode('utf-8')
                callback(key_pattern)

    def atomic_increment(self, key: str, ttl: int = 3600) -> int:
        """Distributed atomic increment with TTL"""
        pipe = self.redis_cluster.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl)
        result = pipe.execute()
        return result[0]

    def distributed_lock(self, lock_key: str, timeout: int = 10):
        """Distributed lock for cache operations"""
        return self.redis_cluster.lock(lock_key, timeout=timeout)
```

**Expected Outcome**: Cache coherence maintained across nodes
**Validation**: All nodes serve consistent data, no stale entries

### Step 6: Cache Hit Rate Monitoring and Optimization (Estimated Time: 10 minutes)
**Action**: Monitor cache performance and optimize hit rates

**Metrics Collection**:
```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class CacheMetrics:
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate_percent: float
    avg_latency_ms: float
    memory_usage_mb: float
    eviction_count: int

class CacheMonitor:
    def __init__(self, cache: CacheManager):
        self.cache = cache
        self.metrics_key = "cache:metrics"

    def record_hit(self, latency_ms: float):
        """Record cache hit"""
        self.cache.redis.hincrby(self.metrics_key, 'hits', 1)
        self.cache.redis.hincrbyfloat(self.metrics_key, 'total_latency', latency_ms)

    def record_miss(self):
        """Record cache miss"""
        self.cache.redis.hincrby(self.metrics_key, 'misses', 1)

    def get_metrics(self) -> CacheMetrics:
        """Get current cache metrics"""
        metrics_data = self.cache.redis.hgetall(self.metrics_key)

        hits = int(metrics_data.get(b'hits', 0))
        misses = int(metrics_data.get(b'misses', 0))
        total = hits + misses

        hit_rate = (hits / total * 100) if total > 0 else 0.0

        return CacheMetrics(
            total_requests=total,
            cache_hits=hits,
            cache_misses=misses,
            hit_rate_percent=round(hit_rate, 2),
            avg_latency_ms=0.0,  # Calculate from total_latency
            memory_usage_mb=0.0,  # Get from Redis INFO
            eviction_count=0
        )

    def analyze_cache_efficiency(self) -> Dict:
        """Analyze cache efficiency and recommend optimizations"""
        metrics = self.get_metrics()

        recommendations = []
        if metrics.hit_rate_percent < 80:
            recommendations.append("Low hit rate: Consider increasing TTL or cache size")
        if metrics.eviction_count > metrics.cache_hits * 0.1:
            recommendations.append("High eviction rate: Increase cache size or optimize eviction policy")

        return {
            'metrics': metrics,
            'health_status': 'healthy' if metrics.hit_rate_percent >= 80 else 'needs_attention',
            'recommendations': recommendations
        }
```

**Expected Outcome**: Cache metrics collected, optimization recommendations generated
**Validation**: Hit rate ≥80%, latency within target, memory usage optimal

### Step 7: Cache Performance Report and Optimization (Estimated Time: 10 minutes)
**Action**: Generate cache performance report and apply optimizations

**Expected Outcome**: Performance report with optimization actions
**Validation**: Hit rate improved, application performance enhanced

## Expected Outputs

- **Cache Strategy Document**: Selected strategies per data type
- **Hit Rate Report**: Cache hits/misses, hit rate ≥80%
- **Invalidation Log**: Cache invalidations triggered, coherence maintained
- **Warming Schedule**: Pre-loaded data, cache warming times
- **Performance Metrics**: Latency, memory usage, eviction counts
- **Optimization Recommendations**: TTL adjustments, size increases, strategy changes
- **Success Indicators**: ≥80% hit rate, <10ms cache latency, <5% eviction rate

## Rollback/Recovery

**Trigger**: Cache corruption, distributed cache failures, performance degradation

**P-RECOVERY Integration**:
1. Flush corrupted cache and rebuild from source
2. Disable caching temporarily if failures persist
3. Fallback to direct database access
4. Restore cache from backup if available

**Verification**: Application functional without cache, performance acceptable
**Data Integrity**: Medium risk - Cache can be rebuilt from source

## Failure Handling

### Failure Scenario 1: Cache Stampede (Thundering Herd)
- **Symptoms**: Sudden cache miss causes all requests to hit database simultaneously
- **Root Cause**: Popular key expires, no request coalescing
- **Impact**: High - Database overload, application slowdown
- **Resolution**: Implement request coalescing, probabilistic early expiration
- **Prevention**: Refresh-ahead strategy, staggered TTL, mutex locks

### Failure Scenario 2: Stale Data Served Due to Invalidation Failure
- **Symptoms**: Users seeing old data after updates
- **Root Cause**: Invalidation message not propagated to all cache nodes
- **Impact**: High - Data consistency violations, user confusion
- **Resolution**: Force full cache flush, fix pub/sub mechanism
- **Prevention**: Reliable invalidation (Redis Pub/Sub), versioned cache keys

### Failure Scenario 3: Cache Memory Exhaustion
- **Symptoms**: Frequent evictions, degraded performance, OOM errors
- **Root Cause**: Cache size insufficient for working set, memory leak
- **Impact**: High - Reduced hit rate, application instability
- **Resolution**: Increase cache size, optimize eviction policy, fix leaks
- **Prevention**: Capacity planning, memory monitoring, eviction alerts

### Failure Scenario 4: Distributed Cache Split-Brain
- **Symptoms**: Different cache nodes serving different data
- **Root Cause**: Network partition, failed synchronization
- **Impact**: Critical - Data consistency violations across users
- **Resolution**: Force cache invalidation, rebuild from source, fix network
- **Prevention**: Consistent hashing, health checks, partition detection

### Failure Scenario 5: Cache Warming Overloading Source Database
- **Symptoms**: Database slow during cache warming, production impacted
- **Root Cause**: Too aggressive warming, no rate limiting
- **Impact**: High - Database overload, slow user experience
- **Resolution**: Throttle warming, use read replicas, schedule off-peak
- **Prevention**: Rate-limited warming, replica usage, gradual loading

### Failure Scenario 6: Over-Caching Causing Stale Data
- **Symptoms**: Frequently changing data served from cache, users see stale info
- **Root Cause**: TTL too long for data volatility
- **Impact**: Medium - User experience degraded, data freshness issues
- **Resolution**: Reduce TTL, implement cache-aside with short TTL
- **Prevention**: TTL aligned with data volatility, event-driven invalidation

## Validation Criteria

### Quantitative Thresholds
- Cache hit rate: ≥80%
- Cache latency: ≤10ms (p95)
- Memory usage: ≤80% of allocated
- Eviction rate: ≤5% of requests
- Invalidation accuracy: ≥99% stale entries invalidated
- Distributed coherence: 100% consistency across nodes

### Boolean Checks
- Cache strategy implemented: Pass/Fail
- TTL and eviction configured: Pass/Fail
- Invalidation working: Pass/Fail
- Cache warming executed: Pass/Fail
- Metrics collection active: Pass/Fail
- Report generated: Pass/Fail

### Qualitative Assessments
- Application responsiveness: User experience (≥4/5)
- Cache effectiveness: Backend team (≥4/5)
- Maintainability: Engineering (≥4/5)

**Overall Success**: Thresholds met AND boolean checks pass AND assessments ≥4/5

## HITL Escalation

### Automatic Triggers
- Hit rate <50%
- Cache memory exhaustion
- Distributed cache split-brain
- Cache stampede detected

### Manual Triggers
- Cache strategy changes
- TTL policy adjustments
- Capacity planning reviews

### Escalation Procedure
1. **Level 1**: Backend-Engineer optimization
2. **Level 2**: Performance-Engineer analysis
3. **Level 3**: System-Architect for strategy redesign

## Related Protocols

### Upstream
- **Application Design**: Defines caching needs
- **Database Architecture**: Provides source data

### Downstream
- **P-PERF-BENCHMARK**: Measures cache impact on performance
- **Monitoring**: Tracks cache metrics

### Alternatives
- **No Caching**: Direct database access vs. caching
- **CDN Only**: Edge caching vs. application-level

## Test Scenarios

### Happy Path
#### Scenario 1: Cache-Aside with High Hit Rate
- **Setup**: User profile cache with 1-hour TTL
- **Execution**: 10K requests, 90% cache hits
- **Expected Result**: <5ms cache latency, 90% hit rate, database load minimal
- **Validation**: Performance improved, database queries reduced

### Failure Scenarios
#### Scenario 2: Cache Stampede Recovery
- **Setup**: Popular product cache expires during traffic spike
- **Execution**: 1000 simultaneous requests cause stampede
- **Expected Result**: Request coalescing limits database to 1 query
- **Validation**: Database protected, cache rebuilt, performance maintained

### Edge Cases
#### Scenario 3: Distributed Cache Invalidation
- **Setup**: Order updated, must invalidate across 5 cache nodes
- **Execution**: Invalidation published via Redis Pub/Sub
- **Expected Result**: All nodes invalidate within 100ms, serve fresh data
- **Validation**: Cache coherence maintained, no stale data served

## Metadata

### Version History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-10 | Initial protocol for Epic 111. Cache management with strategies, invalidation, warming, distributed coordination, 6 failure scenarios. | Backend-Engineer |

### Review Cycle
- **Frequency**: Quarterly
- **Next Review**: 2026-01-10
- **Reviewers**: Backend-Engineer lead, Performance-Engineer, System-Architect

### Compliance Status
- **Framework Standards**: ✅ Compliant
- **Cache Management**: Required
- **Last Validation**: 2025-10-10

## Performance SLOs

- **Hit rate**: ≥80%
- **Cache latency**: ≤10ms (p95)
- **Memory usage**: ≤80%
- **Eviction rate**: ≤5%
- **Invalidation accuracy**: ≥99%
- **Distributed coherence**: 100%
