"""
Knowledge Graph Management CLI for devCrew_s1.

This module provides a comprehensive command-line interface for the Knowledge
Graph Management Platform, supporting extraction, building, querying, search,
RAG, visualization, and analysis operations.

Author: devCrew_s1
License: MIT
"""

import json
import sys
from pathlib import Path
# No typing imports needed

import click
import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

# Initialize Rich console
console = Console()


# Custom exception for CLI errors
class CLIError(click.ClickException):
    """Custom CLI exception with rich formatting."""

    def show(self, file=None):
        """Show error message with rich formatting."""
        console.print(f"[red bold]Error:[/red bold] {self.message}")


@click.group()
@click.version_option(version="1.0.0", prog_name="kg-cli")
@click.pass_context
def cli(ctx):
    """
    Knowledge Graph Management CLI for devCrew_s1.

    A comprehensive tool for building, querying, and analyzing knowledge graphs
    with Neo4j, featuring semantic search, RAG integration, and advanced analytics.

    \b
    Examples:
        # Extract entities from documents
        kg extract --input docs/ --output entities.json

        # Build knowledge graph
        kg build --entities entities.json --neo4j-uri bolt://localhost:7687

        # Query with natural language
        kg query --nl "Find all people who work at Google"

        # Run graph analysis
        kg analyze --type pagerank --top-k 20

    Configuration:
        Set default config in ~/.kg-config.yaml or use --config flag.
    """
    ctx.ensure_object(dict)

    # Load config if exists
    config_path = Path.home() / ".kg-config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            ctx.obj["config"] = yaml.safe_load(f)
    else:
        ctx.obj["config"] = {}


@cli.command()
@click.option(
    "--input",
    "-i",
    "input_path",
    required=True,
    type=click.Path(exists=True),
    help="Input directory or file containing documents",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    required=True,
    type=click.Path(),
    help="Output JSON file for extracted entities",
)
@click.option(
    "--method",
    type=click.Choice(["spacy", "llm", "hybrid"]),
    default="hybrid",
    help="Extraction method (default: hybrid)",
)
@click.option(
    "--llm-model",
    default="gpt-4",
    help="LLM model for extraction (default: gpt-4)",
)
@click.option(
    "--batch-size",
    default=10,
    type=int,
    help="Batch size for processing (default: 10)",
)
@click.option(
    "--entity-types",
    help="Comma-separated entity types to extract (e.g., PERSON,ORG,GPE)",
)
@click.pass_context
def extract(ctx, input_path, output_path, method, llm_model, batch_size, entity_types):
    """
    Extract entities and relationships from documents.

    This command processes documents using spaCy NER, LLM-based extraction,
    or a hybrid approach to identify entities and their relationships.

    \b
    Examples:
        # Extract with spaCy
        kg extract -i docs/ -o entities.json --method spacy

        # Extract with LLM
        kg extract -i docs/ -o entities.json --method llm --llm-model gpt-4

        # Extract specific entity types
        kg extract -i docs/ -o entities.json --entity-types PERSON,ORG
    """
    try:
        from knowledge_extractor import ExtractorConfig, KnowledgeExtractor

        console.print(f"[bold blue]Extracting entities from:[/bold blue] {input_path}")

        # Build entity types list
        entity_types_list = None
        if entity_types:
            entity_types_list = [t.strip() for t in entity_types.split(",")]

        # Configure extractor
        config = ExtractorConfig(
            spacy_model="en_core_web_sm",
            llm_model=llm_model,
            enable_llm=method in ["llm", "hybrid"],
        )

        extractor = KnowledgeExtractor(config)

        # Process input
        input_p = Path(input_path)
        documents = []

        if input_p.is_file():
            with open(input_p) as f:
                documents = [{"id": input_p.stem, "text": f.read()}]
        else:
            # Process directory
            for file_path in input_p.glob("**/*.txt"):
                with open(file_path) as f:
                    documents.append({"id": file_path.stem, "text": f.read()})

        if not documents:
            raise CLIError("No documents found to process")

        # Extract with progress bar
        all_entities = []
        all_relationships = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Extracting from {len(documents)} document(s)...",
                total=len(documents),
            )

            for doc in documents:
                if method == "spacy":
                    entities = extractor.extract_entities_spacy(
                        doc["text"], entity_types_list
                    )
                elif method == "llm":
                    entities = extractor.extract_entities_llm(
                        doc["text"], entity_types_list
                    )
                else:  # hybrid
                    entities = extractor.extract_entities_spacy(
                        doc["text"], entity_types_list
                    )
                    llm_entities = extractor.extract_entities_llm(
                        doc["text"], entity_types_list
                    )
                    entities.extend(llm_entities)

                all_entities.extend(entities)

                # Extract relationships
                if method in ["llm", "hybrid"]:
                    relationships = extractor.extract_relationships(doc["text"])
                    all_relationships.extend(relationships)

                progress.advance(task)

        # Save results
        results = {"entities": all_entities, "relationships": all_relationships}

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        # Display summary
        console.print(
            f"\n[green]✓[/green] Extracted {len(all_entities)} entities "
            f"and {len(all_relationships)} relationships"
        )
        console.print(f"[green]✓[/green] Results saved to: {output_path}")

        # Show sample
        if all_entities:
            table = Table(title="Sample Entities", box=box.ROUNDED)
            table.add_column("Text", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Confidence", style="green")

            for entity in all_entities[:5]:
                table.add_row(
                    entity.get("text", ""),
                    entity.get("label", ""),
                    f"{entity.get('confidence', 0):.2f}",
                )

            console.print(table)

    except Exception as e:
        raise CLIError(f"Extraction failed: {e}")


@cli.command()
@click.option(
    "--entities",
    "-e",
    "entities_path",
    required=True,
    type=click.Path(exists=True),
    help="JSON file containing extracted entities",
)
@click.option(
    "--neo4j-uri",
    required=True,
    help="Neo4j database URI (e.g., bolt://localhost:7687)",
)
@click.option("--username", default="neo4j", help="Neo4j username (default: neo4j)")
@click.option("--password", required=True, help="Neo4j password")
@click.option(
    "--batch-size",
    default=500,
    type=int,
    help="Batch size for imports (default: 500)",
)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear existing graph data before building",
)
@click.pass_context
def build(ctx, entities_path, neo4j_uri, username, password, batch_size, clear):
    """
    Build knowledge graph in Neo4j from extracted entities.

    This command creates nodes and relationships in Neo4j based on
    extracted entities and relationships.

    \b
    Examples:
        # Build graph
        kg build -e entities.json --neo4j-uri bolt://localhost:7687 --password pass

        # Clear and rebuild
        kg build -e entities.json --neo4j-uri bolt://localhost:7687 \\
            --password pass --clear
    """
    try:
        from graph_builder import BuilderConfig, GraphBuilder

        console.print("[bold blue]Building knowledge graph...[/bold blue]")

        # Load entities
        with open(entities_path) as f:
            data = json.load(f)
            entities = data.get("entities", [])
            relationships = data.get("relationships", [])

        if not entities:
            raise CLIError("No entities found in input file")

        # Configure builder
        config = BuilderConfig(
            neo4j_uri=neo4j_uri,
            auth=(username, password),
            batch_size=batch_size,
        )

        builder = GraphBuilder(config)

        # Clear if requested
        if clear:
            with console.status("[yellow]Clearing existing data...[/yellow]"):
                builder.clear_graph()
            console.print("[green]✓[/green] Cleared existing graph")

        # Create schema
        with console.status("[yellow]Creating schema...[/yellow]"):
            builder.create_schema(entities, relationships)
        console.print("[green]✓[/green] Created graph schema")

        # Import entities
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Importing {len(entities)} entities...", total=len(entities)
            )

            for i in range(0, len(entities), batch_size):
                batch = entities[i : i + batch_size]
                builder.create_entities_batch(batch)
                progress.advance(task, advance=len(batch))

        console.print(f"[green]✓[/green] Imported {len(entities)} entities")

        # Import relationships
        if relationships:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Importing {len(relationships)} relationships...",
                    total=len(relationships),
                )

                for i in range(0, len(relationships), batch_size):
                    batch = relationships[i : i + batch_size]
                    builder.create_relationships_batch(batch)
                    progress.advance(task, advance=len(batch))

            console.print(
                f"[green]✓[/green] Imported {len(relationships)} relationships"
            )

        # Get statistics
        stats = builder.get_statistics()

        # Display summary
        table = Table(title="Graph Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        for key, value in stats.items():
            table.add_row(key.replace("_", " ").title(), str(value))

        console.print("\n", table)

        builder.close()

    except Exception as e:
        raise CLIError(f"Build failed: {e}")


@cli.command()
@click.option(
    "--cypher",
    "-c",
    help="Cypher query to execute",
)
@click.option(
    "--nl",
    "-n",
    help="Natural language query to translate and execute",
)
@click.option(
    "--neo4j-uri",
    required=True,
    help="Neo4j database URI",
)
@click.option("--username", default="neo4j", help="Neo4j username")
@click.option("--password", required=True, help="Neo4j password")
@click.option(
    "--format",
    type=click.Choice(["table", "json", "cypher"]),
    default="table",
    help="Output format (default: table)",
)
@click.option(
    "--limit",
    default=25,
    type=int,
    help="Maximum results to return (default: 25)",
)
@click.pass_context
def query(ctx, cypher, nl, neo4j_uri, username, password, format, limit):
    """
    Execute Cypher or natural language queries.

    This command supports both direct Cypher queries and natural language
    queries that are automatically translated to Cypher.

    \b
    Examples:
        # Cypher query
        kg query -c "MATCH (n:Person) RETURN n LIMIT 10" \\
            --neo4j-uri bolt://localhost:7687 --password pass

        # Natural language query
        kg query -n "Find all people who work at Google" \\
            --neo4j-uri bolt://localhost:7687 --password pass

        # JSON output
        kg query -c "MATCH (n) RETURN n LIMIT 5" \\
            --neo4j-uri bolt://localhost:7687 --password pass --format json
    """
    if not cypher and not nl:
        raise CLIError("Must provide either --cypher or --nl")

    if cypher and nl:
        raise CLIError("Cannot provide both --cypher and --nl")

    try:
        from graph_query import CypherQuery, GraphQueryEngine, QueryConfig

        # Configure query engine
        config = QueryConfig(
            neo4j_uri=neo4j_uri,
            auth=(username, password),
            enable_nl_translation=bool(nl),
        )

        engine = GraphQueryEngine(config)

        # Execute query
        if nl:
            console.print(f"[bold blue]Translating query:[/bold blue] {nl}")
            with console.status("[yellow]Translating to Cypher...[/yellow]"):
                result = engine.execute_natural_language(nl)
            console.print(f"[green]✓[/green] Generated Cypher: {result.query}")
        else:
            console.print("[bold blue]Executing Cypher query...[/bold blue]")
            query_obj = CypherQuery(query=cypher)
            result = engine.execute_cypher(query_obj)

        # Display results based on format
        if format == "json":
            console.print_json(json.dumps(result.records[:limit], indent=2))

        elif format == "cypher":
            syntax = Syntax(result.query, "cypher", theme="monokai", line_numbers=True)
            console.print(syntax)

        else:  # table
            if not result.records:
                console.print("[yellow]No results found[/yellow]")
            else:
                # Build table from first record keys
                table = Table(
                    title=f"Query Results ({result.summary})", box=box.ROUNDED
                )

                # Add columns
                first_record = result.records[0]
                for key in first_record.keys():
                    table.add_column(key, style="cyan")

                # Add rows (limited)
                for record in result.records[:limit]:
                    row = []
                    for value in record.values():
                        if isinstance(value, dict):
                            row.append(json.dumps(value, indent=2))
                        else:
                            row.append(str(value))
                    table.add_row(*row)

                console.print(table)

        # Display metadata
        console.print(
            f"\n[dim]Execution time: {result.execution_time:.3f}s | "
            f"Records: {len(result.records)}[/dim]"
        )

        engine.close()

    except Exception as e:
        raise CLIError(f"Query failed: {e}")


@cli.command()
@click.option(
    "--query",
    "-q",
    required=True,
    help="Search query text",
)
@click.option(
    "--neo4j-uri",
    required=True,
    help="Neo4j database URI",
)
@click.option("--username", default="neo4j", help="Neo4j username")
@click.option("--password", required=True, help="Neo4j password")
@click.option(
    "--top-k",
    default=10,
    type=int,
    help="Number of results to return (default: 10)",
)
@click.option(
    "--entity-type",
    help="Filter by entity type (e.g., Person, Organization)",
)
@click.option(
    "--method",
    type=click.Choice(["vector", "keyword", "hybrid"]),
    default="hybrid",
    help="Search method (default: hybrid)",
)
@click.pass_context
def search(ctx, query, neo4j_uri, username, password, top_k, entity_type, method):
    """
    Perform semantic search on knowledge graph entities.

    This command searches entities using vector similarity, keyword matching,
    or a hybrid approach combining both methods.

    \b
    Examples:
        # Semantic search
        kg search -q "artificial intelligence researchers" \\
            --neo4j-uri bolt://localhost:7687 --password pass

        # Filter by type
        kg search -q "tech companies" --entity-type Organization \\
            --neo4j-uri bolt://localhost:7687 --password pass

        # Keyword search
        kg search -q "machine learning" --method keyword \\
            --neo4j-uri bolt://localhost:7687 --password pass
    """
    try:
        from semantic_search import SearchConfig, SemanticSearch

        console.print(f"[bold blue]Searching for:[/bold blue] {query}")

        # Configure search
        config = SearchConfig(
            neo4j_uri=neo4j_uri,
            auth=(username, password),
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        )

        search_engine = SemanticSearch(config)

        # Build index if needed
        with console.status("[yellow]Preparing search index...[/yellow]"):
            search_engine.build_faiss_index(entity_type=entity_type)

        # Perform search
        with console.status(f"[yellow]Searching with {method} method...[/yellow]"):
            if method == "vector":
                results = search_engine.vector_search(query, top_k, entity_type)
            elif method == "keyword":
                results = search_engine.keyword_search(query, top_k, entity_type)
            else:  # hybrid
                results = search_engine.hybrid_search(query, top_k, entity_type)

        # Display results
        if not results:
            console.print("[yellow]No results found[/yellow]")
        else:
            table = Table(title=f"Search Results (Top {len(results)})", box=box.ROUNDED)
            table.add_column("Rank", style="dim", width=6)
            table.add_column("Entity", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Score", style="green", justify="right")

            for i, result in enumerate(results, 1):
                table.add_row(
                    str(i),
                    result.get("text", "N/A"),
                    result.get("type", "N/A"),
                    f"{result.get('score', 0):.3f}",
                )

            console.print(table)

        search_engine.close()

    except Exception as e:
        raise CLIError(f"Search failed: {e}")


@cli.command()
@click.option(
    "--question",
    "-q",
    required=True,
    help="Question to answer",
)
@click.option(
    "--neo4j-uri",
    required=True,
    help="Neo4j database URI",
)
@click.option("--username", default="neo4j", help="Neo4j username")
@click.option("--password", required=True, help="Neo4j password")
@click.option(
    "--framework",
    type=click.Choice(["langchain", "llamaindex"]),
    default="langchain",
    help="RAG framework to use (default: langchain)",
)
@click.option(
    "--llm-model",
    default="gpt-4",
    help="LLM model for answer generation (default: gpt-4)",
)
@click.option(
    "--context-window",
    default=3,
    type=int,
    help="Context window size (default: 3)",
)
@click.pass_context
def rag(
    ctx, question, neo4j_uri, username, password, framework, llm_model, context_window
):
    """
    Answer questions using RAG with knowledge graph context.

    This command uses Retrieval-Augmented Generation to answer questions
    by retrieving relevant context from the knowledge graph.

    \b
    Examples:
        # Answer with LangChain
        kg rag -q "What is the relationship between AI and robotics?" \\
            --neo4j-uri bolt://localhost:7687 --password pass

        # Use LlamaIndex
        kg rag -q "Who are the founders of OpenAI?" --framework llamaindex \\
            --neo4j-uri bolt://localhost:7687 --password pass

        # Custom model
        kg rag -q "Explain neural networks" --llm-model gpt-3.5-turbo \\
            --neo4j-uri bolt://localhost:7687 --password pass
    """
    try:
        from rag_integrator import RAGConfig, RAGIntegrator

        console.print(f"[bold blue]Question:[/bold blue] {question}")

        # Configure RAG
        config = RAGConfig(
            neo4j_uri=neo4j_uri,
            auth=(username, password),
            llm_model=llm_model,
            framework=framework,
        )

        rag_engine = RAGIntegrator(config)

        # Generate answer
        with console.status("[yellow]Generating answer...[/yellow]"):
            result = rag_engine.answer_question(question, context_window)

        # Display answer
        answer_panel = Panel(
            result.get("answer", "No answer generated"),
            title="[bold green]Answer[/bold green]",
            box=box.ROUNDED,
            border_style="green",
        )
        console.print(answer_panel)

        # Display context
        if result.get("context"):
            console.print("\n[bold]Retrieved Context:[/bold]")
            for i, ctx in enumerate(result["context"][:3], 1):
                console.print(f"{i}. {ctx}")

        # Display metadata
        if result.get("metadata"):
            conf = result['metadata'].get('confidence', 'N/A')
            console.print(f"\n[dim]Confidence: {conf}[/dim]")

        rag_engine.close()

    except Exception as e:
        raise CLIError(f"RAG query failed: {e}")


@cli.command()
@click.option(
    "--neo4j-uri",
    required=True,
    help="Neo4j database URI",
)
@click.option("--username", default="neo4j", help="Neo4j username")
@click.option("--password", required=True, help="Neo4j password")
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(),
    help="Output file (HTML, PNG, or JSON)",
)
@click.option(
    "--layout",
    type=click.Choice(["spring", "circular", "kamada_kawai", "random"]),
    default="spring",
    help="Graph layout algorithm (default: spring)",
)
@click.option(
    "--node-type",
    help="Filter by node type",
)
@click.option(
    "--max-nodes",
    default=100,
    type=int,
    help="Maximum nodes to visualize (default: 100)",
)
@click.pass_context
def visualize(ctx, neo4j_uri, username, password, output, layout, node_type, max_nodes):
    """
    Generate graph visualizations.

    This command creates visual representations of the knowledge graph
    in various formats (HTML, PNG, JSON).

    \b
    Examples:
        # Generate HTML visualization
        kg visualize --neo4j-uri bolt://localhost:7687 --password pass \\
            -o graph.html

        # Filter by node type
        kg visualize --neo4j-uri bolt://localhost:7687 --password pass \\
            -o graph.html --node-type Person

        # Different layout
        kg visualize --neo4j-uri bolt://localhost:7687 --password pass \\
            -o graph.html --layout circular
    """
    try:
        from graph_visualizer import GraphVisualizer, VisualizerConfig

        console.print("[bold blue]Generating visualization...[/bold blue]")

        # Configure visualizer
        config = VisualizerConfig(
            neo4j_uri=neo4j_uri,
            auth=(username, password),
        )

        visualizer = GraphVisualizer(config)

        # Generate visualization
        with console.status("[yellow]Creating visualization...[/yellow]"):
            visualizer.create_visualization(
                output_path=output,
                layout=layout,
                node_type=node_type,
                max_nodes=max_nodes,
            )

        console.print(f"[green]✓[/green] Visualization saved to: {output}")

        visualizer.close()

    except Exception as e:
        raise CLIError(f"Visualization failed: {e}")


@cli.command()
@click.option(
    "--type",
    "analysis_type",
    type=click.Choice(
        [
            "pagerank",
            "betweenness",
            "closeness",
            "communities",
            "metrics",
            "bridges",
        ]
    ),
    required=True,
    help="Type of analysis to perform",
)
@click.option(
    "--neo4j-uri",
    required=True,
    help="Neo4j database URI",
)
@click.option("--username", default="neo4j", help="Neo4j username")
@click.option("--password", required=True, help="Neo4j password")
@click.option(
    "--node-type",
    help="Filter by node type",
)
@click.option(
    "--top-k",
    default=10,
    type=int,
    help="Number of top results (default: 10)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save results to JSON file",
)
@click.pass_context
def analyze(
    ctx, analysis_type, neo4j_uri, username, password, node_type, top_k, output
):
    """
    Run graph analysis algorithms.

    This command performs various graph analytics including centrality
    measures, community detection, and graph metrics.

    \b
    Examples:
        # PageRank analysis
        kg analyze --type pagerank --neo4j-uri bolt://localhost:7687 \\
            --password pass --top-k 20

        # Community detection
        kg analyze --type communities --neo4j-uri bolt://localhost:7687 \\
            --password pass

        # Graph metrics
        kg analyze --type metrics --neo4j-uri bolt://localhost:7687 \\
            --password pass

        # Bridge nodes
        kg analyze --type bridges --neo4j-uri bolt://localhost:7687 \\
            --password pass
    """
    try:
        from graph_analyzer import AnalyzerConfig, GraphAnalyzer

        console.print(f"[bold blue]Running {analysis_type} analysis...[/bold blue]")

        # Configure analyzer
        config = AnalyzerConfig(
            neo4j_uri=neo4j_uri,
            auth=(username, password),
        )

        analyzer = GraphAnalyzer(config)

        # Run analysis
        with console.status(f"[yellow]Analyzing graph...[/yellow]"):
            if analysis_type == "pagerank":
                results = analyzer.calculate_pagerank(top_k, node_type)
                title = f"PageRank (Top {top_k})"

            elif analysis_type == "betweenness":
                results = analyzer.calculate_betweenness_centrality(top_k, node_type)
                title = f"Betweenness Centrality (Top {top_k})"

            elif analysis_type == "closeness":
                results = analyzer.calculate_closeness_centrality(top_k, node_type)
                title = f"Closeness Centrality (Top {top_k})"

            elif analysis_type == "communities":
                results = analyzer.detect_communities(node_type=node_type)
                title = "Community Detection"

            elif analysis_type == "metrics":
                results = analyzer.calculate_graph_metrics(node_type)
                title = "Graph Metrics"

            elif analysis_type == "bridges":
                results = analyzer.identify_bridge_nodes(node_type)
                title = "Bridge Nodes"

        # Display results
        if analysis_type in ["pagerank", "betweenness", "closeness"]:
            table = Table(title=title, box=box.ROUNDED)
            table.add_column("Rank", style="dim", width=6)
            table.add_column("Node ID", style="cyan")
            table.add_column("Score", style="green", justify="right")

            for i, (node_id, score) in enumerate(results.items(), 1):
                table.add_row(str(i), node_id, f"{score:.6f}")

            console.print(table)

        elif analysis_type == "communities":
            table = Table(title=title, box=box.ROUNDED)
            table.add_column("Community ID", style="cyan")
            table.add_column("Size", style="green", justify="right")
            table.add_column("Sample Nodes", style="yellow")

            for comm_id, nodes in results.communities.items():
                sample = ", ".join(nodes[:3])
                if len(nodes) > 3:
                    sample += "..."
                table.add_row(str(comm_id), str(len(nodes)), sample)

            console.print(table)
            console.print(f"\n[dim]Modularity: {results.modularity:.3f}[/dim]")

        elif analysis_type == "metrics":
            table = Table(title=title, box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            metrics_dict = results.dict()
            for key, value in metrics_dict.items():
                if value is not None:
                    if isinstance(value, float):
                        value = f"{value:.4f}"
                    table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)

        elif analysis_type == "bridges":
            table = Table(title=title, box=box.ROUNDED)
            table.add_column("Node ID", style="cyan")
            table.add_column("Community", style="magenta")
            table.add_column("Connections", style="green", justify="right")
            table.add_column("Degree", style="yellow", justify="right")

            for bridge in results[:top_k]:
                table.add_row(
                    bridge["node_id"],
                    str(bridge["community"]),
                    str(bridge["num_connections"]),
                    str(bridge["degree"]),
                )

            console.print(table)

        # Save if output specified
        if output:
            with open(output, "w") as f:
                if hasattr(results, "dict"):
                    json.dump(results.dict(), f, indent=2)
                else:
                    json.dump(results, f, indent=2)
            console.print(f"\n[green]✓[/green] Results saved to: {output}")

        analyzer.close()

    except Exception as e:
        raise CLIError(f"Analysis failed: {e}")


@cli.command()
@click.option(
    "--neo4j-uri",
    required=True,
    help="Neo4j database URI",
)
@click.option("--username", default="neo4j", help="Neo4j username")
@click.option("--password", required=True, help="Neo4j password")
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(),
    help="Output file (JSON, CSV, or GraphML)",
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "graphml"]),
    default="json",
    help="Export format (default: json)",
)
@click.option(
    "--node-type",
    help="Filter by node type",
)
@click.pass_context
def export(ctx, neo4j_uri, username, password, output, format, node_type):
    """
    Export graph data to various formats.

    This command exports the knowledge graph to JSON, CSV, or GraphML
    format for use in other tools.

    \b
    Examples:
        # Export to JSON
        kg export --neo4j-uri bolt://localhost:7687 --password pass \\
            -o graph.json

        # Export to GraphML
        kg export --neo4j-uri bolt://localhost:7687 --password pass \\
            -o graph.graphml --format graphml

        # Filter by node type
        kg export --neo4j-uri bolt://localhost:7687 --password pass \\
            -o persons.json --node-type Person
    """
    try:
        from graph_builder import BuilderConfig, GraphBuilder

        console.print(f"[bold blue]Exporting graph to {format.upper()}...[/bold blue]")

        # Configure builder
        config = BuilderConfig(
            neo4j_uri=neo4j_uri,
            auth=(username, password),
        )

        builder = GraphBuilder(config)

        # Export
        with console.status("[yellow]Exporting data...[/yellow]"):
            builder.export_graph(output, format, node_type)

        console.print(f"[green]✓[/green] Graph exported to: {output}")

        builder.close()

    except Exception as e:
        raise CLIError(f"Export failed: {e}")


@cli.command()
@click.option(
    "--neo4j-uri",
    required=True,
    help="Neo4j database URI",
)
@click.option("--username", default="neo4j", help="Neo4j username")
@click.option("--password", required=True, help="Neo4j password")
@click.pass_context
def info(ctx, neo4j_uri, username, password):
    """
    Display knowledge graph information and statistics.

    \b
    Examples:
        kg info --neo4j-uri bolt://localhost:7687 --password pass
    """
    try:
        from graph_query import GraphQueryEngine, QueryConfig

        console.print("[bold blue]Retrieving graph information...[/bold blue]")

        # Configure engine
        config = QueryConfig(
            neo4j_uri=neo4j_uri,
            auth=(username, password),
            enable_nl_translation=False,
        )

        engine = GraphQueryEngine(config)

        # Get schema
        with console.status("[yellow]Loading schema...[/yellow]"):
            schema = engine.get_schema()

        # Display schema
        console.print("\n[bold]Node Labels:[/bold]")
        for label in schema["node_labels"]:
            console.print(f"  • {label}")

        console.print("\n[bold]Relationship Types:[/bold]")
        for rel_type in schema["relationship_types"]:
            console.print(f"  • {rel_type}")

        console.print("\n[bold]Property Keys:[/bold]")
        for prop in schema["property_keys"][:20]:  # Show first 20
            console.print(f"  • {prop}")

        # Summary table
        table = Table(title="Graph Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green", justify="right")

        table.add_row("Node Labels", str(schema["node_label_count"]))
        table.add_row("Relationship Types", str(schema["relationship_type_count"]))
        table.add_row("Property Keys", str(len(schema["property_keys"])))

        console.print("\n", table)

        engine.close()

    except Exception as e:
        raise CLIError(f"Info retrieval failed: {e}")


def main():
    """Main entry point for CLI."""
    try:
        cli(obj={})
    except Exception as e:
        console.print(f"[red bold]Fatal error:[/red bold] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
