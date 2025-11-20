"""
Comprehensive Test Suite for AI Reasoning Framework.

Tests all modules with mocked LLM calls to ensure functionality
without requiring actual API keys.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import modules to test
from issue_42_chain_of_thought import (
    ChainOfThoughtReasoner, ReasoningStrategy, ThoughtStep,
    ReasoningResult, CoTValidator
)
from issue_42_tree_of_thought import (
    TreeOfThoughtsExplorer, SearchStrategy, ThoughtNode,
    NodeState, TreePath, ToTResult
)
from issue_42_context_manager import ContextManager, ContextEntry
from issue_42_llm_providers import (
    MockLLMProvider, LLMProviderFactory, LLMProvider,
    OpenAIProvider, AnthropicProvider
)
from issue_42_prompt_templates import (
    PromptTemplate, PromptTemplateLibrary, TemplateType, FewShotExample
)
from issue_42_evaluator import ReasoningEvaluator, MetricType
from issue_42_tracer import LangSmithTracer, TracingContext, TraceType
from issue_42_cost_tracker import CostTracker, TokenCounter, CostOptimizer


# Fixtures

@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    return MockLLMProvider(
        responses=[
            "Let's start by analyzing the requirements.",
            "Next, we should consider the architectural patterns.",
            "Therefore, I recommend using microservices architecture.",
        ]
    )


@pytest.fixture
def sample_question():
    """Sample question for testing."""
    return "What is the best architectural pattern for a scalable web application?"


# Chain-of-Thought Tests

@pytest.mark.asyncio
async def test_cot_zero_shot_reasoning(mock_llm_provider, sample_question):
    """Test zero-shot CoT reasoning."""
    reasoner = ChainOfThoughtReasoner(
        llm_provider=mock_llm_provider,
        max_steps=3
    )

    result = await reasoner.reason(
        question=sample_question,
        strategy=ReasoningStrategy.ZERO_SHOT
    )

    assert isinstance(result, ReasoningResult)
    assert result.question == sample_question
    assert len(result.steps) > 0
    assert result.final_answer
    assert 0 <= result.confidence <= 1
    assert result.strategy == ReasoningStrategy.ZERO_SHOT


@pytest.mark.asyncio
async def test_cot_few_shot_reasoning(mock_llm_provider, sample_question):
    """Test few-shot CoT reasoning with examples."""
    reasoner = ChainOfThoughtReasoner(
        llm_provider=mock_llm_provider,
        max_steps=3
    )

    examples = [
        {
            "question": "What database should I use?",
            "reasoning": "Step 1: Assess data structure. Step 2: Consider scale.",
            "answer": "PostgreSQL for structured data"
        }
    ]

    result = await reasoner.reason(
        question=sample_question,
        strategy=ReasoningStrategy.FEW_SHOT,
        examples=examples
    )

    assert isinstance(result, ReasoningResult)
    assert result.strategy == ReasoningStrategy.FEW_SHOT
    assert len(result.steps) > 0


@pytest.mark.asyncio
async def test_cot_self_consistency(mock_llm_provider, sample_question):
    """Test self-consistency CoT reasoning."""
    reasoner = ChainOfThoughtReasoner(
        llm_provider=mock_llm_provider,
        max_steps=2,
        self_consistency_samples=2
    )

    result = await reasoner.reason(
        question=sample_question,
        strategy=ReasoningStrategy.SELF_CONSISTENCY
    )

    assert isinstance(result, ReasoningResult)
    assert result.strategy == ReasoningStrategy.SELF_CONSISTENCY
    assert "consistency_ratio" in result.metadata


@pytest.mark.asyncio
async def test_cot_reflection(mock_llm_provider, sample_question):
    """Test reflection-based CoT reasoning."""
    reasoner = ChainOfThoughtReasoner(
        llm_provider=mock_llm_provider,
        max_steps=3,
        enable_reflection=True
    )

    result = await reasoner.reason(
        question=sample_question,
        strategy=ReasoningStrategy.REFLECTION
    )

    assert isinstance(result, ReasoningResult)
    assert result.strategy == ReasoningStrategy.REFLECTION
    assert "reflection" in result.metadata


def test_cot_validator():
    """Test CoT validation."""
    # Create mock result
    result = ReasoningResult(
        question="Test question",
        steps=[
            ThoughtStep(1, "Test question", "Step 1 thought", confidence=0.9),
            ThoughtStep(2, "Test question", "Step 2 thought", confidence=0.8)
        ],
        final_answer="Test answer",
        confidence=0.85,
        strategy=ReasoningStrategy.ZERO_SHOT
    )

    validation = CoTValidator.validate_reasoning_chain(result)
    assert "is_valid" in validation
    assert "issues" in validation
    assert "warnings" in validation


# Tree-of-Thought Tests

@pytest.mark.asyncio
async def test_tot_breadth_first_search(mock_llm_provider, sample_question):
    """Test breadth-first ToT exploration."""
    explorer = TreeOfThoughtsExplorer(
        llm_provider=mock_llm_provider,
        max_depth=2,
        branching_factor=2
    )

    result = await explorer.explore(
        question=sample_question,
        strategy=SearchStrategy.BREADTH_FIRST
    )

    assert isinstance(result, ToTResult)
    assert result.question == sample_question
    assert result.total_nodes > 0
    assert result.best_path is not None
    assert result.strategy == SearchStrategy.BREADTH_FIRST


@pytest.mark.asyncio
async def test_tot_depth_first_search(mock_llm_provider, sample_question):
    """Test depth-first ToT exploration."""
    explorer = TreeOfThoughtsExplorer(
        llm_provider=mock_llm_provider,
        max_depth=2,
        branching_factor=2
    )

    result = await explorer.explore(
        question=sample_question,
        strategy=SearchStrategy.DEPTH_FIRST
    )

    assert isinstance(result, ToTResult)
    assert result.strategy == SearchStrategy.DEPTH_FIRST
    assert len(result.all_nodes) > 0


@pytest.mark.asyncio
async def test_tot_best_first_search(mock_llm_provider, sample_question):
    """Test best-first ToT exploration."""
    explorer = TreeOfThoughtsExplorer(
        llm_provider=mock_llm_provider,
        max_depth=2,
        branching_factor=2
    )

    result = await explorer.explore(
        question=sample_question,
        strategy=SearchStrategy.BEST_FIRST
    )

    assert isinstance(result, ToTResult)
    assert result.strategy == SearchStrategy.BEST_FIRST


@pytest.mark.asyncio
async def test_tot_beam_search(mock_llm_provider, sample_question):
    """Test beam search ToT exploration."""
    explorer = TreeOfThoughtsExplorer(
        llm_provider=mock_llm_provider,
        max_depth=2,
        branching_factor=2,
        beam_width=2
    )

    result = await explorer.explore(
        question=sample_question,
        strategy=SearchStrategy.BEAM_SEARCH
    )

    assert isinstance(result, ToTResult)
    assert result.strategy == SearchStrategy.BEAM_SEARCH


def test_tot_node_creation():
    """Test ToT node creation and state."""
    node = ThoughtNode(
        id="test_1",
        depth=0,
        thought="Test thought",
        score=0.8
    )

    assert node.id == "test_1"
    assert node.depth == 0
    assert node.state == NodeState.PENDING
    assert node.score == 0.8


# Context Manager Tests

@pytest.mark.asyncio
async def test_context_manager_add_entry():
    """Test adding entries to context."""
    manager = ContextManager(max_tokens=1000)

    entry = await manager.add_entry(
        content="Test content",
        role="user",
        tokens=10
    )

    assert isinstance(entry, ContextEntry)
    assert entry.content == "Test content"
    assert entry.role == "user"
    assert manager.context_window.total_tokens == 10


@pytest.mark.asyncio
async def test_context_manager_get_context():
    """Test retrieving context."""
    manager = ContextManager(max_tokens=1000)

    await manager.add_entry("Entry 1", "user", 10)
    await manager.add_entry("Entry 2", "assistant", 10)

    context = await manager.get_context()
    assert len(context) == 2


@pytest.mark.asyncio
async def test_context_manager_clear():
    """Test clearing context."""
    manager = ContextManager(max_tokens=1000)

    await manager.add_entry("Entry 1", "user", 10)
    await manager.clear_context(keep_system=False)

    context = await manager.get_context()
    assert len(context) == 0
    assert manager.context_window.total_tokens == 0


@pytest.mark.asyncio
async def test_context_manager_compression(mock_llm_provider):
    """Test context compression."""
    manager = ContextManager(max_tokens=1000, sliding_window_size=2)

    # Add multiple entries
    for i in range(5):
        await manager.add_entry(f"Entry {i}", "user", 100)

    # Compress
    result = await manager.compress_context(mock_llm_provider)

    assert result["compressed"]
    assert result["new_tokens"] < result["original_tokens"]


@pytest.mark.asyncio
async def test_context_validation():
    """Test context validation."""
    manager = ContextManager(max_tokens=1000)

    await manager.add_entry("Test", "user", 10)

    validation = await manager.validate_context()
    assert validation["is_valid"]


# LLM Provider Tests

@pytest.mark.asyncio
async def test_mock_llm_provider():
    """Test mock LLM provider."""
    provider = MockLLMProvider(responses=["Test response"])

    response = await provider.generate(
        prompt="Test prompt",
        temperature=0.7,
        max_tokens=100
    )

    assert response.text == "Test response"
    assert response.provider == "mock"
    assert response.token_count > 0


def test_llm_provider_factory():
    """Test LLM provider factory."""
    provider = LLMProviderFactory.create(
        provider_type=LLMProvider.MOCK,
        api_key="test_key"
    )

    assert isinstance(provider, MockLLMProvider)


@pytest.mark.asyncio
async def test_provider_rate_limiting():
    """Test rate limiting."""
    provider = MockLLMProvider(rate_limit_per_minute=2)

    # Make requests
    await provider.generate("Test 1", 0.7, 100)
    await provider.generate("Test 2", 0.7, 100)

    # Third request should be rate limited
    import time
    start = time.time()
    await provider.generate("Test 3", 0.7, 100)
    duration = time.time() - start

    # Should have been delayed
    assert duration > 0


# Prompt Template Tests

def test_prompt_template_library():
    """Test prompt template library."""
    library = PromptTemplateLibrary()

    # Should have default templates
    templates = library.list_templates()
    assert len(templates) > 0


def test_get_prompt_template():
    """Test getting prompt template."""
    library = PromptTemplateLibrary()

    template = library.get("cot_zero_shot")
    assert template is not None
    assert template.type == TemplateType.CHAIN_OF_THOUGHT


def test_render_prompt_template():
    """Test rendering prompt template."""
    template = PromptTemplate(
        name="test",
        type=TemplateType.CHAIN_OF_THOUGHT,
        version="1.0",
        template="Question: {question}\nAnswer:",
        variables=["question"],
        description="Test template"
    )

    rendered = template.render(question="What is AI?")
    assert "What is AI?" in rendered


def test_few_shot_examples():
    """Test few-shot example management."""
    manager = FewShotExample()

    examples = manager.get_examples("architecture", limit=2)
    assert len(examples) <= 2

    manager.add_example(
        "test_category",
        "Test question",
        "Test reasoning",
        "Test answer"
    )

    examples = manager.get_examples("test_category")
    assert len(examples) == 1


# Evaluator Tests

@pytest.mark.asyncio
async def test_evaluator_cot():
    """Test CoT evaluation."""
    evaluator = ReasoningEvaluator()

    result = ReasoningResult(
        question="What is 2+2?",
        steps=[
            ThoughtStep(1, "What is 2+2?", "Add 2 and 2", confidence=0.9),
            ThoughtStep(2, "What is 2+2?", "2 + 2 = 4", confidence=0.95)
        ],
        final_answer="4",
        confidence=0.92,
        strategy=ReasoningStrategy.ZERO_SHOT,
        token_count=100,
        execution_time=1.5
    )

    evaluations = await evaluator.evaluate_cot(result, ground_truth="4")

    assert "completeness" in evaluations
    assert "consistency" in evaluations
    assert "accuracy" in evaluations
    assert evaluations["accuracy"].score > 0.8


@pytest.mark.asyncio
async def test_self_consistency_evaluation():
    """Test self-consistency evaluation."""
    evaluator = ReasoningEvaluator()

    results = [
        ReasoningResult(
            question="Test",
            steps=[],
            final_answer="Answer A",
            confidence=0.9,
            strategy=ReasoningStrategy.ZERO_SHOT
        ),
        ReasoningResult(
            question="Test",
            steps=[],
            final_answer="Answer A",
            confidence=0.9,
            strategy=ReasoningStrategy.ZERO_SHOT
        ),
        ReasoningResult(
            question="Test",
            steps=[],
            final_answer="Answer B",
            confidence=0.9,
            strategy=ReasoningStrategy.ZERO_SHOT
        )
    ]

    eval_result = await evaluator.evaluate_self_consistency(results, "Test")

    assert eval_result.metric_type == MetricType.CONSISTENCY
    assert 0 <= eval_result.score <= 1


# Tracer Tests

def test_tracer_initialization():
    """Test tracer initialization."""
    tracer = LangSmithTracer(
        project_name="test",
        enabled=True
    )

    assert tracer.project_name == "test"
    assert tracer.enabled


def test_trace_lifecycle():
    """Test trace start and end."""
    tracer = LangSmithTracer(enabled=True)

    trace_id = tracer.start_trace("Test Trace", tags=["test"])
    assert trace_id
    assert trace_id in tracer.active_traces

    trace = tracer.end_trace(trace_id)
    assert trace is not None
    assert trace.end_time is not None
    assert trace_id not in tracer.active_traces


def test_trace_events():
    """Test adding events to trace."""
    tracer = LangSmithTracer(enabled=True)

    trace_id = tracer.start_trace("Test")

    event_id = tracer.add_event(
        trace_id=trace_id,
        event_type=TraceType.STEP_START,
        name="Test Step"
    )

    assert event_id is not None

    trace = tracer.get_trace(trace_id)
    assert len(trace.events) == 1


def test_tracing_context():
    """Test tracing context manager."""
    tracer = LangSmithTracer(enabled=True)

    with TracingContext(tracer, "Test Context") as trace_id:
        assert trace_id in tracer.active_traces

    # Should be completed after context exits
    assert trace_id not in tracer.active_traces


# Cost Tracker Tests

def test_token_counter():
    """Test token counting."""
    counter = TokenCounter()

    tokens = counter.count_tokens("Hello world", model="gpt-4")
    assert tokens > 0


def test_cost_tracker_usage():
    """Test tracking usage."""
    tracker = CostTracker()

    usage = tracker.track_usage(
        operation_id="op_1",
        model="gpt-4",
        input_tokens=100,
        output_tokens=50
    )

    assert usage.total_tokens == 150
    assert tracker.total_input_tokens == 100
    assert tracker.total_output_tokens == 50


def test_cost_estimation():
    """Test cost estimation."""
    tracker = CostTracker()

    estimate = tracker.estimate_cost(
        model="gpt-4",
        input_tokens=1000,
        output_tokens=500
    )

    assert estimate.total_cost > 0
    assert estimate.input_cost > 0
    assert estimate.output_cost > 0


def test_budget_alerts():
    """Test budget alert system."""
    alerts = []

    def alert_callback(alert):
        alerts.append(alert)

    tracker = CostTracker(
        budget_limit=0.01,
        warning_threshold=0.5,
        alert_callback=alert_callback
    )

    # Track usage that exceeds budget
    tracker.track_usage("op_1", "gpt-4", 10000, 5000)

    # Should have generated alerts
    assert len(alerts) > 0


def test_cost_optimizer():
    """Test cost optimizer recommendations."""
    model = CostOptimizer.recommend_model("simple", budget_conscious=True)
    assert model in ["gpt-3.5-turbo", "gpt-4o"]

    budget = CostOptimizer.estimate_budget_for_operations(
        model="gpt-4",
        avg_input_tokens=1000,
        avg_output_tokens=500,
        num_operations=10
    )
    assert budget > 0


# Integration Tests

@pytest.mark.asyncio
async def test_end_to_end_cot_workflow(mock_llm_provider, sample_question):
    """Test complete CoT workflow."""
    # Initialize components
    reasoner = ChainOfThoughtReasoner(mock_llm_provider, max_steps=3)
    evaluator = ReasoningEvaluator()
    tracer = LangSmithTracer(enabled=True)
    cost_tracker = CostTracker()

    # Execute reasoning with tracing
    with TracingContext(tracer, "E2E CoT Test") as trace_id:
        result = await reasoner.reason(
            question=sample_question,
            strategy=ReasoningStrategy.ZERO_SHOT
        )

        # Track cost
        cost_tracker.track_usage(
            operation_id=trace_id,
            model="gpt-4",
            input_tokens=result.token_count // 2,
            output_tokens=result.token_count // 2
        )

    # Evaluate
    evaluations = await evaluator.evaluate_cot(result)

    # Verify complete workflow
    assert result.final_answer
    assert len(evaluations) > 0
    assert cost_tracker.total_tokens > 0
    assert len(tracer.completed_traces) > 0


@pytest.mark.asyncio
async def test_end_to_end_tot_workflow(mock_llm_provider, sample_question):
    """Test complete ToT workflow."""
    explorer = TreeOfThoughtsExplorer(
        mock_llm_provider,
        max_depth=2,
        branching_factor=2
    )
    tracer = LangSmithTracer(enabled=True)

    with TracingContext(tracer, "E2E ToT Test") as trace_id:
        result = await explorer.explore(
            question=sample_question,
            strategy=SearchStrategy.BEST_FIRST
        )

    assert result.best_path is not None
    assert result.total_nodes > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=term-missing"])
