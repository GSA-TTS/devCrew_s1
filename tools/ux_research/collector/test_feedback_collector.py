"""
Comprehensive test suite for Feedback Collector module.

Tests all feedback collection functionality including survey platforms,
heatmap data, support tickets, and NPS calculations.
Part of the devCrew_s1 UX Research Platform (TOOL-UX-001).
"""

import csv
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
import requests
from feedback_collector import (ClickEvent, FeedbackCollector, HeatmapData,
                                HeatmapPlatform, HoverEvent, NPSScore,
                                ScrollEvent, SupportPlatform, SupportTicket,
                                SurveyPlatform, SurveyResponse)
from pydantic import ValidationError


class TestDataModels:
    """Test data model validation and serialization."""

    def test_survey_response_valid(self):
        """Test valid survey response creation."""
        response = SurveyResponse(
            response_id="resp_123",
            timestamp=datetime.now(),
            respondent_id="user_456",
            answers={"q1": "answer1", "q2": "answer2"},
            rating=9,
            free_text="Great product!",
        )

        assert response.response_id == "resp_123"
        assert response.rating == 9
        assert len(response.answers) == 2

    def test_survey_response_rating_validation(self):
        """Test rating validation (0-10)."""
        with pytest.raises(ValidationError):
            SurveyResponse(response_id="resp_123", timestamp=datetime.now(), rating=11)

        with pytest.raises(ValidationError):
            SurveyResponse(response_id="resp_123", timestamp=datetime.now(), rating=-1)

    def test_click_event_valid(self):
        """Test click event creation."""
        event = ClickEvent(
            x=100.5, y=200.3, timestamp=datetime.now(), element="button#submit"
        )

        assert event.x == 100.5
        assert event.y == 200.3
        assert event.element == "button#submit"

    def test_scroll_event_validation(self):
        """Test scroll event depth validation."""
        event = ScrollEvent(
            depth_percent=75.5, timestamp=datetime.now(), viewport_height=1080
        )

        assert event.depth_percent == 75.5

        # Test bounds
        with pytest.raises(ValidationError):
            ScrollEvent(depth_percent=150, timestamp=datetime.now())

    def test_nps_score_validation(self):
        """Test NPS score validation."""
        nps = NPSScore(
            score=50.5, promoters=10, passives=5, detractors=3, total_responses=18
        )

        assert nps.score == 50.5
        assert nps.total_responses == 18

        # Test total validation
        with pytest.raises(ValidationError):
            NPSScore(
                score=50,
                promoters=10,
                passives=5,
                detractors=3,
                total_responses=20,  # Wrong total
            )

    def test_heatmap_data_valid(self):
        """Test heatmap data creation."""
        heatmap = HeatmapData(
            site_id="site_123",
            page_url="https://example.com/page",
            clicks=[ClickEvent(x=100, y=200, timestamp=datetime.now())],
            scrolls=[ScrollEvent(depth_percent=50, timestamp=datetime.now())],
            hovers=[],
        )

        assert heatmap.site_id == "site_123"
        assert len(heatmap.clicks) == 1
        assert len(heatmap.scrolls) == 1

    def test_support_ticket_valid(self):
        """Test support ticket creation."""
        ticket = SupportTicket(
            ticket_id="TKT-123",
            created_at=datetime.now(),
            status="open",
            subject="Bug report",
            description="Something is broken",
            priority="high",
            tags=["bug", "urgent"],
        )

        assert ticket.ticket_id == "TKT-123"
        assert ticket.priority == "high"
        assert len(ticket.tags) == 2


class TestFeedbackCollectorInit:
    """Test FeedbackCollector initialization."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        collector = FeedbackCollector()

        assert collector.config == {}
        assert collector.rate_limit_delay == 1.0
        assert collector.cache_enabled is True
        assert collector.cache_ttl == 3600

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = {
            "typeform_api_key": "test_key",
            "rate_limit_delay": 2.0,
            "cache_enabled": False,
            "cache_ttl": 7200,
        }
        collector = FeedbackCollector(config)

        assert collector.config["typeform_api_key"] == "test_key"
        assert collector.rate_limit_delay == 2.0
        assert collector.cache_enabled is False
        assert collector.cache_ttl == 7200


class TestSurveyCollection:
    """Test survey response collection."""

    def test_collect_from_csv(self, tmp_path):
        """Test collecting survey responses from CSV file."""
        # Create test CSV
        csv_file = tmp_path / "survey.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "response_id",
                    "timestamp",
                    "respondent_id",
                    "rating",
                    "free_text",
                    "q1",
                    "q2",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "response_id": "resp_1",
                    "timestamp": "2024-01-01T10:00:00",
                    "respondent_id": "user_1",
                    "rating": "9",
                    "free_text": "Great!",
                    "q1": "Yes",
                    "q2": "No",
                }
            )
            writer.writerow(
                {
                    "response_id": "resp_2",
                    "timestamp": "2024-01-01T11:00:00",
                    "respondent_id": "user_2",
                    "rating": "6",
                    "free_text": "Okay",
                    "q1": "No",
                    "q2": "Yes",
                }
            )

        collector = FeedbackCollector()
        responses = collector.collect_survey_responses(
            source="csv", file_path=str(csv_file)
        )

        assert len(responses) == 2
        assert responses[0].response_id == "resp_1"
        assert responses[0].rating == 9
        assert responses[0].answers["q1"] == "Yes"
        assert responses[1].rating == 6

    def test_collect_from_json(self, tmp_path):
        """Test collecting survey responses from JSON file."""
        # Create test JSON
        json_file = tmp_path / "survey.json"
        data = [
            {
                "response_id": "resp_1",
                "timestamp": "2024-01-01T10:00:00",
                "respondent_id": "user_1",
                "rating": 10,
                "free_text": "Excellent!",
                "answers": {"q1": "answer1"},
            },
            {
                "response_id": "resp_2",
                "timestamp": "2024-01-01T11:00:00",
                "respondent_id": "user_2",
                "rating": 7,
                "free_text": "Good",
                "answers": {"q1": "answer2"},
            },
        ]

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        collector = FeedbackCollector()
        responses = collector.collect_survey_responses(
            source="json", file_path=str(json_file)
        )

        assert len(responses) == 2
        assert responses[0].rating == 10
        assert responses[1].rating == 7

    def test_collect_from_csv_missing_file(self):
        """Test error handling for missing CSV file."""
        collector = FeedbackCollector()

        with pytest.raises(FileNotFoundError):
            collector.collect_survey_responses(
                source="csv", file_path="/nonexistent/file.csv"
            )

    def test_collect_requires_file_path_for_csv(self):
        """Test that file_path is required for CSV source."""
        collector = FeedbackCollector()

        with pytest.raises(ValueError, match="file_path required"):
            collector.collect_survey_responses(source="csv")

    @patch("feedback_collector.requests.get")
    def test_collect_from_typeform_api(self, mock_get):
        """Test collecting from TypeForm API."""
        # Mock API response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "items": [
                {
                    "response_id": "resp_1",
                    "submitted_at": "2024-01-01T10:00:00Z",
                    "respondent_id": "user_1",
                    "answers": [
                        {
                            "field": {"id": "field_1", "type": "opinion_scale"},
                            "number": 9,
                        },
                        {
                            "field": {"id": "field_2", "type": "short_text"},
                            "text": "Great product!",
                        },
                    ],
                }
            ]
        }
        mock_get.return_value = mock_response

        config = {"typeform_api_key": "test_key"}
        collector = FeedbackCollector(config)

        responses = collector.collect_survey_responses(
            source="typeform", survey_id="form_123"
        )

        assert len(responses) == 1
        assert responses[0].response_id == "resp_1"
        assert responses[0].rating == 9
        assert responses[0].free_text == "Great product!"

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "form_123" in call_args[0][0]

    @patch("feedback_collector.requests.get")
    def test_collect_from_surveymonkey_api(self, mock_get):
        """Test collecting from SurveyMonkey API."""
        # Mock API response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "resp_1",
                    "date_created": "2024-01-01T10:00:00Z",
                    "recipient_id": "user_1",
                    "pages": [
                        {
                            "questions": [
                                {"id": "q1", "answers": [{"row_id": "r1", "value": 8}]}
                            ]
                        }
                    ],
                }
            ]
        }
        mock_get.return_value = mock_response

        config = {"surveymonkey_api_key": "test_key"}
        collector = FeedbackCollector(config)

        responses = collector.collect_survey_responses(
            source="surveymonkey", survey_id="survey_123"
        )

        assert len(responses) == 1
        assert responses[0].response_id == "resp_1"
        assert responses[0].rating == 8

    def test_typeform_requires_api_key(self):
        """Test that TypeForm API requires API key."""
        collector = FeedbackCollector()

        with pytest.raises(ValueError, match="typeform_api_key not configured"):
            collector.collect_survey_responses(source="typeform", survey_id="form_123")

    def test_api_source_requires_survey_id(self):
        """Test that API sources require survey_id."""
        config = {"typeform_api_key": "test_key"}
        collector = FeedbackCollector(config)

        with pytest.raises(ValueError, match="survey_id required"):
            collector.collect_survey_responses(source="typeform")


class TestHeatmapCollection:
    """Test heatmap data collection."""

    def test_collect_from_json(self, tmp_path):
        """Test collecting heatmap data from JSON file."""
        # Create test JSON
        json_file = tmp_path / "heatmap.json"
        data = {
            "site_id": "site_123",
            "page_url": "https://example.com/page",
            "clicks": [
                {
                    "x": 100.5,
                    "y": 200.3,
                    "timestamp": "2024-01-01T10:00:00",
                    "element": "button",
                }
            ],
            "scrolls": [
                {
                    "depth_percent": 75.0,
                    "timestamp": "2024-01-01T10:01:00",
                    "viewport_height": 1080,
                }
            ],
            "hovers": [],
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        collector = FeedbackCollector()
        heatmap = collector.collect_heatmap_data(
            platform="json", site_id="site_123", file_path=str(json_file)
        )

        assert heatmap.site_id == "site_123"
        assert len(heatmap.clicks) == 1
        assert heatmap.clicks[0].x == 100.5
        assert len(heatmap.scrolls) == 1
        assert heatmap.scrolls[0].depth_percent == 75.0

    @patch("feedback_collector.requests.get")
    def test_collect_from_hotjar_api(self, mock_get):
        """Test collecting from Hotjar API."""
        # Mock API responses
        heatmaps_response = Mock()
        heatmaps_response.ok = True
        heatmaps_response.json.return_value = {
            "heatmaps": [{"id": "hm_1", "url": "https://example.com/page"}]
        }

        clicks_response = Mock()
        clicks_response.ok = True
        clicks_response.json.return_value = {
            "clicks": [
                {
                    "x": 150.0,
                    "y": 250.0,
                    "timestamp": "2024-01-01T10:00:00Z",
                    "element": "a.link",
                }
            ]
        }

        scrolls_response = Mock()
        scrolls_response.ok = True
        scrolls_response.json.return_value = {
            "scrolls": [
                {
                    "depth_percent": 50.0,
                    "timestamp": "2024-01-01T10:01:00Z",
                    "viewport_height": 768,
                }
            ]
        }

        mock_get.side_effect = [heatmaps_response, clicks_response, scrolls_response]

        config = {"hotjar_api_key": "test_key"}
        collector = FeedbackCollector(config)

        heatmap = collector.collect_heatmap_data(platform="hotjar", site_id="site_123")

        assert len(heatmap.clicks) == 1
        assert heatmap.clicks[0].x == 150.0
        assert len(heatmap.scrolls) == 1

    def test_json_source_requires_file_path(self):
        """Test that JSON source requires file_path."""
        collector = FeedbackCollector()

        with pytest.raises(ValueError, match="file_path required"):
            collector.collect_heatmap_data(platform="json", site_id="site_123")

    def test_hotjar_requires_api_key(self):
        """Test that Hotjar API requires API key."""
        collector = FeedbackCollector()

        with pytest.raises(ValueError, match="hotjar_api_key not configured"):
            collector.collect_heatmap_data(platform="hotjar", site_id="site_123")


class TestSupportTicketAggregation:
    """Test support ticket aggregation."""

    def test_aggregate_from_csv(self, tmp_path):
        """Test aggregating tickets from CSV file."""
        # Create test CSV
        csv_file = tmp_path / "tickets.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ticket_id",
                    "created_at",
                    "status",
                    "subject",
                    "description",
                    "priority",
                    "tags",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "ticket_id": "TKT-1",
                    "created_at": "2024-01-01T10:00:00",
                    "status": "open",
                    "subject": "Bug report",
                    "description": "Something broke",
                    "priority": "high",
                    "tags": "bug,urgent",
                }
            )
            writer.writerow(
                {
                    "ticket_id": "TKT-2",
                    "created_at": "2024-01-02T10:00:00",
                    "status": "closed",
                    "subject": "Feature request",
                    "description": "Need new feature",
                    "priority": "low",
                    "tags": "enhancement",
                }
            )

        collector = FeedbackCollector()
        tickets = collector.aggregate_support_tickets(
            platform="csv", file_path=str(csv_file)
        )

        assert len(tickets) == 2
        assert tickets[0].ticket_id == "TKT-1"
        assert tickets[0].priority == "high"
        assert "bug" in tickets[0].tags
        assert tickets[1].status == "closed"

    def test_aggregate_from_json(self, tmp_path):
        """Test aggregating tickets from JSON file."""
        # Create test JSON
        json_file = tmp_path / "tickets.json"
        data = [
            {
                "ticket_id": "TKT-1",
                "created_at": "2024-01-01T10:00:00",
                "status": "open",
                "subject": "Bug report",
                "description": "Something broke",
                "priority": "high",
                "tags": ["bug", "urgent"],
            }
        ]

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        collector = FeedbackCollector()
        tickets = collector.aggregate_support_tickets(
            platform="json", file_path=str(json_file)
        )

        assert len(tickets) == 1
        assert tickets[0].ticket_id == "TKT-1"

    @patch("feedback_collector.requests.get")
    def test_aggregate_from_zendesk_api(self, mock_get):
        """Test aggregating from Zendesk API."""
        # Mock API response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "tickets": [
                {
                    "id": 12345,
                    "created_at": "2024-01-01T10:00:00Z",
                    "status": "open",
                    "subject": "Help needed",
                    "description": "I need assistance",
                    "priority": "normal",
                    "tags": ["support"],
                }
            ]
        }
        mock_get.return_value = mock_response

        config = {
            "zendesk_api_key": "test_key",
            "zendesk_subdomain": "test",
            "zendesk_email": "test@example.com",
        }
        collector = FeedbackCollector(config)

        tickets = collector.aggregate_support_tickets(platform="zendesk")

        assert len(tickets) == 1
        assert tickets[0].ticket_id == "12345"
        assert tickets[0].status == "open"

    @patch("feedback_collector.requests.get")
    def test_aggregate_from_intercom_api(self, mock_get):
        """Test aggregating from Intercom API."""
        # Mock API response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "conversations": [
                {
                    "id": "conv_123",
                    "created_at": 1704106800,  # Unix timestamp
                    "state": "open",
                    "source": {"subject": "Question"},
                    "conversation_parts": {
                        "conversation_parts": [{"body": "I have a question"}]
                    },
                    "priority": "normal",
                    "tags": {"tags": ["question"]},
                }
            ]
        }
        mock_get.return_value = mock_response

        config = {"intercom_api_key": "test_key"}
        collector = FeedbackCollector(config)

        tickets = collector.aggregate_support_tickets(platform="intercom")

        assert len(tickets) == 1
        assert tickets[0].ticket_id == "conv_123"

    def test_filter_tickets_by_status(self, tmp_path):
        """Test filtering tickets by status."""
        # Create test data
        csv_file = tmp_path / "tickets.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ticket_id",
                    "created_at",
                    "status",
                    "subject",
                    "description",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "ticket_id": "TKT-1",
                    "created_at": "2024-01-01T10:00:00",
                    "status": "open",
                    "subject": "Issue 1",
                    "description": "Description 1",
                }
            )
            writer.writerow(
                {
                    "ticket_id": "TKT-2",
                    "created_at": "2024-01-02T10:00:00",
                    "status": "closed",
                    "subject": "Issue 2",
                    "description": "Description 2",
                }
            )

        collector = FeedbackCollector()
        tickets = collector.aggregate_support_tickets(
            platform="csv", file_path=str(csv_file), filters={"status": "open"}
        )

        assert len(tickets) == 1
        assert tickets[0].status == "open"

    def test_filter_tickets_by_tags(self, tmp_path):
        """Test filtering tickets by tags."""
        # Create test data
        csv_file = tmp_path / "tickets.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ticket_id",
                    "created_at",
                    "status",
                    "subject",
                    "description",
                    "tags",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "ticket_id": "TKT-1",
                    "created_at": "2024-01-01T10:00:00",
                    "status": "open",
                    "subject": "Issue 1",
                    "description": "Description 1",
                    "tags": "bug,urgent",
                }
            )
            writer.writerow(
                {
                    "ticket_id": "TKT-2",
                    "created_at": "2024-01-02T10:00:00",
                    "status": "open",
                    "subject": "Issue 2",
                    "description": "Description 2",
                    "tags": "feature",
                }
            )

        collector = FeedbackCollector()
        tickets = collector.aggregate_support_tickets(
            platform="csv", file_path=str(csv_file), filters={"tags": ["bug"]}
        )

        assert len(tickets) == 1
        assert "bug" in tickets[0].tags


class TestNPSCalculation:
    """Test NPS score calculation."""

    def test_calculate_nps_all_promoters(self):
        """Test NPS with all promoters."""
        responses = [
            SurveyResponse(
                response_id=f"resp_{i}",
                timestamp=datetime.now(),
                rating=9 if i % 2 == 0 else 10,
            )
            for i in range(10)
        ]

        collector = FeedbackCollector()
        nps = collector.calculate_nps(responses)

        assert nps.score == 100.0
        assert nps.promoters == 10
        assert nps.passives == 0
        assert nps.detractors == 0

    def test_calculate_nps_all_detractors(self):
        """Test NPS with all detractors."""
        responses = [
            SurveyResponse(
                response_id=f"resp_{i}", timestamp=datetime.now(), rating=i % 7  # 0-6
            )
            for i in range(10)
        ]

        collector = FeedbackCollector()
        nps = collector.calculate_nps(responses)

        assert nps.score == -100.0
        assert nps.promoters == 0
        assert nps.passives == 0
        assert nps.detractors == 10

    def test_calculate_nps_mixed(self):
        """Test NPS with mixed responses."""
        responses = [
            # 3 promoters (9-10)
            SurveyResponse(response_id="resp_1", timestamp=datetime.now(), rating=9),
            SurveyResponse(response_id="resp_2", timestamp=datetime.now(), rating=10),
            SurveyResponse(response_id="resp_3", timestamp=datetime.now(), rating=9),
            # 2 passives (7-8)
            SurveyResponse(response_id="resp_4", timestamp=datetime.now(), rating=7),
            SurveyResponse(response_id="resp_5", timestamp=datetime.now(), rating=8),
            # 5 detractors (0-6)
            SurveyResponse(response_id="resp_6", timestamp=datetime.now(), rating=6),
            SurveyResponse(response_id="resp_7", timestamp=datetime.now(), rating=5),
            SurveyResponse(response_id="resp_8", timestamp=datetime.now(), rating=4),
            SurveyResponse(response_id="resp_9", timestamp=datetime.now(), rating=3),
            SurveyResponse(response_id="resp_10", timestamp=datetime.now(), rating=0),
        ]

        collector = FeedbackCollector()
        nps = collector.calculate_nps(responses)

        # NPS = (3/10 * 100) - (5/10 * 100) = 30 - 50 = -20
        assert nps.score == -20.0
        assert nps.promoters == 3
        assert nps.passives == 2
        assert nps.detractors == 5
        assert nps.total_responses == 10

    def test_calculate_nps_no_ratings(self):
        """Test NPS calculation with no ratings."""
        responses = [
            SurveyResponse(
                response_id="resp_1", timestamp=datetime.now(), free_text="No rating"
            )
        ]

        collector = FeedbackCollector()

        with pytest.raises(ValueError, match="No survey responses with ratings"):
            collector.calculate_nps(responses)

    def test_calculate_nps_filters_none_ratings(self):
        """Test that NPS calculation filters out None ratings."""
        responses = [
            SurveyResponse(response_id="resp_1", timestamp=datetime.now(), rating=9),
            SurveyResponse(response_id="resp_2", timestamp=datetime.now(), rating=None),
            SurveyResponse(response_id="resp_3", timestamp=datetime.now(), rating=10),
        ]

        collector = FeedbackCollector()
        nps = collector.calculate_nps(responses)

        assert nps.total_responses == 2
        assert nps.score == 100.0


class TestExportFeedback:
    """Test feedback data export."""

    def test_export_to_json_string(self):
        """Test exporting to JSON string."""
        feedback = [
            {"id": 1, "type": "survey", "rating": 9, "text": "Great!"},
            {"id": 2, "type": "ticket", "priority": "high", "status": "open"},
        ]

        collector = FeedbackCollector()
        result = collector.export_feedback(feedback, format="json")

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["rating"] == 9

    def test_export_to_json_file(self, tmp_path):
        """Test exporting to JSON file."""
        feedback = [{"id": 1, "data": "test1"}, {"id": 2, "data": "test2"}]

        output_file = tmp_path / "export.json"
        collector = FeedbackCollector()
        result = collector.export_feedback(
            feedback, format="json", output_path=str(output_file)
        )

        assert result == str(output_file)
        assert output_file.exists()

        # Verify content
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 2

    def test_export_to_csv_string(self):
        """Test exporting to CSV string."""
        feedback = [
            {"id": 1, "name": "Item 1", "value": 100},
            {"id": 2, "name": "Item 2", "value": 200},
        ]

        collector = FeedbackCollector()
        result = collector.export_feedback(feedback, format="csv")

        assert isinstance(result, str)
        assert "id,name,value" in result
        assert "Item 1" in result

    def test_export_to_csv_file(self, tmp_path):
        """Test exporting to CSV file."""
        feedback = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

        output_file = tmp_path / "export.csv"
        collector = FeedbackCollector()
        result = collector.export_feedback(
            feedback, format="csv", output_path=str(output_file)
        )

        assert result == str(output_file)
        assert output_file.exists()

        # Verify content
        df = pd.read_csv(output_file)
        assert len(df) == 2

    def test_export_unsupported_format(self):
        """Test error handling for unsupported format."""
        feedback = [{"id": 1}]
        collector = FeedbackCollector()

        with pytest.raises(ValueError, match="Unsupported export format"):
            collector.export_feedback(feedback, format="xml")


class TestCaching:
    """Test response caching functionality."""

    def test_cache_enabled_by_default(self):
        """Test that caching is enabled by default."""
        collector = FeedbackCollector()
        assert collector.cache_enabled is True

    def test_cache_disabled_option(self):
        """Test disabling cache."""
        config = {"cache_enabled": False}
        collector = FeedbackCollector(config)
        assert collector.cache_enabled is False

    def test_cache_stores_survey_responses(self, tmp_path):
        """Test that survey responses are cached."""
        # Create test file
        csv_file = tmp_path / "survey.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["response_id", "timestamp", "rating"]
            )
            writer.writeheader()
            writer.writerow(
                {
                    "response_id": "resp_1",
                    "timestamp": "2024-01-01T10:00:00",
                    "rating": "9",
                }
            )

        collector = FeedbackCollector()

        # First call
        responses1 = collector.collect_survey_responses(
            source="csv", file_path=str(csv_file)
        )

        # Second call should use cache
        responses2 = collector.collect_survey_responses(
            source="csv", file_path=str(csv_file)
        )

        assert responses1 == responses2
        assert len(collector._cache) > 0

    def test_clear_cache(self):
        """Test clearing the cache."""
        collector = FeedbackCollector()
        collector._cache["test_key"] = ("value", datetime.now())

        assert len(collector._cache) > 0

        collector.clear_cache()
        assert len(collector._cache) == 0

    def test_cache_expiry(self):
        """Test that cache entries expire."""
        config = {"cache_ttl": 1}  # 1 second TTL
        collector = FeedbackCollector(config)

        # Set a cache entry with old timestamp
        old_time = datetime.now() - timedelta(seconds=2)
        collector._cache["test_key"] = ("value", old_time)

        # Should return None for expired cache
        result = collector._get_cached("test_key")
        assert result is None
        assert "test_key" not in collector._cache


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_survey_platform(self):
        """Test handling of invalid survey platform."""
        collector = FeedbackCollector()

        with pytest.raises(ValueError):
            collector.collect_survey_responses(
                source="invalid_platform", survey_id="123"
            )

    def test_invalid_heatmap_platform(self):
        """Test handling of invalid heatmap platform."""
        collector = FeedbackCollector()

        with pytest.raises(ValueError):
            collector.collect_heatmap_data(platform="invalid_platform", site_id="123")

    def test_invalid_support_platform(self):
        """Test handling of invalid support platform."""
        collector = FeedbackCollector()

        with pytest.raises(ValueError):
            collector.aggregate_support_tickets(platform="invalid_platform")

    @patch("feedback_collector.requests.get")
    def test_api_error_handling(self, mock_get):
        """Test handling of API errors."""
        # Mock failed API call
        mock_get.side_effect = requests.HTTPError("API Error")

        config = {"typeform_api_key": "test_key"}
        collector = FeedbackCollector(config)

        with pytest.raises(requests.HTTPError):
            collector.collect_survey_responses(source="typeform", survey_id="form_123")

    def test_malformed_json_file(self, tmp_path):
        """Test handling of malformed JSON file."""
        json_file = tmp_path / "bad.json"
        with open(json_file, "w", encoding="utf-8") as f:
            f.write("not valid json{")

        collector = FeedbackCollector()

        with pytest.raises(json.JSONDecodeError):
            collector.collect_survey_responses(source="json", file_path=str(json_file))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
