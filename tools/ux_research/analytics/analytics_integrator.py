"""Analytics integration for UX Research Platform.

This module provides integration with Google Analytics, Hotjar, Heap, and other
analytics platforms for comprehensive user behavior analysis, journey mapping,
and conversion rate optimization.
"""

import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (DateRange, Dimension, Metric,
                                                RunReportRequest)
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Represents a user event in analytics."""

    event_name: str
    timestamp: datetime
    user_id: str
    session_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"


@dataclass
class AnalyticsData:
    """Container for analytics data from various sources."""

    metrics: Dict[str, float] = field(default_factory=dict)
    dimensions: Dict[str, Any] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)
    date_range: Optional[Tuple[str, str]] = None
    source: str = "unknown"
    raw_data: Optional[pd.DataFrame] = None


@dataclass
class HotjarData:
    """Container for Hotjar-specific data."""

    site_id: str
    data_type: str
    heatmaps: List[Dict[str, Any]] = field(default_factory=list)
    recordings: List[Dict[str, Any]] = field(default_factory=list)
    polls: List[Dict[str, Any]] = field(default_factory=list)
    surveys: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JourneyStep:
    """Represents a step in a user journey."""

    step_name: str
    event_count: int
    unique_users: int
    avg_time_to_next: Optional[float] = None
    drop_off_rate: Optional[float] = None
    conversion_rate: Optional[float] = None


@dataclass
class JourneyAnalysis:
    """Analysis of user journey paths."""

    steps: List[JourneyStep]
    total_journeys: int
    completed_journeys: int
    avg_journey_time: float
    most_common_paths: List[Tuple[List[str], int]]
    drop_off_points: List[Tuple[str, float]]
    bottlenecks: List[str]


@dataclass
class FunnelStep:
    """Represents a step in a conversion funnel."""

    step_name: str
    users_entered: int
    users_completed: int
    completion_rate: float
    drop_off_count: int
    drop_off_rate: float
    avg_time_spent: Optional[float] = None


@dataclass
class ConversionAnalysis:
    """Analysis of conversion funnel performance."""

    funnel_steps: List[FunnelStep]
    overall_conversion_rate: float
    total_users: int
    converted_users: int
    avg_time_to_convert: float
    bottleneck_step: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


class AnalyticsCache:
    """Simple in-memory cache for analytics data."""

    def __init__(self, ttl: int = 3600):
        """Initialize cache with time-to-live in seconds.

        Args:
            ttl: Time-to-live for cache entries in seconds (default: 1 hour)
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached data if not expired.

        Args:
            key: Cache key

        Returns:
            Cached data or None if expired/missing
        """
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Store data in cache with current timestamp.

        Args:
            key: Cache key
            value: Data to cache
        """
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()

    def _make_key(self, *args: Any) -> str:
        """Generate cache key from arguments.

        Args:
            *args: Arguments to hash

        Returns:
            MD5 hash as cache key
        """
        key_str = json.dumps(args, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, max_calls: int, time_window: int):
        """Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self._max_calls = max_calls
        self._time_window = time_window
        self._calls: List[float] = []

    def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded."""
        now = time.time()
        # Remove calls outside the time window
        self._calls = [
            call_time
            for call_time in self._calls
            if now - call_time < self._time_window
        ]

        if len(self._calls) >= self._max_calls:
            sleep_time = self._time_window - (now - self._calls[0]) + 0.1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self._calls.append(now)


class AnalyticsIntegrator:
    """Integrates with multiple analytics platforms for UX research."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize analytics integrator with platform credentials.

        Args:
            config: Configuration dictionary with API credentials:
                - google_analytics: Service account JSON path or dict
                - hotjar_api_key: Hotjar API key
                - heap_app_id: Heap application ID
                - heap_api_key: Heap API key
                - cache_ttl: Cache TTL in seconds (default: 3600)
        """
        self.config = config or {}
        self._ga_client: Optional[BetaAnalyticsDataClient] = None
        self._cache = AnalyticsCache(ttl=self.config.get("cache_ttl", 3600))

        # Rate limiters for different platforms
        self._ga_limiter = RateLimiter(max_calls=10, time_window=60)
        self._hotjar_limiter = RateLimiter(max_calls=100, time_window=60)
        self._heap_limiter = RateLimiter(max_calls=200, time_window=60)

        # Initialize Google Analytics client if configured
        if "google_analytics" in self.config:
            self._initialize_ga_client()

        logger.info("AnalyticsIntegrator initialized")

    def _initialize_ga_client(self) -> None:
        """Initialize Google Analytics client with service account."""
        try:
            ga_config = self.config["google_analytics"]
            if isinstance(ga_config, str):
                # Path to service account JSON file
                scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
                credentials = service_account.Credentials.from_service_account_file(
                    ga_config,
                    scopes=scopes,
                )
            elif isinstance(ga_config, dict):
                # Service account info as dict
                scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
                credentials = service_account.Credentials.from_service_account_info(
                    ga_config,
                    scopes=scopes,
                )
            else:
                raise ValueError("Invalid Google Analytics configuration")

            self._ga_client = BetaAnalyticsDataClient(credentials=credentials)
            logger.info("Google Analytics client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GA client: {e}")
            raise

    def fetch_google_analytics_data(
        self,
        property_id: str,
        metrics: List[str],
        dimensions: Optional[List[str]] = None,
        date_range: Optional[Tuple[str, str]] = None,
    ) -> AnalyticsData:
        """Fetch data from Google Analytics 4.

        Args:
            property_id: GA4 property ID
            metrics: List of metrics to fetch (e.g., 'sessions', 'bounceRate')
            dimensions: Optional list of dimensions (e.g., 'date', 'country')
            date_range: Optional tuple of (start_date, end_date) in YYYY-MM-DD

        Returns:
            AnalyticsData object with fetched data

        Raises:
            ValueError: If GA client is not initialized
            RuntimeError: If API request fails
        """
        if not self._ga_client:
            raise ValueError("Google Analytics client not initialized")

        # Check cache
        cache_key = self._cache._make_key(
            "ga", property_id, metrics, dimensions, date_range
        )
        cached = self._cache.get(cache_key)
        if cached:
            logger.info("Returning cached GA data")
            return cached

        # Apply rate limiting
        self._ga_limiter.wait_if_needed()

        # Set default date range if not provided
        if not date_range:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            date_range = (start_date, end_date)

        try:
            # Build request
            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[
                    DateRange(start_date=date_range[0], end_date=date_range[1])
                ],
                metrics=[Metric(name=metric) for metric in metrics],
                dimensions=[Dimension(name=dim) for dim in (dimensions or [])],
            )

            # Execute request
            response = self._ga_client.run_report(request)

            # Parse response into structured data
            metrics_data: Dict[str, float] = {}
            dimensions_data: Dict[str, Any] = defaultdict(list)
            rows_data = []

            for row in response.rows:
                row_dict = {}

                # Extract dimensions
                for i, dimension_value in enumerate(row.dimension_values):
                    dim_name = dimensions[i] if dimensions else f"dim_{i}"
                    dim_value = dimension_value.value
                    dimensions_data[dim_name].append(dim_value)
                    row_dict[dim_name] = dim_value

                # Extract metrics
                for i, metric_value in enumerate(row.metric_values):
                    metric_name = metrics[i]
                    metric_val = float(metric_value.value)
                    row_dict[metric_name] = metric_val

                    # Aggregate metrics
                    if metric_name not in metrics_data:
                        metrics_data[metric_name] = 0
                    metrics_data[metric_name] += metric_val

                rows_data.append(row_dict)

            # Create DataFrame if we have data
            raw_df = pd.DataFrame(rows_data) if rows_data else None

            result = AnalyticsData(
                metrics=metrics_data,
                dimensions=dict(dimensions_data),
                date_range=date_range,
                source="google_analytics",
                raw_data=raw_df,
            )

            # Cache result
            self._cache.set(cache_key, result)

            logger.info(
                f"Fetched GA data: {len(rows_data)} rows, "
                f"{len(metrics_data)} metrics"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to fetch GA data: {e}")
            raise RuntimeError(f"Google Analytics API error: {e}") from e

    def fetch_hotjar_data(self, site_id: str, data_type: str = "heatmap") -> HotjarData:
        """Fetch data from Hotjar API.

        Args:
            site_id: Hotjar site ID
            data_type: Type of data to fetch ('heatmap', 'recording',
                      'poll', 'survey')

        Returns:
            HotjarData object with fetched data

        Raises:
            ValueError: If API key is not configured or invalid data type
            RuntimeError: If API request fails
        """
        if "hotjar_api_key" not in self.config:
            raise ValueError("Hotjar API key not configured")

        valid_types = ["heatmap", "recording", "poll", "survey"]
        if data_type not in valid_types:
            raise ValueError(f"Invalid data_type. Must be one of {valid_types}")

        # Check cache
        cache_key = self._cache._make_key("hotjar", site_id, data_type)
        cached = self._cache.get(cache_key)
        if cached:
            logger.info("Returning cached Hotjar data")
            return cached

        # Apply rate limiting
        self._hotjar_limiter.wait_if_needed()

        api_key = self.config["hotjar_api_key"]
        headers = {"Authorization": f"Bearer {api_key}"}
        base_url = "https://api.hotjar.com/v1"

        result = HotjarData(site_id=site_id, data_type=data_type)

        try:
            if data_type == "heatmap":
                url = f"{base_url}/sites/{site_id}/heatmaps"
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                result.heatmaps = response.json().get("heatmaps", [])

            elif data_type == "recording":
                url = f"{base_url}/sites/{site_id}/recordings"
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                result.recordings = response.json().get("recordings", [])

            elif data_type == "poll":
                url = f"{base_url}/sites/{site_id}/polls"
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                result.polls = response.json().get("polls", [])

            elif data_type == "survey":
                url = f"{base_url}/sites/{site_id}/surveys"
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                result.surveys = response.json().get("surveys", [])

            result.metadata = {
                "fetched_at": datetime.now().isoformat(),
                "site_id": site_id,
                "data_type": data_type,
            }

            # Cache result
            self._cache.set(cache_key, result)

            logger.info(f"Fetched Hotjar {data_type} data for site {site_id}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Hotjar data: {e}")
            raise RuntimeError(f"Hotjar API error: {e}") from e

    def fetch_heap_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_names: Optional[List[str]] = None,
    ) -> List[Event]:
        """Fetch events from Heap Analytics.

        Args:
            start_time: Start time for event query
            end_time: End time for event query
            event_names: Optional list of specific event names to fetch

        Returns:
            List of Event objects

        Raises:
            ValueError: If Heap credentials are not configured
            RuntimeError: If API request fails
        """
        if "heap_app_id" not in self.config or "heap_api_key" not in self.config:
            raise ValueError("Heap app_id and api_key not configured")

        # Set default time range
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=7)

        # Check cache
        cache_key = self._cache._make_key("heap", start_time, end_time, event_names)
        cached = self._cache.get(cache_key)
        if cached:
            logger.info("Returning cached Heap events")
            return cached

        # Apply rate limiting
        self._heap_limiter.wait_if_needed()

        app_id = self.config["heap_app_id"]
        api_key = self.config["heap_api_key"]
        headers = {"Authorization": f"Bearer {api_key}"}
        url = f"https://heapanalytics.com/api/v1/apps/{app_id}/events"

        params = {
            "from_time": start_time.isoformat(),
            "to_time": end_time.isoformat(),
        }

        if event_names:
            params["event_names"] = ",".join(event_names)

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            events = []
            for event_data in data.get("events", []):
                event = Event(
                    event_name=event_data.get("event", "unknown"),
                    timestamp=datetime.fromisoformat(
                        event_data.get("time", datetime.now().isoformat())
                    ),
                    user_id=event_data.get("user_id", ""),
                    session_id=event_data.get("session_id", ""),
                    properties=event_data.get("properties", {}),
                    source="heap",
                )
                events.append(event)

            # Cache result
            self._cache.set(cache_key, events)

            logger.info(f"Fetched {len(events)} events from Heap")
            return events

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Heap events: {e}")
            raise RuntimeError(f"Heap API error: {e}") from e

    def analyze_user_journey(
        self,
        events: List[Event],
        start_event: Optional[str] = None,
        end_event: Optional[str] = None,
    ) -> JourneyAnalysis:
        """Analyze user journey paths through events.

        Args:
            events: List of user events
            start_event: Optional starting event name
            end_event: Optional ending event name

        Returns:
            JourneyAnalysis with path insights
        """
        if not events:
            return JourneyAnalysis(
                steps=[],
                total_journeys=0,
                completed_journeys=0,
                avg_journey_time=0.0,
                most_common_paths=[],
                drop_off_points=[],
                bottlenecks=[],
            )

        # Group events by session
        sessions: Dict[str, List[Event]] = defaultdict(list)
        for event in sorted(events, key=lambda e: e.timestamp):
            sessions[event.session_id].append(event)

        # Analyze journeys
        paths: List[Tuple[str, ...]] = []
        journey_times: List[float] = []
        step_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "users": set(),
                "next_times": [],
                "drop_offs": 0,
            }
        )

        completed_count = 0
        total_count = len(sessions)

        for session_events in sessions.values():
            if not session_events:
                continue

            # Filter by start/end events if specified
            if start_event:
                try:
                    start_idx = next(
                        i
                        for i, e in enumerate(session_events)
                        if e.event_name == start_event
                    )
                    session_events = session_events[start_idx:]
                except StopIteration:
                    continue

            if not session_events:
                continue

            # Extract path
            path = tuple(e.event_name for e in session_events)
            paths.append(path)

            # Calculate journey time
            if len(session_events) > 1:
                journey_time = (
                    session_events[-1].timestamp - session_events[0].timestamp
                ).total_seconds()
                journey_times.append(journey_time)

            # Track if journey completed
            if end_event and session_events[-1].event_name == end_event:
                completed_count += 1

            # Collect step statistics
            for i, event in enumerate(session_events):
                step_name = event.event_name
                step_stats[step_name]["count"] += 1
                step_stats[step_name]["users"].add(event.user_id)

                # Time to next step
                if i < len(session_events) - 1:
                    time_to_next = (
                        session_events[i + 1].timestamp - event.timestamp
                    ).total_seconds()
                    step_stats[step_name]["next_times"].append(time_to_next)
                else:
                    # Last step in journey (potential drop-off)
                    if not end_event or event.event_name != end_event:
                        step_stats[step_name]["drop_offs"] += 1

        # Build journey steps
        steps = []
        for step_name, stats in step_stats.items():
            avg_time_to_next = (
                sum(stats["next_times"]) / len(stats["next_times"])
                if stats["next_times"]
                else None
            )
            drop_off_rate = (
                stats["drop_offs"] / stats["count"] if stats["count"] > 0 else 0.0
            )

            steps.append(
                JourneyStep(
                    step_name=step_name,
                    event_count=stats["count"],
                    unique_users=len(stats["users"]),
                    avg_time_to_next=avg_time_to_next,
                    drop_off_rate=drop_off_rate,
                )
            )

        # Find most common paths
        path_counts: Dict[Tuple[str, ...], int] = defaultdict(int)
        for path in paths:
            path_counts[path] += 1

        most_common_paths = sorted(
            [(list(path), count) for path, count in path_counts.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        # Identify drop-off points (steps with high drop-off rates)
        drop_off_points = sorted(
            [
                (step.step_name, step.drop_off_rate or 0.0)
                for step in steps
                if step.drop_off_rate
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        # Identify bottlenecks (steps with long avg time to next)
        bottlenecks = [
            step.step_name
            for step in sorted(
                steps, key=lambda s: s.avg_time_to_next or 0, reverse=True
            )[:3]
            if step.avg_time_to_next and step.avg_time_to_next > 60
        ]

        avg_journey_time = (
            sum(journey_times) / len(journey_times) if journey_times else 0.0
        )

        return JourneyAnalysis(
            steps=steps,
            total_journeys=total_count,
            completed_journeys=completed_count,
            avg_journey_time=avg_journey_time,
            most_common_paths=most_common_paths,
            drop_off_points=drop_off_points,
            bottlenecks=bottlenecks,
        )

    def calculate_conversion_rate(
        self, funnel_steps: List[str], events: List[Event]
    ) -> ConversionAnalysis:
        """Calculate conversion rates through a defined funnel.

        Args:
            funnel_steps: Ordered list of event names defining the funnel
            events: List of user events

        Returns:
            ConversionAnalysis with funnel metrics
        """
        if not funnel_steps or not events:
            return ConversionAnalysis(
                funnel_steps=[],
                overall_conversion_rate=0.0,
                total_users=0,
                converted_users=0,
                avg_time_to_convert=0.0,
            )

        # Group events by user
        user_events: Dict[str, List[Event]] = defaultdict(list)
        for event in sorted(events, key=lambda e: e.timestamp):
            user_events[event.user_id].append(event)

        # Track funnel progression for each user
        users_at_step: Dict[int, set] = {i: set() for i in range(len(funnel_steps))}
        step_times: Dict[int, List[float]] = defaultdict(list)
        conversion_times: List[float] = []

        for user_id, user_event_list in user_events.items():
            event_names = [e.event_name for e in user_event_list]
            current_step = 0
            step_start_time = None

            for i, event in enumerate(user_event_list):
                if (
                    current_step < len(funnel_steps)
                    and event.event_name == funnel_steps[current_step]
                ):
                    users_at_step[current_step].add(user_id)

                    if current_step == 0:
                        step_start_time = event.timestamp

                    if current_step > 0 and step_start_time:
                        time_spent = (event.timestamp - step_start_time).total_seconds()
                        step_times[current_step].append(time_spent)
                        step_start_time = event.timestamp

                    current_step += 1

                    # Check if user completed funnel
                    if (
                        current_step == len(funnel_steps)
                        and user_event_list[0].timestamp
                    ):
                        conversion_time = (
                            event.timestamp - user_event_list[0].timestamp
                        ).total_seconds()
                        conversion_times.append(conversion_time)

        # Build funnel steps analysis
        funnel_analysis = []
        for i, step_name in enumerate(funnel_steps):
            users_entered = len(users_at_step[i])
            next_step_exists = i + 1 < len(funnel_steps)
            users_completed = (
                len(users_at_step[i + 1]) if next_step_exists else users_entered
            )

            completion_rate = (
                users_completed / users_entered if users_entered > 0 else 0.0
            )
            drop_off_count = users_entered - users_completed
            drop_off_rate = 1.0 - completion_rate

            avg_time_spent = (
                sum(step_times[i + 1]) / len(step_times[i + 1])
                if step_times[i + 1]
                else None
            )

            funnel_analysis.append(
                FunnelStep(
                    step_name=step_name,
                    users_entered=users_entered,
                    users_completed=users_completed,
                    completion_rate=completion_rate,
                    drop_off_count=drop_off_count,
                    drop_off_rate=drop_off_rate,
                    avg_time_spent=avg_time_spent,
                )
            )

        # Calculate overall metrics
        total_users = len(users_at_step[0]) if users_at_step[0] else 0
        converted_users = (
            len(users_at_step[len(funnel_steps) - 1])
            if len(funnel_steps) - 1 in users_at_step
            else 0
        )
        overall_conversion_rate = (
            converted_users / total_users if total_users > 0 else 0.0
        )
        avg_time_to_convert = (
            sum(conversion_times) / len(conversion_times) if conversion_times else 0.0
        )

        # Identify bottleneck (step with highest drop-off rate)
        bottleneck_step = None
        if funnel_analysis:
            bottleneck = max(funnel_analysis, key=lambda s: s.drop_off_rate)
            if bottleneck.drop_off_rate > 0.3:  # More than 30% drop-off
                bottleneck_step = bottleneck.step_name

        # Generate recommendations
        recommendations = []
        for step in funnel_analysis:
            if step.drop_off_rate > 0.4:
                drop_off_pct = f"{step.drop_off_rate:.1%}"
                recommendations.append(
                    f"High drop-off at '{step.step_name}' ({drop_off_pct})"
                    " - investigate UX issues"
                )
            if step.avg_time_spent and step.avg_time_spent > 120:
                recommendations.append(
                    f"Users spending {step.avg_time_spent:.0f}s at "
                    f"'{step.step_name}' - consider simplifying"
                )

        if overall_conversion_rate < 0.2:
            recommendations.append(
                "Overall conversion rate is low (<20%) - review entire funnel"
            )

        return ConversionAnalysis(
            funnel_steps=funnel_analysis,
            overall_conversion_rate=overall_conversion_rate,
            total_users=total_users,
            converted_users=converted_users,
            avg_time_to_convert=avg_time_to_convert,
            bottleneck_step=bottleneck_step,
            recommendations=recommendations,
        )

    def aggregate_events(self, *event_sources: List[Event]) -> List[Event]:
        """Aggregate events from multiple sources.

        Args:
            *event_sources: Variable number of event lists

        Returns:
            Combined and deduplicated list of events sorted by timestamp
        """
        all_events = []
        for events in event_sources:
            all_events.extend(events)

        # Deduplicate based on event signature
        seen = set()
        unique_events = []
        for event in all_events:
            signature = (
                event.event_name,
                event.timestamp.isoformat(),
                event.user_id,
                event.session_id,
            )
            if signature not in seen:
                seen.add(signature)
                unique_events.append(event)

        # Sort by timestamp
        unique_events.sort(key=lambda e: e.timestamp)

        logger.info(
            f"Aggregated {len(all_events)} events into "
            f"{len(unique_events)} unique events"
        )
        return unique_events

    def export_analytics(
        self,
        data: AnalyticsData,
        output_format: str = "json",
        output_path: Optional[str] = None,
    ) -> str:
        """Export analytics data to various formats.

        Args:
            data: AnalyticsData to export
            output_format: Format to export ('json', 'csv', 'excel')
            output_path: Optional file path to save export

        Returns:
            Exported data as string (or file path if output_path specified)

        Raises:
            ValueError: If invalid format specified
        """
        if output_format == "json":
            export_data = {
                "metrics": data.metrics,
                "dimensions": data.dimensions,
                "date_range": data.date_range,
                "source": data.source,
                "events": [
                    {
                        "event_name": e.event_name,
                        "timestamp": e.timestamp.isoformat(),
                        "user_id": e.user_id,
                        "session_id": e.session_id,
                        "properties": e.properties,
                        "source": e.source,
                    }
                    for e in data.events
                ],
            }
            result = json.dumps(export_data, indent=2)

            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result)
                logger.info(f"Exported analytics to {output_path}")
                return output_path
            return result

        elif output_format == "csv":
            if data.raw_data is not None:
                if output_path:
                    data.raw_data.to_csv(output_path, index=False)
                    logger.info(f"Exported analytics to {output_path}")
                    return output_path
                return data.raw_data.to_csv(index=False)
            else:
                # Create DataFrame from events
                if data.events:
                    df = pd.DataFrame(
                        [
                            {
                                "event_name": e.event_name,
                                "timestamp": e.timestamp.isoformat(),
                                "user_id": e.user_id,
                                "session_id": e.session_id,
                                "source": e.source,
                            }
                            for e in data.events
                        ]
                    )
                    if output_path:
                        df.to_csv(output_path, index=False)
                        logger.info(f"Exported analytics to {output_path}")
                        return output_path
                    return df.to_csv(index=False)
                return ""

        elif output_format == "excel":
            if not output_path:
                raise ValueError("output_path required for Excel export")

            if data.raw_data is not None:
                data.raw_data.to_excel(output_path, index=False)
            else:
                # Create DataFrame from events
                if data.events:
                    df = pd.DataFrame(
                        [
                            {
                                "event_name": e.event_name,
                                "timestamp": e.timestamp.isoformat(),
                                "user_id": e.user_id,
                                "session_id": e.session_id,
                                "source": e.source,
                            }
                            for e in data.events
                        ]
                    )
                    df.to_excel(output_path, index=False)

            logger.info(f"Exported analytics to {output_path}")
            return output_path

        else:
            raise ValueError(
                f"Invalid format '{output_format}'. "
                "Must be 'json', 'csv', or 'excel'"
            )

    def clear_cache(self) -> None:
        """Clear all cached analytics data."""
        self._cache.clear()
        logger.info("Analytics cache cleared")
