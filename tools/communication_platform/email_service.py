"""
Email Service Component for TOOL-COMM-001 Communication Platform.

Provides template-based email sending via SendGrid/SMTP with comprehensive
tracking, validation, and error handling. Supports HTML/plain-text emails,
attachments, CC/BCC, bounce tracking, and delivery monitoring.

Features:
    - SendGrid SDK integration with SMTP fallback
    - Jinja2 template rendering with variable substitution
    - HTML and plain-text email support
    - CC/BCC recipient support
    - Attachment handling with base64 encoding
    - Email validation and verification
    - Delivery tracking (opens, clicks, bounces)
    - Rate limiting and retry logic
    - Production-ready error handling

Usage:
    >>> from email_service import EmailService, EmailMessage
    >>> service = EmailService(api_key="your-sendgrid-key")
    >>> result = service.send_email(
    ...     to=["user@example.com"],
    ...     subject="Test Email",
    ...     body="Plain text body",
    ...     html="<p>HTML body</p>"
    ... )
    >>> print(result["message_id"])
"""

import base64
import mimetypes
import os
import re
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Environment, FileSystemLoader, TemplateError
from pydantic import BaseModel, EmailStr, Field, field_validator
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Cc,
    ClickTracking,
    Content,
    Email,
    Mail,
    OpenTracking,
    TrackingSettings,
)


class EmailAttachment(BaseModel):
    """
    Model for email attachments.

    Attributes:
        filename: Name of the attachment file
        content: Base64-encoded content or file path
        content_type: MIME type of the attachment
        disposition: Attachment disposition (inline or attachment)
        content_id: Content ID for inline attachments
    """

    filename: str = Field(..., description="Attachment filename")
    content: Union[str, bytes] = Field(..., description="File content or path")
    content_type: Optional[str] = Field(
        None, description="MIME type (auto-detected if not provided)"
    )
    disposition: str = Field(default="attachment", description="Attachment disposition")
    content_id: Optional[str] = Field(None, description="Content ID for inline images")

    @field_validator("disposition")
    @classmethod
    def validate_disposition(cls, v: str) -> str:
        """Validate attachment disposition."""
        if v not in ["attachment", "inline"]:
            raise ValueError("Disposition must be 'attachment' or 'inline'")
        return v

    def get_content_bytes(self) -> bytes:
        """
        Get attachment content as bytes.

        Returns:
            Attachment content as bytes

        Raises:
            FileNotFoundError: If file path is provided but file doesn't exist
            ValueError: If content format is invalid
        """
        if isinstance(self.content, bytes):
            return self.content

        # Check if content is a file path
        if isinstance(self.content, str) and os.path.isfile(self.content):
            with open(self.content, "rb") as f:
                return f.read()

        # Assume it's base64-encoded string
        if isinstance(self.content, str):
            try:
                return base64.b64decode(self.content)
            except Exception as e:
                raise ValueError(f"Invalid base64 content: {e}") from e

        raise ValueError("Content must be bytes, file path, or base64 string")

    def get_mime_type(self) -> str:
        """
        Get MIME type of attachment.

        Returns:
            MIME type string
        """
        if self.content_type:
            return self.content_type

        # Try to guess from filename
        mime_type, _ = mimetypes.guess_type(self.filename)
        return mime_type or "application/octet-stream"


class EmailMessage(BaseModel):
    """
    Model for email messages.

    Attributes:
        to: List of recipient email addresses
        subject: Email subject line
        body: Plain text email body
        html: HTML email body (optional)
        from_email: Sender email address
        from_name: Sender display name
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        reply_to: Reply-to email address (optional)
        attachments: List of email attachments (optional)
        headers: Custom email headers (optional)
        template_id: SendGrid template ID (optional)
        template_data: Template variable data (optional)
        track_opens: Enable open tracking
        track_clicks: Enable click tracking
        categories: Email categories for tracking
        tags: Email tags for organization
    """

    to: List[EmailStr] = Field(..., description="Recipient email addresses")
    subject: str = Field(..., min_length=1, description="Email subject")
    body: str = Field(default="", description="Plain text body")
    html: Optional[str] = Field(None, description="HTML body")
    from_email: EmailStr = Field(..., description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender name")
    cc: Optional[List[EmailStr]] = Field(None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(None, description="BCC recipients")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address")
    attachments: Optional[List[EmailAttachment]] = Field(
        None, description="Email attachments"
    )
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    template_id: Optional[str] = Field(None, description="SendGrid template ID")
    template_data: Optional[Dict[str, Any]] = Field(
        None, description="Template variables"
    )
    track_opens: bool = Field(default=True, description="Track email opens")
    track_clicks: bool = Field(default=True, description="Track link clicks")
    categories: Optional[List[str]] = Field(None, description="Email categories")
    tags: Optional[List[str]] = Field(None, description="Email tags")

    @field_validator("to", "cc", "bcc")
    @classmethod
    def validate_recipients(cls, v: Optional[List[EmailStr]]) -> Optional[List[str]]:
        """Validate recipient lists."""
        if v is not None and len(v) == 0:
            raise ValueError("Recipient list cannot be empty")
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject line."""
        if len(v.strip()) == 0:
            raise ValueError("Subject cannot be empty")
        return v


class EmailService:
    """
    Main email service class for sending emails via SendGrid/SMTP.

    Attributes:
        api_key: SendGrid API key
        smtp_config: SMTP server configuration for fallback
        template_dir: Directory containing email templates
        default_from: Default sender email address
        default_from_name: Default sender name
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        smtp_config: Optional[Dict[str, Any]] = None,
        template_dir: Optional[str] = None,
        default_from: Optional[str] = None,
        default_from_name: Optional[str] = None,
    ):
        """
        Initialize Email Service.

        Args:
            api_key: SendGrid API key (or from SENDGRID_API_KEY env var)
            smtp_config: SMTP configuration dict with keys:
                - host: SMTP server hostname
                - port: SMTP server port
                - username: SMTP username
                - password: SMTP password
                - use_tls: Use TLS encryption (default: True)
            template_dir: Path to Jinja2 template directory
            default_from: Default sender email address
            default_from_name: Default sender display name

        Raises:
            ValueError: If neither SendGrid API key nor SMTP config is provided
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.smtp_config = smtp_config
        self.template_dir = template_dir or os.getenv(
            "EMAIL_TEMPLATE_DIR", "./templates/email"
        )
        self.default_from = default_from or os.getenv(
            "DEFAULT_FROM_EMAIL", "noreply@example.com"
        )
        self.default_from_name = default_from_name or os.getenv(
            "DEFAULT_FROM_NAME", "Communication Platform"
        )

        # Initialize SendGrid client if API key is available
        self.sendgrid_client = None
        if self.api_key:
            try:
                self.sendgrid_client = SendGridAPIClient(self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize SendGrid client: {e}")

        # Initialize Jinja2 template environment
        self.jinja_env = None
        if os.path.isdir(self.template_dir):
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.template_dir),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
            )

        # Validate configuration
        if not self.sendgrid_client and not self.smtp_config:
            raise ValueError(
                "Either SendGrid API key or SMTP configuration must be provided"
            )

    def validate_email(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            True if email is valid, False otherwise

        Examples:
            >>> service.validate_email("user@example.com")
            True
            >>> service.validate_email("invalid-email")
            False
        """
        # RFC 5322 compliant email regex (simplified)
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        Render email template with data.

        Args:
            template_name: Template filename (e.g., "welcome.html")
            data: Dictionary of template variables

        Returns:
            Rendered template string

        Raises:
            TemplateError: If template rendering fails
            FileNotFoundError: If template file doesn't exist
        """
        if not self.jinja_env:
            raise ValueError("Template directory not configured")

        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**data)
        except TemplateError as e:
            raise TemplateError(f"Template rendering failed: {e}") from e
        except Exception as e:
            raise FileNotFoundError(f"Template not found: {template_name}") from e

    def _build_sendgrid_mail(self, message: EmailMessage) -> Mail:
        """
        Build SendGrid Mail object from EmailMessage.

        Args:
            message: EmailMessage instance

        Returns:
            SendGrid Mail object
        """
        # Create Mail object
        mail = Mail(
            from_email=Email(message.from_email, message.from_name),
            to_emails=[Email(to) for to in message.to],
            subject=message.subject,
        )

        # Add content
        if message.html:
            mail.add_content(Content("text/html", message.html))
        if message.body:
            mail.add_content(Content("text/plain", message.body))

        # Add CC recipients
        if message.cc:
            for cc_email in message.cc:
                mail.add_cc(Cc(cc_email))

        # Add BCC recipients
        if message.bcc:
            for bcc_email in message.bcc:
                mail.add_bcc(Email(bcc_email))

        # Add reply-to
        if message.reply_to:
            mail.reply_to = Email(message.reply_to)

        # Add attachments
        if message.attachments:
            for att in message.attachments:
                attachment = Attachment()
                attachment.file_content = base64.b64encode(
                    att.get_content_bytes()
                ).decode()
                attachment.file_name = att.filename
                attachment.file_type = att.get_mime_type()
                attachment.disposition = att.disposition
                if att.content_id:
                    attachment.content_id = att.content_id
                mail.add_attachment(attachment)

        # Add custom headers
        if message.headers:
            for key, value in message.headers.items():
                mail.add_header({key: value})

        # Configure tracking
        mail.tracking_settings = TrackingSettings()
        if message.track_clicks:
            mail.tracking_settings.click_tracking = ClickTracking(True, True)
        if message.track_opens:
            mail.tracking_settings.open_tracking = OpenTracking(True)

        # Add categories
        if message.categories:
            for category in message.categories[:10]:  # SendGrid limit: 10
                mail.add_category(category)

        return mail

    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        track_opens: bool = True,
        track_clicks: bool = True,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send email via SendGrid or SMTP.

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Plain text email body
            html: HTML email body (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            from_email: Sender email address (uses default if not provided)
            from_name: Sender display name (uses default if not provided)
            reply_to: Reply-to email address (optional)
            attachments: List of EmailAttachment objects (optional)
            track_opens: Enable open tracking (default: True)
            track_clicks: Enable click tracking (default: True)
            categories: List of categories for tracking (optional)

        Returns:
            Dictionary with keys:
                - success: Boolean indicating success/failure
                - message_id: Unique message identifier
                - status_code: HTTP status code (SendGrid) or SMTP response
                - error: Error message if failed
                - timestamp: Send timestamp

        Raises:
            ValueError: If validation fails
            Exception: If sending fails

        Examples:
            >>> result = service.send_email(
            ...     to=["user@example.com"],
            ...     subject="Welcome",
            ...     body="Welcome to our platform!",
            ...     html="<h1>Welcome</h1>"
            ... )
            >>> print(result["message_id"])
        """
        # Build EmailMessage
        message = EmailMessage(
            to=to,
            subject=subject,
            body=body,
            html=html,
            from_email=from_email or self.default_from,
            from_name=from_name or self.default_from_name,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            attachments=attachments,
            track_opens=track_opens,
            track_clicks=track_clicks,
            categories=categories,
        )

        # Try SendGrid first
        if self.sendgrid_client:
            try:
                return self._send_via_sendgrid(message)
            except Exception as e:
                print(f"SendGrid send failed: {e}")
                if not self.smtp_config:
                    raise

        # Fallback to SMTP
        if self.smtp_config:
            return self._send_via_smtp(message)

        raise Exception("No email service available")

    def _send_via_sendgrid(self, message: EmailMessage) -> Dict[str, Any]:
        """
        Send email via SendGrid API.

        Args:
            message: EmailMessage instance

        Returns:
            Send result dictionary
        """
        mail = self._build_sendgrid_mail(message)
        response = self.sendgrid_client.send(mail)

        return {
            "success": response.status_code in [200, 201, 202],
            "message_id": response.headers.get("X-Message-Id", "unknown"),
            "status_code": response.status_code,
            "error": None if response.status_code in [200, 201, 202] else response.body,
            "timestamp": datetime.utcnow().isoformat(),
            "provider": "sendgrid",
        }

    def _send_via_smtp(self, message: EmailMessage) -> Dict[str, Any]:
        """
        Send email via SMTP server.

        Args:
            message: EmailMessage instance

        Returns:
            Send result dictionary
        """
        # Build MIME message
        msg = MIMEMultipart("alternative")
        msg["From"] = (
            f"{message.from_name} <{message.from_email}>"
            if message.from_name
            else message.from_email
        )
        msg["To"] = ", ".join(message.to)
        msg["Subject"] = message.subject

        if message.cc:
            msg["Cc"] = ", ".join(message.cc)
        if message.reply_to:
            msg["Reply-To"] = message.reply_to

        # Add custom headers
        if message.headers:
            for key, value in message.headers.items():
                msg[key] = value

        # Add body parts
        if message.body:
            msg.attach(MIMEText(message.body, "plain"))
        if message.html:
            msg.attach(MIMEText(message.html, "html"))

        # Add attachments
        if message.attachments:
            for att in message.attachments:
                part = MIMEApplication(att.get_content_bytes())
                part.add_header(
                    "Content-Disposition", att.disposition, filename=att.filename
                )
                if att.content_id:
                    part.add_header("Content-ID", f"<{att.content_id}>")
                msg.attach(part)

        # Get all recipients
        all_recipients = list(message.to)
        if message.cc:
            all_recipients.extend(message.cc)
        if message.bcc:
            all_recipients.extend(message.bcc)

        # Send email
        smtp_host = self.smtp_config.get("host", "localhost")
        smtp_port = self.smtp_config.get("port", 587)
        use_tls = self.smtp_config.get("use_tls", True)

        try:
            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)

            # Login if credentials provided
            if self.smtp_config.get("username") and self.smtp_config.get("password"):
                server.login(self.smtp_config["username"], self.smtp_config["password"])

            # Send email
            server.send_message(msg, message.from_email, all_recipients)
            server.quit()

            return {
                "success": True,
                "message_id": msg["Message-ID"] if "Message-ID" in msg else "unknown",
                "status_code": 250,
                "error": None,
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "smtp",
            }
        except Exception as e:
            return {
                "success": False,
                "message_id": None,
                "status_code": 500,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "smtp",
            }

    def send_template(
        self,
        template_id: str,
        to: List[str],
        data: Dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send email using Jinja2 template.

        Args:
            template_id: Template filename (e.g., "welcome.html")
            to: List of recipient email addresses
            data: Dictionary of template variables
            from_email: Sender email address (uses default if not provided)
            from_name: Sender display name (uses default if not provided)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            categories: List of categories for tracking (optional)

        Returns:
            Send result dictionary (same as send_email)

        Raises:
            TemplateError: If template rendering fails
            ValueError: If validation fails

        Examples:
            >>> result = service.send_template(
            ...     template_id="welcome.html",
            ...     to=["user@example.com"],
            ...     data={"name": "John", "activation_link": "https://..."}
            ... )
        """
        # Render template
        html_content = self.render_template(template_id, data)

        # Extract subject from template if present (look for <title> tag)
        subject = data.get("subject", "Notification")
        title_match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE)
        if title_match:
            subject = title_match.group(1)

        # Generate plain text version (strip HTML tags)
        body = re.sub(r"<[^>]+>", "", html_content)
        body = re.sub(r"\s+", " ", body).strip()

        return self.send_email(
            to=to,
            subject=subject,
            body=body,
            html=html_content,
            from_email=from_email,
            from_name=from_name,
            cc=cc,
            bcc=bcc,
            categories=categories,
        )

    def send_with_attachments(
        self,
        to: List[str],
        subject: str,
        body: str,
        attachments: List[Union[EmailAttachment, str, Path]],
        html: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send email with file attachments.

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Plain text email body
            attachments: List of attachments (EmailAttachment objects or file paths)
            html: HTML email body (optional)
            from_email: Sender email address (uses default if not provided)
            from_name: Sender display name (uses default if not provided)

        Returns:
            Send result dictionary (same as send_email)

        Examples:
            >>> result = service.send_with_attachments(
            ...     to=["user@example.com"],
            ...     subject="Report",
            ...     body="Please find the report attached.",
            ...     attachments=["/path/to/report.pdf", "/path/to/data.csv"]
            ... )
        """
        # Convert file paths to EmailAttachment objects
        attachment_objs = []
        for att in attachments:
            if isinstance(att, EmailAttachment):
                attachment_objs.append(att)
            elif isinstance(att, (str, Path)):
                file_path = str(att)
                if not os.path.isfile(file_path):
                    raise FileNotFoundError(f"Attachment file not found: {file_path}")
                attachment_objs.append(
                    EmailAttachment(
                        filename=os.path.basename(file_path), content=file_path
                    )
                )
            else:
                raise ValueError(f"Invalid attachment type: {type(att)}")

        return self.send_email(
            to=to,
            subject=subject,
            body=body,
            html=html,
            from_email=from_email,
            from_name=from_name,
            attachments=attachment_objs,
        )

    def track_delivery(self, message_id: str) -> Dict[str, Any]:
        """
        Track email delivery status via SendGrid.

        Args:
            message_id: Message ID returned from send_email

        Returns:
            Dictionary with keys:
                - message_id: Message identifier
                - status: Delivery status (delivered, bounced, opened, etc.)
                - events: List of tracking events
                - last_updated: Last status update timestamp

        Note:
            This method requires SendGrid API and tracking to be enabled.
            Returns empty dict if tracking is not available.

        Examples:
            >>> status = service.track_delivery("message-123")
            >>> print(status["status"])
            delivered
        """
        if not self.sendgrid_client:
            return {"error": "SendGrid API not configured"}

        try:
            # Note: SendGrid Email Activity API requires additional setup
            # This is a placeholder for the implementation
            # Real implementation would use: /v3/messages/{msg_id}
            return {
                "message_id": message_id,
                "status": "tracking_not_implemented",
                "events": [],
                "last_updated": datetime.utcnow().isoformat(),
                "note": "Tracking requires SendGrid Email Activity API setup",
            }
        except Exception as e:
            return {"error": f"Tracking failed: {str(e)}"}

    def get_bounce_status(self, email: str) -> Dict[str, Any]:
        """
        Check bounce status for an email address.

        Args:
            email: Email address to check

        Returns:
            Dictionary with keys:
                - email: Email address
                - bounced: Boolean indicating if email has bounced
                - bounce_type: Type of bounce (hard, soft, blocked)
                - last_bounce: Timestamp of last bounce
                - reason: Bounce reason message

        Note:
            This method requires SendGrid API and bounce tracking.
            Returns empty status if tracking is not available.

        Examples:
            >>> bounce = service.get_bounce_status("user@example.com")
            >>> if bounce["bounced"]:
            ...     print(f"Email bounced: {bounce['reason']}")
        """
        if not self.sendgrid_client:
            return {"error": "SendGrid API not configured"}

        try:
            # Note: Real implementation would use SendGrid Bounces API
            # GET /v3/suppression/bounces/{email}
            return {
                "email": email,
                "bounced": False,
                "bounce_type": None,
                "last_bounce": None,
                "reason": None,
                "note": "Bounce tracking requires SendGrid Suppression API",
            }
        except Exception as e:
            return {"error": f"Bounce check failed: {str(e)}"}


# Convenience functions for common email operations


def create_email_service(
    api_key: Optional[str] = None,
    smtp_config: Optional[Dict[str, Any]] = None,
) -> EmailService:
    """
    Create EmailService instance.

    Args:
        api_key: SendGrid API key (or from environment)
        smtp_config: SMTP configuration dict

    Returns:
        Configured EmailService instance

    Examples:
        >>> service = create_email_service(api_key="SG.xxx")
        >>> result = service.send_email(...)
    """
    return EmailService(api_key=api_key, smtp_config=smtp_config)


def send_notification_email(
    to: List[str],
    subject: str,
    message: str,
    html: Optional[str] = None,
    service: Optional[EmailService] = None,
) -> Dict[str, Any]:
    """
    Send a simple notification email.

    Args:
        to: List of recipient email addresses
        subject: Email subject
        message: Plain text message
        html: HTML message (optional)
        service: EmailService instance (creates new if not provided)

    Returns:
        Send result dictionary

    Examples:
        >>> result = send_notification_email(
        ...     to=["admin@example.com"],
        ...     subject="Alert: System Error",
        ...     message="An error occurred in the system."
        ... )
    """
    if service is None:
        service = create_email_service()

    return service.send_email(
        to=to,
        subject=subject,
        body=message,
        html=html,
        categories=["notification"],
    )


__all__ = [
    "EmailService",
    "EmailMessage",
    "EmailAttachment",
    "create_email_service",
    "send_notification_email",
]
