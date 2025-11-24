"""
Cache Management CLI.

Command-line interface for LLM cache management, reasoning step caching,
and distributed cache operations with metrics and monitoring.

Protocol Coverage:
- P-COG-COT: Chain-of-Thought reasoning caching
- P-COG-TOT: Tree-of-Thoughts reasoning caching
- CORE-CACHE-003: LLM response caching with semantic similarity
- P-CACHE-MANAGEMENT: Distributed cache orchestration
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

# Import cache management modules
try:
    from .cache_manager import CacheManager, EvictionPolicy
    from .distributed_cache import DistributedCache, ReplicationConfig, ShardingStrategy
    from .llm_cache import CacheBackend, CacheConfig, LLMCache
    from .metrics import MetricsCollector
    from .reasoning_cache import CoTStep, ReasoningCache, ToTNode
    from .similarity_matcher import EmbeddingModel, SimilarityConfig, SimilarityMatcher
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).parent))
    from cache_manager import CacheManager, EvictionPolicy
    from distributed_cache import DistributedCache, ReplicationConfig, ShardingStrategy
    from llm_cache import CacheBackend, CacheConfig, LLMCache
    from metrics import MetricsCollector
    from reasoning_cache import CoTStep, ReasoningCache, ToTNode
    from similarity_matcher import EmbeddingModel, SimilarityConfig, SimilarityMatcher

# Initialize console
console = Console()
logger = logging.getLogger(__name__)


class CLIContext:
    """CLI context manager for shared state."""

    def __init__(self) -> None:
        """Initialize CLI context."""
        self.config_path: Optional[Path] = None
        self.config: Optional[Dict[str, Any]] = None
        self.cache_manager: Optional[CacheManager] = None
        self.metrics_collector: Optional[MetricsCollector] = None
        self.distributed_cache: Optional[DistributedCache] = None

    def load_config(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        if not config_path.exists():
            raise click.ClickException(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.config_path = config_path

    def initialize_cache_manager(self) -> None:
        """Initialize cache manager from config."""
        if not self.config:
            raise click.ClickException("Config not loaded")

        redis_host = self.config.get("redis_host", "localhost")
        redis_port = self.config.get("redis_port", 6379)
        redis_db = self.config.get("redis_db", 0)
        redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

        cache_config = CacheConfig(
            backend=CacheBackend(self.config.get("backend", "redis")),
            redis_url=redis_url,
            redis_db=redis_db,
            ttl_seconds=self.config.get("ttl_seconds", 3600),
            max_size_mb=self.config.get("max_size_mb", 500),
            max_entries=self.config.get("max_entries", 10000),
        )

        llm_cache = LLMCache(cache_config)
        reasoning_cache = ReasoningCache(cache_config)
        similarity_config = SimilarityConfig(
            model_name=EmbeddingModel.MINILM,
            threshold=self.config.get("similarity_threshold", 0.85),
        )
        similarity_matcher = SimilarityMatcher(similarity_config, llm_cache)

        self.cache_manager = CacheManager(
            llm_cache=llm_cache,
            reasoning_cache=reasoning_cache,
            similarity_matcher=similarity_matcher,
            eviction_policy=EvictionPolicy(self.config.get("eviction_policy", "lru")),
        )

        self.metrics_collector = MetricsCollector()

    def initialize_distributed_cache(self) -> None:
        """Initialize distributed cache from config."""
        if not self.config:
            raise click.ClickException("Config not loaded")

        if not self.cache_manager:
            self.initialize_cache_manager()

        distributed_config = self.config.get("distributed", {})
        replication_config = ReplicationConfig(
            replicas=distributed_config.get("replicas", 2),
        )

        # Parse node strings to dict format
        node_strings = distributed_config.get("nodes", ["localhost:6379"])
        redis_cluster_nodes = []
        for node_str in node_strings:
            if ":" in node_str:
                host, port = node_str.split(":", 1)
                redis_cluster_nodes.append({"host": host, "port": int(port)})
            else:
                redis_cluster_nodes.append({"host": node_str, "port": 6379})

        self.distributed_cache = DistributedCache(
            redis_cluster_nodes=redis_cluster_nodes,
            replication_config=replication_config,
            sharding_strategy=ShardingStrategy(
                distributed_config.get("sharding", "consistent_hash")
            ),
        )


# Create global context
cli_context = CLIContext()


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default="cache_config.yaml",
    help="Path to configuration file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
def cli(config: Path, verbose: bool, debug: bool) -> None:
    """
    Cache Management CLI.

    Intelligent LLM response caching, reasoning step caching, and
    distributed cache operations.
    """
    # Configure logging
    log_level = (
        logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    )
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load config if exists
    if config.exists():
        try:
            cli_context.load_config(config)
            if verbose:
                console.print(f"[green]Loaded config from {config}[/green]")
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.argument("prompt")
@click.argument("response")
@click.option("--model", "-m", default="gpt-4", help="LLM model name")
@click.option("--ttl", "-t", type=int, help="TTL in seconds (overrides config)")
@click.option(
    "--metadata",
    "-M",
    type=str,
    help="JSON metadata string",
)
def set_cache(
    prompt: str, response: str, model: str, ttl: Optional[int], metadata: str
) -> None:
    """
    Cache an LLM response.

    \b
    Examples:
        cache-cli set "What is Python?" "Python is a programming language"
        cache-cli set "Translate to French" "Bonjour" -m gpt-3.5-turbo
        cache-cli set "Code review" "LGTM" --ttl 7200
    """
    try:
        cli_context.initialize_cache_manager()

        # Parse metadata
        meta_dict = {}
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except json.JSONDecodeError:
                console.print("[yellow]Warning: Invalid JSON metadata[/yellow]")

        # Store in cache using the LLMCache set method
        success = cli_context.cache_manager.llm_cache.set(
            prompt=prompt,
            response=response,
            ttl=ttl,
            metadata=meta_dict,
            token_count=len(response.split()),
            model_name=model,
        )

        if success:
            console.print(
                Panel(
                    f"[green]Cached response for prompt:[/green]\n{prompt}",
                    title="Cache Set",
                    border_style="green",
                )
            )
        else:
            console.print("[red]Failed to cache response[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error setting cache: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("prompt")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "text", "yaml"]),
    default="text",
    help="Output format",
)
def get_cache(prompt: str, format: str) -> None:
    """
    Retrieve a cached LLM response.

    \b
    Examples:
        cache-cli get "What is Python?"
        cache-cli get "Translate to French" --format json
        cache-cli get "Code review" -f yaml
    """
    try:
        cli_context.initialize_cache_manager()

        # Retrieve from cache
        cached_response = cli_context.cache_manager.llm_cache.get(prompt=prompt)

        if not cached_response:
            console.print("[yellow]Cache miss - no entry found[/yellow]")
            sys.exit(0)

        # Format output
        if format == "json":
            output = json.dumps(cached_response.model_dump(), indent=2, default=str)
            console.print(Syntax(output, "json", theme="monokai"))
        elif format == "yaml":
            output = yaml.dump(cached_response.model_dump(), default_flow_style=False)
            console.print(Syntax(output, "yaml", theme="monokai"))
        else:
            # Text format
            table = Table(title="Cached Response", show_header=True)
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Response", cached_response.value)
            table.add_row("Model", cached_response.model_name or "N/A")
            table.add_row(
                "Timestamp",
                datetime.fromtimestamp(cached_response.timestamp).isoformat(),
            )
            table.add_row("Token Count", str(cached_response.token_count or 0))
            table.add_row("Hit Count", str(cached_response.hit_count))

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting cache: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("prompt")
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.85,
    help="Similarity threshold (0.0-1.0)",
)
@click.option("--limit", "-l", type=int, default=5, help="Max results to return")
def get_similar(prompt: str, threshold: float, limit: int) -> None:
    """
    Find similar cached responses using semantic search.

    \b
    Examples:
        cache-cli get-similar "Explain Python"
        cache-cli get-similar "What is ML?" --threshold 0.9
        cache-cli get-similar "Code review guidelines" -t 0.8 -l 10
    """
    try:
        cli_context.initialize_cache_manager()

        # Find similar entries
        similar_matches = cli_context.cache_manager.similarity_matcher.find_similar(
            prompt=prompt,
            threshold=threshold,
            top_k=limit,
        )

        if not similar_matches:
            console.print(
                f"[yellow]No similar entries found "
                f"(threshold: {threshold})[/yellow]"
            )
            sys.exit(0)

        # Display results
        table = Table(
            title=f"Similar Cached Entries (threshold: {threshold})",
            show_header=True,
        )
        table.add_column("Score", style="cyan", justify="right")
        table.add_column("Prompt", style="green")
        table.add_column("Response Preview", style="yellow")

        for match in similar_matches:
            response_preview = match.response[:100] + (
                "..." if len(match.response) > 100 else ""
            )
            table.add_row(
                f"{match.similarity_score:.3f}",
                match.prompt,
                response_preview,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error finding similar entries: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("reasoning_type", type=click.Choice(["cot", "tot"]))
@click.argument("problem")
@click.argument("steps_json")
@click.option("--final-answer", "-a", help="Final answer/solution")
def set_reasoning(
    reasoning_type: str,
    problem: str,
    steps_json: str,
    final_answer: Optional[str],
) -> None:
    """
    Cache reasoning steps (CoT or ToT).

    \b
    Examples:
        cache-cli set-reasoning cot "2+2=?" '[{"step":1,"text":"Add"}]'
        cache-cli set-reasoning tot "Pathfinding" '[{"id":"n1"}]' -a "A*"
    """
    try:
        cli_context.initialize_cache_manager()

        # Parse steps
        try:
            steps_data = json.loads(steps_json)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON for steps: {e}[/red]")
            sys.exit(1)

        if reasoning_type == "cot":
            # Chain-of-Thought
            steps = [
                CoTStep(
                    step_number=s.get("step", i + 1),
                    thought=s.get("text", ""),
                    result=s.get("result", ""),
                    confidence=s.get("confidence", 1.0),
                )
                for i, s in enumerate(steps_data)
            ]

            pass  # Steps are already created above
        else:
            # Tree-of-Thoughts
            nodes_dict = {}
            for i, s in enumerate(steps_data):
                node = ToTNode(
                    node_id=s.get("id", f"node_{i}"),
                    thought=s.get("text", ""),
                    evaluation_score=s.get("score", 0.5),
                    parent_id=s.get("parent"),
                    children=s.get("children", []),
                    depth=s.get("depth", 0),
                )
                nodes_dict[node.node_id] = node

            # Find root node (one without parent)
            root_node = next(
                (n for n in nodes_dict.values() if n.parent_id is None), None
            )
            if root_node is None and nodes_dict:
                root_node = list(nodes_dict.values())[0]

        # Store in cache based on type
        if reasoning_type == "cot":
            cli_context.cache_manager.reasoning_cache.cache_cot_steps(
                problem=problem,
                steps=steps,
                solution=final_answer or "",
            )
        else:
            cli_context.cache_manager.reasoning_cache.cache_tot_tree(
                problem=problem,
                tree_root=root_node,
                tree_nodes=nodes_dict,
                solution=final_answer or "",
            )

        console.print(
            Panel(
                f"[green]Cached {reasoning_type.upper()} reasoning for:[/green]\n"
                f"{problem}\n\n"
                f"Steps: {len(steps_data)}",
                title="Reasoning Cache Set",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]Error setting reasoning cache: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("problem")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "tree", "yaml"]),
    default="tree",
    help="Output format",
)
def get_reasoning(problem: str, format: str) -> None:
    """
    Retrieve cached reasoning steps.

    \b
    Examples:
        cache-cli get-reasoning "2+2=?"
        cache-cli get-reasoning "Pathfinding" --format json
        cache-cli get-reasoning "Algorithm" -f tree
    """
    try:
        cli_context.initialize_cache_manager()

        # Retrieve from cache
        cache_mgr = cli_context.cache_manager.reasoning_cache
        reasoning_result = cache_mgr.get_reasoning_result(problem=problem)

        if not reasoning_result:
            console.print("[yellow]Cache miss - no entry found[/yellow]")
            sys.exit(0)

        # Format output
        if format == "json":
            output = json.dumps(reasoning_result.model_dump(), indent=2, default=str)
            console.print(Syntax(output, "json", theme="monokai"))
        elif format == "yaml":
            output = yaml.dump(
                reasoning_result.model_dump(), default_flow_style=False
            )
            console.print(Syntax(output, "yaml", theme="monokai"))
        else:
            # Tree format
            tree = Tree(f"[bold]{problem}[/bold]")

            if reasoning_result.reasoning_type == "cot":
                if reasoning_result.steps:
                    for step in reasoning_result.steps:
                        step_node = tree.add(
                            f"Step {step.step_number}: {step.thought}"
                        )
                        step_node.add(f"[dim]{step.result}[/dim]")
                        if step.confidence:
                            step_node.add(
                                f"[cyan]Confidence: {step.confidence:.2f}[/cyan]"
                            )
            else:
                # ToT
                if reasoning_result.tree_nodes:
                    node_map = reasoning_result.tree_nodes
                    root_nodes = [
                        n for n in node_map.values() if not n.parent_id
                    ]

                    def add_tot_node(parent_tree: Tree, node: ToTNode) -> None:
                        """Add ToT node to tree recursively."""
                        node_tree = parent_tree.add(
                            f"{node.node_id}: {node.thought} "
                            f"[cyan](score: {node.evaluation_score:.2f})[/cyan]"
                        )
                        for child_id in node.children:
                            if child_id in node_map:
                                add_tot_node(node_tree, node_map[child_id])

                    for root in root_nodes:
                        add_tot_node(tree, root)

            console.print(tree)

            if reasoning_result.solution:
                console.print(
                    Panel(
                        reasoning_result.solution,
                        title="[bold green]Final Answer[/bold green]",
                        border_style="green",
                    )
                )

    except Exception as e:
        console.print(f"[red]Error getting reasoning cache: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--pattern", "-p", help="Pattern to match for invalidation")
@click.option("--regex", "-r", is_flag=True, help="Use regex pattern matching")
@click.option(
    "--older-than",
    "-o",
    type=int,
    help="Invalidate entries older than N seconds",
)
@click.option("--all", "-a", is_flag=True, help="Invalidate all cache entries")
@click.option(
    "--confirm/--no-confirm",
    default=True,
    help="Confirm before invalidation",
)
def invalidate(
    pattern: Optional[str],
    regex: bool,
    older_than: Optional[int],
    all: bool,
    confirm: bool,
) -> None:
    """
    Invalidate cache entries by pattern or age.

    \b
    Examples:
        cache-cli invalidate --pattern "What is*"
        cache-cli invalidate --regex --pattern "^Code.*"
        cache-cli invalidate --older-than 3600
        cache-cli invalidate --all
    """
    try:
        cli_context.initialize_cache_manager()

        if not any([pattern, older_than, all]):
            console.print(
                "[red]Error: Must specify --pattern, --older-than, " "or --all[/red]"
            )
            sys.exit(1)

        # Confirm operation
        if confirm:
            if all:
                msg = "Invalidate ALL cache entries?"
            elif pattern:
                msg = f"Invalidate entries matching '{pattern}'?"
            else:
                msg = f"Invalidate entries older than {older_than}s?"

            if not click.confirm(msg):
                console.print("[yellow]Operation cancelled[/yellow]")
                sys.exit(0)

        # Perform invalidation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Invalidating cache...", total=None)

            if all:
                cli_context.cache_manager.llm_cache.clear()
                cli_context.cache_manager.reasoning_cache.invalidate_pattern("*")
                count = 0  # Cannot easily count cleared entries
            elif pattern:
                count = cli_context.cache_manager.llm_cache.invalidate(pattern)
                count += cli_context.cache_manager.reasoning_cache.invalidate_pattern(
                    pattern
                )
            else:
                # For older_than, need to get all keys and check timestamps
                count = 0
                console.print(
                    "[yellow]Warning: older_than not fully implemented[/yellow]"
                )

            progress.update(task, completed=True)

        console.print(
            Panel(
                f"[green]Invalidated {count} cache entries[/green]",
                title="Invalidation Complete",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]Error invalidating cache: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "table", "yaml"]),
    default="table",
    help="Output format",
)
def stats(format: str) -> None:
    """
    Display cache statistics.

    \b
    Examples:
        cache-cli stats
        cache-cli stats --format json
        cache-cli stats -f yaml
    """
    try:
        cli_context.initialize_cache_manager()

        # Collect statistics from LLMCache
        llm_cache_stats = cli_context.cache_manager.llm_cache.get_stats()

        if format == "json":
            output = json.dumps(llm_cache_stats.model_dump(), indent=2, default=str)
            console.print(Syntax(output, "json", theme="monokai"))
        elif format == "yaml":
            output = yaml.dump(
                llm_cache_stats.model_dump(), default_flow_style=False
            )
            console.print(Syntax(output, "yaml", theme="monokai"))
        else:
            # Table format
            table = Table(title="Cache Statistics", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            table.add_row("Total Entries", str(llm_cache_stats.total_entries))
            table.add_row("Cache Hits", str(llm_cache_stats.total_hits))
            table.add_row("Cache Misses", str(llm_cache_stats.total_misses))
            table.add_row("Hit Rate", f"{llm_cache_stats.hit_rate * 100:.2f}%")
            table.add_row(
                "Total Size (MB)", f"{llm_cache_stats.total_size_mb:.2f}"
            )
            table.add_row("Backend", llm_cache_stats.backend)
            table.add_row("Eviction Policy", llm_cache_stats.eviction_policy)

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting stats: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("queries_file", type=click.Path(exists=True, path_type=Path))
@click.option("--workers", "-w", type=int, default=4, help="Number of worker threads")
@click.option("--batch-size", "-b", type=int, default=10, help="Batch size")
def warm(queries_file: Path, workers: int, batch_size: int) -> None:
    """
    Warm cache with queries from file.

    \b
    File format (JSON):
        [
            {"prompt": "What is Python?", "response": "..."},
            {"prompt": "Translate hello", "response": "..."}
        ]

    \b
    Examples:
        cache-cli warm queries.json
        cache-cli warm queries.json --workers 8 --batch-size 20
    """
    try:
        cli_context.initialize_cache_manager()

        # Load queries
        with open(queries_file, "r") as f:
            queries = json.load(f)

        if not isinstance(queries, list):
            console.print("[red]Error: Queries file must be JSON array[/red]")
            sys.exit(1)

        console.print(f"[cyan]Loading {len(queries)} queries...[/cyan]")

        # Warm cache
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Warming cache ({len(queries)} queries)...",
                total=len(queries),
            )

            def warm_with_progress() -> int:
                """Warm cache and update progress."""
                count = 0
                for query in queries:
                    cli_context.cache_manager.llm_cache.set(
                        prompt=query["prompt"],
                        response=query["response"],
                        model_name=query.get("model", "unknown"),
                        token_count=len(query["response"].split()),
                        metadata=query.get("metadata", {}),
                    )
                    count += 1
                    progress.update(task, advance=1)
                return count

            warmed_count = warm_with_progress()

        console.print(
            Panel(
                f"[green]Warmed cache with {warmed_count} entries[/green]",
                title="Cache Warming Complete",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]Error warming cache: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--port", "-p", type=int, default=8000, help="Prometheus metrics port")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["prometheus", "json", "yaml"]),
    default="prometheus",
    help="Metrics format",
)
def metrics(port: int, format: str) -> None:
    """
    Display or export cache metrics.

    \b
    Examples:
        cache-cli metrics
        cache-cli metrics --port 9090
        cache-cli metrics --format json
    """
    try:
        if not cli_context.metrics_collector:
            cli_context.initialize_cache_manager()

        cache_metrics = cli_context.metrics_collector.get_metrics()
        perf_metrics = cli_context.metrics_collector.get_performance_metrics()

        if format == "json":
            output = {
                "cache": cache_metrics.model_dump(),
                "performance": perf_metrics.model_dump(),
            }
            console.print(Syntax(json.dumps(output, indent=2), "json", theme="monokai"))
        elif format == "yaml":
            output = {
                "cache": cache_metrics.model_dump(),
                "performance": perf_metrics.model_dump(),
            }
            console.print(
                Syntax(
                    yaml.dump(output, default_flow_style=False),
                    "yaml",
                    theme="monokai",
                )
            )
        else:
            # Prometheus format
            console.print(
                f"[cyan]Metrics available at http://localhost:{port}/metrics" "[/cyan]"
            )

            # Display sample metrics
            table = Table(title="Cache Metrics", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            table.add_row("cache_hits_total", str(cache_metrics.total_hits))
            table.add_row("cache_misses_total", str(cache_metrics.total_misses))
            table.add_row("total_requests", str(cache_metrics.total_requests))
            table.add_row("hit_rate", f"{cache_metrics.hit_rate * 100:.2f}%")
            table.add_row("avg_latency_ms", f"{cache_metrics.avg_latency_ms:.2f}")

            console.print(table)

            # Performance metrics
            perf_table = Table(title="Performance Metrics", show_header=True)
            perf_table.add_column("Metric", style="cyan")
            perf_table.add_column("Value", style="green", justify="right")

            perf_table.add_row(
                "Avg Cached Latency (ms)",
                f"{perf_metrics.avg_latency_cached_ms:.2f}",
            )
            perf_table.add_row(
                "Avg Uncached Latency (ms)",
                f"{perf_metrics.avg_latency_uncached_ms:.2f}",
            )
            perf_table.add_row(
                "Speedup Factor",
                f"{perf_metrics.speedup_factor:.2f}x",
            )
            perf_table.add_row(
                "Cost Savings (USD)",
                f"${perf_metrics.cost_savings_usd:.4f}",
            )

            console.print(perf_table)

    except Exception as e:
        console.print(f"[red]Error getting metrics: {e}[/red]")
        sys.exit(1)


@cli.group()
def config() -> None:
    """Configuration management commands."""
    pass


@config.command()
def show() -> None:
    """Display current configuration."""
    try:
        if not cli_context.config:
            console.print("[yellow]No configuration loaded[/yellow]")
            sys.exit(0)

        syntax = Syntax(
            yaml.dump(cli_context.config, default_flow_style=False),
            "yaml",
            theme="monokai",
            line_numbers=True,
        )
        console.print(
            Panel(
                syntax,
                title=f"Configuration: {cli_context.config_path}",
                border_style="cyan",
            )
        )

    except Exception as e:
        console.print(f"[red]Error showing config: {e}[/red]")
        sys.exit(1)


@config.command()
@click.argument("key")
@click.argument("value")
def set_config(key: str, value: str) -> None:
    """
    Set configuration value.

    \b
    Examples:
        cache-cli config set backend redis
        cache-cli config set ttl_seconds 7200
        cache-cli config set similarity_threshold 0.9
    """
    try:
        if not cli_context.config:
            cli_context.config = {}

        # Parse value
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            parsed_value = value

        # Set nested keys
        keys = key.split(".")
        current = cli_context.config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = parsed_value

        # Save config
        if cli_context.config_path:
            with open(cli_context.config_path, "w") as f:
                yaml.dump(cli_context.config, f, default_flow_style=False)

        console.print(f"[green]Set {key} = {parsed_value}[/green]")

    except Exception as e:
        console.print(f"[red]Error setting config: {e}[/red]")
        sys.exit(1)


@config.command()
def validate() -> None:
    """Validate configuration file."""
    try:
        if not cli_context.config:
            console.print("[yellow]No configuration loaded[/yellow]")
            sys.exit(0)

        errors = []

        # Validate required fields
        required_fields = ["backend", "redis_host", "redis_port"]
        for field in required_fields:
            if field not in cli_context.config:
                errors.append(f"Missing required field: {field}")

        # Validate backend
        valid_backends = ["redis", "memory", "disk"]
        if cli_context.config.get("backend") not in valid_backends:
            errors.append(
                f"Invalid backend: {cli_context.config.get('backend')} "
                f"(must be one of {valid_backends})"
            )

        # Validate numeric fields
        numeric_fields = {
            "redis_port": (1, 65535),
            "ttl_seconds": (1, None),
            "max_size": (1, None),
        }
        for field, (min_val, max_val) in numeric_fields.items():
            if field in cli_context.config:
                val = cli_context.config[field]
                if not isinstance(val, (int, float)):
                    errors.append(f"{field} must be numeric")
                elif min_val and val < min_val:
                    errors.append(f"{field} must be >= {min_val}")
                elif max_val and val > max_val:
                    errors.append(f"{field} must be <= {max_val}")

        if errors:
            console.print("[red]Configuration validation failed:[/red]")
            for error in errors:
                console.print(f"  - {error}")
            sys.exit(1)
        else:
            console.print("[green]Configuration is valid[/green]")

    except Exception as e:
        console.print(f"[red]Error validating config: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Export format",
)
@click.option("--filter", "-F", help="Filter pattern for keys to export")
def export(output_file: Path, format: str, filter: Optional[str]) -> None:
    """
    Export cache entries to file.

    \b
    Examples:
        cache-cli export cache_backup.json
        cache-cli export cache_backup.yaml --format yaml
        cache-cli export filtered.json --filter "Code*"
    """
    try:
        cli_context.initialize_cache_manager()

        # Export entries
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Exporting cache...", total=None)

            # Get all keys and export them
            all_keys = cli_context.cache_manager.llm_cache.get_all_keys(
                pattern=filter or "*"
            )
            entries = []
            for key in all_keys:
                cached_response = cli_context.cache_manager.llm_cache.get_entry_by_key(
                    key
                )
                if cached_response:
                    entries.append(cached_response.model_dump())

            progress.update(task, completed=True)

        # Write to file
        with open(output_file, "w") as f:
            if format == "yaml":
                yaml.dump(entries, f, default_flow_style=False)
            else:
                json.dump(entries, f, indent=2, default=str)

        console.print(
            Panel(
                f"[green]Exported {len(entries)} entries to " f"{output_file}[/green]",
                title="Export Complete",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]Error exporting cache: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--merge/--replace",
    default=True,
    help="Merge with existing entries or replace",
)
@click.option(
    "--confirm/--no-confirm",
    default=True,
    help="Confirm before import",
)
def import_cache(input_file: Path, merge: bool, confirm: bool) -> None:
    """
    Import cache entries from file.

    \b
    Examples:
        cache-cli import cache_backup.json
        cache-cli import cache_backup.yaml --replace
        cache-cli import filtered.json --no-confirm
    """
    try:
        cli_context.initialize_cache_manager()

        # Load entries
        with open(input_file, "r") as f:
            if input_file.suffix in [".yaml", ".yml"]:
                entries = yaml.safe_load(f)
            else:
                entries = json.load(f)

        if not isinstance(entries, list):
            console.print("[red]Error: Import file must contain array[/red]")
            sys.exit(1)

        # Confirm operation
        if confirm:
            action = "merge" if merge else "replace"
            if not click.confirm(f"Import {len(entries)} entries ({action} mode)?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                sys.exit(0)

        # Import entries
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Importing {len(entries)} entries...",
                total=len(entries),
            )

            def import_with_progress() -> int:
                """Import entries and update progress."""
                if not merge:
                    cli_context.cache_manager.llm_cache.clear()

                count = 0
                for entry in entries:
                    # Import using the value from the cached response
                    cli_context.cache_manager.llm_cache.set(
                        prompt=entry.get("key", ""),
                        response=entry.get("value", ""),
                        model_name=entry.get("model_name", "unknown"),
                        token_count=entry.get("token_count", 0),
                        metadata=entry.get("metadata", {}),
                    )
                    count += 1
                    progress.update(task, advance=1)
                return count

            imported_count = import_with_progress()

        console.print(
            Panel(
                f"[green]Imported {imported_count} entries[/green]",
                title="Import Complete",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]Error importing cache: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
