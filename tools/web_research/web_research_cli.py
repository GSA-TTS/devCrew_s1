#!/usr/bin/env python3
"""
Web Research & Content Extraction Platform CLI.

Complete command-line interface for web scraping, content extraction,
knowledge indexing, semantic search, validation, and cache management.
Supports batch operations, multiple output formats, and comprehensive
configuration management.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.tree import Tree

from . import (
    BrowserAutomation,
    CacheConfig,
    CacheManager,
    ContentExtractor,
    ContentValidator,
    KnowledgeIndexer,
    RenderConfig,
    ScrapingConfig,
    WebScraper,
)

# Initialize Rich console for formatted output
console = Console()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
    '"message": "%(message)s"}',
)
logger = logging.getLogger(__name__)


class CLIConfig:
    """Configuration manager for CLI operations."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _get_default_config_path(self) -> Path:
        """Get default configuration file path.

        Returns:
            Path to default config directory
        """
        config_dir = Path.home() / ".devcrew-web"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yaml"

    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Load from file
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = self._get_default_config()
            self.save()

        # Override with environment variables
        env_overrides = {
            "DEVCREW_WEB_CACHE_DIR": ("cache", "cache_dir"),
            "DEVCREW_WEB_OUTPUT_DIR": ("output", "output_dir"),
            "DEVCREW_WEB_VECTOR_DB_PATH": ("indexer", "db_path"),
            "DEVCREW_WEB_LOG_LEVEL": ("logging", "level"),
            "DEVCREW_WEB_USER_AGENT": ("scraper", "user_agent"),
            "DEVCREW_WEB_TIMEOUT": ("scraper", "timeout"),
            "DEVCREW_WEB_MAX_RETRIES": ("scraper", "max_retries"),
        }

        for env_var, (section, key) in env_overrides.items():
            value = os.getenv(env_var)
            if value:
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][key] = value

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration.

        Returns:
            Default configuration dictionary
        """
        config_dir = Path.home() / ".devcrew-web"
        return {
            "cache": {
                "cache_dir": str(config_dir / "cache"),
                "ttl": 86400,
                "max_size_mb": 1024,
            },
            "output": {"output_dir": str(config_dir / "output")},
            "scraper": {
                "user_agent": "devCrew-WebResearch/1.0",
                "timeout": 30,
                "max_retries": 3,
                "delay": 1.0,
                "respect_robots_txt": True,
            },
            "extractor": {"min_text_length": 100, "clean_html": True},
            "indexer": {
                "db_path": str(config_dir / "vector_db"),
                "collection_name": "web_content",
                "embedding_model": "all-MiniLM-L6-v2",
            },
            "validator": {
                "min_quality_score": 0.7,
                "check_duplicates": True,
                "check_readability": True,
            },
            "logging": {"level": "INFO", "format": "json"},
        }

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def save(self) -> None:
        """Save configuration to file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False)


def format_output(data: Any, output_format: str, pretty: bool = True) -> str:
    """Format output data based on requested format.

    Args:
        data: Data to format
        output_format: Output format (json, yaml, text, markdown)
        pretty: Whether to pretty-print

    Returns:
        Formatted output string
    """
    if output_format == "json":
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
    elif output_format == "yaml":
        return yaml.dump(data, default_flow_style=False)
    elif output_format == "markdown":
        return _format_markdown(data)
    else:  # text
        return _format_text(data)


def _format_markdown(data: Any) -> str:
    """Format data as markdown.

    Args:
        data: Data to format

    Returns:
        Markdown formatted string
    """
    if isinstance(data, dict):
        lines = ["# Web Research Results\n"]
        for key, value in data.items():
            lines.append(f"## {key.replace('_', ' ').title()}\n")
            if isinstance(value, (list, dict)):
                lines.append(f"```json\n{json.dumps(value, indent=2)}\n```\n")
            else:
                lines.append(f"{value}\n")
        return "\n".join(lines)
    return str(data)


def _format_text(data: Any) -> str:
    """Format data as plain text.

    Args:
        data: Data to format

    Returns:
        Plain text formatted string
    """
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    return str(data)


def save_output(
    data: Any,
    output_path: Optional[Path],
    output_format: str,
    console_output: bool = True,
) -> None:
    """Save output to file and/or console.

    Args:
        data: Data to output
        output_path: Optional path to save file
        output_format: Output format
        console_output: Whether to output to console
    """
    formatted = format_output(data, output_format)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted)
        if console_output:
            console.print(f"[green]Output saved to: {output_path}[/green]")

    if console_output:
        console.print(formatted)


# CLI Context object
pass_config = click.make_pass_decorator(CLIConfig, ensure=True)


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Configuration file path",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", "-d", is_flag=True, help="Enable debug mode")
@click.version_option(version="1.0.0", prog_name="web-research")
@click.pass_context
def cli(
    ctx: click.Context,
    config: Optional[Path],
    verbose: bool,
    debug: bool,
) -> None:
    """Web Research & Content Extraction Platform CLI.

    Multi-functional web research platform for scraping, extraction,
    indexing, and validation of web content.
    """
    # Setup logging level
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Initialize configuration
    ctx.obj = CLIConfig(config)


# ============================================================================
# SCRAPE COMMAND GROUP
# ============================================================================


@cli.group()
def scrape() -> None:
    """Web scraping commands for content retrieval."""
    pass


@scrape.command(name="url")
@click.argument("url")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text", "markdown"]),
    default="json",
    help="Output format",
)
@click.option(
    "--render",
    is_flag=True,
    help="Use browser rendering for JavaScript sites",
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Request timeout in seconds",
)
@pass_config
def scrape_url(
    config: CLIConfig,
    url: str,
    output: Optional[Path],
    format: str,
    render: bool,
    timeout: int,
) -> None:
    """Scrape content from a single URL.

    Example:
        web-research scrape url https://example.com -o output.json
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Scraping {url}...", total=1)

            if render:
                # Use browser automation for JavaScript rendering
                browser_config = RenderConfig(
                    headless=True,
                    timeout=timeout * 1000,  # Convert to milliseconds
                )
                browser = BrowserAutomation(browser_config)
                result = asyncio.run(browser.render_page(url))
                scraped_data = {
                    "url": url,
                    "html": result.html,
                    "title": result.title,
                    "screenshot": result.screenshot,
                    "console_logs": result.console_logs,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                # Use standard HTTP scraping
                scraping_config = ScrapingConfig(
                    user_agent=config.get("scraper", "user_agent"),
                    timeout=timeout,
                    max_retries=config.get("scraper", "max_retries", 3),
                    delay=config.get("scraper", "delay", 1.0),
                    respect_robots_txt=config.get(
                        "scraper", "respect_robots_txt", True
                    ),
                )
                scraper = WebScraper(scraping_config)
                result = scraper.scrape(url)
                scraped_data = {
                    "url": result.url,
                    "html": result.html,
                    "status_code": result.status_code,
                    "headers": dict(result.headers),
                    "encoding": result.encoding,
                    "timestamp": result.timestamp.isoformat(),
                }

            progress.update(task, advance=1)

        save_output(scraped_data, output, format)
        console.print("[green]✓[/green] Successfully scraped URL")

    except Exception as e:
        console.print(f"[red]✗[/red] Error scraping URL: {e}")
        logger.exception("Scraping error")
        sys.exit(1)


@scrape.command(name="batch")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory for scraped content",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
@click.option(
    "--render",
    is_flag=True,
    help="Use browser rendering for JavaScript sites",
)
@click.option(
    "--parallel",
    type=int,
    default=5,
    help="Number of parallel requests",
)
@pass_config
def scrape_batch(
    config: CLIConfig,
    file: Path,
    output_dir: Optional[Path],
    format: str,
    render: bool,
    parallel: int,
) -> None:
    """Scrape multiple URLs from a file (one URL per line).

    Example:
        web-research scrape batch urls.txt -o output_dir/
    """
    try:
        # Read URLs from file
        with open(file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        if not urls:
            console.print("[yellow]No URLs found in file[/yellow]")
            return

        # Setup output directory
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path(config.get("output", "output_dir"))
            output_dir.mkdir(parents=True, exist_ok=True)

        results: List[Dict[str, Any]] = []
        failed_urls: List[Tuple[str, str]] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Scraping {len(urls)} URLs...", total=len(urls))

            scraping_config = ScrapingConfig(
                user_agent=config.get("scraper", "user_agent"),
                timeout=config.get("scraper", "timeout", 30),
                max_retries=config.get("scraper", "max_retries", 3),
                delay=config.get("scraper", "delay", 1.0),
            )
            scraper = WebScraper(scraping_config)

            for idx, url in enumerate(urls):
                try:
                    if render:
                        browser_config = RenderConfig(headless=True)
                        browser = BrowserAutomation(browser_config)
                        result = asyncio.run(browser.render_page(url))
                        scraped_data = {
                            "url": url,
                            "html": result.html,
                            "title": result.title,
                            "timestamp": datetime.now().isoformat(),
                        }
                    else:
                        result = scraper.scrape(url)
                        scraped_data = {
                            "url": result.url,
                            "html": result.html,
                            "status_code": result.status_code,
                            "timestamp": result.timestamp.isoformat(),
                        }

                    results.append(scraped_data)

                    # Save individual result
                    filename = f"scraped_{idx:04d}.{format}"
                    output_path = output_dir / filename
                    with open(output_path, "w", encoding="utf-8") as f:
                        if format == "json":
                            json.dump(scraped_data, f, indent=2)
                        else:
                            yaml.dump(scraped_data, f)

                except Exception as e:
                    failed_urls.append((url, str(e)))
                    logger.error(f"Failed to scrape {url}: {e}")

                progress.update(task, advance=1)

        # Display summary
        table = Table(title="Batch Scraping Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total URLs", str(len(urls)))
        table.add_row("Successful", str(len(results)))
        table.add_row("Failed", str(len(failed_urls)))
        table.add_row("Output Directory", str(output_dir))
        console.print(table)

        if failed_urls:
            console.print("\n[yellow]Failed URLs:[/yellow]")
            for url, error in failed_urls[:10]:
                console.print(f"  • {url}: {error}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error in batch scraping: {e}")
        logger.exception("Batch scraping error")
        sys.exit(1)


@scrape.command(name="sitemap")
@click.argument("url")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory for scraped content",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
@click.option(
    "--max-pages",
    type=int,
    default=100,
    help="Maximum number of pages to scrape",
)
@pass_config
def scrape_sitemap(
    config: CLIConfig,
    url: str,
    output_dir: Optional[Path],
    format: str,
    max_pages: int,
) -> None:
    """Scrape pages from a sitemap.xml URL.

    Example:
        web-research scrape sitemap https://example.com/sitemap.xml
    """
    try:
        console.print(f"[cyan]Parsing sitemap: {url}[/cyan]")

        scraping_config = ScrapingConfig(
            user_agent=config.get("scraper", "user_agent"),
            timeout=config.get("scraper", "timeout", 30),
        )
        scraper = WebScraper(scraping_config)

        # Fetch sitemap
        sitemap_content = scraper.scrape(url)
        from xml.etree import ElementTree as ET

        root = ET.fromstring(sitemap_content.html)

        # Extract URLs from sitemap
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [loc.text for loc in root.findall(".//sm:loc", namespace) if loc.text][
            :max_pages
        ]

        console.print(f"[green]Found {len(urls)} URLs in sitemap[/green]")

        # Setup output directory
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path(config.get("output", "output_dir")) / "sitemap"
            output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Scraping {len(urls)} pages...", total=len(urls))

            for idx, page_url in enumerate(urls):
                try:
                    result = scraper.scrape(page_url)
                    scraped_data = {
                        "url": result.url,
                        "html": result.html,
                        "status_code": result.status_code,
                        "timestamp": result.timestamp.isoformat(),
                    }
                    results.append(scraped_data)

                    # Save individual result
                    filename = f"page_{idx:04d}.{format}"
                    output_path = output_dir / filename
                    with open(output_path, "w", encoding="utf-8") as f:
                        if format == "json":
                            json.dump(scraped_data, f, indent=2)
                        else:
                            yaml.dump(scraped_data, f)

                except Exception as e:
                    logger.error(f"Failed to scrape {page_url}: {e}")

                progress.update(task, advance=1)

        console.print(f"[green]✓[/green] Successfully scraped {len(results)} pages")
        console.print(f"[cyan]Output directory: {output_dir}[/cyan]")

    except Exception as e:
        console.print(f"[red]✗[/red] Error scraping sitemap: {e}")
        logger.exception("Sitemap scraping error")
        sys.exit(1)


# ============================================================================
# EXTRACT COMMAND GROUP
# ============================================================================


@cli.group()
def extract() -> None:
    """Content extraction commands for article parsing."""
    pass


@extract.command(name="url")
@click.argument("url")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text", "markdown"]),
    default="json",
    help="Output format",
)
@pass_config
def extract_url(
    config: CLIConfig, url: str, output: Optional[Path], format: str
) -> None:
    """Extract article content from a URL.

    Example:
        web-research extract url https://example.com/article
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Extracting content from {url}...", total=1)

            # First scrape the URL
            scraping_config = ScrapingConfig(
                user_agent=config.get("scraper", "user_agent"),
                timeout=config.get("scraper", "timeout", 30),
            )
            scraper = WebScraper(scraping_config)
            scraped = scraper.scrape(url)

            # Extract article content
            extractor = ContentExtractor()
            article = extractor.extract(scraped.html, url)

            extracted_data = {
                "url": url,
                "title": article.title,
                "author": article.author,
                "publish_date": (
                    article.publish_date.isoformat() if article.publish_date else None
                ),
                "text": article.text,
                "summary": article.summary,
                "language": article.language,
                "tags": article.tags,
                "images": article.images,
                "videos": article.videos,
                "word_count": len(article.text.split()) if article.text else 0,
            }

            progress.update(task, advance=1)

        save_output(extracted_data, output, format)
        console.print("[green]✓[/green] Successfully extracted article content")

    except Exception as e:
        console.print(f"[red]✗[/red] Error extracting content: {e}")
        logger.exception("Extraction error")
        sys.exit(1)


@extract.command(name="file")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text", "markdown"]),
    default="json",
    help="Output format",
)
@click.option("--url", help="Original URL for the HTML file")
@pass_config
def extract_file(
    config: CLIConfig,
    file: Path,
    output: Optional[Path],
    format: str,
    url: Optional[str],
) -> None:
    """Extract article content from a saved HTML file.

    Example:
        web-research extract file article.html --url https://example.com
    """
    try:
        with open(file, "r", encoding="utf-8") as f:
            html = f.read()

        extractor = ContentExtractor()
        article = extractor.extract(html, url or str(file))

        extracted_data = {
            "source": str(file),
            "url": url,
            "title": article.title,
            "author": article.author,
            "publish_date": (
                article.publish_date.isoformat() if article.publish_date else None
            ),
            "text": article.text,
            "summary": article.summary,
            "language": article.language,
            "tags": article.tags,
            "word_count": len(article.text.split()) if article.text else 0,
        }

        save_output(extracted_data, output, format)
        console.print("[green]✓[/green] Successfully extracted article content")

    except Exception as e:
        console.print(f"[red]✗[/red] Error extracting content: {e}")
        logger.exception("Extraction error")
        sys.exit(1)


@extract.command(name="batch")
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
@click.option("--pattern", default="*.html", help="File pattern to match")
@pass_config
def extract_batch(
    config: CLIConfig,
    directory: Path,
    output_dir: Optional[Path],
    format: str,
    pattern: str,
) -> None:
    """Batch extract articles from a directory of HTML files.

    Example:
        web-research extract batch html_files/ -o extracted/
    """
    try:
        # Find HTML files
        html_files = list(directory.glob(pattern))

        if not html_files:
            console.print(f"[yellow]No files matching {pattern} found[/yellow]")
            return

        # Setup output directory
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path(config.get("output", "output_dir")) / "extracted"
            output_dir.mkdir(parents=True, exist_ok=True)

        extractor = ContentExtractor()
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Extracting {len(html_files)} files...", total=len(html_files)
            )

            for idx, html_file in enumerate(html_files):
                try:
                    with open(html_file, "r", encoding="utf-8") as f:
                        html = f.read()

                    article = extractor.extract(html, str(html_file))

                    extracted_data = {
                        "source": str(html_file),
                        "title": article.title,
                        "author": article.author,
                        "text": article.text,
                        "summary": article.summary,
                        "word_count": (
                            len(article.text.split()) if article.text else 0
                        ),
                    }
                    results.append(extracted_data)

                    # Save individual result
                    filename = f"extracted_{idx:04d}.{format}"
                    output_path = output_dir / filename
                    with open(output_path, "w", encoding="utf-8") as f:
                        if format == "json":
                            json.dump(extracted_data, f, indent=2)
                        else:
                            yaml.dump(extracted_data, f)

                except Exception as e:
                    logger.error(f"Failed to extract {html_file}: {e}")

                progress.update(task, advance=1)

        console.print(
            f"[green]✓[/green] Successfully extracted {len(results)} articles"
        )
        console.print(f"[cyan]Output directory: {output_dir}[/cyan]")

    except Exception as e:
        console.print(f"[red]✗[/red] Error in batch extraction: {e}")
        logger.exception("Batch extraction error")
        sys.exit(1)


# ============================================================================
# INDEX COMMAND GROUP
# ============================================================================


@cli.group()
def index() -> None:
    """Vector database indexing commands for semantic search."""
    pass


@index.command(name="add")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--collection",
    "-c",
    default="web_content",
    help="Collection name in vector DB",
)
@click.option(
    "--metadata",
    "-m",
    type=click.Path(exists=True, path_type=Path),
    help="JSON file with metadata",
)
@pass_config
def index_add(
    config: CLIConfig,
    source: Path,
    collection: str,
    metadata: Optional[Path],
) -> None:
    """Add content to vector database index.

    Example:
        web-research index add article.json -c tech_articles
    """
    try:
        # Load source data
        with open(source, "r", encoding="utf-8") as f:
            if source.suffix == ".json":
                data = json.load(f)
            elif source.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            else:
                console.print("[red]Unsupported file format[/red]")
                sys.exit(1)

        # Load metadata if provided
        meta = {}
        if metadata:
            with open(metadata, "r", encoding="utf-8") as f:
                meta = json.load(f)

        # Initialize indexer
        db_path = Path(config.get("indexer", "db_path"))
        indexer = KnowledgeIndexer(
            db_path=db_path,
            collection_name=collection,
            embedding_model=config.get(
                "indexer", "embedding_model", "all-MiniLM-L6-v2"
            ),
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            progress.add_task("Indexing content...", total=None)

            # Add to index
            doc_id = indexer.add_document(
                text=data.get("text", ""),
                metadata={
                    "title": data.get("title", ""),
                    "url": data.get("url", ""),
                    "author": data.get("author", ""),
                    "timestamp": datetime.now().isoformat(),
                    **meta,
                },
            )

        console.print(
            f"[green]✓[/green] Successfully indexed content with ID: {doc_id}"
        )

    except Exception as e:
        console.print(f"[red]✗[/red] Error indexing content: {e}")
        logger.exception("Indexing error")
        sys.exit(1)


@index.command(name="delete")
@click.argument("doc_id")
@click.option(
    "--collection",
    "-c",
    default="web_content",
    help="Collection name in vector DB",
)
@pass_config
def index_delete(config: CLIConfig, doc_id: str, collection: str) -> None:
    """Remove a document from the index.

    Example:
        web-research index delete doc_12345
    """
    try:
        db_path = Path(config.get("indexer", "db_path"))
        indexer = KnowledgeIndexer(db_path=db_path, collection_name=collection)

        indexer.delete_document(doc_id)
        console.print(f"[green]✓[/green] Successfully deleted document: {doc_id}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error deleting document: {e}")
        logger.exception("Delete error")
        sys.exit(1)


@index.command(name="list")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text"]),
    default="text",
    help="Output format",
)
@pass_config
def index_list(config: CLIConfig, format: str) -> None:
    """List all collections in the vector database.

    Example:
        web-research index list
    """
    try:
        db_path = Path(config.get("indexer", "db_path"))
        indexer = KnowledgeIndexer(db_path=db_path)

        collections = indexer.list_collections()

        if format == "text":
            table = Table(title="Vector DB Collections")
            table.add_column("Collection Name", style="cyan")
            table.add_column("Documents", style="green")
            for name, count in collections.items():
                table.add_row(name, str(count))
            console.print(table)
        else:
            save_output(collections, None, format)

    except Exception as e:
        console.print(f"[red]✗[/red] Error listing collections: {e}")
        logger.exception("List error")
        sys.exit(1)


@index.command(name="stats")
@click.argument("collection")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text"]),
    default="text",
    help="Output format",
)
@pass_config
def index_stats(config: CLIConfig, collection: str, format: str) -> None:
    """Show statistics for a collection.

    Example:
        web-research index stats web_content
    """
    try:
        db_path = Path(config.get("indexer", "db_path"))
        indexer = KnowledgeIndexer(db_path=db_path, collection_name=collection)

        stats = indexer.get_collection_stats()

        if format == "text":
            table = Table(title=f"Collection: {collection}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            for key, value in stats.items():
                table.add_row(key.replace("_", " ").title(), str(value))
            console.print(table)
        else:
            save_output(stats, None, format)

    except Exception as e:
        console.print(f"[red]✗[/red] Error retrieving stats: {e}")
        logger.exception("Stats error")
        sys.exit(1)


# ============================================================================
# SEARCH COMMAND GROUP
# ============================================================================


@cli.group()
def search() -> None:
    """Semantic search commands for content discovery."""
    pass


@search.command(name="query")
@click.argument("query")
@click.option(
    "--collection",
    "-c",
    default="web_content",
    help="Collection to search",
)
@click.option(
    "--limit",
    "-n",
    type=int,
    default=10,
    help="Maximum number of results",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text"]),
    default="text",
    help="Output format",
)
@pass_config
def search_query(
    config: CLIConfig,
    query: str,
    collection: str,
    limit: int,
    output: Optional[Path],
    format: str,
) -> None:
    """Perform semantic search with a text query.

    Example:
        web-research search query "machine learning best practices" -n 5
    """
    try:
        db_path = Path(config.get("indexer", "db_path"))
        indexer = KnowledgeIndexer(db_path=db_path, collection_name=collection)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            progress.add_task(f"Searching for: {query}...", total=None)

            results = indexer.search(query, top_k=limit)

        if format == "text":
            console.print(f"\n[cyan]Search Results for: {query}[/cyan]\n")
            for idx, result in enumerate(results, 1):
                panel = Panel(
                    f"[bold]{result.metadata.get('title', 'Untitled')}[/bold]\n"
                    f"Score: {result.score:.4f}\n"
                    f"URL: {result.metadata.get('url', 'N/A')}\n"
                    f"Preview: {result.text[:200]}...",
                    title=f"Result {idx}",
                    border_style="green",
                )
                console.print(panel)
        else:
            results_data = [
                {
                    "id": r.id,
                    "score": r.score,
                    "text": r.text,
                    "metadata": r.metadata,
                }
                for r in results
            ]
            save_output(results_data, output, format, console_output=False)

        console.print(f"\n[green]Found {len(results)} results[/green]")

    except Exception as e:
        console.print(f"[red]✗[/red] Error searching: {e}")
        logger.exception("Search error")
        sys.exit(1)


@search.command(name="similar")
@click.argument("url")
@click.option(
    "--collection",
    "-c",
    default="web_content",
    help="Collection to search",
)
@click.option(
    "--limit",
    "-n",
    type=int,
    default=10,
    help="Maximum number of results",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text"]),
    default="text",
    help="Output format",
)
@pass_config
def search_similar(
    config: CLIConfig,
    url: str,
    collection: str,
    limit: int,
    format: str,
) -> None:
    """Find content similar to a given URL.

    Example:
        web-research search similar https://example.com/article
    """
    try:
        # First scrape and extract the reference content
        scraping_config = ScrapingConfig(user_agent=config.get("scraper", "user_agent"))
        scraper = WebScraper(scraping_config)
        scraped = scraper.scrape(url)

        extractor = ContentExtractor()
        article = extractor.extract(scraped.html, url)

        # Search for similar content
        db_path = Path(config.get("indexer", "db_path"))
        indexer = KnowledgeIndexer(db_path=db_path, collection_name=collection)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            progress.add_task("Finding similar content...", total=None)

            results = indexer.search(article.text[:1000], top_k=limit)

        if format == "text":
            console.print(f"\n[cyan]Similar Content to: {url}[/cyan]\n")
            for idx, result in enumerate(results, 1):
                panel = Panel(
                    f"[bold]{result.metadata.get('title', 'Untitled')}[/bold]\n"
                    f"Similarity: {result.score:.4f}\n"
                    f"URL: {result.metadata.get('url', 'N/A')}\n",
                    title=f"Result {idx}",
                    border_style="green",
                )
                console.print(panel)
        else:
            results_data = [
                {
                    "id": r.id,
                    "score": r.score,
                    "metadata": r.metadata,
                }
                for r in results
            ]
            save_output(results_data, None, format)

        console.print(f"\n[green]Found {len(results)} similar items[/green]")

    except Exception as e:
        console.print(f"[red]✗[/red] Error finding similar content: {e}")
        logger.exception("Similarity search error")
        sys.exit(1)


# ============================================================================
# VALIDATE COMMAND GROUP
# ============================================================================


@cli.group()
def validate() -> None:
    """Content validation and quality assurance commands."""
    pass


@validate.command(name="url")
@click.argument("url")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text"]),
    default="text",
    help="Output format",
)
@pass_config
def validate_url(
    config: CLIConfig, url: str, output: Optional[Path], format: str
) -> None:
    """Validate content quality from a URL.

    Example:
        web-research validate url https://example.com/article
    """
    try:
        # Scrape and extract content
        scraping_config = ScrapingConfig(user_agent=config.get("scraper", "user_agent"))
        scraper = WebScraper(scraping_config)
        scraped = scraper.scrape(url)

        extractor = ContentExtractor()
        article = extractor.extract(scraped.html, url)

        # Validate content
        validator = ContentValidator()
        result = validator.validate(article)

        validation_data = {
            "url": url,
            "is_valid": result.is_valid,
            "quality_score": result.quality_score,
            "quality_rating": result.quality_rating.value,
            "checks": {
                "has_sufficient_content": result.has_sufficient_content,
                "is_readable": result.is_readable,
                "has_metadata": result.has_metadata,
                "is_duplicate": result.is_duplicate,
            },
            "issues": result.issues,
            "suggestions": result.suggestions,
            "metrics": result.metrics,
        }

        if format == "text":
            # Display as formatted panel
            status = "✓ VALID" if result.is_valid else "✗ INVALID"
            status_color = "green" if result.is_valid else "red"

            content = (
                f"[bold]Quality Score:[/bold] {result.quality_score:.2f}\n"
                f"[bold]Rating:[/bold] {result.quality_rating.value.upper()}\n\n"
            )

            if result.issues:
                content += "[bold red]Issues:[/bold red]\n"
                for issue in result.issues:
                    content += f"  • {issue}\n"
                content += "\n"

            if result.suggestions:
                content += "[bold yellow]Suggestions:[/bold yellow]\n"
                for suggestion in result.suggestions:
                    content += f"  • {suggestion}\n"

            panel = Panel(
                content,
                title=f"[{status_color}]{status}[/{status_color}] {url}",
                border_style=status_color,
            )
            console.print(panel)
        else:
            save_output(validation_data, output, format, console_output=False)

    except Exception as e:
        console.print(f"[red]✗[/red] Error validating URL: {e}")
        logger.exception("Validation error")
        sys.exit(1)


@validate.command(name="batch")
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output report file",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
@click.option("--pattern", default="*.json", help="File pattern to match")
@pass_config
def validate_batch(
    config: CLIConfig,
    directory: Path,
    output: Optional[Path],
    format: str,
    pattern: str,
) -> None:
    """Batch validate content from a directory of extracted articles.

    Example:
        web-research validate batch extracted/ -o validation_report.json
    """
    try:
        # Find files
        files = list(directory.glob(pattern))

        if not files:
            console.print(f"[yellow]No files matching {pattern} found[/yellow]")
            return

        validator = ContentValidator()
        results = []
        stats = {"valid": 0, "invalid": 0, "total": len(files)}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Validating {len(files)} files...", total=len(files)
            )

            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        if file_path.suffix == ".json":
                            data = json.load(f)
                        else:
                            data = yaml.safe_load(f)

                    # Create article object for validation
                    from . import ExtractedArticle

                    article = ExtractedArticle(
                        url=data.get("url", ""),
                        title=data.get("title", ""),
                        text=data.get("text", ""),
                        author=data.get("author"),
                        publish_date=None,
                        summary=data.get("summary", ""),
                        language=data.get("language", "en"),
                    )

                    result = validator.validate(article)

                    if result.is_valid:
                        stats["valid"] += 1
                    else:
                        stats["invalid"] += 1

                    results.append(
                        {
                            "file": str(file_path),
                            "url": data.get("url"),
                            "is_valid": result.is_valid,
                            "quality_score": result.quality_score,
                            "quality_rating": result.quality_rating.value,
                            "issues": result.issues,
                        }
                    )

                except Exception as e:
                    logger.error(f"Failed to validate {file_path}: {e}")

                progress.update(task, advance=1)

        # Save results
        report_data = {"stats": stats, "results": results}

        if output:
            with open(output, "w", encoding="utf-8") as f:
                if format == "json":
                    json.dump(report_data, f, indent=2)
                else:
                    yaml.dump(report_data, f)
            console.print(f"[green]Report saved to: {output}[/green]")

        # Display summary
        table = Table(title="Batch Validation Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total Files", str(stats["total"]))
        table.add_row("Valid", str(stats["valid"]))
        table.add_row("Invalid", str(stats["invalid"]))
        table.add_row(
            "Success Rate",
            (
                f"{(stats['valid'] / stats['total'] * 100):.1f}%"
                if stats["total"] > 0
                else "N/A"
            ),
        )
        console.print(table)

    except Exception as e:
        console.print(f"[red]✗[/red] Error in batch validation: {e}")
        logger.exception("Batch validation error")
        sys.exit(1)


@validate.command(name="report")
@click.argument("results", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output report file",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["html", "markdown", "text"]),
    default="html",
    help="Report format",
)
def validate_report(results: Path, output: Optional[Path], format: str) -> None:
    """Generate a validation report from batch results.

    Example:
        web-research validate report validation.json -o report.html
    """
    try:
        # Load validation results
        with open(results, "r", encoding="utf-8") as f:
            if results.suffix == ".json":
                data = json.load(f)
            else:
                data = yaml.safe_load(f)

        stats = data.get("stats", {})
        results_list = data.get("results", [])

        if format == "html":
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Content Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .stats {{ background: #f0f0f0; padding: 20px; margin: 20px 0; }}
        .valid {{ color: green; }}
        .invalid {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>Content Validation Report</h1>
    <div class="stats">
        <h2>Summary Statistics</h2>
        <p>Total Files: {stats.get('total', 0)}</p>
        <p class="valid">Valid: {stats.get('valid', 0)}</p>
        <p class="invalid">Invalid: {stats.get('invalid', 0)}</p>
    </div>
    <h2>Detailed Results</h2>
    <table>
        <tr>
            <th>File</th>
            <th>URL</th>
            <th>Status</th>
            <th>Quality Score</th>
            <th>Issues</th>
        </tr>
"""
            for result in results_list:
                status_class = "valid" if result["is_valid"] else "invalid"
                status_text = "✓ Valid" if result["is_valid"] else "✗ Invalid"
                issues = "<br>".join(result.get("issues", [])) or "None"
                html += f"""
        <tr>
            <td>{result['file']}</td>
            <td>{result.get('url', 'N/A')}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{result.get('quality_score', 0):.2f}</td>
            <td>{issues}</td>
        </tr>
"""
            html += """
    </table>
</body>
</html>
"""
            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(html)
                console.print(f"[green]HTML report saved to: {output}[/green]")
            else:
                console.print(html)

        elif format == "markdown":
            md = f"""# Content Validation Report

## Summary Statistics

- **Total Files**: {stats.get('total', 0)}
- **Valid**: {stats.get('valid', 0)}
- **Invalid**: {stats.get('invalid', 0)}

## Detailed Results

| File | URL | Status | Quality Score | Issues |
|------|-----|--------|---------------|--------|
"""
            for result in results_list:
                status = "✓ Valid" if result["is_valid"] else "✗ Invalid"
                issues = ", ".join(result.get("issues", [])) or "None"
                md += (
                    f"| {result['file']} | {result.get('url', 'N/A')} | "
                    f"{status} | {result.get('quality_score', 0):.2f} | "
                    f"{issues} |\n"
                )

            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(md)
                console.print(f"[green]Markdown report saved to: {output}[/green]")
            else:
                console.print(md)

        else:  # text
            text = "=" * 60 + "\n"
            text += "CONTENT VALIDATION REPORT\n"
            text += "=" * 60 + "\n\n"
            text += f"Total Files: {stats.get('total', 0)}\n"
            text += f"Valid: {stats.get('valid', 0)}\n"
            text += f"Invalid: {stats.get('invalid', 0)}\n\n"
            text += "-" * 60 + "\n"

            for result in results_list:
                status = "VALID" if result["is_valid"] else "INVALID"
                text += f"\nFile: {result['file']}\n"
                text += f"URL: {result.get('url', 'N/A')}\n"
                text += f"Status: {status}\n"
                text += f"Quality Score: {result.get('quality_score', 0):.2f}\n"
                if result.get("issues"):
                    text += "Issues:\n"
                    for issue in result["issues"]:
                        text += f"  - {issue}\n"
                text += "-" * 60 + "\n"

            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(text)
                console.print(f"[green]Text report saved to: {output}[/green]")
            else:
                console.print(text)

    except Exception as e:
        console.print(f"[red]✗[/red] Error generating report: {e}")
        logger.exception("Report generation error")
        sys.exit(1)


# ============================================================================
# CACHE COMMAND GROUP
# ============================================================================


@cli.group()
def cache() -> None:
    """Cache management commands for performance optimization."""
    pass


@cache.command(name="warm")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--parallel",
    type=int,
    default=5,
    help="Number of parallel requests",
)
@pass_config
def cache_warm(config: CLIConfig, file: Path, parallel: int) -> None:
    """Pre-populate cache with URLs from a file.

    Example:
        web-research cache warm urls.txt
    """
    try:
        # Read URLs from file
        with open(file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        if not urls:
            console.print("[yellow]No URLs found in file[/yellow]")
            return

        # Initialize cache and scraper
        cache_config = CacheConfig(
            cache_dir=Path(config.get("cache", "cache_dir")),
            ttl=config.get("cache", "ttl", 86400),
            max_size_mb=config.get("cache", "max_size_mb", 1024),
        )
        cache_manager = CacheManager(cache_config)

        scraping_config = ScrapingConfig(user_agent=config.get("scraper", "user_agent"))
        scraper = WebScraper(scraping_config)

        cached_count = 0
        failed_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Warming cache with {len(urls)} URLs...", total=len(urls)
            )

            for url in urls:
                try:
                    # Check if already cached
                    if cache_manager.get(url):
                        cached_count += 1
                        progress.update(task, advance=1)
                        continue

                    # Scrape and cache
                    result = scraper.scrape(url)
                    cache_manager.set(url, result.html)
                    cached_count += 1

                except Exception as e:
                    logger.error(f"Failed to cache {url}: {e}")
                    failed_count += 1

                progress.update(task, advance=1)

        console.print(f"[green]✓[/green] Successfully cached {cached_count} URLs")
        if failed_count > 0:
            console.print(f"[yellow]⚠[/yellow] Failed to cache {failed_count} URLs")

    except Exception as e:
        console.print(f"[red]✗[/red] Error warming cache: {e}")
        logger.exception("Cache warming error")
        sys.exit(1)


@cache.command(name="stats")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text"]),
    default="text",
    help="Output format",
)
@pass_config
def cache_stats(config: CLIConfig, format: str) -> None:
    """Show cache statistics.

    Example:
        web-research cache stats
    """
    try:
        cache_config = CacheConfig(
            cache_dir=Path(config.get("cache", "cache_dir")),
            ttl=config.get("cache", "ttl", 86400),
        )
        cache_manager = CacheManager(cache_config)

        stats = cache_manager.get_stats()

        stats_data = {
            "total_entries": stats.total_entries,
            "total_size_mb": stats.total_size_mb,
            "hit_rate": stats.hit_rate,
            "cache_dir": str(cache_config.cache_dir),
        }

        if format == "text":
            table = Table(title="Cache Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Total Entries", str(stats.total_entries))
            table.add_row("Total Size (MB)", f"{stats.total_size_mb:.2f}")
            table.add_row("Hit Rate", f"{stats.hit_rate:.2%}")
            table.add_row("Cache Directory", str(cache_config.cache_dir))
            console.print(table)
        else:
            save_output(stats_data, None, format)

    except Exception as e:
        console.print(f"[red]✗[/red] Error retrieving cache stats: {e}")
        logger.exception("Cache stats error")
        sys.exit(1)


@cache.command(name="clear")
@click.option("--force", "-f", is_flag=True, help="Force clear without confirmation")
@pass_config
def cache_clear(config: CLIConfig, force: bool) -> None:
    """Clear all cached content.

    Example:
        web-research cache clear --force
    """
    try:
        if not force:
            confirm = click.confirm("This will delete all cached content. Continue?")
            if not confirm:
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        cache_config = CacheConfig(cache_dir=Path(config.get("cache", "cache_dir")))
        cache_manager = CacheManager(cache_config)

        cache_manager.clear()
        console.print("[green]✓[/green] Cache cleared successfully")

    except Exception as e:
        console.print(f"[red]✗[/red] Error clearing cache: {e}")
        logger.exception("Cache clear error")
        sys.exit(1)


# ============================================================================
# CONFIG COMMAND GROUP
# ============================================================================


@cli.group()
def config() -> None:
    """Configuration management commands."""
    pass


@config.command(name="show")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml", "text"]),
    default="yaml",
    help="Output format",
)
@pass_config
def config_show(config: CLIConfig, format: str) -> None:
    """Display current configuration.

    Example:
        web-research config show
    """
    try:
        if format == "text":
            tree = Tree("[bold cyan]Configuration[/bold cyan]")
            for section, values in config.config.items():
                section_node = tree.add(f"[yellow]{section}[/yellow]")
                if isinstance(values, dict):
                    for key, value in values.items():
                        section_node.add(f"[green]{key}[/green]: {value}")
                else:
                    section_node.add(str(values))
            console.print(tree)
        else:
            save_output(config.config, None, format)

        console.print(f"\n[dim]Config file: {config.config_path}[/dim]")

    except Exception as e:
        console.print(f"[red]✗[/red] Error displaying config: {e}")
        logger.exception("Config show error")
        sys.exit(1)


@config.command(name="set")
@click.argument("key")
@click.argument("value")
@pass_config
def config_set(config: CLIConfig, key: str, value: str) -> None:
    """Set a configuration value.

    Example:
        web-research config set scraper.timeout 60
    """
    try:
        # Parse key as section.key
        if "." in key:
            section, config_key = key.split(".", 1)
        else:
            console.print("[red]Key must be in format: section.key[/red]")
            sys.exit(1)

        # Try to parse value as appropriate type
        try:
            if value.lower() in ["true", "false"]:
                parsed_value = value.lower() == "true"
            elif value.isdigit():
                parsed_value = int(value)
            elif value.replace(".", "", 1).isdigit():
                parsed_value = float(value)
            else:
                parsed_value = value
        except ValueError:
            parsed_value = value

        config.set(section, config_key, parsed_value)
        config.save()

        console.print(f"[green]✓[/green] Set {key} = {parsed_value}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error setting config: {e}")
        logger.exception("Config set error")
        sys.exit(1)


@config.command(name="validate")
@pass_config
def config_validate(config: CLIConfig) -> None:
    """Validate current configuration.

    Example:
        web-research config validate
    """
    try:
        issues = []

        # Validate cache directory
        cache_dir = Path(config.get("cache", "cache_dir", ""))
        if not cache_dir or not cache_dir.exists():
            issues.append(f"Cache directory does not exist: {cache_dir}")

        # Validate output directory
        output_dir = Path(config.get("output", "output_dir", ""))
        if not output_dir or not output_dir.exists():
            issues.append(f"Output directory does not exist: {output_dir}")

        # Validate numeric values
        timeout = config.get("scraper", "timeout")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            issues.append(f"Invalid timeout value: {timeout}")

        ttl = config.get("cache", "ttl")
        if not isinstance(ttl, (int, float)) or ttl < 0:
            issues.append(f"Invalid cache TTL value: {ttl}")

        if issues:
            console.print("[red]Configuration validation failed:[/red]")
            for issue in issues:
                console.print(f"  [yellow]⚠[/yellow] {issue}")
            sys.exit(1)
        else:
            console.print("[green]✓[/green] Configuration is valid")

    except Exception as e:
        console.print(f"[red]✗[/red] Error validating config: {e}")
        logger.exception("Config validation error")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli(obj=None)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        logger.exception("Unexpected error in CLI")
        sys.exit(1)


if __name__ == "__main__":
    main()
