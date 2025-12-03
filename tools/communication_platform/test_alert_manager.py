"""
Test suite for Alert Manager.

Tests escalation policies, alert routing, deduplication, suppression,
and time-based escalation logic.
"""

import time
from datetime import datetime, timedelta

import fakeredis
import pytest

from alert_manager import (
    Alert,
    AlertManager,
    AlertSeverity,
    EscalationLevel,
    EscalationPolicy,
    NotificationChannel,
    SuppressionRule,
)


@pytest.fixture
def redis_client():
    """Create fake Redis client for testing."""
    return fakeredis.FakeStrictRedis()


@pytest.fixture
def alert_manager(redis_client):
    """Create AlertManager instance."""
    return AlertManager(
        redis_client=redis_client,
        deduplication_window_minutes=60,
        max_escalation_level=3,
    )


@pytest.fixture
def sample_policy():
    """Create sample escalation policy."""
    return EscalationPolicy(
        name="Critical Infrastructure",
        description="Critical alerts for infrastructure",
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
            EscalationLevel(
                level=3,
                delay_minutes=30,
                channels=[
                    NotificationChannel.SLACK,
                    NotificationChannel.EMAIL,
                    NotificationChannel.PAGERDUTY,
                ],
                recipients=[
                    "team-oncall",
                    "manager@example.com",
                    "director@example.com",
                ],
            ),
        ],
        tags=["infrastructure", "critical"],
    )


class TestEscalationPolicy:
    """Test escalation policy validation and functionality."""

    def test_create_valid_policy(self, sample_policy):
        """Test creating a valid escalation policy."""
        assert sample_policy.name == "Critical Infrastructure"
        assert sample_policy.severity == AlertSeverity.CRITICAL
        assert len(sample_policy.levels) == 3

    def test_policy_levels_sequential(self):
        """Test that policy levels must be sequential."""
        with pytest.raises(ValueError, match="sequential"):
            EscalationPolicy(
                name="Bad Policy",
                severity=AlertSeverity.WARNING,
                levels=[
                    EscalationLevel(
                        level=1,
                        delay_minutes=0,
                        channels=[NotificationChannel.SLACK],
                        recipients=["team"],
                    ),
                    EscalationLevel(
                        level=3,  # Skip level 2
                        delay_minutes=15,
                        channels=[NotificationChannel.EMAIL],
                        recipients=["team"],
                    ),
                ],
            )

    def test_get_level(self, sample_policy):
        """Test getting escalation level by number."""
        level = sample_policy.get_level(2)
        assert level is not None
        assert level.level == 2
        assert level.delay_minutes == 15

        level = sample_policy.get_level(99)
        assert level is None


class TestAlertManager:
    """Test AlertManager core functionality."""

    def test_create_policy(self, alert_manager, sample_policy):
        """Test creating escalation policy."""
        policy_id = alert_manager.create_policy(sample_policy)
        assert policy_id == sample_policy.policy_id

        retrieved = alert_manager.get_policy(policy_id)
        assert retrieved is not None
        assert retrieved.name == sample_policy.name

    def test_send_alert(self, alert_manager, sample_policy):
        """Test sending an alert."""
        policy_id = alert_manager.create_policy(sample_policy)

        result = alert_manager.send_alert(
            severity="critical",
            title="Database Down",
            description="Primary database is not responding",
            context={"host": "db-prod-01"},
            policy_id=policy_id,
        )

        assert result["status"] == "active"
        assert result["alert_id"] is not None
        assert result["severity"] == "critical"
        assert result["current_level"] == 1

    def test_send_alert_invalid_severity(self, alert_manager):
        """Test sending alert with invalid severity."""
        with pytest.raises(ValueError, match="Invalid severity"):
            alert_manager.send_alert(
                severity="super-critical",
                title="Test",
                description="Test",
            )

    def test_send_alert_no_policy(self, alert_manager):
        """Test sending alert without matching policy."""
        with pytest.raises(ValueError, match="No escalation policy found"):
            alert_manager.send_alert(
                severity="critical",
                title="Test",
                description="Test",
            )

    def test_alert_deduplication(self, alert_manager, sample_policy):
        """Test alert deduplication."""
        policy_id = alert_manager.create_policy(sample_policy)

        result1 = alert_manager.send_alert(
            severity="critical",
            title="Database Down",
            description="First occurrence",
            policy_id=policy_id,
        )

        result2 = alert_manager.send_alert(
            severity="critical",
            title="Database Down",  # Same title + severity
            description="Second occurrence",
            policy_id=policy_id,
        )

        assert result1["status"] == "active"
        assert result2["status"] == "deduplicated"

    def test_escalate_alert(self, alert_manager, sample_policy):
        """Test alert escalation."""
        policy_id = alert_manager.create_policy(sample_policy)

        result = alert_manager.send_alert(
            severity="critical",
            title="Service Degraded",
            description="Performance issues",
            policy_id=policy_id,
        )

        alert_id = result["alert_id"]

        escalated = alert_manager.escalate_alert(alert_id)
        assert escalated is True

        alert = alert_manager._get_alert(alert_id)
        assert alert.current_level == 2
        assert len(alert.escalation_history) == 2  # Level 1 + Level 2

    def test_escalate_max_level(self, alert_manager, sample_policy):
        """Test escalation at max level."""
        policy_id = alert_manager.create_policy(sample_policy)

        result = alert_manager.send_alert(
            severity="critical",
            title="Max Level Test",
            description="Test max escalation",
            policy_id=policy_id,
        )

        alert_id = result["alert_id"]

        alert_manager.escalate_alert(alert_id)
        alert_manager.escalate_alert(alert_id)

        escalated = alert_manager.escalate_alert(alert_id)
        assert escalated is False  # Already at max level

    def test_check_escalation_needed(self, alert_manager, sample_policy):
        """Test checking if escalation is needed based on time."""
        sample_policy.levels[1].delay_minutes = 0  # No delay for testing

        policy_id = alert_manager.create_policy(sample_policy)

        result = alert_manager.send_alert(
            severity="critical",
            title="Time Test",
            description="Test time-based escalation",
            policy_id=policy_id,
        )

        alert_id = result["alert_id"]

        time.sleep(0.1)

        needs_escalation = alert_manager.check_escalation_needed(alert_id)
        assert needs_escalation is True

    def test_suppress_alert(self, alert_manager, sample_policy):
        """Test alert suppression."""
        policy_id = alert_manager.create_policy(sample_policy)

        result = alert_manager.send_alert(
            severity="critical",
            title="Suppress Test",
            description="Test suppression",
            policy_id=policy_id,
        )

        alert_id = result["alert_id"]

        suppressed = alert_manager.suppress_alert(alert_id, "Maintenance window")
        assert suppressed is True

        alert = alert_manager._get_alert(alert_id)
        assert alert.suppressed is True
        assert alert.status == "suppressed"

    def test_resolve_alert(self, alert_manager, sample_policy):
        """Test alert resolution."""
        policy_id = alert_manager.create_policy(sample_policy)

        result = alert_manager.send_alert(
            severity="critical",
            title="Resolve Test",
            description="Test resolution",
            policy_id=policy_id,
        )

        alert_id = result["alert_id"]

        resolved = alert_manager.resolve_alert(alert_id, "Issue fixed")
        assert resolved is True

        alert = alert_manager._get_alert(alert_id)
        assert alert.status == "resolved"
        assert alert.resolved_at is not None

    def test_get_active_alerts(self, alert_manager, sample_policy):
        """Test getting active alerts."""
        policy_id = alert_manager.create_policy(sample_policy)

        alert_manager.send_alert(
            severity="critical",
            title="Active Alert 1",
            description="Test",
            policy_id=policy_id,
        )

        result2 = alert_manager.send_alert(
            severity="critical",
            title="Active Alert 2",
            description="Test",
            policy_id=policy_id,
        )

        alert_manager.resolve_alert(result2["alert_id"], "Fixed")

        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0]["title"] == "Active Alert 1"

    def test_get_active_alerts_by_severity(self, alert_manager):
        """Test getting active alerts filtered by severity."""
        critical_policy = EscalationPolicy(
            name="Critical",
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

        warning_policy = EscalationPolicy(
            name="Warning",
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

        critical_id = alert_manager.create_policy(critical_policy)
        warning_id = alert_manager.create_policy(warning_policy)

        alert_manager.send_alert(
            severity="critical",
            title="Critical",
            description="Test",
            policy_id=critical_id,
        )

        alert_manager.send_alert(
            severity="warning",
            title="Warning",
            description="Test",
            policy_id=warning_id,
        )

        critical_alerts = alert_manager.get_active_alerts(AlertSeverity.CRITICAL)
        assert len(critical_alerts) == 1
        assert critical_alerts[0]["severity"] == "critical"

    def test_aggregate_alerts(self, alert_manager, sample_policy):
        """Test alert aggregation."""
        policy_id = alert_manager.create_policy(sample_policy)

        for i in range(5):
            alert_manager.send_alert(
                severity="critical",
                title="Repeated Alert",
                description=f"Occurrence {i}",
                policy_id=policy_id,
            )
            time.sleep(0.01)

        aggregated = alert_manager.aggregate_alerts(timeframe_minutes=60, min_count=3)

        assert len(aggregated) >= 1

        for fingerprint, alert_ids in aggregated.items():
            assert len(alert_ids) >= 3


class TestSuppressionRule:
    """Test suppression rules for maintenance windows."""

    def test_create_suppression_rule(self, alert_manager):
        """Test creating suppression rule."""
        rule = SuppressionRule(
            name="Maintenance Window",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=2),
            severities=[AlertSeverity.INFO, AlertSeverity.WARNING],
        )

        rule_id = alert_manager.create_suppression_rule(rule)
        assert rule_id == rule.rule_id

    def test_suppression_rule_validation(self):
        """Test suppression rule time validation."""
        now = datetime.utcnow()

        with pytest.raises(ValueError, match="end_time must be after start_time"):
            SuppressionRule(
                name="Invalid",
                start_time=now,
                end_time=now - timedelta(hours=1),
            )

    def test_alert_suppression_by_rule(self, alert_manager, sample_policy):
        """Test alert suppression by active rule."""
        rule = SuppressionRule(
            name="Maintenance",
            start_time=datetime.utcnow() - timedelta(minutes=5),
            end_time=datetime.utcnow() + timedelta(hours=1),
            severities=[AlertSeverity.CRITICAL],
        )

        alert_manager.create_suppression_rule(rule)
        policy_id = alert_manager.create_policy(sample_policy)

        result = alert_manager.send_alert(
            severity="critical",
            title="During Maintenance",
            description="Should be suppressed",
            policy_id=policy_id,
        )

        assert result["status"] == "suppressed"
        assert result["reason"] == "maintenance_window"

    def test_suppression_rule_inactive(self, alert_manager, sample_policy):
        """Test that inactive suppression rules don't suppress alerts."""
        rule = SuppressionRule(
            name="Past Maintenance",
            start_time=datetime.utcnow() - timedelta(hours=2),
            end_time=datetime.utcnow() - timedelta(hours=1),
            severities=[AlertSeverity.CRITICAL],
        )

        alert_manager.create_suppression_rule(rule)
        policy_id = alert_manager.create_policy(sample_policy)

        result = alert_manager.send_alert(
            severity="critical",
            title="After Maintenance",
            description="Should not be suppressed",
            policy_id=policy_id,
        )

        assert result["status"] == "active"


class TestAlertFingerprint:
    """Test alert fingerprinting and deduplication."""

    def test_alert_fingerprint(self):
        """Test alert fingerprint generation."""
        alert1 = Alert(
            severity=AlertSeverity.CRITICAL,
            title="Database Down",
            description="First occurrence",
            policy_id="test-policy",
        )

        alert2 = Alert(
            severity=AlertSeverity.CRITICAL,
            title="Database Down",
            description="Different description",  # Different description
            policy_id="test-policy",
        )

        assert alert1.fingerprint == alert2.fingerprint

    def test_different_fingerprints(self):
        """Test that different alerts have different fingerprints."""
        alert1 = Alert(
            severity=AlertSeverity.CRITICAL,
            title="Database Down",
            description="Test",
            policy_id="test-policy",
        )

        alert2 = Alert(
            severity=AlertSeverity.WARNING,  # Different severity
            title="Database Down",
            description="Test",
            policy_id="test-policy",
        )

        assert alert1.fingerprint != alert2.fingerprint


class TestEscalationHistory:
    """Test escalation history tracking."""

    def test_escalation_history(self, alert_manager, sample_policy):
        """Test that escalation history is tracked."""
        policy_id = alert_manager.create_policy(sample_policy)

        result = alert_manager.send_alert(
            severity="critical",
            title="History Test",
            description="Test history tracking",
            policy_id=policy_id,
        )

        alert_id = result["alert_id"]

        alert_manager.escalate_alert(alert_id)

        alert = alert_manager._get_alert(alert_id)
        assert len(alert.escalation_history) == 2  # Level 1 + Level 2

        for entry in alert.escalation_history:
            assert "level" in entry
            assert "timestamp" in entry
            assert "channels" in entry
            assert "recipients" in entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
