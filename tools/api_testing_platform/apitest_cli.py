#!/usr/bin/env python3
"""
API Testing Platform CLI

Comprehensive command-line interface for API testing, contract validation,
and regression testing using OpenAPI specifications.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .api_client import APIClient
from .contract_validator import ContractValidator
from .pact_manager import PactManager
from .regression_engine import RegressionEngine
from .schema_validator import SchemaValidator
from .test_generator import TestGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rich console for colorized output
console = Console()

# Default config file
DEFAULT_CONFIG_FILE = "api-test-config.yaml"


class CLIError(Exception):
    """Base exception for CLI errors."""

    pass


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_file: Path to config file. If None, uses default.

    Returns:
        Configuration dictionary

    Raises:
        CLIError: If config file not found or invalid
    """
    config_path = Path(config_file or DEFAULT_CONFIG_FILE)

    if not config_path.exists():
        return {}

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except yaml.YAMLError as e:
        raise CLIError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise CLIError(f"Error loading config file: {e}")


def load_spec(spec_path: str) -> Dict[str, Any]:
    """
    Load OpenAPI specification from file.

    Args:
        spec_path: Path to OpenAPI spec file (YAML or JSON)

    Returns:
        Specification dictionary

    Raises:
        CLIError: If spec file not found or invalid
    """
    spec_file = Path(spec_path)

    if not spec_file.exists():
        raise CLIError(f"Specification file not found: {spec_path}")

    try:
        with open(spec_file, "r") as f:
            if spec_file.suffix in [".yaml", ".yml"]:
                spec = yaml.safe_load(f)
            elif spec_file.suffix == ".json":
                spec = json.load(f)
            else:
                raise CLIError(f"Unsupported spec format: {spec_file.suffix}")
        return spec
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise CLIError(f"Invalid spec file format: {e}")
    except Exception as e:
        raise CLIError(f"Error loading spec file: {e}")


def output_results(data: Dict[str, Any], output_file: Optional[str] = None) -> None:
    """
    Output results to console or file.

    Args:
        data: Results data to output
        output_file: Optional path to output file (JSON)
    """
    if output_file:
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
            console.print(f"[green]Results written to {output_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error writing output file: {e}[/red]")
            sys.exit(2)
    else:
        console.print_json(json.dumps(data))


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool) -> None:
    """
    API Testing Platform CLI.

    Comprehensive toolkit for API testing, contract validation, and
    regression testing using OpenAPI specifications.
    """
    ctx.ensure_object(dict)

    # Load configuration
    try:
        ctx.obj["config"] = load_config(config)
    except CLIError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(2)

    # Configure logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


@cli.command()
@click.option(
    "--spec",
    type=click.Path(exists=True),
    required=True,
    help="OpenAPI spec file",
)
@click.option("--lint", is_flag=True, help="Enable linting")
@click.option(
    "--rules",
    type=click.Path(exists=True),
    help="Custom lint rules file",
)
@click.option("--output", type=click.Path(), help="Output report file (JSON)")
@click.option("--strict", is_flag=True, help="Strict validation mode")
@click.pass_context
def validate(
    ctx: click.Context,
    spec: str,
    lint: bool,
    rules: Optional[str],
    output: Optional[str],
    strict: bool,
) -> None:
    """
    Validate OpenAPI specifications.

    Performs syntax and semantic validation of OpenAPI specs with
    optional linting and custom rule enforcement.
    """
    console.print("[bold blue]Validating OpenAPI Specification[/bold blue]")

    try:
        # Initialize validator
        validator = ContractValidator(strict=strict)

        # Validate specification
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Validating...", total=None)
            result = validator.validate(spec)
            progress.update(task, completed=True)

        # Lint if requested
        lint_result = None
        if lint:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Linting...", total=None)
                lint_result = validator.lint(spec)
                progress.update(task, completed=True)

        # Prepare results
        validation_results = {
            "spec_file": spec,
            "valid": result.is_valid,
            "errors": [
                {
                    "message": err.message,
                    "path": err.path,
                    "severity": err.severity.value,
                    "rule": err.rule,
                    "suggestion": err.suggestion,
                }
                for err in result.errors
            ],
            "warnings": [
                {
                    "message": w.message,
                    "path": w.path,
                    "rule": w.rule,
                }
                for w in result.warnings
            ],
            "lint_errors": (
                [
                    {
                        "message": err.message,
                        "path": err.path,
                        "severity": err.severity.value,
                    }
                    for err in lint_result.errors
                ]
                if lint and lint_result
                else []
            ),
        }

        # Display results
        valid_result = result.is_valid and (
            not lint or not lint_result or lint_result.is_valid
        )
        if valid_result:
            console.print("[green]✓ Specification is valid[/green]")
            sys.exit(0)
        else:
            if result.errors:
                console.print(
                    f"[red]✗ Found {len(result.errors)} " f"validation error(s)[/red]"
                )
                table = Table(title="Validation Errors")
                table.add_column("Path", style="cyan")
                table.add_column("Message", style="white")
                table.add_column("Severity", style="yellow")

                for err in result.errors:
                    table.add_row(err.path, err.message, err.severity.value)
                console.print(table)

            if lint_result and lint_result.errors:
                console.print(
                    f"[yellow]⚠ Found {len(lint_result.errors)} "
                    f"linting issue(s)[/yellow]"
                )

        # Output results
        if output:
            output_results(validation_results, output)

        exit_code = 0
        if not result.is_valid:
            exit_code = 1
        elif lint_result and not lint_result.is_valid:
            exit_code = 1

        sys.exit(exit_code)

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Validation failed")
        sys.exit(2)


@cli.command()
@click.option(
    "--spec",
    type=click.Path(exists=True),
    required=True,
    help="OpenAPI spec file",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="generated_tests",
    help="Output directory for tests",
)
@click.option(
    "--template",
    type=click.Choice(["pytest", "unittest"]),
    default="pytest",
    help="Template type",
)
@click.option(
    "--include-negative",
    is_flag=True,
    help="Include negative tests",
)
@click.option(
    "--auth-method",
    type=click.Choice(["bearer", "apikey", "basic", "oauth2"]),
    help="Auth method",
)
@click.pass_context
def generate(
    ctx: click.Context,
    spec: str,
    output_dir: str,
    template: str,
    include_negative: bool,
    auth_method: Optional[str],
) -> None:
    """
    Generate tests from OpenAPI specs.

    Auto-generates test cases with property-based testing, boundary
    value analysis, and negative test scenarios.
    """
    console.print("[bold blue]Generating API Tests[/bold blue]")

    try:
        # Initialize generator
        generator = TestGenerator()

        # Generate tests
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating test cases...", total=None)

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate from spec file
            generated_file = generator.generate_from_spec(
                spec_file=spec,
                output_dir=output_path,
            )
            progress.update(task, completed=True)

        # Display results
        console.print(f"[green]✓ Generated test file: {generated_file}[/green]")
        console.print(f"[blue]Output directory: {output_dir}[/blue]")

        # Show generated file info
        table = Table(title="Generated Test Files")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="white")

        table.add_row(
            str(generated_file),
            "[green]Created[/green]",
        )
        console.print(table)

        sys.exit(0)

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Test generation failed")
        sys.exit(2)


@cli.command()
@click.option("--spec", type=click.Path(exists=True), help="OpenAPI spec file")
@click.option("--base-url", type=str, help="Base API URL")
@click.option("--endpoint", type=str, help="Specific endpoint to test")
@click.option(
    "--method",
    type=click.Choice(["GET", "POST", "PUT", "DELETE", "PATCH"]),
    help="HTTP method filter",
)
@click.option("--auth-token", type=str, help="Authentication token")
@click.option(
    "--workers",
    type=int,
    default=1,
    help="Parallel workers",
)
@click.pass_context
def run(
    ctx: click.Context,
    spec: Optional[str],
    base_url: Optional[str],
    endpoint: Optional[str],
    method: Optional[str],
    auth_token: Optional[str],
    workers: int,
) -> None:
    """
    Execute API test suites.

    Run comprehensive API tests including schema validation,
    response validation, and endpoint testing.
    """
    console.print("[bold blue]Running API Tests[/bold blue]")

    try:
        # Get configuration
        config = ctx.obj.get("config", {})
        base_url = base_url or config.get("base_url")
        auth_token = auth_token or config.get("auth", {}).get("token")

        if not base_url:
            raise CLIError("Base URL is required (--base-url or config)")

        if not spec:
            raise CLIError("OpenAPI spec is required (--spec)")

        # Load specification
        spec_data = load_spec(spec)

        # Initialize API client
        client_config = {
            "base_url": base_url,
            "timeout": config.get("timeout", 30),
            "retry_attempts": config.get("retry_attempts", 3),
        }
        client = APIClient(config=client_config)

        # Setup authentication
        if auth_token:
            client.set_bearer_token(auth_token)

        # Initialize schema validator
        validator = SchemaValidator(spec_file=spec)

        # Get endpoints to test
        paths = spec_data.get("paths", {})

        if endpoint:
            paths = {endpoint: paths.get(endpoint, {})}

        if method:
            for path, operations in paths.items():
                paths[path] = {
                    m: op for m, op in operations.items() if m.upper() == method
                }

        total_tests = sum(
            len(
                [
                    k
                    for k in ops.keys()
                    if k in ["get", "post", "put", "delete", "patch"]
                ]
            )
            for ops in paths.values()
        )

        console.print(
            f"[blue]Testing {total_tests} endpoint(s) with "
            f"{workers} worker(s)[/blue]"
        )

        # Run tests
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running tests...", total=total_tests)

            for path, operations in paths.items():
                for http_method, operation in operations.items():
                    if http_method not in ["get", "post", "put", "delete", "patch"]:
                        continue

                    results["total"] += 1

                    try:
                        # Make API request
                        api_response = client._request(
                            http_method.upper(),
                            path,
                        )

                        # Validate response
                        validation = validator.validate_response(
                            path,
                            http_method,
                            api_response.status_code,
                            api_response.body,
                        )

                        if validation.valid:
                            results["passed"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(
                                {
                                    "endpoint": f"{http_method.upper()} " f"{path}",
                                    "errors": [
                                        err.to_dict() for err in validation.errors
                                    ],
                                }
                            )

                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(
                            {
                                "endpoint": f"{http_method.upper()} {path}",
                                "error": str(e),
                            }
                        )

                    progress.update(task, advance=1)

        # Display results
        console.print("\n[bold]Test Results[/bold]")
        table = Table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Total Tests", str(results["total"]))
        table.add_row(
            "Passed",
            f"[green]{results['passed']}[/green]",
        )
        table.add_row(
            "Failed",
            f"[red]{results['failed']}[/red]",
        )
        console.print(table)

        if results["errors"]:
            console.print("\n[bold red]Failures:[/bold red]")
            for error in results["errors"]:
                console.print(f"  • {error['endpoint']}")

        sys.exit(0 if results["failed"] == 0 else 1)

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Test execution failed")
        sys.exit(2)


@cli.group()
def pact() -> None:
    """
    Manage Pact contracts.

    Consumer-driven contract testing with Pact broker integration,
    provider verification, and Can-I-Deploy checks.
    """
    pass


@pact.command(name="create")
@click.option("--consumer", type=str, required=True, help="Consumer name")
@click.option("--provider", type=str, required=True, help="Provider name")
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output contract file",
)
@click.option(
    "--interaction-file",
    type=click.Path(exists=True),
    help="Interaction definition file (JSON)",
)
def pact_create(
    consumer: str,
    provider: str,
    output: str,
    interaction_file: Optional[str],
) -> None:
    """Create Pact contract."""
    console.print("[bold blue]Creating Pact Contract[/bold blue]")

    try:
        # Initialize Pact manager
        pact_manager = PactManager(consumer=consumer, provider=provider)

        # Load interactions if provided
        if interaction_file:
            with open(interaction_file, "r") as f:
                interactions = json.load(f)

            for interaction in interactions:
                pact_manager.add_interaction(interaction)

        # Create and save contract
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating contract...", total=None)
            contract = pact_manager.create_consumer_contract()
            contract.save(Path(output))
            progress.update(task, completed=True)

        console.print(f"[green]✓ Contract created: {output}[/green]")
        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Contract creation failed")
        sys.exit(2)


@pact.command(name="publish")
@click.option(
    "--contract",
    type=click.Path(exists=True),
    required=True,
    help="Contract file",
)
@click.option(
    "--broker-url",
    type=str,
    required=True,
    help="Pact broker URL",
)
@click.option("--version", type=str, required=True, help="Consumer version")
@click.option("--username", type=str, help="Broker username")
@click.option(
    "--password",
    type=str,
    help="Broker password",
)
@click.option("--tag", type=str, multiple=True, help="Version tags")
def pact_publish(
    contract: str,
    broker_url: str,
    version: str,
    username: Optional[str],
    password: Optional[str],
    tag: tuple,
) -> None:
    """Publish to broker."""
    console.print("[bold blue]Publishing Pact Contract[/bold blue]")

    try:
        # Load contract
        with open(contract, "r") as f:
            contract_data = json.load(f)

        # Initialize Pact manager
        pact_manager = PactManager(
            consumer=contract_data["consumer"]["name"],
            provider=contract_data["provider"]["name"],
            broker_url=broker_url,
            broker_username=username,
            broker_password=password,
        )

        # Publish contract
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Publishing to broker...", total=None)
            pact_manager.publish_to_broker(
                Path(contract), version, tags=list(tag) or None
            )
            progress.update(task, completed=True)

        console.print(f"[green]✓ Contract published to {broker_url}[/green]")
        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Contract publication failed")
        sys.exit(2)


@pact.command(name="verify")
@click.option(
    "--provider-url",
    type=str,
    required=True,
    help="Provider base URL",
)
@click.option("--broker-url", type=str, required=True, help="Pact broker URL")
@click.option(
    "--provider",
    type=str,
    required=True,
    help="Provider name",
)
@click.option("--username", type=str, help="Broker username")
@click.option("--password", type=str, help="Broker password")
@click.option(
    "--consumer-version-tag",
    type=str,
    help="Consumer version tag",
)
def pact_verify(
    provider_url: str,
    broker_url: str,
    provider: str,
    username: Optional[str],
    password: Optional[str],
    consumer_version_tag: Optional[str],
) -> None:
    """Verify provider."""
    console.print("[bold blue]Verifying Provider[/bold blue]")

    try:
        # Initialize Pact manager
        pact_manager = PactManager(
            consumer="",  # Not needed for verification
            provider=provider,
            broker_url=broker_url,
            broker_username=username,
            broker_password=password,
        )

        # Verify provider
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Verifying provider...", total=None)
            result = pact_manager.verify_provider(
                provider=provider,
                base_url=provider_url,
            )
            progress.update(task, completed=True)

        if result.success:
            console.print("[green]✓ Provider verification passed[/green]")
            sys.exit(0)
        else:
            console.print("[red]✗ Provider verification failed[/red]")
            for failure in result.failures:
                console.print(f"  • {failure}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Provider verification failed")
        sys.exit(2)


@pact.command(name="deploy")
@click.option("--broker-url", type=str, required=True, help="Pact broker URL")
@click.option(
    "--application",
    type=str,
    required=True,
    help="Application name",
)
@click.option("--version", type=str, required=True, help="Application version")
@click.option(
    "--to",
    type=str,
    required=True,
    help="Target environment",
)
@click.option("--username", type=str, help="Broker username")
@click.option("--password", type=str, help="Broker password")
def pact_deploy(
    broker_url: str,
    application: str,
    version: str,
    to: str,
    username: Optional[str],
    password: Optional[str],
) -> None:
    """Can-I-Deploy check."""
    console.print("[bold blue]Can-I-Deploy Check[/bold blue]")

    try:
        # Initialize Pact manager
        pact_manager = PactManager(
            consumer=application,
            provider="",
            broker_url=broker_url,
            broker_username=username,
            broker_password=password,
        )

        # Can-I-Deploy check
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Checking deployment safety...", total=None)
            result = pact_manager.can_i_deploy(
                participant=application,
                version=version,
                to_environment=to,
            )
            progress.update(task, completed=True)

        if result.is_deployable():
            console.print(
                f"[green]✓ Safe to deploy {application} " f"{version} to {to}[/green]"
            )
            sys.exit(0)
        else:
            console.print(
                f"[red]✗ Cannot deploy {application} " f"{version} to {to}[/red]"
            )
            console.print(f"[yellow]Reason: {result.reason}[/yellow]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Can-I-Deploy check failed")
        sys.exit(2)


@cli.command()
@click.option(
    "--spec",
    type=click.Path(exists=True),
    required=True,
    help="OpenAPI spec file",
)
@click.option(
    "--base-url",
    type=str,
    required=True,
    help="Base API URL",
)
@click.option(
    "--baseline-dir",
    type=click.Path(),
    required=True,
    help="Baseline directory",
)
@click.option(
    "--capture",
    is_flag=True,
    help="Capture new baseline",
)
@click.option(
    "--compare",
    is_flag=True,
    help="Compare with baseline",
)
@click.option("--auth-token", type=str, help="Authentication token")
@click.pass_context
def regression(
    ctx: click.Context,
    spec: str,
    base_url: str,
    baseline_dir: str,
    capture: bool,
    compare: bool,
    auth_token: Optional[str],
) -> None:
    """
    Run regression tests.

    Capture API response baselines and detect regressions including
    structural changes, data changes, and performance degradation.
    """
    console.print("[bold blue]API Regression Testing[/bold blue]")

    try:
        if not capture and not compare:
            raise CLIError("Must specify either --capture or --compare")

        # Get configuration
        config = ctx.obj.get("config", {})
        auth_token = auth_token or config.get("auth", {}).get("token")

        # Load specification
        spec_data = load_spec(spec)

        # Initialize components
        client_config = {
            "base_url": base_url,
            "timeout": config.get("timeout", 30),
        }
        client = APIClient(config=client_config)

        # Setup authentication
        if auth_token:
            client.set_bearer_token(auth_token)

        engine = RegressionEngine(baseline_dir=baseline_dir)

        if capture:
            # Capture baseline
            console.print("[blue]Capturing baseline...[/blue]")

            paths = spec_data.get("paths", {})
            total = sum(
                len(
                    [
                        k
                        for k in ops.keys()
                        if k in ["get", "post", "put", "delete", "patch"]
                    ]
                )
                for ops in paths.values()
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Capturing responses...", total=total)

                for path, operations in paths.items():
                    for http_method, operation in operations.items():
                        if http_method not in ["get", "post", "put", "delete", "patch"]:
                            continue

                        try:
                            api_response = client._request(http_method.upper(), path)
                            engine.capture_baseline(
                                endpoint=f"{http_method.upper()} {path}",
                                response=api_response.body,
                                method=http_method.upper(),
                                latency_ms=api_response.elapsed * 1000,
                            )
                        except Exception as e:
                            logger.warning(f"Failed to capture {path}: {e}")

                        progress.update(task, advance=1)

            console.print(f"[green]✓ Baseline captured to {baseline_dir}[/green]")

        if compare:
            # Compare with baseline
            console.print("[blue]Comparing with baseline...[/blue]")

            paths = spec_data.get("paths", {})
            total_changes = 0
            breaking_changes = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Analyzing changes...", total=len(paths))

                for path, operations in paths.items():
                    for http_method, operation in operations.items():
                        if http_method not in ["get", "post", "put", "delete", "patch"]:
                            continue

                        try:
                            api_response = client._request(http_method.upper(), path)
                            diff_result = engine.compare_with_baseline(
                                endpoint=f"{http_method.upper()} {path}",
                                response=api_response.body,
                                method=http_method.upper(),
                                latency_ms=api_response.elapsed * 1000,
                            )

                            if diff_result.has_breaking_changes:
                                total_changes += 1
                                if diff_result.breaking_changes:
                                    breaking_changes += len(
                                        diff_result.breaking_changes
                                    )

                        except Exception as e:
                            logger.warning(f"Failed to compare {path}: {e}")

                    progress.update(task, advance=1)

            # Display results
            console.print("\n[bold]Regression Results[/bold]")
            table = Table()
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Total Changes", str(total_changes))
            table.add_row(
                "Breaking Changes",
                (
                    f"[red]{breaking_changes}[/red]"
                    if breaking_changes > 0
                    else "[green]0[/green]"
                ),
            )
            console.print(table)

            if breaking_changes > 0:
                console.print("[red]⚠ Breaking changes detected[/red]")
                sys.exit(1)
            elif total_changes > 0:
                console.print("[yellow]⚠ Non-breaking changes detected[/yellow]")
            else:
                console.print("[green]✓ No regressions detected[/green]")

        sys.exit(0)

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Regression testing failed")
        sys.exit(2)


@cli.command()
@click.option(
    "--spec",
    type=click.Path(exists=True),
    required=True,
    help="OpenAPI spec file",
)
@click.option(
    "--base-url",
    type=str,
    required=True,
    help="Base API URL",
)
@click.option(
    "--requests",
    type=int,
    default=100,
    help="Number of requests",
)
@click.option(
    "--concurrency",
    type=int,
    default=10,
    help="Concurrent requests",
)
@click.option("--endpoint", type=str, help="Specific endpoint to test")
@click.option("--auth-token", type=str, help="Authentication token")
@click.pass_context
def performance(
    ctx: click.Context,
    spec: str,
    base_url: str,
    requests: int,
    concurrency: int,
    endpoint: Optional[str],
    auth_token: Optional[str],
) -> None:
    """
    Performance benchmarks.

    Basic performance testing with configurable request counts and
    concurrency levels. Measures latency, throughput, and error rates.
    """
    console.print("[bold blue]Performance Benchmarking[/bold blue]")

    try:
        # Get configuration
        config = ctx.obj.get("config", {})
        auth_token = auth_token or config.get("auth", {}).get("token")

        # Load specification
        spec_data = load_spec(spec)

        # Initialize API client
        client_config = {
            "base_url": base_url,
            "timeout": config.get("timeout", 30),
        }
        client = APIClient(config=client_config)

        # Setup authentication
        if auth_token:
            client.set_bearer_token(auth_token)

        # Get endpoints to test
        paths = spec_data.get("paths", {})
        if endpoint:
            paths = {endpoint: paths.get(endpoint, {})}

        endpoints = []
        for path, operations in paths.items():
            for http_method in operations.keys():
                if http_method in ["get", "post", "put", "delete", "patch"]:
                    endpoints.append((http_method.upper(), path))

        if not endpoints:
            raise CLIError("No endpoints found to test")

        console.print(
            f"[blue]Testing {len(endpoints)} endpoint(s) with "
            f"{requests} requests at {concurrency} concurrency[/blue]"
        )

        # Run performance tests
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for method, path in endpoints:
                task = progress.add_task(
                    f"Testing {method} {path}...",
                    total=requests,
                )

                latencies = []
                errors = 0
                start_time = time.time()

                for i in range(requests):
                    try:
                        api_response = client._request(method, path)
                        latencies.append(api_response.elapsed * 1000)
                    except Exception as e:
                        errors += 1
                        logger.debug(f"Request failed: {e}")

                    progress.update(task, advance=1)

                end_time = time.time()

                # Calculate metrics
                if latencies:
                    import statistics

                    avg_latency = statistics.mean(latencies)
                    min_latency = min(latencies)
                    max_latency = max(latencies)
                    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
                    p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
                else:
                    avg_latency = 0
                    min_latency = 0
                    max_latency = 0
                    p95_latency = 0
                    p99_latency = 0

                duration = end_time - start_time
                throughput = requests / duration if duration > 0 else 0

                results.append(
                    {
                        "endpoint": f"{method} {path}",
                        "requests": requests,
                        "errors": errors,
                        "avg_latency_ms": round(avg_latency, 2),
                        "min_latency_ms": round(min_latency, 2),
                        "max_latency_ms": round(max_latency, 2),
                        "p95_latency_ms": round(p95_latency, 2),
                        "p99_latency_ms": round(p99_latency, 2),
                        "throughput_rps": round(throughput, 2),
                    }
                )

        # Display results
        console.print("\n[bold]Performance Results[/bold]")
        table = Table()
        table.add_column("Endpoint", style="cyan")
        table.add_column("Requests", style="white")
        table.add_column("Errors", style="red")
        table.add_column("Avg Latency (ms)", style="white")
        table.add_column("P95 (ms)", style="yellow")
        table.add_column("P99 (ms)", style="yellow")
        table.add_column("Throughput (rps)", style="green")

        for result in results:
            table.add_row(
                result["endpoint"],
                str(result["requests"]),
                str(result["errors"]),
                str(result["avg_latency_ms"]),
                str(result["p95_latency_ms"]),
                str(result["p99_latency_ms"]),
                str(result["throughput_rps"]),
            )
        console.print(table)

        sys.exit(0)

    except CLIError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logger.exception("Performance testing failed")
        sys.exit(2)


if __name__ == "__main__":
    cli(obj={})
