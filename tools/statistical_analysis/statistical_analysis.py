"""
Statistical Analysis Module for devCrew_s1 project.

Tool ID: TOOL-DATA-002
Issue: #34
Module: issue_34_statistical_analysis.py

Provides comprehensive statistical analysis capabilities including:
- Descriptive statistics
- Hypothesis testing (t-tests, chi-square)
- Correlation analysis
- Trend detection
- Outlier detection
- Forecasting
"""

import logging
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class StatisticalError(Exception):
    """Raised when statistical operation fails."""

    pass


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


@dataclass
class DescriptiveStats:
    """Container for descriptive statistics results."""

    count: int
    mean: float
    median: float
    std: float
    variance: float
    min_value: float
    max_value: float
    q25: float
    q50: float
    q75: float
    iqr: float
    skewness: float
    kurtosis: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "mean": round(self.mean, 4),
            "median": round(self.median, 4),
            "std": round(self.std, 4),
            "variance": round(self.variance, 4),
            "min": round(self.min_value, 4),
            "max": round(self.max_value, 4),
            "q25": round(self.q25, 4),
            "q50": round(self.q50, 4),
            "q75": round(self.q75, 4),
            "iqr": round(self.iqr, 4),
            "skewness": round(self.skewness, 4),
            "kurtosis": round(self.kurtosis, 4),
        }


@dataclass
class HypothesisTestResult:
    """Container for hypothesis test results."""

    test_name: str
    statistic: float
    p_value: float
    degrees_of_freedom: Optional[float]
    effect_size: Optional[float]
    confidence_interval: Optional[Tuple[float, float]]
    conclusion: str

    def is_significant(self, alpha: float = 0.05) -> bool:
        """Check if result is statistically significant."""
        return self.p_value < alpha

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "statistic": round(self.statistic, 4),
            "p_value": round(self.p_value, 6),
            "degrees_of_freedom": self.degrees_of_freedom,
            "effect_size": (
                round(self.effect_size, 4) if self.effect_size is not None else None
            ),
            "confidence_interval": (
                tuple(round(x, 4) for x in self.confidence_interval)
                if self.confidence_interval
                else None
            ),
            "conclusion": self.conclusion,
        }


@dataclass
class CorrelationResult:
    """Container for correlation analysis results."""

    coefficient: float
    p_value: float
    method: str
    sample_size: int
    interpretation: str

    def is_significant(self, alpha: float = 0.05) -> bool:
        """Check if correlation is statistically significant."""
        return self.p_value < alpha

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "coefficient": round(self.coefficient, 4),
            "p_value": round(self.p_value, 6),
            "method": self.method,
            "sample_size": self.sample_size,
            "interpretation": self.interpretation,
        }


@dataclass
class TrendResult:
    """Container for trend detection results."""

    direction: str  # 'up', 'down', 'stable'
    velocity: float  # Change per period
    velocity_pct: float  # Percentage change per period
    changepoints: List[int]
    p_value: float
    r_squared: float
    forecast: Optional[pd.DataFrame] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "direction": self.direction,
            "velocity": round(self.velocity, 4),
            "velocity_pct": round(self.velocity_pct, 2),
            "changepoints": self.changepoints,
            "p_value": round(self.p_value, 6),
            "r_squared": round(self.r_squared, 4),
            "forecast": (
                self.forecast.to_dict("records") if self.forecast is not None else None
            ),
        }


class StatisticalAnalyzer:
    """
    Comprehensive statistical analysis toolkit.

    Provides methods for:
    - Descriptive statistics
    - Hypothesis testing
    - Correlation analysis
    - Distribution fitting
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize statistical analyzer.

        Args:
            confidence_level: Confidence level for intervals (default: 0.95)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

        logger.info(
            f"Initialized StatisticalAnalyzer with confidence_level={confidence_level}"
        )

    def describe(
        self, data: Union[pd.Series, np.ndarray, List[float]]
    ) -> DescriptiveStats:
        """
        Calculate descriptive statistics.

        Args:
            data: Numerical data to analyze

        Returns:
            DescriptiveStats object with summary statistics
        """
        if isinstance(data, list):
            data = np.array(data)
        elif isinstance(data, pd.Series):
            data = data.dropna().values

        if len(data) == 0:
            raise ValidationError("Data is empty")

        q25, q50, q75 = np.percentile(data, [25, 50, 75])
        iqr = q75 - q25

        stats_obj = DescriptiveStats(
            count=len(data),
            mean=float(np.mean(data)),
            median=float(np.median(data)),
            std=float(np.std(data, ddof=1)),
            variance=float(np.var(data, ddof=1)),
            min_value=float(np.min(data)),
            max_value=float(np.max(data)),
            q25=float(q25),
            q50=float(q50),
            q75=float(q75),
            iqr=float(iqr),
            skewness=float(stats.skew(data)),
            kurtosis=float(stats.kurtosis(data)),
        )

        logger.debug(
            f"Calculated descriptive stats: n={stats_obj.count}, "
            f"mean={stats_obj.mean:.2f}, median={stats_obj.median:.2f}"
        )

        return stats_obj

    def t_test(
        self,
        group_a: Union[pd.Series, np.ndarray, List[float]],
        group_b: Union[pd.Series, np.ndarray, List[float]],
        alternative: str = "two-sided",
        equal_var: bool = True,
    ) -> HypothesisTestResult:
        """
        Perform independent samples t-test.

        Args:
            group_a: First group data
            group_b: Second group data
            alternative: 'two-sided', 'less', or 'greater'
            equal_var: Assume equal variance (True) or Welch's t-test (False)

        Returns:
            HypothesisTestResult object
        """
        # Convert to numpy arrays
        group_a = self._to_array(group_a)
        group_b = self._to_array(group_b)

        # Validate inputs
        if len(group_a) < 2 or len(group_b) < 2:
            raise StatisticalError("Each group must have at least 2 samples")

        if np.var(group_a) == 0 and np.var(group_b) == 0:
            raise StatisticalError("No variance in groups - cannot perform t-test")

        # Perform t-test
        statistic, p_value = stats.ttest_ind(
            group_a, group_b, alternative=alternative, equal_var=equal_var
        )

        # Calculate effect size (Cohen's d)
        mean_diff = np.mean(group_a) - np.mean(group_b)
        pooled_std = np.sqrt(
            (
                (len(group_a) - 1) * np.var(group_a, ddof=1)
                + (len(group_b) - 1) * np.var(group_b, ddof=1)
            )
            / (len(group_a) + len(group_b) - 2)
        )
        cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0.0

        # Calculate confidence interval for difference
        se = pooled_std * np.sqrt(1 / len(group_a) + 1 / len(group_b))
        df = len(group_a) + len(group_b) - 2
        t_crit = stats.t.ppf(1 - self.alpha / 2, df)
        ci = (mean_diff - t_crit * se, mean_diff + t_crit * se)

        # Determine conclusion
        if p_value < self.alpha:
            conclusion = (
                f"Significant difference detected (p={p_value:.4f} < {self.alpha})"
            )
        else:
            conclusion = f"No significant difference (p={p_value:.4f} >= {self.alpha})"

        logger.info(
            f"T-test: statistic={statistic:.4f}, p={p_value:.6f}, d={cohens_d:.4f}"
        )

        return HypothesisTestResult(
            test_name="Independent Samples T-Test",
            statistic=float(statistic),
            p_value=float(p_value),
            degrees_of_freedom=float(df),
            effect_size=float(cohens_d),
            confidence_interval=ci,
            conclusion=conclusion,
        )

    def paired_t_test(
        self,
        before: Union[pd.Series, np.ndarray, List[float]],
        after: Union[pd.Series, np.ndarray, List[float]],
        alternative: str = "two-sided",
    ) -> HypothesisTestResult:
        """
        Perform paired samples t-test.

        Args:
            before: Measurements before intervention
            after: Measurements after intervention
            alternative: 'two-sided', 'less', or 'greater'

        Returns:
            HypothesisTestResult object
        """
        before = self._to_array(before)
        after = self._to_array(after)

        if len(before) != len(after):
            raise ValidationError("Before and after samples must have same length")

        if len(before) < 2:
            raise StatisticalError("Need at least 2 paired samples")

        # Perform paired t-test
        statistic, p_value = stats.ttest_rel(before, after, alternative=alternative)

        # Calculate effect size
        differences = after - before
        mean_diff = np.mean(differences)
        std_diff = np.std(differences, ddof=1)
        cohens_d = mean_diff / std_diff if std_diff > 0 else 0.0

        # Calculate confidence interval
        se = std_diff / np.sqrt(len(differences))
        df = len(differences) - 1
        t_crit = stats.t.ppf(1 - self.alpha / 2, df)
        ci = (mean_diff - t_crit * se, mean_diff + t_crit * se)

        conclusion = (
            f"Significant change detected (p={p_value:.4f} < {self.alpha})"
            if p_value < self.alpha
            else f"No significant change (p={p_value:.4f} >= {self.alpha})"
        )

        logger.info(f"Paired t-test: statistic={statistic:.4f}, p={p_value:.6f}")

        return HypothesisTestResult(
            test_name="Paired Samples T-Test",
            statistic=float(statistic),
            p_value=float(p_value),
            degrees_of_freedom=float(df),
            effect_size=float(cohens_d),
            confidence_interval=ci,
            conclusion=conclusion,
        )

    def mann_whitney(
        self,
        group_a: Union[pd.Series, np.ndarray, List[float]],
        group_b: Union[pd.Series, np.ndarray, List[float]],
        alternative: str = "two-sided",
    ) -> HypothesisTestResult:
        """
        Perform Mann-Whitney U test (non-parametric alternative to t-test).

        Args:
            group_a: First group data
            group_b: Second group data
            alternative: 'two-sided', 'less', or 'greater'

        Returns:
            HypothesisTestResult object
        """
        group_a = self._to_array(group_a)
        group_b = self._to_array(group_b)

        if len(group_a) < 2 or len(group_b) < 2:
            raise StatisticalError("Each group must have at least 2 samples")

        statistic, p_value = stats.mannwhitneyu(
            group_a, group_b, alternative=alternative
        )

        conclusion = (
            f"Significant difference detected (p={p_value:.4f} < {self.alpha})"
            if p_value < self.alpha
            else f"No significant difference (p={p_value:.4f} >= {self.alpha})"
        )

        logger.info(f"Mann-Whitney U: U={statistic:.4f}, p={p_value:.6f}")

        return HypothesisTestResult(
            test_name="Mann-Whitney U Test",
            statistic=float(statistic),
            p_value=float(p_value),
            degrees_of_freedom=None,
            effect_size=None,
            confidence_interval=None,
            conclusion=conclusion,
        )

    def correlate(
        self,
        x: Union[pd.Series, np.ndarray, List[float]],
        y: Union[pd.Series, np.ndarray, List[float]],
        method: str = "pearson",
    ) -> CorrelationResult:
        """
        Calculate correlation between two variables.

        Args:
            x: First variable
            y: Second variable
            method: 'pearson', 'spearman', or 'kendall'

        Returns:
            CorrelationResult object
        """
        x = self._to_array(x)
        y = self._to_array(y)

        if len(x) != len(y):
            raise ValidationError("Variables must have same length")

        if len(x) < 3:
            raise StatisticalError("Need at least 3 data points for correlation")

        # Calculate correlation
        if method == "pearson":
            coef, p_value = stats.pearsonr(x, y)
        elif method == "spearman":
            coef, p_value = stats.spearmanr(x, y)
        elif method == "kendall":
            coef, p_value = stats.kendalltau(x, y)
        else:
            raise ValueError(f"Unknown correlation method: {method}")

        # Interpret strength
        abs_coef = abs(coef)
        if abs_coef < 0.3:
            strength = "weak"
        elif abs_coef < 0.7:
            strength = "moderate"
        else:
            strength = "strong"

        direction = "positive" if coef > 0 else "negative"
        interpretation = f"{strength} {direction} correlation"

        logger.info(f"Correlation ({method}): r={coef:.4f}, p={p_value:.6f}")

        return CorrelationResult(
            coefficient=float(coef),
            p_value=float(p_value),
            method=method,
            sample_size=len(x),
            interpretation=interpretation,
        )

    def check_normality(
        self, data: Union[pd.Series, np.ndarray, List[float]]
    ) -> Tuple[bool, float]:
        """
        Check if data follows normal distribution using Shapiro-Wilk test.

        Args:
            data: Data to test

        Returns:
            Tuple of (is_normal, p_value)
        """
        data = self._to_array(data)

        if len(data) < 3:
            logger.warning("Need at least 3 samples for normality test")
            return False, 1.0

        statistic, p_value = stats.shapiro(data)
        is_normal = p_value > self.alpha

        logger.info(
            f"Normality test: W={statistic:.4f}, p={p_value:.6f}, "
            f"normal={is_normal}"
        )

        return is_normal, float(p_value)

    def detect_outliers(
        self,
        data: Union[pd.Series, np.ndarray, List[float]],
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect outliers in data.

        Args:
            data: Data to analyze
            method: 'iqr' (interquartile range) or 'zscore'
            threshold: Threshold for outlier detection
                      For IQR: typically 1.5 or 3.0
                      For Z-score: typically 2.5 or 3.0

        Returns:
            Tuple of (outlier_indices, outlier_values)
        """
        data = self._to_array(data)

        if method == "iqr":
            q25, q75 = np.percentile(data, [25, 75])
            iqr = q75 - q25
            lower_bound = q25 - threshold * iqr
            upper_bound = q75 + threshold * iqr
            outlier_mask = (data < lower_bound) | (data > upper_bound)

        elif method == "zscore":
            z_scores = np.abs(stats.zscore(data))
            outlier_mask = z_scores > threshold

        else:
            raise ValueError(f"Unknown outlier detection method: {method}")

        outlier_indices = np.where(outlier_mask)[0]
        outlier_values = data[outlier_mask]

        logger.info(f"Detected {len(outlier_indices)} outliers using {method} method")

        return outlier_indices, outlier_values

    def _to_array(self, data: Union[pd.Series, np.ndarray, List[float]]) -> np.ndarray:
        """Convert input to numpy array and remove NaN values."""
        if isinstance(data, pd.Series):
            data = data.dropna().values
        elif isinstance(data, list):
            data = np.array(data)

        # Remove NaN values
        data = data[~np.isnan(data)]

        return data


class TrendDetector:
    """
    Detect trends and patterns in time series data.

    Supports:
    - Linear trend detection
    - Changepoint detection
    - Moving averages
    - Exponential smoothing
    - Forecasting
    """

    def __init__(self):
        """Initialize trend detector."""
        logger.info("Initialized TrendDetector")

    def detect_trend(
        self,
        data: Union[pd.Series, np.ndarray, List[float]],
        dates: Optional[Union[pd.Series, List]] = None,
        significance_level: float = 0.05,
    ) -> TrendResult:
        """
        Detect trend in time series using linear regression.

        Args:
            data: Time series data
            dates: Optional date/time index
            significance_level: P-value threshold for significance

        Returns:
            TrendResult object with trend information
        """
        if isinstance(data, pd.Series):
            if dates is None and isinstance(data.index, pd.DatetimeIndex):
                dates = data.index
            data = data.values

        data = np.array(data)
        n = len(data)

        if n < 3:
            raise StatisticalError("Need at least 3 data points for trend detection")

        # Linear regression: y = mx + b
        x = np.arange(n)
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)

        # Determine trend direction
        if p_value < significance_level:
            direction = "up" if slope > 0 else "down"
        else:
            direction = "stable"

        # Calculate velocity (change per period)
        velocity = float(slope)
        mean_value = np.mean(data)
        velocity_pct = (velocity / mean_value * 100) if mean_value != 0 else 0.0

        # Detect changepoints using peaks in differences
        diffs = np.diff(data)
        peaks, _ = find_peaks(np.abs(diffs), height=np.std(diffs) * 2)
        changepoints = peaks.tolist()

        logger.info(
            f"Trend detected: direction={direction}, velocity={velocity:.4f}, "
            f"p={p_value:.6f}, r²={r_value**2:.4f}"
        )

        return TrendResult(
            direction=direction,
            velocity=velocity,
            velocity_pct=velocity_pct,
            changepoints=changepoints,
            p_value=float(p_value),
            r_squared=float(r_value**2),
        )

    def moving_average(
        self, data: Union[pd.Series, np.ndarray, List[float]], window: int
    ) -> np.ndarray:
        """
        Calculate moving average.

        Args:
            data: Time series data
            window: Window size for moving average

        Returns:
            Array of moving averages
        """
        data = np.array(data)

        if window > len(data):
            raise ValueError(
                f"Window size {window} larger than data length {len(data)}"
            )

        if window < 2:
            raise ValueError("Window size must be at least 2")

        return pd.Series(data).rolling(window=window).mean().values

    def exponential_smoothing(
        self,
        data: Union[pd.Series, np.ndarray, List[float]],
        alpha: float = 0.3,
    ) -> np.ndarray:
        """
        Apply exponential smoothing.

        Args:
            data: Time series data
            alpha: Smoothing parameter (0-1)

        Returns:
            Smoothed series
        """
        if not 0 <= alpha <= 1:
            raise ValueError("Alpha must be between 0 and 1")

        data = np.array(data)
        result = np.zeros_like(data)
        result[0] = data[0]

        for t in range(1, len(data)):
            result[t] = alpha * data[t] + (1 - alpha) * result[t - 1]

        return result

    def forecast(
        self,
        data: Union[pd.Series, np.ndarray, List[float]],
        periods: int,
        method: str = "linear",
        confidence: float = 0.95,
    ) -> pd.DataFrame:
        """
        Forecast future values.

        Args:
            data: Historical time series data
            periods: Number of periods to forecast
            method: 'linear' or 'exponential'
            confidence: Confidence level for prediction intervals

        Returns:
            DataFrame with forecast, lower_bound, upper_bound
        """
        data = np.array(data)
        n = len(data)

        if n < 3:
            raise StatisticalError("Need at least 3 data points for forecasting")

        if method == "linear":
            # Linear regression forecast
            x = np.arange(n)
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)

            # Predict future values
            future_x = np.arange(n, n + periods)
            forecast_values = slope * future_x + intercept

            # Calculate prediction intervals
            residuals = data - (slope * x + intercept)
            mse = np.sum(residuals**2) / (n - 2)
            se_forecast = np.sqrt(
                mse
                * (
                    1
                    + 1 / n
                    + (future_x - np.mean(x)) ** 2 / np.sum((x - np.mean(x)) ** 2)
                )
            )

            t_crit = stats.t.ppf((1 + confidence) / 2, n - 2)
            lower_bound = forecast_values - t_crit * se_forecast
            upper_bound = forecast_values + t_crit * se_forecast

        elif method == "exponential":
            # Simple exponential smoothing
            alpha = 0.3
            smoothed = self.exponential_smoothing(data, alpha)
            last_value = smoothed[-1]

            # Forecast as constant (simple exponential smoothing)
            forecast_values = np.full(periods, last_value)

            # Use historical std for intervals
            std = np.std(data)
            z_crit = stats.norm.ppf((1 + confidence) / 2)
            lower_bound = forecast_values - z_crit * std
            upper_bound = forecast_values + z_crit * std

        else:
            raise ValueError(f"Unknown forecast method: {method}")

        # Create forecast DataFrame
        forecast_df = pd.DataFrame(
            {
                "period": list(range(1, periods + 1)),
                "forecast": forecast_values,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
            }
        )

        logger.info(f"Generated {periods}-period forecast using {method} method")

        return forecast_df


# Example usage
if __name__ == "__main__":
    import json

    # Example 1: Descriptive statistics
    print("=" * 60)
    print("Example 1: Descriptive Statistics")
    print("=" * 60)

    data = [10, 12, 23, 23, 16, 23, 21, 16, 18, 19, 25, 28, 30]
    analyzer = StatisticalAnalyzer()
    stats_result = analyzer.describe(data)

    print(json.dumps(stats_result.to_dict(), indent=2))

    # Example 2: T-test
    print("\n" + "=" * 60)
    print("Example 2: Independent T-Test")
    print("=" * 60)

    group_a = [20, 22, 19, 21, 25, 23, 24, 26, 22, 21]
    group_b = [30, 32, 29, 31, 35, 33, 34, 36, 32, 31]

    test_result = analyzer.t_test(group_a, group_b)
    print(json.dumps(test_result.to_dict(), indent=2))

    # Example 3: Correlation
    print("\n" + "=" * 60)
    print("Example 3: Correlation Analysis")
    print("=" * 60)

    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    y = [2.1, 3.9, 6.2, 7.8, 10.1, 12.3, 13.9, 16.2, 17.8, 20.1]

    corr_result = analyzer.correlate(x, y, method="pearson")
    print(json.dumps(corr_result.to_dict(), indent=2))

    # Example 4: Trend detection
    print("\n" + "=" * 60)
    print("Example 4: Trend Detection")
    print("=" * 60)

    trend_data = [10, 12, 14, 13, 15, 17, 19, 18, 20, 22, 24, 23, 25]
    detector = TrendDetector()
    trend_result = detector.detect_trend(trend_data)

    print(json.dumps(trend_result.to_dict(), indent=2))

    # Example 5: Forecasting
    print("\n" + "=" * 60)
    print("Example 5: Forecasting")
    print("=" * 60)

    forecast_df = detector.forecast(trend_data, periods=5, method="linear")
    print(forecast_df.to_string(index=False))

    # Example 6: Outlier detection
    print("\n" + "=" * 60)
    print("Example 6: Outlier Detection")
    print("=" * 60)

    data_with_outliers = [10, 12, 11, 13, 12, 100, 14, 15, 13, 12, 14, 200]
    outlier_indices, outlier_values = analyzer.detect_outliers(
        data_with_outliers, method="iqr"
    )

    print(f"Outlier indices: {outlier_indices.tolist()}")
    print(f"Outlier values: {outlier_values.tolist()}")
