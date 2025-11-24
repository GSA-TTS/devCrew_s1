"""
Delivery Tracker for Communication Platform.

Tracks notification delivery status with retry logic, dead letter queue
management, and comprehensive metrics reporting. Supports exponential backoff
retry strategy and maintains delivery history with 90+ day retention.

Components:
    - DeliveryStatus: Enum for delivery states
    - DeliveryRecord: Pydantic model for delivery records
    - RetryPolicy: Configuration for retry behavior
    - DeliveryTracker: Main tracking class with PostgreSQL and Redis

Features:
    - Exponential backoff retry (1s, 2s, 4s)
    - Dead letter queue for permanent failures
    - Delivery metrics and analytics
    - Webhook callbacks for confirmations
    - Alert on repeated failures
    - Export delivery history (CSV, JSON)
"""

import csv
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import psycopg2
import redis
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeliveryStatus(str, Enum):
    """Delivery status enumeration."""

    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class DeliveryRecord(BaseModel):
    """
    Delivery record model.

    Attributes:
        notification_id: Unique notification identifier
        channel: Delivery channel (slack, email, teams, pagerduty)
        status: Current delivery status
        recipient: Recipient address/ID
        message_content: Message content (truncated for storage)
        retry_count: Number of retry attempts
        last_error: Last error message if any
        queued_at: Time notification was queued
        sent_at: Time notification was sent
        delivered_at: Time notification was delivered
        failed_at: Time notification permanently failed
        metadata: Additional metadata
    """

    notification_id: str = Field(..., min_length=1, max_length=255)
    channel: str = Field(..., min_length=1, max_length=50)
    status: DeliveryStatus = Field(default=DeliveryStatus.QUEUED)
    recipient: str = Field(..., min_length=1, max_length=255)
    message_content: Optional[str] = Field(default=None, max_length=2000)
    retry_count: int = Field(default=0, ge=0)
    last_error: Optional[str] = Field(default=None, max_length=500)
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        """Validate channel is supported."""
        allowed = ["slack", "email", "teams", "pagerduty", "sms", "webhook"]
        if v.lower() not in allowed:
            raise ValueError(f"Channel must be one of {allowed}")
        return v.lower()


class RetryPolicy(BaseModel):
    """
    Retry policy configuration.

    Attributes:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retry_on_statuses: HTTP status codes to retry on
        enable_jitter: Add random jitter to delays
    """

    max_retries: int = Field(default=3, ge=1, le=10)
    initial_delay: float = Field(default=1.0, gt=0)
    max_delay: float = Field(default=60.0, gt=0)
    exponential_base: float = Field(default=2.0, gt=1)
    retry_on_statuses: List[int] = Field(
        default_factory=lambda: [408, 429, 500, 502, 503, 504]
    )
    enable_jitter: bool = Field(default=True)

    def get_delay(self, retry_count: int) -> float:
        """
        Calculate delay for given retry count.

        Args:
            retry_count: Current retry attempt number

        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.exponential_base**retry_count), self.max_delay
        )
        if self.enable_jitter:
            import random

            delay = delay * (0.5 + random.random())
        return delay


class DeliveryTracker:
    """
    Track notification delivery with retry logic.

    Manages delivery tracking, retry queues, dead letter queue, and metrics
    collection using PostgreSQL for persistent storage and Redis for
    retry queue management.
    """

    def __init__(
        self,
        db_config: Dict[str, Any],
        redis_config: Dict[str, Any],
        retry_policy: Optional[RetryPolicy] = None,
        webhook_callback: Optional[Callable[[str, str], None]] = None,
        alert_callback: Optional[Callable[[str, str], None]] = None,
    ):
        """
        Initialize DeliveryTracker.

        Args:
            db_config: PostgreSQL configuration
            redis_config: Redis configuration
            retry_policy: Retry policy configuration
            webhook_callback: Callback for delivery confirmations
            alert_callback: Callback for repeated failures

        Raises:
            ConnectionError: If unable to connect to databases
        """
        self.db_config = db_config
        self.redis_config = redis_config
        self.retry_policy = retry_policy or RetryPolicy()
        self.webhook_callback = webhook_callback
        self.alert_callback = alert_callback

        # Initialize connections
        self._init_postgres()
        self._init_redis()

        logger.info("DeliveryTracker initialized successfully")

    def _init_postgres(self) -> None:
        """Initialize PostgreSQL connection and create tables."""
        try:
            self.db_conn = psycopg2.connect(**self.db_config)
            self._create_tables()
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise ConnectionError(f"PostgreSQL connection failed: {e}")

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config.get("host", "localhost"),
                port=self.redis_config.get("port", 6379),
                db=self.redis_config.get("db", 0),
                password=self.redis_config.get("password"),
                decode_responses=True,
            )
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS delivery_log (
            id SERIAL PRIMARY KEY,
            notification_id VARCHAR(255) NOT NULL,
            channel VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL,
            recipient VARCHAR(255) NOT NULL,
            message_content TEXT,
            retry_count INTEGER DEFAULT 0,
            last_error TEXT,
            queued_at TIMESTAMP NOT NULL,
            sent_at TIMESTAMP,
            delivered_at TIMESTAMP,
            failed_at TIMESTAMP,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_notification_id (notification_id),
            INDEX idx_status (status),
            INDEX idx_channel (channel),
            INDEX idx_queued_at (queued_at)
        );

        CREATE TABLE IF NOT EXISTS dead_letter_queue (
            id SERIAL PRIMARY KEY,
            notification_id VARCHAR(255) NOT NULL,
            channel VARCHAR(50) NOT NULL,
            recipient VARCHAR(255) NOT NULL,
            message_content TEXT,
            retry_count INTEGER NOT NULL,
            last_error TEXT,
            failed_at TIMESTAMP NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_dlq_notification_id (notification_id),
            INDEX idx_dlq_channel (channel)
        );

        CREATE TABLE IF NOT EXISTS delivery_metrics (
            id SERIAL PRIMARY KEY,
            metric_date DATE NOT NULL,
            channel VARCHAR(50) NOT NULL,
            total_sent INTEGER DEFAULT 0,
            total_delivered INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0,
            total_retries INTEGER DEFAULT 0,
            avg_latency_ms FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(metric_date, channel)
        );
        """
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                self.db_conn.commit()
            logger.info("Database tables created successfully")
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Failed to create tables: {e}")
            raise

    def track_delivery(
        self,
        notification_id: str,
        channel: str,
        status: str,
        recipient: Optional[str] = None,
        message_content: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Track delivery status for a notification.

        Args:
            notification_id: Unique notification identifier
            channel: Delivery channel
            status: Delivery status
            recipient: Recipient address
            message_content: Message content (truncated)
            error: Error message if failed
            metadata: Additional metadata

        Returns:
            True if tracking successful, False otherwise
        """
        try:
            # Get current record if exists
            current = self._get_record(notification_id, channel)

            if current:
                # Update existing record
                return self._update_record(
                    notification_id=notification_id,
                    channel=channel,
                    status=status,
                    error=error,
                    metadata=metadata,
                )
            else:
                # Create new record
                record = DeliveryRecord(
                    notification_id=notification_id,
                    channel=channel,
                    status=DeliveryStatus(status),
                    recipient=recipient or "unknown",
                    message_content=(
                        message_content[:2000] if message_content else None
                    ),  # noqa: E501
                    last_error=error[:500] if error else None,
                    metadata=metadata or {},
                )
                return self._insert_record(record)

        except Exception as e:
            logger.error(f"Failed to track delivery: {e}")
            return False

    def _get_record(
        self, notification_id: str, channel: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing delivery record."""
        query = """
        SELECT * FROM delivery_log
        WHERE notification_id = %s AND channel = %s
        ORDER BY created_at DESC LIMIT 1
        """
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (notification_id, channel))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Failed to get record: {e}")
            return None

    def _insert_record(self, record: DeliveryRecord) -> bool:
        """Insert new delivery record."""
        query = """
        INSERT INTO delivery_log (
            notification_id, channel, status, recipient, message_content,
            retry_count, last_error, queued_at, sent_at, delivered_at,
            failed_at, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        record.notification_id,
                        record.channel,
                        record.status.value,
                        record.recipient,
                        record.message_content,
                        record.retry_count,
                        record.last_error,
                        record.queued_at,
                        record.sent_at,
                        record.delivered_at,
                        record.failed_at,
                        json.dumps(record.metadata),
                    ),
                )
                self.db_conn.commit()
            return True
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Failed to insert record: {e}")
            return False

    def _update_record(
        self,
        notification_id: str,
        channel: str,
        status: str,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update existing delivery record."""
        status_enum = DeliveryStatus(status)
        timestamp_field = None
        timestamp_value = datetime.utcnow()

        if status_enum == DeliveryStatus.SENT:
            timestamp_field = "sent_at"
        elif status_enum == DeliveryStatus.DELIVERED:
            timestamp_field = "delivered_at"
        elif status_enum == DeliveryStatus.FAILED:
            timestamp_field = "failed_at"

        # Build update query dynamically
        updates = ["status = %s", "updated_at = CURRENT_TIMESTAMP"]
        params: List[Any] = [status]

        if timestamp_field:
            updates.append(f"{timestamp_field} = %s")
            params.append(timestamp_value)

        if error:
            updates.append("last_error = %s")
            params.append(error[:500])

        if status_enum == DeliveryStatus.RETRYING:
            updates.append("retry_count = retry_count + 1")

        if metadata:
            updates.append("metadata = %s")
            params.append(json.dumps(metadata))

        params.extend([notification_id, channel])

        # Dynamic query with controlled column names (not user input)
        query = f"""
        UPDATE delivery_log
        SET {', '.join(updates)}
        WHERE notification_id = %s AND channel = %s
        """  # nosec B608 - Column names are controlled, not user input

        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(query, params)
                self.db_conn.commit()

            # Trigger webhook callback for delivered status
            if status_enum == DeliveryStatus.DELIVERED and self.webhook_callback:
                try:
                    self.webhook_callback(notification_id, channel)
                except Exception as e:
                    logger.error(f"Webhook callback failed: {e}")

            # Check for repeated failures and alert
            if status_enum == DeliveryStatus.FAILED:
                self._check_repeated_failures(notification_id, channel)

            return True
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Failed to update record: {e}")
            return False

    def get_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Get delivery status for a notification.

        Args:
            notification_id: Notification identifier

        Returns:
            Dictionary with status information per channel
        """
        query = """
        SELECT channel, status, retry_count, last_error,
               queued_at, sent_at, delivered_at, failed_at
        FROM delivery_log
        WHERE notification_id = %s
        ORDER BY created_at DESC
        """
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (notification_id,))
                results = cursor.fetchall()

            if not results:
                return {
                    "notification_id": notification_id,
                    "channels": {},
                    "overall_status": "not_found",
                }

            channels = {}
            for row in results:
                channels[row["channel"]] = {
                    "status": row["status"],
                    "retry_count": row["retry_count"],
                    "last_error": row["last_error"],
                    "queued_at": (
                        row["queued_at"].isoformat() if row["queued_at"] else None
                    ),  # noqa: E501
                    "sent_at": (
                        row["sent_at"].isoformat() if row["sent_at"] else None
                    ),  # noqa: E501
                    "delivered_at": (
                        row["delivered_at"].isoformat() if row["delivered_at"] else None
                    ),  # noqa: E501
                    "failed_at": (
                        row["failed_at"].isoformat() if row["failed_at"] else None
                    ),  # noqa: E501
                }

            # Determine overall status
            statuses = [c["status"] for c in channels.values()]
            if all(s == "delivered" for s in statuses):
                overall = "delivered"
            elif any(s == "failed" for s in statuses):
                overall = "failed"
            elif any(s == "retrying" for s in statuses):
                overall = "retrying"
            elif any(s == "sent" for s in statuses):
                overall = "sent"
            else:
                overall = "queued"

            return {
                "notification_id": notification_id,
                "channels": channels,
                "overall_status": overall,
            }

        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {
                "notification_id": notification_id,
                "channels": {},
                "overall_status": "error",
                "error": str(e),
            }

    def retry_failed(self, notification_id: str, channel: str) -> bool:
        """
        Retry failed notification delivery.

        Args:
            notification_id: Notification identifier
            channel: Delivery channel

        Returns:
            True if retry queued, False otherwise
        """
        try:
            # Get current record
            record = self._get_record(notification_id, channel)
            if not record:
                logger.error(f"No record found for {notification_id}/{channel}")
                return False

            retry_count = record.get("retry_count", 0)

            # Check if max retries exceeded
            if retry_count >= self.retry_policy.max_retries:
                logger.warning(f"Max retries exceeded for {notification_id}/{channel}")
                self.move_to_dead_letter_queue(notification_id)
                return False

            # Calculate retry delay
            delay = self.retry_policy.get_delay(retry_count)

            # Update status to retrying
            self._update_record(
                notification_id=notification_id,
                channel=channel,
                status=DeliveryStatus.RETRYING.value,
            )

            # Add to Redis retry queue with delay
            retry_key = f"retry:{channel}:{notification_id}"
            retry_data = {
                "notification_id": notification_id,
                "channel": channel,
                "retry_count": retry_count + 1,
                "scheduled_at": (
                    datetime.utcnow() + timedelta(seconds=delay)
                ).isoformat(),  # noqa: E501
            }
            self.redis_client.setex(
                retry_key,
                int(delay) + 60,  # TTL slightly longer than delay
                json.dumps(retry_data),
            )

            # Add to sorted set for scheduling
            score = time.time() + delay
            self.redis_client.zadd("retry_queue", {retry_key: score})

            logger.info(
                f"Retry queued for {notification_id}/{channel} "
                f"(attempt {retry_count + 1}, delay {delay:.1f}s)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to retry delivery: {e}")
            return False

    def move_to_dead_letter_queue(self, notification_id: str) -> bool:
        """
        Move notification to dead letter queue.

        Args:
            notification_id: Notification identifier

        Returns:
            True if moved successfully, False otherwise
        """
        try:
            # Get all records for this notification
            query = """
            SELECT * FROM delivery_log
            WHERE notification_id = %s
            ORDER BY created_at DESC
            """
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (notification_id,))
                records = cursor.fetchall()

            if not records:
                logger.error(f"No records found for {notification_id}")
                return False

            # Insert into dead letter queue
            dlq_query = """
            INSERT INTO dead_letter_queue (
                notification_id, channel, recipient, message_content,
                retry_count, last_error, failed_at, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            for record in records:
                with self.db_conn.cursor() as cursor:
                    cursor.execute(
                        dlq_query,
                        (
                            record["notification_id"],
                            record["channel"],
                            record["recipient"],
                            record["message_content"],
                            record["retry_count"],
                            record["last_error"],
                            datetime.utcnow(),
                            (
                                json.dumps(record["metadata"])
                                if record["metadata"]
                                else "{}"
                            ),  # noqa: E501
                        ),
                    )

            # Update delivery_log status
            update_query = """
            UPDATE delivery_log
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE notification_id = %s
            """
            with self.db_conn.cursor() as cursor:
                cursor.execute(
                    update_query, (DeliveryStatus.DEAD_LETTER.value, notification_id)
                )

            self.db_conn.commit()
            logger.info(f"Moved {notification_id} to dead letter queue")
            return True

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Failed to move to DLQ: {e}")
            return False

    def get_metrics(
        self, time_range: str = "24h", channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get delivery metrics.

        Args:
            time_range: Time range (24h, 7d, 30d, 90d)
            channel: Optional channel filter

        Returns:
            Dictionary with metrics
        """
        # Parse time range
        range_map = {
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
        }
        delta = range_map.get(time_range, timedelta(hours=24))
        start_time = datetime.utcnow() - delta

        # Base query
        base_query = """
        SELECT
            channel,
            COUNT(*) as total_notifications,
            SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status = 'dead_letter' THEN 1 ELSE 0 END) as dead_letter,  # noqa: E501
            SUM(retry_count) as total_retries,
            AVG(CASE
                WHEN delivered_at IS NOT NULL AND queued_at IS NOT NULL
                THEN EXTRACT(EPOCH FROM (delivered_at - queued_at)) * 1000
                ELSE NULL
            END) as avg_latency_ms
        FROM delivery_log
        WHERE queued_at >= %s
        """

        params: List[Any] = [start_time]

        if channel:
            base_query += " AND channel = %s"
            params.append(channel)

        base_query += " GROUP BY channel"

        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(base_query, params)
                results = cursor.fetchall()

            metrics: Dict[str, Any] = {
                "time_range": time_range,
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "channels": {},
            }

            total_notifications = 0
            total_delivered = 0
            total_failed = 0

            for row in results:
                ch = row["channel"]
                notifications = row["total_notifications"]
                delivered = row["delivered"]
                failed = row["failed"]

                total_notifications += notifications
                total_delivered += delivered
                total_failed += failed

                metrics["channels"][ch] = {
                    "total_notifications": notifications,
                    "delivered": delivered,
                    "failed": failed,
                    "dead_letter": row["dead_letter"],
                    "total_retries": row["total_retries"],
                    "success_rate": (
                        round(delivered / notifications * 100, 2)
                        if notifications > 0
                        else 0.0
                    ),  # noqa: E501
                    "avg_latency_ms": (
                        round(row["avg_latency_ms"], 2)
                        if row["avg_latency_ms"]
                        else 0.0
                    ),  # noqa: E501
                    "retry_success_rate": self._calculate_retry_success_rate(
                        ch, start_time
                    ),  # noqa: E501
                }

            metrics["overall"] = {
                "total_notifications": total_notifications,
                "delivered": total_delivered,
                "failed": total_failed,
                "success_rate": (
                    round(total_delivered / total_notifications * 100, 2)
                    if total_notifications > 0
                    else 0.0
                ),  # noqa: E501
            }

            return metrics

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"error": str(e)}

    def _calculate_retry_success_rate(
        self, channel: str, start_time: datetime
    ) -> float:
        """Calculate retry success rate for channel."""
        query = """
        SELECT
            SUM(CASE WHEN retry_count > 0 THEN 1 ELSE 0 END) as retried,
            SUM(CASE WHEN retry_count > 0 AND status = 'delivered' THEN 1 ELSE 0 END) as retry_success  # noqa: E501
        FROM delivery_log
        WHERE channel = %s AND queued_at >= %s
        """
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(query, (channel, start_time))
                result = cursor.fetchone()
                if result and result[0] > 0:
                    return round(result[1] / result[0] * 100, 2)
                return 0.0
        except Exception as e:
            logger.error(f"Failed to calculate retry success rate: {e}")
            return 0.0

    def _check_repeated_failures(self, notification_id: str, channel: str) -> None:
        """Check for repeated failures and trigger alert."""
        query = """
        SELECT COUNT(*) FROM delivery_log
        WHERE channel = %s
        AND status = 'failed'
        AND queued_at >= %s
        """
        threshold_time = datetime.utcnow() - timedelta(hours=1)

        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(query, (channel, threshold_time))
                count = cursor.fetchone()[0]

            if count >= 3 and self.alert_callback:
                try:
                    self.alert_callback(
                        notification_id,
                        f"Repeated failures on {channel}: {count} in last hour",
                    )
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")

        except Exception as e:
            logger.error(f"Failed to check repeated failures: {e}")

    def get_delivery_history(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Query delivery history with filters.

        Args:
            filters: Optional filters (channel, status, start_date, end_date)
            limit: Maximum records to return
            offset: Offset for pagination

        Returns:
            List of delivery records
        """
        query = "SELECT * FROM delivery_log WHERE 1=1"
        params = []

        if filters:
            if "channel" in filters:
                query += " AND channel = %s"
                params.append(filters["channel"])

            if "status" in filters:
                query += " AND status = %s"
                params.append(filters["status"])

            if "start_date" in filters:
                query += " AND queued_at >= %s"
                params.append(filters["start_date"])

            if "end_date" in filters:
                query += " AND queued_at <= %s"
                params.append(filters["end_date"])

            if "notification_id" in filters:
                query += " AND notification_id = %s"
                params.append(filters["notification_id"])

        query += " ORDER BY queued_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to get delivery history: {e}")
            return []

    def export_history(
        self,
        output_path: str,
        export_format: str = "csv",
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Export delivery history to file.

        Args:
            output_path: Output file path
            export_format: Export format (csv or json)
            filters: Optional filters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get all matching records
            records = self.get_delivery_history(filters=filters, limit=10000)

            if not records:
                return False, "No records found to export"

            if export_format == "csv":
                with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                    fieldnames = [
                        "notification_id",
                        "channel",
                        "status",
                        "recipient",
                        "retry_count",
                        "last_error",
                        "queued_at",
                        "sent_at",
                        "delivered_at",
                        "failed_at",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    for record in records:
                        row = {k: record.get(k) for k in fieldnames}
                        # Convert datetime objects to strings
                        for k, v in row.items():
                            if isinstance(v, datetime):
                                row[k] = v.isoformat()
                        writer.writerow(row)

            elif export_format == "json":
                with open(output_path, "w", encoding="utf-8") as jsonfile:
                    # Convert datetime objects to strings
                    for record in records:
                        for k, v in record.items():
                            if isinstance(v, datetime):
                                record[k] = v.isoformat()
                    json.dump(records, jsonfile, indent=2)

            else:
                return False, f"Unsupported format: {export_format}"

            return True, f"Exported {len(records)} records to {output_path}"

        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            return False, f"Export failed: {e}"

    def cleanup_old_records(self, days: int = 90) -> int:
        """
        Clean up old delivery records.

        Args:
            days: Delete records older than this many days

        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = "DELETE FROM delivery_log WHERE queued_at < %s"

        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(query, (cutoff_date,))
                deleted = cursor.rowcount
                self.db_conn.commit()

            logger.info(f"Cleaned up {deleted} old delivery records")
            return deleted

        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Failed to cleanup old records: {e}")
            return 0

    def close(self) -> None:
        """Close database connections."""
        try:
            if hasattr(self, "db_conn"):
                self.db_conn.close()
            if hasattr(self, "redis_client"):
                self.redis_client.close()
            logger.info("DeliveryTracker connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
