"""
RICE Scoring Engine for devCrew_s1 project.

Tool ID: TOOL-DATA-002
Issue: #34
Module: issue_34_rice_scorer.py

Provides RICE (Reach × Impact × Confidence / Effort) scoring capabilities
for feature prioritization and backlog management.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


class StatisticalError(Exception):
    """Raised when statistical operation fails."""

    pass


@dataclass
class RICEScore:
    """Represents a calculated RICE score with metadata."""

    reach: float
    impact: float
    confidence: float
    effort: float
    score: float
    normalized_score: Optional[float] = None
    tier: Optional[str] = None
    category: Optional[str] = None
    weights: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "reach": self.reach,
            "impact": self.impact,
            "confidence": self.confidence,
            "effort": self.effort,
            "score": round(self.score, 2),
            "normalized_score": (
                round(self.normalized_score, 2)
                if self.normalized_score is not None
                else None
            ),
            "tier": self.tier,
            "category": self.category,
            "weights": self.weights,
        }


class RICEScorer:
    """
    Calculate RICE priority scores for items.

    RICE Score = (Reach × Impact × Confidence) / Effort

    Supports:
    - Configurable weights for each dimension
    - Batch scoring of multiple items
    - Normalization to 0-100 scale
    - Quick wins identification
    - Priority tier assignment
    """

    # Valid impact values
    IMPACT_VALUES = {
        "minimal": 0.25,
        "low": 0.5,
        "medium": 1.0,
        "high": 2.0,
        "massive": 3.0,
    }

    # Default priority tier thresholds (normalized scores)
    DEFAULT_TIERS = {"P0": 75, "P1": 50, "P2": 25, "P3": 0}

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        default_confidence: Optional[float] = None,
        allow_missing: bool = True,
    ):
        """
        Initialize RICE scorer.

        Args:
            weights: Custom weights for dimensions (reach, impact, confidence)
            default_confidence: Default confidence value for missing data
            allow_missing: Whether to allow missing values (use defaults/medians)
        """
        self.weights = weights or {"reach": 1.0, "impact": 1.0, "confidence": 1.0}
        self.default_confidence = default_confidence
        self.allow_missing = allow_missing

        # Validate weights
        for key in ["reach", "impact", "confidence"]:
            if key not in self.weights:
                self.weights[key] = 1.0
            if self.weights[key] <= 0:
                raise ValidationError(f"Weight for {key} must be positive")

        logger.info(
            f"Initialized RICEScorer with weights: {self.weights}, "
            f"allow_missing: {allow_missing}"
        )

    def calculate(
        self,
        reach: float,
        impact: float,
        confidence: Optional[float] = None,
        effort: float = 1.0,
    ) -> RICEScore:
        """
        Calculate RICE score for a single item.

        Args:
            reach: Number/percentage of users affected (0-100)
            impact: Impact per user (0.25, 0.5, 1.0, 2.0, 3.0)
            confidence: Confidence in estimates (0-100), optional
            effort: Person-weeks required (>0)

        Returns:
            RICEScore object with calculated score and metadata

        Raises:
            ValidationError: If inputs are invalid
        """
        # Validate inputs
        self._validate_reach(reach)
        self._validate_impact(impact)
        self._validate_effort(effort)

        # Handle missing confidence
        if confidence is None:
            if self.default_confidence is not None:
                confidence = self.default_confidence
            elif self.allow_missing:
                confidence = 80.0  # Default medium confidence
                logger.warning("Confidence not provided, using default: 80%")
            else:
                raise ValidationError("Confidence is required (allow_missing=False)")

        self._validate_confidence(confidence)

        # Calculate weighted score
        weighted_reach = reach * self.weights["reach"]
        weighted_impact = impact * self.weights["impact"]
        weighted_confidence = (confidence / 100.0) * self.weights["confidence"]

        # RICE formula: (Reach × Impact × Confidence) / Effort
        score = (weighted_reach * weighted_impact * weighted_confidence) / effort

        logger.debug(
            f"Calculated RICE score: reach={reach}, impact={impact}, "
            f"confidence={confidence}, effort={effort}, score={score:.2f}"
        )

        return RICEScore(
            reach=reach,
            impact=impact,
            confidence=confidence,
            effort=effort,
            score=score,
            weights=self.weights.copy(),
        )

    def score_dataframe(
        self, df: pd.DataFrame, normalize: bool = False, assign_tiers: bool = True
    ) -> pd.DataFrame:
        """
        Score multiple items from a DataFrame.

        Args:
            df: DataFrame with columns: reach, impact, confidence, effort
            normalize: Whether to normalize scores to 0-100 scale
            assign_tiers: Whether to assign priority tiers (P0, P1, P2, P3)

        Returns:
            DataFrame with additional columns: score, normalized_score, tier, category

        Raises:
            ValidationError: If required columns are missing
        """
        required_cols = ["reach", "impact", "effort"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValidationError(f"Missing required columns: {missing_cols}")

        logger.info(f"Scoring {len(df)} items from DataFrame")

        # Make a copy to avoid modifying original
        result = df.copy()

        # Handle missing confidence
        if "confidence" not in result.columns:
            if self.default_confidence is not None:
                result["confidence"] = self.default_confidence
            elif self.allow_missing:
                result["confidence"] = 80.0
                logger.warning("Confidence column missing, using default: 80%")
            else:
                raise ValidationError(
                    "Confidence column required (allow_missing=False)"
                )

        # Validate all values
        for idx, row in result.iterrows():
            try:
                self._validate_reach(row["reach"])
                self._validate_impact(row["impact"])
                self._validate_confidence(row["confidence"])
                self._validate_effort(row["effort"])
            except ValidationError as e:
                logger.error(f"Validation error at row {idx}: {e}")
                raise

        # Calculate scores vectorized
        weighted_reach = result["reach"] * self.weights["reach"]
        weighted_impact = result["impact"] * self.weights["impact"]
        weighted_confidence = (result["confidence"] / 100.0) * self.weights[
            "confidence"
        ]

        result["score"] = (
            weighted_reach * weighted_impact * weighted_confidence
        ) / result["effort"]

        # Normalize scores if requested
        if normalize:
            result["normalized_score"] = self._normalize_scores(result["score"])
        else:
            result["normalized_score"] = result["score"]

        # Assign priority tiers
        if assign_tiers:
            result["tier"] = result["normalized_score"].apply(self._assign_tier)

        # Categorize items
        result["category"] = result.apply(self._categorize_item, axis=1)

        logger.info(
            f"Scored {len(result)} items. "
            f"Mean score: {result['score'].mean():.2f}, "
            f"Median: {result['score'].median():.2f}"
        )

        return result

    def score_items(
        self, items: List[Dict[str, Any]], normalize: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Score multiple items from list of dictionaries.

        Args:
            items: List of dicts with keys: reach, impact, confidence, effort
            normalize: Whether to normalize scores to 0-100 scale

        Returns:
            List of dicts with added score, normalized_score, tier, category
        """
        df = pd.DataFrame(items)
        result_df = self.score_dataframe(df, normalize=normalize)
        return result_df.to_dict("records")

    def _normalize_scores(self, scores: pd.Series) -> pd.Series:
        """
        Normalize scores to 0-100 scale using min-max normalization.

        Args:
            scores: Series of raw RICE scores

        Returns:
            Series of normalized scores (0-100)
        """
        min_score = scores.min()
        max_score = scores.max()

        if max_score == min_score:
            logger.warning("All scores are equal, returning 50 for all items")
            return pd.Series([50.0] * len(scores), index=scores.index)

        normalized = ((scores - min_score) / (max_score - min_score)) * 100.0
        return normalized

    def _assign_tier(self, normalized_score: float) -> str:
        """
        Assign priority tier based on normalized score.

        Args:
            normalized_score: Score normalized to 0-100 scale

        Returns:
            Priority tier: P0, P1, P2, or P3
        """
        for tier, threshold in self.DEFAULT_TIERS.items():
            if normalized_score >= threshold:
                return tier
        return "P3"

    def _categorize_item(self, row: pd.Series) -> str:
        """
        Categorize item based on score and effort.

        Categories:
        - Quick Win: High score, low effort (score >= 50, effort <= 2)
        - Major Project: High score, high effort (score >= 50, effort > 2)
        - Incremental: Low score, low effort (score < 50, effort <= 2)
        - Time Sink: Low score, high effort (score < 50, effort > 2)

        Args:
            row: DataFrame row with score and effort

        Returns:
            Category string
        """
        score = row.get("normalized_score", row["score"])
        effort = row["effort"]

        if score >= 50:
            return "Quick Win" if effort <= 2 else "Major Project"
        else:
            return "Incremental" if effort <= 2 else "Time Sink"

    def _validate_reach(self, reach: float) -> None:
        """Validate reach value."""
        if not isinstance(reach, (int, float)):
            raise ValidationError(f"Reach must be numeric, got {type(reach)}")
        if reach < 0 or reach > 100:
            raise ValidationError(f"Reach must be 0-100, got {reach}")

    def _validate_impact(self, impact: float) -> None:
        """Validate impact value."""
        if not isinstance(impact, (int, float)):
            raise ValidationError(f"Impact must be numeric, got {type(impact)}")

        valid_values = list(self.IMPACT_VALUES.values())
        if impact not in valid_values:
            raise ValidationError(f"Impact must be one of {valid_values}, got {impact}")

    def _validate_confidence(self, confidence: float) -> None:
        """Validate confidence value."""
        if not isinstance(confidence, (int, float)):
            raise ValidationError(f"Confidence must be numeric, got {type(confidence)}")
        if confidence < 0 or confidence > 100:
            raise ValidationError(f"Confidence must be 0-100, got {confidence}")

    def _validate_effort(self, effort: float) -> None:
        """Validate effort value."""
        if not isinstance(effort, (int, float)):
            raise ValidationError(f"Effort must be numeric, got {type(effort)}")
        if effort <= 0:
            raise ValidationError(f"Effort must be positive, got {effort}")

    def impute_missing(
        self, df: pd.DataFrame, strategy: str = "median"
    ) -> pd.DataFrame:
        """
        Impute missing values in DataFrame.

        Args:
            df: DataFrame with potential missing values
            strategy: Imputation strategy ('median', 'mean', 'mode')

        Returns:
            DataFrame with imputed values
        """
        result = df.copy()

        for col in ["reach", "impact", "confidence", "effort"]:
            if col in result.columns and result[col].isna().any():
                if strategy == "median":
                    fill_value = result[col].median()
                elif strategy == "mean":
                    fill_value = result[col].mean()
                elif strategy == "mode":
                    fill_value = result[col].mode()[0]
                else:
                    raise ValueError(f"Unknown strategy: {strategy}")

                result[col] = result[col].fillna(fill_value)
                logger.info(f"Imputed {col} with {strategy}: {fill_value:.2f}")

        return result


class PriorityQueue:
    """
    Manage priority queue of items with RICE scores.

    Supports:
    - Ranking by score
    - Filtering by tier, confidence, effort
    - Quick wins identification
    - Export to various formats
    """

    def __init__(self, items: Union[pd.DataFrame, List[Dict[str, Any]]]):
        """
        Initialize priority queue.

        Args:
            items: DataFrame or list of dicts with scored items
        """
        if isinstance(items, list):
            self.df = pd.DataFrame(items)
        else:
            self.df = items.copy()

        logger.info(f"Initialized PriorityQueue with {len(self.df)} items")

    def rank_by(self, column: str = "score", ascending: bool = False) -> pd.DataFrame:
        """
        Rank items by specified column.

        Args:
            column: Column to rank by
            ascending: Sort order

        Returns:
            Sorted DataFrame
        """
        if column not in self.df.columns:
            raise ValidationError(f"Column {column} not found in items")

        self.df = self.df.sort_values(by=column, ascending=ascending).reset_index(
            drop=True
        )
        return self.df

    def quick_wins(
        self, score_threshold: float = 50, effort_threshold: float = 2
    ) -> pd.DataFrame:
        """
        Identify quick wins (high score, low effort).

        Args:
            score_threshold: Minimum score (normalized or raw)
            effort_threshold: Maximum effort

        Returns:
            DataFrame with quick wins
        """
        score_col = (
            "normalized_score" if "normalized_score" in self.df.columns else "score"
        )

        quick_wins = self.df[
            (self.df[score_col] >= score_threshold)
            & (self.df["effort"] <= effort_threshold)
        ]

        logger.info(
            f"Found {len(quick_wins)} quick wins "
            f"(score >= {score_threshold}, effort <= {effort_threshold})"
        )

        return quick_wins

    def get_tier(self, tier: str) -> pd.DataFrame:
        """
        Get items by priority tier.

        Args:
            tier: Priority tier (P0, P1, P2, P3)

        Returns:
            DataFrame with items in specified tier
        """
        if "tier" not in self.df.columns:
            raise ValidationError("Items have not been assigned tiers")

        return self.df[self.df["tier"] == tier]

    def filter_by_confidence(self, min_confidence: float) -> pd.DataFrame:
        """
        Filter items by minimum confidence.

        Args:
            min_confidence: Minimum confidence threshold

        Returns:
            DataFrame with items meeting confidence threshold
        """
        return self.df[self.df["confidence"] >= min_confidence]

    def to_csv(self, filepath: str) -> None:
        """Export to CSV file."""
        self.df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(self.df)} items to {filepath}")

    def to_json(self, filepath: str, orient: str = "records") -> None:
        """Export to JSON file."""
        self.df.to_json(filepath, orient=orient, indent=2)
        logger.info(f"Exported {len(self.df)} items to {filepath}")

    def to_markdown(self, filepath: str, columns: Optional[List[str]] = None) -> None:
        """
        Export to markdown table.

        Args:
            filepath: Output file path
            columns: Columns to include (default: all)
        """
        if columns:
            df_export = self.df[columns]
        else:
            df_export = self.df

        with open(filepath, "w") as f:
            f.write("# Priority Queue\n\n")
            f.write(df_export.to_markdown(index=False))
            f.write(f"\n\n**Total items**: {len(self.df)}\n")

        logger.info(f"Exported {len(self.df)} items to {filepath}")

    def summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics for the queue.

        Returns:
            Dictionary with summary stats
        """
        score_col = (
            "normalized_score" if "normalized_score" in self.df.columns else "score"
        )

        summary = {
            "total_items": len(self.df),
            "score_stats": {
                "mean": float(self.df[score_col].mean()),
                "median": float(self.df[score_col].median()),
                "std": float(self.df[score_col].std()),
                "min": float(self.df[score_col].min()),
                "max": float(self.df[score_col].max()),
            },
        }

        # Tier distribution
        if "tier" in self.df.columns:
            summary["tier_distribution"] = self.df["tier"].value_counts().to_dict()

        # Category distribution
        if "category" in self.df.columns:
            summary["category_distribution"] = (
                self.df["category"].value_counts().to_dict()
            )

        # Quick wins count
        quick_wins_count = len(self.quick_wins())
        summary["quick_wins_count"] = quick_wins_count

        # Low confidence items
        if "confidence" in self.df.columns:
            low_confidence = len(self.df[self.df["confidence"] < 60])
            summary["low_confidence_count"] = low_confidence

        return summary


# Example usage
if __name__ == "__main__":
    # Example 1: Calculate single RICE score
    scorer = RICEScorer()
    score = scorer.calculate(reach=80, impact=2.0, confidence=90, effort=4)
    print("\nExample 1 - Single RICE Score:")
    print(f"Score: {score.score:.2f}")
    print(json.dumps(score.to_dict(), indent=2))

    # Example 2: Score multiple items
    items = [
        {
            "id": "FEAT-123",
            "name": "User authentication",
            "reach": 80,
            "impact": 2.0,
            "confidence": 90,
            "effort": 4,
        },
        {
            "id": "FEAT-124",
            "name": "Dark mode",
            "reach": 50,
            "impact": 0.5,
            "confidence": 100,
            "effort": 1,
        },
        {
            "id": "FEAT-125",
            "name": "Advanced search",
            "reach": 30,
            "impact": 2.0,
            "confidence": 70,
            "effort": 8,
        },
        {
            "id": "FEAT-126",
            "name": "Email notifications",
            "reach": 90,
            "impact": 1.0,
            "confidence": 95,
            "effort": 2,
        },
    ]

    df = pd.DataFrame(items)
    results = scorer.score_dataframe(df, normalize=True)

    print("\nExample 2 - Multiple Items:")
    print(results[["id", "name", "score", "normalized_score", "tier", "category"]])

    # Example 3: Priority queue operations
    queue = PriorityQueue(results)
    queue.rank_by("normalized_score", ascending=False)

    print("\nExample 3 - Priority Queue:")
    print(f"Total items: {len(queue.df)}")

    quick_wins = queue.quick_wins()
    print(f"Quick wins: {len(quick_wins)}")
    print(quick_wins[["id", "name", "normalized_score", "effort"]])

    print("\nQueue Summary:")
    print(json.dumps(queue.summary(), indent=2))
