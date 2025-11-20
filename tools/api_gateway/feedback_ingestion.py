"""
Issue #41: Feedback Ingestion Module
Implements multi-format feedback collection and processing.
"""

import csv
import json
from datetime import datetime
from enum import Enum
from io import StringIO
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class FeedbackSource(str, Enum):
    """Feedback source types."""

    API = "api"
    WEB_FORM = "web_form"
    EMAIL = "email"
    CSV_UPLOAD = "csv_upload"
    JSON_UPLOAD = "json_upload"
    SURVEY = "survey"
    SUPPORT_TICKET = "support_ticket"


class FeedbackType(str, Enum):
    """Feedback types."""

    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GENERAL_FEEDBACK = "general_feedback"
    COMPLAINT = "complaint"
    PRAISE = "praise"
    QUESTION = "question"


class FeedbackStatus(str, Enum):
    """Feedback processing status."""

    RECEIVED = "received"
    VALIDATED = "validated"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class FeedbackBase(BaseModel):
    """Base feedback schema."""

    customer_id: str = Field(..., min_length=1)
    feedback_type: FeedbackType
    subject: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: FeedbackSource
    rating: Optional[int] = Field(None, ge=1, le=5)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("rating")
    def validate_rating(cls, v):
        """Validate rating is between 1 and 5."""
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


class FeedbackCreate(FeedbackBase):
    """Feedback creation schema."""

    pass


class FeedbackResponse(FeedbackBase):
    """Feedback response schema."""

    feedback_id: str
    status: FeedbackStatus
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class FeedbackBatch(BaseModel):
    """Batch feedback upload."""

    feedbacks: List[FeedbackCreate]
    source: FeedbackSource


class FeedbackIngestionResult(BaseModel):
    """Feedback ingestion result."""

    total: int
    successful: int
    failed: int
    feedback_ids: List[str]
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class FeedbackProcessor:
    """Process and validate feedback data."""

    def __init__(self):
        """Initialize feedback processor."""
        self.feedbacks: Dict[str, Dict[str, Any]] = {}

    def generate_feedback_id(self, customer_id: str) -> str:
        """
        Generate unique feedback ID.

        Args:
            customer_id: Customer ID

        Returns:
            Feedback ID
        """
        import hashlib
        from time import time

        timestamp = str(time())
        hash_input = f"{customer_id}_{timestamp}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:12].upper()
        return f"FB_{hash_value}"

    def ingest_feedback(self, feedback: FeedbackCreate) -> FeedbackResponse:
        """
        Ingest a single feedback.

        Args:
            feedback: Feedback data

        Returns:
            Feedback response

        Raises:
            ValueError: If feedback validation fails
        """
        # Generate feedback ID
        feedback_id = self.generate_feedback_id(feedback.customer_id)

        # Create feedback response
        feedback_response = FeedbackResponse(
            feedback_id=feedback_id,
            customer_id=feedback.customer_id,
            feedback_type=feedback.feedback_type,
            subject=feedback.subject,
            content=feedback.content,
            source=feedback.source,
            rating=feedback.rating,
            metadata=feedback.metadata,
            status=FeedbackStatus.RECEIVED,
            created_at=datetime.utcnow(),
        )

        # Store feedback
        self.feedbacks[feedback_id] = feedback_response.model_dump()

        return feedback_response

    def ingest_batch(self, batch: FeedbackBatch) -> FeedbackIngestionResult:
        """
        Ingest batch of feedbacks.

        Args:
            batch: Batch of feedbacks

        Returns:
            Ingestion result
        """
        result = FeedbackIngestionResult(
            total=len(batch.feedbacks), successful=0, failed=0, feedback_ids=[]
        )

        for feedback in batch.feedbacks:
            try:
                response = self.ingest_feedback(feedback)
                result.successful += 1
                result.feedback_ids.append(response.feedback_id)
            except Exception as e:
                result.failed += 1
                result.errors.append(
                    {
                        "customer_id": feedback.customer_id,
                        "error": str(e),
                    }
                )

        return result

    def get_feedback(self, feedback_id: str) -> Optional[FeedbackResponse]:
        """
        Get feedback by ID.

        Args:
            feedback_id: Feedback ID

        Returns:
            Feedback response or None
        """
        feedback_data = self.feedbacks.get(feedback_id)
        if feedback_data:
            return FeedbackResponse(**feedback_data)
        return None

    def list_feedbacks(
        self,
        customer_id: Optional[str] = None,
        status: Optional[FeedbackStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FeedbackResponse]:
        """
        List feedbacks with filters.

        Args:
            customer_id: Filter by customer ID
            status: Filter by status
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of feedbacks
        """
        feedbacks = []

        for feedback_data in self.feedbacks.values():
            if customer_id and feedback_data.get("customer_id") != customer_id:
                continue

            if status and feedback_data.get("status") != status:
                continue

            feedbacks.append(FeedbackResponse(**feedback_data))

        return feedbacks[skip : skip + limit]

    def update_status(
        self, feedback_id: str, status: FeedbackStatus
    ) -> Optional[FeedbackResponse]:
        """
        Update feedback status.

        Args:
            feedback_id: Feedback ID
            status: New status

        Returns:
            Updated feedback response or None
        """
        feedback_data = self.feedbacks.get(feedback_id)
        if not feedback_data:
            return None

        feedback_data["status"] = status

        if status == FeedbackStatus.PROCESSED:
            feedback_data["processed_at"] = datetime.utcnow()

        self.feedbacks[feedback_id] = feedback_data
        return FeedbackResponse(**feedback_data)


class FeedbackParser:
    """Parse feedback from various formats."""

    @staticmethod
    def parse_json(json_data: str) -> List[FeedbackCreate]:
        """
        Parse feedback from JSON.

        Args:
            json_data: JSON string

        Returns:
            List of feedback objects

        Raises:
            ValueError: If JSON is invalid
        """
        try:
            data = json.loads(json_data)

            # Handle single feedback
            if isinstance(data, dict):
                return [FeedbackCreate(**data)]

            # Handle list of feedbacks
            if isinstance(data, list):
                return [FeedbackCreate(**item) for item in data]

            raise ValueError("Invalid JSON structure")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

    @staticmethod
    def parse_csv(csv_data: str) -> List[FeedbackCreate]:
        """
        Parse feedback from CSV.

        Args:
            csv_data: CSV string

        Returns:
            List of feedback objects

        Raises:
            ValueError: If CSV is invalid
        """
        feedbacks = []
        csv_file = StringIO(csv_data)
        reader = csv.DictReader(csv_file)

        required_fields = [
            "customer_id",
            "feedback_type",
            "subject",
            "content",
            "source",
        ]

        for row_num, row in enumerate(reader, start=1):
            try:
                # Check required fields
                missing_fields = [f for f in required_fields if f not in row]
                if missing_fields:
                    raise ValueError(
                        f"Missing required fields: {', '.join(missing_fields)}"
                    )

                # Parse metadata if present
                metadata = {}
                if "metadata" in row and row["metadata"]:
                    try:
                        metadata = json.loads(row["metadata"])
                    except json.JSONDecodeError:
                        pass

                # Parse rating
                rating = None
                if "rating" in row and row["rating"]:
                    try:
                        rating = int(row["rating"])
                    except ValueError:
                        pass

                feedback = FeedbackCreate(
                    customer_id=row["customer_id"],
                    feedback_type=FeedbackType(row["feedback_type"]),
                    subject=row["subject"],
                    content=row["content"],
                    source=FeedbackSource(row["source"]),
                    rating=rating,
                    metadata=metadata,
                )

                feedbacks.append(feedback)
            except Exception as e:
                raise ValueError(f"Error parsing row {row_num}: {str(e)}")

        return feedbacks

    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> List[str]:
        """
        Validate feedback data schema.

        Args:
            data: Feedback data

        Returns:
            List of validation errors
        """
        errors = []

        required_fields = [
            "customer_id",
            "feedback_type",
            "subject",
            "content",
            "source",
        ]

        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate feedback_type
        if "feedback_type" in data:
            try:
                FeedbackType(data["feedback_type"])
            except ValueError:
                errors.append(
                    f"Invalid feedback_type: {data['feedback_type']}"
                )

        # Validate source
        if "source" in data:
            try:
                FeedbackSource(data["source"])
            except ValueError:
                errors.append(f"Invalid source: {data['source']}")

        # Validate rating
        if "rating" in data and data["rating"] is not None:
            try:
                rating = int(data["rating"])
                if rating < 1 or rating > 5:
                    errors.append("Rating must be between 1 and 5")
            except (ValueError, TypeError):
                errors.append("Rating must be an integer")

        return errors


class FeedbackCleaner:
    """Clean and normalize feedback data."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text content.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove null bytes
        text = text.replace("\x00", "")

        return text.strip()

    @staticmethod
    def normalize_feedback(feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize feedback data.

        Args:
            feedback: Feedback data

        Returns:
            Normalized feedback data
        """
        normalized = feedback.copy()

        # Clean text fields
        if "subject" in normalized:
            normalized["subject"] = FeedbackCleaner.clean_text(
                normalized["subject"]
            )

        if "content" in normalized:
            normalized["content"] = FeedbackCleaner.clean_text(
                normalized["content"]
            )

        # Normalize customer_id
        if "customer_id" in normalized:
            normalized["customer_id"] = normalized["customer_id"].strip()

        return normalized


class FeedbackDeduplicator:
    """Deduplicate feedback data."""

    def __init__(self):
        """Initialize deduplicator."""
        self.seen_hashes: set = set()

    def generate_hash(self, feedback: FeedbackCreate) -> str:
        """
        Generate hash for feedback.

        Args:
            feedback: Feedback object

        Returns:
            Hash string
        """
        import hashlib

        content = f"{feedback.customer_id}_{feedback.subject}_{feedback.content}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_duplicate(self, feedback: FeedbackCreate) -> bool:
        """
        Check if feedback is duplicate.

        Args:
            feedback: Feedback object

        Returns:
            True if duplicate, False otherwise
        """
        feedback_hash = self.generate_hash(feedback)
        if feedback_hash in self.seen_hashes:
            return True

        self.seen_hashes.add(feedback_hash)
        return False

    def filter_duplicates(
        self, feedbacks: List[FeedbackCreate]
    ) -> List[FeedbackCreate]:
        """
        Filter duplicate feedbacks.

        Args:
            feedbacks: List of feedbacks

        Returns:
            List of unique feedbacks
        """
        unique_feedbacks = []

        for feedback in feedbacks:
            if not self.is_duplicate(feedback):
                unique_feedbacks.append(feedback)

        return unique_feedbacks


# Global instances
feedback_processor = FeedbackProcessor()
feedback_parser = FeedbackParser()
feedback_cleaner = FeedbackCleaner()
feedback_deduplicator = FeedbackDeduplicator()
