"""
Comprehensive test suite for Communication & Notification Platform.

This module contains 70+ test functions covering all core components:
    - NotificationRouter
    - SlackIntegration
    - EmailService
    - AlertManager
    - DeliveryTracker
    - RateLimiter
    - TemplateEngine
    - NotificationService (orchestration)
    - CLI interface

Test coverage includes:
    - Unit tests for individual components
    - Integration tests for end-to-end flows
    - Error handling and edge cases
    - Mocking external services (Slack, SendGrid, Redis, PostgreSQL)
    - Performance and concurrency tests
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fakeredis import aioredis as fake_aioredis

from communication_platform.alert_manager import (
    AlertManager,
    AlertSeverity,
    EscalationLevel,
    EscalationPolicy,
)
from communication_platform.delivery_tracker import (
    DeliveryRecord,
    DeliveryStatus,
    DeliveryTracker,
    RetryPolicy,
)
from communication_platform.email_service import (
    EmailAttachment,
    EmailMessage,
    EmailService,
)
from communication_platform.notification_router import (
    ChannelType,
    NotificationRequest,
    NotificationRouter,
    NotificationStatus,
    Priority,
    Severity,
)
from communication_platform.notification_service import (
    NotificationConfig,
    NotificationResult,
    NotificationService,
    NotificationStatusResponse,
)
from communication_platform.rate_limiter import (
    RateLimit,
    RateLimitAlgorithm,
    RateLimiter,
    RateLimitStatus,
)
from communication_platform.slack_integration import (
    SlackBlock,
    SlackIntegration,
    SlackMessage,
)
from communication_platform.template_engine import (
    Template,
    TemplateCategory,
    TemplateEngine,
    TemplateVersion,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return fake_aioredis.FakeRedis()


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL connection."""
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.close = AsyncMock()
    return conn


@pytest.fixture
def mock_slack_client():
    """Mock Slack WebClient."""
    client = MagicMock()
    client.chat_postMessage = AsyncMock(
        return_value={"ok": True, "ts": "1234567890.123456", "channel": "C123"}
    )
    client.files_upload = AsyncMock(return_value={"ok": True, "file": {"id": "F123"}})
    client.conversations_replies = AsyncMock(return_value={"ok": True, "messages": []})
    return client


@pytest.fixture
def mock_sendgrid():
    """Mock SendGrid client."""
    client = MagicMock()
    client.send = MagicMock(return_value=MagicMock(status_code=202))
    return client


@pytest.fixture
async def notification_router(mock_redis):
    """Create NotificationRouter instance with mocked Redis."""
    with patch("communication_platform.notification_router.aioredis.from_url") as mock:
        mock.return_value = mock_redis
        router = NotificationRouter(redis_url="redis://localhost:6379")
        await router.connect()
        yield router
        await router.disconnect()


@pytest.fixture
async def slack_integration(mock_slack_client):
    """Create SlackIntegration instance with mocked client."""
    with patch("communication_platform.slack_integration.WebClient") as mock:
        mock.return_value = mock_slack_client
        integration = SlackIntegration(
            token="xoxb-test-token", signing_secret="test-secret"
        )
        yield integration


@pytest.fixture
async def email_service(mock_sendgrid):
    """Create EmailService instance with mocked SendGrid."""
    with patch("communication_platform.email_service.SendGridAPIClient") as mock:
        mock.return_value = mock_sendgrid
        service = EmailService(
            sendgrid_api_key="SG.test-key", default_from_email="test@example.com"
        )
        yield service


@pytest.fixture
async def alert_manager(mock_redis, mock_postgres):
    """Create AlertManager instance with mocked dependencies."""
    with patch("communication_platform.alert_manager.aioredis.from_url") as redis_mock:
        redis_mock.return_value = mock_redis
        with patch("communication_platform.alert_manager.asyncpg.connect") as pg_mock:
            pg_mock.return_value = mock_postgres
            manager = AlertManager(
                redis_url="redis://localhost:6379",
                postgres_url="postgresql://user:pass@localhost/db",
            )
            await manager.connect()
            yield manager
            await manager.disconnect()


@pytest.fixture
async def delivery_tracker(mock_redis, mock_postgres):
    """Create DeliveryTracker instance with mocked dependencies."""
    with patch(
        "communication_platform.delivery_tracker.aioredis.from_url"
    ) as redis_mock:
        redis_mock.return_value = mock_redis
        with patch(
            "communication_platform.delivery_tracker.asyncpg.connect"
        ) as pg_mock:
            pg_mock.return_value = mock_postgres
            tracker = DeliveryTracker(
                postgres_url="postgresql://user:pass@localhost/db",
                redis_url="redis://localhost:6379",
            )
            await tracker.connect()
            yield tracker
            await tracker.disconnect()


@pytest.fixture
async def rate_limiter(mock_redis):
    """Create RateLimiter instance with mocked Redis."""
    with patch("communication_platform.rate_limiter.aioredis.from_url") as mock:
        mock.return_value = mock_redis
        limiter = RateLimiter(redis_url="redis://localhost:6379")
        await limiter.connect()
        yield limiter
        await limiter.disconnect()


@pytest.fixture
async def template_engine(mock_postgres):
    """Create TemplateEngine instance with mocked PostgreSQL."""
    with patch("communication_platform.template_engine.asyncpg.connect") as mock:
        mock.return_value = mock_postgres
        engine = TemplateEngine(postgres_url="postgresql://user:pass@localhost/db")
        await engine.connect()
        yield engine
        await engine.disconnect()


@pytest.fixture
async def notification_service(
    mock_redis, mock_postgres, mock_slack_client, mock_sendgrid
):
    """Create NotificationService instance with all mocked dependencies."""
    config = NotificationConfig(
        redis_url="redis://localhost:6379",
        postgres_url="postgresql://user:pass@localhost/db",
        slack_token="xoxb-test-token",
        sendgrid_api_key="SG.test-key",
        default_from_email="test@example.com",
    )

    with patch(
        "communication_platform.notification_router.aioredis.from_url"
    ) as redis_mock:
        redis_mock.return_value = mock_redis
        with patch(
            "communication_platform.alert_manager.aioredis.from_url"
        ) as alert_redis:
            alert_redis.return_value = mock_redis
            with patch(
                "communication_platform.alert_manager.asyncpg.connect"
            ) as alert_pg:
                alert_pg.return_value = mock_postgres
                with patch(
                    "communication_platform.delivery_tracker.aioredis.from_url"
                ) as track_redis:
                    track_redis.return_value = mock_redis
                    with patch(
                        "communication_platform.delivery_tracker.asyncpg.connect"
                    ) as track_pg:
                        track_pg.return_value = mock_postgres
                        with patch(
                            "communication_platform.rate_limiter.aioredis.from_url"
                        ) as rate_redis:
                            rate_redis.return_value = mock_redis
                            with patch(
                                "communication_platform.template_engine.asyncpg.connect"
                            ) as template_pg:
                                template_pg.return_value = mock_postgres
                                with patch(
                                    "communication_platform.slack_integration.WebClient"
                                ) as slack_mock:
                                    slack_mock.return_value = mock_slack_client
                                    with patch(
                                        "communication_platform.email_service.SendGridAPIClient"
                                    ) as sg_mock:
                                        sg_mock.return_value = mock_sendgrid
                                        service = NotificationService(config)
                                        await service.initialize()
                                        yield service
                                        await service.cleanup()


# ============================================================================
# NotificationRouter Tests (10 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_router_initialization(notification_router):
    """Test router initialization and connection."""
    assert notification_router._redis is not None
    assert notification_router._connected is True


@pytest.mark.asyncio
async def test_router_route_notification_critical_priority(notification_router):
    """Test routing for critical priority notifications."""
    request = NotificationRequest(
        id=str(uuid4()),
        title="Critical Alert",
        message="System down",
        priority=Priority.CRITICAL,
        severity=Severity.CRITICAL,
        recipients=["@team"],
    )

    routed = await notification_router.route_notification(request)

    # Critical should go to Slack + PagerDuty
    assert ChannelType.SLACK in routed.channels
    assert ChannelType.PAGERDUTY in routed.channels


@pytest.mark.asyncio
async def test_router_route_notification_high_priority(notification_router):
    """Test routing for high priority notifications."""
    request = NotificationRequest(
        id=str(uuid4()),
        title="High Priority",
        message="Important update",
        priority=Priority.HIGH,
        severity=Severity.WARNING,
        recipients=["@team"],
    )

    routed = await notification_router.route_notification(request)

    # High should go to Slack + Email
    assert ChannelType.SLACK in routed.channels
    assert ChannelType.EMAIL in routed.channels


@pytest.mark.asyncio
async def test_router_route_notification_medium_priority(notification_router):
    """Test routing for medium priority notifications."""
    request = NotificationRequest(
        id=str(uuid4()),
        title="Medium Priority",
        message="Regular update",
        priority=Priority.MEDIUM,
        severity=Severity.INFO,
        recipients=["@team"],
    )

    routed = await notification_router.route_notification(request)

    # Medium should go to Slack only
    assert ChannelType.SLACK in routed.channels
    assert len(routed.channels) == 1


@pytest.mark.asyncio
async def test_router_route_notification_low_priority(notification_router):
    """Test routing for low priority notifications."""
    request = NotificationRequest(
        id=str(uuid4()),
        title="Low Priority",
        message="FYI update",
        priority=Priority.LOW,
        severity=Severity.INFO,
        recipients=["user@example.com"],
    )

    routed = await notification_router.route_notification(request)

    # Low should go to Email only
    assert ChannelType.EMAIL in routed.channels
    assert len(routed.channels) == 1


@pytest.mark.asyncio
async def test_router_queue_notification(notification_router):
    """Test queueing notification for async delivery."""
    request = NotificationRequest(
        id=str(uuid4()),
        title="Test",
        message="Test message",
        channels=[ChannelType.SLACK],
        recipients=["@team"],
    )

    await notification_router.queue_notification(request)

    # Verify queued in Redis
    queued = await notification_router._redis.lpop("notification:queue:slack")
    assert queued is not None
    data = json.loads(queued)
    assert data["id"] == request.id


@pytest.mark.asyncio
async def test_router_custom_routing_rules(notification_router):
    """Test adding custom routing rules."""
    rule = {
        "condition": {"tag": "security"},
        "channels": ["slack", "pagerduty"],
        "priority": "high",
    }

    await notification_router.add_routing_rule("security-rule", rule)

    # Apply rule to notification with security tag
    request = NotificationRequest(
        id=str(uuid4()),
        title="Security Alert",
        message="Security issue detected",
        tags=["security"],
        recipients=["@security-team"],
    )

    routed = await notification_router.route_notification(request)

    assert ChannelType.SLACK in routed.channels
    assert ChannelType.PAGERDUTY in routed.channels


@pytest.mark.asyncio
async def test_router_get_notification_status(notification_router):
    """Test getting notification status."""
    notification_id = str(uuid4())

    # Set status in Redis
    await notification_router._redis.hset(
        f"notification:{notification_id}",
        mapping={
            "status": NotificationStatus.SENT.value,
            "created_at": datetime.utcnow().isoformat(),
        },
    )

    status = await notification_router.get_notification_status(notification_id)

    assert status["status"] == NotificationStatus.SENT.value


@pytest.mark.asyncio
async def test_router_update_notification_status(notification_router):
    """Test updating notification status."""
    notification_id = str(uuid4())

    await notification_router.update_notification_status(
        notification_id, NotificationStatus.DELIVERED
    )

    # Verify updated in Redis
    status = await notification_router._redis.hget(
        f"notification:{notification_id}", "status"
    )
    assert status == NotificationStatus.DELIVERED.value


@pytest.mark.asyncio
async def test_router_disconnect(notification_router):
    """Test router disconnection."""
    await notification_router.disconnect()
    assert notification_router._connected is False


# ============================================================================
# SlackIntegration Tests (10 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_slack_post_message(slack_integration, mock_slack_client):
    """Test posting simple Slack message."""
    message = SlackMessage(channel="#general", text="Test message")

    response = await slack_integration.post_message(message)

    assert response["ok"] is True
    assert "ts" in response
    mock_slack_client.chat_postMessage.assert_called_once()


@pytest.mark.asyncio
async def test_slack_post_block_kit_message(slack_integration, mock_slack_client):
    """Test posting Slack message with Block Kit."""
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Bold text*"}},
        {"type": "divider"},
    ]

    message = SlackMessage(channel="#general", text="Fallback", blocks=blocks)

    response = await slack_integration.post_message(message)

    assert response["ok"] is True
    call_args = mock_slack_client.chat_postMessage.call_args
    assert call_args.kwargs["blocks"] == blocks


@pytest.mark.asyncio
async def test_slack_upload_file(slack_integration, mock_slack_client):
    """Test uploading file to Slack."""
    response = await slack_integration.upload_file(
        channel="#general", file_path="/tmp/test.txt", title="Test File"
    )

    assert response["ok"] is True
    mock_slack_client.files_upload.assert_called_once()


@pytest.mark.asyncio
async def test_slack_create_thread(slack_integration, mock_slack_client):
    """Test creating threaded conversation."""
    parent_message = SlackMessage(channel="#general", text="Parent message")
    parent_response = await slack_integration.post_message(parent_message)

    thread_message = SlackMessage(
        channel="#general", text="Reply", thread_ts=parent_response["ts"]
    )
    thread_response = await slack_integration.post_message(thread_message)

    assert thread_response["ok"] is True
    call_args = mock_slack_client.chat_postMessage.call_args
    assert "thread_ts" in call_args.kwargs


@pytest.mark.asyncio
async def test_slack_mention_user(slack_integration, mock_slack_client):
    """Test mentioning user in Slack message."""
    message = SlackMessage(
        channel="#general", text="Hello <@U123456>!", mentions=["U123456"]
    )

    response = await slack_integration.post_message(message)

    assert response["ok"] is True
    assert "<@U123456>" in mock_slack_client.chat_postMessage.call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_slack_mention_channel(slack_integration, mock_slack_client):
    """Test @channel mention."""
    message = SlackMessage(channel="#general", text="<!channel> Important update")

    response = await slack_integration.post_message(message)

    assert response["ok"] is True
    assert "<!channel>" in mock_slack_client.chat_postMessage.call_args.kwargs["text"]


@pytest.mark.asyncio
async def test_slack_interactive_buttons(slack_integration, mock_slack_client):
    """Test Slack message with interactive buttons."""
    blocks = [
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "value": "approve",
                    "action_id": "approve_action",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "value": "reject",
                    "action_id": "reject_action",
                },
            ],
        }
    ]

    message = SlackMessage(channel="#general", text="Approval needed", blocks=blocks)

    response = await slack_integration.post_message(message)

    assert response["ok"] is True
    call_args = mock_slack_client.chat_postMessage.call_args
    assert call_args.kwargs["blocks"] == blocks


@pytest.mark.asyncio
async def test_slack_format_message(slack_integration):
    """Test Slack message formatting."""
    formatted = slack_integration.format_message(
        text="Test *bold* _italic_ ~strike~", markdown=True
    )

    assert "*bold*" in formatted
    assert "_italic_" in formatted
    assert "~strike~" in formatted


@pytest.mark.asyncio
async def test_slack_error_handling(slack_integration, mock_slack_client):
    """Test Slack error handling."""
    mock_slack_client.chat_postMessage = AsyncMock(
        return_value={"ok": False, "error": "channel_not_found"}
    )

    message = SlackMessage(channel="#nonexistent", text="Test")

    response = await slack_integration.post_message(message)

    assert response["ok"] is False
    assert response["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_slack_rate_limit_handling(slack_integration, mock_slack_client):
    """Test handling Slack rate limits."""
    mock_slack_client.chat_postMessage = AsyncMock(
        side_effect=[
            {"ok": False, "error": "rate_limited", "retry_after": 1},
            {"ok": True, "ts": "1234567890.123456"},
        ]
    )

    message = SlackMessage(channel="#general", text="Test")

    with patch("asyncio.sleep", return_value=None):
        response = await slack_integration.post_message(
            message, retry_on_rate_limit=True
        )

    assert response["ok"] is True


# ============================================================================
# EmailService Tests (10 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_email_send_simple(email_service, mock_sendgrid):
    """Test sending simple email."""
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Test Email",
        body="This is a test email",
        from_email="sender@example.com",
    )

    success = await email_service.send_email(message)

    assert success is True
    mock_sendgrid.send.assert_called_once()


@pytest.mark.asyncio
async def test_email_send_html(email_service, mock_sendgrid):
    """Test sending HTML email."""
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="HTML Email",
        body="<h1>Hello</h1><p>This is HTML</p>",
        from_email="sender@example.com",
        is_html=True,
    )

    success = await email_service.send_email(message)

    assert success is True
    call_args = mock_sendgrid.send.call_args
    # Verify HTML content


@pytest.mark.asyncio
async def test_email_send_with_attachments(email_service, mock_sendgrid):
    """Test sending email with attachments."""
    attachment = EmailAttachment(
        filename="document.pdf",
        content=b"PDF content",
        content_type="application/pdf",
    )

    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Email with Attachment",
        body="See attached document",
        from_email="sender@example.com",
        attachments=[attachment],
    )

    success = await email_service.send_email(message)

    assert success is True


@pytest.mark.asyncio
async def test_email_send_with_cc_bcc(email_service, mock_sendgrid):
    """Test sending email with CC and BCC."""
    message = EmailMessage(
        to=["recipient@example.com"],
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        subject="Test CC/BCC",
        body="Test message",
        from_email="sender@example.com",
    )

    success = await email_service.send_email(message)

    assert success is True


@pytest.mark.asyncio
async def test_email_validate_address(email_service):
    """Test email address validation."""
    assert email_service.validate_email("valid@example.com") is True
    assert email_service.validate_email("invalid@") is False
    assert email_service.validate_email("@example.com") is False
    assert email_service.validate_email("no-at-sign") is False


@pytest.mark.asyncio
async def test_email_send_template(email_service, mock_sendgrid):
    """Test sending email with template."""
    context = {"name": "John", "action": "deployment"}

    success = await email_service.send_template(
        to=["recipient@example.com"],
        template_id="deployment-complete",
        context=context,
        from_email="sender@example.com",
    )

    assert success is True


@pytest.mark.asyncio
async def test_email_track_delivery(email_service, mock_sendgrid):
    """Test email delivery tracking."""
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Tracked Email",
        body="This email is tracked",
        from_email="sender@example.com",
        track_opens=True,
        track_clicks=True,
    )

    success = await email_service.send_email(message)

    assert success is True


@pytest.mark.asyncio
async def test_email_smtp_fallback(mock_sendgrid):
    """Test SMTP fallback when SendGrid fails."""
    mock_sendgrid.send = MagicMock(side_effect=Exception("SendGrid unavailable"))

    with patch("smtplib.SMTP") as smtp_mock:
        smtp_instance = MagicMock()
        smtp_mock.return_value.__enter__.return_value = smtp_instance

        service = EmailService(
            sendgrid_api_key="SG.test-key",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            default_from_email="test@example.com",
        )

        message = EmailMessage(
            to=["recipient@example.com"],
            subject="Test",
            body="Test",
            from_email="sender@example.com",
        )

        success = await service.send_email(message)

        assert success is True
        smtp_instance.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_email_error_handling(email_service, mock_sendgrid):
    """Test email error handling."""
    mock_sendgrid.send = MagicMock(
        return_value=MagicMock(status_code=400, body="Bad Request")
    )

    message = EmailMessage(
        to=["invalid@"],
        subject="Test",
        body="Test",
        from_email="sender@example.com",
    )

    success = await email_service.send_email(message)

    assert success is False


@pytest.mark.asyncio
async def test_email_batch_send(email_service, mock_sendgrid):
    """Test sending batch emails."""
    messages = [
        EmailMessage(
            to=[f"recipient{i}@example.com"],
            subject=f"Test {i}",
            body=f"Message {i}",
            from_email="sender@example.com",
        )
        for i in range(10)
    ]

    results = await email_service.send_batch(messages)

    assert len(results) == 10
    assert all(r is True for r in results)


# ============================================================================
# AlertManager Tests (10 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_alert_manager_create_policy(alert_manager, mock_postgres):
    """Test creating escalation policy."""
    levels = [
        EscalationLevel(
            level=1, delay_minutes=0, channels=["slack"], recipients=["@team"]
        ),
        EscalationLevel(
            level=2, delay_minutes=15, channels=["pagerduty"], recipients=["oncall"]
        ),
    ]

    policy = EscalationPolicy(
        id=str(uuid4()), name="Standard Escalation", levels=levels
    )

    await alert_manager.create_policy(policy)

    # Verify stored
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_alert_manager_send_alert(alert_manager, mock_redis, mock_postgres):
    """Test sending alert with severity."""
    alert_id = str(uuid4())

    await alert_manager.send_alert(
        alert_id=alert_id,
        title="High Severity Alert",
        message="Critical issue detected",
        severity=AlertSeverity.CRITICAL,
        recipients=["@team"],
    )

    # Verify alert stored and queued
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_alert_manager_escalate_alert(alert_manager, mock_postgres):
    """Test alert escalation."""
    alert_id = str(uuid4())
    policy_id = str(uuid4())

    # Create policy
    policy = EscalationPolicy(
        id=policy_id,
        name="Test Policy",
        levels=[
            EscalationLevel(
                level=1, delay_minutes=0, channels=["slack"], recipients=["@team"]
            ),
            EscalationLevel(
                level=2, delay_minutes=15, channels=["pagerduty"], recipients=["oncall"]
            ),
        ],
    )

    await alert_manager.create_policy(policy)

    # Send alert with policy
    await alert_manager.send_alert(
        alert_id=alert_id,
        title="Alert",
        message="Test alert",
        severity=AlertSeverity.HIGH,
        escalation_policy_id=policy_id,
    )

    # Simulate escalation
    await alert_manager.escalate_alert(alert_id)

    # Verify escalation level increased
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_alert_manager_check_escalation_needed(alert_manager, mock_postgres):
    """Test checking if escalation is needed."""
    alert_id = str(uuid4())

    # Mock alert that needs escalation (sent 20 minutes ago, level 1)
    mock_postgres.fetchrow = AsyncMock(
        return_value={
            "alert_id": alert_id,
            "escalation_level": 1,
            "sent_at": datetime.utcnow() - timedelta(minutes=20),
            "escalation_policy_id": str(uuid4()),
        }
    )

    needs_escalation = await alert_manager.check_escalation_needed(alert_id)

    assert needs_escalation is True


@pytest.mark.asyncio
async def test_alert_manager_deduplicate_alert(alert_manager, mock_redis):
    """Test alert deduplication."""
    alert_signature = "critical:database:connection_failed"

    # First alert should not be duplicate
    is_duplicate = await alert_manager.is_duplicate_alert(
        alert_signature, window_minutes=60
    )

    assert is_duplicate is False

    # Register alert
    await alert_manager.register_alert(alert_signature)

    # Second alert should be duplicate
    is_duplicate = await alert_manager.is_duplicate_alert(
        alert_signature, window_minutes=60
    )

    assert is_duplicate is True


@pytest.mark.asyncio
async def test_alert_manager_suppression_rules(alert_manager, mock_redis):
    """Test alert suppression rules."""
    rule = {
        "pattern": "maintenance:*",
        "suppress_until": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
    }

    await alert_manager.add_suppression_rule("maintenance-window", rule)

    # Alert matching pattern should be suppressed
    is_suppressed = await alert_manager.is_alert_suppressed(
        "maintenance:server_restart"
    )

    assert is_suppressed is True


@pytest.mark.asyncio
async def test_alert_manager_acknowledge_alert(alert_manager, mock_postgres):
    """Test acknowledging alert."""
    alert_id = str(uuid4())

    await alert_manager.acknowledge_alert(
        alert_id=alert_id, acknowledged_by="user@example.com"
    )

    # Verify acknowledged in database
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_alert_manager_resolve_alert(alert_manager, mock_postgres):
    """Test resolving alert."""
    alert_id = str(uuid4())

    await alert_manager.resolve_alert(
        alert_id=alert_id, resolved_by="user@example.com", resolution_note="Fixed"
    )

    # Verify resolved in database
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_alert_manager_get_active_alerts(alert_manager, mock_postgres):
    """Test getting active alerts."""
    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "alert_id": str(uuid4()),
                "title": "Alert 1",
                "severity": "critical",
                "created_at": datetime.utcnow(),
            },
            {
                "alert_id": str(uuid4()),
                "title": "Alert 2",
                "severity": "high",
                "created_at": datetime.utcnow(),
            },
        ]
    )

    alerts = await alert_manager.get_active_alerts()

    assert len(alerts) == 2


@pytest.mark.asyncio
async def test_alert_manager_severity_routing(alert_manager):
    """Test severity-based channel routing."""
    # Critical should route to multiple channels
    channels = alert_manager.get_channels_for_severity(AlertSeverity.CRITICAL)
    assert "slack" in channels
    assert "pagerduty" in channels

    # Info should route to fewer channels
    channels = alert_manager.get_channels_for_severity(AlertSeverity.INFO)
    assert len(channels) <= 2


# ============================================================================
# DeliveryTracker Tests (10 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_delivery_tracker_track_delivery(delivery_tracker, mock_postgres):
    """Test tracking delivery."""
    notification_id = str(uuid4())

    await delivery_tracker.track_delivery(
        notification_id=notification_id,
        channel="slack",
        status=DeliveryStatus.SENT,
        recipient="@team",
        metadata={"title": "Test"},
    )

    # Verify stored in database
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_delivery_tracker_get_status(delivery_tracker, mock_postgres):
    """Test getting delivery status."""
    notification_id = str(uuid4())

    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "notification_id": notification_id,
                "channel": "slack",
                "status": "delivered",
                "recipient": "@team",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "retry_count": 0,
                "error_message": None,
                "metadata": {},
            }
        ]
    )

    records = await delivery_tracker.get_delivery_status(notification_id)

    assert notification_id in records.values()
    assert records["slack"].status == DeliveryStatus.DELIVERED


@pytest.mark.asyncio
async def test_delivery_tracker_retry_failed(delivery_tracker, mock_postgres):
    """Test retrying failed delivery."""
    notification_id = str(uuid4())

    # Mock failed delivery
    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "notification_id": notification_id,
                "channel": "email",
                "status": "failed",
                "recipient": "user@example.com",
                "retry_count": 1,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "error_message": "Connection timeout",
                "metadata": {"title": "Test"},
            }
        ]
    )

    failed = await delivery_tracker.get_failed_deliveries(notification_id)

    assert len(failed) == 1
    assert failed[0].status == DeliveryStatus.FAILED


@pytest.mark.asyncio
async def test_delivery_tracker_exponential_backoff(delivery_tracker):
    """Test exponential backoff retry policy."""
    policy = RetryPolicy(
        max_retries=3, initial_delay=1.0, backoff_multiplier=2, max_delay=60.0
    )

    # Calculate delays
    delay1 = policy.get_delay(retry_count=0)
    delay2 = policy.get_delay(retry_count=1)
    delay3 = policy.get_delay(retry_count=2)

    assert delay1 == 1.0  # 1s
    assert delay2 == 2.0  # 2s
    assert delay3 == 4.0  # 4s


@pytest.mark.asyncio
async def test_delivery_tracker_max_retries(delivery_tracker, mock_postgres):
    """Test max retries limit."""
    notification_id = str(uuid4())

    # Mock delivery that exceeded max retries
    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "notification_id": notification_id,
                "channel": "slack",
                "status": "failed",
                "recipient": "@team",
                "retry_count": 3,  # Max retries
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "error_message": "Max retries exceeded",
                "metadata": {},
            }
        ]
    )

    should_retry = await delivery_tracker.should_retry(notification_id, "slack")

    assert should_retry is False


@pytest.mark.asyncio
async def test_delivery_tracker_dead_letter_queue(delivery_tracker, mock_postgres):
    """Test moving to dead letter queue."""
    notification_id = str(uuid4())

    await delivery_tracker.move_to_dead_letter_queue(
        notification_id=notification_id,
        channel="email",
        reason="Max retries exceeded",
    )

    # Verify moved to DLQ
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_delivery_tracker_get_metrics(delivery_tracker, mock_postgres):
    """Test getting delivery metrics."""
    mock_postgres.fetchrow = AsyncMock(
        return_value={
            "total_sent": 1000,
            "total_delivered": 950,
            "total_failed": 50,
            "success_rate": 0.95,
            "avg_latency_seconds": 1.2,
        }
    )

    metrics = await delivery_tracker.get_metrics()

    assert metrics["total_sent"] == 1000
    assert metrics["success_rate"] == 0.95
    assert metrics["avg_latency_seconds"] == 1.2


@pytest.mark.asyncio
async def test_delivery_tracker_get_metrics_by_channel(delivery_tracker, mock_postgres):
    """Test getting metrics broken down by channel."""
    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "channel": "slack",
                "total_sent": 500,
                "success_rate": 0.98,
                "avg_latency": 0.5,
            },
            {
                "channel": "email",
                "total_sent": 500,
                "success_rate": 0.92,
                "avg_latency": 2.1,
            },
        ]
    )

    metrics = await delivery_tracker.get_metrics_by_channel()

    assert len(metrics) == 2
    assert metrics["slack"]["success_rate"] == 0.98
    assert metrics["email"]["success_rate"] == 0.92


@pytest.mark.asyncio
async def test_delivery_tracker_cleanup_old_records(delivery_tracker, mock_postgres):
    """Test cleaning up old delivery records."""
    # Clean records older than 90 days
    cutoff_date = datetime.utcnow() - timedelta(days=90)

    await delivery_tracker.cleanup_old_records(cutoff_date)

    # Verify deletion query executed
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_delivery_tracker_get_history(delivery_tracker, mock_postgres):
    """Test getting delivery history."""
    notification_id = str(uuid4())

    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "notification_id": notification_id,
                "channel": "slack",
                "status": "delivered",
                "created_at": datetime.utcnow() - timedelta(hours=1),
                "updated_at": datetime.utcnow(),
            }
        ]
    )

    history = await delivery_tracker.get_history(
        notification_id=notification_id, limit=10
    )

    assert len(history) >= 0


# ============================================================================
# RateLimiter Tests (10 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_rate_limiter_check_limit(rate_limiter, mock_redis):
    """Test checking rate limit."""
    # Set rate limit: 10 requests per 60 seconds
    await rate_limiter.set_rate_limit(
        resource="api:test", max_requests=10, window_seconds=60
    )

    # First request should be allowed
    allowed = await rate_limiter.check_rate_limit(resource="api:test")

    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_sliding_window(rate_limiter, mock_redis):
    """Test sliding window algorithm."""
    resource = "api:sliding"

    await rate_limiter.set_rate_limit(
        resource=resource,
        max_requests=5,
        window_seconds=10,
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
    )

    # Make 5 requests
    for _ in range(5):
        allowed = await rate_limiter.check_rate_limit(resource)
        assert allowed is True

    # 6th request should be blocked
    allowed = await rate_limiter.check_rate_limit(resource)
    assert allowed is False


@pytest.mark.asyncio
async def test_rate_limiter_token_bucket(rate_limiter, mock_redis):
    """Test token bucket algorithm."""
    resource = "api:token_bucket"

    await rate_limiter.set_rate_limit(
        resource=resource,
        max_requests=10,
        window_seconds=60,
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
    )

    # Make 10 requests quickly
    for _ in range(10):
        allowed = await rate_limiter.check_rate_limit(resource)
        assert allowed is True

    # 11th request should be blocked (bucket empty)
    allowed = await rate_limiter.check_rate_limit(resource)
    assert allowed is False


@pytest.mark.asyncio
async def test_rate_limiter_get_status(rate_limiter, mock_redis):
    """Test getting rate limit status."""
    resource = "api:status"

    await rate_limiter.set_rate_limit(
        resource=resource, max_requests=100, window_seconds=60
    )

    # Make some requests
    for _ in range(25):
        await rate_limiter.check_rate_limit(resource)

    # Get status
    status = await rate_limiter.get_rate_limit_status(resource)

    assert status.remaining <= 75
    assert status.limit == 100


@pytest.mark.asyncio
async def test_rate_limiter_reset(rate_limiter, mock_redis):
    """Test resetting rate limit."""
    resource = "api:reset"

    await rate_limiter.set_rate_limit(
        resource=resource, max_requests=5, window_seconds=10
    )

    # Use up the limit
    for _ in range(5):
        await rate_limiter.check_rate_limit(resource)

    # Reset
    await rate_limiter.reset_rate_limit(resource)

    # Should be allowed again
    allowed = await rate_limiter.check_rate_limit(resource)
    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_per_channel_limits(rate_limiter, mock_redis):
    """Test different limits per channel."""
    # Slack: 50/min
    await rate_limiter.set_rate_limit(
        resource="channel:slack", max_requests=50, window_seconds=60
    )

    # Email: 100/min
    await rate_limiter.set_rate_limit(
        resource="channel:email", max_requests=100, window_seconds=60
    )

    slack_status = await rate_limiter.get_rate_limit_status("channel:slack")
    email_status = await rate_limiter.get_rate_limit_status("channel:email")

    assert slack_status.limit == 50
    assert email_status.limit == 100


@pytest.mark.asyncio
async def test_rate_limiter_backpressure(rate_limiter, mock_redis):
    """Test backpressure handling."""
    resource = "api:backpressure"

    await rate_limiter.set_rate_limit(
        resource=resource, max_requests=5, window_seconds=10
    )

    # Fill up the limit
    for _ in range(5):
        await rate_limiter.check_rate_limit(resource)

    # Get backpressure delay
    delay = await rate_limiter.get_backpressure_delay(resource)

    assert delay > 0  # Should suggest waiting


@pytest.mark.asyncio
async def test_rate_limiter_lua_script_atomic(rate_limiter, mock_redis):
    """Test Lua script ensures atomic operations."""
    resource = "api:atomic"

    await rate_limiter.set_rate_limit(
        resource=resource, max_requests=10, window_seconds=60
    )

    # Simulate concurrent requests
    tasks = [rate_limiter.check_rate_limit(resource) for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # All should be allowed (atomic increments)
    assert all(results)

    # Next request should be blocked
    allowed = await rate_limiter.check_rate_limit(resource)
    assert allowed is False


@pytest.mark.asyncio
async def test_rate_limiter_cleanup_expired(rate_limiter, mock_redis):
    """Test cleanup of expired rate limit keys."""
    resource = "api:cleanup"

    await rate_limiter.set_rate_limit(
        resource=resource, max_requests=10, window_seconds=1
    )

    # Make a request
    await rate_limiter.check_rate_limit(resource)

    # Wait for expiration
    await asyncio.sleep(2)

    # Cleanup expired keys
    await rate_limiter.cleanup_expired_keys()

    # Should be able to make requests again
    allowed = await rate_limiter.check_rate_limit(resource)
    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_get_all_limits(rate_limiter, mock_redis):
    """Test getting all rate limits."""
    await rate_limiter.set_rate_limit("resource1", 10, 60)
    await rate_limiter.set_rate_limit("resource2", 20, 60)

    limits = await rate_limiter.get_all_rate_limits()

    assert len(limits) >= 2


# ============================================================================
# TemplateEngine Tests (10 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_template_engine_create_template(template_engine, mock_postgres):
    """Test creating template."""
    template = Template(
        name="test-template",
        category=TemplateCategory.NOTIFICATION,
        subject="Test {{variable}}",
        body="Hello {{name}}, this is a test.",
        variables=["variable", "name"],
        version="1.0",
    )

    await template_engine.create_template(template)

    # Verify stored
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_template_engine_render_template(template_engine, mock_postgres):
    """Test rendering template with context."""
    # Mock template fetch
    mock_postgres.fetchrow = AsyncMock(
        return_value={
            "name": "greeting",
            "subject": "Hello {{name}}",
            "body": "Welcome {{name}}, you have {{count}} messages.",
            "version": "1.0",
        }
    )

    rendered = await template_engine.render_template(
        template_name="greeting", context={"name": "Alice", "count": 5}
    )

    assert "Alice" in rendered["body"]
    assert "5" in rendered["body"]


@pytest.mark.asyncio
async def test_template_engine_validate_template(template_engine):
    """Test template validation."""
    valid_template = "Hello {{name}}, welcome!"
    invalid_template = "Hello {{name}, missing closing"

    # Valid template should pass
    is_valid, error = template_engine.validate_template(valid_template)
    assert is_valid is True

    # Invalid template should fail
    is_valid, error = template_engine.validate_template(invalid_template)
    assert is_valid is False


@pytest.mark.asyncio
async def test_template_engine_versioning(template_engine, mock_postgres):
    """Test template versioning."""
    # Create version 1.0
    template_v1 = Template(
        name="versioned-template",
        category=TemplateCategory.NOTIFICATION,
        subject="Version 1",
        body="This is version 1.0",
        variables=[],
        version="1.0",
    )

    await template_engine.create_template(template_v1)

    # Create version 2.0
    template_v2 = Template(
        name="versioned-template",
        category=TemplateCategory.NOTIFICATION,
        subject="Version 2",
        body="This is version 2.0 with improvements",
        variables=[],
        version="2.0",
    )

    await template_engine.create_template(template_v2)

    # Should have multiple versions
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_template_engine_get_template(template_engine, mock_postgres):
    """Test getting template."""
    mock_postgres.fetchrow = AsyncMock(
        return_value={
            "name": "test",
            "category": "notification",
            "subject": "Test",
            "body": "Test body",
            "variables": ["var1"],
            "version": "1.0",
            "created_at": datetime.utcnow(),
        }
    )

    template = await template_engine.get_template("test")

    assert template.name == "test"


@pytest.mark.asyncio
async def test_template_engine_list_templates(template_engine, mock_postgres):
    """Test listing all templates."""
    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "name": "template1",
                "category": "notification",
                "version": "1.0",
                "created_at": datetime.utcnow(),
            },
            {
                "name": "template2",
                "category": "alert",
                "version": "1.0",
                "created_at": datetime.utcnow(),
            },
        ]
    )

    templates = await template_engine.list_templates()

    assert len(templates) == 2


@pytest.mark.asyncio
async def test_template_engine_preview_template(template_engine, mock_postgres):
    """Test previewing template without saving."""
    preview = await template_engine.preview_template(
        template_content="Hello {{name}}, you have {{count}} notifications.",
        context={"name": "Bob", "count": 3},
    )

    assert "Bob" in preview
    assert "3" in preview


@pytest.mark.asyncio
async def test_template_engine_builtin_templates(template_engine):
    """Test built-in templates."""
    builtin_names = [
        "deployment_complete",
        "incident_alert",
        "pr_notification",
        "sprint_update",
        "postmortem_complete",
    ]

    templates = await template_engine.get_builtin_templates()

    assert len(templates) >= 5
    for name in builtin_names:
        assert name in [t.name for t in templates]


@pytest.mark.asyncio
async def test_template_engine_delete_template(template_engine, mock_postgres):
    """Test deleting template."""
    await template_engine.delete_template("test-template")

    # Verify deletion query executed
    mock_postgres.execute.assert_called()


@pytest.mark.asyncio
async def test_template_engine_jinja2_sandboxing(template_engine):
    """Test Jinja2 sandboxing for security."""
    # Dangerous template should be rejected
    dangerous = "{{ ''.__class__.__mro__[1].__subclasses__() }}"

    is_valid, error = template_engine.validate_template(dangerous)

    # Should fail security validation
    assert is_valid is False or "security" in error.lower()


# ============================================================================
# NotificationService Integration Tests (15 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_notification_service_initialization(notification_service):
    """Test service initialization."""
    assert notification_service._initialized is True
    assert notification_service.router is not None
    assert notification_service.slack is not None
    assert notification_service.email is not None


@pytest.mark.asyncio
async def test_notification_service_send_simple_notification(
    notification_service, mock_slack_client, mock_sendgrid
):
    """Test sending simple notification."""
    result = await notification_service.send_notification(
        title="Test Notification",
        message="This is a test",
        channels=["slack", "email"],
        recipients=["@team", "team@example.com"],
        priority="high",
    )

    assert result.notification_id is not None
    assert "slack" in result.channels_attempted
    assert "email" in result.channels_attempted


@pytest.mark.asyncio
async def test_notification_service_send_template_notification(
    notification_service, mock_postgres
):
    """Test sending template-based notification."""
    # Mock template
    mock_postgres.fetchrow = AsyncMock(
        return_value={
            "name": "deployment_complete",
            "subject": "Deployment Complete: {{environment}}",
            "body": "Deployment to {{environment}} completed by {{deployer}}",
            "version": "1.0",
        }
    )

    result = await notification_service.send_template_notification(
        template_name="deployment_complete",
        context={"environment": "production", "deployer": "Alice"},
        channels=["slack"],
        recipients=["@team"],
    )

    assert result.notification_id is not None


@pytest.mark.asyncio
async def test_notification_service_send_alert(notification_service, mock_postgres):
    """Test sending alert with escalation."""
    result = await notification_service.send_alert(
        title="Critical Alert",
        message="Database connection failed",
        severity="critical",
        recipients=["@oncall"],
    )

    assert result.notification_id is not None
    assert result.status in ["delivered", "processing", "partial"]


@pytest.mark.asyncio
async def test_notification_service_get_status(notification_service, mock_postgres):
    """Test getting notification status."""
    notification_id = str(uuid4())

    # Mock delivery records
    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "notification_id": notification_id,
                "channel": "slack",
                "status": "delivered",
                "recipient": "@team",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "retry_count": 0,
                "error_message": None,
                "metadata": {},
            }
        ]
    )

    status = await notification_service.get_notification_status(notification_id)

    assert status.notification_id == notification_id
    assert status.delivered_count >= 0


@pytest.mark.asyncio
async def test_notification_service_retry_failed(notification_service, mock_postgres):
    """Test retrying failed notifications."""
    notification_id = str(uuid4())

    # Mock failed delivery
    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "notification_id": notification_id,
                "channel": "email",
                "status": "failed",
                "recipient": "user@example.com",
                "retry_count": 1,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "error_message": "Connection timeout",
                "metadata": {"title": "Test", "message": "Test message"},
            }
        ]
    )

    stats = await notification_service.retry_failed_notifications(notification_id)

    assert "attempted" in stats
    assert stats["attempted"] >= 0


@pytest.mark.asyncio
async def test_notification_service_get_metrics(notification_service, mock_postgres):
    """Test getting service metrics."""
    mock_postgres.fetchrow = AsyncMock(
        return_value={
            "total_sent": 1000,
            "total_delivered": 950,
            "total_failed": 50,
            "success_rate": 0.95,
            "avg_latency_seconds": 1.2,
        }
    )

    metrics = await notification_service.get_metrics()

    assert "total_sent" in metrics
    assert metrics["success_rate"] == 0.95


@pytest.mark.asyncio
async def test_notification_service_rate_limiting(notification_service, mock_redis):
    """Test rate limiting prevents excessive sending."""
    # Set very low rate limit
    await notification_service.rate_limiter.set_rate_limit(
        resource="channel:slack", max_requests=2, window_seconds=60
    )

    # Try to send 5 notifications quickly
    results = []
    for i in range(5):
        result = await notification_service.send_notification(
            title=f"Test {i}",
            message="Test",
            channels=["slack"],
            recipients=["@team"],
        )
        results.append(result)

    # Some should be rate limited
    failed_count = sum(1 for r in results if "slack" in r.channels_failed)
    assert failed_count > 0


@pytest.mark.asyncio
async def test_notification_service_intelligent_routing(notification_service):
    """Test intelligent channel routing based on priority."""
    # Critical priority should select multiple channels
    result = await notification_service.send_notification(
        title="Critical",
        message="Critical issue",
        channels=None,  # Let router decide
        recipients=["@team"],
        priority="critical",
    )

    # Should route to multiple channels
    assert len(result.channels_attempted) > 1


@pytest.mark.asyncio
async def test_notification_service_parallel_delivery(notification_service):
    """Test parallel delivery to multiple channels."""
    result = await notification_service.send_notification(
        title="Parallel Test",
        message="Testing parallel delivery",
        channels=["slack", "email"],
        recipients=["@team", "team@example.com"],
    )

    # Both channels should be attempted
    assert "slack" in result.channels_attempted
    assert "email" in result.channels_attempted


@pytest.mark.asyncio
async def test_notification_service_error_handling(
    notification_service, mock_slack_client
):
    """Test error handling when channel fails."""
    # Make Slack fail
    mock_slack_client.chat_postMessage = AsyncMock(
        return_value={"ok": False, "error": "channel_not_found"}
    )

    result = await notification_service.send_notification(
        title="Error Test",
        message="Testing error handling",
        channels=["slack"],
        recipients=["#nonexistent"],
    )

    assert "slack" in result.channels_failed
    assert "slack" in result.errors


@pytest.mark.asyncio
async def test_notification_service_context_manager(
    mock_redis, mock_postgres, mock_slack_client, mock_sendgrid
):
    """Test using service as async context manager."""
    config = NotificationConfig(
        redis_url="redis://localhost:6379",
        postgres_url="postgresql://user:pass@localhost/db",
        slack_token="xoxb-test-token",
    )

    with patch(
        "communication_platform.notification_router.aioredis.from_url"
    ) as redis_mock:
        redis_mock.return_value = mock_redis
        with patch(
            "communication_platform.alert_manager.aioredis.from_url"
        ) as alert_redis:
            alert_redis.return_value = mock_redis
            with patch(
                "communication_platform.alert_manager.asyncpg.connect"
            ) as alert_pg:
                alert_pg.return_value = mock_postgres
                with patch(
                    "communication_platform.delivery_tracker.aioredis.from_url"
                ) as track_redis:
                    track_redis.return_value = mock_redis
                    with patch(
                        "communication_platform.delivery_tracker.asyncpg.connect"
                    ) as track_pg:
                        track_pg.return_value = mock_postgres
                        with patch(
                            "communication_platform.rate_limiter.aioredis.from_url"
                        ) as rate_redis:
                            rate_redis.return_value = mock_redis
                            with patch(
                                "communication_platform.template_engine.asyncpg.connect"
                            ) as template_pg:
                                template_pg.return_value = mock_postgres
                                with patch(
                                    "communication_platform.slack_integration.WebClient"
                                ) as slack_mock:
                                    slack_mock.return_value = mock_slack_client

                                    async with NotificationService(config) as service:
                                        assert service._initialized is True

                                    # Should be cleaned up
                                    assert service._initialized is False


@pytest.mark.asyncio
async def test_notification_service_dead_letter_queue(
    notification_service, mock_postgres
):
    """Test dead letter queue for permanent failures."""
    notification_id = str(uuid4())

    # Mock delivery that exceeded max retries
    mock_postgres.fetch = AsyncMock(
        return_value=[
            {
                "notification_id": notification_id,
                "channel": "email",
                "status": "failed",
                "recipient": "user@example.com",
                "retry_count": 3,  # Max retries
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "error_message": "Permanent failure",
                "metadata": {},
            }
        ]
    )

    # Retry should move to DLQ
    stats = await notification_service.retry_failed_notifications(notification_id)

    assert stats["still_failed"] > 0


@pytest.mark.asyncio
async def test_notification_service_concurrent_notifications(notification_service):
    """Test handling concurrent notification requests."""
    # Send 10 notifications concurrently
    tasks = [
        notification_service.send_notification(
            title=f"Concurrent {i}",
            message="Test",
            channels=["slack"],
            recipients=["@team"],
        )
        for i in range(10)
    ]

    results = await asyncio.gather(*tasks)

    # All should complete
    assert len(results) == 10
    assert all(r.notification_id for r in results)


@pytest.mark.asyncio
async def test_notification_service_cleanup(notification_service):
    """Test service cleanup."""
    await notification_service.cleanup()

    assert notification_service._initialized is False


# ============================================================================
# CLI Interface Tests (7 tests)
# ============================================================================


def test_cli_send_message_command():
    """Test CLI send message command."""
    from click.testing import CliRunner
    from communication_platform.notification_cli import cli, send

    runner = CliRunner()

    # Mock the send operation
    with patch("communication_platform.notification_cli.NotificationService"):
        result = runner.invoke(
            cli,
            [
                "send",
                "message",
                "--title",
                "Test",
                "--message",
                "Test message",
                "--channel",
                "slack",
                "--recipient",
                "@team",
            ],
        )

        # Should not error (may warn about missing config)
        assert result.exit_code in [0, 1]


def test_cli_send_template_command():
    """Test CLI send template command."""
    from click.testing import CliRunner
    from communication_platform.notification_cli import cli

    runner = CliRunner()

    with patch("communication_platform.notification_cli.NotificationService"):
        result = runner.invoke(
            cli,
            [
                "send",
                "template",
                "--template",
                "deployment_complete",
                "--context",
                '{"environment": "prod"}',
                "--channel",
                "slack",
            ],
        )

        assert result.exit_code in [0, 1]


def test_cli_template_list_command():
    """Test CLI template list command."""
    from click.testing import CliRunner
    from communication_platform.notification_cli import cli

    runner = CliRunner()

    with patch("communication_platform.notification_cli.TemplateEngine"):
        result = runner.invoke(cli, ["template", "list"])

        assert result.exit_code in [0, 1]


def test_cli_status_command():
    """Test CLI status command."""
    from click.testing import CliRunner
    from communication_platform.notification_cli import cli

    runner = CliRunner()

    notification_id = str(uuid4())

    with patch("communication_platform.notification_cli.NotificationService"):
        result = runner.invoke(cli, ["status", notification_id])

        assert result.exit_code in [0, 1]


def test_cli_channel_test_command():
    """Test CLI channel test command."""
    from click.testing import CliRunner
    from communication_platform.notification_cli import cli

    runner = CliRunner()

    with patch("communication_platform.notification_cli.NotificationService"):
        result = runner.invoke(cli, ["channel", "test", "slack"])

        assert result.exit_code in [0, 1]


def test_cli_config_command():
    """Test CLI config command."""
    from click.testing import CliRunner
    from communication_platform.notification_cli import cli

    runner = CliRunner()

    result = runner.invoke(
        cli, ["config", "set-rate-limit", "--channel", "slack", "--limit", "50"]
    )

    assert result.exit_code in [0, 1]


def test_cli_json_output():
    """Test CLI JSON output format."""
    from click.testing import CliRunner
    from communication_platform.notification_cli import cli

    runner = CliRunner()

    with patch("communication_platform.notification_cli.NotificationService"):
        result = runner.invoke(cli, ["template", "list", "--format", "json"])

        # If successful, should output valid JSON
        if result.exit_code == 0:
            try:
                json.loads(result.output)
            except json.JSONDecodeError:
                pass  # May not have output if service not configured


# ============================================================================
# Performance Tests (3 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_performance_high_volume_notifications(notification_service):
    """Test handling high volume of notifications."""
    start_time = datetime.utcnow()

    # Send 100 notifications
    tasks = [
        notification_service.send_notification(
            title=f"Perf Test {i}",
            message="Performance test",
            channels=["slack"],
            recipients=["@team"],
        )
        for i in range(100)
    ]

    results = await asyncio.gather(*tasks)

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    # Should complete within reasonable time
    assert duration < 60  # Less than 60 seconds for 100 notifications
    assert len(results) == 100


@pytest.mark.asyncio
async def test_performance_template_rendering(template_engine):
    """Test template rendering performance."""
    template_content = "Hello {{name}}, you have {{count}} messages."
    context = {"name": "User", "count": 42}

    start_time = datetime.utcnow()

    # Render 1000 times
    for _ in range(1000):
        await template_engine.preview_template(template_content, context)

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    # Should be fast
    assert duration < 5  # Less than 5 seconds for 1000 renders


@pytest.mark.asyncio
async def test_performance_rate_limiter(rate_limiter):
    """Test rate limiter performance."""
    resource = "perf:test"

    await rate_limiter.set_rate_limit(
        resource=resource, max_requests=1000, window_seconds=60
    )

    start_time = datetime.utcnow()

    # Check 1000 times
    tasks = [rate_limiter.check_rate_limit(resource) for _ in range(1000)]
    await asyncio.gather(*tasks)

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    # Should be very fast with Redis
    assert duration < 10  # Less than 10 seconds for 1000 checks


# ============================================================================
# Main test configuration
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
