"""
Budget Manager for Cloud Cost Management.

Provides comprehensive budget tracking, alerting, and forecasting capabilities.
Monitors spending against budgets, detects budget overruns, calculates burn rates,
and sends notifications through multiple channels.

Features:
- Multi-period budget support (daily, weekly, monthly, quarterly, yearly)
- Real-time spend tracking and projections
- Burn rate calculation and forecasting
- Multi-threshold alerting with customizable channels
- Budget status tracking (on track, at risk, over budget)
- Historical budget performance analysis

Protocol Coverage:
- P-FINOPS-COST-MONITOR: Budget monitoring and alerting
- P-OBSERVABILITY: Budget metrics export
"""

import json
import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class BudgetPeriod(str, Enum):
    """Budget time period."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BudgetStatus(str, Enum):
    """Budget status indicator."""

    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    OVER_BUDGET = "over_budget"
    APPROACHING_LIMIT = "approaching_limit"


class NotificationChannel(str, Enum):
    """Notification channel type."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


class BudgetConfig(BaseModel):
    """Budget configuration."""

    name: str = Field(description="Budget name")
    amount: float = Field(description="Budget amount in USD", gt=0)
    period: BudgetPeriod = Field(description="Budget period")
    alert_thresholds: List[float] = Field(
        default=[0.5, 0.8, 0.9, 1.0],
        description="Alert thresholds as percentages (0.0-1.0)",
    )
    notification_channels: List[str] = Field(
        default_factory=list, description="Notification channel identifiers"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Cost filters (provider, service, tags)"
    )
    start_date: Optional[datetime] = Field(
        default=None, description="Budget start date (defaults to period start)"
    )
    auto_adjust: bool = Field(
        default=False, description="Auto-adjust budget based on historical trends"
    )
    notification_cooldown: int = Field(
        default=3600, description="Cooldown between alerts in seconds", ge=60
    )

    @field_validator("alert_thresholds")
    @classmethod
    def validate_thresholds(cls, v: List[float]) -> List[float]:
        """Validate alert thresholds."""
        if not v:
            raise ValueError("At least one alert threshold required")
        for threshold in v:
            if not 0 < threshold <= 1.5:
                raise ValueError(f"Threshold {threshold} must be between 0 and 1.5")
        # Sort thresholds
        return sorted(set(v))


class Budget(BaseModel):
    """Budget with current status."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    config: BudgetConfig = Field(description="Budget configuration")
    current_spend: float = Field(default=0.0, description="Current spend", ge=0)
    projected_spend: float = Field(
        default=0.0, description="Projected spend for period", ge=0
    )
    burn_rate: float = Field(default=0.0, description="Spend rate per day", ge=0)
    days_remaining: int = Field(default=0, description="Days remaining in period", ge=0)
    status: BudgetStatus = Field(
        default=BudgetStatus.ON_TRACK, description="Budget status"
    )
    alerts_sent: List[float] = Field(
        default_factory=list, description="Thresholds that have triggered alerts"
    )
    last_alert_time: Optional[datetime] = Field(
        default=None, description="Last alert timestamp"
    )
    period_start: datetime = Field(
        default_factory=datetime.utcnow, description="Current period start"
    )
    period_end: datetime = Field(
        default_factory=datetime.utcnow, description="Current period end"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Budget creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update time"
    )

    def get_percentage_used(self) -> float:
        """Get percentage of budget used."""
        if self.config.amount == 0:
            return 0.0
        return (self.current_spend / self.config.amount) * 100

    def get_percentage_projected(self) -> float:
        """Get projected percentage of budget."""
        if self.config.amount == 0:
            return 0.0
        return (self.projected_spend / self.config.amount) * 100

    def get_remaining_budget(self) -> float:
        """Get remaining budget amount."""
        return max(0.0, self.config.amount - self.current_spend)

    def should_alert(self, threshold: float) -> bool:
        """Check if alert should be sent for threshold."""
        percentage = self.current_spend / self.config.amount
        return percentage >= threshold and threshold not in self.alerts_sent


class BudgetAlert(BaseModel):
    """Budget alert notification."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    budget_id: str = Field(description="Budget ID")
    budget_name: str = Field(description="Budget name")
    threshold: float = Field(description="Alert threshold percentage")
    current_spend: float = Field(description="Current spend amount", ge=0)
    budget_amount: float = Field(description="Total budget amount", gt=0)
    projected_spend: float = Field(default=0.0, description="Projected spend", ge=0)
    burn_rate: float = Field(default=0.0, description="Daily burn rate", ge=0)
    days_remaining: int = Field(default=0, description="Days left in period", ge=0)
    status: BudgetStatus = Field(description="Budget status")
    message: str = Field(description="Alert message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Alert timestamp"
    )
    severity: str = Field(default="info", description="Alert severity")

    def get_percentage_used(self) -> float:
        """Get percentage of budget used."""
        if self.budget_amount == 0:
            return 0.0
        return (self.current_spend / self.budget_amount) * 100

    def format_message(self) -> str:
        """Format alert message for notifications."""
        pct = self.get_percentage_used()
        msg = [
            f"Budget Alert: {self.budget_name}",
            f"Status: {self.status.value.upper()}",
            f"Current Spend: ${self.current_spend:,.2f} ({pct:.1f}%)",
            f"Budget: ${self.budget_amount:,.2f}",
        ]

        if self.projected_spend > 0:
            proj_pct = (self.projected_spend / self.budget_amount) * 100
            msg.append(f"Projected: ${self.projected_spend:,.2f} ({proj_pct:.1f}%)")

        if self.burn_rate > 0:
            msg.append(f"Burn Rate: ${self.burn_rate:,.2f}/day")

        if self.days_remaining > 0:
            msg.append(f"Days Remaining: {self.days_remaining}")

        msg.append(f"\n{self.message}")
        return "\n".join(msg)


class BudgetHistory(BaseModel):
    """Historical budget performance."""

    budget_id: str = Field(description="Budget ID")
    period_start: datetime = Field(description="Period start")
    period_end: datetime = Field(description="Period end")
    budgeted_amount: float = Field(description="Budgeted amount", gt=0)
    actual_spend: float = Field(description="Actual spend", ge=0)
    variance: float = Field(description="Variance (actual - budgeted)")
    variance_percentage: float = Field(description="Variance as percentage")
    alerts_triggered: int = Field(default=0, description="Number of alerts", ge=0)
    peak_burn_rate: float = Field(default=0.0, description="Peak burn rate", ge=0)
    avg_burn_rate: float = Field(default=0.0, description="Average burn rate", ge=0)


class BudgetManager:
    """
    Budget Manager for cloud cost tracking and alerting.

    Provides comprehensive budget management including creation, tracking,
    alerting, and historical analysis. Monitors spending against budgets,
    calculates burn rates, projects future spending, and sends alerts through
    multiple notification channels.
    """

    def __init__(
        self, cost_aggregator: Any, storage_path: Optional[Path] = None
    ) -> None:
        """
        Initialize Budget Manager.

        Args:
            cost_aggregator: Cost aggregator for retrieving spend data
            storage_path: Path for budget persistence
        """
        self.cost_aggregator = cost_aggregator
        self.storage_path = storage_path or Path("budgets.json")
        self.budgets: Dict[str, Budget] = {}
        self.history: List[BudgetHistory] = []
        self._load_budgets()
        logger.info("Initialized BudgetManager")

    def create_budget(self, config: BudgetConfig) -> Budget:
        """
        Create a new budget.

        Args:
            config: Budget configuration

        Returns:
            Created budget

        Raises:
            ValueError: If budget with same name exists
        """
        # Check for duplicate name
        if any(b.config.name == config.name for b in self.budgets.values()):
            raise ValueError(f"Budget with name '{config.name}' already exists")

        # Calculate period dates
        period_start, period_end = self._calculate_period_dates(
            config.period, config.start_date
        )

        # Create budget
        budget = Budget(
            config=config,
            period_start=period_start,
            period_end=period_end,
            days_remaining=self._calculate_days_remaining(period_end),
        )

        # Initialize current spend
        self._update_budget_spend(budget)

        # Store budget
        self.budgets[budget.id] = budget
        self._save_budgets()

        logger.info(
            f"Created budget '{config.name}' (${config.amount:,.2f} "
            f"{config.period.value})"
        )
        return budget

    def list_budgets(self, status: Optional[BudgetStatus] = None) -> List[Budget]:
        """
        List all budgets, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of budgets
        """
        budgets = list(self.budgets.values())
        if status:
            budgets = [b for b in budgets if b.status == status]
        return sorted(budgets, key=lambda b: b.config.name)

    def get_budget(self, budget_id: str) -> Optional[Budget]:
        """
        Get budget by ID.

        Args:
            budget_id: Budget ID

        Returns:
            Budget if found, None otherwise
        """
        budget = self.budgets.get(budget_id)
        if budget:
            self._update_budget_spend(budget)
        return budget

    def update_budget(self, budget: Budget) -> Budget:
        """
        Update existing budget.

        Args:
            budget: Updated budget

        Returns:
            Updated budget

        Raises:
            ValueError: If budget not found
        """
        if budget.id not in self.budgets:
            raise ValueError(f"Budget '{budget.id}' not found")

        budget.updated_at = datetime.utcnow()
        self.budgets[budget.id] = budget
        self._save_budgets()

        logger.info(f"Updated budget '{budget.config.name}'")
        return budget

    def delete_budget(self, budget_id: str) -> bool:
        """
        Delete budget.

        Args:
            budget_id: Budget ID to delete

        Returns:
            True if deleted, False if not found
        """
        if budget_id in self.budgets:
            name = self.budgets[budget_id].config.name
            del self.budgets[budget_id]
            self._save_budgets()
            logger.info(f"Deleted budget '{name}'")
            return True
        return False

    def check_budgets(self) -> List[BudgetAlert]:
        """
        Check all budgets and generate alerts.

        Returns:
            List of alerts that should be sent

        Raises:
            Exception: On cost retrieval failure
        """
        alerts: List[BudgetAlert] = []

        for budget in self.budgets.values():
            # Update spend data
            self._update_budget_spend(budget)

            # Check if period has rolled over
            if datetime.utcnow() > budget.period_end:
                self._roll_over_budget(budget)
                continue

            # Check each threshold
            for threshold in budget.config.alert_thresholds:
                if budget.should_alert(threshold):
                    # Check cooldown
                    if self._is_in_cooldown(budget):
                        logger.debug(
                            f"Budget '{budget.config.name}' in cooldown, "
                            f"skipping alert"
                        )
                        continue

                    # Generate alert
                    alert = self._create_alert(budget, threshold)
                    alerts.append(alert)

                    # Mark threshold as alerted
                    budget.alerts_sent.append(threshold)
                    budget.last_alert_time = datetime.utcnow()

            # Update budget
            self.update_budget(budget)

        logger.info(f"Generated {len(alerts)} budget alerts")
        return alerts

    def send_alert(self, alert: BudgetAlert) -> bool:
        """
        Send alert through configured channels.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully

        Raises:
            Exception: On send failure
        """
        budget = self.budgets.get(alert.budget_id)
        if not budget:
            logger.error(f"Budget '{alert.budget_id}' not found for alert")
            return False

        success = True
        channels = budget.config.notification_channels

        # Default to log if no channels configured
        if not channels:
            channels = ["log"]

        for channel in channels:
            try:
                if channel == "log" or channel == NotificationChannel.LOG.value:
                    self._send_log_alert(alert)
                elif channel.startswith("email:"):
                    email = channel.split(":", 1)[1]
                    self._send_email_alert(alert, email)
                elif channel.startswith("slack:"):
                    webhook_url = channel.split(":", 1)[1]
                    self._send_slack_alert(alert, webhook_url)
                elif channel.startswith("webhook:"):
                    webhook_url = channel.split(":", 1)[1]
                    self._send_webhook_alert(alert, webhook_url)
                else:
                    logger.warning(f"Unknown notification channel: {channel}")

            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
                success = False

        return success

    def get_budget_summary(self) -> Dict[str, Any]:
        """
        Get summary of all budgets.

        Returns:
            Summary statistics
        """
        budgets = list(self.budgets.values())
        if not budgets:
            return {
                "total_budgets": 0,
                "total_allocated": 0.0,
                "total_spent": 0.0,
                "total_remaining": 0.0,
            }

        # Update all budgets
        for budget in budgets:
            self._update_budget_spend(budget)

        total_allocated = sum(b.config.amount for b in budgets)
        total_spent = sum(b.current_spend for b in budgets)
        total_remaining = sum(b.get_remaining_budget() for b in budgets)

        status_counts = {}
        for status in BudgetStatus:
            count = sum(1 for b in budgets if b.status == status)
            if count > 0:
                status_counts[status.value] = count

        return {
            "total_budgets": len(budgets),
            "total_allocated": total_allocated,
            "total_spent": total_spent,
            "total_remaining": total_remaining,
            "utilization_percentage": (
                (total_spent / total_allocated * 100) if total_allocated > 0 else 0
            ),
            "status_breakdown": status_counts,
            "at_risk_count": status_counts.get("at_risk", 0),
            "over_budget_count": status_counts.get("over_budget", 0),
        }

    def get_budget_history(
        self, budget_id: str, limit: int = 10
    ) -> List[BudgetHistory]:
        """
        Get historical performance for a budget.

        Args:
            budget_id: Budget ID
            limit: Maximum number of history records

        Returns:
            List of historical records
        """
        history = [h for h in self.history if h.budget_id == budget_id]
        return sorted(history, key=lambda h: h.period_end, reverse=True)[:limit]

    def _update_budget_spend(self, budget: Budget) -> None:
        """Update budget with current spend data."""
        try:
            # Get costs for current period
            costs = self.cost_aggregator.get_costs(
                start_date=budget.period_start.date().isoformat(),
                end_date=datetime.utcnow().date().isoformat(),
                filters=budget.config.filters,
            )

            # Calculate current spend
            budget.current_spend = sum(c.cost for c in costs)

            # Calculate burn rate (spend per day)
            days_elapsed = (datetime.utcnow() - budget.period_start).days
            if days_elapsed > 0:
                budget.burn_rate = budget.current_spend / days_elapsed
            else:
                budget.burn_rate = 0.0

            # Calculate days remaining
            budget.days_remaining = self._calculate_days_remaining(budget.period_end)

            # Project spend for remaining period
            if budget.days_remaining > 0 and budget.burn_rate > 0:
                projected_additional = budget.burn_rate * budget.days_remaining
                budget.projected_spend = budget.current_spend + projected_additional
            else:
                budget.projected_spend = budget.current_spend

            # Update status
            budget.status = self._calculate_budget_status(budget)
            budget.updated_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Failed to update budget spend: {e}")
            raise

    def _calculate_budget_status(self, budget: Budget) -> BudgetStatus:
        """Calculate budget status based on spend and projections."""
        pct_used = budget.current_spend / budget.config.amount
        pct_projected = budget.projected_spend / budget.config.amount

        if pct_used >= 1.0:
            return BudgetStatus.OVER_BUDGET
        elif pct_projected >= 1.0 or pct_used >= 0.9:
            return BudgetStatus.AT_RISK
        elif pct_used >= 0.8:
            return BudgetStatus.APPROACHING_LIMIT
        else:
            return BudgetStatus.ON_TRACK

    def _create_alert(self, budget: Budget, threshold: float) -> BudgetAlert:
        """Create alert for budget threshold."""
        pct_used = budget.get_percentage_used()

        # Generate message based on status
        if budget.status == BudgetStatus.OVER_BUDGET:
            message = (
                f"Budget exceeded! Current spend is "
                f"${budget.current_spend:,.2f} ({pct_used:.1f}%), "
                f"which is over the ${budget.config.amount:,.2f} budget."
            )
            severity = "critical"
        elif budget.status == BudgetStatus.AT_RISK:
            message = (
                f"Budget at risk! Projected spend "
                f"${budget.projected_spend:,.2f} will exceed budget. "
                f"Current: ${budget.current_spend:,.2f} ({pct_used:.1f}%)"
            )
            severity = "warning"
        else:
            message = (
                f"Budget alert: {threshold:.0%} threshold reached. "
                f"Current spend: ${budget.current_spend:,.2f} ({pct_used:.1f}%)"
            )
            severity = "info"

        return BudgetAlert(
            budget_id=budget.id,
            budget_name=budget.config.name,
            threshold=threshold,
            current_spend=budget.current_spend,
            budget_amount=budget.config.amount,
            projected_spend=budget.projected_spend,
            burn_rate=budget.burn_rate,
            days_remaining=budget.days_remaining,
            status=budget.status,
            message=message,
            severity=severity,
        )

    def _is_in_cooldown(self, budget: Budget) -> bool:
        """Check if budget is in alert cooldown period."""
        if not budget.last_alert_time:
            return False

        cooldown = timedelta(seconds=budget.config.notification_cooldown)
        return datetime.utcnow() - budget.last_alert_time < cooldown

    def _roll_over_budget(self, budget: Budget) -> None:
        """Roll over budget to next period."""
        # Save history
        history = BudgetHistory(
            budget_id=budget.id,
            period_start=budget.period_start,
            period_end=budget.period_end,
            budgeted_amount=budget.config.amount,
            actual_spend=budget.current_spend,
            variance=budget.current_spend - budget.config.amount,
            variance_percentage=(
                (budget.current_spend - budget.config.amount)
                / budget.config.amount
                * 100
            ),
            alerts_triggered=len(budget.alerts_sent),
            peak_burn_rate=budget.burn_rate,
            avg_burn_rate=budget.burn_rate,
        )
        self.history.append(history)

        # Reset for new period
        budget.period_start, budget.period_end = self._calculate_period_dates(
            budget.config.period
        )
        budget.current_spend = 0.0
        budget.projected_spend = 0.0
        budget.burn_rate = 0.0
        budget.alerts_sent = []
        budget.last_alert_time = None
        budget.days_remaining = self._calculate_days_remaining(budget.period_end)

        logger.info(f"Rolled over budget '{budget.config.name}' to new period")

    @staticmethod
    def _calculate_period_dates(
        period: BudgetPeriod, start_date: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
        """Calculate period start and end dates."""
        now = start_date or datetime.utcnow()

        if period == BudgetPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == BudgetPeriod.WEEKLY:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        elif period == BudgetPeriod.MONTHLY:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1)
            else:
                end = start.replace(month=now.month + 1)
        elif period == BudgetPeriod.QUARTERLY:
            quarter = (now.month - 1) // 3
            start = now.replace(
                month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end_month = start.month + 3
            if end_month > 12:
                end = start.replace(year=start.year + 1, month=end_month - 12)
            else:
                end = start.replace(month=end_month)
        elif period == BudgetPeriod.YEARLY:
            start = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end = start.replace(year=now.year + 1)
        else:
            raise ValueError(f"Invalid period: {period}")

        return start, end

    @staticmethod
    def _calculate_days_remaining(end_date: datetime) -> int:
        """Calculate days remaining in period."""
        delta = end_date - datetime.utcnow()
        return max(0, delta.days)

    def _send_log_alert(self, alert: BudgetAlert) -> None:
        """Send alert to log."""
        logger.warning(f"BUDGET ALERT: {alert.format_message()}")

    def _send_email_alert(self, alert: BudgetAlert, email: str) -> None:
        """Send alert via email."""
        # Get SMTP configuration from environment
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM", "budgets@finops.local")

        # Create message
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = email
        msg["Subject"] = f"Budget Alert: {alert.budget_name}"

        body = alert.format_message()
        msg.attach(MIMEText(body, "plain"))

        # Send email
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            logger.info(f"Sent email alert to {email}")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            raise

    def _send_slack_alert(self, alert: BudgetAlert, webhook_url: str) -> None:
        """Send alert to Slack."""
        import requests

        color = {
            "critical": "#FF0000",
            "warning": "#FFA500",
            "info": "#0000FF",
        }.get(alert.severity, "#808080")

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"Budget Alert: {alert.budget_name}",
                    "text": alert.format_message(),
                    "footer": "FinOps Budget Manager",
                    "ts": int(alert.timestamp.timestamp()),
                }
            ]
        }

        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Sent Slack alert for budget '{alert.budget_name}'")

    def _send_webhook_alert(self, alert: BudgetAlert, webhook_url: str) -> None:
        """Send alert to generic webhook."""
        import requests

        payload = {
            "alert_id": alert.id,
            "budget_id": alert.budget_id,
            "budget_name": alert.budget_name,
            "threshold": alert.threshold,
            "current_spend": alert.current_spend,
            "budget_amount": alert.budget_amount,
            "status": alert.status.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "severity": alert.severity,
        }

        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Sent webhook alert for budget '{alert.budget_name}'")

    def _save_budgets(self) -> None:
        """Save budgets to storage."""
        try:
            data = {
                "budgets": {
                    budget_id: budget.model_dump(mode="json")
                    for budget_id, budget in self.budgets.items()
                },
                "history": [h.model_dump(mode="json") for h in self.history],
            }

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug(f"Saved {len(self.budgets)} budgets to {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to save budgets: {e}")

    def _load_budgets(self) -> None:
        """Load budgets from storage."""
        if not self.storage_path.exists():
            logger.info("No existing budgets found")
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

            # Load budgets
            for budget_id, budget_data in data.get("budgets", {}).items():
                budget = Budget(**budget_data)
                self.budgets[budget_id] = budget

            # Load history
            for history_data in data.get("history", []):
                history = BudgetHistory(**history_data)
                self.history.append(history)

            logger.info(f"Loaded {len(self.budgets)} budgets from {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to load budgets: {e}")
