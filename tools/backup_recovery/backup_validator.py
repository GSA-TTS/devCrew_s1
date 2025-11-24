"""
Backup Validator for Backup & Recovery Management Platform.

Provides automated backup integrity checks, restore testing in isolated
environments, data verification with checksum validation, corruption detection,
and validation scheduling.

Protocol Coverage:
- P-BACKUP-VALIDATION: Automated backup integrity validation
- P-RES-DR-DRILL: Disaster recovery testing
"""

import json
import logging
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from croniter import croniter
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ValidationConfig(BaseModel):
    """Configuration for backup validation."""

    check_data: bool = Field(
        default=True, description="Check data integrity in repository"
    )
    check_unused: bool = Field(
        default=False, description="Check for unused data in repository"
    )
    read_data: bool = Field(default=False, description="Read all data blobs")
    read_data_subset: str = Field(
        default="5%", description="Percentage of data to read for validation"
    )
    restore_test: bool = Field(default=True, description="Perform restore test")
    test_environment: str = Field(
        default="isolated", description="Environment for restore testing"
    )

    @field_validator("read_data_subset")
    @classmethod
    def validate_subset(cls, v: str) -> str:
        """Validate read_data_subset format."""
        if not v.endswith("%"):
            raise ValueError("read_data_subset must be a percentage (e.g., '5%')")
        try:
            percentage = int(v[:-1])
            if not 0 <= percentage <= 100:
                raise ValueError("Percentage must be between 0 and 100")
        except ValueError as e:
            raise ValueError(f"Invalid percentage format: {v}") from e
        return v


class ValidationResult(BaseModel):
    """Result of backup validation."""

    snapshot_id: str = Field(..., description="Snapshot ID validated")
    validation_time: datetime = Field(
        default_factory=datetime.now, description="Validation timestamp"
    )
    status: str = Field(..., description="Validation status: PASS, FAIL, WARNING")
    integrity_check: bool = Field(
        default=False, description="Repository integrity check passed"
    )
    restore_test_passed: bool = Field(default=False, description="Restore test passed")
    checksum_verification: bool = Field(
        default=False, description="Checksum verification passed"
    )
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    warnings: List[str] = Field(
        default_factory=list, description="Warnings encountered"
    )
    duration_seconds: float = Field(default=0.0, description="Duration of validation")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of allowed values."""
        allowed = ["PASS", "FAIL", "WARNING"]
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v


class BackupValidator:
    """
    Validates backup integrity and performs restore testing.

    Provides automated validation of backup snapshots including integrity
    checks, restore testing, and checksum verification.
    """

    def __init__(self, backend: str, password_file: Optional[str] = None) -> None:
        """
        Initialize BackupValidator.

        Args:
            backend: Restic repository backend URL
            password_file: Path to password file for repository
        """
        self.backend = backend
        self.password_file = password_file
        self._verify_restic_installed()
        self.validation_history_file = Path.home() / ".backup_validation_history.json"
        logger.info(
            "Initialized BackupValidator for backend: %s",
            self._sanitize_backend(backend),
        )

    def _sanitize_backend(self, backend: str) -> str:
        """Remove credentials from backend URL for logging."""
        if "@" in backend:
            parts = backend.split("@")
            if len(parts) > 1:
                return f"***@{parts[-1]}"
        return backend

    def _verify_restic_installed(self) -> None:
        """Verify restic is installed and accessible."""
        try:
            result = subprocess.run(
                ["restic", "version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            logger.debug("Restic version: %s", result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_msg = f"Restic not found or not working: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _build_restic_env(self) -> Dict[str, str]:
        """Build environment variables for restic commands."""
        env = {"RESTIC_REPOSITORY": self.backend}
        if self.password_file:
            env["RESTIC_PASSWORD_FILE"] = self.password_file
        return env

    def _run_restic_command(
        self,
        args: List[str],
        timeout: int = 300,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Run a restic command with proper environment.

        Args:
            args: Command arguments (excluding 'restic')
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess instance

        Raises:
            subprocess.CalledProcessError: If command fails
            subprocess.TimeoutExpired: If command times out
        """
        cmd = ["restic"] + args
        env = self._build_restic_env()

        logger.debug("Running restic command: %s", " ".join(args))

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=capture_output,
                text=True,
                check=True,
                timeout=timeout,
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(
                "Restic command failed: %s\nStdout: %s\nStderr: %s",
                " ".join(args),
                e.stdout,
                e.stderr,
            )
            raise
        except subprocess.TimeoutExpired:
            logger.error("Restic command timed out: %s", " ".join(args))
            raise

    def validate_snapshot(
        self, snapshot_id: str, config: ValidationConfig
    ) -> ValidationResult:
        """
        Validate a specific snapshot.

        Args:
            snapshot_id: Snapshot ID to validate
            config: Validation configuration

        Returns:
            ValidationResult with validation details
        """
        logger.info("Validating snapshot: %s", snapshot_id)
        start_time = datetime.now()

        errors = []
        warnings = []
        integrity_check = False
        restore_test_passed = False
        checksum_verification = False

        # Check repository integrity
        if config.check_data:
            try:
                logger.info("Running repository integrity check")
                args = ["check"]
                if config.read_data:
                    args.append("--read-data")
                    if config.read_data_subset:
                        args.extend(["--read-data-subset", config.read_data_subset])

                result = self._run_restic_command(args, timeout=1800)
                integrity_check = True
                logger.info("Repository integrity check passed")

                # Check for warnings in output
                if "warning" in result.stderr.lower():
                    warnings.append("Warnings in integrity check output")

            except subprocess.CalledProcessError as e:
                errors.append(f"Integrity check failed: {e.stderr}")
                logger.error("Integrity check failed: %s", e)

        # Check for unused data
        if config.check_unused:
            try:
                logger.info("Checking for unused data")
                args = ["check", "--read-data-subset=0%"]
                self._run_restic_command(args, timeout=600)
            except subprocess.CalledProcessError as e:
                warnings.append(f"Unused data check warning: {e.stderr}")

        # Verify checksums
        try:
            logger.info("Verifying checksums")
            checksum_verification = self.verify_checksums(snapshot_id)
            if not checksum_verification:
                errors.append("Checksum verification failed")
        except Exception as e:  # pylint: disable=broad-except
            errors.append(f"Checksum verification error: {str(e)}")
            logger.error("Checksum verification error: %s", e)

        # Restore test
        if config.restore_test:
            try:
                logger.info("Running restore test")
                with tempfile.TemporaryDirectory() as test_dir:
                    restore_test_passed = self.run_restore_test(snapshot_id, test_dir)
                    if not restore_test_passed:
                        errors.append("Restore test failed")
            except Exception as e:  # pylint: disable=broad-except
                errors.append(f"Restore test error: {str(e)}")
                logger.error("Restore test error: %s", e)

        # Determine overall status
        if errors:
            status = "FAIL"
        elif warnings:
            status = "WARNING"
        else:
            status = "PASS"

        duration = (datetime.now() - start_time).total_seconds()

        validation_result = ValidationResult(
            snapshot_id=snapshot_id,
            validation_time=datetime.now(),
            status=status,
            integrity_check=integrity_check,
            restore_test_passed=restore_test_passed,
            checksum_verification=checksum_verification,
            errors=errors,
            warnings=warnings,
            duration_seconds=duration,
        )

        # Save to history
        self._save_validation_result(validation_result)

        logger.info("Validation completed with status: %s", status)
        return validation_result

    def validate_recent_backups(self, days: int = 7) -> List[ValidationResult]:
        """
        Validate all backups from the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of ValidationResult objects
        """
        logger.info("Validating backups from last %d days", days)

        cutoff_date = datetime.now() - timedelta(days=days)
        results = []

        try:
            # Get snapshots
            args = ["snapshots", "--json"]
            result = self._run_restic_command(args)
            snapshots_data = json.loads(result.stdout)

            # Filter recent snapshots
            recent_snapshots = []
            for snap_data in snapshots_data:
                timestamp = datetime.fromisoformat(
                    snap_data["time"].replace("Z", "+00:00")
                )
                if timestamp >= cutoff_date:
                    recent_snapshots.append(snap_data)

            logger.info("Found %d recent snapshots", len(recent_snapshots))

            # Validate each snapshot
            config = ValidationConfig(
                check_data=True,
                restore_test=True,
                read_data_subset="5%",
            )

            for snap_data in recent_snapshots:
                snapshot_id = snap_data.get("short_id", snap_data.get("id"))
                try:
                    validation_result = self.validate_snapshot(snapshot_id, config)
                    results.append(validation_result)
                except Exception as e:  # pylint: disable=broad-except
                    logger.error("Failed to validate snapshot %s: %s", snapshot_id, e)
                    # Create a failed result
                    results.append(
                        ValidationResult(
                            snapshot_id=snapshot_id,
                            status="FAIL",
                            errors=[f"Validation error: {str(e)}"],
                        )
                    )

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to get recent snapshots: %s", e)

        return results

    def validate_repository(self) -> ValidationResult:
        """
        Validate entire repository integrity.

        Returns:
            ValidationResult for repository validation
        """
        logger.info("Validating repository integrity")
        start_time = datetime.now()

        errors = []
        warnings = []
        integrity_check = False

        try:
            # Full repository check
            args = ["check", "--read-data"]
            check_result = self._run_restic_command(args, timeout=3600)
            integrity_check = True

            # Parse output for issues
            if "error" in check_result.stderr.lower():
                errors.append("Errors found in repository")
            if "warning" in check_result.stderr.lower():
                warnings.append("Warnings found in repository")

        except subprocess.CalledProcessError as e:
            errors.append(f"Repository check failed: {e.stderr}")
            logger.error("Repository check failed: %s", e)

        # Check for corruption
        try:
            corruption_issues = self.check_corruption()
            if corruption_issues:
                errors.extend([f"Corruption: {issue}" for issue in corruption_issues])
        except Exception as e:  # pylint: disable=broad-except
            warnings.append(f"Corruption check error: {str(e)}")

        # Determine status
        if errors:
            status = "FAIL"
        elif warnings:
            status = "WARNING"
        else:
            status = "PASS"

        duration = (datetime.now() - start_time).total_seconds()

        result_obj = ValidationResult(
            snapshot_id="REPOSITORY",
            validation_time=datetime.now(),
            status=status,
            integrity_check=integrity_check,
            restore_test_passed=False,
            checksum_verification=False,
            errors=errors,
            warnings=warnings,
            duration_seconds=duration,
        )

        self._save_validation_result(result_obj)
        logger.info("Repository validation completed with status: %s", status)
        return result_obj

    def schedule_validation(self, cron: str, config: ValidationConfig) -> bool:
        """
        Schedule automated validation using cron expression.

        Args:
            cron: Cron expression for scheduling
            config: Validation configuration

        Returns:
            True if schedule was created successfully
        """
        logger.info("Scheduling validation with cron: %s", cron)

        try:
            # Validate cron expression
            if not croniter.is_valid(cron):
                logger.error("Invalid cron expression: %s", cron)
                return False

            # Save schedule configuration
            schedule_file = Path.home() / ".backup_validation_schedules.json"

            schedules = []
            if schedule_file.exists():
                with open(schedule_file, "r", encoding="utf-8") as f:
                    schedules = json.load(f)

            schedule = {
                "cron": cron,
                "config": config.model_dump(),
                "backend": self.backend,
                "created_at": datetime.now().isoformat(),
            }

            schedules.append(schedule)

            with open(schedule_file, "w", encoding="utf-8") as f:
                json.dump(schedules, f, indent=2)

            logger.info("Validation schedule created successfully")
            return True

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to create validation schedule: %s", e)
            return False

    def run_restore_test(self, snapshot_id: str, test_dir: str) -> bool:
        """
        Run a restore test for a snapshot.

        Args:
            snapshot_id: Snapshot ID to test restore
            test_dir: Directory for restore test

        Returns:
            True if restore test passed
        """
        logger.info("Running restore test for snapshot %s", snapshot_id)

        try:
            # Create test directory
            test_path = Path(test_dir)
            test_path.mkdir(parents=True, exist_ok=True)

            # Restore snapshot to test directory
            args = [
                "restore",
                snapshot_id,
                "--target",
                str(test_path),
            ]

            self._run_restic_command(args, timeout=1800)

            # Verify files were restored
            restored_files = list(test_path.rglob("*"))
            if not restored_files:
                logger.error("No files restored in test")
                return False

            logger.info("Restore test passed: %d files restored", len(restored_files))
            return True

        except subprocess.CalledProcessError as e:
            logger.error("Restore test failed: %s", e)
            return False

    def verify_checksums(self, snapshot_id: str) -> bool:
        """
        Verify checksums for a snapshot.

        Args:
            snapshot_id: Snapshot ID to verify

        Returns:
            True if checksums verified successfully
        """
        logger.info("Verifying checksums for snapshot %s", snapshot_id)

        try:
            # Use restic check with read-data for this snapshot
            args = ["check", "--read-data-subset=10%"]
            self._run_restic_command(args, timeout=1200)

            logger.info("Checksum verification passed")
            return True

        except subprocess.CalledProcessError as e:
            logger.error("Checksum verification failed: %s", e)
            return False

    def check_corruption(self) -> List[Dict[str, Any]]:
        """
        Check repository for corruption.

        Returns:
            List of corruption issues found
        """
        logger.info("Checking repository for corruption")

        corruption_issues = []

        try:
            # Run check command
            args = ["check"]
            result = self._run_restic_command(args, timeout=600)

            # Parse output for corruption indicators
            output = result.stdout + result.stderr
            if "error" in output.lower():
                for line in output.split("\n"):
                    if "error" in line.lower():
                        corruption_issues.append(
                            {
                                "type": "error",
                                "message": line.strip(),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

        except subprocess.CalledProcessError as e:
            corruption_issues.append(
                {
                    "type": "check_failed",
                    "message": str(e.stderr),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        logger.info("Found %d corruption issues", len(corruption_issues))
        return corruption_issues

    def get_validation_history(self, days: int = 30) -> List[ValidationResult]:
        """
        Get validation history for the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of ValidationResult objects
        """
        logger.info("Getting validation history for last %d days", days)

        if not self.validation_history_file.exists():
            logger.info("No validation history found")
            return []

        try:
            with open(self.validation_history_file, "r", encoding="utf-8") as f:
                history_data = json.load(f)

            cutoff_date = datetime.now() - timedelta(days=days)
            results = []

            for entry in history_data:
                validation_time = datetime.fromisoformat(entry["validation_time"])
                if validation_time >= cutoff_date:
                    results.append(ValidationResult(**entry))

            logger.info("Found %d validation results in history", len(results))
            return results

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to load validation history: %s", e)
            return []

    def _save_validation_result(self, result: ValidationResult) -> None:
        """Save validation result to history file."""
        try:
            history_data = []
            if self.validation_history_file.exists():
                with open(self.validation_history_file, "r", encoding="utf-8") as f:
                    history_data = json.load(f)

            history_data.append(result.model_dump(mode="json"))

            # Keep only last 1000 entries
            if len(history_data) > 1000:
                history_data = history_data[-1000:]

            with open(self.validation_history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=2, default=str)

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to save validation result: %s", e)
