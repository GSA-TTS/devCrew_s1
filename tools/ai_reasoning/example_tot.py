"""
Example: Tree-of-Thoughts Exploration for System Design.

This example demonstrates how to use the ToT explorer to explore
multiple solution paths for complex system design problems.
"""

import asyncio
from issue_42_tree_of_thought import (
    TreeOfThoughtsExplorer, SearchStrategy, ToTVisualizer
)
from issue_42_llm_providers import LLMProviderFactory, LLMProvider
from issue_42_cost_tracker import CostTracker


async def main():
    print("=" * 70)
    print("Tree-of-Thoughts Exploration Example: System Design")
    print("=" * 70)

    # Initialize LLM provider (using mock for demonstration)
    print("\n[1] Initializing LLM provider...")
    llm_provider = LLMProviderFactory.create(
        provider_type=LLMProvider.MOCK,
        api_key="demo"
    )

    # Define the system design question
    question = """
    Design a scalable notification system that can handle:
    - 10 million daily active users
    - Push notifications, email, and SMS
    - Priority-based delivery
    - Delivery tracking and analytics
    - Multi-region deployment

    What architecture and technologies should we use?
    """

    context = """
    Requirements:
    - 99.9% uptime
    - < 1 second latency for push notifications
    - Support for A/B testing
    - Cost-effective solution
    - Easy to maintain and scale
    """

    # Example 1: Breadth-First Search
    print("\n" + "=" * 70)
    print("Example 1: Breadth-First Search")
    print("=" * 70)

    explorer_bfs = TreeOfThoughtsExplorer(
        llm_provider=llm_provider,
        max_depth=2,
        branching_factor=3
    )

    print("\nExploring solution space with BFS...")
    result_bfs = await explorer_bfs.explore(
        question=question,
        strategy=SearchStrategy.BREADTH_FIRST,
        context=context
    )

    print(f"\nExploration Results:")
    print(f"  Total Nodes: {result_bfs.total_nodes}")
    print(f"  Pruned Nodes: {result_bfs.pruned_nodes}")
    print(f"  Explored Paths: {len(result_bfs.explored_paths)}")
    print(f"  Best Path Score: {result_bfs.best_path.total_score:.2f}")

    print(f"\nBest Path ({result_bfs.best_path.depth} nodes):")
    for i, node in enumerate(result_bfs.best_path.nodes):
        print(f"  {i}. [{node.score:.2f}] {node.thought[:70]}...")

    # Example 2: Depth-First Search
    print("\n" + "=" * 70)
    print("Example 2: Depth-First Search")
    print("=" * 70)

    explorer_dfs = TreeOfThoughtsExplorer(
        llm_provider=llm_provider,
        max_depth=3,
        branching_factor=2
    )

    print("\nExploring solution space with DFS...")
    result_dfs = await explorer_dfs.explore(
        question=question,
        strategy=SearchStrategy.DEPTH_FIRST,
        context=context
    )

    print(f"\nDFS Exploration:")
    print(f"  Total Nodes: {result_dfs.total_nodes}")
    print(f"  Best Path Score: {result_dfs.best_path.total_score:.2f}")
    print(f"  Max Depth Reached: {result_dfs.best_path.depth}")

    # Example 3: Best-First Search (Greedy)
    print("\n" + "=" * 70)
    print("Example 3: Best-First Search")
    print("=" * 70)

    explorer_best = TreeOfThoughtsExplorer(
        llm_provider=llm_provider,
        max_depth=3,
        branching_factor=3,
        pruning_threshold=0.4
    )

    print("\nExploring solution space with Best-First Search...")
    result_best = await explorer_best.explore(
        question=question,
        strategy=SearchStrategy.BEST_FIRST,
        context=context
    )

    print(f"\nBest-First Search Results:")
    print(f"  Total Nodes: {result_best.total_nodes}")
    print(f"  Pruned Nodes: {result_best.pruned_nodes}")
    print(f"  Pruning Rate: {result_best.pruned_nodes/result_best.total_nodes:.1%}")
    print(f"  Best Path Score: {result_best.best_path.total_score:.2f}")

    # Example 4: Beam Search
    print("\n" + "=" * 70)
    print("Example 4: Beam Search")
    print("=" * 70)

    explorer_beam = TreeOfThoughtsExplorer(
        llm_provider=llm_provider,
        max_depth=3,
        branching_factor=4,
        beam_width=2
    )

    print("\nExploring solution space with Beam Search...")
    result_beam = await explorer_beam.explore(
        question=question,
        strategy=SearchStrategy.BEAM_SEARCH,
        context=context
    )

    print(f"\nBeam Search Results:")
    print(f"  Total Nodes: {result_beam.total_nodes}")
    print(f"  Beam Width: 2")
    print(f"  Best Path Score: {result_beam.best_path.total_score:.2f}")

    print(f"\nTop paths explored:")
    for i, path in enumerate(result_beam.explored_paths[:3], 1):
        print(f"  Path {i}: Score {path.total_score:.2f}, Depth {path.depth}")

    # Example 5: Visualizing the tree
    print("\n" + "=" * 70)
    print("Example 5: Tree Visualization")
    print("=" * 70)

    print("\nFull tree structure (Best-First Search):")
    ToTVisualizer.print_tree(result_best, max_depth=2)

    # Example 6: Comparing strategies
    print("\n" + "=" * 70)
    print("Example 6: Strategy Comparison")
    print("=" * 70)

    results = [
        ("Breadth-First", result_bfs),
        ("Depth-First", result_dfs),
        ("Best-First", result_best),
        ("Beam Search", result_beam)
    ]

    print("\nStrategy Comparison:")
    print(f"{'Strategy':<20} {'Nodes':<10} {'Pruned':<10} {'Score':<10} {'Time (s)':<10}")
    print("-" * 70)

    for name, result in results:
        print(f"{name:<20} {result.total_nodes:<10} {result.pruned_nodes:<10} "
              f"{result.best_path.total_score:<10.2f} {result.execution_time:<10.2f}")

    # Example 7: Cost tracking
    print("\n" + "=" * 70)
    print("Example 7: Cost Tracking")
    print("=" * 70)

    cost_tracker = CostTracker()

    for name, result in results:
        cost_tracker.track_usage(
            operation_id=f"tot_{name.lower().replace(' ', '_')}",
            model="gpt-4",
            input_tokens=result.token_count // 2,
            output_tokens=result.token_count // 2
        )

    stats = cost_tracker.get_statistics()
    print(f"\nTotal Cost for All Explorations:")
    print(f"  Total Tokens: {stats['total_tokens']:,}")
    print(f"  Total Cost: ${stats['total_cost']:.4f}")
    print(f"  Average Cost per Strategy: ${stats['total_cost']/4:.4f}")

    # Recommendations
    print("\n" + "=" * 70)
    print("Recommendations")
    print("=" * 70)

    print("""
Based on the exploration results:

1. Breadth-First Search: Good for exploring all options at each level
   - Use when: You need comprehensive exploration
   - Trade-off: Can be slow for deep trees

2. Depth-First Search: Fast exploration of deep paths
   - Use when: Quick prototyping needed
   - Trade-off: May miss better shallow alternatives

3. Best-First Search: Efficient with good pruning
   - Use when: You have good heuristics for scoring
   - Trade-off: Can get stuck in local optima

4. Beam Search: Balanced approach with controlled width
   - Use when: You need balance between exploration and efficiency
   - Trade-off: May miss some good paths outside the beam

For this system design problem, Best-First or Beam Search are recommended
for their balance of exploration quality and computational efficiency.
    """)

    print("\n" + "=" * 70)
    print("Example Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
