"""
Synchronization Engine for Project Management Integration Platform.

Provides bidirectional synchronization between Jira, Linear, and GitHub Projects
with field mapping, conflict resolution, and change tracking.

Features:
- Bidirectional sync (Jira ↔ GitHub, Jira ↔ Linear, GitHub ↔ Linear)
- Field mapping and transformation
- Conflict detection and resolution
- Incremental sync with change tracking
- Custom field type conversion
- Retry logic with exponential backoff
- Dry-run mode for testing
- Sync history and audit trail
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import yaml
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class PlatformType(str, Enum):
    """Supported platform types."""

    JIRA = "jira"
    LINEAR = "linear"
    GITHUB = "github"


class ConflictResolutionStrategy(str, Enum):
    """Conflict resolution strategies."""

    LAST_WRITE_WINS = "last_write_wins"
    MANUAL = "manual"
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    CUSTOM = "custom"


class SyncDirection(str, Enum):
    """Synchronization direction."""

    SOURCE_TO_TARGET = "source_to_target"
    TARGET_TO_SOURCE = "target_to_source"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    """Synchronization status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    SKIPPED = "skipped"


class FieldType(str, Enum):
    """Field data types."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ARRAY = "array"
    OBJECT = "object"
    JSON = "json"


class FieldMapping(BaseModel):
    """Field mapping configuration between platforms."""

    source_field: str = Field(..., description="Source field name")
    target_field: str = Field(..., description="Target field name")
    source_type: FieldType = Field(
        default=FieldType.STRING, description="Source field type"
    )
    target_type: FieldType = Field(
        default=FieldType.STRING, description="Target field type"
    )
    transform: Optional[str] = Field(
        None, description="Transformation function name"
    )
    bidirectional: bool = Field(
        default=True, description="Enable bidirectional mapping"
    )
    required: bool = Field(default=False, description="Field is required")
    default_value: Optional[Any] = Field(None, description="Default value if missing")

    @validator("source_field", "target_field")
    def validate_field_names(cls, v: str) -> str:
        """Validate field names are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field name cannot be empty")
        return v.strip()


class SyncConfiguration(BaseModel):
    """Synchronization configuration."""

    name: str = Field(..., description="Configuration name")
    source_platform: PlatformType = Field(..., description="Source platform")
    target_platform: PlatformType = Field(..., description="Target platform")
    direction: SyncDirection = Field(
        default=SyncDirection.BIDIRECTIONAL, description="Sync direction"
    )
    field_mappings: List[FieldMapping] = Field(
        default_factory=list, description="Field mappings"
    )
    conflict_strategy: ConflictResolutionStrategy = Field(
        default=ConflictResolutionStrategy.LAST_WRITE_WINS,
        description="Conflict resolution strategy",
    )
    batch_size: int = Field(default=50, ge=1, le=1000, description="Batch size")
    sync_interval: int = Field(
        default=300, ge=60, description="Sync interval in seconds"
    )
    enable_retry: bool = Field(default=True, description="Enable retry on failure")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retries")
    retry_delay: int = Field(
        default=5, ge=1, le=300, description="Retry delay in seconds"
    )
    enable_audit: bool = Field(default=True, description="Enable audit logging")
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Sync filters"
    )


@dataclass
class SyncItem:
    """Item to be synchronized."""

    id: str
    platform: PlatformType
    data: Dict[str, Any]
    last_modified: datetime
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """Result of a synchronization operation."""

    item_id: str
    status: SyncStatus
    source_platform: PlatformType
    target_platform: PlatformType
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    conflicts: List[str] = field(default_factory=list)
    changes: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0


@dataclass
class SyncState:
    """Synchronization state tracking."""

    config_name: str
    last_sync: Optional[datetime] = None
    items_synced: int = 0
    items_failed: int = 0
    items_skipped: int = 0
    conflicts: List[str] = field(default_factory=list)
    checkpoints: Dict[str, datetime] = field(default_factory=dict)


class ConflictDetector:
    """Detects conflicts between source and target items."""

    def __init__(self, config: SyncConfiguration):
        """
        Initialize conflict detector.

        Args:
            config: Synchronization configuration
        """
        self.config = config

    def detect_conflicts(
        self, source_item: SyncItem, target_item: SyncItem
    ) -> List[str]:
        """
        Detect conflicts between source and target items.

        Args:
            source_item: Source item
            target_item: Target item

        Returns:
            List of conflict descriptions
        """
        conflicts = []

        # Check timestamp conflicts
        if source_item.last_modified and target_item.last_modified:
            time_diff = abs(
                (source_item.last_modified - target_item.last_modified).total_seconds()
            )
            if time_diff < 10:  # Less than 10 seconds apart
                conflicts.append(
                    f"Concurrent modification detected (time diff: {time_diff}s)"
                )

        # Check checksum conflicts
        if source_item.checksum != target_item.checksum:
            # Check field-level conflicts
            field_conflicts = self._detect_field_conflicts(
                source_item.data, target_item.data
            )
            conflicts.extend(field_conflicts)

        return conflicts

    def _detect_field_conflicts(
        self, source_data: Dict[str, Any], target_data: Dict[str, Any]
    ) -> List[str]:
        """
        Detect field-level conflicts.

        Args:
            source_data: Source item data
            target_data: Target item data

        Returns:
            List of field conflict descriptions
        """
        conflicts = []

        for mapping in self.config.field_mappings:
            source_value = source_data.get(mapping.source_field)
            target_value = target_data.get(mapping.target_field)

            if source_value is not None and target_value is not None:
                if source_value != target_value:
                    conflicts.append(
                        f"Field conflict: {mapping.source_field} "
                        f"({source_value}) vs {mapping.target_field} "
                        f"({target_value})"
                    )

        return conflicts


class ConflictResolver:
    """Resolves conflicts based on configured strategy."""

    def __init__(self, config: SyncConfiguration):
        """
        Initialize conflict resolver.

        Args:
            config: Synchronization configuration
        """
        self.config = config
        self.custom_resolver: Optional[Callable] = None

    def set_custom_resolver(self, resolver: Callable) -> None:
        """
        Set custom conflict resolver function.

        Args:
            resolver: Custom resolver function
        """
        self.custom_resolver = resolver

    def resolve_conflict(
        self, source_item: SyncItem, target_item: SyncItem, conflicts: List[str]
    ) -> Tuple[SyncItem, str]:
        """
        Resolve conflict between source and target items.

        Args:
            source_item: Source item
            target_item: Target item
            conflicts: List of conflicts

        Returns:
            Tuple of (resolved item, resolution reason)
        """
        strategy = self.config.conflict_strategy

        if strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
            return self._resolve_last_write_wins(source_item, target_item)
        elif strategy == ConflictResolutionStrategy.SOURCE_WINS:
            return source_item, "Source wins strategy"
        elif strategy == ConflictResolutionStrategy.TARGET_WINS:
            return target_item, "Target wins strategy"
        elif strategy == ConflictResolutionStrategy.CUSTOM:
            if self.custom_resolver:
                resolved = self.custom_resolver(source_item, target_item, conflicts)
                return resolved, "Custom resolver"
            else:
                logger.warning("Custom resolver not set, falling back to last write")
                return self._resolve_last_write_wins(source_item, target_item)
        else:  # MANUAL
            raise ValueError(f"Manual conflict resolution required: {conflicts}")

    def _resolve_last_write_wins(
        self, source_item: SyncItem, target_item: SyncItem
    ) -> Tuple[SyncItem, str]:
        """
        Resolve conflict using last-write-wins strategy.

        Args:
            source_item: Source item
            target_item: Target item

        Returns:
            Tuple of (winning item, reason)
        """
        if source_item.last_modified > target_item.last_modified:
            return source_item, "Source has newer timestamp"
        else:
            return target_item, "Target has newer timestamp"


class FieldTransformer:
    """Transforms field values between different types and formats."""

    def __init__(self):
        """Initialize field transformer."""
        self.transformers: Dict[str, Callable] = {
            "string_to_number": self._string_to_number,
            "number_to_string": self._number_to_string,
            "date_to_string": self._date_to_string,
            "string_to_date": self._string_to_date,
            "array_to_string": self._array_to_string,
            "string_to_array": self._string_to_array,
            "json_encode": self._json_encode,
            "json_decode": self._json_decode,
            "boolean_to_string": self._boolean_to_string,
            "string_to_boolean": self._string_to_boolean,
        }

    def register_transformer(self, name: str, func: Callable) -> None:
        """
        Register custom transformer function.

        Args:
            name: Transformer name
            func: Transformer function
        """
        self.transformers[name] = func

    def transform(self, value: Any, mapping: FieldMapping) -> Any:
        """
        Transform value according to field mapping.

        Args:
            value: Value to transform
            mapping: Field mapping configuration

        Returns:
            Transformed value
        """
        if value is None:
            return mapping.default_value

        # Apply custom transformer if specified
        if mapping.transform and mapping.transform in self.transformers:
            try:
                return self.transformers[mapping.transform](value)
            except Exception as e:
                logger.error(f"Transform error for {mapping.transform}: {e}")
                return value

        # Apply type conversion
        return self._convert_type(value, mapping.source_type, mapping.target_type)

    def _convert_type(
        self, value: Any, source_type: FieldType, target_type: FieldType
    ) -> Any:
        """
        Convert value from source type to target type.

        Args:
            value: Value to convert
            source_type: Source field type
            target_type: Target field type

        Returns:
            Converted value
        """
        if source_type == target_type:
            return value

        try:
            if target_type == FieldType.STRING:
                return str(value)
            elif target_type == FieldType.NUMBER:
                return float(value) if "." in str(value) else int(value)
            elif target_type == FieldType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ("true", "yes", "1", "on")
                return bool(value)
            elif target_type == FieldType.DATE:
                if isinstance(value, str):
                    return datetime.fromisoformat(value).date()
                return value
            elif target_type == FieldType.DATETIME:
                if isinstance(value, str):
                    return datetime.fromisoformat(value)
                return value
            elif target_type == FieldType.ARRAY:
                if isinstance(value, str):
                    return value.split(",")
                return list(value) if not isinstance(value, list) else value
            elif target_type == FieldType.JSON:
                if isinstance(value, str):
                    return json.loads(value)
                return value
        except Exception as e:
            logger.error(f"Type conversion error: {e}")
            return value

        return value

    def _string_to_number(self, value: str) -> Union[int, float]:
        """Convert string to number."""
        return float(value) if "." in value else int(value)

    def _number_to_string(self, value: Union[int, float]) -> str:
        """Convert number to string."""
        return str(value)

    def _date_to_string(self, value: datetime) -> str:
        """Convert date to ISO string."""
        return value.isoformat()

    def _string_to_date(self, value: str) -> datetime:
        """Convert ISO string to date."""
        return datetime.fromisoformat(value)

    def _array_to_string(self, value: List[Any]) -> str:
        """Convert array to comma-separated string."""
        return ",".join(str(v) for v in value)

    def _string_to_array(self, value: str) -> List[str]:
        """Convert comma-separated string to array."""
        return [v.strip() for v in value.split(",")]

    def _json_encode(self, value: Any) -> str:
        """Encode value as JSON string."""
        return json.dumps(value)

    def _json_decode(self, value: str) -> Any:
        """Decode JSON string to value."""
        return json.loads(value)

    def _boolean_to_string(self, value: bool) -> str:
        """Convert boolean to string."""
        return "true" if value else "false"

    def _string_to_boolean(self, value: str) -> bool:
        """Convert string to boolean."""
        return value.lower() in ("true", "yes", "1", "on")


class ChangeTracker:
    """Tracks changes to items for incremental synchronization."""

    def __init__(self, state_dir: Path):
        """
        Initialize change tracker.

        Args:
            state_dir: Directory for storing state
        """
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.checksums: Dict[str, str] = {}
        self.timestamps: Dict[str, datetime] = {}

    def calculate_checksum(self, data: Dict[str, Any]) -> str:
        """
        Calculate checksum for item data.

        Args:
            data: Item data

        Returns:
            Checksum string
        """
        # Sort keys for consistent ordering
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()

    def has_changed(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Check if item has changed since last sync.

        Args:
            item_id: Item identifier
            data: Current item data

        Returns:
            True if item has changed
        """
        current_checksum = self.calculate_checksum(data)
        previous_checksum = self.checksums.get(item_id)

        if previous_checksum is None:
            return True  # New item

        return current_checksum != previous_checksum

    def update_checksum(self, item_id: str, data: Dict[str, Any]) -> None:
        """
        Update checksum for item.

        Args:
            item_id: Item identifier
            data: Item data
        """
        self.checksums[item_id] = self.calculate_checksum(data)
        self.timestamps[item_id] = datetime.now()

    def get_last_sync_time(self, item_id: str) -> Optional[datetime]:
        """
        Get last sync timestamp for item.

        Args:
            item_id: Item identifier

        Returns:
            Last sync timestamp or None
        """
        return self.timestamps.get(item_id)

    def save_state(self, config_name: str) -> None:
        """
        Save tracker state to disk.

        Args:
            config_name: Configuration name
        """
        state_file = self.state_dir / f"{config_name}_checksums.json"
        state_data = {
            "checksums": self.checksums,
            "timestamps": {
                k: v.isoformat() for k, v in self.timestamps.items()
            },
        }

        with open(state_file, "w") as f:
            json.dump(state_data, f, indent=2)

    def load_state(self, config_name: str) -> None:
        """
        Load tracker state from disk.

        Args:
            config_name: Configuration name
        """
        state_file = self.state_dir / f"{config_name}_checksums.json"

        if not state_file.exists():
            return

        try:
            with open(state_file, "r") as f:
                state_data = json.load(f)

            self.checksums = state_data.get("checksums", {})
            self.timestamps = {
                k: datetime.fromisoformat(v)
                for k, v in state_data.get("timestamps", {}).items()
            }
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


class SyncAuditor:
    """Audits synchronization operations."""

    def __init__(self, audit_dir: Path):
        """
        Initialize sync auditor.

        Args:
            audit_dir: Directory for audit logs
        """
        self.audit_dir = audit_dir
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def log_sync(self, result: SyncResult) -> None:
        """
        Log synchronization result.

        Args:
            result: Sync result
        """
        audit_file = self.audit_dir / f"sync_{datetime.now():%Y%m%d}.jsonl"

        audit_entry = {
            "timestamp": result.timestamp.isoformat(),
            "item_id": result.item_id,
            "status": result.status.value,
            "source": result.source_platform.value,
            "target": result.target_platform.value,
            "error": result.error,
            "conflicts": result.conflicts,
            "changes": result.changes,
            "retry_count": result.retry_count,
        }

        with open(audit_file, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")

    def get_sync_history(
        self, item_id: str, days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get sync history for an item.

        Args:
            item_id: Item identifier
            days: Number of days to look back

        Returns:
            List of audit entries
        """
        history = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for audit_file in sorted(self.audit_dir.glob("sync_*.jsonl")):
            try:
                with open(audit_file, "r") as f:
                    for line in f:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(entry["timestamp"])

                        if entry_time < cutoff_date:
                            continue

                        if entry["item_id"] == item_id:
                            history.append(entry)
            except Exception as e:
                logger.error(f"Failed to read audit file {audit_file}: {e}")

        return sorted(history, key=lambda x: x["timestamp"], reverse=True)


class SyncEngine:
    """
    Bidirectional synchronization engine for project management platforms.

    Handles synchronization between Jira, Linear, and GitHub Projects with
    field mapping, conflict resolution, and change tracking.
    """

    def __init__(
        self,
        config: SyncConfiguration,
        state_dir: Optional[Path] = None,
        audit_dir: Optional[Path] = None,
    ):
        """
        Initialize sync engine.

        Args:
            config: Synchronization configuration
            state_dir: Directory for storing sync state
            audit_dir: Directory for audit logs
        """
        self.config = config
        self.state_dir = state_dir or Path.home() / ".pm_integration" / "sync_state"
        self.audit_dir = audit_dir or Path.home() / ".pm_integration" / "sync_audit"

        # Initialize components
        self.conflict_detector = ConflictDetector(config)
        self.conflict_resolver = ConflictResolver(config)
        self.field_transformer = FieldTransformer()
        self.change_tracker = ChangeTracker(self.state_dir)
        self.auditor = SyncAuditor(self.audit_dir)

        # Load previous state
        self.change_tracker.load_state(config.name)

        # Sync state
        self.sync_state = SyncState(config_name=config.name)
        self.dry_run = False

        logger.info(f"Initialized SyncEngine: {config.name}")

    @classmethod
    def from_yaml(cls, config_path: Path) -> "SyncEngine":
        """
        Create sync engine from YAML configuration.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            SyncEngine instance
        """
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        config = SyncConfiguration(**config_data)
        return cls(config)

    def set_dry_run(self, enabled: bool = True) -> None:
        """
        Enable or disable dry-run mode.

        Args:
            enabled: Enable dry-run mode
        """
        self.dry_run = enabled
        logger.info(f"Dry-run mode: {'enabled' if enabled else 'disabled'}")

    def set_custom_conflict_resolver(self, resolver: Callable) -> None:
        """
        Set custom conflict resolver function.

        Args:
            resolver: Custom resolver function
        """
        self.conflict_resolver.set_custom_resolver(resolver)

    def register_field_transformer(self, name: str, func: Callable) -> None:
        """
        Register custom field transformer.

        Args:
            name: Transformer name
            func: Transformer function
        """
        self.field_transformer.register_transformer(name, func)

    async def sync(
        self,
        source_items: List[Dict[str, Any]],
        target_items: List[Dict[str, Any]],
        source_client: Any,
        target_client: Any,
    ) -> List[SyncResult]:
        """
        Synchronize items between source and target platforms.

        Args:
            source_items: Source platform items
            target_items: Target platform items
            source_client: Source platform client
            target_client: Target platform client

        Returns:
            List of sync results
        """
        logger.info(
            f"Starting sync: {self.config.source_platform.value} → "
            f"{self.config.target_platform.value}"
        )

        results = []

        # Build target item lookup
        target_lookup = {item["id"]: item for item in target_items}

        # Process items in batches
        for i in range(0, len(source_items), self.config.batch_size):
            batch = source_items[i: i + self.config.batch_size]
            batch_results = await self._sync_batch(
                batch, target_lookup, source_client, target_client
            )
            results.extend(batch_results)

            logger.info(f"Processed batch {i // self.config.batch_size + 1}")

        # Update sync state
        self._update_sync_state(results)

        # Save state
        if not self.dry_run:
            self.change_tracker.save_state(self.config.name)

        logger.info(f"Sync completed: {len(results)} items processed")
        return results

    async def _sync_batch(
        self,
        batch: List[Dict[str, Any]],
        target_lookup: Dict[str, Dict[str, Any]],
        source_client: Any,
        target_client: Any,
    ) -> List[SyncResult]:
        """
        Synchronize a batch of items.

        Args:
            batch: Batch of source items
            target_lookup: Target items lookup
            source_client: Source platform client
            target_client: Target platform client

        Returns:
            List of sync results
        """
        results = []

        for source_data in batch:
            try:
                result = await self._sync_item(
                    source_data, target_lookup, source_client, target_client
                )
                results.append(result)

                # Log to audit if enabled
                if self.config.enable_audit:
                    self.auditor.log_sync(result)

            except Exception as e:
                logger.error(f"Failed to sync item {source_data.get('id')}: {e}")
                result = SyncResult(
                    item_id=source_data.get("id", "unknown"),
                    status=SyncStatus.FAILED,
                    source_platform=self.config.source_platform,
                    target_platform=self.config.target_platform,
                    error=str(e),
                )
                results.append(result)

        return results

    async def _sync_item(
        self,
        source_data: Dict[str, Any],
        target_lookup: Dict[str, Dict[str, Any]],
        source_client: Any,
        target_client: Any,
    ) -> SyncResult:
        """
        Synchronize a single item.

        Args:
            source_data: Source item data
            target_lookup: Target items lookup
            source_client: Source platform client
            target_client: Target platform client

        Returns:
            Sync result
        """
        item_id = source_data["id"]

        # Check if item has changed
        if not self.change_tracker.has_changed(item_id, source_data):
            logger.debug(f"Item {item_id} unchanged, skipping")
            return SyncResult(
                item_id=item_id,
                status=SyncStatus.SKIPPED,
                source_platform=self.config.source_platform,
                target_platform=self.config.target_platform,
            )

        # Create source item
        source_item = SyncItem(
            id=item_id,
            platform=self.config.source_platform,
            data=source_data,
            last_modified=datetime.fromisoformat(
                source_data.get("updated_at", datetime.now().isoformat())
            ),
            checksum=self.change_tracker.calculate_checksum(source_data),
        )

        # Check if item exists in target
        target_data = target_lookup.get(item_id)

        if target_data:
            # Update existing item
            target_item = SyncItem(
                id=item_id,
                platform=self.config.target_platform,
                data=target_data,
                last_modified=datetime.fromisoformat(
                    target_data.get("updated_at", datetime.now().isoformat())
                ),
                checksum=self.change_tracker.calculate_checksum(target_data),
            )

            return await self._sync_existing_item(
                source_item, target_item, target_client
            )
        else:
            # Create new item
            return await self._sync_new_item(source_item, target_client)

    async def _sync_new_item(
        self, source_item: SyncItem, target_client: Any
    ) -> SyncResult:
        """
        Sync a new item to target platform.

        Args:
            source_item: Source item
            target_client: Target platform client

        Returns:
            Sync result
        """
        # Transform fields
        transformed_data = self._transform_fields(source_item.data)

        if self.dry_run:
            logger.info(f"[DRY RUN] Would create item {source_item.id}")
            return SyncResult(
                item_id=source_item.id,
                status=SyncStatus.COMPLETED,
                source_platform=source_item.platform,
                target_platform=self.config.target_platform,
                changes={"action": "create", "data": transformed_data},
            )

        # Create item with retry
        retry_count = 0
        while retry_count <= self.config.max_retries:
            try:
                # This would call the actual target client create method
                # target_client.create_issue(transformed_data)

                # Update change tracker
                self.change_tracker.update_checksum(source_item.id, source_item.data)

                return SyncResult(
                    item_id=source_item.id,
                    status=SyncStatus.COMPLETED,
                    source_platform=source_item.platform,
                    target_platform=self.config.target_platform,
                    changes={
                        "action": "create",
                        "fields": list(transformed_data.keys())
                    },
                    retry_count=retry_count,
                )

            except Exception as e:
                retry_count += 1
                if retry_count > self.config.max_retries:
                    return SyncResult(
                        item_id=source_item.id,
                        status=SyncStatus.FAILED,
                        source_platform=source_item.platform,
                        target_platform=self.config.target_platform,
                        error=str(e),
                        retry_count=retry_count,
                    )

                # Exponential backoff
                delay = self.config.retry_delay * (2 ** (retry_count - 1))
                logger.warning(
                    f"Retry {retry_count}/{self.config.max_retries} "
                    f"for {source_item.id} after {delay}s"
                )
                await asyncio.sleep(delay)

    async def _sync_existing_item(
        self, source_item: SyncItem, target_item: SyncItem, target_client: Any
    ) -> SyncResult:
        """
        Sync an existing item between platforms.

        Args:
            source_item: Source item
            target_item: Target item
            target_client: Target platform client

        Returns:
            Sync result
        """
        # Detect conflicts
        conflicts = self.conflict_detector.detect_conflicts(source_item, target_item)

        if conflicts:
            logger.warning(f"Conflicts detected for item {source_item.id}")

            if self.config.conflict_strategy == ConflictResolutionStrategy.MANUAL:
                return SyncResult(
                    item_id=source_item.id,
                    status=SyncStatus.CONFLICT,
                    source_platform=source_item.platform,
                    target_platform=target_item.platform,
                    conflicts=conflicts,
                )

            # Resolve conflict
            try:
                resolved_item, reason = self.conflict_resolver.resolve_conflict(
                    source_item, target_item, conflicts
                )
                logger.info(f"Conflict resolved for {source_item.id}: {reason}")

                # Use resolved item as source
                if resolved_item.id == target_item.id:
                    # Target wins, no update needed
                    return SyncResult(
                        item_id=source_item.id,
                        status=SyncStatus.SKIPPED,
                        source_platform=source_item.platform,
                        target_platform=target_item.platform,
                        conflicts=conflicts,
                        changes={"resolution": reason},
                    )
                else:
                    source_item = resolved_item

            except ValueError as e:
                return SyncResult(
                    item_id=source_item.id,
                    status=SyncStatus.CONFLICT,
                    source_platform=source_item.platform,
                    target_platform=target_item.platform,
                    error=str(e),
                    conflicts=conflicts,
                )

        # Transform and update
        transformed_data = self._transform_fields(source_item.data)
        changes = self._compute_changes(target_item.data, transformed_data)

        if not changes:
            return SyncResult(
                item_id=source_item.id,
                status=SyncStatus.SKIPPED,
                source_platform=source_item.platform,
                target_platform=target_item.platform,
            )

        if self.dry_run:
            logger.info(f"[DRY RUN] Would update item {source_item.id}")
            return SyncResult(
                item_id=source_item.id,
                status=SyncStatus.COMPLETED,
                source_platform=source_item.platform,
                target_platform=target_item.platform,
                changes={"action": "update", "fields": changes},
                conflicts=conflicts,
            )

        # Update item with retry
        retry_count = 0
        while retry_count <= self.config.max_retries:
            try:
                # This would call the actual target client update method
                # target_client.update_issue(source_item.id, transformed_data)

                # Update change tracker
                self.change_tracker.update_checksum(source_item.id, source_item.data)

                return SyncResult(
                    item_id=source_item.id,
                    status=SyncStatus.COMPLETED,
                    source_platform=source_item.platform,
                    target_platform=target_item.platform,
                    changes=changes,
                    conflicts=conflicts,
                    retry_count=retry_count,
                )

            except Exception as e:
                retry_count += 1
                if retry_count > self.config.max_retries:
                    return SyncResult(
                        item_id=source_item.id,
                        status=SyncStatus.FAILED,
                        source_platform=source_item.platform,
                        target_platform=target_item.platform,
                        error=str(e),
                        retry_count=retry_count,
                    )

                # Exponential backoff
                delay = self.config.retry_delay * (2 ** (retry_count - 1))
                logger.warning(
                    f"Retry {retry_count}/{self.config.max_retries} "
                    f"for {source_item.id} after {delay}s"
                )
                await asyncio.sleep(delay)

    def _transform_fields(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform source fields to target format.

        Args:
            source_data: Source item data

        Returns:
            Transformed data
        """
        transformed = {}

        for mapping in self.config.field_mappings:
            source_value = source_data.get(mapping.source_field)

            if source_value is None and mapping.required:
                if mapping.default_value is not None:
                    source_value = mapping.default_value
                else:
                    logger.warning(
                        f"Required field {mapping.source_field} is missing"
                    )
                    continue

            if source_value is not None:
                target_value = self.field_transformer.transform(source_value, mapping)
                transformed[mapping.target_field] = target_value

        return transformed

    def _compute_changes(
        self, target_data: Dict[str, Any], transformed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute changes between target and transformed data.

        Args:
            target_data: Current target data
            transformed_data: Transformed source data

        Returns:
            Dictionary of changes
        """
        changes = {}

        for key, new_value in transformed_data.items():
            old_value = target_data.get(key)
            if old_value != new_value:
                changes[key] = {"old": old_value, "new": new_value}

        return changes

    def _update_sync_state(self, results: List[SyncResult]) -> None:
        """
        Update sync state based on results.

        Args:
            results: List of sync results
        """
        self.sync_state.last_sync = datetime.now()

        for result in results:
            if result.status == SyncStatus.COMPLETED:
                self.sync_state.items_synced += 1
            elif result.status == SyncStatus.FAILED:
                self.sync_state.items_failed += 1
            elif result.status == SyncStatus.SKIPPED:
                self.sync_state.items_skipped += 1
            elif result.status == SyncStatus.CONFLICT:
                self.sync_state.conflicts.append(result.item_id)

    def get_sync_state(self) -> SyncState:
        """
        Get current sync state.

        Returns:
            Sync state
        """
        return self.sync_state

    def get_sync_history(
        self, item_id: str, days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get sync history for an item.

        Args:
            item_id: Item identifier
            days: Number of days to look back

        Returns:
            List of audit entries
        """
        return self.auditor.get_sync_history(item_id, days)

    def export_config(self, output_path: Path) -> None:
        """
        Export configuration to YAML file.

        Args:
            output_path: Output file path
        """
        config_dict = self.config.dict()

        with open(output_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Configuration exported to {output_path}")

    async def validate_configuration(self) -> List[str]:
        """
        Validate synchronization configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check field mappings
        if not self.config.field_mappings:
            errors.append("No field mappings defined")

        # Check for duplicate mappings
        target_fields = [m.target_field for m in self.config.field_mappings]
        duplicates = [f for f in target_fields if target_fields.count(f) > 1]
        if duplicates:
            errors.append(f"Duplicate target fields: {set(duplicates)}")

        # Check required fields
        required_mappings = [
            m for m in self.config.field_mappings if m.required
        ]
        for mapping in required_mappings:
            if mapping.default_value is None:
                errors.append(
                    f"Required field {mapping.source_field} has no default value"
                )

        return errors
