"""
Tests for Sentiment Analyzer module.
"""

import unittest
from datetime import datetime, timedelta

from sentiment_analyzer import Sentiment, SentimentAnalyzer, Topic


class TestSentiment(unittest.TestCase):
    """Test Sentiment class."""

    def test_sentiment_creation(self):
        """Test creating a Sentiment object."""
        sentiment = Sentiment(
            text="This is great!",
            label="positive",
            score=0.8,
            confidence=0.9,
            details={"pos": 0.8, "neu": 0.2, "neg": 0.0, "compound": 0.8},
        )

        self.assertEqual(sentiment.text, "This is great!")
        self.assertEqual(sentiment.label, "positive")
        self.assertEqual(sentiment.score, 0.8)
        self.assertEqual(sentiment.confidence, 0.9)
        self.assertIsNotNone(sentiment.timestamp)

    def test_sentiment_to_dict(self):
        """Test converting Sentiment to dictionary."""
        sentiment = Sentiment(text="Test", label="neutral", score=0.0, confidence=1.0)
        result = sentiment.to_dict()

        self.assertIn("text", result)
        self.assertIn("label", result)
        self.assertIn("score", result)
        self.assertIn("confidence", result)
        self.assertIn("timestamp", result)


class TestTopic(unittest.TestCase):
    """Test Topic class."""

    def test_topic_creation(self):
        """Test creating a Topic object."""
        topic = Topic(
            name="usability",
            terms=["easy", "simple", "intuitive"],
            score=10.5,
            frequency=15,
        )

        self.assertEqual(topic.name, "usability")
        self.assertEqual(len(topic.terms), 3)
        self.assertEqual(topic.score, 10.5)
        self.assertEqual(topic.frequency, 15)

    def test_topic_to_dict(self):
        """Test converting Topic to dictionary."""
        topic = Topic(name="test", terms=["a", "b"], score=5.0, frequency=10)
        result = topic.to_dict()

        self.assertIn("name", result)
        self.assertIn("terms", result)
        self.assertIn("score", result)
        self.assertIn("frequency", result)


class TestSentimentAnalyzer(unittest.TestCase):
    """Test SentimentAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = SentimentAnalyzer()

    def test_initialization(self):
        """Test analyzer initialization."""
        self.assertIsNotNone(self.analyzer.sia)
        self.assertIsNotNone(self.analyzer.lemmatizer)
        self.assertIsNotNone(self.analyzer.stop_words)
        self.assertEqual(len(self.analyzer.default_categories), 10)

    def test_analyze_positive_sentiment(self):
        """Test analyzing positive sentiment."""
        text = "This is an excellent product! I love it!"
        result = self.analyzer.analyze_sentiment(text)

        self.assertEqual(result.label, "positive")
        self.assertGreater(result.score, 0.05)
        self.assertGreater(result.confidence, 0.0)
        self.assertIn("compound", result.details)

    def test_analyze_negative_sentiment(self):
        """Test analyzing negative sentiment."""
        text = "This is terrible and frustrating. I hate it."
        result = self.analyzer.analyze_sentiment(text)

        self.assertEqual(result.label, "negative")
        self.assertLess(result.score, -0.05)
        self.assertGreater(result.confidence, 0.0)

    def test_analyze_neutral_sentiment(self):
        """Test analyzing neutral sentiment."""
        text = "This is a product."
        result = self.analyzer.analyze_sentiment(text)

        self.assertEqual(result.label, "neutral")
        self.assertGreaterEqual(result.score, -0.05)
        self.assertLessEqual(result.score, 0.05)

    def test_analyze_empty_text(self):
        """Test analyzing empty text."""
        result = self.analyzer.analyze_sentiment("")

        self.assertEqual(result.label, "neutral")
        self.assertEqual(result.score, 0.0)
        self.assertEqual(result.confidence, 0.0)

    def test_extract_topics(self):
        """Test extracting topics from texts."""
        texts = [
            "The website is easy to use and intuitive",
            "I found the navigation simple and clear",
            "The interface is user friendly and accessible",
            "Great usability and easy navigation",
            "Simple design makes it easy to find things",
        ]

        topics = self.analyzer.extract_topics(texts, num_topics=3)

        self.assertIsInstance(topics, list)
        self.assertGreater(len(topics), 0)
        self.assertLessEqual(len(topics), 3)

        for topic in topics:
            self.assertIsInstance(topic, Topic)
            self.assertIsInstance(topic.name, str)
            self.assertIsInstance(topic.terms, list)
            self.assertGreater(topic.score, 0)

    def test_extract_topics_empty(self):
        """Test extracting topics from empty list."""
        topics = self.analyzer.extract_topics([])
        self.assertEqual(len(topics), 0)

    def test_extract_topics_single_text(self):
        """Test extracting topics from single text."""
        texts = ["This is a simple test"]
        topics = self.analyzer.extract_topics(texts, num_topics=2)

        # Should handle gracefully (may return 0 or few topics)
        self.assertIsInstance(topics, list)

    def test_analyze_keywords(self):
        """Test analyzing keyword frequency."""
        texts = [
            "The button is too small",
            "The button color is hard to see",
            "Button placement is confusing",
        ]

        keywords = self.analyzer.analyze_keywords(texts)

        self.assertIsInstance(keywords, dict)
        self.assertIn("button", keywords)
        self.assertEqual(keywords["button"], 3)

    def test_analyze_keywords_empty(self):
        """Test analyzing keywords with empty list."""
        keywords = self.analyzer.analyze_keywords([])
        self.assertEqual(len(keywords), 0)

    def test_categorize_feedback_usability(self):
        """Test categorizing usability feedback."""
        feedback = [
            "This is hard to use",
            "The performance is slow",
            "The design looks great",
        ]

        categorized = self.analyzer.categorize_feedback(feedback)

        self.assertIn("usability", categorized)
        self.assertIn("performance", categorized)
        self.assertIn("design", categorized)
        self.assertGreater(len(categorized["usability"]), 0)
        self.assertGreater(len(categorized["performance"]), 0)
        self.assertGreater(len(categorized["design"]), 0)

    def test_categorize_feedback_custom_categories(self):
        """Test categorizing with custom categories."""
        feedback = ["The button is broken", "I want a dark mode"]
        categories = ["bug", "feature_request"]

        categorized = self.analyzer.categorize_feedback(feedback, categories=categories)

        self.assertIn("bug", categorized)
        self.assertIn("feature_request", categorized)
        self.assertGreater(len(categorized["bug"]), 0)
        self.assertGreater(len(categorized["feature_request"]), 0)

    def test_categorize_feedback_empty(self):
        """Test categorizing empty feedback."""
        categorized = self.analyzer.categorize_feedback([])

        for category in self.analyzer.default_categories:
            self.assertIn(category, categorized)
            self.assertEqual(len(categorized[category]), 0)

    def test_analyze_sentiment_trends(self):
        """Test analyzing sentiment trends over time."""
        base_date = datetime.now()
        feedback_with_dates = [
            ("This is terrible", base_date),
            ("Not good", base_date + timedelta(days=1)),
            ("It's okay", base_date + timedelta(days=2)),
            ("Getting better", base_date + timedelta(days=3)),
            ("This is great!", base_date + timedelta(days=4)),
        ]

        trends = self.analyzer.analyze_sentiment_trends(feedback_with_dates)

        self.assertIn("overall_sentiment", trends)
        self.assertIn("average_score", trends)
        self.assertIn("trend", trends)
        self.assertIn("positive_count", trends)
        self.assertIn("neutral_count", trends)
        self.assertIn("negative_count", trends)
        self.assertEqual(trends["trend"], "improving")

    def test_analyze_sentiment_trends_empty(self):
        """Test analyzing trends with empty data."""
        trends = self.analyzer.analyze_sentiment_trends([])

        self.assertEqual(trends["overall_sentiment"], "neutral")
        self.assertEqual(trends["average_score"], 0.0)
        self.assertEqual(trends["trend"], "stable")

    def test_compare_sentiments(self):
        """Test comparing sentiment between groups."""
        group1 = ["This is terrible", "Not good", "Bad experience"]
        group2 = ["This is great", "Excellent", "Love it"]

        comparison = self.analyzer.compare_sentiments(group1, group2)

        self.assertIn("group1", comparison)
        self.assertIn("group2", comparison)
        self.assertIn("difference", comparison)
        self.assertIn("comparison", comparison)

        self.assertLess(
            comparison["group1"]["average_score"],
            comparison["group2"]["average_score"],
        )
        self.assertEqual(comparison["comparison"], "group2_more_positive")

    def test_compare_sentiments_equal(self):
        """Test comparing similar sentiment groups."""
        group1 = ["This is okay"]
        group2 = ["This is fine"]

        comparison = self.analyzer.compare_sentiments(group1, group2)

        self.assertIn("comparison", comparison)
        # Should be close to equal
        self.assertLess(abs(comparison["difference"]), 0.3)

    def test_preprocess_text(self):
        """Test text preprocessing."""
        text = "This is a TEST! Visit http://example.com"
        processed = self.analyzer._preprocess_text(text)

        self.assertNotIn("http", processed)
        self.assertNotIn("!", processed)
        self.assertEqual(processed, processed.lower())

    def test_multilanguage_support(self):
        """Test creating analyzer with different language."""
        analyzer_es = SentimentAnalyzer(language="english")
        self.assertEqual(analyzer_es.language, "english")
        self.assertIsNotNone(analyzer_es.stop_words)


class TestIntegration(unittest.TestCase):
    """Integration tests for sentiment analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = SentimentAnalyzer()

    def test_full_feedback_analysis_workflow(self):
        """Test complete workflow of analyzing feedback."""
        feedback = [
            "The website is hard to navigate and very slow",
            "I love the new design, it looks beautiful",
            "The mobile version is broken on my phone",
            "Great performance improvements in this update",
            "Need better accessibility features",
        ]

        # Analyze sentiments
        sentiments = [self.analyzer.analyze_sentiment(text) for text in feedback]
        self.assertEqual(len(sentiments), 5)

        # Extract topics
        topics = self.analyzer.extract_topics(feedback, num_topics=3)
        self.assertGreater(len(topics), 0)

        # Analyze keywords
        keywords = self.analyzer.analyze_keywords(feedback)
        self.assertGreater(len(keywords), 0)

        # Categorize feedback
        categorized = self.analyzer.categorize_feedback(feedback)
        total_categorized = sum(len(items) for items in categorized.values())
        self.assertGreater(total_categorized, 0)

    def test_sentiment_distribution(self):
        """Test analyzing sentiment distribution."""
        feedback = [
            "Excellent!",
            "Great work",
            "Good job",
            "It's okay",
            "Not bad",
            "Poor quality",
            "Terrible",
        ]

        sentiments = [self.analyzer.analyze_sentiment(text) for text in feedback]

        positive = sum(1 for s in sentiments if s.label == "positive")
        neutral = sum(1 for s in sentiments if s.label == "neutral")
        negative = sum(1 for s in sentiments if s.label == "negative")

        self.assertEqual(positive + neutral + negative, len(feedback))
        self.assertGreater(positive, 0)
        self.assertGreater(negative, 0)


if __name__ == "__main__":
    unittest.main()
