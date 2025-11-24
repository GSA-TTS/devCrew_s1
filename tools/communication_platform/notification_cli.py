"""
CLI Interface for Communication & Notification Platform.

Command-line notification management tool providing comprehensive notification
management, template handling, delivery monitoring, and configuration.

Features:
    - Multi-channel notification sending (Slack, Email, Teams, PagerDuty)
    - Template management with versioning
    - Delivery status tracking and monitoring
    - Channel configuration and testing
    - Rate limiting and escalation rules
    - JSON/YAML/Table output formats
    - Progress indicators and colored output

Usage:
    notification-cli send --channel slack --destination "#channel" --message "text"
    notification-cli template list --filter "category=incident"
    notification-cli status --notification-id notif-123
    notification-cli channel test-slack --channel "#test"

Environment Variables:
    DEVCREW_CONFIG: Path to configuration file (~/.devcrew/config.yaml)
    SLACK_BOT_TOKEN: Slack bot token
    SENDGRID_API_KEY: SendGrid API key
    REDIS_URL: Redis connection URL

Author: devCrew_s1
Version: 1.0.0
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml
from tabulate import tabulate

# Type hints for better code quality
JsonDict = Dict[str, Any]
ConfigDict = Dict[str, Any]


# ============================================================================
# Configuration Management
# ============================================================================


class ConfigManager:
    """Manage CLI configuration and environment settings."""

    DEFAULT_CONFIG_PATH = Path.home() / ".devcrew" / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Optional custom configuration file path
        """
        self.config_path = config_path or self.get_config_path()
        self.config = self.load_config()

    @staticmethod
    def get_config_path() -> Path:
        """
        Get configuration file path from environment or default.

        Returns:
            Path to configuration file
        """
        env_path = os.environ.get("DEVCREW_CONFIG")
        if env_path:
            return Path(env_path)
        return ConfigManager.DEFAULT_CONFIG_PATH

    def load_config(self) -> ConfigDict:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary

        Raises:
            click.ClickException: If configuration file cannot be loaded
        """
        if not self.config_path.exists():
            return self.get_default_config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config or self.get_default_config()
        except Exception as e:
            raise click.ClickException(
                f"Failed to load config from {self.config_path}: {e}"
            )

    @staticmethod
    def get_default_config() -> ConfigDict:
        """
        Get default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            "channels": {
                "slack": {"enabled": True, "rate_limit": "50/min"},
                "email": {"enabled": True, "rate_limit": "100/min"},
                "teams": {"enabled": False, "rate_limit": "30/min"},
                "pagerduty": {"enabled": False, "rate_limit": "20/min"},
            },
            "output": {"format": "table", "colors": True},
            "api": {
                "base_url": "http://localhost:8000",
                "timeout": 30,
            },
        }

    def save_config(self) -> None:
        """
        Save current configuration to file.

        Raises:
            click.ClickException: If configuration cannot be saved
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            raise click.ClickException(
                f"Failed to save config to {self.config_path}: {e}"
            )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., 'channels.slack.enabled')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., 'channels.slack.enabled')
            value: Value to set
        """
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value


# ============================================================================
# Output Formatting Utilities
# ============================================================================


class OutputFormatter:
    """Handle output formatting for CLI commands."""

    def __init__(self, config: ConfigManager):
        """
        Initialize output formatter.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.colors_enabled = config.get("output.colors", True)

    def success(self, message: str) -> None:
        """
        Print success message.

        Args:
            message: Message to display
        """
        if self.colors_enabled:
            click.echo(click.style(f"✓ {message}", fg="green", bold=True))
        else:
            click.echo(f"[SUCCESS] {message}")

    def error(self, message: str) -> None:
        """
        Print error message.

        Args:
            message: Message to display
        """
        if self.colors_enabled:
            click.echo(click.style(f"✗ {message}", fg="red", bold=True), err=True)
        else:
            click.echo(f"[ERROR] {message}", err=True)

    def warning(self, message: str) -> None:
        """
        Print warning message.

        Args:
            message: Message to display
        """
        if self.colors_enabled:
            click.echo(click.style(f"⚠ {message}", fg="yellow", bold=True))
        else:
            click.echo(f"[WARNING] {message}")

    def info(self, message: str) -> None:
        """
        Print info message.

        Args:
            message: Message to display
        """
        if self.colors_enabled:
            click.echo(click.style(f"ℹ {message}", fg="blue"))
        else:
            click.echo(f"[INFO] {message}")

    def format_output(
        self,
        data: Any,
        format_type: Optional[str] = None,
        headers: Optional[List[str]] = None,
    ) -> None:
        """
        Format and print output based on configured format.

        Args:
            data: Data to format and display
            format_type: Output format (table, json, yaml), or None for default
            headers: Optional headers for table format
        """
        output_format = format_type or self.config.get("output.format", "table")

        if output_format == "json":
            click.echo(json.dumps(data, indent=2))
        elif output_format == "yaml":
            click.echo(yaml.dump(data, default_flow_style=False))
        elif output_format == "table":
            self._format_table(data, headers)
        else:
            click.echo(str(data))

    def _format_table(self, data: Any, headers: Optional[List[str]] = None) -> None:
        """
        Format data as table.

        Args:
            data: Data to format
            headers: Optional column headers
        """
        if not data:
            self.warning("No data to display")
            return

        if isinstance(data, list):
            if isinstance(data[0], dict):
                # If custom headers not provided, use dict keys
                if headers is None:
                    headers = list(data[0].keys())
                    rows = [[item.get(h, "") for h in headers] for item in data]
                else:
                    # Custom headers provided - use dict keys in order
                    dict_keys = list(data[0].keys())
                    rows = [[item.get(k, "") for k in dict_keys] for item in data]
            else:
                rows = [[item] for item in data]
        elif isinstance(data, dict):
            headers = headers or ["Key", "Value"]
            rows = [[k, v] for k, v in data.items()]
        else:
            rows = [[str(data)]]

        table = tabulate(rows, headers=headers, tablefmt="grid")
        click.echo(table)


# ============================================================================
# API Client Mock (Replace with actual API client)
# ============================================================================


class NotificationAPIClient:
    """Mock API client for notification service."""

    def __init__(self, config: ConfigManager):
        """
        Initialize API client.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.base_url = config.get("api.base_url", "http://localhost:8000")
        self.timeout = config.get("api.timeout", 30)

    def send_notification(
        self,
        channel: str,
        destination: str,
        message: str,
        severity: str = "info",
        **kwargs: Any,
    ) -> JsonDict:
        """
        Send notification via API.

        Args:
            channel: Target channel (slack, email, teams, pagerduty)
            destination: Destination address/channel
            message: Message content
            severity: Notification severity
            **kwargs: Additional parameters

        Returns:
            API response dictionary
        """
        # Mock implementation - replace with actual API call
        return {
            "notification_id": f"notif-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "sent",
            "channel": channel,
            "destination": destination,
            "timestamp": datetime.now().isoformat(),
        }

    def send_template_notification(
        self,
        template: str,
        channels: List[str],
        data: JsonDict,
    ) -> JsonDict:
        """
        Send template-based notification.

        Args:
            template: Template name
            channels: List of channels to send to
            data: Template data

        Returns:
            API response dictionary
        """
        # Mock implementation
        return {
            "notification_id": f"notif-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "sent",
            "template": template,
            "channels": channels,
            "timestamp": datetime.now().isoformat(),
        }

    def get_notification_status(self, notification_id: str) -> JsonDict:
        """
        Get notification delivery status.

        Args:
            notification_id: Notification ID

        Returns:
            Status dictionary
        """
        # Mock implementation
        return {
            "notification_id": notification_id,
            "status": "delivered",
            "sent_at": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "delivered_at": (datetime.now() - timedelta(minutes=4)).isoformat(),
            "channel": "slack",
            "destination": "#general",
            "retries": 0,
        }

    def get_notification_history(
        self, filter_params: Optional[JsonDict] = None, time_range: str = "24h"
    ) -> List[JsonDict]:
        """
        Get notification history.

        Args:
            filter_params: Filter parameters
            time_range: Time range (e.g., '24h', '7d')

        Returns:
            List of notifications
        """
        # Mock implementation
        return [
            {
                "notification_id": f"notif-{i:06d}",
                "status": "delivered",
                "channel": "slack",
                "severity": "info" if i % 3 == 0 else "warning",
                "sent_at": (datetime.now() - timedelta(hours=i)).isoformat(),
            }
            for i in range(1, 11)
        ]

    def get_metrics(self, time_range: str = "24h") -> JsonDict:
        """
        Get notification metrics.

        Args:
            time_range: Time range (e.g., '24h', '7d')

        Returns:
            Metrics dictionary
        """
        # Mock implementation
        return {
            "time_range": time_range,
            "total_sent": 1234,
            "delivered": 1198,
            "failed": 36,
            "pending": 0,
            "delivery_rate": 97.08,
            "avg_delivery_time_ms": 245,
            "by_channel": {
                "slack": {"sent": 678, "delivered": 670, "failed": 8},
                "email": {"sent": 456, "delivered": 445, "failed": 11},
                "teams": {"sent": 100, "delivered": 83, "failed": 17},
            },
        }

    def create_template(self, template_data: JsonDict) -> JsonDict:
        """
        Create notification template.

        Args:
            template_data: Template definition

        Returns:
            Created template
        """
        # Mock implementation
        return {
            "template_id": f"tmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": template_data.get("name"),
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }

    def list_templates(
        self, filter_params: Optional[JsonDict] = None
    ) -> List[JsonDict]:
        """
        List notification templates.

        Args:
            filter_params: Filter parameters

        Returns:
            List of templates
        """
        # Mock implementation
        templates = [
            {
                "template_id": "tmpl-001",
                "name": "deployment_complete",
                "category": "deployment",
                "version": "1.2.0",
                "channels": ["slack", "email"],
                "created_at": "2025-01-15T10:30:00Z",
            },
            {
                "template_id": "tmpl-002",
                "name": "incident_alert",
                "category": "incident",
                "version": "2.0.0",
                "channels": ["slack", "pagerduty"],
                "created_at": "2025-01-10T14:20:00Z",
            },
            {
                "template_id": "tmpl-003",
                "name": "weekly_report",
                "category": "reporting",
                "version": "1.0.0",
                "channels": ["email"],
                "created_at": "2025-01-05T09:15:00Z",
            },
        ]

        if filter_params:
            for key, value in filter_params.items():
                templates = [t for t in templates if t.get(key) == value]

        return templates

    def get_template(self, template_name: str) -> JsonDict:
        """
        Get template details.

        Args:
            template_name: Template name

        Returns:
            Template details
        """
        # Mock implementation
        return {
            "template_id": "tmpl-001",
            "name": template_name,
            "category": "deployment",
            "version": "1.2.0",
            "channels": ["slack", "email"],
            "subject": "Deployment Complete: {{ service_name }}",
            "body": (
                "Service {{ service_name }} deployed "
                "successfully to {{ environment }}"
            ),
            "variables": ["service_name", "environment", "version"],
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-20T15:45:00Z",
        }

    def preview_template(self, template_name: str, data: JsonDict) -> JsonDict:
        """
        Preview template with sample data.

        Args:
            template_name: Template name
            data: Sample data for rendering

        Returns:
            Rendered template preview
        """
        # Mock implementation
        return {
            "template": template_name,
            "rendered": {
                "subject": f"Deployment Complete: {data.get('service_name', 'N/A')}",
                "body": (
                    f"Service {data.get('service_name', 'N/A')} deployed "
                    f"successfully to {data.get('environment', 'N/A')}"
                ),
            },
        }

    def list_channels(self) -> List[JsonDict]:
        """
        List configured channels.

        Returns:
            List of channel configurations
        """
        # Mock implementation
        return [
            {
                "channel": "slack",
                "enabled": True,
                "rate_limit": "50/min",
                "status": "healthy",
            },
            {
                "channel": "email",
                "enabled": True,
                "rate_limit": "100/min",
                "status": "healthy",
            },
            {
                "channel": "teams",
                "enabled": False,
                "rate_limit": "30/min",
                "status": "disabled",
            },
        ]

    def test_channel(self, channel: str, destination: str) -> JsonDict:
        """
        Test channel connectivity.

        Args:
            channel: Channel to test
            destination: Test destination

        Returns:
            Test result
        """
        # Mock implementation
        return {
            "channel": channel,
            "destination": destination,
            "status": "success",
            "latency_ms": 234,
            "message": "Test notification sent successfully",
        }


# ============================================================================
# Main CLI Group
# ============================================================================


@click.group()
@click.version_option(version="1.0.0", prog_name="notification-cli")
@click.option(
    "--config",
    type=click.Path(exists=False, path_type=Path),
    help="Path to configuration file",
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[Path]) -> None:
    """
    Communication & Notification Platform CLI.

    Multi-channel notification management tool for sending notifications,
    managing templates, monitoring delivery, and configuring channels.
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = ConfigManager(config)
    ctx.obj["formatter"] = OutputFormatter(ctx.obj["config"])
    ctx.obj["api"] = NotificationAPIClient(ctx.obj["config"])


# ============================================================================
# Send Command Group
# ============================================================================


@cli.group()
def send() -> None:
    """Send notifications to various channels."""


@send.command(name="message")
@click.option(
    "--channel",
    required=True,
    type=click.Choice(["slack", "email", "teams", "pagerduty"]),
    help="Target channel",
)
@click.option(
    "--destination",
    required=True,
    help="Destination (channel name, email, etc.)",
)
@click.option("--message", required=True, help="Message content")
@click.option(
    "--severity",
    type=click.Choice(["info", "warning", "error", "critical"]),
    default="info",
    help="Message severity",
)
@click.option("--subject", help="Message subject (for email)")
@click.option("--to", help="Email recipient (alias for --destination)")
@click.pass_context
def send_message(
    ctx: click.Context,
    channel: str,
    destination: str,
    message: str,
    severity: str,
    subject: Optional[str],
    to: Optional[str],
) -> None:
    r"""
    Send a direct notification message.

    Examples:
        notification-cli send message --channel slack --destination "#general" \
            --message "Deployment complete" --severity info

        notification-cli send message --channel email --to user@example.com \
            --subject "Alert" --message "System issue detected"
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    # Handle email alias
    if to:
        destination = to

    try:
        with click.progressbar(
            length=1,
            label=f"Sending to {channel}",
            show_eta=False,
        ) as bar:
            result = api.send_notification(
                channel=channel,
                destination=destination,
                message=message,
                severity=severity,
                subject=subject,
            )
            bar.update(1)

        formatter.success(f"Notification sent: {result['notification_id']}")
        formatter.format_output(result)

    except Exception as e:
        formatter.error(f"Failed to send notification: {e}")
        sys.exit(1)


@send.command(name="template")
@click.option("--template", required=True, help="Template name")
@click.option(
    "--channels",
    required=True,
    help="Comma-separated list of channels",
)
@click.option(
    "--data",
    type=click.Path(exists=True, path_type=Path),
    help="JSON file with template data",
)
@click.option("--var", multiple=True, help="Template variable (key=value)")
@click.pass_context
def send_template(
    ctx: click.Context,
    template: str,
    channels: str,
    data: Optional[Path],
    var: Tuple[str, ...],
) -> None:
    r"""
    Send template-based notification.

    Examples:
        notification-cli send template --template deployment_complete \
            --channels slack,email --data data.json

        notification-cli send template --template incident_alert \
            --channels slack,pagerduty --var severity=critical \
            --var service=api
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    # Parse channels
    channel_list = [c.strip() for c in channels.split(",")]

    # Load data from file or parse from variables
    template_data: JsonDict = {}
    if data:
        try:
            with open(data, "r", encoding="utf-8") as f:
                template_data = json.load(f)
        except Exception as e:
            formatter.error(f"Failed to load data file: {e}")
            sys.exit(1)

    # Override with command-line variables
    for v in var:
        if "=" in v:
            key, value = v.split("=", 1)
            template_data[key] = value

    try:
        with click.progressbar(
            length=len(channel_list),
            label="Sending to channels",
            show_eta=False,
        ) as bar:
            result = api.send_template_notification(
                template=template,
                channels=channel_list,
                data=template_data,
            )
            bar.update(len(channel_list))

        formatter.success(f"Template notification sent: {result['notification_id']}")
        formatter.format_output(result)

    except Exception as e:
        formatter.error(f"Failed to send template notification: {e}")
        sys.exit(1)


# ============================================================================
# Template Command Group
# ============================================================================


@cli.group()
def template() -> None:
    """Manage notification templates."""


@template.command(name="list")
@click.option("--filter", help="Filter templates (key=value)")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
@click.pass_context
def list_templates(
    ctx: click.Context,
    filter: Optional[str],
    output_format: Optional[str],
) -> None:
    """
    List all notification templates.

    Examples:
        notification-cli template list
        notification-cli template list --filter category=incident
        notification-cli template list --format json
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    # Parse filter
    filter_params: Optional[JsonDict] = None
    if filter:
        if "=" in filter:
            key, value = filter.split("=", 1)
            filter_params = {key: value}

    try:
        templates = api.list_templates(filter_params)
        formatter.format_output(
            templates,
            format_type=output_format,
            headers=["Template ID", "Name", "Category", "Version", "Channels"],
        )

    except Exception as e:
        formatter.error(f"Failed to list templates: {e}")
        sys.exit(1)


@template.command(name="show")
@click.option("--template", required=True, help="Template name")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
@click.pass_context
def show_template(
    ctx: click.Context,
    template: str,
    output_format: Optional[str],
) -> None:
    """
    Show template details.

    Examples:
        notification-cli template show --template deployment_complete
        notification-cli template show --template incident_alert --format json
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    try:
        template_data = api.get_template(template)
        formatter.format_output(template_data, format_type=output_format)

    except Exception as e:
        formatter.error(f"Failed to get template: {e}")
        sys.exit(1)


@template.command(name="create")
@click.option(
    "--file",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Template definition file (YAML/JSON)",
)
@click.pass_context
def create_template(ctx: click.Context, file: Path) -> None:
    """
    Create a new notification template.

    Examples:
        notification-cli template create --file template.yaml
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    try:
        # Load template file
        with open(file, "r", encoding="utf-8") as f:
            if file.suffix in [".yaml", ".yml"]:
                template_data = yaml.safe_load(f)
            else:
                template_data = json.load(f)

        result = api.create_template(template_data)
        formatter.success(f"Template created: {result['template_id']}")
        formatter.format_output(result)

    except Exception as e:
        formatter.error(f"Failed to create template: {e}")
        sys.exit(1)


@template.command(name="preview")
@click.option("--template", required=True, help="Template name")
@click.option(
    "--data",
    type=click.Path(exists=True, path_type=Path),
    help="JSON file with sample data",
)
@click.option("--var", multiple=True, help="Template variable (key=value)")
@click.pass_context
def preview_template(
    ctx: click.Context,
    template: str,
    data: Optional[Path],
    var: Tuple[str, ...],
) -> None:
    r"""
    Preview template with sample data.

    Examples:
        notification-cli template preview --template deployment_complete \
            --data sample.json

        notification-cli template preview --template incident_alert \
            --var service=api --var severity=critical
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    # Load data
    template_data: JsonDict = {}
    if data:
        try:
            with open(data, "r", encoding="utf-8") as f:
                template_data = json.load(f)
        except Exception as e:
            formatter.error(f"Failed to load data file: {e}")
            sys.exit(1)

    # Override with variables
    for v in var:
        if "=" in v:
            key, value = v.split("=", 1)
            template_data[key] = value

    try:
        preview = api.preview_template(template, template_data)
        formatter.info(f"Preview for template: {template}")
        formatter.format_output(preview)

    except Exception as e:
        formatter.error(f"Failed to preview template: {e}")
        sys.exit(1)


# ============================================================================
# Status Command Group
# ============================================================================


@cli.group()
def status() -> None:
    """Monitor notification delivery status."""


@status.command(name="get")
@click.option(
    "--notification-id",
    required=True,
    help="Notification ID",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
@click.pass_context
def get_status(
    ctx: click.Context,
    notification_id: str,
    output_format: Optional[str],
) -> None:
    """
    Get notification delivery status.

    Examples:
        notification-cli status get --notification-id notif-123
        notification-cli status get --notification-id notif-456 --format json
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    try:
        status_data = api.get_notification_status(notification_id)
        formatter.format_output(status_data, format_type=output_format)

    except Exception as e:
        formatter.error(f"Failed to get status: {e}")
        sys.exit(1)


@status.command(name="history")
@click.option("--filter", help="Filter notifications (key=value)")
@click.option(
    "--last",
    default="24h",
    help="Time range (e.g., 24h, 7d, 30d)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
@click.pass_context
def get_history(
    ctx: click.Context,
    filter: Optional[str],
    last: str,
    output_format: Optional[str],
) -> None:
    """
    Get notification history.

    Examples:
        notification-cli status history --last 24h
        notification-cli status history --filter severity=critical --last 7d
        notification-cli status history --format json
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    # Parse filter
    filter_params: Optional[JsonDict] = None
    if filter:
        if "=" in filter:
            key, value = filter.split("=", 1)
            filter_params = {key: value}

    try:
        history = api.get_notification_history(filter_params, last)
        formatter.format_output(
            history,
            format_type=output_format,
            headers=["Notification ID", "Status", "Channel", "Severity", "Sent At"],
        )

    except Exception as e:
        formatter.error(f"Failed to get history: {e}")
        sys.exit(1)


@status.command(name="metrics")
@click.option(
    "--time-range",
    default="24h",
    help="Time range (e.g., 24h, 7d, 30d)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
@click.pass_context
def get_metrics(
    ctx: click.Context,
    time_range: str,
    output_format: Optional[str],
) -> None:
    """
    Get notification metrics.

    Examples:
        notification-cli status metrics --time-range 24h
        notification-cli status metrics --time-range 7d --format json
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    try:
        metrics = api.get_metrics(time_range)
        formatter.info(f"Metrics for last {time_range}")
        formatter.format_output(metrics, format_type=output_format)

    except Exception as e:
        formatter.error(f"Failed to get metrics: {e}")
        sys.exit(1)


# ============================================================================
# Channel Command Group
# ============================================================================


@cli.group()
def channel() -> None:
    """Manage notification channels."""


@channel.command(name="list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
@click.pass_context
def list_channels(
    ctx: click.Context,
    output_format: Optional[str],
) -> None:
    """
    List configured channels.

    Examples:
        notification-cli channel list
        notification-cli channel list --format json
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    try:
        channels = api.list_channels()
        formatter.format_output(
            channels,
            format_type=output_format,
            headers=["Channel", "Enabled", "Rate Limit", "Status"],
        )

    except Exception as e:
        formatter.error(f"Failed to list channels: {e}")
        sys.exit(1)


@channel.command(name="test-slack")
@click.option("--channel", required=True, help="Slack channel to test")
@click.pass_context
def test_slack(ctx: click.Context, channel: str) -> None:
    """
    Test Slack channel connectivity.

    Examples:
        notification-cli channel test-slack --channel "#test"
    """
    formatter = ctx.obj["formatter"]
    api = ctx.obj["api"]

    try:
        formatter.info(f"Testing Slack channel: {channel}")
        result = api.test_channel("slack", channel)

        if result["status"] == "success":
            formatter.success(
                f"Slack test successful (latency: {result['latency_ms']}ms)"
            )
        else:
            formatter.error("Slack test failed")

        formatter.format_output(result)

    except Exception as e:
        formatter.error(f"Failed to test Slack channel: {e}")
        sys.exit(1)


@channel.command(name="add-slack")
@click.option("--token", required=True, help="Slack bot token")
@click.pass_context
def add_slack(ctx: click.Context, token: str) -> None:
    """
    Configure Slack integration.

    Examples:
        notification-cli channel add-slack --token xoxb-xxx
    """
    formatter = ctx.obj["formatter"]
    config = ctx.obj["config"]

    try:
        # Save to configuration
        config.set("channels.slack.token", token)
        config.set("channels.slack.enabled", True)
        config.save_config()

        formatter.success("Slack integration configured")
        formatter.info("Test with: notification-cli channel test-slack")

    except Exception as e:
        formatter.error(f"Failed to configure Slack: {e}")
        sys.exit(1)


# ============================================================================
# Config Command Group
# ============================================================================


@cli.group()
def config() -> None:
    """Manage CLI configuration."""


@config.command(name="show")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
@click.pass_context
def show_config(
    ctx: click.Context,
    output_format: Optional[str],
) -> None:
    """
    Show current configuration.

    Examples:
        notification-cli config show
        notification-cli config show --format json
    """
    formatter = ctx.obj["formatter"]
    config = ctx.obj["config"]

    formatter.info(f"Configuration file: {config.config_path}")
    formatter.format_output(config.config, format_type=output_format)


@config.command(name="set-rate-limit")
@click.option(
    "--channel",
    required=True,
    type=click.Choice(["slack", "email", "teams", "pagerduty"]),
    help="Channel to configure",
)
@click.option(
    "--limit",
    required=True,
    help="Rate limit (e.g., 50/min, 100/hour)",
)
@click.pass_context
def set_rate_limit(
    ctx: click.Context,
    channel: str,
    limit: str,
) -> None:
    """
    Set channel rate limit.

    Examples:
        notification-cli config set-rate-limit --channel slack --limit 50/min
        notification-cli config set-rate-limit --channel email --limit 100/min
    """
    formatter = ctx.obj["formatter"]
    config = ctx.obj["config"]

    try:
        config.set(f"channels.{channel}.rate_limit", limit)
        config.save_config()

        formatter.success(f"Rate limit set for {channel}: {limit}")

    except Exception as e:
        formatter.error(f"Failed to set rate limit: {e}")
        sys.exit(1)


@config.command(name="show-escalation-rules")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
@click.pass_context
def show_escalation_rules(
    ctx: click.Context,
    output_format: Optional[str],
) -> None:
    """
    Show escalation rules configuration.

    Examples:
        notification-cli config show-escalation-rules
        notification-cli config show-escalation-rules --format json
    """
    formatter = ctx.obj["formatter"]

    # Mock escalation rules
    rules = [
        {
            "rule_id": "rule-001",
            "severity": "critical",
            "initial_channel": "slack",
            "escalate_after": "5m",
            "escalate_to": "pagerduty",
        },
        {
            "rule_id": "rule-002",
            "severity": "warning",
            "initial_channel": "slack",
            "escalate_after": "30m",
            "escalate_to": "email",
        },
    ]

    formatter.format_output(
        rules,
        format_type=output_format,
        headers=["Rule ID", "Severity", "Initial", "After", "Escalate To"],
    )


# ============================================================================
# Main Entry Point
# ============================================================================


def main() -> None:
    """Execute the main CLI entry point."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\nAborted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n\nUnexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
