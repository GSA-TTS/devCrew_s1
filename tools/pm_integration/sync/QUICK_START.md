# Synchronization Engine - Quick Start Guide

## Installation

```bash
cd tools/pm_integration/sync
pip install pydantic pyyaml pytest
```

## 5-Minute Quick Start

### 1. Create Configuration File

```yaml
# config.yaml
name: "my-sync"
source_platform: "jira"
target_platform: "github"
direction: "bidirectional"
conflict_strategy: "last_write_wins"
batch_size: 50

field_mappings:
  - source_field: "summary"
    target_field: "title"
    source_type: "string"
    target_type: "string"
    bidirectional: true
    required: true

  - source_field: "description"
    target_field: "body"
    source_type: "string"
    target_type: "string"
    bidirectional: true
```

### 2. Basic Usage

```python
from pathlib import Path
from sync_engine import SyncEngine, SyncStatus

# Load configuration
engine = SyncEngine.from_yaml(Path("config.yaml"))

# Enable dry-run for testing
engine.set_dry_run(True)

# Fetch items from platforms
source_items = [
    {
        "id": "ISSUE-1",
        "summary": "Bug fix",
        "description": "Fix login issue",
        "updated_at": "2023-12-03T10:00:00"
    }
]

target_items = [
    {
        "id": "ISSUE-1",
        "title": "Old title",
        "body": "Old description",
        "updated_at": "2023-12-03T09:00:00"
    }
]

# Perform sync
results = await engine.sync(
    source_items=source_items,
    target_items=target_items,
    source_client=None,  # Your platform client
    target_client=None   # Your platform client
)

# Check results
for result in results:
    print(f"{result.item_id}: {result.status.value}")
    if result.changes:
        print(f"  Changes: {result.changes}")
```

## Common Use Cases

### Use Case 1: Dry Run Test

```python
# Test sync without making changes
engine.set_dry_run(True)
results = await engine.sync(source_items, target_items, source_client, target_client)

# Review changes
for result in results:
    if result.changes:
        print(f"{result.item_id} would be updated: {result.changes}")
```

### Use Case 2: Custom Field Transformer

```python
# Define custom transformer
def priority_to_number(priority: str) -> int:
    mapping = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
    return mapping.get(priority, 3)

# Register transformer
engine.register_field_transformer("priority_to_number", priority_to_number)
```

### Use Case 3: Custom Conflict Resolver

```python
from sync_engine import ConflictResolutionStrategy

# Set custom strategy
engine.config.conflict_strategy = ConflictResolutionStrategy.CUSTOM

# Define resolver
def custom_resolver(source_item, target_item, conflicts):
    # Your logic here
    return source_item  # or target_item

engine.set_custom_conflict_resolver(custom_resolver)
```

### Use Case 4: Audit Trail

```python
# Get sync history for item
history = engine.get_sync_history(item_id="ISSUE-123", days=7)

for entry in history:
    print(f"{entry['timestamp']}: {entry['status']}")
    if entry['error']:
        print(f"  Error: {entry['error']}")
```

## Configuration Options

### Field Types
- `string`: Text values
- `number`: Integer or float
- `boolean`: True/false
- `date`: Date without time
- `datetime`: Date with time
- `array`: List of values
- `json`: JSON objects

### Conflict Strategies
- `last_write_wins`: Most recent wins (default)
- `source_wins`: Source always wins
- `target_wins`: Target always wins
- `manual`: Require manual resolution
- `custom`: Use custom function

### Sync Directions
- `bidirectional`: Both directions (default)
- `source_to_target`: One-way, source → target
- `target_to_source`: One-way, target → source

## Example Configurations

See `example_configs/` directory:
- `jira_to_github.yaml` - Jira → GitHub sync
- `linear_to_jira.yaml` - Linear → Jira sync
- `github_to_linear.yaml` - GitHub → Linear sync

## Testing

```bash
# Run all tests
pytest test_sync_engine.py -v

# Run specific test
pytest test_sync_engine.py::TestFieldTransformer::test_string_to_number -v
```

## Common Issues

### Issue 1: Import Error
```python
# Wrong
from sync_engine import SyncEngine

# Correct (if running from sync directory)
from sync.sync_engine import SyncEngine

# Or use absolute import
import sys
sys.path.append("/path/to/pm_integration")
from sync.sync_engine import SyncEngine
```

### Issue 2: Configuration Validation Error
```python
# Validate configuration
errors = await engine.validate_configuration()
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
```

### Issue 3: All Items Syncing Every Time
```python
# Check if change tracking is enabled
# State is saved automatically, but verify state directory exists
state_dir = Path.home() / ".pm_integration" / "sync_state"
print(f"State directory: {state_dir}")
print(f"Exists: {state_dir.exists()}")
```

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture
3. Explore example configurations in `example_configs/`
4. Run tests: `pytest test_sync_engine.py -v`
5. Integrate with your platform clients

## Support

For issues or questions:
1. Check the README.md documentation
2. Review test cases for examples
3. Examine example configurations
4. Check the implementation summary for architecture details
