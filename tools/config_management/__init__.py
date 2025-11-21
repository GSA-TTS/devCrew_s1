"""Configuration Management Platform for devCrew_s1.

This package provides comprehensive configuration management capabilities including:
- Multi-format parsing (YAML, JSON, TOML)
- Schema validation (JSON Schema, Pydantic)
- Template-based configuration generation
- Version control and rollback
- Drift detection and reconciliation
- Secrets management integration
"""

from .config_parser import ConfigParser, ConfigFormat
from .schema_validator import SchemaValidator, ValidationResult
from .config_generator import ConfigGenerator
from .version_manager import VersionManager
from .drift_detector import DriftDetector, DriftReport
from .secrets_manager import SecretsManager

__version__ = "1.0.0"
__all__ = [
    "ConfigParser",
    "ConfigFormat",
    "SchemaValidator",
    "ValidationResult",
    "ConfigGenerator",
    "VersionManager",
    "DriftDetector",
    "DriftReport",
    "SecretsManager",
]
