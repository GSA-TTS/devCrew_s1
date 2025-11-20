"""
Token and Cost Tracking Module.

This module provides token counting, cost estimation,
usage tracking, and budget monitoring.

Protocol Coverage:
- P-RESOURCE: Resource allocation and optimization
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported model types with pricing."""
    # OpenAI models
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_35_TURBO = "gpt-3.5-turbo"

    # Anthropic models
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_35_SONNET = "claude-3-5-sonnet-20240620"


# Pricing per 1M tokens (as of 2024)
MODEL_PRICING = {
    ModelType.GPT_4: {"input": 30.0, "output": 60.0},
    ModelType.GPT_4_TURBO: {"input": 10.0, "output": 30.0},
    ModelType.GPT_4O: {"input": 5.0, "output": 15.0},
    ModelType.GPT_35_TURBO: {"input": 0.5, "output": 1.5},

    ModelType.CLAUDE_3_OPUS: {"input": 15.0, "output": 75.0},
    ModelType.CLAUDE_3_SONNET: {"input": 3.0, "output": 15.0},
    ModelType.CLAUDE_3_HAIKU: {"input": 0.25, "output": 1.25},
    ModelType.CLAUDE_35_SONNET: {"input": 3.0, "output": 15.0}
}


@dataclass
class TokenUsage:
    """Token usage for a single operation."""
    operation_id: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_id": self.operation_id,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class CostEstimate:
    """Cost estimate for token usage."""
    input_cost: float
    output_cost: float
    total_cost: float
    model: str
    currency: str = "USD"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "total_cost": self.total_cost,
            "model": self.model,
            "currency": self.currency
        }


@dataclass
class BudgetAlert:
    """Budget alert notification."""
    alert_id: str
    timestamp: datetime
    message: str
    severity: str  # "warning" or "critical"
    current_cost: float
    budget_limit: float
    utilization: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "severity": self.severity,
            "current_cost": self.current_cost,
            "budget_limit": self.budget_limit,
            "utilization": self.utilization
        }


class TokenCounter:
    """Token counter using tiktoken."""

    def __init__(self):
        """Initialize token counter."""
        self._tiktoken_encoders = {}

    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count
            model: Model to use for encoding

        Returns:
            Token count
        """
        try:
            import tiktoken

            # Get or create encoder
            if model not in self._tiktoken_encoders:
                try:
                    self._tiktoken_encoders[model] = tiktoken.encoding_for_model(model)
                except KeyError:
                    # Fallback to cl100k_base for unknown models
                    self._tiktoken_encoders[model] = tiktoken.get_encoding("cl100k_base")

            encoder = self._tiktoken_encoders[model]
            return len(encoder.encode(text))

        except ImportError:
            logger.warning("tiktoken not installed, using word-based estimation")
            return self._estimate_tokens(text)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return self._estimate_tokens(text)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens using word count."""
        # Rough estimate: 1 token ≈ 0.75 words
        words = len(text.split())
        return int(words * 1.3)


class CostTracker:
    """
    Tracks token usage and costs with budget monitoring.
    """

    def __init__(
        self,
        budget_limit: Optional[float] = None,
        warning_threshold: float = 0.8,
        alert_callback: Optional[Any] = None
    ):
        """
        Initialize cost tracker.

        Args:
            budget_limit: Budget limit in USD
            warning_threshold: Threshold for warnings (0-1)
            alert_callback: Callback for budget alerts
        """
        self.budget_limit = budget_limit
        self.warning_threshold = warning_threshold
        self.alert_callback = alert_callback

        self.token_counter = TokenCounter()
        self.usage_history: List[TokenUsage] = []
        self.alerts: List[BudgetAlert] = []

        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

        self._model_usage: Dict[str, Dict[str, int]] = {}

    def track_usage(
        self,
        operation_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TokenUsage:
        """
        Track token usage for an operation.

        Args:
            operation_id: Operation identifier
            model: Model used
            input_tokens: Input tokens
            output_tokens: Output tokens
            metadata: Additional metadata

        Returns:
            TokenUsage record
        """
        usage = TokenUsage(
            operation_id=operation_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        self.usage_history.append(usage)

        # Update totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        # Update model-specific usage
        if model not in self._model_usage:
            self._model_usage[model] = {"input": 0, "output": 0}
        self._model_usage[model]["input"] += input_tokens
        self._model_usage[model]["output"] += output_tokens

        # Calculate cost
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        self.total_cost += cost.total_cost

        # Check budget
        if self.budget_limit:
            self._check_budget()

        logger.debug(
            f"Tracked usage: {operation_id}, {model}, "
            f"{usage.total_tokens} tokens, ${cost.total_cost:.4f}"
        )

        return usage

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> CostEstimate:
        """
        Estimate cost for token usage.

        Args:
            model: Model name
            input_tokens: Input tokens
            output_tokens: Output tokens

        Returns:
            CostEstimate
        """
        # Try to get pricing for model
        model_enum = None
        for mt in ModelType:
            if mt.value == model:
                model_enum = mt
                break

        if model_enum and model_enum in MODEL_PRICING:
            pricing = MODEL_PRICING[model_enum]
        else:
            # Default to GPT-4 pricing if unknown
            logger.warning(f"Unknown model: {model}, using GPT-4 pricing")
            pricing = MODEL_PRICING[ModelType.GPT_4]

        # Calculate costs (pricing is per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return CostEstimate(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model=model
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_operations": len(self.usage_history),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": self.total_cost,
            "budget_limit": self.budget_limit,
            "budget_utilization": self.total_cost / self.budget_limit if self.budget_limit else None,
            "model_breakdown": self._get_model_breakdown(),
            "alerts_count": len(self.alerts)
        }

    def get_usage_by_model(self, model: str) -> Dict[str, int]:
        """
        Get usage statistics for specific model.

        Args:
            model: Model name

        Returns:
            Usage dictionary
        """
        return self._model_usage.get(model, {"input": 0, "output": 0})

    def get_cost_by_model(self, model: str) -> float:
        """
        Get total cost for specific model.

        Args:
            model: Model name

        Returns:
            Total cost
        """
        usage = self.get_usage_by_model(model)
        estimate = self.estimate_cost(
            model,
            usage["input"],
            usage["output"]
        )
        return estimate.total_cost

    def reset_tracking(self) -> None:
        """Reset all tracking data."""
        self.usage_history = []
        self.alerts = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self._model_usage = {}
        logger.info("Reset cost tracking data")

    def export_report(self, filepath: str) -> None:
        """
        Export cost report to JSON file.

        Args:
            filepath: Output file path
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "usage_history": [u.to_dict() for u in self.usage_history],
            "alerts": [a.to_dict() for a in self.alerts]
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported cost report to {filepath}")

    def set_budget_limit(self, limit: float) -> None:
        """
        Set or update budget limit.

        Args:
            limit: Budget limit in USD
        """
        self.budget_limit = limit
        logger.info(f"Budget limit set to ${limit:.2f}")
        self._check_budget()

    def _check_budget(self) -> None:
        """Check budget and create alerts if needed."""
        if not self.budget_limit:
            return

        utilization = self.total_cost / self.budget_limit

        # Critical alert (100% budget)
        if utilization >= 1.0:
            alert = BudgetAlert(
                alert_id=f"alert_{len(self.alerts) + 1}",
                timestamp=datetime.now(),
                message=f"Budget limit exceeded! ${self.total_cost:.2f} / ${self.budget_limit:.2f}",
                severity="critical",
                current_cost=self.total_cost,
                budget_limit=self.budget_limit,
                utilization=utilization
            )
            self.alerts.append(alert)

            if self.alert_callback:
                self.alert_callback(alert)

            logger.critical(alert.message)

        # Warning alert (80% budget by default)
        elif utilization >= self.warning_threshold:
            # Check if we already warned at this level
            recent_warnings = [
                a for a in self.alerts[-5:]
                if a.severity == "warning" and a.utilization >= self.warning_threshold
            ]

            if not recent_warnings:
                alert = BudgetAlert(
                    alert_id=f"alert_{len(self.alerts) + 1}",
                    timestamp=datetime.now(),
                    message=f"Budget warning: ${self.total_cost:.2f} / ${self.budget_limit:.2f} ({utilization:.1%})",
                    severity="warning",
                    current_cost=self.total_cost,
                    budget_limit=self.budget_limit,
                    utilization=utilization
                )
                self.alerts.append(alert)

                if self.alert_callback:
                    self.alert_callback(alert)

                logger.warning(alert.message)

    def _get_model_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get breakdown of usage by model."""
        breakdown = {}

        for model, usage in self._model_usage.items():
            cost = self.get_cost_by_model(model)
            breakdown[model] = {
                "input_tokens": usage["input"],
                "output_tokens": usage["output"],
                "total_tokens": usage["input"] + usage["output"],
                "total_cost": cost
            }

        return breakdown


class CostOptimizer:
    """Helper for cost optimization recommendations."""

    @staticmethod
    def recommend_model(
        task_complexity: str,
        budget_conscious: bool = True
    ) -> str:
        """
        Recommend model based on task complexity and budget.

        Args:
            task_complexity: "simple", "moderate", or "complex"
            budget_conscious: Prioritize cost savings

        Returns:
            Recommended model name
        """
        if task_complexity == "simple":
            return ModelType.GPT_35_TURBO.value if budget_conscious else ModelType.GPT_4O.value
        elif task_complexity == "moderate":
            return ModelType.GPT_4O.value if budget_conscious else ModelType.GPT_4_TURBO.value
        else:  # complex
            return ModelType.GPT_4_TURBO.value if budget_conscious else ModelType.GPT_4.value

    @staticmethod
    def estimate_budget_for_operations(
        model: str,
        avg_input_tokens: int,
        avg_output_tokens: int,
        num_operations: int
    ) -> float:
        """
        Estimate budget needed for operations.

        Args:
            model: Model to use
            avg_input_tokens: Average input tokens per operation
            avg_output_tokens: Average output tokens per operation
            num_operations: Number of operations

        Returns:
            Estimated cost in USD
        """
        tracker = CostTracker()
        cost_per_op = tracker.estimate_cost(model, avg_input_tokens, avg_output_tokens)
        return cost_per_op.total_cost * num_operations


# Example usage
if __name__ == "__main__":
    # Initialize tracker with budget
    tracker = CostTracker(budget_limit=10.0, warning_threshold=0.8)

    # Track some usage
    tracker.track_usage(
        operation_id="op_1",
        model="gpt-4",
        input_tokens=1000,
        output_tokens=500
    )

    tracker.track_usage(
        operation_id="op_2",
        model="gpt-3.5-turbo",
        input_tokens=500,
        output_tokens=300
    )

    # Get statistics
    stats = tracker.get_statistics()
    print(f"Total cost: ${stats['total_cost']:.4f}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Budget utilization: {stats['budget_utilization']:.1%}")

    # Model recommendation
    recommended = CostOptimizer.recommend_model("moderate", budget_conscious=True)
    print(f"Recommended model: {recommended}")
