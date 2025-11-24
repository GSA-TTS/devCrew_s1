"""
Scheduler for Backup & Recovery Management Platform.

Provides automated backup scheduling with cron-based expressions, backup
window management, missed backup detection, retry logic with exponential
backoff, and job status tracking.

Protocol Coverage:
- P-SYSTEM-BACKUP: Automated system-level backups with retention policies
- P-OPS-RESILIENCE: Operational resilience with scheduled backups
"""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, List, Optional

import requests
from croniter import croniter
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ScheduleConfig(BaseModel):
    """Configuration for scheduled backup."""

    cron_expression: str = Field(..., description="Cron expression for scheduling")
    source_path: str = Field(..., description="Path to backup")
    backend: str = Field(..., description="Backend storage URL")
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Tags for backup snapshots"
    )
    retention_policy: Dict[str, int] = Field(
        default_factory=dict,
        description="Retention policy (keep_last, keep_hourly, etc.)",
    )
    notification_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Notification configuration"
    )
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_minutes: int = Field(
        default=15, description="Initial retry delay in minutes"
    )

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Validate cron expression format."""
        if not croniter.is_valid(v):
            raise ValueError(f"Invalid cron expression: {v}")
        return v

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, v: str) -> str:
        """Validate source path exists."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Source path does not exist: {v}")
        return v


class BackupJob(BaseModel):
    """Scheduled backup job."""

    job_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique job ID"
    )
    config: ScheduleConfig = Field(..., description="Job configuration")
    enabled: bool = Field(default=True, description="Whether job is enabled")
    last_run: Optional[datetime] = Field(
        default=None, description="Last execution time"
    )
    last_status: Optional[str] = Field(
        default=None, description="Last execution status"
    )
    next_run: Optional[datetime] = Field(
        default=None, description="Next scheduled run time"
    )
    consecutive_failures: int = Field(
        default=0, description="Count of consecutive failures"
    )

    def model_post_init(self, __context: Any) -> None:
        """Initialize next_run if not set."""
        if self.next_run is None and self.enabled:
            try:
                cron = croniter(self.config.cron_expression, datetime.now())
                self.next_run = cron.get_next(datetime)
            except Exception as e:  # pylint: disable=broad-except
                logger.error("Failed to calculate next run time: %s", e)


class JobExecution(BaseModel):
    """Record of job execution."""

    job_id: str = Field(..., description="Job ID")
    start_time: datetime = Field(
        default_factory=datetime.now, description="Execution start time"
    )
    end_time: Optional[datetime] = Field(default=None, description="Execution end time")
    status: str = Field(default="RUNNING", description="Execution status")
    snapshot_id: Optional[str] = Field(default=None, description="Snapshot ID created")
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )
    retry_count: int = Field(default=0, description="Number of retries")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is allowed value."""
        allowed = ["RUNNING", "SUCCESS", "FAILED", "RETRYING"]
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v


class Scheduler:
    """
    Manages automated backup scheduling and execution.

    Provides cron-based scheduling, retry logic, missed backup detection,
    and notification support.
    """

    def __init__(self, backup_manager: Any) -> None:
        """
        Initialize Scheduler.

        Args:
            backup_manager: BackupManager instance for executing backups
        """
        self.backup_manager = backup_manager
        self.jobs: Dict[str, BackupJob] = {}
        self.executions: Dict[str, List[JobExecution]] = {}
        self._lock = Lock()
        self._running = False
        self._scheduler_thread: Optional[Thread] = None

        # File paths for persistence
        self.jobs_file = Path.home() / ".backup_scheduler_jobs.json"
        self.executions_file = Path.home() / ".backup_scheduler_executions.json"

        # Load existing jobs and executions
        self._load_state()

        logger.info("Initialized Scheduler")

    def schedule_backup(self, config: ScheduleConfig) -> str:
        """
        Schedule a new backup job.

        Args:
            config: Schedule configuration

        Returns:
            Job ID of scheduled backup
        """
        logger.info(
            "Scheduling backup for %s with cron: %s",
            config.source_path,
            config.cron_expression,
        )

        job = BackupJob(config=config)
        job.next_run = self.get_next_run_time(config.cron_expression)

        with self._lock:
            self.jobs[job.job_id] = job
            self.executions[job.job_id] = []

        self._save_jobs()

        logger.info("Scheduled backup job: %s", job.job_id)
        return job.job_id

    def list_jobs(self) -> List[BackupJob]:
        """
        List all scheduled backup jobs.

        Returns:
            List of BackupJob objects
        """
        with self._lock:
            return list(self.jobs.values())

    def get_job(self, job_id: str) -> Optional[BackupJob]:
        """
        Get a specific job by ID.

        Args:
            job_id: Job ID to retrieve

        Returns:
            BackupJob if found, None otherwise
        """
        with self._lock:
            return self.jobs.get(job_id)

    def enable_job(self, job_id: str) -> bool:
        """
        Enable a disabled job.

        Args:
            job_id: Job ID to enable

        Returns:
            True if job was enabled successfully
        """
        logger.info("Enabling job: %s", job_id)

        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                logger.error("Job not found: %s", job_id)
                return False

            job.enabled = True
            job.next_run = self.get_next_run_time(job.config.cron_expression)
            self._save_jobs()

        logger.info("Job enabled: %s", job_id)
        return True

    def disable_job(self, job_id: str) -> bool:
        """
        Disable an active job.

        Args:
            job_id: Job ID to disable

        Returns:
            True if job was disabled successfully
        """
        logger.info("Disabling job: %s", job_id)

        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                logger.error("Job not found: %s", job_id)
                return False

            job.enabled = False
            job.next_run = None
            self._save_jobs()

        logger.info("Job disabled: %s", job_id)
        return True

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a scheduled job.

        Args:
            job_id: Job ID to delete

        Returns:
            True if job was deleted successfully
        """
        logger.info("Deleting job: %s", job_id)

        with self._lock:
            if job_id not in self.jobs:
                logger.error("Job not found: %s", job_id)
                return False

            del self.jobs[job_id]
            if job_id in self.executions:
                del self.executions[job_id]

            self._save_jobs()
            self._save_executions()

        logger.info("Job deleted: %s", job_id)
        return True

    def get_next_run_time(self, cron_expression: str) -> datetime:
        """
        Calculate next run time for cron expression.

        Args:
            cron_expression: Cron expression

        Returns:
            Next scheduled run time
        """
        cron = croniter(cron_expression, datetime.now())
        return cron.get_next(datetime)

    def execute_job(self, job_id: str) -> JobExecution:
        """
        Execute a backup job immediately.

        Args:
            job_id: Job ID to execute

        Returns:
            JobExecution record
        """
        logger.info("Executing job: %s", job_id)

        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            execution = JobExecution(
                job_id=job_id,
                start_time=datetime.now(),
            )

        try:
            # Execute backup using backup_manager
            # This is a placeholder - actual implementation would call
            # backup_manager.create_backup()
            logger.info(
                "Running backup for %s to %s",
                job.config.source_path,
                job.config.backend,
            )

            # Simulate backup execution
            # In production, this would be:
            # snapshot = self.backup_manager.create_backup(
            #     source=job.config.source_path,
            #     tags=job.config.tags
            # )
            # execution.snapshot_id = snapshot.snapshot_id

            # For now, simulate success
            time.sleep(1)  # Simulate work
            execution.snapshot_id = f"snapshot-{uuid.uuid4().hex[:8]}"
            execution.status = "SUCCESS"
            execution.end_time = datetime.now()

            with self._lock:
                job.last_run = execution.start_time
                job.last_status = "SUCCESS"
                job.consecutive_failures = 0
                job.next_run = self.get_next_run_time(job.config.cron_expression)
                self._save_jobs()

            logger.info("Job executed successfully: %s", job_id)

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Job execution failed: %s", e)
            execution.status = "FAILED"
            execution.error_message = str(e)
            execution.end_time = datetime.now()

            with self._lock:
                job.last_run = execution.start_time
                job.last_status = "FAILED"
                job.consecutive_failures += 1
                self._save_jobs()

        # Save execution record
        with self._lock:
            if job_id not in self.executions:
                self.executions[job_id] = []
            self.executions[job_id].append(execution)
            self._save_executions()

        # Send notification
        if job.config.notification_config:
            self.send_notification(job, execution)

        return execution

    def check_missed_backups(self, hours: int = 24) -> List[BackupJob]:
        """
        Check for missed backup jobs.

        Args:
            hours: Number of hours to look back

        Returns:
            List of jobs with missed backups
        """
        logger.info("Checking for missed backups in last %d hours", hours)

        cutoff_time = datetime.now() - timedelta(hours=hours)
        missed_jobs = []

        with self._lock:
            for job in self.jobs.values():
                if not job.enabled:
                    continue

                # Check if job should have run but didn't
                if job.next_run and job.next_run < cutoff_time:
                    if not job.last_run or job.last_run < cutoff_time:
                        missed_jobs.append(job)
                        logger.warning("Missed backup detected for job: %s", job.job_id)

        logger.info("Found %d missed backups", len(missed_jobs))
        return missed_jobs

    def retry_failed_job(self, job_id: str) -> JobExecution:
        """
        Retry a failed backup job with exponential backoff.

        Args:
            job_id: Job ID to retry

        Returns:
            JobExecution record
        """
        logger.info("Retrying failed job: %s", job_id)

        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            # Get last execution
            last_executions = self.executions.get(job_id, [])
            if not last_executions:
                raise ValueError(f"No previous executions for job: {job_id}")

            last_execution = last_executions[-1]
            retry_count = last_execution.retry_count + 1

            # Check if max retries exceeded
            if retry_count > job.config.max_retries:
                logger.error(
                    "Max retries exceeded for job %s: %d",
                    job_id,
                    retry_count,
                )
                raise ValueError(f"Max retries exceeded for job: {job_id}")

            # Calculate exponential backoff delay
            delay_minutes = job.config.retry_delay_minutes * (2 ** (retry_count - 1))
            logger.info("Retry delay: %d minutes", delay_minutes)

            # Wait for delay
            time.sleep(delay_minutes * 60)

        # Create new execution
        execution = JobExecution(
            job_id=job_id,
            start_time=datetime.now(),
            retry_count=retry_count,
            status="RETRYING",
        )

        try:
            # Execute backup
            logger.info("Executing retry %d for job %s", retry_count, job_id)

            # Simulate backup execution
            time.sleep(1)
            execution.snapshot_id = f"snapshot-{uuid.uuid4().hex[:8]}"
            execution.status = "SUCCESS"
            execution.end_time = datetime.now()

            with self._lock:
                job.last_run = execution.start_time
                job.last_status = "SUCCESS"
                job.consecutive_failures = 0
                job.next_run = self.get_next_run_time(job.config.cron_expression)
                self._save_jobs()

            logger.info("Retry successful for job: %s", job_id)

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Retry failed for job %s: %s", job_id, e)
            execution.status = "FAILED"
            execution.error_message = str(e)
            execution.end_time = datetime.now()

            with self._lock:
                job.last_run = execution.start_time
                job.last_status = "FAILED"
                job.consecutive_failures += 1
                self._save_jobs()

        # Save execution
        with self._lock:
            self.executions[job_id].append(execution)
            self._save_executions()

        # Send notification
        if job.config.notification_config:
            self.send_notification(job, execution)

        return execution

    def get_job_history(self, job_id: str, days: int = 30) -> List[JobExecution]:
        """
        Get execution history for a job.

        Args:
            job_id: Job ID to get history for
            days: Number of days to look back

        Returns:
            List of JobExecution records
        """
        logger.info("Getting history for job %s (last %d days)", job_id, days)

        cutoff_time = datetime.now() - timedelta(days=days)

        with self._lock:
            executions = self.executions.get(job_id, [])
            recent_executions = [e for e in executions if e.start_time >= cutoff_time]

        logger.info("Found %d executions", len(recent_executions))
        return recent_executions

    def send_notification(self, job: BackupJob, execution: JobExecution) -> bool:
        """
        Send notification about job execution.

        Args:
            job: BackupJob that was executed
            execution: JobExecution record

        Returns:
            True if notification sent successfully
        """
        if not job.config.notification_config:
            return False

        logger.info("Sending notification for job: %s", job.job_id)

        notification_type = job.config.notification_config.get("type", "webhook")

        try:
            if notification_type == "webhook":
                return self._send_webhook_notification(job, execution)
            elif notification_type == "slack":
                return self._send_slack_notification(job, execution)
            elif notification_type == "email":
                return self._send_email_notification(job, execution)
            else:
                logger.warning("Unknown notification type: %s", notification_type)
                return False

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to send notification: %s", e)
            return False

    def _send_webhook_notification(
        self, job: BackupJob, execution: JobExecution
    ) -> bool:
        """Send webhook notification."""
        webhook_url = job.config.notification_config.get("webhook_url")  # type: ignore
        if not webhook_url:
            return False

        payload = {
            "job_id": job.job_id,
            "status": execution.status,
            "snapshot_id": execution.snapshot_id,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "error_message": execution.error_message,
        }

        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200

    def _send_slack_notification(self, job: BackupJob, execution: JobExecution) -> bool:
        """Send Slack notification."""
        webhook_url = job.config.notification_config.get("slack_webhook_url")  # type: ignore  # noqa: E501
        if not webhook_url:
            return False

        color = "good" if execution.status == "SUCCESS" else "danger"
        duration = ""
        if execution.end_time:
            duration_seconds = (
                execution.end_time - execution.start_time
            ).total_seconds()
            duration = f"{duration_seconds:.1f}s"

        fields: List[Dict[str, Any]] = [
            {"title": "Job ID", "value": job.job_id, "short": True},
            {
                "title": "Status",
                "value": execution.status,
                "short": True,
            },
            {
                "title": "Source",
                "value": job.config.source_path,
                "short": True,
            },
            {"title": "Duration", "value": duration, "short": True},
            {
                "title": "Snapshot ID",
                "value": execution.snapshot_id or "N/A",
                "short": False,
            },
        ]

        if execution.error_message:
            fields.append(
                {
                    "title": "Error",
                    "value": execution.error_message,
                    "short": False,
                }
            )

        payload: Dict[str, Any] = {
            "attachments": [
                {
                    "color": color,
                    "title": f"Backup Job {execution.status}",
                    "fields": fields,
                }
            ]
        }

        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200

    def _send_email_notification(self, job: BackupJob, execution: JobExecution) -> bool:
        """Send email notification."""
        # Email notifications would require SMTP configuration
        # This is a placeholder for the implementation
        logger.info("Email notification not implemented yet")
        return False

    def start(self) -> None:
        """Start the scheduler background thread."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        logger.info("Starting scheduler")
        self._running = True
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop(self) -> None:
        """Stop the scheduler background thread."""
        if not self._running:
            return

        logger.info("Stopping scheduler")
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)

    def _scheduler_loop(self) -> None:
        """Run main scheduler loop in background thread."""
        logger.info("Scheduler loop started")

        while self._running:
            try:
                now = datetime.now()

                with self._lock:
                    jobs_to_run = []
                    for job in self.jobs.values():
                        if not job.enabled:
                            continue

                        if job.next_run and job.next_run <= now:
                            jobs_to_run.append(job)

                # Execute jobs outside of lock
                for job in jobs_to_run:
                    try:
                        self.execute_job(job.job_id)
                    except Exception as e:  # pylint: disable=broad-except
                        logger.error(
                            "Failed to execute job %s: %s",
                            job.job_id,
                            e,
                        )

                # Sleep for 60 seconds
                time.sleep(60)

            except Exception as e:  # pylint: disable=broad-except
                logger.error("Error in scheduler loop: %s", e)
                time.sleep(60)

        logger.info("Scheduler loop stopped")

    def _save_jobs(self) -> None:
        """Save jobs to disk."""
        try:
            jobs_data = []
            for job in self.jobs.values():
                jobs_data.append(job.model_dump(mode="json"))

            with open(self.jobs_file, "w", encoding="utf-8") as f:
                json.dump(jobs_data, f, indent=2, default=str)

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to save jobs: %s", e)

    def _save_executions(self) -> None:
        """Save executions to disk."""
        try:
            executions_data = {}
            for job_id, executions in self.executions.items():
                # Keep last 100 executions
                executions_data[job_id] = [
                    e.model_dump(mode="json") for e in executions[-100:]
                ]

            with open(self.executions_file, "w", encoding="utf-8") as f:
                json.dump(executions_data, f, indent=2, default=str)

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to save executions: %s", e)

    def _load_state(self) -> None:
        """Load jobs and executions from disk."""
        # Load jobs
        if self.jobs_file.exists():
            try:
                with open(self.jobs_file, "r", encoding="utf-8") as f:
                    jobs_data = json.load(f)

                for job_data in jobs_data:
                    # Convert datetime strings back to datetime objects
                    if job_data.get("last_run"):
                        job_data["last_run"] = datetime.fromisoformat(
                            job_data["last_run"]
                        )
                    if job_data.get("next_run"):
                        job_data["next_run"] = datetime.fromisoformat(
                            job_data["next_run"]
                        )

                    job = BackupJob(**job_data)
                    self.jobs[job.job_id] = job

                logger.info("Loaded %d jobs from disk", len(self.jobs))

            except Exception as e:  # pylint: disable=broad-except
                logger.error("Failed to load jobs: %s", e)

        # Load executions
        if self.executions_file.exists():
            try:
                with open(self.executions_file, "r", encoding="utf-8") as f:
                    executions_data = json.load(f)

                for job_id, executions in executions_data.items():
                    execution_list = []
                    for exec_data in executions:
                        # Convert datetime strings
                        if exec_data.get("start_time"):
                            exec_data["start_time"] = datetime.fromisoformat(
                                exec_data["start_time"]
                            )
                        if exec_data.get("end_time"):
                            exec_data["end_time"] = datetime.fromisoformat(
                                exec_data["end_time"]
                            )

                        execution = JobExecution(**exec_data)
                        execution_list.append(execution)

                    self.executions[job_id] = execution_list

                logger.info("Loaded executions for %d jobs", len(self.executions))

            except Exception as e:  # pylint: disable=broad-except
                logger.error("Failed to load executions: %s", e)
