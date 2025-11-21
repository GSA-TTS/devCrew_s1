"""Git-based version management for configurations."""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from deepdiff import DeepDiff


@dataclass
class ConfigVersion:
    """Represents a configuration version."""

    version_id: str
    timestamp: datetime
    author: str
    message: str
    config_hash: str
    parent_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigDiff:
    """Represents a diff between two configurations."""

    version_from: str
    version_to: str
    changes: Dict[str, Any]
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)


class VersionManager:
    """Git-based version manager for configurations."""

    def __init__(
        self,
        repo_path: Union[str, Path],
        config_dir: str = "configs",
    ) -> None:
        """Initialize the version manager.

        Args:
            repo_path: Path to the Git repository.
            config_dir: Subdirectory for configuration files.
        """
        self._repo_path = Path(repo_path)
        self._config_dir = config_dir
        self._versions_file = self._repo_path / ".config_versions.json"
        self._versions: Dict[str, ConfigVersion] = {}
        self._load_versions()

    def _load_versions(self) -> None:
        """Load version history from file."""
        if self._versions_file.exists():
            data = json.loads(self._versions_file.read_text(encoding="utf-8"))
            for vid, vdata in data.items():
                self._versions[vid] = ConfigVersion(
                    version_id=vdata["version_id"],
                    timestamp=datetime.fromisoformat(vdata["timestamp"]),
                    author=vdata["author"],
                    message=vdata["message"],
                    config_hash=vdata["config_hash"],
                    parent_version=vdata.get("parent_version"),
                    metadata=vdata.get("metadata", {}),
                )

    def _save_versions(self) -> None:
        """Save version history to file."""
        data = {}
        for vid, version in self._versions.items():
            data[vid] = {
                "version_id": version.version_id,
                "timestamp": version.timestamp.isoformat(),
                "author": version.author,
                "message": version.message,
                "config_hash": version.config_hash,
                "parent_version": version.parent_version,
                "metadata": version.metadata,
            }
        self._versions_file.parent.mkdir(parents=True, exist_ok=True)
        self._versions_file.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _compute_hash(self, config: Dict[str, Any]) -> str:
        """Compute hash for a configuration."""
        import hashlib

        content = json.dumps(config, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def _generate_version_id(self) -> str:
        """Generate a new version ID."""
        import uuid

        return f"v{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

    def commit(
        self,
        config_name: str,
        config: Dict[str, Any],
        author: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConfigVersion:
        """Commit a new configuration version.

        Args:
            config_name: Name of the configuration.
            config: Configuration dictionary.
            author: Author of the change.
            message: Commit message.
            metadata: Optional metadata.

        Returns:
            Created ConfigVersion.
        """
        version_id = self._generate_version_id()
        config_hash = self._compute_hash(config)

        latest = self.get_latest_version(config_name)
        parent_version = latest.version_id if latest else None

        version = ConfigVersion(
            version_id=version_id,
            timestamp=datetime.now(),
            author=author,
            message=message,
            config_hash=config_hash,
            parent_version=parent_version,
            metadata=metadata or {},
        )

        version_key = f"{config_name}:{version_id}"
        self._versions[version_key] = version

        config_path = (
            self._repo_path
            / self._config_dir
            / config_name
            / f"{version_id}.json"
        )
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

        self._save_versions()
        return version

    def get_version(
        self,
        config_name: str,
        version_id: str,
    ) -> Optional[ConfigVersion]:
        """Get a specific configuration version.

        Args:
            config_name: Name of the configuration.
            version_id: Version ID.

        Returns:
            ConfigVersion or None if not found.
        """
        version_key = f"{config_name}:{version_id}"
        return self._versions.get(version_key)

    def get_config(
        self,
        config_name: str,
        version_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get configuration content for a specific version.

        Args:
            config_name: Name of the configuration.
            version_id: Version ID.

        Returns:
            Configuration dictionary or None if not found.
        """
        config_path = (
            self._repo_path
            / self._config_dir
            / config_name
            / f"{version_id}.json"
        )
        if not config_path.exists():
            return None
        return json.loads(config_path.read_text(encoding="utf-8"))

    def get_latest_version(self, config_name: str) -> Optional[ConfigVersion]:
        """Get the latest version of a configuration.

        Args:
            config_name: Name of the configuration.

        Returns:
            Latest ConfigVersion or None if no versions exist.
        """
        versions = self.list_versions(config_name)
        if not versions:
            return None
        return versions[0]

    def get_latest_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Get the latest configuration content.

        Args:
            config_name: Name of the configuration.

        Returns:
            Latest configuration dictionary or None.
        """
        latest = self.get_latest_version(config_name)
        if not latest:
            return None
        return self.get_config(config_name, latest.version_id)

    def list_versions(self, config_name: str) -> List[ConfigVersion]:
        """List all versions of a configuration.

        Args:
            config_name: Name of the configuration.

        Returns:
            List of ConfigVersion objects, newest first.
        """
        prefix = f"{config_name}:"
        versions = [
            v for k, v in self._versions.items() if k.startswith(prefix)
        ]
        return sorted(versions, key=lambda v: v.timestamp, reverse=True)

    def diff(
        self,
        config_name: str,
        version_from: str,
        version_to: str,
    ) -> Optional[ConfigDiff]:
        """Generate diff between two versions.

        Args:
            config_name: Name of the configuration.
            version_from: Source version ID.
            version_to: Target version ID.

        Returns:
            ConfigDiff or None if versions not found.
        """
        config_from = self.get_config(config_name, version_from)
        config_to = self.get_config(config_name, version_to)

        if config_from is None or config_to is None:
            return None

        diff = DeepDiff(config_from, config_to, ignore_order=True)

        added = []
        removed = []
        modified = []

        if "dictionary_item_added" in diff:
            added = [str(k) for k in diff["dictionary_item_added"]]
        if "dictionary_item_removed" in diff:
            removed = [str(k) for k in diff["dictionary_item_removed"]]
        if "values_changed" in diff:
            modified = [str(k) for k in diff["values_changed"]]
        if "type_changes" in diff:
            modified.extend([str(k) for k in diff["type_changes"]])

        return ConfigDiff(
            version_from=version_from,
            version_to=version_to,
            changes=dict(diff),
            added=added,
            removed=removed,
            modified=modified,
        )

    def rollback(
        self,
        config_name: str,
        target_version: str,
        author: str,
        message: Optional[str] = None,
    ) -> Optional[ConfigVersion]:
        """Rollback to a previous version.

        Args:
            config_name: Name of the configuration.
            target_version: Version ID to rollback to.
            author: Author of the rollback.
            message: Optional rollback message.

        Returns:
            New ConfigVersion representing the rollback, or None if failed.
        """
        target_config = self.get_config(config_name, target_version)
        if target_config is None:
            return None

        rollback_message = message or f"Rollback to {target_version}"
        return self.commit(
            config_name=config_name,
            config=target_config,
            author=author,
            message=rollback_message,
            metadata={"rollback_from": target_version},
        )

    def get_history(
        self,
        config_name: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get version history with details.

        Args:
            config_name: Name of the configuration.
            limit: Maximum number of entries to return.

        Returns:
            List of version history entries.
        """
        versions = self.list_versions(config_name)
        if limit:
            versions = versions[:limit]

        history = []
        for version in versions:
            entry = {
                "version_id": version.version_id,
                "timestamp": version.timestamp.isoformat(),
                "author": version.author,
                "message": version.message,
                "config_hash": version.config_hash,
            }
            if version.parent_version:
                entry["parent_version"] = version.parent_version
            history.append(entry)

        return history
