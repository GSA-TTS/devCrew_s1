"""
Web Research & Content Extraction Platform.

Multi-functional web research platform enabling web scraping, content extraction,
knowledge base population, and content validation. Supports automated technology
discovery, RAG system population, and content quality assurance workflows.
"""

__version__ = "1.0.0"
__author__ = "devCrew_s1"

from .web_scraper import WebScraper, ScrapingConfig, ScrapedContent
from .browser_automation import BrowserAutomation, RenderConfig, RenderedPage
from .content_extractor import (
    ContentExtractor,
    ExtractedArticle,
    ArticleMetadata,
)
from .knowledge_indexer import (
    KnowledgeIndexer,
    VectorDB,
    SemanticSearchResult,
)
from .content_validator import (
    ContentValidator,
    ValidationResult,
    QualityRating,
)
from .cache_manager import CacheManager, CacheConfig, CacheStats

__all__ = [
    "WebScraper",
    "ScrapingConfig",
    "ScrapedContent",
    "BrowserAutomation",
    "RenderConfig",
    "RenderedPage",
    "ContentExtractor",
    "ExtractedArticle",
    "ArticleMetadata",
    "KnowledgeIndexer",
    "VectorDB",
    "SemanticSearchResult",
    "ContentValidator",
    "ValidationResult",
    "QualityRating",
    "CacheManager",
    "CacheConfig",
    "CacheStats",
]
