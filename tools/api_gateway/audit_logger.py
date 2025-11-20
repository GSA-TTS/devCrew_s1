"""
Issue #41: Audit Logger Module
Implements comprehensive audit logging for compliance and security.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import structlog
from pydantic import BaseModel, Field


# Audit event types
class AuditEventType(str, Enum):
    """Audit event types."""

    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"

    # Customer data events
    CUSTOMER_CREATE = "customer_create"
    CUSTOMER_READ = "customer_read"
    CUSTOMER_UPDATE = "customer_update"
    CUSTOMER_DELETE = "customer_delete"
    CUSTOMER_EXPORT = "customer_export"

    # Privacy events
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    DATA_ANONYMIZED = "data_anonymized"
    DATA_ERASED = "data_erased"
    PII_ACCESSED = "pii_accessed"

    # API events
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Admin events
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"

    # Data pipeline events
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"

    # Feedback events
    FEEDBACK_RECEIVED = "feedback_received"
    FEEDBACK_PROCESSED = "feedback_processed"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent(BaseModel):
    """Audit event model."""

    event_id: str = Field(default_factory=lambda: f"evt_{datetime.utcnow().timestamp()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.INFO
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    status: str  # success, failure, pending
    details: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


class AuditLogger:
    """Audit logger for compliance and security."""

    def __init__(self, logger_name: str = "audit"):
        """
        Initialize audit logger.

        Args:
            logger_name: Logger name
        """
        self.logger = structlog.get_logger(logger_name)
        self.standard_logger = logging.getLogger(logger_name)
        self.standard_logger.setLevel(logging.INFO)

    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: Audit event to log
        """
        event_dict = event.model_dump()

        # Convert datetime to string
        event_dict["timestamp"] = event.timestamp.isoformat()

        # Log to structured logger
        self.logger.info(
            f"audit_event_{event.event_type}",
            **event_dict,
        )

        # Also log to standard logger for backward compatibility
        self.standard_logger.info(json.dumps(event_dict))

    def log_authentication(
        self,
        event_type: AuditEventType,
        username: str,
        ip_address: str,
        status: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log authentication event.

        Args:
            event_type: Authentication event type
            username: Username
            ip_address: IP address
            status: Event status
            user_id: User ID
            details: Additional details
        """
        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.WARNING
            if event_type == AuditEventType.LOGIN_FAILED
            else AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action=event_type.value,
            status=status,
            details=details or {},
        )
        self.log_event(event)

    def log_customer_operation(
        self,
        event_type: AuditEventType,
        user_id: int,
        username: str,
        customer_id: str,
        action: str,
        status: str,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log customer data operation.

        Args:
            event_type: Customer operation event type
            user_id: User ID performing operation
            username: Username
            customer_id: Customer ID
            action: Action performed
            status: Operation status
            ip_address: IP address
            details: Additional details
        """
        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            resource_type="customer",
            resource_id=customer_id,
            action=action,
            status=status,
            details=details or {},
        )
        self.log_event(event)

    def log_privacy_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[int],
        username: Optional[str],
        customer_id: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log privacy-related event.

        Args:
            event_type: Privacy event type
            user_id: User ID
            username: Username
            customer_id: Customer ID
            action: Action performed
            status: Event status
            details: Additional details
        """
        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            username=username,
            resource_type="customer",
            resource_id=customer_id,
            action=action,
            status=status,
            details=details or {},
        )
        self.log_event(event)

    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        duration_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log API request.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            user_id: User ID
            username: Username
            ip_address: IP address
            duration_ms: Request duration in milliseconds
            details: Additional details
        """
        event_type = (
            AuditEventType.API_ERROR
            if status_code >= 400
            else AuditEventType.API_REQUEST
        )
        severity = AuditSeverity.ERROR if status_code >= 500 else AuditSeverity.INFO

        event_details = details or {}
        event_details.update(
            {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }
        )

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action=f"{method} {path}",
            status="success" if status_code < 400 else "failure",
            details=event_details,
        )
        self.log_event(event)

    def log_rate_limit(
        self,
        user_id: Optional[int],
        username: Optional[str],
        ip_address: str,
        limit_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log rate limit exceeded event.

        Args:
            user_id: User ID
            username: Username
            ip_address: IP address
            limit_type: Type of rate limit
            details: Additional details
        """
        event_details = details or {}
        event_details["limit_type"] = limit_type

        event = AuditEvent(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action="rate_limit_exceeded",
            status="blocked",
            details=event_details,
        )
        self.log_event(event)

    def log_role_change(
        self,
        event_type: AuditEventType,
        admin_user_id: int,
        admin_username: str,
        target_user_id: int,
        target_username: str,
        role: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log role change event.

        Args:
            event_type: Role event type
            admin_user_id: Admin user ID
            admin_username: Admin username
            target_user_id: Target user ID
            target_username: Target username
            role: Role name
            status: Event status
            details: Additional details
        """
        event_details = details or {}
        event_details.update(
            {
                "target_user_id": target_user_id,
                "target_username": target_username,
                "role": role,
            }
        )

        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.WARNING,
            user_id=admin_user_id,
            username=admin_username,
            resource_type="user_role",
            resource_id=str(target_user_id),
            action=event_type.value,
            status=status,
            details=event_details,
        )
        self.log_event(event)

    def log_pipeline_event(
        self,
        event_type: AuditEventType,
        pipeline_name: str,
        pipeline_id: str,
        status: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log data pipeline event.

        Args:
            event_type: Pipeline event type
            pipeline_name: Pipeline name
            pipeline_id: Pipeline ID
            status: Pipeline status
            user_id: User ID
            username: Username
            details: Additional details
        """
        event_details = details or {}
        event_details["pipeline_name"] = pipeline_name

        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.ERROR
            if event_type == AuditEventType.PIPELINE_FAILED
            else AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            resource_type="pipeline",
            resource_id=pipeline_id,
            action=event_type.value,
            status=status,
            details=event_details,
        )
        self.log_event(event)

    def log_feedback_event(
        self,
        event_type: AuditEventType,
        feedback_id: str,
        status: str,
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log feedback event.

        Args:
            event_type: Feedback event type
            feedback_id: Feedback ID
            status: Event status
            source: Feedback source
            details: Additional details
        """
        event_details = details or {}
        if source:
            event_details["source"] = source

        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            resource_type="feedback",
            resource_id=feedback_id,
            action=event_type.value,
            status=status,
            details=event_details,
        )
        self.log_event(event)


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions
def log_login(
    username: str, ip_address: str, success: bool, user_id: Optional[int] = None
) -> None:
    """Log login attempt."""
    audit_logger.log_authentication(
        event_type=AuditEventType.LOGIN
        if success
        else AuditEventType.LOGIN_FAILED,
        username=username,
        ip_address=ip_address,
        status="success" if success else "failure",
        user_id=user_id,
    )


def log_customer_read(
    user_id: int, username: str, customer_id: str, ip_address: Optional[str] = None
) -> None:
    """Log customer data read."""
    audit_logger.log_customer_operation(
        event_type=AuditEventType.CUSTOMER_READ,
        user_id=user_id,
        username=username,
        customer_id=customer_id,
        action="read",
        status="success",
        ip_address=ip_address,
    )


def log_pii_access(
    user_id: int, username: str, customer_id: str, pii_fields: list
) -> None:
    """Log PII access."""
    audit_logger.log_privacy_event(
        event_type=AuditEventType.PII_ACCESSED,
        user_id=user_id,
        username=username,
        customer_id=customer_id,
        action="pii_accessed",
        status="success",
        details={"pii_fields": pii_fields},
    )


def log_data_erasure(customer_id: str, reason: str) -> None:
    """Log data erasure for GDPR compliance."""
    audit_logger.log_privacy_event(
        event_type=AuditEventType.DATA_ERASED,
        user_id=None,
        username="system",
        customer_id=customer_id,
        action="data_erased",
        status="success",
        details={"reason": reason},
    )
