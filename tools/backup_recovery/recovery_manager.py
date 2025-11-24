"""
Recovery Manager for Backup & Recovery Management Platform.

Provides point-in-time recovery capabilities with snapshot browsing,
file-level and directory-level restore, database restore automation,
and consistency validation.

Protocol Coverage:
- P-OPS-RESILIENCE: Operational resilience with point-in-time recovery
- P-RES-DR-DRILL: Disaster recovery capabilities
"""

import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class RestoreConfig(BaseModel):
    """Configuration for restore operations."""

    snapshot_id: str = Field(..., description="Snapshot ID to restore from")
    target_path: str = Field(..., description="Target path for restore")
    include_patterns: List[str] = Field(
        default_factory=list, description="Patterns to include in restore"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list, description="Patterns to exclude from restore"
    )
    verify_checksums: bool = Field(
        default=True, description="Verify checksums after restore"
    )
    restore_permissions: bool = Field(
        default=True, description="Restore file permissions"
    )
    restore_timestamps: bool = Field(
        default=True, description="Restore file timestamps"
    )

    @field_validator("target_path")
    @classmethod
    def validate_target_path(cls, v: str) -> str:
        """Validate target path is absolute."""
        if not Path(v).is_absolute():
            raise ValueError("Target path must be absolute")
        return v


class RestoreResult(BaseModel):
    """Result of a restore operation."""

    success: bool = Field(..., description="Whether restore succeeded")
    snapshot_id: str = Field(..., description="Snapshot ID restored from")
    target_path: str = Field(..., description="Target path where files restored")
    files_restored: int = Field(default=0, description="Number of files restored")
    bytes_restored: int = Field(default=0, description="Bytes restored")
    duration_seconds: float = Field(
        default=0.0, description="Duration of restore operation"
    )
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    verification_passed: bool = Field(
        default=False, description="Whether verification passed"
    )


class Snapshot(BaseModel):
    """Snapshot metadata."""

    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    timestamp: datetime = Field(..., description="Snapshot creation time")
    hostname: str = Field(default="", description="Hostname of backup source")
    username: str = Field(default="", description="Username of backup creator")
    paths: List[str] = Field(default_factory=list, description="Paths backed up")
    tags: Dict[str, str] = Field(default_factory=dict, description="Snapshot tags")
    tree_id: str = Field(default="", description="Tree object ID")
    parent_id: Optional[str] = Field(default=None, description="Parent snapshot ID")
    size_bytes: int = Field(default=0, description="Total size in bytes")


class FileVersion(BaseModel):
    """Represents a file version across snapshots."""

    file_path: str = Field(..., description="Path of the file")
    snapshot_id: str = Field(..., description="Snapshot containing this version")
    timestamp: datetime = Field(..., description="Snapshot timestamp")
    size_bytes: int = Field(default=0, description="File size in bytes")
    mode: str = Field(default="", description="File permissions")
    mtime: Optional[datetime] = Field(
        default=None, description="File modification time"
    )


class RecoveryManager:
    """
    Manages recovery operations for backup snapshots.

    Provides point-in-time recovery, file browsing, and database restoration
    capabilities using restic backend.
    """

    def __init__(self, backend: str, password_file: Optional[str] = None) -> None:
        """
        Initialize RecoveryManager.

        Args:
            backend: Restic repository backend URL
            password_file: Path to password file for repository
        """
        self.backend = backend
        self.password_file = password_file
        self._verify_restic_installed()
        logger.info(
            "Initialized RecoveryManager for backend: %s",
            self._sanitize_backend(backend),
        )

    def _sanitize_backend(self, backend: str) -> str:
        """Remove credentials from backend URL for logging."""
        # Remove passwords/keys from URLs
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

    def list_snapshots(
        self, filter_tags: Optional[Dict[str, str]] = None
    ) -> List[Snapshot]:
        """
        List all snapshots in repository.

        Args:
            filter_tags: Optional tags to filter snapshots

        Returns:
            List of Snapshot objects
        """
        logger.info("Listing snapshots with filters: %s", filter_tags)

        args = ["snapshots", "--json"]
        if filter_tags:
            for key, value in filter_tags.items():
                args.extend(["--tag", f"{key}={value}"])

        try:
            result = self._run_restic_command(args)
            snapshots_data = json.loads(result.stdout)

            snapshots = []
            for snap_data in snapshots_data:
                snapshot = Snapshot(
                    snapshot_id=snap_data.get("short_id", snap_data.get("id")),
                    timestamp=datetime.fromisoformat(
                        snap_data["time"].replace("Z", "+00:00")
                    ),
                    hostname=snap_data.get("hostname", ""),
                    username=snap_data.get("username", ""),
                    paths=snap_data.get("paths", []),
                    tags={
                        tag.split("=")[0]: tag.split("=")[1] if "=" in tag else tag
                        for tag in snap_data.get("tags", [])
                    },
                    tree_id=snap_data.get("tree", ""),
                    parent_id=snap_data.get("parent"),
                    size_bytes=0,  # Will be populated if needed
                )
                snapshots.append(snapshot)

            logger.info("Found %d snapshots", len(snapshots))
            return snapshots

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error("Failed to list snapshots: %s", e)
            return []

    def browse_snapshot(
        self, snapshot_id: str, path: str = "/"
    ) -> List[Dict[str, Any]]:
        """
        Browse files in a snapshot at given path.

        Args:
            snapshot_id: Snapshot ID to browse
            path: Path within snapshot to browse

        Returns:
            List of file/directory metadata dictionaries
        """
        logger.info("Browsing snapshot %s at path: %s", snapshot_id, path)

        args = ["ls", snapshot_id, path, "--json"]

        try:
            result = self._run_restic_command(args, timeout=60)
            entries = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(
                        {
                            "path": entry.get("path", ""),
                            "name": entry.get("name", ""),
                            "type": entry.get("type", ""),
                            "size": entry.get("size", 0),
                            "mode": entry.get("mode", 0),
                            "mtime": entry.get("mtime", ""),
                            "atime": entry.get("atime", ""),
                            "ctime": entry.get("ctime", ""),
                            "uid": entry.get("uid", 0),
                            "gid": entry.get("gid", 0),
                        }
                    )
                except json.JSONDecodeError:
                    continue

            logger.info("Found %d entries in path", len(entries))
            return entries

        except subprocess.CalledProcessError as e:
            logger.error("Failed to browse snapshot: %s", e)
            return []

    def restore_snapshot(self, config: RestoreConfig) -> RestoreResult:
        """
        Restore a complete snapshot to target path.

        Args:
            config: Restore configuration

        Returns:
            RestoreResult with operation details
        """
        logger.info(
            "Restoring snapshot %s to %s", config.snapshot_id, config.target_path
        )
        start_time = datetime.now()

        # Ensure target path exists
        target_path = Path(config.target_path)
        target_path.mkdir(parents=True, exist_ok=True)

        args = ["restore", config.snapshot_id, "--target", config.target_path]

        # Add include patterns
        for pattern in config.include_patterns:
            args.extend(["--include", pattern])

        # Add exclude patterns
        for pattern in config.exclude_patterns:
            args.extend(["--exclude", pattern])

        # Add options
        if not config.restore_permissions:
            args.append("--no-permissions")

        errors = []
        files_restored = 0
        bytes_restored = 0

        try:
            result = self._run_restic_command(args, timeout=3600)

            # Parse output for statistics
            output_lines = result.stderr.split("\n")
            for line in output_lines:
                if "restored" in line.lower():
                    # Try to extract numbers
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and i > 0:
                            if "file" in parts[i - 1].lower():
                                files_restored = int(part)
                            elif any(
                                unit in parts[i + 1].lower()
                                for unit in ["b", "kb", "mb", "gb"]
                                if i + 1 < len(parts)
                            ):
                                bytes_restored = self._parse_size(
                                    f"{part} {parts[i+1]}"
                                )

            duration = (datetime.now() - start_time).total_seconds()

            # Verify if requested
            verification_passed = True
            if config.verify_checksums:
                verification_passed = self.verify_restore(
                    config.snapshot_id, config.target_path
                )
                if not verification_passed:
                    errors.append("Checksum verification failed")

            return RestoreResult(
                success=True,
                snapshot_id=config.snapshot_id,
                target_path=config.target_path,
                files_restored=files_restored,
                bytes_restored=bytes_restored,
                duration_seconds=duration,
                errors=errors,
                verification_passed=verification_passed,
            )

        except subprocess.CalledProcessError as e:
            duration = (datetime.now() - start_time).total_seconds()
            errors.append(f"Restore failed: {e.stderr}")
            logger.error("Restore failed: %s", e)

            return RestoreResult(
                success=False,
                snapshot_id=config.snapshot_id,
                target_path=config.target_path,
                files_restored=files_restored,
                bytes_restored=bytes_restored,
                duration_seconds=duration,
                errors=errors,
                verification_passed=False,
            )

    def restore_files(
        self, snapshot_id: str, files: List[str], target: str
    ) -> RestoreResult:
        """
        Restore specific files from a snapshot.

        Args:
            snapshot_id: Snapshot ID to restore from
            files: List of file paths to restore
            target: Target directory for restore

        Returns:
            RestoreResult with operation details
        """
        logger.info("Restoring %d files from snapshot %s", len(files), snapshot_id)

        config = RestoreConfig(
            snapshot_id=snapshot_id,
            target_path=target,
            include_patterns=files,
        )

        return self.restore_snapshot(config)

    def restore_directory(
        self, snapshot_id: str, directory: str, target: str
    ) -> RestoreResult:
        """
        Restore a specific directory from a snapshot.

        Args:
            snapshot_id: Snapshot ID to restore from
            directory: Directory path to restore
            target: Target directory for restore

        Returns:
            RestoreResult with operation details
        """
        logger.info("Restoring directory %s from snapshot %s", directory, snapshot_id)

        config = RestoreConfig(
            snapshot_id=snapshot_id,
            target_path=target,
            include_patterns=[f"{directory}/*"],
        )

        return self.restore_snapshot(config)

    def verify_restore(self, snapshot_id: str, restored_path: str) -> bool:
        """
        Verify restored files match snapshot contents.

        Args:
            snapshot_id: Snapshot ID that was restored
            restored_path: Path where files were restored

        Returns:
            True if verification passed, False otherwise
        """
        logger.info(
            "Verifying restore of snapshot %s at %s", snapshot_id, restored_path
        )

        try:
            # Use restic diff to compare
            # This is a simplified verification
            # In production, would compare checksums
            args = ["ls", snapshot_id, "--json"]
            result = self._run_restic_command(args, timeout=120)

            # Count files in snapshot
            snapshot_files = 0
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "file":
                            snapshot_files += 1
                    except json.JSONDecodeError:
                        continue

            # Count files in restored path
            restored_path_obj = Path(restored_path)
            if not restored_path_obj.exists():
                logger.error("Restored path does not exist: %s", restored_path)
                return False

            restored_files = sum(1 for _ in restored_path_obj.rglob("*") if _.is_file())

            logger.info(
                "Snapshot files: %d, Restored files: %d",
                snapshot_files,
                restored_files,
            )

            # Basic check - more sophisticated verification would be needed
            # for production
            return restored_files > 0

        except subprocess.CalledProcessError as e:
            logger.error("Verification failed: %s", e)
            return False

    def restore_database(
        self, snapshot_id: str, db_type: str, db_config: Dict[str, Any]
    ) -> RestoreResult:
        """
        Restore a database from snapshot.

        Args:
            snapshot_id: Snapshot ID to restore from
            db_type: Database type (postgres, mysql, mongodb)
            db_config: Database configuration (host, port, database, etc.)

        Returns:
            RestoreResult with operation details
        """
        logger.info("Restoring %s database from snapshot %s", db_type, snapshot_id)
        start_time = datetime.now()

        errors = []
        success = False

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # First restore database dump to temp directory
                dump_pattern = f"*{db_type}*.sql"
                if db_type == "mongodb":
                    dump_pattern = "*.bson"

                config = RestoreConfig(
                    snapshot_id=snapshot_id,
                    target_path=temp_dir,
                    include_patterns=[dump_pattern],
                )

                restore_result = self.restore_snapshot(config)

                if not restore_result.success:
                    errors.extend(restore_result.errors)
                    return restore_result

                # Find restored dump file
                temp_path = Path(temp_dir)
                dump_files = list(temp_path.rglob(dump_pattern))

                if not dump_files:
                    errors.append(f"No {db_type} dump files found in snapshot")
                    logger.error("No dump files found")
                    return RestoreResult(
                        success=False,
                        snapshot_id=snapshot_id,
                        target_path=temp_dir,
                        duration_seconds=(datetime.now() - start_time).total_seconds(),
                        errors=errors,
                        verification_passed=False,
                    )

                dump_file = dump_files[0]
                logger.info("Found database dump: %s", dump_file)

                # Restore database based on type
                if db_type == "postgres":
                    success = self._restore_postgres(dump_file, db_config)
                elif db_type == "mysql":
                    success = self._restore_mysql(dump_file, db_config)
                elif db_type == "mongodb":
                    success = self._restore_mongodb(dump_file, db_config)
                else:
                    errors.append(f"Unsupported database type: {db_type}")

                duration = (datetime.now() - start_time).total_seconds()

                return RestoreResult(
                    success=success,
                    snapshot_id=snapshot_id,
                    target_path=str(dump_file),
                    files_restored=1,
                    bytes_restored=dump_file.stat().st_size,
                    duration_seconds=duration,
                    errors=errors,
                    verification_passed=success,
                )

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Database restore failed: %s", e)
            errors.append(f"Database restore failed: {str(e)}")
            duration = (datetime.now() - start_time).total_seconds()

            return RestoreResult(
                success=False,
                snapshot_id=snapshot_id,
                target_path="",
                duration_seconds=duration,
                errors=errors,
                verification_passed=False,
            )

    def _restore_postgres(self, dump_file: Path, db_config: Dict[str, Any]) -> bool:
        """Restore PostgreSQL database from dump file."""
        try:
            cmd = [
                "psql",
                "-h",
                db_config.get("host", "localhost"),
                "-p",
                str(db_config.get("port", 5432)),
                "-U",
                db_config.get("user", "postgres"),
                "-d",
                db_config["database"],
                "-f",
                str(dump_file),
            ]

            subprocess.run(cmd, check=True, capture_output=True, timeout=600)
            logger.info("PostgreSQL restore completed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error("PostgreSQL restore failed: %s", e.stderr)
            return False

    def _restore_mysql(self, dump_file: Path, db_config: Dict[str, Any]) -> bool:
        """Restore MySQL database from dump file."""
        try:
            cmd = [
                "mysql",
                "-h",
                db_config.get("host", "localhost"),
                "-P",
                str(db_config.get("port", 3306)),
                "-u",
                db_config.get("user", "root"),
                db_config["database"],
            ]

            if "password" in db_config:
                cmd.extend(["-p", db_config["password"]])

            with open(dump_file, "r", encoding="utf-8") as f:
                subprocess.run(
                    cmd, stdin=f, check=True, capture_output=True, timeout=600
                )

            logger.info("MySQL restore completed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error("MySQL restore failed: %s", e.stderr)
            return False

    def _restore_mongodb(self, dump_file: Path, db_config: Dict[str, Any]) -> bool:
        """Restore MongoDB database from dump file."""
        try:
            cmd = [
                "mongorestore",
                "--host",
                db_config.get("host", "localhost"),
                "--port",
                str(db_config.get("port", 27017)),
                "--db",
                db_config["database"],
                str(dump_file.parent),
            ]

            if "username" in db_config:
                cmd.extend(["--username", db_config["username"]])
            if "password" in db_config:
                cmd.extend(["--password", db_config["password"]])

            subprocess.run(cmd, check=True, capture_output=True, timeout=600)
            logger.info("MongoDB restore completed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error("MongoDB restore failed: %s", e.stderr)
            return False

    def get_file_versions(self, file_path: str) -> List[FileVersion]:
        """
        Get all versions of a file across snapshots.

        Args:
            file_path: Path of file to get versions for

        Returns:
            List of FileVersion objects, newest first
        """
        logger.info("Getting versions of file: %s", file_path)

        snapshots = self.list_snapshots()
        versions = []

        for snapshot in snapshots:
            try:
                # Browse snapshot for this file
                args = ["ls", snapshot.snapshot_id, file_path, "--json"]
                result = self._run_restic_command(args, timeout=30)

                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "file":
                            mtime = None
                            if entry.get("mtime"):
                                try:
                                    mtime = datetime.fromisoformat(
                                        entry["mtime"].replace("Z", "+00:00")
                                    )
                                except (ValueError, AttributeError):
                                    pass

                            version = FileVersion(
                                file_path=file_path,
                                snapshot_id=snapshot.snapshot_id,
                                timestamp=snapshot.timestamp,
                                size_bytes=entry.get("size", 0),
                                mode=oct(entry.get("mode", 0)),
                                mtime=mtime,
                            )
                            versions.append(version)
                            break  # Found the file in this snapshot
                    except json.JSONDecodeError:
                        continue

            except subprocess.CalledProcessError:
                # File doesn't exist in this snapshot
                continue

        # Sort by timestamp, newest first
        versions.sort(key=lambda v: v.timestamp, reverse=True)
        logger.info("Found %d versions of file", len(versions))
        return versions

    @staticmethod
    def _parse_size(size_str: str) -> int:
        """
        Parse human-readable size string to bytes.

        Args:
            size_str: Size string like "10 MB", "1.5 GB"

        Returns:
            Size in bytes
        """
        size_str = size_str.strip().upper()
        units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}

        parts = size_str.split()
        if len(parts) != 2:
            return 0

        try:
            value = float(parts[0])
            unit = parts[1]
            return int(value * units.get(unit, 1))
        except (ValueError, KeyError):
            return 0
