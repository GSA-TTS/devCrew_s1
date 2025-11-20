"""
Chain-of-Thought (CoT) Reasoning Implementation.

This module implements multi-step reasoning with explicit intermediate thoughts,
self-consistency checking, and reflection capabilities.

Protocol Coverage:
- P-COG-COT: Chain-of-Thought protocol
- P-ASR-ADR-ALIGNMENT: ASR to ADR reasoning
- P-CONTEXT-VALIDATION: Context integrity checking
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json


logger = logging.getLogger(__name__)


class ReasoningStrategy(Enum):
    """Reasoning strategy types."""
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    SELF_CONSISTENCY = "self_consistency"
    REFLECTION = "reflection"


@dataclass
class ThoughtStep:
    """Represents a single step in the reasoning chain."""
    step_number: int
    question: str
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "question": self.question,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class ReasoningResult:
    """Result of a CoT reasoning process."""
    question: str
    steps: List[ThoughtStep]
    final_answer: str
    confidence: float
    strategy: ReasoningStrategy
    token_count: int = 0
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "steps": [step.to_dict() for step in self.steps],
            "final_answer": self.final_answer,
            "confidence": self.confidence,
            "strategy": self.strategy.value,
            "token_count": self.token_count,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


class ChainOfThoughtReasoner:
    """
    Chain-of-Thought reasoning engine with step-by-step reasoning,
    self-consistency checking, and reflection capabilities.
    """

    def __init__(
        self,
        llm_provider: Any,
        max_steps: int = 5,
        temperature: float = 0.7,
        self_consistency_samples: int = 3,
        enable_reflection: bool = True
    ):
        """
        Initialize CoT reasoner.

        Args:
            llm_provider: LLM provider instance
            max_steps: Maximum reasoning steps
            temperature: LLM temperature
            self_consistency_samples: Number of samples for self-consistency
            enable_reflection: Enable reflection and self-critique
        """
        self.llm_provider = llm_provider
        self.max_steps = max_steps
        self.temperature = temperature
        self.self_consistency_samples = self_consistency_samples
        self.enable_reflection = enable_reflection
        self.token_count = 0

    async def reason(
        self,
        question: str,
        strategy: ReasoningStrategy = ReasoningStrategy.ZERO_SHOT,
        examples: Optional[List[Dict[str, str]]] = None,
        context: Optional[str] = None
    ) -> ReasoningResult:
        """
        Perform Chain-of-Thought reasoning.

        Args:
            question: Question to reason about
            strategy: Reasoning strategy to use
            examples: Few-shot examples (if using few-shot strategy)
            context: Additional context for reasoning

        Returns:
            ReasoningResult with steps and final answer
        """
        import time
        start_time = time.time()

        logger.info(f"Starting CoT reasoning with strategy: {strategy.value}")

        if strategy == ReasoningStrategy.SELF_CONSISTENCY:
            result = await self._self_consistency_reasoning(question, context)
        elif strategy == ReasoningStrategy.FEW_SHOT:
            result = await self._few_shot_reasoning(question, examples, context)
        elif strategy == ReasoningStrategy.REFLECTION:
            result = await self._reflection_reasoning(question, context)
        else:
            result = await self._zero_shot_reasoning(question, context)

        result.execution_time = time.time() - start_time
        result.token_count = self.token_count

        logger.info(f"CoT reasoning completed in {result.execution_time:.2f}s")
        return result

    async def _zero_shot_reasoning(
        self,
        question: str,
        context: Optional[str] = None
    ) -> ReasoningResult:
        """Zero-shot CoT reasoning."""
        prompt = self._build_zero_shot_prompt(question, context)
        steps = []

        for step_num in range(1, self.max_steps + 1):
            thought_step = await self._generate_thought_step(
                prompt, step_num, question, steps
            )
            steps.append(thought_step)

            # Check if we reached a conclusion
            if self._is_conclusion(thought_step):
                break

            # Update prompt with new step
            prompt = self._update_prompt_with_step(prompt, thought_step)

        final_answer = await self._extract_final_answer(steps)
        confidence = self._calculate_confidence(steps)

        return ReasoningResult(
            question=question,
            steps=steps,
            final_answer=final_answer,
            confidence=confidence,
            strategy=ReasoningStrategy.ZERO_SHOT
        )

    async def _few_shot_reasoning(
        self,
        question: str,
        examples: Optional[List[Dict[str, str]]],
        context: Optional[str] = None
    ) -> ReasoningResult:
        """Few-shot CoT reasoning with examples."""
        if not examples:
            logger.warning("No examples provided for few-shot reasoning")
            return await self._zero_shot_reasoning(question, context)

        prompt = self._build_few_shot_prompt(question, examples, context)
        steps = []

        for step_num in range(1, self.max_steps + 1):
            thought_step = await self._generate_thought_step(
                prompt, step_num, question, steps
            )
            steps.append(thought_step)

            if self._is_conclusion(thought_step):
                break

            prompt = self._update_prompt_with_step(prompt, thought_step)

        final_answer = await self._extract_final_answer(steps)
        confidence = self._calculate_confidence(steps)

        return ReasoningResult(
            question=question,
            steps=steps,
            final_answer=final_answer,
            confidence=confidence,
            strategy=ReasoningStrategy.FEW_SHOT
        )

    async def _self_consistency_reasoning(
        self,
        question: str,
        context: Optional[str] = None
    ) -> ReasoningResult:
        """Self-consistency CoT with multiple reasoning paths."""
        logger.info(f"Generating {self.self_consistency_samples} reasoning paths")

        # Generate multiple reasoning paths
        tasks = [
            self._zero_shot_reasoning(question, context)
            for _ in range(self.self_consistency_samples)
        ]
        results = await asyncio.gather(*tasks)

        # Find most common answer
        answer_counts: Dict[str, List[ReasoningResult]] = {}
        for result in results:
            answer = result.final_answer.strip().lower()
            if answer not in answer_counts:
                answer_counts[answer] = []
            answer_counts[answer].append(result)

        # Select most consistent answer
        most_common_answer = max(answer_counts.keys(), key=lambda k: len(answer_counts[k]))
        best_result = answer_counts[most_common_answer][0]

        # Calculate consistency-based confidence
        consistency_ratio = len(answer_counts[most_common_answer]) / len(results)
        best_result.confidence = consistency_ratio
        best_result.strategy = ReasoningStrategy.SELF_CONSISTENCY
        best_result.metadata["consistency_ratio"] = consistency_ratio
        best_result.metadata["num_samples"] = len(results)
        best_result.metadata["unique_answers"] = len(answer_counts)

        logger.info(f"Self-consistency: {consistency_ratio:.2%} agreement")
        return best_result

    async def _reflection_reasoning(
        self,
        question: str,
        context: Optional[str] = None
    ) -> ReasoningResult:
        """CoT reasoning with reflection and self-critique."""
        # Initial reasoning
        initial_result = await self._zero_shot_reasoning(question, context)

        # Reflect on the reasoning
        reflection = await self._generate_reflection(initial_result)

        # Refine based on reflection
        refined_result = await self._refine_reasoning(
            initial_result, reflection, context
        )

        refined_result.strategy = ReasoningStrategy.REFLECTION
        refined_result.metadata["initial_answer"] = initial_result.final_answer
        refined_result.metadata["reflection"] = reflection

        return refined_result

    async def _generate_thought_step(
        self,
        prompt: str,
        step_num: int,
        question: str,
        previous_steps: List[ThoughtStep]
    ) -> ThoughtStep:
        """Generate a single thought step."""
        response = await self.llm_provider.generate(
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=500
        )

        self.token_count += response.token_count

        thought = response.text.strip()

        return ThoughtStep(
            step_number=step_num,
            question=question,
            thought=thought,
            confidence=self._estimate_step_confidence(thought)
        )

    async def _generate_reflection(self, result: ReasoningResult) -> str:
        """Generate reflection on reasoning process."""
        reflection_prompt = f"""
Review the following reasoning process and identify any flaws, gaps, or areas for improvement:

Question: {result.question}

Reasoning Steps:
{self._format_steps_for_reflection(result.steps)}

Final Answer: {result.final_answer}

Provide a critical reflection on:
1. Logical consistency
2. Completeness of reasoning
3. Potential biases or assumptions
4. Alternative perspectives

Reflection:
"""

        response = await self.llm_provider.generate(
            prompt=reflection_prompt,
            temperature=0.3,
            max_tokens=300
        )

        self.token_count += response.token_count
        return response.text.strip()

    async def _refine_reasoning(
        self,
        initial_result: ReasoningResult,
        reflection: str,
        context: Optional[str] = None
    ) -> ReasoningResult:
        """Refine reasoning based on reflection."""
        refinement_prompt = f"""
Original Question: {initial_result.question}

Initial Reasoning:
{self._format_steps_for_reflection(initial_result.steps)}

Initial Answer: {initial_result.final_answer}

Reflection:
{reflection}

Based on the reflection, provide a refined reasoning process that addresses the identified issues:
"""

        # Generate refined reasoning
        steps = []
        for step_num in range(1, self.max_steps + 1):
            thought_step = await self._generate_thought_step(
                refinement_prompt, step_num, initial_result.question, steps
            )
            steps.append(thought_step)

            if self._is_conclusion(thought_step):
                break

            refinement_prompt = self._update_prompt_with_step(refinement_prompt, thought_step)

        final_answer = await self._extract_final_answer(steps)
        confidence = self._calculate_confidence(steps)

        return ReasoningResult(
            question=initial_result.question,
            steps=steps,
            final_answer=final_answer,
            confidence=confidence,
            strategy=ReasoningStrategy.REFLECTION
        )

    def _build_zero_shot_prompt(self, question: str, context: Optional[str]) -> str:
        """Build zero-shot CoT prompt."""
        prompt = "Let's think step by step to solve this problem.\n\n"
        if context:
            prompt += f"Context: {context}\n\n"
        prompt += f"Question: {question}\n\n"
        prompt += "Step 1:"
        return prompt

    def _build_few_shot_prompt(
        self,
        question: str,
        examples: List[Dict[str, str]],
        context: Optional[str]
    ) -> str:
        """Build few-shot CoT prompt with examples."""
        prompt = "Here are some examples of step-by-step reasoning:\n\n"

        for i, example in enumerate(examples, 1):
            prompt += f"Example {i}:\n"
            prompt += f"Question: {example.get('question', '')}\n"
            prompt += f"Reasoning: {example.get('reasoning', '')}\n"
            prompt += f"Answer: {example.get('answer', '')}\n\n"

        if context:
            prompt += f"Context: {context}\n\n"

        prompt += f"Now, let's solve this question step by step:\n"
        prompt += f"Question: {question}\n\n"
        prompt += "Step 1:"
        return prompt

    def _update_prompt_with_step(self, prompt: str, step: ThoughtStep) -> str:
        """Update prompt with new thought step."""
        return f"{prompt}\n{step.thought}\n\nStep {step.step_number + 1}:"

    def _is_conclusion(self, step: ThoughtStep) -> bool:
        """Check if step represents a conclusion."""
        conclusion_keywords = [
            "therefore", "thus", "hence", "in conclusion",
            "final answer", "the answer is", "we conclude"
        ]
        thought_lower = step.thought.lower()
        return any(keyword in thought_lower for keyword in conclusion_keywords)

    async def _extract_final_answer(self, steps: List[ThoughtStep]) -> str:
        """Extract final answer from reasoning steps."""
        if not steps:
            return ""

        # Check last step for explicit answer
        last_step = steps[-1]
        if "answer is" in last_step.thought.lower():
            # Extract answer after "answer is"
            parts = last_step.thought.lower().split("answer is")
            if len(parts) > 1:
                return parts[-1].strip().rstrip(".")

        # Return last step thought as answer
        return last_step.thought

    def _calculate_confidence(self, steps: List[ThoughtStep]) -> float:
        """Calculate overall confidence from steps."""
        if not steps:
            return 0.0

        # Average confidence across steps
        total_confidence = sum(step.confidence for step in steps)
        return total_confidence / len(steps)

    def _estimate_step_confidence(self, thought: str) -> float:
        """Estimate confidence of a thought step."""
        # Simple heuristic based on length and certainty markers
        confidence = 0.7  # Base confidence

        # Boost for certainty markers
        certainty_markers = ["clearly", "definitely", "certainly", "obviously"]
        if any(marker in thought.lower() for marker in certainty_markers):
            confidence += 0.1

        # Reduce for uncertainty markers
        uncertainty_markers = ["maybe", "perhaps", "might", "possibly", "unclear"]
        if any(marker in thought.lower() for marker in uncertainty_markers):
            confidence -= 0.2

        return max(0.1, min(1.0, confidence))

    def _format_steps_for_reflection(self, steps: List[ThoughtStep]) -> str:
        """Format steps for reflection prompt."""
        formatted = []
        for step in steps:
            formatted.append(f"Step {step.step_number}: {step.thought}")
        return "\n".join(formatted)


class CoTValidator:
    """Validator for CoT reasoning results."""

    @staticmethod
    def validate_reasoning_chain(result: ReasoningResult) -> Dict[str, Any]:
        """
        Validate reasoning chain for logical consistency.

        Returns:
            Dict with validation results
        """
        validation = {
            "is_valid": True,
            "issues": [],
            "warnings": []
        }

        # Check for minimum steps
        if len(result.steps) < 2:
            validation["warnings"].append("Reasoning chain is very short")

        # Check for contradictions
        thoughts = [step.thought.lower() for step in result.steps]
        if CoTValidator._has_contradictions(thoughts):
            validation["is_valid"] = False
            validation["issues"].append("Contradictions detected in reasoning")

        # Check confidence levels
        low_confidence_steps = [
            step for step in result.steps if step.confidence < 0.5
        ]
        if low_confidence_steps:
            validation["warnings"].append(
                f"{len(low_confidence_steps)} steps have low confidence"
            )

        return validation

    @staticmethod
    def _has_contradictions(thoughts: List[str]) -> bool:
        """Check for contradictions in thoughts."""
        # Simple contradiction detection
        contradiction_pairs = [
            ("yes", "no"),
            ("true", "false"),
            ("should", "should not"),
            ("will", "will not")
        ]

        for i, thought in enumerate(thoughts):
            for j, other_thought in enumerate(thoughts[i+1:], start=i+1):
                for pos, neg in contradiction_pairs:
                    if pos in thought and neg in other_thought:
                        return True
                    if neg in thought and pos in other_thought:
                        return True

        return False


# Example usage
if __name__ == "__main__":
    import asyncio

    # Mock LLM provider for demonstration
    class MockLLMProvider:
        async def generate(self, prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
            return {
                "text": "This is a mock thought step for demonstration.",
                "token_count": 50
            }

    async def main():
        provider = MockLLMProvider()
        reasoner = ChainOfThoughtReasoner(provider, max_steps=3)

        result = await reasoner.reason(
            question="What is the best architectural pattern for a microservices system?",
            strategy=ReasoningStrategy.ZERO_SHOT
        )

        print(f"Question: {result.question}")
        print(f"Steps: {len(result.steps)}")
        print(f"Final Answer: {result.final_answer}")
        print(f"Confidence: {result.confidence:.2%}")

    asyncio.run(main())
