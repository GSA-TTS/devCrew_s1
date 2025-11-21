"""Command-line interface for configuration management."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click

from .config_generator import ConfigGenerator
from .config_parser import ConfigFormat, ConfigParser
from .drift_detector import DriftDetector
from .schema_validator import SchemaValidator
from .secrets_manager import EnvBackend, SecretsManager
from .version_manager import VersionManager


@click.group()
@click.version_option(version="1.0.0")
def cli() -> None:
    """Configuration Management Platform CLI for devCrew_s1."""
    pass


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option(
    "--schema",
    "-s",
    type=click.Path(exists=True),
    help="JSON Schema file to validate against",
)
@click.option("--format", "-f", type=click.Choice(["yaml", "json", "toml"]))
def validate(
    config_file: str,
    schema: Optional[str],
    format: Optional[str],
) -> None:
    """Validate a configuration file.

    CONFIG_FILE: Path to the configuration file to validate.
    """
    parser = ConfigParser()
    validator = SchemaValidator()

    try:
        if format:
            format_type = ConfigFormat(format)
        else:
            format_type = ConfigFormat.AUTO

        config = parser.parse_file(config_file, format_type)
        click.echo(f"Parsed configuration from: {config_file}")

        if schema:
            schema_data = json.loads(Path(schema).read_text(encoding="utf-8"))
            result = validator.validate_json_schema(config, schema_data)

            if result.valid:
                click.echo(click.style("Validation passed", fg="green"))
            else:
                click.echo(click.style("Validation failed:", fg="red"))
                for error in result.errors:
                    click.echo(f"  - {error}")
                sys.exit(1)
        else:
            click.echo("No schema provided. Syntax validation passed.")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("template_file", type=click.Path(exists=True))
@click.option(
    "--vars",
    "-v",
    type=click.Path(exists=True),
    help="Variables file (YAML/JSON)",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json", "toml"]),
    default="yaml",
)
@click.option("--env", "-e", multiple=True, help="Environment variables (KEY=VALUE)")
def generate(
    template_file: str,
    vars: Optional[str],
    output: Optional[str],
    format: str,
    env: tuple,
) -> None:
    """Generate configuration from a template.

    TEMPLATE_FILE: Path to the Jinja2 template file.
    """
    parser = ConfigParser()
    generator = ConfigGenerator()

    try:
        template_content = Path(template_file).read_text(encoding="utf-8")
        variables: Dict[str, Any] = {}

        if vars:
            variables = parser.parse_file(vars)

        for env_var in env:
            if "=" in env_var:
                key, value = env_var.split("=", 1)
                variables[key] = value

        rendered = generator.render_template(template_content, variables)

        if output:
            Path(output).write_text(rendered, encoding="utf-8")
            click.echo(f"Generated configuration written to: {output}")
        else:
            click.echo(rendered)

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["yaml", "json", "toml"]))
def diff(file1: str, file2: str, format: Optional[str]) -> None:
    """Show differences between two configuration files.

    FILE1: First configuration file.
    FILE2: Second configuration file.
    """
    from deepdiff import DeepDiff

    parser = ConfigParser()

    try:
        format_type = ConfigFormat(format) if format else ConfigFormat.AUTO

        config1 = parser.parse_file(file1, format_type)
        config2 = parser.parse_file(file2, format_type)

        differences = DeepDiff(config1, config2, ignore_order=True)

        if not differences:
            click.echo(click.style("No differences found", fg="green"))
            return

        click.echo(click.style("Differences found:", fg="yellow"))

        if "dictionary_item_added" in differences:
            click.echo("\nAdded:")
            for item in differences["dictionary_item_added"]:
                click.echo(f"  + {item}")

        if "dictionary_item_removed" in differences:
            click.echo("\nRemoved:")
            for item in differences["dictionary_item_removed"]:
                click.echo(f"  - {item}")

        if "values_changed" in differences:
            click.echo("\nChanged:")
            for path, change in differences["values_changed"].items():
                click.echo(f"  ~ {path}:")
                click.echo(f"    old: {change['old_value']}")
                click.echo(f"    new: {change['new_value']}")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("config_name")
@click.argument("target_version")
@click.option(
    "--repo",
    "-r",
    type=click.Path(exists=True),
    default=".",
    help="Repository path",
)
@click.option("--author", "-a", default="cli", help="Author name")
@click.option("--message", "-m", help="Rollback message")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
def rollback(
    config_name: str,
    target_version: str,
    repo: str,
    author: str,
    message: Optional[str],
    dry_run: bool,
) -> None:
    """Rollback configuration to a previous version.

    CONFIG_NAME: Name of the configuration.
    TARGET_VERSION: Version ID to rollback to.
    """
    try:
        vm = VersionManager(repo)

        target_config = vm.get_config(config_name, target_version)
        if target_config is None:
            click.echo(click.style(f"Version not found: {target_version}", fg="red"))
            sys.exit(1)

        if dry_run:
            click.echo(f"Would rollback {config_name} to version {target_version}")
            click.echo("Configuration content:")
            click.echo(json.dumps(target_config, indent=2))
            return

        new_version = vm.rollback(config_name, target_version, author, message)
        if new_version:
            click.echo(
                click.style(
                    f"Rolled back to {target_version}. "
                    f"New version: {new_version.version_id}",
                    fg="green",
                )
            )
        else:
            click.echo(click.style("Rollback failed", fg="red"))
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.argument("live_file", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["yaml", "json", "toml"]))
@click.option("--output", "-o", type=click.Path(), help="Output report file")
def drift(
    config_file: str,
    live_file: str,
    format: Optional[str],
    output: Optional[str],
) -> None:
    """Detect configuration drift between desired and live state.

    CONFIG_FILE: Desired configuration file.
    LIVE_FILE: Live configuration file.
    """
    parser = ConfigParser()
    detector = DriftDetector()

    try:
        format_type = ConfigFormat(format) if format else ConfigFormat.AUTO

        desired = parser.parse_file(config_file, format_type)
        live = parser.parse_file(live_file, format_type)

        report = detector.compare(desired, live, Path(config_file).stem)

        if output:
            Path(output).write_text(
                json.dumps(report.to_dict(), indent=2),
                encoding="utf-8",
            )
            click.echo(f"Drift report written to: {output}")

        if report.has_drift:
            click.echo(click.style("Drift detected:", fg="yellow"))
            click.echo(f"  Critical: {report.critical_count}")
            click.echo(f"  Warning: {report.warning_count}")
            click.echo(f"  Total: {len(report.drift_items)}")

            for item in report.drift_items:
                color = "red" if item.severity.value == "critical" else "yellow"
                click.echo(click.style(f"\n  [{item.severity.value}] {item.path}", fg=color))
                click.echo(f"    Type: {item.drift_type}")
                click.echo(f"    Expected: {item.expected}")
                click.echo(f"    Actual: {item.actual}")
        else:
            click.echo(click.style("No drift detected", fg="green"))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("config_name")
@click.option(
    "--repo",
    "-r",
    type=click.Path(exists=True),
    default=".",
    help="Repository path",
)
@click.option("--limit", "-n", type=int, default=10, help="Number of versions to show")
def history(config_name: str, repo: str, limit: int) -> None:
    """Show version history for a configuration.

    CONFIG_NAME: Name of the configuration.
    """
    try:
        vm = VersionManager(repo)
        history_list = vm.get_history(config_name, limit)

        if not history_list:
            click.echo(f"No versions found for: {config_name}")
            return

        click.echo(f"Version history for {config_name}:")
        for entry in history_list:
            click.echo(f"\n  {entry['version_id']}")
            click.echo(f"    Date: {entry['timestamp']}")
            click.echo(f"    Author: {entry['author']}")
            click.echo(f"    Message: {entry['message']}")
            click.echo(f"    Hash: {entry['config_hash']}")

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output schema file")
def schema(config_file: str, output: Optional[str]) -> None:
    """Generate JSON Schema from a configuration file.

    CONFIG_FILE: Configuration file to analyze.
    """
    parser = ConfigParser()

    try:
        config = parser.parse_file(config_file)
        generated_schema = parser.detect_schema(config)

        if generated_schema is None:
            click.echo("Could not generate schema from empty configuration")
            return

        schema_json = json.dumps(generated_schema, indent=2)

        if output:
            Path(output).write_text(schema_json, encoding="utf-8")
            click.echo(f"Schema written to: {output}")
        else:
            click.echo(schema_json)

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
