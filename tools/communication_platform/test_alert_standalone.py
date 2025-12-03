"""
Standalone test for Alert Manager (no package imports).

Tests core functionality without requiring full package dependencies.
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import fakeredis

sys.path.insert(0, str(Path(__file__).parent))

from alert_manager import (
    Alert,
    AlertManager,
    AlertSeverity,
    EscalationLevel,
    EscalationPolicy,
    NotificationChannel,
    SuppressionRule,
)


def test_create_escalation_policy():
    """Test creating escalation policy."""
    policy = EscalationPolicy(
        name="Test Policy",
        description="Test policy for critical alerts",
        severity=AlertSeverity.CRITICAL,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team-oncall"],
            ),
            EscalationLevel(
                level=2,
                delay_minutes=15,
                channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
                recipients=["team-oncall", "manager@example.com"],
            ),
        ],
    )

    assert policy.name == "Test Policy"
    assert policy.severity == AlertSeverity.CRITICAL
    assert len(policy.levels) == 2
    print("✓ test_create_escalation_policy passed")


def test_send_alert():
    """Test sending an alert."""
    redis_client = fakeredis.FakeStrictRedis()
    manager = AlertManager(redis_client)

    policy = EscalationPolicy(
        name="Critical Policy",
        severity=AlertSeverity.CRITICAL,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team"],
            )
        ],
    )

    policy_id = manager.create_policy(policy)

    result = manager.send_alert(
        severity="critical",
        title="Database Down",
        description="Primary database is not responding",
        context={"host": "db-prod-01"},
        policy_id=policy_id,
    )

    assert result["status"] == "active"
    assert result["alert_id"] is not None
    assert result["severity"] == "critical"
    print("✓ test_send_alert passed")


def test_alert_deduplication():
    """Test alert deduplication."""
    redis_client = fakeredis.FakeStrictRedis()
    manager = AlertManager(redis_client, deduplication_window_minutes=60)

    policy = EscalationPolicy(
        name="Test Policy",
        severity=AlertSeverity.CRITICAL,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team"],
            )
        ],
    )

    policy_id = manager.create_policy(policy)

    result1 = manager.send_alert(
        severity="critical",
        title="Database Down",
        description="First occurrence",
        policy_id=policy_id,
    )

    result2 = manager.send_alert(
        severity="critical",
        title="Database Down",  # Same title + severity
        description="Second occurrence",
        policy_id=policy_id,
    )

    assert result1["status"] == "active"
    assert result2["status"] == "deduplicated"
    print("✓ test_alert_deduplication passed")


def test_escalate_alert():
    """Test alert escalation."""
    redis_client = fakeredis.FakeStrictRedis()
    manager = AlertManager(redis_client)

    policy = EscalationPolicy(
        name="Multi-Level",
        severity=AlertSeverity.CRITICAL,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team"],
            ),
            EscalationLevel(
                level=2,
                delay_minutes=15,
                channels=[NotificationChannel.EMAIL],
                recipients=["manager"],
            ),
        ],
    )

    policy_id = manager.create_policy(policy)

    result = manager.send_alert(
        severity="critical",
        title="Service Degraded",
        description="Performance issues",
        policy_id=policy_id,
    )

    alert_id = result["alert_id"]

    escalated = manager.escalate_alert(alert_id)
    assert escalated is True

    alert = manager._get_alert(alert_id)
    assert alert.current_level == 2
    assert len(alert.escalation_history) == 2
    print("✓ test_escalate_alert passed")


def test_suppress_alert():
    """Test alert suppression."""
    redis_client = fakeredis.FakeStrictRedis()
    manager = AlertManager(redis_client)

    policy = EscalationPolicy(
        name="Test",
        severity=AlertSeverity.CRITICAL,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team"],
            )
        ],
    )

    policy_id = manager.create_policy(policy)

    result = manager.send_alert(
        severity="critical",
        title="Suppress Test",
        description="Test suppression",
        policy_id=policy_id,
    )

    alert_id = result["alert_id"]

    suppressed = manager.suppress_alert(alert_id, "Maintenance window")
    assert suppressed is True

    alert = manager._get_alert(alert_id)
    assert alert.suppressed is True
    assert alert.status == "suppressed"
    print("✓ test_suppress_alert passed")


def test_resolve_alert():
    """Test alert resolution."""
    redis_client = fakeredis.FakeStrictRedis()
    manager = AlertManager(redis_client)

    policy = EscalationPolicy(
        name="Test",
        severity=AlertSeverity.WARNING,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team"],
            )
        ],
    )

    policy_id = manager.create_policy(policy)

    result = manager.send_alert(
        severity="warning",
        title="Resolve Test",
        description="Test resolution",
        policy_id=policy_id,
    )

    alert_id = result["alert_id"]

    resolved = manager.resolve_alert(alert_id, "Issue fixed")
    assert resolved is True

    alert = manager._get_alert(alert_id)
    assert alert.status == "resolved"
    assert alert.resolved_at is not None
    print("✓ test_resolve_alert passed")


def test_suppression_rule():
    """Test suppression rules for maintenance windows."""
    redis_client = fakeredis.FakeStrictRedis()
    manager = AlertManager(redis_client)

    rule = SuppressionRule(
        name="Maintenance",
        start_time=datetime.utcnow() - timedelta(minutes=5),
        end_time=datetime.utcnow() + timedelta(hours=1),
        severities=[AlertSeverity.CRITICAL],
    )

    manager.create_suppression_rule(rule)

    policy = EscalationPolicy(
        name="Test",
        severity=AlertSeverity.CRITICAL,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team"],
            )
        ],
    )

    policy_id = manager.create_policy(policy)

    result = manager.send_alert(
        severity="critical",
        title="During Maintenance",
        description="Should be suppressed",
        policy_id=policy_id,
    )

    assert result["status"] == "suppressed"
    assert result["reason"] == "maintenance_window"
    print("✓ test_suppression_rule passed")


def test_get_active_alerts():
    """Test getting active alerts."""
    redis_client = fakeredis.FakeStrictRedis()
    manager = AlertManager(redis_client)

    policy = EscalationPolicy(
        name="Test",
        severity=AlertSeverity.CRITICAL,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team"],
            )
        ],
    )

    policy_id = manager.create_policy(policy)

    manager.send_alert(
        severity="critical",
        title="Active Alert 1",
        description="Test",
        policy_id=policy_id,
    )

    result2 = manager.send_alert(
        severity="critical",
        title="Active Alert 2",
        description="Test",
        policy_id=policy_id,
    )

    manager.resolve_alert(result2["alert_id"], "Fixed")

    active_alerts = manager.get_active_alerts()
    assert len(active_alerts) == 1
    assert active_alerts[0]["title"] == "Active Alert 1"
    print("✓ test_get_active_alerts passed")


def test_alert_aggregation():
    """Test alert aggregation."""
    redis_client = fakeredis.FakeStrictRedis()
    manager = AlertManager(redis_client, deduplication_window_minutes=1)

    policy = EscalationPolicy(
        name="Test",
        severity=AlertSeverity.WARNING,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team"],
            )
        ],
    )

    policy_id = manager.create_policy(policy)

    for i in range(5):
        manager.send_alert(
            severity="warning",
            title=f"Repeated Alert {i}",  # Different titles to avoid deduplication
            description=f"Occurrence {i}",
            policy_id=policy_id,
        )
        time.sleep(0.01)

    active_alerts = manager.get_active_alerts()
    assert len(active_alerts) == 5

    aggregated = manager.aggregate_alerts(timeframe_minutes=60, min_count=1)

    assert len(aggregated) >= 1
    print("✓ test_alert_aggregation passed")


def test_check_escalation_needed():
    """Test checking if escalation is needed."""
    redis_client = fakeredis.FakeStrictRedis()
    manager = AlertManager(redis_client)

    policy = EscalationPolicy(
        name="Test",
        severity=AlertSeverity.CRITICAL,
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                channels=[NotificationChannel.SLACK],
                recipients=["team"],
            ),
            EscalationLevel(
                level=2,
                delay_minutes=0,  # No delay for testing
                channels=[NotificationChannel.EMAIL],
                recipients=["manager"],
            ),
        ],
    )

    policy_id = manager.create_policy(policy)

    result = manager.send_alert(
        severity="critical",
        title="Time Test",
        description="Test time-based escalation",
        policy_id=policy_id,
    )

    alert_id = result["alert_id"]

    time.sleep(0.1)

    needs_escalation = manager.check_escalation_needed(alert_id)
    assert needs_escalation is True
    print("✓ test_check_escalation_needed passed")


def main():
    """Run all tests."""
    print("\nRunning Alert Manager Tests\n" + "=" * 50)

    tests = [
        test_create_escalation_policy,
        test_send_alert,
        test_alert_deduplication,
        test_escalate_alert,
        test_suppress_alert,
        test_resolve_alert,
        test_suppression_rule,
        test_get_active_alerts,
        test_alert_aggregation,
        test_check_escalation_needed,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
