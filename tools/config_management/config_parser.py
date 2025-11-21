"""Multi-format configuration parser supporting YAML, JSON, and TOML."""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

import toml
import yaml


class ConfigFormat(Enum):
    """Supported configuration file formats."""

    YAML = "yaml"
    JSON = "json"
    TOML = "toml"
    AUTO = "auto"


class ConfigParser:
    """Multi-format configuration parser with automatic format detection."""

    FORMAT_EXTENSIONS = {
        ".yaml": ConfigFormat.YAML,
        ".yml": ConfigFormat.YAML,
        ".json": ConfigFormat.JSON,
        ".toml": ConfigFormat.TOML,
    }

    def __init__(self) -> None:
        """Initialize the configuration parser."""
        pass

    def detect_format(self, file_path: Union[str, Path]) -> ConfigFormat:
        """Detect configuration format from file extension.

        Args:
            file_path: Path to the configuration file.

        Returns:
            Detected ConfigFormat.

        Raises:
            ValueError: If format cannot be detected.
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        if extension in self.FORMAT_EXTENSIONS:
            return self.FORMAT_EXTENSIONS[extension]
        raise ValueError(f"Cannot detect format for extension: {extension}")

    def parse_file(
        self,
        file_path: Union[str, Path],
        format_type: ConfigFormat = ConfigFormat.AUTO,
    ) -> Dict[str, Any]:
        """Parse a configuration file.

        Args:
            file_path: Path to the configuration file.
            format_type: Format to use for parsing. AUTO detects from extension.

        Returns:
            Parsed configuration as a dictionary.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If format cannot be determined or parsing fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        if format_type == ConfigFormat.AUTO:
            format_type = self.detect_format(path)

        content = path.read_text(encoding="utf-8")
        return self.parse_string(content, format_type)

    def parse_string(
        self,
        content: str,
        format_type: ConfigFormat,
    ) -> Dict[str, Any]:
        """Parse configuration from a string.

        Args:
            content: Configuration content as string.
            format_type: Format of the content.

        Returns:
            Parsed configuration as a dictionary.

        Raises:
            ValueError: If parsing fails or format is AUTO.
        """
        if format_type == ConfigFormat.AUTO:
            raise ValueError("Format must be specified for string parsing")

        try:
            if format_type == ConfigFormat.YAML:
                result = yaml.safe_load(content)
                return result if result is not None else {}
            elif format_type == ConfigFormat.JSON:
                return json.loads(content) if content.strip() else {}
            elif format_type == ConfigFormat.TOML:
                return toml.loads(content)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
        except (yaml.YAMLError, json.JSONDecodeError, toml.TomlDecodeError) as e:
            raise ValueError(f"Failed to parse {format_type.value}: {e}") from e

    def serialize(
        self,
        config: Dict[str, Any],
        format_type: ConfigFormat,
        indent: int = 2,
    ) -> str:
        """Serialize configuration to a string.

        Args:
            config: Configuration dictionary to serialize.
            format_type: Target format.
            indent: Indentation level for JSON.

        Returns:
            Serialized configuration string.

        Raises:
            ValueError: If format is AUTO or unsupported.
        """
        if format_type == ConfigFormat.AUTO:
            raise ValueError("Format must be specified for serialization")

        if format_type == ConfigFormat.YAML:
            return yaml.dump(config, default_flow_style=False, sort_keys=False)
        elif format_type == ConfigFormat.JSON:
            return json.dumps(config, indent=indent)
        elif format_type == ConfigFormat.TOML:
            return toml.dumps(config)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def write_file(
        self,
        config: Dict[str, Any],
        file_path: Union[str, Path],
        format_type: ConfigFormat = ConfigFormat.AUTO,
    ) -> None:
        """Write configuration to a file.

        Args:
            config: Configuration dictionary to write.
            file_path: Path to write to.
            format_type: Format to use. AUTO detects from extension.

        Raises:
            ValueError: If format cannot be determined.
        """
        path = Path(file_path)
        if format_type == ConfigFormat.AUTO:
            format_type = self.detect_format(path)

        content = self.serialize(config, format_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def detect_schema(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect and generate a basic JSON schema from configuration structure.

        Args:
            config: Configuration dictionary to analyze.

        Returns:
            Generated JSON schema or None if config is empty.
        """
        if not config:
            return None

        def infer_type(value: Any) -> Dict[str, Any]:
            """Infer JSON schema type from a Python value."""
            if value is None:
                return {"type": "null"}
            elif isinstance(value, bool):
                return {"type": "boolean"}
            elif isinstance(value, int):
                return {"type": "integer"}
            elif isinstance(value, float):
                return {"type": "number"}
            elif isinstance(value, str):
                return {"type": "string"}
            elif isinstance(value, list):
                if not value:
                    return {"type": "array", "items": {}}
                item_types = [infer_type(item) for item in value]
                return {"type": "array", "items": item_types[0]}
            elif isinstance(value, dict):
                properties = {}
                for k, v in value.items():
                    properties[k] = infer_type(v)
                return {
                    "type": "object",
                    "properties": properties,
                    "required": list(value.keys()),
                }
            else:
                return {}

        schema = infer_type(config)
        schema["$schema"] = "http://json-schema.org/draft-07/schema#"
        return schema
