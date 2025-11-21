"""Configuration generator with Jinja2 templating and environment merging."""

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template


class ConfigGenerator:
    """Configuration generator with templating and environment support."""

    def __init__(
        self,
        template_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize the configuration generator.

        Args:
            template_dir: Optional directory containing Jinja2 templates.
        """
        self._template_dir = Path(template_dir) if template_dir else None
        self._env: Optional[Environment] = None
        if self._template_dir and self._template_dir.exists():
            self._env = Environment(
                loader=FileSystemLoader(str(self._template_dir)),
                undefined=StrictUndefined,
                autoescape=False,
            )

    def render_template(
        self,
        template_content: str,
        variables: Dict[str, Any],
    ) -> str:
        """Render a Jinja2 template string.

        Args:
            template_content: Jinja2 template string.
            variables: Variables to substitute in the template.

        Returns:
            Rendered template string.
        """
        template = Template(template_content, undefined=StrictUndefined)
        return template.render(**variables)

    def render_template_file(
        self,
        template_name: str,
        variables: Dict[str, Any],
    ) -> str:
        """Render a template file from the template directory.

        Args:
            template_name: Name of the template file.
            variables: Variables to substitute in the template.

        Returns:
            Rendered template string.

        Raises:
            RuntimeError: If no template directory is configured.
        """
        if self._env is None:
            raise RuntimeError("No template directory configured")
        template = self._env.get_template(template_name)
        return template.render(**variables)

    def substitute_variables(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any],
        prefix: str = "${",
        suffix: str = "}",
    ) -> Dict[str, Any]:
        """Substitute variables in configuration values.

        Args:
            config: Configuration dictionary.
            variables: Variables to substitute.
            prefix: Variable reference prefix.
            suffix: Variable reference suffix.

        Returns:
            Configuration with substituted values.
        """
        result = deepcopy(config)

        def substitute(value: Any) -> Any:
            if isinstance(value, str):
                for var_name, var_value in variables.items():
                    placeholder = f"{prefix}{var_name}{suffix}"
                    if placeholder in value:
                        if value == placeholder:
                            return var_value
                        value = value.replace(placeholder, str(var_value))
                return value
            elif isinstance(value, dict):
                return {k: substitute(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute(item) for item in value]
            return value

        return substitute(result)

    def substitute_env_variables(
        self,
        config: Dict[str, Any],
        prefix: str = "${env:",
        suffix: str = "}",
        default_prefix: str = ":-",
    ) -> Dict[str, Any]:
        """Substitute environment variables in configuration.

        Args:
            config: Configuration dictionary.
            prefix: Environment variable reference prefix.
            suffix: Environment variable reference suffix.
            default_prefix: Prefix for default values in references.

        Returns:
            Configuration with substituted environment variables.
        """
        result = deepcopy(config)

        def substitute(value: Any) -> Any:
            if isinstance(value, str):
                import re

                pattern = re.escape(prefix) + r"([^}]+)" + re.escape(suffix)
                matches = re.findall(pattern, value)
                for match in matches:
                    if default_prefix in match:
                        var_name, default = match.split(default_prefix, 1)
                    else:
                        var_name = match
                        default = ""
                    env_value = os.environ.get(var_name.strip(), default)
                    placeholder = f"{prefix}{match}{suffix}"
                    if value == placeholder:
                        return env_value
                    value = value.replace(placeholder, env_value)
                return value
            elif isinstance(value, dict):
                return {k: substitute(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute(item) for item in value]
            return value

        return substitute(result)

    def merge_configs(
        self,
        *configs: Dict[str, Any],
        deep: bool = True,
    ) -> Dict[str, Any]:
        """Merge multiple configurations.

        Args:
            *configs: Configuration dictionaries to merge.
            deep: If True, perform deep merge. Otherwise shallow.

        Returns:
            Merged configuration dictionary.
        """
        if not configs:
            return {}

        result: Dict[str, Any] = {}

        def deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
            merged = deepcopy(base)
            for key, value in overlay.items():
                if (
                    deep
                    and key in merged
                    and isinstance(merged[key], dict)
                    and isinstance(value, dict)
                ):
                    merged[key] = deep_merge(merged[key], value)
                else:
                    merged[key] = deepcopy(value)
            return merged

        for config in configs:
            result = deep_merge(result, config)

        return result

    def merge_environments(
        self,
        base_config: Dict[str, Any],
        environment: str,
        env_configs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Merge base configuration with environment-specific overrides.

        Args:
            base_config: Base configuration dictionary.
            environment: Target environment name.
            env_configs: Mapping of environment names to configurations.

        Returns:
            Merged configuration for the specified environment.

        Raises:
            KeyError: If environment is not found in env_configs.
        """
        if environment not in env_configs:
            raise KeyError(f"Environment not found: {environment}")
        return self.merge_configs(base_config, env_configs[environment])

    def generate_from_template(
        self,
        template_content: str,
        variables: Dict[str, Any],
        output_format: str = "yaml",
    ) -> Dict[str, Any]:
        """Generate configuration from a template.

        Args:
            template_content: Jinja2 template string.
            variables: Variables to substitute.
            output_format: Expected output format (yaml, json, toml).

        Returns:
            Parsed configuration dictionary.
        """
        from .config_parser import ConfigFormat, ConfigParser

        rendered = self.render_template(template_content, variables)
        parser = ConfigParser()

        format_map = {
            "yaml": ConfigFormat.YAML,
            "json": ConfigFormat.JSON,
            "toml": ConfigFormat.TOML,
        }
        config_format = format_map.get(output_format.lower(), ConfigFormat.YAML)

        return parser.parse_string(rendered, config_format)

    def generate_config(
        self,
        base_config: Dict[str, Any],
        variables: Optional[Dict[str, Any]] = None,
        environment: Optional[str] = None,
        env_configs: Optional[Dict[str, Dict[str, Any]]] = None,
        include_env_vars: bool = True,
    ) -> Dict[str, Any]:
        """Generate a complete configuration.

        Args:
            base_config: Base configuration dictionary.
            variables: Variables to substitute.
            environment: Optional target environment.
            env_configs: Optional environment-specific configurations.
            include_env_vars: Whether to substitute environment variables.

        Returns:
            Generated configuration dictionary.
        """
        result = deepcopy(base_config)

        if environment and env_configs:
            result = self.merge_environments(result, environment, env_configs)

        if variables:
            result = self.substitute_variables(result, variables)

        if include_env_vars:
            result = self.substitute_env_variables(result)

        return result
