"""Comprehensive tests for the Configuration Management Platform."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
import yaml
from pydantic import BaseModel

from .config_generator import ConfigGenerator
from .config_parser import ConfigFormat, ConfigParser
from .drift_detector import DriftDetector, DriftReport, DriftSeverity
from .schema_validator import (
    SchemaValidator,
    ValidationResult,
    create_required_fields_validator,
    create_type_validator,
)
from .secrets_manager import EnvBackend, SecretsManager
from .version_manager import ConfigDiff, ConfigVersion, VersionManager


class TestConfigParser:
    """Tests for ConfigParser."""

    def test_detect_format_yaml(self) -> None:
        parser = ConfigParser()
        assert parser.detect_format("config.yaml") == ConfigFormat.YAML
        assert parser.detect_format("config.yml") == ConfigFormat.YAML

    def test_detect_format_json(self) -> None:
        parser = ConfigParser()
        assert parser.detect_format("config.json") == ConfigFormat.JSON

    def test_detect_format_toml(self) -> None:
        parser = ConfigParser()
        assert parser.detect_format("config.toml") == ConfigFormat.TOML

    def test_detect_format_unknown(self) -> None:
        parser = ConfigParser()
        with pytest.raises(ValueError):
            parser.detect_format("config.txt")

    def test_parse_yaml_string(self) -> None:
        parser = ConfigParser()
        content = "key: value\nnested:\n  inner: 123"
        result = parser.parse_string(content, ConfigFormat.YAML)
        assert result == {"key": "value", "nested": {"inner": 123}}

    def test_parse_json_string(self) -> None:
        parser = ConfigParser()
        content = '{"key": "value", "number": 42}'
        result = parser.parse_string(content, ConfigFormat.JSON)
        assert result == {"key": "value", "number": 42}

    def test_parse_toml_string(self) -> None:
        parser = ConfigParser()
        content = 'key = "value"\nnumber = 42'
        result = parser.parse_string(content, ConfigFormat.TOML)
        assert result == {"key": "value", "number": 42}

    def test_parse_string_auto_format_raises(self) -> None:
        parser = ConfigParser()
        with pytest.raises(ValueError):
            parser.parse_string("content", ConfigFormat.AUTO)

    def test_parse_file(self) -> None:
        parser = ConfigParser()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("key: value")
            f.flush()
            result = parser.parse_file(f.name)
            assert result == {"key": "value"}
            os.unlink(f.name)

    def test_parse_file_not_found(self) -> None:
        parser = ConfigParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/config.yaml")

    def test_serialize_yaml(self) -> None:
        parser = ConfigParser()
        config = {"key": "value", "number": 42}
        result = parser.serialize(config, ConfigFormat.YAML)
        assert "key: value" in result

    def test_serialize_json(self) -> None:
        parser = ConfigParser()
        config = {"key": "value"}
        result = parser.serialize(config, ConfigFormat.JSON)
        assert json.loads(result) == config

    def test_serialize_toml(self) -> None:
        parser = ConfigParser()
        config = {"key": "value"}
        result = parser.serialize(config, ConfigFormat.TOML)
        assert 'key = "value"' in result

    def test_serialize_auto_raises(self) -> None:
        parser = ConfigParser()
        with pytest.raises(ValueError):
            parser.serialize({}, ConfigFormat.AUTO)

    def test_write_file(self) -> None:
        parser = ConfigParser()
        config = {"key": "value"}
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "output.yaml"
            parser.write_file(config, path)
            assert path.exists()
            content = yaml.safe_load(path.read_text())
            assert content == config

    def test_detect_schema(self) -> None:
        parser = ConfigParser()
        config = {
            "name": "test",
            "count": 5,
            "enabled": True,
            "items": ["a", "b"],
        }
        schema = parser.detect_schema(config)
        assert schema is not None
        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["count"]["type"] == "integer"
        assert schema["properties"]["enabled"]["type"] == "boolean"
        assert schema["properties"]["items"]["type"] == "array"

    def test_detect_schema_empty(self) -> None:
        parser = ConfigParser()
        assert parser.detect_schema({}) is None

    def test_parse_empty_yaml(self) -> None:
        parser = ConfigParser()
        result = parser.parse_string("", ConfigFormat.YAML)
        assert result == {}

    def test_parse_empty_json(self) -> None:
        parser = ConfigParser()
        result = parser.parse_string("", ConfigFormat.JSON)
        assert result == {}


class TestSchemaValidator:
    """Tests for SchemaValidator."""

    def test_validate_json_schema_valid(self) -> None:
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        config = {"name": "test"}
        result = validator.validate_json_schema(config, schema)
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_json_schema_invalid(self) -> None:
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        config = {"other": "value"}
        result = validator.validate_json_schema(config, schema)
        assert not result.valid
        assert len(result.errors) > 0

    def test_validate_json_schema_type_error(self) -> None:
        validator = SchemaValidator()
        schema = {"type": "object", "properties": {"count": {"type": "integer"}}}
        config = {"count": "not a number"}
        result = validator.validate_json_schema(config, schema)
        assert not result.valid

    def test_validate_pydantic_valid(self) -> None:
        class TestModel(BaseModel):
            name: str
            count: int

        validator = SchemaValidator()
        config = {"name": "test", "count": 5}
        result = validator.validate_pydantic(config, TestModel)
        assert result.valid

    def test_validate_pydantic_invalid(self) -> None:
        class TestModel(BaseModel):
            name: str
            count: int

        validator = SchemaValidator()
        config = {"name": "test", "count": "not a number"}
        result = validator.validate_pydantic(config, TestModel)
        assert not result.valid

    def test_register_custom_validator(self) -> None:
        validator = SchemaValidator()

        def custom_validator(config: Dict[str, Any]) -> ValidationResult:
            result = ValidationResult(valid=True)
            if config.get("value", 0) < 0:
                result.add_error("Value must be non-negative")
            return result

        validator.register_custom_validator("non_negative", custom_validator)
        result = validator.validate_custom({"value": -1}, "non_negative")
        assert not result.valid

    def test_validate_custom_not_found(self) -> None:
        validator = SchemaValidator()
        with pytest.raises(KeyError):
            validator.validate_custom({}, "nonexistent")

    def test_validate_all(self) -> None:
        validator = SchemaValidator()
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        class TestModel(BaseModel):
            name: str

        config = {"name": "test"}
        result = validator.validate_all(
            config, json_schema=schema, pydantic_model=TestModel
        )
        assert result.valid

    def test_create_required_fields_validator(self) -> None:
        validator_func = create_required_fields_validator(["database.host"])
        result = validator_func({"database": {"host": "localhost"}})
        assert result.valid

        result = validator_func({"database": {}})
        assert not result.valid

    def test_create_type_validator(self) -> None:
        validator_func = create_type_validator({"port": int})
        result = validator_func({"port": 5432})
        assert result.valid

        result = validator_func({"port": "5432"})
        assert not result.valid

    def test_validation_result_add_warning(self) -> None:
        result = ValidationResult(valid=True)
        result.add_warning("This is a warning")
        assert result.valid
        assert len(result.warnings) == 1


class TestConfigGenerator:
    """Tests for ConfigGenerator."""

    def test_render_template(self) -> None:
        generator = ConfigGenerator()
        template = "Hello, {{ name }}!"
        result = generator.render_template(template, {"name": "World"})
        assert result == "Hello, World!"

    def test_render_template_complex(self) -> None:
        generator = ConfigGenerator()
        template = """
database:
  host: {{ db_host }}
  port: {{ db_port }}
"""
        result = generator.render_template(
            template, {"db_host": "localhost", "db_port": 5432}
        )
        assert "host: localhost" in result
        assert "port: 5432" in result

    def test_substitute_variables(self) -> None:
        generator = ConfigGenerator()
        config = {"host": "${HOST}", "port": "${PORT}"}
        variables = {"HOST": "localhost", "PORT": 5432}
        result = generator.substitute_variables(config, variables)
        assert result["host"] == "localhost"
        assert result["port"] == 5432

    def test_substitute_variables_nested(self) -> None:
        generator = ConfigGenerator()
        config = {"database": {"url": "postgres://${HOST}:${PORT}/db"}}
        variables = {"HOST": "localhost", "PORT": "5432"}
        result = generator.substitute_variables(config, variables)
        assert result["database"]["url"] == "postgres://localhost:5432/db"

    def test_substitute_env_variables(self) -> None:
        generator = ConfigGenerator()
        os.environ["TEST_HOST"] = "testhost"
        config = {"host": "${env:TEST_HOST}"}
        result = generator.substitute_env_variables(config)
        assert result["host"] == "testhost"
        del os.environ["TEST_HOST"]

    def test_substitute_env_variables_default(self) -> None:
        generator = ConfigGenerator()
        config = {"host": "${env:NONEXISTENT_VAR:-default_value}"}
        result = generator.substitute_env_variables(config)
        assert result["host"] == "default_value"

    def test_merge_configs(self) -> None:
        generator = ConfigGenerator()
        base = {"a": 1, "b": {"c": 2}}
        overlay = {"b": {"d": 3}, "e": 4}
        result = generator.merge_configs(base, overlay)
        assert result == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

    def test_merge_configs_shallow(self) -> None:
        generator = ConfigGenerator()
        base = {"a": {"b": 1}}
        overlay = {"a": {"c": 2}}
        result = generator.merge_configs(base, overlay, deep=False)
        assert result == {"a": {"c": 2}}

    def test_merge_environments(self) -> None:
        generator = ConfigGenerator()
        base = {"debug": False, "database": {"host": "localhost"}}
        env_configs = {
            "production": {"debug": False, "database": {"host": "prod-db"}},
            "development": {"debug": True},
        }
        result = generator.merge_environments(base, "production", env_configs)
        assert result["database"]["host"] == "prod-db"

    def test_merge_environments_not_found(self) -> None:
        generator = ConfigGenerator()
        with pytest.raises(KeyError):
            generator.merge_environments({}, "nonexistent", {})

    def test_generate_from_template(self) -> None:
        generator = ConfigGenerator()
        template = "key: {{ value }}"
        result = generator.generate_from_template(
            template, {"value": "test"}, "yaml"
        )
        assert result == {"key": "test"}

    def test_generate_config(self) -> None:
        generator = ConfigGenerator()
        base = {"host": "${HOST}"}
        result = generator.generate_config(
            base, variables={"HOST": "localhost"}, include_env_vars=False
        )
        assert result["host"] == "localhost"

    def test_render_template_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "test.j2"
            template_path.write_text("Hello, {{ name }}!")

            generator = ConfigGenerator(template_dir=tmpdir)
            result = generator.render_template_file("test.j2", {"name": "World"})
            assert result == "Hello, World!"

    def test_render_template_file_no_dir(self) -> None:
        generator = ConfigGenerator()
        with pytest.raises(RuntimeError):
            generator.render_template_file("test.j2", {})

    def test_merge_configs_empty(self) -> None:
        generator = ConfigGenerator()
        result = generator.merge_configs()
        assert result == {}

    def test_substitute_variables_list(self) -> None:
        generator = ConfigGenerator()
        config = {"hosts": ["${HOST1}", "${HOST2}"]}
        variables = {"HOST1": "host1", "HOST2": "host2"}
        result = generator.substitute_variables(config, variables)
        assert result["hosts"] == ["host1", "host2"]


class TestVersionManager:
    """Tests for VersionManager."""

    def test_commit_and_get(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            config = {"key": "value"}
            version = vm.commit("test", config, "author", "Initial commit")

            assert version.author == "author"
            assert version.message == "Initial commit"

            retrieved = vm.get_config("test", version.version_id)
            assert retrieved == config

    def test_get_latest_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            vm.commit("test", {"v": 1}, "author", "v1")
            v2 = vm.commit("test", {"v": 2}, "author", "v2")

            latest = vm.get_latest_version("test")
            assert latest is not None
            assert latest.version_id == v2.version_id

    def test_get_latest_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            vm.commit("test", {"v": 1}, "author", "v1")
            vm.commit("test", {"v": 2}, "author", "v2")

            latest = vm.get_latest_config("test")
            assert latest == {"v": 2}

    def test_list_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            vm.commit("test", {"v": 1}, "author", "v1")
            vm.commit("test", {"v": 2}, "author", "v2")

            versions = vm.list_versions("test")
            assert len(versions) == 2

    def test_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            v1 = vm.commit("test", {"a": 1, "b": 2}, "author", "v1")
            v2 = vm.commit("test", {"a": 1, "c": 3}, "author", "v2")

            diff = vm.diff("test", v1.version_id, v2.version_id)
            assert diff is not None
            assert len(diff.added) > 0 or len(diff.removed) > 0

    def test_diff_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            diff = vm.diff("test", "v1", "v2")
            assert diff is None

    def test_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            v1 = vm.commit("test", {"v": 1}, "author", "v1")
            vm.commit("test", {"v": 2}, "author", "v2")

            new_version = vm.rollback("test", v1.version_id, "author")
            assert new_version is not None

            latest = vm.get_latest_config("test")
            assert latest == {"v": 1}

    def test_rollback_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            result = vm.rollback("test", "nonexistent", "author")
            assert result is None

    def test_get_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            vm.commit("test", {"v": 1}, "author", "v1")
            vm.commit("test", {"v": 2}, "author", "v2")

            history = vm.get_history("test", limit=1)
            assert len(history) == 1

    def test_get_version_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            result = vm.get_version("test", "nonexistent")
            assert result is None

    def test_get_latest_version_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            result = vm.get_latest_version("nonexistent")
            assert result is None

    def test_get_latest_config_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vm = VersionManager(tmpdir)
            result = vm.get_latest_config("nonexistent")
            assert result is None


class TestDriftDetector:
    """Tests for DriftDetector."""

    def test_compare_no_drift(self) -> None:
        detector = DriftDetector()
        desired = {"key": "value"}
        live = {"key": "value"}
        report = detector.compare(desired, live)
        assert not report.has_drift

    def test_compare_with_drift(self) -> None:
        detector = DriftDetector()
        desired = {"key": "desired_value"}
        live = {"key": "live_value"}
        report = detector.compare(desired, live)
        assert report.has_drift
        assert len(report.drift_items) > 0

    def test_compare_added_item(self) -> None:
        detector = DriftDetector()
        desired = {"a": 1}
        live = {"a": 1, "b": 2}
        report = detector.compare(desired, live)
        assert report.has_drift
        assert any(item.drift_type == "added" for item in report.drift_items)

    def test_compare_removed_item(self) -> None:
        detector = DriftDetector()
        desired = {"a": 1, "b": 2}
        live = {"a": 1}
        report = detector.compare(desired, live)
        assert report.has_drift
        assert any(item.drift_type == "removed" for item in report.drift_items)

    def test_severity_rules(self) -> None:
        detector = DriftDetector()
        detector.set_severity_rule("password", DriftSeverity.CRITICAL)
        desired = {"password": "secret"}
        live = {"password": "different"}
        report = detector.compare(desired, live)
        assert any(
            item.severity == DriftSeverity.CRITICAL for item in report.drift_items
        )

    def test_ignore_paths(self) -> None:
        detector = DriftDetector()
        detector.add_ignore_path("timestamp")
        desired = {"key": "value", "timestamp": "2024-01-01"}
        live = {"key": "value", "timestamp": "2024-01-02"}
        report = detector.compare(desired, live)
        assert not report.has_drift

    def test_register_live_state_fetcher(self) -> None:
        detector = DriftDetector()

        def fetcher() -> Dict[str, Any]:
            return {"key": "live_value"}

        detector.register_live_state_fetcher("test", fetcher)
        report = detector.detect("test", {"key": "desired_value"})
        assert report.has_drift

    def test_detect_no_fetcher(self) -> None:
        detector = DriftDetector()
        with pytest.raises(KeyError):
            detector.detect("nonexistent", {})

    def test_generate_reconciliation_plan(self) -> None:
        detector = DriftDetector()
        desired = {"a": 1}
        live = {"a": 2, "b": 3}
        report = detector.compare(desired, live)
        plan = detector.generate_reconciliation_plan(report)
        assert len(plan) > 0
        assert any(action["action"] == "remove" for action in plan)
        assert any(action["action"] == "update" for action in plan)

    def test_drift_report_to_dict(self) -> None:
        report = DriftReport(
            config_name="test",
            timestamp=datetime.now(),
            has_drift=False,
        )
        result = report.to_dict()
        assert "config_name" in result
        assert "timestamp" in result
        assert "has_drift" in result

    def test_type_change_detection(self) -> None:
        detector = DriftDetector()
        desired = {"value": 123}
        live = {"value": "123"}
        report = detector.compare(desired, live)
        assert report.has_drift
        assert any(item.drift_type == "type_changed" for item in report.drift_items)


class TestSecretsManager:
    """Tests for SecretsManager."""

    def test_env_backend(self) -> None:
        os.environ["TEST_SECRET"] = "secret_value"
        backend = EnvBackend()
        value = backend.get_secret("TEST_SECRET")
        assert value == "secret_value"
        del os.environ["TEST_SECRET"]

    def test_env_backend_with_prefix(self) -> None:
        os.environ["APP_SECRET"] = "secret_value"
        backend = EnvBackend(prefix="APP_")
        value = backend.get_secret("SECRET")
        assert value == "secret_value"
        del os.environ["APP_SECRET"]

    def test_env_backend_list(self) -> None:
        os.environ["TEST_A"] = "a"
        os.environ["TEST_B"] = "b"
        backend = EnvBackend()
        secrets = backend.list_secrets("TEST_")
        assert "TEST_A" in secrets
        assert "TEST_B" in secrets
        del os.environ["TEST_A"]
        del os.environ["TEST_B"]

    def test_secrets_manager_register_backend(self) -> None:
        manager = SecretsManager()
        backend = EnvBackend()
        manager.register_backend("env", backend, default=True)
        os.environ["MY_SECRET"] = "value"
        value = manager.get_secret("MY_SECRET")
        assert value == "value"
        del os.environ["MY_SECRET"]

    def test_secrets_manager_backend_not_found(self) -> None:
        manager = SecretsManager()
        with pytest.raises(KeyError):
            manager.get_secret("path", backend="nonexistent")

    def test_substitute_secrets(self) -> None:
        manager = SecretsManager()
        backend = EnvBackend()
        manager.register_backend("env", backend)
        os.environ["DB_PASSWORD"] = "secret123"

        config = {"password": "${secret:DB_PASSWORD}"}
        result = manager.substitute_secrets(config)
        assert result["password"] == "secret123"
        del os.environ["DB_PASSWORD"]

    def test_substitute_secrets_nested(self) -> None:
        manager = SecretsManager()
        backend = EnvBackend()
        manager.register_backend("env", backend)
        os.environ["API_KEY"] = "key123"

        config = {"api": {"key": "${secret:API_KEY}"}}
        result = manager.substitute_secrets(config)
        assert result["api"]["key"] == "key123"
        del os.environ["API_KEY"]

    def test_mask_secrets(self) -> None:
        manager = SecretsManager()
        config = {"database": {"password": "secret123", "host": "localhost"}}
        result = manager.mask_secrets(config, ["database.password"])
        assert result["database"]["password"] == "***MASKED***"
        assert result["database"]["host"] == "localhost"

    def test_mask_secrets_custom_mask(self) -> None:
        manager = SecretsManager()
        config = {"password": "secret"}
        result = manager.mask_secrets(config, ["password"], mask="[REDACTED]")
        assert result["password"] == "[REDACTED]"

    def test_substitute_secrets_list(self) -> None:
        manager = SecretsManager()
        backend = EnvBackend()
        manager.register_backend("env", backend)
        os.environ["KEY1"] = "val1"

        config = {"keys": ["${secret:KEY1}"]}
        result = manager.substitute_secrets(config)
        assert result["keys"] == ["val1"]
        del os.environ["KEY1"]


class TestVaultBackend:
    """Tests for VaultBackend."""

    def test_vault_get_secret_mock(self) -> None:
        from .secrets_manager import VaultBackend

        backend = VaultBackend(url="http://localhost:8200", token="test-token")

        mock_client = MagicMock()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "secret123"}}
        }

        with patch.object(backend, "_get_client", return_value=mock_client):
            result = backend.get_secret("secret/myapp")
            assert result == "secret123"

    def test_vault_get_secret_with_key(self) -> None:
        from .secrets_manager import VaultBackend

        backend = VaultBackend()

        mock_client = MagicMock()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"password": "secret123"}}
        }

        with patch.object(backend, "_get_client", return_value=mock_client):
            result = backend.get_secret("secret/myapp#password")
            assert result == "secret123"

    def test_vault_list_secrets(self) -> None:
        from .secrets_manager import VaultBackend

        backend = VaultBackend()

        mock_client = MagicMock()
        mock_client.secrets.kv.v2.list_secrets.return_value = {
            "data": {"keys": ["secret1", "secret2"]}
        }

        with patch.object(backend, "_get_client", return_value=mock_client):
            result = backend.list_secrets("secret/")
            assert result == ["secret1", "secret2"]


class TestAWSSecretsBackend:
    """Tests for AWSSecretsBackend."""

    def test_aws_get_secret_mock(self) -> None:
        from .secrets_manager import AWSSecretsBackend

        backend = AWSSecretsBackend(region_name="us-east-1")

        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {"SecretString": "secret123"}

        with patch.object(backend, "_get_client", return_value=mock_client):
            result = backend.get_secret("my-secret")
            assert result == "secret123"

    def test_aws_get_secret_with_key(self) -> None:
        from .secrets_manager import AWSSecretsBackend

        backend = AWSSecretsBackend()

        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": '{"password": "secret123"}'
        }

        with patch.object(backend, "_get_client", return_value=mock_client):
            result = backend.get_secret("my-secret#password")
            assert result == "secret123"


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_validate_basic(self) -> None:
        from click.testing import CliRunner

        from .config_cli import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            Path("config.yaml").write_text("key: value")
            result = runner.invoke(cli, ["validate", "config.yaml"])
            assert result.exit_code == 0
            assert "Parsed configuration" in result.output

    def test_cli_validate_with_schema(self) -> None:
        from click.testing import CliRunner

        from .config_cli import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            Path("config.yaml").write_text("name: test")
            schema = {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            }
            Path("schema.json").write_text(json.dumps(schema))

            result = runner.invoke(
                cli, ["validate", "config.yaml", "--schema", "schema.json"]
            )
            assert result.exit_code == 0
            assert "Validation passed" in result.output

    def test_cli_generate(self) -> None:
        from click.testing import CliRunner

        from .config_cli import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            Path("template.j2").write_text("key: {{ value }}")
            Path("vars.yaml").write_text("value: test")

            result = runner.invoke(
                cli, ["generate", "template.j2", "--vars", "vars.yaml"]
            )
            assert result.exit_code == 0
            assert "key: test" in result.output

    def test_cli_diff(self) -> None:
        from click.testing import CliRunner

        from .config_cli import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            Path("config1.yaml").write_text("key: value1")
            Path("config2.yaml").write_text("key: value2")

            result = runner.invoke(cli, ["diff", "config1.yaml", "config2.yaml"])
            assert result.exit_code == 0
            assert "Differences found" in result.output or "Changed" in result.output

    def test_cli_diff_no_changes(self) -> None:
        from click.testing import CliRunner

        from .config_cli import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            Path("config1.yaml").write_text("key: value")
            Path("config2.yaml").write_text("key: value")

            result = runner.invoke(cli, ["diff", "config1.yaml", "config2.yaml"])
            assert result.exit_code == 0
            assert "No differences found" in result.output

    def test_cli_schema_generate(self) -> None:
        from click.testing import CliRunner

        from .config_cli import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            Path("config.yaml").write_text("name: test\ncount: 5")

            result = runner.invoke(cli, ["schema", "config.yaml"])
            assert result.exit_code == 0
            assert '"type": "object"' in result.output

    def test_cli_history(self) -> None:
        from click.testing import CliRunner

        from .config_cli import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            vm = VersionManager(".")
            vm.commit("test", {"key": "value"}, "author", "Initial")

            result = runner.invoke(cli, ["history", "test", "--repo", "."])
            assert result.exit_code == 0

    def test_cli_drift(self) -> None:
        from click.testing import CliRunner

        from .config_cli import cli

        runner = CliRunner()

        with runner.isolated_filesystem():
            Path("desired.yaml").write_text("key: desired")
            Path("live.yaml").write_text("key: live")

            result = runner.invoke(cli, ["drift", "desired.yaml", "live.yaml"])
            assert result.exit_code == 0
            assert "Drift detected" in result.output or "drift" in result.output.lower()
