"""
Evaluation and Quality Metrics Module.

This module provides evaluation capabilities for reasoning quality,
self-consistency, and benchmark testing.

Protocol Coverage:
- P-COG-COT: Chain-of-Thought evaluation
- P-COG-TOT: Tree-of-Thought path scoring
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import asyncio


logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Evaluation metric types."""
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"


@dataclass
class EvaluationResult:
    """Result of an evaluation."""
    metric_type: MetricType
    score: float
    max_score: float
    details: Dict[str, Any]
    timestamp: str

    def percentage(self) -> float:
        """Get score as percentage."""
        if self.max_score == 0:
            return 0.0
        return (self.score / self.max_score) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_type": self.metric_type.value,
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage(),
            "details": self.details,
            "timestamp": self.timestamp
        }


class ReasoningEvaluator:
    """Evaluator for reasoning quality and consistency."""

    def __init__(self, llm_provider: Optional[Any] = None):
        """
        Initialize evaluator.

        Args:
            llm_provider: LLM provider for evaluation (optional)
        """
        self.llm_provider = llm_provider

    async def evaluate_cot(
        self,
        result: Any,  # ReasoningResult from chain_of_thought.py
        ground_truth: Optional[str] = None
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluate Chain-of-Thought reasoning result.

        Args:
            result: ReasoningResult object
            ground_truth: Expected answer (optional)

        Returns:
            Dictionary of evaluation results by metric
        """
        from datetime import datetime

        evaluations = {}

        # Evaluate completeness
        completeness = self._evaluate_completeness(result)
        evaluations["completeness"] = EvaluationResult(
            metric_type=MetricType.COMPLETENESS,
            score=completeness,
            max_score=1.0,
            details={"num_steps": len(result.steps)},
            timestamp=datetime.now().isoformat()
        )

        # Evaluate consistency
        consistency = self._evaluate_consistency(result)
        evaluations["consistency"] = EvaluationResult(
            metric_type=MetricType.CONSISTENCY,
            score=consistency,
            max_score=1.0,
            details={"confidence": result.confidence},
            timestamp=datetime.now().isoformat()
        )

        # Evaluate quality
        if self.llm_provider:
            quality = await self._evaluate_quality_llm(result)
        else:
            quality = self._evaluate_quality_heuristic(result)

        evaluations["quality"] = EvaluationResult(
            metric_type=MetricType.QUALITY,
            score=quality,
            max_score=1.0,
            details={"strategy": result.strategy.value},
            timestamp=datetime.now().isoformat()
        )

        # Evaluate accuracy (if ground truth provided)
        if ground_truth:
            accuracy = self._evaluate_accuracy(result.final_answer, ground_truth)
            evaluations["accuracy"] = EvaluationResult(
                metric_type=MetricType.ACCURACY,
                score=accuracy,
                max_score=1.0,
                details={"ground_truth": ground_truth},
                timestamp=datetime.now().isoformat()
            )

        # Evaluate efficiency
        efficiency = self._evaluate_efficiency(result)
        evaluations["efficiency"] = EvaluationResult(
            metric_type=MetricType.EFFICIENCY,
            score=efficiency,
            max_score=1.0,
            details={
                "token_count": result.token_count,
                "execution_time": result.execution_time
            },
            timestamp=datetime.now().isoformat()
        )

        return evaluations

    async def evaluate_tot(
        self,
        result: Any,  # ToTResult from tree_of_thought.py
        ground_truth: Optional[str] = None
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluate Tree-of-Thoughts exploration result.

        Args:
            result: ToTResult object
            ground_truth: Expected answer (optional)

        Returns:
            Dictionary of evaluation results by metric
        """
        from datetime import datetime

        evaluations = {}

        # Evaluate exploration efficiency
        exploration_efficiency = self._evaluate_exploration_efficiency(result)
        evaluations["efficiency"] = EvaluationResult(
            metric_type=MetricType.EFFICIENCY,
            score=exploration_efficiency,
            max_score=1.0,
            details={
                "total_nodes": result.total_nodes,
                "pruned_nodes": result.pruned_nodes,
                "explored_paths": len(result.explored_paths)
            },
            timestamp=datetime.now().isoformat()
        )

        # Evaluate path quality
        path_quality = self._evaluate_path_quality(result.best_path)
        evaluations["quality"] = EvaluationResult(
            metric_type=MetricType.QUALITY,
            score=path_quality,
            max_score=1.0,
            details={
                "path_score": result.best_path.total_score,
                "path_depth": result.best_path.depth
            },
            timestamp=datetime.now().isoformat()
        )

        # Evaluate completeness
        completeness = 1.0 if result.best_path.is_solution else 0.7
        evaluations["completeness"] = EvaluationResult(
            metric_type=MetricType.COMPLETENESS,
            score=completeness,
            max_score=1.0,
            details={"is_solution": result.best_path.is_solution},
            timestamp=datetime.now().isoformat()
        )

        return evaluations

    async def evaluate_self_consistency(
        self,
        results: List[Any],  # List of ReasoningResult
        question: str
    ) -> EvaluationResult:
        """
        Evaluate self-consistency across multiple reasoning attempts.

        Args:
            results: List of ReasoningResult objects
            question: Original question

        Returns:
            EvaluationResult for consistency
        """
        from datetime import datetime

        if len(results) < 2:
            return EvaluationResult(
                metric_type=MetricType.CONSISTENCY,
                score=1.0,
                max_score=1.0,
                details={"message": "Insufficient results for consistency check"},
                timestamp=datetime.now().isoformat()
            )

        # Count answer frequencies
        answer_counts: Dict[str, int] = {}
        for result in results:
            answer = result.final_answer.strip().lower()
            answer_counts[answer] = answer_counts.get(answer, 0) + 1

        # Calculate consistency score
        most_common_count = max(answer_counts.values())
        consistency_score = most_common_count / len(results)

        # Calculate answer diversity
        diversity = len(answer_counts) / len(results)

        return EvaluationResult(
            metric_type=MetricType.CONSISTENCY,
            score=consistency_score,
            max_score=1.0,
            details={
                "total_attempts": len(results),
                "unique_answers": len(answer_counts),
                "most_common_count": most_common_count,
                "diversity": diversity,
                "answer_distribution": answer_counts
            },
            timestamp=datetime.now().isoformat()
        )

    def _evaluate_completeness(self, result: Any) -> float:
        """Evaluate completeness of reasoning."""
        # Check if reasoning has sufficient steps
        step_score = min(len(result.steps) / 3.0, 1.0)  # Ideal: 3+ steps

        # Check if conclusion is reached
        has_conclusion = any(
            keyword in result.final_answer.lower()
            for keyword in ["therefore", "thus", "conclusion", "answer"]
        )
        conclusion_score = 1.0 if has_conclusion else 0.7

        return (step_score + conclusion_score) / 2

    def _evaluate_consistency(self, result: Any) -> float:
        """Evaluate internal consistency."""
        # Use built-in confidence as base
        base_score = result.confidence

        # Check for contradictions in steps
        thoughts = [step.thought.lower() for step in result.steps]
        has_contradiction = self._detect_contradictions(thoughts)
        consistency_penalty = 0.3 if has_contradiction else 0.0

        return max(0.0, base_score - consistency_penalty)

    async def _evaluate_quality_llm(self, result: Any) -> float:
        """Evaluate reasoning quality using LLM."""
        prompt = f"""
Evaluate the quality of the following reasoning process:

Question: {result.question}

Reasoning Steps:
{self._format_steps(result.steps)}

Final Answer: {result.final_answer}

Rate the reasoning quality on these criteria (0-1 scale):
1. Logical coherence
2. Depth of analysis
3. Clarity of explanation
4. Soundness of conclusion

Provide only the average score as a decimal (e.g., 0.85):
"""

        try:
            response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=10
            )

            score_text = response.text.strip()
            return float(score_text)
        except Exception as e:
            logger.warning(f"Failed to evaluate quality with LLM: {e}")
            return self._evaluate_quality_heuristic(result)

    def _evaluate_quality_heuristic(self, result: Any) -> float:
        """Evaluate reasoning quality using heuristics."""
        scores = []

        # Length and depth
        avg_thought_length = statistics.mean(
            len(step.thought.split()) for step in result.steps
        )
        length_score = min(avg_thought_length / 20, 1.0)  # Ideal: 20+ words
        scores.append(length_score)

        # Confidence
        scores.append(result.confidence)

        # Number of steps
        step_score = min(len(result.steps) / 4, 1.0)  # Ideal: 4+ steps
        scores.append(step_score)

        return statistics.mean(scores)

    def _evaluate_accuracy(self, answer: str, ground_truth: str) -> float:
        """Evaluate accuracy against ground truth."""
        answer_norm = answer.strip().lower()
        truth_norm = ground_truth.strip().lower()

        # Exact match
        if answer_norm == truth_norm:
            return 1.0

        # Contains ground truth
        if truth_norm in answer_norm:
            return 0.8

        # Fuzzy match based on word overlap
        answer_words = set(answer_norm.split())
        truth_words = set(truth_norm.split())

        if not truth_words:
            return 0.0

        overlap = len(answer_words & truth_words) / len(truth_words)
        return overlap * 0.6  # Partial credit

    def _evaluate_efficiency(self, result: Any) -> float:
        """Evaluate efficiency of reasoning."""
        # Token efficiency: penalize excessive token usage
        token_score = 1.0
        if result.token_count > 5000:
            token_score = max(0.3, 1.0 - (result.token_count - 5000) / 10000)

        # Time efficiency: penalize long execution
        time_score = 1.0
        if result.execution_time > 10:
            time_score = max(0.3, 1.0 - (result.execution_time - 10) / 20)

        return (token_score + time_score) / 2

    def _evaluate_exploration_efficiency(self, result: Any) -> float:
        """Evaluate ToT exploration efficiency."""
        # Pruning efficiency
        if result.total_nodes == 0:
            pruning_score = 0.5
        else:
            pruning_ratio = result.pruned_nodes / result.total_nodes
            pruning_score = min(pruning_ratio * 1.5, 1.0)  # Good pruning

        # Path efficiency
        path_score = 1.0 if result.best_path.is_solution else 0.7

        return (pruning_score + path_score) / 2

    def _evaluate_path_quality(self, path: Any) -> float:
        """Evaluate quality of ToT path."""
        # Use path score directly
        return path.total_score

    def _detect_contradictions(self, thoughts: List[str]) -> bool:
        """Detect contradictions in thoughts."""
        contradiction_pairs = [
            ("should", "should not"),
            ("yes", "no"),
            ("correct", "incorrect"),
            ("true", "false")
        ]

        for i, thought in enumerate(thoughts):
            for j, other_thought in enumerate(thoughts[i+1:], start=i+1):
                for pos, neg in contradiction_pairs:
                    if pos in thought and neg in other_thought:
                        return True
                    if neg in thought and pos in other_thought:
                        return True

        return False

    def _format_steps(self, steps: List[Any]) -> str:
        """Format reasoning steps for prompt."""
        return "\n".join(
            f"Step {step.step_number}: {step.thought}"
            for step in steps
        )


class BenchmarkEvaluator:
    """Evaluator for benchmark datasets."""

    def __init__(self, llm_provider: Any):
        """
        Initialize benchmark evaluator.

        Args:
            llm_provider: LLM provider for reasoning
        """
        self.llm_provider = llm_provider
        self.evaluator = ReasoningEvaluator(llm_provider)

    async def run_benchmark(
        self,
        dataset: List[Dict[str, str]],
        reasoner: Any,
        strategy: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Run benchmark evaluation.

        Args:
            dataset: List of question-answer pairs
            reasoner: CoT or ToT reasoner
            strategy: Reasoning strategy

        Returns:
            Benchmark results
        """
        results = []
        correct = 0
        total = len(dataset)

        for item in dataset:
            question = item["question"]
            ground_truth = item["answer"]

            # Run reasoning
            result = await reasoner.reason(question, strategy=strategy)

            # Evaluate
            evaluations = await self.evaluator.evaluate_cot(result, ground_truth)

            # Check accuracy
            if "accuracy" in evaluations:
                if evaluations["accuracy"].score >= 0.8:
                    correct += 1

            results.append({
                "question": question,
                "answer": result.final_answer,
                "ground_truth": ground_truth,
                "evaluations": {k: v.to_dict() for k, v in evaluations.items()}
            })

        accuracy = correct / total if total > 0 else 0.0

        return {
            "total_questions": total,
            "correct": correct,
            "accuracy": accuracy,
            "results": results
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    from dataclasses import dataclass
    from enum import Enum

    # Mock classes for demonstration
    class ReasoningStrategy(Enum):
        ZERO_SHOT = "zero_shot"

    @dataclass
    class ThoughtStep:
        step_number: int
        thought: str
        confidence: float = 1.0

    @dataclass
    class ReasoningResult:
        question: str
        steps: List[ThoughtStep]
        final_answer: str
        confidence: float
        strategy: ReasoningStrategy
        token_count: int = 0
        execution_time: float = 0.0

    async def main():
        evaluator = ReasoningEvaluator()

        # Mock result
        result = ReasoningResult(
            question="What is 2 + 2?",
            steps=[
                ThoughtStep(1, "We need to add 2 and 2", 0.9),
                ThoughtStep(2, "2 + 2 = 4", 0.95),
                ThoughtStep(3, "Therefore, the answer is 4", 0.98)
            ],
            final_answer="The answer is 4",
            confidence=0.94,
            strategy=ReasoningStrategy.ZERO_SHOT,
            token_count=150,
            execution_time=2.5
        )

        evaluations = await evaluator.evaluate_cot(result, ground_truth="4")

        print("Evaluation Results:")
        for metric, eval_result in evaluations.items():
            print(f"{metric}: {eval_result.percentage():.1f}%")

    asyncio.run(main())
