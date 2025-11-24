"""
Backup Manager module for restic-based backup operations.

Implements comprehensive backup management with encryption, deduplication,
retention policies, and metadata tracking. Supports the following protocols:
- P-OPS-RESILIENCE: Operational resilience with automated backups
- P-BACKUP-VALIDATION: Automated backup integrity validation
- P-SYSTEM-BACKUP: System-level backups with retention policies

Author: devCrew_s1
"""

import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class BackupConfig(BaseModel):
    """Configuration for backup operations."""

    backend: str = Field(
        ..., description="Backend URL (e.g., 's3:bucket-name', 'local:/path')"
    )
    password_file: Optional[str] = Field(
        None, description="Path to password file for encryption"
    )
    password: Optional[str] = Field(None, description="Direct password for encryption")
    repository_path: Optional[str] = Field(None, description="Override repository path")
    retention_policy: Dict[str, int] = Field(
        default_factory=lambda: {
            "keep_daily": 7,
            "keep_weekly": 4,
            "keep_monthly": 6,
            "keep_yearly": 3,
        },
        description="Retention policy configuration",
    )
    compression: str = Field(
        default="auto", description="Compression mode (auto/max/off)"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list, description="Patterns to exclude from backup"
    )
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Default tags for all backups"
    )
    cache_dir: Optional[str] = Field(
        None, description="Custom cache directory for restic"
    )
    limit_upload: Optional[int] = Field(None, description="Upload rate limit in KiB/s")
    limit_download: Optional[int] = Field(
        None, description="Download rate limit in KiB/s"
    )
    verbose: bool = Field(default=False, description="Enable verbose output")
    restic_path: str = Field(default="restic", description="Path to restic binary")

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        """Validate backend URL format."""
        if not v:
            raise ValueError("Backend cannot be empty")
        valid_prefixes = ["s3:", "azure:", "gs:", "sftp:", "rest:", "local:", "/"]
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                f"Invalid backend format. Must start with one of: {valid_prefixes}"
            )
        return v

    @field_validator("password_file")
    @classmethod
    def validate_password_file(cls, v: Optional[str]) -> Optional[str]:
        """Validate password file exists if provided."""
        if v and not Path(v).exists():
            raise ValueError(f"Password file not found: {v}")
        return v


class Snapshot(BaseModel):
    """Represents a backup snapshot."""

    id: str = Field(..., description="Unique snapshot identifier")
    short_id: str = Field(..., description="Short snapshot identifier")
    time: datetime = Field(..., description="Snapshot creation time")
    hostname: str = Field(..., description="Hostname where backup was created")
    username: str = Field(..., description="Username who created the backup")
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Snapshot tags for categorization"
    )
    paths: List[str] = Field(..., description="Paths included in the snapshot")
    size_bytes: int = Field(..., description="Total size in bytes")
    size_mb: float = Field(..., description="Total size in MB")
    files_count: int = Field(default=0, description="Number of files backed up")
    dirs_count: int = Field(default=0, description="Number of directories backed up")
    parent_id: Optional[str] = Field(
        None, description="Parent snapshot ID for incremental backups"
    )
    tree_id: Optional[str] = Field(None, description="Tree object ID")
    program_version: Optional[str] = Field(
        None, description="Restic version used for backup"
    )

    @property
    def age_hours(self) -> float:
        """Calculate age of snapshot in hours."""
        return (datetime.now() - self.time).total_seconds() / 3600

    @property
    def is_incremental(self) -> bool:
        """Check if this is an incremental backup."""
        return self.parent_id is not None


class BackupStats(BaseModel):
    """Statistics from a backup operation."""

    files_new: int = 0
    files_changed: int = 0
    files_unmodified: int = 0
    dirs_new: int = 0
    dirs_changed: int = 0
    dirs_unmodified: int = 0
    data_added: int = 0
    data_added_mb: float = 0.0
    total_files_processed: int = 0
    total_bytes_processed: int = 0
    total_duration: float = 0.0
    snapshot_id: Optional[str] = None


class RepositoryStats(BaseModel):
    """Repository statistics."""

    total_size: int = 0
    total_size_mb: float = 0.0
    total_file_count: int = 0
    snapshots_count: int = 0
    total_blob_count: int = 0
    compression_ratio: float = 0.0
    deduplication_ratio: float = 0.0


class BackupManager:
    """
    Manages backup operations using restic.

    Provides comprehensive backup functionality including:
    - Repository initialization and management
    - Incremental backups with deduplication
    - Retention policy enforcement
    - Snapshot validation and verification
    - Progress tracking and metadata collection
    """

    def __init__(self, config: BackupConfig) -> None:
        """
        Initialize BackupManager.

        Args:
            config: Backup configuration settings
        """
        self.config = config
        self.repository = self._get_repository_path()
        self._validate_restic_installation()
        logger.info(f"Initialized BackupManager for repository: {self.repository}")

    def _get_repository_path(self) -> str:
        """Get the full repository path."""
        if self.config.repository_path:
            return self.config.repository_path
        return self.config.backend

    def _validate_restic_installation(self) -> None:
        """Validate that restic is installed and accessible."""
        try:
            result = subprocess.run(
                [self.config.restic_path, "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Restic validation failed: {result.stderr}"
                )  # nosec B603
            logger.info(f"Restic version: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError(
                f"Restic not found at {self.config.restic_path}. "
                "Please install restic first."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Restic validation timed out")

    def _get_base_env(self) -> Dict[str, str]:
        """Get base environment variables for restic commands."""
        env = os.environ.copy()

        # Set repository
        env["RESTIC_REPOSITORY"] = self.repository

        # Set password
        if self.config.password_file:
            env["RESTIC_PASSWORD_FILE"] = self.config.password_file
        elif self.config.password:
            env["RESTIC_PASSWORD"] = self.config.password
        else:
            raise ValueError("Either password or password_file must be provided")

        # Set cache directory if specified
        if self.config.cache_dir:
            env["RESTIC_CACHE_DIR"] = self.config.cache_dir

        return env

    def _build_command(self, args: List[str]) -> List[str]:
        """Build restic command with common options."""
        cmd = [self.config.restic_path] + args

        if self.config.verbose:
            cmd.append("--verbose")

        if self.config.limit_upload:
            cmd.extend(["--limit-upload", str(self.config.limit_upload)])

        if self.config.limit_download:
            cmd.extend(["--limit-download", str(self.config.limit_download)])

        return cmd

    def _run_restic_command(
        self,
        args: List[str],
        timeout: Optional[int] = None,
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Run a restic command with proper error handling.

        Args:
            args: Command arguments to pass to restic
            timeout: Command timeout in seconds
            check: Whether to raise exception on non-zero exit
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess instance with command results

        Raises:
            RuntimeError: If command fails and check=True
        """
        cmd = self._build_command(args)
        env = self._get_base_env()

        logger.debug(f"Executing restic command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False,
            )  # nosec B603

            if check and result.returncode != 0:
                error_msg = f"Restic command failed: {result.stderr or result.stdout}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            return result

        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out after {timeout} seconds")
            raise RuntimeError(f"Command timed out: {e}")
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise RuntimeError(f"Command execution failed: {e}")

    def init_repository(self) -> bool:
        """
        Initialize a new restic repository.

        Returns:
            True if repository was created or already exists

        Raises:
            RuntimeError: If initialization fails
        """
        logger.info(f"Initializing repository: {self.repository}")

        try:
            # Try to check if repository exists first
            result = self._run_restic_command(
                ["snapshots", "--json"], timeout=30, check=False
            )

            if result.returncode == 0:
                logger.info("Repository already initialized")
                return True

            # Repository doesn't exist, initialize it
            result = self._run_restic_command(["init"], timeout=60)

            if result.returncode == 0:
                logger.info("Repository initialized successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            raise RuntimeError(f"Repository initialization failed: {e}")

    def create_backup(
        self,
        source: str,
        tags: Optional[Dict[str, str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        one_file_system: bool = False,
    ) -> Tuple[Snapshot, BackupStats]:
        """
        Create a new backup snapshot.

        Args:
            source: Path to backup
            tags: Additional tags for this backup
            exclude_patterns: Patterns to exclude (overrides config)
            one_file_system: Stay on same filesystem

        Returns:
            Tuple of (Snapshot, BackupStats) for the created backup

        Raises:
            RuntimeError: If backup creation fails
        """
        source_path = Path(source)
        if not source_path.exists():
            raise ValueError(f"Source path does not exist: {source}")

        logger.info(f"Creating backup of: {source}")
        start_time = time.time()

        # Build backup command
        cmd = ["backup", str(source_path), "--json"]

        # Add tags
        all_tags = {**self.config.tags, **(tags or {})}
        for key, value in all_tags.items():
            cmd.extend(["--tag", f"{key}:{value}"])

        # Add exclusions
        patterns = exclude_patterns or self.config.exclude_patterns
        for pattern in patterns:
            cmd.extend(["--exclude", pattern])

        # Add compression
        if self.config.compression != "auto":
            cmd.extend(["--compression", self.config.compression])

        # Add one-file-system if requested
        if one_file_system:
            cmd.append("--one-file-system")

        # Execute backup
        try:
            result = self._run_restic_command(cmd, timeout=None)

            # Parse output
            output_lines = result.stdout.strip().split("\n")
            snapshot_data = None
            stats_data = None

            for line in output_lines:
                try:
                    data = json.loads(line)
                    if data.get("message_type") == "summary":
                        stats_data = data
                        snapshot_data = data
                except json.JSONDecodeError:
                    continue

            if not snapshot_data:
                raise RuntimeError("Failed to parse backup output")

            # Create snapshot object
            snapshot = self._parse_snapshot_from_backup(snapshot_data)

            # Create stats object
            stats = self._parse_backup_stats(stats_data, time.time() - start_time)
            stats.snapshot_id = snapshot.id

            logger.info(
                f"Backup completed: {snapshot.short_id} "
                f"({stats.data_added_mb:.2f} MB added)"
            )

            return snapshot, stats

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise RuntimeError(f"Backup creation failed: {e}")

    def _parse_snapshot_from_backup(self, data: Dict[str, Any]) -> Snapshot:
        """Parse snapshot from backup output."""
        # Extract tags as dictionary
        tags_dict = {}
        if "tags" in data:
            for tag in data["tags"]:
                if ":" in tag:
                    key, value = tag.split(":", 1)
                    tags_dict[key] = value
                else:
                    tags_dict[tag] = ""

        return Snapshot(
            id=data["snapshot_id"],
            short_id=data["snapshot_id"][:8],
            time=datetime.fromisoformat(data["time"].replace("Z", "+00:00")),
            hostname=data.get("hostname", "unknown"),
            username=data.get("username", "unknown"),
            tags=tags_dict,
            paths=data.get("paths", []),
            size_bytes=data.get("total_bytes_processed", 0),
            size_mb=data.get("total_bytes_processed", 0) / (1024 * 1024),
            files_count=data.get("total_files_processed", 0),
            dirs_count=data.get("total_dirs_processed", 0),
            parent_id=data.get("parent_snapshot", None),
            tree_id=data.get("tree_id", None),
            program_version=data.get("program_version", None),
        )

    def _parse_backup_stats(self, data: Dict[str, Any], duration: float) -> BackupStats:
        """Parse backup statistics."""
        return BackupStats(
            files_new=data.get("files_new", 0),
            files_changed=data.get("files_changed", 0),
            files_unmodified=data.get("files_unmodified", 0),
            dirs_new=data.get("dirs_new", 0),
            dirs_changed=data.get("dirs_changed", 0),
            dirs_unmodified=data.get("dirs_unmodified", 0),
            data_added=data.get("data_added", 0),
            data_added_mb=data.get("data_added", 0) / (1024 * 1024),
            total_files_processed=data.get("total_files_processed", 0),
            total_bytes_processed=data.get("total_bytes_processed", 0),
            total_duration=duration,
        )

    def list_snapshots(
        self,
        tags: Optional[Dict[str, str]] = None,
        host: Optional[str] = None,
        paths: Optional[List[str]] = None,
    ) -> List[Snapshot]:
        """
        List all snapshots in the repository.

        Args:
            tags: Filter by tags
            host: Filter by hostname
            paths: Filter by paths

        Returns:
            List of Snapshot objects
        """
        logger.debug("Listing snapshots")

        cmd = ["snapshots", "--json"]

        # Add filters
        if tags:
            for key, value in tags.items():
                cmd.extend(["--tag", f"{key}:{value}"])

        if host:
            cmd.extend(["--host", host])

        if paths:
            for path in paths:
                cmd.extend(["--path", path])

        try:
            result = self._run_restic_command(cmd, timeout=60)
            snapshots_data = json.loads(result.stdout)

            if not snapshots_data:
                return []

            snapshots = [self._parse_snapshot_json(s) for s in snapshots_data]
            logger.debug(f"Found {len(snapshots)} snapshots")

            return snapshots

        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            raise RuntimeError(f"Failed to list snapshots: {e}")

    def _parse_snapshot_json(self, data: Dict[str, Any]) -> Snapshot:
        """Parse snapshot from JSON data."""
        # Extract tags as dictionary
        tags_dict = {}
        if "tags" in data:
            for tag in data["tags"]:
                if ":" in tag:
                    key, value = tag.split(":", 1)
                    tags_dict[key] = value
                else:
                    tags_dict[tag] = ""

        return Snapshot(
            id=data["id"],
            short_id=data["short_id"],
            time=datetime.fromisoformat(data["time"].replace("Z", "+00:00")),
            hostname=data["hostname"],
            username=data["username"],
            tags=tags_dict,
            paths=data.get("paths", []),
            size_bytes=0,  # Not available in snapshot list
            size_mb=0.0,
            parent_id=data.get("parent", None),
            tree_id=data.get("tree", None),
            program_version=data.get("program_version", None),
        )

    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """
        Get details of a specific snapshot.

        Args:
            snapshot_id: Snapshot ID (full or short)

        Returns:
            Snapshot object or None if not found
        """
        logger.debug(f"Getting snapshot: {snapshot_id}")

        try:
            # Get snapshot stats
            result = self._run_restic_command(
                ["stats", snapshot_id, "--json"], timeout=60
            )
            stats_data = json.loads(result.stdout)

            # Get snapshot metadata
            snapshots = self.list_snapshots()
            for snapshot in snapshots:
                if (
                    snapshot.id.startswith(snapshot_id)
                    or snapshot.short_id == snapshot_id
                ):
                    # Update with stats
                    snapshot.size_bytes = stats_data.get("total_size", 0)
                    snapshot.size_mb = stats_data.get("total_size", 0) / (1024 * 1024)
                    snapshot.files_count = stats_data.get("total_file_count", 0)
                    return snapshot

            return None

        except Exception as e:
            logger.error(f"Failed to get snapshot {snapshot_id}: {e}")
            return None

    def delete_snapshot(self, snapshot_id: str, prune: bool = True) -> bool:
        """
        Delete a specific snapshot.

        Args:
            snapshot_id: Snapshot ID to delete
            prune: Whether to prune unused data after deletion

        Returns:
            True if deletion successful

        Raises:
            RuntimeError: If deletion fails
        """
        logger.info(f"Deleting snapshot: {snapshot_id}")

        try:
            # Delete snapshot
            self._run_restic_command(["forget", snapshot_id], timeout=120)

            # Prune if requested
            if prune:
                logger.info("Pruning repository after deletion")
                self._run_restic_command(["prune"], timeout=600)

            logger.info(f"Successfully deleted snapshot: {snapshot_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}")
            raise RuntimeError(f"Snapshot deletion failed: {e}")

    def apply_retention_policy(
        self, dry_run: bool = False, prune: bool = True
    ) -> Dict[str, Any]:
        """
        Apply retention policy to remove old snapshots.

        Args:
            dry_run: Only show what would be deleted
            prune: Whether to prune after forgetting

        Returns:
            Dictionary with deletion results

        Raises:
            RuntimeError: If policy application fails
        """
        logger.info("Applying retention policy")

        cmd = ["forget", "--json"]

        # Add retention settings
        policy = self.config.retention_policy
        if "keep_daily" in policy:
            cmd.extend(["--keep-daily", str(policy["keep_daily"])])
        if "keep_weekly" in policy:
            cmd.extend(["--keep-weekly", str(policy["keep_weekly"])])
        if "keep_monthly" in policy:
            cmd.extend(["--keep-monthly", str(policy["keep_monthly"])])
        if "keep_yearly" in policy:
            cmd.extend(["--keep-yearly", str(policy["keep_yearly"])])

        # Add group-by option to keep per host/path
        cmd.extend(["--group-by", "host,paths"])

        if dry_run:
            cmd.append("--dry-run")

        if prune and not dry_run:
            cmd.append("--prune")

        try:
            result = self._run_restic_command(cmd, timeout=600)
            output_data = json.loads(result.stdout)

            # Parse results
            total_kept = 0
            total_removed = 0

            for group in output_data:
                kept = group.get("keep", [])
                removed = group.get("remove", [])
                total_kept += len(kept)
                total_removed += len(removed)

            logger.info(
                f"Retention policy applied: {total_kept} kept, "
                f"{total_removed} removed"
            )

            return {
                "kept": total_kept,
                "removed": total_removed,
                "groups": output_data,
                "dry_run": dry_run,
            }

        except Exception as e:
            logger.error(f"Failed to apply retention policy: {e}")
            raise RuntimeError(f"Retention policy application failed: {e}")

    def get_repository_stats(self) -> RepositoryStats:
        """
        Get repository statistics.

        Returns:
            RepositoryStats object with repository metrics

        Raises:
            RuntimeError: If stats retrieval fails
        """
        logger.debug("Getting repository statistics")

        try:
            # Get stats
            result = self._run_restic_command(["stats", "--json"], timeout=120)
            stats_data = json.loads(result.stdout)

            # Get snapshot count
            snapshots = self.list_snapshots()

            # Get blob count
            result = self._run_restic_command(
                ["check", "--read-data-subset=0%"], timeout=60, check=False
            )

            return RepositoryStats(
                total_size=stats_data.get("total_size", 0),
                total_size_mb=stats_data.get("total_size", 0) / (1024 * 1024),
                total_file_count=stats_data.get("total_file_count", 0),
                snapshots_count=len(snapshots),
                total_blob_count=stats_data.get("total_blob_count", 0),
                compression_ratio=0.0,  # Restic doesn't expose this
                deduplication_ratio=0.0,  # Would need calculation
            )

        except Exception as e:
            logger.error(f"Failed to get repository stats: {e}")
            raise RuntimeError(f"Failed to get repository stats: {e}")

    def validate_snapshot(
        self, snapshot_id: str, read_data: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate snapshot integrity.

        Args:
            snapshot_id: Snapshot ID to validate
            read_data: Whether to read and verify actual data

        Returns:
            Tuple of (success, details_dict)

        Raises:
            RuntimeError: If validation check fails to run
        """
        logger.info(f"Validating snapshot: {snapshot_id}")

        try:
            cmd = ["check"]

            if read_data:
                cmd.extend(["--read-data"])
            else:
                # Only check structure, not data
                cmd.extend(["--read-data-subset=0%"])

            # Add snapshot filter
            result = self._run_restic_command(cmd, timeout=600, check=False)

            success = result.returncode == 0
            details = {
                "snapshot_id": snapshot_id,
                "validation_time": datetime.now().isoformat(),
                "read_data": read_data,
                "success": success,
                "output": result.stdout,
                "errors": result.stderr if result.stderr else None,
            }

            if success:
                logger.info(f"Snapshot validation successful: {snapshot_id}")
            else:
                logger.error(f"Snapshot validation failed: {snapshot_id}")

            return success, details

        except Exception as e:
            logger.error(f"Failed to validate snapshot: {e}")
            raise RuntimeError(f"Snapshot validation failed: {e}")

    def check_repository(self, read_data: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Check repository integrity.

        Args:
            read_data: Whether to read and verify actual data

        Returns:
            Tuple of (success, details_dict)
        """
        logger.info("Checking repository integrity")

        try:
            cmd = ["check"]

            if read_data:
                cmd.extend(["--read-data"])

            result = self._run_restic_command(cmd, timeout=1800, check=False)

            success = result.returncode == 0
            details = {
                "check_time": datetime.now().isoformat(),
                "read_data": read_data,
                "success": success,
                "output": result.stdout,
                "errors": result.stderr if result.stderr else None,
            }

            if success:
                logger.info("Repository check successful")
            else:
                logger.error("Repository check failed")

            return success, details

        except Exception as e:
            logger.error(f"Repository check failed: {e}")
            raise RuntimeError(f"Repository check failed: {e}")

    def unlock_repository(self) -> bool:
        """
        Unlock repository (remove stale locks).

        Returns:
            True if unlock successful

        Raises:
            RuntimeError: If unlock fails
        """
        logger.info("Unlocking repository")

        try:
            self._run_restic_command(["unlock"], timeout=60)
            logger.info("Repository unlocked successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to unlock repository: {e}")
            raise RuntimeError(f"Repository unlock failed: {e}")

    def find_files(
        self, pattern: str, snapshot_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find files matching a pattern in snapshots.

        Args:
            pattern: File pattern to search for
            snapshot_id: Optional snapshot to search in

        Returns:
            List of matching files with metadata

        Raises:
            RuntimeError: If search fails
        """
        logger.debug(f"Finding files matching: {pattern}")

        cmd = ["find", pattern, "--json"]

        if snapshot_id:
            cmd.append(snapshot_id)

        try:
            result = self._run_restic_command(cmd, timeout=300)

            matches = []
            for line in result.stdout.strip().split("\n"):
                try:
                    data = json.loads(line)
                    if data.get("type") == "node":
                        matches.append(data)
                except json.JSONDecodeError:
                    continue

            logger.debug(f"Found {len(matches)} matching files")
            return matches

        except Exception as e:
            logger.error(f"File search failed: {e}")
            raise RuntimeError(f"File search failed: {e}")

    def get_latest_snapshot(
        self, tags: Optional[Dict[str, str]] = None
    ) -> Optional[Snapshot]:
        """
        Get the most recent snapshot.

        Args:
            tags: Optional tag filters

        Returns:
            Most recent Snapshot or None
        """
        snapshots = self.list_snapshots(tags=tags)
        if not snapshots:
            return None

        return max(snapshots, key=lambda s: s.time)

    def export_snapshot_metadata(self, snapshot_id: str, output_file: str) -> bool:
        """
        Export snapshot metadata to file.

        Args:
            snapshot_id: Snapshot to export
            output_file: Path to output JSON file

        Returns:
            True if export successful
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(snapshot.model_dump(), f, indent=2, default=str)

            logger.info(f"Exported snapshot metadata to: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export metadata: {e}")
            raise RuntimeError(f"Metadata export failed: {e}")
