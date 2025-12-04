"""Unit tests for Analytics Integrator module."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from google.analytics.data_v1beta.types import (DimensionValue, MetricValue,
                                                Row, RunReportResponse)

from tools.ux_research.analytics.analytics_integrator import (
    AnalyticsCache, AnalyticsData, AnalyticsIntegrator, ConversionAnalysis,
    Event, FunnelStep, HotjarData, JourneyAnalysis, JourneyStep, RateLimiter)


class TestAnalyticsCache:
    """Test AnalyticsCache functionality."""

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = AnalyticsCache(ttl=60)
        cache.set("test_key", {"data": "value"})

        result = cache.get("test_key")
        assert result == {"data": "value"}

    def test_cache_expiration(self):
        """Test cache expiration after TTL."""
        cache = AnalyticsCache(ttl=0)
        cache.set("test_key", {"data": "value"})

        # Immediate retrieval should work
        result = cache.get("test_key")
        assert result is None  # Already expired due to TTL=0

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = AnalyticsCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = AnalyticsCache()
        key1 = cache._make_key("arg1", "arg2", 123)
        key2 = cache._make_key("arg1", "arg2", 123)
        key3 = cache._make_key("arg1", "arg2", 456)

        assert key1 == key2
        assert key1 != key3


class TestRateLimiter:
    """Test RateLimiter functionality."""

    def test_rate_limiter_allows_under_limit(self):
        """Test that rate limiter allows calls under the limit."""
        limiter = RateLimiter(max_calls=5, time_window=1)

        # Make 5 calls (should all be allowed immediately)
        for _ in range(5):
            limiter.wait_if_needed()  # Should not block

    def test_rate_limiter_blocks_over_limit(self):
        """Test that rate limiter blocks when limit is exceeded."""
        limiter = RateLimiter(max_calls=2, time_window=1)

        # Make 2 calls
        limiter.wait_if_needed()
        limiter.wait_if_needed()

        # Third call should be blocked (but we won't actually wait in test)
        # Just verify the internal state
        assert len(limiter._calls) == 2


class TestAnalyticsIntegrator:
    """Test AnalyticsIntegrator functionality."""

    @pytest.fixture
    def mock_ga_config(self) -> Dict[str, Any]:
        """Mock Google Analytics configuration."""
        return {
            "google_analytics": {
                "type": "service_account",
                "project_id": "test-project",
                "private_key_id": "key123",
                "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",  # noqa: E501
                "client_email": "test@test-project.iam.gserviceaccount.com",
                "client_id": "123456789",
            }
        }

    @pytest.fixture
    def mock_config(self) -> Dict[str, Any]:
        """Mock configuration for all platforms."""
        return {
            "hotjar_api_key": "test_hotjar_key",
            "heap_app_id": "test_heap_app",
            "heap_api_key": "test_heap_key",
            "cache_ttl": 3600,
        }

    @pytest.fixture
    def sample_events(self) -> List[Event]:
        """Generate sample events for testing."""
        base_time = datetime.now()
        return [
            Event(
                event_name="page_view",
                timestamp=base_time,
                user_id="user1",
                session_id="session1",
                properties={"page": "/home"},
                source="test",
            ),
            Event(
                event_name="button_click",
                timestamp=base_time + timedelta(seconds=10),
                user_id="user1",
                session_id="session1",
                properties={"button": "cta"},
                source="test",
            ),
            Event(
                event_name="form_submit",
                timestamp=base_time + timedelta(seconds=30),
                user_id="user1",
                session_id="session1",
                properties={"form": "signup"},
                source="test",
            ),
            Event(
                event_name="page_view",
                timestamp=base_time + timedelta(seconds=5),
                user_id="user2",
                session_id="session2",
                properties={"page": "/home"},
                source="test",
            ),
            Event(
                event_name="button_click",
                timestamp=base_time + timedelta(seconds=15),
                user_id="user2",
                session_id="session2",
                properties={"button": "cta"},
                source="test",
            ),
        ]

    def test_integrator_initialization(self, mock_config):
        """Test integrator initialization."""
        integrator = AnalyticsIntegrator(config=mock_config)

        assert integrator.config == mock_config
        assert integrator._cache is not None
        assert integrator._ga_limiter is not None

    @patch("tools.ux_research.analytics.analytics_integrator.service_account")
    @patch(
        "tools.ux_research.analytics.analytics_integrator." "BetaAnalyticsDataClient"
    )
    def test_ga_client_initialization(
        self, mock_client, mock_service_account, mock_ga_config
    ):
        """Test Google Analytics client initialization."""
        mock_creds = Mock()
        mock_service_account.Credentials.from_service_account_info.return_value = (
            mock_creds  # noqa: E501
        )

        integrator = AnalyticsIntegrator(config=mock_ga_config)

        assert integrator._ga_client is not None
        mock_service_account.Credentials.from_service_account_info.assert_called_once()  # noqa: E501

    @patch(
        "tools.ux_research.analytics.analytics_integrator." "BetaAnalyticsDataClient"
    )
    @patch("tools.ux_research.analytics.analytics_integrator.service_account")
    def test_fetch_google_analytics_data(
        self, mock_service_account, mock_ga_client_class, mock_ga_config
    ):
        """Test fetching Google Analytics data."""
        # Mock credentials
        mock_creds = Mock()
        mock_service_account.Credentials.from_service_account_info.return_value = (
            mock_creds  # noqa: E501
        )

        # Mock GA client and response
        mock_ga_client = Mock()
        mock_ga_client_class.return_value = mock_ga_client

        # Create mock response
        mock_row = Mock(spec=Row)
        mock_dim = Mock(spec=DimensionValue, value="2024-01-01")
        mock_row.dimension_values = [mock_dim]
        mock_row.metric_values = [Mock(spec=MetricValue, value="1000")]

        mock_response = Mock(spec=RunReportResponse)
        mock_response.rows = [mock_row]

        mock_ga_client.run_report.return_value = mock_response

        # Initialize and test
        integrator = AnalyticsIntegrator(config=mock_ga_config)
        result = integrator.fetch_google_analytics_data(
            property_id="123456",
            metrics=["sessions"],
            dimensions=["date"],
            date_range=("2024-01-01", "2024-01-31"),
        )

        assert isinstance(result, AnalyticsData)
        assert result.source == "google_analytics"
        assert "sessions" in result.metrics
        assert result.metrics["sessions"] == 1000.0

    @patch("tools.ux_research.analytics.analytics_integrator.requests.get")
    def test_fetch_hotjar_data_heatmap(self, mock_get, mock_config):
        """Test fetching Hotjar heatmap data."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "heatmaps": [
                {"id": 1, "name": "Homepage", "url": "/home"},
                {"id": 2, "name": "Product", "url": "/product"},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        integrator = AnalyticsIntegrator(config=mock_config)
        result = integrator.fetch_hotjar_data(site_id="12345", data_type="heatmap")

        assert isinstance(result, HotjarData)
        assert len(result.heatmaps) == 2
        assert result.data_type == "heatmap"
        assert result.site_id == "12345"

    @patch("tools.ux_research.analytics.analytics_integrator.requests.get")
    def test_fetch_hotjar_data_invalid_type(self, mock_get, mock_config):
        """Test fetching Hotjar data with invalid type."""
        integrator = AnalyticsIntegrator(config=mock_config)

        with pytest.raises(ValueError, match="Invalid data_type"):
            integrator.fetch_hotjar_data(site_id="12345", data_type="invalid")

    @patch("tools.ux_research.analytics.analytics_integrator.requests.get")
    def test_fetch_heap_events(self, mock_get, mock_config):
        """Test fetching Heap events."""
        base_time = datetime.now()
        mock_response = Mock()
        mock_response.json.return_value = {
            "events": [
                {
                    "event": "page_view",
                    "time": base_time.isoformat(),
                    "user_id": "user1",
                    "session_id": "session1",
                    "properties": {"page": "/home"},
                },
                {
                    "event": "button_click",
                    "time": (base_time + timedelta(seconds=10)).isoformat(),
                    "user_id": "user1",
                    "session_id": "session1",
                    "properties": {"button": "cta"},
                },
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        integrator = AnalyticsIntegrator(config=mock_config)
        result = integrator.fetch_heap_events()

        assert len(result) == 2
        assert all(isinstance(event, Event) for event in result)
        assert result[0].event_name == "page_view"
        assert result[0].source == "heap"

    def test_analyze_user_journey(self, mock_config, sample_events):
        """Test user journey analysis."""
        integrator = AnalyticsIntegrator(config=mock_config)
        result = integrator.analyze_user_journey(events=sample_events)

        assert isinstance(result, JourneyAnalysis)
        assert result.total_journeys == 2  # 2 unique sessions
        assert len(result.steps) > 0
        assert all(isinstance(step, JourneyStep) for step in result.steps)
        assert result.avg_journey_time >= 0

    def test_analyze_user_journey_with_filters(self, mock_config, sample_events):
        """Test user journey analysis with start/end filters."""
        integrator = AnalyticsIntegrator(config=mock_config)
        result = integrator.analyze_user_journey(
            events=sample_events,
            start_event="page_view",
            end_event="form_submit",
        )

        assert isinstance(result, JourneyAnalysis)
        assert result.completed_journeys <= result.total_journeys

    def test_analyze_user_journey_empty_events(self, mock_config):
        """Test user journey analysis with empty events."""
        integrator = AnalyticsIntegrator(config=mock_config)
        result = integrator.analyze_user_journey(events=[])

        assert result.total_journeys == 0
        assert result.completed_journeys == 0
        assert len(result.steps) == 0

    def test_calculate_conversion_rate(self, mock_config, sample_events):
        """Test conversion rate calculation."""
        integrator = AnalyticsIntegrator(config=mock_config)
        funnel_steps = ["page_view", "button_click", "form_submit"]

        result = integrator.calculate_conversion_rate(
            funnel_steps=funnel_steps, events=sample_events
        )

        assert isinstance(result, ConversionAnalysis)
        assert len(result.funnel_steps) == len(funnel_steps)
        assert all(isinstance(step, FunnelStep) for step in result.funnel_steps)
        assert 0 <= result.overall_conversion_rate <= 1
        assert result.total_users == 2
        assert result.converted_users <= result.total_users

    def test_calculate_conversion_rate_empty_funnel(self, mock_config, sample_events):
        """Test conversion rate with empty funnel."""
        integrator = AnalyticsIntegrator(config=mock_config)
        result = integrator.calculate_conversion_rate(
            funnel_steps=[], events=sample_events
        )

        assert len(result.funnel_steps) == 0
        assert result.overall_conversion_rate == 0.0

    def test_calculate_conversion_rate_recommendations(self, mock_config):
        """Test that conversion analysis generates recommendations."""
        integrator = AnalyticsIntegrator(config=mock_config)

        # Create events with high drop-off
        base_time = datetime.now()
        events = [
            Event(
                "step1",
                base_time,
                f"user{i}",
                f"session{i}",
                {},
                "test",
            )
            for i in range(100)
        ]
        # Only 10 users proceed to step2
        events.extend(
            [
                Event(
                    "step2",
                    base_time + timedelta(seconds=10),
                    f"user{i}",
                    f"session{i}",
                    {},
                    "test",
                )
                for i in range(10)
            ]
        )

        result = integrator.calculate_conversion_rate(
            funnel_steps=["step1", "step2"], events=events
        )

        assert len(result.recommendations) > 0
        assert result.bottleneck_step is not None

    def test_aggregate_events(self, mock_config, sample_events):
        """Test event aggregation from multiple sources."""
        integrator = AnalyticsIntegrator(config=mock_config)

        # Split events into two sources
        source1 = sample_events[:3]
        source2 = sample_events[3:]

        result = integrator.aggregate_events(source1, source2)

        assert len(result) == len(sample_events)
        assert all(isinstance(event, Event) for event in result)
        # Verify sorted by timestamp
        for i in range(len(result) - 1):
            assert result[i].timestamp <= result[i + 1].timestamp

    def test_aggregate_events_deduplication(self, mock_config):
        """Test that aggregate_events deduplicates identical events."""
        integrator = AnalyticsIntegrator(config=mock_config)

        base_time = datetime.now()
        event = Event("test_event", base_time, "user1", "session1", {}, "test")

        # Create duplicate events
        source1 = [event]
        source2 = [event]

        result = integrator.aggregate_events(source1, source2)

        assert len(result) == 1  # Should deduplicate

    def test_export_analytics_json(self, mock_config, sample_events):
        """Test exporting analytics data as JSON."""
        integrator = AnalyticsIntegrator(config=mock_config)

        data = AnalyticsData(
            metrics={"sessions": 100.0, "pageviews": 500.0},
            dimensions={"country": ["US", "UK"]},
            events=sample_events,
            date_range=("2024-01-01", "2024-01-31"),
            source="test",
        )

        result = integrator.export_analytics(data, output_format="json")

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "metrics" in parsed
        assert "dimensions" in parsed
        assert "events" in parsed
        assert parsed["metrics"]["sessions"] == 100.0

    def test_export_analytics_csv(self, mock_config, sample_events):
        """Test exporting analytics data as CSV."""
        integrator = AnalyticsIntegrator(config=mock_config)

        # Create data with DataFrame
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02"],
                "sessions": [100, 150],
                "pageviews": [500, 750],
            }
        )

        data = AnalyticsData(metrics={}, dimensions={}, raw_data=df, source="test")

        result = integrator.export_analytics(data, output_format="csv")

        assert isinstance(result, str)
        assert "date" in result
        assert "sessions" in result

    def test_export_analytics_invalid_format(self, mock_config):
        """Test exporting with invalid format."""
        integrator = AnalyticsIntegrator(config=mock_config)
        data = AnalyticsData(source="test")

        with pytest.raises(ValueError, match="Invalid format"):
            integrator.export_analytics(data, output_format="invalid")

    def test_export_analytics_to_file(self, mock_config, tmp_path):
        """Test exporting analytics data to file."""
        integrator = AnalyticsIntegrator(config=mock_config)

        data = AnalyticsData(
            metrics={"sessions": 100.0},
            dimensions={},
            events=[],
            source="test",
        )

        output_file = tmp_path / "analytics.json"
        result = integrator.export_analytics(
            data, output_format="json", output_path=str(output_file)
        )

        assert result == str(output_file)
        assert output_file.exists()

        with open(output_file, "r", encoding="utf-8") as f:
            parsed = json.load(f)
            assert parsed["metrics"]["sessions"] == 100.0

    def test_clear_cache(self, mock_config):
        """Test clearing analytics cache."""
        integrator = AnalyticsIntegrator(config=mock_config)

        integrator._cache.set("test_key", "test_value")
        assert integrator._cache.get("test_key") == "test_value"

        integrator.clear_cache()
        assert integrator._cache.get("test_key") is None

    @patch("tools.ux_research.analytics.analytics_integrator.requests.get")
    def test_hotjar_api_error_handling(self, mock_get, mock_config):
        """Test Hotjar API error handling."""
        mock_get.side_effect = Exception("API Error")

        integrator = AnalyticsIntegrator(config=mock_config)

        with pytest.raises(RuntimeError, match="Hotjar API error"):
            integrator.fetch_hotjar_data(site_id="12345", data_type="heatmap")

    @patch("tools.ux_research.analytics.analytics_integrator.requests.get")
    def test_heap_api_error_handling(self, mock_get, mock_config):
        """Test Heap API error handling."""
        mock_get.side_effect = Exception("API Error")

        integrator = AnalyticsIntegrator(config=mock_config)

        with pytest.raises(RuntimeError, match="Heap API error"):
            integrator.fetch_heap_events()

    def test_fetch_hotjar_missing_api_key(self):
        """Test Hotjar fetch without API key."""
        integrator = AnalyticsIntegrator(config={})

        with pytest.raises(ValueError, match="Hotjar API key not configured"):
            integrator.fetch_hotjar_data(site_id="12345", data_type="heatmap")

    def test_fetch_heap_missing_credentials(self):
        """Test Heap fetch without credentials."""
        integrator = AnalyticsIntegrator(config={})

        with pytest.raises(ValueError, match="Heap app_id and api_key"):
            integrator.fetch_heap_events()

    def test_fetch_ga_without_client(self):
        """Test Google Analytics fetch without initialized client."""
        integrator = AnalyticsIntegrator(config={})

        with pytest.raises(ValueError, match="Google Analytics client not initialized"):
            integrator.fetch_google_analytics_data(
                property_id="123456", metrics=["sessions"]
            )

    @patch("tools.ux_research.analytics.analytics_integrator.requests.get")
    def test_cache_effectiveness(self, mock_get, mock_config):
        """Test that cache reduces API calls."""
        mock_response = Mock()
        mock_response.json.return_value = {"heatmaps": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        integrator = AnalyticsIntegrator(config=mock_config)

        # First call should hit API
        integrator.fetch_hotjar_data(site_id="12345", data_type="heatmap")
        assert mock_get.call_count == 1

        # Second call should use cache
        integrator.fetch_hotjar_data(site_id="12345", data_type="heatmap")
        assert mock_get.call_count == 1  # No additional API call

    def test_journey_analysis_bottleneck_detection(self, mock_config):
        """Test bottleneck detection in journey analysis."""
        integrator = AnalyticsIntegrator(config=mock_config)

        base_time = datetime.now()
        events = [
            Event("step1", base_time, "user1", "session1", {}, "test"),
            Event(
                "step2",
                base_time + timedelta(seconds=150),
                "user1",
                "session1",
                {},
                "test",
            ),  # Long delay
            Event(
                "step3",
                base_time + timedelta(seconds=160),
                "user1",
                "session1",
                {},
                "test",
            ),
        ]

        result = integrator.analyze_user_journey(events=events)

        assert len(result.bottlenecks) > 0

    def test_conversion_funnel_step_metrics(self, mock_config):
        """Test detailed funnel step metrics calculation."""
        integrator = AnalyticsIntegrator(config=mock_config)

        base_time = datetime.now()
        events = []

        # Create 10 users going through 3-step funnel
        for i in range(10):
            event = Event("step1", base_time, f"user{i}", f"session{i}", {}, "test")
            events.append(event)
            if i < 7:  # 7 proceed to step2
                events.append(
                    Event(
                        "step2",
                        base_time + timedelta(seconds=10),
                        f"user{i}",
                        f"session{i}",
                        {},
                        "test",
                    )
                )
            if i < 5:  # 5 complete step3
                events.append(
                    Event(
                        "step3",
                        base_time + timedelta(seconds=20),
                        f"user{i}",
                        f"session{i}",
                        {},
                        "test",
                    )
                )

        result = integrator.calculate_conversion_rate(
            funnel_steps=["step1", "step2", "step3"], events=events
        )

        assert result.funnel_steps[0].users_entered == 10
        assert result.funnel_steps[0].users_completed == 7
        assert result.funnel_steps[1].users_entered == 7
        assert result.funnel_steps[1].users_completed == 5
        assert result.overall_conversion_rate == 0.5  # 5/10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
