"""
Feedback Collector for UX Research Platform.

This module implements comprehensive feedback collection from multiple sources including
survey platforms, heatmap tools, session recordings, and support ticket systems.
Part of the devCrew_s1 UX Research & Design Feedback Platform (TOOL-UX-001).
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SurveyPlatform(str, Enum):
    """Supported survey platforms."""

    TYPEFORM = "typeform"
    GOOGLE_FORMS = "google_forms"
    SURVEYMONKEY = "surveymonkey"
    CSV = "csv"
    JSON = "json"


class HeatmapPlatform(str, Enum):
    """Supported heatmap platforms."""

    HOTJAR = "hotjar"
    CRAZY_EGG = "crazy_egg"
    JSON = "json"


class SupportPlatform(str, Enum):
    """Supported support ticket platforms."""

    ZENDESK = "zendesk"
    INTERCOM = "intercom"
    CSV = "csv"
    JSON = "json"


class ClickEvent(BaseModel):
    """Model for click event data."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    timestamp: datetime = Field(..., description="Event timestamp")
    element: Optional[str] = Field(None, description="HTML element clicked")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ScrollEvent(BaseModel):
    """Model for scroll event data."""

    depth_percent: float = Field(..., ge=0, le=100, description="Scroll depth %")
    timestamp: datetime = Field(..., description="Event timestamp")
    viewport_height: Optional[int] = Field(None, description="Viewport height")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class HoverEvent(BaseModel):
    """Model for hover event data."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    duration_ms: int = Field(..., ge=0, description="Hover duration")
    timestamp: datetime = Field(..., description="Event timestamp")
    element: Optional[str] = Field(None, description="HTML element hovered")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SurveyResponse(BaseModel):
    """Model for survey response data."""

    response_id: str = Field(..., description="Unique response identifier")
    timestamp: datetime = Field(..., description="Response timestamp")
    respondent_id: Optional[str] = Field(None, description="Respondent identifier")
    answers: Dict[str, Any] = Field(
        default_factory=dict, description="Question-answer pairs"
    )
    rating: Optional[int] = Field(None, ge=0, le=10, description="NPS rating (0-10)")
    free_text: Optional[str] = Field(None, description="Free text feedback")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @validator("rating")
    def validate_rating(cls, v: Optional[int]) -> Optional[int]:
        """Validate rating is in NPS range."""
        if v is not None and not (0 <= v <= 10):
            raise ValueError("Rating must be between 0 and 10")
        return v


class HeatmapData(BaseModel):
    """Model for heatmap data."""

    site_id: str = Field(..., description="Site identifier")
    page_url: str = Field(..., description="Page URL")
    clicks: List[ClickEvent] = Field(default_factory=list, description="Click events")
    scrolls: List[ScrollEvent] = Field(
        default_factory=list, description="Scroll events"
    )
    hovers: List[HoverEvent] = Field(default_factory=list, description="Hover events")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SupportTicket(BaseModel):
    """Model for support ticket data."""

    ticket_id: str = Field(..., description="Ticket identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    status: str = Field(..., description="Ticket status")
    subject: str = Field(..., description="Ticket subject")
    description: str = Field(..., description="Ticket description")
    priority: Optional[str] = Field(None, description="Ticket priority")
    tags: List[str] = Field(default_factory=list, description="Ticket tags")
    sentiment: Optional[str] = Field(None, description="Sentiment analysis result")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class NPSScore(BaseModel):
    """Model for Net Promoter Score calculation."""

    score: float = Field(..., ge=-100, le=100, description="NPS score (-100 to 100)")
    promoters: int = Field(..., ge=0, description="Number of promoters (9-10)")
    passives: int = Field(..., ge=0, description="Number of passives (7-8)")
    detractors: int = Field(..., ge=0, description="Number of detractors (0-6)")
    total_responses: int = Field(..., ge=0, description="Total responses")

    @validator("total_responses")
    def validate_total(cls, v: int, values: Dict[str, Any]) -> int:
        """Validate total equals sum of categories."""
        if "promoters" in values and "passives" in values and "detractors" in values:
            expected = values["promoters"] + values["passives"] + values["detractors"]
            if v != expected:
                raise ValueError(f"Total responses {v} != sum of categories {expected}")
        return v


class FeedbackCollector:
    """
    Comprehensive feedback collector for UX research.

    Supports multiple data sources including survey platforms, heatmap tools,
    session recordings, and support ticket systems.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize feedback collector.

        Args:
            config: Configuration dictionary containing API keys and settings.
                Expected keys:
                - typeform_api_key: TypeForm API key
                - surveymonkey_api_key: SurveyMonkey API key
                - google_forms_credentials: Google Forms credentials
                - hotjar_api_key: Hotjar API key
                - crazy_egg_api_key: Crazy Egg API key
                - zendesk_api_key: Zendesk API key
                - intercom_api_key: Intercom API key
                - rate_limit_delay: Delay between API calls (seconds)
                - cache_enabled: Enable response caching
                - cache_ttl: Cache time-to-live (seconds)
        """
        self.config = config or {}
        self.rate_limit_delay = self.config.get("rate_limit_delay", 1.0)
        self.cache_enabled = self.config.get("cache_enabled", True)
        self.cache_ttl = self.config.get("cache_ttl", 3600)
        self._cache: Dict[str, Tuple[Any, datetime]] = {}

        logger.info("FeedbackCollector initialized with config")

    def _get_cache_key(self, *args: Any) -> str:
        """Generate cache key from arguments."""
        return json.dumps(args, sort_keys=True, default=str)

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if valid."""
        if not self.cache_enabled:
            return None

        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Cache hit for key: {key[:50]}")
                return value
            else:
                del self._cache[key]
        return None

    def _set_cached(self, key: str, value: Any) -> None:
        """Set cached value."""
        if self.cache_enabled:
            self._cache[key] = (value, datetime.now())

    def collect_survey_responses(
        self,
        source: str,
        survey_id: Optional[str] = None,
        date_range: Optional[Tuple[str, str]] = None,
        file_path: Optional[str] = None,
    ) -> List[SurveyResponse]:
        """
        Collect survey responses from specified platform.

        Args:
            source: Survey platform (typeform, google_forms, surveymonkey, csv, json)
            survey_id: Survey identifier (required for API sources)
            date_range: Optional date range tuple (start_date, end_date) as ISO strings
            file_path: Path to CSV/JSON file for file-based sources

        Returns:
            List of SurveyResponse objects

        Raises:
            ValueError: If required parameters are missing
            requests.HTTPError: If API request fails
        """
        cache_key = self._get_cache_key(
            "survey", source, survey_id, date_range, file_path
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        platform = SurveyPlatform(source.lower())

        if platform in [SurveyPlatform.CSV, SurveyPlatform.JSON]:
            if not file_path:
                raise ValueError(f"file_path required for {platform} source")
            responses = self._load_survey_from_file(file_path, platform)
        else:
            if not survey_id:
                raise ValueError(f"survey_id required for {platform} source")
            responses = self._collect_survey_from_api(platform, survey_id, date_range)

        self._set_cached(cache_key, responses)
        logger.info(f"Collected {len(responses)} survey responses from {source}")
        return responses

    def _load_survey_from_file(
        self, file_path: str, platform: SurveyPlatform
    ) -> List[SurveyResponse]:
        """Load survey responses from CSV or JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if platform == SurveyPlatform.CSV:
            df = pd.read_csv(file_path)
            responses = []

            for _, row in df.iterrows():
                # Extract standard fields
                response_data = {
                    "response_id": str(row.get("response_id", row.name)),
                    "timestamp": pd.to_datetime(row.get("timestamp", datetime.now())),
                    "respondent_id": (
                        str(row.get("respondent_id"))
                        if pd.notna(row.get("respondent_id"))
                        else None
                    ),
                    "rating": (
                        int(row.get("rating")) if pd.notna(row.get("rating")) else None
                    ),
                    "free_text": (
                        str(row.get("free_text"))
                        if pd.notna(row.get("free_text"))
                        else None
                    ),
                }

                # Extract all other columns as answers
                excluded_cols = {
                    "response_id",
                    "timestamp",
                    "respondent_id",
                    "rating",
                    "free_text",
                }
                answers = {
                    col: row[col]
                    for col in df.columns
                    if col not in excluded_cols and pd.notna(row[col])
                }
                response_data["answers"] = answers

                responses.append(SurveyResponse(**response_data))

            return responses

        else:  # JSON
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                data = [data]

            responses = []
            for item in data:
                # Parse timestamp if string
                if isinstance(item.get("timestamp"), str):
                    item["timestamp"] = datetime.fromisoformat(
                        item["timestamp"].replace("Z", "+00:00")
                    )
                responses.append(SurveyResponse(**item))

            return responses

    def _collect_survey_from_api(
        self,
        platform: SurveyPlatform,
        survey_id: str,
        date_range: Optional[Tuple[str, str]],
    ) -> List[SurveyResponse]:
        """Collect survey responses from API."""
        if platform == SurveyPlatform.TYPEFORM:
            return self._collect_typeform_responses(survey_id, date_range)
        elif platform == SurveyPlatform.GOOGLE_FORMS:
            return self._collect_google_forms_responses(survey_id, date_range)
        elif platform == SurveyPlatform.SURVEYMONKEY:
            return self._collect_surveymonkey_responses(survey_id, date_range)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _collect_typeform_responses(
        self, survey_id: str, date_range: Optional[Tuple[str, str]]
    ) -> List[SurveyResponse]:
        """Collect responses from TypeForm API."""
        api_key = self.config.get("typeform_api_key")
        if not api_key:
            raise ValueError("typeform_api_key not configured")

        url = f"https://api.typeform.com/forms/{survey_id}/responses"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        params = {}
        if date_range:
            params["since"] = date_range[0]
            params["until"] = date_range[1]

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        responses = []

        for item in data.get("items", []):
            answers = {}
            rating = None
            free_text = None

            for answer in item.get("answers", []):
                field_id = answer.get("field", {}).get("id")
                field_type = answer.get("field", {}).get("type")

                if field_type == "opinion_scale":
                    rating = answer.get("number")
                elif field_type in ["long_text", "short_text"]:
                    free_text = answer.get("text")
                else:
                    answers[field_id] = answer.get(field_type, answer)

            responses.append(
                SurveyResponse(
                    response_id=item["response_id"],
                    timestamp=datetime.fromisoformat(
                        item["submitted_at"].replace("Z", "+00:00")
                    ),
                    respondent_id=item.get("respondent_id"),
                    answers=answers,
                    rating=rating,
                    free_text=free_text,
                )
            )

        return responses

    def _collect_google_forms_responses(
        self, survey_id: str, date_range: Optional[Tuple[str, str]]
    ) -> List[SurveyResponse]:
        """Collect responses from Google Forms API."""
        # Note: Google Forms API requires OAuth2 credentials
        # This is a simplified implementation
        credentials = self.config.get("google_forms_credentials")
        if not credentials:
            raise ValueError("google_forms_credentials not configured")

        # This would use Google Sheets API to read form responses
        # Implementation requires google-auth and google-api-python-client
        logger.warning(
            "Google Forms API collection requires OAuth2 setup. "
            "Use CSV export as fallback."
        )
        return []

    def _collect_surveymonkey_responses(
        self, survey_id: str, date_range: Optional[Tuple[str, str]]
    ) -> List[SurveyResponse]:
        """Collect responses from SurveyMonkey API."""
        api_key = self.config.get("surveymonkey_api_key")
        if not api_key:
            raise ValueError("surveymonkey_api_key not configured")

        url = f"https://api.surveymonkey.com/v3/surveys/{survey_id}/responses/bulk"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        params = {}
        if date_range:
            params["start_created_at"] = date_range[0]
            params["end_created_at"] = date_range[1]

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        responses = []

        for item in data.get("data", []):
            answers = {}
            rating = None
            free_text = None

            for page in item.get("pages", []):
                for question in page.get("questions", []):
                    q_id = question["id"]
                    for answer in question.get("answers", []):
                        if "row_id" in answer:
                            # Matrix/rating question
                            rating = answer.get("value")
                        elif "text" in answer:
                            free_text = answer["text"]
                        else:
                            answers[q_id] = answer

            responses.append(
                SurveyResponse(
                    response_id=item["id"],
                    timestamp=datetime.fromisoformat(
                        item["date_created"].replace("Z", "+00:00")
                    ),
                    respondent_id=item.get("recipient_id"),
                    answers=answers,
                    rating=rating,
                    free_text=free_text,
                )
            )

        return responses

    def collect_heatmap_data(
        self,
        platform: str,
        site_id: str,
        pages: Optional[List[str]] = None,
        file_path: Optional[str] = None,
    ) -> HeatmapData:
        """
        Extract heatmap data from specified platform.

        Args:
            platform: Heatmap platform (hotjar, crazy_egg, json)
            site_id: Site identifier
            pages: Optional list of page URLs to collect
            file_path: Path to JSON file for file-based source

        Returns:
            HeatmapData object

        Raises:
            ValueError: If required parameters are missing
        """
        cache_key = self._get_cache_key("heatmap", platform, site_id, pages)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        heatmap_platform = HeatmapPlatform(platform.lower())

        if heatmap_platform == HeatmapPlatform.JSON:
            if not file_path:
                raise ValueError("file_path required for json source")
            heatmap = self._load_heatmap_from_file(file_path)
        else:
            heatmap = self._collect_heatmap_from_api(heatmap_platform, site_id, pages)

        self._set_cached(cache_key, heatmap)
        logger.info(
            f"Collected heatmap data from {platform}: "
            f"{len(heatmap.clicks)} clicks, {len(heatmap.scrolls)} scrolls"
        )
        return heatmap

    def _load_heatmap_from_file(self, file_path: str) -> HeatmapData:
        """Load heatmap data from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Parse datetime strings
        for click in data.get("clicks", []):
            if isinstance(click.get("timestamp"), str):
                click["timestamp"] = datetime.fromisoformat(
                    click["timestamp"].replace("Z", "+00:00")
                )

        for scroll in data.get("scrolls", []):
            if isinstance(scroll.get("timestamp"), str):
                scroll["timestamp"] = datetime.fromisoformat(
                    scroll["timestamp"].replace("Z", "+00:00")
                )

        for hover in data.get("hovers", []):
            if isinstance(hover.get("timestamp"), str):
                hover["timestamp"] = datetime.fromisoformat(
                    hover["timestamp"].replace("Z", "+00:00")
                )

        return HeatmapData(**data)

    def _collect_heatmap_from_api(
        self, platform: HeatmapPlatform, site_id: str, pages: Optional[List[str]]
    ) -> HeatmapData:
        """Collect heatmap data from API."""
        if platform == HeatmapPlatform.HOTJAR:
            return self._collect_hotjar_heatmap(site_id, pages)
        elif platform == HeatmapPlatform.CRAZY_EGG:
            return self._collect_crazy_egg_heatmap(site_id, pages)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _collect_hotjar_heatmap(
        self, site_id: str, pages: Optional[List[str]]
    ) -> HeatmapData:
        """Collect heatmap data from Hotjar API."""
        api_key = self.config.get("hotjar_api_key")
        if not api_key:
            raise ValueError("hotjar_api_key not configured")

        # Hotjar API v1 endpoints
        base_url = "https://api.hotjar.com/v1"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Get heatmaps list
        url = f"{base_url}/sites/{site_id}/heatmaps"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        heatmaps = response.json().get("heatmaps", [])

        # Aggregate data from all heatmaps
        all_clicks = []
        all_scrolls = []
        all_hovers = []
        page_url = pages[0] if pages else f"site-{site_id}"

        for heatmap in heatmaps:
            heatmap_id = heatmap["id"]

            # Get click data
            clicks_url = f"{base_url}/heatmaps/{heatmap_id}/clicks"
            clicks_resp = requests.get(clicks_url, headers=headers, timeout=30)
            if clicks_resp.ok:
                for click in clicks_resp.json().get("clicks", []):
                    all_clicks.append(
                        ClickEvent(
                            x=click["x"],
                            y=click["y"],
                            timestamp=datetime.fromisoformat(
                                click["timestamp"].replace("Z", "+00:00")
                            ),
                            element=click.get("element"),
                        )
                    )

            # Get scroll data
            scrolls_url = f"{base_url}/heatmaps/{heatmap_id}/scrolls"
            scrolls_resp = requests.get(scrolls_url, headers=headers, timeout=30)
            if scrolls_resp.ok:
                for scroll in scrolls_resp.json().get("scrolls", []):
                    all_scrolls.append(
                        ScrollEvent(
                            depth_percent=scroll["depth_percent"],
                            timestamp=datetime.fromisoformat(
                                scroll["timestamp"].replace("Z", "+00:00")
                            ),
                            viewport_height=scroll.get("viewport_height"),
                        )
                    )

        return HeatmapData(
            site_id=site_id,
            page_url=page_url,
            clicks=all_clicks,
            scrolls=all_scrolls,
            hovers=all_hovers,
        )

    def _collect_crazy_egg_heatmap(
        self, site_id: str, pages: Optional[List[str]]
    ) -> HeatmapData:
        """Collect heatmap data from Crazy Egg API."""
        api_key = self.config.get("crazy_egg_api_key")
        if not api_key:
            raise ValueError("crazy_egg_api_key not configured")

        # Crazy Egg API implementation would go here
        logger.warning("Crazy Egg API collection not yet implemented")

        return HeatmapData(
            site_id=site_id,
            page_url=pages[0] if pages else f"site-{site_id}",
            clicks=[],
            scrolls=[],
            hovers=[],
        )

    def aggregate_support_tickets(
        self,
        platform: str,
        filters: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
    ) -> List[SupportTicket]:
        """
        Aggregate support tickets from specified platform.

        Args:
            platform: Support platform (zendesk, intercom, csv, json)
            filters: Optional filters (status, priority, tags, date_range)
            file_path: Path to CSV/JSON file for file-based sources

        Returns:
            List of SupportTicket objects

        Raises:
            ValueError: If required parameters are missing
        """
        cache_key = self._get_cache_key("tickets", platform, filters)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        support_platform = SupportPlatform(platform.lower())
        filters = filters or {}

        if support_platform in [SupportPlatform.CSV, SupportPlatform.JSON]:
            if not file_path:
                raise ValueError(f"file_path required for {platform} source")
            tickets = self._load_tickets_from_file(file_path, support_platform)
        else:
            tickets = self._collect_tickets_from_api(support_platform, filters)

        # Apply filters
        if filters:
            tickets = self._filter_tickets(tickets, filters)

        self._set_cached(cache_key, tickets)
        logger.info(f"Aggregated {len(tickets)} support tickets from {platform}")
        return tickets

    def _load_tickets_from_file(
        self, file_path: str, platform: SupportPlatform
    ) -> List[SupportTicket]:
        """Load support tickets from CSV or JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if platform == SupportPlatform.CSV:
            df = pd.read_csv(file_path)
            tickets = []

            for _, row in df.iterrows():
                # Parse tags if string
                tags = row.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]

                tickets.append(
                    SupportTicket(
                        ticket_id=str(row["ticket_id"]),
                        created_at=pd.to_datetime(row["created_at"]),
                        status=str(row["status"]),
                        subject=str(row["subject"]),
                        description=str(row["description"]),
                        priority=(
                            str(row.get("priority"))
                            if pd.notna(row.get("priority"))
                            else None
                        ),
                        tags=tags,
                        sentiment=(
                            str(row.get("sentiment"))
                            if pd.notna(row.get("sentiment"))
                            else None
                        ),
                    )
                )

            return tickets

        else:  # JSON
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                data = [data]

            tickets = []
            for item in data:
                if isinstance(item.get("created_at"), str):
                    item["created_at"] = datetime.fromisoformat(
                        item["created_at"].replace("Z", "+00:00")
                    )
                tickets.append(SupportTicket(**item))

            return tickets

    def _collect_tickets_from_api(
        self, platform: SupportPlatform, filters: Dict[str, Any]
    ) -> List[SupportTicket]:
        """Collect support tickets from API."""
        if platform == SupportPlatform.ZENDESK:
            return self._collect_zendesk_tickets(filters)
        elif platform == SupportPlatform.INTERCOM:
            return self._collect_intercom_tickets(filters)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _collect_zendesk_tickets(self, filters: Dict[str, Any]) -> List[SupportTicket]:
        """Collect tickets from Zendesk API."""
        api_key = self.config.get("zendesk_api_key")
        subdomain = self.config.get("zendesk_subdomain")

        if not api_key or not subdomain:
            raise ValueError("zendesk_api_key and zendesk_subdomain required")

        url = f"https://{subdomain}.zendesk.com/api/v2/tickets"
        auth = (f"{self.config.get('zendesk_email')}/token", api_key)

        params = {}
        if "status" in filters:
            params["status"] = filters["status"]
        if "priority" in filters:
            params["priority"] = filters["priority"]

        response = requests.get(url, auth=auth, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        tickets = []

        for item in data.get("tickets", []):
            tickets.append(
                SupportTicket(
                    ticket_id=str(item["id"]),
                    created_at=datetime.fromisoformat(
                        item["created_at"].replace("Z", "+00:00")
                    ),
                    status=item["status"],
                    subject=item["subject"],
                    description=item["description"],
                    priority=item.get("priority"),
                    tags=item.get("tags", []),
                    sentiment=None,
                )
            )

        return tickets

    def _collect_intercom_tickets(self, filters: Dict[str, Any]) -> List[SupportTicket]:
        """Collect tickets from Intercom API."""
        api_key = self.config.get("intercom_api_key")
        if not api_key:
            raise ValueError("intercom_api_key not configured")

        url = "https://api.intercom.io/conversations"
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        tickets = []

        for conv in data.get("conversations", []):
            # Get first message as description
            description = ""
            if conv.get("conversation_parts", {}).get("conversation_parts"):
                first_part = conv["conversation_parts"]["conversation_parts"][0]
                description = first_part.get("body", "")

            tickets.append(
                SupportTicket(
                    ticket_id=str(conv["id"]),
                    created_at=datetime.fromtimestamp(conv["created_at"]),
                    status=conv["state"],
                    subject=conv.get("source", {}).get("subject", "No subject"),
                    description=description,
                    priority=conv.get("priority"),
                    tags=conv.get("tags", {}).get("tags", []),
                    sentiment=None,
                )
            )

        return tickets

    def _filter_tickets(
        self, tickets: List[SupportTicket], filters: Dict[str, Any]
    ) -> List[SupportTicket]:
        """Apply filters to ticket list."""
        filtered = tickets

        if "status" in filters:
            status_filter = filters["status"]
            if isinstance(status_filter, str):
                status_filter = [status_filter]
            filtered = [t for t in filtered if t.status in status_filter]

        if "priority" in filters:
            priority_filter = filters["priority"]
            if isinstance(priority_filter, str):
                priority_filter = [priority_filter]
            filtered = [
                t for t in filtered if t.priority and t.priority in priority_filter
            ]

        if "tags" in filters:
            required_tags = set(filters["tags"])
            filtered = [t for t in filtered if required_tags.intersection(set(t.tags))]

        if "date_range" in filters:
            start_date = datetime.fromisoformat(filters["date_range"][0])
            end_date = datetime.fromisoformat(filters["date_range"][1])
            filtered = [t for t in filtered if start_date <= t.created_at <= end_date]

        return filtered

    def calculate_nps(self, responses: List[SurveyResponse]) -> NPSScore:
        """
        Calculate Net Promoter Score from survey responses.

        NPS is calculated as: % Promoters - % Detractors
        - Promoters: rating 9-10
        - Passives: rating 7-8
        - Detractors: rating 0-6

        Args:
            responses: List of survey responses with ratings

        Returns:
            NPSScore object with calculated score and breakdown

        Raises:
            ValueError: If no valid ratings found
        """
        # Filter responses with ratings
        rated_responses = [r for r in responses if r.rating is not None]

        if not rated_responses:
            raise ValueError("No survey responses with ratings found")

        # Categorize responses
        promoters = sum(1 for r in rated_responses if r.rating >= 9)
        passives = sum(1 for r in rated_responses if 7 <= r.rating <= 8)
        detractors = sum(1 for r in rated_responses if r.rating <= 6)
        total = len(rated_responses)

        # Calculate NPS
        promoter_pct = (promoters / total) * 100
        detractor_pct = (detractors / total) * 100
        nps_score = promoter_pct - detractor_pct

        logger.info(
            f"NPS calculated: {nps_score:.1f} "
            f"(P:{promoters} Pa:{passives} D:{detractors} T:{total})"
        )

        return NPSScore(
            score=round(nps_score, 2),
            promoters=promoters,
            passives=passives,
            detractors=detractors,
            total_responses=total,
        )

    def export_feedback(
        self,
        feedback: List[Dict[str, Any]],
        format: str = "json",
        output_path: Optional[str] = None,
    ) -> str:
        """
        Export feedback data to specified format.

        Args:
            feedback: List of feedback dictionaries
            format: Export format (json, csv)
            output_path: Optional output file path

        Returns:
            Exported data as string or file path

        Raises:
            ValueError: If format is unsupported
        """
        if format.lower() == "json":
            # Convert to JSON string
            json_str = json.dumps(feedback, indent=2, default=str, ensure_ascii=False)

            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(json_str)
                logger.info(f"Feedback exported to {output_path}")
                return output_path
            else:
                return json_str

        elif format.lower() == "csv":
            # Convert to DataFrame
            df = pd.DataFrame(feedback)

            if output_path:
                df.to_csv(output_path, index=False, encoding="utf-8")
                logger.info(f"Feedback exported to {output_path}")
                return output_path
            else:
                return df.to_csv(index=False, encoding="utf-8")

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()
        logger.info("Cache cleared")
