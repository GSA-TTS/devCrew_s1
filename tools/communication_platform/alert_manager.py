"""
Alert Manager for Communication Platform.

Manages alert escalation, routing, de-duplication, and suppression with
multi-level escalation policies, time-based delays, severity-based routing,
and integration with on-call schedules.

Features:
    - Multi-level escalation policies (Level 1 → Level 2 → Level 3)
    - Time-based escalation with configurable delays
    - Severity-based routing (critical → PagerDuty + Slack)
    - Alert de-duplication within configurable timeframes
    - Suppression rules for maintenance windows
    - Alert aggregation for batch processing
    - Escalation history tracking
    - Redis-based state management
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

import redis
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification channel types."""

    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    TEAMS = "teams"
    SMS = "sms"


class EscalationLevel(BaseModel):
    """Escalation level configuration."""

    level: int = Field(..., ge=1, le=10, description="Escalation level (1-10)")
    delay_minutes: int = Field(
        ..., ge=0, description="Minutes to wait before escalating"
    )
    channels: List[NotificationChannel] = Field(
        ..., min_length=1, description="Notification channels for this level"
    )
    recipients: List[str] = Field(
        ..., min_length=1, description="Recipients for this level"
    )
    conditions: Optional[Dict[str, Any]] = Field(
        default=None, description="Conditions for this level"
    )

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, v: List[str]) -> List[str]:
        """Validate recipients are not empty."""
        if not all(r.strip() for r in v):
            raise ValueError("Recipients cannot be empty strings")
        return v


class EscalationPolicy(BaseModel):
    """Escalation policy configuration."""

    policy_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, description="Policy name")
    description: str = Field(default="", description="Policy description")
    severity: AlertSeverity = Field(
        ..., description="Severity level this policy applies to"
    )
    levels: List[EscalationLevel] = Field(
        ..., min_length=1, description="Escalation levels"
    )
    enabled: bool = Field(default=True, description="Whether policy is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list, description="Policy tags")

    @field_validator("levels")
    @classmethod
    def validate_levels(cls, v: List[EscalationLevel]) -> List[EscalationLevel]:
        """Validate escalation levels are sequential."""
        if not v:
            raise ValueError("At least one escalation level required")

        levels = sorted(v, key=lambda x: x.level)
        for i, level in enumerate(levels, start=1):
            if level.level != i:
                raise ValueError("Escalation levels must be sequential (1, 2, 3...)")

        return levels

    def get_level(self, level_num: int) -> Optional[EscalationLevel]:
        """Get escalation level by number."""
        for level in self.levels:
            if level.level == level_num:
                return level
        return None


class Alert(BaseModel):
    """Alert instance."""

    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., min_length=1, description="Alert title")
    description: str = Field(..., description="Alert description")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )
    policy_id: str = Field(..., description="Escalation policy ID")
    current_level: int = Field(default=1, ge=1, description="Current escalation level")
    status: str = Field(
        default="active", description="Alert status (active, resolved, suppressed)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(default=None)
    escalated_at: Optional[datetime] = Field(default=None)
    last_notification_at: Optional[datetime] = Field(default=None)
    notification_count: int = Field(default=0, ge=0)
    escalation_history: List[Dict[str, Any]] = Field(default_factory=list)
    suppressed: bool = Field(default=False)
    deduplicated_from: Optional[str] = Field(default=None)

    @property
    def fingerprint(self) -> str:
        """Generate fingerprint for deduplication."""
        data = f"{self.severity}:{self.title}".encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @property
    def is_active(self) -> bool:
        """Check if alert is active."""
        return self.status == "active" and not self.suppressed

    def add_escalation_entry(
        self, level: int, channels: List[str], recipients: List[str]
    ) -> None:
        """Add escalation history entry."""
        self.escalation_history.append(
            {
                "level": level,
                "timestamp": datetime.utcnow().isoformat(),
                "channels": channels,
                "recipients": recipients,
            }
        )
        self.updated_at = datetime.utcnow()


class SuppressionRule(BaseModel):
    """Alert suppression rule for maintenance windows."""

    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1)
    start_time: datetime = Field(...)
    end_time: datetime = Field(...)
    severities: List[AlertSeverity] = Field(
        default_factory=lambda: [
            AlertSeverity.INFO,
            AlertSeverity.WARNING,
            AlertSeverity.CRITICAL,
        ]
    )
    tags: List[str] = Field(default_factory=list)
    enabled: bool = Field(default=True)

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: datetime, info: Any) -> datetime:
        """Validate end time is after start time."""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    def is_active(self) -> bool:
        """Check if suppression rule is currently active."""
        if not self.enabled:
            return False
        now = datetime.utcnow()
        return self.start_time <= now <= self.end_time

    def should_suppress(self, severity: AlertSeverity, tags: List[str]) -> bool:
        """Check if alert should be suppressed."""
        if not self.is_active():
            return False

        if severity not in self.severities:
            return False

        if self.tags and not any(tag in self.tags for tag in tags):
            return False

        return True


class AlertManager:
    """
    Alert management with escalation, routing, and de-duplication.

    Manages alert lifecycle including creation, escalation, suppression,
    and resolution with Redis-based state tracking.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        deduplication_window_minutes: int = 60,
        max_escalation_level: int = 3,
    ):
        """
        Initialize AlertManager.

        Args:
            redis_client: Redis client for state management
            deduplication_window_minutes: Time window for alert deduplication
            max_escalation_level: Maximum escalation level
        """
        self.redis = redis_client
        self.deduplication_window_minutes = deduplication_window_minutes
        self.max_escalation_level = max_escalation_level
        self.policies: Dict[str, EscalationPolicy] = {}
        self.suppression_rules: Dict[str, SuppressionRule] = {}
        self.alerts: Dict[str, Alert] = {}

        logger.info("AlertManager initialized")

    def create_policy(self, policy: EscalationPolicy) -> str:
        """
        Create escalation policy.

        Args:
            policy: Escalation policy configuration

        Returns:
            Policy ID

        Raises:
            ValueError: If policy validation fails
        """
        if not policy.enabled:
            logger.warning(f"Creating disabled policy: {policy.name}")

        self.policies[policy.policy_id] = policy

        policy_key = f"policy:{policy.policy_id}"
        self.redis.setex(
            policy_key,
            86400 * 30,  # 30 days TTL
            policy.model_dump_json(),
        )

        logger.info(
            f"Created escalation policy: {policy.name} "
            f"(ID: {policy.policy_id}, severity: {policy.severity})"
        )
        return policy.policy_id

    def get_policy(self, policy_id: str) -> Optional[EscalationPolicy]:
        """
        Get escalation policy by ID.

        Args:
            policy_id: Policy ID

        Returns:
            Escalation policy or None
        """
        if policy_id in self.policies:
            return self.policies[policy_id]

        policy_key = f"policy:{policy_id}"
        policy_data = self.redis.get(policy_key)
        if policy_data:
            policy = EscalationPolicy.model_validate_json(policy_data)
            self.policies[policy_id] = policy
            return policy

        return None

    def send_alert(
        self,
        severity: str,
        title: str,
        description: str,
        context: Optional[Dict[str, Any]] = None,
        policy_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send alert with automatic routing and escalation.

        Args:
            severity: Alert severity (info, warning, critical)
            title: Alert title
            description: Alert description
            context: Additional context
            policy_id: Escalation policy ID (auto-selected if None)
            tags: Alert tags for routing

        Returns:
            Alert details including alert_id and status

        Raises:
            ValueError: If severity is invalid or no policy found
        """
        try:
            alert_severity = AlertSeverity(severity.lower())
        except ValueError:
            raise ValueError(
                f"Invalid severity: {severity}. "
                f"Must be one of: {[s.value for s in AlertSeverity]}"
            )

        if context is None:
            context = {}

        if tags is None:
            tags = []

        if self._should_suppress_alert(alert_severity, tags):
            logger.info(f"Alert suppressed by maintenance window: {title}")
            return {
                "alert_id": None,
                "status": "suppressed",
                "reason": "maintenance_window",
            }

        if policy_id is None:
            policy_id = self._select_policy(alert_severity, tags)

        if policy_id is None:
            raise ValueError(f"No escalation policy found for severity: {severity}")

        policy = self.get_policy(policy_id)
        if not policy:
            raise ValueError(f"Policy not found: {policy_id}")

        if not policy.enabled:
            raise ValueError(f"Policy is disabled: {policy.name}")

        alert = Alert(
            severity=alert_severity,
            title=title,
            description=description,
            context=context,
            policy_id=policy_id,
        )

        if self.deduplicate_alert(alert):
            logger.info(f"Alert deduplicated: {title}")
            return {
                "alert_id": alert.alert_id,
                "status": "deduplicated",
                "original_fingerprint": alert.fingerprint,
            }

        self.alerts[alert.alert_id] = alert

        alert_key = f"alert:{alert.alert_id}"
        self.redis.setex(
            alert_key,
            86400 * 7,  # 7 days TTL
            alert.model_dump_json(),
        )

        fingerprint_key = f"fingerprint:{alert.fingerprint}"
        self.redis.setex(
            fingerprint_key,
            self.deduplication_window_minutes * 60,
            alert.alert_id,
        )

        self._notify_level(alert, policy.levels[0])

        logger.info(
            f"Alert created: {alert.alert_id} "
            f"(severity: {severity}, policy: {policy.name})"
        )

        return {
            "alert_id": alert.alert_id,
            "status": "active",
            "severity": severity,
            "current_level": alert.current_level,
            "policy_id": policy_id,
            "fingerprint": alert.fingerprint,
        }

    def escalate_alert(self, alert_id: str) -> bool:
        """
        Escalate alert to next level.

        Args:
            alert_id: Alert ID

        Returns:
            True if escalated, False if already at max level or alert not found

        Raises:
            ValueError: If alert or policy not found
        """
        alert = self._get_alert(alert_id)
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")

        if not alert.is_active:
            logger.warning(f"Cannot escalate inactive alert: {alert_id}")
            return False

        policy = self.get_policy(alert.policy_id)
        if not policy:
            raise ValueError(f"Policy not found: {alert.policy_id}")

        if alert.current_level >= len(policy.levels):
            logger.warning(
                f"Alert {alert_id} already at max escalation level "
                f"({alert.current_level})"
            )
            return False

        alert.current_level += 1
        alert.escalated_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()

        next_level = policy.get_level(alert.current_level)
        if next_level:
            self._notify_level(alert, next_level)

        self._save_alert(alert)

        logger.info(
            f"Alert escalated: {alert_id} to level {alert.current_level} "
            f"({next_level.channels if next_level else 'unknown'})"
        )

        return True

    def check_escalation_needed(self, alert_id: str) -> bool:
        """
        Check if alert needs escalation based on time delays.

        Args:
            alert_id: Alert ID

        Returns:
            True if escalation is needed
        """
        alert = self._get_alert(alert_id)
        if not alert or not alert.is_active:
            return False

        policy = self.get_policy(alert.policy_id)
        if not policy or alert.current_level >= len(policy.levels):
            return False

        next_level = policy.get_level(alert.current_level + 1)
        if not next_level:
            return False

        time_since_last = datetime.utcnow() - (alert.escalated_at or alert.created_at)
        delay_threshold = timedelta(minutes=next_level.delay_minutes)

        return time_since_last >= delay_threshold

    def deduplicate_alert(self, alert: Alert) -> bool:
        """
        Check if alert is duplicate within deduplication window.

        Args:
            alert: Alert to check

        Returns:
            True if duplicate exists
        """
        fingerprint_key = f"fingerprint:{alert.fingerprint}"
        existing_alert_id = self.redis.get(fingerprint_key)

        if existing_alert_id:
            existing_alert_id = existing_alert_id.decode("utf-8")
            existing_alert = self._get_alert(existing_alert_id)

            if existing_alert and existing_alert.is_active:
                alert.deduplicated_from = existing_alert_id
                logger.debug(
                    f"Alert deduplicated: {alert.title} "
                    f"(matches {existing_alert_id})"
                )
                return True

        return False

    def suppress_alert(self, alert_id: str, reason: str = "") -> bool:
        """
        Suppress alert during maintenance window.

        Args:
            alert_id: Alert ID
            reason: Suppression reason

        Returns:
            True if suppressed successfully
        """
        alert = self._get_alert(alert_id)
        if not alert:
            logger.warning(f"Cannot suppress non-existent alert: {alert_id}")
            return False

        alert.suppressed = True
        alert.status = "suppressed"
        alert.context["suppression_reason"] = reason
        alert.updated_at = datetime.utcnow()

        self._save_alert(alert)

        logger.info(f"Alert suppressed: {alert_id} (reason: {reason})")
        return True

    def resolve_alert(self, alert_id: str, resolution: str = "") -> bool:
        """
        Resolve alert.

        Args:
            alert_id: Alert ID
            resolution: Resolution details

        Returns:
            True if resolved successfully
        """
        alert = self._get_alert(alert_id)
        if not alert:
            logger.warning(f"Cannot resolve non-existent alert: {alert_id}")
            return False

        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        alert.context["resolution"] = resolution

        self._save_alert(alert)

        logger.info(f"Alert resolved: {alert_id}")
        return True

    def create_suppression_rule(self, rule: SuppressionRule) -> str:
        """
        Create suppression rule for maintenance windows.

        Args:
            rule: Suppression rule

        Returns:
            Rule ID
        """
        self.suppression_rules[rule.rule_id] = rule

        rule_key = f"suppression:{rule.rule_id}"
        self.redis.setex(
            rule_key,
            86400 * 30,  # 30 days TTL
            rule.model_dump_json(),
        )

        logger.info(
            f"Created suppression rule: {rule.name} "
            f"({rule.start_time} to {rule.end_time})"
        )
        return rule.rule_id

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active alerts.

        Args:
            severity: Filter by severity (optional)

        Returns:
            List of active alerts
        """
        active_alerts = []

        for alert in self.alerts.values():
            if not alert.is_active:
                continue

            if severity and alert.severity != severity:
                continue

            active_alerts.append(
                {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "current_level": alert.current_level,
                    "created_at": alert.created_at.isoformat(),
                    "notification_count": alert.notification_count,
                }
            )

        return sorted(active_alerts, key=lambda x: x["created_at"], reverse=True)

    def get_escalation_candidates(self) -> List[str]:
        """
        Get alerts that need escalation.

        Returns:
            List of alert IDs requiring escalation
        """
        candidates = []

        for alert_id in self.alerts.keys():
            if self.check_escalation_needed(alert_id):
                candidates.append(alert_id)

        return candidates

    def aggregate_alerts(
        self, timeframe_minutes: int = 60, min_count: int = 3
    ) -> Dict[str, List[str]]:
        """
        Aggregate similar alerts for batch processing.

        Args:
            timeframe_minutes: Time window for aggregation
            min_count: Minimum alerts to trigger aggregation

        Returns:
            Dictionary of aggregated alerts by fingerprint
        """
        aggregated: Dict[str, List[str]] = {}
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeframe_minutes)

        for alert in self.alerts.values():
            if not alert.is_active or alert.created_at < cutoff_time:
                continue

            fingerprint = alert.fingerprint
            if fingerprint not in aggregated:
                aggregated[fingerprint] = []

            aggregated[fingerprint].append(alert.alert_id)

        return {
            fp: alert_ids
            for fp, alert_ids in aggregated.items()
            if len(alert_ids) >= min_count
        }

    def _get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert from cache or Redis."""
        if alert_id in self.alerts:
            return self.alerts[alert_id]

        alert_key = f"alert:{alert_id}"
        alert_data = self.redis.get(alert_key)
        if alert_data:
            alert = Alert.model_validate_json(alert_data)
            self.alerts[alert_id] = alert
            return alert

        return None

    def _save_alert(self, alert: Alert) -> None:
        """Save alert to Redis."""
        alert_key = f"alert:{alert.alert_id}"
        self.redis.setex(
            alert_key,
            86400 * 7,  # 7 days TTL
            alert.model_dump_json(),
        )
        self.alerts[alert.alert_id] = alert

    def _select_policy(self, severity: AlertSeverity, tags: List[str]) -> Optional[str]:
        """Select appropriate policy based on severity and tags."""
        matching_policies = [
            p for p in self.policies.values() if p.severity == severity and p.enabled
        ]

        if not matching_policies:
            return None

        if tags:
            for policy in matching_policies:
                if any(tag in policy.tags for tag in tags):
                    return policy.policy_id

        return matching_policies[0].policy_id if matching_policies else None

    def _should_suppress_alert(self, severity: AlertSeverity, tags: List[str]) -> bool:
        """Check if alert should be suppressed by active rules."""
        for rule in self.suppression_rules.values():
            if rule.should_suppress(severity, tags):
                return True
        return False

    def _notify_level(self, alert: Alert, level: EscalationLevel) -> None:
        """
        Send notifications for escalation level.

        Args:
            alert: Alert to notify
            level: Escalation level configuration
        """
        alert.last_notification_at = datetime.utcnow()
        alert.notification_count += 1

        alert.add_escalation_entry(
            level=level.level,
            channels=[ch.value for ch in level.channels],
            recipients=level.recipients,
        )

        logger.info(
            f"Notifying level {level.level} for alert {alert.alert_id}: "
            f"channels={[ch.value for ch in level.channels]}, "
            f"recipients={level.recipients}"
        )

        notification_data = {
            "alert_id": alert.alert_id,
            "level": level.level,
            "channels": [ch.value for ch in level.channels],
            "recipients": level.recipients,
            "timestamp": datetime.utcnow().isoformat(),
        }

        notification_key = f"notification:{alert.alert_id}:{level.level}"
        self.redis.setex(
            notification_key,
            86400,  # 1 day TTL
            json.dumps(notification_data),
        )
