"""
Web Scraper Module for devCrew_s1 Web Research Platform.

Production-ready web scraping implementation with Scrapy integration,
BeautifulSoup parsing, robots.txt compliance, rate limiting, and
comprehensive error handling.

Author: devCrew_s1
Version: 1.0.0
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator
from requests.adapters import HTTPAdapter
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    RequestException,
    Timeout,
    TooManyRedirects,
)
from urllib3.util.retry import Retry

# Configure module logger
logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """Base exception for scraping-related errors."""

    def __init__(self, message: str, url: Optional[str] = None) -> None:
        """Initialize scraping error with optional URL context."""
        self.url = url
        self.message = message
        super().__init__(self.message)


class RateLimitError(ScrapingError):
    """Exception raised when rate limit is exceeded."""

    pass


class RobotsDisallowedError(ScrapingError):
    """Exception raised when URL is disallowed by robots.txt."""

    pass


class RobotsRule(BaseModel):
    """Model representing robots.txt rules for a domain."""

    domain: str = Field(description="Domain the rules apply to")
    user_agent: str = Field(description="User agent the rules apply to")
    allowed_paths: List[str] = Field(
        default_factory=list, description="Explicitly allowed paths"
    )
    disallowed_paths: List[str] = Field(
        default_factory=list, description="Disallowed paths"
    )
    crawl_delay: Optional[float] = Field(
        default=None, description="Requested crawl delay in seconds"
    )
    sitemap_urls: List[str] = Field(
        default_factory=list,
        description="Sitemap URLs from robots.txt",
    )
    last_fetched: datetime = Field(
        default_factory=datetime.now,
        description="When robots.txt was last fetched",
    )

    class Config:
        """Pydantic model configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ScrapingConfig(BaseModel):
    """Configuration model for web scraping operations."""

    rate_limit: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Minimum delay between requests in seconds",
    )
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum number of retry attempts"
    )
    user_agent: str = Field(
        default=(
            "devCrew_s1-WebScraper/1.0 " "(+https://github.com/devCrew/web-research)"
        ),
        description="User agent string for HTTP requests",
    )
    respect_robots_txt: bool = Field(
        default=True, description="Whether to respect robots.txt rules"
    )
    max_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum depth for recursive scraping",
    )
    allowed_domains: List[str] = Field(
        default_factory=list,
        description="List of allowed domains for scraping",
    )
    timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Request timeout in seconds",
    )
    max_redirects: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of redirects to follow",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Whether to verify SSL certificates",
    )
    custom_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom HTTP headers",
    )
    cookies: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP cookies",
    )
    proxy: Optional[str] = Field(
        default=None,
        description="Proxy server URL",
    )
    backoff_factor: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Exponential backoff multiplier for retries",
    )

    @field_validator("user_agent")
    @classmethod
    def validate_user_agent(cls, v: str) -> str:
        """Validate user agent string is not empty."""
        if not v or not v.strip():
            raise ValueError("User agent cannot be empty")
        return v.strip()

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, v: List[str]) -> List[str]:
        """Validate and normalize domain names."""
        normalized = []
        for domain in v:
            domain = domain.lower().strip()
            if domain.startswith("http://") or domain.startswith("https://"):
                parsed = urlparse(domain)
                domain = parsed.netloc
            normalized.append(domain)
        return normalized


class ScrapedContent(BaseModel):
    """Model representing scraped content from a URL."""

    url: str = Field(description="The scraped URL")
    html: str = Field(description="Raw HTML content")
    status_code: int = Field(description="HTTP status code")
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP response headers",
    )
    links: List[str] = Field(
        default_factory=list,
        description="Extracted links from the page",
    )
    scraped_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of scraping",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    content_type: Optional[str] = Field(
        default=None,
        description="Content type from headers",
    )
    encoding: Optional[str] = Field(
        default=None,
        description="Character encoding detected",
    )
    response_time: float = Field(default=0.0, description="Response time in seconds")

    class Config:
        """Pydantic model configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class WebScraper:
    """
    Production-ready web scraper with comprehensive features.

    Features:
    - Robots.txt compliance with caching
    - Configurable rate limiting
    - Exponential backoff retry logic
    - Session management with connection pooling
    - Link extraction and normalization
    - Domain filtering
    - Custom headers and user agents
    - SSL verification control
    - Proxy support
    """

    def __init__(self, config: ScrapingConfig) -> None:
        """
        Initialize web scraper with configuration.

        Args:
            config: ScrapingConfig instance with scraping parameters
        """
        self.config = config
        self._session = self._create_session()
        self._robots_cache: Dict[str, RobotFileParser] = {}
        self._last_request_time: Dict[str, float] = {}
        self._request_count: int = 0

        logger.info(
            "Initialized WebScraper with rate_limit=%s, max_retries=%s",
            config.rate_limit,
            config.max_retries,
        )

    def _create_session(self) -> requests.Session:
        """
        Create and configure requests session with retry strategy.

        Returns:
            Configured requests.Session instance
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "OPTIONS"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(
            {
                "User-Agent": self.config.user_agent,
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;" "q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }
        )

        # Add custom headers
        if self.config.custom_headers:
            session.headers.update(self.config.custom_headers)

        # Add cookies
        if self.config.cookies:
            session.cookies.update(self.config.cookies)

        # Configure proxy
        if self.config.proxy:
            session.proxies = {"http": self.config.proxy, "https": self.config.proxy}

        return session

    def _get_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name (e.g., 'example.com')
        """
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def _get_robots_url(self, url: str) -> str:
        """
        Construct robots.txt URL for a given URL.

        Args:
            url: URL to get robots.txt for

        Returns:
            robots.txt URL
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def _fetch_robots_txt(self, url: str) -> RobotFileParser:
        """
        Fetch and parse robots.txt for a URL.

        Args:
            url: URL to fetch robots.txt for

        Returns:
            Parsed RobotFileParser instance

        Raises:
            ScrapingError: If fetching robots.txt fails
        """
        domain = self._get_domain(url)

        # Check cache
        if domain in self._robots_cache:
            return self._robots_cache[domain]

        robots_url = self._get_robots_url(url)
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            parser.read()
            self._robots_cache[domain] = parser
            logger.debug("Fetched robots.txt for %s", domain)
            return parser
        except Exception as e:
            logger.warning(
                "Failed to fetch robots.txt for %s: %s. Assuming allowed.",
                domain,
                str(e),
            )
            # Create permissive parser if robots.txt unavailable
            parser = RobotFileParser()
            self._robots_cache[domain] = parser
            return parser

    def is_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt rules.

        Args:
            url: URL to check

        Returns:
            True if scraping is allowed, False otherwise
        """
        if not self.config.respect_robots_txt:
            return True

        try:
            parser = self._fetch_robots_txt(url)
            allowed = parser.can_fetch(self.config.user_agent, url)
            if not allowed:
                logger.info("URL disallowed by robots.txt: %s", url)
            return allowed
        except Exception as e:
            logger.error("Error checking robots.txt for %s: %s", url, str(e))
            # Assume allowed if check fails
            return True

    def _is_domain_allowed(self, url: str) -> bool:
        """
        Check if URL domain is in allowed domains list.

        Args:
            url: URL to check

        Returns:
            True if domain is allowed or no domain filtering is configured
        """
        if not self.config.allowed_domains:
            return True

        domain = self._get_domain(url)
        return domain in self.config.allowed_domains

    def _apply_rate_limit(self, domain: str) -> None:
        """
        Apply rate limiting for a domain.

        Args:
            domain: Domain to apply rate limiting for
        """
        if domain in self._last_request_time:
            elapsed = time.time() - self._last_request_time[domain]
            sleep_time = self.config.rate_limit - elapsed

            if sleep_time > 0:
                logger.debug("Rate limiting: sleeping for %.2f seconds", sleep_time)
                time.sleep(sleep_time)

        self._last_request_time[domain] = time.time()

    def _retry_request(self, url: str, retries: int = 0) -> requests.Response:
        """
        Make HTTP request with retry logic and exponential backoff.

        Args:
            url: URL to request
            retries: Current retry attempt number

        Returns:
            requests.Response object

        Raises:
            ScrapingError: If all retry attempts fail
        """
        domain = self._get_domain(url)

        try:
            # Apply rate limiting
            self._apply_rate_limit(domain)

            # Make request
            start_time = time.time()
            response = self._session.get(
                url,
                timeout=self.config.timeout,
                allow_redirects=True,
                verify=self.config.verify_ssl,
            )
            response_time = time.time() - start_time

            self._request_count += 1

            # Log response
            logger.debug(
                "Request to %s: status=%s, time=%.2fs",
                url,
                response.status_code,
                response_time,
            )

            # Check for rate limiting
            if response.status_code == 429:
                if retries < self.config.max_retries:
                    backoff = self.config.backoff_factor ** (retries + 1)
                    logger.warning(
                        "Rate limited (429). Retrying in %.2f seconds", backoff
                    )
                    time.sleep(backoff)
                    return self._retry_request(url, retries + 1)
                raise RateLimitError(
                    f"Rate limit exceeded after {retries} retries", url
                )

            # Store response time for metadata
            response.elapsed_time = response_time  # type: ignore[attr-defined]

            return response

        except Timeout as e:
            if retries < self.config.max_retries:
                backoff = self.config.backoff_factor ** (retries + 1)
                logger.warning(
                    "Timeout on %s. Retrying in %.2f seconds (attempt %d/%d)",
                    url,
                    backoff,
                    retries + 1,
                    self.config.max_retries,
                )
                time.sleep(backoff)
                return self._retry_request(url, retries + 1)
            raise ScrapingError(f"Timeout after {retries} retries: {str(e)}", url)

        except TooManyRedirects as e:
            raise ScrapingError(
                f"Too many redirects (max {self.config.max_redirects}): {str(e)}", url
            )

        except ConnectionError as e:
            if retries < self.config.max_retries:
                backoff = self.config.backoff_factor ** (retries + 1)
                logger.warning(
                    "Connection error on %s. Retrying in %.2f seconds",
                    url,
                    backoff,
                )
                time.sleep(backoff)
                return self._retry_request(url, retries + 1)
            raise ScrapingError(
                f"Connection error after {retries} retries: {str(e)}", url
            )

        except HTTPError as e:
            raise ScrapingError(f"HTTP error: {str(e)}", url)

        except RequestException as e:
            raise ScrapingError(f"Request failed: {str(e)}", url)

    def parse_html(self, html: str, url: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup.

        Args:
            html: Raw HTML content
            url: Source URL for context

        Returns:
            BeautifulSoup object

        Raises:
            ScrapingError: If parsing fails
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            logger.debug("Successfully parsed HTML from %s", url)
            return soup
        except Exception:
            # Fallback to html.parser
            try:
                soup = BeautifulSoup(html, "html.parser")
                logger.debug("Parsed HTML from %s using html.parser fallback", url)
                return soup
            except Exception as fallback_error:
                raise ScrapingError(f"Failed to parse HTML: {str(fallback_error)}", url)

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs extracted from the page
        """
        try:
            soup = self.parse_html(html, base_url)
            links: Set[str] = set()

            # Extract links from <a> tags
            for anchor in soup.find_all("a", href=True):
                href = str(anchor.get("href", ""))  # type: ignore[union-attr]
                if not href:
                    continue
                absolute_url = urljoin(base_url, href)

                # Filter out non-HTTP(S) links
                parsed = urlparse(absolute_url)
                if parsed.scheme in ["http", "https"]:
                    links.add(absolute_url)

            # Extract links from <link> tags
            for link_tag in soup.find_all("link", href=True):
                href = str(link_tag.get("href", ""))  # type: ignore[union-attr]
                if not href:
                    continue
                absolute_url = urljoin(base_url, href)
                parsed = urlparse(absolute_url)
                if parsed.scheme in ["http", "https"]:
                    links.add(absolute_url)

            logger.debug("Extracted %d unique links from %s", len(links), base_url)
            return sorted(list(links))

        except Exception as e:
            logger.error("Error extracting links from %s: %s", base_url, str(e))
            return []

    def scrape_url(self, url: str) -> ScrapedContent:
        """
        Scrape a single URL.

        Args:
            url: URL to scrape

        Returns:
            ScrapedContent object with scraped data

        Raises:
            ScrapingError: If scraping fails
            RobotsDisallowedError: If URL is disallowed by robots.txt
        """
        logger.info("Scraping URL: %s", url)

        # Validate URL format
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception as e:
            raise ScrapingError(f"Invalid URL: {str(e)}", url)

        # Check domain allowlist
        if not self._is_domain_allowed(url):
            raise ScrapingError(
                f"Domain not in allowed list: {self._get_domain(url)}", url
            )

        # Check robots.txt
        if not self.is_allowed(url):
            raise RobotsDisallowedError(f"URL disallowed by robots.txt: {url}", url)

        # Make request with retry logic
        response = self._retry_request(url)

        # Extract content type and encoding
        content_type = response.headers.get("Content-Type", "")
        encoding = response.encoding

        # Validate content type (should be HTML)
        if "text/html" not in content_type.lower():
            logger.warning("Non-HTML content type for %s: %s", url, content_type)

        # Get HTML content
        html = response.text

        # Extract links
        links = self.extract_links(html, url)

        # Build metadata
        metadata = {
            "final_url": response.url,
            "redirects": len(response.history),
            "request_count": self._request_count,
        }

        # Create ScrapedContent object
        scraped_content = ScrapedContent(
            url=url,
            html=html,
            status_code=response.status_code,
            headers=dict(response.headers),
            links=links,
            scraped_at=datetime.now(),
            metadata=metadata,
            content_type=content_type,
            encoding=encoding,
            response_time=getattr(response, "elapsed_time", 0.0),
        )

        logger.info(
            "Successfully scraped %s: status=%s, links=%d, size=%d bytes",
            url,
            response.status_code,
            len(links),
            len(html),
        )

        return scraped_content

    def scrape_urls(self, urls: List[str]) -> List[ScrapedContent]:
        """
        Scrape multiple URLs in batch.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of ScrapedContent objects (excludes failed scrapes)
        """
        logger.info("Starting batch scrape of %d URLs", len(urls))

        results: List[ScrapedContent] = []
        failed_urls: List[tuple[str, str]] = []

        for i, url in enumerate(urls, 1):
            logger.info("Scraping URL %d/%d: %s", i, len(urls), url)

            try:
                content = self.scrape_url(url)
                results.append(content)
            except RobotsDisallowedError as e:
                logger.warning("Skipping disallowed URL: %s", url)
                failed_urls.append((url, f"Robots disallowed: {str(e)}"))
            except ScrapingError as e:
                logger.error("Failed to scrape %s: %s", url, str(e))
                failed_urls.append((url, str(e)))
            except Exception as e:
                logger.exception("Unexpected error scraping %s", url)
                failed_urls.append((url, f"Unexpected error: {str(e)}"))

        logger.info(
            "Batch scrape complete: %d successful, %d failed",
            len(results),
            len(failed_urls),
        )

        if failed_urls:
            logger.warning("Failed URLs:")
            for url, error in failed_urls:
                logger.warning("  - %s: %s", url, error)

        return results

    def get_robots_rules(self, url: str) -> RobotsRule:
        """
        Get detailed robots.txt rules for a URL.

        Args:
            url: URL to get robots.txt rules for

        Returns:
            RobotsRule object with parsed rules
        """
        domain = self._get_domain(url)
        parser = self._fetch_robots_txt(url)

        # Extract rules (note: RobotFileParser has limited inspection API)
        robots_rule = RobotsRule(
            domain=domain,
            user_agent=self.config.user_agent,
            allowed_paths=[],
            disallowed_paths=[],
            crawl_delay=None,
            sitemap_urls=[],
            last_fetched=datetime.now(),
        )

        # Try to extract crawl delay if available
        try:
            crawl_delay = parser.crawl_delay(self.config.user_agent)
            if crawl_delay:
                robots_rule.crawl_delay = float(crawl_delay)
        except (AttributeError, ValueError, TypeError):
            pass

        # Extract sitemap URLs if available
        try:
            if hasattr(parser, "site_maps") and parser.site_maps():
                sitemaps = parser.site_maps()
                if sitemaps:
                    robots_rule.sitemap_urls = list(sitemaps)
        except (AttributeError, TypeError):
            pass

        logger.debug("Retrieved robots.txt rules for %s", domain)
        return robots_rule

    def clear_robots_cache(self) -> None:
        """Clear the robots.txt cache."""
        self._robots_cache.clear()
        logger.info("Cleared robots.txt cache")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get scraping statistics.

        Returns:
            Dictionary with scraping statistics
        """
        return {
            "total_requests": self._request_count,
            "cached_robots": len(self._robots_cache),
            "tracked_domains": len(self._last_request_time),
            "config": {
                "rate_limit": self.config.rate_limit,
                "max_retries": self.config.max_retries,
                "respect_robots_txt": self.config.respect_robots_txt,
                "timeout": self.config.timeout,
            },
        }

    def close(self) -> None:
        """Close the scraper and clean up resources."""
        if self._session:
            self._session.close()
        logger.info("WebScraper closed. Total requests: %d", self._request_count)

    def __enter__(self) -> "WebScraper":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of WebScraper."""
        return (
            f"WebScraper(rate_limit={self.config.rate_limit}, "
            f"max_retries={self.config.max_retries}, "
            f"requests={self._request_count})"
        )
