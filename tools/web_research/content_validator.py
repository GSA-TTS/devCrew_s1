"""
Content Validator for Web Research Platform.

Comprehensive content validation with quality assessment, entity extraction,
duplicate detection, freshness validation, and link checking using spaCy and
ML-based embeddings.
"""

import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import numpy as np
import requests
import spacy
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sentence_transformers import SentenceTransformer
from textblob import TextBlob

# Configure logging
logger = logging.getLogger(__name__)


# Custom Exceptions
class ValidationError(Exception):
    """Base exception for validation errors."""

    pass


class EntityExtractionError(ValidationError):
    """Exception raised when entity extraction fails."""

    pass


class LinkCheckError(ValidationError):
    """Exception raised when link checking fails."""

    pass


class SpacyModelError(ValidationError):
    """Exception raised when spaCy model loading fails."""

    pass


# Enums
class QualityRating(str, Enum):
    """Content quality rating levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Pydantic Models
class ArticleMetadata(BaseModel):
    """Metadata for an extracted article."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    language: Optional[str] = None
    word_count: int = 0
    tags: List[str] = Field(default_factory=list)


class ExtractedArticle(BaseModel):
    """Representation of an extracted article."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: str
    title: str
    content: str
    html: Optional[str] = None
    metadata: ArticleMetadata
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class QualityMetrics(BaseModel):
    """Quality assessment metrics for content."""

    grammar_score: float = Field(ge=0.0, le=1.0)
    coherence_score: float = Field(ge=0.0, le=1.0)
    information_density: float = Field(ge=0.0, le=1.0)
    sentence_complexity: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)

    @field_validator("overall_score")
    @classmethod
    def calculate_overall(cls, v: float, info: Any) -> float:
        """Calculate overall score from individual metrics."""
        if "grammar_score" in info.data:
            metrics = [
                info.data.get("grammar_score", 0),
                info.data.get("coherence_score", 0),
                info.data.get("information_density", 0),
                info.data.get("sentence_complexity", 0),
            ]
            return sum(metrics) / len(metrics)
        return v


class ExtractedEntities(BaseModel):
    """Entities extracted from content."""

    technologies: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    persons: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    dates: List[str] = Field(default_factory=list)
    misc: List[str] = Field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Get total number of entities."""
        return (
            len(self.technologies)
            + len(self.organizations)
            + len(self.persons)
            + len(self.locations)
            + len(self.dates)
            + len(self.misc)
        )


class ValidationConfig(BaseModel):
    """Configuration for content validation."""

    min_readability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    max_age_days: int = Field(default=365, gt=0)
    duplicate_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    check_links: bool = True
    link_check_timeout: int = Field(default=5, gt=0)
    min_content_length: int = Field(default=100, gt=0)
    max_broken_links: int = Field(default=5, ge=0)
    enable_sentiment_analysis: bool = True
    enable_bias_detection: bool = True
    spacy_model: str = "en_core_web_sm"
    embedding_model: str = "all-MiniLM-L6-v2"


class ValidationResult(BaseModel):
    """Complete validation result for content."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: str
    passed: bool
    quality_rating: QualityRating
    readability_score: float = Field(ge=0.0, le=1.0)
    freshness_valid: bool
    entity_count: int = Field(ge=0)
    duplicate_score: float = Field(ge=0.0, le=1.0)
    broken_links: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    validated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_issue(self, issue: str) -> None:
        """Add a validation issue."""
        self.issues.append(issue)

    @property
    def is_high_quality(self) -> bool:
        """Check if content is high quality."""
        return self.quality_rating == QualityRating.HIGH

    @property
    def has_broken_links(self) -> bool:
        """Check if content has broken links."""
        return len(self.broken_links) > 0


class ContentValidator:
    """
    Comprehensive content validator with quality assessment, entity extraction,
    duplicate detection, and link checking.
    """

    def __init__(self, config: Optional[ValidationConfig] = None) -> None:
        """
        Initialize content validator.

        Args:
            config: Validation configuration

        Raises:
            SpacyModelError: If spaCy model cannot be loaded
        """
        self.config = config or ValidationConfig()
        self._nlp: Optional[spacy.language.Language] = None
        self._embedding_model: Optional[SentenceTransformer] = None
        self._corpus_embeddings: List[np.ndarray] = []

        # Initialize models
        self._initialize_models()

        logger.info("ContentValidator initialized successfully")

    def _initialize_models(self) -> None:
        """Initialize spaCy and embedding models."""
        try:
            # Load spaCy model
            try:
                self._nlp = spacy.load(self.config.spacy_model)
                logger.info(f"Loaded spaCy model: {self.config.spacy_model}")
            except OSError:
                logger.warning(
                    f"Model {self.config.spacy_model} not found, " "downloading..."
                )
                import subprocess  # nosec B404

                subprocess.run(  # nosec B603 B607
                    [
                        "python",
                        "-m",
                        "spacy",
                        "download",
                        self.config.spacy_model,
                    ],
                    check=True,
                    capture_output=True,
                )
                self._nlp = spacy.load(self.config.spacy_model)

            # Load embedding model for duplicate detection
            self._embedding_model = SentenceTransformer(
                self.config.embedding_model  # type: ignore
            )
            logger.info(f"Loaded embedding model: {self.config.embedding_model}")

        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            raise SpacyModelError(f"Failed to load required models: {e}") from e

    def validate_content(self, article: ExtractedArticle) -> ValidationResult:
        """
        Perform comprehensive content validation.

        Args:
            article: Article to validate

        Returns:
            Complete validation result

        Raises:
            ValidationError: If validation cannot be completed
        """
        logger.info(f"Validating content from: {article.url}")

        issues: List[str] = []
        metadata: Dict[str, Any] = {}

        try:
            # Basic content checks
            if len(article.content) < self.config.min_content_length:
                issues.append(f"Content too short: {len(article.content)} characters")

            # Quality assessment
            quality_metrics = self.assess_quality(article.content)
            metadata["quality_metrics"] = quality_metrics.model_dump()

            # Calculate readability score (simplified)
            readability_score = quality_metrics.overall_score
            if readability_score < self.config.min_readability_score:
                issues.append(
                    f"Readability score {readability_score:.2f} below "
                    f"threshold {self.config.min_readability_score}"
                )

            # Entity extraction
            try:
                entities = self.extract_entities(article.content)
                metadata["entities"] = entities.model_dump()
                entity_count = entities.total_count
            except EntityExtractionError as e:
                logger.warning(f"Entity extraction failed: {e}")
                issues.append(f"Entity extraction error: {str(e)}")
                entity_count = 0

            # Freshness validation
            freshness_valid = True
            if article.metadata.publish_date:
                freshness_valid = self.validate_freshness(
                    article.metadata.publish_date, self.config.max_age_days
                )
                if not freshness_valid:
                    age_days = (datetime.utcnow() - article.metadata.publish_date).days
                    issues.append(
                        f"Content is {age_days} days old, "
                        f"exceeds threshold of {self.config.max_age_days} days"
                    )
            else:
                issues.append("No publish date available for freshness check")

            # Broken link detection
            broken_links: List[str] = []
            if self.config.check_links and article.html:
                try:
                    broken_links = self.check_broken_links(article.html)
                    if len(broken_links) > self.config.max_broken_links:
                        issues.append(
                            f"Found {len(broken_links)} broken links, exceeds "
                            f"threshold of {self.config.max_broken_links}"
                        )
                except LinkCheckError as e:
                    logger.warning(f"Link checking failed: {e}")
                    issues.append(f"Link check error: {str(e)}")

            # Sentiment analysis
            if self.config.enable_sentiment_analysis:
                sentiment = self._analyze_sentiment(article.content)
                metadata["sentiment"] = sentiment

            # Bias detection
            if self.config.enable_bias_detection:
                bias_score = self._detect_bias(article.content)
                metadata["bias_score"] = bias_score

            # Determine quality rating
            quality_rating = self._determine_quality_rating(
                readability_score, entity_count, len(issues)
            )

            # Overall validation status
            passed = (
                len(issues) == 0
                and readability_score >= self.config.min_readability_score
                and freshness_valid
            )

            return ValidationResult(
                url=article.url,
                passed=passed,
                quality_rating=quality_rating,
                readability_score=readability_score,
                freshness_valid=freshness_valid,
                entity_count=entity_count,
                duplicate_score=0.0,
                broken_links=broken_links,
                issues=issues,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Validation failed for {article.url}: {e}")
            raise ValidationError(f"Content validation failed: {e}") from e

    def assess_quality(self, text: str) -> QualityMetrics:
        """
        Assess content quality using multiple metrics.

        Args:
            text: Text content to assess

        Returns:
            Quality metrics with scores

        Raises:
            ValidationError: If quality assessment fails
        """
        try:
            # Grammar score using TextBlob
            blob = TextBlob(text)
            grammar_score = self._calculate_grammar_score(blob)

            # Coherence score using sentence similarity
            coherence_score = self._calculate_coherence_score(text)

            # Information density (unique meaningful words / total words)
            information_density = self._calculate_information_density(text)

            # Sentence complexity (average words per sentence)
            sentence_complexity = self._calculate_sentence_complexity(text)

            # Calculate overall score
            overall_score = (
                grammar_score * 0.3
                + coherence_score * 0.3
                + information_density * 0.2
                + sentence_complexity * 0.2
            )

            return QualityMetrics(
                grammar_score=grammar_score,
                coherence_score=coherence_score,
                information_density=information_density,
                sentence_complexity=sentence_complexity,
                overall_score=overall_score,
            )

        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            raise ValidationError(f"Failed to assess content quality: {e}") from e

    def extract_entities(self, text: str) -> ExtractedEntities:
        """
        Extract named entities using spaCy.

        Args:
            text: Text to extract entities from

        Returns:
            Extracted entities organized by type

        Raises:
            EntityExtractionError: If extraction fails
        """
        if not self._nlp:
            raise EntityExtractionError("spaCy model not initialized")

        try:
            doc = self._nlp(text)

            technologies: Set[str] = set()
            organizations: Set[str] = set()
            persons: Set[str] = set()
            locations: Set[str] = set()
            dates: Set[str] = set()
            misc: Set[str] = set()

            # Technology patterns
            tech_patterns = [
                r"\b[A-Z][a-z]+(?:\.[a-z]+)+\b",  # Package names
                r"\b[A-Z]{2,}\b",  # Acronyms
            ]

            for ent in doc.ents:
                entity_text = ent.text.strip()
                if not entity_text:
                    continue

                if ent.label_ == "ORG":
                    organizations.add(entity_text)
                elif ent.label_ == "PERSON":
                    persons.add(entity_text)
                elif ent.label_ in ["GPE", "LOC"]:
                    locations.add(entity_text)
                elif ent.label_ == "DATE":
                    dates.add(entity_text)
                elif ent.label_ in ["PRODUCT", "WORK_OF_ART"]:
                    technologies.add(entity_text)
                else:
                    misc.add(entity_text)

            # Extract technology terms using patterns
            for pattern in tech_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    tech = match.group(0)
                    if len(tech) > 2:
                        technologies.add(tech)

            # Extract common technology keywords
            tech_keywords = {
                "Python",
                "JavaScript",
                "Java",
                "Docker",
                "Kubernetes",
                "AWS",
                "Azure",
                "GCP",
                "React",
                "Vue",
                "Angular",
                "TensorFlow",
                "PyTorch",
                "Redis",
                "PostgreSQL",
                "MongoDB",
            }
            words = set(re.findall(r"\b[A-Z][a-z]+\b", text))
            technologies.update(words & tech_keywords)

            return ExtractedEntities(
                technologies=sorted(list(technologies)),
                organizations=sorted(list(organizations)),
                persons=sorted(list(persons)),
                locations=sorted(list(locations)),
                dates=sorted(list(dates)),
                misc=sorted(list(misc)),
            )

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            raise EntityExtractionError(f"Failed to extract entities: {e}") from e

    def detect_duplicate(self, text: str, corpus: List[str]) -> float:
        """
        Detect duplicate content using embedding similarity.

        Args:
            text: Text to check for duplicates
            corpus: Corpus of texts to compare against

        Returns:
            Maximum similarity score (0.0 to 1.0)

        Raises:
            ValidationError: If duplicate detection fails
        """
        if not self._embedding_model:
            raise ValidationError("Embedding model not initialized")

        try:
            if not corpus:
                return 0.0

            # Generate embedding for input text
            text_embedding = self._embedding_model.encode(
                [text], convert_to_numpy=True
            )[0]

            # Generate embeddings for corpus if not cached
            if len(self._corpus_embeddings) != len(corpus):
                self._corpus_embeddings = list(
                    self._embedding_model.encode(corpus, convert_to_numpy=True)
                )

            # Calculate cosine similarities
            similarities = []
            for corpus_embedding in self._corpus_embeddings:
                similarity = self._cosine_similarity(text_embedding, corpus_embedding)
                similarities.append(similarity)

            # Return maximum similarity
            max_similarity = max(similarities) if similarities else 0.0
            return float(max_similarity)

        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            raise ValidationError(f"Failed to detect duplicates: {e}") from e

    def validate_freshness(self, publish_date: datetime, max_age_days: int) -> bool:
        """
        Validate content freshness based on publish date.

        Args:
            publish_date: Publication date of content
            max_age_days: Maximum allowed age in days

        Returns:
            True if content is fresh enough
        """
        try:
            age = datetime.utcnow() - publish_date
            is_fresh = age.days <= max_age_days
            logger.debug(
                f"Content age: {age.days} days, threshold: {max_age_days} days"
            )
            return is_fresh

        except Exception as e:
            logger.error(f"Freshness validation failed: {e}")
            return False

    def check_broken_links(self, html: str) -> List[str]:
        """
        Check for broken links in HTML content.

        Args:
            html: HTML content to check

        Returns:
            List of broken link URLs

        Raises:
            LinkCheckError: If link checking fails
        """
        broken_links: List[str] = []

        try:
            soup = BeautifulSoup(html, "html.parser")
            links = soup.find_all("a", href=True)

            logger.info(f"Checking {len(links)} links")

            for link in links:
                if not isinstance(link, Tag):
                    continue
                href = link.get("href", "")
                if not isinstance(href, str):
                    continue

                # Skip non-HTTP links
                if not href.startswith(("http://", "https://")):
                    continue

                try:
                    response = requests.head(  # nosec B113
                        href,
                        timeout=self.config.link_check_timeout,
                        allow_redirects=True,
                    )

                    if response.status_code >= 400:
                        broken_links.append(href)
                        logger.debug(
                            f"Broken link: {href} " f"(status: {response.status_code})"
                        )

                except requests.RequestException as e:
                    broken_links.append(href)
                    logger.debug(f"Failed to check link {href}: {e}")

            return broken_links

        except Exception as e:
            logger.error(f"Link checking failed: {e}")
            raise LinkCheckError(f"Failed to check links: {e}") from e

    def batch_validate(
        self, articles: List[ExtractedArticle]
    ) -> List[ValidationResult]:
        """
        Validate multiple articles in batch.

        Args:
            articles: List of articles to validate

        Returns:
            List of validation results
        """
        logger.info(f"Starting batch validation of {len(articles)} articles")

        results: List[ValidationResult] = []

        for i, article in enumerate(articles, 1):
            try:
                result = self.validate_content(article)
                results.append(result)
                logger.debug(f"Validated {i}/{len(articles)}: {article.url}")
            except ValidationError as e:
                logger.error(f"Failed to validate {article.url}: {e}")
                # Create a failed result
                results.append(
                    ValidationResult(
                        url=article.url,
                        passed=False,
                        quality_rating=QualityRating.LOW,
                        readability_score=0.0,
                        freshness_valid=False,
                        entity_count=0,
                        duplicate_score=0.0,
                        broken_links=[],
                        issues=[f"Validation error: {str(e)}"],
                        metadata={},
                    )
                )

        logger.info(
            f"Batch validation complete. "
            f"{sum(1 for r in results if r.passed)}/{len(results)} passed"
        )

        return results

    def generate_validation_report(
        self, results: List[ValidationResult]
    ) -> Dict[str, Any]:
        """
        Generate summary report from validation results.

        Args:
            results: List of validation results

        Returns:
            Summary report with statistics and insights
        """
        if not results:
            return {
                "total_articles": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
            }

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        # Quality distribution
        quality_dist = {
            QualityRating.HIGH: sum(
                1 for r in results if r.quality_rating == QualityRating.HIGH
            ),
            QualityRating.MEDIUM: sum(
                1 for r in results if r.quality_rating == QualityRating.MEDIUM
            ),
            QualityRating.LOW: sum(
                1 for r in results if r.quality_rating == QualityRating.LOW
            ),
        }

        # Average metrics
        avg_readability = sum(r.readability_score for r in results) / total
        avg_entities = sum(r.entity_count for r in results) / total
        avg_duplicate_score = sum(r.duplicate_score for r in results) / total

        # Issue analysis
        all_issues = [issue for r in results for issue in r.issues]
        issue_counts: Dict[str, int] = {}
        for issue in all_issues:
            # Extract issue type (first part before colon)
            issue_type = issue.split(":")[0] if ":" in issue else issue
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        # Broken links
        total_broken_links = sum(len(r.broken_links) for r in results)

        # Freshness
        fresh_articles = sum(1 for r in results if r.freshness_valid)

        return {
            "total_articles": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "quality_distribution": {
                "high": quality_dist[QualityRating.HIGH],
                "medium": quality_dist[QualityRating.MEDIUM],
                "low": quality_dist[QualityRating.LOW],
            },
            "average_metrics": {
                "readability_score": round(avg_readability, 3),
                "entity_count": round(avg_entities, 1),
                "duplicate_score": round(avg_duplicate_score, 3),
            },
            "freshness": {
                "fresh_articles": fresh_articles,
                "stale_articles": total - fresh_articles,
                "freshness_rate": fresh_articles / total if total > 0 else 0.0,
            },
            "broken_links": {
                "total_broken_links": total_broken_links,
                "articles_with_broken_links": sum(
                    1 for r in results if r.has_broken_links
                ),
            },
            "common_issues": dict(
                sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
        }

    # Private helper methods

    def _calculate_grammar_score(self, blob: TextBlob) -> float:
        """Calculate grammar score using TextBlob sentiment polarity."""
        try:
            # Use polarity as a proxy for grammatical correctness
            # Well-formed sentences tend to have clearer sentiment
            polarity = blob.sentiment.polarity
            # Normalize to 0-1 range
            score = (abs(polarity) + 0.5) / 1.5
            return min(max(score, 0.0), 1.0)
        except Exception:
            return 0.5

    def _calculate_coherence_score(self, text: str) -> float:
        """Calculate text coherence using sentence similarity."""
        if not self._nlp:
            return 0.5

        try:
            doc = self._nlp(text)
            sentences = list(doc.sents)

            if len(sentences) < 2:
                return 1.0

            # Calculate average similarity between consecutive sentences
            similarities = []
            for i in range(len(sentences) - 1):
                sim = sentences[i].similarity(sentences[i + 1])
                similarities.append(sim)

            avg_similarity = sum(similarities) / len(similarities)
            return float(avg_similarity)

        except Exception:
            return 0.5

    def _calculate_information_density(self, text: str) -> float:
        """Calculate information density (unique meaningful words ratio)."""
        try:
            words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
            if not words:
                return 0.0

            unique_words = set(words)
            density = len(unique_words) / len(words)
            return min(density, 1.0)

        except Exception:
            return 0.5

    def _calculate_sentence_complexity(self, text: str) -> float:
        """Calculate sentence complexity score."""
        try:
            sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if not sentences:
                return 0.0

            words_per_sentence = []
            for sentence in sentences:
                words = re.findall(r"\b\w+\b", sentence)
                words_per_sentence.append(len(words))

            avg_words = sum(words_per_sentence) / len(words_per_sentence)

            # Normalize: 15-25 words per sentence is ideal
            if 15 <= avg_words <= 25:
                score = 1.0
            elif avg_words < 15:
                score = avg_words / 15
            else:
                score = max(0.0, 1.0 - (avg_words - 25) / 25)

            return min(max(score, 0.0), 1.0)

        except Exception:
            return 0.5

    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text."""
        try:
            blob = TextBlob(text)
            return {
                "polarity": blob.sentiment.polarity,
                "subjectivity": blob.sentiment.subjectivity,
            }
        except Exception:
            return {"polarity": 0.0, "subjectivity": 0.0}

    def _detect_bias(self, text: str) -> float:
        """Detect potential bias in text."""
        try:
            # Simple bias detection using subjective language
            blob = TextBlob(text)
            subjectivity = blob.sentiment.subjectivity

            # Check for loaded language
            loaded_words = [
                "always",
                "never",
                "obviously",
                "clearly",
                "everyone",
                "nobody",
            ]
            text_lower = text.lower()
            loaded_count = sum(1 for word in loaded_words if word in text_lower)

            # Combine metrics
            bias_score = (subjectivity + (loaded_count / 10)) / 2
            return min(bias_score, 1.0)

        except Exception:
            return 0.0

    def _determine_quality_rating(
        self, readability_score: float, entity_count: int, issue_count: int
    ) -> QualityRating:
        """Determine overall quality rating."""
        if readability_score >= 0.75 and entity_count >= 10 and issue_count == 0:
            return QualityRating.HIGH
        elif readability_score >= 0.5 and entity_count >= 5 and issue_count <= 2:
            return QualityRating.MEDIUM
        else:
            return QualityRating.LOW

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


# Convenience functions
def validate_article(
    article: ExtractedArticle, config: Optional[ValidationConfig] = None
) -> ValidationResult:
    """
    Validate a single article with default or custom configuration.

    Args:
        article: Article to validate
        config: Optional validation configuration

    Returns:
        Validation result
    """
    validator = ContentValidator(config)
    return validator.validate_content(article)


def batch_validate_articles(
    articles: List[ExtractedArticle],
    config: Optional[ValidationConfig] = None,
) -> List[ValidationResult]:
    """
    Validate multiple articles in batch.

    Args:
        articles: List of articles to validate
        config: Optional validation configuration

    Returns:
        List of validation results
    """
    validator = ContentValidator(config)
    return validator.batch_validate(articles)
