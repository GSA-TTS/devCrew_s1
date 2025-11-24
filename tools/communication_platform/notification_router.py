"""
Notification Router - Route notifications to appropriate channels.

Routes notifications to multiple channels (Slack, Email, Teams, PagerDuty, SMS)
with intelligent channel selection based on priority and severity, lifecycle
tracking, and Redis-based queuing for async delivery.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import yaml
from pydantic import BaseModel, Field, field_validator
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

# Configure logging
logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Supported notification channels."""

    SLACK = "slack"
    EMAIL = "email"
    TEAMS = "teams"
    PAGERDUTY = "pagerduty"
    SMS = "sms"


class Priority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Severity(str, Enum):
    """Notification severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification lifecycle status."""

    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationRequest(BaseModel):
    """
    Notification request model.

    Represents a notification to be routed to one or more channels.
    """

    notification_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique notification identifier",
    )
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message content")
    priority: Priority = Field(
        default=Priority.MEDIUM, description="Notification priority"
    )
    severity: Severity = Field(
        default=Severity.INFO, description="Notification severity"
    )
    channels: Optional[List[ChannelType]] = Field(
        default=None,
        description="Explicit channel list (overrides auto-selection)",
    )
    recipients: Dict[str, List[str]] = Field(
        default_factory=dict,
        description=("Recipients per channel (e.g., {'email': ['user@example.com']})"),
    )
    template: Optional[str] = Field(
        default=None, description="Template name for message formatting"
    )
    template_data: Dict[str, Any] = Field(
        default_factory=dict, description="Data for template rendering"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    tags: List[str] = Field(default_factory=list, description="Notification tags")
    protocol: Optional[str] = Field(
        default=None,
        description="Protocol identifier (e.g., P-OPS-POSTMORTEM)",
    )
    source: Optional[str] = Field(
        default=None,
        description="Source system or agent",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Request creation timestamp",
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="Notification expiration timestamp"
    )
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    status: NotificationStatus = Field(
        default=NotificationStatus.QUEUED,
        description="Current status",
    )

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Priority) -> Priority:
        """Validate priority level."""
        if not isinstance(v, Priority):
            raise ValueError(f"Priority must be one of {[p.value for p in Priority]}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Severity) -> Severity:
        """Validate severity level."""
        if not isinstance(v, Severity):
            raise ValueError(f"Severity must be one of {[s.value for s in Severity]}")
        return v

    @field_validator("channels")
    @classmethod
    def validate_channels(
        cls, v: Optional[List[ChannelType]]
    ) -> Optional[List[ChannelType]]:
        """Validate channel types."""
        if v is not None:
            for channel in v:
                if not isinstance(channel, ChannelType):
                    raise ValueError(
                        "Channel must be one of " f"{[c.value for c in ChannelType]}"
                    )
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = self.model_dump()
        # Convert enums to strings
        data["priority"] = self.priority.value
        data["severity"] = self.severity.value
        data["status"] = self.status.value
        if self.channels:
            data["channels"] = [c.value for c in self.channels]
        # Convert datetime to ISO format
        data["created_at"] = self.created_at.isoformat()
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationRequest":
        """Create from dictionary."""
        # Convert string enums back to enum types
        if "priority" in data and isinstance(data["priority"], str):
            data["priority"] = Priority(data["priority"])
        if "severity" in data and isinstance(data["severity"], str):
            data["severity"] = Severity(data["severity"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = NotificationStatus(data["status"])
        if "channels" in data and data["channels"]:
            data["channels"] = [ChannelType(c) for c in data["channels"]]
        # Convert ISO strings to datetime
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "expires_at" in data and isinstance(data["expires_at"], str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        return cls(**data)


class RoutingRule(BaseModel):
    """
    Routing rule for channel selection.

    Defines conditions and resulting channels for notification routing.
    """

    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    conditions: Dict[str, Any] = Field(
        default_factory=dict, description="Matching conditions"
    )
    channels: List[ChannelType] = Field(
        default_factory=list, description="Channels to route to"
    )
    priority: int = Field(default=100, description="Rule priority (lower = higher)")
    enabled: bool = Field(default=True, description="Whether rule is active")

    def matches(self, request: NotificationRequest) -> bool:
        """
        Check if request matches this rule's conditions.

        Args:
            request: Notification request to check

        Returns:
            True if request matches all conditions
        """
        if not self.enabled:
            return False

        for key, value in self.conditions.items():
            if key == "priority":
                if isinstance(value, list):
                    if request.priority.value not in value:
                        return False
                elif request.priority.value != value:
                    return False
            elif key == "severity":
                if isinstance(value, list):
                    if request.severity.value not in value:
                        return False
                elif request.severity.value != value:
                    return False
            elif key == "protocol":
                if isinstance(value, list):
                    if request.protocol not in value:
                        return False
                elif request.protocol != value:
                    return False
            elif key == "tags":
                # Match if any tag in value is present in request.tags
                if isinstance(value, list):
                    if not any(tag in request.tags for tag in value):
                        return False
            elif key == "source":
                if isinstance(value, list):
                    if request.source not in value:
                        return False
                elif request.source != value:
                    return False

        return True


class NotificationRouter:
    """
    Route notifications to appropriate channels.

    Provides intelligent channel selection based on priority/severity,
    custom routing rules, lifecycle tracking, and Redis-based queuing.
    """

    # Default routing rules based on priority
    DEFAULT_ROUTING: Dict[Priority, List[ChannelType]] = {
        Priority.CRITICAL: [ChannelType.SLACK, ChannelType.PAGERDUTY],
        Priority.HIGH: [ChannelType.SLACK, ChannelType.EMAIL],
        Priority.MEDIUM: [ChannelType.SLACK],
        Priority.LOW: [ChannelType.EMAIL],
    }

    # Severity-based routing (used as fallback or override)
    SEVERITY_ROUTING: Dict[Severity, List[ChannelType]] = {
        Severity.CRITICAL: [
            ChannelType.SLACK,
            ChannelType.PAGERDUTY,
            ChannelType.SMS,
        ],
        Severity.ERROR: [ChannelType.SLACK, ChannelType.EMAIL],
        Severity.WARNING: [ChannelType.SLACK],
        Severity.INFO: [ChannelType.EMAIL],
    }

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        routing_rules: Optional[List[RoutingRule]] = None,
        queue_prefix: str = "notification:queue",
        status_prefix: str = "notification:status",
    ):
        """
        Initialize notification router.

        Args:
            redis_client: Redis client for queue management
            routing_rules: Custom routing rules
            queue_prefix: Redis key prefix for notification queue
            status_prefix: Redis key prefix for status tracking
        """
        self.redis_client = redis_client
        self.routing_rules = routing_rules or []
        self.queue_prefix = queue_prefix
        self.status_prefix = status_prefix

        # Sort routing rules by priority
        self.routing_rules.sort(key=lambda r: r.priority)

        logger.info(
            f"NotificationRouter initialized with {len(self.routing_rules)} "
            f"custom routing rules"
        )

    def parse_request(self, data: Dict[str, Any]) -> NotificationRequest:
        """
        Parse notification request from dictionary.

        Supports both JSON and YAML-compatible dictionaries.

        Args:
            data: Request data dictionary

        Returns:
            Parsed NotificationRequest

        Raises:
            ValueError: If data is invalid
        """
        try:
            return NotificationRequest.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to parse notification request: {e}")
            raise ValueError(f"Invalid notification request data: {e}") from e

    def parse_request_yaml(self, yaml_str: str) -> NotificationRequest:
        """
        Parse notification request from YAML string.

        Args:
            yaml_str: YAML string representation

        Returns:
            Parsed NotificationRequest

        Raises:
            ValueError: If YAML is invalid
        """
        try:
            data = yaml.safe_load(yaml_str)
            return self.parse_request(data)
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML: {e}")
            raise ValueError(f"Invalid YAML format: {e}") from e

    def parse_request_json(self, json_str: str) -> NotificationRequest:
        """
        Parse notification request from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            Parsed NotificationRequest

        Raises:
            ValueError: If JSON is invalid
        """
        try:
            data = json.loads(json_str)
            return self.parse_request(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise ValueError(f"Invalid JSON format: {e}") from e

    def select_channels(self, severity: str, priority: str) -> List[str]:
        """
        Select channels based on severity and priority.

        Uses default routing logic:
        - Priority takes precedence
        - Severity used for additional context
        - Combines channels from both if applicable

        Args:
            severity: Severity level (info, warning, error, critical)
            priority: Priority level (low, medium, high, critical)

        Returns:
            List of channel names

        Raises:
            ValueError: If severity or priority is invalid
        """
        try:
            sev = Severity(severity)
            pri = Priority(priority)
        except ValueError as e:
            logger.error(f"Invalid severity or priority: {e}")
            raise ValueError(f"Invalid severity or priority: {e}") from e

        channels: Set[ChannelType] = set()

        # Add channels based on priority
        if pri in self.DEFAULT_ROUTING:
            channels.update(self.DEFAULT_ROUTING[pri])

        # Add additional channels based on severity if critical
        if sev == Severity.CRITICAL and sev in self.SEVERITY_ROUTING:
            channels.update(self.SEVERITY_ROUTING[sev])

        return [c.value for c in sorted(channels, key=lambda x: x.value)]

    def apply_routing_rules(self, request: NotificationRequest) -> List[str]:
        """
        Apply custom routing rules to determine channels.

        Evaluates rules in priority order and returns channels from
        the first matching rule.

        Args:
            request: Notification request

        Returns:
            List of channel names from matching rules
        """
        channels: Set[ChannelType] = set()

        # Apply custom routing rules
        for rule in self.routing_rules:
            if rule.matches(request):
                channels.update(rule.channels)
                logger.debug(
                    f"Applied routing rule '{rule.name}' to "
                    f"notification {request.notification_id}"
                )

        return [c.value for c in sorted(channels, key=lambda x: x.value)]

    def _determine_channels(self, request: NotificationRequest) -> List[ChannelType]:
        """
        Determine final channels for notification.

        Priority:
        1. Explicit channels in request
        2. Custom routing rules
        3. Default priority-based routing
        4. Severity-based routing

        Args:
            request: Notification request

        Returns:
            List of channel types
        """
        channels: Set[ChannelType] = set()

        # 1. Use explicit channels if provided
        if request.channels:
            channels.update(request.channels)
            logger.debug(
                f"Using explicit channels for notification "
                f"{request.notification_id}: {[c.value for c in channels]}"
            )
            return sorted(channels, key=lambda x: x.value)

        # 2. Apply custom routing rules
        rule_channels = self.apply_routing_rules(request)
        if rule_channels:
            channels.update(ChannelType(c) for c in rule_channels)

        # 3. Apply default priority-based routing
        if request.priority in self.DEFAULT_ROUTING:
            channels.update(self.DEFAULT_ROUTING[request.priority])

        # 4. Apply severity-based routing for critical cases
        if request.severity == Severity.CRITICAL:
            if request.severity in self.SEVERITY_ROUTING:
                channels.update(self.SEVERITY_ROUTING[request.severity])

        # Default to email if no channels determined
        if not channels:
            channels.add(ChannelType.EMAIL)
            logger.warning(
                f"No channels determined for notification "
                f"{request.notification_id}, defaulting to email"
            )

        return sorted(channels, key=lambda x: x.value)

    def queue_notification(self, request: NotificationRequest) -> str:
        """
        Queue notification for async delivery.

        Adds notification to Redis queue with lifecycle tracking.

        Args:
            request: Notification request

        Returns:
            Notification ID

        Raises:
            RuntimeError: If Redis is unavailable
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not configured for queuing")

        try:
            # Update status
            request.status = NotificationStatus.QUEUED

            # Store in queue
            queue_key = f"{self.queue_prefix}:{request.notification_id}"
            self.redis_client.setex(
                queue_key,
                3600,  # 1 hour TTL
                json.dumps(request.to_dict()),
            )

            # Add to processing queue
            processing_queue = f"{self.queue_prefix}:pending"
            self.redis_client.lpush(processing_queue, request.notification_id)

            # Store status
            self._update_status(request)

            logger.info(
                f"Queued notification {request.notification_id} "
                f"with priority {request.priority.value}"
            )

            return request.notification_id

        except RedisConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            raise RuntimeError(f"Failed to queue notification: {e}") from e

    def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Get notification status and details.

        Args:
            notification_id: Notification identifier

        Returns:
            Status information dictionary

        Raises:
            ValueError: If notification not found
            RuntimeError: If Redis is unavailable
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not configured")

        try:
            # Get from status store
            status_key = f"{self.status_prefix}:{notification_id}"
            status_data = self.redis_client.get(status_key)

            if not status_data:
                # Try queue store as fallback
                queue_key = f"{self.queue_prefix}:{notification_id}"
                queue_data = self.redis_client.get(queue_key)

                if not queue_data:
                    raise ValueError(f"Notification {notification_id} not found")

                data = json.loads(queue_data)
            else:
                data = json.loads(status_data)

            return data

        except RedisConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            raise RuntimeError(f"Failed to get notification status: {e}") from e

    def _update_status(self, request: NotificationRequest) -> None:
        """
        Update notification status in Redis.

        Args:
            request: Notification request with updated status
        """
        if not self.redis_client:
            return

        try:
            status_key = f"{self.status_prefix}:{request.notification_id}"
            self.redis_client.setex(
                status_key,
                86400,  # 24 hour TTL
                json.dumps(request.to_dict()),
            )
        except RedisConnectionError as e:
            logger.error(f"Failed to update status: {e}")

    def route(self, request: NotificationRequest) -> Dict[str, Any]:
        """
        Main routing method - route notification to appropriate channels.

        Determines channels, validates request, and either queues for
        async delivery or returns routing information.

        Args:
            request: Notification request

        Returns:
            Routing result with notification_id, channels, and status

        Raises:
            ValueError: If request is invalid
            RuntimeError: If routing fails
        """
        try:
            # Check if notification has expired
            if request.expires_at:
                now = datetime.now(timezone.utc)
                if now > request.expires_at:
                    logger.warning(
                        f"Notification {request.notification_id} has expired"
                    )
                    request.status = NotificationStatus.FAILED
                    return {
                        "notification_id": request.notification_id,
                        "status": request.status.value,
                        "error": "Notification expired",
                        "channels": [],
                    }

            # Determine channels
            channels = self._determine_channels(request)

            # Queue notification if Redis is available
            if self.redis_client:
                notification_id = self.queue_notification(request)
            else:
                notification_id = request.notification_id
                logger.warning(
                    "Redis not available, notification not queued for " "async delivery"
                )

            result = {
                "notification_id": notification_id,
                "status": request.status.value,
                "channels": [c.value for c in channels],
                "priority": request.priority.value,
                "severity": request.severity.value,
                "queued": self.redis_client is not None,
                "created_at": request.created_at.isoformat(),
            }

            logger.info(
                f"Routed notification {notification_id} to channels: "
                f"{[c.value for c in channels]}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to route notification: {e}")
            raise RuntimeError(f"Routing failed: {e}") from e

    def add_routing_rule(self, rule: RoutingRule) -> None:
        """
        Add custom routing rule.

        Args:
            rule: Routing rule to add
        """
        self.routing_rules.append(rule)
        # Re-sort by priority
        self.routing_rules.sort(key=lambda r: r.priority)
        logger.info(f"Added routing rule '{rule.name}' with priority {rule.priority}")

    def remove_routing_rule(self, rule_id: str) -> bool:
        """
        Remove routing rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            True if rule was removed, False otherwise
        """
        original_count = len(self.routing_rules)
        self.routing_rules = [r for r in self.routing_rules if r.rule_id != rule_id]
        removed = len(self.routing_rules) < original_count

        if removed:
            logger.info(f"Removed routing rule {rule_id}")
        else:
            logger.warning(f"Routing rule {rule_id} not found")

        return removed

    def get_routing_rules(self) -> List[RoutingRule]:
        """
        Get all routing rules.

        Returns:
            List of routing rules sorted by priority
        """
        return self.routing_rules.copy()

    def load_routing_rules_from_config(self, config_path: str) -> None:
        """
        Load routing rules from YAML config file.

        Args:
            config_path: Path to YAML config file

        Raises:
            ValueError: If config file is invalid
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if "routing_rules" not in config:
                raise ValueError("Config file missing 'routing_rules' section")

            for rule_data in config["routing_rules"]:
                # Convert channel strings to ChannelType
                if "channels" in rule_data:
                    rule_data["channels"] = [
                        ChannelType(c) for c in rule_data["channels"]
                    ]

                rule = RoutingRule(**rule_data)
                self.add_routing_rule(rule)

            logger.info(
                f"Loaded {len(config['routing_rules'])} routing rules "
                f"from {config_path}"
            )

        except FileNotFoundError as e:
            logger.error(f"Config file not found: {config_path}")
            raise ValueError(f"Config file not found: {config_path}") from e
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse config YAML: {e}")
            raise ValueError(f"Invalid YAML in config file: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load routing rules: {e}")
            raise ValueError(f"Failed to load routing rules: {e}") from e


# Example usage and factory functions
def create_notification_router(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_db: int = 0,
    routing_rules: Optional[List[RoutingRule]] = None,
) -> NotificationRouter:
    """
    Factory function to create NotificationRouter with Redis.

    Args:
        redis_host: Redis host
        redis_port: Redis port
        redis_db: Redis database number
        routing_rules: Custom routing rules

    Returns:
        Configured NotificationRouter instance
    """
    try:
        redis_client = Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        # Test connection
        redis_client.ping()
        logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
    except RedisConnectionError as e:
        logger.warning(f"Redis connection failed: {e}. Router will run without queue.")
        redis_client = None

    return NotificationRouter(
        redis_client=redis_client,
        routing_rules=routing_rules,
    )


def create_notification_request(
    title: str,
    message: str,
    priority: str = "medium",
    severity: str = "info",
    recipients: Optional[Dict[str, List[str]]] = None,
    **kwargs: Any,
) -> NotificationRequest:
    """
    Factory function to create NotificationRequest.

    Args:
        title: Notification title
        message: Notification message
        priority: Priority level
        severity: Severity level
        recipients: Recipients per channel
        **kwargs: Additional fields

    Returns:
        NotificationRequest instance
    """
    return NotificationRequest(
        title=title,
        message=message,
        priority=Priority(priority),
        severity=Severity(severity),
        recipients=recipients or {},
        **kwargs,
    )
