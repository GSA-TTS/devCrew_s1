"""
Sentiment analysis module for user feedback.

Provides NLP-based sentiment classification, topic extraction,
and automated feedback categorization.
"""

from .sentiment_analyzer import Sentiment, SentimentAnalyzer, Topic

__all__ = [
    "Sentiment",
    "SentimentAnalyzer",
    "Topic",
]
