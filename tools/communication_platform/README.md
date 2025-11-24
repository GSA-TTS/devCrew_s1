# Communication & Notification Platform (TOOL-COMM-001)

Multi-channel notification and stakeholder communication platform enabling autonomous agents and humans to send notifications across Slack, Email, Microsoft Teams, and PagerDuty with template-based messaging, delivery tracking, escalation rules, and rate limiting.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Python API](#python-api)
  - [CLI Interface](#cli-interface)
- [Components](#components)
- [Templates](#templates)
- [Escalation Policies](#escalation-policies)
- [Monitoring & Metrics](#monitoring--metrics)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Communication & Notification Platform provides a unified interface for sending notifications across multiple channels with intelligent routing, template-based messaging, delivery tracking, and automatic retries. Designed for autonomous agent systems and DevOps workflows.

### Supported Protocols

- **P-OPS-POSTMORTEM**: Postmortem completion notifications
- **P-STAKEHOLDER-COMM**: Stakeholder communication workflows
- **CA-CS-NotifyHuman**: Agent-to-human notifications
- **P-HUB-SPOKE-COORDINATION**: Hub-spoke coordination updates
- **P-OBSERVABILITY**: System health and monitoring alerts
- **P-SYSTEM-NOTIFY**: Infrastructure event notifications

### Supported Channels

- **Slack**: Rich messages with Block Kit, interactive buttons, file uploads, threading
- **Email**: HTML/plain-text emails via SendGrid or SMTP with attachments
- **Microsoft Teams**: (Planned) Adaptive Cards and webhook integration
- **PagerDuty**: (Planned) Incident creation and escalation
- **SMS**: (Planned) Twilio integration

## Features

### Core Capabilities

- **Multi-Channel Routing**: Automatically route notifications to appropriate channels based on priority and severity
- **Template Engine**: Jinja2-based templates with versioning and built-in templates for common scenarios
- **Delivery Tracking**: Track notification delivery status with PostgreSQL persistence
- **Automatic Retries**: Exponential backoff retry logic (1s → 2s → 4s, max 3 retries)
- **Rate Limiting**: Redis-based rate limiting with sliding window and token bucket algorithms
- **Escalation Policies**: Multi-level escalation with time-based triggers
- **Alert Deduplication**: Prevent duplicate alerts within configurable time windows
- **Dead Letter Queue**: Capture permanently failed notifications for analysis
- **CLI Interface**: Complete command-line tool for notification management

### Advanced Features

- **Intelligent Routing**: Automatic channel selection based on:
  - Message priority (low, medium, high, critical)
  - Severity level (info, warning, error, critical)
  - Custom routing rules with pattern matching
  - Recipient preferences

- **Template Management**:
  - Jinja2 template engine with sandboxing
  - Template versioning (v1.0, v2.0, etc.)
  - 5 built-in templates (deployment, incident, PR, sprint, postmortem)
  - Custom template creation with validation
  - Template preview without sending

- **Delivery Assurance**:
  - Per-channel delivery status tracking
  - Exponential backoff retries with jitter
  - Dead letter queue for permanent failures
  - Delivery metrics and analytics
  - 90-day retention with automatic cleanup

- **Rate Limiting**:
  - Per-channel rate limits (Slack: 50/min, Email: 100/min)
  - Sliding window algorithm for smooth throttling
  - Token bucket for burst handling
  - Lua scripts for atomic Redis operations
  - Backpressure feedback

- **Alert Management**:
  - Multi-level escalation policies
  - Time-based escalation triggers
  - Alert acknowledgment and resolution tracking
  - Suppression rules for maintenance windows
  - Severity-based routing

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NotificationService                          │
│                   (Main Orchestration)                          │
└───────────┬─────────────────────────────────────────────────────┘
            │
            ├──> NotificationRouter ──> Redis Queue
            │         │
            │         ├──> Routing Rules Engine
            │         └──> Channel Selection Logic
            │
            ├──> RateLimiter (Redis)
            │         │
            │         ├──> Sliding Window Algorithm
            │         └──> Token Bucket Algorithm
            │
            ├──> Channel Integrations
            │         │
            │         ├──> SlackIntegration (Block Kit, WebClient)
            │         ├──> EmailService (SendGrid/SMTP)
            │         ├──> TeamsIntegration (Planned)
            │         └──> PagerDutyIntegration (Planned)
            │
            ├──> DeliveryTracker (PostgreSQL + Redis)
            │         │
            │         ├──> Delivery Log (90-day retention)
            │         ├──> Retry Queue (exponential backoff)
            │         └──> Dead Letter Queue
            │
            ├──> AlertManager (PostgreSQL + Redis)
            │         │
            │         ├──> Escalation Policies
            │         ├──> Alert Deduplication
            │         └──> Suppression Rules
            │
            └──> TemplateEngine (PostgreSQL + Jinja2)
                      │
                      ├──> Template Storage (versioned)
                      ├──> Jinja2 Sandbox
                      └──> Built-in Templates
```

### Data Flow

1. **Notification Request** → NotificationService
2. **Route Selection** → NotificationRouter applies routing rules
3. **Rate Limit Check** → RateLimiter validates request quota
4. **Channel Delivery** → SlackIntegration / EmailService send notification
5. **Status Tracking** → DeliveryTracker logs delivery status
6. **Retry Logic** → Failed deliveries queued for retry with exponential backoff
7. **Escalation** → AlertManager triggers escalation if needed

### Technology Stack

- **Python 3.10+**: Core language with type hints throughout
- **Redis 7.2+**: Message queuing, rate limiting, caching
- **PostgreSQL 15+**: Notification history, templates, delivery tracking
- **Slack SDK 3.23+**: Native Slack integration with Block Kit
- **SendGrid 6.11+**: Transactional email delivery
- **Jinja2 3.1+**: Template engine with sandboxing
- **Celery 5.3+**: Asynchronous task processing (optional)
- **Pydantic 2.5+**: Data validation and serialization

## Installation

### Prerequisites

- Python 3.10 or higher
- Redis 7.2+ (for queuing and rate limiting)
- PostgreSQL 15+ (for persistence)
- (Optional) Slack workspace with bot token
- (Optional) SendGrid API key or SMTP server

### Install via pip

```bash
pip install communication-platform
```

### Install from source

```bash
git clone https://github.com/devCrew_s1/communication-platform.git
cd communication-platform
pip install -e .
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Docker Setup (Recommended)

```bash
# Start Redis and PostgreSQL
docker-compose up -d

# The docker-compose.yml includes:
# - Redis 7.2 (port 6379)
# - PostgreSQL 15 (port 5432)
# - Volumes for data persistence
```

## Quick Start

### Python API

```python
import asyncio
from communication_platform import NotificationService, NotificationConfig

async def main():
    # Configure service
    config = NotificationConfig(
        redis_url="redis://localhost:6379",
        postgres_url="postgresql://user:pass@localhost/notifications",
        slack_token="xoxb-your-slack-token",
        sendgrid_api_key="SG.your-sendgrid-key",
        default_from_email="notifications@company.com"
    )

    # Initialize service
    async with NotificationService(config) as service:
        # Send simple notification
        result = await service.send_notification(
            title="Deployment Complete",
            message="Production deployment v2.1.0 successful",
            channels=["slack", "email"],
            recipients=["@team-ops", "ops@company.com"],
            priority="high"
        )

        print(f"Notification {result.notification_id} sent!")
        print(f"Succeeded: {result.channels_succeeded}")
        print(f"Failed: {result.channels_failed}")

asyncio.run(main())
```

### CLI Interface

```bash
# Send a simple notification
notification-cli send message \
    --title "Deployment Complete" \
    --message "Production deployment successful" \
    --channel slack \
    --recipient "@team-ops" \
    --priority high

# Send using a template
notification-cli send template \
    --template deployment_complete \
    --context '{"environment": "production", "version": "v2.1.0"}' \
    --channel slack \
    --recipient "@team-ops"

# Check notification status
notification-cli status <notification-id>

# List available templates
notification-cli template list

# Test a channel
notification-cli channel test slack
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# PostgreSQL Configuration
POSTGRES_URL=postgresql://user:password@localhost:5432/notifications

# Slack Configuration (optional)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# SendGrid Configuration (optional)
SENDGRID_API_KEY=SG.your-api-key

# SMTP Configuration (alternative to SendGrid)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Default Settings
DEFAULT_FROM_EMAIL=notifications@company.com
NOTIFICATION_RETENTION_DAYS=90

# Rate Limits (requests per minute)
RATE_LIMIT_SLACK=50
RATE_LIMIT_EMAIL=100
RATE_LIMIT_TEAMS=60
RATE_LIMIT_PAGERDUTY=60

# Retry Policy
MAX_RETRIES=3
RETRY_BACKOFF_MULTIPLIER=2
RETRY_INITIAL_DELAY=1.0
```

### Configuration Object

```python
from communication_platform import NotificationConfig

config = NotificationConfig(
    redis_url="redis://localhost:6379",
    postgres_url="postgresql://user:pass@localhost/db",

    # Slack configuration
    slack_token="xoxb-...",
    slack_signing_secret="...",

    # Email configuration
    sendgrid_api_key="SG....",
    default_from_email="notifications@company.com",

    # Rate limits (per minute)
    rate_limits={
        "slack": 50,
        "email": 100,
        "teams": 60,
        "pagerduty": 60,
    },

    # Retry policy
    retry_policy={
        "max_retries": 3,
        "backoff_multiplier": 2,
        "initial_delay": 1.0,
    },

    # Other settings
    enable_dead_letter_queue=True,
    retention_days=90,
)
```

### Slack Bot Setup

1. Create a Slack App at https://api.slack.com/apps
2. Add Bot Token Scopes:
   - `chat:write` - Send messages
   - `chat:write.public` - Send to public channels
   - `files:write` - Upload files
   - `channels:read` - List channels
   - `users:read` - Read user info
3. Install app to workspace
4. Copy Bot Token (xoxb-...)
5. Copy Signing Secret

### SendGrid Setup

1. Sign up at https://sendgrid.com
2. Create API Key with "Mail Send" permission
3. Verify sender email address
4. Copy API key (SG....)

### Database Initialization

The platform automatically creates required tables on first run:

```sql
-- Delivery tracking
CREATE TABLE delivery_log (...)
CREATE TABLE dead_letter_queue (...)

-- Templates
CREATE TABLE templates (...)
CREATE TABLE template_versions (...)

-- Alerts
CREATE TABLE escalation_policies (...)
CREATE TABLE alerts (...)
```

Manual initialization (optional):

```bash
# Run database migrations
python -m communication_platform.migrations.init_db \
    --postgres-url "postgresql://user:pass@localhost/db"
```

## Usage

### Python API

#### Basic Notification

```python
import asyncio
from communication_platform import NotificationService, NotificationConfig

async def send_basic_notification():
    config = NotificationConfig(
        redis_url="redis://localhost:6379",
        postgres_url="postgresql://user:pass@localhost/db",
        slack_token="xoxb-...",
        sendgrid_api_key="SG....",
    )

    async with NotificationService(config) as service:
        result = await service.send_notification(
            title="System Alert",
            message="CPU usage exceeded 90%",
            channels=["slack", "email"],
            recipients=["@ops-team", "ops@company.com"],
            priority="high",
            severity="warning",
            tags=["monitoring", "cpu"],
            metadata={"server": "prod-01", "cpu_usage": 92.5}
        )

        print(f"Notification ID: {result.notification_id}")
        print(f"Status: {result.status}")
        print(f"Succeeded: {result.channels_succeeded}")

asyncio.run(send_basic_notification())
```

#### Template-Based Notification

```python
async def send_template_notification():
    async with NotificationService(config) as service:
        # Send deployment notification using built-in template
        result = await service.send_template_notification(
            template_name="deployment_complete",
            context={
                "environment": "production",
                "version": "v2.1.0",
                "deployer": "Alice",
                "duration": "5m 23s",
                "status": "success"
            },
            channels=["slack", "email"],
            recipients=["@team-ops", "team@company.com"],
            priority="medium"
        )

        return result.notification_id
```

#### Alert with Escalation

```python
async def send_alert_with_escalation():
    async with NotificationService(config) as service:
        # Create escalation policy
        from communication_platform import EscalationPolicy, EscalationLevel

        policy = EscalationPolicy(
            name="Critical Incident",
            levels=[
                EscalationLevel(
                    level=1,
                    delay_minutes=0,
                    channels=["slack"],
                    recipients=["@team-ops"]
                ),
                EscalationLevel(
                    level=2,
                    delay_minutes=15,
                    channels=["slack", "pagerduty"],
                    recipients=["@team-leads", "oncall"]
                ),
                EscalationLevel(
                    level=3,
                    delay_minutes=30,
                    channels=["slack", "pagerduty", "email"],
                    recipients=["@engineering", "executives@company.com"]
                )
            ]
        )

        # Save policy
        await service.alert_manager.create_policy(policy)

        # Send alert
        result = await service.send_alert(
            title="Database Connection Failed",
            message="Unable to connect to primary database",
            severity="critical",
            escalation_policy_id=policy.id,
            recipients=["@team-ops"],
            metadata={"database": "prod-db-01", "error": "Connection timeout"}
        )

        return result.notification_id
```

#### Check Notification Status

```python
async def check_notification_status(notification_id: str):
    async with NotificationService(config) as service:
        status = await service.get_notification_status(notification_id)

        print(f"Notification: {status.notification_id}")
        print(f"Status: {status.status}")
        print(f"Delivered: {status.delivered_count}/{len(status.delivery_records)}")
        print(f"Failed: {status.failed_count}")
        print(f"Pending: {status.pending_count}")

        # Check individual channels
        for channel, record in status.delivery_records.items():
            print(f"\n{channel}:")
            print(f"  Status: {record.status}")
            print(f"  Recipient: {record.recipient}")
            print(f"  Retries: {record.retry_count}")
            if record.error_message:
                print(f"  Error: {record.error_message}")
```

#### Retry Failed Notifications

```python
async def retry_failed():
    async with NotificationService(config) as service:
        # Retry all failed notifications
        stats = await service.retry_failed_notifications()

        print(f"Attempted: {stats['attempted']}")
        print(f"Succeeded: {stats['succeeded']}")
        print(f"Still Failed: {stats['still_failed']}")

        # Retry specific notification
        stats = await service.retry_failed_notifications(
            notification_id="specific-id"
        )
```

#### Get Metrics

```python
from datetime import datetime, timedelta

async def get_delivery_metrics():
    async with NotificationService(config) as service:
        # Get metrics for last 24 hours
        metrics = await service.get_metrics(
            start_date=datetime.utcnow() - timedelta(hours=24),
            end_date=datetime.utcnow()
        )

        print(f"Total Sent: {metrics['total_sent']}")
        print(f"Success Rate: {metrics['success_rate']:.2%}")
        print(f"Avg Latency: {metrics['avg_latency_seconds']:.2f}s")

        # Metrics by channel
        for channel, data in metrics['by_channel'].items():
            print(f"\n{channel}:")
            print(f"  Sent: {data['total_sent']}")
            print(f"  Success Rate: {data['success_rate']:.2%}")
            print(f"  Avg Latency: {data['avg_latency']:.2f}s")
```

### CLI Interface

#### Installation

The CLI is included with the package:

```bash
pip install communication-platform

# Verify installation
notification-cli --version
```

#### Configuration

Create `~/.notification-cli.yaml`:

```yaml
redis_url: redis://localhost:6379
postgres_url: postgresql://user:pass@localhost/notifications

slack:
  token: xoxb-your-token
  signing_secret: your-secret

email:
  sendgrid_api_key: SG.your-key
  default_from: notifications@company.com

# Or use SMTP
smtp:
  host: smtp.gmail.com
  port: 587
  username: your-email@gmail.com
  password: your-app-password

rate_limits:
  slack: 50
  email: 100

retention_days: 90
```

#### Send Commands

**Simple Message:**

```bash
notification-cli send message \
    --title "Deployment Complete" \
    --message "Production deployment v2.1.0 successful" \
    --channel slack \
    --channel email \
    --recipient "@team-ops" \
    --recipient "ops@company.com" \
    --priority high \
    --severity info \
    --tag deployment \
    --tag production
```

**Template-Based:**

```bash
notification-cli send template \
    --template deployment_complete \
    --context '{"environment": "production", "version": "v2.1.0", "deployer": "Alice"}' \
    --channel slack \
    --recipient "@team-ops"
```

**Alert with Escalation:**

```bash
notification-cli send alert \
    --title "Database Connection Failed" \
    --message "Unable to connect to primary database" \
    --severity critical \
    --escalation-policy critical-incident \
    --recipient "@team-ops"
```

#### Template Commands

**List Templates:**

```bash
# List all templates
notification-cli template list

# List in JSON format
notification-cli template list --format json

# Filter by category
notification-cli template list --category alert
```

**Preview Template:**

```bash
notification-cli template preview deployment_complete \
    --context '{"environment": "staging", "version": "v1.0.0"}'
```

**Create Template:**

```bash
notification-cli template create \
    --name custom-alert \
    --category alert \
    --subject "Alert: {{title}}" \
    --body "{{message}}\n\nSeverity: {{severity}}" \
    --variable title \
    --variable message \
    --variable severity
```

**Delete Template:**

```bash
notification-cli template delete custom-alert
```

#### Status Commands

**Check Status:**

```bash
# Get notification status
notification-cli status <notification-id>

# Get status in JSON format
notification-cli status <notification-id> --format json
```

**View History:**

```bash
# View notification history (last 24 hours)
notification-cli status history --hours 24

# View with filters
notification-cli status history \
    --channel slack \
    --status delivered \
    --limit 100
```

**Retry Failed:**

```bash
# Retry all failed notifications
notification-cli status retry-failed

# Retry specific notification
notification-cli status retry-failed --notification-id <id>
```

#### Channel Commands

**Test Channel:**

```bash
# Test Slack integration
notification-cli channel test slack

# Test Email integration
notification-cli channel test email
```

**List Channels:**

```bash
notification-cli channel list
```

**Add Channel:**

```bash
notification-cli channel add teams \
    --webhook-url "https://outlook.office.com/webhook/..."
```

#### Config Commands

**View Config:**

```bash
notification-cli config show
```

**Set Rate Limit:**

```bash
notification-cli config set-rate-limit \
    --channel slack \
    --limit 50 \
    --window 60
```

**Set Retention:**

```bash
notification-cli config set-retention --days 90
```

## Components

### NotificationRouter

Routes notifications to appropriate channels based on rules.

**Key Features:**
- Priority-based routing (critical → multiple channels, low → email only)
- Severity-based routing (critical → Slack + PagerDuty)
- Custom routing rules with pattern matching
- Redis-backed notification queue
- Lifecycle tracking (queued → sent → delivered → failed)

**Example:**

```python
from communication_platform import NotificationRouter, NotificationRequest, Priority

router = NotificationRouter(redis_url="redis://localhost:6379")
await router.connect()

request = NotificationRequest(
    id="notif-123",
    title="Test",
    message="Test message",
    priority=Priority.HIGH,
    recipients=["@team"]
)

# Router selects channels based on priority
routed = await router.route_notification(request)
print(routed.channels)  # [ChannelType.SLACK, ChannelType.EMAIL]
```

### SlackIntegration

Send rich notifications to Slack with Block Kit.

**Key Features:**
- Block Kit message formatting
- Interactive buttons and forms
- Thread management
- File uploads
- Mentions (@user, @channel, @here)
- Rate limit handling

**Example:**

```python
from communication_platform import SlackIntegration, SlackMessage

slack = SlackIntegration(token="xoxb-...", signing_secret="...")

# Simple message
message = SlackMessage(
    channel="#general",
    text="Deployment complete!"
)
await slack.post_message(message)

# Block Kit message with button
blocks = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Deployment Ready*\nApprove to proceed?"}
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Approve"},
                "style": "primary",
                "value": "approve"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Reject"},
                "style": "danger",
                "value": "reject"
            }
        ]
    }
]

message = SlackMessage(channel="#deployments", text="Approval needed", blocks=blocks)
await slack.post_message(message)
```

### EmailService

Send emails via SendGrid or SMTP with templates.

**Key Features:**
- SendGrid API integration
- SMTP fallback support
- HTML and plain-text emails
- Attachment handling
- CC/BCC support
- Template rendering
- Delivery tracking

**Example:**

```python
from communication_platform import EmailService, EmailMessage, EmailAttachment

email = EmailService(
    sendgrid_api_key="SG....",
    default_from_email="notifications@company.com"
)

# Simple email
message = EmailMessage(
    to=["user@example.com"],
    subject="Deployment Complete",
    body="Production deployment successful",
    from_email="notifications@company.com"
)
await email.send_email(message)

# HTML email with attachment
attachment = EmailAttachment(
    filename="report.pdf",
    content=pdf_bytes,
    content_type="application/pdf"
)

message = EmailMessage(
    to=["user@example.com"],
    cc=["manager@example.com"],
    subject="Monthly Report",
    body="<h1>Report</h1><p>See attached PDF</p>",
    from_email="notifications@company.com",
    is_html=True,
    attachments=[attachment]
)
await email.send_email(message)
```

### AlertManager

Manage alerts with escalation policies.

**Key Features:**
- Multi-level escalation policies
- Time-based escalation triggers
- Alert deduplication
- Suppression rules for maintenance windows
- Severity-based routing
- Acknowledgment and resolution tracking

**Example:**

```python
from communication_platform import AlertManager, EscalationPolicy, EscalationLevel, AlertSeverity

manager = AlertManager(
    redis_url="redis://localhost:6379",
    postgres_url="postgresql://user:pass@localhost/db"
)
await manager.connect()

# Create escalation policy
policy = EscalationPolicy(
    name="On-Call Escalation",
    levels=[
        EscalationLevel(
            level=1,
            delay_minutes=0,
            channels=["slack"],
            recipients=["@on-call-primary"]
        ),
        EscalationLevel(
            level=2,
            delay_minutes=15,
            channels=["slack", "pagerduty"],
            recipients=["@on-call-secondary", "oncall"]
        )
    ]
)

await manager.create_policy(policy)

# Send alert
await manager.send_alert(
    alert_id="alert-123",
    title="High CPU Usage",
    message="Server prod-01 CPU at 95%",
    severity=AlertSeverity.HIGH,
    escalation_policy_id=policy.id,
    recipients=["@on-call-primary"]
)
```

### DeliveryTracker

Track notification delivery with retries.

**Key Features:**
- PostgreSQL-backed delivery log
- Per-channel status tracking
- Exponential backoff retries (1s → 2s → 4s)
- Dead letter queue for permanent failures
- Delivery metrics (success rate, latency)
- 90-day retention with automatic cleanup

**Example:**

```python
from communication_platform import DeliveryTracker, DeliveryStatus

tracker = DeliveryTracker(
    postgres_url="postgresql://user:pass@localhost/db",
    redis_url="redis://localhost:6379",
    max_retries=3
)
await tracker.connect()

# Track delivery
await tracker.track_delivery(
    notification_id="notif-123",
    channel="slack",
    status=DeliveryStatus.DELIVERED,
    recipient="@team",
    metadata={"title": "Test"}
)

# Get status
records = await tracker.get_delivery_status("notif-123")
for channel, record in records.items():
    print(f"{channel}: {record.status}")

# Get metrics
metrics = await tracker.get_metrics()
print(f"Success rate: {metrics['success_rate']:.2%}")
```

### RateLimiter

Prevent API rate limit violations.

**Key Features:**
- Redis-based sliding window algorithm
- Token bucket algorithm for burst handling
- Per-channel rate limits
- Lua scripts for atomic operations
- Backpressure feedback
- Automatic cleanup of expired keys

**Example:**

```python
from communication_platform import RateLimiter, RateLimitAlgorithm

limiter = RateLimiter(redis_url="redis://localhost:6379")
await limiter.connect()

# Set rate limit
await limiter.set_rate_limit(
    resource="channel:slack",
    max_requests=50,
    window_seconds=60,
    algorithm=RateLimitAlgorithm.SLIDING_WINDOW
)

# Check rate limit
allowed = await limiter.check_rate_limit("channel:slack")
if allowed:
    # Send notification
    pass
else:
    # Wait for backpressure delay
    delay = await limiter.get_backpressure_delay("channel:slack")
    await asyncio.sleep(delay)
```

### TemplateEngine

Manage notification templates with Jinja2.

**Key Features:**
- Jinja2 template engine with sandboxing
- Template versioning (v1.0, v2.0, etc.)
- PostgreSQL template storage
- 5 built-in templates
- Template validation and preview
- Variable extraction and validation

**Example:**

```python
from communication_platform import TemplateEngine, Template, TemplateCategory

engine = TemplateEngine(postgres_url="postgresql://user:pass@localhost/db")
await engine.connect()

# Create custom template
template = Template(
    name="custom-alert",
    category=TemplateCategory.ALERT,
    subject="Alert: {{title}}",
    body="{{message}}\n\nSeverity: {{severity}}\nTime: {{timestamp}}",
    variables=["title", "message", "severity", "timestamp"],
    version="1.0"
)

await engine.create_template(template)

# Render template
rendered = await engine.render_template(
    template_name="custom-alert",
    context={
        "title": "High CPU",
        "message": "CPU usage at 95%",
        "severity": "high",
        "timestamp": "2024-01-15 10:30:00"
    }
)

print(rendered["subject"])  # "Alert: High CPU"
print(rendered["body"])     # Full rendered body
```

## Templates

### Built-in Templates

The platform includes 5 built-in templates for common scenarios:

#### 1. Deployment Complete

**Template Name:** `deployment_complete`

**Variables:**
- `environment` (required): Target environment (production, staging, etc.)
- `version` (required): Deployed version (e.g., v2.1.0)
- `deployer` (required): Person who deployed
- `duration` (optional): Deployment duration
- `status` (optional): Deployment status (default: success)
- `changes` (optional): List of changes

**Example:**

```python
await service.send_template_notification(
    template_name="deployment_complete",
    context={
        "environment": "production",
        "version": "v2.1.0",
        "deployer": "Alice",
        "duration": "5m 23s",
        "status": "success",
        "changes": ["Fix login bug", "Add new feature", "Update dependencies"]
    },
    channels=["slack", "email"],
    recipients=["@team-ops", "ops@company.com"]
)
```

**Output:**

```
Deployment Complete: production

Version: v2.1.0
Deployed by: Alice
Duration: 5m 23s
Status: ✅ success

Changes:
• Fix login bug
• Add new feature
• Update dependencies
```

#### 2. Incident Alert

**Template Name:** `incident_alert`

**Variables:**
- `title` (required): Incident title
- `severity` (required): Severity level (low, medium, high, critical)
- `description` (required): Incident description
- `affected_systems` (optional): List of affected systems
- `incident_id` (optional): Incident tracking ID
- `responder` (optional): Assigned responder

**Example:**

```python
await service.send_template_notification(
    template_name="incident_alert",
    context={
        "title": "Database Connection Failure",
        "severity": "critical",
        "description": "Primary database is unreachable. All read/write operations failing.",
        "affected_systems": ["API Server", "Web App", "Mobile App"],
        "incident_id": "INC-2024-001",
        "responder": "@alice"
    },
    channels=["slack", "pagerduty"],
    recipients=["@on-call", "oncall"]
)
```

#### 3. Pull Request Notification

**Template Name:** `pr_notification`

**Variables:**
- `pr_number` (required): Pull request number
- `title` (required): PR title
- `author` (required): PR author
- `repository` (required): Repository name
- `url` (required): PR URL
- `reviewers` (optional): List of requested reviewers
- `labels` (optional): PR labels

**Example:**

```python
await service.send_template_notification(
    template_name="pr_notification",
    context={
        "pr_number": 123,
        "title": "Fix authentication bug",
        "author": "bob",
        "repository": "api-server",
        "url": "https://github.com/company/api-server/pull/123",
        "reviewers": ["alice", "charlie"],
        "labels": ["bug", "high-priority"]
    },
    channels=["slack"],
    recipients=["#code-reviews"]
)
```

#### 4. Sprint Update

**Template Name:** `sprint_update`

**Variables:**
- `sprint_name` (required): Sprint name or number
- `status` (required): Sprint status (started, completed, etc.)
- `team` (required): Team name
- `completed_stories` (optional): Number of completed stories
- `total_stories` (optional): Total number of stories
- `velocity` (optional): Sprint velocity
- `highlights` (optional): List of sprint highlights

**Example:**

```python
await service.send_template_notification(
    template_name="sprint_update",
    context={
        "sprint_name": "Sprint 24",
        "status": "completed",
        "team": "Platform Team",
        "completed_stories": 18,
        "total_stories": 20,
        "velocity": 45,
        "highlights": [
            "Migrated to new database",
            "Reduced API latency by 40%",
            "Fixed 12 critical bugs"
        ]
    },
    channels=["slack", "email"],
    recipients=["@team", "stakeholders@company.com"]
)
```

#### 5. Postmortem Complete

**Template Name:** `postmortem_complete`

**Variables:**
- `incident_title` (required): Incident title
- `incident_id` (required): Incident ID
- `date` (required): Incident date
- `duration` (required): Incident duration
- `impact` (required): Impact description
- `root_cause` (required): Root cause summary
- `action_items` (optional): List of action items
- `postmortem_url` (optional): Link to full postmortem

**Example:**

```python
await service.send_template_notification(
    template_name="postmortem_complete",
    context={
        "incident_title": "API Service Outage",
        "incident_id": "INC-2024-001",
        "date": "2024-01-15",
        "duration": "2h 15m",
        "impact": "Complete service outage affecting 10,000 users",
        "root_cause": "Database connection pool exhaustion due to memory leak",
        "action_items": [
            "Implement connection pool monitoring",
            "Add automated leak detection",
            "Update deployment runbook"
        ],
        "postmortem_url": "https://docs.company.com/postmortems/2024-001"
    },
    channels=["slack", "email"],
    recipients=["@engineering", "leadership@company.com"]
)
```

### Custom Templates

Create custom templates for your specific use cases:

```python
from communication_platform import Template, TemplateCategory

# Define template
template = Template(
    name="weekly-report",
    category=TemplateCategory.NOTIFICATION,
    subject="Weekly Report: {{team}} - Week {{week_number}}",
    body="""
Weekly Report for {{team}}
Week: {{week_number}}

## Accomplishments
{% for item in accomplishments %}
• {{ item }}
{% endfor %}

## Metrics
• Deployments: {{metrics.deployments}}
• Incidents: {{metrics.incidents}}
• Uptime: {{metrics.uptime}}%

## Next Week
{% for item in next_week %}
• {{ item }}
{% endfor %}
    """.strip(),
    variables=["team", "week_number", "accomplishments", "metrics", "next_week"],
    version="1.0"
)

# Create template
await engine.create_template(template)

# Use template
await service.send_template_notification(
    template_name="weekly-report",
    context={
        "team": "Platform Team",
        "week_number": 42,
        "accomplishments": [
            "Completed migration to Kubernetes",
            "Reduced deployment time by 50%",
            "Zero incidents this week"
        ],
        "metrics": {
            "deployments": 23,
            "incidents": 0,
            "uptime": 99.99
        },
        "next_week": [
            "Begin cache optimization",
            "Update monitoring dashboards",
            "Team retrospective"
        ]
    },
    channels=["email"],
    recipients=["team@company.com", "management@company.com"]
)
```

### Template Best Practices

1. **Use Clear Variable Names**
   ```python
   # Good
   variables=["user_name", "order_id", "total_amount"]

   # Bad
   variables=["un", "oid", "amt"]
   ```

2. **Provide Defaults for Optional Variables**
   ```jinja2
   Duration: {{ duration | default("Unknown") }}
   ```

3. **Use Loops for Lists**
   ```jinja2
   Changes:
   {% for change in changes %}
   • {{ change }}
   {% endfor %}
   ```

4. **Format Dates and Numbers**
   ```jinja2
   Date: {{ timestamp | date_format("%Y-%m-%d %H:%M") }}
   Amount: ${{ amount | number_format(2) }}
   ```

5. **Include Fallback Text**
   ```jinja2
   {{ message | default("No message provided") }}
   ```

6. **Version Your Templates**
   - Start with v1.0
   - Increment for breaking changes (v2.0)
   - Use minor versions for additions (v1.1)

## Escalation Policies

### Creating Escalation Policies

```python
from communication_platform import EscalationPolicy, EscalationLevel

policy = EscalationPolicy(
    name="Critical Incident Escalation",
    description="Escalation for critical production incidents",
    levels=[
        # Level 1: Immediate notification to on-call
        EscalationLevel(
            level=1,
            delay_minutes=0,
            channels=["slack", "pagerduty"],
            recipients=["@on-call-primary", "oncall-primary"]
        ),

        # Level 2: After 15 minutes, escalate to secondary on-call
        EscalationLevel(
            level=2,
            delay_minutes=15,
            channels=["slack", "pagerduty", "email"],
            recipients=["@on-call-secondary", "oncall-secondary", "secondary@company.com"]
        ),

        # Level 3: After 30 minutes, escalate to engineering leadership
        EscalationLevel(
            level=3,
            delay_minutes=30,
            channels=["slack", "pagerduty", "email", "sms"],
            recipients=["@engineering-leads", "leads@company.com", "+1-555-0100"]
        ),

        # Level 4: After 60 minutes, escalate to executives
        EscalationLevel(
            level=4,
            delay_minutes=60,
            channels=["email", "sms"],
            recipients=["executives@company.com", "+1-555-0200"]
        )
    ]
)

# Save policy
await alert_manager.create_policy(policy)
```

### Using Escalation Policies

```python
# Send alert with escalation
result = await service.send_alert(
    title="Database Cluster Down",
    message="All database nodes are unreachable. Critical service impact.",
    severity="critical",
    escalation_policy_id=policy.id,
    recipients=["@on-call-primary"],
    metadata={
        "cluster": "prod-db-cluster",
        "nodes_down": 3,
        "last_check": "2024-01-15T10:30:00Z"
    }
)

# Check if escalation is needed
needs_escalation = await alert_manager.check_escalation_needed(result.notification_id)

if needs_escalation:
    await alert_manager.escalate_alert(result.notification_id)
```

### Alert Deduplication

Prevent duplicate alerts within a time window:

```python
# Set deduplication window (60 minutes)
alert_signature = "critical:database:connection_failed"

is_duplicate = await alert_manager.is_duplicate_alert(
    alert_signature,
    window_minutes=60
)

if not is_duplicate:
    # Send alert
    await service.send_alert(...)

    # Register alert to prevent duplicates
    await alert_manager.register_alert(alert_signature)
else:
    print("Alert already sent within last 60 minutes, skipping")
```

### Suppression Rules

Suppress alerts during maintenance windows:

```python
from datetime import datetime, timedelta

# Add suppression rule
rule = {
    "pattern": "maintenance:*",
    "suppress_until": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
    "reason": "Scheduled maintenance window"
}

await alert_manager.add_suppression_rule("maintenance-window", rule)

# Check if alert should be suppressed
is_suppressed = await alert_manager.is_alert_suppressed("maintenance:database_restart")

if is_suppressed:
    print("Alert suppressed due to maintenance window")
```

## Monitoring & Metrics

### Delivery Metrics

```python
# Get overall metrics
metrics = await service.get_metrics(
    start_date=datetime.utcnow() - timedelta(days=7),
    end_date=datetime.utcnow()
)

print(f"""
Delivery Metrics (Last 7 Days)
==============================
Total Sent:       {metrics['total_sent']}
Delivered:        {metrics['total_delivered']}
Failed:           {metrics['total_failed']}
Success Rate:     {metrics['success_rate']:.2%}
Avg Latency:      {metrics['avg_latency_seconds']:.2f}s
""")

# Metrics by channel
for channel, data in metrics['by_channel'].items():
    print(f"""
{channel.upper()}:
  Sent:          {data['total_sent']}
  Success Rate:  {data['success_rate']:.2%}
  Avg Latency:   {data['avg_latency']:.2f}s
""")
```

### Rate Limit Status

```python
# Check rate limit status for all channels
channels = ["slack", "email", "teams", "pagerduty"]

for channel in channels:
    status = await rate_limiter.get_rate_limit_status(f"channel:{channel}")

    print(f"{channel}: {status.remaining}/{status.limit} remaining")
    print(f"  Reset in: {status.reset_seconds}s")

    if status.remaining < status.limit * 0.2:  # Less than 20% remaining
        print(f"  ⚠️ Low quota warning!")
```

### Dead Letter Queue

```python
# Get failed notifications in dead letter queue
dlq_items = await delivery_tracker.get_dead_letter_queue()

for item in dlq_items:
    print(f"""
Notification: {item.notification_id}
Channel:      {item.channel}
Recipient:    {item.recipient}
Retries:      {item.retry_count}
Last Error:   {item.error_message}
Timestamp:    {item.updated_at}
""")

# Manually retry DLQ items
for item in dlq_items:
    # Fix underlying issue first, then retry
    await service.retry_failed_notifications(item.notification_id)
```

### Health Checks

```python
async def check_service_health():
    """Check health of all service components."""
    health = {
        "redis": False,
        "postgres": False,
        "slack": False,
        "email": False
    }

    try:
        # Check Redis
        await service.rate_limiter._redis.ping()
        health["redis"] = True
    except Exception as e:
        print(f"Redis unhealthy: {e}")

    try:
        # Check PostgreSQL
        await service.delivery_tracker._conn.fetchval("SELECT 1")
        health["postgres"] = True
    except Exception as e:
        print(f"PostgreSQL unhealthy: {e}")

    try:
        # Check Slack
        response = await service.slack.client.api_test()
        health["slack"] = response.get("ok", False)
    except Exception as e:
        print(f"Slack unhealthy: {e}")

    try:
        # Check Email (SendGrid API)
        # Perform lightweight test
        health["email"] = True
    except Exception as e:
        print(f"Email unhealthy: {e}")

    return health
```

## Troubleshooting

### Common Issues

#### 1. Redis Connection Failed

**Error:**
```
ConnectionError: Error connecting to Redis at localhost:6379
```

**Solutions:**
- Verify Redis is running: `redis-cli ping`
- Check connection URL: `redis://localhost:6379`
- For Redis with password: `redis://:password@localhost:6379`
- Check firewall rules

#### 2. PostgreSQL Connection Failed

**Error:**
```
asyncpg.exceptions.InvalidCatalogNameError: database "notifications" does not exist
```

**Solutions:**
- Create database: `createdb notifications`
- Verify connection string format: `postgresql://user:pass@host:port/dbname`
- Check PostgreSQL is running: `pg_isready`
- Verify user permissions

#### 3. Slack API Token Invalid

**Error:**
```
slack_sdk.errors.SlackApiError: invalid_auth
```

**Solutions:**
- Verify token starts with `xoxb-`
- Check token has required scopes:
  - `chat:write`
  - `chat:write.public`
  - `files:write`
- Reinstall Slack app to workspace
- Generate new token

#### 4. SendGrid API Key Invalid

**Error:**
```
Unauthorized: The provided authorization grant is invalid
```

**Solutions:**
- Verify API key starts with `SG.`
- Check key has "Mail Send" permission
- Generate new API key
- Verify sender email is verified in SendGrid

#### 5. Rate Limit Exceeded

**Error:**
```
Rate limit exceeded for channel slack
```

**Solutions:**
- Check current rate limits: `notification-cli config show`
- Increase rate limit: `notification-cli config set-rate-limit --channel slack --limit 100`
- Implement exponential backoff
- Spread notifications over time

#### 6. Template Rendering Failed

**Error:**
```
jinja2.exceptions.UndefinedError: 'variable_name' is undefined
```

**Solutions:**
- Check all required variables are provided in context
- Use default values: `{{ variable | default("N/A") }}`
- Preview template first: `notification-cli template preview <name> --context '{...}'`
- Validate template: Check for typos in variable names

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now all operations will log debug information
```

### Testing Configuration

Test each component individually:

```bash
# Test Redis connection
redis-cli ping

# Test PostgreSQL connection
psql postgresql://user:pass@localhost/notifications -c "SELECT 1"

# Test Slack integration
notification-cli channel test slack

# Test Email integration
notification-cli channel test email
```

### Performance Tuning

**Redis Connection Pool:**

```python
config = NotificationConfig(
    redis_url="redis://localhost:6379?max_connections=50",
    # ... other config
)
```

**PostgreSQL Connection Pool:**

```python
config = NotificationConfig(
    postgres_url="postgresql://user:pass@localhost/db?min_size=10&max_size=20",
    # ... other config
)
```

**Async Task Concurrency:**

```python
# Process notifications in batches
async def send_batch(notifications):
    tasks = [
        service.send_notification(**notif)
        for notif in notifications
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/devCrew_s1/communication-platform.git
cd communication-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=communication_platform --cov-report=html

# Run specific test file
pytest tests/test_notification_router.py -v

# Run specific test
pytest tests/test_notification_router.py::test_router_route_notification -v
```

### Code Quality

```bash
# Format code
black communication_platform/
isort communication_platform/

# Lint code
flake8 communication_platform/
pylint communication_platform/

# Type checking
mypy communication_platform/

# Security scanning
bandit -r communication_platform/

# Run all checks
pre-commit run --all-files
```

### Building Documentation

```bash
# Install docs dependencies
pip install sphinx sphinx-rtd-theme

# Build docs
cd docs/
make html

# View docs
open _build/html/index.html
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run code quality checks: `pre-commit run --all-files`
5. Commit changes: `git commit -m "feat: add my feature"`
6. Push to branch: `git push origin feature/my-feature`
7. Create Pull Request

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
chore: update dependencies
```

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: https://docs.company.com/communication-platform
- **Issues**: https://github.com/devCrew_s1/communication-platform/issues
- **Discussions**: https://github.com/devCrew_s1/communication-platform/discussions
- **Email**: support@company.com

## Changelog

### v1.0.0 (2024-01-15)

- Initial release
- Multi-channel notification support (Slack, Email)
- Template engine with 5 built-in templates
- Delivery tracking with retries
- Rate limiting with Redis
- Alert management with escalation
- CLI interface
- Comprehensive test suite (85%+ coverage)
- Complete documentation
