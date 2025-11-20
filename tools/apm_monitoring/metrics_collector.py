"""
Custom Metrics Collection for APM & Monitoring Platform.

This module provides comprehensive custom metrics collection capabilities,
including metric definitions, collection decorators, context managers for
timing, and metric export endpoints.

Supports:
- Counter, Gauge, Histogram, and Summary metrics
- Decorators for automatic instrumentation
- Context managers for timing operations
- Metric export in Prometheus format
- Custom metric registration and management
"""

import functools
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
)

logger = logging.getLogger(__name__)


@dataclass
class MetricDefinition:
    """Definition of a custom metric."""

    name: str
    metric_type: str  # counter, gauge, histogram, summary
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    namespace: str = "apm"
    subsystem: str = ""


class MetricsCollector:
    """
    Custom metrics collector with automatic instrumentation.

    Provides decorators, context managers, and helpers for collecting
    application metrics in Prometheus format.
    """

    def __init__(
        self,
        namespace: str = "apm",
        registry=None,
    ):
        """
        Initialize metrics collector.

        Args:
            namespace: Metric namespace prefix
            registry: Prometheus registry (uses default if None)
        """
        self.namespace = namespace
        self.registry = registry or REGISTRY

        # Metric instances
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.summaries: Dict[str, Summary] = {}

        # Initialize default metrics
        self._init_default_metrics()

        logger.info(f"Initialized MetricsCollector with namespace={namespace}")

    def _init_default_metrics(self):
        """Initialize default APM metrics."""
        # Request counter
        self.register_counter(
            name="http_requests_total",
            description="Total HTTP requests",
            labels=["method", "endpoint", "status_code"],
        )

        # Request duration histogram
        self.register_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration in seconds",
            labels=["method", "endpoint"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        # In-flight requests gauge
        self.register_gauge(
            name="http_requests_in_flight",
            description="Current number of HTTP requests being processed",
            labels=["method", "endpoint"],
        )

        # Error counter
        self.register_counter(
            name="errors_total",
            description="Total errors",
            labels=["error_type", "severity"],
        )

        logger.info("Default APM metrics initialized")

    def register_counter(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        subsystem: str = "",
    ) -> Counter:
        """
        Register a counter metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names
            subsystem: Metric subsystem

        Returns:
            Counter instance
        """
        full_name = self._build_metric_name(name, subsystem)

        if full_name in self.counters:
            logger.warning(f"Counter already registered: {full_name}")
            return self.counters[full_name]

        counter = Counter(
            name=full_name,
            documentation=description,
            labelnames=labels or [],
            registry=self.registry,
        )

        self.counters[full_name] = counter
        logger.debug(f"Registered counter: {full_name}")

        return counter

    def register_gauge(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        subsystem: str = "",
    ) -> Gauge:
        """
        Register a gauge metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names
            subsystem: Metric subsystem

        Returns:
            Gauge instance
        """
        full_name = self._build_metric_name(name, subsystem)

        if full_name in self.gauges:
            logger.warning(f"Gauge already registered: {full_name}")
            return self.gauges[full_name]

        gauge = Gauge(
            name=full_name,
            documentation=description,
            labelnames=labels or [],
            registry=self.registry,
        )

        self.gauges[full_name] = gauge
        logger.debug(f"Registered gauge: {full_name}")

        return gauge

    def register_histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
        subsystem: str = "",
    ) -> Histogram:
        """
        Register a histogram metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names
            buckets: Histogram buckets
            subsystem: Metric subsystem

        Returns:
            Histogram instance
        """
        full_name = self._build_metric_name(name, subsystem)

        if full_name in self.histograms:
            logger.warning(f"Histogram already registered: {full_name}")
            return self.histograms[full_name]

        histogram = Histogram(
            name=full_name,
            documentation=description,
            labelnames=labels or [],
            buckets=buckets or Histogram.DEFAULT_BUCKETS,
            registry=self.registry,
        )

        self.histograms[full_name] = histogram
        logger.debug(f"Registered histogram: {full_name}")

        return histogram

    def register_summary(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        subsystem: str = "",
    ) -> Summary:
        """
        Register a summary metric.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names
            subsystem: Metric subsystem

        Returns:
            Summary instance
        """
        full_name = self._build_metric_name(name, subsystem)

        if full_name in self.summaries:
            logger.warning(f"Summary already registered: {full_name}")
            return self.summaries[full_name]

        summary = Summary(
            name=full_name,
            documentation=description,
            labelnames=labels or [],
            registry=self.registry,
        )

        self.summaries[full_name] = summary
        logger.debug(f"Registered summary: {full_name}")

        return summary

    def _build_metric_name(self, name: str, subsystem: str = "") -> str:
        """Build full metric name with namespace and subsystem."""
        parts = [self.namespace]
        if subsystem:
            parts.append(subsystem)
        parts.append(name)
        return "_".join(parts)

    def inc_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Increment counter metric.

        Args:
            name: Counter name (without namespace)
            value: Increment value
            labels: Label values
        """
        full_name = self._build_metric_name(name)

        if full_name not in self.counters:
            logger.warning(f"Counter not found: {full_name}")
            return

        counter = self.counters[full_name]

        if labels:
            counter.labels(**labels).inc(value)
        else:
            counter.inc(value)

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Set gauge metric value.

        Args:
            name: Gauge name (without namespace)
            value: Gauge value
            labels: Label values
        """
        full_name = self._build_metric_name(name)

        if full_name not in self.gauges:
            logger.warning(f"Gauge not found: {full_name}")
            return

        gauge = self.gauges[full_name]

        if labels:
            gauge.labels(**labels).set(value)
        else:
            gauge.set(value)

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Observe value in histogram.

        Args:
            name: Histogram name (without namespace)
            value: Observed value
            labels: Label values
        """
        full_name = self._build_metric_name(name)

        if full_name not in self.histograms:
            logger.warning(f"Histogram not found: {full_name}")
            return

        histogram = self.histograms[full_name]

        if labels:
            histogram.labels(**labels).observe(value)
        else:
            histogram.observe(value)

    @contextmanager
    def timer(
        self,
        histogram_name: str = "http_request_duration_seconds",
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Context manager for timing operations.

        Args:
            histogram_name: Histogram to record duration
            labels: Label values

        Example:
            with collector.timer(labels={"endpoint": "/api/users"}):
                # Do work
                pass
        """
        start_time = time.time()

        try:
            yield
        finally:
            duration = time.time() - start_time
            self.observe_histogram(histogram_name, duration, labels=labels)

    def track_in_flight(
        self,
        gauge_name: str = "http_requests_in_flight",
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Decorator to track in-flight operations.

        Args:
            gauge_name: Gauge to track in-flight count
            labels: Label values

        Example:
            @collector.track_in_flight(labels={"endpoint": "/api"})
            def my_function():
                pass
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                full_name = self._build_metric_name(gauge_name)

                if full_name in self.gauges:
                    gauge = self.gauges[full_name]
                    if labels:
                        gauge.labels(**labels).inc()
                    else:
                        gauge.inc()

                try:
                    return func(*args, **kwargs)
                finally:
                    if full_name in self.gauges:
                        gauge = self.gauges[full_name]
                        if labels:
                            gauge.labels(**labels).dec()
                        else:
                            gauge.dec()

            return wrapper

        return decorator

    def count_calls(
        self,
        counter_name: str = "function_calls_total",
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Decorator to count function calls.

        Args:
            counter_name: Counter to increment
            labels: Label values

        Example:
            @collector.count_calls(labels={"function": "process_data"})
            def process_data():
                pass
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Add function name to labels
                func_labels = labels.copy() if labels else {}
                if "function" not in func_labels:
                    func_labels["function"] = func.__name__

                self.inc_counter(counter_name, labels=func_labels)

                return func(*args, **kwargs)

            return wrapper

        return decorator

    def measure_time(
        self,
        histogram_name: str = "function_duration_seconds",
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Decorator to measure function execution time.

        Args:
            histogram_name: Histogram to record duration
            labels: Label values

        Example:
            @collector.measure_time(labels={"function": "slow_operation"})
            def slow_operation():
                time.sleep(1)
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.time() - start_time

                    # Add function name to labels
                    func_labels = labels.copy() if labels else {}
                    if "function" not in func_labels:
                        func_labels["function"] = func.__name__

                    self.observe_histogram(histogram_name, duration, labels=func_labels)

            return wrapper

        return decorator

    def count_exceptions(
        self,
        counter_name: str = "errors_total",
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Decorator to count exceptions.

        Args:
            counter_name: Counter to increment on exception
            labels: Label values

        Example:
            @collector.count_exceptions(labels={"severity": "error"})
            def risky_operation():
                raise ValueError("Error")
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Add error info to labels
                    error_labels = labels.copy() if labels else {}
                    error_labels["error_type"] = type(e).__name__

                    self.inc_counter(counter_name, labels=error_labels)

                    raise

            return wrapper

        return decorator

    def export_metrics(self) -> bytes:
        """
        Export all metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest(self.registry)

    def get_metric_families(self) -> List[Any]:
        """
        Get all metric families.

        Returns:
            List of metric families
        """
        return list(self.registry.collect())

    def get_metrics_summary(self) -> Dict[str, int]:
        """
        Get summary of registered metrics.

        Returns:
            Dictionary with metric counts by type
        """
        return {
            "counters": len(self.counters),
            "gauges": len(self.gauges),
            "histograms": len(self.histograms),
            "summaries": len(self.summaries),
            "total": (
                len(self.counters)
                + len(self.gauges)
                + len(self.histograms)
                + len(self.summaries)
            ),
        }


# Global metrics collector instance
_default_collector: Optional[MetricsCollector] = None


def get_default_collector() -> MetricsCollector:
    """Get or create default metrics collector."""
    global _default_collector

    if _default_collector is None:
        _default_collector = MetricsCollector()

    return _default_collector


# Convenience decorators using default collector
def timer(labels: Optional[Dict[str, str]] = None):
    """Timer context manager using default collector."""
    return get_default_collector().timer(labels=labels)


def track_in_flight(labels: Optional[Dict[str, str]] = None):
    """Track in-flight decorator using default collector."""
    return get_default_collector().track_in_flight(labels=labels)


def count_calls(labels: Optional[Dict[str, str]] = None):
    """Count calls decorator using default collector."""
    return get_default_collector().count_calls(labels=labels)


def measure_time(labels: Optional[Dict[str, str]] = None):
    """Measure time decorator using default collector."""
    return get_default_collector().measure_time(labels=labels)


def count_exceptions(labels: Optional[Dict[str, str]] = None):
    """Count exceptions decorator using default collector."""
    return get_default_collector().count_exceptions(labels=labels)
