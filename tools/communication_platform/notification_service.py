"""
Notification Service - Main orchestration class for the communication platform.

This module provides the primary interface for sending notifications across
multiple channels (Slack, Email, Teams, PagerDuty, SMS) with template-based
messaging, escalation rules, delivery tracking, and rate limiting.

The NotificationService integrates all core components:
    - NotificationRouter: Route notifications to appropriate channels
    - SlackIntegration: Send Slack messages with Block Kit
    - EmailService: Send emails via SendGrid/SMTP
    - AlertManager: Handle escalation policies
    - DeliveryTracker: Track delivery status and retries
    - RateLimiter: Prevent API rate limit violations
    - TemplateEngine: Render notification templates

Example:
    Basic usage::

        service = NotificationService(
            redis_url="redis://localhost:6379",
            postgres_url="postgresql://user:pass@localhost/db",
            slack_token="xoxb-...",
            sendgrid_api_key="SG...."
        )

        # Simple notification
        notification_id = await service.send_notification(
            title="Deployment Complete",
            message="Production deployment successful",
            channels=["slack", "email"],
            recipients=["@team-ops", "ops@company.com"],
            priority="high"
        )

        # Template-based notification
        notification_id = await service.send_template_notification(
            template_name="deployment_complete",
            context={
                "environment": "production",
                "version": "v2.1.0",
                "deployer": "Alice"
            },
            channels=["slack", "email"],
            recipients=["@team-ops"]
        )

        # Check status
        status = await service.get_notification_status(notification_id)
        print(f"Status: {status.status}, Delivered: {status.delivered_count}")
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from .alert_manager import AlertManager, AlertSeverity
from .delivery_tracker import DeliveryRecord, DeliveryStatus, DeliveryTracker
from .email_service import EmailMessage, EmailService
from .notification_router import (
    ChannelType,
    NotificationRequest,
    NotificationRouter,
    Priority,
    Severity,
)
from .rate_limiter import RateLimiter
from .slack_integration import SlackIntegration, SlackMessage
from .template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class NotificationConfig(BaseModel):
    """Configuration for notification service.

    Attributes:
        redis_url: Redis connection URL (e.g., 'redis://localhost:6379')
        postgres_url: PostgreSQL connection URL
        slack_token: Slack bot token (optional, for Slack integration)
        slack_signing_secret: Slack signing secret (optional, for verification)
        sendgrid_api_key: SendGrid API key (optional, for email)
        smtp_host: SMTP server host (optional, alternative to SendGrid)
        smtp_port: SMTP server port (optional)
        smtp_username: SMTP username (optional)
        smtp_password: SMTP password (optional)
        default_from_email: Default sender email address
        rate_limits: Custom rate limits per channel (requests per minute)
        retry_policy: Retry configuration (max_retries, backoff_multiplier)
        enable_dead_letter_queue: Enable dead letter queue for failed notifications
        retention_days: Days to retain notification history (default: 90)
    """

    redis_url: str = Field(..., description="Redis connection URL")
    postgres_url: str = Field(..., description="PostgreSQL connection URL")
    slack_token: Optional[str] = Field(None, description="Slack bot token")
    slack_signing_secret: Optional[str] = Field(
        None, description="Slack signing secret"
    )
    sendgrid_api_key: Optional[str] = Field(None, description="SendGrid API key")
    smtp_host: Optional[str] = Field(None, description="SMTP server host")
    smtp_port: Optional[int] = Field(None, description="SMTP server port")
    smtp_username: Optional[str] = Field(None, description="SMTP username")
    smtp_password: Optional[str] = Field(None, description="SMTP password")
    default_from_email: str = Field(
        "notifications@company.com", description="Default sender email"
    )
    rate_limits: Dict[str, int] = Field(
        default_factory=lambda: {
            "slack": 50,  # per minute
            "email": 100,
            "teams": 60,
            "pagerduty": 60,
            "sms": 10,
        }
    )
    retry_policy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_retries": 3,
            "backoff_multiplier": 2,  # 1s, 2s, 4s
            "initial_delay": 1.0,
        }
    )
    enable_dead_letter_queue: bool = Field(True, description="Enable dead letter queue")
    retention_days: int = Field(90, description="Notification history retention days")

    @validator("redis_url")
    def validate_redis_url(cls, v: str) -> str:
        """Validate Redis URL format."""
        if not v.startswith("redis://") and not v.startswith("rediss://"):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v

    @validator("postgres_url")
    def validate_postgres_url(cls, v: str) -> str:
        """Validate PostgreSQL URL format."""
        if not v.startswith("postgresql://") and not v.startswith("postgres://"):
            raise ValueError(
                "PostgreSQL URL must start with postgresql:// or postgres://"
            )
        return v


class NotificationResult(BaseModel):
    """Result of a notification send operation.

    Attributes:
        notification_id: Unique notification identifier
        status: Current notification status
        channels_attempted: Channels that were attempted
        channels_succeeded: Channels that succeeded
        channels_failed: Channels that failed
        delivery_records: Delivery records per channel
        errors: Error messages per channel
        created_at: Notification creation timestamp
    """

    notification_id: str
    status: str
    channels_attempted: List[str]
    channels_succeeded: List[str]
    channels_failed: List[str]
    delivery_records: Dict[str, DeliveryRecord] = Field(default_factory=dict)
    errors: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationStatusResponse(BaseModel):
    """Notification status query response.

    Attributes:
        notification_id: Unique notification identifier
        status: Current overall status
        delivered_count: Number of successfully delivered channels
        failed_count: Number of failed channels
        pending_count: Number of pending channels
        delivery_records: Detailed delivery records per channel
        last_updated: Last status update timestamp
    """

    notification_id: str
    status: str
    delivered_count: int
    failed_count: int
    pending_count: int
    delivery_records: Dict[str, DeliveryRecord]
    last_updated: datetime


class NotificationService:
    """Main notification service orchestrating all components.

    This service provides a unified interface for sending notifications across
    multiple channels with intelligent routing, rate limiting, delivery tracking,
    and automatic retries.

    The service handles the complete notification flow:
        1. Parse and validate notification request
        2. Apply routing rules to select channels
        3. Check rate limits for each channel
        4. Send notification via selected channels
        5. Track delivery status
        6. Handle retries for failed deliveries
        7. Move permanently failed notifications to dead letter queue

    Attributes:
        config: Service configuration
        router: Notification router for channel selection
        slack: Slack integration (if configured)
        email: Email service (if configured)
        alert_manager: Alert manager for escalation
        delivery_tracker: Delivery tracking and retry logic
        rate_limiter: Rate limiting per channel
        template_engine: Template rendering
    """

    def __init__(self, config: Union[NotificationConfig, Dict[str, Any]]):
        """Initialize notification service.

        Args:
            config: Service configuration (NotificationConfig or dict)

        Raises:
            ValueError: If required configuration is missing
            ConnectionError: If unable to connect to Redis/PostgreSQL
        """
        if isinstance(config, dict):
            config = NotificationConfig(**config)

        self.config = config
        self._initialized = False

        # Initialize core components
        self.router: Optional[NotificationRouter] = None
        self.slack: Optional[SlackIntegration] = None
        self.email: Optional[EmailService] = None
        self.alert_manager: Optional[AlertManager] = None
        self.delivery_tracker: Optional[DeliveryTracker] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.template_engine: Optional[TemplateEngine] = None

        logger.info("NotificationService created, call initialize() to connect")

    async def initialize(self) -> None:
        """Initialize all components and establish connections.

        This must be called before sending notifications.

        Raises:
            ConnectionError: If unable to connect to required services
            ValueError: If required configuration is missing
        """
        if self._initialized:
            logger.warning("NotificationService already initialized")
            return

        logger.info("Initializing NotificationService components...")

        try:
            # Initialize router
            self.router = NotificationRouter(redis_url=self.config.redis_url)
            await self.router.connect()
            logger.info("NotificationRouter initialized")

            # Initialize Slack (if configured)
            if self.config.slack_token:
                self.slack = SlackIntegration(
                    token=self.config.slack_token,
                    signing_secret=self.config.slack_signing_secret,
                )
                logger.info("SlackIntegration initialized")

            # Initialize Email (if configured)
            if self.config.sendgrid_api_key or self.config.smtp_host:
                self.email = EmailService(
                    sendgrid_api_key=self.config.sendgrid_api_key,
                    smtp_host=self.config.smtp_host,
                    smtp_port=self.config.smtp_port,
                    smtp_username=self.config.smtp_username,
                    smtp_password=self.config.smtp_password,
                    default_from_email=self.config.default_from_email,
                )
                logger.info("EmailService initialized")

            # Initialize alert manager
            self.alert_manager = AlertManager(
                redis_url=self.config.redis_url,
                postgres_url=self.config.postgres_url,
            )
            await self.alert_manager.connect()
            logger.info("AlertManager initialized")

            # Initialize delivery tracker
            self.delivery_tracker = DeliveryTracker(
                postgres_url=self.config.postgres_url,
                redis_url=self.config.redis_url,
                max_retries=self.config.retry_policy["max_retries"],
                initial_delay=self.config.retry_policy["initial_delay"],
                backoff_multiplier=self.config.retry_policy["backoff_multiplier"],
            )
            await self.delivery_tracker.connect()
            logger.info("DeliveryTracker initialized")

            # Initialize rate limiter
            self.rate_limiter = RateLimiter(redis_url=self.config.redis_url)
            await self.rate_limiter.connect()

            # Set custom rate limits
            for channel, limit in self.config.rate_limits.items():
                await self.rate_limiter.set_rate_limit(
                    resource=f"channel:{channel}", max_requests=limit, window_seconds=60
                )
            logger.info("RateLimiter initialized with custom limits")

            # Initialize template engine
            self.template_engine = TemplateEngine(postgres_url=self.config.postgres_url)
            await self.template_engine.connect()
            logger.info("TemplateEngine initialized")

            self._initialized = True
            logger.info("NotificationService initialization complete")

        except Exception as e:
            logger.error(f"Failed to initialize NotificationService: {e}")
            await self.cleanup()
            raise ConnectionError(f"Initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Cleanup resources and close connections."""
        logger.info("Cleaning up NotificationService...")

        if self.router:
            await self.router.disconnect()
        if self.alert_manager:
            await self.alert_manager.disconnect()
        if self.delivery_tracker:
            await self.delivery_tracker.disconnect()
        if self.rate_limiter:
            await self.rate_limiter.disconnect()
        if self.template_engine:
            await self.template_engine.disconnect()

        self._initialized = False
        logger.info("NotificationService cleanup complete")

    async def send_notification(
        self,
        title: str,
        message: str,
        channels: Optional[List[str]] = None,
        recipients: Optional[List[str]] = None,
        priority: str = "medium",
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> NotificationResult:
        """Send a simple notification across specified channels.

        Args:
            title: Notification title
            message: Notification message body
            channels: Target channels (e.g., ['slack', 'email']).
                If None, router decides.
            recipients: Recipients per channel
                (e.g., ['@team', 'user@company.com'])
            priority: Notification priority (low, medium, high, critical)
            severity: Notification severity (info, warning, error, critical)
            metadata: Additional metadata for routing/tracking
            tags: Tags for categorization and filtering

        Returns:
            NotificationResult with delivery status per channel

        Raises:
            ValueError: If service not initialized or invalid parameters
            RuntimeError: If all channels fail to send
        """
        if not self._initialized:
            raise ValueError(
                "NotificationService not initialized. Call initialize() first."
            )

        notification_id = str(uuid4())
        logger.info(f"Sending notification {notification_id}: {title}")

        # Create notification request
        request = NotificationRequest(
            id=notification_id,
            title=title,
            message=message,
            channels=[ChannelType(c) for c in channels] if channels else None,
            recipients=recipients or [],
            priority=Priority(priority),
            severity=Severity(severity),
            metadata=metadata or {},
            tags=tags or [],
        )

        # Route notification to determine channels
        if not request.channels:
            request = await self.router.route_notification(request)
            logger.info(
                f"Router selected channels: {[c.value for c in request.channels]}"
            )

        # Send to each channel
        result = NotificationResult(
            notification_id=notification_id,
            status="processing",
            channels_attempted=[],
            channels_succeeded=[],
            channels_failed=[],
        )

        for channel in request.channels:
            channel_name = channel.value
            result.channels_attempted.append(channel_name)

            try:
                # Check rate limit
                allowed = await self.rate_limiter.check_rate_limit(
                    resource=f"channel:{channel_name}"
                )
                if not allowed:
                    logger.warning(
                        f"Rate limit exceeded for channel {channel_name}, "
                        f"queuing for retry"
                    )
                    result.channels_failed.append(channel_name)
                    result.errors[channel_name] = "Rate limit exceeded"
                    continue

                # Send to channel
                success = await self._send_to_channel(
                    channel=channel_name,
                    notification_id=notification_id,
                    title=title,
                    message=message,
                    recipients=recipients or [],
                    metadata=metadata or {},
                )

                if success:
                    result.channels_succeeded.append(channel_name)
                    # Track successful delivery
                    await self.delivery_tracker.track_delivery(
                        notification_id=notification_id,
                        channel=channel_name,
                        status=DeliveryStatus.DELIVERED,
                        recipient=",".join(recipients or []),
                        metadata={"title": title},
                    )
                else:
                    result.channels_failed.append(channel_name)
                    # Track failed delivery for retry
                    await self.delivery_tracker.track_delivery(
                        notification_id=notification_id,
                        channel=channel_name,
                        status=DeliveryStatus.FAILED,
                        recipient=",".join(recipients or []),
                        error_message="Delivery failed",
                        metadata={"title": title},
                    )

            except Exception as e:
                logger.error(f"Error sending to {channel_name}: {e}")
                result.channels_failed.append(channel_name)
                result.errors[channel_name] = str(e)
                # Track error
                await self.delivery_tracker.track_delivery(
                    notification_id=notification_id,
                    channel=channel_name,
                    status=DeliveryStatus.FAILED,
                    recipient=",".join(recipients or []),
                    error_message=str(e),
                    metadata={"title": title},
                )

        # Update overall status
        if result.channels_succeeded and not result.channels_failed:
            result.status = "delivered"
        elif result.channels_succeeded:
            result.status = "partial"
        else:
            result.status = "failed"

        logger.info(
            f"Notification {notification_id} completed: "
            f"{len(result.channels_succeeded)}/"
            f"{len(result.channels_attempted)} succeeded"
        )

        return result

    async def send_template_notification(
        self,
        template_name: str,
        context: Dict[str, Any],
        channels: Optional[List[str]] = None,
        recipients: Optional[List[str]] = None,
        priority: str = "medium",
        severity: str = "info",
        template_version: Optional[str] = None,
    ) -> NotificationResult:
        """Send a template-based notification.

        Args:
            template_name: Name of the template to use
            context: Template context variables
            channels: Target channels (if None, router decides)
            recipients: Recipients per channel
            priority: Notification priority
            severity: Notification severity
            template_version: Specific template version (if None, uses latest)

        Returns:
            NotificationResult with delivery status

        Raises:
            ValueError: If template not found or invalid context
        """
        if not self._initialized:
            raise ValueError("NotificationService not initialized")

        # Render template
        rendered = await self.template_engine.render_template(
            template_name=template_name,
            context=context,
            version=template_version,
        )

        # Send notification with rendered content
        return await self.send_notification(
            title=rendered.get("title", template_name),
            message=rendered.get("body", ""),
            channels=channels,
            recipients=recipients,
            priority=priority,
            severity=severity,
            metadata={"template": template_name, "template_context": context},
        )

    async def send_alert(
        self,
        title: str,
        message: str,
        severity: str,
        escalation_policy_id: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NotificationResult:
        """Send an alert with escalation policy.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity (info, warning, error, critical)
            escalation_policy_id: ID of escalation policy to apply
            recipients: Initial recipients
            metadata: Additional metadata

        Returns:
            NotificationResult with delivery status
        """
        if not self._initialized:
            raise ValueError("NotificationService not initialized")

        alert_id = str(uuid4())

        # Send through alert manager for escalation handling
        await self.alert_manager.send_alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=AlertSeverity(severity),
            escalation_policy_id=escalation_policy_id,
            recipients=recipients,
            metadata=metadata or {},
        )

        # Also send immediate notification
        return await self.send_notification(
            title=title,
            message=message,
            channels=None,  # Let router decide based on severity
            recipients=recipients,
            priority="high" if severity in ["error", "critical"] else "medium",
            severity=severity,
            metadata={**(metadata or {}), "alert_id": alert_id},
            tags=["alert", severity],
        )

    async def get_notification_status(
        self, notification_id: str
    ) -> NotificationStatusResponse:
        """Get current status of a notification.

        Args:
            notification_id: Notification identifier

        Returns:
            NotificationStatusResponse with current status and delivery records

        Raises:
            ValueError: If notification not found
        """
        if not self._initialized:
            raise ValueError("NotificationService not initialized")

        # Get delivery records from tracker
        records = await self.delivery_tracker.get_delivery_status(notification_id)

        if not records:
            raise ValueError(f"Notification {notification_id} not found")

        # Aggregate status
        delivered_count = sum(
            1 for r in records.values() if r.status == DeliveryStatus.DELIVERED
        )
        failed_count = sum(
            1 for r in records.values() if r.status == DeliveryStatus.FAILED
        )
        pending_count = sum(
            1
            for r in records.values()
            if r.status in [DeliveryStatus.PENDING, DeliveryStatus.QUEUED]
        )

        # Determine overall status
        if delivered_count == len(records):
            status = "delivered"
        elif failed_count == len(records):
            status = "failed"
        elif pending_count > 0:
            status = "pending"
        else:
            status = "partial"

        return NotificationStatusResponse(
            notification_id=notification_id,
            status=status,
            delivered_count=delivered_count,
            failed_count=failed_count,
            pending_count=pending_count,
            delivery_records=records,
            last_updated=max(r.updated_at for r in records.values()),
        )

    async def retry_failed_notifications(
        self, notification_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Retry failed notification deliveries.

        Args:
            notification_id: Specific notification to retry
                (if None, retries all failed)

        Returns:
            Dict with retry statistics (attempted, succeeded, still_failed)
        """
        if not self._initialized:
            raise ValueError("NotificationService not initialized")

        # Get failed deliveries
        failed = await self.delivery_tracker.get_failed_deliveries(
            notification_id=notification_id
        )

        stats = {"attempted": 0, "succeeded": 0, "still_failed": 0}

        for record in failed:
            stats["attempted"] += 1

            # Check if max retries exceeded
            if record.retry_count >= self.config.retry_policy["max_retries"]:
                logger.warning(
                    f"Max retries exceeded for {record.notification_id} "
                    f"on channel {record.channel}"
                )
                if self.config.enable_dead_letter_queue:
                    await self.delivery_tracker.move_to_dead_letter_queue(
                        record.notification_id, record.channel
                    )
                stats["still_failed"] += 1
                continue

            # Attempt retry
            try:
                success = await self._send_to_channel(
                    channel=record.channel,
                    notification_id=record.notification_id,
                    title=record.metadata.get("title", "Notification"),
                    message=record.metadata.get("message", ""),
                    recipients=[record.recipient] if record.recipient else [],
                    metadata=record.metadata,
                )

                if success:
                    stats["succeeded"] += 1
                    await self.delivery_tracker.track_delivery(
                        notification_id=record.notification_id,
                        channel=record.channel,
                        status=DeliveryStatus.DELIVERED,
                        recipient=record.recipient,
                        metadata=record.metadata,
                    )
                else:
                    stats["still_failed"] += 1
                    await self.delivery_tracker.track_delivery(
                        notification_id=record.notification_id,
                        channel=record.channel,
                        status=DeliveryStatus.FAILED,
                        recipient=record.recipient,
                        error_message="Retry failed",
                        metadata=record.metadata,
                    )

            except Exception as e:
                logger.error(f"Retry failed for {record.notification_id}: {e}")
                stats["still_failed"] += 1

        logger.info(f"Retry completed: {stats}")
        return stats

    async def get_metrics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get notification delivery metrics.

        Args:
            start_date: Start date for metrics (if None, last 24 hours)
            end_date: End date for metrics (if None, current time)

        Returns:
            Dict with metrics (total_sent, success_rate, avg_latency, by_channel, etc.)
        """
        if not self._initialized:
            raise ValueError("NotificationService not initialized")

        return await self.delivery_tracker.get_metrics(
            start_date=start_date, end_date=end_date
        )

    async def _send_to_channel(
        self,
        channel: str,
        notification_id: str,
        title: str,
        message: str,
        recipients: List[str],
        metadata: Dict[str, Any],
    ) -> bool:
        """Send notification to a specific channel.

        Args:
            channel: Channel name (slack, email, etc.)
            notification_id: Notification identifier
            title: Notification title
            message: Notification message
            recipients: List of recipients
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            if channel == "slack" and self.slack:
                # Send to Slack
                for recipient in recipients:
                    slack_msg = SlackMessage(
                        channel=recipient if recipient.startswith("#") else recipient,
                        text=message,
                        blocks=None,  # Could enhance with Block Kit
                    )
                    response = await self.slack.post_message(slack_msg)
                    if not response.get("ok"):
                        return False
                return True

            elif channel == "email" and self.email:
                # Send email
                for recipient in recipients:
                    email_msg = EmailMessage(
                        to=[recipient],
                        subject=title,
                        body=message,
                        from_email=self.config.default_from_email,
                    )
                    success = await self.email.send_email(email_msg)
                    if not success:
                        return False
                return True

            else:
                logger.warning(f"Channel {channel} not configured or unsupported")
                return False

        except Exception as e:
            logger.error(f"Error sending to {channel}: {e}")
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
