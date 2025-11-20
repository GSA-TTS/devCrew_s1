"""
Example: Chain-of-Thought Reasoning for Architectural Decision.

This example demonstrates how to use the CoT reasoner to make
architectural decisions with step-by-step reasoning.
"""

import asyncio
from issue_42_chain_of_thought import ChainOfThoughtReasoner, ReasoningStrategy
from issue_42_llm_providers import LLMProviderFactory, LLMProvider
from issue_42_evaluator import ReasoningEvaluator
from issue_42_cost_tracker import CostTracker


async def main():
    print("=" * 70)
    print("Chain-of-Thought Reasoning Example: Architectural Decision")
    print("=" * 70)

    # Initialize LLM provider (using mock for demonstration)
    print("\n[1] Initializing LLM provider...")
    llm_provider = LLMProviderFactory.create(
        provider_type=LLMProvider.MOCK,
        api_key="demo"
    )

    # Initialize reasoner
    print("[2] Initializing CoT reasoner...")
    reasoner = ChainOfThoughtReasoner(
        llm_provider=llm_provider,
        max_steps=5,
        temperature=0.7,
        enable_reflection=True
    )

    # Define the architectural decision question
    question = """
    Our startup is building a social media platform that needs to handle:
    - 100K users initially, scaling to millions
    - Real-time messaging and notifications
    - Photo and video uploads
    - User feeds with recommendation algorithms

    Should we use a microservices architecture or a monolithic architecture?
    """

    context = """
    Team context:
    - 5 developers (2 backend, 2 frontend, 1 DevOps)
    - 6-month timeline to MVP
    - Limited budget for infrastructure
    - Need to iterate quickly based on user feedback
    """

    # Example 1: Zero-shot reasoning
    print("\n" + "=" * 70)
    print("Example 1: Zero-Shot Chain-of-Thought")
    print("=" * 70)

    result = await reasoner.reason(
        question=question,
        strategy=ReasoningStrategy.ZERO_SHOT,
        context=context
    )

    print(f"\nQuestion: {question.strip()}")
    print(f"\nReasoning Steps ({len(result.steps)} steps):")
    for step in result.steps:
        print(f"\n  Step {step.step_number}:")
        print(f"  {step.thought}")
        print(f"  Confidence: {step.confidence:.2%}")

    print(f"\n{'='*70}")
    print(f"Final Answer: {result.final_answer}")
    print(f"Overall Confidence: {result.confidence:.2%}")
    print(f"Tokens Used: {result.token_count}")
    print(f"Execution Time: {result.execution_time:.2f}s")

    # Example 2: Few-shot reasoning with examples
    print("\n" + "=" * 70)
    print("Example 2: Few-Shot Chain-of-Thought")
    print("=" * 70)

    examples = [
        {
            "question": "Should we use SQL or NoSQL for a blog platform?",
            "reasoning": "Step 1: Analyze data structure (posts, comments, users) - highly relational. Step 2: Consider query patterns - need complex joins. Step 3: Evaluate scale - moderate scale, consistency important. Step 4: Conclusion - SQL database is better fit.",
            "answer": "Use SQL (PostgreSQL) for structured data with strong consistency requirements."
        }
    ]

    result_few_shot = await reasoner.reason(
        question=question,
        strategy=ReasoningStrategy.FEW_SHOT,
        examples=examples,
        context=context
    )

    print(f"\nWith few-shot learning:")
    print(f"Final Answer: {result_few_shot.final_answer}")
    print(f"Confidence: {result_few_shot.confidence:.2%}")

    # Example 3: Self-consistency reasoning
    print("\n" + "=" * 70)
    print("Example 3: Self-Consistency Chain-of-Thought")
    print("=" * 70)

    reasoner_sc = ChainOfThoughtReasoner(
        llm_provider=llm_provider,
        max_steps=4,
        self_consistency_samples=3
    )

    result_sc = await reasoner_sc.reason(
        question=question,
        strategy=ReasoningStrategy.SELF_CONSISTENCY,
        context=context
    )

    print(f"\nSelf-consistency analysis:")
    print(f"Final Answer: {result_sc.final_answer}")
    print(f"Confidence: {result_sc.confidence:.2%}")
    print(f"Consistency Ratio: {result_sc.metadata.get('consistency_ratio', 0):.2%}")
    print(f"Unique Answers: {result_sc.metadata.get('unique_answers', 0)}")

    # Example 4: Evaluation
    print("\n" + "=" * 70)
    print("Example 4: Evaluating Reasoning Quality")
    print("=" * 70)

    evaluator = ReasoningEvaluator(llm_provider)
    evaluations = await evaluator.evaluate_cot(result)

    print(f"\nEvaluation Metrics:")
    for metric_name, eval_result in evaluations.items():
        print(f"  {metric_name.capitalize()}: {eval_result.percentage():.1f}%")

    # Example 5: Cost tracking
    print("\n" + "=" * 70)
    print("Example 5: Cost Tracking")
    print("=" * 70)

    cost_tracker = CostTracker(budget_limit=10.0)

    cost_tracker.track_usage(
        operation_id="cot_example",
        model="gpt-4",
        input_tokens=result.token_count // 2,
        output_tokens=result.token_count // 2
    )

    stats = cost_tracker.get_statistics()
    print(f"\nCost Statistics:")
    print(f"  Total Tokens: {stats['total_tokens']:,}")
    print(f"  Total Cost: ${stats['total_cost']:.4f}")
    print(f"  Budget Remaining: ${stats['budget_limit'] - stats['total_cost']:.4f}")

    print("\n" + "=" * 70)
    print("Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
