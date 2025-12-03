"""
Comprehensive tests for Synchronization Engine.

Tests field mapping, conflict resolution, change tracking, and synchronization.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from sync_engine import (
    ChangeTracker,
    ConflictDetector,
    ConflictResolutionStrategy,
    ConflictResolver,
    FieldMapping,
    FieldTransformer,
    FieldType,
    PlatformType,
    SyncAuditor,
    SyncConfiguration,
    SyncDirection,
    SyncEngine,
    SyncItem,
    SyncResult,
    SyncStatus,
)


class TestFieldMapping:
    """Test field mapping configuration."""

    def test_field_mapping_creation(self):
        """Test creating field mapping."""
        mapping = FieldMapping(
            source_field="summary",
            target_field="title",
            source_type=FieldType.STRING,
            target_type=FieldType.STRING,
        )

        assert mapping.source_field == "summary"
        assert mapping.target_field == "title"
        assert mapping.bidirectional is True
        assert mapping.required is False

    def test_field_mapping_validation(self):
        """Test field mapping validation."""
        with pytest.raises(ValueError):
            FieldMapping(
                source_field="",
                target_field="title",
            )

        with pytest.raises(ValueError):
            FieldMapping(
                source_field="summary",
                target_field="   ",
            )


class TestFieldTransformer:
    """Test field transformation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = FieldTransformer()

    def test_string_to_number(self):
        """Test string to number transformation."""
        result = self.transformer._string_to_number("42")
        assert result == 42
        assert isinstance(result, int)

        result = self.transformer._string_to_number("3.14")
        assert result == 3.14
        assert isinstance(result, float)

    def test_number_to_string(self):
        """Test number to string transformation."""
        assert self.transformer._number_to_string(42) == "42"
        assert self.transformer._number_to_string(3.14) == "3.14"

    def test_array_to_string(self):
        """Test array to string transformation."""
        result = self.transformer._array_to_string(["bug", "urgent", "backend"])
        assert result == "bug,urgent,backend"

    def test_string_to_array(self):
        """Test string to array transformation."""
        result = self.transformer._string_to_array("bug, urgent, backend")
        assert result == ["bug", "urgent", "backend"]

    def test_boolean_transformations(self):
        """Test boolean transformations."""
        assert self.transformer._boolean_to_string(True) == "true"
        assert self.transformer._boolean_to_string(False) == "false"

        assert self.transformer._string_to_boolean("true") is True
        assert self.transformer._string_to_boolean("yes") is True
        assert self.transformer._string_to_boolean("1") is True
        assert self.transformer._string_to_boolean("false") is False

    def test_json_transformations(self):
        """Test JSON transformations."""
        data = {"key": "value", "number": 42}
        encoded = self.transformer._json_encode(data)
        assert isinstance(encoded, str)

        decoded = self.transformer._json_decode(encoded)
        assert decoded == data

    def test_type_conversion(self):
        """Test type conversion."""
        # String to number
        result = self.transformer._convert_type(
            "42", FieldType.STRING, FieldType.NUMBER
        )
        assert result == 42

        # Number to string
        result = self.transformer._convert_type(
            42, FieldType.NUMBER, FieldType.STRING
        )
        assert result == "42"

        # String to boolean
        result = self.transformer._convert_type(
            "true", FieldType.STRING, FieldType.BOOLEAN
        )
        assert result is True

        # Array to string
        result = self.transformer._convert_type(
            ["a", "b"], FieldType.ARRAY, FieldType.STRING
        )
        assert isinstance(result, str)

    def test_transform_with_mapping(self):
        """Test transformation with field mapping."""
        mapping = FieldMapping(
            source_field="priority",
            target_field="priority_level",
            source_type=FieldType.NUMBER,
            target_type=FieldType.STRING,
        )

        result = self.transformer.transform(1, mapping)
        assert result == "1"

    def test_transform_with_default_value(self):
        """Test transformation with default value."""
        mapping = FieldMapping(
            source_field="status",
            target_field="state",
            default_value="open",
        )

        result = self.transformer.transform(None, mapping)
        assert result == "open"

    def test_custom_transformer(self):
        """Test custom transformer registration."""
        def double_number(value: int) -> int:
            return value * 2

        self.transformer.register_transformer("double", double_number)

        mapping = FieldMapping(
            source_field="count",
            target_field="doubled_count",
            transform="double",
        )

        result = self.transformer.transform(5, mapping)
        assert result == 10


class TestConflictDetection:
    """Test conflict detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = SyncConfiguration(
            name="test-sync",
            source_platform=PlatformType.JIRA,
            target_platform=PlatformType.GITHUB,
            field_mappings=[
                FieldMapping(
                    source_field="summary",
                    target_field="title",
                ),
                FieldMapping(
                    source_field="status",
                    target_field="state",
                ),
            ],
        )
        self.detector = ConflictDetector(self.config)

    def test_no_conflicts(self):
        """Test when there are no conflicts."""
        source_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.JIRA,
            data={"summary": "Test issue", "status": "open"},
            last_modified=datetime.now(),
            checksum="abc123",
        )

        target_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.GITHUB,
            data={"title": "Test issue", "state": "open"},
            last_modified=datetime.now() - timedelta(hours=1),
            checksum="abc123",
        )

        conflicts = self.detector.detect_conflicts(source_item, target_item)
        assert len(conflicts) == 0

    def test_timestamp_conflict(self):
        """Test concurrent modification detection."""
        now = datetime.now()

        source_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.JIRA,
            data={"summary": "Test issue"},
            last_modified=now,
            checksum="abc123",
        )

        target_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.GITHUB,
            data={"title": "Test issue"},
            last_modified=now + timedelta(seconds=5),
            checksum="def456",
        )

        conflicts = self.detector.detect_conflicts(source_item, target_item)
        assert len(conflicts) > 0
        assert "Concurrent modification" in conflicts[0]

    def test_field_conflict(self):
        """Test field-level conflict detection."""
        source_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.JIRA,
            data={"summary": "Original title", "status": "open"},
            last_modified=datetime.now(),
            checksum="abc123",
        )

        target_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.GITHUB,
            data={"title": "Modified title", "state": "closed"},
            last_modified=datetime.now() - timedelta(hours=1),
            checksum="def456",
        )

        conflicts = self.detector.detect_conflicts(source_item, target_item)
        assert len(conflicts) > 0


class TestConflictResolution:
    """Test conflict resolution strategies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = SyncConfiguration(
            name="test-sync",
            source_platform=PlatformType.JIRA,
            target_platform=PlatformType.GITHUB,
        )
        self.resolver = ConflictResolver(self.config)

    def test_last_write_wins(self):
        """Test last-write-wins strategy."""
        self.config.conflict_strategy = ConflictResolutionStrategy.LAST_WRITE_WINS

        source_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.JIRA,
            data={"summary": "Source"},
            last_modified=datetime.now(),
            checksum="abc",
        )

        target_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.GITHUB,
            data={"title": "Target"},
            last_modified=datetime.now() - timedelta(hours=1),
            checksum="def",
        )

        resolved, reason = self.resolver.resolve_conflict(
            source_item, target_item, []
        )

        assert resolved.id == source_item.id
        assert "newer timestamp" in reason.lower()

    def test_source_wins(self):
        """Test source-wins strategy."""
        self.config.conflict_strategy = ConflictResolutionStrategy.SOURCE_WINS

        source_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.JIRA,
            data={"summary": "Source"},
            last_modified=datetime.now() - timedelta(hours=1),
            checksum="abc",
        )

        target_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.GITHUB,
            data={"title": "Target"},
            last_modified=datetime.now(),
            checksum="def",
        )

        resolved, reason = self.resolver.resolve_conflict(
            source_item, target_item, []
        )

        assert resolved.id == source_item.id
        assert reason == "Source wins strategy"

    def test_target_wins(self):
        """Test target-wins strategy."""
        self.config.conflict_strategy = ConflictResolutionStrategy.TARGET_WINS

        source_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.JIRA,
            data={"summary": "Source"},
            last_modified=datetime.now(),
            checksum="abc",
        )

        target_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.GITHUB,
            data={"title": "Target"},
            last_modified=datetime.now() - timedelta(hours=1),
            checksum="def",
        )

        resolved, reason = self.resolver.resolve_conflict(
            source_item, target_item, []
        )

        assert resolved.id == target_item.id
        assert reason == "Target wins strategy"

    def test_manual_resolution(self):
        """Test manual resolution strategy."""
        self.config.conflict_strategy = ConflictResolutionStrategy.MANUAL

        source_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.JIRA,
            data={"summary": "Source"},
            last_modified=datetime.now(),
            checksum="abc",
        )

        target_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.GITHUB,
            data={"title": "Target"},
            last_modified=datetime.now(),
            checksum="def",
        )

        with pytest.raises(ValueError, match="Manual conflict resolution required"):
            self.resolver.resolve_conflict(
                source_item, target_item, ["conflict"]
            )

    def test_custom_resolver(self):
        """Test custom resolver function."""
        self.config.conflict_strategy = ConflictResolutionStrategy.CUSTOM

        def custom_resolver(source, target, conflicts):
            # Always prefer source with specific condition
            return source

        self.resolver.set_custom_resolver(custom_resolver)

        source_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.JIRA,
            data={"summary": "Source"},
            last_modified=datetime.now(),
            checksum="abc",
        )

        target_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.GITHUB,
            data={"title": "Target"},
            last_modified=datetime.now(),
            checksum="def",
        )

        resolved, reason = self.resolver.resolve_conflict(
            source_item, target_item, []
        )

        assert resolved.id == source_item.id
        assert reason == "Custom resolver"


class TestChangeTracker:
    """Test change tracking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = ChangeTracker(Path(self.temp_dir))

    def test_checksum_calculation(self):
        """Test checksum calculation."""
        data1 = {"key": "value", "number": 42}
        data2 = {"number": 42, "key": "value"}  # Different order
        data3 = {"key": "value", "number": 43}  # Different value

        checksum1 = self.tracker.calculate_checksum(data1)
        checksum2 = self.tracker.calculate_checksum(data2)
        checksum3 = self.tracker.calculate_checksum(data3)

        # Same data, different order should produce same checksum
        assert checksum1 == checksum2

        # Different data should produce different checksum
        assert checksum1 != checksum3

    def test_change_detection(self):
        """Test change detection."""
        item_id = "ISSUE-1"
        data1 = {"summary": "Original"}
        data2 = {"summary": "Modified"}

        # First check - should be changed (new item)
        assert self.tracker.has_changed(item_id, data1) is True

        # Update checksum
        self.tracker.update_checksum(item_id, data1)

        # Second check with same data - should not be changed
        assert self.tracker.has_changed(item_id, data1) is False

        # Third check with different data - should be changed
        assert self.tracker.has_changed(item_id, data2) is True

    def test_timestamp_tracking(self):
        """Test timestamp tracking."""
        item_id = "ISSUE-1"
        data = {"summary": "Test"}

        # Initially no timestamp
        assert self.tracker.get_last_sync_time(item_id) is None

        # Update and check timestamp
        self.tracker.update_checksum(item_id, data)
        timestamp = self.tracker.get_last_sync_time(item_id)

        assert timestamp is not None
        assert isinstance(timestamp, datetime)

    def test_state_persistence(self):
        """Test saving and loading state."""
        item_id = "ISSUE-1"
        data = {"summary": "Test"}
        config_name = "test-config"

        # Update and save
        self.tracker.update_checksum(item_id, data)
        self.tracker.save_state(config_name)

        # Create new tracker and load
        new_tracker = ChangeTracker(Path(self.temp_dir))
        new_tracker.load_state(config_name)

        # Verify state was loaded
        assert new_tracker.checksums.get(item_id) == self.tracker.checksums[item_id]
        assert item_id in new_tracker.timestamps


class TestSyncAuditor:
    """Test sync auditing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.auditor = SyncAuditor(Path(self.temp_dir))

    def test_log_sync(self):
        """Test logging sync result."""
        result = SyncResult(
            item_id="ISSUE-1",
            status=SyncStatus.COMPLETED,
            source_platform=PlatformType.JIRA,
            target_platform=PlatformType.GITHUB,
            changes={"title": {"old": "Old", "new": "New"}},
        )

        self.auditor.log_sync(result)

        # Verify audit file was created
        audit_files = list(Path(self.temp_dir).glob("sync_*.jsonl"))
        assert len(audit_files) == 1

        # Verify content
        with open(audit_files[0], "r") as f:
            entry = json.loads(f.readline())
            assert entry["item_id"] == "ISSUE-1"
            assert entry["status"] == "completed"

    def test_get_sync_history(self):
        """Test retrieving sync history."""
        # Log multiple results
        for i in range(3):
            result = SyncResult(
                item_id="ISSUE-1",
                status=SyncStatus.COMPLETED,
                source_platform=PlatformType.JIRA,
                target_platform=PlatformType.GITHUB,
            )
            self.auditor.log_sync(result)

        # Get history
        history = self.auditor.get_sync_history("ISSUE-1", days=7)
        assert len(history) == 3


class TestSyncEngine:
    """Test sync engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = SyncConfiguration(
            name="test-sync",
            source_platform=PlatformType.JIRA,
            target_platform=PlatformType.GITHUB,
            field_mappings=[
                FieldMapping(
                    source_field="summary",
                    target_field="title",
                ),
                FieldMapping(
                    source_field="description",
                    target_field="body",
                ),
                FieldMapping(
                    source_field="status",
                    target_field="state",
                ),
            ],
            batch_size=10,
        )
        self.engine = SyncEngine(
            self.config,
            state_dir=Path(self.temp_dir) / "state",
            audit_dir=Path(self.temp_dir) / "audit",
        )

    def test_engine_initialization(self):
        """Test engine initialization."""
        assert self.engine.config.name == "test-sync"
        assert self.engine.dry_run is False
        assert isinstance(self.engine.conflict_detector, ConflictDetector)
        assert isinstance(self.engine.conflict_resolver, ConflictResolver)
        assert isinstance(self.engine.field_transformer, FieldTransformer)

    def test_dry_run_mode(self):
        """Test dry-run mode."""
        self.engine.set_dry_run(True)
        assert self.engine.dry_run is True

        self.engine.set_dry_run(False)
        assert self.engine.dry_run is False

    def test_field_transformation(self):
        """Test field transformation."""
        source_data = {
            "summary": "Test Issue",
            "description": "Test description",
            "status": "open",
            "extra_field": "ignored",
        }

        transformed = self.engine._transform_fields(source_data)

        assert "title" in transformed
        assert transformed["title"] == "Test Issue"
        assert "body" in transformed
        assert transformed["body"] == "Test description"
        assert "state" in transformed
        assert "extra_field" not in transformed

    def test_compute_changes(self):
        """Test computing changes."""
        target_data = {
            "title": "Old Title",
            "body": "Old Body",
            "state": "open",
        }

        transformed_data = {
            "title": "New Title",
            "body": "Old Body",  # No change
            "state": "closed",
        }

        changes = self.engine._compute_changes(target_data, transformed_data)

        assert "title" in changes
        assert changes["title"]["old"] == "Old Title"
        assert changes["title"]["new"] == "New Title"

        assert "body" not in changes  # No change

        assert "state" in changes

    @pytest.mark.asyncio
    async def test_sync_new_item_dry_run(self):
        """Test syncing new item in dry-run mode."""
        self.engine.set_dry_run(True)

        source_item = SyncItem(
            id="ISSUE-1",
            platform=PlatformType.JIRA,
            data={
                "summary": "Test Issue",
                "description": "Description",
                "status": "open",
                "updated_at": datetime.now().isoformat(),
            },
            last_modified=datetime.now(),
            checksum="abc123",
        )

        result = await self.engine._sync_new_item(source_item, None)

        assert result.status == SyncStatus.COMPLETED
        assert result.item_id == "ISSUE-1"
        assert "create" in result.changes["action"]

    @pytest.mark.asyncio
    async def test_validation(self):
        """Test configuration validation."""
        # Valid configuration
        errors = await self.engine.validate_configuration()
        assert len(errors) == 0

        # Invalid configuration - no mappings
        invalid_config = SyncConfiguration(
            name="invalid",
            source_platform=PlatformType.JIRA,
            target_platform=PlatformType.GITHUB,
            field_mappings=[],
        )
        invalid_engine = SyncEngine(invalid_config)
        errors = await invalid_engine.validate_configuration()
        assert len(errors) > 0
        assert "No field mappings" in errors[0]

    def test_config_export(self):
        """Test configuration export."""
        output_path = Path(self.temp_dir) / "config.yaml"
        self.engine.export_config(output_path)

        assert output_path.exists()

        # Verify we can load it back
        with open(output_path, "r") as f:
            import yaml
            config_data = yaml.safe_load(f)
            assert config_data["name"] == "test-sync"

    def test_sync_state_tracking(self):
        """Test sync state tracking."""
        results = [
            SyncResult(
                item_id="ISSUE-1",
                status=SyncStatus.COMPLETED,
                source_platform=PlatformType.JIRA,
                target_platform=PlatformType.GITHUB,
            ),
            SyncResult(
                item_id="ISSUE-2",
                status=SyncStatus.FAILED,
                source_platform=PlatformType.JIRA,
                target_platform=PlatformType.GITHUB,
                error="Test error",
            ),
            SyncResult(
                item_id="ISSUE-3",
                status=SyncStatus.SKIPPED,
                source_platform=PlatformType.JIRA,
                target_platform=PlatformType.GITHUB,
            ),
        ]

        self.engine._update_sync_state(results)

        state = self.engine.get_sync_state()
        assert state.items_synced == 1
        assert state.items_failed == 1
        assert state.items_skipped == 1
        assert state.last_sync is not None


class TestSyncConfiguration:
    """Test sync configuration."""

    def test_config_creation(self):
        """Test creating configuration."""
        config = SyncConfiguration(
            name="test",
            source_platform=PlatformType.JIRA,
            target_platform=PlatformType.GITHUB,
            direction=SyncDirection.BIDIRECTIONAL,
        )

        assert config.name == "test"
        assert config.batch_size == 50
        assert config.enable_retry is True
        assert config.max_retries == 3

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = SyncConfiguration(
            name="test",
            source_platform=PlatformType.JIRA,
            target_platform=PlatformType.GITHUB,
            batch_size=100,
            max_retries=5,
        )
        assert config.batch_size == 100
        assert config.max_retries == 5

        # Invalid batch size
        with pytest.raises(ValueError):
            SyncConfiguration(
                name="test",
                source_platform=PlatformType.JIRA,
                target_platform=PlatformType.GITHUB,
                batch_size=2000,  # Too large
            )

        # Invalid retry count
        with pytest.raises(ValueError):
            SyncConfiguration(
                name="test",
                source_platform=PlatformType.JIRA,
                target_platform=PlatformType.GITHUB,
                max_retries=20,  # Too many
            )


def test_sync_from_yaml():
    """Test loading sync engine from YAML."""
    yaml_content = """
name: "test-sync"
source_platform: "jira"
target_platform: "github"
direction: "bidirectional"
batch_size: 25
field_mappings:
  - source_field: "summary"
    target_field: "title"
    source_type: "string"
    target_type: "string"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        config_path = f.name

    try:
        engine = SyncEngine.from_yaml(Path(config_path))
        assert engine.config.name == "test-sync"
        assert engine.config.batch_size == 25
        assert len(engine.config.field_mappings) == 1
    finally:
        Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
