#!/usr/bin/env python3
"""
API Documentation Generator CLI.

Command-line interface for generating, serving, and validating API
documentation from FastAPI applications and OpenAPI specifications.
"""

import importlib
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

import click
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from .doc_renderer import DocRenderer
from .spec_generator import (
    DependencyError,
    InvalidAppError,
    SpecGenerator,
    SpecGeneratorError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rich console for formatted output
console = Console()


class CLIError(Exception):
    """Base exception for CLI errors."""

    pass


class AppLoadError(CLIError):
    """Failed to load FastAPI application."""

    pass


class SpecLoadError(CLIError):
    """Failed to load OpenAPI specification."""

    pass


class ServerError(CLIError):
    """Failed to start documentation server."""

    pass


def load_fastapi_app(app_path: str) -> Any:
    """
    Load FastAPI application from module path.

    Args:
        app_path: Module path in format "module.path:app_name"

    Returns:
        FastAPI application instance

    Raises:
        AppLoadError: If app cannot be loaded
    """
    try:
        if ":" not in app_path:
            raise AppLoadError(
                f"Invalid app path format: {app_path}. "
                "Expected format: module.path:app_name"
            )

        module_path, app_name = app_path.rsplit(":", 1)

        # Import the module
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            raise AppLoadError(
                f"Module not found: {module_path}. "
                f"Make sure the module is in PYTHONPATH. Error: {e}"
            ) from e
        except Exception as e:
            raise AppLoadError(f"Failed to import module {module_path}: {e}") from e

        # Get the app instance
        if not hasattr(module, app_name):
            raise AppLoadError(f"App '{app_name}' not found in module {module_path}")

        app = getattr(module, app_name)

        # Verify it's a FastAPI app
        try:
            from fastapi import FastAPI

            if not isinstance(app, FastAPI):
                raise AppLoadError(
                    f"Object '{app_name}' is not a FastAPI instance. "
                    f"Got: {type(app).__name__}"
                )
        except ImportError:
            raise AppLoadError(
                "FastAPI is not installed. Install with: pip install fastapi"
            )

        return app

    except AppLoadError:
        raise
    except Exception as e:
        logger.error("Unexpected error loading app: %s", str(e))
        raise AppLoadError(f"Failed to load app: {e}") from e


def load_spec_file(spec_path: Path) -> Dict[str, Any]:
    """
    Load OpenAPI specification from file.

    Args:
        spec_path: Path to spec file (JSON or YAML)

    Returns:
        Specification dictionary

    Raises:
        SpecLoadError: If spec cannot be loaded
    """
    try:
        if not spec_path.exists():
            raise SpecLoadError(f"Spec file not found: {spec_path}")

        if not spec_path.is_file():
            raise SpecLoadError(f"Not a file: {spec_path}")

        suffix = spec_path.suffix.lower()

        if suffix == ".json":
            with open(spec_path, "r", encoding="utf-8") as f:
                return json.load(f)
        elif suffix in {".yaml", ".yml"}:
            try:
                import yaml

                with open(spec_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except ImportError as e:
                raise SpecLoadError(
                    "PyYAML is not installed. Install with: pip install pyyaml"
                ) from e
        else:
            raise SpecLoadError(
                f"Unsupported file format: {suffix}. "
                "Supported formats: .json, .yaml, .yml"
            )

    except SpecLoadError:
        raise
    except json.JSONDecodeError as e:
        raise SpecLoadError(f"Invalid JSON in {spec_path}: {e}") from e
    except Exception as e:
        raise SpecLoadError(f"Failed to load spec: {e}") from e


def display_spec_info(spec: Dict[str, Any]) -> None:
    """
    Display specification information in formatted table.

    Args:
        spec: OpenAPI specification dictionary
    """
    info = spec.get("info", {})
    paths = spec.get("paths", {})

    # Create info panel
    info_table = Table(show_header=False, box=None, padding=(0, 1))
    info_table.add_column("Key", style="cyan bold")
    info_table.add_column("Value")

    info_table.add_row("Title", info.get("title", "N/A"))
    info_table.add_row("Version", info.get("version", "N/A"))
    info_table.add_row("OpenAPI Version", spec.get("openapi", "N/A"))
    info_table.add_row("Paths", str(len(paths)))

    # Count operations
    operation_count = 0
    for path_item in paths.values():
        if isinstance(path_item, dict):
            http_methods = {
                "get",
                "post",
                "put",
                "delete",
                "patch",
                "options",
                "head",
                "trace",
            }
            operation_count += len([m for m in path_item.keys() if m in http_methods])

    info_table.add_row("Operations", str(operation_count))

    console.print(
        Panel(
            info_table,
            title="[bold]API Specification[/bold]",
            border_style="blue",
        )
    )


def display_paths_tree(spec: Dict[str, Any]) -> None:
    """
    Display API paths in tree format.

    Args:
        spec: OpenAPI specification dictionary
    """
    paths = spec.get("paths", {})

    if not paths:
        console.print("[yellow]No paths found in specification[/yellow]")
        return

    tree = Tree("[bold cyan]API Endpoints[/bold cyan]")

    for path, path_item in sorted(paths.items()):
        if not isinstance(path_item, dict):
            continue

        path_node = tree.add(f"[bold]{path}[/bold]")

        http_methods = {
            "get",
            "post",
            "put",
            "delete",
            "patch",
            "options",
            "head",
            "trace",
        }

        for method in http_methods:
            if method in path_item:
                operation = path_item[method]
                summary = operation.get("summary", "No summary")
                method_color = {
                    "get": "green",
                    "post": "blue",
                    "put": "yellow",
                    "delete": "red",
                    "patch": "cyan",
                    "options": "magenta",
                    "head": "white",
                    "trace": "white",
                }.get(method, "white")

                path_node.add(
                    f"[{method_color}]{method.upper()}[/{method_color}] - " f"{summary}"
                )

    console.print(tree)


@click.group()
@click.version_option(version="1.0.0", prog_name="apidocs")
def cli() -> None:
    """
    Manage API Documentation Generator CLI.

    Generate, serve, and validate API documentation from FastAPI applications
    and OpenAPI specifications.
    """
    pass


@cli.command()
@click.option(
    "--app",
    required=True,
    help="FastAPI app in format 'module.path:app_name' (e.g., 'main:app')",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path (default: openapi.json)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "yaml", "swagger-ui", "redoc"], case_sensitive=False),
    default="json",
    help="Output format (default: json)",
)
@click.option("--title", help="API title (overrides app title)")
@click.option("--version", help="API version (overrides app version)")
@click.option("--description", help="API description (overrides app description)")
@click.option("--indent", type=int, default=2, help="JSON indentation (default: 2)")
@click.option(
    "--theme",
    type=click.Choice(["light", "dark"], case_sensitive=False),
    default="light",
    help="Theme for HTML output (default: light)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def generate(
    app: str,
    output: Optional[str],
    output_format: str,
    title: Optional[str],
    version: Optional[str],
    description: Optional[str],
    indent: int,
    theme: str,
    verbose: bool,
) -> None:
    r"""
    Generate OpenAPI specification from FastAPI application.

    Examples:
        \b
        # Generate JSON spec
        apidocs generate --app main:app --output openapi.json

        \b
        # Generate YAML spec
        apidocs generate --app main:app --format yaml

        \b
        # Generate Swagger UI HTML
        apidocs generate --app main:app --format swagger-ui --output docs.html

        \b
        # Generate with custom metadata
        apidocs generate --app main:app --title "My API" --version "2.0.0"
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        console.print(f"[bold blue]Loading FastAPI app:[/bold blue] {app}")

        # Load FastAPI app
        fastapi_app = load_fastapi_app(app)
        console.print("[green]App loaded successfully[/green]")

        # Generate specification
        console.print("[bold blue]Generating OpenAPI specification...[/bold blue]")
        generator = SpecGenerator()

        generator.from_fastapi(
            fastapi_app,
            title=title,
            version=version,
            description=description,
        )

        spec = generator.to_dict()
        console.print("[green]Specification generated successfully[/green]")

        # Display spec info
        display_spec_info(spec)

        # Determine output path
        if output:
            output_path = Path(output)
        else:
            extension_map = {
                "json": "json",
                "yaml": "yaml",
                "swagger-ui": "html",
                "redoc": "html",
            }
            ext = extension_map.get(output_format, "json")
            output_path = Path(f"openapi.{ext}")

        # Generate output based on format
        console.print(f"[bold blue]Generating output:[/bold blue] {output_format}")

        if output_format == "json":
            # Save as JSON
            output_path = generator.save(output_path, format="json", indent=indent)
            console.print(f"[green]Saved JSON spec to:[/green] {output_path}")

        elif output_format == "yaml":
            # Save as YAML
            output_path = generator.save(output_path, format="yaml")
            console.print(f"[green]Saved YAML spec to:[/green] {output_path}")

        elif output_format == "swagger-ui":
            # Generate Swagger UI HTML
            renderer = DocRenderer()
            html = renderer.render_swagger_ui(
                spec, title=spec["info"]["title"], theme=theme
            )

            output_path.write_text(html, encoding="utf-8")
            console.print(f"[green]Saved Swagger UI HTML to:[/green] {output_path}")

        elif output_format == "redoc":
            # Generate Redoc HTML
            renderer = DocRenderer()
            html = renderer.render_redoc(spec, title=spec["info"]["title"], theme=theme)

            output_path.write_text(html, encoding="utf-8")
            console.print(f"[green]Saved Redoc HTML to:[/green] {output_path}")

        # Display paths tree
        if verbose:
            console.print("\n")
            display_paths_tree(spec)

        console.print("\n[bold green]Generation completed successfully![/bold green]")

    except AppLoadError as e:
        console.print(f"[bold red]Error loading app:[/bold red] {e}")
        if verbose:
            console.print(f"\n[red]{traceback.format_exc()}[/red]")
        sys.exit(1)

    except (DependencyError, InvalidAppError, SpecGeneratorError) as e:
        console.print(f"[bold red]Error generating spec:[/bold red] {e}")
        if verbose:
            console.print(f"\n[red]{traceback.format_exc()}[/red]")
        sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        console.print(f"\n[red]{traceback.format_exc()}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--spec",
    required=True,
    type=click.Path(exists=True),
    help="OpenAPI spec file (JSON or YAML)",
)
@click.option(
    "--ui",
    type=click.Choice(["swagger", "redoc"], case_sensitive=False),
    default="swagger",
    help="UI type (default: swagger)",
)
@click.option("--port", type=int, default=8000, help="Server port (default: 8000)")
@click.option("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
@click.option(
    "--theme",
    type=click.Choice(["light", "dark"], case_sensitive=False),
    default="light",
    help="UI theme (default: light)",
)
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def serve(
    spec: str,
    ui: str,
    port: int,
    host: str,
    theme: str,
    reload: bool,
    verbose: bool,
) -> None:
    r"""
    Launch local documentation server.

    Serves interactive API documentation with live spec reloading.

    Examples:
        \b
        # Serve with Swagger UI
        apidocs serve --spec openapi.json

        \b
        # Serve with Redoc on custom port
        apidocs serve --spec openapi.yaml --ui redoc --port 8080

        \b
        # Serve with dark theme and auto-reload
        apidocs serve --spec openapi.json --theme dark --reload
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        spec_path = Path(spec)

        console.print(f"[bold blue]Loading specification:[/bold blue] {spec_path}")

        # Load specification
        spec_data = load_spec_file(spec_path)
        console.print("[green]Specification loaded successfully[/green]")

        # Display spec info
        display_spec_info(spec_data)

        # Validate spec
        console.print("[bold blue]Validating specification...[/bold blue]")
        generator = SpecGenerator()
        generator.from_dict(spec_data)
        errors = generator.validate()

        if errors:
            console.print(f"[yellow]Found {len(errors)} validation warnings:[/yellow]")
            for error in errors:
                console.print(f"  [yellow]- {error}[/yellow]")
        else:
            console.print("[green]Specification is valid[/green]")

        # Generate HTML
        console.print(
            f"[bold blue]Generating {ui.upper()} documentation...[/bold blue]"
        )
        renderer = DocRenderer()

        if ui == "swagger":
            html = renderer.render_swagger_ui(
                spec_data, title=spec_data["info"]["title"], theme=theme
            )
        else:  # redoc
            html = renderer.render_redoc(
                spec_data, title=spec_data["info"]["title"], theme=theme
            )

        # Create temporary server directory
        server_dir = Path.cwd() / ".apidocs_server"
        server_dir.mkdir(exist_ok=True)

        # Save HTML to temporary file
        html_file = server_dir / "index.html"
        html_file.write_text(html, encoding="utf-8")

        # Create simple FastAPI app to serve the HTML
        try:
            from fastapi import FastAPI
            from fastapi.responses import HTMLResponse

            server_app = FastAPI()

            @server_app.get("/")
            async def serve_docs() -> HTMLResponse:
                return HTMLResponse(content=html)

            @server_app.get("/spec.json")
            async def serve_spec() -> Dict[str, Any]:
                # Reload spec if reload flag is set
                if reload:
                    current_spec = load_spec_file(spec_path)
                    return current_spec
                return spec_data

            console.print("\n[bold green]Starting documentation server...[/bold green]")
            console.print(f"[cyan]Server URL:[/cyan] http://{host}:{port}")
            console.print(f"[cyan]Spec URL:[/cyan] http://{host}:{port}/spec.json")
            console.print("\n[yellow]Press Ctrl+C to stop the server[/yellow]\n")

            # Start uvicorn server
            uvicorn.run(
                server_app,
                host=host,
                port=port,
                log_level="info" if verbose else "warning",
                reload=reload,
            )

        except ImportError as e:
            raise ServerError(
                "FastAPI or uvicorn not installed. "
                "Install with: pip install fastapi uvicorn"
            ) from e

    except SpecLoadError as e:
        console.print(f"[bold red]Error loading spec:[/bold red] {e}")
        if verbose:
            console.print(f"\n[red]{traceback.format_exc()}[/red]")
        sys.exit(1)

    except ServerError as e:
        console.print(f"[bold red]Server error:[/bold red] {e}")
        if verbose:
            console.print(f"\n[red]{traceback.format_exc()}[/red]")
        sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
        sys.exit(0)

    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        console.print(f"\n[red]{traceback.format_exc()}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--spec",
    required=True,
    type=click.Path(exists=True),
    help="OpenAPI spec file (JSON or YAML)",
)
@click.option(
    "--endpoint",
    help="Live API endpoint URL to validate against",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Enable strict validation (treat warnings as errors)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def validate(spec: str, endpoint: Optional[str], strict: bool, verbose: bool) -> None:
    r"""
    Validate OpenAPI specification.

    Performs comprehensive validation of OpenAPI spec structure and optionally
    validates against a live API endpoint.

    Examples:
        \b
        # Validate spec file
        apidocs validate --spec openapi.json

        \b
        # Validate against live API
        apidocs validate --spec openapi.json --endpoint http://localhost:8000

        \b
        # Strict validation
        apidocs validate --spec openapi.json --strict
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        spec_path = Path(spec)

        console.print(f"[bold blue]Loading specification:[/bold blue] {spec_path}")

        # Load specification
        spec_data = load_spec_file(spec_path)
        console.print("[green]Specification loaded successfully[/green]")

        # Display spec info
        display_spec_info(spec_data)

        # Validate spec structure
        console.print("\n[bold blue]Validating specification structure...[/bold blue]")
        generator = SpecGenerator()
        generator.from_dict(spec_data)
        errors = generator.validate()

        # Create validation results table
        results_table = Table(title="Validation Results", show_header=True)
        results_table.add_column("Check", style="cyan")
        results_table.add_column("Status", style="bold")
        results_table.add_column("Details")

        # Basic structure validation
        if errors:
            results_table.add_row(
                "Structure",
                "[red]FAILED[/red]",
                f"{len(errors)} errors found",
            )
            for error in errors:
                console.print(f"  [red]- {error}[/red]")
        else:
            results_table.add_row(
                "Structure",
                "[green]PASSED[/green]",
                "All required fields present",
            )

        # Check for common best practices
        warnings = []

        # Check for description fields
        if not spec_data.get("info", {}).get("description"):
            warnings.append("Missing API description in info section")

        # Check for operation summaries
        paths = spec_data.get("paths", {})
        missing_summaries = 0
        for path, path_item in paths.items():
            if isinstance(path_item, dict):
                for method in ["get", "post", "put", "delete", "patch"]:
                    if method in path_item:
                        operation = path_item[method]
                        if not operation.get("summary"):
                            missing_summaries += 1

        if missing_summaries > 0:
            warnings.append(
                f"{missing_summaries} operations missing summary " "descriptions"
            )

        # Check for examples
        has_examples = False
        for path, path_item in paths.items():
            if isinstance(path_item, dict):
                for method in ["get", "post", "put", "delete", "patch"]:
                    if method in path_item:
                        operation = path_item[method]
                        if "requestBody" in operation:
                            content = operation["requestBody"].get("content", {})
                            for media_type in content.values():
                                has_example = "example" in media_type
                                has_examples_field = "examples" in media_type
                                if has_example or has_examples_field:
                                    has_examples = True
                                    break

        request_body_methods = ["post", "put", "patch"]
        has_request_bodies = any(
            "requestBody" in path_item.get(m, {})
            for path_item in paths.values()
            if isinstance(path_item, dict)
            for m in request_body_methods
        )
        if not has_examples and has_request_bodies:
            warnings.append("Request bodies missing examples")

        # Display warnings
        if warnings:
            status = "[red]FAILED[/red]" if strict else "[yellow]WARNING[/yellow]"
            results_table.add_row(
                "Best Practices",
                status,
                f"{len(warnings)} issues found",
            )
            for warning in warnings:
                color = "red" if strict else "yellow"
                console.print(f"  [{color}]- {warning}[/{color}]")
        else:
            results_table.add_row(
                "Best Practices",
                "[green]PASSED[/green]",
                "Follows OpenAPI best practices",
            )

        # Live endpoint validation
        if endpoint:
            console.print(
                f"\n[bold blue]Validating against live API:[/bold blue] " f"{endpoint}"
            )

            try:
                import requests

                # Test API availability
                try:
                    response = requests.get(endpoint, timeout=5)
                    results_table.add_row(
                        "API Availability",
                        "[green]PASSED[/green]",
                        f"HTTP {response.status_code}",
                    )
                except requests.exceptions.RequestException as e:
                    results_table.add_row(
                        "API Availability",
                        "[red]FAILED[/red]",
                        f"Cannot reach endpoint: {e}",
                    )

                # Try to fetch OpenAPI spec from endpoint
                spec_endpoints = [
                    "/openapi.json",
                    "/openapi.yaml",
                    "/docs/openapi.json",
                    "/api/openapi.json",
                ]

                live_spec = None
                for spec_endpoint in spec_endpoints:
                    try:
                        url = f"{endpoint.rstrip('/')}{spec_endpoint}"
                        response = requests.get(url, timeout=5)
                        if response.status_code == 200:
                            live_spec = response.json()
                            break
                    except Exception:  # nosec B112
                        # Continue trying other spec endpoints
                        continue

                if live_spec:
                    # Compare versions
                    local_version = spec_data.get("info", {}).get("version")
                    live_version = live_spec.get("info", {}).get("version")

                    if local_version == live_version:
                        results_table.add_row(
                            "Version Match",
                            "[green]PASSED[/green]",
                            f"Version {local_version}",
                        )
                    else:
                        results_table.add_row(
                            "Version Match",
                            "[yellow]WARNING[/yellow]",
                            f"Local: {local_version}, Live: " f"{live_version}",
                        )

                    # Compare paths
                    local_paths = set(spec_data.get("paths", {}).keys())
                    live_paths = set(live_spec.get("paths", {}).keys())

                    missing_paths = local_paths - live_paths
                    extra_paths = live_paths - local_paths

                    if not missing_paths and not extra_paths:
                        results_table.add_row(
                            "Path Match",
                            "[green]PASSED[/green]",
                            f"{len(local_paths)} paths match",
                        )
                    else:
                        status_msg = []
                        if missing_paths:
                            status_msg.append(f"{len(missing_paths)} missing from live")
                        if extra_paths:
                            status_msg.append(f"{len(extra_paths)} extra in live")

                        results_table.add_row(
                            "Path Match",
                            "[yellow]WARNING[/yellow]",
                            ", ".join(status_msg),
                        )
                else:
                    results_table.add_row(
                        "Live Spec",
                        "[yellow]SKIPPED[/yellow]",
                        "OpenAPI spec not found at endpoint",
                    )

            except ImportError:
                results_table.add_row(
                    "Live Validation",
                    "[yellow]SKIPPED[/yellow]",
                    "requests library not installed",
                )

        # Display results table
        console.print("\n")
        console.print(results_table)

        # Final summary
        console.print("\n")
        if errors or (strict and warnings):
            console.print("[bold red]Validation FAILED[/bold red]")
            console.print(
                f"[red]Found {len(errors)} errors and {len(warnings)} "
                f"warnings[/red]"
            )
            sys.exit(1)
        elif warnings:
            console.print("[bold yellow]Validation PASSED with warnings[/bold yellow]")
            console.print(f"[yellow]Found {len(warnings)} warnings[/yellow]")
            sys.exit(0)
        else:
            console.print("[bold green]Validation PASSED[/bold green]")
            console.print("[green]Specification is valid and complete[/green]")
            sys.exit(0)

    except SpecLoadError as e:
        console.print(f"[bold red]Error loading spec:[/bold red] {e}")
        if verbose:
            console.print(f"\n[red]{traceback.format_exc()}[/red]")
        sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        console.print(f"\n[red]{traceback.format_exc()}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
