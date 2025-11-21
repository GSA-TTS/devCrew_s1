# Configuration Management Platform

A comprehensive configuration management platform for devCrew_s1 providing multi-format parsing, schema validation, template-based generation, version control, drift detection, and secrets management.

## Features

- **Multi-format Parsing**: YAML, JSON, and TOML support with automatic format detection
- **Schema Validation**: JSON Schema and Pydantic model validation with custom validators
- **Configuration Generation**: Jinja2 templating with variable substitution and environment merging
- **Version Management**: Git-based versioning with rollback, change tracking, and diff generation
- **Drift Detection**: Live vs desired state comparison with reconciliation reports
- **Secrets Management**: HashiCorp Vault and AWS Secrets Manager integration

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Configuration Parser

```python
from tools.config_management import ConfigParser, ConfigFormat

parser = ConfigParser()

# Parse files with auto-detection
config = parser.parse_file("config.yaml")

# Parse specific format
config = parser.parse_file("config.json", ConfigFormat.JSON)

# Parse string content
config = parser.parse_string("key: value", ConfigFormat.YAML)

# Write configuration
parser.write_file(config, "output.yaml")

# Generate schema from configuration
schema = parser.detect_schema(config)
```

### Schema Validation

```python
from tools.config_management import SchemaValidator, ValidationResult
from pydantic import BaseModel

validator = SchemaValidator()

# JSON Schema validation
schema = {"type": "object", "properties": {"name": {"type": "string"}}}
result = validator.validate_json_schema(config, schema)

# Pydantic model validation
class ConfigModel(BaseModel):
    name: str
    port: int

result = validator.validate_pydantic(config, ConfigModel)

# Custom validators
def port_validator(config):
    result = ValidationResult(valid=True)
    if config.get("port", 0) < 1024:
        result.add_error("Port must be >= 1024")
    return result

validator.register_custom_validator("port_check", port_validator)
result = validator.validate_custom(config, "port_check")
```

### Configuration Generator

```python
from tools.config_management import ConfigGenerator

generator = ConfigGenerator()

# Jinja2 templating
template = "database:\n  host: {{ db_host }}\n  port: {{ db_port }}"
rendered = generator.render_template(template, {"db_host": "localhost", "db_port": 5432})

# Variable substitution
config = {"host": "${HOST}", "port": "${PORT}"}
result = generator.substitute_variables(config, {"HOST": "localhost", "PORT": 5432})

# Environment variable substitution
config = {"host": "${env:DB_HOST:-localhost}"}
result = generator.substitute_env_variables(config)

# Merge configurations
base = {"debug": False, "database": {"host": "localhost"}}
overlay = {"database": {"port": 5432}}
merged = generator.merge_configs(base, overlay)

# Environment-specific merging
env_configs = {
    "production": {"debug": False, "database": {"host": "prod-db"}},
    "development": {"debug": True}
}
result = generator.merge_environments(base, "production", env_configs)
```

### Version Manager

```python
from tools.config_management import VersionManager

vm = VersionManager("/path/to/repo")

# Commit a new version
version = vm.commit("app-config", config, "author", "Update database settings")

# Get configuration versions
latest = vm.get_latest_config("app-config")
specific = vm.get_config("app-config", "v20240101120000-abc123")

# List version history
versions = vm.list_versions("app-config")
history = vm.get_history("app-config", limit=10)

# Compare versions
diff = vm.diff("app-config", "v1", "v2")

# Rollback to previous version
vm.rollback("app-config", "v20240101120000-abc123", "author", "Rollback due to issue")
```

### Drift Detector

```python
from tools.config_management import DriftDetector, DriftSeverity

detector = DriftDetector()

# Set severity rules
detector.set_severity_rule("password", DriftSeverity.CRITICAL)
detector.add_ignore_path("timestamp")

# Compare configurations
report = detector.compare(desired_config, live_config, "app-config")

if report.has_drift:
    print(f"Critical: {report.critical_count}")
    print(f"Warnings: {report.warning_count}")
    for item in report.drift_items:
        print(f"  {item.path}: {item.drift_type}")

# Generate reconciliation plan
plan = detector.generate_reconciliation_plan(report)

# Register live state fetcher for automatic detection
detector.register_live_state_fetcher("app-config", fetch_live_config)
report = detector.detect("app-config", desired_config)
```

### Secrets Manager

```python
from tools.config_management import SecretsManager
from tools.config_management.secrets_manager import EnvBackend, VaultBackend, AWSSecretsBackend

manager = SecretsManager()

# Register backends
manager.register_backend("env", EnvBackend(), default=True)
manager.register_backend("vault", VaultBackend(url="http://vault:8200"))
manager.register_backend("aws", AWSSecretsBackend(region_name="us-east-1"))

# Get secrets
secret = manager.get_secret("DB_PASSWORD", backend="env")
secret = manager.get_secret("secret/myapp#password", backend="vault")

# Substitute secrets in configuration
config = {"password": "${secret:DB_PASSWORD}"}
resolved = manager.substitute_secrets(config)

# Mask secrets for display
masked = manager.mask_secrets(config, ["password"])
```

## CLI Usage

```bash
# Validate configuration
config-cli validate config.yaml
config-cli validate config.yaml --schema schema.json

# Generate configuration from template
config-cli generate template.j2 --vars vars.yaml --output config.yaml
config-cli generate template.j2 -e HOST=localhost -e PORT=5432

# Compare configurations
config-cli diff config1.yaml config2.yaml

# Show version history
config-cli history app-config --repo /path/to/repo --limit 10

# Rollback to previous version
config-cli rollback app-config v20240101120000-abc123 --repo /path/to/repo

# Detect drift
config-cli drift desired.yaml live.yaml --output report.json

# Generate schema from configuration
config-cli schema config.yaml --output schema.json
```

## Testing

```bash
# Run all tests
pytest tools/config_management/test_config.py -v

# Run with coverage
pytest tools/config_management/test_config.py -v --cov=tools/config_management --cov-report=term-missing
```

## Dependencies

- pydantic>=2.0.0 - Data validation using Python type hints
- jsonschema>=4.17.0 - JSON Schema validation
- PyYAML>=6.0 - YAML parsing
- Jinja2>=3.1.0 - Template engine
- toml>=0.10.2 - TOML parsing
- deepdiff>=6.0.0 - Deep comparison of objects
- click>=8.0.0 - CLI framework
- hvac>=1.0.0 - HashiCorp Vault client
- boto3>=1.26.0 - AWS SDK
- gitpython>=3.1.0 - Git operations

## License

Part of the devCrew_s1 project.
