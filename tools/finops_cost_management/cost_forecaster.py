"""
Cost forecasting using time series analysis.

This module provides time series forecasting capabilities for cloud cost
prediction using Prophet, linear regression, and exponential smoothing.
Includes trend analysis, seasonality detection, budget burn rate calculation,
and accuracy metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from prophet import Prophet
from pydantic import BaseModel, Field, field_validator
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

logger = logging.getLogger(__name__)


class ForecastConfig(BaseModel):
    """Configuration for cost forecaster."""

    forecast_days: int = Field(
        default=30, description="Number of days to forecast", ge=1, le=365
    )
    confidence_level: float = Field(
        default=0.95, description="Confidence level for intervals", ge=0.5, le=0.99
    )
    include_seasonality: bool = Field(
        default=True, description="Include seasonality in forecast"
    )
    include_holidays: bool = Field(default=False, description="Include holiday effects")
    model_type: str = Field(default="prophet", description="Forecasting model type")
    weekly_seasonality: bool = Field(default=True, description="Model weekly patterns")
    monthly_seasonality: bool = Field(
        default=True, description="Model monthly patterns"
    )
    changepoint_prior_scale: float = Field(
        default=0.05, description="Prophet changepoint prior scale"
    )
    seasonality_prior_scale: float = Field(
        default=10.0, description="Prophet seasonality prior scale"
    )

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        """Validate model type."""
        allowed = ["prophet", "linear", "exponential"]
        if v not in allowed:
            raise ValueError(f"model_type must be one of {allowed}")
        return v

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence level."""
        if not 0.5 <= v <= 0.99:
            raise ValueError("confidence_level must be between 0.5 and 0.99")
        return v


class CostData(BaseModel):
    """Single cost data point."""

    date: datetime
    cost: float = Field(ge=0.0)
    provider: Optional[str] = None
    service: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)


class Forecast(BaseModel):
    """Single forecast data point."""

    date: datetime
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("lower_bound", "upper_bound")
    @classmethod
    def validate_bounds(cls, v: float) -> float:
        """Ensure bounds are non-negative."""
        return max(0.0, v)


class TrendType(str):
    """Trend direction types."""

    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"


class ForecastResult(BaseModel):
    """Complete forecast result with metadata."""

    forecasts: List[Forecast]
    total_predicted: float = Field(ge=0.0)
    trend: str
    seasonality_detected: bool
    accuracy_metrics: Dict[str, float] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    config: ForecastConfig
    historical_days: int
    model_type: str

    @property
    def daily_average(self) -> float:
        """Calculate daily average predicted cost."""
        if not self.forecasts:
            return 0.0
        return self.total_predicted / len(self.forecasts)

    @property
    def monthly_projected(self) -> float:
        """Calculate 30-day projected cost."""
        return self.daily_average * 30

    @property
    def annual_projected(self) -> float:
        """Calculate annual projected cost."""
        return self.daily_average * 365


class CostForecasterError(Exception):
    """Base exception for cost forecaster operations."""

    pass


class CostForecaster:
    """
    Time series cost forecaster.

    Uses Prophet, linear regression, or exponential smoothing to predict
    future costs based on historical spending patterns.
    """

    def __init__(self, config: Optional[ForecastConfig] = None):
        """
        Initialize cost forecaster.

        Args:
            config: Forecaster configuration
        """
        self.config = config or ForecastConfig()
        self._prophet_model: Optional[Prophet] = None
        self._linear_model: Optional[LinearRegression] = None

        logger.info(f"CostForecaster initialized with model: {self.config.model_type}")

    def forecast(
        self,
        historical_data: List[CostData],
        days: Optional[int] = None,
    ) -> ForecastResult:
        """
        Generate cost forecast.

        Args:
            historical_data: Historical cost data points
            days: Number of days to forecast (overrides config)

        Returns:
            ForecastResult with predictions and metadata

        Raises:
            CostForecasterError: If forecasting fails
        """
        if not historical_data:
            raise CostForecasterError("No historical data provided")

        if len(historical_data) < 7:
            logger.warning(
                f"Only {len(historical_data)} days of data. "
                "Recommend at least 7 days for accurate forecasting."
            )

        days = days or self.config.forecast_days

        logger.info(
            f"Forecasting {days} days using {len(historical_data)} "
            f"historical data points"
        )

        # Convert to DataFrame
        df = self._prepare_dataframe(historical_data)

        # Detect trend and seasonality
        trend = self._detect_trend(df)
        seasonality = self._detect_seasonality(df)

        logger.info(f"Detected trend: {trend}, seasonality: {seasonality}")

        # Generate forecast based on model type
        if self.config.model_type == "prophet":
            forecast_df = self._forecast_prophet(df, days)
        elif self.config.model_type == "linear":
            forecast_df = self._forecast_linear(df, days)
        elif self.config.model_type == "exponential":
            forecast_df = self._forecast_exponential(df, days)
        else:
            raise CostForecasterError(f"Unknown model type: {self.config.model_type}")

        # Convert to Forecast objects
        forecasts = self._dataframe_to_forecasts(forecast_df)

        # Calculate accuracy metrics if we have enough data
        accuracy_metrics = {}
        if len(df) >= 14:
            accuracy_metrics = self._calculate_backtest_accuracy(df)

        # Calculate total predicted cost
        total_predicted = sum(f.predicted_cost for f in forecasts)

        result = ForecastResult(
            forecasts=forecasts,
            total_predicted=round(total_predicted, 2),
            trend=trend,
            seasonality_detected=seasonality,
            accuracy_metrics=accuracy_metrics,
            config=self.config,
            historical_days=len(historical_data),
            model_type=self.config.model_type,
        )

        logger.info(
            f"Forecast complete. Total predicted: ${total_predicted:.2f} "
            f"over {days} days"
        )

        return result

    def _prepare_dataframe(self, data: List[CostData]) -> pd.DataFrame:
        """Convert CostData list to pandas DataFrame."""
        records = []
        for item in data:
            records.append({"ds": item.date, "y": item.cost})

        df = pd.DataFrame(records)
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.sort_values("ds")

        # Remove duplicates, keep last
        df = df.drop_duplicates(subset=["ds"], keep="last")

        return df

    def _forecast_prophet(self, df: pd.DataFrame, days: int) -> pd.DataFrame:
        """
        Forecast using Facebook Prophet.

        Args:
            df: Historical data with 'ds' and 'y' columns
            days: Number of days to forecast

        Returns:
            DataFrame with forecast results
        """
        try:
            # Initialize Prophet model
            model = Prophet(
                changepoint_prior_scale=self.config.changepoint_prior_scale,
                seasonality_prior_scale=self.config.seasonality_prior_scale,
                interval_width=self.config.confidence_level,
                daily_seasonality=False,
                weekly_seasonality=self.config.weekly_seasonality,
                yearly_seasonality=False,
            )

            # Add monthly seasonality if requested
            if self.config.monthly_seasonality and self.config.include_seasonality:
                model.add_seasonality(name="monthly", period=30.5, fourier_order=5)

            # Fit model (suppress output)
            with pd.option_context("mode.chained_assignment", None):
                model.fit(df)

            self._prophet_model = model

            # Create future dataframe
            future = model.make_future_dataframe(periods=days)

            # Generate forecast
            forecast = model.predict(future)

            # Extract only future dates
            last_date = df["ds"].max()
            forecast = forecast[forecast["ds"] > last_date].copy()

            # Ensure non-negative predictions
            forecast["yhat"] = forecast["yhat"].clip(lower=0)
            forecast["yhat_lower"] = forecast["yhat_lower"].clip(lower=0)
            forecast["yhat_upper"] = forecast["yhat_upper"].clip(lower=0)

            logger.debug(f"Prophet forecast generated for {len(forecast)} days")

            return forecast

        except Exception as e:
            logger.error(f"Prophet forecasting failed: {e}", exc_info=True)
            raise CostForecasterError(f"Prophet forecasting failed: {e}") from e

    def _forecast_linear(self, df: pd.DataFrame, days: int) -> pd.DataFrame:
        """
        Forecast using linear regression.

        Args:
            df: Historical data with 'ds' and 'y' columns
            days: Number of days to forecast

        Returns:
            DataFrame with forecast results
        """
        try:
            # Convert dates to numeric (days since start)
            df = df.copy()
            start_date = df["ds"].min()
            df["x"] = (df["ds"] - start_date).dt.total_seconds() / 86400

            # Fit linear regression
            X = df[["x"]].values
            y = df["y"].values

            model = LinearRegression()
            model.fit(X, y)
            self._linear_model = model

            # Generate future dates
            last_date = df["ds"].max()
            future_dates = [last_date + timedelta(days=i + 1) for i in range(days)]

            # Convert to numeric
            future_x = np.array(
                [(d - start_date).total_seconds() / 86400 for d in future_dates]
            ).reshape(-1, 1)

            # Predict
            predictions = model.predict(future_x)
            predictions = np.maximum(predictions, 0)  # Ensure non-negative

            # Calculate confidence intervals (simple approach)
            residuals = y - model.predict(X)
            std_error = np.std(residuals)
            margin = 1.96 * std_error  # 95% confidence

            # Create forecast dataframe
            forecast = pd.DataFrame(
                {
                    "ds": future_dates,
                    "yhat": predictions,
                    "yhat_lower": np.maximum(predictions - margin, 0),
                    "yhat_upper": predictions + margin,
                }
            )

            logger.debug(f"Linear forecast generated for {len(forecast)} days")

            return forecast

        except Exception as e:
            logger.error(f"Linear forecasting failed: {e}", exc_info=True)
            raise CostForecasterError(f"Linear forecasting failed: {e}") from e

    def _forecast_exponential(self, df: pd.DataFrame, days: int) -> pd.DataFrame:
        """
        Forecast using exponential smoothing.

        Args:
            df: Historical data with 'ds' and 'y' columns
            days: Number of days to forecast

        Returns:
            DataFrame with forecast results
        """
        try:
            # Simple exponential smoothing
            alpha = 0.3  # Smoothing parameter

            y = df["y"].values
            smoothed = [y[0]]

            # Apply exponential smoothing
            for i in range(1, len(y)):
                smoothed.append(alpha * y[i] + (1 - alpha) * smoothed[-1])

            # Use last smoothed value for forecast
            last_smoothed = smoothed[-1]

            # Calculate trend from last few points
            window = min(7, len(y))
            recent_trend = (y[-1] - y[-window]) / window

            # Generate forecast
            last_date = df["ds"].max()
            future_dates = [last_date + timedelta(days=i + 1) for i in range(days)]

            predictions = []
            for i in range(days):
                pred = last_smoothed + recent_trend * (i + 1)
                predictions.append(max(pred, 0))

            # Calculate confidence intervals
            std_error = np.std(y - np.array(smoothed[: len(y)]))
            margin = 1.96 * std_error

            forecast = pd.DataFrame(
                {
                    "ds": future_dates,
                    "yhat": predictions,
                    "yhat_lower": np.maximum(np.array(predictions) - margin, 0),
                    "yhat_upper": np.array(predictions) + margin,
                }
            )

            logger.debug(
                f"Exponential smoothing forecast generated for {len(forecast)} days"
            )

            return forecast

        except Exception as e:
            logger.error(f"Exponential forecasting failed: {e}", exc_info=True)
            raise CostForecasterError(f"Exponential forecasting failed: {e}") from e

    def _dataframe_to_forecasts(self, df: pd.DataFrame) -> List[Forecast]:
        """Convert forecast DataFrame to Forecast objects."""
        forecasts = []

        for _, row in df.iterrows():
            forecast = Forecast(
                date=pd.Timestamp(row["ds"]).to_pydatetime(),
                predicted_cost=round(float(row["yhat"]), 2),
                lower_bound=round(float(row["yhat_lower"]), 2),
                upper_bound=round(float(row["yhat_upper"]), 2),
                confidence=self.config.confidence_level,
            )
            forecasts.append(forecast)

        return forecasts

    def _detect_trend(self, df: pd.DataFrame) -> str:
        """
        Detect overall trend in historical data.

        Args:
            df: Historical data with 'ds' and 'y' columns

        Returns:
            Trend type (INCREASING, DECREASING, STABLE)
        """
        if len(df) < 3:
            return TrendType.STABLE

        # Calculate linear regression slope
        df = df.copy()
        df["x"] = range(len(df))
        X = df[["x"]].values
        y = df["y"].values

        model = LinearRegression()
        model.fit(X, y)

        slope = model.coef_[0]
        mean_y = np.mean(y)

        # Normalize slope by mean to get percentage change
        if mean_y > 0:
            normalized_slope = slope / mean_y
        else:
            normalized_slope = 0

        # Classify trend
        if normalized_slope > 0.02:  # >2% increase per day
            return TrendType.INCREASING
        elif normalized_slope < -0.02:  # >2% decrease per day
            return TrendType.DECREASING
        else:
            return TrendType.STABLE

    def _detect_seasonality(self, df: pd.DataFrame) -> bool:
        """
        Detect if data has significant seasonality.

        Args:
            df: Historical data with 'ds' and 'y' columns

        Returns:
            True if seasonality detected
        """
        if len(df) < 14:  # Need at least 2 weeks for weekly seasonality
            return False

        try:
            # Check for weekly pattern using autocorrelation
            y = df["y"].values

            # Detrend by subtracting moving average
            window = 7
            if len(y) >= window:
                ma = pd.Series(y).rolling(window=window, center=True).mean()
                detrended = y - ma.fillna(method="bfill").fillna(method="ffill")

                # Calculate autocorrelation at lag 7 (weekly)
                if len(detrended) >= 14:
                    lag_7 = self._autocorrelation(detrended, 7)

                    # Significant if autocorrelation > 0.3
                    if abs(lag_7) > 0.3:
                        logger.debug(
                            f"Weekly seasonality detected (autocorr={lag_7:.3f})"
                        )
                        return True

        except Exception as e:
            logger.debug(f"Seasonality detection failed: {e}")

        return False

    def _autocorrelation(self, x: np.ndarray, lag: int) -> float:
        """Calculate autocorrelation at given lag."""
        n = len(x)
        if lag >= n:
            return 0.0

        x = x - np.mean(x)
        c0 = np.sum(x**2) / n
        c_lag = np.sum(x[:-lag] * x[lag:]) / n

        if c0 == 0:
            return 0.0

        return c_lag / c0

    def _calculate_backtest_accuracy(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate accuracy metrics using backtesting.

        Args:
            df: Historical data

        Returns:
            Dictionary with MAE, RMSE, MAPE
        """
        try:
            # Use last 7 days as test set
            test_days = min(7, len(df) // 3)
            train_df = df.iloc[:-test_days]
            test_df = df.iloc[-test_days:]

            # Generate forecast for test period
            if self.config.model_type == "prophet":
                forecast_df = self._forecast_prophet(train_df, test_days)
            elif self.config.model_type == "linear":
                forecast_df = self._forecast_linear(train_df, test_days)
            else:
                forecast_df = self._forecast_exponential(train_df, test_days)

            # Merge with actual values
            forecast_df = forecast_df.merge(
                test_df, on="ds", how="inner", suffixes=("_pred", "_actual")
            )

            if len(forecast_df) == 0:
                return {}

            actual = forecast_df["y"].values
            predicted = forecast_df["yhat"].values

            # Calculate metrics
            mae = mean_absolute_error(actual, predicted)
            rmse = np.sqrt(mean_squared_error(actual, predicted))

            # MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((actual - predicted) / (actual + 1e-10))) * 100

            return {
                "mae": round(float(mae), 2),
                "rmse": round(float(rmse), 2),
                "mape": round(float(mape), 2),
            }

        except Exception as e:
            logger.debug(f"Backtest accuracy calculation failed: {e}")
            return {}

    def calculate_burn_rate(
        self, historical_data: List[CostData], budget: float
    ) -> Dict[str, Any]:
        """
        Calculate budget burn rate and depletion date.

        Args:
            historical_data: Historical cost data
            budget: Total budget amount

        Returns:
            Dictionary with burn rate metrics
        """
        if not historical_data or budget <= 0:
            return {
                "error": "Invalid input data",
            }

        # Convert to DataFrame
        df = self._prepare_dataframe(historical_data)

        # Calculate daily average
        daily_avg = df["y"].mean()

        # Calculate total spent
        total_spent = df["y"].sum()

        # Calculate remaining budget
        remaining = budget - total_spent

        # Calculate days until depletion
        if daily_avg > 0:
            days_remaining = remaining / daily_avg
        else:
            days_remaining = float("inf")

        # Calculate depletion date
        if days_remaining < float("inf"):
            last_date = df["ds"].max()
            depletion_date = last_date + timedelta(days=int(days_remaining))
        else:
            depletion_date = None

        # Calculate burn rate percentage
        budget_used_pct = (total_spent / budget) * 100 if budget > 0 else 0

        # Calculate trend
        trend = self._detect_trend(df)

        result = {
            "budget": round(budget, 2),
            "total_spent": round(total_spent, 2),
            "remaining": round(remaining, 2),
            "budget_used_percentage": round(budget_used_pct, 2),
            "daily_average": round(daily_avg, 2),
            "days_remaining": (
                round(days_remaining, 1) if days_remaining < float("inf") else None
            ),
            "estimated_depletion_date": (
                depletion_date.isoformat() if depletion_date else None
            ),
            "trend": trend,
            "status": self._get_burn_rate_status(budget_used_pct, days_remaining),
        }

        logger.info(
            f"Burn rate calculated: {budget_used_pct:.1f}% used, "
            f"{days_remaining:.0f} days remaining"
        )

        return result

    def _get_burn_rate_status(
        self, budget_used_pct: float, days_remaining: float
    ) -> str:
        """Determine burn rate status."""
        if budget_used_pct >= 100:
            return "EXCEEDED"
        elif budget_used_pct >= 90:
            return "CRITICAL"
        elif budget_used_pct >= 75:
            return "WARNING"
        elif days_remaining < 7:
            return "WARNING"
        else:
            return "HEALTHY"

    def calculate_accuracy(
        self, actual: List[float], predicted: List[float]
    ) -> Dict[str, float]:
        """
        Calculate forecast accuracy metrics.

        Args:
            actual: Actual cost values
            predicted: Predicted cost values

        Returns:
            Dictionary with accuracy metrics (MAE, RMSE, MAPE)
        """
        if not actual or not predicted or len(actual) != len(predicted):
            raise ValueError(
                "Actual and predicted must be non-empty equal-length lists"
            )

        actual_arr = np.array(actual)
        predicted_arr = np.array(predicted)

        # Mean Absolute Error
        mae = mean_absolute_error(actual_arr, predicted_arr)

        # Root Mean Squared Error
        rmse = np.sqrt(mean_squared_error(actual_arr, predicted_arr))

        # Mean Absolute Percentage Error
        mape = (
            np.mean(np.abs((actual_arr - predicted_arr) / (actual_arr + 1e-10))) * 100
        )

        # R-squared
        ss_res = np.sum((actual_arr - predicted_arr) ** 2)
        ss_tot = np.sum((actual_arr - np.mean(actual_arr)) ** 2)
        r2 = 1 - (ss_res / (ss_tot + 1e-10))

        return {
            "mae": round(float(mae), 2),
            "rmse": round(float(rmse), 2),
            "mape": round(float(mape), 2),
            "r2": round(float(r2), 3),
        }

    def get_forecast_report(self, result: ForecastResult) -> str:
        """
        Generate human-readable forecast report.

        Args:
            result: Forecast result to report

        Returns:
            Formatted report string
        """
        lines = ["=" * 60]
        lines.append("COST FORECAST REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append(
            f"Generated: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        lines.append(f"Model: {result.model_type.upper()}")
        lines.append(f"Historical Data: {result.historical_days} days")
        lines.append(f"Forecast Period: {len(result.forecasts)} days")
        lines.append("")

        # Predictions
        lines.append("PREDICTIONS:")
        lines.append(f"  Total Predicted: ${result.total_predicted:,.2f}")
        lines.append(f"  Daily Average: ${result.daily_average:,.2f}")
        lines.append(f"  30-Day Projected: ${result.monthly_projected:,.2f}")
        lines.append(f"  Annual Projected: ${result.annual_projected:,.2f}")
        lines.append("")

        # Trend Analysis
        lines.append("TREND ANALYSIS:")
        lines.append(f"  Trend: {result.trend}")
        lines.append(f"  Seasonality: {'Yes' if result.seasonality_detected else 'No'}")
        lines.append("")

        # Accuracy Metrics
        if result.accuracy_metrics:
            lines.append("ACCURACY METRICS (Backtest):")
            lines.append(f"  MAE: ${result.accuracy_metrics.get('mae', 0):.2f}")
            lines.append(f"  RMSE: ${result.accuracy_metrics.get('rmse', 0):.2f}")
            lines.append(f"  MAPE: {result.accuracy_metrics.get('mape', 0):.2f}%")
            lines.append("")

        # Sample Forecasts
        lines.append("SAMPLE FORECASTS (First 7 Days):")
        for i, forecast in enumerate(result.forecasts[:7]):
            lines.append(
                f"  {forecast.date.strftime('%Y-%m-%d')}: "
                f"${forecast.predicted_cost:,.2f} "
                f"(${forecast.lower_bound:,.2f} - ${forecast.upper_bound:,.2f})"
            )

        if len(result.forecasts) > 7:
            lines.append(f"  ... ({len(result.forecasts) - 7} more days)")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def export_forecast(self, result: ForecastResult, format: str = "json") -> str:
        """
        Export forecast to specified format.

        Args:
            result: Forecast result to export
            format: Export format (json, csv, markdown)

        Returns:
            Formatted string representation
        """
        if format == "json":
            import json

            return json.dumps(result.model_dump(mode="json"), indent=2)

        elif format == "csv":
            records = []
            for forecast in result.forecasts:
                records.append(
                    {
                        "Date": forecast.date.strftime("%Y-%m-%d"),
                        "Predicted Cost": forecast.predicted_cost,
                        "Lower Bound": forecast.lower_bound,
                        "Upper Bound": forecast.upper_bound,
                        "Confidence": f"{forecast.confidence:.0%}",
                    }
                )

            df = pd.DataFrame(records)
            return df.to_csv(index=False)

        elif format == "markdown":
            return self.get_forecast_report(result)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def compare_models(
        self, historical_data: List[CostData], days: int = 30
    ) -> Dict[str, Any]:
        """
        Compare different forecasting models.

        Args:
            historical_data: Historical cost data
            days: Number of days to forecast

        Returns:
            Dictionary with model comparison results
        """
        models = ["prophet", "linear", "exponential"]
        results = {}

        for model in models:
            try:
                # Create config for this model
                config = ForecastConfig(
                    model_type=model,
                    forecast_days=days,
                    confidence_level=self.config.confidence_level,
                )

                # Create forecaster
                forecaster = CostForecaster(config)

                # Generate forecast
                result = forecaster.forecast(historical_data, days)

                results[model] = {
                    "total_predicted": result.total_predicted,
                    "daily_average": result.daily_average,
                    "trend": result.trend,
                    "accuracy_metrics": result.accuracy_metrics,
                }

                logger.info(f"Model {model}: ${result.total_predicted:.2f}")

            except Exception as e:
                logger.error(f"Error forecasting with {model}: {e}")
                results[model] = {"error": str(e)}

        return results

    def analyze_cost_patterns(self, historical_data: List[CostData]) -> Dict[str, Any]:
        """
        Analyze cost patterns and provide insights.

        Args:
            historical_data: Historical cost data

        Returns:
            Dictionary with pattern analysis results
        """
        if not historical_data:
            return {"error": "No data provided"}

        df = self._prepare_dataframe(historical_data)

        # Calculate basic statistics
        mean_cost = df["y"].mean()
        median_cost = df["y"].median()
        std_cost = df["y"].std()
        min_cost = df["y"].min()
        max_cost = df["y"].max()

        # Calculate coefficient of variation
        cv = (std_cost / mean_cost) * 100 if mean_cost > 0 else 0

        # Identify anomalous days (>2 standard deviations from mean)
        threshold = mean_cost + (2 * std_cost)
        anomalous_days = df[df["y"] > threshold]

        # Day of week analysis
        df["day_of_week"] = df["ds"].dt.day_name()
        dow_avg = df.groupby("day_of_week")["y"].mean().to_dict()

        # Find most/least expensive days
        most_expensive = df.nlargest(3, "y")[["ds", "y"]].to_dict("records")
        least_expensive = df.nsmallest(3, "y")[["ds", "y"]].to_dict("records")

        # Calculate growth rate
        if len(df) >= 7:
            first_week = df.head(7)["y"].mean()
            last_week = df.tail(7)["y"].mean()
            growth_rate = (
                ((last_week - first_week) / first_week) * 100 if first_week > 0 else 0
            )
        else:
            growth_rate = 0

        # Volatility analysis
        volatility = self._calculate_volatility(df)

        return {
            "statistics": {
                "mean": round(mean_cost, 2),
                "median": round(median_cost, 2),
                "std_dev": round(std_cost, 2),
                "min": round(min_cost, 2),
                "max": round(max_cost, 2),
                "coefficient_of_variation": round(cv, 2),
            },
            "anomalies": {
                "count": len(anomalous_days),
                "dates": [
                    d.strftime("%Y-%m-%d") for d in anomalous_days["ds"].tolist()
                ],
            },
            "day_of_week_average": {k: round(v, 2) for k, v in dow_avg.items()},
            "extremes": {
                "most_expensive": [
                    {
                        "date": r["ds"].strftime("%Y-%m-%d"),
                        "cost": round(r["y"], 2),
                    }
                    for r in most_expensive
                ],
                "least_expensive": [
                    {
                        "date": r["ds"].strftime("%Y-%m-%d"),
                        "cost": round(r["y"], 2),
                    }
                    for r in least_expensive
                ],
            },
            "growth_rate_percent": round(growth_rate, 2),
            "volatility": volatility,
        }

    def _calculate_volatility(self, df: pd.DataFrame) -> str:
        """Calculate cost volatility level."""
        if len(df) < 2:
            return "UNKNOWN"

        std = df["y"].std()
        mean = df["y"].mean()

        cv = (std / mean) * 100 if mean > 0 else 0

        if cv < 10:
            return "LOW"
        elif cv < 30:
            return "MODERATE"
        else:
            return "HIGH"

    def generate_budget_alert(
        self, current_spend: float, budget: float, days_elapsed: int, total_days: int
    ) -> Dict[str, Any]:
        """
        Generate budget alert based on current spending rate.

        Args:
            current_spend: Current total spend
            budget: Total budget
            days_elapsed: Days elapsed in budget period
            total_days: Total days in budget period

        Returns:
            Dictionary with alert information
        """
        if days_elapsed <= 0 or total_days <= 0:
            return {"error": "Invalid time periods"}

        # Calculate expected spend based on linear consumption
        expected_spend = (days_elapsed / total_days) * budget

        # Calculate actual vs expected
        spend_ratio = current_spend / expected_spend if expected_spend > 0 else 0

        # Calculate projected end-of-period spend
        daily_rate = current_spend / days_elapsed if days_elapsed > 0 else 0
        projected_total = daily_rate * total_days

        # Calculate overspend amount
        projected_overspend = projected_total - budget

        # Determine alert level
        if spend_ratio >= 1.5:
            alert_level = "CRITICAL"
            message = "Spending 50%+ over expected rate"
        elif spend_ratio >= 1.25:
            alert_level = "WARNING"
            message = "Spending 25%+ over expected rate"
        elif spend_ratio >= 1.1:
            alert_level = "CAUTION"
            message = "Spending 10%+ over expected rate"
        else:
            alert_level = "NORMAL"
            message = "Spending on track"

        # Calculate days until budget exhaustion
        if daily_rate > 0:
            remaining_budget = budget - current_spend
            days_until_exhaustion = remaining_budget / daily_rate
        else:
            days_until_exhaustion = float("inf")

        return {
            "alert_level": alert_level,
            "message": message,
            "current_spend": round(current_spend, 2),
            "budget": round(budget, 2),
            "expected_spend": round(expected_spend, 2),
            "spend_ratio": round(spend_ratio, 2),
            "budget_used_percent": round((current_spend / budget) * 100, 2),
            "projected_total": round(projected_total, 2),
            "projected_overspend": (
                round(projected_overspend, 2) if projected_overspend > 0 else 0
            ),
            "days_elapsed": days_elapsed,
            "days_remaining": total_days - days_elapsed,
            "days_until_exhaustion": (
                round(days_until_exhaustion, 1)
                if days_until_exhaustion < float("inf")
                else None
            ),
        }

    def forecast_with_scenarios(
        self,
        historical_data: List[CostData],
        days: int = 30,
    ) -> Dict[str, ForecastResult]:
        """
        Generate forecasts for different scenarios.

        Args:
            historical_data: Historical cost data
            days: Number of days to forecast

        Returns:
            Dictionary with best-case, expected, and worst-case forecasts
        """
        # Base forecast
        base_result = self.forecast(historical_data, days)

        # Calculate adjustment factors
        df = self._prepare_dataframe(historical_data)
        std = df["y"].std()

        scenarios = {}

        # Best case: -1 std dev
        best_case_adjustment = -std
        best_forecasts = []
        for f in base_result.forecasts:
            adjusted = max(0, f.predicted_cost + best_case_adjustment)
            best_forecasts.append(
                Forecast(
                    date=f.date,
                    predicted_cost=round(adjusted, 2),
                    lower_bound=round(max(0, f.lower_bound + best_case_adjustment), 2),
                    upper_bound=round(f.upper_bound + best_case_adjustment, 2),
                    confidence=f.confidence,
                )
            )

        scenarios["best_case"] = ForecastResult(
            forecasts=best_forecasts,
            total_predicted=sum(f.predicted_cost for f in best_forecasts),
            trend=base_result.trend,
            seasonality_detected=base_result.seasonality_detected,
            accuracy_metrics=base_result.accuracy_metrics,
            config=base_result.config,
            historical_days=base_result.historical_days,
            model_type=base_result.model_type,
        )

        # Expected case: base result
        scenarios["expected"] = base_result

        # Worst case: +1 std dev
        worst_case_adjustment = std
        worst_forecasts = []
        for f in base_result.forecasts:
            adjusted = f.predicted_cost + worst_case_adjustment
            worst_forecasts.append(
                Forecast(
                    date=f.date,
                    predicted_cost=round(adjusted, 2),
                    lower_bound=round(max(0, f.lower_bound + worst_case_adjustment), 2),
                    upper_bound=round(f.upper_bound + worst_case_adjustment, 2),
                    confidence=f.confidence,
                )
            )

        scenarios["worst_case"] = ForecastResult(
            forecasts=worst_forecasts,
            total_predicted=sum(f.predicted_cost for f in worst_forecasts),
            trend=base_result.trend,
            seasonality_detected=base_result.seasonality_detected,
            accuracy_metrics=base_result.accuracy_metrics,
            config=base_result.config,
            historical_days=base_result.historical_days,
            model_type=base_result.model_type,
        )

        logger.info(
            f"Scenario forecasts: Best=${scenarios['best_case'].total_predicted:.2f}, "
            f"Expected=${scenarios['expected'].total_predicted:.2f}, "
            f"Worst=${scenarios['worst_case'].total_predicted:.2f}"
        )

        return scenarios

    def detect_anomalies_in_forecast(
        self, historical_data: List[CostData], forecast: ForecastResult
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in forecast compared to historical patterns.

        Args:
            historical_data: Historical cost data
            forecast: Forecast result to analyze

        Returns:
            List of detected anomalies
        """
        df = self._prepare_dataframe(historical_data)

        # Calculate historical statistics
        mean = df["y"].mean()
        std = df["y"].std()
        threshold_high = mean + (2 * std)
        threshold_low = max(0, mean - (2 * std))

        anomalies = []

        for f in forecast.forecasts:
            if f.predicted_cost > threshold_high:
                anomalies.append(
                    {
                        "date": f.date.strftime("%Y-%m-%d"),
                        "predicted_cost": f.predicted_cost,
                        "type": "HIGH",
                        "deviation_from_mean": round(f.predicted_cost - mean, 2),
                        "deviation_std": round((f.predicted_cost - mean) / std, 2),
                        "message": f"Predicted cost ${f.predicted_cost:.2f} is "
                        f"{((f.predicted_cost - mean) / mean * 100):.1f}% "
                        "above historical mean",
                    }
                )
            elif f.predicted_cost < threshold_low:
                anomalies.append(
                    {
                        "date": f.date.strftime("%Y-%m-%d"),
                        "predicted_cost": f.predicted_cost,
                        "type": "LOW",
                        "deviation_from_mean": round(f.predicted_cost - mean, 2),
                        "deviation_std": round((f.predicted_cost - mean) / std, 2),
                        "message": f"Predicted cost ${f.predicted_cost:.2f} is "
                        f"{((mean - f.predicted_cost) / mean * 100):.1f}% "
                        "below historical mean",
                    }
                )

        return anomalies

    def calculate_forecast_confidence_bands(
        self, historical_data: List[CostData], forecast: ForecastResult
    ) -> Dict[str, Any]:
        """
        Calculate multiple confidence bands for forecast.

        Args:
            historical_data: Historical cost data
            forecast: Forecast result

        Returns:
            Dictionary with multiple confidence levels
        """
        df = self._prepare_dataframe(historical_data)
        std = df["y"].std()

        # Calculate bands at different confidence levels
        confidence_levels = [0.68, 0.90, 0.95, 0.99]
        z_scores = [1.0, 1.645, 1.96, 2.576]

        bands = {}

        for conf, z in zip(confidence_levels, z_scores):
            level_bands = []
            for f in forecast.forecasts:
                margin = z * std
                level_bands.append(
                    {
                        "date": f.date.strftime("%Y-%m-%d"),
                        "predicted": f.predicted_cost,
                        "lower": round(max(0, f.predicted_cost - margin), 2),
                        "upper": round(f.predicted_cost + margin, 2),
                    }
                )

            bands[f"{int(conf * 100)}%"] = level_bands

        return bands
