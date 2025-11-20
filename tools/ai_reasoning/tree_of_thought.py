"""
Tree-of-Thoughts (ToT) Reasoning Implementation.

This module implements multi-path exploration with branching, pruning,
backtracking, and path scoring capabilities.

Protocol Coverage:
- P-COG-TOT: Tree-of-Thought protocol
- P-PATTERN-MANAGEMENT: Architectural pattern selection
- P-RESOURCE: Resource allocation and optimization
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import heapq
from collections import deque


logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Tree search strategy types."""
    BREADTH_FIRST = "breadth_first"
    DEPTH_FIRST = "depth_first"
    BEST_FIRST = "best_first"
    BEAM_SEARCH = "beam_search"


class NodeState(Enum):
    """Node state in the tree."""
    PENDING = "pending"
    EXPLORING = "exploring"
    EVALUATED = "evaluated"
    PRUNED = "pruned"
    SOLUTION = "solution"


@dataclass
class ThoughtNode:
    """Represents a node in the thought tree."""
    id: str
    depth: int
    thought: str
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    score: float = 0.0
    state: NodeState = NodeState.PENDING
    path_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "depth": self.depth,
            "thought": self.thought,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "score": self.score,
            "state": self.state.value,
            "path_score": self.path_score,
            "metadata": self.metadata
        }


@dataclass
class TreePath:
    """Represents a complete path through the tree."""
    nodes: List[ThoughtNode]
    total_score: float
    is_solution: bool
    depth: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "total_score": self.total_score,
            "is_solution": self.is_solution,
            "depth": self.depth
        }


@dataclass
class ToTResult:
    """Result of Tree-of-Thoughts exploration."""
    question: str
    root_node: ThoughtNode
    all_nodes: Dict[str, ThoughtNode]
    best_path: TreePath
    explored_paths: List[TreePath]
    strategy: SearchStrategy
    total_nodes: int
    pruned_nodes: int
    token_count: int = 0
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "root_node": self.root_node.to_dict(),
            "best_path": self.best_path.to_dict(),
            "explored_paths": [path.to_dict() for path in self.explored_paths],
            "strategy": self.strategy.value,
            "total_nodes": self.total_nodes,
            "pruned_nodes": self.pruned_nodes,
            "token_count": self.token_count,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }


class TreeOfThoughtsExplorer:
    """
    Tree-of-Thoughts exploration engine with multi-path exploration,
    pruning, backtracking, and path scoring.
    """

    def __init__(
        self,
        llm_provider: Any,
        max_depth: int = 3,
        branching_factor: int = 3,
        beam_width: int = 2,
        pruning_threshold: float = 0.3,
        temperature: float = 0.8
    ):
        """
        Initialize ToT explorer.

        Args:
            llm_provider: LLM provider instance
            max_depth: Maximum tree depth
            branching_factor: Number of branches per node
            beam_width: Width for beam search
            pruning_threshold: Minimum score to keep exploring
            temperature: LLM temperature for diversity
        """
        self.llm_provider = llm_provider
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.beam_width = beam_width
        self.pruning_threshold = pruning_threshold
        self.temperature = temperature
        self.token_count = 0
        self.node_counter = 0

    async def explore(
        self,
        question: str,
        strategy: SearchStrategy = SearchStrategy.BEST_FIRST,
        goal_checker: Optional[Any] = None,
        context: Optional[str] = None
    ) -> ToTResult:
        """
        Explore thought tree using specified strategy.

        Args:
            question: Question to explore
            strategy: Search strategy to use
            goal_checker: Function to check if goal is reached
            context: Additional context

        Returns:
            ToTResult with best path and exploration details
        """
        import time
        start_time = time.time()

        logger.info(f"Starting ToT exploration with strategy: {strategy.value}")

        # Initialize tree
        root_node = self._create_root_node(question)
        all_nodes = {root_node.id: root_node}

        # Explore based on strategy
        if strategy == SearchStrategy.BREADTH_FIRST:
            best_path, explored_paths = await self._breadth_first_search(
                root_node, all_nodes, question, goal_checker, context
            )
        elif strategy == SearchStrategy.DEPTH_FIRST:
            best_path, explored_paths = await self._depth_first_search(
                root_node, all_nodes, question, goal_checker, context
            )
        elif strategy == SearchStrategy.BEAM_SEARCH:
            best_path, explored_paths = await self._beam_search(
                root_node, all_nodes, question, goal_checker, context
            )
        else:  # BEST_FIRST
            best_path, explored_paths = await self._best_first_search(
                root_node, all_nodes, question, goal_checker, context
            )

        # Count pruned nodes
        pruned_count = sum(
            1 for node in all_nodes.values() if node.state == NodeState.PRUNED
        )

        result = ToTResult(
            question=question,
            root_node=root_node,
            all_nodes=all_nodes,
            best_path=best_path,
            explored_paths=explored_paths,
            strategy=strategy,
            total_nodes=len(all_nodes),
            pruned_nodes=pruned_count,
            token_count=self.token_count,
            execution_time=time.time() - start_time
        )

        logger.info(
            f"ToT exploration completed: {len(all_nodes)} nodes, "
            f"{pruned_count} pruned, {result.execution_time:.2f}s"
        )
        return result

    async def _breadth_first_search(
        self,
        root: ThoughtNode,
        all_nodes: Dict[str, ThoughtNode],
        question: str,
        goal_checker: Optional[Any],
        context: Optional[str]
    ) -> Tuple[TreePath, List[TreePath]]:
        """Breadth-first tree exploration."""
        queue = deque([root])
        explored_paths = []

        while queue:
            node = queue.popleft()

            if node.depth >= self.max_depth:
                path = self._construct_path(node, all_nodes)
                explored_paths.append(path)
                continue

            # Check if goal reached
            if goal_checker and await goal_checker(node):
                node.state = NodeState.SOLUTION
                path = self._construct_path(node, all_nodes)
                return path, explored_paths

            # Generate children
            children = await self._generate_children(node, question, context)
            for child in children:
                all_nodes[child.id] = child
                node.children_ids.append(child.id)

                # Evaluate and prune
                await self._evaluate_node(child, question, context)
                if child.score >= self.pruning_threshold:
                    queue.append(child)
                else:
                    child.state = NodeState.PRUNED

        # Return best path
        best_path = max(explored_paths, key=lambda p: p.total_score) if explored_paths else self._construct_path(root, all_nodes)
        return best_path, explored_paths

    async def _depth_first_search(
        self,
        root: ThoughtNode,
        all_nodes: Dict[str, ThoughtNode],
        question: str,
        goal_checker: Optional[Any],
        context: Optional[str]
    ) -> Tuple[TreePath, List[TreePath]]:
        """Depth-first tree exploration with backtracking."""
        stack = [root]
        explored_paths = []

        while stack:
            node = stack.pop()

            if node.depth >= self.max_depth:
                path = self._construct_path(node, all_nodes)
                explored_paths.append(path)
                continue

            # Check if goal reached
            if goal_checker and await goal_checker(node):
                node.state = NodeState.SOLUTION
                path = self._construct_path(node, all_nodes)
                return path, explored_paths

            # Generate children
            children = await self._generate_children(node, question, context)
            for child in children:
                all_nodes[child.id] = child
                node.children_ids.append(child.id)

                # Evaluate and prune
                await self._evaluate_node(child, question, context)
                if child.score >= self.pruning_threshold:
                    stack.append(child)
                else:
                    child.state = NodeState.PRUNED

        # Return best path
        best_path = max(explored_paths, key=lambda p: p.total_score) if explored_paths else self._construct_path(root, all_nodes)
        return best_path, explored_paths

    async def _best_first_search(
        self,
        root: ThoughtNode,
        all_nodes: Dict[str, ThoughtNode],
        question: str,
        goal_checker: Optional[Any],
        context: Optional[str]
    ) -> Tuple[TreePath, List[TreePath]]:
        """Best-first tree exploration using priority queue."""
        # Priority queue: (-score, counter, node) where counter ensures ordering
        heap = [(-root.score, 0, root)]
        explored_paths = []
        counter = 1  # Counter to break ties

        while heap:
            neg_score, _, node = heapq.heappop(heap)

            if node.depth >= self.max_depth:
                path = self._construct_path(node, all_nodes)
                explored_paths.append(path)
                continue

            # Check if goal reached
            if goal_checker and await goal_checker(node):
                node.state = NodeState.SOLUTION
                path = self._construct_path(node, all_nodes)
                return path, explored_paths

            # Generate children
            children = await self._generate_children(node, question, context)
            for child in children:
                all_nodes[child.id] = child
                node.children_ids.append(child.id)

                # Evaluate and prune
                await self._evaluate_node(child, question, context)
                if child.score >= self.pruning_threshold:
                    heapq.heappush(heap, (-child.score, counter, child))
                    counter += 1
                else:
                    child.state = NodeState.PRUNED

        # Return best path
        best_path = max(explored_paths, key=lambda p: p.total_score) if explored_paths else self._construct_path(root, all_nodes)
        return best_path, explored_paths

    async def _beam_search(
        self,
        root: ThoughtNode,
        all_nodes: Dict[str, ThoughtNode],
        question: str,
        goal_checker: Optional[Any],
        context: Optional[str]
    ) -> Tuple[TreePath, List[TreePath]]:
        """Beam search with limited width."""
        current_beam = [root]
        explored_paths = []

        for depth in range(self.max_depth):
            next_beam = []

            for node in current_beam:
                # Check if goal reached
                if goal_checker and await goal_checker(node):
                    node.state = NodeState.SOLUTION
                    path = self._construct_path(node, all_nodes)
                    return path, explored_paths

                # Generate children
                children = await self._generate_children(node, question, context)
                for child in children:
                    all_nodes[child.id] = child
                    node.children_ids.append(child.id)

                    # Evaluate
                    await self._evaluate_node(child, question, context)
                    next_beam.append(child)

            # Keep top beam_width nodes
            next_beam.sort(key=lambda n: n.score, reverse=True)
            current_beam = next_beam[:self.beam_width]

            # Prune others
            for node in next_beam[self.beam_width:]:
                node.state = NodeState.PRUNED

            if not current_beam:
                break

        # Collect final paths
        for node in current_beam:
            path = self._construct_path(node, all_nodes)
            explored_paths.append(path)

        # Return best path
        best_path = max(explored_paths, key=lambda p: p.total_score) if explored_paths else self._construct_path(root, all_nodes)
        return best_path, explored_paths

    async def _generate_children(
        self,
        parent: ThoughtNode,
        question: str,
        context: Optional[str]
    ) -> List[ThoughtNode]:
        """Generate child nodes for a parent node."""
        parent.state = NodeState.EXPLORING

        prompt = self._build_branching_prompt(parent, question, context)

        children = []
        for i in range(self.branching_factor):
            response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=300
            )

            self.token_count += response.token_count
            thought = response.text.strip()

            child = ThoughtNode(
                id=self._generate_node_id(),
                depth=parent.depth + 1,
                thought=thought,
                parent_id=parent.id,
                state=NodeState.PENDING
            )
            children.append(child)

        return children

    async def _evaluate_node(
        self,
        node: ThoughtNode,
        question: str,
        context: Optional[str]
    ) -> None:
        """Evaluate a node and assign score."""
        evaluation_prompt = f"""
Evaluate the following thought in the context of solving this problem:

Question: {question}
{f"Context: {context}" if context else ""}

Thought: {node.thought}

Rate this thought on a scale of 0.0 to 1.0 based on:
1. Relevance to the question
2. Logical soundness
3. Progress toward solution
4. Clarity and specificity

Provide only the numerical score (e.g., 0.75):
"""

        response = await self.llm_provider.generate(
            prompt=evaluation_prompt,
            temperature=0.2,
            max_tokens=10
        )

        self.token_count += response.token_count

        try:
            score_text = response.text.strip()
            node.score = float(score_text)
        except ValueError:
            logger.warning(f"Failed to parse score: {response.text}")
            node.score = 0.5

        node.state = NodeState.EVALUATED

    def _create_root_node(self, question: str) -> ThoughtNode:
        """Create root node of the tree."""
        return ThoughtNode(
            id=self._generate_node_id(),
            depth=0,
            thought=f"Initial question: {question}",
            score=1.0,
            state=NodeState.EVALUATED
        )

    def _construct_path(
        self,
        leaf: ThoughtNode,
        all_nodes: Dict[str, ThoughtNode]
    ) -> TreePath:
        """Construct path from root to leaf."""
        path_nodes = []
        current = leaf

        while current:
            path_nodes.insert(0, current)
            if current.parent_id:
                current = all_nodes.get(current.parent_id)
            else:
                current = None

        # Calculate path score
        total_score = sum(node.score for node in path_nodes) / len(path_nodes)

        return TreePath(
            nodes=path_nodes,
            total_score=total_score,
            is_solution=leaf.state == NodeState.SOLUTION,
            depth=leaf.depth
        )

    def _build_branching_prompt(
        self,
        parent: ThoughtNode,
        question: str,
        context: Optional[str]
    ) -> str:
        """Build prompt for generating child thoughts."""
        prompt = f"""
We are solving the following problem step by step:

Question: {question}
{f"Context: {context}" if context else ""}

Current thought path (depth {parent.depth}):
{parent.thought}

Generate a different possible next step or approach to continue solving this problem.
Think creatively and explore alternative directions.

Next thought:
"""
        return prompt

    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        self.node_counter += 1
        return f"node_{self.node_counter}"


class ToTVisualizer:
    """Visualizer for Tree-of-Thoughts exploration."""

    @staticmethod
    def print_tree(result: ToTResult, max_depth: Optional[int] = None) -> None:
        """Print tree structure in console."""
        print(f"\n=== Tree of Thoughts: {result.question} ===\n")
        print(f"Total nodes: {result.total_nodes}")
        print(f"Pruned nodes: {result.pruned_nodes}")
        print(f"Strategy: {result.strategy.value}\n")

        ToTVisualizer._print_node(
            result.root_node, result.all_nodes, 0, max_depth or result.best_path.depth
        )

        print(f"\n=== Best Path (score: {result.best_path.total_score:.2f}) ===")
        for i, node in enumerate(result.best_path.nodes):
            print(f"{i}. [{node.score:.2f}] {node.thought}")

    @staticmethod
    def _print_node(
        node: ThoughtNode,
        all_nodes: Dict[str, ThoughtNode],
        indent: int,
        max_depth: int
    ) -> None:
        """Recursively print node and children."""
        if node.depth > max_depth:
            return

        prefix = "  " * indent
        state_icon = {
            NodeState.PENDING: "⏳",
            NodeState.EXPLORING: "🔍",
            NodeState.EVALUATED: "✓",
            NodeState.PRUNED: "✗",
            NodeState.SOLUTION: "🎯"
        }.get(node.state, "?")

        print(f"{prefix}{state_icon} [{node.score:.2f}] {node.thought[:60]}...")

        for child_id in node.children_ids:
            child = all_nodes.get(child_id)
            if child:
                ToTVisualizer._print_node(child, all_nodes, indent + 1, max_depth)


# Example usage
if __name__ == "__main__":
    import asyncio

    # Mock LLM provider
    class MockLLMProvider:
        async def generate(self, prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
            import random
            thoughts = [
                "Consider using microservices architecture",
                "Evaluate monolithic vs distributed approach",
                "Assess team capabilities and infrastructure",
                "Analyze scalability requirements",
                "Review existing system constraints"
            ]
            return {
                "text": random.choice(thoughts),
                "token_count": 50
            }

    async def main():
        provider = MockLLMProvider()
        explorer = TreeOfThoughtsExplorer(
            provider,
            max_depth=2,
            branching_factor=2,
            beam_width=2
        )

        result = await explorer.explore(
            question="What architecture should we use for our new application?",
            strategy=SearchStrategy.BEAM_SEARCH
        )

        ToTVisualizer.print_tree(result)

    asyncio.run(main())
