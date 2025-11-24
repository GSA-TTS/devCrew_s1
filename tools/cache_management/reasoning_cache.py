"""
Reasoning Cache Management System.

This module provides specialized caching for Chain-of-Thought (CoT) and
Tree-of-Thoughts (ToT) reasoning patterns with msgpack serialization.

Author: devCrew_s1
License: MIT
"""

import hashlib
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

import msgpack
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class CoTStep(BaseModel):
    """Chain-of-Thought reasoning step."""

    step_number: int = Field(description="Sequential step number (1-indexed)")
    thought: str = Field(description="Reasoning thought/explanation")
    result: str = Field(description="Result or conclusion of this step")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional step metadata"
    )
    confidence: Optional[float] = Field(
        default=None, description="Confidence score (0-1)"
    )
    timestamp: float = Field(
        default_factory=time.time, description="Step creation timestamp"
    )
    dependencies: List[int] = Field(
        default_factory=list, description="Step numbers this step depends on"
    )

    @field_validator("step_number")
    @classmethod
    def validate_step_number(cls, v: int) -> int:
        """Validate step number is positive."""
        if v <= 0:
            raise ValueError("Step number must be positive")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Validate confidence is between 0 and 1."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Confidence must be between 0 and 1")
        return v


class ToTNode(BaseModel):
    """Tree-of-Thoughts node."""

    node_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique node identifier"
    )
    thought: str = Field(description="Reasoning thought at this node")
    evaluation_score: float = Field(description="Node evaluation score")
    children: List[str] = Field(default_factory=list, description="Child node IDs")
    parent_id: Optional[str] = Field(default=None, description="Parent node ID")
    depth: int = Field(default=0, description="Depth in the tree (0=root)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional node metadata"
    )
    is_terminal: bool = Field(default=False, description="Whether this is a leaf node")
    visited: bool = Field(default=False, description="Whether node has been explored")
    timestamp: float = Field(
        default_factory=time.time, description="Node creation timestamp"
    )

    @field_validator("evaluation_score")
    @classmethod
    def validate_evaluation_score(cls, v: float) -> float:
        """Validate evaluation score is between 0 and 1."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Evaluation score must be between 0 and 1")
        return v

    @field_validator("depth")
    @classmethod
    def validate_depth(cls, v: int) -> int:
        """Validate depth is non-negative."""
        if v < 0:
            raise ValueError("Depth must be non-negative")
        return v

    def add_child(self, child_node_id: str) -> None:
        """Add a child node ID to this node."""
        if child_node_id not in self.children:
            self.children.append(child_node_id)

    def get_child_count(self) -> int:
        """Get the number of children."""
        return len(self.children)

    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return len(self.children) == 0 or self.is_terminal


class ReasoningType(str):
    """Reasoning type identifiers."""

    COT = "cot"  # Chain-of-Thought
    TOT = "tot"  # Tree-of-Thoughts


class ReasoningResult(BaseModel):
    """Complete reasoning result."""

    problem: str = Field(description="Original problem statement")
    reasoning_type: str = Field(description="Type of reasoning (cot/tot)")
    steps: Optional[List[CoTStep]] = Field(
        default=None, description="CoT reasoning steps"
    )
    tree_root: Optional[ToTNode] = Field(default=None, description="ToT tree root node")
    tree_nodes: Optional[Dict[str, ToTNode]] = Field(
        default=None, description="All ToT tree nodes by ID"
    )
    solution: str = Field(description="Final solution or answer")
    cache_key: str = Field(description="Cache key for this reasoning")
    total_steps: int = Field(default=0, description="Total number of steps/nodes")
    execution_time_ms: Optional[float] = Field(
        default=None, description="Execution time in milliseconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: float = Field(
        default_factory=time.time, description="Result creation timestamp"
    )

    @field_validator("reasoning_type")
    @classmethod
    def validate_reasoning_type(cls, v: str) -> str:
        """Validate reasoning type."""
        if v not in [ReasoningType.COT, ReasoningType.TOT]:
            raise ValueError(f"Invalid reasoning type: {v}")
        return v

    def get_step_count(self) -> int:
        """Get the total number of reasoning steps."""
        if self.steps:
            return len(self.steps)
        if self.tree_nodes:
            return len(self.tree_nodes)
        return 0


class ReasoningCache:
    """
    Specialized cache for Chain-of-Thought and Tree-of-Thoughts reasoning.

    Provides caching for complex reasoning patterns with efficient serialization
    using msgpack and integration with LLM cache backends.

    Examples:
        >>> from llm_cache import LLMCache, CacheConfig
        >>> llm_cache = LLMCache(CacheConfig())
        >>> reasoning_cache = ReasoningCache(llm_cache)
        >>> steps = [CoTStep(step_number=1, thought="First", result="1")]
        >>> key = reasoning_cache.cache_cot_steps("What is 1+1?", steps, ttl=600)
        >>> retrieved = reasoning_cache.get_cot_steps("What is 1+1?")
    """

    def __init__(self, cache_backend: Any, prefix: str = "reasoning:"):
        """
        Initialize reasoning cache with shared cache backend.

        Args:
            cache_backend: LLM cache backend instance
            prefix: Prefix for reasoning cache keys

        Raises:
            ValueError: If cache backend is invalid
        """
        if cache_backend is None:
            raise ValueError("Cache backend cannot be None")

        self._cache = cache_backend
        self._prefix = prefix
        logger.info(
            f"Initialized reasoning cache with prefix: {prefix}, "
            f"backend: {cache_backend.config.backend}"
        )

    def _generate_problem_hash(self, problem: str) -> str:
        """
        Generate SHA256 hash for a problem statement.

        Args:
            problem: Problem statement text

        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(problem.encode("utf-8")).hexdigest()

    def _generate_cache_key(
        self, problem: str, reasoning_type: str, suffix: str = ""
    ) -> str:
        """
        Generate cache key for reasoning result.

        Args:
            problem: Problem statement
            reasoning_type: Type of reasoning (cot/tot)
            suffix: Optional suffix for key

        Returns:
            Cache key string
        """
        problem_hash = self._generate_problem_hash(problem)
        key = f"{self._prefix}{reasoning_type}:{problem_hash}"
        if suffix:
            key = f"{key}:{suffix}"
        return key

    def _serialize_reasoning(self, data: Any) -> bytes:
        """
        Serialize reasoning data using msgpack.

        Args:
            data: Data to serialize (dict, list, or Pydantic model)

        Returns:
            Serialized bytes

        Raises:
            ValueError: If serialization fails
        """
        try:
            serializable_data: Any
            if isinstance(data, BaseModel):
                serializable_data = data.model_dump()
            elif isinstance(data, list):
                serializable_data = [
                    item.model_dump() if isinstance(item, BaseModel) else item
                    for item in data
                ]
            elif isinstance(data, dict):
                serializable_data = {
                    k: (v.model_dump() if isinstance(v, BaseModel) else v)
                    for k, v in data.items()
                }
            else:
                serializable_data = data

            return msgpack.packb(serializable_data, use_bin_type=True)

        except Exception as e:
            logger.error(f"Failed to serialize reasoning data: {e}")
            raise ValueError(f"Serialization failed: {e}") from e

    def _deserialize_reasoning(self, data: bytes) -> Any:
        """
        Deserialize reasoning data from msgpack.

        Args:
            data: Serialized bytes

        Returns:
            Deserialized data

        Raises:
            ValueError: If deserialization fails
        """
        try:
            return msgpack.unpackb(data, raw=False)
        except Exception as e:
            logger.error(f"Failed to deserialize reasoning data: {e}")
            raise ValueError(f"Deserialization failed: {e}") from e

    def cache_cot_steps(
        self,
        problem: str,
        steps: List[CoTStep],
        solution: str = "",
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
    ) -> str:
        """
        Cache Chain-of-Thought reasoning steps.

        Args:
            problem: Problem statement
            steps: List of CoT reasoning steps
            solution: Final solution
            ttl: Time-to-live in seconds
            metadata: Additional metadata
            execution_time_ms: Execution time in milliseconds

        Returns:
            Cache key for the stored reasoning

        Raises:
            ValueError: If steps list is empty
        """
        if not steps:
            raise ValueError("Steps list cannot be empty")

        try:
            cache_key = self._generate_cache_key(problem, ReasoningType.COT)

            reasoning_result = ReasoningResult(
                problem=problem,
                reasoning_type=ReasoningType.COT,
                steps=steps,
                solution=solution,
                cache_key=cache_key,
                total_steps=len(steps),
                execution_time_ms=execution_time_ms,
                metadata=metadata or {},
            )

            serialized_data = self._serialize_reasoning(reasoning_result)

            success = self._cache.set(
                prompt=cache_key,
                response=serialized_data.hex(),
                ttl=ttl,
                metadata={
                    "reasoning_type": ReasoningType.COT,
                    "total_steps": len(steps),
                    "problem_hash": self._generate_problem_hash(problem),
                },
            )

            if success:
                logger.info(
                    f"Cached CoT reasoning with {len(steps)} steps "
                    f"for problem hash {cache_key[:16]}..."
                )
                return cache_key
            else:
                raise ValueError("Failed to cache CoT steps")

        except Exception as e:
            logger.error(f"Failed to cache CoT steps: {e}")
            raise

    def get_cot_steps(
        self, problem: str, include_metadata: bool = True
    ) -> Optional[ReasoningResult]:
        """
        Retrieve cached Chain-of-Thought reasoning steps.

        Args:
            problem: Problem statement
            include_metadata: Whether to include metadata in result

        Returns:
            ReasoningResult with CoT steps if found, None otherwise
        """
        try:
            cache_key = self._generate_cache_key(problem, ReasoningType.COT)
            cached_response = self._cache.get(cache_key)

            if cached_response is None:
                logger.debug("No cached CoT steps found for problem")
                return None

            serialized_data = bytes.fromhex(cached_response.value)
            reasoning_data = self._deserialize_reasoning(serialized_data)

            reasoning_result = ReasoningResult(**reasoning_data)

            if not include_metadata:
                reasoning_result.metadata = {}

            logger.info(
                f"Retrieved CoT reasoning with {len(reasoning_result.steps or [])} "
                f"steps from cache"
            )
            return reasoning_result

        except Exception as e:
            logger.error(f"Failed to retrieve CoT steps: {e}")
            return None

    def cache_tot_tree(
        self,
        problem: str,
        tree_root: ToTNode,
        tree_nodes: Dict[str, ToTNode],
        solution: str = "",
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[float] = None,
    ) -> str:
        """
        Cache Tree-of-Thoughts reasoning tree.

        Args:
            problem: Problem statement
            tree_root: Root node of the ToT tree
            tree_nodes: Dictionary of all tree nodes by ID
            solution: Final solution
            ttl: Time-to-live in seconds
            metadata: Additional metadata
            execution_time_ms: Execution time in milliseconds

        Returns:
            Cache key for the stored reasoning

        Raises:
            ValueError: If tree is invalid
        """
        if not tree_nodes:
            raise ValueError("Tree nodes dictionary cannot be empty")

        if tree_root.node_id not in tree_nodes:
            raise ValueError("Root node must be in tree nodes dictionary")

        try:
            cache_key = self._generate_cache_key(problem, ReasoningType.TOT)

            reasoning_result = ReasoningResult(
                problem=problem,
                reasoning_type=ReasoningType.TOT,
                tree_root=tree_root,
                tree_nodes=tree_nodes,
                solution=solution,
                cache_key=cache_key,
                total_steps=len(tree_nodes),
                execution_time_ms=execution_time_ms,
                metadata=metadata or {},
            )

            serialized_data = self._serialize_reasoning(reasoning_result)

            success = self._cache.set(
                prompt=cache_key,
                response=serialized_data.hex(),
                ttl=ttl,
                metadata={
                    "reasoning_type": ReasoningType.TOT,
                    "total_nodes": len(tree_nodes),
                    "tree_depth": self._calculate_tree_depth(tree_root, tree_nodes),
                    "problem_hash": self._generate_problem_hash(problem),
                },
            )

            if success:
                logger.info(
                    f"Cached ToT tree with {len(tree_nodes)} nodes "
                    f"for problem hash {cache_key[:16]}..."
                )
                return cache_key
            else:
                raise ValueError("Failed to cache ToT tree")

        except Exception as e:
            logger.error(f"Failed to cache ToT tree: {e}")
            raise

    def get_tot_tree(
        self, problem: str, include_metadata: bool = True
    ) -> Optional[ReasoningResult]:
        """
        Retrieve cached Tree-of-Thoughts reasoning tree.

        Args:
            problem: Problem statement
            include_metadata: Whether to include metadata in result

        Returns:
            ReasoningResult with ToT tree if found, None otherwise
        """
        try:
            cache_key = self._generate_cache_key(problem, ReasoningType.TOT)
            cached_response = self._cache.get(cache_key)

            if cached_response is None:
                logger.debug("No cached ToT tree found for problem")
                return None

            serialized_data = bytes.fromhex(cached_response.value)
            reasoning_data = self._deserialize_reasoning(serialized_data)

            reasoning_result = ReasoningResult(**reasoning_data)

            if reasoning_result.tree_nodes:
                reasoning_result.tree_nodes = {
                    k: ToTNode(**v) if isinstance(v, dict) else v
                    for k, v in reasoning_result.tree_nodes.items()
                }

            if reasoning_result.tree_root and isinstance(
                reasoning_result.tree_root, dict
            ):
                reasoning_result.tree_root = ToTNode(**reasoning_result.tree_root)

            if not include_metadata:
                reasoning_result.metadata = {}

            logger.info(
                f"Retrieved ToT tree with {len(reasoning_result.tree_nodes or {})} "
                f"nodes from cache"
            )
            return reasoning_result

        except Exception as e:
            logger.error(f"Failed to retrieve ToT tree: {e}")
            return None

    def _calculate_tree_depth(self, root: ToTNode, nodes: Dict[str, ToTNode]) -> int:
        """
        Calculate the maximum depth of the ToT tree.

        Args:
            root: Root node of the tree
            nodes: All tree nodes

        Returns:
            Maximum tree depth
        """
        max_depth = 0

        def traverse(node_id: str, current_depth: int) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)

            node = nodes.get(node_id)
            if node:
                for child_id in node.children:
                    traverse(child_id, current_depth + 1)

        traverse(root.node_id, 0)
        return max_depth

    def get_reasoning_result(
        self, problem: str, reasoning_type: Optional[str] = None
    ) -> Optional[ReasoningResult]:
        """
        Get reasoning result (auto-detect type if not specified).

        Args:
            problem: Problem statement
            reasoning_type: Type of reasoning (cot/tot), auto-detect if None

        Returns:
            ReasoningResult if found, None otherwise
        """
        if reasoning_type == ReasoningType.COT:
            return self.get_cot_steps(problem)
        elif reasoning_type == ReasoningType.TOT:
            return self.get_tot_tree(problem)
        else:
            result = self.get_cot_steps(problem)
            if result is None:
                result = self.get_tot_tree(problem)
            return result

    def exists(self, problem: str, reasoning_type: Optional[str] = None) -> bool:
        """
        Check if reasoning is cached for a problem.

        Args:
            problem: Problem statement
            reasoning_type: Type of reasoning (cot/tot), check both if None

        Returns:
            True if cached, False otherwise
        """
        if reasoning_type == ReasoningType.COT:
            cache_key = self._generate_cache_key(problem, ReasoningType.COT)
            return self._cache.exists(cache_key)
        elif reasoning_type == ReasoningType.TOT:
            cache_key = self._generate_cache_key(problem, ReasoningType.TOT)
            return self._cache.exists(cache_key)
        else:
            cot_key = self._generate_cache_key(problem, ReasoningType.COT)
            tot_key = self._generate_cache_key(problem, ReasoningType.TOT)
            return self._cache.exists(cot_key) or self._cache.exists(tot_key)

    def invalidate(self, problem: str, reasoning_type: Optional[str] = None) -> int:
        """
        Invalidate cached reasoning for a problem.

        Args:
            problem: Problem statement
            reasoning_type: Type of reasoning (cot/tot), invalidate both if None

        Returns:
            Number of entries invalidated
        """
        count = 0

        if reasoning_type == ReasoningType.COT:
            cache_key = self._generate_cache_key(problem, ReasoningType.COT)
            count += self._cache.invalidate(cache_key)
        elif reasoning_type == ReasoningType.TOT:
            cache_key = self._generate_cache_key(problem, ReasoningType.TOT)
            count += self._cache.invalidate(cache_key)
        else:
            cot_key = self._generate_cache_key(problem, ReasoningType.COT)
            tot_key = self._generate_cache_key(problem, ReasoningType.TOT)
            count += self._cache.invalidate(cot_key)
            count += self._cache.invalidate(tot_key)

        logger.info(f"Invalidated {count} reasoning cache entries for problem")
        return count

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all reasoning entries matching pattern.

        Args:
            pattern: Pattern to match (e.g., "reasoning:cot:*")

        Returns:
            Number of entries invalidated
        """
        full_pattern = (
            f"{self._prefix}{pattern}"
            if not pattern.startswith(self._prefix)
            else pattern
        )
        count = self._cache.invalidate(full_pattern)
        logger.info(
            f"Invalidated {count} reasoning entries matching pattern: {pattern}"
        )
        return count

    def get_all_problems(self, reasoning_type: Optional[str] = None) -> List[str]:
        """
        Get all cached problem statements.

        Args:
            reasoning_type: Filter by reasoning type (cot/tot), all if None

        Returns:
            List of problem hashes (cache keys)
        """
        try:
            if reasoning_type:
                pattern = f"{self._prefix}{reasoning_type}:*"
            else:
                pattern = f"{self._prefix}*"

            keys = self._cache.get_all_keys(pattern)
            logger.info(f"Found {len(keys)} cached reasoning problems")
            return keys

        except Exception as e:
            logger.error(f"Failed to get cached problems: {e}")
            return []

    def merge_cot_steps(
        self,
        problem: str,
        additional_steps: List[CoTStep],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Merge additional steps into existing CoT reasoning.

        Args:
            problem: Problem statement
            additional_steps: Additional steps to merge
            ttl: New TTL for updated reasoning

        Returns:
            True if successful, False otherwise
        """
        try:
            existing_result = self.get_cot_steps(problem)
            if existing_result is None or existing_result.steps is None:
                logger.warning("No existing CoT reasoning found to merge into")
                return False

            existing_steps = existing_result.steps
            max_step_number = max(step.step_number for step in existing_steps)

            for step in additional_steps:
                step.step_number = max_step_number + step.step_number

            merged_steps = existing_steps + additional_steps

            self.cache_cot_steps(
                problem=problem,
                steps=merged_steps,
                solution=existing_result.solution,
                ttl=ttl,
                metadata=existing_result.metadata,
            )

            logger.info(
                f"Merged {len(additional_steps)} steps into existing CoT reasoning"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to merge CoT steps: {e}")
            return False

    def expand_tot_tree(
        self,
        problem: str,
        parent_node_id: str,
        new_nodes: List[ToTNode],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Expand existing ToT tree with new nodes.

        Args:
            problem: Problem statement
            parent_node_id: ID of parent node to attach new nodes to
            new_nodes: New nodes to add to tree
            ttl: New TTL for updated reasoning

        Returns:
            True if successful, False otherwise
        """
        try:
            existing_result = self.get_tot_tree(problem)
            if (
                existing_result is None
                or existing_result.tree_nodes is None
                or existing_result.tree_root is None
            ):
                logger.warning("No existing ToT tree found to expand")
                return False

            tree_nodes = existing_result.tree_nodes
            parent_node = tree_nodes.get(parent_node_id)

            if parent_node is None:
                logger.error(f"Parent node {parent_node_id} not found in tree")
                return False

            for node in new_nodes:
                node.parent_id = parent_node_id
                node.depth = parent_node.depth + 1
                tree_nodes[node.node_id] = node
                parent_node.add_child(node.node_id)

            tree_nodes[parent_node_id] = parent_node

            self.cache_tot_tree(
                problem=problem,
                tree_root=existing_result.tree_root,
                tree_nodes=tree_nodes,
                solution=existing_result.solution,
                ttl=ttl,
                metadata=existing_result.metadata,
            )

            logger.info(
                f"Expanded ToT tree with {len(new_nodes)} new nodes "
                f"under parent {parent_node_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to expand ToT tree: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get reasoning cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            all_keys = self.get_all_problems()
            cot_keys = [k for k in all_keys if f":{ReasoningType.COT}:" in k]
            tot_keys = [k for k in all_keys if f":{ReasoningType.TOT}:" in k]

            cache_stats = self._cache.get_stats()

            return {
                "total_reasoning_entries": len(all_keys),
                "cot_entries": len(cot_keys),
                "tot_entries": len(tot_keys),
                "cache_backend": cache_stats.backend,
                "total_cache_size_mb": cache_stats.total_size_mb,
                "cache_hit_rate": cache_stats.hit_rate,
                "prefix": self._prefix,
            }

        except Exception as e:
            logger.error(f"Failed to get reasoning cache statistics: {e}")
            return {}

    def visualize_tot_tree(
        self, reasoning_result: ReasoningResult, max_depth: Optional[int] = None
    ) -> str:
        """
        Create a text visualization of a ToT tree.

        Args:
            reasoning_result: ToT reasoning result to visualize
            max_depth: Maximum depth to visualize (None for all)

        Returns:
            Text representation of the tree
        """
        if (
            reasoning_result.reasoning_type != ReasoningType.TOT
            or not reasoning_result.tree_root
            or not reasoning_result.tree_nodes
        ):
            return "Invalid ToT reasoning result"

        lines: List[str] = []
        nodes = reasoning_result.tree_nodes
        root = reasoning_result.tree_root

        def traverse(node_id: str, indent: str, is_last: bool, depth: int) -> None:
            if max_depth is not None and depth > max_depth:
                return

            node = nodes.get(node_id)
            if not node:
                return

            prefix = "└── " if is_last else "├── "
            lines.append(
                f"{indent}{prefix}[{node.evaluation_score:.2f}] "
                f"{node.thought[:60]}..."
            )

            child_indent = indent + ("    " if is_last else "│   ")
            for i, child_id in enumerate(node.children):
                is_last_child = i == len(node.children) - 1
                traverse(child_id, child_indent, is_last_child, depth + 1)

        lines.append(f"Root: [{root.evaluation_score:.2f}] {root.thought[:60]}...")
        for i, child_id in enumerate(root.children):
            is_last_child = i == len(root.children) - 1
            traverse(child_id, "", is_last_child, 1)

        return "\n".join(lines)
