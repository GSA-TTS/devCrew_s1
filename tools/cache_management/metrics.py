"""
Metrics Collection and Monitoring for LLM Cache Platform.

This module provides comprehensive metrics collection, aggregation,
and export capabilities for cache performance monitoring.

Features:
- Real-time cache hit/miss tracking
- Latency percentile calculations (p50, p95, p99)
- Cost savings estimation
- Prometheus metrics export
- Dashboard data generation
- Time-series metrics aggregation
"""

import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

from prometheus_client import (REGISTRY, Counter, Gauge, Histogram, Summary,
                               generate_latest)
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class CacheMetrics(BaseModel):
    """Cache performance metrics."""

    hit_rate: float = Field(default=0.0, description="Cache hit rate (0-1)")
    miss_rate: float = Field(default=0.0, description="Cache miss rate (0-1)")
    exact_hit_rate: float = Field(default=0.0, description="Exact match hit rate")
    fuzzy_hit_rate: float = Field(default=0.0, description="Fuzzy match hit rate")
    latency_p50: float = Field(default=0.0, description="50th percentile latency")
    latency_p95: float = Field(default=0.0, description="95th percentile latency")
    latency_p99: float = Field(default=0.0, description="99th percentile latency")
    avg_latency_ms: float = Field(default=0.0, description="Average latency in ms")
    total_hits: int = Field(default=0, description="Total cache hits")
    total_misses: int = Field(default=0, description="Total cache misses")
    total_requests: int = Field(default=0, description="Total requests")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Metrics timestamp"
    )

    @field_validator("hit_rate", "miss_rate", "exact_hit_rate", "fuzzy_hit_rate")
    @classmethod
    def validate_rate(cls, v: float) -> float:
        """Validate rate is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Rate must be between 0.0 and 1.0")
        return v


class PerformanceMetrics(BaseModel):
    """Performance comparison metrics."""

    avg_latency_cached_ms: float = Field(
        default=0.0, description="Average cached response latency"
    )
    avg_latency_uncached_ms: float = Field(
        default=0.0, description="Average uncached response latency"
    )
    speedup_factor: float = Field(default=1.0, description="Cache speedup factor")
    cost_savings_usd: float = Field(default=0.0, description="Estimated cost savings")
    tokens_saved: int = Field(default=0, description="Tokens saved by caching")
    api_calls_saved: int = Field(default=0, description="API calls saved by caching")
    memory_efficiency: float = Field(default=0.0, description="Memory efficiency score")
    throughput_rps: float = Field(
        default=0.0, description="Throughput in requests per second"
    )

    @field_validator("speedup_factor")
    @classmethod
    def validate_speedup(cls, v: float) -> float:
        """Validate speedup factor is positive."""
        if v < 0:
            raise ValueError("Speedup factor must be positive")
        return v


@dataclass
class LatencyBucket:
    """Latency histogram bucket."""

    min_ms: float
    max_ms: float
    count: int = 0


@dataclass
class TimeSeriesPoint:
    """Single time series data point."""

    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Comprehensive metrics collector for cache monitoring.

    Collects, aggregates, and exports cache performance metrics
    with Prometheus integration and dashboard support.
    """

    def __init__(
        self,
        cache_manager: Optional[Any] = None,
        window_size: int = 1000,
        cost_per_1k_tokens: float = 0.002,
        avg_tokens_per_request: int = 500,
        registry=None,
    ):
        """
        Initialize metrics collector.

        Args:
            cache_manager: Cache manager instance
            window_size: Rolling window size for latency calculations
            cost_per_1k_tokens: Cost per 1000 tokens
            avg_tokens_per_request: Average tokens per request
            registry: Prometheus registry
        """
        self.cache_manager = cache_manager
        self.window_size = window_size
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.avg_tokens_per_request = avg_tokens_per_request
        self.registry = registry or REGISTRY

        # Rolling windows for latency tracking
        self._hit_latencies: Deque[float] = deque(maxlen=window_size)
        self._miss_latencies: Deque[float] = deque(maxlen=window_size)
        self._uncached_latencies: Deque[float] = deque(maxlen=window_size)

        # Counters
        self._total_hits = 0
        self._total_misses = 0
        self._exact_hits = 0
        self._fuzzy_hits = 0
        self._llm_calls = 0

        # Cost tracking
        self._total_cost_llm = 0.0
        self._total_cost_saved = 0.0

        # Time series data
        self._timeseries: Dict[str, List[TimeSeriesPoint]] = defaultdict(list)

        # Request tracking
        self._request_timestamps: Deque[float] = deque(maxlen=1000)

        # Initialize Prometheus metrics
        self._init_prometheus_metrics()

        logger.info("Initialized MetricsCollector with " f"window_size={window_size}")

    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        namespace = "llm_cache"

        # Counters
        self.prom_cache_hits = Counter(
            f"{namespace}_hits_total",
            "Total cache hits",
            ["match_type"],
            registry=self.registry,
        )

        self.prom_cache_misses = Counter(
            f"{namespace}_misses_total",
            "Total cache misses",
            registry=self.registry,
        )

        self.prom_llm_calls = Counter(
            f"{namespace}_llm_calls_total",
            "Total LLM API calls",
            registry=self.registry,
        )

        # Gauges
        self.prom_hit_rate = Gauge(
            f"{namespace}_hit_rate",
            "Current cache hit rate",
            registry=self.registry,
        )

        self.prom_cost_saved = Gauge(
            f"{namespace}_cost_saved_usd",
            "Total cost saved in USD",
            registry=self.registry,
        )

        # Histograms
        self.prom_latency = Histogram(
            f"{namespace}_latency_seconds",
            "Cache operation latency",
            ["operation_type"],
            buckets=[
                0.001,
                0.005,
                0.01,
                0.025,
                0.05,
                0.1,
                0.25,
                0.5,
                1.0,
                2.5,
                5.0,
            ],
            registry=self.registry,
        )

        # Summary for percentiles
        self.prom_latency_summary = Summary(
            f"{namespace}_latency_summary_seconds",
            "Cache latency summary with quantiles",
            ["operation_type"],
            registry=self.registry,
        )

    def record_hit(
        self,
        latency_ms: float,
        match_type: str = "exact",
    ) -> None:
        """
        Record cache hit.

        Args:
            latency_ms: Response latency in milliseconds
            match_type: Type of match (exact/fuzzy)
        """
        try:
            self._total_hits += 1
            self._hit_latencies.append(latency_ms)
            self._request_timestamps.append(time.time())

            if match_type == "exact":
                self._exact_hits += 1
            elif match_type == "fuzzy":
                self._fuzzy_hits += 1

            # Update Prometheus metrics
            self.prom_cache_hits.labels(match_type=match_type).inc()
            self.prom_latency.labels(operation_type="hit").observe(latency_ms / 1000.0)
            self.prom_latency_summary.labels(operation_type="hit").observe(
                latency_ms / 1000.0
            )

            # Calculate cost saved
            cost_saved = self._calculate_cost_per_call()
            self._total_cost_saved += cost_saved
            self.prom_cost_saved.set(self._total_cost_saved)

            # Update hit rate
            self._update_hit_rate()

            # Record time series
            self._record_timeseries("cache_hit", 1.0, {"type": match_type})

            logger.debug(f"Recorded {match_type} hit with latency={latency_ms:.2f}ms")

        except Exception as e:
            logger.error(f"Error recording hit: {e}", exc_info=True)

    def record_miss(self, latency_ms: float) -> None:
        """
        Record cache miss.

        Args:
            latency_ms: Lookup latency in milliseconds
        """
        try:
            self._total_misses += 1
            self._miss_latencies.append(latency_ms)
            self._request_timestamps.append(time.time())

            # Update Prometheus metrics
            self.prom_cache_misses.inc()
            self.prom_latency.labels(operation_type="miss").observe(latency_ms / 1000.0)
            self.prom_latency_summary.labels(operation_type="miss").observe(
                latency_ms / 1000.0
            )

            # Update hit rate
            self._update_hit_rate()

            # Record time series
            self._record_timeseries("cache_miss", 1.0)

            logger.debug(f"Recorded miss with latency={latency_ms:.2f}ms")

        except Exception as e:
            logger.error(f"Error recording miss: {e}", exc_info=True)

    def record_llm_call(
        self, cost_usd: float, latency_ms: float, tokens: Optional[int] = None
    ) -> None:
        """
        Record uncached LLM API call.

        Args:
            cost_usd: Cost of the call in USD
            latency_ms: Call latency in milliseconds
            tokens: Number of tokens used
        """
        try:
            self._llm_calls += 1
            self._total_cost_llm += cost_usd
            self._uncached_latencies.append(latency_ms)

            # Update Prometheus metrics
            self.prom_llm_calls.inc()
            self.prom_latency.labels(operation_type="llm_call").observe(
                latency_ms / 1000.0
            )
            self.prom_latency_summary.labels(operation_type="llm_call").observe(
                latency_ms / 1000.0
            )

            # Record time series
            self._record_timeseries("llm_call", 1.0)
            self._record_timeseries("llm_cost", cost_usd)
            if tokens:
                self._record_timeseries("llm_tokens", float(tokens))

            logger.debug(
                f"Recorded LLM call: cost=${cost_usd:.4f}, "
                f"latency={latency_ms:.2f}ms"
            )

        except Exception as e:
            logger.error(f"Error recording LLM call: {e}", exc_info=True)

    def get_metrics(self) -> CacheMetrics:
        """
        Get current cache metrics.

        Returns:
            Current metrics snapshot
        """
        try:
            total_requests = self._total_hits + self._total_misses
            hit_rate = self._total_hits / total_requests if total_requests > 0 else 0.0
            miss_rate = 1.0 - hit_rate

            exact_hit_rate = (
                self._exact_hits / total_requests if total_requests > 0 else 0.0
            )
            fuzzy_hit_rate = (
                self._fuzzy_hits / total_requests if total_requests > 0 else 0.0
            )

            # Calculate latency percentiles
            all_latencies = list(self._hit_latencies) + list(self._miss_latencies)
            latency_p50 = (
                self._calculate_percentile(all_latencies, 50) if all_latencies else 0.0
            )
            latency_p95 = (
                self._calculate_percentile(all_latencies, 95) if all_latencies else 0.0
            )
            latency_p99 = (
                self._calculate_percentile(all_latencies, 99) if all_latencies else 0.0
            )

            avg_latency = statistics.mean(all_latencies) if all_latencies else 0.0

            metrics = CacheMetrics(
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                exact_hit_rate=exact_hit_rate,
                fuzzy_hit_rate=fuzzy_hit_rate,
                latency_p50=latency_p50,
                latency_p95=latency_p95,
                latency_p99=latency_p99,
                avg_latency_ms=avg_latency,
                total_hits=self._total_hits,
                total_misses=self._total_misses,
                total_requests=total_requests,
                timestamp=datetime.utcnow(),
            )

            return metrics

        except Exception as e:
            logger.error(f"Error getting metrics: {e}", exc_info=True)
            return CacheMetrics()

    def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Get performance comparison metrics.

        Returns:
            Performance metrics
        """
        try:
            # Calculate average latencies
            avg_cached = (
                statistics.mean(self._hit_latencies) if self._hit_latencies else 0.0
            )
            avg_uncached = (
                statistics.mean(self._uncached_latencies)
                if self._uncached_latencies
                else 1000.0
            )

            # Calculate speedup
            speedup = avg_uncached / avg_cached if avg_cached > 0 else 1.0

            # Calculate tokens saved
            tokens_saved = self._total_hits * self.avg_tokens_per_request

            # Calculate throughput
            throughput = self._calculate_throughput()

            # Calculate memory efficiency
            memory_efficiency = self._calculate_memory_efficiency()

            metrics = PerformanceMetrics(
                avg_latency_cached_ms=round(avg_cached, 2),
                avg_latency_uncached_ms=round(avg_uncached, 2),
                speedup_factor=round(speedup, 2),
                cost_savings_usd=round(self._total_cost_saved, 4),
                tokens_saved=tokens_saved,
                api_calls_saved=self._total_hits,
                memory_efficiency=memory_efficiency,
                throughput_rps=throughput,
            )

            return metrics

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}", exc_info=True)
            return PerformanceMetrics()

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics
        """
        try:
            return generate_latest(self.registry).decode("utf-8")

        except Exception as e:
            logger.error(f"Error exporting Prometheus metrics: {e}", exc_info=True)
            return ""

    def calculate_cost_savings(self) -> float:
        """
        Calculate total cost savings from caching.

        Returns:
            Total cost savings in USD
        """
        return round(self._total_cost_saved, 4)

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """
        Generate data for monitoring dashboard.

        Returns:
            Dashboard-ready metrics data
        """
        try:
            cache_metrics = self.get_metrics()
            perf_metrics = self.get_performance_metrics()

            # Calculate time-based aggregations
            hourly_stats = self._aggregate_timeseries(3600)
            daily_stats = self._aggregate_timeseries(86400)

            dashboard = {
                "overview": {
                    "hit_rate": cache_metrics.hit_rate,
                    "total_requests": cache_metrics.total_requests,
                    "cost_savings_usd": perf_metrics.cost_savings_usd,
                    "speedup_factor": perf_metrics.speedup_factor,
                    "throughput_rps": perf_metrics.throughput_rps,
                },
                "latency": {
                    "p50": cache_metrics.latency_p50,
                    "p95": cache_metrics.latency_p95,
                    "p99": cache_metrics.latency_p99,
                    "avg_cached_ms": perf_metrics.avg_latency_cached_ms,
                    "avg_uncached_ms": perf_metrics.avg_latency_uncached_ms,
                },
                "cache_performance": {
                    "exact_hits": self._exact_hits,
                    "fuzzy_hits": self._fuzzy_hits,
                    "misses": self._total_misses,
                    "exact_hit_rate": cache_metrics.exact_hit_rate,
                    "fuzzy_hit_rate": cache_metrics.fuzzy_hit_rate,
                },
                "cost_analysis": {
                    "total_saved_usd": perf_metrics.cost_savings_usd,
                    "tokens_saved": perf_metrics.tokens_saved,
                    "api_calls_saved": perf_metrics.api_calls_saved,
                    "total_llm_cost_usd": round(self._total_cost_llm, 4),
                },
                "trends": {
                    "hourly": hourly_stats,
                    "daily": daily_stats,
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "window_size": self.window_size,
                    "cost_per_1k_tokens": self.cost_per_1k_tokens,
                },
            }

            return dashboard

        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}", exc_info=True)
            return {"error": str(e)}

    def reset_metrics(self) -> bool:
        """
        Reset all collected metrics.

        Returns:
            True if reset successful
        """
        try:
            self._hit_latencies.clear()
            self._miss_latencies.clear()
            self._uncached_latencies.clear()
            self._request_timestamps.clear()

            self._total_hits = 0
            self._total_misses = 0
            self._exact_hits = 0
            self._fuzzy_hits = 0
            self._llm_calls = 0

            self._total_cost_llm = 0.0
            self._total_cost_saved = 0.0

            self._timeseries.clear()

            logger.info("Metrics reset successfully")

            return True

        except Exception as e:
            logger.error(f"Error resetting metrics: {e}", exc_info=True)
            return False

    def get_timeseries(
        self, metric_name: str, duration_seconds: int = 3600
    ) -> List[Dict[str, Any]]:
        """
        Get time series data for a specific metric.

        Args:
            metric_name: Name of metric
            duration_seconds: Time window in seconds

        Returns:
            List of time series points
        """
        try:
            if metric_name not in self._timeseries:
                return []

            cutoff_time = time.time() - duration_seconds
            points = self._timeseries[metric_name]

            filtered_points = [
                {
                    "timestamp": p.timestamp,
                    "value": p.value,
                    "labels": p.labels,
                }
                for p in points
                if p.timestamp >= cutoff_time
            ]

            return filtered_points

        except Exception as e:
            logger.error(f"Error getting timeseries: {e}", exc_info=True)
            return []

    # Private helper methods

    def _calculate_cost_per_call(self) -> float:
        """Calculate cost saved per cached call."""
        tokens = self.avg_tokens_per_request
        return (tokens / 1000.0) * self.cost_per_1k_tokens

    def _update_hit_rate(self) -> None:
        """Update Prometheus hit rate gauge."""
        total = self._total_hits + self._total_misses
        if total > 0:
            hit_rate = self._total_hits / total
            self.prom_hit_rate.set(hit_rate)

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0

        try:
            sorted_values = sorted(values)
            index = int(len(sorted_values) * (percentile / 100.0))
            index = min(index, len(sorted_values) - 1)
            return sorted_values[index]

        except Exception as e:
            logger.error(f"Error calculating percentile: {e}")
            return 0.0

    def _calculate_throughput(self) -> float:
        """Calculate current throughput in requests per second."""
        if len(self._request_timestamps) < 2:
            return 0.0

        try:
            time_window = 60.0  # Last 60 seconds
            cutoff = time.time() - time_window

            recent_requests = sum(1 for ts in self._request_timestamps if ts >= cutoff)

            return round(recent_requests / time_window, 2)

        except Exception as e:
            logger.error(f"Error calculating throughput: {e}")
            return 0.0

    def _calculate_memory_efficiency(self) -> float:
        """Calculate memory efficiency score."""
        if not self.cache_manager:
            return 0.0

        try:
            stats = self.cache_manager.get_stats()

            if stats.memory_usage_mb == 0 or stats.entry_count == 0:
                return 0.0

            # Efficiency = hit_rate * entries / memory_mb
            efficiency = stats.hit_rate * stats.entry_count / stats.memory_usage_mb

            return round(min(efficiency, 1.0), 4)

        except Exception as e:
            logger.error(f"Error calculating memory efficiency: {e}")
            return 0.0

    def _record_timeseries(
        self, metric_name: str, value: float, labels: Optional[Dict] = None
    ) -> None:
        """Record time series data point."""
        try:
            point = TimeSeriesPoint(
                timestamp=time.time(),
                value=value,
                labels=labels or {},
            )

            self._timeseries[metric_name].append(point)

            # Keep only recent data (last 24 hours)
            cutoff = time.time() - 86400
            self._timeseries[metric_name] = [
                p for p in self._timeseries[metric_name] if p.timestamp >= cutoff
            ]

        except Exception as e:
            logger.error(f"Error recording timeseries: {e}")

    def _aggregate_timeseries(self, bucket_seconds: int) -> List[Dict[str, Any]]:
        """Aggregate time series data into buckets."""
        try:
            aggregated = []
            current_time = time.time()

            # Get last 24 hours of data
            for i in range(24):
                bucket_end = current_time - (i * bucket_seconds)
                bucket_start = bucket_end - bucket_seconds

                bucket_data = {
                    "timestamp": bucket_end,
                    "hits": 0,
                    "misses": 0,
                    "avg_latency_ms": 0.0,
                    "cost_saved_usd": 0.0,
                }

                # Count events in this bucket
                if "cache_hit" in self._timeseries:
                    bucket_data["hits"] = sum(
                        1
                        for p in self._timeseries["cache_hit"]
                        if bucket_start <= p.timestamp < bucket_end
                    )

                if "cache_miss" in self._timeseries:
                    bucket_data["misses"] = sum(
                        1
                        for p in self._timeseries["cache_miss"]
                        if bucket_start <= p.timestamp < bucket_end
                    )

                # Calculate average latency
                latencies_in_bucket = [
                    lat
                    for lat, ts in zip(self._hit_latencies, self._request_timestamps)
                    if bucket_start <= ts < bucket_end
                ]

                if latencies_in_bucket:
                    bucket_data["avg_latency_ms"] = round(
                        statistics.mean(latencies_in_bucket), 2
                    )

                # Estimate cost saved in bucket
                bucket_data["cost_saved_usd"] = round(
                    bucket_data["hits"] * self._calculate_cost_per_call(), 4
                )

                aggregated.append(bucket_data)

            return aggregated

        except Exception as e:
            logger.error(f"Error aggregating timeseries: {e}")
            return []

    def export_summary(self) -> Dict[str, Any]:
        """
        Export comprehensive summary of all metrics.

        Returns:
            Complete metrics summary
        """
        return {
            "cache_metrics": self.get_metrics().model_dump(),
            "performance_metrics": self.get_performance_metrics().model_dump(),
            "total_cost_llm_usd": round(self._total_cost_llm, 4),
            "total_llm_calls": self._llm_calls,
        }
