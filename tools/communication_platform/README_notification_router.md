# Notification Router

Intelligent notification routing component for TOOL-COMM-001 Communication Platform.

## Overview

The Notification Router provides sophisticated routing of notifications to multiple channels (Slack, Email, Teams, PagerDuty, SMS) with:

- **Intelligent Channel Selection**: Automatic channel selection based on priority and severity
- **Custom Routing Rules**: Flexible rule-based routing with pattern matching
- **Lifecycle Tracking**: Track notifications through their entire lifecycle (queued → sent → delivered → failed)
- **Redis-Based Queuing**: Asynchronous notification delivery with Redis queue management
- **Multiple Input Formats**: Support for JSON and YAML request formats
- **Template Support**: Integration with template engine for message formatting

## Core Components

### Enumerations

#### ChannelType
Supported notification channels:
- `SLACK` - Slack workspace channels
- `EMAIL` - Email delivery
- `TEAMS` - Microsoft Teams
- `PAGERDUTY` - PagerDuty incident management
- `SMS` - SMS text messages

#### Priority
Notification priority levels:
- `LOW` - Low priority notifications
- `MEDIUM` - Standard priority (default)
- `HIGH` - High priority requiring immediate attention
- `CRITICAL` - Critical alerts requiring immediate action

#### Severity
Notification severity indicators:
- `INFO` - Informational messages
- `WARNING` - Warning messages
- `ERROR` - Error notifications
- `CRITICAL` - Critical system alerts

#### NotificationStatus
Lifecycle status tracking:
- `QUEUED` - Notification queued for delivery
- `SENT` - Notification sent to channel
- `DELIVERED` - Confirmed delivery
- `FAILED` - Delivery failed
- `RETRYING` - Retry in progress

### Models

#### NotificationRequest

Primary model for notification requests.

**Key Fields**:
- `notification_id` - Unique identifier (auto-generated UUID)
- `title` - Notification title
- `message` - Message content
- `priority` - Priority level
- `severity` - Severity level
- `channels` - Explicit channel list (optional, overrides auto-selection)
- `recipients` - Per-channel recipient lists
- `template` - Template name for rendering
- `template_data` - Data for template rendering
- `metadata` - Additional metadata
- `tags` - Classification tags
- `protocol` - Protocol identifier (e.g., P-OPS-POSTMORTEM)
- `source` - Source system or agent
- `expires_at` - Expiration timestamp
- `max_retries` - Maximum retry attempts (default: 3)
- `status` - Current lifecycle status

**Example**:
```python
from notification_router import NotificationRequest, Priority, Severity

request = NotificationRequest(
    title="Database Connection Lost",
    message="Production database server unreachable",
    priority=Priority.CRITICAL,
    severity=Severity.ERROR,
    recipients={
        "slack": ["#incidents"],
        "pagerduty": ["ops-team"],
        "email": ["ops@example.com"]
    },
    tags=["database", "production"],
    source="monitoring-system"
)
```

#### RoutingRule

Custom routing rule for pattern-based channel selection.

**Key Fields**:
- `rule_id` - Unique rule identifier
- `name` - Rule name
- `conditions` - Matching conditions dictionary
- `channels` - Channels to route to when matched
- `priority` - Rule priority (lower number = higher priority)
- `enabled` - Whether rule is active

**Condition Matching**:
- `priority`: Match notification priority (string or list)
- `severity`: Match notification severity (string or list)
- `protocol`: Match protocol identifier (string or list)
- `tags`: Match any tag (list)
- `source`: Match source system (string or list)

**Example**:
```python
from notification_router import RoutingRule, ChannelType

rule = RoutingRule(
    rule_id="incident-rule",
    name="Incident Response Rule",
    conditions={
        "protocol": "P-INCIDENT-RESPONSE",
        "priority": ["high", "critical"],
        "tags": ["security", "production"]
    },
    channels=[ChannelType.SLACK, ChannelType.PAGERDUTY, ChannelType.TEAMS],
    priority=5,
    enabled=True
)
```

### NotificationRouter Class

Main routing class providing intelligent notification routing.

#### Initialization

```python
from notification_router import NotificationRouter, create_notification_router
from redis import Redis

# Option 1: Manual initialization
redis_client = Redis(host='localhost', port=6379, db=0)
router = NotificationRouter(redis_client=redis_client)

# Option 2: Factory function (recommended)
router = create_notification_router(
    redis_host='localhost',
    redis_port=6379,
    redis_db=0
)

# Option 3: Without Redis (no queuing)
router = NotificationRouter()
```

#### Key Methods

##### parse_request(data: dict) -> NotificationRequest
Parse notification request from dictionary.

```python
data = {
    "title": "System Alert",
    "message": "High CPU usage detected",
    "priority": "high",
    "severity": "warning"
}
request = router.parse_request(data)
```

##### parse_request_json(json_str: str) -> NotificationRequest
Parse notification request from JSON string.

```python
json_str = '{"title": "Alert", "message": "Test", "priority": "high"}'
request = router.parse_request_json(json_str)
```

##### parse_request_yaml(yaml_str: str) -> NotificationRequest
Parse notification request from YAML string.

```python
yaml_str = """
title: System Alert
message: High CPU usage detected
priority: high
severity: warning
"""
request = router.parse_request_yaml(yaml_str)
```

##### select_channels(severity: str, priority: str) -> List[str]
Select channels based on severity and priority.

```python
channels = router.select_channels(severity="critical", priority="high")
# Returns: ['email', 'pagerduty', 'slack', 'sms']
```

##### apply_routing_rules(request: NotificationRequest) -> List[str]
Apply custom routing rules to determine channels.

```python
channels = router.apply_routing_rules(request)
```

##### queue_notification(request: NotificationRequest) -> str
Queue notification for async delivery (requires Redis).

```python
notification_id = router.queue_notification(request)
```

##### get_notification_status(notification_id: str) -> dict
Get notification status and details.

```python
status = router.get_notification_status(notification_id)
print(status['status'])  # 'queued', 'sent', 'delivered', 'failed'
```

##### route(request: NotificationRequest) -> dict
Main routing method - routes notification to appropriate channels.

```python
result = router.route(request)
# Returns:
# {
#     "notification_id": "uuid",
#     "status": "queued",
#     "channels": ["slack", "email"],
#     "priority": "high",
#     "severity": "warning",
#     "queued": true,
#     "created_at": "2024-11-24T10:30:00Z"
# }
```

##### add_routing_rule(rule: RoutingRule) -> None
Add custom routing rule.

```python
router.add_routing_rule(rule)
```

##### remove_routing_rule(rule_id: str) -> bool
Remove routing rule by ID.

```python
removed = router.remove_routing_rule("incident-rule")
```

##### load_routing_rules_from_config(config_path: str) -> None
Load routing rules from YAML configuration file.

```python
router.load_routing_rules_from_config("routing_rules.yml")
```

## Default Routing Logic

### Priority-Based Routing

| Priority | Channels |
|----------|----------|
| CRITICAL | Slack + PagerDuty |
| HIGH | Slack + Email |
| MEDIUM | Slack |
| LOW | Email |

### Severity-Based Routing (Critical Cases)

| Severity | Channels |
|----------|----------|
| CRITICAL | Slack + PagerDuty + SMS |
| ERROR | Slack + Email |
| WARNING | Slack |
| INFO | Email |

### Channel Selection Priority

1. **Explicit channels** in request (highest priority)
2. **Custom routing rules** (evaluated in rule priority order)
3. **Default priority-based routing**
4. **Severity-based routing** (for critical severity)
5. **Email fallback** (if no channels determined)

## Usage Examples

### Basic Usage

```python
from notification_router import (
    create_notification_router,
    create_notification_request
)

# Initialize router
router = create_notification_router(redis_host="localhost")

# Create notification
request = create_notification_request(
    title="Deployment Complete",
    message="Application v2.5.0 deployed to production",
    priority="medium",
    severity="info",
    recipients={
        "slack": ["#deployments"],
        "email": ["team@example.com"]
    }
)

# Route notification
result = router.route(request)
print(f"Notification {result['notification_id']} routed to {result['channels']}")
```

### Custom Routing Rules

```python
from notification_router import NotificationRouter, RoutingRule, ChannelType

router = NotificationRouter()

# Add rule for postmortem notifications
postmortem_rule = RoutingRule(
    rule_id="postmortem-001",
    name="Postmortem Notifications",
    conditions={
        "protocol": "P-OPS-POSTMORTEM",
        "priority": ["high", "critical"]
    },
    channels=[ChannelType.SLACK, ChannelType.EMAIL, ChannelType.TEAMS],
    priority=10
)
router.add_routing_rule(postmortem_rule)

# Add rule for security alerts
security_rule = RoutingRule(
    rule_id="security-001",
    name="Security Alerts",
    conditions={
        "tags": ["security", "vulnerability"],
        "severity": ["error", "critical"]
    },
    channels=[ChannelType.SLACK, ChannelType.PAGERDUTY, ChannelType.EMAIL],
    priority=5  # Higher priority than postmortem rule
)
router.add_routing_rule(security_rule)
```

### YAML Configuration

Create `routing_rules.yml`:

```yaml
routing_rules:
  - rule_id: incident-response
    name: Incident Response Notifications
    conditions:
      protocol: P-INCIDENT-RESPONSE
      priority:
        - high
        - critical
    channels:
      - slack
      - pagerduty
      - teams
    priority: 5
    enabled: true

  - rule_id: stakeholder-comms
    name: Stakeholder Communications
    conditions:
      protocol: P-STAKEHOLDER-COMM
      severity: info
    channels:
      - email
      - teams
    priority: 20
    enabled: true
```

Load configuration:

```python
router.load_routing_rules_from_config("routing_rules.yml")
```

### Protocol-Specific Examples

#### P-OPS-POSTMORTEM
```python
request = NotificationRequest(
    title="Postmortem: Database Outage",
    message="Postmortem analysis complete for incident #123",
    priority=Priority.HIGH,
    severity=Severity.INFO,
    protocol="P-OPS-POSTMORTEM",
    recipients={
        "slack": ["#incidents"],
        "email": ["engineering@example.com"]
    }
)
```

#### P-STAKEHOLDER-COMM
```python
request = NotificationRequest(
    title="Quarterly Release Update",
    message="Q4 2024 release schedule and features",
    priority=Priority.MEDIUM,
    severity=Severity.INFO,
    protocol="P-STAKEHOLDER-COMM",
    recipients={
        "email": ["stakeholders@example.com"],
        "teams": ["Executive Team"]
    }
)
```

#### CA-CS-NotifyHuman
```python
request = NotificationRequest(
    title="Agent Needs Human Approval",
    message="Code review agent requires approval for merge",
    priority=Priority.HIGH,
    severity=Severity.WARNING,
    protocol="CA-CS-NotifyHuman",
    source="code-review-agent",
    recipients={
        "slack": ["@senior-engineer"],
        "email": ["engineer@example.com"]
    }
)
```

## Redis Queue Management

### Queue Keys

- `notification:queue:{notification_id}` - Individual notification data
- `notification:queue:pending` - List of pending notifications
- `notification:status:{notification_id}` - Status tracking

### Queue Operations

```python
# Queue notification
notification_id = router.queue_notification(request)

# Check status
status = router.get_notification_status(notification_id)
print(status['status'])  # 'queued', 'sent', 'delivered', 'failed'

# Note: Actual delivery is handled by separate delivery service
```

## Error Handling

### Common Exceptions

```python
from notification_router import NotificationRouter

router = NotificationRouter()

try:
    # Invalid priority
    request = NotificationRequest(
        title="Test",
        message="Test",
        priority="invalid"  # ValueError
    )
except ValueError as e:
    print(f"Validation error: {e}")

try:
    # Missing Redis for queue operations
    router_no_redis = NotificationRouter()
    router_no_redis.queue_notification(request)  # RuntimeError
except RuntimeError as e:
    print(f"Queue error: {e}")

try:
    # Notification not found
    status = router.get_notification_status("non-existent-id")  # ValueError
except ValueError as e:
    print(f"Not found: {e}")
```

## Integration with Other Components

### Template Engine Integration

```python
request = NotificationRequest(
    title="Deployment Status",
    message="See details below",
    priority=Priority.MEDIUM,
    severity=Severity.INFO,
    template="deployment_notification",
    template_data={
        "version": "2.5.0",
        "environment": "production",
        "status": "success",
        "duration": "5m 23s"
    }
)
```

### Delivery Tracker Integration

```python
# Route notification
result = router.route(request)

# Pass to delivery tracker for actual sending
from delivery_tracker import DeliveryTracker

tracker = DeliveryTracker()
for channel in result['channels']:
    tracker.track_delivery(
        notification_id=result['notification_id'],
        channel=channel,
        status='sent'
    )
```

## Performance Considerations

- **Redis Connection Pool**: Use connection pooling for high-throughput scenarios
- **Rule Evaluation**: Rules are evaluated in priority order; place most common rules first
- **Queue TTL**: Notifications expire after 1 hour in queue, 24 hours in status store
- **Retry Logic**: Max 3 retries by default, configurable per notification

## Testing

Run basic tests:

```bash
python3 test_notification_router_basic.py
```

## Requirements

- Python 3.10+
- Redis 5.0+ (optional, for queuing)
- pydantic 2.5+
- redis-py 5.0+
- pyyaml 6.0+

## Best Practices

1. **Use factory functions** for initialization
2. **Define routing rules** in YAML configuration files
3. **Use protocols** for cross-component communication patterns
4. **Tag notifications** for better filtering and routing
5. **Set expiration times** for time-sensitive notifications
6. **Monitor queue depth** in production environments
7. **Use explicit channels** only when necessary; prefer routing rules
8. **Include source information** for debugging and auditing

## Troubleshooting

### Notifications not being queued
- Verify Redis connection: `redis_client.ping()`
- Check Redis logs for connection errors
- Ensure queue keys are not being deleted by other processes

### Unexpected channel selection
- Check routing rules order (lower priority number = higher precedence)
- Verify rule conditions match notification attributes
- Review default routing logic in code

### Status not found
- Notifications expire after TTL (1 hour queue, 24 hours status)
- Check notification_id is correct
- Verify Redis connection is stable

## License

Part of devCrew_s1 TOOL-COMM-001 Communication Platform.
