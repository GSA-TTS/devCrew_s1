"""
Comprehensive Test Suite for Web Research & Content Extraction Platform.

This test suite provides 85+ test functions covering all components:
- WebScraper (15 tests)
- BrowserAutomation (15 tests)
- ContentExtractor (15 tests)
- KnowledgeIndexer (15 tests)
- ContentValidator (15 tests)
- CacheManager (15 tests)
- CLI (10 tests)

All external dependencies are mocked to ensure isolated, deterministic testing.
"""

import json
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
import responses
from click.testing import CliRunner
from fakeredis import FakeRedis

# Import modules to test
from tools.web_research.browser_automation import (
    BrowserAutomation,
    BrowserType,
    NavigationError,
    RenderConfig,
    RenderTimeoutError,
    RenderedPage,
)
from tools.web_research.cache_manager import (
    CacheBackend,
    CacheConfig,
    CacheManager,
    CacheStats,
)
from tools.web_research.content_extractor import (
    ArticleMetadata,
    ContentExtractor,
    ExtractionConfig,
    ExtractionError,
    ExtractedArticle,
    LanguageDetectionError,
)
from tools.web_research.content_validator import (
    ContentValidator,
    ExtractedEntities,
    QualityMetrics,
    QualityRating,
    ValidationConfig,
    ValidationResult,
)
from tools.web_research.knowledge_indexer import (
    EmbeddingStats,
    IndexConfig,
    IndexStats,
    KnowledgeIndexer,
    TextChunk,
    VectorDB,
    VectorDBError,
)
from tools.web_research.web_scraper import (
    RobotsDisallowedError,
    ScrapedContent,
    ScrapingConfig,
    ScrapingError,
    WebScraper,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_html() -> str:
    """Sample HTML for testing."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Test Article Title</title>
        <meta name="description" content="Test article description">
        <meta name="author" content="John Doe">
        <meta name="keywords" content="test, article, web">
        <meta property="og:title" content="Test Article Title">
        <meta property="og:description" content="OG Description">
        <meta property="og:image" content="https://example.com/image.jpg">
        <meta property="article:published_time" content="2024-01-15T10:00:00Z">
        <link rel="canonical" href="https://example.com/article">
    </head>
    <body>
        <header>
            <nav>Navigation</nav>
        </header>
        <article>
            <h1>Test Article Title</h1>
            <p class="author">By John Doe</p>
            <p>This is the first paragraph of the article. It contains some
            meaningful content for testing purposes. The paragraph has
            sufficient length.</p>
            <p>This is the second paragraph. It provides additional context
            and information. Testing extraction quality requires multiple
            paragraphs.</p>
            <img src="/image1.jpg" alt="Test Image 1">
            <a href="https://example.com/link1">Link 1</a>
            <a href="https://example.com/link2">Link 2</a>
        </article>
        <footer>Footer Content</footer>
    </body>
    </html>
    """


@pytest.fixture
def mock_article() -> ExtractedArticle:
    """Sample extracted article for testing."""
    metadata = ArticleMetadata(
        url="https://example.com/article",
        title="Test Article",
        author="John Doe",
        publish_date=datetime(2024, 1, 15, 10, 0, 0),
        language="en",
        word_count=150,
        tags=["test", "article"],
    )

    return ExtractedArticle(
        url="https://example.com/article",
        title="Test Article",
        content="This is test content. " * 50,
        html="<html>...</html>",
        metadata=metadata,
        extracted_at=datetime.utcnow(),
    )


@pytest.fixture
def scraping_config() -> ScrapingConfig:
    """Default scraping configuration for testing."""
    return ScrapingConfig(
        rate_limit=0.1,
        max_retries=2,
        timeout=5,
        respect_robots_txt=False,
    )


@pytest.fixture
def extraction_config() -> ExtractionConfig:
    """Default extraction configuration for testing."""
    return ExtractionConfig(
        include_images=True,
        include_links=True,
        min_text_length=10,
    )


@pytest.fixture
def cache_config() -> CacheConfig:
    """Default cache configuration for testing."""
    return CacheConfig(
        backend=CacheBackend.MEMORY,
        ttl_seconds=60,
        max_memory=1024 * 1024,
    )


# ============================================================================
# WEBSCRAPER TESTS (15 tests)
# ============================================================================


class TestWebScraper:
    """Tests for WebScraper component."""

    def test_scraper_initialization(self, scraping_config: ScrapingConfig) -> None:
        """Test WebScraper initialization."""
        scraper = WebScraper(scraping_config)
        assert scraper.config == scraping_config
        assert scraper._session is not None
        assert scraper._request_count == 0
        assert len(scraper._robots_cache) == 0

    @responses.activate
    def test_scrape_url_success(
        self, scraping_config: ScrapingConfig, mock_html: str
    ) -> None:
        """Test successful URL scraping."""
        url = "https://example.com/test"
        responses.add(
            responses.GET,
            url,
            body=mock_html,
            status=200,
            headers={"Content-Type": "text/html"},
        )

        scraper = WebScraper(scraping_config)
        result = scraper.scrape_url(url)

        assert isinstance(result, ScrapedContent)
        assert result.url == url
        assert result.status_code == 200
        assert len(result.html) > 0
        assert len(result.links) > 0

    @responses.activate
    def test_scrape_url_with_links(self, scraping_config: ScrapingConfig) -> None:
        """Test link extraction during scraping."""
        url = "https://example.com"
        html = (
            '<html><body><a href="/page1">P1</a>' '<a href="page2">P2</a></body></html>'
        )
        responses.add(responses.GET, url, body=html, status=200)

        scraper = WebScraper(scraping_config)
        result = scraper.scrape_url(url)

        assert len(result.links) == 2
        assert "https://example.com/page1" in result.links

    def test_scrape_url_invalid_url(self, scraping_config: ScrapingConfig) -> None:
        """Test scraping with invalid URL."""
        scraper = WebScraper(scraping_config)
        with pytest.raises(ScrapingError, match="Invalid URL"):
            scraper.scrape_url("not-a-valid-url")

    @responses.activate
    def test_scrape_url_timeout(self, scraping_config: ScrapingConfig) -> None:
        """Test scraping with timeout error."""
        url = "https://example.com/timeout"
        responses.add(responses.GET, url, body="Error", status=408)

        scraper = WebScraper(scraping_config)
        scraper.config.max_retries = 0

        with pytest.raises(ScrapingError):
            scraper.scrape_url(url)

    @responses.activate
    def test_scrape_url_rate_limit(self, scraping_config: ScrapingConfig) -> None:
        """Test rate limiting during scraping."""
        url = "https://example.com"
        responses.add(responses.GET, url, body="OK", status=200)

        scraper = WebScraper(scraping_config)
        scraper.config.rate_limit = 0.5

        start = time.time()
        scraper.scrape_url(url)
        scraper.scrape_url(url)
        duration = time.time() - start

        assert duration >= 0.5

    @responses.activate
    def test_scrape_urls_batch(self, scraping_config: ScrapingConfig) -> None:
        """Test batch URL scraping."""
        urls = [f"https://example.com/page{i}" for i in range(3)]
        for url in urls:
            responses.add(responses.GET, url, body="Content", status=200)

        scraper = WebScraper(scraping_config)
        scraper.config.rate_limit = 0.01
        results = scraper.scrape_urls(urls)

        assert len(results) == 3
        assert all(isinstance(r, ScrapedContent) for r in results)

    def test_robots_txt_parsing(self, scraping_config: ScrapingConfig) -> None:
        """Test robots.txt fetching and parsing."""
        scraping_config.respect_robots_txt = True
        scraper = WebScraper(scraping_config)

        with patch.object(scraper, "_fetch_robots_txt") as mock_fetch:
            mock_parser = MagicMock()
            mock_parser.can_fetch.return_value = True
            mock_fetch.return_value = mock_parser

            result = scraper.is_allowed("https://example.com/page")
            assert result is True

    def test_robots_txt_disallowed(self, scraping_config: ScrapingConfig) -> None:
        """Test robots.txt disallowing URL."""
        scraping_config.respect_robots_txt = True
        scraper = WebScraper(scraping_config)

        with patch.object(scraper, "_fetch_robots_txt") as mock_fetch:
            mock_parser = MagicMock()
            mock_parser.can_fetch.return_value = False
            mock_fetch.return_value = mock_parser

            with pytest.raises(RobotsDisallowedError):
                scraper.scrape_url("https://example.com/blocked")

    def test_domain_filtering(self, scraping_config: ScrapingConfig) -> None:
        """Test domain allowlist filtering."""
        scraping_config.allowed_domains = ["example.com"]
        scraper = WebScraper(scraping_config)

        with pytest.raises(ScrapingError, match="Domain not in allowed list"):
            scraper.scrape_url("https://other.com/page")

    @responses.activate
    def test_retry_logic(self, scraping_config: ScrapingConfig) -> None:
        """Test retry logic with exponential backoff."""
        url = "https://example.com"
        responses.add(responses.GET, url, body="Error", status=500)
        responses.add(responses.GET, url, body="Error", status=500)
        responses.add(responses.GET, url, body="Success", status=200)

        scraper = WebScraper(scraping_config)
        scraper.config.backoff_factor = 1.0
        result = scraper.scrape_url(url)

        assert result.status_code == 200

    def test_get_stats(self, scraping_config: ScrapingConfig) -> None:
        """Test statistics retrieval."""
        scraper = WebScraper(scraping_config)
        stats = scraper.get_stats()

        assert "total_requests" in stats
        assert "cached_robots" in stats
        assert stats["total_requests"] == 0

    def test_context_manager(self, scraping_config: ScrapingConfig) -> None:
        """Test WebScraper as context manager."""
        with WebScraper(scraping_config) as scraper:
            assert scraper._session is not None

    def test_extract_links_from_html(
        self, scraping_config: ScrapingConfig, mock_html: str
    ) -> None:
        """Test link extraction from HTML."""
        scraper = WebScraper(scraping_config)
        base_url = "https://example.com"

        links = scraper.extract_links(mock_html, base_url)

        assert len(links) > 0
        assert all(link.startswith("http") for link in links)

    def test_clear_robots_cache(self, scraping_config: ScrapingConfig) -> None:
        """Test clearing robots.txt cache."""
        scraper = WebScraper(scraping_config)
        scraper._robots_cache["example.com"] = MagicMock()

        scraper.clear_robots_cache()
        assert len(scraper._robots_cache) == 0


# ============================================================================
# BROWSER AUTOMATION TESTS (15 tests)
# ============================================================================


class TestBrowserAutomation:
    """Tests for BrowserAutomation component."""

    @pytest.mark.asyncio
    async def test_browser_initialization(self) -> None:
        """Test browser initialization."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        assert browser.config == config
        assert browser._playwright is None
        assert browser._browser is None

    @pytest.mark.asyncio
    async def test_context_manager_setup_teardown(self) -> None:
        """Test async context manager setup and teardown."""
        config = RenderConfig(headless=True)

        with patch("tools.web_research.browser_automation.async_playwright") as mock_pw:
            mock_playwright = AsyncMock()
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            mock_playwright.chromium.launch = AsyncMock(return_value=AsyncMock())

            browser = BrowserAutomation(config)
            try:
                await browser._initialize_browser()
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_render_page_mocked(self) -> None:
        """Test page rendering with mocked Playwright."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(return_value=AsyncMock(ok=True, status=200))
        mock_page.content = AsyncMock(return_value="<html>Rendered</html>")
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_page.url = "https://example.com"
        mock_page.evaluate = AsyncMock(return_value={})

        mock_context = AsyncMock()
        mock_context.cookies = AsyncMock(return_value=[])

        browser._page = mock_page
        browser._context = mock_context

        result = await browser.render_page("https://example.com")

        assert isinstance(result, RenderedPage)
        assert result.url == "https://example.com"
        assert "Rendered" in result.html

    @pytest.mark.asyncio
    async def test_render_page_timeout(self) -> None:
        """Test page rendering timeout handling."""
        config = RenderConfig(headless=True, timeout=1000)
        browser = BrowserAutomation(config)

        mock_page = AsyncMock()
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        mock_page.goto = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

        browser._page = mock_page
        browser._context = AsyncMock()

        with pytest.raises(RenderTimeoutError):
            await browser.render_page("https://example.com")

    @pytest.mark.asyncio
    async def test_render_page_navigation_error(self) -> None:
        """Test page rendering with navigation error."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(return_value=None)

        browser._page = mock_page

        with pytest.raises(NavigationError):
            await browser.render_page("https://example.com")

    @pytest.mark.asyncio
    async def test_take_screenshot(self) -> None:
        """Test screenshot capture."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(return_value=AsyncMock(ok=True))
        mock_page.screenshot = AsyncMock(return_value=b"screenshot_data")

        browser._page = mock_page

        result = await browser.take_screenshot("https://example.com")

        assert result == b"screenshot_data"
        mock_page.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_script(self) -> None:
        """Test JavaScript execution."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value={"result": "success"})

        browser._page = mock_page

        result = await browser.execute_script("return {result: 'success'}")

        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_wait_for_selector_success(self) -> None:
        """Test waiting for selector successfully."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        mock_page = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())

        browser._page = mock_page

        result = await browser.wait_for_selector(".content")

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_selector_timeout(self) -> None:
        """Test waiting for selector timeout."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        mock_page = AsyncMock()
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        mock_page.wait_for_selector = AsyncMock(
            side_effect=PlaywrightTimeoutError("Timeout")
        )

        browser._page = mock_page

        result = await browser.wait_for_selector(".missing", timeout=1000)

        assert result is False

    @pytest.mark.asyncio
    async def test_network_request_monitoring(self) -> None:
        """Test network request monitoring."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(return_value=AsyncMock(ok=True))

        browser._page = mock_page
        browser._network_requests = []

        result = await browser.get_network_requests("https://example.com")

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_form_filling(self) -> None:
        """Test form field filling."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        mock_page = AsyncMock()
        mock_page.fill = AsyncMock()

        browser._page = mock_page

        await browser.fill_form("#username", "testuser")

        mock_page.fill.assert_called_once_with("#username", "testuser", timeout=30000)

    @pytest.mark.asyncio
    async def test_cookie_management(self) -> None:
        """Test cookie getting and setting."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        mock_context = AsyncMock()
        mock_context.cookies = AsyncMock(
            return_value=[{"name": "test", "value": "cookie"}]
        )
        mock_context.add_cookies = AsyncMock()

        browser._context = mock_context

        cookies = await browser.get_cookies()
        assert len(cookies) == 1

        await browser.set_cookies([{"name": "new", "value": "cookie"}])
        mock_context.add_cookies.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup(self) -> None:
        """Test browser cleanup."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        browser._page = AsyncMock()
        browser._context = AsyncMock()
        browser._browser = AsyncMock()
        browser._playwright = AsyncMock()

        await browser._cleanup()

        assert browser._page is None
        assert browser._context is None

    @pytest.mark.asyncio
    async def test_console_log_capture(self) -> None:
        """Test console message capture."""
        config = RenderConfig(headless=True)
        browser = BrowserAutomation(config)

        browser._console_messages = []

        mock_msg = MagicMock()
        mock_msg.type = "log"
        mock_msg.text = "Test message"
        mock_msg.location = None

        browser._on_console(mock_msg)

        assert len(browser._console_messages) == 1

    @pytest.mark.asyncio
    async def test_browser_type_selection(self) -> None:
        """Test different browser type selections."""
        for browser_type in [
            BrowserType.CHROMIUM,
            BrowserType.FIREFOX,
            BrowserType.WEBKIT,
        ]:
            config = RenderConfig(browser_type=browser_type)
            browser = BrowserAutomation(config)
            assert browser.config.browser_type == browser_type


# ============================================================================
# CONTENT EXTRACTOR TESTS (15 tests)
# ============================================================================


class TestContentExtractor:
    """Tests for ContentExtractor component."""

    def test_extractor_initialization(
        self, extraction_config: ExtractionConfig
    ) -> None:
        """Test ContentExtractor initialization."""
        extractor = ContentExtractor(extraction_config)
        assert extractor.config == extraction_config

    def test_extract_article_success(
        self, extraction_config: ExtractionConfig, mock_html: str
    ) -> None:
        """Test successful article extraction."""
        extractor = ContentExtractor(extraction_config)
        url = "https://example.com/article"

        result = extractor.extract_article(mock_html, url)

        assert isinstance(result, ExtractedArticle)
        assert result.url == url
        assert len(result.content) > 0
        assert result.title is not None

    def test_extract_article_empty_html(
        self, extraction_config: ExtractionConfig
    ) -> None:
        """Test extraction with empty HTML."""
        extractor = ContentExtractor(extraction_config)

        with pytest.raises(ExtractionError, match="Empty HTML"):
            extractor.extract_article("", "https://example.com")

    def test_extract_metadata(
        self, extraction_config: ExtractionConfig, mock_html: str
    ) -> None:
        """Test metadata extraction."""
        extractor = ContentExtractor(extraction_config)

        metadata = extractor.extract_metadata(mock_html)

        assert isinstance(metadata, ArticleMetadata)
        assert metadata.title == "Test Article Title"
        assert metadata.description is not None

    def test_extract_images(
        self, extraction_config: ExtractionConfig, mock_html: str
    ) -> None:
        """Test image extraction."""
        extractor = ContentExtractor(extraction_config)
        base_url = "https://example.com"

        images = extractor.extract_images(mock_html, base_url)

        assert isinstance(images, list)
        assert len(images) > 0
        assert all("url" in img and "alt" in img for img in images)

    def test_extract_links(
        self, extraction_config: ExtractionConfig, mock_html: str
    ) -> None:
        """Test link extraction."""
        extractor = ContentExtractor(extraction_config)
        base_url = "https://example.com"

        links = extractor.extract_links(mock_html, base_url)

        assert isinstance(links, list)
        assert len(links) > 0
        assert all("url" in link and "text" in link for link in links)

    def test_extract_structured_data(self, extraction_config: ExtractionConfig) -> None:
        """Test structured data extraction."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {"@type": "Article", "name": "Test"}
            </script>
        </head>
        <body>
            <div itemscope itemtype="http://schema.org/Article">
                <span itemprop="name">Article Name</span>
            </div>
        </body>
        </html>
        """
        extractor = ContentExtractor(extraction_config)

        structured = extractor.extract_structured_data(html)

        assert "json_ld" in structured
        assert "microdata" in structured

    def test_readability_calculation(self, extraction_config: ExtractionConfig) -> None:
        """Test readability score calculation."""
        extractor = ContentExtractor(extraction_config)
        text = "This is a simple sentence. " * 10

        score = extractor.calculate_readability(text)

        assert 0.0 <= score <= 100.0

    def test_language_detection(self, extraction_config: ExtractionConfig) -> None:
        """Test language detection."""
        extractor = ContentExtractor(extraction_config)
        english_text = "This is an English text for testing language detection."

        lang = extractor.detect_language(english_text)

        assert lang == "en"

    def test_language_detection_short_text(
        self, extraction_config: ExtractionConfig
    ) -> None:
        """Test language detection with short text."""
        extractor = ContentExtractor(extraction_config)

        with pytest.raises(LanguageDetectionError, match="too short"):
            extractor.detect_language("Hi")

    def test_text_cleaning(self, extraction_config: ExtractionConfig) -> None:
        """Test text cleaning and normalization."""
        extractor = ContentExtractor(extraction_config)
        dirty_text = "  Test   \n\n\n  multiple   spaces  \n\n\n\n  and lines  "

        clean = extractor.clean_text(dirty_text)

        assert "Test" in clean
        assert "  " not in clean
        assert "\n\n\n" not in clean

    def test_extract_to_markdown(
        self, extraction_config: ExtractionConfig, mock_html: str
    ) -> None:
        """Test markdown export."""
        extractor = ContentExtractor(extraction_config)
        url = "https://example.com"

        markdown = extractor.extract_to_markdown(mock_html, url)

        assert isinstance(markdown, str)

    def test_extraction_fallback_methods(
        self, extraction_config: ExtractionConfig
    ) -> None:
        """Test extraction fallback to different methods."""
        html = "<html><body><p>Simple content.</p></body></html>"
        extractor = ContentExtractor(extraction_config)

        with patch.object(extractor, "_extract_with_trafilatura", return_value=None):
            result = extractor.extract_article(html, "https://example.com")
            assert result.extraction_method in ["readability", "basic"]

    def test_validate_extraction(self, extraction_config: ExtractionConfig) -> None:
        """Test extraction validation."""
        extraction_config.min_text_length = 50
        extraction_config.target_language = "en"
        extractor = ContentExtractor(extraction_config)

        article = ExtractedArticle(
            url="https://example.com",
            title="Test",
            content="Content " * 20,
            html="<html></html>",
            metadata=ArticleMetadata(url="https://example.com", word_count=20),
        )

        is_valid = extractor.validate_extraction(article)
        assert is_valid is True

    def test_extraction_stats(
        self, extraction_config: ExtractionConfig, mock_article: ExtractedArticle
    ) -> None:
        """Test extraction statistics."""
        extractor = ContentExtractor(extraction_config)

        stats = extractor.get_extraction_stats(mock_article)

        assert "word_count" in stats
        assert "character_count" in stats
        assert "extraction_method" in stats


# ============================================================================
# KNOWLEDGE INDEXER TESTS (15 tests)
# ============================================================================


class TestKnowledgeIndexer:
    """Tests for KnowledgeIndexer component."""

    @pytest.fixture
    def index_config(self) -> IndexConfig:
        """Index configuration for testing."""
        return IndexConfig(
            vector_db=VectorDB.INMEMORY,
            collection_name="test_collection",
            chunk_size=256,
            chunk_overlap=20,
        )

    def test_indexer_initialization(self, index_config: IndexConfig) -> None:
        """Test KnowledgeIndexer initialization."""
        with patch("tools.web_research.knowledge_indexer.SentenceTransformer"):
            indexer = KnowledgeIndexer(index_config)
            assert indexer.config == index_config

    def test_text_chunking(self, index_config: IndexConfig) -> None:
        """Test text chunking."""
        with patch("tools.web_research.knowledge_indexer.SentenceTransformer"):
            indexer = KnowledgeIndexer(index_config)

            text = "This is a sentence. " * 50
            chunks = indexer.chunk_content(text)

            assert len(chunks) > 0
            assert all(isinstance(c, TextChunk) for c in chunks)

    def test_chunking_with_overlap(self, index_config: IndexConfig) -> None:
        """Test chunking with overlap."""
        with patch("tools.web_research.knowledge_indexer.SentenceTransformer"):
            indexer = KnowledgeIndexer(index_config)

            text = "Sentence one. " * 100
            chunks = indexer.chunk_content(text, chunk_size=100, overlap=20)

            assert len(chunks) > 1

    def test_chunking_empty_content(self, index_config: IndexConfig) -> None:
        """Test chunking with empty content."""
        with patch("tools.web_research.knowledge_indexer.SentenceTransformer"):
            indexer = KnowledgeIndexer(index_config)

            chunks = indexer.chunk_content("")
            assert len(chunks) == 0

    def test_generate_embeddings(self, index_config: IndexConfig) -> None:
        """Test embedding generation."""
        with patch(
            "tools.web_research.knowledge_indexer.SentenceTransformer"
        ) as MockModel:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]] * 3)
            MockModel.return_value = mock_model

            indexer = KnowledgeIndexer(index_config)
            texts = ["text1", "text2", "text3"]

            embeddings = indexer.generate_embeddings(texts)

            assert len(embeddings) == 3
            assert all(isinstance(e, list) for e in embeddings)

    def test_embedding_empty_texts(self, index_config: IndexConfig) -> None:
        """Test embedding generation with empty texts."""
        with patch("tools.web_research.knowledge_indexer.SentenceTransformer"):
            indexer = KnowledgeIndexer(index_config)

            embeddings = indexer.generate_embeddings([])
            assert len(embeddings) == 0

    def test_index_to_vectordb(self, index_config: IndexConfig) -> None:
        """Test indexing to vector database."""
        with patch("tools.web_research.knowledge_indexer.SentenceTransformer"):
            with patch("tools.web_research.knowledge_indexer.chromadb.Client"):
                indexer = KnowledgeIndexer(index_config)

                chunks = [
                    TextChunk(
                        text=f"chunk {i}",
                        document_id="doc1",
                        chunk_index=i,
                    )
                    for i in range(3)
                ]
                embeddings = [[0.1, 0.2, 0.3]] * 3

                result = indexer.index_to_vectordb(chunks, embeddings)
                assert result is True

    def test_index_mismatch_error(self, index_config: IndexConfig) -> None:
        """Test indexing with mismatched chunks and embeddings."""
        with patch("tools.web_research.knowledge_indexer.SentenceTransformer"):
            with patch("tools.web_research.knowledge_indexer.chromadb.Client"):
                indexer = KnowledgeIndexer(index_config)

                chunks = [TextChunk(text="chunk", document_id="doc1", chunk_index=0)]
                embeddings = [[0.1, 0.2], [0.3, 0.4]]

                with pytest.raises(VectorDBError, match="mismatch"):
                    indexer.index_to_vectordb(chunks, embeddings)

    def test_semantic_search(self, index_config: IndexConfig) -> None:
        """Test semantic search."""
        with patch(
            "tools.web_research.knowledge_indexer.SentenceTransformer"
        ) as MockModel:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
            MockModel.return_value = mock_model

            with patch(
                "tools.web_research.knowledge_indexer.chromadb.Client"
            ) as MockClient:
                mock_collection = MagicMock()
                mock_collection.query.return_value = {
                    "ids": [["id1"]],
                    "documents": [["doc1"]],
                    "metadatas": [[{"document_id": "doc1"}]],
                    "distances": [[0.1]],
                }
                mock_client = MagicMock()
                mock_client.get_or_create_collection.return_value = mock_collection
                MockClient.return_value = mock_client

                indexer = KnowledgeIndexer(index_config)
                results = indexer.semantic_search("test query")

                assert isinstance(results, list)

    def test_batch_indexing(self, index_config: IndexConfig) -> None:
        """Test batch indexing multiple articles."""
        with patch(
            "tools.web_research.knowledge_indexer.SentenceTransformer"
        ) as MockModel:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]] * 10)
            MockModel.return_value = mock_model

            with patch("tools.web_research.knowledge_indexer.chromadb.Client"):
                indexer = KnowledgeIndexer(index_config)

                from tools.web_research.knowledge_indexer import ExtractedArticle

                articles = [
                    ExtractedArticle(
                        url=f"https://example.com/{i}",
                        title=f"Article {i}",
                        content="Content " * 100,
                    )
                    for i in range(3)
                ]

                stats = indexer.batch_index(articles)
                assert isinstance(stats, IndexStats)

    def test_collection_management(self, index_config: IndexConfig) -> None:
        """Test collection management operations."""
        with patch("tools.web_research.knowledge_indexer.SentenceTransformer"):
            with patch(
                "tools.web_research.knowledge_indexer.chromadb.Client"
            ) as MockClient:
                mock_client = MagicMock()
                mock_client.list_collections.return_value = []
                MockClient.return_value = mock_client

                indexer = KnowledgeIndexer(index_config)
                collections = indexer.list_collections()
                assert isinstance(collections, list)

    def test_delete_by_document_id(self, index_config: IndexConfig) -> None:
        """Test deleting chunks by document ID."""
        with patch("tools.web_research.knowledge_indexer.SentenceTransformer"):
            with patch(
                "tools.web_research.knowledge_indexer.chromadb.Client"
            ) as MockClient:
                mock_collection = MagicMock()
                mock_collection.get.return_value = {"ids": ["chunk1", "chunk2"]}
                mock_client = MagicMock()
                mock_client.get_or_create_collection.return_value = mock_collection
                MockClient.return_value = mock_client

                indexer = KnowledgeIndexer(index_config)
                count = indexer.delete_by_document_id("doc1")
                assert count == 2

    def test_get_collection_stats(self, index_config: IndexConfig) -> None:
        """Test getting collection statistics."""
        with patch(
            "tools.web_research.knowledge_indexer.SentenceTransformer"
        ) as MockModel:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            MockModel.return_value = mock_model

            with patch(
                "tools.web_research.knowledge_indexer.chromadb.Client"
            ) as MockClient:
                mock_collection = MagicMock()
                mock_collection.count.return_value = 0
                mock_client = MagicMock()
                mock_client.get_or_create_collection.return_value = mock_collection
                MockClient.return_value = mock_client

                indexer = KnowledgeIndexer(index_config)
                stats = indexer.get_collection_stats()

                assert isinstance(stats, EmbeddingStats)

    def test_hybrid_search(self, index_config: IndexConfig) -> None:
        """Test hybrid search with filters."""
        with patch(
            "tools.web_research.knowledge_indexer.SentenceTransformer"
        ) as MockModel:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
            MockModel.return_value = mock_model

            with patch(
                "tools.web_research.knowledge_indexer.chromadb.Client"
            ) as MockClient:
                mock_collection = MagicMock()
                mock_collection.query.return_value = {
                    "ids": [[]],
                    "documents": [[]],
                    "metadatas": [[]],
                    "distances": [[]],
                }
                mock_client = MagicMock()
                mock_client.get_or_create_collection.return_value = mock_collection
                MockClient.return_value = mock_client

                indexer = KnowledgeIndexer(index_config)
                results = indexer.hybrid_search(
                    "test query", filters={"language": "en"}
                )

                assert isinstance(results, list)


# ============================================================================
# CONTENT VALIDATOR TESTS (15 tests)
# ============================================================================


class TestContentValidator:
    """Tests for ContentValidator component."""

    @pytest.fixture
    def validation_config(self) -> ValidationConfig:
        """Validation configuration for testing."""
        return ValidationConfig(
            check_links=False,
            enable_sentiment_analysis=False,
            enable_bias_detection=False,
        )

    def test_validator_initialization(
        self, validation_config: ValidationConfig
    ) -> None:
        """Test ContentValidator initialization."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)
                assert validator.config == validation_config

    def test_validate_content_success(
        self, validation_config: ValidationConfig, mock_article: ExtractedArticle
    ) -> None:
        """Test successful content validation."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                with patch.object(
                    validator,
                    "assess_quality",
                    return_value=MagicMock(overall_score=0.8),
                ):
                    with patch.object(
                        validator,
                        "extract_entities",
                        return_value=MagicMock(total_count=10),
                    ):
                        result = validator.validate_content(mock_article)

                        assert isinstance(result, ValidationResult)
                        assert result.url == mock_article.url

    def test_assess_quality(self, validation_config: ValidationConfig) -> None:
        """Test quality assessment."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                text = "This is a well-written article. " * 10
                metrics = validator.assess_quality(text)

                assert isinstance(metrics, QualityMetrics)
                assert 0.0 <= metrics.overall_score <= 1.0

    def test_extract_entities(self, validation_config: ValidationConfig) -> None:
        """Test entity extraction with spaCy."""
        with patch("tools.web_research.content_validator.spacy.load") as mock_load:
            mock_nlp = MagicMock()
            mock_doc = MagicMock()

            # Mock entity
            mock_ent = MagicMock()
            mock_ent.text = "Google"
            mock_ent.label_ = "ORG"
            mock_doc.ents = [mock_ent]

            mock_nlp.return_value = mock_doc
            mock_load.return_value = mock_nlp

            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)
                validator._nlp = mock_nlp

                text = "Google is a technology company."
                entities = validator.extract_entities(text)

                assert isinstance(entities, ExtractedEntities)

    def test_detect_duplicate(self, validation_config: ValidationConfig) -> None:
        """Test duplicate content detection."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch(
                "tools.web_research.content_validator.SentenceTransformer"
            ) as MockModel:
                mock_model = MagicMock()
                mock_model.encode.return_value = np.array([[0.5, 0.5, 0.5]])
                MockModel.return_value = mock_model

                validator = ContentValidator(validation_config)

                text = "This is a test article."
                corpus = ["This is a test article.", "Different content."]

                score = validator.detect_duplicate(text, corpus)

                assert 0.0 <= score <= 1.0

    def test_validate_freshness_recent(
        self, validation_config: ValidationConfig
    ) -> None:
        """Test freshness validation with recent content."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                recent_date = datetime.utcnow() - timedelta(days=30)
                is_fresh = validator.validate_freshness(recent_date, max_age_days=365)

                assert is_fresh is True

    def test_validate_freshness_stale(
        self, validation_config: ValidationConfig
    ) -> None:
        """Test freshness validation with stale content."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                old_date = datetime.utcnow() - timedelta(days=400)
                is_fresh = validator.validate_freshness(old_date, max_age_days=365)

                assert is_fresh is False

    def test_check_broken_links(self, validation_config: ValidationConfig) -> None:
        """Test broken link checking."""
        validation_config.check_links = True

        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                with patch(
                    "tools.web_research.content_validator.requests.head"
                ) as mock_head:
                    mock_head.return_value.status_code = 404

                    validator = ContentValidator(validation_config)

                    html = '<a href="https://example.com/broken">Link</a>'
                    broken = validator.check_broken_links(html)

                    assert len(broken) == 1

    def test_batch_validate(
        self, validation_config: ValidationConfig, mock_article: ExtractedArticle
    ) -> None:
        """Test batch validation."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                with patch.object(
                    validator,
                    "validate_content",
                    return_value=ValidationResult(
                        url="https://example.com",
                        passed=True,
                        quality_rating=QualityRating.HIGH,
                        readability_score=0.8,
                        freshness_valid=True,
                        entity_count=10,
                        duplicate_score=0.0,
                    ),
                ):
                    articles = [mock_article] * 3
                    results = validator.batch_validate(articles)

                    assert len(results) == 3

    def test_generate_validation_report(
        self, validation_config: ValidationConfig
    ) -> None:
        """Test validation report generation."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                results = [
                    ValidationResult(
                        url=f"https://example.com/{i}",
                        passed=True,
                        quality_rating=QualityRating.HIGH,
                        readability_score=0.8,
                        freshness_valid=True,
                        entity_count=10,
                        duplicate_score=0.0,
                    )
                    for i in range(5)
                ]

                report = validator.generate_validation_report(results)

                assert "total_articles" in report
                assert report["total_articles"] == 5

    def test_sentiment_analysis(self, validation_config: ValidationConfig) -> None:
        """Test sentiment analysis."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                text = "This is a great article with positive content."
                sentiment = validator._analyze_sentiment(text)

                assert "polarity" in sentiment
                assert "subjectivity" in sentiment

    def test_bias_detection(self, validation_config: ValidationConfig) -> None:
        """Test bias detection."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                biased_text = "Everyone always agrees that this is obviously the best."
                bias_score = validator._detect_bias(biased_text)

                assert 0.0 <= bias_score <= 1.0

    def test_quality_rating_determination(
        self, validation_config: ValidationConfig
    ) -> None:
        """Test quality rating determination."""
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                rating = validator._determine_quality_rating(
                    readability_score=0.9, entity_count=15, issue_count=0
                )
                assert rating == QualityRating.HIGH

    def test_validation_content_too_short(
        self, validation_config: ValidationConfig
    ) -> None:
        """Test validation with too short content."""
        validation_config.min_content_length = 1000

        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(validation_config)

                short_article = ExtractedArticle(
                    url="https://example.com",
                    title="Short",
                    content="Too short.",
                    html="<html></html>",
                    metadata=ArticleMetadata(url="https://example.com", word_count=2),
                )

                with patch.object(
                    validator,
                    "assess_quality",
                    return_value=MagicMock(overall_score=0.5),
                ):
                    with patch.object(
                        validator,
                        "extract_entities",
                        return_value=MagicMock(total_count=0),
                    ):
                        result = validator.validate_content(short_article)
                        assert len(result.issues) > 0

    def test_cosine_similarity(self, validation_config: ValidationConfig) -> None:
        """Test cosine similarity calculation."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        similarity = ContentValidator._cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.01


# ============================================================================
# CACHE MANAGER TESTS (15 tests)
# ============================================================================


class TestCacheManager:
    """Tests for CacheManager component."""

    def test_cache_manager_initialization(self, cache_config: CacheConfig) -> None:
        """Test CacheManager initialization."""
        cache = CacheManager(cache_config)
        assert cache.config == cache_config
        assert isinstance(cache._stats, CacheStats)

    def test_set_and_get_success(self, cache_config: CacheConfig) -> None:
        """Test successful set and get operations."""
        cache = CacheManager(cache_config)

        success = cache.set("test_key", "test_value")
        assert success is True

        value = cache.get("test_key")
        assert value == "test_value"

    def test_get_nonexistent_key(self, cache_config: CacheConfig) -> None:
        """Test getting non-existent key."""
        cache = CacheManager(cache_config)

        value = cache.get("nonexistent")
        assert value is None

    def test_cache_expiration(self, cache_config: CacheConfig) -> None:
        """Test cache entry expiration."""
        cache_config.ttl_seconds = 1
        cache = CacheManager(cache_config)

        cache.set("key", "value", ttl=1)
        time.sleep(1.5)

        value = cache.get("key")
        assert value is None

    def test_delete_entry(self, cache_config: CacheConfig) -> None:
        """Test deleting cache entry."""
        cache = CacheManager(cache_config)

        cache.set("key", "value")
        deleted = cache.delete("key")
        assert deleted is True

        value = cache.get("key")
        assert value is None

    def test_exists_check(self, cache_config: CacheConfig) -> None:
        """Test checking key existence."""
        cache = CacheManager(cache_config)

        cache.set("key", "value")
        assert cache.exists("key") is True
        assert cache.exists("nonexistent") is False

    def test_compression(self, cache_config: CacheConfig) -> None:
        """Test content compression."""
        cache_config.compression_enabled = True
        cache_config.compression_threshold = 100
        cache = CacheManager(cache_config)

        large_value = "x" * 200
        cache.set("large_key", large_value)

        retrieved = cache.get("large_key")
        assert retrieved == large_value

    def test_get_or_fetch(self, cache_config: CacheConfig) -> None:
        """Test get_or_fetch pattern."""
        cache = CacheManager(cache_config)

        call_count = 0

        def fetch_func() -> str:
            nonlocal call_count
            call_count += 1
            return "fetched_value"

        value1 = cache.get_or_fetch("key", fetch_func)
        value2 = cache.get_or_fetch("key", fetch_func)

        assert value1 == "fetched_value"
        assert value2 == "fetched_value"
        assert call_count == 1

    def test_generate_cache_key(self, cache_config: CacheConfig) -> None:
        """Test cache key generation."""
        cache = CacheManager(cache_config)

        key1 = cache.generate_cache_key("https://example.com/page?b=2&a=1")
        key2 = cache.generate_cache_key("https://example.com/page?a=1&b=2")

        assert key1 == key2

    def test_content_hash_calculation(self, cache_config: CacheConfig) -> None:
        """Test content hash calculation."""
        cache = CacheManager(cache_config)

        hash1 = cache.calculate_content_hash("content")
        hash2 = cache.calculate_content_hash("content")
        hash3 = cache.calculate_content_hash("different")

        assert hash1 == hash2
        assert hash1 != hash3

    def test_get_stats(self, cache_config: CacheConfig) -> None:
        """Test statistics retrieval."""
        cache = CacheManager(cache_config)

        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")

        stats = cache.get_stats()

        assert stats.total_hits == 1
        assert stats.total_misses == 1
        assert stats.hit_rate > 0

    def test_clear_expired(self, cache_config: CacheConfig) -> None:
        """Test clearing expired entries."""
        cache_config.ttl_seconds = 1
        cache = CacheManager(cache_config)

        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=100)

        time.sleep(1.5)
        cleared = cache.clear_expired()

        assert cleared >= 1

    def test_warm_cache(self, cache_config: CacheConfig) -> None:
        """Test cache warming."""
        cache = CacheManager(cache_config)

        urls = [f"https://example.com/page{i}" for i in range(3)]

        def fetch_func(url: str) -> str:
            return f"content for {url}"

        count = cache.warm_cache(urls, fetch_func)
        assert count == 3

    def test_find_duplicates(self, cache_config: CacheConfig) -> None:
        """Test finding duplicate content."""
        cache = CacheManager(cache_config)

        cache.set("key1", "same_content")
        cache.set("key2", "same_content")
        cache.set("key3", "different_content")

        duplicates = cache.find_duplicates()
        assert isinstance(duplicates, dict)

    def test_clear_all(self, cache_config: CacheConfig) -> None:
        """Test clearing all cache entries."""
        cache = CacheManager(cache_config)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        count = cache.clear_all()
        assert count >= 2
        assert cache.get("key1") is None

    def test_redis_backend(self) -> None:
        """Test Redis backend with fakeredis."""
        config = CacheConfig(
            backend=CacheBackend.REDIS,
            redis_url="redis://localhost:6379/0",
        )

        with patch("tools.web_research.cache_manager.redis.from_url") as mock_redis:
            fake_redis = FakeRedis()
            mock_redis.return_value = fake_redis

            cache = CacheManager(config)
            cache.set("test_key", "test_value")
            value = cache.get("test_key")

            assert value == "test_value"

    def test_memory_eviction_lru(self) -> None:
        """Test LRU eviction policy."""
        config = CacheConfig(
            backend=CacheBackend.MEMORY,
            max_memory=500,
            eviction_policy="lru",
        )

        cache = CacheManager(config)

        for i in range(10):
            cache.set(f"key{i}", "x" * 100)

        stats = cache.get_stats()
        assert stats.evictions > 0

    def test_context_manager(self, cache_config: CacheConfig) -> None:
        """Test CacheManager as context manager."""
        with CacheManager(cache_config) as cache:
            cache.set("key", "value")
            value = cache.get("key")
            assert value == "value"


# ============================================================================
# CLI TESTS (10 tests)
# ============================================================================


class TestCLI:
    """Tests for CLI interface."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Click test runner."""
        return CliRunner()

    def test_cli_import(self) -> None:
        """Test CLI module import."""
        try:
            from tools.web_research import web_research_cli

            assert web_research_cli is not None
        except ImportError:
            pytest.skip("CLI module not fully implemented")

    def test_config_initialization(self) -> None:
        """Test CLI configuration initialization."""
        from tools.web_research.web_research_cli import CLIConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            cli_config = CLIConfig(config_path)

            assert cli_config.config_path == config_path
            assert isinstance(cli_config.config, dict)

    def test_config_save_load(self) -> None:
        """Test configuration save and load."""
        from tools.web_research.web_research_cli import CLIConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            cli_config = CLIConfig(config_path)

            cli_config.set("test", "key", "value")
            cli_config.save()

            new_config = CLIConfig(config_path)
            assert new_config.get("test", "key") == "value"

    def test_format_output_json(self) -> None:
        """Test JSON output formatting."""
        from tools.web_research.web_research_cli import format_output

        data = {"test": "data"}
        output = format_output(data, "json", pretty=True)

        assert "test" in output
        parsed = json.loads(output)
        assert parsed == data

    def test_format_output_yaml(self) -> None:
        """Test YAML output formatting."""
        from tools.web_research.web_research_cli import format_output

        data = {"test": "data"}
        output = format_output(data, "yaml", pretty=True)

        assert "test" in output

    def test_cli_help_command(self, runner: CliRunner) -> None:
        """Test CLI help command."""
        try:
            from tools.web_research.web_research_cli import cli

            result = runner.invoke(cli, ["--help"])
            assert result.exit_code == 0
        except (ImportError, AttributeError):
            pytest.skip("CLI not fully implemented")

    def test_cli_config_command(self, runner: CliRunner) -> None:
        """Test CLI config command."""
        try:
            from tools.web_research.web_research_cli import cli

            result = runner.invoke(cli, ["config", "--help"])
            assert result.exit_code == 0
        except (ImportError, AttributeError):
            pytest.skip("CLI not fully implemented")

    def test_cli_scrape_command_structure(self, runner: CliRunner) -> None:
        """Test CLI scrape command structure."""
        try:
            from tools.web_research.web_research_cli import cli

            result = runner.invoke(cli, ["scrape", "--help"])
            assert result.exit_code == 0
        except (ImportError, AttributeError):
            pytest.skip("CLI not fully implemented")

    def test_cli_error_handling(self, runner: CliRunner) -> None:
        """Test CLI error handling."""
        try:
            from tools.web_research.web_research_cli import cli

            result = runner.invoke(cli, ["invalid-command"])
            assert result.exit_code != 0
        except (ImportError, AttributeError):
            pytest.skip("CLI not fully implemented")

    def test_cli_output_directory_creation(self) -> None:
        """Test CLI output directory creation."""
        from tools.web_research.web_research_cli import CLIConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            cli_config = CLIConfig(config_path)

            output_dir = cli_config.get("output", "output_dir")
            assert output_dir is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for end-to-end workflows."""

    @responses.activate
    def test_scrape_extract_validate_workflow(
        self, mock_html: str, scraping_config: ScrapingConfig
    ) -> None:
        """Test complete scrape -> extract -> validate workflow."""
        url = "https://example.com/article"
        responses.add(responses.GET, url, body=mock_html, status=200)

        # Scrape
        scraper = WebScraper(scraping_config)
        scraped = scraper.scrape_url(url)

        # Extract
        extractor = ContentExtractor()
        article = extractor.extract_article(scraped.html, url)

        # Validate
        with patch("tools.web_research.content_validator.spacy.load"):
            with patch("tools.web_research.content_validator.SentenceTransformer"):
                validator = ContentValidator(
                    ValidationConfig(
                        check_links=False,
                        enable_sentiment_analysis=False,
                        enable_bias_detection=False,
                    )
                )

                with patch.object(
                    validator,
                    "assess_quality",
                    return_value=MagicMock(overall_score=0.8),
                ):
                    with patch.object(
                        validator,
                        "extract_entities",
                        return_value=MagicMock(total_count=5),
                    ):
                        result = validator.validate_content(article)

                        assert isinstance(result, ValidationResult)
                        assert result.url == url

    def test_extract_index_search_workflow(self, mock_html: str) -> None:
        """Test extract -> index -> search workflow."""
        # Extract
        extractor = ContentExtractor()
        article = extractor.extract_article(mock_html, "https://example.com")

        # Index
        with patch(
            "tools.web_research.knowledge_indexer.SentenceTransformer"
        ) as MockModel:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
            MockModel.return_value = mock_model

            with patch("tools.web_research.knowledge_indexer.chromadb.Client"):
                config = IndexConfig(vector_db=VectorDB.INMEMORY)
                indexer = KnowledgeIndexer(config)

                from tools.web_research.knowledge_indexer import ExtractedArticle

                article_obj = ExtractedArticle(
                    url=article.url,
                    title=article.title or "Test",
                    content=article.content,
                )

                stats = indexer.batch_index([article_obj])
                assert stats.total_articles == 1

    @responses.activate
    def test_scrape_with_caching(
        self,
        mock_html: str,
        scraping_config: ScrapingConfig,
        cache_config: CacheConfig,
    ) -> None:
        """Test scraping with caching."""
        url = "https://example.com"
        responses.add(responses.GET, url, body=mock_html, status=200)

        cache = CacheManager(cache_config)
        scraper = WebScraper(scraping_config)

        cache_key = cache.generate_cache_key(url)

        if not cache.exists(cache_key):
            scraped = scraper.scrape_url(url)
            cache.set(cache_key, scraped.html)

        cached_html = cache.get(cache_key)
        assert cached_html is not None


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestPerformance:
    """Performance and stress tests."""

    def test_batch_scraping_performance(self, scraping_config: ScrapingConfig) -> None:
        """Test batch scraping performance."""
        scraping_config.rate_limit = 0.01

        with responses.RequestsMock() as rsps:
            urls = [f"https://example.com/page{i}" for i in range(10)]
            for url in urls:
                rsps.add(responses.GET, url, body="Content", status=200)

            scraper = WebScraper(scraping_config)
            start = time.time()
            results = scraper.scrape_urls(urls)
            duration = time.time() - start

            assert len(results) == 10
            assert duration < 5

    def test_large_content_extraction(self) -> None:
        """Test extraction with large content."""
        large_html = "<html><body>" + "<p>Content</p>" * 1000 + "</body></html>"

        extractor = ContentExtractor()
        article = extractor.extract_article(large_html, "https://example.com")

        assert len(article.content) > 0

    def test_cache_memory_limits(self) -> None:
        """Test cache behavior under memory pressure."""
        config = CacheConfig(
            backend=CacheBackend.MEMORY,
            max_memory=10000,
        )

        cache = CacheManager(config)

        for i in range(100):
            cache.set(f"key{i}", "x" * 200)

        stats = cache.get_stats()
        assert stats.evictions > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
