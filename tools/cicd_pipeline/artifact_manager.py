"""
Artifact Manager Module
Issue #36 - TOOL-CICD-001

Handles artifact upload, download, cleanup, and retention
for CI/CD pipeline workflows.
"""

import gzip
import logging
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from issue_36_github_actions_wrapper import GitHubActionsWrapper

logger = logging.getLogger(__name__)


class ArtifactError(Exception):
    """Base exception for artifact operations."""

    pass


class ArtifactManager:
    """
    Manages workflow artifacts for CI/CD pipelines.

    Provides methods for uploading, downloading, extracting,
    and managing artifact lifecycle with retention policies.
    """

    def __init__(
        self,
        github_wrapper: GitHubActionsWrapper,
        download_path: str = "./artifacts",
        retention_days: int = 90,
    ):
        """
        Initialize artifact manager.

        Args:
            github_wrapper: GitHubActionsWrapper instance
            download_path: Default path for downloaded artifacts
            retention_days: Artifact retention period in days
        """
        self.github = github_wrapper
        self.download_path = Path(download_path)
        self.retention_days = retention_days

        # Create download directory
        self.download_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized artifact manager with download path: {download_path}"
        )

    def list_artifacts(
        self,
        run_id: Optional[int] = None,
        name_filter: Optional[str] = None,
        include_expired: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List available artifacts.

        Args:
            run_id: Filter by workflow run ID
            name_filter: Filter by artifact name (substring match)
            include_expired: Include expired artifacts

        Returns:
            List of artifact dictionaries
        """
        artifacts = self.github.list_artifacts(run_id)

        # Filter by name
        if name_filter:
            artifacts = [
                art for art in artifacts if name_filter in art["name"]
            ]

        # Filter expired
        if not include_expired:
            artifacts = [art for art in artifacts if not art["expired"]]

        logger.info(f"Found {len(artifacts)} artifacts")
        return artifacts

    def download_artifact(
        self,
        artifact_id: int,
        destination: Optional[str] = None,
        extract: bool = True,
    ) -> str:
        """
        Download and optionally extract an artifact.

        Args:
            artifact_id: Artifact ID
            destination: Destination path (default: download_path)
            extract: Extract archive after download

        Returns:
            Path to downloaded/extracted artifact

        Raises:
            ArtifactError: If download or extraction fails
        """
        try:
            # Get artifact info
            artifacts = self.github.list_artifacts()
            artifact = next(
                (art for art in artifacts if art["id"] == artifact_id), None
            )

            if not artifact:
                raise ArtifactError(f"Artifact {artifact_id} not found")

            # Determine destination
            if destination is None:
                destination = self.download_path / f"{artifact['name']}.zip"
            else:
                destination = Path(destination)

            destination.parent.mkdir(parents=True, exist_ok=True)

            # Download artifact
            self.github.download_artifact(artifact_id, str(destination))

            logger.info(f"Downloaded artifact {artifact['name']} to {destination}")

            # Extract if requested
            if extract and zipfile.is_zipfile(destination):
                extract_path = destination.parent / artifact["name"]
                self._extract_archive(str(destination), str(extract_path))
                logger.info(f"Extracted artifact to {extract_path}")
                return str(extract_path)

            return str(destination)

        except Exception as e:
            logger.error(f"Failed to download artifact: {e}")
            raise ArtifactError(f"Failed to download artifact: {e}")

    def download_run_artifacts(
        self,
        run_id: int,
        name_filter: Optional[str] = None,
        extract: bool = True,
    ) -> List[str]:
        """
        Download all artifacts from a workflow run.

        Args:
            run_id: Workflow run ID
            name_filter: Filter by artifact name
            extract: Extract archives after download

        Returns:
            List of paths to downloaded/extracted artifacts
        """
        artifacts = self.list_artifacts(run_id=run_id, name_filter=name_filter)

        downloaded_paths = []
        for artifact in artifacts:
            try:
                path = self.download_artifact(
                    artifact["id"],
                    extract=extract,
                )
                downloaded_paths.append(path)
            except ArtifactError as e:
                logger.warning(f"Failed to download artifact {artifact['name']}: {e}")

        logger.info(
            f"Downloaded {len(downloaded_paths)}/{len(artifacts)} "
            f"artifacts from run {run_id}"
        )

        return downloaded_paths

    def _extract_archive(self, archive_path: str, extract_path: str) -> None:
        """
        Extract ZIP or GZ archive.

        Args:
            archive_path: Path to archive file
            extract_path: Destination directory

        Raises:
            ArtifactError: If extraction fails
        """
        try:
            extract_path_obj = Path(extract_path)
            extract_path_obj.mkdir(parents=True, exist_ok=True)

            if zipfile.is_zipfile(archive_path):
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    zip_ref.extractall(extract_path)
            elif archive_path.endswith(".gz"):
                with gzip.open(archive_path, "rb") as f_in:
                    output_file = extract_path_obj / Path(archive_path).stem
                    with open(output_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                raise ArtifactError(f"Unsupported archive format: {archive_path}")

        except Exception as e:
            raise ArtifactError(f"Failed to extract archive: {e}")

    def cleanup_artifacts(
        self,
        older_than_days: Optional[int] = None,
        name_pattern: Optional[str] = None,
        dry_run: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Clean up old artifacts based on retention policy.

        Args:
            older_than_days: Delete artifacts older than this (default: retention_days)
            name_pattern: Filter by artifact name pattern
            dry_run: If True, only list artifacts to be deleted

        Returns:
            List of artifacts that were/would be deleted

        Note:
            Actual deletion requires repository admin permissions
        """
        if older_than_days is None:
            older_than_days = self.retention_days

        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        # List all artifacts
        artifacts = self.list_artifacts(include_expired=True)

        # Filter by age and pattern
        to_delete = []
        for artifact in artifacts:
            created_at = artifact["created_at"]

            # Check age
            if created_at < cutoff_date:
                # Check name pattern
                if name_pattern is None or name_pattern in artifact["name"]:
                    to_delete.append(artifact)

        logger.info(
            f"Found {len(to_delete)} artifacts older than {older_than_days} days"
        )

        if not dry_run:
            logger.warning(
                "Artifact deletion requires admin permissions and is not "
                "supported via API. Please use GitHub UI or workflow."
            )

        return to_delete

    def get_artifact_metadata(self, artifact_id: int) -> Dict[str, Any]:
        """
        Get detailed metadata for an artifact.

        Args:
            artifact_id: Artifact ID

        Returns:
            Dictionary with artifact metadata

        Raises:
            ArtifactError: If artifact not found
        """
        artifacts = self.github.list_artifacts()
        artifact = next(
            (art for art in artifacts if art["id"] == artifact_id), None
        )

        if not artifact:
            raise ArtifactError(f"Artifact {artifact_id} not found")

        # Calculate age
        created_at = artifact["created_at"]
        age_days = (datetime.now() - created_at).days

        # Add computed fields
        artifact["age_days"] = age_days
        artifact["size_mb"] = artifact["size_in_bytes"] / (1024 * 1024)

        return artifact

    def find_artifacts(
        self,
        workflow_name: Optional[str] = None,
        branch: Optional[str] = None,
        status: Optional[str] = None,
        artifact_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find artifacts matching criteria across workflow runs.

        Args:
            workflow_name: Filter by workflow name
            branch: Filter by branch
            status: Filter by run status (completed, success, failure)
            artifact_name: Filter by artifact name

        Returns:
            List of artifact dictionaries with run metadata
        """
        # Get workflow runs
        runs = self.github.list_workflow_runs(
            workflow_id=workflow_name,
            branch=branch,
            status=status,
            limit=50,
        )

        all_artifacts = []
        for run in runs:
            artifacts = self.github.list_artifacts(run_id=run["id"])

            # Filter by artifact name
            if artifact_name:
                artifacts = [
                    art for art in artifacts if artifact_name in art["name"]
                ]

            # Add run metadata
            for artifact in artifacts:
                artifact["run_id"] = run["id"]
                artifact["run_name"] = run["name"]
                artifact["run_status"] = run["status"]
                artifact["run_conclusion"] = run["conclusion"]
                artifact["branch"] = run["head_branch"]
                all_artifacts.append(artifact)

        logger.info(f"Found {len(all_artifacts)} artifacts matching criteria")
        return all_artifacts

    def cleanup_local_artifacts(
        self, older_than_days: int = 7
    ) -> List[str]:
        """
        Clean up local downloaded artifacts.

        Args:
            older_than_days: Delete files older than this many days

        Returns:
            List of deleted file paths
        """
        cutoff_time = datetime.now() - timedelta(days=older_than_days)
        deleted_files = []

        for file_path in self.download_path.rglob("*"):
            if file_path.is_file():
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                if modified_time < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_files.append(str(file_path))
                        logger.debug(f"Deleted local artifact: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")

        logger.info(f"Cleaned up {len(deleted_files)} local artifacts")
        return deleted_files

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for artifacts.

        Returns:
            Dictionary with storage stats
        """
        artifacts = self.github.list_artifacts()

        total_size = sum(art["size_in_bytes"] for art in artifacts)
        total_count = len(artifacts)
        expired_count = sum(1 for art in artifacts if art["expired"])

        # Group by name
        by_name = {}
        for artifact in artifacts:
            name = artifact["name"]
            if name not in by_name:
                by_name[name] = {"count": 0, "total_size": 0}
            by_name[name]["count"] += 1
            by_name[name]["total_size"] += artifact["size_in_bytes"]

        return {
            "total_artifacts": total_count,
            "expired_artifacts": expired_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "by_name": by_name,
        }

    def validate_artifacts(
        self, run_id: int, expected_artifacts: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that expected artifacts exist for a run.

        Args:
            run_id: Workflow run ID
            expected_artifacts: List of expected artifact names

        Returns:
            Tuple of (all_present, missing_artifacts)
        """
        artifacts = self.list_artifacts(run_id=run_id)
        artifact_names = {art["name"] for art in artifacts}

        missing = [name for name in expected_artifacts if name not in artifact_names]

        all_present = len(missing) == 0

        if all_present:
            logger.info(f"All {len(expected_artifacts)} expected artifacts present")
        else:
            logger.warning(f"Missing artifacts: {missing}")

        return all_present, missing
