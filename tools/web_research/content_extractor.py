"""
Content Extractor for Web Research Platform.

This module provides comprehensive content extraction capabilities using
Trafilatura and Readability-lxml, with support for metadata extraction,
language detection, readability scoring, and structured data extraction.
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

import trafilatura
from bs4 import BeautifulSoup
from langdetect import LangDetectException, detect, detect_langs
from pydantic import BaseModel, Field, validator
from readability import Document
from readability.readability import Unparseable


class ExtractionError(Exception):
    """Base exception for extraction errors."""

    pass


class LanguageDetectionError(ExtractionError):
    """Exception raised when language detection fails."""

    pass


class MetadataExtractionError(ExtractionError):
    """Exception raised when metadata extraction fails."""

    pass


class ExtractionConfig(BaseModel):
    """Configuration for content extraction.

    Attributes:
        include_images: Whether to extract image URLs and alt text
        include_links: Whether to preserve links in extracted content
        target_language: Preferred language for content (None = any)
        min_text_length: Minimum text length to consider valid extraction
        extract_comments: Whether to extract comments from article
        date_format: Format string for date output
        favor_precision: Prefer precision over recall in extraction
        favor_recall: Prefer recall over precision in extraction
        include_tables: Whether to preserve tables in extracted content
        include_formatting: Whether to preserve text formatting
    """

    include_images: bool = Field(default=True, description="Extract images")
    include_links: bool = Field(default=True, description="Preserve links")
    target_language: Optional[str] = Field(
        default=None, description="Target language code"
    )
    min_text_length: int = Field(default=100, description="Minimum text length", ge=0)
    extract_comments: bool = Field(default=False, description="Extract comments")
    date_format: str = Field(default="%Y-%m-%d", description="Date format string")
    favor_precision: bool = Field(
        default=True, description="Favor precision over recall"
    )
    favor_recall: bool = Field(default=False, description="Favor recall over precision")
    include_tables: bool = Field(default=True, description="Include tables")
    include_formatting: bool = Field(default=True, description="Include formatting")

    @validator("target_language")
    def validate_language_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate language code format."""
        if v is not None and len(v) != 2:
            raise ValueError("Language code must be 2 characters (ISO 639-1)")
        return v.lower() if v else None


class ArticleMetadata(BaseModel):
    """Metadata structure for extracted articles.

    Attributes:
        title: Article title
        author: Article author(s)
        publish_date: Publication date
        modified_date: Last modification date
        description: Article description/summary
        keywords: Article keywords/tags
        site_name: Name of the publishing site
        canonical_url: Canonical URL of the article
        image_url: Main article image URL
        language: Article language code
    """

    title: Optional[str] = Field(default=None, description="Article title")
    author: Optional[List[str]] = Field(default=None, description="Article authors")
    publish_date: Optional[datetime] = Field(
        default=None, description="Publication date"
    )
    modified_date: Optional[datetime] = Field(
        default=None, description="Modification date"
    )
    description: Optional[str] = Field(default=None, description="Article description")
    keywords: Optional[List[str]] = Field(default=None, description="Article keywords")
    site_name: Optional[str] = Field(default=None, description="Site name")
    canonical_url: Optional[str] = Field(default=None, description="Canonical URL")
    image_url: Optional[str] = Field(default=None, description="Main image URL")
    language: Optional[str] = Field(default=None, description="Language code")


class ExtractedArticle(BaseModel):
    """Complete article data structure.

    Attributes:
        url: Source URL of the article
        title: Article title
        content: Main article content
        author: Article author(s)
        publish_date: Publication date
        description: Article description
        language: Detected language code
        readability_score: Readability score (0-100)
        word_count: Number of words in content
        tags: Article tags/keywords
        structured_data: Extracted structured data (JSON-LD, microdata)
        extraction_method: Method used for extraction
        metadata: Complete metadata object
        images: List of extracted images
        links: List of extracted links
        extracted_at: Timestamp of extraction
    """

    url: str = Field(..., description="Source URL")
    title: Optional[str] = Field(default=None, description="Article title")
    content: str = Field(..., description="Main content")
    author: Optional[List[str]] = Field(default=None, description="Authors")
    publish_date: Optional[datetime] = Field(
        default=None, description="Publication date"
    )
    description: Optional[str] = Field(default=None, description="Article description")
    language: Optional[str] = Field(default=None, description="Language code")
    readability_score: Optional[float] = Field(
        default=None, description="Readability score", ge=0, le=100
    )
    word_count: int = Field(default=0, description="Word count", ge=0)
    tags: Optional[List[str]] = Field(default=None, description="Article tags")
    structured_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Structured data"
    )
    extraction_method: str = Field(
        default="trafilatura", description="Extraction method"
    )
    metadata: Optional[ArticleMetadata] = Field(
        default=None, description="Complete metadata"
    )
    images: Optional[List[Dict[str, str]]] = Field(
        default=None, description="Extracted images"
    )
    links: Optional[List[Dict[str, str]]] = Field(
        default=None, description="Extracted links"
    )
    extracted_at: datetime = Field(
        default_factory=datetime.utcnow, description="Extraction timestamp"
    )


class ContentExtractor:
    """Content extractor using Trafilatura and Readability-lxml.

    This class provides comprehensive content extraction capabilities including
    main content detection, metadata extraction, readability scoring, language
    detection, and structured data extraction.
    """

    def __init__(self, config: Optional[ExtractionConfig] = None) -> None:
        """Initialize the content extractor.

        Args:
            config: Extraction configuration. If None, uses default config.
        """
        self.config = config or ExtractionConfig()
        self._date_patterns = self._compile_date_patterns()

    def _compile_date_patterns(self) -> List[re.Pattern]:
        """Compile regular expressions for date extraction.

        Returns:
            List of compiled regex patterns for date detection.
        """
        patterns = [
            # ISO 8601: 2024-01-15
            r"\b(\d{4})-(\d{2})-(\d{2})\b",
            # US format: 01/15/2024
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
            # European format: 15.01.2024
            r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b",
            # Month Day, Year: January 15, 2024
            r"\b([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})\b",
            # Day Month Year: 15 January 2024
            r"\b(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})\b",
        ]
        return [re.compile(pattern) for pattern in patterns]

    def extract_article(self, html: str, url: str) -> ExtractedArticle:
        """Extract article content and metadata from HTML.

        This is the main extraction method that orchestrates all extraction
        operations and returns a complete ExtractedArticle object.

        Args:
            html: Raw HTML content
            url: Source URL of the article

        Returns:
            ExtractedArticle object with all extracted data

        Raises:
            ExtractionError: If extraction fails completely
        """
        if not html or not html.strip():
            raise ExtractionError("Empty HTML content provided")

        try:
            # Primary extraction using Trafilatura
            content = self._extract_with_trafilatura(html, url)
            extraction_method = "trafilatura"

            # Fallback to Readability if Trafilatura fails
            if not content or len(content) < self.config.min_text_length:
                content = self._extract_with_readability(html)
                extraction_method = "readability"

            # Final fallback to basic extraction
            if not content or len(content) < self.config.min_text_length:
                content = self._extract_basic(html)
                extraction_method = "basic"

            # Validate extracted content
            if not content or len(content) < self.config.min_text_length:
                raise ExtractionError(
                    f"Extracted content too short: {len(content)} chars"
                )

            # Clean and normalize text
            content = self.clean_text(content)

            # Extract metadata
            try:
                metadata = self.extract_metadata(html)
            except MetadataExtractionError:
                metadata = ArticleMetadata()

            # Detect language
            try:
                language = self.detect_language(content)
            except LanguageDetectionError:
                language = None

            # Calculate readability
            try:
                readability_score = self.calculate_readability(content)
            except Exception:
                readability_score = None

            # Extract structured data
            try:
                structured_data = self.extract_structured_data(html)
            except Exception:
                structured_data = None

            # Extract images if configured
            images = None
            if self.config.include_images:
                try:
                    images = self.extract_images(html, url)
                except Exception:
                    images = None

            # Extract links if configured
            links = None
            if self.config.include_links:
                try:
                    links = self.extract_links(html, url)
                except Exception:
                    links = None

            # Calculate word count
            word_count = len(content.split())

            # Build article object
            article = ExtractedArticle(
                url=url,
                title=metadata.title,
                content=content,
                author=metadata.author,
                publish_date=metadata.publish_date,
                description=metadata.description,
                language=language or metadata.language,
                readability_score=readability_score,
                word_count=word_count,
                tags=metadata.keywords,
                structured_data=structured_data,
                extraction_method=extraction_method,
                metadata=metadata,
                images=images,
                links=links,
            )

            return article

        except Exception as e:
            raise ExtractionError(f"Failed to extract article: {str(e)}") from e

    def _extract_with_trafilatura(self, html: str, url: str) -> Optional[str]:
        """Extract content using Trafilatura.

        Args:
            html: Raw HTML content
            url: Source URL for context

        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            extracted = trafilatura.extract(
                html,
                url=url,
                include_comments=self.config.extract_comments,
                include_tables=self.config.include_tables,
                include_images=self.config.include_images,
                include_links=self.config.include_links,
                favor_precision=self.config.favor_precision,
                favor_recall=self.config.favor_recall,
                output_format="txt",
            )
            return extracted
        except Exception:
            return None

    def _extract_with_readability(self, html: str) -> Optional[str]:
        """Extract content using Readability-lxml.

        Args:
            html: Raw HTML content

        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            doc = Document(html)
            content_html = doc.summary(html_partial=True)
            soup = BeautifulSoup(content_html, "html.parser")
            return soup.get_text(separator="\n", strip=True)
        except (Unparseable, Exception):
            return None

    def _extract_basic(self, html: str) -> Optional[str]:
        """Basic content extraction using BeautifulSoup.

        This is a fallback method that extracts text from common content
        containers when other methods fail.

        Args:
            html: Raw HTML content

        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for element in soup(
                ["script", "style", "nav", "header", "footer", "aside"]
            ):
                element.decompose()

            # Try to find main content containers
            content_selectors = [
                "article",
                '[role="main"]',
                "main",
                ".article-content",
                ".post-content",
                ".entry-content",
                "#content",
            ]

            for selector in content_selectors:
                container = soup.select_one(selector)
                if container:
                    return container.get_text(separator="\n", strip=True)

            # Fallback to body text
            body = soup.find("body")
            if body:
                return body.get_text(separator="\n", strip=True)

            return None

        except Exception:
            return None

    def extract_metadata(self, html: str) -> ArticleMetadata:
        """Extract all metadata from HTML.

        Args:
            html: Raw HTML content

        Returns:
            ArticleMetadata object with extracted metadata

        Raises:
            MetadataExtractionError: If critical metadata extraction fails
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            metadata = ArticleMetadata(
                title=self._extract_title(soup),
                author=self._extract_authors(soup),
                publish_date=self._extract_publish_date(soup),
                modified_date=self._extract_modified_date(soup),
                description=self._extract_description(soup),
                keywords=self._extract_keywords(soup),
                site_name=self._extract_site_name(soup),
                canonical_url=self._extract_canonical_url(soup),
                image_url=self._extract_main_image(soup),
                language=self._extract_language_meta(soup),
            )

            return metadata

        except Exception as e:
            raise MetadataExtractionError(
                f"Failed to extract metadata: {str(e)}"
            ) from e

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted title or None
        """
        # Try Open Graph
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Try Twitter Card
        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        if twitter_title and twitter_title.get("content"):
            return twitter_title["content"].strip()

        # Try standard title tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        return None

    def _extract_authors(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract article authors from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of author names or None
        """
        authors = []

        # Try meta author tag
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            authors.append(meta_author["content"].strip())

        # Try article:author
        article_author = soup.find("meta", property="article:author")
        if article_author and article_author.get("content"):
            authors.append(article_author["content"].strip())

        # Try rel=author links
        author_links = soup.find_all("a", rel="author")
        for link in author_links:
            if link.get_text(strip=True):
                authors.append(link.get_text(strip=True))

        # Try common author classes
        author_elements = soup.find_all(
            class_=re.compile(r"author|byline", re.IGNORECASE)
        )
        for element in author_elements:
            text = element.get_text(strip=True)
            if text and len(text) < 100:  # Sanity check
                authors.append(text)

        # Deduplicate while preserving order
        seen = set()
        unique_authors = []
        for author in authors:
            if author not in seen:
                seen.add(author)
                unique_authors.append(author)

        return unique_authors if unique_authors else None

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publication date from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Publication datetime or None
        """
        # Try article:published_time
        published_time = soup.find("meta", property="article:published_time")
        if published_time and published_time.get("content"):
            date = self._parse_date(published_time["content"])
            if date:
                return date

        # Try datePublished schema.org
        date_published = soup.find("meta", attrs={"itemprop": "datePublished"})
        if date_published and date_published.get("content"):
            date = self._parse_date(date_published["content"])
            if date:
                return date

        # Try time tags with datetime attribute
        time_tag = soup.find("time", attrs={"datetime": True})
        if time_tag:
            date = self._parse_date(time_tag["datetime"])
            if date:
                return date

        return None

    def _extract_modified_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract last modified date from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Modified datetime or None
        """
        # Try article:modified_time
        modified_time = soup.find("meta", property="article:modified_time")
        if modified_time and modified_time.get("content"):
            date = self._parse_date(modified_time["content"])
            if date:
                return date

        # Try dateModified schema.org
        date_modified = soup.find("meta", attrs={"itemprop": "dateModified"})
        if date_modified and date_modified.get("content"):
            date = self._parse_date(date_modified["content"])
            if date:
                return date

        return None

    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string into datetime object.

        Args:
            date_string: Date string to parse

        Returns:
            Parsed datetime or None
        """
        if not date_string:
            return None

        # Common date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%d %B %Y",
            "%b %d, %Y",
            "%d %b %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string.strip(), fmt)
            except ValueError:
                continue

        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article description from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Description text or None
        """
        # Try Open Graph
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"].strip()

        # Try Twitter Card
        twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
        if twitter_desc and twitter_desc.get("content"):
            return twitter_desc["content"].strip()

        # Try standard meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"].strip()

        return None

    def _extract_keywords(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract article keywords from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of keywords or None
        """
        keywords = []

        # Try meta keywords
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            kw_list = [
                kw.strip() for kw in meta_keywords["content"].split(",") if kw.strip()
            ]
            keywords.extend(kw_list)

        # Try article:tag
        article_tags = soup.find_all("meta", property="article:tag")
        for tag in article_tags:
            if tag.get("content"):
                keywords.append(tag["content"].strip())

        return keywords if keywords else None

    def _extract_site_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract site name from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Site name or None
        """
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            return og_site["content"].strip()

        return None

    def _extract_canonical_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract canonical URL from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Canonical URL or None
        """
        # Try link rel=canonical
        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            return canonical["href"].strip()

        # Try og:url
        og_url = soup.find("meta", property="og:url")
        if og_url and og_url.get("content"):
            return og_url["content"].strip()

        return None

    def _extract_main_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main article image URL from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Image URL or None
        """
        # Try Open Graph
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"].strip()

        # Try Twitter Card
        twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter_image and twitter_image.get("content"):
            return twitter_image["content"].strip()

        return None

    def _extract_language_meta(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract language from HTML metadata.

        Args:
            soup: BeautifulSoup object

        Returns:
            Language code or None
        """
        # Try html lang attribute
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            lang = html_tag["lang"].strip().lower()
            return lang[:2] if len(lang) >= 2 else None

        # Try meta content-language
        meta_lang = soup.find("meta", attrs={"http-equiv": "content-language"})
        if meta_lang and meta_lang.get("content"):
            lang = meta_lang["content"].strip().lower()
            return lang[:2] if len(lang) >= 2 else None

        return None

    def calculate_readability(self, text: str) -> float:
        """Calculate readability score for text.

        Uses Flesch Reading Ease formula. Score ranges from 0 (very difficult)
        to 100 (very easy).

        Args:
            text: Text to analyze

        Returns:
            Readability score (0-100)
        """
        if not text or not text.strip():
            return 0.0

        # Clean text
        text = self.clean_text(text)

        # Count sentences
        sentence_endings = re.findall(r"[.!?]+", text)
        num_sentences = max(len(sentence_endings), 1)

        # Count words
        words = text.split()
        num_words = len(words)

        if num_words == 0:
            return 0.0

        # Count syllables
        num_syllables = sum(self._count_syllables(word) for word in words)

        # Flesch Reading Ease formula
        avg_words_per_sentence = num_words / num_sentences
        avg_syllables_per_word = num_syllables / num_words

        score = (
            206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
        )

        # Clamp score between 0 and 100
        return max(0.0, min(100.0, score))

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word.

        Args:
            word: Word to analyze

        Returns:
            Number of syllables
        """
        word = word.lower().strip()
        if len(word) <= 3:
            return 1

        # Remove non-alphabetic characters
        word = re.sub(r"[^a-z]", "", word)

        # Count vowel groups
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent 'e'
        if word.endswith("e"):
            syllable_count -= 1

        # Ensure at least one syllable
        return max(1, syllable_count)

    def detect_language(self, text: str) -> str:
        """Detect language of text content.

        Args:
            text: Text to analyze

        Returns:
            ISO 639-1 language code (e.g., 'en', 'es', 'fr')

        Raises:
            LanguageDetectionError: If language detection fails
        """
        if not text or len(text.strip()) < 10:
            raise LanguageDetectionError("Text too short for language detection")

        try:
            # Use first 1000 characters for detection (performance)
            sample = text[:1000]
            lang_code = detect(sample)
            return lang_code

        except LangDetectException as e:
            raise LanguageDetectionError(f"Language detection failed: {str(e)}") from e

    def detect_language_with_confidence(
        self, text: str
    ) -> List[Dict[str, Union[str, float]]]:
        """Detect language with confidence scores.

        Args:
            text: Text to analyze

        Returns:
            List of dictionaries with 'lang' and 'prob' keys

        Raises:
            LanguageDetectionError: If language detection fails
        """
        if not text or len(text.strip()) < 10:
            raise LanguageDetectionError("Text too short for language detection")

        try:
            sample = text[:1000]
            langs = detect_langs(sample)
            return [{"lang": lang.lang, "prob": lang.prob} for lang in langs]

        except LangDetectException as e:
            raise LanguageDetectionError(f"Language detection failed: {str(e)}") from e

    def extract_structured_data(self, html: str) -> Dict[str, Any]:
        """Extract structured data from HTML.

        Extracts JSON-LD, microdata, and other structured data formats.

        Args:
            html: Raw HTML content

        Returns:
            Dictionary containing structured data
        """
        soup = BeautifulSoup(html, "html.parser")
        structured = {"json_ld": [], "microdata": {}, "rdfa": {}}

        # Extract JSON-LD
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured["json_ld"].append(data)
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue

        # Extract microdata
        microdata_items = soup.find_all(attrs={"itemscope": True})
        for item in microdata_items:
            item_type = item.get("itemtype", "unknown")
            properties = {}

            for prop in item.find_all(attrs={"itemprop": True}):
                prop_name = prop.get("itemprop")
                prop_value = (
                    prop.get("content") or prop.get("href") or prop.get_text(strip=True)
                )
                properties[prop_name] = prop_value

            if properties:
                structured["microdata"][item_type] = properties

        return structured

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove excessive newlines (more than 2)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        # Remove control characters except newlines and tabs
        text = "".join(char for char in text if char.isprintable() or char in "\n\t")

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def extract_to_markdown(self, html: str, url: str) -> str:
        """Extract content and convert to markdown format.

        Args:
            html: Raw HTML content
            url: Source URL

        Returns:
            Content in markdown format
        """
        try:
            markdown = trafilatura.extract(
                html,
                url=url,
                include_comments=self.config.extract_comments,
                include_tables=self.config.include_tables,
                include_images=self.config.include_images,
                include_links=self.config.include_links,
                output_format="markdown",
            )
            return markdown or ""
        except Exception:
            return ""

    def extract_images(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract image URLs and alt text from HTML.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative URLs

        Returns:
            List of dictionaries with 'url' and 'alt' keys
        """
        soup = BeautifulSoup(html, "html.parser")
        images = []

        img_tags = soup.find_all("img")
        for img in img_tags:
            src = img.get("src") or img.get("data-src")
            if not src:
                continue

            # Resolve relative URLs
            full_url = urljoin(base_url, src)

            # Get alt text
            alt = img.get("alt", "").strip()

            images.append({"url": full_url, "alt": alt})

        return images

    def extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract links from HTML.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative URLs

        Returns:
            List of dictionaries with 'url' and 'text' keys
        """
        soup = BeautifulSoup(html, "html.parser")
        links = []

        # Find all anchor tags
        a_tags = soup.find_all("a", href=True)
        for a in a_tags:
            href = a["href"]

            # Skip anchor links and javascript
            if href.startswith("#") or href.startswith("javascript:"):
                continue

            # Resolve relative URLs
            full_url = urljoin(base_url, href)

            # Get link text
            text = a.get_text(strip=True)

            # Only include links with text
            if text:
                links.append({"url": full_url, "text": text})

        return links

    def extract_article_to_dict(self, html: str, url: str) -> Dict[str, Any]:
        """Extract article and return as dictionary.

        Convenience method for serialization.

        Args:
            html: Raw HTML content
            url: Source URL

        Returns:
            Dictionary representation of ExtractedArticle
        """
        article = self.extract_article(html, url)
        return article.dict()

    def extract_article_to_json(self, html: str, url: str) -> str:
        """Extract article and return as JSON string.

        Args:
            html: Raw HTML content
            url: Source URL

        Returns:
            JSON string representation of ExtractedArticle
        """
        article = self.extract_article(html, url)
        return article.json(indent=2, ensure_ascii=False)

    def validate_extraction(self, article: ExtractedArticle) -> bool:
        """Validate extracted article meets quality criteria.

        Args:
            article: Extracted article to validate

        Returns:
            True if article meets quality criteria, False otherwise
        """
        # Check minimum content length
        if len(article.content) < self.config.min_text_length:
            return False

        # Check language if target specified
        if (
            self.config.target_language
            and article.language != self.config.target_language
        ):
            return False

        # Check if content has reasonable structure
        if article.word_count < 50:
            return False

        return True

    def get_extraction_stats(self, article: ExtractedArticle) -> Dict[str, Any]:
        """Get statistics about extracted article.

        Args:
            article: Extracted article

        Returns:
            Dictionary with extraction statistics
        """
        return {
            "word_count": article.word_count,
            "character_count": len(article.content),
            "readability_score": article.readability_score,
            "language": article.language,
            "has_author": article.author is not None,
            "has_date": article.publish_date is not None,
            "has_images": bool(article.images),
            "image_count": len(article.images) if article.images else 0,
            "has_links": bool(article.links),
            "link_count": len(article.links) if article.links else 0,
            "extraction_method": article.extraction_method,
            "has_structured_data": bool(article.structured_data),
        }
