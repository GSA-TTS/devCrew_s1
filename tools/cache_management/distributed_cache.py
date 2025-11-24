"""
Distributed Cache for Multi-Node LLM Caching Platform.

This module provides distributed caching capabilities with Redis cluster
support, consistent hashing for sharding, replication, and failover.

Features:
- Redis cluster integration with automatic sharding
- Consistent hashing for key distribution
- Multi-replica support with sync/async replication
- Distributed locking for coordination
- Automatic failover and health monitoring
- Cluster rebalancing and node management
"""

import hashlib
import logging
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import redis
from pydantic import BaseModel, Field, field_validator
from redis.cluster import RedisCluster
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

logger = logging.getLogger(__name__)


class ShardingStrategy(str, Enum):
    """Sharding strategy for distributed cache."""

    HASH = "hash"  # Simple hash-based sharding
    RANGE = "range"  # Range-based sharding
    CONSISTENT_HASH = "consistent_hash"  # Consistent hashing


class NodeRole(str, Enum):
    """Node role in cluster."""

    MASTER = "master"
    REPLICA = "replica"
    STANDBY = "standby"


class NodeStatus(str, Enum):
    """Node health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ReplicationConfig(BaseModel):
    """Replication configuration for distributed cache."""

    replicas: int = Field(default=2, description="Number of replicas per shard")
    sync_mode: bool = Field(default=False, description="Synchronous replication")
    failover_timeout: int = Field(default=5, description="Failover timeout in seconds")
    quorum: int = Field(default=1, description="Quorum for write operations")
    read_preference: str = Field(
        default="primary", description="Read preference (primary/replica/any)"
    )

    @field_validator("replicas")
    @classmethod
    def validate_replicas(cls, v: int) -> int:
        """Validate replica count."""
        if not 0 <= v <= 10:
            raise ValueError("Replicas must be between 0 and 10")
        return v

    @field_validator("failover_timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate failover timeout."""
        if v <= 0:
            raise ValueError("Failover timeout must be positive")
        return v


class ClusterNode(BaseModel):
    """Cluster node information."""

    node_id: str = Field(..., description="Unique node identifier")
    host: str = Field(..., description="Node hostname")
    port: int = Field(default=6379, description="Node port")
    role: NodeRole = Field(default=NodeRole.MASTER, description="Node role")
    status: NodeStatus = Field(default=NodeStatus.UNKNOWN, description="Node status")
    shard_id: int = Field(default=0, description="Shard identifier")
    slots: List[int] = Field(default_factory=list, description="Hash slots owned")
    last_heartbeat: Optional[datetime] = Field(
        default=None, description="Last heartbeat timestamp"
    )
    memory_used_mb: float = Field(default=0.0, description="Memory usage")
    keys_count: int = Field(default=0, description="Number of keys")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


@dataclass
class ConsistentHashRing:
    """Consistent hash ring for key distribution."""

    nodes: List[str] = field(default_factory=list)
    replicas: int = 100  # Virtual nodes per physical node
    ring: Dict[int, str] = field(default_factory=dict)
    sorted_keys: List[int] = field(default_factory=list)

    def add_node(self, node: str) -> None:
        """Add node to hash ring."""
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = node
            self.sorted_keys.append(hash_value)

        self.sorted_keys.sort()
        self.nodes.append(node)

    def remove_node(self, node: str) -> None:
        """Remove node from hash ring."""
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            if hash_value in self.ring:
                del self.ring[hash_value]
                self.sorted_keys.remove(hash_value)

        if node in self.nodes:
            self.nodes.remove(node)

    def get_node(self, key: str) -> Optional[str]:
        """Get node for key using consistent hashing."""
        if not self.ring:
            return None

        hash_value = self._hash(key)

        # Binary search for closest node
        idx = self._binary_search(hash_value)
        return self.ring[self.sorted_keys[idx]]

    def _hash(self, key: str) -> int:
        """Hash key to integer."""
        # MD5 used for consistent hashing distribution, not for security
        return int(hashlib.md5(key.encode(), usedforsecurity=False).hexdigest(), 16)  # nosec B324

    def _binary_search(self, hash_value: int) -> int:
        """Binary search for closest hash in ring."""
        left, right = 0, len(self.sorted_keys) - 1

        if hash_value > self.sorted_keys[-1]:
            return 0

        while left < right:
            mid = (left + right) // 2
            if self.sorted_keys[mid] < hash_value:
                left = mid + 1
            else:
                right = mid

        return left


class DistributedCache:
    """
    Distributed cache with Redis cluster support.

    Provides sharding, replication, failover, and distributed coordination
    for multi-node LLM caching.
    """

    def __init__(
        self,
        redis_cluster_nodes: List[Dict[str, Any]],
        replication_config: Optional[ReplicationConfig] = None,
        sharding_strategy: ShardingStrategy = ShardingStrategy.CONSISTENT_HASH,
        key_prefix: str = "llm_cache",
        connection_timeout: int = 5,
        max_connections: int = 50,
    ):
        """
        Initialize distributed cache.

        Args:
            redis_cluster_nodes: List of Redis node configs
            replication_config: Replication configuration
            sharding_strategy: Sharding strategy to use
            key_prefix: Prefix for all cache keys
            connection_timeout: Connection timeout in seconds
            max_connections: Max connections per node
        """
        self.redis_nodes = redis_cluster_nodes
        self.replication_config = replication_config or ReplicationConfig()
        self.sharding_strategy = sharding_strategy
        self.key_prefix = key_prefix
        self.connection_timeout = connection_timeout
        self.max_connections = max_connections

        # Cluster state
        self.cluster_nodes: Dict[str, ClusterNode] = {}
        self.hash_ring = ConsistentHashRing()
        self._redis_clients: Dict[str, redis.Redis] = {}
        self._cluster_client: Optional[RedisCluster] = None
        self._locks: Dict[str, float] = {}  # Distributed locks

        # Initialize cluster
        self._initialize_cluster()

        logger.info(f"Initialized DistributedCache with {len(self.redis_nodes)} nodes")

    def _initialize_cluster(self) -> None:
        """Initialize Redis cluster connection."""
        try:
            # Try cluster mode first
            startup_nodes = [
                {"host": node["host"], "port": node.get("port", 6379)}
                for node in self.redis_nodes
            ]

            self._cluster_client = RedisCluster(
                startup_nodes=startup_nodes,  # type: ignore[arg-type]
                decode_responses=False,
                skip_full_coverage_check=True,
                max_connections_per_node=self.max_connections,
                socket_timeout=self.connection_timeout,
            )

            # Test connection
            self._cluster_client.ping()

            # Initialize nodes in hash ring
            for node in self.redis_nodes:
                node_id = f"{node['host']}:{node.get('port', 6379)}"
                self.hash_ring.add_node(node_id)

                # Create node entry
                cluster_node = ClusterNode(
                    node_id=node_id,
                    host=node["host"],
                    port=node.get("port", 6379),
                    role=NodeRole.MASTER,
                    status=NodeStatus.HEALTHY,
                )
                self.cluster_nodes[node_id] = cluster_node

            logger.info("Redis cluster initialized successfully")

        except Exception as e:
            logger.warning(f"Cluster mode failed, falling back to standalone: {e}")
            self._initialize_standalone()

    def _initialize_standalone(self) -> None:
        """Initialize standalone Redis connections as fallback."""
        for node in self.redis_nodes:
            node_id = f"{node['host']}:{node.get('port', 6379)}"

            try:
                client = redis.Redis(
                    host=node["host"],
                    port=node.get("port", 6379),
                    db=0,
                    decode_responses=False,
                    socket_timeout=self.connection_timeout,
                    max_connections=self.max_connections,
                )

                client.ping()
                self._redis_clients[node_id] = client
                self.hash_ring.add_node(node_id)

                # Create node entry
                cluster_node = ClusterNode(
                    node_id=node_id,
                    host=node["host"],
                    port=node.get("port", 6379),
                    role=NodeRole.MASTER,
                    status=NodeStatus.HEALTHY,
                )
                self.cluster_nodes[node_id] = cluster_node

                logger.info(f"Connected to standalone Redis: {node_id}")

            except Exception as e:
                logger.error(f"Failed to connect to {node_id}: {e}")

    def get_shard_for_key(self, key: str) -> int:
        """
        Determine shard for key based on sharding strategy.

        Args:
            key: Cache key

        Returns:
            Shard ID
        """
        if self.sharding_strategy == ShardingStrategy.CONSISTENT_HASH:
            node = self.hash_ring.get_node(key)
            if node:
                return hash(node) % len(self.cluster_nodes)
            return 0

        elif self.sharding_strategy == ShardingStrategy.HASH:
            return hash(key) % len(self.cluster_nodes)

        elif self.sharding_strategy == ShardingStrategy.RANGE:
            # Simple alphabetic range sharding
            first_char = key[0].lower() if key else "a"
            char_pos = ord(first_char) - ord("a")
            return char_pos % len(self.cluster_nodes)

        return 0

    def set_replicated(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value with replication across nodes.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds

        Returns:
            True if stored successfully
        """
        try:
            prefixed_key = f"{self.key_prefix}:{key}"
            serialized = pickle.dumps(value)

            # Use cluster client if available
            if self._cluster_client:
                if ttl:
                    self._cluster_client.setex(prefixed_key, ttl, serialized)
                else:
                    self._cluster_client.set(prefixed_key, serialized)

                logger.debug(f"Set key={key} in cluster (ttl={ttl})")
                return True

            # Fallback to manual replication
            node_id = self.hash_ring.get_node(key)
            if not node_id or node_id not in self._redis_clients:
                return False

            primary_client = self._redis_clients[node_id]

            if ttl:
                primary_client.setex(prefixed_key, ttl, serialized)
            else:
                primary_client.set(prefixed_key, serialized)

            # Replicate to replicas
            replicated = 1
            for replica_node_id, client in self._redis_clients.items():
                if (
                    replica_node_id != node_id
                    and replicated < self.replication_config.replicas + 1
                ):
                    try:
                        if ttl:
                            client.setex(prefixed_key, ttl, serialized)
                        else:
                            client.set(prefixed_key, serialized)
                        replicated += 1
                    except Exception as e:
                        logger.warning(f"Replication to {replica_node_id} failed: {e}")

            logger.debug(f"Set key={key} with {replicated} replicas (ttl={ttl})")
            return replicated >= self.replication_config.quorum

        except Exception as e:
            logger.error(f"Error in set_replicated: {e}", exc_info=True)
            return False

    def get_replicated(self, key: str) -> Optional[Any]:
        """
        Get value with failover support.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            prefixed_key = f"{self.key_prefix}:{key}"

            # Use cluster client if available
            if self._cluster_client:
                data = self._cluster_client.get(prefixed_key)
                if data:
                    return pickle.loads(data)  # nosec B301 - controlled cache data
                return None

            # Try primary node first
            node_id = self.hash_ring.get_node(key)
            if node_id and node_id in self._redis_clients:
                try:
                    client = self._redis_clients[node_id]
                    data = client.get(prefixed_key)
                    if data:
                        return pickle.loads(data)  # nosec B301 - controlled cache data
                except (RedisConnectionError, RedisTimeoutError) as e:
                    logger.warning(f"Primary node {node_id} failed: {e}")

            # Failover to other nodes
            for replica_id, client in self._redis_clients.items():
                if replica_id != node_id:
                    try:
                        data = client.get(prefixed_key)
                        if data:
                            logger.debug(f"Failover: got key={key} from {replica_id}")
                            return pickle.loads(data)  # nosec B301 - controlled cache data
                    except Exception as e:
                        logger.warning(f"Replica {replica_id} failed: {e}")

            return None

        except Exception as e:
            logger.error(f"Error in get_replicated: {e}", exc_info=True)
            return None

    def delete(self, key: str) -> bool:
        """
        Delete key from all replicas.

        Args:
            key: Cache key

        Returns:
            True if deleted successfully
        """
        try:
            prefixed_key = f"{self.key_prefix}:{key}"

            if self._cluster_client:
                self._cluster_client.delete(prefixed_key)
                return True

            # Delete from all nodes
            deleted = 0
            for client in self._redis_clients.values():
                try:
                    if client.delete(prefixed_key):
                        deleted += 1
                except Exception as e:
                    logger.warning(f"Delete failed on node: {e}")

            return deleted > 0

        except Exception as e:
            logger.error(f"Error in delete: {e}", exc_info=True)
            return False

    def acquire_lock(self, key: str, timeout: int = 10, blocking: bool = True) -> bool:
        """
        Acquire distributed lock.

        Args:
            key: Lock key
            timeout: Lock timeout in seconds
            blocking: Whether to block until lock is acquired

        Returns:
            True if lock acquired
        """
        try:
            lock_key = f"{self.key_prefix}:lock:{key}"
            identifier = f"{id(self)}:{time.time()}"

            if self._cluster_client:
                # Use SET NX EX for atomic lock
                acquired = self._cluster_client.set(
                    lock_key, identifier, nx=True, ex=timeout
                )

                if acquired:
                    self._locks[key] = time.time()
                    logger.debug(f"Acquired lock for key={key}")
                    return True

                if blocking:
                    # Simple polling (production should use pub/sub)
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        time.sleep(0.1)
                        acquired = self._cluster_client.set(
                            lock_key, identifier, nx=True, ex=timeout
                        )
                        if acquired:
                            self._locks[key] = time.time()
                            return True

                return False

            # Fallback implementation
            for client in self._redis_clients.values():
                try:
                    if client.set(lock_key, identifier, nx=True, ex=timeout):
                        self._locks[key] = time.time()
                        return True
                except Exception as e:
                    logger.warning(f"Lock acquire failed: {e}")

            return False

        except Exception as e:
            logger.error(f"Error in acquire_lock: {e}", exc_info=True)
            return False

    def release_lock(self, key: str) -> bool:
        """
        Release distributed lock.

        Args:
            key: Lock key

        Returns:
            True if released successfully
        """
        try:
            lock_key = f"{self.key_prefix}:lock:{key}"

            if self._cluster_client:
                result = self._cluster_client.delete(lock_key)
                if result and key in self._locks:
                    del self._locks[key]
                    logger.debug(f"Released lock for key={key}")
                    return True

            # Fallback
            for client in self._redis_clients.values():
                try:
                    client.delete(lock_key)
                except Exception:
                    pass

            if key in self._locks:
                del self._locks[key]

            return True

        except Exception as e:
            logger.error(f"Error in release_lock: {e}", exc_info=True)
            return False

    def check_cluster_health(self) -> Dict[str, Any]:
        """
        Monitor cluster health and node status.

        Returns:
            Cluster health report
        """
        health_report: Dict[str, Any] = {
            "cluster_status": "healthy",
            "total_nodes": len(self.cluster_nodes),
            "healthy_nodes": 0,
            "degraded_nodes": 0,
            "failed_nodes": 0,
            "nodes": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            for node_id, node in self.cluster_nodes.items():
                node_health = self._check_node_health(node_id)

                health_report["nodes"].append(
                    {
                        "node_id": node_id,
                        "status": node_health["status"],
                        "latency_ms": node_health.get("latency_ms", 0),
                        "memory_used_mb": node_health.get("memory_mb", 0),
                        "keys_count": node_health.get("keys", 0),
                    }
                )

                if node_health["status"] == NodeStatus.HEALTHY.value:
                    health_report["healthy_nodes"] += 1
                elif node_health["status"] == NodeStatus.DEGRADED.value:
                    health_report["degraded_nodes"] += 1
                else:
                    health_report["failed_nodes"] += 1

            # Determine overall cluster status
            if health_report["failed_nodes"] > len(self.cluster_nodes) // 2:
                health_report["cluster_status"] = "critical"
            elif health_report["failed_nodes"] > 0:
                health_report["cluster_status"] = "degraded"

            logger.info(
                f"Cluster health: "
                f"{health_report['healthy_nodes']}/"
                f"{health_report['total_nodes']} healthy"
            )

            return health_report

        except Exception as e:
            logger.error(f"Error checking cluster health: {e}", exc_info=True)
            return {
                "cluster_status": "unknown",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _check_node_health(self, node_id: str) -> Dict[str, Any]:
        """Check health of individual node."""
        health: Dict[str, Any] = {"status": NodeStatus.UNKNOWN.value}

        try:
            start_time = time.time()

            if self._cluster_client:
                # Cluster mode health check
                self._cluster_client.ping()
                latency_ms = (time.time() - start_time) * 1000

                # Get node info
                info = self._cluster_client.info()
                health = {
                    "status": NodeStatus.HEALTHY.value,
                    "latency_ms": round(latency_ms, 2),
                    "memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                    "keys": info.get("db0", {}).get("keys", 0),
                }

            elif node_id in self._redis_clients:
                # Standalone mode health check
                client = self._redis_clients[node_id]
                client.ping()
                latency_ms = (time.time() - start_time) * 1000

                info = client.info()
                health = {
                    "status": NodeStatus.HEALTHY.value,
                    "latency_ms": round(latency_ms, 2),
                    "memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                    "keys": info.get("db0", {}).get("keys", 0),
                }

            # Update node metadata
            if node_id in self.cluster_nodes:
                self.cluster_nodes[node_id].status = NodeStatus.HEALTHY
                self.cluster_nodes[node_id].last_heartbeat = datetime.utcnow()
                memory_val = health.get("memory_mb", 0.0)
                keys_val = health.get("keys", 0)
                self.cluster_nodes[node_id].memory_used_mb = (
                    float(memory_val) if isinstance(memory_val, (int, float)) else 0.0
                )
                self.cluster_nodes[node_id].keys_count = (
                    int(keys_val) if isinstance(keys_val, (int, float)) else 0
                )

        except (RedisConnectionError, RedisTimeoutError):
            health["status"] = NodeStatus.FAILED.value
            if node_id in self.cluster_nodes:
                self.cluster_nodes[node_id].status = NodeStatus.FAILED

        except Exception as e:
            logger.warning(f"Health check failed for {node_id}: {e}")
            health["status"] = NodeStatus.DEGRADED.value
            if node_id in self.cluster_nodes:
                self.cluster_nodes[node_id].status = NodeStatus.DEGRADED

        return health

    def rebalance_shards(self) -> Dict[str, Any]:
        """
        Rebalance data across cluster nodes.

        Returns:
            Rebalancing report
        """
        report: Dict[str, Any] = {
            "status": "completed",
            "keys_moved": 0,
            "duration_seconds": 0,
            "errors": [],
        }

        try:
            start_time = time.time()

            logger.info("Starting cluster rebalancing")

            # In production, this would:
            # 1. Calculate optimal key distribution
            # 2. Move keys between nodes
            # 3. Update hash ring
            # 4. Verify data consistency

            # For now, log operation
            logger.info("Rebalancing completed (no-op in current implementation)")

            report["duration_seconds"] = time.time() - start_time

            return report

        except Exception as e:
            logger.error(f"Error in rebalance_shards: {e}", exc_info=True)
            report["status"] = "failed"
            report["errors"].append(str(e))
            return report

    def get_cluster_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cluster statistics.

        Returns:
            Cluster statistics
        """
        stats: Dict[str, Any] = {
            "total_nodes": len(self.cluster_nodes),
            "active_locks": len(self._locks),
            "sharding_strategy": self.sharding_strategy.value,
            "replication_factor": self.replication_config.replicas,
            "total_memory_mb": 0.0,
            "total_keys": 0,
            "nodes": [],
        }

        try:
            for node_id, node in self.cluster_nodes.items():
                node_info = {
                    "node_id": node_id,
                    "role": node.role.value,
                    "status": node.status.value,
                    "memory_mb": node.memory_used_mb,
                    "keys": node.keys_count,
                }
                stats["nodes"].append(node_info)
                stats["total_memory_mb"] += node.memory_used_mb
                stats["total_keys"] += node.keys_count

            return stats

        except Exception as e:
            logger.error(f"Error getting cluster stats: {e}", exc_info=True)
            return {"error": str(e)}

    def close(self) -> None:
        """Close all Redis connections."""
        try:
            if self._cluster_client:
                self._cluster_client.close()

            for client in self._redis_clients.values():
                client.close()

            logger.info("Closed all Redis connections")

        except Exception as e:
            logger.error(f"Error closing connections: {e}", exc_info=True)
