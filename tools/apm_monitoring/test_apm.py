"""
Comprehensive Test Suite for APM & Monitoring Platform.

This module provides unit tests for all APM components with mocked external
services (Prometheus, Grafana, AlertManager).

Test Coverage:
- PrometheusWrapper
- HealthChecker
- AlertManager
- SLOTracker
- GrafanaDashboard
- MetricsCollector
"""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, mock_open

import pytest
import requests

from issue_35_alert_manager import (
    Alert,
    AlertManager,
    AlertRule,
    AlertSeverity,
    AlertState,
)
from issue_35_grafana_dashboard import GrafanaDashboard, PanelConfig
from issue_35_health_checker import (
    HealthCheckConfig,
    HealthChecker,
    HealthStatus,
)
from issue_35_metrics_collector import MetricsCollector
from issue_35_prometheus_wrapper import (
    PrometheusError,
    PrometheusWrapper,
)
from issue_35_slo_tracker import (
    SLODefinition,
    SLOTracker,
    SLOType,
    WindowType,
)


class TestPrometheusWrapper:
    """Tests for PrometheusWrapper."""

    @pytest.fixture
    def mock_response(self):
        """Create mock response."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"__name__": "up", "instance": "localhost:9090"},
                        "value": [1234567890, "1"],
                    }
                ],
            },
        }
        return response

    @pytest.fixture
    def prometheus(self):
        """Create PrometheusWrapper instance."""
        return PrometheusWrapper(base_url="http://localhost:9090")

    def test_init(self, prometheus):
        """Test initialization."""
        assert prometheus.base_url == "http://localhost:9090"
        assert prometheus.timeout == 30

    @patch("requests.Session.request")
    def test_query_success(self, mock_request, prometheus, mock_response):
        """Test successful query."""
        mock_request.return_value = mock_response

        result = prometheus.query("up")

        assert result["status"] == "success"
        assert "data" in result
        mock_request.assert_called_once()

    @patch("requests.Session.request")
    def test_query_error(self, mock_request, prometheus):
        """Test query with error response."""
        error_response = Mock()
        error_response.status_code = 200
        error_response.json.return_value = {
            "status": "error",
            "error": "invalid query",
        }
        mock_request.return_value = error_response

        with pytest.raises(PrometheusError):
            prometheus.query("invalid{}")

    @patch("requests.Session.request")
    def test_query_range(self, mock_request, prometheus, mock_response):
        """Test range query."""
        mock_request.return_value = mock_response

        start = datetime.utcnow() - timedelta(hours=1)
        end = datetime.utcnow()

        result = prometheus.query_range("up", start=start, end=end, step="1m")

        assert result["status"] == "success"
        mock_request.assert_called_once()

    @patch("requests.Session.request")
    def test_check_health(self, mock_request, prometheus):
        """Test health check."""
        health_response = Mock()
        health_response.status_code = 200
        health_response.json.return_value = {}
        mock_request.return_value = health_response

        assert prometheus.check_health() is True

    @patch("requests.Session.request")
    def test_get_labels(self, mock_request, prometheus):
        """Test get labels."""
        labels_response = Mock()
        labels_response.status_code = 200
        labels_response.json.return_value = {
            "status": "success",
            "data": ["__name__", "instance", "job"],
        }
        mock_request.return_value = labels_response

        labels = prometheus.get_labels()

        assert len(labels) == 3
        assert "__name__" in labels


class TestHealthChecker:
    """Tests for HealthChecker."""

    @pytest.fixture
    def health_checker(self):
        """Create HealthChecker instance."""
        return HealthChecker(check_interval=30)

    @pytest.fixture
    def endpoint_config(self):
        """Create endpoint configuration."""
        return HealthCheckConfig(
            url="http://localhost:8080/health",
            name="test_service",
            timeout_seconds=5,
        )

    def test_init(self, health_checker):
        """Test initialization."""
        assert health_checker.check_interval == 30
        assert len(health_checker.endpoints) == 0

    def test_add_endpoint(self, health_checker, endpoint_config):
        """Test adding endpoint."""
        health_checker.add_endpoint(endpoint_config)

        assert "test_service" in health_checker.endpoints
        assert health_checker.endpoints["test_service"].url == endpoint_config.url

    @patch("requests.Session.request")
    def test_check_endpoint_healthy(self, mock_request, health_checker, endpoint_config):
        """Test checking healthy endpoint."""
        health_checker.add_endpoint(endpoint_config)

        response = Mock()
        response.status_code = 200
        mock_request.return_value = response

        result = health_checker.check_endpoint("test_service")

        assert result.status == HealthStatus.HEALTHY
        assert result.status_code == 200
        assert result.response_time_ms is not None

    @patch("requests.Session.request")
    def test_check_endpoint_unhealthy(self, mock_request, health_checker, endpoint_config):
        """Test checking unhealthy endpoint."""
        health_checker.add_endpoint(endpoint_config)

        response = Mock()
        response.status_code = 500
        mock_request.return_value = response

        result = health_checker.check_endpoint("test_service")

        assert result.status == HealthStatus.UNHEALTHY
        assert result.status_code == 500

    @patch("requests.Session.request")
    def test_check_endpoint_timeout(self, mock_request, health_checker, endpoint_config):
        """Test endpoint timeout."""
        health_checker.add_endpoint(endpoint_config)

        mock_request.side_effect = requests.exceptions.Timeout()

        result = health_checker.check_endpoint("test_service")

        assert result.status == HealthStatus.UNHEALTHY
        assert "Timeout" in result.error_message

    def test_get_availability(self, health_checker, endpoint_config):
        """Test availability calculation."""
        health_checker.add_endpoint(endpoint_config)

        # Manually add some history
        from issue_35_health_checker import HealthCheckResult

        for i in range(10):
            status = HealthStatus.HEALTHY if i < 9 else HealthStatus.UNHEALTHY
            result = HealthCheckResult(
                endpoint="test_service",
                status=status,
                response_time_ms=100,
            )
            health_checker.history["test_service"].append(result)

        availability = health_checker.get_availability("test_service")

        assert availability == 90.0


class TestAlertManager:
    """Tests for AlertManager."""

    @pytest.fixture
    def alert_manager(self):
        """Create AlertManager instance."""
        return AlertManager(
            prometheus_url="http://localhost:9090",
            alertmanager_url="http://localhost:9093",
        )

    @pytest.fixture
    def alert_rule(self):
        """Create alert rule."""
        return AlertRule(
            name="HighErrorRate",
            query='rate(http_errors_total[5m]) > 0.1',
            duration="5m",
            severity=AlertSeverity.CRITICAL,
            threshold=0.1,
            comparison=">",
        )

    def test_init(self, alert_manager):
        """Test initialization."""
        assert alert_manager.prometheus_url == "http://localhost:9090"
        assert len(alert_manager.rules) == 0

    def test_add_rule(self, alert_manager, alert_rule):
        """Test adding alert rule."""
        alert_manager.add_rule(alert_rule)

        assert "HighErrorRate" in alert_manager.rules
        assert alert_manager.rules["HighErrorRate"].threshold == 0.1

    def test_evaluate_condition(self, alert_manager):
        """Test condition evaluation."""
        assert alert_manager._evaluate_condition(10, ">", 5) is True
        assert alert_manager._evaluate_condition(3, ">", 5) is False
        assert alert_manager._evaluate_condition(5, ">=", 5) is True
        assert alert_manager._evaluate_condition(5, "==", 5) is True

    @patch("requests.Session.post")
    def test_fire_alert(self, mock_post, alert_manager):
        """Test firing alert."""
        mock_post.return_value = Mock(status_code=200)

        alert = Alert(
            name="TestAlert",
            state=AlertState.FIRING,
            value=0.5,
            fired_at=datetime.utcnow(),
        )

        result = alert_manager.fire_alert(alert)

        assert result is True
        mock_post.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data="""
groups:
  - name: example
    rules:
      - alert: HighErrorRate
        expr: rate(errors[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate
""")
    def test_load_rules_from_file(self, mock_file, alert_manager):
        """Test loading rules from YAML file."""
        alert_manager.load_rules_from_file("test.yaml")

        assert "HighErrorRate" in alert_manager.rules
        assert alert_manager.rules["HighErrorRate"].severity == AlertSeverity.CRITICAL


class TestSLOTracker:
    """Tests for SLOTracker."""

    @pytest.fixture
    def slo_tracker(self):
        """Create SLOTracker instance."""
        return SLOTracker()

    @pytest.fixture
    def availability_slo(self):
        """Create availability SLO."""
        return SLODefinition(
            name="api_availability",
            slo_type=SLOType.AVAILABILITY,
            target=99.9,
            window_days=30,
            service="api",
        )

    @pytest.fixture
    def latency_slo(self):
        """Create latency SLO."""
        return SLODefinition(
            name="api_latency",
            slo_type=SLOType.LATENCY,
            target=95.0,
            window_days=30,
            service="api",
            latency_threshold_ms=100,
        )

    def test_init(self, slo_tracker):
        """Test initialization."""
        assert len(slo_tracker.slos) == 0

    def test_add_slo(self, slo_tracker, availability_slo):
        """Test adding SLO."""
        slo_tracker.add_slo(availability_slo)

        assert "api_availability" in slo_tracker.slos
        assert slo_tracker.slos["api_availability"].target == 99.9

    def test_slo_validation(self, slo_tracker):
        """Test SLO validation."""
        invalid_slo = SLODefinition(
            name="invalid",
            slo_type=SLOType.AVAILABILITY,
            target=150.0,  # Invalid target
            window_days=30,
        )

        with pytest.raises(ValueError):
            slo_tracker.add_slo(invalid_slo)

    def test_calculate_error_budget(self, slo_tracker):
        """Test error budget calculation."""
        # Target 99.9%, actual 99.95% -> high remaining budget
        budget = slo_tracker._calculate_error_budget(
            target=99.9,
            actual=99.95,
            window_days=30,
        )

        assert budget >= 50.0  # More than half budget remaining

        # Target 99.9%, actual 99.0% -> low remaining budget
        budget = slo_tracker._calculate_error_budget(
            target=99.9,
            actual=99.0,
            window_days=30,
        )

        assert budget < 0.0  # Budget exceeded


class TestGrafanaDashboard:
    """Tests for GrafanaDashboard."""

    @pytest.fixture
    def grafana(self):
        """Create GrafanaDashboard instance."""
        return GrafanaDashboard(
            base_url="http://localhost:3000",
            username="admin",
            password="admin",
        )

    @pytest.fixture
    def panel_config(self):
        """Create panel configuration."""
        return PanelConfig(
            title="Request Rate",
            panel_type="graph",
            targets=[
                {
                    "expr": "rate(http_requests_total[5m])",
                    "refId": "A",
                }
            ],
        )

    def test_init(self, grafana):
        """Test initialization."""
        assert grafana.base_url == "http://localhost:3000"

    def test_panel_to_json(self, panel_config):
        """Test panel JSON conversion."""
        panel_json = panel_config.to_json(panel_id=1)

        assert panel_json["id"] == 1
        assert panel_json["title"] == "Request Rate"
        assert panel_json["type"] == "graph"
        assert len(panel_json["targets"]) == 1

    @patch("requests.Session.request")
    def test_create_dashboard(self, mock_request, grafana, panel_config):
        """Test dashboard creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "uid": "test-dashboard",
            "url": "/d/test-dashboard",
        }
        mock_request.return_value = mock_response

        result = grafana.create_dashboard(
            title="Test Dashboard",
            panels=[panel_config],
        )

        assert result["uid"] == "test-dashboard"
        mock_request.assert_called_once()

    @patch("requests.Session.request")
    def test_get_dashboards(self, mock_request, grafana):
        """Test listing dashboards."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"uid": "dash1", "title": "Dashboard 1"},
            {"uid": "dash2", "title": "Dashboard 2"},
        ]
        mock_request.return_value = mock_response

        dashboards = grafana.list_dashboards()

        assert len(dashboards) == 2
        assert dashboards[0]["title"] == "Dashboard 1"


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    @pytest.fixture
    def collector(self):
        """Create MetricsCollector instance."""
        from prometheus_client import CollectorRegistry

        registry = CollectorRegistry()
        return MetricsCollector(namespace="test", registry=registry)

    def test_init(self, collector):
        """Test initialization."""
        assert collector.namespace == "test"
        assert len(collector.counters) > 0  # Default metrics

    def test_register_counter(self, collector):
        """Test counter registration."""
        counter = collector.register_counter(
            name="requests_total",
            description="Total requests",
            labels=["method", "endpoint"],
        )

        assert "test_requests_total" in collector.counters
        assert counter is not None

    def test_register_gauge(self, collector):
        """Test gauge registration."""
        gauge = collector.register_gauge(
            name="temperature",
            description="Current temperature",
        )

        assert "test_temperature" in collector.gauges
        assert gauge is not None

    def test_register_histogram(self, collector):
        """Test histogram registration."""
        histogram = collector.register_histogram(
            name="request_duration",
            description="Request duration",
            buckets=[0.1, 0.5, 1.0, 5.0],
        )

        assert "test_request_duration" in collector.histograms
        assert histogram is not None

    def test_inc_counter(self, collector):
        """Test incrementing counter."""
        collector.register_counter("test_counter", "Test counter")
        collector.inc_counter("test_counter", value=5.0)

        # Counter should have been incremented
        counter = collector.counters["test_test_counter"]
        assert counter._value._value >= 5.0

    def test_set_gauge(self, collector):
        """Test setting gauge."""
        collector.register_gauge("test_gauge", "Test gauge")
        collector.set_gauge("test_gauge", value=42.0)

        # Gauge should be set to 42
        gauge = collector.gauges["test_test_gauge"]
        assert gauge._value._value == 42.0

    def test_timer_context_manager(self, collector):
        """Test timer context manager."""
        collector.register_histogram("test_duration", "Test duration")

        with collector.timer(histogram_name="test_duration"):
            time.sleep(0.01)  # Sleep for 10ms

        # Histogram should have recorded a value
        histogram = collector.histograms["test_test_duration"]
        assert histogram._sum._value > 0

    def test_measure_time_decorator(self, collector):
        """Test measure_time decorator."""
        collector.register_histogram("function_duration_seconds", "Function duration")

        @collector.measure_time()
        def slow_function():
            time.sleep(0.01)
            return "done"

        result = slow_function()

        assert result == "done"
        # Should have recorded timing

    def test_count_calls_decorator(self, collector):
        """Test count_calls decorator."""
        collector.register_counter("function_calls_total", "Function calls", labels=["function"])

        @collector.count_calls()
        def my_function():
            return "done"

        my_function()
        my_function()

        # Should have counted 2 calls

    def test_export_metrics(self, collector):
        """Test metrics export."""
        collector.register_counter("test_metric", "Test metric")
        collector.inc_counter("test_metric", value=1.0)

        metrics = collector.export_metrics()

        assert isinstance(metrics, bytes)
        assert b"test_test_metric" in metrics

    def test_get_metrics_summary(self, collector):
        """Test metrics summary."""
        summary = collector.get_metrics_summary()

        assert "counters" in summary
        assert "gauges" in summary
        assert "histograms" in summary
        assert summary["total"] > 0


class TestIntegration:
    """Integration tests for APM components."""

    def test_full_workflow(self):
        """Test full APM workflow."""
        # This would require running services, so we'll keep it simple
        # In practice, this would be an end-to-end test

        # 1. Initialize components
        collector = MetricsCollector(namespace="integration_test")

        # 2. Collect some metrics
        collector.inc_counter("http_requests_total", labels={"method": "GET", "endpoint": "/api", "status_code": "200"})

        # 3. Export metrics
        metrics = collector.export_metrics()
        assert len(metrics) > 0

        # 4. Verify metrics format
        metrics_str = metrics.decode("utf-8")
        assert "integration_test" in metrics_str


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=term-missing"])
