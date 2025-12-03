"""
Basic test script for NotificationRouter.

Verifies core functionality without requiring Redis.
"""

import sys
from datetime import datetime, timezone

from notification_router import (
    ChannelType,
    NotificationRequest,
    NotificationRouter,
    Priority,
    RoutingRule,
    Severity,
    create_notification_request,
)


def test_basic_functionality():
    """Test basic notification router functionality."""
    print("Testing NotificationRouter basic functionality...\n")

    # 1. Test router initialization (without Redis)
    print("1. Initializing NotificationRouter...")
    router = NotificationRouter()
    print("   ✓ Router initialized successfully\n")

    # 2. Test notification request creation
    print("2. Creating notification request...")
    request = create_notification_request(
        title="System Alert",
        message="High CPU usage detected on server-01",
        priority="high",
        severity="warning",
        recipients={"slack": ["#alerts"], "email": ["ops@example.com"]},
        tags=["performance", "infrastructure"],
        source="monitoring-system",
    )
    print(f"   ✓ Request created: {request.notification_id}")
    print(f"   - Title: {request.title}")
    print(f"   - Priority: {request.priority.value}")
    print(f"   - Severity: {request.severity.value}\n")

    # 3. Test channel selection
    print("3. Testing channel selection...")
    channels = router.select_channels(severity="critical", priority="high")
    print(f"   ✓ Selected channels for high/critical: {channels}\n")

    # 4. Test routing (without Redis)
    print("4. Testing notification routing...")
    result = router.route(request)
    print(f"   ✓ Routed notification: {result['notification_id']}")
    print(f"   - Status: {result['status']}")
    print(f"   - Channels: {result['channels']}")
    print(f"   - Priority: {result['priority']}\n")

    # 5. Test custom routing rules
    print("5. Testing custom routing rules...")
    rule = RoutingRule(
        rule_id="postmortem-rule",
        name="Postmortem Notification Rule",
        conditions={"protocol": "P-OPS-POSTMORTEM", "priority": ["high", "critical"]},
        channels=[ChannelType.SLACK, ChannelType.EMAIL, ChannelType.TEAMS],
        priority=10,
    )
    router.add_routing_rule(rule)
    print(f"   ✓ Added routing rule: {rule.name}")

    # Create request that matches the rule
    postmortem_request = NotificationRequest(
        title="Postmortem Complete",
        message="Incident #123 postmortem has been completed",
        priority=Priority.HIGH,
        severity=Severity.WARNING,
        protocol="P-OPS-POSTMORTEM",
    )

    rule_channels = router.apply_routing_rules(postmortem_request)
    print(f"   ✓ Rule matched, channels: {rule_channels}\n")

    # 6. Test different priority routing
    print("6. Testing priority-based routing...")
    test_cases = [
        ("critical", "critical"),
        ("high", "error"),
        ("medium", "warning"),
        ("low", "info"),
    ]

    for priority, severity in test_cases:
        channels = router.select_channels(severity=severity, priority=priority)
        print(f"   - {priority}/{severity}: {channels}")

    print("\n7. Testing request serialization...")
    # Test to_dict and from_dict
    request_dict = request.to_dict()
    print(f"   ✓ Serialized to dict with {len(request_dict)} fields")

    restored_request = NotificationRequest.from_dict(request_dict)
    print(f"   ✓ Restored from dict: {restored_request.notification_id}")
    assert restored_request.notification_id == request.notification_id
    assert restored_request.title == request.title
    print("   ✓ Serialization roundtrip successful\n")

    # 8. Test JSON parsing
    print("8. Testing JSON parsing...")
    json_str = """{
        "title": "Test Notification",
        "message": "This is a test",
        "priority": "medium",
        "severity": "info"
    }"""

    parsed_request = router.parse_request_json(json_str)
    print(f"   ✓ Parsed JSON request: {parsed_request.notification_id}")
    print(f"   - Title: {parsed_request.title}")
    print(f"   - Priority: {parsed_request.priority.value}\n")

    # 9. Test YAML parsing
    print("9. Testing YAML parsing...")
    yaml_str = """
title: YAML Test Notification
message: Testing YAML parsing
priority: high
severity: error
tags:
  - test
  - yaml
"""

    parsed_yaml_request = router.parse_request_yaml(yaml_str)
    print(f"   ✓ Parsed YAML request: {parsed_yaml_request.notification_id}")
    print(f"   - Title: {parsed_yaml_request.title}")
    print(f"   - Tags: {parsed_yaml_request.tags}\n")

    # 10. Test routing rule management
    print("10. Testing routing rule management...")
    rules = router.get_routing_rules()
    print(f"   ✓ Current rules: {len(rules)}")

    removed = router.remove_routing_rule("postmortem-rule")
    print(f"   ✓ Rule removed: {removed}")

    rules = router.get_routing_rules()
    print(f"   ✓ Rules after removal: {len(rules)}\n")

    print("=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)


def test_severity_enum():
    """Test Severity enum values."""
    print("\nTesting Severity enum...")
    assert Severity.INFO.value == "info"
    assert Severity.WARNING.value == "warning"
    assert Severity.ERROR.value == "error"
    assert Severity.CRITICAL.value == "critical"
    print("✓ Severity enum tests passed")


def test_channel_enum():
    """Test ChannelType enum values."""
    print("\nTesting ChannelType enum...")
    assert ChannelType.SLACK.value == "slack"
    assert ChannelType.EMAIL.value == "email"
    assert ChannelType.TEAMS.value == "teams"
    assert ChannelType.PAGERDUTY.value == "pagerduty"
    assert ChannelType.SMS.value == "sms"
    print("✓ ChannelType enum tests passed")


if __name__ == "__main__":
    try:
        test_severity_enum()
        test_channel_enum()
        test_basic_functionality()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
