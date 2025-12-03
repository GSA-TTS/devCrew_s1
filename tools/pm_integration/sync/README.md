# Synchronization Engine

Bidirectional synchronization engine for project management platforms (Jira, Linear, GitHub Projects) with field mapping, conflict resolution, and change tracking.

## Features

- **Bidirectional Sync**: Sync between any combination of Jira, Linear, and GitHub Projects
- **Field Mapping**: Flexible field mapping with type conversion
- **Conflict Resolution**: Multiple strategies (last-write-wins, manual, source-wins, target-wins, custom)
- **Change Tracking**: Incremental sync with checksum-based change detection
- **Type Conversion**: Automatic conversion between string, number, date, array, and JSON types
- **Retry Logic**: Exponential backoff for failed operations
- **Dry-Run Mode**: Test synchronization without making changes
- **Audit Trail**: Complete history of all synchronization operations
- **Batch Processing**: Efficient batch synchronization
- **State Management**: Persistent state tracking between syncs

## Architecture

```
SyncEngine
├── ConflictDetector       # Detects conflicts between items
├── ConflictResolver       # Resolves conflicts using strategies
├── FieldTransformer       # Transforms field values and types
├── ChangeTracker          # Tracks changes with checksums
└── SyncAuditor           # Logs sync operations
```

## Installation

```bash
pip install -r requirements.txt
```

Required dependencies:
- pydantic >= 2.0
- pyyaml >= 6.0
- pytest >= 7.0 (for testing)

## Quick Start

### Basic Usage

```python
from pathlib import Path
from sync_engine import SyncEngine

# Load configuration from YAML
engine = SyncEngine.from_yaml(Path("config/jira_to_github.yaml"))

# Enable dry-run mode for testing
engine.set_dry_run(True)

# Perform synchronization
results = await engine.sync(
    source_items=jira_issues,
    target_items=github_issues,
    source_client=jira_client,
    target_client=github_client
)

# Check results
for result in results:
    print(f"{result.item_id}: {result.status.value}")
```

### Configuration

Create a YAML configuration file:

```yaml
name: "jira-github-sync"
source_platform: "jira"
target_platform: "github"
direction: "bidirectional"
conflict_strategy: "last_write_wins"
batch_size: 50
sync_interval: 300

field_mappings:
  - source_field: "summary"
    target_field: "title"
    source_type: "string"
    target_type: "string"
    bidirectional: true
    required: true

  - source_field: "customfield_10001"
    target_field: "story_points"
    source_type: "number"
    target_type: "number"
    transform: "custom_transform"
```

## Field Mapping

### Supported Field Types

- `string`: Text values
- `number`: Integer or float values
- `boolean`: True/false values
- `date`: Date without time
- `datetime`: Date with time
- `array`: List of values
- `object`: Complex objects
- `json`: JSON-encoded data

### Type Conversions

The engine automatically converts between types:

```python
# String to number
"42" → 42

# Number to string
42 → "42"

# Array to string
["bug", "urgent"] → "bug,urgent"

# String to array
"bug,urgent" → ["bug", "urgent"]

# JSON encode/decode
{"key": "value"} ↔ '{"key": "value"}'
```

### Custom Transformers

Register custom transformation functions:

```python
def jira_status_to_github(status: str) -> str:
    mapping = {
        "To Do": "open",
        "In Progress": "in_progress",
        "Done": "closed"
    }
    return mapping.get(status, "open")

engine.register_field_transformer(
    "jira_status_to_github",
    jira_status_to_github
)
```

## Conflict Resolution

### Strategies

1. **Last Write Wins** (default): Most recently modified item wins
   ```yaml
   conflict_strategy: "last_write_wins"
   ```

2. **Source Wins**: Source platform always wins
   ```yaml
   conflict_strategy: "source_wins"
   ```

3. **Target Wins**: Target platform always wins
   ```yaml
   conflict_strategy: "target_wins"
   ```

4. **Manual**: Require manual resolution
   ```yaml
   conflict_strategy: "manual"
   ```

5. **Custom**: Use custom resolver function
   ```yaml
   conflict_strategy: "custom"
   ```

### Custom Conflict Resolver

```python
def custom_resolver(source_item, target_item, conflicts):
    # Custom logic to resolve conflicts
    if "priority" in str(conflicts):
        # Prefer higher priority
        if source_item.data.get("priority", 0) > target_item.data.get("priority", 0):
            return source_item
        return target_item

    # Default to source
    return source_item

engine.set_custom_conflict_resolver(custom_resolver)
```

## Change Tracking

The engine tracks changes using checksums to avoid unnecessary updates:

```python
# Check if item has changed
tracker = ChangeTracker(state_dir)
has_changed = tracker.has_changed(item_id, data)

# Update checksum after sync
tracker.update_checksum(item_id, data)

# Get last sync time
last_sync = tracker.get_last_sync_time(item_id)

# Persist state
tracker.save_state(config_name)
```

## Sync Results

Each synchronization returns detailed results:

```python
@dataclass
class SyncResult:
    item_id: str
    status: SyncStatus  # COMPLETED, FAILED, CONFLICT, SKIPPED
    source_platform: PlatformType
    target_platform: PlatformType
    timestamp: datetime
    error: Optional[str]
    conflicts: List[str]
    changes: Dict[str, Any]
    retry_count: int
```

### Processing Results

```python
results = await engine.sync(source_items, target_items, source_client, target_client)

# Count by status
completed = sum(1 for r in results if r.status == SyncStatus.COMPLETED)
failed = sum(1 for r in results if r.status == SyncStatus.FAILED)
conflicts = sum(1 for r in results if r.status == SyncStatus.CONFLICT)

print(f"Completed: {completed}, Failed: {failed}, Conflicts: {conflicts}")

# Get failed items
failed_items = [r for r in results if r.status == SyncStatus.FAILED]
for result in failed_items:
    print(f"Failed to sync {result.item_id}: {result.error}")

# Get conflicts
conflict_items = [r for r in results if r.status == SyncStatus.CONFLICT]
for result in conflict_items:
    print(f"Conflict in {result.item_id}: {result.conflicts}")
```

## Sync State

Track overall synchronization state:

```python
state = engine.get_sync_state()

print(f"Last sync: {state.last_sync}")
print(f"Items synced: {state.items_synced}")
print(f"Items failed: {state.items_failed}")
print(f"Items skipped: {state.items_skipped}")
print(f"Conflicts: {len(state.conflicts)}")
```

## Audit Trail

View sync history for any item:

```python
# Get last 7 days of sync history
history = engine.get_sync_history(item_id="ISSUE-123", days=7)

for entry in history:
    print(f"{entry['timestamp']}: {entry['status']}")
    if entry['error']:
        print(f"  Error: {entry['error']}")
    if entry['changes']:
        print(f"  Changes: {entry['changes']}")
```

## Dry-Run Mode

Test synchronization without making changes:

```python
# Enable dry-run mode
engine.set_dry_run(True)

# Perform sync (no actual changes made)
results = await engine.sync(source_items, target_items, source_client, target_client)

# Review what would have been changed
for result in results:
    if result.changes:
        print(f"{result.item_id}: {result.changes}")

# Disable dry-run for actual sync
engine.set_dry_run(False)
```

## Examples

### Example 1: Jira to GitHub Sync

```python
from pathlib import Path
from sync_engine import SyncEngine, SyncStatus

# Load configuration
engine = SyncEngine.from_yaml(Path("config/jira_to_github.yaml"))

# Custom transformer for status
def jira_status_to_github(status: str) -> str:
    mapping = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "Done": "done",
    }
    return mapping.get(status, "todo")

engine.register_field_transformer("jira_status_to_github", jira_status_to_github)

# Fetch items from both platforms
jira_issues = jira_client.get_issues(project="PROJ")
github_issues = github_client.get_issues(repo="myorg/myrepo")

# Sync
results = await engine.sync(
    source_items=jira_issues,
    target_items=github_issues,
    source_client=jira_client,
    target_client=github_client
)

# Report results
print(f"Sync completed:")
print(f"  Synced: {sum(1 for r in results if r.status == SyncStatus.COMPLETED)}")
print(f"  Failed: {sum(1 for r in results if r.status == SyncStatus.FAILED)}")
print(f"  Conflicts: {sum(1 for r in results if r.status == SyncStatus.CONFLICT)}")
```

### Example 2: Linear to Jira Sync with Custom Conflict Resolution

```python
from sync_engine import SyncEngine, ConflictResolutionStrategy

# Load configuration
engine = SyncEngine.from_yaml(Path("config/linear_to_jira.yaml"))

# Set custom conflict resolver
def priority_based_resolver(source_item, target_item, conflicts):
    """Prefer item with higher priority."""
    source_priority = source_item.data.get("priority", 999)
    target_priority = target_item.data.get("priority", 999)

    if source_priority < target_priority:  # Lower number = higher priority
        return source_item
    return target_item

engine.config.conflict_strategy = ConflictResolutionStrategy.CUSTOM
engine.set_custom_conflict_resolver(priority_based_resolver)

# Sync
results = await engine.sync(
    source_items=linear_issues,
    target_items=jira_issues,
    source_client=linear_client,
    target_client=jira_client
)
```

### Example 3: Batch Sync with Progress Reporting

```python
from sync_engine import SyncEngine

engine = SyncEngine.from_yaml(Path("config/github_to_linear.yaml"))

# Large dataset
all_github_issues = github_client.get_all_issues()  # 1000+ issues
all_linear_issues = linear_client.get_all_issues()

print(f"Starting sync of {len(all_github_issues)} issues...")

# Sync will process in batches
results = await engine.sync(
    source_items=all_github_issues,
    target_items=all_linear_issues,
    source_client=github_client,
    target_client=linear_client
)

# Show progress
state = engine.get_sync_state()
print(f"\nSync completed:")
print(f"  Total processed: {len(results)}")
print(f"  Successfully synced: {state.items_synced}")
print(f"  Failed: {state.items_failed}")
print(f"  Skipped (no changes): {state.items_skipped}")
```

## Configuration Validation

Validate configuration before syncing:

```python
engine = SyncEngine.from_yaml(Path("config/my_sync.yaml"))

# Validate configuration
errors = await engine.validate_configuration()

if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid")
    # Proceed with sync
```

## Best Practices

1. **Start with Dry-Run**: Always test with dry-run mode first
   ```python
   engine.set_dry_run(True)
   ```

2. **Enable Audit Logging**: Keep track of all sync operations
   ```yaml
   enable_audit: true
   ```

3. **Use Appropriate Batch Size**: Balance performance and memory
   ```yaml
   batch_size: 50  # Good default
   ```

4. **Handle Conflicts Proactively**: Choose appropriate strategy
   ```yaml
   conflict_strategy: "last_write_wins"  # For most cases
   ```

5. **Monitor Sync State**: Track failures and conflicts
   ```python
   state = engine.get_sync_state()
   if state.items_failed > 0:
       # Handle failures
   ```

6. **Use Required Fields**: Mark critical fields as required
   ```yaml
   field_mappings:
     - source_field: "summary"
       target_field: "title"
       required: true
       default_value: "Untitled"
   ```

7. **Implement Custom Transformers**: Handle platform-specific logic
   ```python
   engine.register_field_transformer("custom_transform", my_function)
   ```

## Performance Optimization

### Batch Size Tuning

```yaml
# Small batches: Less memory, more API calls
batch_size: 25

# Medium batches: Balanced (recommended)
batch_size: 50

# Large batches: More memory, fewer API calls
batch_size: 100
```

### Incremental Sync

```python
# Only sync changed items
tracker = ChangeTracker(state_dir)
changed_items = [
    item for item in source_items
    if tracker.has_changed(item["id"], item)
]

# Sync only changed items
results = await engine.sync(changed_items, target_items, source_client, target_client)
```

### Sync Interval

```yaml
# Frequent syncs for real-time updates
sync_interval: 60  # 1 minute

# Moderate syncs for most use cases
sync_interval: 300  # 5 minutes

# Infrequent syncs for less critical data
sync_interval: 3600  # 1 hour
```

## Troubleshooting

### Common Issues

1. **Conflicts on Every Sync**
   - Check timestamp handling in field mappings
   - Verify checksum calculation includes all relevant fields
   - Consider using `source_wins` or `target_wins` strategy

2. **High Failure Rate**
   - Increase `max_retries` and `retry_delay`
   - Check network connectivity
   - Verify API credentials

3. **Slow Synchronization**
   - Increase batch size
   - Enable incremental sync
   - Reduce sync frequency

4. **Type Conversion Errors**
   - Add custom transformers for complex types
   - Use `default_value` for optional fields
   - Check field type definitions

### Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("sync_engine")

# Detailed logging will show:
# - Field transformations
# - Conflict detection
# - Retry attempts
# - State changes
```

## Testing

Run comprehensive tests:

```bash
# Run all tests
pytest test_sync_engine.py -v

# Run specific test class
pytest test_sync_engine.py::TestFieldTransformer -v

# Run with coverage
pytest test_sync_engine.py --cov=sync_engine --cov-report=html
```

## API Reference

See inline documentation in `sync_engine.py` for detailed API reference.

Key classes:
- `SyncEngine`: Main synchronization engine
- `SyncConfiguration`: Configuration model
- `FieldMapping`: Field mapping definition
- `ConflictDetector`: Conflict detection
- `ConflictResolver`: Conflict resolution
- `FieldTransformer`: Field transformation
- `ChangeTracker`: Change tracking
- `SyncAuditor`: Audit logging

## License

Part of devCrew_s Project Management Integration Platform.
