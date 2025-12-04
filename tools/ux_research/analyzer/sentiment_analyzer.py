"""
Sentiment Analyzer for UX Research & Design Feedback Platform.

This module provides NLP-based sentiment analysis, topic extraction, and
automated feedback categorization for user feedback data.
"""

import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import nltk
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer


class Sentiment:
    """Sentiment analysis result."""

    def __init__(
        self,
        text: str,
        label: str,
        score: float,
        confidence: float,
        details: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize Sentiment result.

        Args:
            text: Original text analyzed
            label: Sentiment label (positive, neutral, negative)
            score: Overall sentiment score (-1 to 1)
            confidence: Confidence level (0 to 1)
            details: Detailed scores (positive, neutral, negative, compound)
        """
        self.text = text
        self.label = label
        self.score = score
        self.confidence = confidence
        self.details = details or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "label": self.label,
            "score": self.score,
            "confidence": self.confidence,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class Topic:
    """Extracted topic with related terms."""

    def __init__(self, name: str, terms: List[str], score: float, frequency: int):
        """
        Initialize Topic.

        Args:
            name: Topic name (primary term)
            terms: Related terms
            score: Topic relevance score
            frequency: Number of occurrences
        """
        self.name = name
        self.terms = terms
        self.score = score
        self.frequency = frequency

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "terms": self.terms,
            "score": self.score,
            "frequency": self.frequency,
        }


class SentimentAnalyzer:
    """NLP-based sentiment analyzer for user feedback."""

    def __init__(self, language: str = "english"):
        """
        Initialize sentiment analyzer.

        Args:
            language: Language for NLP processing (default: english)
        """
        self.language = language
        self._ensure_nltk_data()
        self.sia = SentimentIntensityAnalyzer()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words(language))

        # Predefined categories for feedback
        self.default_categories = [
            "usability",
            "performance",
            "design",
            "accessibility",
            "functionality",
            "content",
            "navigation",
            "mobile",
            "bug",
            "feature_request",
        ]

    def _ensure_nltk_data(self) -> None:
        """Download required NLTK data if not present."""
        required_data = [
            "punkt",
            "stopwords",
            "vader_lexicon",
            "wordnet",
            "averaged_perceptron_tagger",
        ]

        for data_name in required_data:
            try:
                nltk.data.find(f"tokenizers/{data_name}")
            except LookupError:
                try:
                    nltk.data.find(f"corpora/{data_name}")
                except LookupError:
                    try:
                        nltk.data.find(f"sentiment/{data_name}")
                    except LookupError:
                        try:
                            nltk.data.find(f"taggers/{data_name}")
                        except LookupError:
                            nltk.download(data_name, quiet=True)

    def analyze_sentiment(self, text: str) -> Sentiment:
        """
        Classify sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment object with classification results
        """
        if not text or not text.strip():
            return Sentiment(
                text=text,
                label="neutral",
                score=0.0,
                confidence=0.0,
                details={"pos": 0.0, "neu": 1.0, "neg": 0.0, "compound": 0.0},
            )

        # Get sentiment scores
        scores = self.sia.polarity_scores(text)

        # Determine label based on compound score
        compound = scores["compound"]
        if compound >= 0.05:
            label = "positive"
            confidence = min(abs(compound), 1.0)
        elif compound <= -0.05:
            label = "negative"
            confidence = min(abs(compound), 1.0)
        else:
            label = "neutral"
            confidence = 1.0 - abs(compound)

        return Sentiment(
            text=text,
            label=label,
            score=compound,
            confidence=confidence,
            details=scores,
        )

    def extract_topics(self, texts: List[str], num_topics: int = 5) -> List[Topic]:
        """
        Extract common topics from texts.

        Args:
            texts: List of text strings
            num_topics: Number of topics to extract

        Returns:
            List of Topic objects
        """
        if not texts:
            return []

        # Preprocess texts
        processed_texts = [self._preprocess_text(text) for text in texts]

        # Remove empty texts
        processed_texts = [t for t in processed_texts if t]

        if not processed_texts:
            return []

        # Use TF-IDF to identify important terms
        try:
            vectorizer = TfidfVectorizer(
                max_features=num_topics * 5,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8,
            )
            tfidf_matrix = vectorizer.fit_transform(processed_texts)
            feature_names = vectorizer.get_feature_names_out()

            # Get term frequencies
            term_freq: Counter = Counter()
            for text in processed_texts:
                words = text.split()
                term_freq.update(words)

            # Calculate topic scores
            topic_scores = []
            for idx, term in enumerate(feature_names):
                score = tfidf_matrix[:, idx].sum()
                frequency = term_freq.get(term, 0)
                topic_scores.append((term, score, frequency))

            # Sort by score and get top topics
            topic_scores.sort(key=lambda x: x[1], reverse=True)
            top_topics = topic_scores[:num_topics]

            # Create Topic objects
            topics = []
            for term, score, frequency in top_topics:
                # Find related terms (co-occurring terms)
                related = self._find_related_terms(term, processed_texts, max_terms=3)
                topics.append(
                    Topic(
                        name=term,
                        terms=related,
                        score=float(score),
                        frequency=frequency,
                    )
                )

            return topics

        except ValueError:
            # Fallback to simple word frequency if TF-IDF fails
            return self._extract_topics_simple(processed_texts, num_topics)

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for topic extraction.

        Args:
            text: Raw text

        Returns:
            Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r"http\S+|www.\S+", "", text)

        # Remove special characters but keep spaces
        text = re.sub(r"[^a-z\s]", " ", text)

        # Tokenize
        tokens = word_tokenize(text)

        # Remove stopwords and lemmatize
        tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]

        return " ".join(tokens)

    def _find_related_terms(
        self, term: str, texts: List[str], max_terms: int = 3
    ) -> List[str]:
        """
        Find terms that co-occur with the given term.

        Args:
            term: Term to find related terms for
            texts: List of preprocessed texts
            max_terms: Maximum number of related terms

        Returns:
            List of related terms
        """
        co_occurrence: Counter = Counter()

        for text in texts:
            words = text.split()
            if term in words:
                # Add all other words in this text
                co_occurrence.update([w for w in words if w != term])

        # Get most common co-occurring terms
        related = [word for word, _ in co_occurrence.most_common(max_terms)]
        return related

    def _extract_topics_simple(self, texts: List[str], num_topics: int) -> List[Topic]:
        """
        Simple fallback topic extraction using word frequency.

        Args:
            texts: List of preprocessed texts
            num_topics: Number of topics to extract

        Returns:
            List of Topic objects
        """
        word_freq: Counter = Counter()
        for text in texts:
            words = text.split()
            word_freq.update(words)

        topics = []
        for word, freq in word_freq.most_common(num_topics):
            related = self._find_related_terms(word, texts, max_terms=2)
            topics.append(
                Topic(
                    name=word,
                    terms=related,
                    score=float(freq),
                    frequency=freq,
                )
            )

        return topics

    def analyze_keywords(self, texts: List[str]) -> Dict[str, int]:
        """
        Analyze keyword frequency across texts.

        Args:
            texts: List of text strings

        Returns:
            Dictionary mapping keywords to frequencies
        """
        if not texts:
            return {}

        # Preprocess and combine all texts
        all_words = []
        for text in texts:
            processed = self._preprocess_text(text)
            words = processed.split()
            all_words.extend(words)

        # Count frequencies
        word_freq = Counter(all_words)

        # Return as dictionary
        return dict(word_freq.most_common(50))

    def categorize_feedback(
        self,
        feedback: List[str],
        categories: Optional[List[str]] = None,
    ) -> Dict[str, List[str]]:
        """
        Categorize feedback items into predefined categories.

        Args:
            feedback: List of feedback strings
            categories: List of category names (uses defaults if None)

        Returns:
            Dictionary mapping categories to feedback items
        """
        if categories is None:
            categories = self.default_categories

        # Initialize result dictionary
        categorized: Dict[str, List[str]] = {cat: [] for cat in categories}
        categorized["uncategorized"] = []

        # Category keywords mapping
        category_keywords = {
            "usability": [
                "hard",
                "difficult",
                "confusing",
                "easy",
                "simple",
                "intuitive",
                "user friendly",
            ],
            "performance": [
                "slow",
                "fast",
                "loading",
                "speed",
                "lag",
                "performance",
                "responsive",
            ],
            "design": [
                "look",
                "appearance",
                "color",
                "layout",
                "style",
                "visual",
                "design",
                "ui",
            ],
            "accessibility": [
                "accessibility",
                "screen reader",
                "keyboard",
                "contrast",
                "readable",
                "wcag",
            ],
            "functionality": [
                "feature",
                "work",
                "function",
                "broken",
                "working",
                "does not",
            ],
            "content": [
                "content",
                "text",
                "information",
                "copy",
                "writing",
                "message",
            ],
            "navigation": [
                "navigate",
                "menu",
                "find",
                "search",
                "link",
                "navigation",
            ],
            "mobile": [
                "mobile",
                "phone",
                "tablet",
                "responsive",
                "touch",
                "android",
                "ios",
            ],
            "bug": [
                "bug",
                "error",
                "issue",
                "problem",
                "crash",
                "broken",
                "not working",
            ],
            "feature_request": [
                "would like",
                "wish",
                "want",
                "need",
                "should",
                "could",
                "feature",
            ],
        }

        # Categorize each feedback item
        for item in feedback:
            item_lower = item.lower()
            matched_categories = []

            # Check each category
            for category, keywords in category_keywords.items():
                if category in categories:
                    for keyword in keywords:
                        if keyword in item_lower:
                            matched_categories.append(category)
                            break

            # Add to matched categories or uncategorized
            if matched_categories:
                for cat in matched_categories:
                    categorized[cat].append(item)
            else:
                categorized["uncategorized"].append(item)

        return categorized

    def analyze_sentiment_trends(
        self, feedback_with_dates: List[Tuple[str, datetime]]
    ) -> Dict[str, Any]:
        """
        Track sentiment trends over time.

        Args:
            feedback_with_dates: List of (feedback_text, date) tuples

        Returns:
            Dictionary with trend analysis
        """
        if not feedback_with_dates:
            return {
                "overall_sentiment": "neutral",
                "average_score": 0.0,
                "trend": "stable",
                "positive_count": 0,
                "neutral_count": 0,
                "negative_count": 0,
            }

        # Sort by date
        sorted_feedback = sorted(feedback_with_dates, key=lambda x: x[1])

        # Analyze each feedback
        sentiment_data = []
        for text, date in sorted_feedback:
            sentiment = self.analyze_sentiment(text)
            sentiment_data.append(
                {"date": date, "score": sentiment.score, "label": sentiment.label}
            )

        # Calculate statistics
        scores = [float(s.get("score", 0.0)) for s in sentiment_data]  # type: ignore
        labels = [str(s.get("label", "")) for s in sentiment_data]

        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Determine overall sentiment
        if avg_score >= 0.05:
            overall = "positive"
        elif avg_score <= -0.05:
            overall = "negative"
        else:
            overall = "neutral"

        # Calculate trend (compare first half to second half)
        mid_point = len(scores) // 2
        if mid_point > 0:
            first_half_avg = (
                sum(scores[:mid_point]) / mid_point if mid_point > 0 else 0.0
            )
            second_half_avg = (
                sum(scores[mid_point:]) / (len(scores) - mid_point)
                if len(scores) > mid_point
                else 0.0
            )

            if second_half_avg > first_half_avg + 0.1:
                trend = "improving"
            elif second_half_avg < first_half_avg - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "overall_sentiment": overall,
            "average_score": avg_score,
            "trend": trend,
            "positive_count": labels.count("positive"),
            "neutral_count": labels.count("neutral"),
            "negative_count": labels.count("negative"),
            "data_points": sentiment_data,
        }

    def compare_sentiments(
        self, group1: List[str], group2: List[str]
    ) -> Dict[str, Any]:
        """
        Compare sentiment between two groups of feedback.

        Args:
            group1: First group of feedback
            group2: Second group of feedback

        Returns:
            Dictionary with comparative analysis
        """
        # Analyze each group
        sentiments1 = [self.analyze_sentiment(text) for text in group1]
        sentiments2 = [self.analyze_sentiment(text) for text in group2]

        # Calculate average scores
        avg1 = (
            sum(s.score for s in sentiments1) / len(sentiments1) if sentiments1 else 0.0
        )
        avg2 = (
            sum(s.score for s in sentiments2) / len(sentiments2) if sentiments2 else 0.0
        )

        # Count labels
        labels1 = [s.label for s in sentiments1]
        labels2 = [s.label for s in sentiments2]

        return {
            "group1": {
                "average_score": avg1,
                "positive_count": labels1.count("positive"),
                "neutral_count": labels1.count("neutral"),
                "negative_count": labels1.count("negative"),
                "total": len(group1),
            },
            "group2": {
                "average_score": avg2,
                "positive_count": labels2.count("positive"),
                "neutral_count": labels2.count("neutral"),
                "negative_count": labels2.count("negative"),
                "total": len(group2),
            },
            "difference": avg2 - avg1,
            "comparison": (
                "group2_more_positive"
                if avg2 > avg1
                else "group1_more_positive" if avg1 > avg2 else "equal"
            ),
        }
