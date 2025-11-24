"""
Communication & Notification Platform.

Multi-channel notification and stakeholder communication platform enabling
autonomous agents and humans to send notifications across Slack, Email,
Microsoft Teams, and PagerDuty with template-based messaging, delivery
tracking, escalation rules, and rate limiting.

Core Components:
    - Notification Router: Route notifications to appropriate channels
    - Slack Integration: Slack SDK with Block Kit formatting
    - Email Service: SendGrid/SMTP with Jinja2 templates
    - Alert Manager: Escalation rules and on-call scheduling
    - Delivery Tracker: Track delivery status with retry logic
    - Rate Limiter: Redis-based rate limiting
    - Template Engine: Jinja2 templates with versioning
    - CLI Interface: Command-line notification management

Protocols Supported:
    - P-OPS-POSTMORTEM: Postmortem completion notifications
    - P-STAKEHOLDER-COMM: Stakeholder communication
    - CA-CS-NotifyHuman: Agent-to-human notifications
    - P-HUB-SPOKE-COORDINATION: Hub-spoke coordination updates
    - P-OBSERVABILITY: System health alerts
    - P-SYSTEM-NOTIFY: Infrastructure notifications
"""

__version__ = "1.0.0"
__author__ = "devCrew_s1"

from .alert_manager import AlertManager, EscalationPolicy
from .delivery_tracker import DeliveryStatus, DeliveryTracker
from .email_service import EmailMessage, EmailService
from .notification_router import NotificationRequest, NotificationRouter
from .notification_service import NotificationService
from .rate_limiter import RateLimit, RateLimiter
from .slack_integration import SlackIntegration, SlackMessage
from .template_engine import Template, TemplateEngine

__all__ = [
    "NotificationRouter",
    "NotificationRequest",
    "SlackIntegration",
    "SlackMessage",
    "EmailService",
    "EmailMessage",
    "AlertManager",
    "EscalationPolicy",
    "DeliveryTracker",
    "DeliveryStatus",
    "RateLimiter",
    "RateLimit",
    "TemplateEngine",
    "Template",
    "NotificationService",
]
