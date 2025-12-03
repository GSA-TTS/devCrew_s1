# NotificationRouter Quick Start Guide

## Installation

```bash
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1/tools/communication_platform
pip install -r requirements.txt
```

## Basic Usage (3 Lines)

```python
from notification_router import create_notification_router, create_notification_request

router = create_notification_router()
request = create_notification_request("Alert", "High CPU usage", priority="high")
result = router.route(request)
```

## Common Patterns

### 1. Simple Notification
```python
from notification_router import create_notification_router, NotificationRequest, Priority

router = create_notification_router()
request = NotificationRequest(
    title="Deployment Complete",
    message="v2.0 deployed to production",
    priority=Priority.MEDIUM
)
result = router.route(request)
print(f"Sent to: {result['channels']}")  # ['slack']
```

### 2. Critical Alert
```python
request = NotificationRequest(
    title="Database Down",
    message="Production database unreachable",
    priority=Priority.CRITICAL,
    recipients={"pagerduty": ["ops-team"]}
)
result = router.route(request)  # Goes to slack + pagerduty
```

### 3. Custom Channels
```python
from notification_router import ChannelType

request = NotificationRequest(
    title="Weekly Report",
    message="See attached report",
    channels=[ChannelType.EMAIL, ChannelType.TEAMS],  # Explicit channels
    recipients={
        "email": ["team@example.com"],
        "teams": ["Engineering Team"]
    }
)
result = router.route(request)
```

### 4. Custom Routing Rule
```python
from notification_router import RoutingRule, ChannelType

rule = RoutingRule(
    rule_id="security-001",
    name="Security Alerts",
    conditions={"tags": ["security"], "severity": ["critical", "error"]},
    channels=[ChannelType.SLACK, ChannelType.PAGERDUTY, ChannelType.EMAIL],
    priority=5
)
router.add_routing_rule(rule)

# Now security alerts go to 3 channels
request = NotificationRequest(
    title="Security Alert",
    message="Suspicious activity detected",
    tags=["security"],
    severity=Severity.ERROR
)
result = router.route(request)  # Goes to slack + pagerduty + email
```

### 5. With Redis Queue
```python
# Requires Redis running on localhost:6379
router = create_notification_router(redis_host="localhost")

request = NotificationRequest(
    title="Queued Notification",
    message="This will be queued for async delivery",
    priority=Priority.HIGH
)

result = router.route(request)
notification_id = result['notification_id']

# Check status later
status = router.get_notification_status(notification_id)
print(status['status'])  # 'queued', 'sent', 'delivered', 'failed'
```

### 6. Protocol-Based Routing
```python
# For postmortem notifications
request = NotificationRequest(
    title="Postmortem Complete",
    message="Incident #123 analysis complete",
    priority=Priority.HIGH,
    protocol="P-OPS-POSTMORTEM",  # Protocol identifier
    recipients={"slack": ["#incidents"], "email": ["team@example.com"]}
)
result = router.route(request)
```

### 7. Load Rules from Config
```yaml
# routing_rules.yml
routing_rules:
  - rule_id: incident-001
    name: Incident Notifications
    conditions:
      protocol: P-INCIDENT-RESPONSE
      priority: [high, critical]
    channels: [slack, pagerduty, teams]
    priority: 5
    enabled: true
```

```python
router.load_routing_rules_from_config("routing_rules.yml")
```

### 8. JSON/YAML Parsing
```python
# From JSON string
json_str = '{"title": "Test", "message": "Hello", "priority": "medium"}'
request = router.parse_request_json(json_str)

# From YAML string
yaml_str = """
title: Test Alert
message: System check
priority: high
"""
request = router.parse_request_yaml(yaml_str)

# From dictionary
data = {"title": "Alert", "message": "Test", "priority": "low"}
request = router.parse_request(data)
```

## Default Routing Matrix

| Priority | Severity | Channels |
|----------|----------|----------|
| critical | any | slack + pagerduty |
| high | any | slack + email |
| medium | any | slack |
| low | any | email |
| any | critical | slack + pagerduty + sms |

## Channel Selection Priority

1. **Explicit channels** in request (highest)
2. **Custom routing rules** (by rule priority)
3. **Default priority routing**
4. **Severity enhancement** (critical)
5. **Email fallback** (lowest)

## Testing Your Setup

```bash
# Run basic tests
python3 test_notification_router_basic.py

# Import check
python3 -c "from notification_router import NotificationRouter; print('OK')"
```

## Common Errors

### ValueError: Invalid priority
```python
# Wrong: Using string directly
request = NotificationRequest(title="Test", message="Test", priority="invalid")

# Right: Use enum or valid string
from notification_router import Priority
request = NotificationRequest(title="Test", message="Test", priority=Priority.HIGH)
# or
request = NotificationRequest(title="Test", message="Test", priority="high")
```

### RuntimeError: Redis not available
```python
# Without Redis - router works but no queuing
router = NotificationRouter()  # OK, will warn but work

# With Redis - requires Redis running
router = create_notification_router(redis_host="localhost")  # Needs Redis
```

## Full Example

```python
#!/usr/bin/env python3
"""Example notification script."""

from notification_router import (
    create_notification_router,
    create_notification_request,
    Priority,
    Severity,
    RoutingRule,
    ChannelType
)

# Initialize router
router = create_notification_router()

# Add custom rule for production alerts
prod_rule = RoutingRule(
    rule_id="prod-001",
    name="Production Alerts",
    conditions={"tags": ["production"], "priority": ["high", "critical"]},
    channels=[ChannelType.SLACK, ChannelType.PAGERDUTY, ChannelType.EMAIL],
    priority=10
)
router.add_routing_rule(prod_rule)

# Send notification
request = create_notification_request(
    title="Production Alert",
    message="High memory usage on prod-server-01",
    priority="high",
    severity="warning",
    recipients={
        "slack": ["#prod-alerts"],
        "pagerduty": ["ops-oncall"],
        "email": ["ops@example.com"]
    },
    tags=["production", "memory"],
    source="monitoring-system"
)

# Route notification
result = router.route(request)

print(f"Notification ID: {result['notification_id']}")
print(f"Status: {result['status']}")
print(f"Channels: {result['channels']}")
print(f"Priority: {result['priority']}")
```

## Environment Variables (Optional)

```bash
# Redis configuration
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0

# Logging level
export LOG_LEVEL=INFO
```

## Next Steps

1. Read [README_notification_router.md](README_notification_router.md) for detailed documentation
2. Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for features
3. Integrate with other communication platform components:
   - Template Engine (for message formatting)
   - Delivery Tracker (for delivery confirmation)
   - Rate Limiter (for rate limiting)
   - Slack Integration (for actual sending)
   - Email Service (for email delivery)

## Support

For issues or questions:
1. Check the troubleshooting section in README
2. Run test_notification_router_basic.py to verify setup
3. Review implementation details in notification_router.py
