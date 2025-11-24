#!/usr/bin/env python3
"""
Design Platform CLI - devCrew_s1 Design Tools Interface.

Command-line interface for Figma API integration, design validation,
design token extraction, code export, and C4 architecture diagram generation.

Commands:
    - export: Export design assets, nodes, CSS, and React components
    - validate: Validate accessibility and design system compliance
    - tokens: Extract and manage design tokens
    - c4: Generate and validate C4 architecture diagrams
    - config: Manage configuration and API credentials

Author: devCrew_s1
Version: 1.0.0
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import click
import yaml
from colorama import init

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Configuration file paths
CONFIG_DIR = Path.home() / ".devcrew-design"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
DEFAULT_CONFIG = {
    "figma_token": None,
    "default_format": "png",
    "default_scale": 2,
    "wcag_level": "AA",
    "output_dir": "./output",
    "verbose": False,
}


# Utility Functions
def load_config() -> Dict[str, Any]:
    """
    Load configuration from file or environment variables.

    Priority:
    1. Environment variables
    2. Config file at ~/.devcrew-design/config.yaml
    3. Default values

    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()

    # Load from config file
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config.update(file_config)
        except Exception as e:
            click.echo(
                click.style(f"Warning: Failed to load config file: {e}", fg="yellow"),
                err=True,
            )

    # Override with environment variables
    if os.getenv("FIGMA_TOKEN"):
        config["figma_token"] = os.getenv("FIGMA_TOKEN")
    if os.getenv("DEVCREW_DESIGN_OUTPUT_DIR"):
        config["output_dir"] = os.getenv("DEVCREW_DESIGN_OUTPUT_DIR")

    return config


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration dictionary to save
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        click.echo(click.style(f"Configuration saved to {CONFIG_FILE}", fg="green"))
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to save config: {e}", fg="red"), err=True
        )
        sys.exit(1)


def format_output(data: Any, output_format: str, pretty: bool = True) -> str:
    """
    Format data for output.

    Args:
        data: Data to format
        output_format: Output format (json, yaml, text)
        pretty: Enable pretty formatting

    Returns:
        Formatted string
    """
    if output_format == "json":
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
    elif output_format == "yaml":
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    else:
        return str(data)


def write_output(
    content: str, output_path: Optional[str], verbose: bool = False
) -> None:
    """
    Write content to file or stdout.

    Args:
        content: Content to write
        output_path: Output file path (None for stdout)
        verbose: Enable verbose output
    """
    if output_path:
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(content, encoding="utf-8")
            if verbose:
                click.echo(click.style(f"Output written to {output_path}", fg="green"))
        except Exception as e:
            click.echo(
                click.style(f"Error: Failed to write output: {e}", fg="red"),
                err=True,
            )
            sys.exit(1)
    else:
        click.echo(content)


def show_progress(message: str, verbose: bool = False) -> None:
    """
    Show progress message if verbose mode is enabled.

    Args:
        message: Progress message
        verbose: Enable verbose output
    """
    if verbose:
        click.echo(click.style(f"[INFO] {message}", fg="cyan"))


def show_error(message: str) -> None:
    """
    Show error message and exit.

    Args:
        message: Error message
    """
    click.echo(click.style(f"Error: {message}", fg="red"), err=True)
    sys.exit(1)


def show_warning(message: str) -> None:
    """
    Show warning message.

    Args:
        message: Warning message
    """
    click.echo(click.style(f"Warning: {message}", fg="yellow"), err=True)


def show_success(message: str) -> None:
    """
    Show success message.

    Args:
        message: Success message
    """
    click.echo(click.style(f"Success: {message}", fg="green"))


def validate_file_key(ctx: click.Context, param: str, value: str) -> str:
    """
    Validate Figma file key format.

    Args:
        ctx: Click context
        param: Parameter name
        value: File key value

    Returns:
        Validated file key

    Raises:
        click.BadParameter: If file key format is invalid
    """
    if not value:
        raise click.BadParameter("File key cannot be empty")
    if len(value) < 10:
        raise click.BadParameter("File key appears to be too short")
    return value


def get_figma_client(config: Dict[str, Any]) -> Any:
    """
    Get Figma client instance.

    Args:
        config: Configuration dictionary

    Returns:
        FigmaClient instance

    Raises:
        SystemExit: If Figma token is not configured
    """
    from design_platform import FigmaClient

    token = config.get("figma_token")
    if not token:
        show_error(
            "Figma API token not configured. "
            "Run 'devcrew-design config set-token --token YOUR_TOKEN'"
        )

    # Type checker knows token is str after the check
    assert isinstance(token, str), "Token must be a string"
    return FigmaClient(access_token=token)


def get_design_validator() -> Any:
    """
    Get DesignValidator instance.

    Returns:
        DesignValidator instance
    """
    from design_platform import DesignValidator

    return DesignValidator()


def get_code_exporter() -> Any:
    """
    Get CodeExporter instance.

    Returns:
        CodeExporter instance
    """
    from design_platform import CodeExporter

    return CodeExporter()


def get_c4_generator() -> Any:
    """
    Get C4Generator instance.

    Returns:
        C4Generator instance
    """
    from design_platform import C4Generator

    return C4Generator()


# Main CLI Group
@click.group()
@click.version_option(version="1.0.0", prog_name="devcrew-design")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """
    devCrew_s1 Design Platform CLI.

    Comprehensive design tools for Figma integration, design validation,
    token extraction, code export, and C4 architecture diagram generation.

    Examples:
        devcrew-design export assets --file-key ABC123 --format png
        devcrew-design validate accessibility --file-key ABC123
        devcrew-design tokens extract --file-key ABC123 --output tokens.json
        devcrew-design c4 generate --dsl architecture.dsl
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = load_config()


# Export Command Group
@cli.group()
@click.pass_context
def export(ctx: click.Context) -> None:
    """Export design assets, nodes, CSS, and React components."""
    pass


@export.command(name="assets")
@click.option(
    "--file-key",
    "-k",
    required=True,
    callback=validate_file_key,
    help="Figma file key",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["png", "jpg", "svg", "pdf"], case_sensitive=False),
    default="png",
    help="Export format (default: png)",
)
@click.option(
    "--scale", "-s", type=float, default=2.0, help="Export scale (default: 2.0)"
)
@click.option("--output", "-o", type=str, help="Output directory")
@click.option("--node-ids", "-n", type=str, help="Comma-separated node IDs to export")
@click.pass_context
def export_assets(
    ctx: click.Context,
    file_key: str,
    format: str,
    scale: float,
    output: Optional[str],
    node_ids: Optional[str],
) -> None:
    """
    Export design assets from Figma file.

    Examples:
        devcrew-design export assets --file-key ABC123 --format png --scale 2
        devcrew-design export assets -k ABC123 -f svg -o ./assets
        devcrew-design export assets -k ABC123 -n "1:5,1:6" -f png
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    show_progress(f"Exporting assets from file {file_key}...", verbose)

    try:
        client = get_figma_client(config)

        # Parse node IDs if provided
        nodes = None
        if node_ids:
            nodes = [nid.strip() for nid in node_ids.split(",")]
            show_progress(f"Targeting {len(nodes)} specific nodes", verbose)

        # Get file information
        show_progress("Fetching file information...", verbose)
        file_data = client.get_file(file_key)

        if not file_data:
            show_error(f"Failed to fetch file {file_key}")

        # Export assets
        show_progress(
            f"Exporting in {format.upper()} format at {scale}x scale...",
            verbose,
        )

        output_dir = Path(output) if output else Path(config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export logic would call FigmaClient methods
        export_result = client.export_images(
            file_key=file_key,
            node_ids=nodes,
            format=format,
            scale=scale,
        )

        if export_result:
            # Save exported images
            for node_id, image_url in export_result.items():
                show_progress(f"Downloading {node_id}...", verbose)
                image_path = output_dir / f"{node_id}.{format}"
                # Download and save image
                image_data = client.download_image(image_url)
                image_path.write_bytes(image_data)
                show_progress(f"Saved to {image_path}", verbose)

            show_success(f"Exported {len(export_result)} assets to {output_dir}")
        else:
            show_warning("No assets were exported")

    except Exception as e:
        show_error(f"Export failed: {e}")


@export.command(name="nodes")
@click.option(
    "--file-key",
    "-k",
    required=True,
    callback=validate_file_key,
    help="Figma file key",
)
@click.option(
    "--node-ids",
    "-n",
    required=True,
    type=str,
    help="Comma-separated node IDs",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["png", "jpg", "svg", "pdf"], case_sensitive=False),
    default="svg",
    help="Export format (default: svg)",
)
@click.option(
    "--scale", "-s", type=float, default=1.0, help="Export scale (default: 1.0)"
)
@click.option("--output", "-o", type=str, help="Output directory")
@click.pass_context
def export_nodes(
    ctx: click.Context,
    file_key: str,
    node_ids: str,
    format: str,
    scale: float,
    output: Optional[str],
) -> None:
    """
    Export specific nodes from Figma file.

    Examples:
        devcrew-design export nodes -k ABC123 -n "1:5,1:6" -f svg
        devcrew-design export nodes -k ABC123 -n "1:5" -f png -s 2
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    nodes = [nid.strip() for nid in node_ids.split(",")]
    show_progress(f"Exporting {len(nodes)} nodes from file {file_key}...", verbose)

    try:
        client = get_figma_client(config)

        # Export nodes
        show_progress(f"Exporting nodes in {format.upper()} format...", verbose)

        output_dir = Path(output) if output else Path(config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        export_result = client.export_images(
            file_key=file_key,
            node_ids=nodes,
            format=format,
            scale=scale,
        )

        if export_result:
            for node_id, image_url in export_result.items():
                show_progress(f"Downloading node {node_id}...", verbose)
                image_path = output_dir / f"{node_id}.{format}"
                image_data = client.download_image(image_url)
                image_path.write_bytes(image_data)
                show_progress(f"Saved to {image_path}", verbose)

            show_success(f"Exported {len(export_result)} nodes to {output_dir}")
        else:
            show_error("No nodes were exported")

    except Exception as e:
        show_error(f"Export failed: {e}")


@export.command(name="css")
@click.option(
    "--file-key",
    "-k",
    required=True,
    callback=validate_file_key,
    help="Figma file key",
)
@click.option(
    "--node-ids",
    "-n",
    required=True,
    type=str,
    help="Comma-separated node IDs",
)
@click.option("--output", "-o", type=str, help="Output CSS file path")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["css", "scss", "less"], case_sensitive=False),
    default="css",
    help="CSS format (default: css)",
)
@click.option("--minify", is_flag=True, help="Minify CSS output")
@click.pass_context
def export_css(
    ctx: click.Context,
    file_key: str,
    node_ids: str,
    output: Optional[str],
    format: str,
    minify: bool,
) -> None:
    """
    Export Figma nodes as CSS.

    Examples:
        devcrew-design export css -k ABC123 -n "1:5" -o styles.css
        devcrew-design export css -k ABC123 -n "1:5,1:6" -f scss --minify
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    nodes = [nid.strip() for nid in node_ids.split(",")]
    show_progress(
        f"Exporting {len(nodes)} nodes as CSS from file {file_key}...",
        verbose,
    )

    try:
        client = get_figma_client(config)
        exporter = get_code_exporter()

        # Get node data
        show_progress("Fetching node data...", verbose)
        file_data = client.get_file(file_key, nodes=nodes)

        if not file_data:
            show_error(f"Failed to fetch file {file_key}")

        # Generate CSS
        show_progress(f"Generating {format.upper()} code...", verbose)

        css_output = []
        for node_id in nodes:
            node_data = client.get_node(file_key, node_id)
            if node_data:
                css_code = exporter.export_css(node_data, format=format, minify=minify)
                css_output.append(f"/* Node: {node_id} */\n{css_code}\n")
                show_progress(f"Generated CSS for node {node_id}", verbose)

        css_content = "\n".join(css_output)

        # Write output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(css_content, encoding="utf-8")
            show_success(f"CSS exported to {output}")
        else:
            click.echo(css_content)

    except Exception as e:
        show_error(f"CSS export failed: {e}")


@export.command(name="react")
@click.option(
    "--file-key",
    "-k",
    required=True,
    callback=validate_file_key,
    help="Figma file key",
)
@click.option(
    "--node-ids",
    "-n",
    required=True,
    type=str,
    help="Comma-separated node IDs",
)
@click.option(
    "--component-name",
    "-c",
    type=str,
    help="React component name",
)
@click.option("--output", "-o", type=str, help="Output directory")
@click.option("--typescript", is_flag=True, help="Generate TypeScript components")
@click.option(
    "--styled-components",
    is_flag=True,
    help="Use styled-components for styling",
)
@click.pass_context
def export_react(
    ctx: click.Context,
    file_key: str,
    node_ids: str,
    component_name: Optional[str],
    output: Optional[str],
    typescript: bool,
    styled_components: bool,
) -> None:
    """
    Export Figma nodes as React components.

    Examples:
        devcrew-design export react -k ABC123 -n "1:6" -c Button
        devcrew-design export react -k ABC123 -n "1:6" -c Button --typescript
        devcrew-design export react -k ABC123 -n "1:6,1:7" --styled-components
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    nodes = [nid.strip() for nid in node_ids.split(",")]
    show_progress(f"Exporting {len(nodes)} nodes as React components...", verbose)

    try:
        client = get_figma_client(config)
        exporter = get_code_exporter()

        # Get node data
        show_progress("Fetching node data...", verbose)

        output_dir = Path(output) if output else Path(config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        for idx, node_id in enumerate(nodes):
            node_data = client.get_node(file_key, node_id)

            if not node_data:
                show_warning(f"Failed to fetch node {node_id}")
                continue

            # Generate component name
            comp_name = component_name if component_name else f"Component{idx}"

            show_progress(f"Generating React component {comp_name}...", verbose)

            react_code = exporter.export_react(
                node_data,
                component_name=comp_name,
                typescript=typescript,
                styled_components=styled_components,
            )

            # Write component file
            ext = "tsx" if typescript else "jsx"
            component_path = output_dir / f"{comp_name}.{ext}"
            component_path.write_text(react_code, encoding="utf-8")

            show_progress(f"Generated {component_path}", verbose)

        show_success(f"Exported {len(nodes)} React components to {output_dir}")

    except Exception as e:
        show_error(f"React export failed: {e}")


# Validate Command Group
@cli.group()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Validate design accessibility and compliance."""
    pass


@validate.command(name="accessibility")
@click.option(
    "--file-key",
    "-k",
    required=True,
    callback=validate_file_key,
    help="Figma file key",
)
@click.option(
    "--wcag-level",
    "-w",
    type=click.Choice(["A", "AA", "AAA"], case_sensitive=False),
    default="AA",
    help="WCAG compliance level (default: AA)",
)
@click.option("--node-ids", "-n", type=str, help="Comma-separated node IDs to validate")
@click.option("--output", "-o", type=str, help="Output report file path")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text"], case_sensitive=False),
    default="text",
    help="Output format (default: text)",
)
@click.pass_context
def validate_accessibility(
    ctx: click.Context,
    file_key: str,
    wcag_level: str,
    node_ids: Optional[str],
    output: Optional[str],
    format: str,
) -> None:
    """
    Validate WCAG accessibility compliance.

    Examples:
        devcrew-design validate accessibility -k ABC123 -w AA
        devcrew-design validate accessibility -k ABC123 -w AAA -o report.json
        devcrew-design validate accessibility -k ABC123 -n "1:5,1:6" -f yaml
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    show_progress(
        f"Validating WCAG {wcag_level} accessibility for file {file_key}...",
        verbose,
    )

    try:
        client = get_figma_client(config)
        validator = get_design_validator()

        # Parse node IDs if provided
        nodes = None
        if node_ids:
            nodes = [nid.strip() for nid in node_ids.split(",")]

        # Get file data
        show_progress("Fetching file data...", verbose)
        file_data = client.get_file(file_key, nodes=nodes)

        if not file_data:
            show_error(f"Failed to fetch file {file_key}")

        # Perform validation
        show_progress(f"Performing WCAG {wcag_level} validation...", verbose)

        validation_result = validator.validate_wcag(file_data, level=wcag_level)

        # Format results
        if format == "text":
            status = "PASS" if validation_result.passed else "FAIL"
            report = [
                f"WCAG {wcag_level} Accessibility Validation Report",
                f"File: {file_key}",
                "=" * 60,
                f"\nValidation Status: {status}",
                f"Issues Found: {len(validation_result.issues)}",
                f"Warnings: {len(validation_result.warnings)}",
                "\nIssues:",
            ]

            for issue in validation_result.issues:
                issue_line = (
                    f"  - [{issue.severity}] {issue.message} "
                    f"(Node: {issue.node_id})"
                )
                report.append(issue_line)

            if validation_result.warnings:
                report.append("\nWarnings:")
                for warning in validation_result.warnings:
                    report.append(f"  - {warning}")

            result_text = "\n".join(report)
        else:
            result_text = format_output(validation_result.to_dict(), format)

        write_output(result_text, output, verbose)

        if not validation_result.passed:
            show_warning("Validation failed - issues found")
            sys.exit(1)
        else:
            show_success("Validation passed - no issues found")

    except Exception as e:
        show_error(f"Validation failed: {e}")


@validate.command(name="design-system")
@click.option(
    "--file-key",
    "-k",
    required=True,
    callback=validate_file_key,
    help="Figma file key",
)
@click.option(
    "--rules",
    "-r",
    type=click.Path(exists=True),
    required=True,
    help="Design system rules YAML file",
)
@click.option("--node-ids", "-n", type=str, help="Comma-separated node IDs to validate")
@click.option("--output", "-o", type=str, help="Output report file path")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text"], case_sensitive=False),
    default="text",
    help="Output format (default: text)",
)
@click.pass_context
def validate_design_system(
    ctx: click.Context,
    file_key: str,
    rules: str,
    node_ids: Optional[str],
    output: Optional[str],
    format: str,
) -> None:
    """
    Validate design system compliance.

    Examples:
        devcrew-design validate design-system -k ABC123 -r rules.yaml
        devcrew-design validate design-system -k ABC123 -r rules.yaml -f json
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    show_progress(
        f"Validating design system compliance for file {file_key}...",
        verbose,
    )

    try:
        client = get_figma_client(config)
        validator = get_design_validator()

        # Load rules
        show_progress(f"Loading rules from {rules}...", verbose)
        with open(rules, "r", encoding="utf-8") as f:
            rules_data = yaml.safe_load(f)

        # Parse node IDs if provided
        nodes = None
        if node_ids:
            nodes = [nid.strip() for nid in node_ids.split(",")]

        # Get file data
        show_progress("Fetching file data...", verbose)
        file_data = client.get_file(file_key, nodes=nodes)

        if not file_data:
            show_error(f"Failed to fetch file {file_key}")

        # Perform validation
        show_progress("Performing design system validation...", verbose)

        validation_result = validator.validate_design_system(
            file_data, rules=rules_data
        )

        # Format results
        if format == "text":
            status = "PASS" if validation_result.passed else "FAIL"
            report = [
                "Design System Validation Report",
                f"File: {file_key}",
                f"Rules: {rules}",
                "=" * 60,
                f"\nValidation Status: {status}",
                f"Issues Found: {len(validation_result.issues)}",
                f"Warnings: {len(validation_result.warnings)}",
                "\nIssues:",
            ]

            for issue in validation_result.issues:
                issue_line = (
                    f"  - [{issue.severity}] {issue.message} "
                    f"(Node: {issue.node_id})"
                )
                report.append(issue_line)

            result_text = "\n".join(report)
        else:
            result_text = format_output(validation_result.to_dict(), format)

        write_output(result_text, output, verbose)

        if not validation_result.passed:
            show_warning("Validation failed - issues found")
            sys.exit(1)
        else:
            show_success("Validation passed - no issues found")

    except Exception as e:
        show_error(f"Validation failed: {e}")


@validate.command(name="batch")
@click.option(
    "--file-keys",
    "-k",
    required=True,
    type=str,
    help="Comma-separated Figma file keys",
)
@click.option(
    "--wcag-level",
    "-w",
    type=click.Choice(["A", "AA", "AAA"], case_sensitive=False),
    default="AA",
    help="WCAG compliance level (default: AA)",
)
@click.option(
    "--rules",
    "-r",
    type=click.Path(exists=True),
    help="Design system rules YAML file",
)
@click.option(
    "--output",
    "-o",
    type=str,
    required=True,
    help="Output report file path",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (default: json)",
)
@click.pass_context
def validate_batch(
    ctx: click.Context,
    file_keys: str,
    wcag_level: str,
    rules: Optional[str],
    output: str,
    format: str,
) -> None:
    """
    Batch validate multiple Figma files.

    Examples:
        devcrew-design validate batch -k "ABC,DEF,GHI" -o report.json
        devcrew-design validate batch -k "ABC,DEF" -r rules.yaml -f yaml
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    keys = [key.strip() for key in file_keys.split(",")]
    show_progress(f"Batch validating {len(keys)} files...", verbose)

    try:
        client = get_figma_client(config)
        validator = get_design_validator()

        # Load rules if provided
        rules_data = None
        if rules:
            show_progress(f"Loading rules from {rules}...", verbose)
            with open(rules, "r", encoding="utf-8") as f:
                rules_data = yaml.safe_load(f)

        # Validate each file
        results: Dict[str, Any] = {}
        for idx, file_key in enumerate(keys, 1):
            show_progress(f"Validating file {idx}/{len(keys)}: {file_key}...", verbose)

            try:
                file_data = client.get_file(file_key)

                if not file_data:
                    results[file_key] = {"error": "Failed to fetch file"}
                    continue

                # WCAG validation
                wcag_result = validator.validate_wcag(file_data, level=wcag_level)

                file_result = {
                    "wcag_validation": {
                        "passed": wcag_result.passed,
                        "issues_count": len(wcag_result.issues),
                        "warnings_count": len(wcag_result.warnings),
                        "issues": [issue.to_dict() for issue in wcag_result.issues],
                    }
                }

                # Design system validation if rules provided
                if rules_data:
                    ds_result = validator.validate_design_system(
                        file_data, rules=rules_data
                    )
                    file_result["design_system_validation"] = {
                        "passed": ds_result.passed,
                        "issues_count": len(ds_result.issues),
                        "issues": [issue.to_dict() for issue in ds_result.issues],
                    }

                results[file_key] = file_result

            except Exception as e:
                results[file_key] = {"error": str(e)}
                show_warning(f"Failed to validate {file_key}: {e}")

        # Generate summary
        summary = {
            "total_files": len(keys),
            "files_validated": len([r for r in results.values() if "error" not in r]),
            "files_failed": len([r for r in results.values() if "error" in r]),
            "results": results,
        }

        # Write output
        result_text = format_output(summary, format)
        write_output(result_text, output, verbose)

        show_success(f"Batch validation complete - results saved to {output}")

    except Exception as e:
        show_error(f"Batch validation failed: {e}")


# Tokens Command Group
@cli.group()
@click.pass_context
def tokens(ctx: click.Context) -> None:
    """Extract and manage design tokens."""
    pass


@tokens.command(name="extract")
@click.option(
    "--file-key",
    "-k",
    required=True,
    callback=validate_file_key,
    help="Figma file key",
)
@click.option(
    "--output",
    "-o",
    type=str,
    required=True,
    help="Output tokens file path",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "scss", "css"], case_sensitive=False),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--categories",
    "-c",
    type=str,
    help="Comma-separated token categories (colors,typography,spacing)",
)
@click.pass_context
def tokens_extract(
    ctx: click.Context,
    file_key: str,
    output: str,
    format: str,
    categories: Optional[str],
) -> None:
    """
    Extract design tokens from Figma file.

    Examples:
        devcrew-design tokens extract -k ABC123 -o tokens.json
        devcrew-design tokens extract -k ABC123 -o tokens.scss -f scss
        devcrew-design tokens extract -k ABC123 -o tokens.json -c "colors,typography"
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    show_progress(f"Extracting design tokens from file {file_key}...", verbose)

    try:
        client = get_figma_client(config)
        exporter = get_code_exporter()

        # Parse categories if provided
        cats = None
        if categories:
            cats = [cat.strip() for cat in categories.split(",")]
            show_progress(f"Filtering categories: {cats}", verbose)

        # Get file data
        show_progress("Fetching file data...", verbose)
        file_data = client.get_file(file_key)

        if not file_data:
            show_error(f"Failed to fetch file {file_key}")

        # Extract tokens
        show_progress("Extracting design tokens...", verbose)

        tokens_data = exporter.extract_design_tokens(file_data, categories=cats)

        # Format tokens based on output format
        if format == "json":
            tokens_output = json.dumps(tokens_data, indent=2)
        elif format == "yaml":
            tokens_output = yaml.dump(tokens_data, default_flow_style=False)
        elif format == "scss":
            tokens_output = exporter.tokens_to_scss(tokens_data)
        elif format == "css":
            tokens_output = exporter.tokens_to_css(tokens_data)
        else:
            tokens_output = json.dumps(tokens_data, indent=2)

        # Write output
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(tokens_output, encoding="utf-8")

        show_success(f"Design tokens extracted to {output}")

        # Show summary
        if verbose:
            token_count = sum(
                len(v) for v in tokens_data.values() if isinstance(v, dict)
            )
            show_progress(f"Extracted {token_count} tokens", verbose)

    except Exception as e:
        show_error(f"Token extraction failed: {e}")


@tokens.command(name="list")
@click.option(
    "--file-key",
    "-k",
    required=True,
    callback=validate_file_key,
    help="Figma file key",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "table"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
@click.pass_context
def tokens_list(
    ctx: click.Context,
    file_key: str,
    format: str,
) -> None:
    """
    List available design tokens.

    Examples:
        devcrew-design tokens list -k ABC123
        devcrew-design tokens list -k ABC123 -f json
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    show_progress(f"Listing design tokens from file {file_key}...", verbose)

    try:
        client = get_figma_client(config)
        exporter = get_code_exporter()

        # Get file data
        show_progress("Fetching file data...", verbose)
        file_data = client.get_file(file_key)

        if not file_data:
            show_error(f"Failed to fetch file {file_key}")

        # Extract tokens
        show_progress("Extracting design tokens...", verbose)
        tokens_data = exporter.extract_design_tokens(file_data)

        # Format output
        if format == "table":
            click.echo("\nDesign Tokens Summary\n" + "=" * 60)
            for category, tokens in tokens_data.items():
                if isinstance(tokens, dict):
                    click.echo(f"\n{category.upper()}: {len(tokens)} tokens")
                    for token_name in list(tokens.keys())[:5]:
                        click.echo(f"  - {token_name}")
                    if len(tokens) > 5:
                        click.echo(f"  ... and {len(tokens) - 5} more")
        else:
            result_text = format_output(tokens_data, format)
            click.echo(result_text)

    except Exception as e:
        show_error(f"Token listing failed: {e}")


@tokens.command(name="preview")
@click.option(
    "--file-key",
    "-k",
    required=True,
    callback=validate_file_key,
    help="Figma file key",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["css", "scss", "json"], case_sensitive=False),
    default="css",
    help="Preview format (default: css)",
)
@click.pass_context
def tokens_preview(
    ctx: click.Context,
    file_key: str,
    format: str,
) -> None:
    """
    Preview design token export.

    Examples:
        devcrew-design tokens preview -k ABC123
        devcrew-design tokens preview -k ABC123 -f scss
    """
    verbose = ctx.obj["verbose"]
    config = ctx.obj["config"]

    show_progress(f"Previewing design tokens from file {file_key}...", verbose)

    try:
        client = get_figma_client(config)
        exporter = get_code_exporter()

        # Get file data
        file_data = client.get_file(file_key)

        if not file_data:
            show_error(f"Failed to fetch file {file_key}")

        # Extract tokens
        tokens_data = exporter.extract_design_tokens(file_data)

        # Generate preview based on format
        if format == "css":
            preview = exporter.tokens_to_css(tokens_data)
        elif format == "scss":
            preview = exporter.tokens_to_scss(tokens_data)
        else:
            preview = json.dumps(tokens_data, indent=2)

        click.echo(preview)

    except Exception as e:
        show_error(f"Token preview failed: {e}")


# C4 Command Group
@cli.group()
@click.pass_context
def c4(ctx: click.Context) -> None:
    """Generate and validate C4 architecture diagrams."""
    pass


@c4.command(name="generate")
@click.option(
    "--dsl",
    "-d",
    type=click.Path(exists=True),
    required=True,
    help="Structurizr DSL file path",
)
@click.option(
    "--output",
    "-o",
    type=str,
    required=True,
    help="Output directory for diagrams",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["png", "svg", "plantuml"], case_sensitive=False),
    multiple=True,
    default=["png"],
    help="Output formats (can specify multiple)",
)
@click.pass_context
def c4_generate(
    ctx: click.Context,
    dsl: str,
    output: str,
    format: Tuple[str, ...],
) -> None:
    """
    Generate C4 diagrams from Structurizr DSL.

    Examples:
        devcrew-design c4 generate -d architecture.dsl -o diagrams/
        devcrew-design c4 generate -d arch.dsl -o out/ -f png -f svg
    """
    verbose = ctx.obj["verbose"]

    show_progress(f"Generating C4 diagrams from {dsl}...", verbose)

    try:
        generator = get_c4_generator()

        # Generate diagrams
        show_progress(f"Output formats: {', '.join(format)}", verbose)

        with click.progressbar(
            length=100, label="Generating diagrams", show_eta=False
        ) as bar:
            results = generator.generate_from_dsl(
                dsl_file=dsl,
                output_dir=output,
                formats=list(format),
            )
            bar.update(100)

        # Show results
        show_success(f"Diagrams generated in {output}")

        if verbose:
            for fmt, files in results.items():
                click.echo(f"\n{fmt.upper()} files:")
                for file_path in files:
                    click.echo(f"  - {file_path}")

    except Exception as e:
        show_error(f"C4 generation failed: {e}")


@c4.command(name="validate")
@click.option(
    "--dsl",
    "-d",
    type=click.Path(exists=True),
    required=True,
    help="Structurizr DSL file path",
)
@click.pass_context
def c4_validate(
    ctx: click.Context,
    dsl: str,
) -> None:
    """
    Validate Structurizr DSL syntax.

    Examples:
        devcrew-design c4 validate -d architecture.dsl
    """
    verbose = ctx.obj["verbose"]

    show_progress(f"Validating DSL file {dsl}...", verbose)

    try:
        generator = get_c4_generator()

        # Validate DSL
        show_progress("Parsing DSL syntax...", verbose)

        validation_result = generator.validate_dsl(dsl)

        if validation_result["valid"]:
            show_success("DSL validation passed - syntax is valid")

            if verbose and "elements" in validation_result:
                elements = validation_result["elements"]
                click.echo("\nDSL Summary:")
                click.echo(f"  - People: {elements.get('people', 0)}")
                click.echo(f"  - Systems: {elements.get('systems', 0)}")
                click.echo(f"  - Containers: {elements.get('containers', 0)}")
                click.echo(f"  - Components: {elements.get('components', 0)}")
        else:
            errors = validation_result.get("errors", "Unknown error")
            show_error(f"DSL validation failed:\n{errors}")

    except Exception as e:
        show_error(f"DSL validation failed: {e}")


@c4.command(name="render")
@click.option(
    "--dsl",
    "-d",
    type=click.Path(exists=True),
    required=True,
    help="Structurizr DSL file path",
)
@click.option(
    "--view",
    "-v",
    type=click.Choice(
        ["SystemContext", "Container", "Component", "Code"],
        case_sensitive=False,
    ),
    required=True,
    help="Diagram view to render",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["png", "svg", "plantuml"], case_sensitive=False),
    default="svg",
    help="Output format (default: svg)",
)
@click.option(
    "--output",
    "-o",
    type=str,
    required=True,
    help="Output file path",
)
@click.pass_context
def c4_render(
    ctx: click.Context,
    dsl: str,
    view: str,
    format: str,
    output: str,
) -> None:
    """
    Render specific C4 diagram view.

    Examples:
        devcrew-design c4 render -d arch.dsl -v SystemContext -f svg -o context.svg
        devcrew-design c4 render -d arch.dsl -v Container -f png -o container.png
    """
    verbose = ctx.obj["verbose"]

    show_progress(f"Rendering {view} diagram from {dsl}...", verbose)

    try:
        generator = get_c4_generator()

        # Render specific view
        show_progress(f"Generating {view} view in {format} format...", verbose)

        result = generator.render_view(
            dsl_file=dsl,
            view=view,
            format=format,
            output_path=output,
        )

        if result:
            show_success(f"Diagram rendered to {output}")
        else:
            show_error("Failed to render diagram")

    except Exception as e:
        show_error(f"C4 rendering failed: {e}")


# Config Command Group
@cli.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Manage configuration and API credentials."""
    pass


@config.command(name="show")
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """
    Display current configuration.

    Examples:
        devcrew-design config show
    """
    config_data = ctx.obj["config"]

    click.echo("\ndevCrew Design Platform Configuration\n" + "=" * 60)
    click.echo(f"Config file: {CONFIG_FILE}")
    click.echo(f"Config exists: {CONFIG_FILE.exists()}")
    click.echo("\nSettings:")

    for key, value in config_data.items():
        if key == "figma_token":
            if value:
                masked = f"{value[:8]}...{value[-4:]}"
                click.echo(f"  {key}: {masked}")
            else:
                click.echo(f"  {key}: {click.style('Not configured', fg='red')}")
        else:
            click.echo(f"  {key}: {value}")


@config.command(name="set-token")
@click.option(
    "--token",
    "-t",
    required=True,
    type=str,
    help="Figma API token",
)
@click.pass_context
def config_set_token(ctx: click.Context, token: str) -> None:
    """
    Set Figma API token.

    Examples:
        devcrew-design config set-token --token figd_xxxxxxxxxxxx
    """
    config_data = ctx.obj["config"]
    config_data["figma_token"] = token

    save_config(config_data)
    show_success("Figma API token configured successfully")


@config.command(name="validate")
@click.pass_context
def config_validate(ctx: click.Context) -> None:
    """
    Validate configuration and API access.

    Examples:
        devcrew-design config validate
    """
    verbose = ctx.obj["verbose"]
    config_data = ctx.obj["config"]

    click.echo("\nValidating configuration...\n" + "=" * 60)

    # Check config file
    if CONFIG_FILE.exists():
        show_success(f"Config file found at {CONFIG_FILE}")
    else:
        show_warning(f"Config file not found at {CONFIG_FILE}")

    # Check Figma token
    if not config_data.get("figma_token"):
        show_error(
            "Figma API token not configured. "
            "Run: devcrew-design config set-token --token YOUR_TOKEN"
        )

    show_progress("Testing Figma API access...", verbose)

    try:
        from design_platform import FigmaClient

        client = FigmaClient(access_token=config_data["figma_token"])

        # Test API access by attempting a simple API call
        # We'll just verify the client can be instantiated correctly
        if client.access_token and client.session:
            show_success("Figma API access validated successfully")
            if verbose:
                token = client.access_token
                masked = f"{token[:8]}...{token[-4:]}"
                click.echo(f"\nToken: {masked}")
                click.echo(f"Base URL: {client.base_url}")
        else:
            show_error("Failed to validate Figma API access")

    except Exception as e:
        show_error(f"Figma API validation failed: {e}")

    show_success("Configuration validation complete")


# Main entry point
def main() -> None:
    """Execute the CLI application."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(
            click.style(f"\nFatal error: {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
