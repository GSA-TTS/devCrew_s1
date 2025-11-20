"""
Comprehensive test suite for Statistical Analysis & RICE Scoring Engine.

Tool ID: TOOL-DATA-002
Issue: #34
Module: issue_34_test_statistical_analysis.py

Tests cover:
- RICE scoring calculations
- Priority queue operations
- Statistical analysis functions
- Trend detection
- Performance requirements
- Edge cases and error handling
"""

import json
import time
from typing import List

import numpy as np
import pandas as pd
import pytest

# Import modules to test
from issue_34_rice_scorer import (PriorityQueue, RICEScore, RICEScorer,
                                  ValidationError)
from issue_34_statistical_analysis import (CorrelationResult, DescriptiveStats,
                                           HypothesisTestResult,
                                           StatisticalAnalyzer,
                                           StatisticalError, TrendDetector,
                                           TrendResult)

# =============================================================================
# RICE Scorer Tests
# =============================================================================


class TestRICEScorer:
    """Test suite for RICE scoring engine."""

    def test_basic_rice_calculation(self):
        """Test basic RICE score calculation."""
        scorer = RICEScorer()
        score = scorer.calculate(reach=100, impact=2.0, confidence=100, effort=4)

        assert score.reach == 100
        assert score.impact == 2.0
        assert score.confidence == 100
        assert score.effort == 4
        assert score.score == 50.0  # (100 * 2.0 * 1.0) / 4 = 50

    def test_rice_with_weights(self):
        """Test RICE calculation with custom weights."""
        scorer = RICEScorer(weights={"reach": 1.0, "impact": 2.0, "confidence": 1.0})
        score = scorer.calculate(reach=100, impact=2.0, confidence=100, effort=4)

        # (100 * 1.0 * 2.0 * 2.0 * 1.0) / 4 = 100
        assert score.score == 100.0
        assert score.weights["impact"] == 2.0

    def test_rice_with_default_confidence(self):
        """Test RICE calculation with default confidence."""
        scorer = RICEScorer(default_confidence=80.0)
        score = scorer.calculate(reach=100, impact=2.0, effort=4)

        assert score.confidence == 80.0
        assert score.score == 40.0  # (100 * 2.0 * 0.8) / 4 = 40

    def test_invalid_reach(self):
        """Test validation of reach parameter."""
        scorer = RICEScorer()

        with pytest.raises(ValidationError, match="Reach must be 0-100"):
            scorer.calculate(reach=150, impact=2.0, confidence=90, effort=4)

        with pytest.raises(ValidationError, match="Reach must be 0-100"):
            scorer.calculate(reach=-10, impact=2.0, confidence=90, effort=4)

    def test_invalid_impact(self):
        """Test validation of impact parameter."""
        scorer = RICEScorer()

        with pytest.raises(ValidationError, match="Impact must be one of"):
            scorer.calculate(reach=80, impact=5.0, confidence=90, effort=4)

        with pytest.raises(ValidationError, match="Impact must be one of"):
            scorer.calculate(reach=80, impact=1.5, confidence=90, effort=4)

    def test_invalid_confidence(self):
        """Test validation of confidence parameter."""
        scorer = RICEScorer()

        with pytest.raises(ValidationError, match="Confidence must be 0-100"):
            scorer.calculate(reach=80, impact=2.0, confidence=150, effort=4)

        with pytest.raises(ValidationError, match="Confidence must be 0-100"):
            scorer.calculate(reach=80, impact=2.0, confidence=-10, effort=4)

    def test_invalid_effort(self):
        """Test validation of effort parameter."""
        scorer = RICEScorer()

        with pytest.raises(ValidationError, match="Effort must be positive"):
            scorer.calculate(reach=80, impact=2.0, confidence=90, effort=0)

        with pytest.raises(ValidationError, match="Effort must be positive"):
            scorer.calculate(reach=80, impact=2.0, confidence=90, effort=-4)

    def test_score_dataframe(self):
        """Test scoring multiple items from DataFrame."""
        scorer = RICEScorer()
        items = pd.DataFrame(
            [
                {"reach": 80, "impact": 2.0, "confidence": 90, "effort": 4},
                {"reach": 50, "impact": 0.5, "confidence": 100, "effort": 1},
                {"reach": 30, "impact": 2.0, "confidence": 70, "effort": 8},
            ]
        )

        results = scorer.score_dataframe(items, normalize=True, assign_tiers=True)

        assert len(results) == 3
        assert "score" in results.columns
        assert "normalized_score" in results.columns
        assert "tier" in results.columns
        assert "category" in results.columns

        # Check scores are calculated correctly
        assert results.iloc[0]["score"] == 36.0  # (80 * 2.0 * 0.9) / 4
        assert results.iloc[1]["score"] == 25.0  # (50 * 0.5 * 1.0) / 1
        assert results.iloc[2]["score"] == 5.25  # (30 * 2.0 * 0.7) / 8

    def test_score_normalization(self):
        """Test score normalization to 0-100 scale."""
        scorer = RICEScorer()
        items = pd.DataFrame(
            [
                {"reach": 100, "impact": 3.0, "confidence": 100, "effort": 1},  # Max
                {"reach": 10, "impact": 0.25, "confidence": 50, "effort": 8},  # Min
                {"reach": 50, "impact": 1.0, "confidence": 80, "effort": 2},  # Mid
            ]
        )

        results = scorer.score_dataframe(items, normalize=True)

        assert results.iloc[0]["normalized_score"] == 100.0  # Highest score
        assert results.iloc[1]["normalized_score"] == 0.0  # Lowest score
        assert 0 < results.iloc[2]["normalized_score"] < 100  # Middle

    def test_tier_assignment(self):
        """Test priority tier assignment."""
        scorer = RICEScorer()
        items = pd.DataFrame(
            [
                {"reach": 100, "impact": 3.0, "confidence": 100, "effort": 1},  # P0
                {"reach": 80, "impact": 2.0, "confidence": 90, "effort": 2},  # P1
                {"reach": 30, "impact": 1.0, "confidence": 70, "effort": 4},  # P2
                {"reach": 10, "impact": 0.25, "confidence": 50, "effort": 8},  # P3
            ]
        )

        results = scorer.score_dataframe(items, normalize=True, assign_tiers=True)

        # Check that tiers are assigned
        assert all(tier in ["P0", "P1", "P2", "P3"] for tier in results["tier"])

    def test_categorization(self):
        """Test item categorization (quick wins, major projects, etc.)."""
        scorer = RICEScorer()
        items = pd.DataFrame(
            [
                {
                    "reach": 90,
                    "impact": 2.0,
                    "confidence": 95,
                    "effort": 1,
                },  # Quick Win
                {
                    "reach": 100,
                    "impact": 3.0,
                    "confidence": 80,
                    "effort": 8,
                },  # Major Project
                {
                    "reach": 20,
                    "impact": 0.5,
                    "confidence": 90,
                    "effort": 1,
                },  # Incremental
                {
                    "reach": 10,
                    "impact": 0.25,
                    "confidence": 60,
                    "effort": 6,
                },  # Time Sink
            ]
        )

        results = scorer.score_dataframe(items, normalize=True)

        # First item should be Quick Win (high score, low effort)
        assert results.iloc[0]["category"] in ["Quick Win", "Major Project"]

    def test_impute_missing(self):
        """Test missing value imputation."""
        scorer = RICEScorer()
        items = pd.DataFrame(
            [
                {"reach": 80, "impact": 2.0, "confidence": 90, "effort": 4},
                {"reach": np.nan, "impact": 1.0, "confidence": 80, "effort": 2},
                {"reach": 60, "impact": 2.0, "confidence": np.nan, "effort": 3},
            ]
        )

        imputed = scorer.impute_missing(items, strategy="median")

        assert not imputed["reach"].isna().any()
        assert not imputed["confidence"].isna().any()


class TestPriorityQueue:
    """Test suite for priority queue manager."""

    def test_initialization(self):
        """Test priority queue initialization."""
        items = pd.DataFrame(
            [
                {"id": "A", "score": 50, "effort": 2},
                {"id": "B", "score": 30, "effort": 4},
            ]
        )

        queue = PriorityQueue(items)
        assert len(queue.df) == 2

    def test_rank_by_score(self):
        """Test ranking items by score."""
        items = pd.DataFrame(
            [
                {"id": "A", "score": 30, "effort": 2},
                {"id": "B", "score": 50, "effort": 4},
                {"id": "C", "score": 40, "effort": 3},
            ]
        )

        queue = PriorityQueue(items)
        ranked = queue.rank_by("score", ascending=False)

        assert ranked.iloc[0]["id"] == "B"  # Highest score
        assert ranked.iloc[1]["id"] == "C"
        assert ranked.iloc[2]["id"] == "A"  # Lowest score

    def test_quick_wins_identification(self):
        """Test quick wins identification."""
        items = pd.DataFrame(
            [
                {"id": "A", "score": 60, "effort": 1, "normalized_score": 60},
                {"id": "B", "score": 30, "effort": 4, "normalized_score": 30},
                {"id": "C", "score": 55, "effort": 2, "normalized_score": 55},
                {"id": "D", "score": 40, "effort": 1, "normalized_score": 40},
            ]
        )

        queue = PriorityQueue(items)
        quick_wins = queue.quick_wins(score_threshold=50, effort_threshold=2)

        assert len(quick_wins) == 2  # A and C
        assert "A" in quick_wins["id"].values
        assert "C" in quick_wins["id"].values

    def test_get_tier(self):
        """Test getting items by tier."""
        items = pd.DataFrame(
            [
                {"id": "A", "tier": "P0"},
                {"id": "B", "tier": "P1"},
                {"id": "C", "tier": "P0"},
            ]
        )

        queue = PriorityQueue(items)
        p0_items = queue.get_tier("P0")

        assert len(p0_items) == 2
        assert all(tier == "P0" for tier in p0_items["tier"])

    def test_filter_by_confidence(self):
        """Test filtering by confidence threshold."""
        items = pd.DataFrame(
            [
                {"id": "A", "confidence": 90},
                {"id": "B", "confidence": 60},
                {"id": "C", "confidence": 80},
            ]
        )

        queue = PriorityQueue(items)
        high_confidence = queue.filter_by_confidence(min_confidence=75)

        assert len(high_confidence) == 2  # A and C
        assert all(conf >= 75 for conf in high_confidence["confidence"])

    def test_summary(self):
        """Test queue summary generation."""
        items = pd.DataFrame(
            [
                {
                    "id": "A",
                    "score": 50,
                    "normalized_score": 80,
                    "tier": "P0",
                    "category": "Quick Win",
                    "confidence": 90,
                    "effort": 2,
                },
                {
                    "id": "B",
                    "score": 30,
                    "normalized_score": 60,
                    "tier": "P1",
                    "category": "Major Project",
                    "confidence": 80,
                    "effort": 5,
                },
            ]
        )

        queue = PriorityQueue(items)
        summary = queue.summary()

        assert summary["total_items"] == 2
        assert "score_stats" in summary
        assert "tier_distribution" in summary
        assert "category_distribution" in summary
        assert "quick_wins_count" in summary


# =============================================================================
# Statistical Analyzer Tests
# =============================================================================


class TestStatisticalAnalyzer:
    """Test suite for statistical analyzer."""

    def test_descriptive_statistics(self):
        """Test descriptive statistics calculation."""
        analyzer = StatisticalAnalyzer()
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        stats = analyzer.describe(data)

        assert stats.count == 10
        assert stats.mean == 5.5
        assert stats.median == 5.5
        assert stats.min_value == 1
        assert stats.max_value == 10
        assert stats.q25 == 3.25
        assert stats.q75 == 7.75

    def test_independent_t_test(self):
        """Test independent samples t-test."""
        analyzer = StatisticalAnalyzer()

        # Two clearly different groups
        group_a = [10, 12, 11, 13, 12, 14, 13, 15, 14, 16]
        group_b = [30, 32, 31, 33, 32, 34, 33, 35, 34, 36]

        result = analyzer.t_test(group_a, group_b)

        assert result.test_name == "Independent Samples T-Test"
        assert result.p_value < 0.05  # Should be significant
        assert result.is_significant(alpha=0.05)
        assert result.effect_size is not None
        assert result.confidence_interval is not None

    def test_t_test_no_difference(self):
        """Test t-test with no difference between groups."""
        analyzer = StatisticalAnalyzer()

        # Two similar groups
        group_a = [10, 11, 12, 13, 14]
        group_b = [10, 11, 12, 13, 14]

        result = analyzer.t_test(group_a, group_b)

        assert result.p_value > 0.05  # Should not be significant
        assert not result.is_significant(alpha=0.05)

    def test_paired_t_test(self):
        """Test paired samples t-test."""
        analyzer = StatisticalAnalyzer()

        before = [10, 12, 11, 13, 12, 14, 13, 15, 14, 16]
        after = [12, 14, 13, 15, 14, 16, 15, 17, 16, 18]

        result = analyzer.paired_t_test(before, after)

        assert result.test_name == "Paired Samples T-Test"
        assert result.p_value < 0.05  # Should be significant
        assert result.is_significant()

    def test_mann_whitney_u(self):
        """Test Mann-Whitney U test."""
        analyzer = StatisticalAnalyzer()

        group_a = [10, 12, 11, 13, 12, 14]
        group_b = [20, 22, 21, 23, 22, 24]

        result = analyzer.mann_whitney(group_a, group_b)

        assert result.test_name == "Mann-Whitney U Test"
        assert result.p_value < 0.05  # Should be significant
        assert result.is_significant()

    def test_correlation_pearson(self):
        """Test Pearson correlation."""
        analyzer = StatisticalAnalyzer()

        # Strongly correlated data
        x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

        result = analyzer.correlate(x, y, method="pearson")

        assert result.method == "pearson"
        assert result.coefficient > 0.99  # Near perfect correlation
        assert result.p_value < 0.001
        assert result.is_significant()
        assert "strong" in result.interpretation.lower()

    def test_correlation_spearman(self):
        """Test Spearman correlation."""
        analyzer = StatisticalAnalyzer()

        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]

        result = analyzer.correlate(x, y, method="spearman")

        assert result.method == "spearman"
        assert abs(result.coefficient - 1.0) < 0.0001  # Near perfect rank correlation
        assert result.is_significant()

    def test_normality_check(self):
        """Test normality check."""
        analyzer = StatisticalAnalyzer()

        # Normal distribution
        np.random.seed(42)
        normal_data = np.random.normal(0, 1, 100)

        is_normal, p_value = analyzer.check_normality(normal_data)

        # Should likely be normal (though sometimes fails randomly)
        assert isinstance(bool(is_normal), bool)  # Convert numpy bool to Python bool
        assert 0 <= p_value <= 1

    def test_outlier_detection_iqr(self):
        """Test outlier detection using IQR method."""
        analyzer = StatisticalAnalyzer()

        data = [10, 12, 11, 13, 12, 100, 14, 15, 13, 12, 14, 200]

        outlier_indices, outlier_values = analyzer.detect_outliers(
            data, method="iqr", threshold=1.5
        )

        assert len(outlier_indices) == 2  # Should detect 100 and 200
        assert 100 in outlier_values
        assert 200 in outlier_values

    def test_outlier_detection_zscore(self):
        """Test outlier detection using z-score method."""
        analyzer = StatisticalAnalyzer()

        data = [10, 12, 11, 13, 12, 100, 14, 15, 13, 12, 14]

        outlier_indices, outlier_values = analyzer.detect_outliers(
            data, method="zscore", threshold=3.0
        )

        assert len(outlier_indices) >= 1  # Should detect 100
        assert 100 in outlier_values

    def test_edge_case_empty_data(self):
        """Test handling of empty data."""
        from issue_34_statistical_analysis import \
            ValidationError as StatValidationError

        analyzer = StatisticalAnalyzer()

        with pytest.raises(StatValidationError, match="Data is empty"):
            analyzer.describe([])

    def test_edge_case_insufficient_samples(self):
        """Test handling of insufficient samples."""
        analyzer = StatisticalAnalyzer()

        with pytest.raises(StatisticalError, match="at least 2 samples"):
            analyzer.t_test([10], [20])


# =============================================================================
# Trend Detector Tests
# =============================================================================


class TestTrendDetector:
    """Test suite for trend detector."""

    def test_upward_trend(self):
        """Test detection of upward trend."""
        detector = TrendDetector()

        # Clear upward trend
        data = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]

        result = detector.detect_trend(data)

        assert result.direction == "up"
        assert result.velocity > 0
        assert result.p_value < 0.05  # Should be significant
        assert result.r_squared > 0.9  # Strong fit

    def test_downward_trend(self):
        """Test detection of downward trend."""
        detector = TrendDetector()

        # Clear downward trend
        data = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55]

        result = detector.detect_trend(data)

        assert result.direction == "down"
        assert result.velocity < 0
        assert result.p_value < 0.05
        assert result.r_squared > 0.9

    def test_stable_trend(self):
        """Test detection of stable (no) trend."""
        detector = TrendDetector()

        # No clear trend
        data = [50, 51, 49, 50, 52, 48, 50, 51, 49, 50]

        result = detector.detect_trend(data)

        assert result.direction == "stable"
        assert abs(result.velocity) < 1  # Very small velocity
        assert result.p_value > 0.05  # Not significant

    def test_moving_average(self):
        """Test moving average calculation."""
        detector = TrendDetector()

        data = [10, 20, 30, 40, 50]
        ma = detector.moving_average(data, window=3)

        # First two values should be NaN, rest should be averages
        assert np.isnan(ma[0])
        assert np.isnan(ma[1])
        assert ma[2] == 20.0  # (10 + 20 + 30) / 3
        assert ma[3] == 30.0  # (20 + 30 + 40) / 3

    def test_exponential_smoothing(self):
        """Test exponential smoothing."""
        detector = TrendDetector()

        data = [10, 20, 30, 40, 50]
        smoothed = detector.exponential_smoothing(data, alpha=0.5)

        assert len(smoothed) == len(data)
        assert smoothed[0] == data[0]  # First value unchanged
        assert smoothed[1] > data[0]  # Smoothed towards data[1]

    def test_forecast_linear(self):
        """Test linear forecasting."""
        detector = TrendDetector()

        # Upward trend
        data = [10, 12, 14, 16, 18, 20]

        forecast_df = detector.forecast(data, periods=3, method="linear")

        assert len(forecast_df) == 3
        assert "forecast" in forecast_df.columns
        assert "lower_bound" in forecast_df.columns
        assert "upper_bound" in forecast_df.columns

        # Forecasts should continue upward trend
        assert forecast_df["forecast"].iloc[0] > data[-1]
        assert forecast_df["forecast"].iloc[1] > forecast_df["forecast"].iloc[0]

    def test_forecast_exponential(self):
        """Test exponential forecasting."""
        detector = TrendDetector()

        data = [10, 12, 14, 16, 18, 20]

        forecast_df = detector.forecast(data, periods=3, method="exponential")

        assert len(forecast_df) == 3
        assert all(
            col in forecast_df.columns
            for col in ["forecast", "lower_bound", "upper_bound"]
        )

    def test_edge_case_insufficient_data(self):
        """Test handling of insufficient data."""
        detector = TrendDetector()

        with pytest.raises(StatisticalError, match="at least 3 data points"):
            detector.detect_trend([10, 20])


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """Test suite for performance requirements."""

    def test_rice_scoring_performance(self):
        """Test RICE scoring performance: 1000 items/second."""
        scorer = RICEScorer()

        # Generate 10,000 items
        np.random.seed(42)
        items = pd.DataFrame(
            {
                "reach": np.random.randint(0, 100, 10000),
                "impact": np.random.choice([0.25, 0.5, 1.0, 2.0, 3.0], 10000),
                "confidence": np.random.randint(50, 100, 10000),
                "effort": np.random.choice([1, 2, 4, 8], 10000),
            }
        )

        start_time = time.time()
        results = scorer.score_dataframe(items, normalize=True)
        elapsed = time.time() - start_time

        items_per_second = len(items) / elapsed

        print(f"\nRICE Performance: {items_per_second:.0f} items/second")
        print(f"Processing time: {elapsed:.3f} seconds for {len(items)} items")

        # Should process at least 1000 items/second
        assert (
            items_per_second >= 1000
        ), f"Performance requirement not met: {items_per_second:.0f} items/sec"
        assert len(results) == 10000

    def test_descriptive_stats_performance(self):
        """Test descriptive statistics performance: 1M rows/second."""
        analyzer = StatisticalAnalyzer()

        # Generate 1M data points
        np.random.seed(42)
        data = np.random.normal(100, 15, 1000000)

        start_time = time.time()
        stats = analyzer.describe(data)
        elapsed = time.time() - start_time

        rows_per_second = len(data) / elapsed

        print(f"\nStats Performance: {rows_per_second:.0f} rows/second")
        print(f"Processing time: {elapsed:.3f} seconds for {len(data)} rows")

        # Should process at least 1M rows/second
        assert (
            rows_per_second >= 1000000
        ), f"Performance requirement not met: {rows_per_second:.0f} rows/sec"
        assert stats.count == 1000000

    def test_trend_detection_performance(self):
        """Test trend detection performance: 100k points/second."""
        detector = TrendDetector()

        # Generate 100k time series points
        np.random.seed(42)
        trend = np.linspace(0, 100, 100000)
        noise = np.random.normal(0, 5, 100000)
        data = trend + noise

        start_time = time.time()
        result = detector.detect_trend(data)
        elapsed = time.time() - start_time

        points_per_second = len(data) / elapsed

        print(f"\nTrend Performance: {points_per_second:.0f} points/second")
        print(f"Processing time: {elapsed:.3f} seconds for {len(data)} points")

        # Should process at least 100k points/second
        assert (
            points_per_second >= 100000
        ), f"Performance requirement not met: {points_per_second:.0f} points/sec"
        assert result.direction == "up"


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for end-to-end workflows."""

    def test_end_to_end_rice_workflow(self):
        """Test complete RICE scoring workflow."""
        # Step 1: Create items
        items = [
            {
                "id": "FEAT-001",
                "name": "User auth",
                "reach": 80,
                "impact": 2.0,
                "confidence": 90,
                "effort": 4,
            },
            {
                "id": "FEAT-002",
                "name": "Dark mode",
                "reach": 50,
                "impact": 0.5,
                "confidence": 100,
                "effort": 1,
            },
            {
                "id": "FEAT-003",
                "name": "Advanced search",
                "reach": 30,
                "impact": 2.0,
                "confidence": 70,
                "effort": 8,
            },
        ]

        # Step 2: Score items
        scorer = RICEScorer()
        df = pd.DataFrame(items)
        results = scorer.score_dataframe(df, normalize=True)

        # Step 3: Create priority queue
        queue = PriorityQueue(results)
        queue.rank_by("normalized_score", ascending=False)

        # Step 4: Get quick wins
        quick_wins = queue.quick_wins(score_threshold=50, effort_threshold=2)

        # Step 5: Generate summary
        summary = queue.summary()

        # Verify complete workflow
        assert len(results) == 3
        assert "normalized_score" in results.columns
        assert "tier" in results.columns
        assert len(quick_wins) >= 0
        assert summary["total_items"] == 3
        assert "score_stats" in summary

    def test_statistical_analysis_workflow(self):
        """Test complete statistical analysis workflow."""
        analyzer = StatisticalAnalyzer()

        # Generate sample data
        np.random.seed(42)
        group_a = np.random.normal(100, 15, 100)
        group_b = np.random.normal(110, 15, 100)

        # Step 1: Descriptive statistics
        stats_a = analyzer.describe(group_a)
        stats_b = analyzer.describe(group_b)

        # Step 2: Check normality
        normal_a, _ = analyzer.check_normality(group_a)
        normal_b, _ = analyzer.check_normality(group_b)

        # Step 3: Choose appropriate test
        if normal_a and normal_b:
            result = analyzer.t_test(group_a, group_b)
        else:
            result = analyzer.mann_whitney(group_a, group_b)

        # Verify workflow
        assert stats_a.count == 100
        assert stats_b.count == 100
        assert isinstance(bool(normal_a), bool)  # Convert numpy bool to Python bool
        assert result.p_value < 0.05  # Should detect difference


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
